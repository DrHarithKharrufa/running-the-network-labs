#!/usr/bin/env python3
"""Checks for route_procurement.py --- the crossover, not a price list.

The chapter asserted that building gives "the lowest long-run cost per bit"
without stating the demand that makes it true. The central checks are that the
cheapest option CHANGES with demand, and that the two kinds of option have
different shapes --- a route's cost per bit falls without limit, a bought
wavelength's does not. If a future edit makes the answer independent of demand,
these fail.

No quotation, price list or market rate. Arithmetic on stated figures.

    python3 test_route_procurement.py
"""
import contextlib, io, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import route_procurement as rp  # noqa: E402

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


OPTS = {o['name']: o for o in rp.options()}
BUILD, IRU = OPTS['build and own'], OPTS['IRU, 20 years']
DARK, WAVES = OPTS['dark fibre lease'], OPTS['leased 400G waves']

# ---- THE POINT: the answer depends on demand ------------------------------
a = rp.analyse(20)
cheapest = [r['cheapest'] for r in a['rows']]
check('the cheapest option changes with demand', len(set(cheapest)) > 1,
      cheapest)
check('a bought wavelength wins at low demand',
      a['rows'][0]['cheapest'] == 'leased 400G waves', a['rows'][0]['cheapest'])
check('a route wins at high demand',
      a['rows'][-1]['cheapest'] != 'leased 400G waves', a['rows'][-1]['cheapest'])
check('there is a real crossover between them',
      a['crossovers']['IRU vs leased waves'] is not None,
      a['crossovers'])

# ---- the two shapes --------------------------------------------------------
fixed_low = rp.cost_per_gbps_year(IRU, 20, 100)
fixed_high = rp.cost_per_gbps_year(IRU, 20, 4800)
check("a route's cost per bit falls as demand rises",
      fixed_high < fixed_low / 10, (fixed_low, fixed_high))
check('...and its annual cost does not move at all',
      rp.annual_cost(IRU, 20, 100)['annual']
      == rp.annual_cost(IRU, 20, 4800)['annual'])
check("a wavelength service's annual cost DOES follow demand",
      rp.annual_cost(WAVES, 20, 1600)['annual']
      > rp.annual_cost(WAVES, 20, 400)['annual'])
check('...in whole waves, so 401 Gb/s costs what 800 does',
      rp.annual_cost(WAVES, 20, 401)['annual']
      == rp.annual_cost(WAVES, 20, 800)['annual'])
check('...and 400 Gb/s costs one wave',
      rp.annual_cost(WAVES, 20, 400)['units'] == 1)
check('the sawtooth is real: cost per bit is worse just past a boundary',
      rp.cost_per_gbps_year(WAVES, 20, 401)
      > rp.cost_per_gbps_year(WAVES, 20, 400))
check('the envelope compares at full waves, not on the sawtooth',
      abs(rp.envelope_rate(WAVES, 20, 401)
          - WAVES['per_unit_annual'] / WAVES['unit_gbps']) < 1e-9)

# ---- crossovers follow the figures ----------------------------------------
x_iru = a['crossovers']['IRU vs leased waves']
x_build = a['crossovers']['build vs leased waves']
check('the dearer route crosses over at a higher demand', x_build > x_iru,
      (x_build, x_iru))
check('the crossover is where the two rates are equal',
      abs(rp.envelope_rate(IRU, 20, x_iru)
          - rp.envelope_rate(WAVES, 20, x_iru)) < 1.0, x_iru)
check('below it the wavelength is cheaper',
      rp.envelope_rate(WAVES, 20, x_iru * 0.5)
      < rp.envelope_rate(IRU, 20, x_iru * 0.5))
check('above it the route is cheaper',
      rp.envelope_rate(IRU, 20, x_iru * 2)
      < rp.envelope_rate(WAVES, 20, x_iru * 2))
cheaper_waves = dict(WAVES, per_unit_annual=60_000.0)
check('halving the wave price moves the crossover out',
      rp.crossover(IRU, cheaper_waves, 20) > x_iru,
      (rp.crossover(IRU, cheaper_waves, 20), x_iru))
check('two options of identical shape never cross',
      rp.crossover(BUILD, IRU, 20) is None)

# ---- an IRU is not ownership: the term is modelled ------------------------
check('an IRU shorter than the comparison is renewed, not free',
      rp.annualised_fixed(IRU, 40) * 40 > IRU['capex'] + 40 * IRU['annual_opex']
      - 1e-6)
check('...so its capex is counted twice over forty years',
      abs(rp.annualised_fixed(IRU, 40)
          - (IRU['capex'] * 2 / 40 + IRU['annual_opex'])) < 1e-9)
check('an owned route is not renewed',
      abs(rp.annualised_fixed(BUILD, 40)
          - (BUILD['capex'] / 40 + BUILD['annual_opex'])) < 1e-9)
check('the O&M charge is part of the IRU, not an extra',
      IRU['annual_opex'] > 0)
check('a longer term spreads an owned route further',
      rp.annualised_fixed(BUILD, 40) < rp.annualised_fixed(BUILD, 10))
check('the term effect is reported for both', set(a['term_effect']['20'])
      == {'IRU', 'build'})

# ---- capacity ceilings are respected --------------------------------------
over = rp.annual_cost(BUILD, 20, 9600)
check('demand beyond a route\'s capacity is flagged', over['exceeds_capacity'])
check('...and such an option is not offered as cheapest',
      'build and own' not in [r['cheapest'] for r in
                              rp.compare(rp.options(), 20, [9600])])
check('within capacity it is not flagged',
      not rp.annual_cost(BUILD, 20, 4800)['exceeds_capacity'])

# ---- rejection -------------------------------------------------------------
for fn, args, word in (
        (rp.annualised_fixed, ({'capex': 1, 'annual_opex': 1,
                                'capacity_gbps': 1, 'name': 'x'}, 0), 'positive number of years'),
        (rp.annualised_fixed, ({'capex': -1, 'annual_opex': 1,
                                'capacity_gbps': 1, 'name': 'x'}, 5), 'not be negative'),
        (rp.annualised_fixed, ({'capex': 1, 'annual_opex': 1,
                                'capacity_gbps': 0, 'name': 'x'}, 5), 'must be positive'),
        (rp.annualised_fixed, ({'capex': 1, 'annual_opex': 1, 'name': 'x'}, 5),
         'has no capacity_gbps'),
        (rp.cost_per_gbps_year, (IRU, 20, 0), 'demand is positive'),
        (rp.annual_cost, (IRU, 20, -1), 'not negative'),
        (rp.compare, ([], 20, [100]), 'nothing to compare')):
    try:
        fn(*args)
        check('rejects %s(...)' % fn.__name__, False, 'no exception')
    except rp.ProcurementError as e:
        check('rejects %s(...)' % fn.__name__, word in str(e), str(e)[:60])

# ---- the report is honest about what it is --------------------------------
_r, out = quiet(rp.report, a)
low = ' '.join(out.lower().split())
check('the report says the figures are illustrative, not prices',
      'illustrative figures, not prices' in low)
check('the report says no quotation was available', 'no quotation' in low)
check('the report names the sawtooth', 'sawtooth' in low)
check('the report says an IRU is a right of use with an end date',
      'right of use' in low and 'end date' in low)
check('the report warns that leased capacity is not automatically diverse',
      'not automatically diverse' in low)
check('the report gives the non-cost reasons to build',
      'not for the arithmetic' in low)
rc, _o = quiet(rp.main, [])
check('the script exits 0', rc == 0, rc)
rc2, _o = quiet(rp.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
