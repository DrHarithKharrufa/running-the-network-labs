#!/usr/bin/env python3
"""Lab 57.1 --- what the observables support about an attack, and what they do not.

THE DEFECT THIS REPLACES. The shipped version took four numbers, walked three
hard-coded thresholds and returned one class with one place to mitigate. Four
things were wrong with it, and the first is the worst:

  1. IT WAS CONFIDENT FROM SPARSE INPUT. Four numbers, no baseline, no units,
     no error bars, and out came "application (L7) --- network scrubbing and
     RTBH will NOT help". An operator acts on that at three in the morning.
  2. ITS ARITHMETIC WAS WRONG ABOUT ITS OWN CLAIM. Its README said 80 per cent
     utilisation meant the flood was "bigger than your pipe". Eighty per cent of
     a pipe is smaller than the pipe. A link at 80 per cent is congested and
     probably losing traffic; it is not proof that the attack exceeds capacity,
     and the mitigation that follows from the two is different.
  3. THE THRESHOLDS DO NOT GENERALISE. 5 Mpps and 10 Mpps are meaningless
     without a platform: they are a rounding error to one box and fatal to
     another. A threshold with no baseline is a guess with a number on it.
  4. THE CLASSES WERE MUTUALLY EXCLUSIVE. Real attacks are not. A packet-rate
     flood can saturate a link; an application flood can be high volume; and
     more than one resource is often exhausted at once, which is exactly when
     picking one class sends you to the wrong mitigation.

So this version returns HYPOTHESES tied to a named resource and a stated
baseline, permits several at once, says what would discriminate between them,
and refuses inputs it cannot reason about.

    python3 ddos_triage.py
    python3 ddos_triage.py --json
    python3 ddos_triage.py --prove     # every hypothesis is reachable
    python3 test_ddos_triage.py
"""
import itertools
import json
import sys

UNKNOWN = 'unknown'


class TriageError(ValueError):
    """The input cannot be reasoned about. Raised, never worked around."""


# ---------------------------------------------------------------------------
# Observations. Each is a measurement WITH its baseline, because a number
# without a baseline cannot support a conclusion about a deviation.
# ---------------------------------------------------------------------------

MEASURES = {
    'ingress_bps': 'offered bits per second at the ingress, measured BEFORE any '
                   'drop [interface counters at the upstream side of the '
                   'congested link, not your own side of it]',
    'link_capacity_bps': 'the capacity of the link that is congested',
    'ingress_pps': 'offered packets per second',
    'platform_pps_capacity': 'the packet rate this platform is rated for, or '
                             'measured at, in the same units',
    'new_flows_per_s': 'new connections or handshakes per second',
    'concurrent_flows': 'concurrent sessions held in state',
    'state_table_capacity': 'the state-table size of the device under pressure',
    'server_cpu_pct': 'CPU of the serving tier',
    'app_latency_ms': 'observed application latency',
    'app_latency_baseline_ms': 'the same measure on a normal day',
    'drops_at_ingress': 'whether the congested device is dropping at ingress',
}

BASELINES = {
    'ingress_bps': 'link_capacity_bps',
    'ingress_pps': 'platform_pps_capacity',
    'concurrent_flows': 'state_table_capacity',
    'app_latency_ms': 'app_latency_baseline_ms',
}

HYPOTHESIS, EXCLUDED, NEEDED = 'HYPOTHESIS', 'EXCLUDED', 'EVIDENCE NEEDED'


def _num(v, name):
    if v == UNKNOWN:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise TriageError('%s must be a number or %r, not %r' % (name, UNKNOWN, v))
    if v < 0:
        raise TriageError('%s cannot be negative (%r) --- a rate or a count is '
                          'never below zero, so this is a unit or sign error' % (name, v))
    return float(v)


def _validate(obs):
    if not isinstance(obs, dict):
        raise TriageError('observations must be a dict, not %s' % type(obs).__name__)
    unknown = sorted(set(obs) - set(MEASURES))
    if unknown:
        raise TriageError('unrecognised measure(s): %s --- add them to MEASURES '
                          'with the instrument that yields them' % ', '.join(unknown))
    vals = {}
    for k, v in obs.items():
        if k == 'drops_at_ingress':
            if v is not True and v is not False and v != UNKNOWN:
                raise TriageError('drops_at_ingress must be True, False or %r' % UNKNOWN)
            vals[k] = v
        else:
            vals[k] = _num(v, k)
    for k, base in BASELINES.items():
        if vals.get(k) is not None and vals.get(base) is None:
            raise TriageError(
                '%s was supplied without %s. A rate with no baseline cannot support '
                'a conclusion about a deviation: 40 Mpps is a rounding error on one '
                'platform and fatal on another.' % (k, base))
    for cap in ('link_capacity_bps', 'platform_pps_capacity', 'state_table_capacity'):
        if vals.get(cap) is not None and vals[cap] == 0:
            raise TriageError('%s is zero; a capacity of zero cannot be a denominator' % cap)
    return vals


