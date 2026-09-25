#!/usr/bin/env python3
"""Checks for Lab 48.1.

The chapter's error was a boundary: it treated a transport delay class as a
total and subtracted radio processing from it again. So the first duty of these
checks is to show both readings computed side by side, and that they differ by
the factor they do.

    python3 test_fronthaul_budget.py
"""
import sys

import fronthaul_budget as B

PASS = 0
FAIL = []


def check(name, cond, detail=''):
    global PASS
    if cond:
        PASS += 1
    else:
        FAIL.append('%s%s' % (name, (' --- ' + detail) if detail else ''))


def close(name, got, want, tol=0.05):
    check(name, abs(got - want) <= tol, 'got %.4f, wanted %.4f' % (got, want))


def raises(name, fn, want):
    try:
        fn()
    except B.BudgetError as e:
        check(name, want.lower() in str(e).lower(),
              'raised %r, wanted something about %r' % (str(e), want))
    except Exception as e:                      # noqa: BLE001
        check(name, False, 'raised %s, not BudgetError' % type(e).__name__)
    else:
        check(name, False, 'did not raise')


# ===========================================================================
# 1. The two readings of the same class
# ===========================================================================
spec = B.max_km('High100', hops=0)
chapter = B.max_km('High100', hops=0, other_us=70.0)
close('direct 25G link includes one serialisation', spec, 20.321, 0.02)
close('double-counted processing leaves about 6.0 km', chapter, 6.027, 0.02)
check('the chapter understated the reach', chapter < spec)
check('by a factor of more than three', spec / chapter > 3.0,
      'factor %.2f' % (spec / chapter))
check('and the error is exactly the double-counted 70 us',
      abs((spec - chapter) - 70.0 / B.propagation_us_per_km()) < 1e-9)

# ===========================================================================
# 2. Propagation, computed not assumed
# ===========================================================================
close('a group index of 1.4682 gives 4.897 us/km',
      B.propagation_us_per_km(1.4682), 4.897, 0.001)
close('the round "5 us/km" corresponds to an index of 1.4990',
      B.propagation_us_per_km(1.4990), 5.000, 0.002)
check('a bigger index is slower',
      B.propagation_us_per_km(1.50) > B.propagation_us_per_km(1.46))
check('vacuum would be 3.336 us/km',
      abs(B.propagation_us_per_km(1.0000001) - 3.3356) < 0.001)
raises('an index below 1 is refused', lambda: B.propagation_us_per_km(0.9),
       'greater than 1')

# ===========================================================================
# 3. The classes are as published, and reach scales with them
# ===========================================================================
check('four classes', set(B.ECPRI_DELAY_CLASSES) ==
      {'High25', 'High100', 'High200', 'High500'})
check('at 25, 100, 200 and 500 us',
      [B.ECPRI_DELAY_CLASSES[k] for k in
       ('High25', 'High100', 'High200', 'High500')] == [25.0, 100.0, 200.0, 500.0])
close('High25 direct 25G link gives about 5.0 km', B.max_km('High25'), 5.007, 0.02)
close('High500 direct link gives about 102.0 km', B.max_km('High500'), 101.997, 0.05)
close('additional delay allowance becomes additional propagation reach',
      B.max_km('High500') - B.max_km('High100'), 400 / B.propagation_us_per_km(), 1e-9)
raises('an unknown class is refused',
       lambda: B.path_delay_us(1.0, 0, delay_class='High50'), 'unknown delay class')

# ===========================================================================
# 4. Serialisation, the term that is usually forgotten
# ===========================================================================
close('1500 bytes at 1 Gb/s is 12 us', B.serialisation_us(1500, 1.0), 12.0, 0.01)
close('1500 bytes at 25 Gb/s is 0.48 us', B.serialisation_us(1500, 25.0), 0.48, 0.01)
close('9000 bytes at 10 Gb/s is 7.2 us', B.serialisation_us(9000, 10.0), 7.2, 0.01)
check('it scales inversely with the rate',
      abs(B.serialisation_us(1500, 1.0) / B.serialisation_us(1500, 10.0) - 10.0) < 1e-9)
raises('a zero line rate is refused', lambda: B.serialisation_us(1500, 0),
       'positive')
raises('a zero frame is refused', lambda: B.serialisation_us(0, 10.0), 'positive')

