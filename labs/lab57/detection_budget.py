#!/usr/bin/env python3
"""Lab 57.2 --- why a 35-second attack is over before you see it, computed.

The chapter's detection table used to say flow telemetry has "broad visibility;
sampling adds a little delay". That gets the mechanism backwards in a way that
matters, and this lab replaces the sentence with two calculations.

  * PACKET SAMPLING REDUCES OBSERVATIONS. Waiting for enough sampled
    evidence can add detection delay; packet and request rates are not equal. What it costs is
    STATISTICAL CONFIDENCE, and it costs it in proportion to how small the
    thing you are looking for is. A 1:4096 sample sees a volumetric flood
    with many more observations than a 500-packet-per-second stream.
    That statement alone does not model application-request detection.
  * THE LATENCY IS IN THE TIMERS. The active-flow export timeout, the
    collector's aggregation window, the detector's own window, the decision,
    and the time for the mitigation to take effect. Those add up to tens of
    seconds in the stated serial-stage scenario. Stages may overlap or have
    different semantics in real collectors; measure the complete path.

Neither is an argument against flow telemetry. It is an argument for knowing
which question your telemetry can answer in time.

    python3 detection_budget.py
    python3 detection_budget.py --json
    python3 test_detection_budget.py
"""
import json
import math
import sys


class BudgetError(ValueError):
    pass


# ---------------------------------------------------------------------------
# 1. The latency budget --- where the seconds actually go
# ---------------------------------------------------------------------------

STAGES = (
    ('export_interval_s',
     'the exporter holds a long-lived flow until its ACTIVE timeout expires, so '
     'a flow that is still running is reported this long after it began'),
    ('collector_aggregation_s',
     'the collector groups records into a bucket before anything looks at them'),
    ('detector_window_s',
     'the detector needs a window of buckets to call a deviation'),
    ('decision_s',
     'the time to confirm and authorise --- zero only if the action is '
     'pre-authorised and automatic'),
    ('mitigation_effective_s',
     'from signalling the mitigation to traffic actually being dropped: BGP '
     'propagation and FIB installation, or a diversion taking effect'),
)


def latency_budget(**stages):
    """Total seconds from the first attack packet to traffic actually dropping."""
    unknown = sorted(set(stages) - {k for k, _ in STAGES})
    if unknown:
        raise BudgetError('unknown stage(s): %s' % ', '.join(unknown))
    total = 0.0
    breakdown = []
    for key, why in STAGES:
        v = stages.get(key)
        if v is None:
            raise BudgetError('%s was not supplied. Every stage must be stated: '
                              'an omitted stage silently becomes zero, and a '
                              'budget with a hidden zero in it is how "we detect '
                              'in five seconds" gets into a design document.' % key)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
            raise BudgetError('%s must be a non-negative number, not %r' % (key, v))
        total += float(v)
        breakdown.append(dict(stage=key, seconds=float(v), why=why))
    return dict(total_s=total, breakdown=breakdown)


def against_attack(total_s, attack_duration_s):
    """What that budget means for an attack of a given length."""
    if not math.isfinite(total_s) or total_s < 0:
        raise BudgetError('total delay must be finite and nonnegative')
    if not math.isfinite(attack_duration_s) or attack_duration_s <= 0:
        raise BudgetError('an attack duration must be positive')
    over = total_s >= attack_duration_s
    return dict(
        total_s=total_s, attack_duration_s=attack_duration_s,
        mitigation_in_time=not over,
        fraction_elapsed=min(1.0, total_s / attack_duration_s),
        seconds_of_attack_unmitigated=min(total_s, attack_duration_s),
        note=('The attack finishes before the mitigation takes effect. Anything '
              'the mitigation then does is applied to traffic that has already '
              'stopped.' if over else
              'The mitigation takes effect with %.1f s of the attack remaining.'
              % (attack_duration_s - total_s)))


# ---------------------------------------------------------------------------
# 2. Sampling --- what it costs, which is not latency
# ---------------------------------------------------------------------------

