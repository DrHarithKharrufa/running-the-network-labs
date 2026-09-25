#!/usr/bin/env python3
"""Checks for scoring_resolution.py.

Everything this lab claims is exact combinatorics, so the tests are exact too:
the distinct-value counts are checked against hand-enumerated answers, the
expected-distinct figure is checked against an independently written closed
form, and the tie statistics are checked against the total-probability identity
that any exact enumeration must satisfy. A Monte Carlo would not be able to
make these checks, which is one reason there is no sampling in the module.
"""
import json
import subprocess
import sys
from fractions import Fraction

import scoring_resolution as S

CHECKS = 0
FAILED = []


def check(label, cond):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except S.ScaleError:
        return True
    except Exception:
        return False
    return False


# ===========================================================================
# the scale, against hand-enumerated answers
# ===========================================================================
check('a 3-point scale has nine cells', len(S.cells(3)) == 9)
check('a 5-point scale has twenty-five cells', len(S.cells(5)) == 25)
check('cells are unique', len(set(S.cells(3))) == 9)
check('a 1-point scale is refused', raises(S.cells, 1))
check('a 0-point scale is refused', raises(S.cells, 0))
check('a negative scale is refused', raises(S.cells, -3))

check('the 3x3 products are exactly 1,2,3,4,6,9',
      S.products(3) == [1, 2, 3, 4, 6, 9])
check('there are six of them', len(S.products(3)) == 6)
check('the 4x4 products are hand-checkable',
      S.products(4) == [1, 2, 3, 4, 6, 8, 9, 12, 16])
check('the 2x2 products are 1,2,4', S.products(2) == [1, 2, 4])
check('products are ascending',
      all(S.products(5)[i] < S.products(5)[i + 1]
          for i in range(len(S.products(5)) - 1)))
check('the largest product is n squared', S.products(6)[-1] == 36)
check('the smallest product is one', S.products(6)[0] == 1)

vc = S.value_counts(3)
check('the cell counts sum to nine', sum(vc.values()) == 9)
check('value 1 has one cell', vc[1] == 1)
check('value 2 has two cells', vc[2] == 2)
check('value 3 has two cells', vc[3] == 2)
check('value 4 has one cell', vc[4] == 1)
check('value 6 has two cells', vc[6] == 2)
check('value 9 has one cell', vc[9] == 1)
check('every distinct product has a count',
      set(vc) == set(S.products(3)))

r3 = S.resolution(3)
check('resolution reports nine cells', r3['cells'] == 9)
check('resolution reports six values', r3['distinct_values'] == 6)
check('resolution reports a 33.3 per cent collapse',
      close(r3['collapse_pct'], 33.3, 1e-3))
check('collapse rises with scale size',
      S.resolution(10)['collapse_pct'] > S.resolution(3)['collapse_pct'])
check('cells per value is cells over values',
      close(r3['cells_per_value'], 9 / 6.0))
for n in (3, 4, 5, 6, 10):
    rr = S.resolution(n)
    check('resolution(%d) is internally consistent' % n,
          rr['cells'] == n * n and rr['distinct_values'] == len(S.products(n)))

# ===========================================================================
# spacing
# ===========================================================================
sp = S.spacing(3)
check('the gaps are 1,1,1,2,3', sp['gaps'] == [1, 1, 1, 2, 3])
check('the spacing is reported as uneven', sp['even'] is False)
check('the smallest gap is one', sp['smallest_gap'] == 1)
check('the largest gap is three', sp['largest_gap'] == 3)
check('the largest gap is three times the smallest',
      sp['largest_gap'] == 3 * sp['smallest_gap'])
check('a 2x2 scale is also uneven', S.spacing(2)['gaps'] == [1, 2])
check('the number of gaps is one less than the values',
      len(sp['gaps']) == len(sp['values']) - 1)

# ===========================================================================
# collisions and the ordering anomalies
# ===========================================================================
col = S.collisions(3)
check('three values collide on a 3x3 scale', len(col) == 3)
check('the colliding values are 2, 3 and 6', sorted(col) == [2, 3, 6])
check('value 3 is reached two ways', len(col[3]) == 2)
check('1x3 and 3x1 both reach 3', set(col[3]) == {(1, 3), (3, 1)})
check('no value collides more than twice on a 3x3 scale',
      all(len(g) == 2 for g in col.values()))