def analyse(observations=None):
    """Return hypotheses, each tied to a measured resource and its baseline."""
    if observations is not None and not isinstance(observations, dict):
        raise TriageError('observations must be a dict, not %s --- an empty list '
                          'is falsy and would otherwise be read as "nothing '
                          'measured"' % type(observations).__name__)
    v = _validate(dict(observations or {}))
    out, needed = [], []

    def ratio(a, b):
        if v.get(a) is None or v.get(b) is None:
            return None
        return v[a] / v[b]

    # --- bandwidth -------------------------------------------------------
    r = ratio('ingress_bps', 'link_capacity_bps')
    if r is None:
        needed.append(('bandwidth', 'ingress_bps and link_capacity_bps'))
    elif r >= 1.0:
        out.append(dict(
            id='bandwidth-exceeded', verdict=HYPOTHESIS, resource='link bandwidth',
            measured='offered %.3g bit/s against a %.3g bit/s link (%.2fx)'
                     % (v['ingress_bps'], v['link_capacity_bps'], r),
            says='The offered load EXCEEDS the link. Filtering downstream of this '
                 'link cannot relieve it --- the loss already happened upstream. '
                 'Mitigation must be applied before the constrained link: at the '
                 'upstream, or by diversion to a scrubbing path with more capacity.',
            caveat='This holds only if ingress_bps was measured as OFFERED load '
                   'before the drop. A counter on your own side of a saturated '
                   'link reads the capacity, not the attack.'))
    elif r >= 0.8:
        out.append(dict(
            id='bandwidth-congested', verdict=HYPOTHESIS, resource='link bandwidth',
            measured='offered %.3g bit/s against a %.3g bit/s link (%.0f%%)'
                     % (v['ingress_bps'], v['link_capacity_bps'], r * 100),
            says='The link is heavily loaded but the offered load DOES NOT EXCEED '
                 'it. Queueing and loss are likely; a flood larger than the link '
                 'is not demonstrated. Local filtering can still help here, which '
                 'is the difference this distinction makes.',
            caveat='80 per cent of a pipe is smaller than the pipe. The shipped '
                   'version of this lab called this "bigger than your pipe".'))

    # --- packet rate ------------------------------------------------------
    r = ratio('ingress_pps', 'platform_pps_capacity')
    if r is None:
        needed.append(('packet rate', 'ingress_pps and platform_pps_capacity'))
    elif r >= 0.8:
        out.append(dict(
            id='packet-rate-pressure', verdict=HYPOTHESIS, resource='per-packet processing',
            measured='%.3g pps against a rated %.3g pps (%.0f%%)'
                     % (v['ingress_pps'], v['platform_pps_capacity'], r * 100),
            says='Packet rate is at or beyond what this platform is rated for. '
                 'Small packets exhaust per-packet processing long before they '
                 'fill a link --- and can also saturate one, so this is not an '
                 'alternative to the bandwidth hypothesis.',
            caveat='The rating must be for this platform and this feature set. '
                   'A figure from a datasheet headline is usually measured with '
                   'no features enabled.'))

    # --- state ------------------------------------------------------------
    r = ratio('concurrent_flows', 'state_table_capacity')
    if r is None:
        needed.append(('state', 'concurrent_flows and state_table_capacity'))
    elif r >= 0.8:
        out.append(dict(
            id='state-exhaustion', verdict=HYPOTHESIS, resource='connection state',
            measured='%.3g concurrent against a table of %.3g (%.0f%%)'
                     % (v['concurrent_flows'], v['state_table_capacity'], r * 100),
            says='The state table is at or near capacity. A device that cannot '
                 'allocate state drops NEW sessions while existing ones continue, '
                 'so the symptom is "new users cannot connect" rather than "the '
                 'site is down".'))
    if v.get('new_flows_per_s') is not None and v.get('concurrent_flows') is not None \
            and v['new_flows_per_s'] > 0 and v['concurrent_flows'] / max(v['new_flows_per_s'], 1) < 2:
        out.append(dict(
            id='half-open-churn', verdict=HYPOTHESIS, resource='connection state',
            measured='%.3g new flows/s holding only %.3g concurrent'
                     % (v['new_flows_per_s'], v['concurrent_flows']),
            says='A high arrival rate with little accumulated state is the shape '
                 'of connections that never complete --- a handshake flood rather '
                 'than a load spike.',
            caveat='It is also the shape of a healthy, very short-lived workload. '
                   'Compare with the same ratio on a normal day before acting.'))

    # --- application ------------------------------------------------------
    cpu = v.get('server_cpu_pct')
    lat = ratio('app_latency_ms', 'app_latency_baseline_ms')
    if cpu is None:
        needed.append(('application', 'server_cpu_pct'))
    elif cpu >= 90:
        out.append(dict(
            id='application-work', verdict=HYPOTHESIS, resource='application CPU',
            measured='serving tier at %.0f%% CPU%s'
                     % (cpu, '' if lat is None else ', latency %.1fx baseline' % lat),
            says='The serving tier is saturated. That is consistent with an '
                 'application-layer flood, and equally consistent with a genuine '
                 'traffic spike, a slow dependency, a bad deploy or a runaway '
                 'query. The measurement does not distinguish them.',
            caveat='Before calling this an attack, exclude the benign causes: '
                   'compare request mix and client population with a normal day, '
                   'and check what changed. CPU is a symptom, not an attacker.'))

    # --- what the evidence cannot decide ----------------------------------
    for topic, what in needed:
        out.append(dict(id='need-%s' % topic.replace(' ', '-'), verdict=NEEDED,
                        resource=topic, measured='not supplied',
                        says='Supply %s. Until then nothing can be said about %s, '
                             'and its absence is not evidence that it is fine.'
                             % (what, topic), caveat=None))

    bottlenecks = sorted({h['resource'] for h in out if h['verdict'] == HYPOTHESIS})
    return {
        'hypotheses': [h for h in out if h['verdict'] == HYPOTHESIS],
        'evidence_needed': [h for h in out if h['verdict'] == NEEDED],
        'resources_under_pressure': bottlenecks,
        'simultaneous': len(bottlenecks) > 1,
        'verdict_withheld': ('This model names resources under pressure. It does '
                             'not name an attacker, a class or a mitigation, '
                             'because the same measurements are produced by faults '
                             'and by legitimate load.'),
        'measures_supplied': len([k for k in v if v[k] is not None]),
        'measures_total': len(MEASURES),
    }