def expected_samples(pps, sample_one_in_n, window_s):
    for name, v in (('pps', pps), ('sample_one_in_n', sample_one_in_n),
                    ('window_s', window_s)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
            raise BudgetError('%s must be a positive number, not %r' % (name, v))
    if sample_one_in_n < 1:
        raise BudgetError('sampling divisor must be at least 1')
    return pps * window_s / float(sample_one_in_n)


def p_at_least(k, lam):
    """P(X >= k) for X ~ Poisson(lam). The count of sampled packets in a window
    is Binomial(n, 1/N) with n large and 1/N small, which Poisson approximates
    closely; the approximation is stated rather than hidden."""
    if type(k) is not int or k < 0:
        raise BudgetError('k must be a non-negative integer')
    if not math.isfinite(lam) or lam < 0:
        raise BudgetError('lam must be non-negative')
    if k == 0:
        return 1.0
    acc, term = 0.0, math.exp(-lam)
    for i in range(k):
        if i:
            term *= lam / i
        acc += term
    return max(0.0, 1.0 - acc)


def visibility(pps, sample_one_in_n, window_s, k=5):
    lam = expected_samples(pps, sample_one_in_n, window_s)
    return dict(pps=pps, sample_one_in_n=sample_one_in_n, window_s=window_s,
                expected_samples=lam, k=k, p_at_least_k=p_at_least(k, lam),
                approximation='Poisson(lambda = pps * window / N)')


# ---------------------------------------------------------------------------

BUDGETS = {
    'ordinary flow telemetry, human in the loop': dict(
        export_interval_s=60, collector_aggregation_s=30, detector_window_s=60,
        decision_s=180, mitigation_effective_s=30),
    'tuned flow telemetry, pre-authorised action': dict(
        export_interval_s=10, collector_aggregation_s=5, detector_window_s=10,
        decision_s=0, mitigation_effective_s=15),
    'in-path inspection, automatic': dict(
        export_interval_s=0, collector_aggregation_s=0, detector_window_s=2,
        decision_s=0, mitigation_effective_s=3),
}

ATTACKS = {'a 35-second burst': 35, 'a ten-minute flood': 600}

SAMPLING = [
    ('a volumetric flood', 9e9, 4096, 10),
    ('a packet-rate flood', 40e6, 4096, 10),
    ('a 500 req/s application flood', 500, 4096, 10),
    ('the same, unsampled', 500, 1, 10),
    ('the same, 1:1000 over 5 minutes', 500, 1000, 300),
]


def report(out=None):
    out = sys.stdout if out is None else out
    out.write('Lab 57.2 --- the detection budget, and what sampling actually costs\n')
    out.write('=' * 74 + '\n\n')
    out.write('WHERE THE SECONDS GO\n\n')
    out.write('  %-44s %8s  %s\n' % ('pipeline', 'total', 'against a 35 s burst'))
    rows = {}
    for name, stages in BUDGETS.items():
        b = latency_budget(**stages)
        rows[name] = b
        v = against_attack(b['total_s'], 35)
        out.write('  %-44s %7.0fs  %s\n'
                  % (name, b['total_s'],
                     'IN TIME, %.0f s to spare' % (35 - b['total_s'])
                     if v['mitigation_in_time'] else
                     'TOO LATE by %.0f s' % (b['total_s'] - 35)))
    out.write('\n  The first row is not a strawman: a 60-second active-flow timeout\n')
    out.write('  is a common default, and it alone is longer than the attack. The\n')
    out.write('  attack is over before its first export record leaves the router.\n\n')
    out.write('WHAT SAMPLING COSTS, WHICH IS NOT LATENCY\n\n')
    out.write('  %-40s %10s %9s\n' % ('what you are looking for', 'expected', 'P(>=5)'))
    for label, pps, n, w in SAMPLING:
        v = visibility(pps, n, w)
        out.write('  %-40s %10.3g %9.4f\n'
                  % ('%s (1:%d, %ds)' % (label, n, w), v['expected_samples'],
                     v['p_at_least_k']))
    out.write('\n  Sampling does not delay anything. It decides whether a small\n')
    out.write('  thing is visible at all --- and the same 1:4096 rate that sees a\n')
    out.write('  volumetric flood instantly is effectively blind to a 500-request\n')
    out.write('  per second application flood in a ten-second window. Widen the\n')
    out.write('  window and it becomes visible, at the cost of the latency in the\n')
    out.write('  table above. That is the real trade, and it is not the one the\n')
    out.write('  phrase "sampling adds a little delay" describes.\n')


def main(argv):
    if '--json' in argv:
        print(json.dumps({
            'budgets': {n: dict(latency_budget(**s),
                                **{'vs_%s' % a.replace(' ', '_'):
                                   against_attack(latency_budget(**s)['total_s'], d)
                                   for a, d in ATTACKS.items()})
                        for n, s in BUDGETS.items()},
            'sampling': [visibility(p, n, w) for _, p, n, w in SAMPLING],
        }, indent=1))
        return 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
