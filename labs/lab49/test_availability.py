#!/usr/bin/env python3
"""Checks for Lab 49.2.

The chapter promised availability maths and did none. These checks establish
the arithmetic that is reusable, and mark the boundary where the placeholder
fade model begins and nothing downstream of it should be trusted.

    python3 test_availability.py
"""
import contextlib
import io
import sys

import availability as A

PASS = 0
FAIL = []


def check(name, cond, detail=''):
    global PASS
    if cond:
        PASS += 1
    else:
        FAIL.append('%s%s' % (name, (' --- ' + detail) if detail else ''))


def close(name, got, want, tol=0.005):
    check(name, abs(got - want) <= tol, 'got %.5f, wanted %.5f' % (got, want))


def raises(name, fn, want):
    try:
        fn()
    except A.AvailabilityError as e:
        check(name, want.lower() in str(e).lower(),
              'raised %r, wanted something about %r' % (str(e), want))
    except Exception as e:                      # noqa: BLE001
        check(name, False, 'raised %s, not AvailabilityError' % type(e).__name__)
    else:
        check(name, False, 'did not raise')


# ===========================================================================
# 1. The nines, exactly
# ===========================================================================
close('five nines is 5.256 minutes a year',
      A.unavailable_minutes(0.99999), 5.256, 0.001)
check('which is not "about five"',
      abs(A.unavailable_minutes(0.99999) - 5.0) > 0.25)
close('four nines is 52.56', A.unavailable_minutes(0.9999), 52.56, 0.01)
close('three nines is 525.6', A.unavailable_minutes(0.999), 525.6, 0.01)
close('six nines is 0.5256', A.unavailable_minutes(0.999999), 0.5256, 0.001)
check('each nine is a factor of ten',
      abs(A.unavailable_minutes(0.999) / A.unavailable_minutes(0.9999) - 10) < 1e-6)
close('a 365-day year is 525,600 minutes', A.MINUTES_PER_YEAR, 525600.0, 0.1)
close('five nines counts as 5 nines', A.nines(0.99999), 5.0, 1e-9)
close('99.95% is 3.3 nines', A.nines(0.9995), 3.301, 0.001)
raises('a percentage rather than a fraction is refused',
       lambda: A.unavailable_minutes(99.999), '99.999% is 0.99999')
raises('an availability of 1 is refused',
       lambda: A.unavailable_minutes(1.0), 'in (0, 1)')
raises('an availability of 0 is refused', lambda: A.nines(0.0), 'in (0, 1)')

# ===========================================================================
# 2. A state set, and what makes one invalid
# ===========================================================================
check('the illustrative link has six states', len(A.LINK) == 6)
ordered = A.check_states(A.LINK)
check('sorted by capacity, the margins rise',
      all(a['margin_db'] < b['margin_db'] for a, b in zip(ordered, ordered[1:])))
check('so lower capacity always survives more fade',
      ordered[0]['capacity_mbps'] > ordered[-1]['capacity_mbps']
      and ordered[0]['margin_db'] < ordered[-1]['margin_db'])
raises('a state set with no link is refused',
       lambda: A.check_states([]), 'at least one modulation state')
raises('a lower-capacity state that is not more robust is refused',
       lambda: A.check_states([A.state('hi', 1000, 10.0),
                               A.state('lo', 500, 10.0)]),
       'not a step down')
raises('a zero-capacity state is refused',
       lambda: A.state('x', 0, 5.0), 'positive')
raises('a negative margin is refused',
       lambda: A.state('x', 100, -1.0), 'not negative')

# ===========================================================================
# 3. A curve, not two numbers
# ===========================================================================
curve = A.capacity_curve(A.LINK, fade_1pct_db=22.0)
check('six states give six rows', len(curve) == 6)
check('every row has its own capacity', len({r['capacity_mbps'] for r in curve}) == 6)
check('and its own availability', len({r['availability'] for r in curve}) == 6)
check('availability rises as capacity falls',
      all(a['availability'] < b['availability']
          for a, b in zip(curve, curve[1:])))
check('so the chapter\'s "two rates" is six here', len(curve) > 2)
check('every row carries its unavailable minutes',
      all(r['unavailable_minutes'] > 0 for r in curve))
