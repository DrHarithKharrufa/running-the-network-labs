#!/usr/bin/env python3
"""Checks for band_choice.py.

The claim this lab exists to make --- that moving a fixed pair of dishes up the
spectrum makes the link STRONGER --- is not obvious and contradicts what most
readers have been told, so it is checked here three independent ways: against
the doubling rule, against the aperture form of the Friis equation derived
separately below, and against the exact square-root relation between the
diameter ratio and the frequency ratio.
"""
import json
import math
import subprocess
import sys

import band_choice as B

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
    except B.BandError:
        return True
    except Exception:
        return False
    return False


# ---------------------------------------------------------------------------
# an independent derivation to check the module against
# ---------------------------------------------------------------------------
def budget_db_from_apertures(freq_ghz, distance_km, dish_m, efficiency=0.55):
    """Pr/Pt = A_t * A_r / (lambda^2 * d^2), the aperture form of Friis.

    Written from the physical-area statement rather than from the gain
    statement the module uses, so agreement between the two is a real check
    rather than the same expression twice.
    """
    lam = B.C_M_S / (freq_ghz * 1e9)
    area = efficiency * math.pi * dish_m ** 2 / 4.0
    d_m = distance_km * 1000.0
    return 10.0 * math.log10(area * area / (lam ** 2 * d_m ** 2))


# ---------------------------------------------------------------------------
# wavelength and the two textbook terms
# ---------------------------------------------------------------------------
check('1 GHz is about 0.2998 m', close(B.wavelength_m(1.0), 0.299792458, 1e-12))
check('300 GHz is about 1 mm', close(B.wavelength_m(300.0), 0.00099930819, 1e-6))
check('wavelength halves when frequency doubles',
      close(B.wavelength_m(20.0) * 2.0, B.wavelength_m(10.0)))
check('zero frequency refused', raises(B.wavelength_m, 0.0))
check('negative frequency refused', raises(B.wavelength_m, -3.0))

check('fspl positive', B.free_space_loss_db(15.0, 2.0) > 0)
check('fspl rises 6.02 dB when frequency doubles',
      close(B.free_space_loss_db(30.0, 2.0) - B.free_space_loss_db(15.0, 2.0),
            20.0 * math.log10(2.0), 1e-12))
check('fspl rises 6.02 dB when distance doubles',
      close(B.free_space_loss_db(15.0, 4.0) - B.free_space_loss_db(15.0, 2.0),
            20.0 * math.log10(2.0), 1e-12))
check('fspl refuses zero distance', raises(B.free_space_loss_db, 15.0, 0.0))
check('fspl refuses negative distance', raises(B.free_space_loss_db, 15.0, -1.0))

check('gain rises 6.02 dB when frequency doubles',
      close(B.dish_gain_db(30.0, 0.3) - B.dish_gain_db(15.0, 0.3),
            20.0 * math.log10(2.0), 1e-12))
check('gain rises 6.02 dB when diameter doubles',
      close(B.dish_gain_db(15.0, 0.6) - B.dish_gain_db(15.0, 0.3),
            20.0 * math.log10(2.0), 1e-12))
check('efficiency enters as a straight dB offset',
      close(B.dish_gain_db(15.0, 0.3, 0.55) - B.dish_gain_db(15.0, 0.3, 0.50),
            10.0 * math.log10(0.55 / 0.50), 1e-12))
check('gain refuses zero diameter', raises(B.dish_gain_db, 15.0, 0.0))
check('gain refuses efficiency above one', raises(B.dish_gain_db, 15.0, 0.3, 1.5))
check('gain refuses zero efficiency', raises(B.dish_gain_db, 15.0, 0.3, 0.0))
check('efficiency of exactly one is allowed', B.dish_gain_db(15.0, 0.3, 1.0) > 0)

# ---------------------------------------------------------------------------
# THE HEADLINE: fixed apertures, budget improves with frequency
# ---------------------------------------------------------------------------
for f in (7.5, 15.0, 23.0, 38.0, 73.0):
    check('budget improves when %g GHz is doubled' % f,
          B.clear_air_budget_db(2.0 * f, 2.0, 0.3)
          > B.clear_air_budget_db(f, 2.0, 0.3))
    check('and improves by exactly 6.02 dB at %g GHz' % f,
          close(B.clear_air_budget_db(2.0 * f, 2.0, 0.3)
                - B.clear_air_budget_db(f, 2.0, 0.3),
                20.0 * math.log10(2.0), 1e-9))

check('budget is a loss, not a gain', B.clear_air_budget_db(15.0, 2.0, 0.3) < 0)
check('budget worsens 6.02 dB when distance doubles',
      close(B.clear_air_budget_db(15.0, 2.0, 0.3)
            - B.clear_air_budget_db(15.0, 4.0, 0.3),
            20.0 * math.log10(2.0), 1e-9))
