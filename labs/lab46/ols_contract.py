#!/usr/bin/env python3
"""Lab 46.3 --- what an open line system has to say before "open" means anything.

WHY THIS LAB EXISTS
-------------------
The chapter said an open line system "accepts any compliant wavelength source"
and left the word compliant undefined.  That is the whole difficulty in one
adjective.  A line system cannot accept an arbitrary channel: it has a band, a
grid, an input power range its ingress can equalise, a channel count it was
engineered for, and a set of things it needs to be TOLD about a channel before
it can manage the amplifiers everybody else's channels share.  "Open" is not
the absence of those constraints.  It is the constraints being PUBLISHED, so
that a third party can engineer against them instead of asking one vendor's
permission.

So this builds the contract as something checkable: a line system declares an
envelope, a wavelength source declares its parameters, and the two are compared
clause by clause.  It also checks the thing the chapter never mentions --- that
the line system accepting a channel says nothing about whether the two MODEMS
at the ends of it can talk to each other, which is a separate agreement between
two transponders and not between a transponder and a line.

    python3 ols_contract.py
    python3 ols_contract.py --json
    python3 test_ols_contract.py

No line system, no transponder, no pluggable and no vendor documentation.  Every
envelope and every declaration below is invented to be plausible, and none of
them is any product's.  A real qualification is done against the line system
vendor's published envelope and the modem vendor's published parameters, and
then proved on the actual path.
"""
import argparse
import json
import math
import sys

# Flexgrid, as Chapter 45 and Lab 45.2 define it: TWO granularities.
ANCHOR_THZ = 193.1
CENTRE_GRANULARITY_GHZ = 6.25     # the n index
SLOT_GRANULARITY_GHZ = 12.5       # width index m for ONE allocated slot


class ContractError(ValueError):
    """The envelope or the declaration is not well formed."""


# ---------------------------------------------------------------------------
# what the line system publishes
# ---------------------------------------------------------------------------
def line_system(name, band_low_thz, band_high_thz, min_psd_dbm_per_ghz,
                max_psd_dbm_per_ghz, max_channels, managed_channels=True,
                centre_granularity_ghz=CENTRE_GRANULARITY_GHZ,
                slot_granularity_ghz=SLOT_GRANULARITY_GHZ,
                per_channel_osnr_db=None):
    """The envelope an open line system has to publish to be open.

    per_channel_osnr_db is what the line delivers on the path in question ---
    which is Lab 46.2's job, not this one's.  It is carried here so that the
    contract can state the honest thing: the line accepting the channel and the
    channel working are two different questions.
    """
    for value in (band_low_thz, band_high_thz, min_psd_dbm_per_ghz,
                  max_psd_dbm_per_ghz, centre_granularity_ghz,
                  slot_granularity_ghz):
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ContractError('envelope values must be finite numbers')
    if per_channel_osnr_db is not None and not math.isfinite(per_channel_osnr_db):
        raise ContractError('OSNR must be finite when declared')
    if type(max_channels) is not int:
        raise ContractError('channel count must be an integer')
    if min(band_low_thz, centre_granularity_ghz, slot_granularity_ghz) <= 0:
        raise ContractError('band frequency and granularities must be positive')
    if band_high_thz <= band_low_thz:
        raise ContractError('%s: the band is empty or inverted' % name)
    if max_psd_dbm_per_ghz < min_psd_dbm_per_ghz:
        raise ContractError('%s: the power window is inverted' % name)
    if max_channels < 1:
        raise ContractError('%s: a line system carries at least one channel'
                            % name)
    return {'name': name, 'band_low_thz': band_low_thz,
            'band_high_thz': band_high_thz,
            'min_psd_dbm_per_ghz': min_psd_dbm_per_ghz,
            'max_psd_dbm_per_ghz': max_psd_dbm_per_ghz,
            'max_channels': max_channels,
            'managed_channels': managed_channels,
            'centre_granularity_ghz': centre_granularity_ghz,
            'slot_granularity_ghz': slot_granularity_ghz,
            'per_channel_osnr_db': per_channel_osnr_db,
            'band_ghz': (band_high_thz - band_low_thz) * 1000.0}


