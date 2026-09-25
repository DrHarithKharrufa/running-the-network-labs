#!/usr/bin/env python3
"""Tests for lab 61.1.  Run: python3 test_incident_record.py"""
import io
import sys

import incident_record as ir

PASS = [0]


def ok(cond, what):
    if not cond:
        raise AssertionError(what)
    PASS[0] += 1


def raises(fn, what):
    try:
        fn()
    except ir.RecordError:
        PASS[0] += 1
        return
    raise AssertionError('expected RecordError: %s' % what)


# ---- the classifier the chapter used to recommend, and what it does ---------
ok(ir.impact_only(dict(subscribers_confirmed=6000)) == 'SEV1', '6,000 is Sev 1')
ok(ir.impact_only(dict(subscribers_confirmed=600)) == 'SEV2', '600 is Sev 2')
ok(ir.impact_only(dict(subscribers_confirmed=60)) == 'SEV3', '60 is Sev 3')
ok(ir.impact_only(dict(subscribers_confirmed=6)) == 'SEV4', '6 is Sev 4')
ok(ir.impact_only(dict(service_down_confirmed=True)) == 'SEV1',
   'a confirmed service outage is Sev 1 regardless of count')
ok(ir.impact_only(dict(subscribers_confirmed=None)) == 'SEV4',
   'THE DEFECT: an unmeasured outage reads as the least severe thing there is')
ok(ir.impact_only({}) == 'SEV4', 'and so does an empty observation')

# ---- severity as the worst of several triggers ------------------------------
ok(ir.classify(dict(subscribers_confirmed=0, safety_risk=True))['severity']
   == 'SEV1', 'safety alone is Sev 1 with no customers affected at all')
ok(ir.classify(dict(subscribers_confirmed=0,
                    security_incident=True))['severity'] == 'SEV1',
   'an active security incident is Sev 1 with nothing down')
ok(ir.classify(dict(subscribers_confirmed=0,
                    imminent_impact=True))['severity'] == 'SEV2',
   'impact that has not arrived yet still classifies')
ok(ir.classify(dict(subscribers_confirmed=0,
                    redundancy_lost=True))['severity'] == 'SEV2',
   'running unprotected classifies without any customer impact')
ok(ir.classify(dict(plausible_upper_bound=18000))['severity'] == 'SEV1',
   'unmeasured scope with a large upper bound is Sev 1, not Sev 4')
ok(ir.classify(dict(plausible_upper_bound=900))['severity'] == 'SEV2',
   'a smaller upper bound is Sev 2')
ok(ir.classify(dict(plausible_upper_bound=40))['severity'] == 'SEV4',
   'and a small one does not inflate the severity, so the trigger is not a '
   'blanket escalation')
worst = ir.classify(dict(subscribers_confirmed=60, safety_risk=True))
ok(worst['severity'] == 'SEV1',
   'the classification is the WORST trigger, not the first or the last')
ok(len(worst['triggers']) == 2, 'and every trigger that fired is listed')

# ---- provisional is a real state, reachable and avoidable ------------------
p = ir.classify(dict(plausible_upper_bound=18000))
ok(p['provisional'] is True, 'an unmeasured incident is provisional')
ok('subscribers_confirmed' in p['unknown'], 'and says what is unknown')
ok('must be reviewed' in p['note'], 'and that it must be reviewed')
ok(ir.classify(dict(subscribers_confirmed=10))['provisional'] is False,
   'a measured incident is not provisional, so the flag carries information')
ok(ir.classify({})['provisional'] is True,
   'an empty observation is provisional, not Sev 4 with confidence')
raises(lambda: ir.classify('not an observation'), 'a string is not an observation')
raises(lambda: ir.classify(dict(subscribers_confirmed=-5)), 'a negative count')
raises(lambda: ir.classify(dict(subscribers_confirmed=True)), 'a bool count')

# ---- reclassification carries a history ------------------------------------
obs = dict(plausible_upper_bound=18000)
rec = dict(id='X', observation=obs, assessment=ir.classify(obs))
down = ir.reclassify(rec, dict(subscribers_confirmed=310), 'duty manager',
                     '04:55', 'field team confirmed the affected node')
ok(down['assessment']['severity'] == 'SEV3', 'the scope came back smaller')
ok(down['assessment']['provisional'] is False, 'and the flag cleared')
h = down['history'][-1]
ok(h['was'] == 'SEV1' and h['now'] == 'SEV3', 'the history records both values')
ok(h['was_provisional'] is True and h['now_provisional'] is False,
   'and that the first call was made without the facts')
ok(h['by'] == 'duty manager' and h['why'], 'and who changed it and why')
ok(rec['assessment']['severity'] == 'SEV1',
   'the original record is not mutated in place')
up = ir.reclassify(rec, dict(subscribers_confirmed=11400), 'duty manager',
                   '04:55', 'more exchanges than feared')
ok(up['assessment']['severity'] == 'SEV1', 'reclassification works upward too')
again = ir.reclassify(down, dict(subscribers_confirmed=9000), 'incident lead',
                      '06:10', 'a second span was found to be cut')
