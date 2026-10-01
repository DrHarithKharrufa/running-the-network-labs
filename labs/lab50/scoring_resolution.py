#!/usr/bin/env python3
"""Lab 50.3 --- how much of a risk ranking is real.

WHY THIS LAB EXISTS
-------------------
The chapter says risk is likelihood times impact, that the formula is trivial,
and that the practice is where it goes wrong.  It then warns about the register
where everything drifts to "high".  A product of ordinal ranks is a prioritisation convention, not expected
loss. The following resolution problem concerns that convention:

    A 3x3 ordinal scale has nine cells and only SIX distinct products.

So a register larger than six entries must contain a tie, and the "ranked gap list" the chapter
asks for --- the thing it calls the output that matters --- is, for most of its
length, not ranked at all.  It is in whatever order the rows were typed, or
whatever order the spreadsheet's sort left them in, and nobody notices because
the risk column looks like a number.

Three consequences, all arithmetic, none requiring any data:

  THE VALUES ARE NOT EVENLY SPACED.  The six products are 1, 2, 3, 4, 6, 9.
  Moving one rank up the register means +1 at the bottom and +3 at the top, so
  the same "one step worse" is three different sizes depending where you stand.
  Differences between risk scores are not magnitudes and must not be summed,
  averaged or budgeted against, which is exactly what a register is used for.

  THE ORDERING HAS ANOMALIES YOU WOULD NOT ACCEPT IF STATED PLAINLY.  Rare and
  catastrophic (1x3) ties with continuous and trivial (3x1) at 3, and BOTH are
  outranked by moderate-moderate (2x2) at 4.  Written out, few people would
  agree to that policy.  Multiplying puts it in place silently.

  THE TIE-BREAK IS THE POLICY.  Once a third of your register sits on one value,
  whatever breaks the tie decides what gets funded.  If you have not written a
  tie-break down, the sort order has chosen one for you.  Section D prices the
  two obvious choices and they give different answers, which is the proof that
  it is a choice.

    python3 scoring_resolution.py
    python3 scoring_resolution.py --json
    python3 test_scoring_resolution.py

Everything here is exact combinatorics over a stated scale. There is no
sampling, no random number and no fitted model anywhere in this file: the
expectations are computed by enumeration, not estimated.  What IS a stated input
is how register items are assumed to be spread over the cells, and Section C
runs two stated spreads to show sensitivity. Actual tie prevalence depends
on the register size and distribution; it is not universal.
"""
import argparse
import json
import textwrap
import sys
from fractions import Fraction
from itertools import product


# Short glosses for the 3-point impact scale, so that the report can describe
# an ordering anomaly in words instead of asserting one. These are kept in step
# with threat_model.py's IMPACT_SCALE by a check in test_scoring_resolution.py.
IMPACT_GLOSS = {
    1: 'one device or service degraded',
    2: 'a site or customer-facing service lost',
    3: 'control of infrastructure others depend on',
}


class ScaleError(ValueError):
    """The described scale or register cannot be evaluated."""


# ---------------------------------------------------------------------------
# the scale itself
# ---------------------------------------------------------------------------
def cells(n):
    """Every (likelihood, impact) pair on an n-point scale."""
    if n < 2:
        raise ScaleError('a scale needs at least two points, got %r' % n)
    return [(l, i) for l in range(1, n + 1) for i in range(1, n + 1)]


def products(n):
    """Distinct likelihood x impact values on an n-point scale, ascending."""
    return sorted({l * i for l, i in cells(n)})


def value_counts(n):
    """How many of the n^2 cells land on each distinct product."""
    out = {}
    for l, i in cells(n):
        out[l * i] = out.get(l * i, 0) + 1
    return dict(sorted(out.items()))


def resolution(n):
    """The headline: cells, distinct values, and the ratio between them."""
    c = n * n
    v = len(products(n))
    return {'scale': n, 'cells': c, 'distinct_values': v,
            'cells_per_value': round(c / v, 3),
            'collapse_pct': round(100.0 * (c - v) / c, 1)}


