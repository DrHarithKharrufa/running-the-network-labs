#!/usr/bin/env python3
"""Lab 49.4 -- fixed-aperture frequency comparison under explicit assumptions.

Ideal far-field Friis, fixed aperture efficiencies and fixed conducted power
give received power proportional to frequency squared for fixed apertures at
both ends. Holding antenna gains fixed gives the opposite trend. Holding
e.i.r.p. and receive aperture fixed removes that ideal frequency dependence.
Actual radio output, regulatory limits and efficiency need not stay fixed.

The beamwidth rule is an approximation with an illumination-dependent
coefficient. Gaseous absorption, obstruction/diffraction and alignment can
matter alongside rain. Supplied rain figures are sensitivity inputs, not local
propagation predictions. No dish, radio or field measurement was involved.
"""
import argparse
import json
import math
import sys

C_M_S = 299792458.0          # metres per second, exact by definition of the metre


class BandError(ValueError):
    """The described link cannot be evaluated."""


# ---------------------------------------------------------------------------
# the exact part: Friis, with and without real antennas
# ---------------------------------------------------------------------------
def wavelength_m(freq_ghz):
    """Wavelength in metres for a frequency in GHz."""
    if freq_ghz <= 0:
        raise BandError('frequency must be positive, got %r' % (freq_ghz,))
    return C_M_S / (freq_ghz * 1e9)


def free_space_loss_db(freq_ghz, distance_km):
    """Free-space path loss between two ISOTROPIC radiators.

    This is the number that rises as the square of frequency, and it is the
    origin of "higher frequency means shorter range".  On its own it describes
    a link nobody builds.
    """
    if distance_km <= 0:
        raise BandError('distance must be positive, got %r' % (distance_km,))
    lam = wavelength_m(freq_ghz)
    return 20.0 * math.log10(4.0 * math.pi * distance_km * 1000.0 / lam)


def dish_gain_db(freq_ghz, diameter_m, efficiency=0.55):
    """Gain of a circular aperture of a stated diameter.

    G = efficiency * (pi * D / lambda)^2.  Also rises as the square of
    frequency, which is the half of the story the chapter left out.
    """
    if diameter_m <= 0:
        raise BandError('diameter must be positive, got %r' % (diameter_m,))
    if not 0.0 < efficiency <= 1.0:
        raise BandError('efficiency must be in (0, 1], got %r' % (efficiency,))
    lam = wavelength_m(freq_ghz)
    return 10.0 * math.log10(efficiency * (math.pi * diameter_m / lam) ** 2)


def clear_air_budget_db(freq_ghz, distance_km, dish_m, efficiency=0.55,
                        far_dish_m=None, far_efficiency=None):
    """Received power relative to transmitted power, in dB, in clear air.

    Two dishes of FIXED SIZE, the free-space loss between them, nothing else.
    Negative: it is a loss.  The point of the function is what happens to it
    when you change only the frequency.
    """
    far_dish_m = dish_m if far_dish_m is None else far_dish_m
    far_efficiency = efficiency if far_efficiency is None else far_efficiency
    gt = dish_gain_db(freq_ghz, dish_m, efficiency)
    gr = dish_gain_db(freq_ghz, far_dish_m, far_efficiency)
    return gt + gr - free_space_loss_db(freq_ghz, distance_km)


def beamwidth_deg(freq_ghz, diameter_m, constant=70.0):
    """Half-power beamwidth of a circular aperture, in degrees.

    The usual engineering approximation, theta ~= constant * lambda / D.  The
    constant depends on how the aperture is illuminated and is quoted anywhere
    between about 58 and 70; the RATIO between two frequencies does not depend
    on it at all, and the ratio is what this lab uses.
    """
    if constant <= 0:
        raise BandError('constant must be positive, got %r' % (constant,))
    return constant * wavelength_m(freq_ghz) / diameter_m


# ---------------------------------------------------------------------------
# the part that needs an input this script will not invent
# ---------------------------------------------------------------------------
def rain_loss_db(specific_db_per_km, distance_km, path_reduction=1.0):
    """Rain attenuation over a path, from a SPECIFIC ATTENUATION you supply.

    specific_db_per_km is not modelled here.  Obtain it from ITU-R P.838 for
    your frequency, polarisation and rain rate, and the effective path length
    from ITU-R P.530; pass the ratio as path_reduction if you are using one.
    A rain cell is not uniform along a long path, which is what that factor
    exists to express, and assuming 1.0 is pessimistic on long hops.
    """
    if specific_db_per_km < 0:
        raise BandError('specific attenuation cannot be negative, got %r'
                        % (specific_db_per_km,))
    if not 0.0 < path_reduction <= 1.0:
        raise BandError('path reduction must be in (0, 1], got %r'
                        % (path_reduction,))
    return specific_db_per_km * distance_km * path_reduction