check('non-colliding values are excluded',
      all(v not in col for v in (1, 4, 9)))

an = S.ordering_anomalies(3)
check('the ordering anomalies exist', len(an) > 0)
check('there are three of them on a 3x3 scale', len(an) == 3)
check('in every anomaly the lower score has the higher impact',
      all(a['outranked']['impact'] > a['outranks']['impact'] and
          a['outranked']['product'] < a['outranks']['product'] for a in an))
check('the rare catastrophe outranked by moderate-moderate is among them',
      any(a['outranked'] == {'likelihood': 1, 'impact': 3, 'product': 3} and
          a['outranks'] == {'likelihood': 2, 'impact': 2, 'product': 4}
          for a in an))
check('a 2x2 scale has NO anomaly, so the fault arrives with the third point',
      len(S.ordering_anomalies(2)) == 0)
check('and it arrives at 3x3 rather than growing from nothing',
      len(S.ordering_anomalies(3)) == 3)
check('a finer scale has more anomalies, not fewer',
      len(S.ordering_anomalies(5)) > len(S.ordering_anomalies(3)))

# ===========================================================================
# weights, checked as exact rationals
# ===========================================================================
for spread in (S.UNIFORM, S.SKEWED):
    cw = S.cell_weights(3, spread)
    check('cell weights sum to exactly one (%s)' % spread[:8],
          sum(cw.values()) == Fraction(1))
    check('every cell weight is exact (%s)' % spread[:8],
          all(isinstance(v, Fraction) for v in cw.values()))
    check('every cell weight is positive (%s)' % spread[:8],
          all(v > 0 for v in cw.values()))
    vw = S.value_weights(3, spread)
    check('value weights sum to exactly one (%s)' % spread[:8],
          sum(vw.values()) == Fraction(1))
    check('value weights cover every product (%s)' % spread[:8],
          set(vw) == set(S.products(3)))
check('uniform weights are all equal',
      len(set(S.cell_weights(3, S.UNIFORM).values())) == 1)
check('skewed weights are not all equal',
      len(set(S.cell_weights(3, S.SKEWED).values())) > 1)
check('the skew favours higher impact',
      S.cell_weights(3, S.SKEWED)[(1, 3)] > S.cell_weights(3, S.SKEWED)[(1, 1)])
check('the skew does not favour higher likelihood',
      S.cell_weights(3, S.SKEWED)[(3, 1)] == S.cell_weights(3, S.SKEWED)[(1, 1)])
check('an unknown spread is refused', raises(S.cell_weights, 3, 'guesswork'))

# ===========================================================================
# expected distinct values, against an independent closed form
# ===========================================================================
def expected_distinct_independently(n, items, spread=S.UNIFORM):
    """E[distinct] = V - sum_v P(no item lands on v), written the other way up."""
    vw = S.value_weights(n, spread)
    missing = sum((1 - p) ** items for p in vw.values())
    return float(len(vw) - missing)


for n in (3, 4, 5):
    for m in (1, 2, 5, 12, 20):
        check('expected distinct agrees with the complement form (%d, %d)' % (n, m),
              close(S.expected_distinct(n, m),
                    expected_distinct_independently(n, m), 1e-9))
check('one item shows exactly one distinct value',
      close(S.expected_distinct(3, 1), 1.0))
check('expected distinct rises with register size',
      S.expected_distinct(3, 20) > S.expected_distinct(3, 5))
check('expected distinct never exceeds the number of values',
      S.expected_distinct(3, 10000) <= 6.0 + 1e-9)
check('and approaches it for a large register',
      S.expected_distinct(3, 200) > 5.99)
check('a finer scale shows more distinct values at the same size',
      S.expected_distinct(5, 20) > S.expected_distinct(3, 20))
check('a zero-item register is refused', raises(S.expected_distinct, 3, 0))
check('a negative register is refused', raises(S.expected_distinct, 3, -5))

