#!/usr/bin/env python3
"""Lab 42.3 --- the egress saving, and what it costs you in availability.

WHY THIS EXISTS
---------------
Chapter 42 used to advise keeping chatty tiers in one availability zone so
their traffic is not metered, and the lab that came with it priced exactly that
move as a saving.  Both stopped at the invoice.

Collapsing a two-zone tier into one zone does reduce the cross-zone bill to
nothing.  It also removes the thing the second zone was there for.  Presented as
a cost optimisation with no mention of what was given up, it is advice that
trades an availability design for a line on a bill --- and the reader is never
told a trade happened.

This prices both sides.  The tariffs and the availability figures are YOUR
inputs: no vendor price list or published availability figure was available when
this was written, and none is assumed.  What the script contributes is the
comparison, which is the part people skip.

THE COMPARISON
--------------
For each design: the monthly transfer bill, and the expected monthly cost of
downtime, given a stated per-zone failure probability and a stated cost per hour
of outage.  A single-zone tier is down when its zone is down.  A two-zone tier
is down when both are, if it genuinely fails over --- which is an assumption the
script makes you state, because a second zone you have never failed over to is
an expense, not a design.

    python3 egress_vs_availability.py
    python3 egress_vs_availability.py --json
    python3 test_egress_vs_availability.py

No cloud account, no measurement, no vendor data.
"""
import argparse
import json
import sys

HOURS_PER_MONTH = 730.0


class ModelError(ValueError):
    """The inputs do not describe a comparison that can be made."""


# --------------------------------------------------------------------------
# YOUR inputs. None of these is a price or a published figure.
# --------------------------------------------------------------------------
TARIFF = {
    'intra_zone': 0.00,
    'cross_zone': 0.01,
    'cross_region': 0.02,
    'internet': 0.09,
}

ASSUMPTIONS = {
    # probability that one zone is unavailable at a given moment
    'zone_failure_probability': 0.001,
    # what an hour of this tier being down costs the business
    'downtime_cost_per_hour': 5000.0,
    # does the two-zone design actually fail over, and how completely?
    'failover_effectiveness': 1.0,
}


def check_tariff(tariff):
    for k, v in tariff.items():
        if not isinstance(v, (int, float)) or v < 0:
            raise ModelError('tariff %r must be a non-negative number, got %r'
                             % (k, v))
    return tariff


def transfer_bill(flows, tariff=None):
    """flows: [(description, kind, gigabytes_per_month), ...]"""
    tariff = check_tariff(dict(tariff or TARIFF))
    lines, total = [], 0.0
    for desc, kind, gb in flows:
        if kind not in tariff:
            raise ModelError('no tariff for %r; the kinds are %s'
                             % (kind, ', '.join(sorted(tariff))))
        if gb < 0:
            raise ModelError('%s: volume must not be negative' % desc)
        cost = gb * tariff[kind]
        lines.append({'description': desc, 'kind': kind, 'gb': gb,
                      'rate': tariff[kind], 'cost': cost})
        total += cost
    return {'lines': lines, 'total': total}


def availability_cost(zones, p_fail, cost_per_hour, effectiveness=1.0):
    """Expected monthly downtime cost for a tier spread across `zones` zones.

    One zone: unavailable whenever that zone is.
    Several zones: unavailable when all of them are, plus the share of
    single-zone failures that failover does not actually cover.

    Note what that means at the bottom end. With effectiveness at zero the
    tier is down whenever ANY of its zones is, which is WORSE than running in
    one zone --- you have doubled the number of zones that can take you down
    and gained nothing back. A second zone is not availability; failing over
    to it is. If you have never tested the failover, model it here at
    something well below 1.0 and see what the second zone is actually buying.
    """
    if zones < 1:
        raise ModelError('a tier occupies at least one zone, got %r' % (zones,))
    if not 0 <= p_fail <= 1:
        raise ModelError('a probability is between 0 and 1, got %r' % (p_fail,))
    if cost_per_hour < 0:
        raise ModelError('the cost of an hour down must not be negative')
    if not 0 <= effectiveness <= 1:
        raise ModelError('failover effectiveness is between 0 and 1, got %r'
                         % (effectiveness,))
    if zones == 1:
        p_down = p_fail
    else:
        p_all = p_fail ** zones
        # any single-zone failure that failover does not cover still hurts
        p_uncovered = (1 - (1 - p_fail) ** zones - p_all) * (1 - effectiveness)
        p_down = p_all + p_uncovered
    hours = p_down * HOURS_PER_MONTH
    return {'zones': zones, 'p_down': p_down, 'expected_hours_down': hours,
            'expected_cost': hours * cost_per_hour}