def faded_budget_db(freq_ghz, distance_km, dish_m, specific_db_per_km,
                    efficiency=0.55, path_reduction=1.0):
    """Clear-air budget minus the rain term for a stated specific attenuation."""
    return (clear_air_budget_db(freq_ghz, distance_km, dish_m, efficiency)
            - rain_loss_db(specific_db_per_km, distance_km, path_reduction))


def crossover_km(low_ghz, high_ghz, dish_m, low_db_per_km, high_db_per_km,
                 efficiency=0.55, path_reduction=1.0, limit_km=200.0,
                 step_km=0.01):
    """Distance at which the higher band stops being the better link.

    Below this distance the higher frequency's antenna gain wins; above it the
    higher frequency's rain term wins.  Returns None if the higher band is
    still ahead at limit_km, or 0.0 if it was never ahead.
    """
    if high_ghz <= low_ghz:
        raise BandError('high frequency must exceed low, got %r and %r'
                        % (high_ghz, low_ghz))
    if high_db_per_km < low_db_per_km:
        raise BandError('the higher band is assumed to suffer more rain; got '
                        '%r dB/km at %r GHz against %r at %r'
                        % (high_db_per_km, high_ghz, low_db_per_km, low_ghz))

    def ahead(d):
        return (faded_budget_db(high_ghz, d, dish_m, high_db_per_km,
                                efficiency, path_reduction)
                - faded_budget_db(low_ghz, d, dish_m, low_db_per_km,
                                  efficiency, path_reduction))

    first = ahead(step_km)
    if first <= 0:
        return 0.0
    d = step_km
    while d < limit_km:
        d += step_km
        if ahead(d) <= 0:
            return round(d, 2)
    return None


# ---------------------------------------------------------------------------
# tables
# ---------------------------------------------------------------------------
BANDS_GHZ = [7.5, 15.0, 23.0, 38.0, 60.0, 73.0, 80.0]
ILLUSTRATIVE_RAIN_DB_PER_KM = {
    # NOT a propagation model and NOT from ITU-R P.838.  A monotonic
    # illustrative ramp, present only so the crossover arithmetic has
    # something to chew on.  Replace every one of these before designing.
    7.5: 0.3, 15.0: 1.5, 23.0: 4.0, 38.0: 9.0,
    60.0: 16.0, 73.0: 19.0, 80.0: 20.0,
}


def band_table(distance_km, dish_m, efficiency=0.55, bands=None):
    """Clear-air arithmetic across bands for one fixed pair of dishes."""
    bands = list(BANDS_GHZ) if bands is None else list(bands)
    rows = []
    for f in bands:
        rows.append({
            'freq_ghz': f,
            'fspl_db': free_space_loss_db(f, distance_km),
            'gain_each_db': dish_gain_db(f, dish_m, efficiency),
            'budget_db': clear_air_budget_db(f, distance_km, dish_m, efficiency),
            'beamwidth_deg': beamwidth_deg(f, dish_m),
        })
    return rows


def doubling_check(freq_ghz, distance_km, dish_m, efficiency=0.55):
    """What doubling the frequency does to each term, with the same dishes."""
    lo = clear_air_budget_db(freq_ghz, distance_km, dish_m, efficiency)
    hi = clear_air_budget_db(2.0 * freq_ghz, distance_km, dish_m, efficiency)
    return {
        'freq_ghz': freq_ghz,
        'doubled_ghz': 2.0 * freq_ghz,
        'fspl_change_db': (free_space_loss_db(2.0 * freq_ghz, distance_km)
                           - free_space_loss_db(freq_ghz, distance_km)),
        'gain_change_each_db': (dish_gain_db(2.0 * freq_ghz, dish_m, efficiency)
                                - dish_gain_db(freq_ghz, dish_m, efficiency)),
        'budget_change_db': hi - lo,
        'beamwidth_ratio': (beamwidth_deg(freq_ghz, dish_m)
                            / beamwidth_deg(2.0 * freq_ghz, dish_m)),
    }


def crossover_sweep(low_ghz, high_ghz, dish_m, low_db_per_km,
                    high_rain_values, efficiency=0.55, path_reduction=1.0):
    """How the crossover moves with the one number this script will not model."""
    out = []
    for r in high_rain_values:
        out.append({
            'high_db_per_km': r,
            'crossover_km': crossover_km(low_ghz, high_ghz, dish_m,
                                         low_db_per_km, r, efficiency,
                                         path_reduction),
        })
    return out