# every hop pays one serialisation
d1 = B.path_delay_us(0, 1, line_rate_gbps=1.0)
d4 = B.path_delay_us(0, 4, line_rate_gbps=1.0)
close('four switches need five frame transmissions', d4['serialisation_us'], 60.0)
close('one switch needs two frame transmissions', d1['serialisation_us'], 24.0)
close('four 10G switches consume 14 us before propagation',
      B.path_delay_us(0, 4, line_rate_gbps=10)['total_us'], 14.0)
close('and four switch delays', d4['switching_us'], 4 * 2.0)

# ===========================================================================
# 5. The line rate can decide the verdict on its own
# ===========================================================================
fast = B.path_delay_us(15.0, 4, line_rate_gbps=10.0)
slow = B.path_delay_us(15.0, 4, line_rate_gbps=1.0)
check('15 km over four 10G hops meets High100', fast['meets'])
check('the same path at 1 Gb/s does not', not slow['meets'])
check('and the whole difference is serialisation',
      abs((slow['total_us'] - fast['total_us'])
          - (slow['serialisation_us'] - fast['serialisation_us'])) < 1e-9)
check('the propagation term is identical',
      fast['propagation_us'] == slow['propagation_us'])

# and the class can decide it on its own
a = B.path_delay_us(12.0, 2, delay_class='High100', line_rate_gbps=25.0)
b = B.path_delay_us(12.0, 2, delay_class='High25', line_rate_gbps=25.0)
check('12 km over two 25G hops meets High100', a['meets'])
check('the identical path fails High25', not b['meets'])
check('the delay is the same in both', a['total_us'] == b['total_us'])
check('only the allowance differs', a['allowance_us'] != b['allowance_us'])

# ===========================================================================
# 6. The model can return a negative reach, and says so
# ===========================================================================
km = B.max_km('High100', hops=8, line_rate_gbps=1.0)
check('eight 1G hops overspend the class before any fibre', km < 0,
      '%.1f km' % km)
check('and the model reports it rather than clamping', isinstance(km, float))
check('the same hops at 25G leave real reach',
      B.max_km('High100', hops=8, line_rate_gbps=25.0) > 15)
zero = B.path_delay_us(0, 0)
close('even a zero-length direct link must transmit the frame', zero['total_us'], 0.48)
check('and meets every class',
      all(B.path_delay_us(0, 0, delay_class=k)['meets']
          for k in B.ECPRI_DELAY_CLASSES))
raises('a negative distance is refused', lambda: B.path_delay_us(-1, 0),
       'not negative')
raises('a negative hop count is refused', lambda: B.path_delay_us(1, -1),
       'not negative')

# ===========================================================================
# 7. What the specification does and does not give
# ===========================================================================
check('frame loss ratios are recorded for three classes of service',
      set(B.ECPRI_FRAME_LOSS) == {'High', 'Medium', 'Low'})
check('High and Medium are 1e-7',
      B.ECPRI_FRAME_LOSS['High'] == B.ECPRI_FRAME_LOSS['Medium'] == 1e-7)
check('Low is 1e-6', B.ECPRI_FRAME_LOSS['Low'] == 1e-6)
check('no packet delay variation figure is recorded anywhere in the module',
      not any('pdv' in n.lower() or 'jitter' in n.lower() for n in dir(B)),
      'a jitter constant here would be invented, as the old lab\'s was')

# ===========================================================================
# 8. The report is consistent with the model
# ===========================================================================
import io                                                     # noqa: E402
import contextlib                                             # noqa: E402

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    B.main([])
out = buf.getvalue()
check('the report runs', 'A. The classes' in out)
check('it states the classes are transport allowances',
      "TRANSPORT network's allowance" in out)
check('it warns against subtracting radio processing again',
      'not a total from' in out)
check('it shows both readings', 'chapter: 100 us less 70 us' in out
      and 'spec: High100 is the transport allowance' in out)
check('it shows a negative reach rather than hiding it', '-4.9 km' in out)
check('it says PDV is not specified', 'NOT SPECIFIED' in out)
check('it discloses what it does not establish', 'does NOT establish' in out)
check('it does not claim the budget is sufficient',
      'necessary, not sufficient' in out)
check('no report line is absurdly wide',
      max(len(l) for l in out.splitlines()) <= 80,
      'widest %d' % max(len(l) for l in out.splitlines()))

# ===========================================================================
if __name__ == '__main__':
    total = PASS + len(FAIL)
    for f in FAIL:
        print('FAIL: %s' % f)
    print('%d/%d checks passed' % (PASS, total))
    sys.exit(1 if FAIL else 0)
