#!/usr/bin/env python3
"""Lab 46.2 --- the budget a converged ring needs on BOTH of its paths.

WHY THIS LAB EXISTS
-------------------
The chapter proposed a converged metro for four PoPs on a ring: an open line
system, ROADMs at every site, coherent pluggables straight in the routers, and
optical restoration for fibre cuts.  It justified the modulation like this:

    "Modulation is high-order (16QAM) because the ring is short and OSNR is
     plentiful."

Two things are wrong with that sentence, and the second one is the dangerous
one.

First, short does not mean plentiful.  Lab 45.1 settled this: OSNR is set by
the number of AMPLIFIED SECTIONS, and a ROADM node is one.  A forty-kilometre
ring through eight nodes has less OSNR than a four-hundred-kilometre regional
path through two.  The kilometres are not the variable.

Second --- and this is the one that takes a network down --- the design picks a
mode from the WORKING path and then promises optical restoration, which moves
the service onto the PROTECTION path.  On a ring the protection path is the
long way round: more spans, and an express ROADM pass at every site in between.
If the mode was chosen with no margin on the short path, restoration puts the
service onto a path where it does not close, and the restoration the design was
sold on is the thing that takes the service down.

A converged design is approved against the worst path it can be restored onto,
not the path it normally runs on.  This works that out.

    python3 path_budget.py
    python3 path_budget.py --json
    python3 test_path_budget.py

No optical equipment, no measurement, no planning tool and no vendor data.  The
fibre figures, node losses, noise figures and required OSNRs below are all
stated inputs; a real design uses the line system's own planning tool and the
transponder vendor's own mode data.
"""
import argparse
import itertools
import json
import math
import sys

NOISE_REF_DBM = -58.0     # 10log10(h.nu.B_ref), 1550 nm in 0.1 nm, as Chapter 44


class BudgetError(ValueError):
    """The described ring or path cannot be evaluated."""


# ---------------------------------------------------------------------------
# modes --- the same illustrative set as Lab 45.1, for the same reason
# ---------------------------------------------------------------------------
def mode(name, baud_gbd, bits_per_symbol_per_pol, fec_overhead_percent,
         required_osnr_db):
    line = baud_gbd * bits_per_symbol_per_pol * 2.0
    return {'name': name, 'baud_gbd': baud_gbd,
            'bits_per_symbol_per_pol': bits_per_symbol_per_pol,
            'fec_overhead_percent': fec_overhead_percent,
            'required_osnr_db': required_osnr_db,
            'line_gbps': line,
            'client_gbps': line / (1.0 + fec_overhead_percent / 100.0),
            # the optical width the channel occupies, which decides how many
            # 12.5 GHz slots it needs --- Lab 45.2
            'width_ghz': baud_gbd * 1.12 + 12.5}


# ILLUSTRATIVE.  Not any vendor's, not any standard's, not measured.  A real
# pluggable implements one or more modes and each one's required OSNR comes
# from its vendor, not from its marketing name.
MODES = [
    mode('QPSK, 60 Gbaud', 60, 2, 20.0, 11.5),
    mode('QPSK, 118 Gbaud', 118, 2, 20.0, 14.5),
    mode('8QAM, 118 Gbaud', 118, 3, 20.0, 17.5),
    mode('16QAM, 60 Gbaud', 60, 4, 20.0, 17.0),
    mode('16QAM, 118 Gbaud', 118, 4, 20.0, 20.0),
]


# ---------------------------------------------------------------------------
# the ring
# ---------------------------------------------------------------------------
def ring(sites, spans_km, ducts=None):
    """A fibre ring: sites in order, spans_km[i] joining sites[i] to sites[i+1].

    ducts[i] names the physical duct or route each span is in.  Two spans in
    the same duct are NOT diverse, however far apart they look on a map, and a
    ring drawn with four sides can have two of them in one trench.
    """
    n = len(sites)
    if n < 3:
        raise BudgetError('a ring has at least three sites, got %d' % n)
    if len(spans_km) != n:
        raise BudgetError('a ring of %d sites has %d spans, got %d'
                          % (n, n, len(spans_km)))
    if any(s <= 0 for s in spans_km):
        raise BudgetError('every span length is positive')
    if ducts is None:
        short = [x.split('-')[-1] for x in sites]
        ducts = ['duct-%s%s' % (short[i], short[(i + 1) % n]) for i in range(n)]
    if len(ducts) != n:
        raise BudgetError('one duct name per span')
    return {'sites': list(sites), 'spans_km': list(spans_km),
            'ducts': list(ducts), 'n': n}


