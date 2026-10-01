#!/usr/bin/env python3
"""Lab 49.1 --- propagation delay, computed, for every medium in the chapter.

WHY THIS LAB EXISTS
-------------------
Chapter 49 shipped no lab at all, and it is the chapter in this part that makes
the most numerical claims.  Three of them do not survive arithmetic.

  THE MEO ROW CONTRADICTS ITSELF.  The satellite table gave MEO an altitude of
  8,000 to 20,000 km and a round-trip latency of 100 to 150 ms.  A request and
  its reply cross the gap FOUR times --- up to the satellite, down to the
  gateway, up again, down again.  At 20,000 km that is 80,000 km, which light
  covers in 266.9 ms: already 78% above the row's own upper figure, before any
  slant geometry, any inter-satellite hop, any gateway and any queue.  The
  altitudes that would actually give 100 to 150 ms are about 7,500 to 11,200 km.

  "ALTITUDE SETS LATENCY" IS TRUE OF GEO AND FALSE OF LEO.  At 35,786 km,
  propagation alone is 477.5 ms and nothing else in the path matters much.  At
  550 km it is 7.3 ms overhead, against a quoted service latency of 25 to 70 ms
  --- so between two thirds and nine tenths of the LEO figure is NOT altitude.
  It is geometry, gateways, scheduling, the terrestrial leg beyond the gateway
  and queuing.  A chapter that explains LEO by altitude alone has explained the
  small part.

  WIRELESS IS SLOWER THAN FIBRE ONLY IN CAPACITY.  The chapter said wireless is
  never chosen to save money or time on a route fibre could serve, and wins only
  on "time, terrain and reach".  It left out the one thing radio beats fibre at
  outright: light travels through air at very nearly c and through fibre at
  c/1.468, so a microwave hop is 47% quicker per kilometre --- before counting
  that the radio path is straight and the fibre route is not.  That is why
  latency-sensitive traffic pays for microwave on routes with fibre already in
  the ground.

    python3 latency_by_path.py
    python3 latency_by_path.py --json
    python3 test_latency_by_path.py

No radio, no satellite, no fibre and no measurement.  This is geometry and the
speed of light.  Refractive indices, route factors, altitudes and elevation
angles are stated inputs; every figure derived from them is arithmetic, and none
of it is a service-level latency, which is dominated by things this script does
not model.
"""
import argparse
import json
import math
import sys

C_KM_S = 299792.458          # speed of light in vacuum, km/s
EARTH_RADIUS_KM = 6371.0     # mean radius

# Refractive indices.  Air is near 1 at radio frequencies; the fibre figure is
# the group index of standard single-mode fibre near 1550 nm, as Chapter 43.
INDEX = {
    'vacuum': 1.0,
    'air (radio)': 1.000293,
    'fibre': 1.4682,
}


class PathError(ValueError):
    """The described path cannot be evaluated."""


def us_per_km(medium='fibre'):
    if medium not in INDEX:
        raise PathError('unknown medium %r; known: %s'
                        % (medium, ', '.join(sorted(INDEX))))
    return 1e6 / (C_KM_S / INDEX[medium])


# ---------------------------------------------------------------------------
# terrestrial
# ---------------------------------------------------------------------------
def terrestrial_ms(straight_km, medium='fibre', route_factor=1.0,
                   round_trip=True):
    """One-way or round-trip propagation over a terrestrial path.

    route_factor is how much longer the actual path is than the straight line.
    A radio hop is essentially straight, so 1.0.  A fibre route follows roads,
    ducts and rights of way and is longer; 1.3 to 1.5 is ordinary, and it is a
    property of the route rather than of the fibre.
    """
    if straight_km <= 0:
        raise PathError('a distance is positive, got %r' % (straight_km,))
    if route_factor < 1.0:
        raise PathError('a route cannot be shorter than the straight line, '
                        'got a factor of %r' % (route_factor,))
    km = straight_km * route_factor
    ms = km * us_per_km(medium) / 1000.0
    return {'medium': medium, 'straight_km': straight_km,
            'route_factor': route_factor, 'path_km': km,
            'one_way_ms': ms, 'ms': ms * (2 if round_trip else 1),
            'round_trip': round_trip}


