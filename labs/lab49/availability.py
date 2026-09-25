#!/usr/bin/env python3
"""Lab 49.2 --- availability arithmetic, and why a link has more than two rates.

WHY THIS LAB EXISTS
-------------------
The chapter promised availability maths and then did not do any.  It said a
microwave link has "two rates --- a headline clear-air rate and a lower
guaranteed rate", that five nines "is about five minutes of outage per year",
and that you "size the fade margin to deliver the availability the service
requires".  Every one of those needs a number behind it, and two of them are
wrong in a way that matters.

  A LINK HAS AS MANY RATES AS IT HAS MODULATION STATES, not two.  Adaptive
  modulation steps down through a set of modulation and coding states, each with
  its own required signal level and its own capacity.  A link with six states
  has six rates and six availabilities, and the useful output is the whole curve
  --- how much time at or above each capacity --- not a headline and a floor.
  Which state you call "guaranteed" is a decision about the service, and the
  chapter skipped the decision by assuming there were only two.

  AVAILABILITY IS STATISTICAL, NOT A MINIMUM.  "99.999% means five minutes of
  outage" is a long-run expectation over a stated period, computed from a
  propagation model and local rain statistics.  It does not promise that any
  particular year contains five minutes of outage, and a single bad storm can
  spend the year's budget in one afternoon.  A contract that treats the figure
  as a guaranteed maximum is a contract about something the physics does not
  offer.

  AND THE NUMBER WAS LOOSE.  Five nines of a 365-day year is 5.256 minutes, not
  "about five".  The difference is small; the habit of not computing it is not,
  because the same habit gives you 52.56 minutes for four nines and 0.526 for
  six, and people routinely quote those as "an hour" and "half a minute".

    python3 availability.py
    python3 availability.py --json
    python3 test_availability.py

No radio, no spectrum analyser, no rain gauge and no propagation model.  The
rain rates, path lengths, modulation states and margins below are stated inputs
chosen to be plausible.  A real availability figure comes from a dated
propagation method with local rainfall statistics for the actual path, and is
then accepted by measurement over time.
"""
import argparse
import json
import math
import sys

MINUTES_PER_YEAR = 365 * 24 * 60.0      # a 365-day year, stated


class AvailabilityError(ValueError):
    """The described link or requirement cannot be evaluated."""


# ---------------------------------------------------------------------------
# nines
# ---------------------------------------------------------------------------
def unavailable_minutes(availability, minutes_per_year=MINUTES_PER_YEAR):
    """Expected unavailable time per year at a stated availability."""
    if not 0 < availability < 1:
        raise AvailabilityError('an availability is a fraction in (0, 1), got '
                                '%r --- 99.999%% is 0.99999' % (availability,))
    return (1.0 - availability) * minutes_per_year


def nines(availability):
    """How many nines, as the count people actually mean."""
    if not 0 < availability < 1:
        raise AvailabilityError('an availability is a fraction in (0, 1)')
    return -math.log10(1.0 - availability)


# ---------------------------------------------------------------------------
# modulation states
# ---------------------------------------------------------------------------
def state(name, capacity_mbps, required_margin_db):
    """One modulation and coding state.

    required_margin_db is how much fade this state survives: the difference
    between the clear-air received level and the level at which this state can
    no longer be held.  A higher-order state carries more and survives less.
    """
    if capacity_mbps <= 0:
        raise AvailabilityError('%s: capacity is positive' % name)
    if required_margin_db < 0:
        raise AvailabilityError('%s: a fade margin is not negative' % name)
    return {'name': name, 'capacity_mbps': capacity_mbps,
            'margin_db': required_margin_db}


def check_states(states):
    """A usable state set falls in capacity as the margin rises."""
    if not states:
        raise AvailabilityError('a link has at least one modulation state')
    s = sorted(states, key=lambda x: -x['capacity_mbps'])
    for a, b in zip(s, s[1:]):
        if b['margin_db'] <= a['margin_db']:
            raise AvailabilityError(
                '%s carries less than %s but survives no more fade (%g dB '
                'against %g dB); a lower-order state that is not more robust '
                'is not a step down, it is a worse state'
                % (b['name'], a['name'], b['margin_db'], a['margin_db']))
    return s