def paths_between(rng, a, b):
    """The two ways round the ring, as lists of span indices.

    Returns (clockwise, anticlockwise).  Each is the span indices traversed and
    the intermediate sites, which are the EXPRESS ROADM passes: nodes the
    channel goes through without being dropped, each one an amplified section
    of its own.
    """
    sites = rng['sites']
    if a not in sites or b not in sites:
        raise BudgetError('%r and %r must both be on the ring' % (a, b))
    if a == b:
        raise BudgetError('a path needs two different sites')
    n = rng['n']
    ia, ib = sites.index(a), sites.index(b)

    cw_spans, cw_through, i = [], [], ia
    while i != ib:
        cw_spans.append(i)
        i = (i + 1) % n
        if i != ib:
            cw_through.append(sites[i])

    acw_spans, acw_through, i = [], [], ia
    while i != ib:
        j = (i - 1) % n
        acw_spans.append(j)
        i = j
        if i != ib:
            acw_through.append(sites[i])

    return ({'spans': cw_spans, 'through': cw_through, 'direction': 'clockwise'},
            {'spans': acw_spans, 'through': acw_through,
             'direction': 'anticlockwise'})


# ---------------------------------------------------------------------------
# the budget
# ---------------------------------------------------------------------------
def path_osnr(rng, path, launch_dbm=-3.0, fibre_db_per_km=0.22,
              connector_db_per_span=1.0, amp_nf_db=5.5, roadm_loss_db=16.0,
              roadm_filter_penalty_db=0.4):
    """OSNR at the far end, counting every amplified section including the nodes.

    Every fibre span is one amplified section.  Every EXPRESS ROADM pass is
    another: the node's insertion loss has to be recovered by an amplifier that
    adds its own noise, and the channel is narrowed a little on the way
    through, which is the filtering penalty.

    Noise powers add, so the reciprocals of the per-section OSNRs add.
    """
    if amp_nf_db < 0 or fibre_db_per_km <= 0 or roadm_loss_db < 0:
        raise BudgetError('the noise figure, attenuation and node loss must be '
                          'sensible')
    sections = []
    for i in path['spans']:
        km = rng['spans_km'][i]
        loss = km * fibre_db_per_km + connector_db_per_span
        sections.append(('fibre span %s, %.0f km'
                         % (rng['ducts'][i], km), loss))
    for site in path['through']:
        sections.append(('express ROADM at %s' % site, roadm_loss_db))

    inv = 0.0
    detail = []
    for label, loss in sections:
        o = launch_dbm - loss - amp_nf_db - NOISE_REF_DBM
        detail.append({'section': label, 'loss_db': loss, 'osnr_db': o})
        inv += 10.0 ** (-o / 10.0)
    ase_db = -10.0 * math.log10(inv)
    filt = len(path['through']) * roadm_filter_penalty_db

    return {
        'sections': detail,
        'amplified_sections': len(sections),
        'express_passes': len(path['through']),
        'distance_km': sum(rng['spans_km'][i] for i in path['spans']),
        'ase_osnr_db': ase_db,
        'filter_penalty_db': filt,
        'osnr_db': ase_db - filt,
    }


def modes_that_close(osnr_db, margin_db=0.0, modes=None):
    modes = MODES if modes is None else modes
    return [m for m in modes if osnr_db - margin_db >= m['required_osnr_db']]


def best_mode(osnr_db, margin_db=0.0, modes=None):
    fit = modes_that_close(osnr_db, margin_db, modes)
    if not fit:
        return None
    return max(fit, key=lambda m: (m['client_gbps'], -m['required_osnr_db']))