# ---------------------------------------------------------------------------
# satellite geometry
# ---------------------------------------------------------------------------
def slant_range_km(altitude_km, elevation_deg=90.0, earth_km=EARTH_RADIUS_KM):
    """Distance from a ground station to a satellite at a given elevation.

    Straight up is the best case and almost never the real one: a terminal
    works a satellite down to some minimum elevation, and the slant range at
    that angle is materially longer.  At 550 km the overhead range is 550 km
    and the range at 25 degrees is 1,123 km --- more than double.
    """
    if altitude_km <= 0:
        raise PathError('an altitude is positive, got %r' % (altitude_km,))
    if not 0 < elevation_deg <= 90:
        raise PathError('an elevation angle is in (0, 90], got %r'
                        % (elevation_deg,))
    e = math.radians(elevation_deg)
    s = earth_km * math.sin(e)
    return math.sqrt(s * s + 2 * earth_km * altitude_km
                     + altitude_km * altitude_km) - s


def satellite_ms(altitude_km, elevation_deg=90.0, legs=4,
                 inter_satellite_km=0.0, terrestrial_km=0.0,
                 terrestrial_route_factor=1.0):
    """Propagation for a satellite path, counting the legs honestly.

    legs=4 is the ordinary bent-pipe round trip: user up, gateway down, gateway
    up, user down.  legs=2 is a one-way hop.  A constellation that routes
    between its own satellites adds inter_satellite_km on top, and whatever
    terrestrial distance lies beyond the gateway is terrestrial_km.

    This is PROPAGATION ONLY.  It is a lower bound on latency and nothing else:
    scheduling, framing, the access protocol, handover between satellites,
    processing and queuing are all absent, and in low orbits they are most of
    the answer.
    """
    if legs < 1:
        raise PathError('a path has at least one leg')
    d = slant_range_km(altitude_km, elevation_deg)
    space_km = d * legs + inter_satellite_km
    ms = space_km / C_KM_S * 1000.0
    ground = 0.0
    if terrestrial_km:
        ground = terrestrial_ms(terrestrial_km, 'fibre',
                                terrestrial_route_factor,
                                round_trip=True)['ms']
    return {'altitude_km': altitude_km, 'elevation_deg': elevation_deg,
            'slant_range_km': d, 'legs': legs,
            'inter_satellite_km': inter_satellite_km,
            'space_km': space_km, 'space_ms': ms,
            'terrestrial_ms': ground, 'ms': ms + ground}


# ---------------------------------------------------------------------------
# what a quoted service latency is actually made of
# ---------------------------------------------------------------------------
def non_propagation_share(quoted_ms, propagation_ms):
    """Residual above a supplied propagation figure (legacy function name).

    If the supplied figure is only a lower bound, residual includes unmodelled
    propagation as well as non-propagation delays. It does not isolate either.
    """
    if quoted_ms <= 0:
        raise PathError('a quoted latency is positive')
    if propagation_ms > quoted_ms:
        return {'quoted_ms': quoted_ms, 'propagation_ms': propagation_ms,
                'other_ms': quoted_ms - propagation_ms, 'share': None,
                'impossible': True}
    other = quoted_ms - propagation_ms
    return {'quoted_ms': quoted_ms, 'propagation_ms': propagation_ms,
            'other_ms': other, 'share': other / quoted_ms, 'impossible': False}


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
# The satellite table exactly as the chapter printed it, so the arithmetic can
# be run against the chapter's own figures rather than against new ones.
CHAPTER_TABLE = [
    ('GEO', 35786, 35786, 600, 700),
    ('MEO', 8000, 20000, 100, 150),
    ('LEO', 550, 1200, 25, 70),
]


