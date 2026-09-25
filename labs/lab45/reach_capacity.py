#!/usr/bin/env python3
"""Lab 45.1 --- from a path to an OSNR to a mode, and what the mode actually carries.

WHY THIS VERSION EXISTS
-----------------------
The previous script took an OSNR as an input, labelled each case with a distance
--- "metro DCI (40 km)", "long-haul (2000 km)" --- and picked the highest-order
modulation that fitted.  Three things were wrong with that.

  It could not infer reach.  Nothing in it related kilometres to OSNR; the
  distances were decoration attached to numbers somebody had typed in, which
  invites the reader to believe a model that was not there.  This version
  computes the OSNR from a described path, so the distance is an input that
  does something.

  Its advice on failure was to "shorten the span or add amplification".
  Amplification does not raise OSNR.  Every amplifier restores power and ADDS
  noise, so an extra amplifier on the same path makes the OSNR worse --- which
  is the central lesson of the preceding chapter, contradicted in the one line
  where a reader in trouble would look.

  It reported baud x bits x 2 as capacity.  That is the LINE rate, which
  includes the FEC overhead.  What you can sell is the payload underneath it,
  and the difference is not small: at 118 Gbaud and 16QAM the line carries
  944 Gb/s and its 20% FEC-only overhead model leaves about 786.7 Gb/s,
  before other framing overhead. This is not an 800 Gb/s client interface.

A fourth correction is structural.  A transponder's "mode" is not a modulation.
It is a combination of baud rate, modulation, FEC and its overhead, and often
constellation shaping --- so two modes both called 16QAM can differ in reach by
a long way, and choosing "the modulation" is not a thing you do.

    python3 reach_capacity.py
    python3 reach_capacity.py --json
    python3 test_reach_capacity.py

No transponder, amplifier, ROADM or planning tool. Arithmetic on stated inputs.
"""
import argparse
import json
import math
import sys

NOISE_REF_DBM = -58.0     # 10log10(h.nu.B_ref), 1550 nm in 0.1 nm, as Chapter 44


class ModeError(ValueError):
    """The path or the mode set cannot be evaluated."""


# --------------------------------------------------------------------------
# a mode is four numbers, not one word
# --------------------------------------------------------------------------
def mode(name, baud_gbd, bits_per_symbol_per_pol, fec_overhead_percent,
         required_osnr_db):
    if baud_gbd <= 0:
        raise ModeError('%s: baud must be positive' % name)
    if bits_per_symbol_per_pol <= 0:
        raise ModeError('%s: bits per symbol must be positive' % name)
    if fec_overhead_percent < 0:
        raise ModeError('%s: FEC overhead is not negative' % name)
    line_gbps = baud_gbd * bits_per_symbol_per_pol * 2.0
    client_gbps = line_gbps / (1.0 + fec_overhead_percent / 100.0)
    return {'name': name, 'baud_gbd': baud_gbd,
            'bits_per_symbol_per_pol': bits_per_symbol_per_pol,
            'fec_overhead_percent': fec_overhead_percent,
            'required_osnr_db': required_osnr_db,
            'line_gbps': line_gbps, 'client_gbps': client_gbps}


# ILLUSTRATIVE MODES. Not any vendor's, not measured, and not comparable with
# a datasheet: the required OSNR of a real mode depends on its FEC, its shaping
# and the transponder's own implementation, and comes from its vendor.
MODES = [
    mode('QPSK, 60 Gbaud', 60, 2, 20.0, 11.5),
    mode('QPSK, 118 Gbaud', 118, 2, 20.0, 14.5),
    mode('8QAM, 118 Gbaud', 118, 3, 20.0, 17.5),
    mode('16QAM, 60 Gbaud', 60, 4, 20.0, 17.0),
    mode('16QAM, 118 Gbaud', 118, 4, 20.0, 20.0),
]