check('and its nines', all(r['nines'] > 0 for r in curve))

# ===========================================================================
# 4. Choosing against a target, including when nothing meets it
# ===========================================================================
check('a loose target is met by the top state',
      A.state_meeting(curve, 0.99)['name'] == '1024QAM')
check('a tighter one drops the capacity',
      A.state_meeting(curve, 0.9999)['capacity_mbps']
      < A.state_meeting(curve, 0.99)['capacity_mbps'])
check('and five nines is met by NOTHING on this path',
      A.state_meeting(curve, 0.99999) is None)
check('which the model returns rather than picking the best available',
      A.state_meeting(curve, 0.99999) is None)
check('the cost of tightening is most of the headline',
      1 - A.state_meeting(curve, 0.9999)['capacity_mbps']
      / A.state_meeting(curve, 0.99)['capacity_mbps'] > 0.7)

# a quieter path DOES reach five nines, so the model is not simply pessimistic
quiet = A.capacity_curve(A.LINK, fade_1pct_db=6.0)
check('on a much drier path a state does meet five nines',
      A.state_meeting(quiet, 0.99999) is not None)
check('so the refusal above is the path, not the model',
      A.state_meeting(curve, 0.99999) is None
      and A.state_meeting(quiet, 0.99999) is not None)

# ===========================================================================
# 5. The fade model is a placeholder and behaves monotonically
# ===========================================================================
check('more margin means less exceedance',
      all(A.fade_exceeded_fraction(m, 22.0)
          > A.fade_exceeded_fraction(m + 2, 22.0)
          for m in (2, 6, 10, 16, 24)))
check('a rainier path is worse at every margin',
      all(A.fade_exceeded_fraction(m, 40.0) > A.fade_exceeded_fraction(m, 12.0)
          for m in (4, 10, 20)))
check('zero margin means the state is never held',
      A.fade_exceeded_fraction(0, 22.0) == 1.0)
check('the fraction stays a probability',
      all(0.0 <= A.fade_exceeded_fraction(m, f) <= 1.0
          for m in (0, 1, 10, 100) for f in (5.0, 22.0, 60.0)))
raises('a non-positive reference fade is refused',
       lambda: A.fade_exceeded_fraction(10, 0), 'positive')
raises('a negative margin is refused',
       lambda: A.fade_exceeded_fraction(-1, 22.0), 'not negative')
check('the placeholder is labelled as one in its own docstring',
      'PLACEHOLDER' in A.fade_exceeded_fraction.__doc__)

# the rain assumption moves everything, which is the warning
dry = A.capacity_curve(A.LINK, 12.0)
wet = A.capacity_curve(A.LINK, 50.0)
check('one input moves every row',
      all(d['availability'] > w['availability'] for d, w in zip(dry, wet)))
check('and by more than a nine at the bottom',
      dry[-1]['nines'] - wet[-1]['nines'] > 1.0,
      '%.2f nines' % (dry[-1]['nines'] - wet[-1]['nines']))

# ===========================================================================
# 6. The report
# ===========================================================================
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    A.main([])
out = buf.getvalue()
check('the report runs', 'A. The nines' in out)
check('it prints 5.256 rather than "about five"', '5.256 min' in out)
check('it says the figure is an expectation', 'EXPECTATION' in out)
check('it says a storm can spend the budget in an afternoon',
      'in an afternoon' in out)
check('it shows six states', '1024QAM' in out and 'QPSK' in out)
check('it shows a target nothing meets', 'NONE' in out)
check('it says a lower modulation is not the fix there',
      'not a lower modulation' in out)
check('it warns that the fade model is a placeholder',
      'placeholder' in out.lower())
check('it says the arithmetic above the fade model is reusable',
      'right\n  and reusable' in out or 'reusable' in out)
check('it discloses what it does not establish', 'does NOT establish' in out)
check('no line is absurdly wide',
      max(len(x) for x in out.splitlines()) <= 80,
      'widest %d' % max(len(x) for x in out.splitlines()))

if __name__ == '__main__':
    total = PASS + len(FAIL)
    for f in FAIL:
        print('FAIL: %s' % f)
    print('%d/%d checks passed' % (PASS, total))
    sys.exit(1 if FAIL else 0)