# ===========================================================================
# tie statistics, against identities an exact enumeration must satisfy
# ===========================================================================
for m in (1, 2, 5, 10):
    t = S.tie_statistics(3, m)
    check('largest tie group is at least one (%d items)' % m,
          t['expected_largest_tie_group'] >= 1.0 - 1e-9)
    check('largest tie group never exceeds the register (%d items)' % m,
          t['expected_largest_tie_group'] <= m + 1e-9)
    check('items in a tie never exceed the register (%d items)' % m,
          t['expected_items_in_a_tie'] <= m + 1e-9)
    check('the share tied is a fraction (%d items)' % m,
          0.0 <= t['expected_share_tied'] <= 1.0 + 1e-9)
    check('the probability of a unique worst item is a probability (%d)' % m,
          0.0 <= t['p_unique_worst_item'] <= 1.0 + 1e-9)
    check('the share tied is the count over the register (%d items)' % m,
          close(t['expected_share_tied'], t['expected_items_in_a_tie'] / m, 1e-9))

# the fast path against the obvious slow one --- the strongest check here,
# because the two share no arithmetic: one enumerates every allocation and
# weights it by a multinomial, the other uses closed forms and a DP.
for n, sizes in ((3, (1, 2, 3, 4, 5, 6, 7)), (4, (1, 2, 3, 4, 5))):
    for m in sizes:
        for spread in (S.UNIFORM, S.SKEWED):
            fast = S.tie_statistics(n, m, spread)
            slow = S.tie_statistics_by_enumeration(n, m, spread)
            check('fast and enumerated agree for %dx%d, %d items, %s'
                  % (n, n, m, spread[:7]),
                  all(close(fast[k], slow[k], 1e-12) for k in fast))
check('the enumeration refuses an empty register',
      raises(S.tie_statistics_by_enumeration, 3, 0))

one = S.tie_statistics(3, 1)
check('one item is never tied', close(one['expected_items_in_a_tie'], 0.0))
check('one item is always uniquely worst', close(one['p_unique_worst_item'], 1.0))
check('one item has a largest group of one',
      close(one['expected_largest_tie_group'], 1.0))

two = S.tie_statistics(3, 2)
# P(both items on the same value) = sum_v p_v^2
p_same = float(sum(p * p for p in S.value_weights(3).values()))
check('two items tie with probability sum p_v squared',
      close(two['expected_items_in_a_tie'], 2.0 * p_same, 1e-9))
check('and the largest group is 1 + that probability',
      close(two['expected_largest_tie_group'], 1.0 + p_same, 1e-9))
check('P(unique worst) for two items is one minus the tie probability',
      close(two['p_unique_worst_item'], 1.0 - p_same, 1e-9))

check('ties get worse as the register grows',
      S.tie_statistics(3, 20)['expected_share_tied']
      > S.tie_statistics(3, 5)['expected_share_tied'])
check('a 20-item register is overwhelmingly tied',
      S.tie_statistics(3, 20)['expected_share_tied'] > 0.9)
check('the worst item is usually NOT uniquely worst',
      S.tie_statistics(3, 20)['p_unique_worst_item'] < 0.5)
check('the conclusion holds under the skewed spread too',
      S.tie_statistics(3, 20, S.SKEWED)['expected_share_tied'] > 0.9)
check('a finer scale ties less at the same size',
      S.tie_statistics(5, 20)['expected_share_tied']
      < S.tie_statistics(3, 20)['expected_share_tied'])
check('a zero-item register is refused', raises(S.tie_statistics, 3, 0))

# ===========================================================================
# tie-breaks
# ===========================================================================
tb = S.tie_break_orders(3)
check('both orders contain every cell',
      set(tb['impact_first']) == set(S.cells(3))
      and set(tb['likelihood_first']) == set(S.cells(3)))
check('both orders are total', len(tb['impact_first']) == 9)
check('the two orders disagree', tb['positions_differing'] > 0)
check('they disagree on six of nine positions', tb['positions_differing'] == 6)
check('both agree the worst cell is 3x3',
      tb['impact_first'][0] == (3, 3) and tb['likelihood_first'][0] == (3, 3))
check('both agree the least bad cell is 1x1',
      tb['impact_first'][-1] == (1, 1) and tb['likelihood_first'][-1] == (1, 1))
