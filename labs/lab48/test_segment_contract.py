#!/usr/bin/env python3
"""Checks for Lab 48.3.

The script this replaces printed FAIL for midhaul and then said the path carried
midhaul. So the first duty of these checks is that every verdict the report
prints is derived from the clause results, and that a clause the contract did
not state comes back unstated rather than passed.

    python3 test_segment_contract.py
"""
import sys

import segment_contract as S

PASS = 0
FAIL = []


def check(name, cond, detail=''):
    global PASS
    if cond:
        PASS += 1
    else:
        FAIL.append('%s%s' % (name, (' --- ' + detail) if detail else ''))


def raises(name, fn, want):
    try:
        fn()
    except S.ContractError as e:
        check(name, want.lower() in str(e).lower(),
              'raised %r, wanted something about %r' % (str(e), want))
    except Exception as e:                      # noqa: BLE001
        check(name, False, 'raised %s, not ContractError' % type(e).__name__)
    else:
        check(name, False, 'did not raise')


# ===========================================================================
# 1. An unstated clause is unstated, not passed
# ===========================================================================
bare = S.contract('bare', 'split 2 (higher layer)', 'user', 'a', 'b')
p = S.path('anything', delay_us=1e6, frame_loss_ratio=1.0, pdv_us=1e6,
           capacity_gbps=0.0, mtu_bytes=64)
r = S.check(bare, p)
check('a contract stating nothing fails nothing', r['failed'] == [])
check('but it is not complete either', not r['complete'])
check('every clause comes back unstated', len(r['unstated']) == len(r['clauses']))
check('and the verdict says so', 'unstated' in S.verdict(r))
check('a truly appalling path passes an empty contract, which is the point',
      r['meets'])

# stating one clause makes exactly that one checkable
one = S.contract('one', 'split 2 (higher layer)', 'user', 'a', 'b',
                 max_delay_us=100.0)
r1 = S.check(one, p)
check('stating a delay makes it fail', r1['failed'] == ['one-way delay'])
check('and leaves the rest unstated', len(r1['unstated']) == len(r1['clauses']) - 1)

# a requirement stated but not delivered is also unstated, not a pass
half = S.path('no loss figure', delay_us=50.0)
rh = S.check(S.contract('c', 'split 2 (higher layer)', 'user', 'a', 'b',
                        max_delay_us=100.0, frame_loss_ratio=1e-7), half)
check('a path that reports no figure cannot be scored on it',
      'frame loss ratio' in rh['unstated'])
check('and it is not counted as a failure', rh['failed'] == [])

# ===========================================================================
# 2. The old lab's contradiction cannot occur here
# ===========================================================================
for ctr in (S.FH, S.MH, S.BH):
    for pth in (S.SHARED, S.ENGINEERED):
        r = S.check(ctr, pth)
        v = S.verdict(r)
        check('%s on %s: verdict agrees with the clauses'
              % (ctr['name'][:20], pth['name'][:20]),
              (r['meets'] and not v.startswith('FAILS'))
              or (not r['meets'] and v.startswith('FAILS')))
        for n in r['failed']:
            check('%s: the failing clause %s is named in the verdict'
                  % (ctr['name'][:20], n), n in v)

# ===========================================================================
# 3. The shared path, and what actually fails
# ===========================================================================
fh = S.check(S.FH, S.SHARED)
check('the fronthaul contract fails on the shared path', not fh['meets'])
check('on delay', 'one-way delay' in fh['failed'])
check('on frame loss', 'frame loss ratio' in fh['failed'])
check('on capacity', 'capacity' in fh['failed'])
check('and NOT on packet delay variation, which it does not state',
      'packet delay variation' in fh['unstated'])
mh = S.check(S.MH, S.SHARED)
check('the midhaul contract is met on the shared path', mh['meets'],
      '%r' % mh['failed'])
check('so the old lab\'s midhaul failure was its invented sync rank',
      mh['failed'] == [])
bh = S.check(S.BH, S.SHARED)
check('the backhaul contract is met too', bh['meets'])

# ===========================================================================
# 4. An engineered shared path CAN meet a fronthaul contract
# ===========================================================================
e = S.check(S.FH, S.ENGINEERED)
check('fronthaul is met on a shared engineered path', e['meets'],
      '%r' % e['failed'])
check('which refutes "fronthaul cannot share"', e['meets'])
check('the delay clause passes',
      [c for c in e['clauses'] if c[0] == 'one-way delay'][0][1] is True)
check('the relative time error clause passes',
      [c for c in e['clauses'] if c[0] == 'relative time error'][0][1] is True)
mtu = [S.check(c, S.ENGINEERED) for c in (S.MH, S.BH)]
check('but the same path fails midhaul and backhaul on MTU',
      all('MTU' in r['failed'] for r in mtu))