def aperture_for_equal_budget_m(low_ghz, high_ghz, dish_m, distance_km,
                                efficiency=0.55):
    """Dish diameter at the LOW band that matches the high band's clear-air budget.

    The mirror of the same physics: if a higher frequency gives a fixed
    aperture more gain, then matching it lower down costs aperture.  The ratio
    is exactly the frequency ratio.
    """
    target = clear_air_budget_db(high_ghz, distance_km, dish_m, efficiency)
    # budget scales as 20*log10(D) at fixed frequency; solve directly.
    have = clear_air_budget_db(low_ghz, distance_km, dish_m, efficiency)
    return dish_m * 10.0 ** ((target - have) / 40.0)


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def build_report(distance_km=2.0, dish_m=0.3, efficiency=0.55):
    return {
        'inputs': {
            'distance_km': distance_km,
            'dish_m': dish_m,
            'efficiency': efficiency,
            'note': 'both ends the same dish; clear air unless stated',
        },
        'bands': band_table(distance_km, dish_m, efficiency),
        'doubling': [doubling_check(f, distance_km, dish_m, efficiency)
                     for f in (7.5, 15.0, 38.0)],
        'crossover': crossover_sweep(
            15.0, 80.0, dish_m,
            ILLUSTRATIVE_RAIN_DB_PER_KM[15.0],
            [5.0, 10.0, 15.0, 20.0, 30.0], efficiency),
        'equal_budget': {
            'low_ghz': 15.0, 'high_ghz': 80.0, 'high_dish_m': dish_m,
            'low_dish_m': aperture_for_equal_budget_m(
                15.0, 80.0, dish_m, distance_km, efficiency),
        },
        'caveats': [
            'Sections A and C are the Friis equation and aperture geometry. '
            'No model is fitted and no figure is a vendor claim.',
            'The specific attenuation figures are an illustrative ramp, NOT '
            'ITU-R P.838 and not a prediction. Obtain real ones for your '
            'frequency, polarisation, rain rate and availability target.',
            'Atmospheric gas absorption is absent. It is not a smooth trend: '
            'the oxygen line near 60 GHz is a large local peak and the E-band '
            'allocations sit deliberately away from it.',
            'Multipath, ducting, diffraction, obstruction, tower sway and '
            'equipment failure are all absent, and some of them dominate.',
            'Clear-air budget is not capacity. Capacity needs the channel '
            'width you are licensed for, the noise figure and the modulation '
            'the margin supports.',
            'Nothing here selects a band. It establishes which arithmetic a '
            'claim about frequency and range has to survive.',
        ],
    }


def _fmt(x, n=1):
    return ('%.' + str(n) + 'f') % x