# --------------------------------------------------------------------------
# a path, and the OSNR it delivers
# --------------------------------------------------------------------------
def path_osnr_db(launch_dbm, fibre_spans, span_km, roadm_passes=0,
                 fibre_db_per_km=0.22, amp_nf_db=5.5, roadm_loss_db=16.0,
                 roadm_filter_penalty_db=0.4):
    """OSNR at the far end, counting every amplified section including the nodes.

    This teaching model represents each ROADM pass as another AMPLIFIED
    SECTION. Actual equipment may place amplification differently; the node's
    insertion loss has to be recovered, by an amplifier that adds its own noise,
    and the channel is narrowed a little on the way through. So a metro ring
    with eight nodes has eight noise contributions that the kilometres never
    mention.

    Noise powers add, so the reciprocals of the per-section OSNRs add.
    """
    if fibre_spans < 1:
        raise ModeError('a path has at least one fibre span, got %r'
                        % (fibre_spans,))
    if span_km <= 0:
        raise ModeError('a span length is positive, got %r' % (span_km,))
    if roadm_passes < 0:
        raise ModeError('ROADM passes is not negative')
    if amp_nf_db < 0 or fibre_db_per_km <= 0 or roadm_loss_db < 0:
        raise ModeError('the noise figure, attenuation and node loss must be '
                        'sensible')

    span_loss = span_km * fibre_db_per_km
    sections = [('fibre span, %g km' % span_km, span_loss)] * int(fibre_spans)
    sections += [('ROADM node', roadm_loss_db)] * int(roadm_passes)

    inv = 0.0
    detail = []
    for label, loss in sections:
        o = launch_dbm - loss - amp_nf_db - NOISE_REF_DBM
        detail.append({'section': label, 'loss_db': loss, 'osnr_db': o})
        inv += 10.0 ** (-o / 10.0)
    ase_db = -10.0 * math.log10(inv)
    filt = roadm_passes * roadm_filter_penalty_db
    return {'span_km': span_km, 'fibre_spans': fibre_spans,
            'total_km': span_km * fibre_spans, 'span_loss_db': span_loss,
            'roadm_passes': roadm_passes, 'sections': len(sections),
            'section_detail': detail, 'ase_osnr_db': ase_db,
            'filter_penalty_db': filt, 'osnr_db': ase_db - filt}


def feasible(osnr_db, modes=None, margin_db=2.0):
    """Which modes work, and which is the best of them.

    'Best' is the highest client rate that fits, which is not always the
    highest-order modulation: a lower-order format at a higher baud can beat a
    higher-order one at a lower baud, and the reason to compute rather than
    reason by rule is exactly that.
    """
    ms = modes or MODES
    if margin_db < 0:
        raise ModeError('the margin is not negative')
    ok = [m for m in ms if osnr_db - margin_db >= m['required_osnr_db']]
    return {'osnr_db': osnr_db, 'margin_db': margin_db,
            'usable_osnr_db': osnr_db - margin_db,
            'feasible': [m['name'] for m in ok],
            'best': max(ok, key=lambda m: m['client_gbps']) if ok else None}


def what_would_help(path, modes=None, margin_db=2.0):
    """The options when nothing fits, and what each actually does.

    Written as a list because the single sentence the previous version offered
    --- "shorten the span or add amplification" --- contains a phrase meaning
    two different things, one of which helps and one of which does nothing.
    """
    base = path_osnr_db(**path)
    out = []

    def trial(label, note, **over):
        p = dict(path)
        p.update(over)
        r = path_osnr_db(**p)
        out.append({'change': label, 'osnr_db': r['osnr_db'],
                    'delta_db': r['osnr_db'] - base['osnr_db'],
                    'feasible': feasible(r['osnr_db'], modes, margin_db)['feasible'],
                    'note': note})

    trial('nothing changed', 'the path as described')
    trial('more gain at the same points',
          'nothing in the path changed, so nothing in the OSNR changed: the '
          'noise is in the signal already and gain amplifies that too')
    trial('one additional hut per original span, halving every span',
          'amplification that DOES help: each amplifier now recovers half '
          'the loss',
          span_km=path['span_km'] / 2.0,
          fibre_spans=path['fibre_spans'] * 2)
    trial('a quieter amplifier, 4.5 dB noise figure',
          'buys OSNR on every section at once, and is bought once',
          amp_nf_db=4.5)
    trial('one fewer ROADM pass',
          'removes a whole amplified section and its filtering --- often the '
          'cheapest decibel in a metro design',
          roadm_passes=max(0, path['roadm_passes'] - 1))
    trial('launch power up 3 dB',
          'helps against ASE alone, but Chapter 44 has the nonlinear optimum '
          'past which it makes the link worse',
          launch_dbm=path['launch_dbm'] + 3.0)
    return {'base': base, 'options': out}


