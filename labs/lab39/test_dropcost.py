#!/usr/bin/env python3
"""Checks for dropcost.py --- that the model stays a model.

The previous version of this script shipped invented nanosecond constants,
multiplied them out and printed a packets-per-second figure as though it were
evidence. These checks exist to stop that coming back: the constants must be
declared placeholders, the output must contain no rate, and the worst case must
be labelled as one.

This executes no network device and measures nothing.

    python3 test_dropcost.py
"""
import io
import contextlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dropcost as dc  # noqa: E402

FAILS = []
COUNT = 0


def check(name, cond, detail=''):
    global COUNT
    COUNT += 1
    # str() first: a tuple or list passed as detail would otherwise be eaten by
    # %-formatting and raise from inside the test helper, which is a confusing
    # way to learn that an assertion failed.
    suffix = ('  [' + str(detail) + ']') if detail else ''
    if not cond:
        FAILS.append(name + suffix)
        print('FAIL  ' + name + suffix)
    else:
        print('ok    ' + name)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


# ---- the arithmetic is the arithmetic --------------------------------------
m = dc.model(100, rule_ns=10, stack_ns=500, lookup_ns=50)
check('the linear worst case is stack + rules x rule cost',
      m['linear_worst_case_ns'] == 500 + 100 * 10, m['linear_worst_case_ns'])
check('the constant cost does not depend on the entry count',
      dc.model(10, lookup_ns=50)['constant_ns']
      == dc.model(1000000, lookup_ns=50)['constant_ns'])
check('the ratio is the two divided', abs(m['ratio'] - 1500 / 50) < 1e-9, m['ratio'])
check('the early-match case is stack + ONE rule',
      m['early_match_ns'] == 510, m['early_match_ns'])
check('the early-match ratio is smaller than the worst case',
      m['ratio_if_first_rule_matches'] < m['ratio'],
      (m['ratio_if_first_rule_matches'], m['ratio']))
big = dc.model(100000, rule_ns=10, stack_ns=500, lookup_ns=50)
check('...and the gap widens with the entry count, which is the real point',
      big['ratio'] / big['ratio_if_first_rule_matches']
      > m['ratio'] / m['ratio_if_first_rule_matches'],
      (m['ratio'] / m['ratio_if_first_rule_matches'],
       big['ratio'] / big['ratio_if_first_rule_matches']))

# ---- it must keep reporting the early-match column --------------------------
# This is the correction: a worst-case-only comparison overstates the result.
for n in (10, 100000):
    mm = dc.model(n, rule_ns=10, stack_ns=500, lookup_ns=50)
    check('the early-match ratio is flat in the entry count at n=%d' % n,
          abs(mm['ratio_if_first_rule_matches'] - 510 / 50) < 1e-9,
          mm['ratio_if_first_rule_matches'])

# ---- validation --------------------------------------------------------------
for bad in (0, -1, 1.5, 'ten', None):
    try:
        dc.model(bad)
        check('rejects a rule count of %r' % (bad,), False, 'no exception')
    except (ValueError, TypeError):
        check('rejects a rule count of %r' % (bad,), True)
for kw in ('rule_ns', 'stack_ns', 'lookup_ns'):
    try:
        dc.model(10, **{kw: 0})
        check('rejects %s = 0' % kw, False, 'no exception')
    except ValueError as e:
        check('rejects %s = 0' % kw, kw in str(e), str(e)[:60])

# ---- the honesty guarantees --------------------------------------------------
_r, out = quiet(dc.report, 12.0, 600.0, 40.0)
low = out.lower()
check('the output declares the constants are placeholders',
      'placeholder' in low and 'not measurement' in low.replace('measurements', 'measurement'),
      [l for l in out.splitlines() if 'placeholder' in l.lower()][:1])
check('the output labels the linear column as the WORST case', 'WORST' in out)
check('the output prints the early-match column', 'FIRST' in out)
check('the output states that no rate was measured',
      'no packets-per-second figure is printed' in low)
for banned in ('drops/sec', 'drops per sec', 'million', 'pps'):
    check('the output contains no %r rate claim' % banned, banned not in low,
          [l for l in out.splitlines() if banned in l.lower()][:1])
check('the docstring names the invented figures it replaced',
      '30015x' in dc.__doc__ and '25 million' in dc.__doc__)
check('the docstring names set-based matching as the missing alternative',
      'nftables' in dc.__doc__ and 'ipset' in dc.__doc__)

rc, _o = quiet(dc.main, [])
check('the CLI exits 0', rc == 0, rc)
try:
    quiet(dc.main, ['--rule-ns', '0'])
    check('the CLI rejects a zero constant', False, 'no SystemExit')
except SystemExit as e:
    check('the CLI rejects a zero constant', e.code != 0, e.code)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