def spacing(n):
    """Gaps between consecutive distinct values --- and whether they are equal."""
    p = products(n)
    gaps = [p[i + 1] - p[i] for i in range(len(p) - 1)]
    return {'values': p, 'gaps': gaps, 'even': len(set(gaps)) == 1,
            'smallest_gap': min(gaps), 'largest_gap': max(gaps)}


def collisions(n):
    """Cells that share a product, grouped --- the ties built into the scale."""
    out = {}
    for l, i in cells(n):
        out.setdefault(l * i, []).append((l, i))
    return {v: g for v, g in sorted(out.items()) if len(g) > 1}


def ordering_anomalies(n):
    """Pairs where a lower product holds a strictly higher impact.

    The case the chapter's formula creates and never states: a rare
    catastrophe scoring below a moderate-moderate.
    """
    out = []
    for (l1, i1), (l2, i2) in product(cells(n), repeat=2):
        if l1 * i1 < l2 * i2 and i1 > i2:
            out.append({'outranked': {'likelihood': l1, 'impact': i1,
                                      'product': l1 * i1},
                        'outranks': {'likelihood': l2, 'impact': i2,
                                     'product': l2 * i2}})
    return out


# ---------------------------------------------------------------------------
# what a register of N items looks like on that scale --- exactly
# ---------------------------------------------------------------------------
UNIFORM = 'uniform over cells'
SKEWED = 'skewed towards high impact, as a real register is'


def cell_weights(n, spread=UNIFORM):
    """Probability of a register item landing on each cell. A stated input."""
    cs = cells(n)
    if spread == UNIFORM:
        w = {c: Fraction(1, len(cs)) for c in cs}
    elif spread == SKEWED:
        # impact weighted by its own value, likelihood flat: the documented
        # tendency for people to score impact high. Still a stated input.
        tot = sum(i for _, i in cs)
        w = {c: Fraction(c[1], tot) for c in cs}
    else:
        raise ScaleError('unknown spread %r' % spread)
    assert sum(w.values()) == 1
    return w


def value_weights(n, spread=UNIFORM):
    """Probability of an item landing on each distinct PRODUCT value."""
    out = {}
    for c, p in cell_weights(n, spread).items():
        v = c[0] * c[1]
        out[v] = out.get(v, Fraction(0)) + p
    return dict(sorted(out.items()))


def expected_distinct(n, items, spread=UNIFORM):
    """Expected number of distinct risk values a register of `items` shows.

    Exact: sum over values of the probability that at least one item lands on
    it. No sampling.
    """
    if items < 1:
        raise ScaleError('a register needs at least one item, got %r' % items)
    total = Fraction(0)
    for _, p in value_weights(n, spread).items():
        total += 1 - (1 - p) ** items
    return float(total)


def _compositions(total, parts):
    """Every way to split `total` items across `parts` values."""
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in _compositions(total - first, parts - 1):
            yield (first,) + rest


def _multinomial(counts):
    from math import factorial
    n = sum(counts)
    d = 1
    for c in counts:
        d *= factorial(c)
    return factorial(n) // d


