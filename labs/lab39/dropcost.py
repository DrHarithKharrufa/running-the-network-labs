#!/usr/bin/env python3
"""Lab 39.1 --- a HYPOTHETICAL cost model, and the honest limits of one.

WHAT THIS IS. Arithmetic on numbers you supply, comparing two idealised costs:
walking a linear rule chain to its LAST rule, versus one assumed constant-time
map lookup. It shows how a linear term and a constant term diverge. That is all
it shows.

WHAT THIS IS NOT. It is not a measurement, and the constants are not measured
values --- they are placeholders you should replace. The previous version of this
script shipped invented nanosecond constants, multiplied them out to a "30015x
speedup" and "25 million drops/sec", and presented those as the reason DDoS
scrubbing is done in XDP. Model arithmetic does not establish packets per
second. If you want a rate, benchmark one; Lab 39.2 shows you the real
mechanism, and deliberately reports no rate either, because generic-mode XDP on
a veth cannot produce a meaningful one.

WHAT THE MODEL LEAVES OUT, all of which moves the answer:

  * Early matches. A chain whose first rule matches costs one rule, not N.
    The linear term is a WORST case, and real traffic is not the worst case.
  * Set-based matching. ipset and nftables sets do not walk linearly; a modern
    nftables ruleset with a set lookup is much closer to the constant-time
    column than to the linear one. Comparing XDP against a worst-case linear
    iptables chain and calling that "the alternative" is a straw man.
  * Map type and cache behaviour. A hash-map lookup is constant in the number
    of entries and not constant in time: it depends on the map type, the size
    of the working set and whether it is in cache.
  * Parsing and driver cost. The lookup is not the whole program. Parsing,
    the driver path and the XDP mode all cost something.
  * What happens under attack. Both sides behave differently at load than at
    idle, which is exactly when you care.

    python3 dropcost.py [--rule-ns N] [--lookup-ns N] [--stack-ns N] [--json]
"""
import argparse
import json
import sys

# PLACEHOLDERS. Not measurements. Replace them with figures from your own
# benchmark before drawing any conclusion about your own system.
DEFAULT_RULE_NS = 12.0
DEFAULT_STACK_NS = 600.0
DEFAULT_LOOKUP_NS = 40.0


def linear_worst_case_ns(rules, rule_ns, stack_ns):
    """Cost of a packet that matches the LAST rule of a linear chain, after
    paying to reach the chain at all. Worst case by construction."""
    return stack_ns + rules * rule_ns


def constant_lookup_ns(lookup_ns):
    """Cost of one assumed constant-time lookup before the stack. The number of
    entries does not appear, which is the whole point of the comparison."""
    return lookup_ns


def model(rules, rule_ns=DEFAULT_RULE_NS, stack_ns=DEFAULT_STACK_NS,
          lookup_ns=DEFAULT_LOOKUP_NS):
    for n in (rules,):
        if not isinstance(n, int) or n < 1:
            raise ValueError('rule count must be a positive integer')
    for name, v in (('rule_ns', rule_ns), ('stack_ns', stack_ns),
                    ('lookup_ns', lookup_ns)):
        if not isinstance(v, (int, float)) or v <= 0:
            raise ValueError(name + ' must be a positive number')
    lin = linear_worst_case_ns(rules, rule_ns, stack_ns)
    con = constant_lookup_ns(lookup_ns)
    return {'rules': rules, 'linear_worst_case_ns': lin, 'constant_ns': con,
            'ratio': lin / con,
            'early_match_ns': stack_ns + rule_ns,
            'ratio_if_first_rule_matches': (stack_ns + rule_ns) / con}


def report(rule_ns, stack_ns, lookup_ns):
    print('HYPOTHETICAL model. The constants below are placeholders, not '
          'measurements.\n')
    print('  cost of evaluating one rule      : %g ns' % rule_ns)
    print('  cost of reaching the chain       : %g ns' % stack_ns)
    print('  cost of one constant-time lookup : %g ns\n' % lookup_ns)
    print('%12s | %14s | %12s | %8s | %16s'
          % ('entries', 'linear WORST', 'constant', 'ratio', 'ratio if FIRST'))
    print('-' * 76)
    rows = []
    for n in (10, 100, 1000, 10000, 100000):
        m = model(n, rule_ns, stack_ns, lookup_ns)
        rows.append(m)
        print('%12s | %14.0f | %12.0f | %7.0fx | %15.1fx'
              % ('{:,}'.format(n), m['linear_worst_case_ns'], m['constant_ns'],
                 m['ratio'], m['ratio_if_first_rule_matches']))
    print('\nThe last column is the same model when the FIRST rule matches. It '
          'barely\nmoves with the entry count, which is the point: the linear '
          'term only dominates\nwhen the match is late, and a set-based ruleset '
          'does not have a linear term at all.')
    print('\nNo packets-per-second figure is printed here, because none was '
          'measured.\nThis model cannot produce one. Lab 39.2 runs the real '
          'mechanism and also\nreports no rate, for the same reason.')
    return rows


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--rule-ns', type=float, default=DEFAULT_RULE_NS)
    p.add_argument('--stack-ns', type=float, default=DEFAULT_STACK_NS)
    p.add_argument('--lookup-ns', type=float, default=DEFAULT_LOOKUP_NS)
    p.add_argument('--json', action='store_true')
    a = p.parse_args(argv)
    for name in ('rule_ns', 'stack_ns', 'lookup_ns'):
        if getattr(a, name) <= 0:
            p.error('--%s must be positive' % name.replace('_', '-'))
    rows = report(a.rule_ns, a.stack_ns, a.lookup_ns)
    if a.json:
        print(json.dumps({'scope': 'hypothetical model; constants are placeholders, '
                                   'not measurements; no rate is implied',
                          'constants_ns': {'rule': a.rule_ns, 'stack': a.stack_ns,
                                           'lookup': a.lookup_ns},
                          'rows': rows}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