PATHS = [
    ('metro ring, 40 km, 2 ROADM passes',
     dict(launch_dbm=-3.0, fibre_spans=2, span_km=20, roadm_passes=2)),
    ('metro ring, 40 km, 8 ROADM passes',
     dict(launch_dbm=-3.0, fibre_spans=8, span_km=5, roadm_passes=8)),
    ('regional, 6 x 80 km, 2 ROADM passes',
     dict(launch_dbm=-3.0, fibre_spans=6, span_km=80, roadm_passes=2)),
    ('long-haul, 25 x 80 km, 4 ROADM passes',
     dict(launch_dbm=-3.0, fibre_spans=25, span_km=80, roadm_passes=4)),
]


def analyse():
    rows = []
    for name, p in PATHS:
        r = path_osnr_db(**p)
        f = feasible(r['osnr_db'])
        rows.append({'name': name, 'path': p, 'osnr': r, 'feasible': f})
    return {'modes': MODES, 'rows': rows,
            'options': what_would_help(PATHS[3][1])}


def report(a):
    print('From a path, to an OSNR, to a mode. ILLUSTRATIVE inputs: no')
    print('transponder, amplifier, ROADM or planning tool was involved, and no')
    print("mode below is any vendor's.\n")

    print('The modes, as four numbers each rather than one word:')
    print('%22s | %7s | %6s | %9s | %9s | %9s'
          % ('mode', 'baud', 'b/sym', 'needs OSNR', 'line rate', 'client'))
    print('-' * 82)
    for m in a['modes']:
        print('%22s | %5.0f G | %5d  | %8.1f dB | %7.0f G | %7.0f G'
              % (m['name'], m['baud_gbd'], m['bits_per_symbol_per_pol'],
                 m['required_osnr_db'], m['line_gbps'], m['client_gbps']))
    print('\nThe last two columns are not the same number. Baud x bits x two')
    print('polarisations is the LINE rate and it includes the FEC overhead; the')
    print('client rate is what you can sell. Quoting the first as capacity')
    print('overstates every channel by the overhead.')

    print('\nPaths, and what each can carry')
    print('%38s | %8s | %7s | %8s | %s'
          % ('path', 'distance', 'ROADMs', 'OSNR', 'best mode that fits'))
    print('-' * 100)
    for r in a['rows']:
        b = r['feasible']['best']
        print('%38s | %6.0f km | %7d | %6.1f dB | %s'
              % (r['name'], r['osnr']['total_km'], r['osnr']['roadm_passes'],
                 r['osnr']['osnr_db'],
                 ('%s, %.0f G to the client' % (b['name'], b['client_gbps']))
                 if b else 'NOTHING FITS'))

    two, six = a['rows'][0], a['rows'][1]
    print('\nRead the first two rows together. Same forty kilometres, same fibre,')
    print('same launch power --- and %.1f dB of OSNR between them, entirely from'
          % (two['osnr']['osnr_db'] - six['osnr']['osnr_db']))
    print('the ROADM passes. The shorter path carries %s and the other carries'
          % (two['feasible']['best']['name'] if two['feasible']['best'] else 'nothing'))
    print('%s. So "metro is short, therefore OSNR is plentiful, therefore'
          % (six['feasible']['best']['name'] if six['feasible']['best'] else 'nothing'))
    print('16QAM" is not a rule --- in a metro ring the ROADM count often')
    print('decides more than the kilometres do.')
    reg = a['rows'][2]
    print('\nAnd look at the third row against the second. The regional path is')
    print('%.0f km --- twelve times the metro ring --- and it has MORE OSNR'
          % reg['osnr']['total_km'])
    print('(%.1f against %.1f) and carries more (%.0f G against %.0f G), because'
          % (reg['osnr']['osnr_db'], six['osnr']['osnr_db'],
             reg['feasible']['best']['client_gbps'],
             six['feasible']['best']['client_gbps']))
    print('it passes through two nodes instead of eight. Distance is not the')
    print('variable. The number of amplified sections is, and a node is one.')

    print('\nWhen nothing fits, what actually helps')
    o = a['options']
    print('(long-haul path, %.1f dB as described)\n' % o['base']['osnr_db'])
    print('%44s | %8s | %7s | %s'
          % ('change', 'OSNR', 'delta', 'what it really does'))
    print('-' * 110)
    for x in o['options']:
        print('%44s | %6.1f dB | %+6.1f | %s'
              % (x['change'], x['osnr_db'], x['delta_db'], x['note'][:44]))
    same = next(x for x in o['options']
                if 'more gain at the same points' in x['change'])
    split = next(x for x in o['options'] if 'halving every span' in x['change'])
    print('\nRead rows two and three together, because "add amplification" ---')
    print('the advice this lab used to give when nothing fitted --- means both')
    print('of them, and they are opposite. More gain at the same points buys')
    print('%+.1f dB: the noise is in the signal already and gain amplifies that'
          % same['delta_db'])
    print('too. One extra hut PER ORIGINAL SPAN buys %+.1f dB, because each'
          % split['delta_db'])
    print('amplifier now recovers half the loss. That distinction is the whole')
    print('of it --- amplification helps when it reduces the loss any one')
    print('amplifier must make up, and not otherwise.')


