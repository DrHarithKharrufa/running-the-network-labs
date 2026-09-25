"""Offline acceptance model. Synthetic inputs; no device or network access.

PASS means only that these declared checks passed on the supplied observations.
It is not authorisation to deploy and cannot prove an absence of other harm.
"""
from copy import deepcopy
from dataclasses import dataclass
import json
import math


def number(value, minimum=0):
    return type(value) in (int, float) and math.isfinite(value) and value >= minimum


@dataclass(frozen=True)
class Check:
    name: str
    state: str
    detail: str


def evaluate(before, after, *, target, approved_digest, required_routes,
             max_age_s=30, min_window_s=120, max_error_rate=0.1,
             max_loss_fraction=0.001):
    """Refuse unknowns. Thresholds are illustrative, explicitly supplied policy.

    Counter samples use a monotonically increasing observation clock, the same
    boot ID and counter epoch. Wraps/resets require fresh baselines. Probe counts
    describe the named service test in the AFTER observation window, not a delta.
    """
    if not all(number(x) for x in (max_age_s, min_window_s, max_error_rate, max_loss_fraction)):
        raise ValueError('finite non-negative limits required')
    if min_window_s == 0 or max_loss_fraction > 1:
        raise ValueError('positive observation window and loss bound <= 1 required')
    if not target or not approved_digest or not required_routes:
        raise ValueError('non-empty target, approved digest and route set required')
    checks = []
    def add(name, state, detail):
        checks.append(Check(name, state, detail))
    for phase, sample in [('before', before), ('after', after)]:
        if sample.get('target') != target:
            add(phase+' target', 'UNKNOWN', 'missing or wrong measurement target')
        else:
            add(phase+' target', 'PASS', target)
        age = sample.get('age_s')
        health = sample.get('collector_ok')
        if health is not True or not number(age) or age > max_age_s:
            add(phase+' freshness', 'UNKNOWN', 'missing, stale or unhealthy collection')
        else:
            add(phase+' freshness', 'PASS', 'fresh when collected')
    # The before sample may now be old; its age_s was measured at capture time.
    digest = after.get('config_digest')
    if not digest:
        add('configuration identity', 'UNKNOWN', 'no read-back digest')
    else:
        add('configuration identity', 'PASS' if digest == approved_digest else 'FAIL',
            'compare canonical read-back to the approved rendered artefact')
    routes = after.get('routes')
    if not isinstance(routes, list) or not all(isinstance(x, str) for x in routes):
        add('required routes', 'UNKNOWN', 'no valid route observation')
    else:
        missing = sorted(set(required_routes)-set(routes))
        add('required routes', 'FAIL' if missing else 'PASS', 'missing='+repr(missing))
    values = [before.get('at_s'), after.get('at_s'), before.get('rx_errors'), after.get('rx_errors')]
    same_epoch = (bool(before.get('boot_id')) and before.get('boot_id') == after.get('boot_id')
                  and bool(before.get('counter_epoch'))
                  and before.get('counter_epoch') == after.get('counter_epoch'))
    if (not all(number(x) for x in values) or not same_epoch
            or values[1] <= values[0] or values[3] < values[2]):
        add('error rate', 'UNKNOWN', 'reset, wrap, identity change or invalid counter interval')
    else:
        rate = (values[3]-values[2])/(values[1]-values[0])
        add('error rate', 'PASS' if rate <= max_error_rate else 'FAIL', f'{rate:.6f} errors/s')
    sent, lost, window = (after.get(x) for x in ['probe_sent', 'probe_lost', 'probe_window_s'])
    if (type(sent) is not int or type(lost) is not int or sent <= 0 or not 0 <= lost <= sent
            or not number(window) or window < min_window_s):
        add('service probe', 'UNKNOWN', 'missing, invalid or too short an observation')
    else:
        loss = lost/sent
        add('service probe', 'PASS' if loss <= max_loss_fraction else 'FAIL', f'{loss:.6f} loss fraction')
    # Keep every check visible: a known failure must not hide concurrent unknowns.
    verdict = 'FAIL' if any(c.state == 'FAIL' for c in checks) else (
        'UNKNOWN' if any(c.state == 'UNKNOWN' for c in checks) else 'PASS')
    return {'verdict':verdict, 'checks':[c.__dict__ for c in checks]}


def fixture():
    before = dict(target='edge-01', age_s=2, collector_ok=True, at_s=0,
                  boot_id='boot-A', counter_epoch='counter-A', rx_errors=100,
                  config_digest='old', routes=['service-A', 'service-B'])
    after = dict(before, at_s=120, rx_errors=106, config_digest='approved',
                 probe_sent=1000, probe_lost=0, probe_window_s=120)
    policy = dict(target='edge-01', approved_digest='approved',
                  required_routes=['service-A','service-B'])
    return before, after, policy


def scenarios():
    before, after, policy = fixture()
    variants = {'healthy':{}, 'stale':{'age_s':31}, 'probe absent':{'probe_sent':None},
                'counter reset':{'rx_errors':3,'counter_epoch':'counter-B'},
                'loss':{'probe_lost':2}, 'wrong render':{'config_digest':'unapproved'},
                'same route count, wrong prefix':{'routes':['service-A','service-C']}}
    return {name:evaluate(before, dict(after,**changes), **policy)
            for name, changes in variants.items()}


if __name__ == '__main__':
    print(json.dumps({'scope':'offline synthetic observations only', 'scenarios':scenarios()},indent=2))
