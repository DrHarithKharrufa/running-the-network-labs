#!/usr/bin/env python3
"""Checks for dbwalk.py --- that the model is right and claims no more than it can.

These checks exist because the previous version of dbwalk.py was confidently
wrong in a way no test would have caught, since it had none. The point here is
not that the code runs: it is that the model says the true thing about a learned
BGP route, and that nothing in it claims a device was contacted.

This executes no network device, no SONiC image, no Containerlab topology and no
ASIC.

    python3 test_dbwalk.py
"""
import io
import contextlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dbwalk as dw  # noqa: E402

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


learned = dw.checklist(static=False)
static = dw.checklist(static=True)
lstages = [s['stage'] for s in learned['stages']]
sstages = [s['stage'] for s in static['stages']]

# ---- the central correction -----------------------------------------------
check('a learned route chain does NOT begin at CONFIG_DB',
      'CONFIG_DB' not in lstages, lstages[:2])
check('a learned route chain begins in the BGP RIB',
      lstages[0].startswith('bgpd'), lstages[0])
check('a static route chain DOES begin at CONFIG_DB',
      sstages[0] == 'CONFIG_DB', sstages[0])
check('the static chain is the learned chain with CONFIG_DB in front',
      sstages[1:] == lstages, sstages[1:4])

# ---- STATE_DB is not the hardware receipt ---------------------------------
check('STATE_DB is not a stage of the route chain', 'STATE_DB' not in lstages)
check('STATE_DB is listed as present-but-not-a-stage',
      'STATE_DB' in learned['not_in_the_chain'])
check('the STATE_DB entry says it is not a per-route receipt',
      'not a per-route acknowledgement'
      in learned['not_in_the_chain']['STATE_DB'].lower()
      or 'NOT a per-route acknowledgement' in learned['not_in_the_chain']['STATE_DB'],
      learned['not_in_the_chain']['STATE_DB'][:60])

# ---- the stages are ordered control-plane to data-plane -------------------
order = ['bgpd RIB', 'bgpd best path', 'zebra RIB and next-hop resolution',
         'APPL_DB ROUTE_TABLE', 'ASIC_DB route entry',
         'syncd and SAI programming status', 'forwarding']
check('the stages are in control-to-forwarding order', lstages == order, lstages)
check('forwarding is the last stage and needs traffic',
      learned['stages'][-1]['stage'] == 'forwarding'
      and 'traffic' in learned['stages'][-1]['evidence'])

# ---- every stage states what it does NOT establish ------------------------
check('every stage declares what it does not establish',
      all(s.get('does_not_establish') for s in learned['stages']))
zebra = next(s for s in learned['stages'] if s['stage'].startswith('zebra'))
check('the zebra stage warns it is not hardware proof',
      'ASIC' in zebra['does_not_establish'],
      zebra['does_not_establish'][:50])
asic = next(s for s in learned['stages'] if s['stage'].startswith('ASIC_DB'))
check('ASIC_DB is described as the request, not the receipt',
      'REQUEST' in asic['does_not_establish'] or 'request' in asic['does_not_establish'],
      asic['does_not_establish'][:60])

# ---- it must not hard-code Redis database numbers -------------------------
joined = ' '.join(s['evidence'] for s in learned['stages'])
check('Redis database numbers are placeholders, not hard-coded',
      '-n <' in joined and '-n 4' not in joined and '-n 0' not in joined
      and '-n 1' not in joined, joined[:120])
check('the scope says the numbers come from database_config.json',
      'database_config.json' in learned['scope'])

# ---- honesty about what was and was not run -------------------------------
check('the docstring says nothing was run on SONiC',
      'has been run on SONiC' in dw.__doc__ or 'no Docker daemon' in dw.__doc__)
check('a caveat warns against virtual-switch capacity claims',
      any('virtual switch' in c and 'capacity' in c for c in learned['caveats']),
      [c[:40] for c in learned['caveats']])
check('a caveat warns that names vary by release',
      any('vary by SONiC release' in c for c in learned['caveats']))
check('a caveat states a learned route is not expected in CONFIG_DB',
      any('NOT expected in CONFIG_DB' in c for c in learned['caveats']))

# ---- the report and CLI ----------------------------------------------------
_r, out = quiet(dw.report, False)
check('the report prints for a learned route', 'LEARNED BGP route' in out)
check('the report prints the does-NOT line for every stage',
      out.count('does NOT :') == len(lstages), out.count('does NOT :'))
_r, out_s = quiet(dw.report, True)
check('the report prints for a static route', 'STATIC route' in out_s)
rc, _o = quiet(dw.main, [])
check('the CLI exits 0', rc == 0, rc)
rc, _o = quiet(dw.main, ['--static', '--json'])
check('the CLI accepts --static --json', rc == 0, rc)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
