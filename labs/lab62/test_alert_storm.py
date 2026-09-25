#!/usr/bin/env python3
"""Tests for lab 62.2.  Run: python3 test_alert_storm.py"""
import io
import sys

import alert_storm as ar

PASS = [0]


def ok(cond, what):
    if not cond:
        raise AssertionError(what)
    PASS[0] += 1


def raises(fn, what):
    try:
        fn()
    except ar.AlertError:
        PASS[0] += 1
        return
    raise AssertionError('expected AlertError: %s' % what)


TL = [(0, {}), (60, {}), (120, {}), (180, {})]

# ---- a rule is a thing that is evaluated -----------------------------------
raises(lambda: ar.Rule('x', lambda s: True, severity='shout'), 'bad severity')
raises(lambda: ar.Rule('x', lambda s: True, kind='vibe'), 'bad kind')
raises(lambda: ar.Rule('x', lambda s: True, for_seconds=-1), 'negative for')
raises(lambda: ar.Rule('x', 'not callable'), 'an expression must be callable')
ok(repr(ar.Rule('x', lambda s: True)) == 'Rule(x)', 'a rule names itself')

# ---- the evaluator ----------------------------------------------------------
raises(lambda: ar.evaluate([], TL), 'no rules')
raises(lambda: ar.evaluate([ar.Rule('x', lambda s: True)], []), 'no timeline')
raises(lambda: ar.evaluate([ar.Rule('x', lambda s: True)],
                           [(60, {}), (0, {})]), 'a timeline out of order')
raises(lambda: ar.evaluate([ar.Rule('x', lambda s: True)], [(0, 'nope')]),
       'a sample that is not a mapping')
raises(lambda: ar.evaluate([ar.Rule('x', lambda s: 'maybe')], TL),
       'an expression returning something other than True/False/None')

r = ar.evaluate([ar.Rule('always', lambda s: True)], TL)
ok(len(r['events']) == 1, 'a firing rule produces one event, not one per sample')
ok(r['events'][0]['at'] == 0, 'and fires at the first instant it is true')
ok(r['firing_at_end'] == ['always'], 'and is still firing at the end')
ok(ar.evaluate([ar.Rule('never', lambda s: False)], TL)['events'] == [],
   'a rule that is never true never fires')

# ---- the for-duration actually delays, and actually resets -----------------
slow = ar.evaluate([ar.Rule('slow', lambda s: True, for_seconds=120)], TL)
ok([e['at'] for e in slow['events']] == [120], 'the for-duration delays firing')
ok(slow['events'][0]['pending_since'] == 0, 'and records when it went pending')
flap = [(0, dict(x=1)), (60, dict(x=0)), (120, dict(x=1)), (180, dict(x=1))]
f = ar.evaluate([ar.Rule('f', lambda s: s['x'] == 1, for_seconds=120)], flap)
ok([e['at'] for e in f['events']] == [],
   'a condition that went false resets the clock, so a 120s rule does not fire '
   'from a 60s run')
longer = flap + [(240, dict(x=1))]
f2 = ar.evaluate([ar.Rule('f', lambda s: s['x'] == 1, for_seconds=120)], longer)
ok([e['at'] for e in f2['events']] == [240], 'and fires once it is sustained')
ok(ar.evaluate([ar.Rule('z', lambda s: True, for_seconds=0)], TL)
   ['events'][0]['at'] == 0, 'a zero for-duration fires immediately')

# ---- "cannot evaluate" is not "healthy" ------------------------------------
u = ar.evaluate([ar.Rule('u', lambda s: None)], TL)
ok(u['events'] == [], 'an unevaluable rule does not fire')
ok(len(u['unevaluable']) == 4, 'and every unevaluable instant is recorded')
ok(u['firing_at_end'] == [], 'and it is not left firing')

# ---- the defect this lab exists to show ------------------------------------
tl = ar.probe_timeline()
ok(len(tl) == 21, 'twenty-one samples, one a minute')
ok('probe_loss_ratio' not in tl[12][1], 'the prober dies at minute 12')
ok(tl[6][1]['probe_loss_ratio'] > 0.02, 'and there is a spike before that')
bare = ar.evaluate([ar.Rule('bare', ar.loss_gt(0.02), for_seconds=300)], tl)
ok(bare['events'] == [],
   'THE DEFECT: the chapter\'s rule never fires, neither for the spike (too '
   'short, correctly) NOR for the prober dying (silently, incorrectly)')
ok(bare['unevaluable'] == [],
   'and it cannot even report that it could not be evaluated, because a bare '
   'comparison returns False for a missing metric')
honest = ar.evaluate([ar.Rule('h', ar.loss_gt_honest(0.02), for_seconds=300)], tl)
ok(honest['events'] == [], 'the honest form also does not fire')
ok(len(honest['unevaluable']) == 9,
   'but it records nine instants it could not evaluate, got %d'
   % len(honest['unevaluable']))
comp = ar.evaluate([ar.Rule('absent', ar.absent_for('probe_loss_ratio'),
                            for_seconds=120)], tl)
ok([e['at'] for e in comp['events']] == [14 * 60],
   'the companion rule fires two minutes after the metric disappears')
ok(ar.evaluate([ar.Rule('absent', ar.absent_for('probe_loss_ratio'))],
               [(0, dict(probe_loss_ratio=0.5))])['events'] == [],
   'and does not fire while the metric is present, however bad it is')
