#!/usr/bin/env python3
"""Lab 44.1 --- the power budget, with a verdict that counts every condition.

WHY THIS VERSION EXISTS
-----------------------
The previous script computed the received power, compared it with the receiver's
sensitivity, subtracted a ten-year reserve, and printed a verdict --- and the
verdict was computed from that one subtraction alone.  It printed the overload
check on the line above and then ignored it.

Given a transmitter of +10 dBm into 5 dB of loss it reported, in the same run:

    overload check: Rx +5.0 < overload -8.0?  NO -- receiver clipped!
    verdict: OK -- still positive in year 10

A receiver driven thirteen decibels past its maximum input, declared good.  That
is not a rounding error; it is a verdict that does not look at all of its own
inputs, and it is the reason this version computes a LIST of conditions and
fails if any one of them fails.

Two further corrections.

  The budget is worked at BOTH extremes rather than at a midpoint.  "Aim for the
  middle of the window" is not a design method: the maximum received power --- a
  new transmitter at the top of its tolerance into a short, low-loss path --- has
  to clear overload, and the minimum --- end of life, maximum losses, after the
  repairs to come --- has to clear sensitivity.  Both have to hold, and no single
  aim-point establishes either.

  A positive power margin does NOT establish that a coherent link works.  Power
  and OSNR are different budgets and the OSNR one governs.  This script says so
  rather than printing "the link works", and Lab 44.2 does the OSNR side.

    python3 link_budget.py
    python3 link_budget.py --json
    python3 test_link_budget.py

No transponder, fibre or power meter. Arithmetic on figures you supply.
"""
import argparse
import json
import sys


class BudgetError(ValueError):
    """The link cannot be evaluated as described."""


def evaluate(tx_min_dbm, tx_max_dbm, loss_min_db, loss_max_db,
             sensitivity_dbm, overload_dbm, extra_end_of_life_db=0.0):
    """Both extremes, and every condition that has to hold at once.

    tx_min/tx_max     the transmitter's output across its tolerance and life
    loss_min/loss_max the path at its best and worst, the worst including the
                      repairs and ageing the span has not had yet
    """
    if tx_max_dbm < tx_min_dbm:
        raise BudgetError('the transmitter maximum is below its minimum')
    if loss_max_db < loss_min_db:
        raise BudgetError('the path maximum loss is below its minimum')
    if loss_min_db < 0:
        raise BudgetError('a path loss is not negative, got %r' % (loss_min_db,))
    if overload_dbm <= sensitivity_dbm:
        raise BudgetError('the overload point (%r) must be above the sensitivity '
                          '(%r) or there is no window at all'
                          % (overload_dbm, sensitivity_dbm))
    if extra_end_of_life_db < 0:
        raise BudgetError('the end-of-life allowance is not negative')

    rx_max = tx_max_dbm - loss_min_db
    rx_min = tx_min_dbm - loss_max_db - extra_end_of_life_db

    conditions = [
        {'name': 'worst case clears sensitivity',
         'detail': 'lowest transmitter into the highest loss, at end of life',
         'value_db': rx_min - sensitivity_dbm,
         'passes': rx_min >= sensitivity_dbm},
        {'name': 'best case stays under overload',
         'detail': 'highest transmitter into the lowest loss, when new',
         'value_db': overload_dbm - rx_max,
         'passes': rx_max <= overload_dbm},
        {'name': 'the window is wider than the spread',
         'detail': 'the path varies by less than the receiver can accept',
         'value_db': (overload_dbm - sensitivity_dbm) - (rx_max - rx_min),
         'passes': (overload_dbm - sensitivity_dbm) >= (rx_max - rx_min)},
    ]
    failed = [c['name'] for c in conditions if not c['passes']]
    return {
        'rx_max_dbm': rx_max, 'rx_min_dbm': rx_min,
        'spread_db': rx_max - rx_min,
        'window_db': overload_dbm - sensitivity_dbm,
        'sensitivity_dbm': sensitivity_dbm, 'overload_dbm': overload_dbm,
        'conditions': conditions,
        'failed': failed,
        # the verdict is ALL of them, which is the whole point of this rewrite
        'power_conditions_met': not failed,
        'worst_case_margin_db': rx_min - sensitivity_dbm,
    }


SHORT = {'worst case clears sensitivity': 'too weak at worst case',
         'best case stays under overload': 'too strong at best case',
         'the window is wider than the spread': 'path varies more than the window'}


def verdict_short(r):
    if r['failed']:
        return 'FAILS: ' + '; '.join(SHORT[f] for f in r['failed'])
    return 'power conditions met'


def verdict_text(r):
    if r['failed']:
        return 'FAILS the power budget: ' + '; '.join(r['failed'])
    return ('power conditions met, %.2f dB of worst-case margin --- which is '
            'NOT the same as "the link works"' % r['worst_case_margin_db'])