def section_a():
    print('A. The chapter\'s own table, checked against its own altitudes')
    print('-' * 74)
    print('%-5s %-18s %-16s %-18s %s'
          % ('orbit', 'altitude', 'claimed RTT', 'propagation alone', 'verdict'))
    out = []
    for name, lo, hi, tlo, thi in CHAPTER_TABLE:
        plo = satellite_ms(lo)['ms']
        phi = satellite_ms(hi)['ms']
        ok = phi <= thi
        out.append((name, lo, hi, tlo, thi, plo, phi, ok))
        print('%-5s %-18s %-16s %-18s %s'
              % (name, '%s-%s km' % ('{:,}'.format(lo), '{:,}'.format(hi)),
                 '%d-%d ms' % (tlo, thi),
                 '%.1f-%.1f ms' % (plo, phi),
                 'consistent' if ok else 'IMPOSSIBLE'))
    print()
    bad = [r for r in out if not r[7]]
    for r in bad:
        over = 100 * (r[6] / r[4] - 1)
        lo_km = r[3] / 1000.0 * C_KM_S / 4
        hi_km = r[4] / 1000.0 * C_KM_S / 4
        print('  %s: at its own upper altitude of %s km the four legs of a'
              % (r[0], '{:,}'.format(r[2])))
        print('  request and its reply are %.1f ms of pure propagation --- %.0f%%'
              % (r[6], over))
        print('  above the row\'s own upper figure, before geometry, gateways or')
        print('  queues. The altitudes that would give %d-%d ms are about'
              % (r[3], r[4]))
        print('  %s to %s km.' % ('{:,.0f}'.format(lo_km), '{:,.0f}'.format(hi_km)))
    print()
    return out


def section_b():
    print('B. Straight up is the best case and almost never the real one')
    print('-' * 74)
    print('%10s %14s %14s %14s %14s'
          % ('altitude', 'overhead', '40 deg', '25 deg', '10 deg'))
    rows = []
    for h in (550, 1200, 8000, 20000, 35786):
        line = []
        for eps in (90, 40, 25, 10):
            s = satellite_ms(h, eps)
            line.append(s)
        rows.append((h, line))
        print('%8s km %11.1f ms %11.1f ms %11.1f ms %11.1f ms'
              % ('{:,}'.format(h), line[0]['ms'], line[1]['ms'],
                 line[2]['ms'], line[3]['ms']))
    print()
    leo = rows[0][1]
    print('  A terminal works a satellite down to some minimum elevation, and')
    print('  the geometry at that angle is what the link has to close. At 550 km')
    print('  the range doubles between overhead and 25 degrees, and the')
    print('  propagation doubles with it: %.1f ms against %.1f ms.'
          % (leo[2]['ms'], leo[0]['ms']))
    print('  The effect is proportionally largest in the LOWEST orbits, which is')
    print('  the opposite of where a table of altitudes suggests the subtlety is.')
    print()
    return rows


def section_c():
    print('C. What a quoted LEO latency is actually made of')
    print('-' * 74)
    prop = satellite_ms(550, 25.0)['ms']
    print('  550 km, 25 degrees elevation, bent pipe: %.1f ms of propagation.'
          % prop)
    print()
    print('%12s %14s %14s %12s' % ('quoted', 'propagation', 'everything else',
                                   'share'))
    out = []
    for q in (25.0, 40.0, 70.0):
        r = non_propagation_share(q, prop)
        out.append(r)
        print('%9.0f ms %11.1f ms %11.1f ms %11.0f%%'
              % (q, r['propagation_ms'], r['other_ms'], 100 * r['share']))
    print()
    print('  Between %.0f and %.0f per cent remains ABOVE this modelled path'
          % (100 * out[0]['share'], 100 * out[-1]['share']))
    print('  propagation. Extra space/ground distance can add propagation too;')
    print('  scheduling, processing and queuing also contribute. Measure the path.')
    print()
    geo = satellite_ms(35786)['ms']
    rgeo = non_propagation_share(650.0, geo)
    print('  Compare GEO: %.1f ms of propagation inside a quoted 650, so only'
          % geo)
    print('  %.0f per cent is anything else. THAT is a latency altitude sets.'
          % (100 * rgeo['share']))
    print('  Geometry gives a lower bound; actual endpoints and route determine')
    print('  how much of a measured RTT is propagation.')
    print()
    return out