short = [(t, dict(probe_loss_ratio=0.06)) for t in (0, 60, 120)]
ok(ar.evaluate([ar.Rule('b', ar.loss_gt(0.02), for_seconds=300)],
               short)['events'] == [],
   'a three-minute spike does not clear a five-minute for-duration')
sustained = [(t, dict(probe_loss_ratio=0.06)) for t in range(0, 601, 60)]
ok(len(ar.evaluate([ar.Rule('b', ar.loss_gt(0.02), for_seconds=300)],
                   sustained)['events']) == 1,
   'a sustained one does, exactly once')
ok('ABSENT' in ar.PROBE_DEFINITION and 'trailing 60 seconds' in
   ar.PROBE_DEFINITION,
   'the metric is defined, including its window and what absence means')

# ---- notification: grouping, inhibition, silences, routing -----------------
rules = ar.fault_rules()
res = ar.evaluate(rules, ar.fault_timeline())
ok(len(res['events']) == 9, 'nine rules fired, evaluated from metrics')
raw = ar.notify(res['events'], rules, group_window=None, inhibition=False)
tuned = ar.notify(res['events'], rules, group_window=300, inhibition=True)
ok(raw['pages'] == 5,
   'five page-severity rules fired; the other four are tickets, got %d'
   % raw['pages'])
ok(tuned['pages'] == 1, 'grouping and inhibition reduce that to one page')
ok(len(tuned['suppressed']) == 8, 'and say why for each of the other eight')
whys = {s['why'].split(' by ')[0].split(' as ')[0] for s in tuned['suppressed']}
ok('inhibited' in whys and 'routed' in whys,
   'suppression distinguishes inhibition from routing')
silenced = ar.notify(res['events'], rules, group_window=300, inhibition=True,
                     silences={'EdgePathLoss'})
ok(any(s['why'] == 'silenced' for s in silenced['suppressed']),
   'a silence suppresses by name')
ok(silenced['pages'] == 0,
   'A SILENCE ON THE SYMPTOM TAKES THE WHOLE GROUP OFF THE AIR, because a '
   'silenced alert is still firing and goes on inhibiting: %d pages'
   % silenced['pages'])
unsil = ar.notify(res['events'], rules, group_window=300, inhibition=True,
                  silences={'EdgePathLoss'}, silenced_still_inhibits=False)
ok(unsil['pages'] > silenced['pages'],
   'under the other semantics the causes come back, which is why the parameter '
   'exists and why you must know which one your stack implements')
raises(lambda: ar.notify([dict(rule='ghost', at=0, severity='page',
                               kind='cause', group='g')], rules),
       'an event for a rule that does not exist')
ok(ar.notify([], rules)['pages'] == 0, 'nothing fired, nothing paged')

# ---- pages that must happen before any customer symptom --------------------
rr, rt = ar.risk_rules(), ar.risk_timeline()
rres = ar.evaluate(rr, rt)
fired = {e['rule'] for e in rres['events']}
ok(fired == {'RedundancyLost', 'GeneratorFuelLow', 'ActiveCompromise',
             'TelemetryLost'},
   'four risk rules fire, got %s' % sorted(fired))
ok(not any(e['kind'] == 'symptom' for e in rres['events']),
   'THE POINT: not one customer symptom fired all night')
ok(all(e['severity'] == 'page' for e in rres['events']),
   'and every one of them is a page')
rn = ar.notify(rres['events'], rr, group_window=300, inhibition=True)
ok(rn['pages'] == 4, 'they are in four different groups, so four pages')
ok(len({e['group'] for e in rres['events']}) == 4,
   'resilience, facilities, security and monitoring are separate concerns')
quiet = ar.evaluate(rr, [(0, dict(transits_up=2,
                                  generator_minutes_remaining=100000,
                                  confirmed_intrusion=False,
                                  collector_series_ingested=450000,
                                  probe_loss_ratio=0.001))])
ok(quiet['events'] == [],
   'and on a genuinely quiet night none of them fires, so they are not simply '
   'always on')
ok(ar.evaluate([rr[3]], [(0, dict(collector_series_ingested=0))])['events'],
   'the monitoring-loss rule fires when ingestion stops')
ok(ar.evaluate([rr[3]], [(0, dict())])['events'] == [],
   'and not when the field is simply absent, which is a different fault')

# ---- the control ------------------------------------------------------------
p = ar.prove_the_evaluator_works()
ok(all(p.values()), 'every property of the evaluator is demonstrated')
ok(set(p) == {'fires', 'stays_quiet', 'for_duration_delays',
              'unevaluable_is_not_healthy', 'pending_resets'},
   'and the set of properties is enumerated')

# ---- the report -------------------------------------------------------------
buf = io.StringIO()
ar.report(buf, demo_original=True)
text = buf.getvalue()
flat = ' '.join(text.split())
ok('%%' not in text, 'no literal double percent leaks')
ok('is FALSE when probe_loss_ratio does not exist' in flat,
   'the fail-open mechanism is stated in words')
ok('would have delivered NOTHING' in flat,
   'the symptom-only policy is shown to deliver nothing on that night')
ok('it did not delete the cause rules' in flat,
   'the causes are kept for diagnosis')
ok('the demonstration established nothing' in flat,
   'the replaced fixture is criticised explicitly')
buf2 = io.StringIO()
ar.report(buf2)
ok('THE FIXTURE THIS LAB SHIPPED WITH' in text,
   'the repaired lab can still show what it originally did')
ok('THE FIXTURE THIS LAB SHIPPED WITH' not in buf2.getvalue(),
   'and that criticism is opt-in')

print('alert_storm: %d checks passed' % PASS[0])
sys.exit(0)
