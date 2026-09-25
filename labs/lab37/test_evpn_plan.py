#!/usr/bin/env python3
"""Checks for evpn_plan.py --- the plan reader, not the network.

The point is that the analysis reports what the plan SAYS, including when the
plan is wrong, and that its answers are not predetermined by how the inputs were
constructed. A planner whose imports are derived from its exports can only ever
agree with itself; these checks feed it mismatched imports and exports on purpose.

This executes no network device, no Containerlab topology and no ASIC, and it
predicts no forwarding behaviour.

    python3 test_evpn_plan.py
"""
import copy
import io
import contextlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import evpn_plan as ep  # noqa: E402

FAILS = []
COUNT = 0


def check(name, cond, detail=''):
    global COUNT
    COUNT += 1
    if not cond:
        FAILS.append('%s%s' % (name, (' [%s]' % detail) if detail else ''))
        print('FAIL  ' + name + ((' [%s]' % detail) if detail else ''))
    else:
        print('ok    ' + name)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


def plan(**edits):
    p = copy.deepcopy(ep.PLAN)
    for name, changes in edits.items():
        p['services'][name].update(changes)
    return p


def sev(findings, s):
    return [f for f in findings if f['severity'] == s]


# ---- the shipped plan ------------------------------------------------------
r = ep.analyse(ep.PLAN)
check('the shipped plan validates', bool(r['services']))
check('the shipped plan has no errors', not sev(r['findings'], 'error'),
      sev(r['findings'], 'error'))
check('red-vrf learns from shared-vrf', '64500:50099'
      in r['learns'].get('red-vrf', {}).get('shared-vrf', []))
check('shared-vrf does NOT learn from red-vrf --- the leak is one way',
      'red-vrf' not in r['learns'].get('shared-vrf', {}),
      r['learns'].get('shared-vrf'))
check('the one-way cross-tenant relationship is reported',
      any('one way only' in f['issue'] for f in r['findings']))
check('red-web and blue-web learn nothing from each other',
      'blue-web' not in r['learns'].get('red-web', {})
      and 'red-web' not in r['learns'].get('blue-web', {}))
check('a multi-leaf service is not flagged for exporting its own target',
      not any(f['service'] == 'red-web' for f in r['findings']),
      [f for f in r['findings'] if f['service'] == 'red-web'])

# ---- imports and exports really are independent inputs ---------------------
# If the analysis derived one from the other, changing only the import side
# could not change the answer. It must.
p = plan(**{'blue-vrf': {'import': ['64500:50020', '64500:50099', '64500:50010']}})
r2 = ep.analyse(p)
check('adding one import makes blue-vrf learn from red-vrf',
      '64500:50010' in r2['learns'].get('blue-vrf', {}).get('red-vrf', []),
      r2['learns'].get('blue-vrf'))
check('...and that new relationship is reported as one way',
      any('blue-vrf' in f['service'] and 'red-vrf' in f['service']
          for f in r2['findings']),
      [f['service'] for f in r2['findings']])
check('red-vrf still does not learn from blue-vrf',
      'blue-vrf' not in r2['learns'].get('red-vrf', {}))

# ---- a mutual cross-tenant path is escalated, not merely noted -------------
p = plan(**{'blue-vrf': {'import': ['64500:50020', '64500:50099', '64500:50010']},
            'red-vrf': {'import': ['64500:50010', '64500:50099', '64500:50020']}})
r3 = ep.analyse(p)
check('a mutual cross-tenant path is raised for review',
      any(f['severity'] == 'review' and 'BOTH directions' in f['issue']
          for f in r3['findings']),
      [f['issue'][:40] for f in r3['findings'] if f['severity'] == 'review'])

# ---- a mistyped target is an error, not a silent no-op ---------------------
p = plan(**{'red-vrf': {'import': ['64500:50010', '64500:50999']}})
r4 = ep.analyse(p)
check('an import that nothing exports is an error',
      any('64500:50999' in f['issue'] for f in sev(r4['findings'], 'error')),
      sev(r4['findings'], 'error'))
check('the mistyped import removes the shared-services relationship',
      'shared-vrf' not in r4['learns'].get('red-vrf', {}))

p = plan(**{'shared-vrf': {'export': ['64500:50099'], 'import': []}})
r5 = ep.analyse(p)
check('a service that imports nothing learns nothing',
      not r5['learns'].get('shared-vrf'))

p = plan(**{'red-db': {'export': ['64500:19999'], 'import': ['64500:10011']}})
r6 = ep.analyse(p)
check('exporting a target nothing imports --- not even itself --- is a warning',
      any('64500:19999' in f['issue'] for f in sev(r6['findings'], 'warning')),
      sev(r6['findings'], 'warning'))
check('...and importing a target nothing exports is still an error',
      any('64500:10011' in f['issue'] for f in sev(r6['findings'], 'error')),
      sev(r6['findings'], 'error'))

# ---- validation -----------------------------------------------------------
for name, edit, word in (
        ('red-web', {'vni': 0}, 'VNI'),
        ('red-web', {'vni': 1 << 24}, 'VNI'),
        ('red-web', {'leaves': []}, 'no leaves'),
        ('red-web', {'kind': 'magic'}, 'kind'),
        ('red-web', {'export': ['not-a-target']}, 'malformed')):
    try:
        ep.analyse(plan(**{name: edit}))
        check('rejects %r for %s' % (edit, name), False, 'no exception')
    except ep.PlanError as e:
        check('rejects %r for %s' % (edit, name), word in str(e), str(e)[:70])

try:
    ep.analyse(plan(**{'red-db': {'vni': 10010}}))
    check('a reused VNI is rejected', False, 'no exception')
except ep.PlanError as e:
    check('a reused VNI is rejected', 'reused' in str(e), str(e)[:70])

try:
    ep.analyse({'services': {}})
    check('an empty plan is rejected', False, 'no exception')
except ep.PlanError as e:
    check('an empty plan is rejected', 'no services' in str(e))

try:
    ep.analyse(plan(**{'red-web': {'import': ['64500:10010'], 'export': None}}))
    check('a missing export list is rejected', False, 'no exception')
except (ep.PlanError, TypeError) as e:
    check('a missing export list is rejected', True, type(e).__name__)

# ---- the report runs and the exit code follows the findings ---------------
_r, out = quiet(ep.report, ep.PLAN)
low = out.lower()
check('the report names what it is not',
      'not reachability' in low and 'not security policy' in low,
      [l for l in out.splitlines() if 'not reachability' in l.lower()][:1])
check('the report prints the directional relationships', 'one way' in out)
rc, _o = quiet(ep.main, [])
check('a clean plan exits 0', rc == 0, rc)

saved = ep.PLAN
try:
    ep.PLAN = plan(**{'red-vrf': {'import': ['64500:50010', '64500:50999']}})
    rc_bad, _o = quiet(ep.main, [])
    check('a plan with an error exits non-zero', rc_bad == 1, rc_bad)
finally:
    ep.PLAN = saved

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