# ---------------------------------------------------------------------------
# what the wavelength source declares
# ---------------------------------------------------------------------------
def wavelength_source(name, centre_thz, baud_gbd, width_ghz, launch_dbm,
                      required_osnr_db, mode_id, telemetry='none',
                      where='transponder shelf'):
    """A transponder, muxponder or a coherent pluggable in a router.

    mode_id is the thing two ends have to AGREE on: baud, modulation, FEC and
    its overhead, and any shaping.  Two modems interoperate when they implement
    the same mode, and not when they merely plug into the same line system.

    telemetry is how the line system learns this channel exists.  A pluggable
    in a router is managed by the IP team's systems, so unless somebody has
    arranged for the optical domain to be told, the line system is equalising
    amplifiers for a channel it does not know about.
    """
    for value in (centre_thz, baud_gbd, width_ghz, launch_dbm, required_osnr_db):
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ContractError('source values must be finite numbers')
    if centre_thz <= 0:
        raise ContractError('centre frequency must be positive')
    if baud_gbd <= 0:
        raise ContractError('%s: baud must be positive' % name)
    if width_ghz <= 0:
        raise ContractError('%s: occupied width must be positive' % name)
    if width_ghz < baud_gbd:
        raise ContractError('%s: a channel is at least as wide as its baud '
                            'rate; %.1f GHz for %.0f Gbaud is not physical'
                            % (name, width_ghz, baud_gbd))
    if telemetry not in ('none', 'manual', 'api'):
        raise ContractError('%s: telemetry is none, manual or api' % name)
    return {'name': name, 'centre_thz': centre_thz, 'baud_gbd': baud_gbd,
            'width_ghz': width_ghz, 'launch_dbm': launch_dbm,
            'required_osnr_db': required_osnr_db, 'mode_id': mode_id,
            'telemetry': telemetry, 'where': where,
            'psd_dbm_per_ghz': launch_dbm - 10.0 * math.log10(width_ghz)}


# ---------------------------------------------------------------------------
# the clauses
# ---------------------------------------------------------------------------
def slots_needed(width_ghz, slot_ghz=SLOT_GRANULARITY_GHZ):
    """Return width index m: one allocated slot is m times the width granularity.

    The legacy function name is retained for callers; m is not a channel count.
    """
    if not all(math.isfinite(x) and x > 0 for x in (width_ghz, slot_ghz)):
        raise ContractError('width and granularity must be finite and positive')
    return int(math.ceil(width_ghz / slot_ghz))


def n_index(centre_thz, granularity_ghz=CENTRE_GRANULARITY_GHZ):
    return (centre_thz - ANCHOR_THZ) * 1000.0 / granularity_ghz


