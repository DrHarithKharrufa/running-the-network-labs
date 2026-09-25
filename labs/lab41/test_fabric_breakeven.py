#!/usr/bin/env python3
"""Checks for fabric_breakeven.py --- the condition, not a price list.

The chapter previously decided the fabric question with a rule of thumb: a
communication-to-compute ratio above roughly 25% justified the premium. The
central check here is that the rule is WRONG, by showing two comparisons with
the same ratio and opposite answers, and two with different ratios and the same
answer. If a future edit reintroduces a ratio-only rule, these fail.

No benchmark, vendor quotation or device is involved.

    python3 test_fabric_breakeven.py
"""
import contextlib
import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fabric_breakeven as fb  # noqa: E402

FAILS = []
COUNT = 0


def check(name, cond, detail=''):
    global COUNT
    COUNT += 1
    detail = str(detail) if detail not in ('', None) else ''
    suffix = ('  [' + detail + ']') if detail else ''
    if cond:
        print('ok    ' + name + suffix)
    else:
        FAILS.append(name + suffix)
        print('FAIL  ' + name + suffix)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


G, A, B = 2.00, 0.30, 0.10

# ---- THE RATIO IS NOT THE RULE --------------------------------------------
same_ratio_yes = fb.compare(G, A, B, 0.45, 0.40)
same_ratio_no = fb.compare(G, A, B, 0.45, 0.05)
check('same communication ratio, opposite answers',
      same_ratio_yes['a_is_cheaper'] and not same_ratio_no['a_is_cheaper'],
      (same_ratio_yes['a_is_cheaper'], same_ratio_no['a_is_cheaper']))
check('...and the ratio really was identical',
      same_ratio_yes['comm_fraction'] == same_ratio_no['comm_fraction'])

low_ratio_yes = fb.compare(G, A, B, 0.10, 0.90)
high_ratio_no = fb.compare(G, A, B, 0.45, 0.05)
check('a LOW ratio can justify the premium and a HIGH one fail to',
      low_ratio_yes['a_is_cheaper'] and not high_ratio_no['a_is_cheaper'],
      (low_ratio_yes['comm_fraction'], high_ratio_no['comm_fraction']))
check('the old 25% rule of thumb would have got both of those wrong',
      low_ratio_yes['comm_fraction'] < 0.25 < high_ratio_no['comm_fraction'])

# ---- the condition itself --------------------------------------------------
r = fb.compare(G, A, B, 0.25, 0.40)
check('premium is f_A - f_B', abs(r['premium'] - 0.20) < 1e-12, r['premium'])
check('wall-clock removed is c * s',
      abs(r['wallclock_removed'] - 0.10) < 1e-12, r['wallclock_removed'])
check('the saved time is worth (g + f_A) * c * s',
      abs(r['saved_time_worth'] - (G + A) * 0.10) < 1e-12)
check('A is cheaper exactly when the premium is below that worth',
      r['a_is_cheaper'] == (r['premium'] < r['saved_time_worth']))
check('the verdict agrees with the cost-per-work comparison',
      r['a_is_cheaper'] == (r['cost_per_work_a'] < r['cost_per_work_b']))

# the two forms of the condition must agree everywhere, not just here
for c in (0.0, 0.05, 0.2, 0.5, 0.9, 1.0):
    for s in (0.0, 0.1, 0.5, 1.0):
        x = fb.compare(G, A, B, c, s)
        check('both forms agree at c=%.2f s=%.2f' % (c, s),
              x['a_is_cheaper'] == (x['premium'] < x['saved_time_worth']))

# ---- break-even points are where the answer flips -------------------------
be = r['breakeven_removed']
just_over = fb.compare(G, A, B, 1.0, min(1.0, be + 1e-6))
just_under = fb.compare(G, A, B, 1.0, max(0.0, be - 1e-6))
check('just above the break-even removal, A wins', just_over['a_is_cheaper'],
      be)
check('just below it, A loses', not just_under['a_is_cheaper'], be)
check('the break-even removal is premium / (g + f_A)',
      abs(be - 0.20 / (G + A)) < 1e-12, be)

bs = r['breakeven_speedup']
check('the break-even speedup accounts for the ratio',
      abs(bs - be / 0.25) < 1e-9, (bs, be))

# ---- degenerate but legal inputs ------------------------------------------
none_removed = fb.compare(G, A, B, 0.9, 0.0)
check('a fabric that removes nothing is never worth a premium',
      not none_removed['a_is_cheaper'])
no_comm = fb.compare(G, A, B, 0.0, 1.0)
check('a job with no communication is never worth a premium',
      not no_comm['a_is_cheaper'])
free = fb.compare(G, B, B, 0.5, 0.5)
check('with no premium the faster fabric always wins', free['a_is_cheaper'],
      free['premium'])
check('...because its premium is zero', free['premium'] == 0)
cheaper_and_faster = fb.compare(G, 0.05, B, 0.3, 0.3)
check('a cheaper AND faster fabric wins outright',
      cheaper_and_faster['a_is_cheaper']
      and cheaper_and_faster['premium'] < 0)

# ---- the GPU cost matters, and in the right direction ---------------------
expensive_gpu = fb.compare(10.0, A, B, 0.25, 0.40)
cheap_gpu = fb.compare(0.50, A, B, 0.25, 0.40)
check('a dearer GPU makes the fabric premium easier to justify',
      expensive_gpu['a_is_cheaper'] and not cheap_gpu['a_is_cheaper'],
      (expensive_gpu['margin'], cheap_gpu['margin']))
check('...which is the real reason AI fabrics are bought expensive',
      expensive_gpu['saved_time_worth'] > cheap_gpu['saved_time_worth'])

# ---- rejection -------------------------------------------------------------
for args, word in (
        ((G, A, B, 1.5, 0.4), 'communication fraction'),
        ((G, A, B, -0.1, 0.4), 'communication fraction'),
        ((G, A, B, 0.4, 1.5), 'removed fraction'),
        ((G, A, B, 0.4, -0.1), 'removed fraction'),
        ((-1, A, B, 0.4, 0.4), 'negative'),
        ((G, -1, B, 0.4, 0.4), 'negative')):
    try:
        fb.compare(*args)
        check('rejects %r' % (args,), False, 'no exception')
    except fb.CostError as e:
        check('rejects %r' % (args,), word in str(e), str(e)[:60])

# ---- the report is honest about where its numbers come from ---------------
_r, out = quiet(fb.report, fb.analyse())
low = ' '.join(out.lower().split())
check('the report says the inputs are illustrative, not prices',
      'illustrative inputs, not prices' in low)
check('the report says no vendor quotation was available',
      'no vendor' in low and 'quotation' in low)
check('the report states that a ratio alone decides nothing',
      'a ratio on its own decides nothing' in low)
check('the report shows the fixed-ratio sweep flipping',
      out.count('| yes') >= 2 and out.count('| no') >= 2)
rc, _o = quiet(fb.main, [])
check('the script exits 0', rc == 0, rc)
rc2, _o = quiet(fb.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
