#!/usr/bin/env python3
"""Lab 41.3 --- when a more expensive fabric is the cheaper fabric.

WHY THIS EXISTS
---------------
Chapter 41 used to settle the InfiniBand-versus-Ethernet question with three
figures --- a fabric cost per GPU-hour for each of three options --- and a rule
of thumb that a communication-to-compute ratio above about 25% justified the
premium.  Neither survives contact with the arithmetic.

The three costs had no derivation, and the rule of thumb is not the break-even
condition.  The ratio of communication to compute tells you how much of the
wall-clock is exposed to the fabric.  It does not tell you how much of THAT the
better fabric takes away, and the money turns entirely on the second number.  A
job that spends 40% of its time on the network gains nothing from a fabric that
is faster at something the job never does.

This script states the condition instead, and lets you put your own numbers
into it.  Every figure below is an ILLUSTRATIVE INPUT, not a market price: no
vendor quotation, price list or benchmark was available when this was written,
and none is implied.  Replace them with quotations you actually hold.

THE CONDITION
-------------
Two fabrics, A (dearer, faster) and B.  Per GPU-hour:

    g    all-in cost of a GPU and the machine around it, excluding the fabric
    f_A  fabric cost, option A
    f_B  fabric cost, option B
    c    fraction of wall-clock the job spends waiting on fabric B
    s    fraction of THAT waiting which fabric A removes

A step that takes T_B on fabric B takes T_B(1 - c*s) on A.  Cost per unit of
work is (g + f)*T, so A is cheaper per unit of work when

    (g + f_A) * (1 - c*s)  <  (g + f_B)

which rearranges to the break-even rule:

    f_A - f_B  <  (g + f_A) * c * s
    ^premium^      ^^^^ what the saved time is worth ^^^^

Read it out loud: the premium has to be smaller than the total hourly cost of
everything you are keeping busy, multiplied by the fraction of the wall-clock
you actually remove.  The communication-to-compute ratio is only one of the two
factors on the right, which is why it cannot decide this on its own.

    python3 fabric_breakeven.py
    python3 fabric_breakeven.py --json
    python3 test_fabric_breakeven.py

No device, no benchmark, no vendor data. Arithmetic on inputs you supply.
"""
import argparse
import json
import sys


class CostError(ValueError):
    """The inputs do not describe a comparison that can be made."""


def check(gpu_hourly, fabric_a, fabric_b, comm_fraction, speedup_fraction):
    if gpu_hourly < 0 or fabric_a < 0 or fabric_b < 0:
        raise CostError('costs must not be negative')
    if not 0 <= comm_fraction <= 1:
        raise CostError('the communication fraction must be between 0 and 1, '
                        'got %r' % (comm_fraction,))
    if not 0 <= speedup_fraction <= 1:
        raise CostError('the removed fraction must be between 0 and 1, '
                        'got %r' % (speedup_fraction,))


def compare(gpu_hourly, fabric_a, fabric_b, comm_fraction, speedup_fraction):
    """Is fabric A cheaper per unit of work than fabric B?

    Returns the premium, what the saved time is worth, and the verdict, plus
    the break-even values of each input with the others held fixed --- which is
    usually more useful than the verdict, because it tells you how wrong an
    assumption has to be before the answer flips.
    """
    check(gpu_hourly, fabric_a, fabric_b, comm_fraction, speedup_fraction)
    premium = fabric_a - fabric_b
    removed = comm_fraction * speedup_fraction       # fraction of wall-clock
    worth = (gpu_hourly + fabric_a) * removed
    # cost per unit of work, normalising fabric B's step time to 1
    cost_b = gpu_hourly + fabric_b
    cost_a = (gpu_hourly + fabric_a) * (1 - removed)
    out = {
        'gpu_hourly': gpu_hourly,
        'fabric_a': fabric_a,
        'fabric_b': fabric_b,
        'comm_fraction': comm_fraction,
        'speedup_fraction': speedup_fraction,
        'wallclock_removed': removed,
        'premium': premium,
        'saved_time_worth': worth,
        'cost_per_work_a': cost_a,
        'cost_per_work_b': cost_b,
        'a_is_cheaper': cost_a < cost_b,
        'margin': cost_b - cost_a,
        # how far each input can move before the answer changes
        'breakeven_removed': (premium / (gpu_hourly + fabric_a)
                              if gpu_hourly + fabric_a > 0 else None),
        'breakeven_premium': worth,
    }
    if removed > 0:
        out['breakeven_speedup'] = min(
            1.0, (premium / (gpu_hourly + fabric_a)) / comm_fraction) \
            if comm_fraction > 0 else None
    else:
        out['breakeven_speedup'] = None
    return out