check('impact-first puts 2x3 above 3x2',
      tb['impact_first'].index((2, 3)) < tb['impact_first'].index((3, 2)))
check('likelihood-first puts 3x2 above 2x3',
      tb['likelihood_first'].index((3, 2)) < tb['likelihood_first'].index((2, 3)))
check('both orders are non-increasing in the product',
      all(a[0] * a[1] >= b[0] * b[1]
          for a, b in zip(tb['impact_first'], tb['impact_first'][1:])))

# ===========================================================================
# the gloss stays in step with the other lab
# ===========================================================================
try:
    import threat_model as TM
    check('the impact gloss covers the same three points as the model scale',
          set(S.IMPACT_GLOSS) == set(TM.IMPACT_SCALE))
    check('each gloss is a shortening of the same idea, not a different one',
          all(S.IMPACT_GLOSS[k].split()[0].lower()
              in TM.IMPACT_SCALE[k].lower() for k in S.IMPACT_GLOSS))
except ImportError:
    check('threat_model is importable for the gloss check', False)

# ===========================================================================
# report and CLI
# ===========================================================================
rep = S.build_report()
check('report carries the resolution table', len(rep['resolution']) == 5)
check('report carries the spacing', rep['spacing']['gaps'] == [1, 1, 1, 2, 3])
check('report carries the anomalies', len(rep['anomalies']) == 3)
check('report runs both spreads',
      len({r['spread'] for r in rep['registers']}) == 2)
check('report runs three register sizes per spread',
      len({r['items'] for r in rep['registers']}) == 3)
check('report compares four scales', len(rep['scale_comparison']) == 4)
check('the scale comparison carries the anomaly count',
      all('anomalies' in r for r in rep['scale_comparison']))
check('anomalies grow faster than distinct values do',
      rep['scale_comparison'][-1]['anomalies']
      / max(1, rep['scale_comparison'][1]['anomalies'])
      > rep['scale_comparison'][-1]['distinct_values']
      / rep['scale_comparison'][1]['distinct_values'])
check('a finer scale does tie less', all(
      rep['scale_comparison'][i]['share_tied_at_20']
      > rep['scale_comparison'][i + 1]['share_tied_at_20']
      for i in range(len(rep['scale_comparison']) - 1)))
check('a 2x2 scale ties essentially every row in a 20-item register',
      rep['scale_comparison'][0]['share_tied_at_20'] > 0.99)
check('but not exactly every row, because a lone item is always possible',
      rep['scale_comparison'][0]['share_tied_at_20'] < 1.0)
check('report carries the tie-break comparison', 'tie_breaks' in rep)
check('report carries caveats', len(rep['caveats']) >= 5)
check('a caveat says there is no sampling',
      any('no sampling' in c for c in rep['caveats']))
check('a caveat says a real register is not a random draw',
      any('not a random draw' in c for c in rep['caveats']))
check('a caveat refuses to call a coarse scale wrong',
      any('Nothing here says a 3x3 scale is wrong' in c for c in rep['caveats']))
check('report JSON-serialises', isinstance(json.dumps(rep), str))
text = S.report_text(rep)
check('the text names the four sections',
      all(x in text for x in ('A.', 'B.', 'C.', 'D.')))
check('the text states there is no random number', 'no random number' in text)
check('the text says the tie-break is a policy', 'the policy' in text)
check('the text discloses what it does not establish', 'does NOT establish' in text)
check('no report line exceeds eighty characters',
      all(len(line) <= 80 for line in text.splitlines()))

out = subprocess.run([sys.executable, 'scoring_resolution.py', '--json'],
                     capture_output=True, text=True)
check('--json exits zero', out.returncode == 0)
check('--json parses', isinstance(json.loads(out.stdout), dict))
plain = subprocess.run([sys.executable, 'scoring_resolution.py'],
                       capture_output=True, text=True)
check('plain run exits zero', plain.returncode == 0)
check('plain run is not JSON', not plain.stdout.lstrip().startswith('{'))

print('scoring_resolution: %d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: ' + f)
sys.exit(1 if FAILED else 0)