def tie_statistics_by_enumeration(n, items, spread=UNIFORM):
    """The same three figures, by enumerating every allocation.

    Correct, obvious, and factorially slow: the number of allocations is
    C(items + values - 1, values - 1), which passes a billion well before a
    register gets interesting. It is kept because it is the version a reader
    can check by eye, and because test_scoring_resolution.py runs it against
    the fast path below for small cases. Do not call it with a large register.
    """
    if items < 1:
        raise ScaleError('a register needs at least one item, got %r' % items)
    vw = value_weights(n, spread)
    vals = sorted(vw)
    probs = [vw[v] for v in vals]
    e_largest = Fraction(0)
    p_unique_top = Fraction(0)
    e_tied_items = Fraction(0)
    for counts in _compositions(items, len(vals)):
        p = Fraction(_multinomial(counts))
        for c, pr in zip(counts, probs):
            if c:
                p *= pr ** c
        if p == 0:
            continue
        e_largest += p * max(counts)
        e_tied_items += p * sum(c for c in counts if c > 1)
        top = max((i for i, c in enumerate(counts) if c), default=None)
        if top is not None and counts[top] == 1:
            p_unique_top += p
    return {'expected_largest_tie_group': float(e_largest),
            'p_unique_worst_item': float(p_unique_top),
            'expected_items_in_a_tie': float(e_tied_items),
            'expected_share_tied': float(e_tied_items / items)}


def _expected_items_in_a_tie(probs, items):
    """Exact, in closed form.

    An item is "in a tie" when at least one other item shares its value, so the
    expected number is the expected total minus the expected number of values
    holding exactly one item:

        E[tied] = sum_v ( items*p_v - items*p_v*(1-p_v)^(items-1) )

    because E[count_v] = items*p_v and the only untied case is count_v = 1.
    """
    total = Fraction(0)
    for p in probs:
        total += items * p * (1 - (1 - p) ** (items - 1))
    return total


def _p_unique_worst(probs, items):
    """Exact: P(exactly one item on the highest OCCUPIED value).

    Sum over values v of P(one item on v, every other item below v), which is
    items * p_v * (P(below v))^(items-1). The events are disjoint because a
    register has one highest occupied value.
    """
    total = Fraction(0)
    below = Fraction(0)
    for p in probs:                      # probs must be in ascending value order
        total += items * p * below ** (items - 1) if items > 1 else p
        below += p
    return total


def _expected_largest(probs, items):
    """Exact E[max count], by dynamic programming over the values.

    Accumulates sum over allocations of prod(p_i^c_i / c_i!), keyed by (items
    placed, largest count so far); multiplying by items! at the end turns it
    into the multinomial probability. Cost is O(values * items^3), which is
    nothing, against the factorial cost of enumerating allocations.
    """
    from math import factorial
    inv = [Fraction(1, factorial(c)) for c in range(items + 1)]
    # state[(placed, largest)] = weight
    state = {(0, 0): Fraction(1)}
    for p in probs:
        nxt = {}
        for (placed, largest), w in state.items():
            room = items - placed
            pw = Fraction(1)
            for c in range(room + 1):
                if c:
                    pw *= p
                key = (placed + c, largest if largest > c else c)
                nxt[key] = nxt.get(key, Fraction(0)) + w * pw * inv[c]
        state = nxt
    total = Fraction(0)
    f = factorial(items)
    for (placed, largest), w in state.items():
        if placed == items:
            total += w * f * largest
    return total


def tie_statistics(n, items, spread=UNIFORM):
    """Exact expected largest tie group, share tied, and P(a unique worst item).

    Closed form for two of the three and a dynamic program for the largest tie
    group. No sampling, no random number, no approximation: every figure is a
    rational computed exactly and converted to a float only on the way out.
    test_scoring_resolution.py checks all three against the enumeration above.
    """
    if items < 1:
        raise ScaleError('a register needs at least one item, got %r' % items)
    vw = value_weights(n, spread)
    probs = [vw[v] for v in sorted(vw)]      # ascending value order matters
    tied = _expected_items_in_a_tie(probs, items)
    return {'expected_largest_tie_group': float(_expected_largest(probs, items)),
            'p_unique_worst_item': float(_p_unique_worst(probs, items)),
            'expected_items_in_a_tie': float(tied),
            'expected_share_tied': float(tied / items)}