# ---------------------------------------------------------------------------
# A REAL mode table, from a published datasheet
# ---------------------------------------------------------------------------
# The modes above are invented to show the shape of the lesson.  These are read
# from the Nokia 400G ZR/ZR+ pluggable coherent modules data sheet, retrieved
# 18 September 2026 and cited in the chapter.  Each entry is one COMPATIBILITY
# MODE of a single module, part number 3HE16565AA, except the first, which is
# the ZR-only module 3HE16564AA.
#
# The column the datasheet calls "Receiver OSNR sensitivity" is what a link
# budget must clear.  Read the table and two things are visible that no
# illustrative set would have produced.
VENDOR_MODES = [
    # (mode name, config, rate Gb/s, modulation, baud, FEC, rx OSNR dB,
    #  max -3dB width GHz, CD tolerance ps/nm)
    ('400G ZR', 'oif-400g-zr', 400, '16QAM', 59.844, 'cFEC', 26.0, 52, 2400),
    ('400G ZR+', 'oif-400g-zr', 400, '16QAM', 59.844, 'cFEC', 26.0, 52, 2400),
    ('400G ZR+', 'open-zrp-ofec1', 400, '16QAM', 60.139, 'oFEC', 24.0, 60, 20000),
    ('400G ZR+', 'open-zrp-ofec2', 400, '16QAM', 60.139, 'oFEC', 24.0, 60, 13000),
    ('300G ZR+', 'long haul', 300, '8QAM', 60.139, 'oFEC', 24.0, 60, 50000),
    ('200G ZR+', 'long haul', 200, 'QPSK', 60.139, 'oFEC', 24.0, 60, 80000),
    ('100G ZR+', 'long haul', 100, 'QPSK', 30.069, 'oFEC', 24.0, 60, 100000),
]