check('budget improves 12.04 dB when BOTH dishes double',
      close(B.clear_air_budget_db(15.0, 2.0, 0.6)
            - B.clear_air_budget_db(15.0, 2.0, 0.3),
            40.0 * math.log10(2.0), 1e-9))

for f in (7.5, 15.0, 38.0, 80.0):
    check('module agrees with the aperture form at %g GHz' % f,
          close(B.clear_air_budget_db(f, 2.0, 0.3),
                budget_db_from_apertures(f, 2.0, 0.3), 1e-12))

check('asymmetric dishes handled',
      close(B.clear_air_budget_db(15.0, 2.0, 0.3, far_dish_m=0.6),
            B.dish_gain_db(15.0, 0.3) + B.dish_gain_db(15.0, 0.6)
            - B.free_space_loss_db(15.0, 2.0), 1e-12))
check('asymmetric dishes beat the small pair',
      B.clear_air_budget_db(15.0, 2.0, 0.3, far_dish_m=0.6)
      > B.clear_air_budget_db(15.0, 2.0, 0.3))

# ---------------------------------------------------------------------------
# beamwidth
# ---------------------------------------------------------------------------
check('beamwidth halves when frequency doubles',
      close(B.beamwidth_deg(30.0, 0.3) * 2.0, B.beamwidth_deg(15.0, 0.3), 1e-12))
check('beamwidth halves when diameter doubles',
      close(B.beamwidth_deg(15.0, 0.6) * 2.0, B.beamwidth_deg(15.0, 0.3), 1e-12))
check('the illumination constant cancels out of a ratio',
      close(B.beamwidth_deg(15.0, 0.3, 70.0) / B.beamwidth_deg(80.0, 0.3, 70.0),
            B.beamwidth_deg(15.0, 0.3, 58.0) / B.beamwidth_deg(80.0, 0.3, 58.0),
            1e-12))
check('beamwidth refuses a zero constant', raises(B.beamwidth_deg, 15.0, 0.3, 0.0))
check('80 GHz on a 0.3 m dish is under one degree',
      B.beamwidth_deg(80.0, 0.3) < 1.0)
check('7.5 GHz on the same dish is over nine degrees',
      B.beamwidth_deg(7.5, 0.3) > 9.0)

# ---------------------------------------------------------------------------
# the square-root relation
# ---------------------------------------------------------------------------
for lo, hi in ((15.0, 80.0), (7.5, 38.0), (23.0, 73.0)):
    got = B.aperture_for_equal_budget_m(lo, hi, 0.3, 2.0)
    check('equal-budget diameter ratio is sqrt(%g/%g)' % (hi, lo),
          close(got / 0.3, math.sqrt(hi / lo), 1e-9))
    check('and it really does equalise the budget at %g/%g' % (lo, hi),
          close(B.clear_air_budget_db(lo, 2.0, got),
                B.clear_air_budget_db(hi, 2.0, 0.3), 1e-9))
check('the equal-budget dish is larger, not smaller',
      B.aperture_for_equal_budget_m(15.0, 80.0, 0.3, 2.0) > 0.3)
check('the relation does not depend on the path length',
      close(B.aperture_for_equal_budget_m(15.0, 80.0, 0.3, 2.0),
            B.aperture_for_equal_budget_m(15.0, 80.0, 0.3, 40.0), 1e-9))

# ---------------------------------------------------------------------------
# the rain term, which is an input
# ---------------------------------------------------------------------------
check('rain loss is linear in distance',
      close(B.rain_loss_db(10.0, 4.0), 2.0 * B.rain_loss_db(10.0, 2.0), 1e-12))
check('rain loss is linear in specific attenuation',
      close(B.rain_loss_db(20.0, 2.0), 2.0 * B.rain_loss_db(10.0, 2.0), 1e-12))
check('path reduction scales it', close(B.rain_loss_db(10.0, 2.0, 0.5), 10.0))
check('zero rain is allowed', close(B.rain_loss_db(0.0, 2.0), 0.0))
check('negative rain refused', raises(B.rain_loss_db, -1.0, 2.0))
check('path reduction above one refused', raises(B.rain_loss_db, 10.0, 2.0, 1.5))
check('path reduction of zero refused', raises(B.rain_loss_db, 10.0, 2.0, 0.0))
check('faded budget is the clear-air budget minus the rain',
      close(B.faded_budget_db(80.0, 2.0, 0.3, 20.0),
            B.clear_air_budget_db(80.0, 2.0, 0.3) - 40.0, 1e-9))
check('zero rain leaves the clear-air budget alone',
      close(B.faded_budget_db(80.0, 2.0, 0.3, 0.0),
            B.clear_air_budget_db(80.0, 2.0, 0.3), 1e-12))

# ---------------------------------------------------------------------------
# the crossover
# ---------------------------------------------------------------------------
x = B.crossover_km(15.0, 80.0, 0.3, 1.5, 20.0)
check('a crossover exists for the illustrative pair', x is not None and x > 0)
check('at the crossover the two budgets are within a step',
      abs(B.faded_budget_db(80.0, x, 0.3, 20.0)
          - B.faded_budget_db(15.0, x, 0.3, 1.5)) < 0.2)