def compare(designs, tariff=None, assumptions=None):
    a = dict(ASSUMPTIONS)
    a.update(assumptions or {})
    out = []
    for name, zones, flows in designs:
        t = transfer_bill(flows, tariff)
        av = availability_cost(zones, a['zone_failure_probability'],
                               a['downtime_cost_per_hour'],
                               a['failover_effectiveness'])
        out.append({'name': name, 'zones': zones, 'transfer': t['total'],
                    'lines': t['lines'],
                    'expected_hours_down': av['expected_hours_down'],
                    'downtime': av['expected_cost'],
                    'total': t['total'] + av['expected_cost']})
    cheapest = min(out, key=lambda d: d['total'])
    for d in out:
        d['cheapest_overall'] = d is cheapest
    return {'designs': out, 'assumptions': a, 'tariff': dict(tariff or TARIFF)}


# --------------------------------------------------------------------------
# the same workload, three ways
# --------------------------------------------------------------------------
def designs():
    return [
        ('spread over two zones', 2, [
            ('app -> db, chatty, across zones', 'cross_zone', 40_000),
            ('analytics export to a SaaS', 'internet', 15_000),
            ('cross-region replica', 'cross_region', 20_000),
        ]),
        ('collapsed into one zone', 1, [
            ('app -> db, chatty, same zone', 'intra_zone', 40_000),
            ('analytics export to a SaaS', 'internet', 15_000),
            ('cross-region replica', 'cross_region', 20_000),
        ]),
        ('two zones, analytics kept cloud-side', 2, [
            ('app -> db, chatty, across zones', 'cross_zone', 40_000),
            ('analytics result only', 'internet', 500),
            ('cross-region replica', 'cross_region', 20_000),
        ]),
    ]


def report(c):
    a, t = c['assumptions'], c['tariff']
    print('Transfer bill against expected downtime, on YOUR figures.')
    print('No vendor price list or published availability figure was available;')
    print('every number below is an input, not a quotation.\n')
    print('  tariff, per GB: ' + '  '.join('%s %.2f' % (k, v)
                                           for k, v in sorted(t.items())))
    print('  one zone unavailable with probability %g'
          % a['zone_failure_probability'])
    print('  an hour of this tier down costs %.0f'
          % a['downtime_cost_per_hour'])
    print('  failover works %.0f%% of the time\n'
          % (a['failover_effectiveness'] * 100))

    print('%36s | %5s | %10s | %8s | %10s | %s'
          % ('design', 'zones', 'transfer', 'hrs down', 'downtime', 'total'))
    print('-' * 92)
    for d in c['designs']:
        print('%36s | %5d | %10.0f | %8.2f | %10.0f | %10.0f%s'
              % (d['name'], d['zones'], d['transfer'],
                 d['expected_hours_down'], d['downtime'], d['total'],
                 '  <-- cheapest' if d['cheapest_overall'] else ''))

    two, one = c['designs'][0], c['designs'][1]
    saved = two['transfer'] - one['transfer']
    added = one['downtime'] - two['downtime']
    print('\nCollapsing into one zone saves %.0f a month on transfer and adds'
          % saved)
    print('%.0f a month in expected downtime. It is not a saving of %.0f; it is'
          % (added, saved))
    print('a trade, and on these figures it comes out %.0f a month %s.'
          % (abs(added - saved), 'WORSE' if added > saved else 'better'))
    print('\nThe figures are yours to set, and the answer moves with them: a')
    print('tier whose downtime costs little, or whose zone rarely fails, can')
    print('well be worth collapsing. What is never right is to price one side')
    print('of the trade and call the result an optimisation.')

    third = c['designs'][2]
    print('\nThe third design changes neither: it keeps both zones and stops')
    print('shipping the raw data out, saving %.0f a month with no availability'
          % (two['transfer'] - third['transfer']))
    print('given up at all. Look for that one first --- it is the saving that')
    print('costs nothing, and it is usually the larger of the two.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--downtime-cost', type=float,
                    default=ASSUMPTIONS['downtime_cost_per_hour'])
    ap.add_argument('--zone-failure', type=float,
                    default=ASSUMPTIONS['zone_failure_probability'])
    ap.add_argument('--failover', type=float,
                    default=ASSUMPTIONS['failover_effectiveness'])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        c = compare(designs(), assumptions={
            'downtime_cost_per_hour': args.downtime_cost,
            'zone_failure_probability': args.zone_failure,
            'failover_effectiveness': args.failover})
    except ModelError as e:
        print('model error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(c, indent=2))
    else:
        report(c)
    return 0


if __name__ == '__main__':
    sys.exit(main())
