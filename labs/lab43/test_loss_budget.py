#!/usr/bin/env python3
"""Checks for loss_budget.py --- the design basis, not a measurement.

The previous script computed one number from typical figures and called it the
budget. The central check here is that the three bases give three different
answers and that the chapter's own worked span passes on one and fails on
another --- so a future edit that quietly reverts to typical values cannot pass.

No fibre, no light source, no power meter, no OTDR.

    python3 test_loss_budget.py
"""
import contextlib, io, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import loss_budget as lb  # noqa: E402

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


# ---- the three bases are three different numbers --------------------------
a = lb.assess(60, 1550, 16.0, fusion_splices=4, connector_pairs=4)
check('typical, acceptance and design are all different',
      len({round(a['typical_db'], 3), round(a['acceptance_limit_db'], 3),
           round(a['design_db'], 3)}) == 3,
      (a['typical_db'], a['acceptance_limit_db'], a['design_db']))
check('they are in the order typical < acceptance < design',
      a['typical_db'] < a['acceptance_limit_db'] < a['design_db'])
check('acceptance differs from typical only by the element figures',
      abs(a['acceptance_limit_db'] - a['typical_db']) > 1.0)
check('design differs from acceptance only by the life allowance',
      abs(a['design_db'] - a['acceptance_limit_db']) > 0.5)

# ---- THE FINDING: the chapter's span passes on typical, fails on design ---
check("the chapter's 60 km span passes on typical figures",
      a['passes_on_typical'], a['typical_db'])
check('...and FAILS on a design basis', not a['passes_on_design'],
      a['design_db'])
check('...by a margin larger than its entire connector allowance',
      a['the_gap_db'] > 4 * lb.ELEMENTS['connector_pair_db']['maximum'],
      a['the_gap_db'])

# ---- every input is actually used -----------------------------------------
base = lb.span_loss(60, 1550, fusion_splices=4, connector_pairs=4,
                    basis='typical', include_repairs=False)['total_db']
for kw, why in (({'km': 61}, 'one more kilometre'),
                ({'fusion_splices': 5}, 'one more splice'),
                ({'connector_pairs': 5}, 'one more connector pair'),
                ({'wavelength_nm': 1310}, 'the other wavelength')):
    args = dict(km=60, wavelength_nm=1550, fusion_splices=4, connector_pairs=4,
                basis='typical', include_repairs=False)
    args.update(kw)
    check('%s changes the total' % why,
          abs(lb.span_loss(**args)['total_db'] - base) > 1e-9)

check('1550 nm beats 1310 nm over distance',
      lb.span_loss(60, 1550, basis='typical', include_repairs=False)['total_db']
      < lb.span_loss(60, 1310, basis='typical', include_repairs=False)['total_db'])
check('a mechanical splice costs more than a fusion splice',
      lb.ELEMENTS['mechanical_splice_db']['maximum']
      > lb.ELEMENTS['fusion_splice_db']['maximum'])
check('mechanical splices are counted when present',
      lb.span_loss(10, 1550, mechanical_splices=2, basis='maximum',
                   include_repairs=False)['total_db']
      > lb.span_loss(10, 1550, basis='maximum',
                     include_repairs=False)['total_db'])

# ---- the repair allowance -------------------------------------------------
with_r = lb.span_loss(60, 1550, fusion_splices=4, connector_pairs=4,
                      basis='maximum', include_repairs=True)
without = lb.span_loss(60, 1550, fusion_splices=4, connector_pairs=4,
                       basis='maximum', include_repairs=False)
check('the repair allowance adds loss', with_r['total_db'] > without['total_db'])
check('a repair costs TWO splices, not one',
      any('2 splices' in label for label, _ in with_r['terms']),
      [l for l, _ in with_r['terms']])
check('the ageing allowance is a separate line',
      any('ageing' in label for label, _ in with_r['terms']))
check('more repairs cost more',
      lb.span_loss(60, 1550, fusion_splices=4, connector_pairs=4,
                   basis='maximum',
                   margins={'repairs_over_life': 6})['total_db']
      > with_r['total_db'])
check('zero repairs matches the acceptance basis',
      abs(lb.span_loss(60, 1550, fusion_splices=4, connector_pairs=4,
                       basis='maximum',
                       margins={'repairs_over_life': 0,
                                'ageing_db': 0})['total_db']
          - without['total_db']) < 1e-9)

# Ageing is independent of whether any future repair is budgeted.
zero_repairs = lb.span_loss(60, 1550, fusion_splices=4, connector_pairs=4,
                            basis='maximum',
                            margins={'repairs_over_life': 0, 'ageing_db': 1})
check('ageing remains with zero repairs',
      abs(zero_repairs['total_db'] - (18.6 + 1.0)) < 1e-9)
check('zero-repair ageing is itemised',
      ('ageing and drift allowance', 1.0) in zero_repairs['terms'])

# ---- the terms add up to the total ----------------------------------------
check('the printed terms sum to the stated total',
      abs(sum(v for _, v in with_r['terms']) - with_r['total_db']) < 1e-9)

# ---- the shipped spans are a spread, not all failures ---------------------
rows = [(n, lb.assess(km, nm, b, fusion_splices=f, connector_pairs=c))
        for n, km, nm, f, c, b in lb.SPANS]
passes = [n for n, r in rows if r['passes_on_design']]
fails = [n for n, r in rows if not r['passes_on_design']]
check('some shipped spans pass on the design basis', len(passes) >= 2, passes)
check('...and some fail, so the basis is not simply stricter about everything',
      len(fails) >= 1, fails)
check('removing two patch panels is a real but insufficient saving',
      rows[0][1]['design_db'] - rows[1][1]['design_db'] > 1.0
      and not rows[1][1]['passes_on_design'])
check('a bigger optical budget is what fits the same span',
      rows[2][1]['passes_on_design'] and rows[2][1]['design_db'] == rows[0][1]['design_db'])

# ---- rejection -------------------------------------------------------------
for args, kw, word in (
        ((-1, 1550), {}, 'not negative'),
        ((10, 1234), {}, 'no attenuation figure'),
        ((10, 1550), {'fusion_splices': -1}, 'non-negative integer'),
        ((10, 1550), {'connector_pairs': 1.5}, 'non-negative integer'),
        ((10, 1550), {'basis': 'optimistic'}, "'typical' or 'maximum'"),
        ((10, 1550), {'margins': {'repairs_over_life': -1}}, 'not negative')):
    try:
        lb.span_loss(*args, **kw)
        check('rejects %r %r' % (args, kw), False, 'no exception')
    except lb.BudgetError as e:
        check('rejects %r %r' % (args, kw), word in str(e), str(e)[:60])
try:
    lb.assess(10, 1550, 0)
    check('rejects a zero system budget', False, 'no exception')
except lb.BudgetError as e:
    check('rejects a zero system budget', 'positive' in str(e))

# ---- the report says which number is which --------------------------------
_r, out = quiet(lb.report, rows)
low = ' '.join(out.lower().split())
check('the report names all three bases',
      'typical' in low and 'acceptance' in low and 'design' in low)
check('the report says the defaults are illustrative',
      'illustrative default' in low)
check('the report tells you what typical figures ARE for',
      'comparing what you measured' in low)
check('the report itemises the design terms', 'ageing and drift' in out)
check('the report flags the pass-on-typical case explicitly',
      'PASSES ON TYPICAL, FAILS ON DESIGN' in out)
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
