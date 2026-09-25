#!/usr/bin/env python3
"""Lab 43.3 --- build, IRU or buy, decided by demand rather than by adjective.

WHY THIS EXISTS
---------------
Chapter 43 described the choice as "a spectrum from control to speed, decided by
scale and time", with building giving "the lowest long-run cost per bit".  The
adjectives are fine and the conclusion is unsupported, because it leaves out the
one variable that decides it: how much traffic the route will carry.

The two kinds of option have different SHAPES, not different sizes.  A route you
own, hold an IRU on, or lease dark costs the same whether you light one
wavelength or fill it --- so the model's cost per carried bit falls with utilisation up to its finite
capacity. Incremental optics, power and upgrades must be costed separately.  Capacity you buy scales with demand, in the unit it is sold in --- so its
cost per bit is flat, and at low demand that flat line is below the falling one.
Somewhere they cross.  Where, is the whole question, and no adjective answers
it.

Two further things the chapter treated as settled and are not:

  An IRU is not ownership.  It is a long right of use with an annual operations
  and maintenance charge attached, a term that ends, and clauses about what
  happens if the grantor relocates the cable or stops existing.  Leaving the
  O&M out of the arithmetic is how an IRU comes to look like a purchase.

  Leased capacity is not automatically diverse.  Two circuits bought as "diverse"
  from one provider, or from two providers who both lease from a third, can share
  a duct.  Diversity is a property of the physical route, and the only way to
  know is to ask for the route and check it against your own.

This computes cost per bit-year for each option as utilisation varies, and finds
the crossover.  Every figure is one you supply: no quotation, price list or
market rate was available when this was written.

    python3 route_procurement.py
    python3 route_procurement.py --json
    python3 test_route_procurement.py
"""
import argparse
import json
import sys


class ProcurementError(ValueError):
    """The options cannot be compared as described."""


def annualised_fixed(option, years):
    """Average annual cost of an option whose cost does not follow demand.

    Capital is spread evenly across the term: a crude annualisation that ignores
    the cost of money, which matters and which you should put back in with your
    own discount rate before quoting anything to a finance director.

    For comparisons longer than an option's term, this teaching model amortises
    repeated terms proportionally at today's capital cost. It does not model
    discrete renewal cash payments, discounting or future renewal prices.
    """
    for k in ('capex', 'annual_opex', 'capacity_gbps'):
        if k not in option:
            raise ProcurementError('option %r has no %s'
                                   % (option.get('name', '?'), k))
    if years <= 0:
        raise ProcurementError('the term is a positive number of years')
    if option['capacity_gbps'] <= 0:
        raise ProcurementError('%s: capacity must be positive'
                               % option.get('name', '?'))
    if option['capex'] < 0 or option['annual_opex'] < 0:
        raise ProcurementError('%s: costs must not be negative'
                               % option.get('name', '?'))
    term = option.get('term_years', years)
    if term <= 0:
        raise ProcurementError('%s: the term is positive' % option['name'])
    renewals = max(1.0, years / float(term))
    return option['capex'] * renewals / years + option['annual_opex']