# ---------------------------------------------------------------------------
# tie-breaks, which are policies
# ---------------------------------------------------------------------------
def tie_break_orders(n):
    """Two defensible tie-breaks, and where they disagree.

    Both take the product first. They differ only on what settles a tie, and
    that difference is a policy about whether you fear the rare catastrophe or
    the constant nuisance.
    """
    cs = cells(n)
    impact_first = sorted(cs, key=lambda c: (-(c[0] * c[1]), -c[1], -c[0]))
    likelihood_first = sorted(cs, key=lambda c: (-(c[0] * c[1]), -c[0], -c[1]))
    disagreements = sum(1 for a, b in zip(impact_first, likelihood_first) if a != b)
    return {
        'impact_first': impact_first,
        'likelihood_first': likelihood_first,
        'positions_differing': disagreements,
        'top_five_impact_first': impact_first[:5],
        'top_five_likelihood_first': likelihood_first[:5],
    }


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def build_report(items=24):
    return {
        'items': items,
        'resolution': [resolution(k) for k in (3, 4, 5, 6, 10)],
        'spacing': spacing(3),
        'value_counts': value_counts(3),
        'collisions': {str(k): v for k, v in collisions(3).items()},
        'anomalies': ordering_anomalies(3),
        'registers': [
            {'items': m, 'spread': s,
             'expected_distinct': round(expected_distinct(3, m, s), 3),
             **{k: round(v, 4) for k, v in tie_statistics(3, m, s).items()}}
            for s in (UNIFORM, SKEWED) for m in (8, 12, 20)
        ],
        'scale_comparison': [
            {'scale': k, 'distinct_values': len(products(k)),
             'expected_distinct_at_20': round(expected_distinct(k, 20), 3),
             'share_tied_at_20': round(
                 tie_statistics(k, 20)['expected_share_tied'], 4),
             'anomalies': len(ordering_anomalies(k))}
            for k in (2, 3, 4, 5)
        ],
        'tie_breaks': tie_break_orders(3),
        'caveats': [
            'The combinatorics are exact and contain no sampling, no random '
            'number and no fitted model. The EXPECTATIONS assume register items '
            'are spread over the cells in a stated way, and two very different '
            'spreads are run so the conclusion can be seen not to depend on it.',
            'A real register is not a random draw. Items are correlated, and an '
            'estate with one bad habit produces many rows with the same score '
            'for a real reason --- which makes the tie problem worse, not '
            'better, because those rows genuinely need separating.',
            'Nothing here says a 3x3 scale is wrong. A coarse scale that people '
            'actually fill in beats a fine one they do not, which is the '
            'chapter\'s own argument about the timebox. It says the RANKING '
            'read off a coarse scale is mostly not there.',
            'Widening the scale buys resolution and costs agreement: the '
            'difference between a 6 and a 7 on a ten-point likelihood scale is '
            'not something two engineers will reliably reproduce.',
            'A tie-break is not a fix for a coarse scale. It is a statement of '
            'policy that a coarse scale forces you to make explicit, which is '
            'the only good news in this lab.',
        ],
    }


def _fmt_cell(c):
    return 'L%d x I%d' % c