def service(rng, a, b, margin_db=2.0, **kw):
    """Evaluate one service both ways round the ring.

    The working path is the shorter of the two by OSNR; the protection path is
    the other one, which is what optical restoration would move the service
    onto.  The mode that may be DEPLOYED is the best one that closes on BOTH,
    because the design has promised the service survives a cut.
    """
    cw, acw = paths_between(rng, a, b)
    bcw, bacw = path_osnr(rng, cw, **kw), path_osnr(rng, acw, **kw)
    if bcw['osnr_db'] >= bacw['osnr_db']:
        work, prot, wp, pp = bcw, bacw, cw, acw
    else:
        work, prot, wp, pp = bacw, bcw, acw, cw

    naive = best_mode(work['osnr_db'], margin_db)
    survivable = best_mode(min(work['osnr_db'], prot['osnr_db']), margin_db)

    # shared ducts between the two paths: if any duct appears on both, the
    # "protection" path fails with the working one and the ring is not diverse
    wducts = {rng['ducts'][i] for i in wp['spans']}
    pducts = {rng['ducts'][i] for i in pp['spans']}
    shared = sorted(wducts & pducts)

    return {
        'a': a, 'b': b, 'margin_db': margin_db,
        'working': dict(work, direction=wp['direction'],
                        through=list(wp['through'])),
        'protection': dict(prot, direction=pp['direction'],
                           through=list(pp['through'])),
        'osnr_penalty_db': work['osnr_db'] - prot['osnr_db'],
        'mode_from_working_path': naive,
        'mode_that_survives_restoration': survivable,
        'overstated': (naive is not None and
                       (survivable is None or
                        naive['name'] != survivable['name'])),
        'no_mode_survives': survivable is None,
        'shared_ducts': shared,
        'diverse': not shared,
    }


def all_services(rng, **kw):
    return [service(rng, a, b, **kw)
            for a, b in itertools.combinations(rng['sites'], 2)]


# ---------------------------------------------------------------------------
# does the restored traffic fit in the spectrum?
# ---------------------------------------------------------------------------
def slots_for(width_ghz, slot_ghz=12.5):
    """Flexgrid slot count, rounded UP --- Lab 45.2."""
    return int(math.ceil(width_ghz / slot_ghz))