def report_text(rep):
    d = rep['inputs']['distance_km']
    dm = rep['inputs']['dish_m']
    L = []
    L.append('What frequency buys and what it costs (Chapter 49)')
    L.append('Ideal aperture model and approximate beamwidth; rain is a supplied input.')
    L.append('Fixed conducted power and aperture efficiency, not a fixed e.i.r.p. limit.')
    L.append('')
    L.append('A. The same two dishes, moved up the spectrum')
    L.append('-' * 74)
    L.append('  %.2f m dishes at both ends, %.1f km apart, clear air.'
             % (dm, d))
    L.append('')
    L.append('%-10s %12s %12s %12s %12s' % ('band', 'free-space',
                                            'gain each', 'budget', 'beamwidth'))
    for r in rep['bands']:
        L.append('%7.1f GHz %10.1f dB %10.1f dB %10.1f dB %9.2f deg'
                 % (r['freq_ghz'], r['fspl_db'], r['gain_each_db'],
                    r['budget_db'], r['beamwidth_deg']))
    lo, hi = rep['bands'][0], rep['bands'][-1]
    L.append('')
    dg = hi['gain_each_db'] - lo['gain_each_db']
    df = hi['fspl_db'] - lo['fspl_db']
    L.append('  Read the columns against each other, %.1f GHz against %.1f. '
             'Free-space loss' % (lo['freq_ghz'], hi['freq_ghz']))
    L.append('  rises by %.1f dB, which is the term everyone quotes. The same '
             'two dishes' % df)
    L.append('  gain %.1f dB EACH over that span, so %.1f dB between them. '
             'Subtract:' % (dg, 2.0 * dg))
    L.append('  %.1f minus %.1f is %+.1f dB, and the budget column agrees. '
             'Moving the'
             % (2.0 * dg, df, hi['budget_db'] - lo['budget_db']))
    L.append('  same aperture sizes at fixed conducted power gives this ideal gain.')
    L.append('  Fixed antenna gains instead lose 6 dB per doubling. Fixed e.i.r.p.')
    L.append('  and receive aperture remove the ideal frequency dependence.')
    L.append('')
    for row in rep['doubling']:
        L.append('  Double %.1f GHz to %.1f with the same dishes: free space '
                 '%+.1f dB,' % (row['freq_ghz'], row['doubled_ghz'],
                                row['fspl_change_db']))
        L.append('    each antenna %+.1f dB, net %+.1f dB, beam %.1fx narrower.'
                 % (row['gain_change_each_db'], row['budget_change_db'],
                    row['beamwidth_ratio']))
    eb = rep['equal_budget']
    L.append('')
    L.append('  The mirror of it: matching the %.0f GHz budget down at %.0f GHz '
             'with the' % (eb['high_ghz'], eb['low_ghz']))
    L.append('  same path needs a %.2f m dish instead of %.2f m --- %.1f times '
             'the' % (eb['low_dish_m'], eb['high_dish_m'],
                      eb['low_dish_m'] / eb['high_dish_m']))
    L.append('  diameter, %.1f times the area, and a mast that can hold it. '
             'Which is'
             % ((eb['low_dish_m'] / eb['high_dish_m']) ** 2))
    L.append('  the real reason small high-band dishes appear on street '
             'furniture.')
    L.append('  The diameter ratio is exactly the square root of the frequency '
             'ratio:')
    L.append('  sqrt(%.0f/%.0f) = %.2f. Nothing in that depends on the weather.'
             % (eb['high_ghz'], eb['low_ghz'],
                math.sqrt(eb['high_ghz'] / eb['low_ghz'])))
    L.append('')
    L.append('B. Where the weather takes it back')
    L.append('-' * 74)
    L.append('  Rain attenuation is per kilometre, so it grows with the path '
             'while the')
    L.append('  antenna advantage above does not. Somewhere the two cross.')
    L.append('')
    L.append('%-22s %s' % ('80 GHz rain (dB/km)',
                          "80 GHz's budget drops below 15 GHz's at"))
    for row in rep['crossover']:
        km = row['crossover_km']
        shown = 'never, out to the search limit' if km is None else (
            'immediately' if km == 0.0 else '%.2f km' % km)
        L.append('%18.1f      %s' % (row['high_db_per_km'], shown))
    L.append('')
    L.append('  One input moves the answer across an order of magnitude, and '
             'that input')
    L.append('  is the one this script refuses to model. Obtain it from a '
             'dated method')
    L.append('  with your own rain statistics --- ITU-R P.838 for the specific '
             'attenuation,')
    L.append('  ITU-R P.530 for the path. The shape of the answer is the '
             'lesson: a high')
    L.append('  band has the stronger budget when the hop is SHORT and the '
             'weaker one')
    L.append('  when it is long, and the distance where that flips belongs to '
             'your')
    L.append('  weather rather than to the band. Note what this comparison is '
             'and is')
    L.append('  not: it compares RECEIVED POWER, not capacity. The high band '
             'is also')
    L.append('  the one with the wide channel, so a band that loses on budget '
             'may')
    L.append('  still be the only one that carries the bits.')
    L.append('')
    L.append('C. The cost nobody puts in the budget')
    L.append('-' * 74)
    L.append('  Beamwidth is inversely proportional to frequency at a fixed '
             'dish size,')
    L.append('  exactly, and the constant in the approximation cancels out of '
             'the ratio.')
    L.append('')
    for r in rep['bands']:
        L.append('%7.1f GHz   %5.2f deg half-power beamwidth'
                 % (r['freq_ghz'], r['beamwidth_deg']))
    L.append('')
    L.append('  At %.1f GHz the %.2f m dish has a %.2f degree beam. A mast that '
             'moves' % (hi['freq_ghz'], dm, hi['beamwidth_deg']))
    L.append('  half of that in a gale has thrown away 3 dB of the margin the '
             'link')
    L.append('  budget said it had, and no rain model will mention it. This is '
             'a')
    L.append('  structural requirement, a survey requirement and a '
             'maintenance')
    L.append('  requirement, and it arrives with the frequency rather than '
             'with the')
    L.append('  weather.')
    L.append('')
    L.append('What this does NOT establish')
    L.append('-' * 74)
    for c in rep['caveats']:
        L.append('- ' + c)
    return '\n'.join(L)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--json', action='store_true', help='emit the report as JSON')
    p.add_argument('--distance-km', type=float, default=2.0)
    p.add_argument('--dish-m', type=float, default=0.3)
    p.add_argument('--efficiency', type=float, default=0.55)
    a = p.parse_args(argv)
    try:
        rep = build_report(a.distance_km, a.dish_m, a.efficiency)
    except BandError as exc:
        print('cannot evaluate: %s' % exc, file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=2) if a.json else report_text(rep))
    return 0


if __name__ == '__main__':
    sys.exit(main())