def ratio_is_not_the_rule(gpu_hourly, fabric_a, fabric_b, comm_fraction):
    """Hold the communication ratio fixed and vary only what A removes.

    The old rule of thumb said a ratio above roughly 25% justified the premium.
    This sweep holds the ratio at whatever you pass and shows the answer
    flipping anyway, which is the point: the ratio alone does not decide it.
    """
    rows = []
    for s in (0.0, 0.1, 0.25, 0.5, 0.75, 1.0):
        rows.append(compare(gpu_hourly, fabric_a, fabric_b, comm_fraction, s))
    return rows


# --------------------------------------------------------------------------
# Illustrative inputs. NOT PRICES. Replace with quotations you hold.
# --------------------------------------------------------------------------
ILLUSTRATIVE = {
    'gpu_hourly': 2.00,      # one GPU and its share of the machine, per hour
    'fabric_a': 0.30,        # the dearer fabric, per GPU-hour
    'fabric_b': 0.10,        # the cheaper fabric, per GPU-hour
}


def analyse(**over):
    p = dict(ILLUSTRATIVE)
    p.update(over)
    scenarios = [
        ('communication-light job', 0.10, 0.40),
        ('the old rule of thumb\'s threshold', 0.25, 0.40),
        ('communication-heavy job', 0.45, 0.40),
        ('heavy job, fabric barely helps', 0.45, 0.05),
        ('light job, fabric helps hugely', 0.10, 0.90),
    ]
    return {
        'inputs': p,
        'scenarios': [dict(compare(p['gpu_hourly'], p['fabric_a'],
                                   p['fabric_b'], c, s), label=label)
                      for label, c, s in scenarios],
        'fixed_ratio_sweep': ratio_is_not_the_rule(
            p['gpu_hourly'], p['fabric_a'], p['fabric_b'], 0.25),
    }


def report(a):
    p = a['inputs']
    print('Fabric break-even. ILLUSTRATIVE INPUTS, not prices: no vendor')
    print('quotation or benchmark was available. Substitute your own.\n')
    print('  GPU and machine, per GPU-hour      %6.2f' % p['gpu_hourly'])
    print('  fabric A (dearer), per GPU-hour    %6.2f' % p['fabric_a'])
    print('  fabric B (cheaper), per GPU-hour   %6.2f' % p['fabric_b'])
    print('  premium to justify                 %6.2f\n'
          % (p['fabric_a'] - p['fabric_b']))

    print('%34s | %5s | %5s | %8s | %8s | %s'
          % ('scenario', 'comm', 'saved', 'wall-clk', 'worth', 'buy A?'))
    print('-' * 88)
    for r in a['scenarios']:
        print('%34s | %4.0f%% | %4.0f%% | %7.1f%% | %8.3f | %s'
              % (r['label'], r['comm_fraction'] * 100,
                 r['speedup_fraction'] * 100, r['wallclock_removed'] * 100,
                 r['saved_time_worth'], 'yes' if r['a_is_cheaper'] else 'no'))

    print('\nRows three and four have the SAME communication-to-compute ratio')
    print('and opposite answers. Rows two and five have opposite ratios and')
    print('the same answer. A ratio on its own decides nothing.')

    print('\nHolding the ratio at 25% --- the old rule of thumb\'s threshold ---')
    print('and varying only how much of the waiting fabric A removes:\n')
    print('%22s | %8s | %8s | %s'
          % ('fabric A removes', 'wall-clk', 'worth', 'buy A?'))
    print('-' * 58)
    for r in a['fixed_ratio_sweep']:
        print('%21.0f%% | %7.1f%% | %8.3f | %s'
              % (r['speedup_fraction'] * 100, r['wallclock_removed'] * 100,
                 r['saved_time_worth'], 'yes' if r['a_is_cheaper'] else 'no'))

    be = a['scenarios'][1]['breakeven_removed']
    print('\nAt these costs the premium is worth paying once fabric A removes')
    print('%.2f%% of the wall-clock, however that arises. That single number ---'
          % (be * 100))
    print('not a ratio, and not a benchmark headline --- is what a fabric')
    print('proposal has to establish, and it is the number vendors are least')
    print('willing to state for YOUR workload.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--gpu-hourly', type=float, default=ILLUSTRATIVE['gpu_hourly'])
    ap.add_argument('--fabric-a', type=float, default=ILLUSTRATIVE['fabric_a'])
    ap.add_argument('--fabric-b', type=float, default=ILLUSTRATIVE['fabric_b'])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        a = analyse(gpu_hourly=args.gpu_hourly, fabric_a=args.fabric_a,
                    fabric_b=args.fabric_b)
    except CostError as e:
        print('cost error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(a, indent=2))
    else:
        report(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