def report_text(rep):
    L = []
    L.append('How much of a risk ranking is real (Chapter 50)')
    L.append('Exact combinatorics. No sampling and no random number anywhere.')
    L.append('')
    L.append('A. A 3x3 scale has nine cells and six values')
    L.append('-' * 74)
    L.append('%-8s %7s %9s %12s %10s' % ('scale', 'cells', 'distinct',
                                         'cells/value', 'collapse'))
    for r in rep['resolution']:
        L.append('%-8s %7d %9d %12.2f %9.1f%%'
                 % ('%dx%d' % (r['scale'], r['scale']), r['cells'],
                    r['distinct_values'], r['cells_per_value'], r['collapse_pct']))
    three = rep['resolution'][0]
    L.append('')
    L.append('  On the scale the chapter teaches, %d cells collapse to %d '
             'values --- %.1f'
             % (three['cells'], three['distinct_values'], three['collapse_pct']))
    L.append('  per cent of the distinctions you made when scoring are thrown '
             'away by the')
    L.append('  multiplication itself, before any two rows are compared.')
    L.append('')
    sp = rep['spacing']
    L.append('  And the values are not evenly spaced:')
    L.append('      values  %s' % ', '.join(str(v) for v in sp['values']))
    L.append('      gaps      %s' % ',  '.join(str(g) for g in sp['gaps']))
    L.append('  So "one rank worse" is %d at the bottom of the register and %d '
             'at the top.'
             % (sp['smallest_gap'], sp['largest_gap']))
    L.append('  A difference between two risk scores is therefore not a '
             'magnitude, and')
    L.append('  it cannot be summed, averaged, or set against a budget --- '
             'which is most')
    L.append('  of what a risk register is used for once it leaves the '
             'engineering team.')
    L.append('')
    L.append('B. The ordering the multiplication imposes, written out')
    L.append('-' * 74)
    for v, group in sorted(rep['collisions'].items(), key=lambda kv: int(kv[0])):
        L.append('  risk %-2s <- %s' % (v, ', '.join(_fmt_cell(tuple(c))
                                                     for c in group)))
    L.append('')
    an = rep['anomalies']
    L.append('  %d ordered pairs exist where the LOWER-scoring item has the '
             'HIGHER impact.' % len(an))
    for a in an[:4]:
        o, u = a['outranked'], a['outranks']
        L.append('    L%d x I%d = %d ranks BELOW L%d x I%d = %d'
                 % (o['likelihood'], o['impact'], o['product'],
                    u['likelihood'], u['impact'], u['product']))
    L.append('')
    # Describe the WORST anomaly, chosen from the data rather than assumed to
    # be the first one printed. The gap that matters is the impact gap.
    worst = max(an, key=lambda a: (a['outranked']['impact'] - a['outranks']['impact'],
                                   a['outranks']['product'] - a['outranked']['product']))
    o, u = worst['outranked'], worst['outranks']
    L.append('  The widest of them is the one to read aloud as a policy. An '
             'item at')
    L.append('  likelihood %d and impact %d scores %d, and is outranked by one '
             'at likelihood'
             % (o['likelihood'], o['impact'], o['product']))
    d = o['impact'] - u['impact']
    L.append('  %d and impact %d scoring %d --- so the item with %d more '
             '%s of impact is'
             % (u['likelihood'], u['impact'], u['product'], d,
                'point' if d == 1 else 'points'))
    L.append('  funded second. Put the scale back into the sentence:')
    L.append('      impact %d  %s'
             % (o['impact'], IMPACT_GLOSS.get(o['impact'], '?')))
    L.append('      impact %d  %s'
             % (u['impact'], IMPACT_GLOSS.get(u['impact'], '?')))
    L.append('  and the register funds the second before the first. Few '
             'people would')
    L.append('  sign that if it were written on the page. Multiplying two '
             'ordinals puts')
    L.append('  it in place without anyone deciding it.')
    L.append('')
    L.append('C. What that does to a register, exactly')
    L.append('-' * 74)
    L.append('%-34s %6s %9s %9s %8s' % ('spread', 'items', 'distinct',
                                        'largest', 'tied'))
    for r in rep['registers']:
        L.append('%-34s %6d %9.2f %9.2f %7.0f%%'
                 % (r['spread'][:34], r['items'], r['expected_distinct'],
                    r['expected_largest_tie_group'],
                    100.0 * r['expected_share_tied']))
    u20 = next(r for r in rep['registers']
               if r['items'] == 20 and r['spread'].startswith('uniform'))
    s20 = next(r for r in rep['registers']
               if r['items'] == 20 and not r['spread'].startswith('uniform'))
    L.append('')
    L.append('  A 20-item register spread evenly shows %.1f distinct risk '
             'values, has an'
             % u20['expected_distinct'])
    L.append('  expected largest tie group of %.1f rows, and %.0f per cent of '
             'its rows are'
             % (u20['expected_largest_tie_group'],
                100.0 * u20['expected_share_tied']))
    L.append('  tied with something. Skew it towards high impact, the way real '
             'registers')
    L.append('  go, and it is %.1f distinct values with %.0f per cent tied. '
             'The conclusion'
             % (s20['expected_distinct'], 100.0 * s20['expected_share_tied']))
    L.append('  does not depend on the spread, which is why both are here.')
    L.append('')
    L.append('  The probability that the WORST item is uniquely worst --- that '
             'the top of')
    L.append('  your gap list is a single row rather than a tie you broke '
             'silently --- is')
    L.append('  %.0f per cent evenly spread and %.0f per cent skewed.'
             % (100.0 * u20['p_unique_worst_item'],
                100.0 * s20['p_unique_worst_item']))
    L.append('')
    L.append('  Widening the scale helps, and it costs something the '
             'resolution column')
    L.append('  hides:')
    L.append('')
    L.append('    %-7s %9s %9s %7s %10s' % ('scale', 'distinct', 'seen@20',
                                            'tied@20', 'anomalies'))
    for r in rep['scale_comparison']:
        L.append('    %-7s %9d %9.1f %6.0f%% %10d'
                 % ('%dx%d' % (r['scale'], r['scale']), r['distinct_values'],
                    r['expected_distinct_at_20'],
                    100.0 * r['share_tied_at_20'], r['anomalies']))
    L.append('')
    L.append('  Read the last column. The ordering anomalies of Section B do '
             'not go away')
    L.append('  with a finer scale --- there are none at all on a 2x2, three '
             'on the 3x3')
    L.append('  the chapter teaches, and they grow faster than the resolution '
             'does. A')
    L.append('  finer scale separates more rows AND misorders more pairs, so '
             '"use a wider')
    L.append('  scale" is a trade rather than a fix, and the thing it trades '
             'away is the')
    L.append('  one nobody checks.')
    L.append('')
    L.append('D. The tie-break is the policy, and you are making it either way')
    L.append('-' * 74)
    tb = rep['tie_breaks']
    L.append('  Two defensible rules. Both take the product first; they differ '
             'only on')
    L.append('  what settles a tie.')
    L.append('')
    L.append('  impact first:     %s'
             % ', '.join(_fmt_cell(tuple(c)) for c in tb['top_five_impact_first']))
    L.append('  likelihood first: %s'
             % ', '.join(_fmt_cell(tuple(c)) for c in tb['top_five_likelihood_first']))
    L.append('')
    L.append('  They disagree on %d of the %d positions. "Impact first" funds '
             'the rare'
             % (tb['positions_differing'], len(tb['impact_first'])))
    L.append('  catastrophe; "likelihood first" funds the constant nuisance. '
             'Both are')
    L.append('  reasonable and they are not the same network strategy.')
    L.append('')
    L.append('  If your register does not state which it uses, it is still '
             'using one:')
    L.append('  whatever your sort left in place, which is usually the order '
             'the rows')
    L.append('  were typed in. The good news in this lab is the only good news '
             'in it ---')
    L.append('  a coarse scale forces the policy into the open, where somebody '
             'can be')
    L.append('  asked to own it.')
    L.append('')
    L.append('What this does NOT establish')
    L.append('-' * 74)
    for c in rep['caveats']:
        L.extend(textwrap.wrap(c, width=74, initial_indent='- ',
                               subsequent_indent='  '))
    return '\n'.join(L)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--json', action='store_true', help='emit the report as JSON')
    p.add_argument('--items', type=int, default=24)
    a = p.parse_args(argv)
    try:
        rep = build_report(a.items)
    except ScaleError as exc:
        print('cannot evaluate: %s' % exc, file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=2) if a.json else report_text(rep))
    return 0


if __name__ == '__main__':
    sys.exit(main())
