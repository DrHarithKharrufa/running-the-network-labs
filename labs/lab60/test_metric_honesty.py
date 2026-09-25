#!/usr/bin/env python3
"""Tests for lab 60.1.  Run: python3 test_metric_honesty.py"""
import io
import random
import sys

import metric_honesty as m

PASS = [0]


def ok(cond, what):
    if not cond:
        raise AssertionError(what)
    PASS[0] += 1


def raises(fn, what):
    try:
        fn()
    except m.MetricError:
        PASS[0] += 1
        return
    raise AssertionError('expected MetricError: %s' % what)


# ---- percentile, stated definition -----------------------------------------
v = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
ok(m.percentile(v, 0.90) == 9.0, 'nearest rank p90 of 1..10 is the 9th value')
ok(m.percentile(v, 0.95) == 10.0, 'ceil(9.5) = 10th value')
ok(m.percentile(v, 1.0) == 10.0, 'p100 is the maximum')
ok(m.percentile([5.0], 0.5) == 5.0, 'a single value is every percentile')
ok(m.percentile([1.0, 2.0], 0.5) == 1.0, 'ceil(1.0) = first value')
raises(lambda: m.percentile([], 0.9), 'no percentile of an empty sample')
raises(lambda: m.percentile(v, 0.0), 'p must exceed 0')
raises(lambda: m.percentile(v, 1.5), 'p must not exceed 1')

# ---- summarise: never a mean alone, and never a fake zero ------------------
s = m.summarise(v)
ok(s['n'] == 10 and s['mean'] == 5.5 and s['median'] == 5.5, 'summary of 1..10')
ok(s['worst'] == 10.0 and s['p90'] == 9.0, 'tail carried alongside the mean')
e = m.summarise([])
ok(e['n'] == 0, 'empty cohort reports n=0')
ok('mean' not in e, 'an empty cohort has NO mean key, so nobody reads a zero')
ok('note' in e and 'no number' in e['note'], 'and says why')
raises(lambda: m.summarise([1.0, -2.0]), 'a negative duration is a clock fault')
ok(m.summarise([3, 1, 2])['median'] == 2, 'unsorted input is sorted first')

# ---- population -------------------------------------------------------------
raises(lambda: m.population(0), 'n must be positive')
raises(lambda: m.population(-5), 'n must be positive')
raises(lambda: m.population(True), 'a bool is not a count')
p1 = m.population()
p2 = m.population()
ok([x['detect_hours'] for x in p1] == [x['detect_hours'] for x in p2],
   'the seed makes the population reproducible')
ok(len(p1) == 200, 'default population is 200 incidents')
ok(all(x['detect_hours'] > 0 for x in p1), 'all detection times positive')
ok(all(x['respond_hours'] >= 0.5 for x in p1), 'response floor honoured')
quiet = [x for x in p1 if x['kind'] == 'quiet']
ok(20 < len(quiet) < 60, 'roughly a fifth are quiet, got %d' % len(quiet))
ok(m.population(10, random.Random(1)) != m.population(10, random.Random(2)),
   'a caller-supplied rng is actually used')

# ---- detected_subset --------------------------------------------------------
raises(lambda: m.detected_subset(p1, -0.1), 'rate below zero')
raises(lambda: m.detected_subset(p1, 1.1), 'rate above one')
raises(lambda: m.detected_subset(p1, True), 'a bool is not a probability')
seen, missed = m.detected_subset(p1, 1.0)
ok(len(missed) == 0 and len(seen) == 200, 'perfect detection misses nothing')
seen, missed = m.detected_subset(p1, 0.0)
ok(all(x['kind'] == 'quiet' for x in missed), 'only quiet incidents are missed')
ok(len(missed) == len(quiet), 'at rate zero every quiet incident is missed')
ok(all(x['kind'] == 'loud' for x in seen), 'and only the loud ones remain')

# ---- the survivorship result this lab exists to show ------------------------
good = m.programme(p1, 0.90, 'good')
bad = m.programme(p1, 0.20, 'bad')
ok(bad['undetected'] > good['undetected'], 'the worse programme misses more')
ok(bad['detection']['mean'] < good['detection']['mean'],
   'AND reports a LOWER mean time to detect: the whole point of the lab')
proof = m.check_demonstration(good, bad)
ok(proof['extra_missed'] == bad['undetected'] - good['undetected'],
   'the extra missed count is reported, not inferred')
ok(40 < proof['mttd_drop_percent'] < 55,
   'the MTTD falls by about half, got %.1f' % proof['mttd_drop_percent'])
ok(good['honest_note'].endswith('NONE of the figures above.'),
   'every programme carries its undetected count in words')
ok(abs(bad['undetected_share'] - bad['undetected'] / 200.0) < 1e-12,
   'undetected share matches the count')

# ---- the positive control refuses to narrate a result it did not get --------
raises(lambda: m.check_demonstration(good, good),
       'identical programmes show no survivorship effect')
raises(lambda: m.check_demonstration(bad, good),
       'reversed arguments must not pass: the "worse" one misses fewer')
empty_side = dict(bad, detection=dict(n=0, note='none'))
raises(lambda: m.check_demonstration(good, empty_side),
       'a programme that detected nothing has no mean to compare')
flat = dict(bad, detection=dict(good['detection']))
raises(lambda: m.check_demonstration(good, flat),
       'equal means are not a demonstrated drop')

# ---- sweep ------------------------------------------------------------------
rows = m.sweep(p1)
ok([r['detected'] for r in rows] == sorted([r['detected'] for r in rows],
                                           reverse=True),
   'detected count falls monotonically as capability falls')
ok(rows[0]['undetected'] == 0, 'at rate 1.0 nothing is missed')
ok(rows[-1]['mean'] < rows[0]['mean'] / 10,
   'a programme blind to every quiet incident reports a spectacular MTTD')

# ---- coverage ---------------------------------------------------------------
raises(lambda: m.coverage(-1, 10, 10), 'negative count')
raises(lambda: m.coverage(True, 10, 10), 'a bool is not a count')
raises(lambda: m.coverage(1.5, 10, 10), 'a float is not a count')
raises(lambda: m.coverage(11, 10, 10), 'more monitored than registered')
raises(lambda: m.coverage(0, 0, 5), 'an empty register yields no rate')
c = m.coverage(940, 1000, 1180)
ok(abs(c['against_register'] - 0.94) < 1e-12, 'coverage against the register')
ok(abs(c['against_discovered'] - 940 / 1180.0) < 1e-12,
   'coverage against what a scan found')
ok(c['register_gap'] == 180, 'the gap is reported as a count, not a percentage')
ok('79.7' in c['note'], 'the honest denominator appears in the note')
c2 = m.coverage(900, 1000, 800)
ok(c2['register_gap'] == -200,
   'a register larger than the estate is reported as a negative gap, not hidden')
ok(abs(c2['against_discovered'] - 0.9) < 1e-12,
   'the denominator is the larger of the two, so coverage is never flattered')

# ---- the report itself ------------------------------------------------------
buf = io.StringIO()
m.report(buf)
text = buf.getvalue()
ok('%%' not in text, 'no literal double percent leaks into the printed report')
ok('MEAN TIME TO DETECT IS' in text, 'the headline claim is printed')
ok(text.count('\n') > 30, 'the report is not empty')
ok('finds 90% of the quiet ones' in text, 'labels render as single percents')

print('metric_honesty: %d checks passed' % PASS[0])
sys.exit(0)