# ---------------------------------------------------------------------------
# An amplification RATIO is arithmetic about two byte counts. It is not a
# measurement of traffic, and the shipped lab printed it as though it were.
# ---------------------------------------------------------------------------

def amplification_ratio(query_bytes, response_bytes):
    """Bytes returned per byte sent. A ratio, nothing more."""
    for n, val in (('query_bytes', query_bytes), ('response_bytes', response_bytes)):
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise TriageError('%s must be a number, not %r' % (n, val))
        if val <= 0:
            raise TriageError('%s must be greater than zero; a zero-length query '
                              'has no ratio, and the shipped lab would have '
                              'divided by it' % n)
    return response_bytes / float(query_bytes)


def amplified_bps(ratio, attacker_bps, reflectors_reachable=None):
    """What a ratio DOES and DOES NOT tell you about delivered traffic."""
    if ratio <= 0 or attacker_bps < 0:
        raise TriageError('a ratio must be positive and a rate non-negative')
    return {
        'ceiling_bps': ratio * attacker_bps,
        'is_a_measurement': False,
        'why': ('This is an upper bound from arithmetic, not traffic. Reaching it '
                'needs enough reachable reflectors, enough path capacity to each '
                'of them and back, and no rate limiting anywhere in between. '
                'Reflectors respond at their own pace and many are already rate '
                'limited. Treat it as the size of the prize, not the size of the '
                'flood.'),
        'reflectors_reachable': reflectors_reachable,
    }


CASES = {
    'the link is full and the offered load is far larger': dict(
        ingress_bps=31.4e12, link_capacity_bps=100e9, ingress_pps=9e9,
        platform_pps_capacity=2e9, server_cpu_pct=20, drops_at_ingress=True),
    'a handshake flood: packet rate high, link half empty': dict(
        ingress_bps=40e9, link_capacity_bps=100e9, ingress_pps=40e6,
        platform_pps_capacity=30e6, new_flows_per_s=2e6, concurrent_flows=1.5e6,
        state_table_capacity=2e6, server_cpu_pct=55),
    'servers pegged, links quiet --- and that is all we know': dict(
        server_cpu_pct=100, ingress_bps=8e9, link_capacity_bps=100e9),
    'the link at 80 per cent, which is NOT bigger than the pipe': dict(
        ingress_bps=80e9, link_capacity_bps=100e9),
    'a ticket that says "we are under attack" and nothing else': dict(),
}