def section_d():
    print('D. The thing radio beats fibre at')
    print('-' * 74)
    print('%-22s %12s' % ('medium', 'per km'))
    for m in ('vacuum', 'air (radio)', 'fibre'):
        print('%-22s %9.3f us' % (m, us_per_km(m)))
    print()
    print('  %.1f per cent slower in fibre, per kilometre, before the route is'
          % (100 * (INDEX['fibre'] / INDEX['air (radio)'] - 1)))
    print('  considered. And the route matters as much: a radio hop is straight,')
    print('  a fibre route follows roads and rights of way.')
    print()
    print('%-34s %12s %12s' % ('100 km between two sites', 'one way', 'round trip'))
    radio = terrestrial_ms(100, 'air (radio)', 1.0)
    for rf in (1.0, 1.3, 1.5):
        f = terrestrial_ms(100, 'fibre', rf)
        print('%-34s %9.3f ms %9.3f ms'
              % ('fibre, route factor %.1f' % rf, f['one_way_ms'], f['ms']))
    print('%-34s %9.3f ms %9.3f ms'
          % ('microwave, straight', radio['one_way_ms'], radio['ms']))
    print()
    f13 = terrestrial_ms(100, 'fibre', 1.3)
    print('  Against an ordinary 1.3 route factor the radio hop saves %.3f ms'
          % (f13['ms'] - radio['ms']))
    print('  on a round trip over 100 km --- %.0f per cent. That is not a rounding'
          % (100 * (1 - radio['ms'] / f13['ms'])))
    print('  error to the people who pay for it, and it is the reason microwave')
    print('  is bought on routes where fibre is already in the ground. Wireless')
    print('  does not win only on time, terrain and reach.')
    print()
    print('  What it does not win is capacity, and the chapter was right about')
    print('  that. Both things are true at once, which is why the choice is a')
    print('  comparison of requirements rather than a ranking of media.')
    print()
    return {'radio': radio, 'fibre_1_3': f13}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    if args.json:
        json.dump({'us_per_km': {m: us_per_km(m) for m in INDEX},
                   'orbits': {n: {'overhead_ms': satellite_ms(lo)['ms'],
                                  'upper_overhead_ms': satellite_ms(hi)['ms']}
                              for n, lo, hi, _, _ in CHAPTER_TABLE}},
                  sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write('\n')
        return 0
    print('Propagation delay by path (Chapter 49)')
    print('Geometry and the speed of light. Nothing here was measured, and no')
    print('figure below is a service latency.')
    print()
    section_a()
    section_b()
    section_c()
    section_d()
    print('What this does NOT establish')
    print('-' * 74)
    print('- Propagation is a LOWER BOUND and usually not the largest term.')
    print('  Scheduling, framing, the access protocol, satellite handover,')
    print('  processing and queuing are not modelled at all.')
    print('- No equipment and no measurement. Indices, route factors, altitudes')
    print('  and elevation angles are stated inputs.')
    print('- The satellite model is a bent pipe with an optional inter-satellite')
    print('  distance. A real constellation routes over several hops whose')
    print('  lengths change as the satellites move, so its latency varies with')
    print('  time in a way no static figure captures.')
    print('- Nothing here says which medium to use. It says which arithmetic a')
    print('  claim about latency has to survive.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