def annual_cost(option, years, demand_gbps):
    """What this option costs per year to carry `demand_gbps`.

    Two shapes, and the difference between them is the entire decision:

      A ROUTE you own, hold an IRU on, or lease dark costs the same whether you
      light one wavelength or fill it. Its cost does not follow demand at all.

      CAPACITY you buy follows demand --- but in the unit it is sold in. Ask for
      500 Gb/s of 400G waves and you buy two, and pay for 800.
    """
    if demand_gbps < 0:
        raise ProcurementError('demand is not negative, got %r' % (demand_gbps,))
    if option.get('per_unit_annual') is not None:
        unit = option.get('unit_gbps', 1.0)
        if unit <= 0:
            raise ProcurementError('%s: the unit size is positive' % option['name'])
        units = 0 if demand_gbps == 0 else int(-(-demand_gbps // unit))
        return {'annual': units * option['per_unit_annual'], 'units': units,
                'supplied_gbps': units * unit, 'exceeds_capacity': False}
    cost = annualised_fixed(option, years)
    return {'annual': cost, 'units': 1, 'supplied_gbps': option['capacity_gbps'],
            'exceeds_capacity': demand_gbps > option['capacity_gbps']}


def cost_per_gbps_year(option, years, demand_gbps):
    """Annual cost divided by the demand actually carried.

    Capacity you have bought and are not using is not free, and this is the
    number that says so.
    """
    if demand_gbps <= 0:
        raise ProcurementError('demand is positive, got %r' % (demand_gbps,))
    return annual_cost(option, years, demand_gbps)['annual'] / demand_gbps


def compare(options, years, demands):
    if not options:
        raise ProcurementError('nothing to compare')
    rows = []
    for d in demands:
        entry = {'demand_gbps': d, 'costs': {}, 'over_capacity': []}
        for o in options:
            ac = annual_cost(o, years, d)
            entry['costs'][o['name']] = ac['annual'] / d
            if ac['exceeds_capacity']:
                entry['over_capacity'].append(o['name'])
        usable = {k: v for k, v in entry['costs'].items()
                  if k not in entry['over_capacity']}
        entry['cheapest'] = min(usable, key=usable.get) if usable else None
        rows.append(entry)
    return rows


def envelope_rate(option, years, demand_gbps):
    """Cost per Gb/s-year, comparing unit-priced options at their BEST case.

    A wavelength service's cost per gigabit is a sawtooth: it is lowest at exact
    multiples of the wave size and worst just past one. Comparing at an
    arbitrary demand therefore tells you as much about where you happened to
    land on that sawtooth as about the options. The crossover is computed on the
    envelope --- the unit-priced option at full waves --- which is the
    comparison that holds however the demand falls.
    """
    if option.get('per_unit_annual') is not None:
        unit = option.get('unit_gbps', 1.0)
        return option['per_unit_annual'] / unit
    return cost_per_gbps_year(option, years, demand_gbps)


def crossover(a, b, years, lo=1.0, hi=100_000.0, tol=1e-3):
    """The demand at which option a becomes cheaper than option b.

    Returns None when one is cheaper at every demand in range, which is an
    answer too --- and a more useful one than a number, because it means the
    decision does not turn on this variable at all.
    """
    f = lambda d: (envelope_rate(a, years, d) - envelope_rate(b, years, d))
    if (f(lo) > 0) == (f(hi) > 0):
        return None
    for _ in range(300):
        mid = (lo + hi) / 2.0
        if (f(lo) > 0) == (f(mid) > 0):
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2.0


# --------------------------------------------------------------------------
# ILLUSTRATIVE OPTIONS. Not prices. Not a quotation. Replace every figure.
# --------------------------------------------------------------------------
def options():
    return [
        {'name': 'build and own', 'capex': 6_000_000.0, 'annual_opex': 180_000.0,
         'capacity_gbps': 4_800.0, 'per_unit_annual': None,
         'note': 'the duct and the glass are yours; so is every repair'},
        {'name': 'IRU, 20 years', 'capex': 3_600_000.0, 'annual_opex': 90_000.0,
         'capacity_gbps': 4_800.0, 'term_years': 20, 'per_unit_annual': None,
         'note': 'a right of USE with an O&M charge and an end date'},
        {'name': 'dark fibre lease', 'capex': 120_000.0,
         'annual_opex': 420_000.0, 'capacity_gbps': 4_800.0,
         'per_unit_annual': None,
         'note': 'your optics, their glass, their restoration priority'},
        {'name': 'leased 400G waves', 'capex': 0.0, 'annual_opex': 0.0,
         'capacity_gbps': 1e9, 'per_unit_annual': 240_000.0, 'unit_gbps': 400.0,
         'note': 'weeks to turn up; you buy capacity in wavelengths, not a route'},
    ]


def analyse(years=20):
    opts = options()
    demands = (100.0, 400.0, 800.0, 1_600.0, 2_400.0, 4_800.0)
    rows = compare(opts, years, demands)
    by = {o['name']: o for o in opts}
    return {
        'years': years, 'options': opts, 'rows': rows,
        'crossovers': {
            'build vs leased waves':
                crossover(by['build and own'], by['leased 400G waves'], years),
            'IRU vs leased waves':
                crossover(by['IRU, 20 years'], by['leased 400G waves'], years),
            'dark fibre vs leased waves':
                crossover(by['dark fibre lease'], by['leased 400G waves'], years),
            'build vs IRU':
                crossover(by['build and own'], by['IRU, 20 years'], years),
        },
        'term_effect': {
            str(y): {'IRU': annualised_fixed(by['IRU, 20 years'], y),
                     'build': annualised_fixed(by['build and own'], y)}
            for y in (10, 20, 30, 40)},
    }


def report(a):
    print('Cost per gigabit-year of carried traffic, over %d years.' % a['years'])
    print('ILLUSTRATIVE FIGURES, not prices: no quotation or market rate was')
    print('available. Replace every one of them before deciding anything.\n')
    names = [o['name'] for o in a['options']]
    for o in a['options']:
        if o.get('per_unit_annual') is not None:
            print('  %-18s %9.0f per %.0f Gb/s wave, bought as needed  --- %s'
                  % (o['name'], o['per_unit_annual'], o['unit_gbps'], o['note']))
        else:
            print('  %-18s capex %10.0f  opex/yr %8.0f  up to %5.0f Gb/s  --- %s'
                  % (o['name'], o['capex'], o['annual_opex'],
                     o['capacity_gbps'], o['note']))
    print()
    print('%12s | %s' % ('demand',
                         ' | '.join('%18s' % n for n in names)))
    print('-' * (14 + 21 * len(names)))
    for r in a['rows']:
        cells = []
        for n in names:
            mark = '*' if r['cheapest'] == n else ' '
            cells.append('%17.0f%s' % (r['costs'][n], mark))
        print('%8.0f Gb/s | %s' % (r['demand_gbps'], ' | '.join(cells)))
    print('\n(* is the cheapest option at that demand)')

    cap = a['options'][0]['capacity_gbps']
    print('\nCrossovers --- the demand at which the answer changes:')
    for label, d in a['crossovers'].items():
        if d is None:
            print('  %-28s never; one wins at every demand in range'
                  % (label + ':'))
        else:
            print('  %-28s %.0f Gb/s  (%.0f%% of a %.0f Gb/s route)'
                  % (label + ':', d, 100.0 * d / cap, cap))

    print('\nThe leased line is a SAWTOOTH, not a line: buy in 400 Gb/s units')
    print('and 401 Gb/s of demand costs what 800 does. The crossovers above are')
    print('computed at full waves, which is the comparison that survives however')
    print('your demand happens to fall.')

    lo, hi = a['rows'][0], a['rows'][-1]
    print('\nAt %.0f Gb/s the cheapest option is "%s". At %.0f Gb/s it is "%s".'
          % (lo['demand_gbps'], lo['cheapest'], hi['demand_gbps'], hi['cheapest']))
    print('Nothing about the routes changed and no price moved --- only the')
    print('assumption about what the route would carry, which is the assumption')
    print('a business case states least clearly and gets most wrong.')

    te = a['term_effect']
    print('\nNotice what building does NOT win on here. At these figures the IRU')
    print('is cheaper than building at every demand and every term:')
    print('%10s | %14s | %14s' % ('years', 'IRU per year', 'build per year'))
    print('-' * 44)
    for y in sorted(te, key=int):
        print('%10s | %14.0f | %14.0f' % (y, te[y]['IRU'], te[y]['build']))
    print('\nSo if you build, be clear it is not for the arithmetic. It is for')
    print('what the arithmetic cannot hold: no counterparty, no renewal')
    print('negotiation conducted from a position of having nowhere else to go,')
    print('no clause letting somebody move your cable, and an asset that is')
    print('still yours when the term on this table would have ended. Those are')
    print('real reasons. They are just not the ones the spreadsheet shows.')

    print('\nTwo things no column above can tell you. An IRU is a right of USE')
    print('with an end date and an O&M charge, so read what happens at expiry')
    print('and on the grantor\'s insolvency before treating it as ownership. And')
    print('leased capacity is not automatically diverse: two circuits sold as')
    print('diverse can share a duct, so ask for the physical route and check it')
    print('against your own rather than against the supplier\'s diagram.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--years', type=int, default=20)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        a = analyse(args.years)
    except ProcurementError as e:
        print('procurement error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(a, indent=2))
    else:
        report(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
