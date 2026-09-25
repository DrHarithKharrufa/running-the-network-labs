#!/usr/bin/env python3
"""Checks for link_budget.py --- every condition, not one of them.

The previous version printed "receiver clipped!" and "OK" in the same run,
because its verdict was computed from the sensitivity margin alone. The central
check here is that a link failing ANY condition is reported as failing, and in
particular that a receiver driven past overload cannot be reported as good.

No transponder, fibre or power meter.

    python3 test_link_budget.py
"""
import contextlib, io, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import link_budget as lb  # noqa: E402

FAILS, COUNT = [], 0


def check(name, cond, detail=''):
    global COUNT
    COUNT += 1
    detail = str(detail) if detail not in ('', None) else ''
    suffix = ('  [' + detail + ']') if detail else ''
    (print('ok    ' + name + suffix) if cond
     else (FAILS.append(name + suffix), print('FAIL  ' + name + suffix)))


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


# ---- THE BUG THAT MADE THIS REWRITE NECESSARY -----------------------------
hot = lb.evaluate(9.0, 11.0, 12.6, 20.5, -22.0, -8.0)
check('a receiver driven past overload has a comfortable sensitivity margin',
      hot['worst_case_margin_db'] > 5, hot['worst_case_margin_db'])
check('...and is nonetheless reported as FAILING',
      not hot['power_conditions_met'], hot['failed'])
check('...naming the overload condition specifically',
      'best case stays under overload' in hot['failed'], hot['failed'])
check('the verdict text says it fails', 'FAILS' in lb.verdict_text(hot))
check('the short verdict says it too', 'FAILS' in lb.verdict_short(hot))
# the phrase appears, but only inside its own denial: a passing link is
# reported as meeting the POWER conditions, explicitly not as working
passing = lb.verdict_text(lb.evaluate(0.0, 2.0, 12.6, 20.5, -22.0, -8.0))
check('a passing verdict claims only that the power conditions are met',
      passing.startswith('power conditions met'), passing[:40])
check('...and denies that this means the link works',
      'NOT the same as "the link works"' in passing, passing[-45:])

# ---- each condition can fail on its own -----------------------------------
weak = lb.evaluate(0.0, 2.0, 25.0, 33.0, -22.0, -8.0)
check('too weak at the worst case fails', not weak['power_conditions_met'])
check('...on the sensitivity condition, not the overload one',
      weak['failed'] == ['worst case clears sensitivity'], weak['failed'])
loud = lb.evaluate(0.0, 2.0, 1.0, 3.0, -22.0, -8.0)
check('too strong at the best case fails', not loud['power_conditions_met'])
check('...even though it has a huge sensitivity margin',
      loud['worst_case_margin_db'] > 15, loud['worst_case_margin_db'])
wide = lb.evaluate(0.0, 2.0, 2.0, 20.0, -22.0, -8.0)
check('a path varying more than the window fails',
      'the window is wider than the spread' in wide['failed'], wide['failed'])
check('...and no transmitter power could fix it',
      wide['spread_db'] > wide['window_db'],
      (wide['spread_db'], wide['window_db']))

good = lb.evaluate(0.0, 2.0, 12.6, 20.5, -22.0, -8.0)
check('a link meeting every condition passes', good['power_conditions_met'],
      good['failed'])
check('...and all three conditions are individually reported',
      len(good['conditions']) == 3 and all(c['passes'] for c in good['conditions']))

# ---- the extremes are really computed from the extremes -------------------
check('the maximum received power uses the max Tx and the MIN loss',
      abs(good['rx_max_dbm'] - (2.0 - 12.6)) < 1e-9, good['rx_max_dbm'])
check('the minimum uses the min Tx and the MAX loss',
      abs(good['rx_min_dbm'] - (0.0 - 20.5)) < 1e-9, good['rx_min_dbm'])