# ---------------------------------------------------------------------------
# a rain-fade model, declared as the crude thing it is
# ---------------------------------------------------------------------------
def fade_exceeded_fraction(margin_db, fade_1pct_db, shape=0.6):
    """Fraction of a year the fade exceeds margin_db.

    THIS IS A PLACEHOLDER, not a propagation method.  It is a two-parameter
    curve fitted to nothing: fade_1pct_db is the fade exceeded 0.01% of the
    time on this path, and the shape exponent controls how quickly the tail
    falls away.  It exists so that the availability ARITHMETIC downstream can
    be exercised, and it must not be used to size a real link.

    A real figure comes from a dated propagation method with the path's own
    geometry, frequency, polarisation and local rain-rate statistics.
    """
    if fade_1pct_db <= 0:
        raise AvailabilityError('the reference fade is positive')
    if margin_db < 0:
        raise AvailabilityError('a margin is not negative')
    if margin_db == 0:
        return 1.0
    # exceedance probability of 1e-4 at the reference fade, decaying with a
    # power of the ratio
    p = 1e-4 * math.exp(-((margin_db / fade_1pct_db) ** shape - 1.0) * 4.0)
    return min(1.0, max(0.0, p))


def capacity_curve(states, fade_1pct_db, shape=0.6):
    """Time at or above each capacity, as a curve rather than two numbers."""
    s = check_states(states)
    out = []
    for st in s:
        unavail = fade_exceeded_fraction(st['margin_db'], fade_1pct_db, shape)
        avail = 1.0 - unavail
        out.append({'name': st['name'], 'capacity_mbps': st['capacity_mbps'],
                    'margin_db': st['margin_db'],
                    'availability': avail,
                    'unavailable_minutes': unavailable_minutes(avail)
                    if 0 < avail < 1 else (0.0 if avail >= 1 else
                                           MINUTES_PER_YEAR),
                    'nines': nines(avail) if 0 < avail < 1 else float('inf')})
    return out


def state_meeting(curve, target_availability):
    """The highest capacity whose availability meets the target, or None."""
    for row in curve:
        if row['availability'] >= target_availability:
            return row
    return None


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
LINK = [
    state('1024QAM', 2000, 2.0),
    state('512QAM', 1700, 4.0),
    state('256QAM', 1400, 7.0),
    state('64QAM', 1000, 12.0),
    state('16QAM', 700, 18.0),
    state('QPSK', 350, 26.0),
]


def section_a():
    print('A. The nines, computed rather than rounded')
    print('-' * 74)
    print('%-12s %14s %14s' % ('availability', 'unavailable', 'the same'))
    out = {}
    for a in (0.99, 0.999, 0.9999, 0.99999, 0.999999):
        m = unavailable_minutes(a)
        out[a] = m
        print('%-12s %11.3f min %11.1f s' % ('%.6g%%' % (a * 100), m, m * 60))
    print()
    print('  Five nines of a 365-day year is %.3f minutes, not "about five".'
          % out[0.99999])
    print('  Four nines is %.2f, which people call "about an hour" and is not.'
          % out[0.9999])
    print('  The arithmetic is trivial; not doing it is the habit that lets a')
    print('  contract be written against a number nobody checked.')
    print()
    print('  And note what the figure is: a long-run EXPECTATION over a stated')
    print('  period. It does not promise that any particular year contains')
    print('  %.3f minutes of outage. One bad storm can spend the whole year\'s'
          % out[0.99999])
    print('  budget in an afternoon, and the link will still have met its')
    print('  design availability over its life.')
    print()
    return out


def section_b():
    print('B. A link has as many rates as it has states')
    print('-' * 74)
    curve = capacity_curve(LINK, fade_1pct_db=22.0)
    print('%-9s %10s %9s %14s %13s %7s'
          % ('state', 'capacity', 'margin', 'availability', 'unavailable',
             'nines'))
    for r in curve:
        print('%-9s %7d Mb/s %6.1f dB %13.6f%% %9.2f min %7.2f'
              % (r['name'], r['capacity_mbps'], r['margin_db'],
                 100 * r['availability'], r['unavailable_minutes'],
                 r['nines']))
    print()
    print('  Six states, six capacities, six availabilities. The chapter said')
    print('  two. Which of these is "the guaranteed rate" is not a property of')
    print('  the link --- it is a decision about the service, and it is only')
    print('  makeable once the curve exists.')
    print()
    return curve


