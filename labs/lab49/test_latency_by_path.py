#!/usr/bin/env python3
"""Checks for Lab 49.1.

Chapter 49 had no lab and three numerical claims that do not survive
arithmetic. The first duty of these checks is to reproduce each claim from the
chapter's own figures and show where it lands.

    python3 test_latency_by_path.py
"""
import contextlib
import io
import sys

import latency_by_path as L

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
    except L.PathError as e:
        check(name, want.lower() in str(e).lower(),
              'raised %r, wanted something about %r' % (str(e), want))
    except Exception as e:                      # noqa: BLE001
        check(name, False, 'raised %s, not PathError' % type(e).__name__)
    else:
        check(name, False, 'did not raise')


# ===========================================================================
# 1. The MEO row contradicts itself
# ===========================================================================
meo_hi = L.satellite_ms(20000)['ms']
meo_lo = L.satellite_ms(8000)['ms']
close('20,000 km over four legs is 266.9 ms', meo_hi, 266.9, 0.1)
close('8,000 km over four legs is 106.7 ms', meo_lo, 106.7, 0.1)
check('so the row\'s own upper altitude exceeds its own upper latency',
      meo_hi > 150.0)
check('by more than seventy per cent', meo_hi / 150.0 > 1.7,
      '%.0f%%' % (100 * (meo_hi / 150.0 - 1)))
check('and even the LOWER altitude is above the lower figure', meo_lo > 100.0)
lo_km = 0.100 * L.C_KM_S / 4
hi_km = 0.150 * L.C_KM_S / 4
close('100 ms corresponds to 7,495 km', lo_km, 7494.8, 1.0)
close('150 ms corresponds to 11,242 km', hi_km, 11242.2, 1.0)

# the other two rows are consistent, so the model is not simply pessimistic
check('the GEO row is consistent with its altitude',
      L.satellite_ms(35786)['ms'] <= 700.0)
check('the LEO row is consistent with its altitudes',
      L.satellite_ms(1200)['ms'] <= 70.0)

# ===========================================================================
# 2. Four legs, not two
# ===========================================================================
check('a round trip crosses the gap four times',
      abs(L.satellite_ms(1000, legs=4)['ms']
          - 2 * L.satellite_ms(1000, legs=2)['ms']) < 1e-9)
close('GEO propagation alone is 477.5 ms', L.satellite_ms(35786)['ms'], 477.5, 0.1)
check('which is the figure the chapter quoted as ~480 ms',
      abs(L.satellite_ms(35786)['ms'] - 480) < 3)
raises('a path with no legs is refused',
       lambda: L.satellite_ms(550, legs=0), 'at least one leg')

# ===========================================================================
# 3. Slant geometry
# ===========================================================================
close('550 km overhead is 550 km of range', L.slant_range_km(550, 90), 550.0, 0.1)
close('at 25 degrees it is 1,123 km', L.slant_range_km(550, 25), 1123.4, 1.0)
check('so the range more than doubles',
      L.slant_range_km(550, 25) / L.slant_range_km(550, 90) > 2.0)
check('and the effect is proportionally larger in lower orbits',
      (L.slant_range_km(550, 25) / L.slant_range_km(550, 90))
      > (L.slant_range_km(35786, 25) / L.slant_range_km(35786, 90)))
check('lower elevation is always longer',
      all(L.slant_range_km(550, e) > L.slant_range_km(550, e + 10)
          for e in (10, 20, 30, 40, 50, 60, 70, 80)))
raises('an elevation of zero is refused',
       lambda: L.slant_range_km(550, 0), 'in (0, 90]')
raises('an elevation above 90 is refused',
       lambda: L.slant_range_km(550, 91), 'in (0, 90]')
raises('a zero altitude is refused',
       lambda: L.slant_range_km(0, 45), 'positive')

# ===========================================================================
# 4. "Altitude sets latency" describes GEO and not LEO
# ===========================================================================
geo_prop = L.satellite_ms(35786)['ms']
leo_prop = L.satellite_ms(550, 25.0)['ms']
g = L.non_propagation_share(650.0, geo_prop)
l25 = L.non_propagation_share(25.0, leo_prop)
l70 = L.non_propagation_share(70.0, leo_prop)
check('GEO: most of the quoted figure IS propagation', g['share'] < 0.30)
check('LEO at 25 ms: most of it is not', l25['share'] > 0.35)
check('LEO at 70 ms: nearly all of it is not', l70['share'] > 0.75)
check('so the same explanation cannot cover both',
      g['share'] < 0.5 < l70['share'])
imp = L.non_propagation_share(5.0, leo_prop)
check('a quoted figure below the propagation is flagged impossible',
      imp['impossible'])
check('and does not silently return a negative share', imp['share'] is None)
raises('a non-positive quote is refused',
       lambda: L.non_propagation_share(0, 10), 'positive')

# ===========================================================================
# 5. Radio beats fibre per kilometre
# ===========================================================================
close('fibre is 4.897 us/km', L.us_per_km('fibre'), 4.897, 0.001)
close('air is 3.337 us/km', L.us_per_km('air (radio)'), 3.337, 0.001)
close('vacuum is 3.336 us/km', L.us_per_km('vacuum'), 3.336, 0.001)
check('fibre is about 47 per cent slower',
      0.46 < L.us_per_km('fibre') / L.us_per_km('air (radio)') - 1 < 0.48)
raises('an unknown medium is refused', lambda: L.us_per_km('copper'),
       'unknown medium')

radio = L.terrestrial_ms(100, 'air (radio)', 1.0)
f10 = L.terrestrial_ms(100, 'fibre', 1.0)
f13 = L.terrestrial_ms(100, 'fibre', 1.3)
check('radio beats fibre even on the same straight line',
      radio['ms'] < f10['ms'])
check('and beats it by more once the fibre route is realistic',
      f13['ms'] - radio['ms'] > f10['ms'] - radio['ms'])
close('the saving over 100 km at a 1.3 route factor is 0.606 ms',
      f13['ms'] - radio['ms'], 0.606, 0.01)
check('which is about half the round trip',
      0.45 < 1 - radio['ms'] / f13['ms'] < 0.52)
check('a round trip is twice a one-way', abs(f13['ms'] - 2 * f13['one_way_ms']) < 1e-9)
raises('a route factor below one is refused',
       lambda: L.terrestrial_ms(100, 'fibre', 0.9), 'shorter than the straight line')
raises('a non-positive distance is refused',
       lambda: L.terrestrial_ms(0, 'fibre'), 'positive')

# ===========================================================================
# 6. The report
# ===========================================================================
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    L.main([])
out = buf.getvalue()
check('the report runs', "A. The chapter's own table" in out)
check('it marks the MEO row impossible', 'IMPOSSIBLE' in out)
check('it does not mark the others impossible', out.count('IMPOSSIBLE') == 1)
check('it gives the altitudes that would fit', '7,495 to 11,242 km' in out)
check('it shows the slant table', '25 deg' in out)
check('it separates propagation from everything else',
      'everything else' in out)
check('it does not classify all residual as processing',
      'Extra space/ground distance can add propagation' in out)
check('it shows radio beating fibre', 'microwave, straight' in out)
check('it concedes capacity to fibre', 'What it does not win is capacity' in out)
check('it calls propagation a lower bound', 'LOWER BOUND' in out)
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