check('and only on MTU', all(r['failed'] == ['MTU'] for r in mtu))
check('because a fronthaul-sized frame is smaller than a tunnelled one',
      S.ENGINEERED['mtu_bytes'] < S.MH['mtu_bytes'])

# ===========================================================================
# 5. The failure state is a separate check and can be missed
# ===========================================================================
w = S.check(S.MH, S.SHARED, 'working')
f = S.check(S.MH, S.SHARED, 'failure')
check('midhaul is met in the working state', w['meets'])
check('and missed on the protection path', not f['meets'])
check('on delay', f['failed'] == ['one-way delay'])
check('because the protection path is slower',
      S.SHARED['delay_us_on_failure'] > S.SHARED['delay_us'])
check('the working check cannot see it', w['meets'] and not f['meets'])
check('the state is recorded in the result', f['state'] == 'failure')

raises('a path with no failure figures cannot be checked in that state',
       lambda: S.check(S.FH, S.path('no figures', delay_us=10.0), 'failure'),
       'not a pass')
raises('an unknown state is refused',
       lambda: S.check(S.FH, S.SHARED, 'degraded'), "'working' or 'failure'")

# ===========================================================================
# 6. Malformed contracts are refused
# ===========================================================================
raises('an unknown split', lambda: S.contract('x', 'split 9', 'user', 'a', 'b'),
       'unknown split')
raises('an unknown plane',
       lambda: S.contract('x', 'integrated', 'data', 'a', 'b'), 'unknown plane')
raises('an unknown delay class',
       lambda: S.contract('x', 'integrated', 'user', 'a', 'b',
                          delay_class='High50'), 'unknown delay class')
raises('a delay stated twice',
       lambda: S.contract('x', 'integrated', 'user', 'a', 'b',
                          delay_class='High100', max_delay_us=100.0),
       'class OR a figure')
raises('absolute and relative time error both stated',
       lambda: S.contract('x', 'integrated', 'user', 'a', 'b',
                          absolute_te_ns=1000, relative_te_ns=100),
       'different requirements')
raises('a negative delay on a path',
       lambda: S.path('x', delay_us=-1), 'not negative')

# a delay class sets the figure, so they cannot diverge
c = S.contract('c', 'split 7.2x (lower layer)', 'user', 'a', 'b',
               delay_class='High25')
check('a class sets the delay figure', c['max_delay_us'] == 25.0)
check('and both are recorded', c['delay_class'] == 'High25')

# ===========================================================================
# 7. Synchronisation is a quantity, not a rank
# ===========================================================================
check('there is no sync rank anywhere in the module',
      not any('rank' in n.lower() for n in dir(S)),
      'the old lab ordered frequency < phase < phase-tight, which is not how '
      'these relate')
check('time error is stated in nanoseconds',
      'relative_te_ns' in S.FH and 'absolute_te_ns' in S.FH)
check('absolute and relative are separate clauses',
      len([c for c in S.check(S.FH, S.ENGINEERED)['clauses']
           if 'time error' in c[0]]) == 2)
check('the fronthaul contract states a relative figure',
      S.FH['relative_te_ns'] is not None and S.FH['absolute_te_ns'] is None)
check('the midhaul contract states neither, which is allowed',
      S.MH['relative_te_ns'] is None and S.MH['absolute_te_ns'] is None)

# ===========================================================================
# 8. The report is consistent with the model
# ===========================================================================
import io                                                     # noqa: E402
import contextlib                                             # noqa: E402

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    S.main([])
out = buf.getvalue()
check('the report runs', 'A. What a contract has to say' in out)
check('it shows the unstated PDV clause', 'NOT STATED' in out)
check('it says a word like phase-tight is not a requirement',
      'is not a requirement and cannot be checked' in out)
check('it reports the MTU failure it found', 'MTU' in out)
check('it does not claim the design works',
      'a design that works' in out and 'a design that might' in out)
check('it names the old contradiction',
      'typed underneath it' in S.__doc__)
check('it discloses what it does not establish', 'does NOT establish' in out)
check('no verdict in the report contradicts its own clause list',
      out.count('FAILS:') == sum(1 for c in (S.FH, S.MH, S.BH)
                                 for p in (S.SHARED, S.ENGINEERED)
                                 if S.check(c, p)['failed'])
      + sum(1 for c, p in ((S.FH, S.ENGINEERED), (S.MH, S.SHARED), (S.BH, S.SHARED))
            if S.check(c, p, 'failure')['failed']))
check('no report line is absurdly wide',
      max(len(l) for l in out.splitlines()) <= 82,
      'widest %d' % max(len(l) for l in out.splitlines()))

# ===========================================================================
if __name__ == '__main__':
    total = PASS + len(FAIL)
    for f in FAIL:
        print('FAIL: %s' % f)
    print('%d/%d checks passed' % (PASS, total))
    sys.exit(1 if FAIL else 0)
