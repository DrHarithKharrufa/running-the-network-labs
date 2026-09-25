#!/usr/bin/env python3
"""Tests for detector_quality.py.

Two claims are under test and both must fail in their strong form: that a
beacon is distinguishable from legitimate automation, and that precision is a
property of a rule.

    python3 test_detector_quality.py
"""
import io
import random
import sys

import detector_quality as dq

CHECKS, FAILED = 0, []


def ok(c, l):
    global CHECKS
    CHECKS += 1
    if not c:
        FAILED.append(l)


def raises(fn, label, fragment=None):
    global CHECKS
    CHECKS += 1
    try:
        fn()
    except dq.DetectorError as e:
        if fragment and fragment not in str(e):
            FAILED.append('%s (message lacked %r)' % (label, fragment))
        return
    except Exception as e:                                       # noqa: BLE001
        FAILED.append('%s (raised %s)' % (label, type(e).__name__))
        return
    FAILED.append('%s (did not raise)' % label)


# -- 1. The regularity measure itself --------------------------------------

ok(dq.regularity([0, 60, 120, 180])['cv'] == 0.0, 'a perfect beacon has CV zero')
ok(dq.regularity([0, 60, 120, 180])['mean_gap'] == 60, 'and a mean gap of 60')
ok(dq.regularity([180, 0, 120, 60])['cv'] == 0.0, 'unsorted input is sorted first')
r = dq.regularity([0, 10, 100, 110])
ok(r['cv'] > 0.5, 'an irregular series has a high CV')
raises(lambda: dq.regularity([0, 60]), 'two events are refused', 'at least three')
raises(lambda: dq.regularity([0, 0, 60]), 'duplicate timestamps are refused', 'clock')
raises(lambda: dq.regularity([]), 'an empty series is refused')
ok(dq.flags([0, 60, 120, 180]) is True, 'the flag fires on a perfect beacon')
ok(dq.flags(dq.person()) is False, 'and not on a person')


# -- 2. Legitimate automation is MORE regular than a jittered beacon -------

s = dq.jitter_sweep()
cron = s['benign_cv']['hourly cron job']
push = s['benign_cv']['telemetry push every 60s']
human = s['benign_cv']['a person browsing']
ok(cron < 0.01, 'a cron job is almost perfectly regular (CV %.4f)' % cron)
ok(push < 0.1, 'and a telemetry push nearly so (CV %.3f)' % push)
ok(human > 0.5, 'while a person is not (CV %.3f)' % human)

rows = {r['jitter']: r for r in s['rows']}
ok(rows[0.0]['detected'] is True, 'an unjittered beacon is detected')
ok(rows[0.3]['detected'] is False, 'A BEACON WITH 30%% JITTER IS NOT')
ok(rows[0.5]['detected'] is False, 'nor one with 50%')
ok(rows[0.3]['cv'] > push and rows[0.3]['cv'] > cron,
   'AND THE MISSED BEACON IS LESS REGULAR THAN BOTH SCHEDULED JOBS --- so no '
   'threshold separates them')
t = dq.threshold_to_catch(0.3)
ok('hourly cron job' in t['also_caught'],
   'loosening the threshold to catch it also catches the cron job')
ok('telemetry push every 60s' in t['also_caught'], 'and the telemetry push')
ok('a person browsing' not in t['also_caught'],
   'though not the human, which is the one thing the detector does do')
ok(t['required_threshold'] > s['threshold'],
   'and the required threshold is looser than the shipped one')
ok(all(rows[a]['cv'] <= rows[b]['cv'] for a, b in zip(sorted(rows)[:-1], sorted(rows)[1:])),
   'CV rises monotonically with jitter')

# Determinism: the same seed gives the same answer.
ok(dq.jitter_sweep() == dq.jitter_sweep(), 'the sweep is deterministic')
ok(dq.regularity(dq.beacon(jitter_frac=0.2, rng=random.Random(1)))['cv'] > 0,
   'a jittered beacon has non-zero CV whatever the seed')


# -- 3. Precision is a property of the rule AND the prevalence -------------

hi = dq.alert_economics(100000, 0.0005, **dq.TUNINGS['precise'])
lo = dq.alert_economics(100000, 0.00002, **dq.TUNINGS['precise'])
ok(abs(hi['precision'] - 0.75) < 0.01, 'the precise rule is 75%% precise at one prevalence')
ok(lo['precision'] < 0.2,
   'AND UNDER 20%% AT ANOTHER, WITH NO CHANGE TO THE RULE (%.1f%%)'
   % (100 * lo['precision']))
ok(hi['recall'] == lo['recall'], 'while recall, which IS a property of the rule, is unchanged')
sens = dq.alert_economics(100000, 0.0005, **dq.TUNINGS['sensitive'])
ok(sens['missed'] < hi['missed'],
   'the sensitive tuning misses far fewer (%.1f against %.1f)'
   % (sens['missed'], hi['missed']))
ok(sens['alerts'] > hi['alerts'] * 20, 'at the price of many more alerts')
ok(sens['analyst_hours'] > hi['analyst_hours'], 'and many more analyst hours')
ok(hi['missed'] / (hi['true_positives'] + hi['missed']) > 0.65,
   'the precise tuning misses more than two thirds of what it looks for')
ok(abs(hi['true_positives'] + hi['false_negatives']
       - 100000 * 0.0005) < 1e-9, 'the positives account for the whole prevalence')
ok(abs(hi['alerts'] - (hi['true_positives'] + hi['false_positives'])) < 1e-9,
   'and the alerts for the whole queue')
ok(dq.alert_economics(100000, 0.0005, recall=0.7, false_positive_rate=0.001,
                      cost_of_a_miss=50000)['cost_of_misses'] > 0,
   'a cost of a miss can be priced when one is supplied')
raises(lambda: dq.alert_economics(100000, 1.5, recall=0.5, false_positive_rate=0.1),
       'a prevalence above 1 is refused', 'probability')
raises(lambda: dq.alert_economics(0, 0.1, recall=0.5, false_positive_rate=0.1),
       'a zero population is refused')
raises(lambda: dq.alert_economics(100, 0.1, recall=True, false_positive_rate=0.1),
       'a bool is not a recall')


# -- 4. The report --------------------------------------------------------

buf = io.StringIO()
dq.report(buf)
raw = buf.getvalue()
t = ' '.join(raw.split())          # the report wraps, so compare flattened
ok('no threshold that catches a jittered beacon' in t,
   'the report states the periodicity conclusion')
ok('not a property of the rule' in t.lower(), 'and the precision one')
ok('price both' in t, 'and asks for both costs to be priced')
for banned in ('nothing human does this', 'cannot avoid'):
    ok(banned not in t.lower(), 'the report never says %r' % banned)
_s = sys.stdout
sys.stdout = io.StringIO()
try:
    rc, rj = dq.main([]), dq.main(['--json'])
finally:
    sys.stdout = _s
ok(rc == 0 and rj == 0, 'both modes run')

print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