def section_c(curve):
    print('C. Choosing against a target, which is what the design actually is')
    print('-' * 74)
    print('%-16s %-11s %10s %13s' % ('target', 'best state', 'capacity',
                                     'unavailable'))
    out = []
    for t in (0.99, 0.999, 0.9999, 0.99999, 0.999999):
        r = state_meeting(curve, t)
        out.append((t, r))
        if r is None:
            print('%-16s %-11s %10s %13s'
                  % ('%.6g%%' % (t * 100), 'NONE', '--',
                     'no state meets it'))
        else:
            print('%-16s %-11s %7d Mb/s %9.2f min'
                  % ('%.6g%%' % (t * 100), r['name'], r['capacity_mbps'],
                     r['unavailable_minutes']))
    print()
    got = [(t, r) for t, r in out if r]
    if len(got) >= 2:
        hi, lo = got[0][1], got[-1][1]
        print('  Tightening the target from %.6g%% to %.6g%% costs %d Mb/s ---'
              % (got[0][0] * 100, got[-1][0] * 100,
                 hi['capacity_mbps'] - lo['capacity_mbps']))
        print('  %.0f per cent of the headline. That trade is the design, and a'
              % (100 * (1 - lo['capacity_mbps'] / float(hi['capacity_mbps']))))
        print('  chapter that quotes a headline rate and an availability target')
        print('  in the same sentence has not said which state it means.')
    miss = [t for t, r in out if r is None]
    if miss:
        print()
        print('  And the last row is the answer a design has to be able to give:')
        print('  on this path, with this state set and this fade, NO state meets')
        print('  %.6g%%. The fix is a bigger antenna, a lower frequency, a'
              % (miss[0] * 100))
        print('  shorter hop or a different medium --- not a lower modulation,')
        print('  because the curve has already run out.')
    print()
    return out


def section_d():
    print('D. What the fade assumption is doing to all of it')
    print('-' * 74)
    print('%-22s %12s %12s %12s'
          % ('fade exceeded 0.01%', '256QAM', '64QAM', 'QPSK'))
    rows = []
    for f in (12.0, 22.0, 35.0, 50.0):
        c = capacity_curve(LINK, fade_1pct_db=f)
        by = {r['name']: r for r in c}
        rows.append((f, by))
        print('%-22s %11.3f %11.3f %11.3f'
              % ('%.0f dB' % f, by['256QAM']['nines'], by['64QAM']['nines'],
                 by['QPSK']['nines']))
    print('  (figures are nines)')
    print()
    print('  One input --- how rainy the path is --- moves every availability in')
    print('  the table. Between the driest and wettest column here, QPSK goes')
    print('  from %.2f nines to %.2f.'
          % (rows[0][1]['QPSK']['nines'], rows[-1][1]['QPSK']['nines']))
    print()
    print('  Which is the honest warning about this whole script: the fade model')
    print('  in it is a placeholder fitted to nothing, and every availability it')
    print('  prints inherits that. The ARITHMETIC above the fade model is right')
    print('  and reusable; the fade model is not, and a real design replaces it')
    print('  with a dated propagation method and this path\'s own rain')
    print('  statistics before any of these numbers mean anything.')
    print()
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    if args.json:
        json.dump({'nines': {str(a): unavailable_minutes(a)
                             for a in (0.99, 0.999, 0.9999, 0.99999)},
                   'curve': capacity_curve(LINK, 22.0)},
                  sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write('\n')
        return 0
    print('Availability arithmetic for an adaptive link (Chapter 49)')
    print('The fade model below is a placeholder. The arithmetic above it is not.')
    print()
    a = section_a()
    curve = section_b()
    section_c(curve)
    section_d()
    print('What this does NOT establish')
    print('-' * 74)
    print('- The fade model is a two-parameter placeholder fitted to nothing.')
    print('  It is here so the availability arithmetic can be exercised. Do not')
    print('  size a link with it. Use a dated propagation method with this')
    print('  path\'s geometry, frequency, polarisation and rain statistics.')
    print('- Rain is not the only fade mechanism. Multipath, ducting,')
    print('  diffraction, obstruction and equipment failure are absent here and')
    print('  dominate on some paths and at some frequencies.')
    print('- The modulation states are invented. A real state set, with its')
    print('  capacities and thresholds, comes from the radio.')
    print('- An availability figure is a long-run expectation, not a guaranteed')
    print('  maximum outage, and it is met over the life of the link rather')
    print('  than in any particular year.')
    print('- Nothing here is an acceptance test. A designed availability is a')
    print('  prediction; the link meets it when it is measured over time.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