def check_contract(ols, src, margin_db=2.0, channels_in_service=0):
    """Compare a declared source with a published envelope, clause by clause.

    Every clause returns (name, ok, detail).  A clause that cannot be evaluated
    because the envelope does not publish the figure returns ok=None, which is
    the honest answer and the commonest one in practice: the reason
    qualification is expensive is that half the clauses are unpublished.
    """
    if not math.isfinite(margin_db) or margin_db < 0:
        raise ContractError('margin must be finite and nonnegative')
    if type(channels_in_service) is not int or channels_in_service < 0:
        raise ContractError('channels in service must be a nonnegative integer')
    clauses = []

    # 1. The WHOLE allocated slot, including rounded width, must fit the band.
    m = slots_needed(src['width_ghz'], ols['slot_granularity_ghz'])
    half_thz = m * ols['slot_granularity_ghz'] / 2000.0
    low, high = src['centre_thz'] - half_thz, src['centre_thz'] + half_thz
    inside = low >= ols['band_low_thz'] - 1e-10 and high <= ols['band_high_thz'] + 1e-10
    clauses.append(('band', inside,
                    'allocated slot [%.5f, %.5f] THz %s [%.5f, %.5f]'
                    % (low, high, 'within' if inside else 'OUTSIDE',
                       ols['band_low_thz'], ols['band_high_thz'])))

    # 2. centre frequency on the grid --- the 6.25 GHz index, not the 12.5
    n = n_index(src['centre_thz'], ols['centre_granularity_ghz'])
    on_grid = abs(n - round(n)) < 1e-6
    clauses.append(('centre on grid', on_grid,
                    'n = %.3f (%s multiple of %.2f GHz from %.1f THz)'
                    % (n, 'is a' if on_grid else 'NOT a',
                       ols['centre_granularity_ghz'], ANCHOR_THZ)))

    # 3. slot width
    m = slots_needed(src['width_ghz'], ols['slot_granularity_ghz'])
    waste = m * ols['slot_granularity_ghz'] - src['width_ghz']
    clauses.append(('slot width', True,
                    '%.1f GHz uses one slot, width index m=%d at %.1f GHz; %.1f GHz is '
                    'bought and unusable'
                    % (src['width_ghz'], m, ols['slot_granularity_ghz'], waste)))

    # 4. power spectral density --- the figure the line system equalises on,
    #    which is not the launch power
    psd = src['psd_dbm_per_ghz']
    in_window = ols['min_psd_dbm_per_ghz'] <= psd <= ols['max_psd_dbm_per_ghz']
    clauses.append(('power spectral density', in_window,
                    '%+.2f dBm/GHz (%+.1f dBm over %.1f GHz) %s [%+.2f, %+.2f]'
                    % (psd, src['launch_dbm'], src['width_ghz'],
                       'within' if in_window else 'OUTSIDE',
                       ols['min_psd_dbm_per_ghz'], ols['max_psd_dbm_per_ghz'])))

    # 5. channel count --- the line system was engineered for a fill
    room = channels_in_service < ols['max_channels']
    clauses.append(('channel count', room,
                    '%d in service against %d engineered'
                    % (channels_in_service + 1, ols['max_channels'])))

    # 6. the line system has to know the channel is there
    known = ols['managed_channels'] is False or src['telemetry'] != 'none'
    clauses.append(('visibility to the line system', known,
                    'source reports by %r from a %s'
                    % (src['telemetry'], src['where'])))

    # 7. OSNR --- evaluated only if the envelope says what the path delivers
    if ols['per_channel_osnr_db'] is None:
        clauses.append(('OSNR on the path', None,
                        'the envelope does not state it; this is Lab 46.2 and '
                        'a planning tool, not a compatibility clause'))
    else:
        ok = ols['per_channel_osnr_db'] - margin_db >= src['required_osnr_db']
        clauses.append(('OSNR on the path', ok,
                        '%.1f dB delivered, %.1f dB required, %.1f dB margin '
                        'wanted' % (ols['per_channel_osnr_db'],
                                    src['required_osnr_db'], margin_db)))

    failed = [c for c in clauses if c[1] is False]
    unknown = [c for c in clauses if c[1] is None]
    return {'ols': ols['name'], 'source': src['name'], 'clauses': clauses,
            'accepted': not failed,
            'failed': [c[0] for c in failed],
            'unevaluated': [c[0] for c in unknown],
            'slots': m,  # legacy key: width index, not number of channels
            'width_index_m': m, 'allocated_slot_thz': [low, high]}


def modems_interoperate(a, b):
    """Two ends of a wavelength, which is a different question entirely.

    The line system is not a party to this.  This fixture compares mode identifiers only; it does not demonstrate
    actual modem interoperability. Two ends need an agreed compatible mode --- the same baud, modulation, FEC
    and overhead and shaping.  A line system that accepts both of them has not
    made them talk.
    """
    same = a['mode_id'] == b['mode_id']
    return {'a': a['name'], 'b': b['name'], 'interoperate': same,
            'a_mode': a['mode_id'], 'b_mode': b['mode_id'],
            'why': 'same mode' if same else
                   'different modes: %r against %r' % (a['mode_id'], b['mode_id'])}


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
OLS = line_system('metro open line system', 191.300, 196.100,
                  min_psd_dbm_per_ghz=-26.0, max_psd_dbm_per_ghz=-20.0,
                  max_channels=64, per_channel_osnr_db=29.0)