check('an end-of-life allowance lowers the minimum further',
      lb.evaluate(0.0, 2.0, 12.6, 20.5, -22.0, -8.0,
                  extra_end_of_life_db=2.0)['rx_min_dbm']
      < good['rx_min_dbm'])
check('...and does not move the maximum',
      lb.evaluate(0.0, 2.0, 12.6, 20.5, -22.0, -8.0,
                  extra_end_of_life_db=2.0)['rx_max_dbm'] == good['rx_max_dbm'])
check('a midpoint would satisfy neither test',
      good['rx_max_dbm'] != good['rx_min_dbm'])

# a wider transmitter tolerance makes the problem harder, not easier
check('a wider transmitter tolerance widens the spread',
      lb.evaluate(-2.0, 4.0, 12.6, 20.5, -22.0, -8.0)['spread_db']
      > good['spread_db'])

# ---- the double-counting trap ---------------------------------------------
sep, inc = lb.reserve(), lb.reserve(already_in_loss_max=True)
check('the two conventions give different reserves',
      sep['total_db'] != inc['total_db'], (sep['total_db'], inc['total_db']))
check('the design-basis convention omits ageing and repairs',
      set(inc['omitted']) == {'ageing', 'repairs'}, inc['omitted'])
check('...leaving only drift', inc['counted'] == ['drift'])
check('the commissioning convention counts all three',
      set(sep['counted']) == {'ageing', 'repairs', 'drift'})
check('each explains itself', sep['why'] and inc['why'])
check('the difference is exactly the double-counted part',
      abs((sep['total_db'] - inc['total_db']) - 4.0) < 1e-9)

# ---- rejection -------------------------------------------------------------
for args, word in (
        ((2.0, 0.0, 1.0, 2.0, -22.0, -8.0), 'maximum is below its minimum'),
        ((0.0, 2.0, 5.0, 1.0, -22.0, -8.0), 'maximum loss is below its minimum'),
        ((0.0, 2.0, -1.0, 2.0, -22.0, -8.0), 'not negative'),
        ((0.0, 2.0, 1.0, 2.0, -8.0, -22.0), 'no window at all'),
        ((0.0, 2.0, 1.0, 2.0, -22.0, -22.0), 'no window at all')):
    try:
        lb.evaluate(*args)
        check('rejects %r' % (args,), False, 'no exception')
    except lb.BudgetError as e:
        check('rejects %r' % (args,), word in str(e), str(e)[:60])
try:
    lb.evaluate(0.0, 2.0, 1.0, 2.0, -22.0, -8.0, extra_end_of_life_db=-1)
    check('rejects a negative end-of-life allowance', False, 'no exception')
except lb.BudgetError as e:
    check('rejects a negative end-of-life allowance', 'not negative' in str(e))
try:
    lb.reserve(ageing_db=-1)
    check('rejects a negative reserve', False, 'no exception')
except lb.BudgetError as e:
    check('rejects a negative reserve', 'not negative' in str(e))

# ---- the shipped cases are a spread ---------------------------------------
a = lb.analyse()
passes = [c['name'] for c in a['cases'] if c['power_conditions_met']]
fails = [c['name'] for c in a['cases'] if not c['power_conditions_met']]
check('some shipped cases pass', len(passes) >= 2, passes)
check('...and each failure mode is represented', len(fails) >= 3, fails)
check('the attenuator fixes the short patch',
      any('attenuator' in p for p in passes), passes)

# ---- the report refuses the claim the chapter used to make ----------------
_r, out = quiet(lb.report, a)
low = ' '.join(out.lower().split())
check('the report refuses to say the link works',
      'none of the above says' in low and 'the link works' in low)
check('the report points at the OSNR budget', 'lab 44.2' in low)
check('the report explains the double-counting trap',
      'counting the same decibels' in low)
check('the report shows the failing condition itemised', 'FAILS' in out)
check('the report disclaims equipment',
      'no transponder' in low and 'power meter' in low)
rc, _o = quiet(lb.main, [])
check('the script exits 0', rc == 0, rc)
rc2, _o = quiet(lb.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
