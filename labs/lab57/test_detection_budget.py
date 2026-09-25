#!/usr/bin/env python3
"""Tests for detection_budget.py.

The claim the chapter now makes is arithmetic, so it is checked as arithmetic:
the budget sums the stages it is given, refuses to invent a missing one, and
the sampling figures come from a distribution rather than from a feeling.

    python3 test_detection_budget.py
"""
import io
import math
import sys

import detection_budget as db

CHECKS = 0
FAILED = []


def ok(cond, label):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


def raises(fn, label, fragment=None):
    global CHECKS
    CHECKS += 1
    try:
        fn()
    except db.BudgetError as exc:
        if fragment and fragment not in str(exc):
            FAILED.append('%s (message lacked %r)' % (label, fragment))
        return
    except Exception as exc:                                    # noqa: BLE001
        FAILED.append('%s (raised %s)' % (label, type(exc).__name__))
        return
    FAILED.append('%s (did not raise)' % label)


# -- 1. The budget is the sum of stated stages, with nothing hidden ---------

b = db.latency_budget(export_interval_s=60, collector_aggregation_s=30,
                      detector_window_s=60, decision_s=180,
                      mitigation_effective_s=30)
ok(b['total_s'] == 360, 'the ordinary pipeline totals 360 s')
ok(len(b['breakdown']) == 5, 'all five stages are itemised')
ok(all(s['why'] for s in b['breakdown']), 'each stage explains itself')
ok(sum(s['seconds'] for s in b['breakdown']) == b['total_s'],
   'the itemisation sums to the total')

raises(lambda: db.latency_budget(export_interval_s=60),
       'an omitted stage is refused, not defaulted to zero', 'hidden zero')
raises(lambda: db.latency_budget(export_interval_s=-1, collector_aggregation_s=0,
                                 detector_window_s=0, decision_s=0,
                                 mitigation_effective_s=0),
       'a negative stage is refused')
raises(lambda: db.latency_budget(export_interval_s=True, collector_aggregation_s=0,
                                 detector_window_s=0, decision_s=0,
                                 mitigation_effective_s=0),
       'a bool is not a duration')
raises(lambda: db.latency_budget(made_up_stage=1), 'an unknown stage is refused',
       'unknown stage')


# -- 2. What the budget means for a burst ----------------------------------

v = db.against_attack(360, 35)
ok(v['mitigation_in_time'] is False, 'a 360 s pipeline does not catch a 35 s burst')
ok(v['fraction_elapsed'] == 1.0, 'the whole attack elapses first')
ok(v['seconds_of_attack_unmitigated'] == 35,
   'and all 35 seconds of it go unmitigated, not 360')
ok('already stopped' in v['note'], 'the note says the mitigation arrives too late')
v = db.against_attack(5, 35)
ok(v['mitigation_in_time'] is True, 'a 5 s pipeline does catch it')
ok(abs(v['fraction_elapsed'] - 5 / 35) < 1e-9, 'the elapsed fraction is right')
ok('30.0 s of the attack remaining' in v['note'], 'and it says how much is left')
v = db.against_attack(35, 35)
ok(v['mitigation_in_time'] is False,
   'equal is not in time: the attack has finished at the moment the filter lands')
raises(lambda: db.against_attack(10, 0), 'a zero-length attack is refused')

# The shipped budgets must actually behave as the chapter says.
totals = {n: db.latency_budget(**s)['total_s'] for n, s in db.BUDGETS.items()}
ok(totals['ordinary flow telemetry, human in the loop'] > 35,
   'the ordinary pipeline is longer than a 35 s burst')
ok(totals['tuned flow telemetry, pre-authorised action'] > 35,
   'AND SO IS THE TUNED ONE --- which is the uncomfortable part of the result')
ok(totals['in-path inspection, automatic'] < 35,
   'only the in-path pipeline is inside the burst')
ok(db.BUDGETS['ordinary flow telemetry, human in the loop']['export_interval_s'] > 35,
   'the 60 s active-flow timeout alone exceeds the attack')


# -- 3. Sampling costs confidence, and the numbers come from a distribution --

ok(db.expected_samples(1000, 100, 10) == 100.0, 'expected samples is pps*window/N')
raises(lambda: db.expected_samples(0, 100, 10), 'a zero rate is refused')
raises(lambda: db.expected_samples(1000, 0, 10), 'a zero sampling divisor is refused')
raises(lambda: db.expected_samples(1000, 100, -1), 'a negative window is refused')

ok(db.p_at_least(0, 5) == 1.0, 'P(X >= 0) is 1')
ok(abs(db.p_at_least(1, 0.0) - 0.0) < 1e-12, 'with lambda 0 nothing is ever seen')
# Check the Poisson tail against a direct sum for a small case.
lam = 2.5
direct = 1 - sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(5))
ok(abs(db.p_at_least(5, lam) - direct) < 1e-12,
   'the tail matches a direct Poisson sum')
ok(db.p_at_least(5, 1000) > 0.999999, 'a large expectation is a certainty')
raises(lambda: db.p_at_least(-1, 1), 'a negative k is refused')
raises(lambda: db.p_at_least(1.5, 1), 'a non-integer k is refused')

vol = db.visibility(9e9, 4096, 10)
app = db.visibility(500, 4096, 10)
ok(vol['p_at_least_k'] > 0.999, 'a volumetric flood is certain to be sampled')
ok(app['p_at_least_k'] < 0.05,
   'A 500 REQ/S FLOOD AT 1:4096 IN TEN SECONDS IS ESSENTIALLY INVISIBLE (%.4f)'
   % app['p_at_least_k'])
ok(app['expected_samples'] < 2, 'because barely one packet is expected')
wide = db.visibility(500, 1000, 300)
ok(wide['p_at_least_k'] > 0.999,
   'widening the window makes the same flood visible --- at the cost of latency')
ok(db.visibility(500, 1, 10)['p_at_least_k'] > 0.999,
   'and so does not sampling at all')
ok('Poisson' in app['approximation'], 'the approximation is stated, not hidden')


# -- 4. The report --------------------------------------------------------

buf = io.StringIO()
db.report(buf)
out = buf.getvalue()
ok('TOO LATE' in out, 'the report marks the pipelines that miss the burst')
ok('IN TIME' in out, 'and the one that does not')
ok('does not delay anything' in out,
   'the report states plainly that sampling is not a latency')
ok('60-second active-flow timeout' in out, 'and names the timer that dominates')
ok(out.count('adds a little delay') <= 1,
   'the old phrase appears at most once')
ok('is not the one the' in out and 'adds a little delay' in out,
   'and where it appears it is quoted in order to be refuted, not asserted')
_s = sys.stdout
sys.stdout = io.StringIO()
try:
    rc, rj = db.main([]), db.main(['--json'])
finally:
    sys.stdout = _s
ok(rc == 0 and rj == 0, 'both modes run')

print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