SOURCES = [
    wavelength_source('the line system vendor\'s own transponder',
                      centre_thz=193.100, baud_gbd=118, width_ghz=137.5,
                      launch_dbm=-3.0, required_osnr_db=20.0,
                      mode_id='118Gbd-16QAM-oFEC-15%', telemetry='api'),
    wavelength_source('a third party transponder, same mode',
                      centre_thz=193.150, baud_gbd=118, width_ghz=137.5,
                      launch_dbm=-3.0, required_osnr_db=20.0,
                      mode_id='118Gbd-16QAM-oFEC-15%', telemetry='api'),
    wavelength_source('a pluggable in a router, nobody told the optical NMS',
                      centre_thz=193.200, baud_gbd=118, width_ghz=137.5,
                      launch_dbm=-3.0, required_osnr_db=20.0,
                      mode_id='118Gbd-16QAM-oFEC-15%', telemetry='none',
                      where='router faceplate'),
    wavelength_source('a pluggable running hot',
                      centre_thz=193.250, baud_gbd=118, width_ghz=137.5,
                      launch_dbm=+3.0, required_osnr_db=20.0,
                      mode_id='118Gbd-16QAM-oFEC-15%', telemetry='api'),
    wavelength_source('a wide channel centred off the 6.25 GHz grid',
                      centre_thz=193.104, baud_gbd=190, width_ghz=225.0,
                      launch_dbm=-1.0, required_osnr_db=22.0,
                      mode_id='190Gbd-16QAM-oFEC-15%', telemetry='api'),
    wavelength_source('a third party transponder, different mode',
                      centre_thz=193.300, baud_gbd=118, width_ghz=137.5,
                      launch_dbm=-3.0, required_osnr_db=17.5,
                      mode_id='118Gbd-8QAM-cFEC-25%', telemetry='api'),
    wavelength_source('an L-band source on a C-band line',
                      centre_thz=186.500, baud_gbd=118, width_ghz=137.5,
                      launch_dbm=-3.0, required_osnr_db=20.0,
                      mode_id='118Gbd-16QAM-oFEC-15%', telemetry='api'),
]


def verdict(r):
    if r['accepted']:
        return 'accepted' + (' (%d clause unevaluated)' % len(r['unevaluated'])
                             if r['unevaluated'] else '')
    return 'REFUSED: ' + ', '.join(r['failed'])


def section_a():
    print('A. The envelope, which is what "open" actually consists of')
    print('-' * 74)
    print('  %-26s %s' % ('line system', OLS['name']))
    print('  %-26s %.3f -- %.3f THz (%.0f GHz)'
          % ('band', OLS['band_low_thz'], OLS['band_high_thz'], OLS['band_ghz']))
    print('  %-26s %.2f GHz centre index, %.1f GHz slot width'
          % ('grid', OLS['centre_granularity_ghz'], OLS['slot_granularity_ghz']))
    print('  %-26s %+.1f to %+.1f dBm/GHz'
          % ('power spectral density', OLS['min_psd_dbm_per_ghz'],
             OLS['max_psd_dbm_per_ghz']))
    print('  %-26s %d' % ('engineered channel count', OLS['max_channels']))
    print('  %-26s %s' % ('must be told of a channel',
                          'yes' if OLS['managed_channels'] else 'no'))
    print()
    print('  None of that is a restriction that makes the system less open.  It')
    print('  is the published envelope a third party engineers against --- which')
    print('  is the difference between an open line system and a closed one.  A')
    print('  closed system has the same constraints and does not tell you them.')
    print()


def section_b():
    print('B. Seven sources against one envelope')
    print('-' * 74)
    results = []
    for src in SOURCES:
        r = check_contract(OLS, src, channels_in_service=12)
        results.append((src, r))
        print('  %-48s %s' % (src['name'][:48], verdict(r)))
    print()
    for src, r in results:
        if r['accepted']:
            continue
        print('  %s' % src['name'])
        for cname, ok, detail in r['clauses']:
            if ok is False:
                print('      %-24s %s' % (cname, detail))
    print()
    print('  Every refusal is a different clause, and only one of them is about')
    print('  the band --- which is the one an engineer would have guessed.  The')
    print('  pluggable running hot is inside its own specification and outside')
    print('  the line system\'s input window, so it is a perfectly good')
    print('  transponder that will degrade every other channel through the')
    print('  amplifier it shares.  The unreported pluggable is worse: it is')
    print('  optically fine and the line system is equalising for a channel it')
    print('  has not been told exists.')
    print()
    return results