def vendor_mode_table():
    """Return the published table plus the two comparisons worth making."""
    rows = [dict(zip(('name', 'config', 'rate_gbps', 'modulation', 'baud_gbd',
                      'fec', 'rx_osnr_db', 'width_ghz', 'cd_ps_nm'), r))
            for r in VENDOR_MODES]
    # the same rate and modulation, at essentially the same baud, differing
    # only in the FEC
    cfec = [r for r in rows if r['fec'] == 'cFEC' and r['rate_gbps'] == 400][0]
    ofec = [r for r in rows if r['fec'] == 'oFEC' and r['rate_gbps'] == 400][0]
    fec_delta = cfec['rx_osnr_db'] - ofec['rx_osnr_db']
    # the spread of required OSNR across everything sharing one FEC
    same_fec = [r for r in rows if r['fec'] == 'oFEC']
    spread = max(r['rx_osnr_db'] for r in same_fec) - min(
        r['rx_osnr_db'] for r in same_fec)
    return {'rows': rows, 'fec_delta_db': fec_delta, 'ofec_spread_db': spread,
            'ofec_rates': sorted({r['rate_gbps'] for r in same_fec}),
            'cd_min': min(r['cd_ps_nm'] for r in rows),
            'cd_max': max(r['cd_ps_nm'] for r in rows)}


def report_vendor_modes():
    v = vendor_mode_table()
    print()
    print('A published mode table, and two things in it')
    print('-' * 74)
    print('%-9s %-15s %5s %-6s %8s %-5s %8s %6s %9s'
          % ('module', 'config', 'rate', 'mod', 'baud', 'FEC', 'rx OSNR',
             'width', 'CD tol'))
    for r in v['rows']:
        print('%-9s %-15s %4dG %-6s %7.3f %-5s %6.1f dB %4d G %9s'
              % (r['name'], r['config'], r['rate_gbps'], r['modulation'],
                 r['baud_gbd'], r['fec'], r['rx_osnr_db'], r['width_ghz'],
                 '{:,}'.format(r['cd_ps_nm'])))
    print()
    print('  FIRST: the two 400G 16QAM rows differ by %.0f dB of required OSNR,'
          % v['fec_delta_db'])
    print('  at the same rate, the same modulation and a baud rate differing by')
    print('  half a per cent. The only difference is the FEC. So the FEC is not')
    print('  a detail below the mode --- on this module it is worth more than')
    print('  most of the things people do argue about, and a mode named by its')
    print('  modulation alone has not been named.')
    print()
    print('  SECOND, and stranger: every oFEC mode here quotes the SAME %.0f dB,'
          % v['rows'][2]['rx_osnr_db'])
    print('  across %s --- from 400G 16QAM down to 100G QPSK.'
          % ', '.join('%dG' % r for r in v['ofec_rates']))
    print('  Spread: %.0f dB.' % v['ofec_spread_db'])
    print()
    print('  That is not how the physics behaves --- QPSK genuinely tolerates')
    print('  worse OSNR than 16QAM --- so the figure is not being published as a')
    print('  per-mode requirement. It reads as a specification FLOOR: a single')
    print('  guaranteed receiver sensitivity the module meets in any of its oFEC')
    print('  modes. That distinction matters to a budget. Taken as physics it')
    print('  says dropping from 400G to 100G buys no OSNR, which is false.')
    print('  Taken as a specification it says the module is GUARANTEED to work')
    print('  at 24 dB in any of them, and whatever extra margin the lower-order')
    print('  modes really have is not something the vendor has committed to.')
    print('  Budget against the published figure; expect the real link to do')
    print('  better at the lower rates; do not design on the difference.')
    print()
    print('  And note the last column: chromatic dispersion tolerance runs')
    print('  from %s to %s ps/nm across these modes, a factor of %.0f.'
          % ('{:,}'.format(v['cd_min']), '{:,}'.format(v['cd_max']),
             v['cd_max'] / float(v['cd_min'])))
    print('  It is the mode, not the module, that decides how much fibre it')
    print('  will tolerate.')
    print()
    print('  Every figure in this table is a manufacturer claim about one')
    print('  product, not a measurement and not a general property of ZR or ZR+.')
    return v


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        a = analyse()
    except ModeError as e:
        print('mode error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(a, indent=2))
    else:
        report(a)
        report_vendor_modes()
    return 0


if __name__ == '__main__':
    sys.exit(main())
