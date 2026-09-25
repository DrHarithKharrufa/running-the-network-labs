#!/usr/bin/env python3
"""Tests for microseg_policy.py.

The property that matters most: AUTHORISED INTENT IS NEVER SILENTLY DROPPED.
The shipped lab generated the intersection of intent and observation, so an
authorised relationship that was quiet during the window produced no rule and no
mention. Most of what follows exists to make that impossible.

    python3 test_microseg_policy.py
"""
import io
import sys

import microseg_policy as mp

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
    except mp.PolicyError as exc:
        if fragment and fragment not in str(exc):
            FAILED.append('%s (message lacked %r: %s)' % (label, fragment, exc))
        return
    except Exception as exc:                                    # noqa: BLE001
        FAILED.append('%s (raised %s, not PolicyError)' % (label, type(exc).__name__))
        return
    FAILED.append('%s (did not raise)' % label)


WIN = {'start': '2026-09-01', 'end': '2026-09-15'}


# -- 1. Authorised intent is never silently dropped ------------------------

LAB = {'a-01': 'a', 'b-01': 'b', 'rare-01': 'rare'}
INT = {('a', 'b', 80): 'the everyday path',
       ('rare', 'b', 80): 'the quarterly job'}
SEEN = [('a-01', 'b-01', 80)]

res = mp.analyse(LAB, INT, SEEN, WIN)
ok(len(res['candidates']) == 1, 'the observed intent becomes a candidate')
ok(len(res['unobserved_intent']) == 1,
   'THE UNOBSERVED INTENT IS REPORTED, not dropped')
ok(res['unobserved_intent'][0]['rule'] == ('rare', 'b', 80),
   'and it is the right one')
ok('KEEP IT' in res['unobserved_intent'][0]['why'],
   'and the advice is to keep it, not to retire it')
ok(res['unobserved_intent'][0]['reason'] == 'the quarterly job',
   'its stated business reason travels with it')

# Every intent key must appear in exactly one of the two buckets, always.
allkeys = ({c['rule'] for c in res['candidates']}
           | {u['rule'] for u in res['unobserved_intent']})
ok(allkeys == set(INT), 'every authorised relationship is accounted for exactly once')

# The same holds for the shipped inputs, and for an empty observation.
full = mp.analyse()
covered = ({c['rule'] for c in full['candidates']}
           | {u['rule'] for u in full['unobserved_intent']})
ok(covered == set(mp.INTENT), 'no authorised relationship is lost on the real inputs')
none_seen = mp.analyse(mp.LABEL, mp.INTENT, [], WIN)
ok(len(none_seen['unobserved_intent']) == len(mp.INTENT),
   'with NOTHING observed, every intent is reported as unobserved')
ok(not none_seen['candidates'],
   'and nothing becomes a candidate on the strength of no evidence')

# The window demonstration must actually demonstrate the failure.
rows = {r['days']: r for r in mp.demo_window()}
ok(rows[7]['monthly_job_seen'] is False,
   'a seven-day window does not see the month-end job')
ok(rows[30]['monthly_job_seen'] is True, 'a thirty-day window does')
ok(rows[7]['unobserved'] > rows[30]['unobserved'],
   'and the shorter window leaves more intent unobserved')
ok(rows[7]['candidates'] < rows[30]['candidates'],
   'so the shorter window yields FEWER candidate rules --- which is the trap: '
   'a smaller policy looks tidier and is an outage')


# -- 2. Observation is never authority -------------------------------------

res = mp.analyse(LAB, {('a', 'b', 80): 'ok'},
                 [('a-01', 'b-01', 80), ('rare-01', 'b-01', 80)], WIN)
ok(len(res['unsanctioned_flows']) == 1, 'an unintended flow is surfaced')
ok(res['unsanctioned_flows'][0]['verdict'] == mp.UNSANCTIONED, 'with its own verdict')
ok('not a reason to write a rule' in res['unsanctioned_flows'][0]['why'],
   'and it is explicitly NOT turned into a rule')
ok(not any(c['rule'] == ('rare', 'b', 80) for c in res['candidates']),
   'the unsanctioned pair does not appear among the candidates')
# No amount of observation promotes a flow into intent.
heavy = [('rare-01', 'b-01', 80)] * 500
res = mp.analyse(LAB, {('a', 'b', 80): 'ok'}, heavy, WIN)
ok(not res['candidates'],
   'five hundred observations of an unauthorised flow still generate no rule')