def span_occupancy(rng, services, band_ghz=4800.0, restored_span=None):
    """How much spectrum a span carries normally, and after one cut.

    A cut on one span pushes every service that used it the other way round the
    ring, so every remaining span carries its own traffic PLUS the rerouted
    traffic.  Whether that fits is a question the chapter's design never asked.
    """
    normal = {i: 0 for i in range(rng['n'])}
    after = {i: 0 for i in range(rng['n'])}
    for s in services:
        m = s['mode_that_survives_restoration'] or s['mode_from_working_path']
        if m is None:
            continue
        slots = slots_for(m['width_ghz'])
        cw, acw = paths_between(rng, s['a'], s['b'])
        work = cw if cw['direction'] == s['working']['direction'] else acw
        prot = acw if work is cw else cw
        for i in work['spans']:
            normal[i] += slots
        use = prot if (restored_span is not None and
                       restored_span in work['spans']) else work
        for i in use['spans']:
            if restored_span is not None and i == restored_span:
                continue
            after[i] += slots
    cap = int(band_ghz // 12.5)
    return {'slots_available': cap,
            'normal': normal, 'after_cut': after,
            'worst_normal': max(normal.values()),
            'worst_after': max(after.values()),
            'fits_normally': max(normal.values()) <= cap,
            'fits_after_cut': max(after.values()) <= cap}



# ---------------------------------------------------------------------------
# how much ring it takes before restoration costs you the mode
# ---------------------------------------------------------------------------
def uniform_ring(n_sites, circumference_km):
    """A ring of n equal spans, for asking what size breaks a design."""
    return ring(['S%02d' % i for i in range(n_sites)],
                [circumference_km / float(n_sites)] * n_sites)


def adjacent_service(n_sites, circumference_km, margin_db=2.0, **kw):
    """The service between two neighbouring sites: the best working path on the
    ring, and therefore the one whose protection path is the worst."""
    r = uniform_ring(n_sites, circumference_km)
    return service(r, r['sites'][0], r['sites'][1], margin_db=margin_db, **kw)


def breaking_point(circumference_km, sites=range(4, 33, 2), margin_db=2.0, **kw):
    """The first ring size at which the protection path will not carry the mode
    the working path allows.  Returns None if none of the sizes tried breaks."""
    for n in sites:
        s = adjacent_service(n, circumference_km, margin_db=margin_db, **kw)
        if s['overstated'] or s['no_mode_survives']:
            return n, s
    return None, None


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
KESTREL = ring(['PoP-A', 'PoP-B', 'PoP-C', 'PoP-D'],
               [18.0, 22.0, 25.0, 31.0])


def name_of(m):
    return m['name'] if m else 'NONE FITS'


def section_a(rng):
    print('A. The ring, and the two paths every service has')
    print('-' * 74)
    for i, km in enumerate(rng['spans_km']):
        j = (i + 1) % rng['n']
        print('  %-7s -- %-7s  %5.1f km   (%s)'
              % (rng['sites'][i], rng['sites'][j], km, rng['ducts'][i]))
    print('  total ring circumference: %.1f km' % sum(rng['spans_km']))
    print()
    cw, acw = paths_between(rng, 'PoP-A', 'PoP-B')
    print('  PoP-A to PoP-B, the two ways round:')
    for p in (cw, acw):
        print('    %-14s %2d span(s), %2d express ROADM pass(es), %5.1f km'
              % (p['direction'], len(p['spans']), len(p['through']),
                 sum(rng['spans_km'][i] for i in p['spans'])))
    print()
    print('  The short way is one span and no express node.  The long way is')
    print('  three spans AND two express nodes --- five amplified sections')
    print('  against one.  That is the whole of the problem.')
    print()


def section_b(services):
    print('B. OSNR on both paths, and the mode each one allows')
    print('-' * 74)
    print('%-9s %9s %9s %9s  %-20s %s'
          % ('service', 'working', 'protect', 'penalty',
             'mode from working', 'mode that survives'))
    for s in services:
        print('%-9s %6.1f dB %6.1f dB %6.1f dB  %-20s %s'
              % ('%s-%s' % (s['a'].replace('PoP-', ''),
                            s['b'].replace('PoP-', '')),
                 s['working']['osnr_db'], s['protection']['osnr_db'],
                 s['osnr_penalty_db'],
                 name_of(s['mode_from_working_path']),
                 name_of(s['mode_that_survives_restoration'])))
    print()
    over = [s for s in services if s['overstated']]
    worst = min(s['protection']['osnr_db'] for s in services)
    need = max(m['required_osnr_db'] for m in MODES)
    print('  Services whose mode the protection path cannot carry: %d of %d.'
          % (len(over), len(services)))
    print()
    print('  So the chapter\'s design survives --- and it is worth being exact')
    print('  about what that does and does not mean.  It is TRUE that 16QAM')
    print('  closes both ways round this ring.  It was not true BECAUSE the ring')
    print('  is short.  The worst protection path here delivers %.1f dB against'
          % worst)
    print('  a %.1f dB requirement --- %.1f dB of headroom, and that headroom comes'
          % (need, worst - need))
    print('  from there being four sites on the ring, not from there being 96 km')
    print('  of it.  Nobody computed either number.  The design asserted a')
    print('  conclusion that happened to hold, which is not the same as holding.')
    print()
    print('  The penalty column is the part to keep.  Restoration costs between')
    print('  %.1f and %.1f dB on this ring depending on which pair you take ---'
          % (min(s['osnr_penalty_db'] for s in services),
             max(s['osnr_penalty_db'] for s in services)))
    print('  and the pairs that lose most are the ADJACENT ones, whose working')
    print('  path is a single span and whose protection path is the whole rest')
    print('  of the ring.  A design reviewed on its longest service looks at')
    print('  exactly the pair with the least to lose.')
    print()
    return {'overstated': len(over), 'worst_protection_db': worst,
            'hardest_mode_db': need}


def section_c(rng):
    print('C. What it takes to stop being true')
    print('-' * 74)
    print('  Adjacent-pair service, equal spans, 2 dB design margin.')
    print()
    print('%6s %10s %8s %9s %9s  %-18s %s'
          % ('sites', 'circum.', 'spans', 'working', 'protect',
             'from working', 'survives'))
    rows = []
    for circ in (96.0, 240.0):
        for n in (4, 6, 8, 12, 16):
            s = adjacent_service(n, circ)
            rows.append((n, circ, s))
            print('%6d %8.0f km %8d %6.1f dB %6.1f dB  %-18s %s'
                  % (n, circ, s['protection']['amplified_sections'],
                     s['working']['osnr_db'], s['protection']['osnr_db'],
                     name_of(s['mode_from_working_path']),
                     name_of(s['mode_that_survives_restoration'])))
        print()

    out = {}
    for circ in (96.0, 240.0, 400.0):
        n, s = breaking_point(circ)
        out[circ] = n
        if n is None:
            print('  at %.0f km the mode survives every ring size tried' % circ)
        else:
            print('  at %.0f km circumference, %d sites is where restoration '
                  'starts' % (circ, n))
            print('  costing the mode: protection falls to %.1f dB and the best'
                  % s['protection']['osnr_db'])
            print('  mode that survives it is %s.'
                  % name_of(s['mode_that_survives_restoration']))
    print()
    print('  Four sites on 96 km sits comfortably inside the safe region --- and')
    print('  ten sites on the same 96 km does not, nor do four sites on the')
    print('  400 km ring a regional operator would draw.  Kilometres move the')
    print('  answer slowly; SITES move it fast, because every one of them is an')
    print('  amplified section on every path that passes through it.  Adding an')
    print('  aggregation site to a working ring is the change most likely to')
    print('  invalidate a restoration promise, and the least likely to be')
    print('  reviewed as though it might.')
    print()
    print('  The lesson is not that the chapter\'s ring was wrong.  It is that')
    print('  the chapter had no way of knowing, and a reader copying the design')
    print('  onto a ring of their own has no way of knowing either.')
    print()
    return {'rows': rows, 'breaking_points': out}


def section_d(rng, services):
    print('D. Two things that make the protection path a promise, not a fact')
    print('-' * 74)
    shared = ring(rng['sites'], rng['spans_km'],
                  ducts=['duct-north', 'duct-east', 'duct-south', 'duct-north'])
    s = service(shared, 'PoP-A', 'PoP-B')
    print('  (i) diversity.  Spans A-B and D-A are drawn as two sides of the')
    print('      ring, but the records say both are in duct-north:')
    print('        shared ducts on the A-B service: %s' % ', '.join(s['shared_ducts']))
    print('        diverse: %s' % ('yes' if s['diverse'] else 'NO'))
    print('      A machine in that trench takes the working and the protection')
    print('      path together, and no optical restoration reaches round it.')
    print()
    occ = span_occupancy(rng, services)
    cut = span_occupancy(rng, services, restored_span=0)
    print('  (ii) capacity.  Every service that used the cut span now rides the')
    print('       other three, on top of what they already carry:')
    print('        slots available per span          : %d' % occ['slots_available'])
    print('        busiest span, normal working      : %d' % occ['worst_normal'])
    print('        busiest span, after a cut on A-B  : %d' % cut['worst_after'])
    print('        fits after the cut                : %s'
          % ('yes' if cut['fits_after_cut'] else 'NO'))
    print('       Fitting in slots is still not the same as fitting: the free')
    print('       slots must be CONTIGUOUS and the same ones on every link of')
    print('       the path, which is Lab 45.2 and not checked here.')
    print()
    return {'shared': s, 'normal': occ, 'after_cut': cut}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)

    services = all_services(KESTREL)

    if args.json:
        json.dump({'ring': KESTREL, 'services': services},
                  sys.stdout, indent=1, sort_keys=True, default=str)
        sys.stdout.write('\n')
        return 0

    print('The Kestrel converged metro, budgeted on both of its paths')
    print('(Chapter 46, section 8).  Every figure below is a stated input.')
    print()
    section_a(KESTREL)
    section_b(services)
    section_c(KESTREL)
    section_d(KESTREL, services)
    print('What this does NOT establish')
    print('-' * 74)
    print('- No optical equipment, no measurement, no planning tool.  The')
    print('  attenuation, node loss, noise figure, launch power and required')
    print('  OSNRs are inputs chosen to be plausible, not data.')
    print('- The modes are illustrative and are not any vendor\'s or any')
    print('  standard\'s.  A pluggable\'s reach is not a property of its name.')
    print('- The model has one channel and ignores what a full band does to it:')
    print('  no nonlinear penalty (Lab 44.2), no Raman tilt, no gain ripple, no')
    print('  polarisation-dependent loss, no dispersion, and no ageing.')
    print('- The capacity check counts slots.  It does not check that the free')
    print('  slots are contiguous or that the same ones are free on every link,')
    print('  which is where a real restoration attempt fails (Lab 45.2).')
    print('- Nothing here approves a design.  It shows which questions a')
    print('  converged design has to answer before anyone can approve it.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