# --------------------------------------------------------------------------
# where the reserve goes, and the double-counting trap
# --------------------------------------------------------------------------
def reserve(ageing_db=2.0, repairs_db=2.0, drift_db=1.0,
            already_in_loss_max=False):
    """The allowance for what the span has not suffered yet.

    The trap: if your maximum path loss ALREADY used specification limits and
    already included the repairs to come --- which is what a design-basis loss
    budget does, and what Lab 43.1 computes --- then adding an ageing and repair
    reserve here counts the same decibels twice. Twice-counted margin is not
    conservative, it is wrong, and it buys equipment nobody needed.

    Say which convention you are using and hold to it.
    """
    for v in (ageing_db, repairs_db, drift_db):
        if v < 0:
            raise BudgetError('a reserve is not negative, got %r' % (v,))
    if already_in_loss_max:
        return {'total_db': drift_db, 'counted': ['drift'],
                'omitted': ['ageing', 'repairs'],
                'why': ('the maximum-loss figure already carries ageing and the '
                        'repairs to come, so only drift is added here')}
    return {'total_db': ageing_db + repairs_db + drift_db,
            'counted': ['ageing', 'repairs', 'drift'], 'omitted': [],
            'why': ('the maximum-loss figure is a commissioning measurement, so '
                    'the life allowance is added here instead')}


# --------------------------------------------------------------------------
# the worked cases
# --------------------------------------------------------------------------
CASES = [
    # name, tx_min, tx_max, loss_min, loss_max, sensitivity, overload
    ("the chapter's 60 km span", 0.0, 2.0, 12.6, 20.5, -22.0, -8.0),
    ('the same span, transmitter at +10 dBm', 9.0, 11.0, 12.6, 20.5, -22.0, -8.0),
    ('a short patch, nobody fitted an attenuator', 0.0, 2.0, 1.0, 3.0, -22.0, -8.0),
    ('...the same patch with a 10 dB attenuator', 0.0, 2.0, 11.0, 13.0, -22.0, -8.0),
    ('a long span at the edge', 0.0, 2.0, 25.0, 33.0, -22.0, -8.0),
    ('a path that varies more than the window', 0.0, 2.0, 2.0, 20.0, -22.0, -8.0),
]


def analyse():
    return {'cases': [dict(evaluate(*c[1:]), name=c[0]) for c in CASES],
            'reserve_separate': reserve(),
            'reserve_already_counted': reserve(already_in_loss_max=True)}


def report(a):
    print('Optical POWER budget, worked at both extremes. No transponder, fibre')
    print('or power meter --- arithmetic on figures you supply.\n')
    print('%42s | %8s | %8s | %7s | %s'
          % ('case', 'Rx max', 'Rx min', 'margin', 'verdict'))
    print('-' * 118)
    for c in a['cases']:
        print('%42s | %7.1f  | %7.1f  | %6.2f  | %s'
              % (c['name'], c['rx_max_dbm'], c['rx_min_dbm'],
                 c['worst_case_margin_db'], verdict_short(c)))
    print('\nFour of those are the four ways a power budget fails, shown')
    print('deliberately. The two that pass are the same path: the short patch')
    print('works once somebody fits the attenuator, which is the fix that feels')
    print('absurd until you have debugged a link that fails for being too loud.')

    hot = next(c for c in a['cases'] if '+10' in c['name'])
    print('\nThe second case is the one the previous version of this lab got')
    print('wrong. Its received power is %+.1f dBm against an overload point of'
          % hot['rx_max_dbm'])
    print('%+.1f, so the receiver is driven %.1f dB past its maximum input ---'
          % (hot['overload_dbm'], hot['rx_max_dbm'] - hot['overload_dbm']))
    print('and its margin over SENSITIVITY is a comfortable %.1f dB. The old'
          % hot['worst_case_margin_db'])
    print('verdict looked only at that second number and reported the link OK.')
    print('Here every condition has to hold, and this one does not:\n')
    for cond in hot['conditions']:
        print('    %-36s %+7.2f dB  %s'
              % (cond['name'], cond['value_db'],
                 'ok' if cond['passes'] else 'FAILS'))

    wide = next(c for c in a['cases'] if 'varies more' in c['name'])
    print('\nThe last case fails a condition a midpoint target cannot even')
    print('express: the path varies by %.1f dB and the receiver accepts only'
          % wide['spread_db'])
    print('%.1f, so there is NO transmitter power that satisfies both ends.'
          % wide['window_db'])
    print('You attenuate the short case, or you use a receiver with a wider')
    print('window, or you accept that one of them will not work.')

    s, c = a['reserve_separate'], a['reserve_already_counted']
    print('\nThe reserve, and the trap in it:')
    print('    if the maximum loss is a commissioning figure: %.1f dB (%s)'
          % (s['total_db'], ', '.join(s['counted'])))
    print('    if it already carries ageing and repairs:      %.1f dB (%s)'
          % (c['total_db'], ', '.join(c['counted'])))
    print('Choose one convention. Counting the same decibels in both the loss')
    print('figure and the reserve is not caution --- it is an error that buys')
    print('equipment nobody needed and can make a workable span look impossible.')

    print('\nAnd the sentence this lab will not print: none of the above says')
    print('the link WORKS. It says the light arrives inside the window the')
    print('receiver can accept. On a coherent link what decides whether the')
    print('data comes back is the OSNR budget, which is Lab 44.2, and a')
    print('comfortable power margin tells you nothing about it.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        a = analyse()
    except BudgetError as e:
        print('budget error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(a, indent=2))
    else:
        report(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