ok(len(res['unsanctioned_flows']) == 500, 'they are all reported as questions')

# Intent alone is enough; it never needs corroboration to survive.
res = mp.analyse(LAB, INT, [], WIN)
ok(len(res['unobserved_intent']) == 2, 'intent survives with zero observations')


# -- 3. Unlabelled endpoints ------------------------------------------------

res = mp.analyse(LAB, INT, [('ghost-9', 'b-01', 80)], WIN)
ok(len(res['unlabelled_endpoints']) == 1, 'an unlabelled source is reported')
ok('ghost-9' in res['unlabelled_endpoints'][0]['unlabelled'], 'and named')
ok(not res['unsanctioned_flows'],
   'an unlabelled flow is NOT also counted as unsanctioned --- it is a different '
   'problem with a different fix')
ok('nobody owns' in res['unlabelled_endpoints'][0]['why'],
   'and the report connects an unlabelled asset to an unowned one')
res = mp.analyse(LAB, INT, [('a-01', 'ghost-9', 80)], WIN)
ok(res['unlabelled_endpoints'][0]['unlabelled'] == ['ghost-9'],
   'an unlabelled destination is caught too')
res = mp.analyse(LAB, INT, [('g1', 'g2', 80)], WIN)
ok(res['unlabelled_endpoints'][0]['unlabelled'] == ['g1', 'g2'],
   'both ends are named when both are unlabelled')


# -- 4. Input validation ----------------------------------------------------

raises(lambda: mp.analyse({}, INT, SEEN, WIN), 'an empty label map is refused',
       'unlabelled estate')
raises(lambda: mp.analyse(LAB, {}, SEEN, WIN), 'empty intent is refused',
       'authority')
raises(lambda: mp.analyse(LAB, {('a', 'b', 80): ''}, SEEN, WIN),
       'intent with no stated reason is refused', 'no stated reason')
raises(lambda: mp.analyse(LAB, {('a', 'b'): 'x'}, SEEN, WIN),
       'a malformed intent key is refused')
raises(lambda: mp.analyse(LAB, {('a', 'b', '80'): 'x'}, SEEN, WIN),
       'a non-integer port in intent is refused', 'non-integer port')
raises(lambda: mp.analyse({'a-01': ''}, INT, SEEN, WIN),
       'an empty label is refused', 'non-empty name')
raises(lambda: mp.analyse(LAB, INT, [('a-01', 'b-01')], WIN),
       'a malformed observed flow is refused')
raises(lambda: mp.analyse(LAB, INT, SEEN, {'start': 'x', 'end': 'y'}),
       'a non-ISO window is refused', 'ISO start and end')
raises(lambda: mp.analyse(LAB, INT, SEEN,
                          {'start': '2026-09-15', 'end': '2026-09-01'}),
       'a backwards window is refused', 'ends before it starts')
raises(lambda: mp.analyse(LAB, INT, SEEN, {}), 'a missing window is refused')

ok(mp._days({'start': '2026-09-01', 'end': '2026-09-01'}) == 1,
   'a single-day window counts as one day')
ok(mp._days(WIN) == 15, 'the shipped window is fifteen days')


# -- 5. The output refuses to call itself policy ---------------------------

buf = io.StringIO()
mp.report(mp.analyse(), buf)
out = buf.getvalue()
ok('Nothing above is policy' in out, 'the report denies being policy')
ok('CANDIDATE' in out, 'it uses the candidate vocabulary')
ok('DO NOT DROP THESE' in out, 'unobserved intent is prominent, not a footnote')
ok('Approval is a human act' in out, 'approval is attributed to a person')
ok('tested separately' in out, 'and enforcement testing is pushed elsewhere')
for banned in ('approved policy', 'ready to deploy', 'safe to push'):
    ok(banned not in out.lower(), 'the report never says %r' % banned)
ok(str(mp.analyse()['window_days']) in out, 'the window length is in the report')

ok(mp.main([]) == 0, 'the module runs')
ok(mp.main(['--json']) == 0, 'the JSON form runs')
ok(mp.main(['--demo-window']) == 0, 'the window demonstration runs')
ok(mp.analyse() == mp.analyse(), 'the analysis is deterministic')

print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