def section_c():
    print('C. The clause the line system cannot settle')
    print('-' * 74)
    a = SOURCES[0]
    b = [x for x in SOURCES if x['name'].endswith('same mode')][0]
    c = [x for x in SOURCES if x['name'].endswith('different mode')][0]
    for x, y in ((a, b), (a, c)):
        r = modems_interoperate(x, y)
        print('  %s\n    <-> %-46s %s'
              % (x['name'], y['name'],
                 'interoperate' if r['interoperate'] else 'DO NOT'))
        if not r['interoperate']:
            print('      %s' % r['why'])
    print()
    print('  Both of those sources were accepted by the line system in section B.')
    print('  Acceptance is a statement about the LINE: the channel is inside the')
    print('  band, on the grid, within the power window and declared.  Whether')
    print('  the two ends carry traffic to each other is an agreement between')
    print('  two MODEMS about a mode, and the line system is not a party to it.')
    print('  This is the clause that turns a disaggregated optical layer into a')
    print('  procurement problem: you can buy the line from one supplier and the')
    print('  transponders from another, but you cannot buy the two ENDS of a')
    print('  wavelength from two different suppliers and assume they meet.')
    print()


def section_d():
    print('D. What acceptance still does not buy you')
    print('-' * 74)
    src = SOURCES[1]
    strict = line_system('the same line, on a longer path', 191.300, 196.100,
                         min_psd_dbm_per_ghz=-26.0, max_psd_dbm_per_ghz=-20.0,
                         max_channels=64, per_channel_osnr_db=20.5)
    silent = line_system('a line system that publishes no OSNR',
                         191.300, 196.100, min_psd_dbm_per_ghz=-26.0,
                         max_psd_dbm_per_ghz=-20.0, max_channels=64)
    for ols in (OLS, strict, silent):
        r = check_contract(ols, src)
        print('  %-40s %s' % (ols['name'][:40], verdict(r)))
    print()
    print('  The same source and the same envelope, on a path that delivers')
    print('  8.5 dB less.  Compatibility did not change; the service did.  And')
    print('  the third line publishes no OSNR at all, so the contract cannot be')
    print('  completed from paperwork: somebody has to compute the path')
    print('  (Lab 46.2) and then prove it on the fibre.')
    print()
    print('  That is the integration responsibility disaggregation transfers.')
    print('  It is not "check the transponder is compliant".  It is: hold the')
    print('  envelope, hold the declaration, compute the path, prove the pair,')
    print('  and own the answer when the three of them disagree.')
    print()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)

    if args.json:
        json.dump({'line_system': OLS,
                   'results': [check_contract(OLS, s, channels_in_service=12)
                               for s in SOURCES]},
                  sys.stdout, indent=1, sort_keys=True, default=str)
        sys.stdout.write('\n')
        return 0

    print('The compatibility contract an open line system needs')
    print('(Chapter 46, sections 2 and 3).  Every figure below is invented to')
    print('be plausible and none of them is any product\'s.')
    print()
    section_a()
    section_b()
    section_c()
    section_d()
    print('What this does NOT establish')
    print('-' * 74)
    print('- No line system, no transponder, no pluggable, no measurement and')
    print('  no vendor documentation.  The clause list is the point; the numbers')
    print('  in it are invented.')
    print('- The clause list is not complete.  A real envelope also covers')
    print('  transient control when channels are added or removed, ripple and')
    print('  tilt across the band, polarisation-dependent loss, reflectance,')
    print('  Raman pumping where used, and the management interface in detail.')
    print('- Passing every clause is not a qualification.  A qualification is')
    print('  the pair proved on the actual path, in both directions, under the')
    print('  channel loading it will really see.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