check('just inside it the high band leads',
      B.faded_budget_db(80.0, x * 0.5, 0.3, 20.0)
      > B.faded_budget_db(15.0, x * 0.5, 0.3, 1.5))
check('just outside it the low band leads',
      B.faded_budget_db(80.0, x * 2.0, 0.3, 20.0)
      < B.faded_budget_db(15.0, x * 2.0, 0.3, 1.5))
check('more rain moves the crossover closer in',
      B.crossover_km(15.0, 80.0, 0.3, 1.5, 30.0)
      < B.crossover_km(15.0, 80.0, 0.3, 1.5, 10.0))
check('equal rain means the high band never loses',
      B.crossover_km(15.0, 80.0, 0.3, 2.0, 2.0) is None)
check('the guard rejects a high band with LESS rain than the low',
      raises(B.crossover_km, 15.0, 80.0, 0.3, 20.0, 1.5))
check('the guard rejects a high frequency below the low one',
      raises(B.crossover_km, 80.0, 15.0, 0.3, 1.5, 20.0))
check('equal frequencies refused',
      raises(B.crossover_km, 15.0, 15.0, 0.3, 1.5, 1.5))

# ---------------------------------------------------------------------------
# tables and the report
# ---------------------------------------------------------------------------
rows = B.band_table(2.0, 0.3)
check('one row per band', len(rows) == len(B.BANDS_GHZ))
check('budget rises monotonically across the band table',
      all(rows[i + 1]['budget_db'] > rows[i]['budget_db']
          for i in range(len(rows) - 1)))
check('free-space loss also rises monotonically',
      all(rows[i + 1]['fspl_db'] > rows[i]['fspl_db']
          for i in range(len(rows) - 1)))
check('beamwidth falls monotonically',
      all(rows[i + 1]['beamwidth_deg'] < rows[i]['beamwidth_deg']
          for i in range(len(rows) - 1)))
check('the two rises are the same size, which is the whole point',
      close((rows[-1]['fspl_db'] - rows[0]['fspl_db']),
            (rows[-1]['budget_db'] - rows[0]['budget_db']), 1e-9))

d = B.doubling_check(15.0, 2.0, 0.3)
check('doubling: free space and each antenna move together',
      close(d['fspl_change_db'], d['gain_change_each_db'], 1e-12))
check('doubling: the net change equals one of them',
      close(d['budget_change_db'], d['fspl_change_db'], 1e-12))
check('doubling: the net change is positive', d['budget_change_db'] > 0)
check('doubling: the beam is exactly twice as narrow',
      close(d['beamwidth_ratio'], 2.0, 1e-12))

check('the illustrative rain ramp is monotonic in frequency',
      all(B.ILLUSTRATIVE_RAIN_DB_PER_KM[B.BANDS_GHZ[i + 1]]
          > B.ILLUSTRATIVE_RAIN_DB_PER_KM[B.BANDS_GHZ[i]]
          for i in range(len(B.BANDS_GHZ) - 1)))
check('every band in the table has a rain figure',
      all(f in B.ILLUSTRATIVE_RAIN_DB_PER_KM for f in B.BANDS_GHZ))

rep = B.build_report()
check('report carries its inputs', rep['inputs']['dish_m'] == 0.3)
check('report carries caveats', len(rep['caveats']) >= 5)
check('a caveat says the rain figures are not P.838',
      any('P.838' in c and 'NOT' in c for c in rep['caveats']))
check('a caveat says the budget is not capacity',
      any('not capacity' in c for c in rep['caveats']))
check('a caveat mentions the 60 GHz oxygen line',
      any('oxygen' in c for c in rep['caveats']))
check('report JSON-serialises', isinstance(json.dumps(rep), str))
text = B.report_text(rep)
check('text names the sections', 'A.' in text and 'B.' in text and 'C.' in text)
check('text states what it does not establish',
      'does NOT establish' in text)
check('text states fixed-power and eirp comparison assumptions',
      'Fixed conducted power' in text and 'Fixed antenna gains' in text)

from pathlib import Path
script_path = str(Path(__file__).with_name('band_choice.py'))
out = subprocess.run([sys.executable, script_path, '--json'],
                     capture_output=True, text=True)
check('--json exits zero', out.returncode == 0)
check('--json parses', isinstance(json.loads(out.stdout), dict))
plain = subprocess.run([sys.executable, script_path],
                       capture_output=True, text=True)
check('plain run exits zero', plain.returncode == 0)
check('plain run is not JSON', not plain.stdout.lstrip().startswith('{'))
bad = subprocess.run([sys.executable, script_path, '--dish-m', '0'],
                     capture_output=True, text=True)
check('a zero dish is refused at the command line', bad.returncode == 2)
check('and says why on stderr', 'cannot evaluate' in bad.stderr)

print('band_choice: %d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: ' + f)
sys.exit(1 if FAILED else 0)