ok(len(again['history']) == 2, 'history accumulates rather than replacing')
raises(lambda: ir.reclassify(rec, dict(subscribers_confirmed=1), '', '04:55',
                             'why'), 'an unattributed reclassification')
raises(lambda: ir.reclassify(rec, dict(subscribers_confirmed=1), 'who', '',
                             'why'), 'a reclassification with no time')
raises(lambda: ir.reclassify(rec, dict(subscribers_confirmed=1), 'who', '04:55',
                             '   '), 'a reclassification with no reason')

# ---- every trigger can fire, and the gap is measured not assumed -----------
t = ir.prove_every_trigger_can_fire()
ok(t['all_reachable'] is True, 'every trigger is reachable')
ok(t['triggers'] == len(ir.TRIGGERS) == 6, 'six triggers, all live')
ok(t['provisional_reachable'] and t['provisional_avoidable'],
   'the provisional flag is both reachable and avoidable')
g = ir.prove_the_gap_is_real()
ok(g['cases'] == 6, 'six worked calls')
ok(g['under_rated_by_impact_only'] == 4,
   'the impact-only classifier under-rates four of the six, got %d'
   % g['under_rated_by_impact_only'])
ok(g['disagreements'] >= g['under_rated_by_impact_only'],
   'under-rating is a subset of disagreement')

# ---- the cause field --------------------------------------------------------
inc = ir.worked_incidents()
ok(len(inc) == 24, 'twenty-four worked incidents')
ok(all(i['true_cause'] in ir.CAUSES for i in inc), 'all causes in the vocabulary')
ok(all(i.get('guess_at_closure') for i in inc),
   'every incident states what the closing engineer would have picked')
ok(ir.close_honest(inc[2]) == 'not established',
   'the honest process records that it does not know')
ok(ir.close_forced(inc[2]) != 'not established',
   'the forced process never records that it does not know')
ok(ir.close_forced(inc[0]) == inc[0]['true_cause'],
   'when the cause IS known, both processes record it')
raises(lambda: ir.close_forced(dict(cause_established=False)),
       'an incident with no stated guess cannot be modelled')

c = ir.cause_comparison()
ok(c['n'] == 24, 'all incidents counted')
ok(c['known_at_closure'] + c['resolved_by_review'] + c['still_unknown']
   == c['n'], 'every incident is in exactly one of the three states')
ok(c['revised_correct'] > c['forced_correct'],
   'the honest process gets more labels right: %d vs %d'
   % (c['revised_correct'], c['forced_correct']))
ok(c['forced_top'][0] != c['true_top'][0],
   'THE RESULT: the forced process names the wrong top cause')
ok(c['revised_top'][0] == c['true_top'][0],
   'and the honest one, after review, names the right one')
ok('not established' not in c['forced'],
   'the forced dataset contains no trace of what nobody knew')
ok(c['honest']['not established'] > c['revised'].get('not established', 0),
   'review reduces the unknown bar without eliminating it')
missing = [k for k in c['truth'] if c['truth'][k] and not c['forced'].get(k)]
ok('software defect' in missing,
   'the true top cause is entirely absent from the forced table')
ok(sum(c['forced'].values()) == 24 and sum(c['revised'].values()) == 24,
   'both processes label every incident exactly once')

# ---- what the dashboard does to an honest dataset ---------------------------
labels = ['configuration change'] * 3 + ['not established'] * 9
name, count, share = ir.top_cause(labels, ignore_unknown=True)
ok(name == 'configuration change' and abs(share - 1.0) < 1e-12,
   'dropping the unknown bar reports a 100 per cent share from 3 of 12')
name2, _, share2 = ir.top_cause(labels, ignore_unknown=False)
ok(name2 == 'not established' and abs(share2 - 0.75) < 1e-12,
   'keeping it reports the honest picture instead')
ok(ir.top_cause(['not established'], ignore_unknown=True) == (None, 0, 0),
   'a dataset of nothing but unknowns yields no top cause at all')
ok(ir.tally([]) == {}, 'an empty tally is empty, not an error')
ok(list(ir.tally(['b', 'a', 'a']))[0] == 'a', 'tallies sort by count')

# ---- the report -------------------------------------------------------------
buf = io.StringIO()
ir.report(buf, demo_fail_open=True)
text = buf.getvalue()
flat = ' '.join(text.split())
ok('%%' not in text, 'no literal double percent leaks')
ok('An unmeasured outage is not a small outage' in flat, 'the headline is stated')
ok('SEV1 -> SEV3' in flat, 'the downgrade is shown, not only an upgrade')
ok('will make everything a Sev 1' in flat,
   'the obvious objection is answered rather than avoided')
ok('It will not give you severity thresholds' in flat, 'the scope is stated')
buf2 = io.StringIO()
ir.report(buf2)
ok('WHAT THE DASHBOARD DOES' not in buf2.getvalue(),
   'the dashboard demonstration is opt-in')

print('incident_record: %d checks passed' % PASS[0])
sys.exit(0)