def prove_every_hypothesis_reachable():
    """The fourth question: can each hypothesis ever fire?"""
    grid = {
        'ingress_bps': [10e9, 80e9, 200e9], 'link_capacity_bps': [100e9],
        'ingress_pps': [1e6, 40e6], 'platform_pps_capacity': [30e6],
        'new_flows_per_s': [10, 2e6], 'concurrent_flows': [100, 1.9e6],
        'state_table_capacity': [2e6], 'server_cpu_pct': [10, 95],
    }
    keys = sorted(grid)
    seen, tried = {}, 0
    for combo in itertools.product(*[grid[k] for k in keys]):
        tried += 1
        obs = dict(zip(keys, combo))
        try:
            res = analyse(obs)
        except TriageError:
            continue
        for h in res['hypotheses']:
            seen.setdefault(h['id'], obs)
    ids = {'bandwidth-exceeded', 'bandwidth-congested', 'packet-rate-pressure',
           'state-exhaustion', 'half-open-churn', 'application-work'}
    return dict(enumerated=tried, reached=sorted(seen), witnesses=seen,
                unreachable=sorted(ids - set(seen)))


def _wrap(text, indent, width=76):
    words, lines, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > width - indent:
            lines.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
    lines.append(cur)
    return ('\n' + ' ' * indent).join(lines)


def report(out=None):
    out = sys.stdout if out is None else out
    out.write('Lab 57.1 --- which resource is under pressure, and on what evidence\n')
    out.write('=' * 74 + '\n\n')
    for name, obs in CASES.items():
        res = analyse(obs)
        out.write('CASE: %s\n' % name)
        out.write('  measures supplied: %d of %d\n'
                  % (res['measures_supplied'], res['measures_total']))
        for h in res['hypotheses']:
            out.write('  %-12s %s\n' % (h['verdict'], h['id']))
            out.write('               measured: %s\n' % _wrap(h['measured'], 25))
            out.write('               %s\n' % _wrap(h['says'], 15))
            if h.get('caveat'):
                out.write('               but: %s\n' % _wrap(h['caveat'], 20))
        if res['simultaneous']:
            out.write('  MORE THAN ONE RESOURCE IS UNDER PRESSURE: %s. Picking one\n'
                      % ', '.join(res['resources_under_pressure']))
            out.write('  class here is how an operator mitigates the wrong thing.\n')
        if not res['hypotheses']:
            out.write('  (no resource can be shown to be under pressure)\n')
        for n in res['evidence_needed']:
            out.write('  %-12s %s\n' % (n['verdict'], _wrap(n['says'], 15)))
        out.write('\n')
    r = amplification_ratio(60, 3000)
    out.write('An amplification RATIO is arithmetic, not traffic:\n')
    out.write('  a %d-byte query drawing a %d-byte reply is a ratio of %.0f to 1.\n'
              % (60, 3000, r))
    a = amplified_bps(r, 1e9)
    out.write('  %s\n' % _wrap('A 1 Gb/s attacker aiming that ratio has a CEILING of '
                               '%.3g bit/s. %s' % (a['ceiling_bps'], a['why']), 2))
    out.write('\nThis model names resources under pressure. It does not name an\n')
    out.write('attacker, a class or a mitigation, because faults and legitimate\n')
    out.write('load produce the same measurements.\n')


def main(argv):
    if '--json' in argv:
        print(json.dumps({n: analyse(o) for n, o in CASES.items()}, indent=1, sort_keys=True))
        return 0
    if '--prove' in argv:
        p = prove_every_hypothesis_reachable()
        print('Reachability of every hypothesis, over %d input combinations.\n' % p['enumerated'])
        for i in p['reached']:
            print('  %-24s CAN FIRE' % i)
        for i in p['unreachable']:
            print('  %-24s DEAD CODE --- no input in the grid reaches it' % i)
        print()
        print('  every hypothesis is reachable' if not p['unreachable']
              else '  %d unreachable' % len(p['unreachable']))
        return 1 if p['unreachable'] else 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
