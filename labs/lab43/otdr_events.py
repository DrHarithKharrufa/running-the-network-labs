#!/usr/bin/env python3
"""Lab 43.2 --- why one OTDR trace does not identify an event, or find a dig site.

WHY THIS EXISTS
---------------
Chapter 43 used to say you could tell a splice from a connector from a bend from
a break "at a glance", from one trace, by its visual signature --- and that doing
so locates a fault "to within metres".  Both halves are wrong in ways that send
crews to the wrong place, and this lab computes the four reasons.

  1. A single-direction loss measurement can be NEGATIVE across a real, lossy
     splice.  The trace shows a step UP.  Nothing is generating light; the two
     fibres simply scatter differently, and the OTDR is reporting the difference
     as well as the loss.  Bidirectional averaging estimates loss in the symmetric-bias model.
  2. Two events closer together than the dead zone appear as one event, and how
     close depends on pulse width, event reflectance and receiver recovery.
  3. The distance the OTDR reports is along the FIBRE.  A dig site is along the
     ROUTE.  Fibre is longer than its cable, and every closure holds slack, so
     the two numbers differ by more than the trench is wide.
  4. That distance is computed from an assumed refractive index.  Set it wrong
     by a fraction of a per cent and you are out by hundreds of metres.

None of this needs an OTDR.  It is arithmetic, and it is the arithmetic that
decides whether the crew opens the right chamber.

WHAT THIS IS NOT
----------------
No OTDR, no fibre, no measurement.  Every value below is one you supply, and the
worked examples are illustrative.  This does not process a real trace file, does
not model backscatter physics beyond the one coefficient difference above, and
cannot tell you what is wrong with a span.  It tells you what a number from a
trace does and does not mean.

    python3 otdr_events.py
    python3 otdr_events.py --json
    python3 test_otdr_events.py
"""
import argparse
import json
import sys

C_VACUUM_M_PER_S = 299_792_458.0


class TraceError(ValueError):
    """The inputs do not describe a measurement that can be interpreted."""


# --------------------------------------------------------------------------
# 1. bidirectional averaging, and the gainer
# --------------------------------------------------------------------------
def true_event_loss(loss_a_to_b_db, loss_b_to_a_db):
    """Loss estimate under the model of equal, opposite backscatter bias.

    An OTDR infers loss from backscattered light, so it measures the event's
    loss PLUS half the difference in the two fibres' backscatter coefficients,
    with the sign of that second term reversing when you measure from the other
    end. Average the two and the backscatter term cancels exactly:

        measured(A->B) = loss + d
        measured(B->A) = loss - d
        loss           = (measured(A->B) + measured(B->A)) / 2
        d              = (measured(A->B) - measured(B->A)) / 2

    When d is larger than the loss, the measurement from one direction is
    NEGATIVE --- the trace steps up. That event is called a gainer, and a
    technician who accepts the one-direction figure has recorded a splice as
    free, or as faulty, depending on which end they happened to stand at.
    """
    for v in (loss_a_to_b_db, loss_b_to_a_db):
        if not isinstance(v, (int, float)):
            raise TraceError('a measured loss is a number in dB, got %r' % (v,))
    loss = (loss_a_to_b_db + loss_b_to_a_db) / 2.0
    d = (loss_a_to_b_db - loss_b_to_a_db) / 2.0
    return {
        'a_to_b_db': loss_a_to_b_db,
        'b_to_a_db': loss_b_to_a_db,
        'true_loss_db': loss,
        'backscatter_term_db': d,
        'is_gainer': min(loss_a_to_b_db, loss_b_to_a_db) < 0,
        'one_way_error_db': max(abs(loss_a_to_b_db - loss),
                                abs(loss_b_to_a_db - loss)),
    }


# --------------------------------------------------------------------------
# 2. dead zones
# --------------------------------------------------------------------------
def dead_zone_m(pulse_width_ns, index=1.4682):
    """Pulse-length resolution proxy, not an instrument dead-zone specification.

    A pulse of width t occupies t*c/n metres of fibre. The reflected light from
    two events separated by less than half that arrives overlapped, so the
    limit is (t*c/n)/2 --- the light makes the trip twice.

    This is the geometric floor. A real instrument's attenuation dead zone ---
    the distance after a reflective event before loss can be measured again ---
    is longer, and is a specification of the instrument. The figure here is the
    pulse-overlap proxy, not a guaranteed best case or visibility promise.
    """
    if pulse_width_ns <= 0:
        raise TraceError('a pulse width is positive, got %r' % (pulse_width_ns,))
    if index <= 1:
        raise TraceError('a group index is greater than 1, got %r' % (index,))
    length = pulse_width_ns * 1e-9 * C_VACUUM_M_PER_S / index
    return length / 2.0


def resolvable(separation_m, pulse_width_ns, index=1.4682):
    dz = dead_zone_m(pulse_width_ns, index)
    return {'separation_m': separation_m, 'dead_zone_m': dz,
            'resolvable': separation_m > dz,
            'note': ('pulse-overlap proxy: separate losses not established'
                     if separation_m <= dz else
                     'outside pulse-overlap proxy; real resolution still unverified')}


# --------------------------------------------------------------------------
# 3. optical distance is not route distance
# --------------------------------------------------------------------------
def dig_position(optical_km, closures_passed=0, slack_per_closure_m=25.0,
                 helix_percent=0.7, launch_lead_m=0.0):
    """Turn a distance along the fibre into a position along the cable route.

    Three corrections, all of which make the route position SHORTER than the
    optical distance, so ignoring them sends the crew too far:

      launch lead   a launch or pigtail fibre at the near end, which is fibre
                    the OTDR measures and route the crew cannot walk
      slack         every closure stores a loop of fibre --- often tens of
                    metres --- that occupies no route at all
      helix         the fibre is stranded around the cable's core, so there is
                    more fibre than cable, typically a fraction of a per cent

    The result is a position along the route. It is still not a hole in the
    ground: you need the route record to turn a distance along the cable into a
    place, and the point of this function is how far wrong you are without it.
    """
    if optical_km < 0:
        raise TraceError('a distance is not negative, got %r' % (optical_km,))
    if closures_passed < 0:
        raise TraceError('closures passed is not negative')
    if helix_percent < 0:
        raise TraceError('the helix allowance is not negative')
    fibre_m = optical_km * 1000.0 - launch_lead_m
    slack_m = closures_passed * slack_per_closure_m
    in_cable_m = fibre_m - slack_m
    route_m = in_cable_m / (1.0 + helix_percent / 100.0)
    return {
        'optical_km': optical_km,
        'launch_lead_m': launch_lead_m,
        'slack_m': slack_m,
        'helix_percent': helix_percent,
        'route_m': route_m,
        'route_km': route_m / 1000.0,
        'error_if_ignored_m': optical_km * 1000.0 - route_m,
    }


# --------------------------------------------------------------------------
# 4. the refractive index you typed in
# --------------------------------------------------------------------------
def index_error(distance_km, assumed_index, actual_index):
    """How far out the reported distance is when the index is set wrong.

    The OTDR has no way to measure the fibre's group index; it uses the one you
    gave it. Distance scales as 1/n, so a fractional error in n is the same
    fractional error in every distance on the trace.
    """
    for n in (assumed_index, actual_index):
        if n <= 1:
            raise TraceError('a group index is greater than 1, got %r' % (n,))
    reported = distance_km * actual_index / assumed_index
    return {'distance_km': distance_km, 'assumed_index': assumed_index,
            'actual_index': actual_index, 'reported_km': reported,
            'error_m': (reported - distance_km) * 1000.0,
            'error_percent': (actual_index / assumed_index - 1.0) * 100.0}


# --------------------------------------------------------------------------
# 5. bend or splice? not from one wavelength
# --------------------------------------------------------------------------
def classify_by_wavelength(loss_1310_db, loss_1550_db, reflective=False,
                           threshold_db=0.15):
    """Illustrative wavelength/reflectance clues, not a validated classifier.

    A macrobend loses much more light at the longer wavelength; a fusion splice
    is close to wavelength-flat. The discriminator is therefore the DIFFERENCE
    between two traces, which a single trace cannot supply at any price.

    Reflectance is a separate axis: a mated connector reflects, a fusion splice
    and a bend essentially do not. Both axes are needed, and even then this is a
    strong hint rather than an identification --- confirm at the closure.
    """
    if reflective and loss_1550_db >= 0:
        kind = 'reflective event: a connector or a mechanical joint'
    elif loss_1550_db - loss_1310_db > threshold_db:
        kind = 'macrobend: markedly worse at the longer wavelength'
    elif abs(loss_1550_db - loss_1310_db) <= threshold_db:
        kind = 'splice or a wavelength-flat loss'
    else:
        kind = ('worse at the SHORTER wavelength --- not a bend; suspect the '
                'measurement, the fibre type or a mismatch')
    return {'loss_1310_db': loss_1310_db, 'loss_1550_db': loss_1550_db,
            'delta_db': loss_1550_db - loss_1310_db, 'reflective': reflective,
            'kind': kind,
            'single_trace_would_say': ('a loss event of %.2f dB, and nothing '
                                       'more' % loss_1550_db)}


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------
def analyse():
    return {
        'gainers': [true_event_loss(a, b) for a, b in
                    ((0.28, 0.12), (-0.09, 0.49), (0.05, 0.05), (1.9, 2.1))],
        'dead_zones': [resolvable(sep, pw) for sep, pw in
                       ((5.0, 100), (25.0, 100), (5.0, 10), (200.0, 1000))],
        'dig': [dig_position(43.210, closures_passed=n) for n in (0, 3, 8)],
        'index': [index_error(43.2, 1.4682, n) for n in
                  (1.4682, 1.4700, 1.4750, 1.4600)],
        # the first two are chosen to read ALIKE at 1550 nm and differ only
        # at 1310 nm, which is the whole argument for the second wavelength
        'classify': [classify_by_wavelength(*a, reflective=r) for a, r in
                     (((0.30, 0.31), False), ((0.09, 0.32), False),
                      ((0.31, 0.34), True), ((0.40, 0.12), False))],
    }


def report(a):
    print('OTDR arithmetic. No OTDR, no fibre, no measurement --- every value')
    print('below is an input, and the worked examples are illustrative.\n')

    print('A. One direction can contain backscatter bias')
    print('%9s | %9s | %9s | %9s | %s'
          % ('A->B', 'B->A', 'true', 'error', 'what one trace would have told you'))
    print('-' * 88)
    for g in a['gainers']:
        note = ('a GAINER: one direction shows a step UP'
                if g['is_gainer'] else
                'both directions agree' if g['one_way_error_db'] < 0.02 else
                'one direction is out by %.2f dB' % g['one_way_error_db'])
        print('%8.2f  | %8.2f  | %8.2f  | %8.2f  | %s'
              % (g['a_to_b_db'], g['b_to_a_db'], g['true_loss_db'],
                 g['one_way_error_db'], note))
    print('\nA splice cannot amplify. The step up is the two fibres scattering')
    print('differently; averaging cancels the equal, opposite bias in this model.')
    print('Accept a one-way figure and you record a real splice as free ---')
    print('or, standing at the other end, as twice its actual loss.')

    print('\nB. Two events closer than the dead zone are one event')
    print('%12s | %11s | %11s | %s'
          % ('separation', 'pulse', 'dead zone', 'result'))
    print('-' * 68)
    for d, pw in zip(a['dead_zones'], (100, 100, 10, 1000)):
        print('%9.1f m | %8d ns | %8.1f m | %s'
              % (d['separation_m'], pw, d['dead_zone_m'],
                 'outside proxy' if d['resolvable'] else 'inside pulse-overlap proxy'))
    print('\nA long pulse reaches further and resolves less. The pulse width is')
    print('a choice you made, so \'there is one event here\' is a statement')
    print('about your settings as much as about the fibre.')

    print('\nC. The trace measures fibre; the crew digs route')
    print('%11s | %9s | %9s | %11s | %s'
          % ('optical', 'closures', 'slack', 'route', 'you would be out by'))
    print('-' * 72)
    for d in a['dig']:
        print('%8.3f km | %9.0f | %7.0f m | %8.3f km | %6.0f m'
              % (d['optical_km'], d['slack_m'] / 25.0, d['slack_m'],
                 d['route_km'], d['error_if_ignored_m']))
    print('\nThe fibre is longer than its cable and every closure holds a loop')
    print('of it. Dig at the optical distance and you are hundreds of metres')
    print('past the fault --- which is not "within metres" of anything.')

    print('\nD. The index is one you typed in')
    print('%9s | %9s | %11s | %s'
          % ('assumed', 'actual', 'reported', 'error at this distance'))
    print('-' * 62)
    for d in a['index']:
        print('%9.4f | %9.4f | %8.3f km | %+7.0f m  (%+.2f%%)'
              % (d['assumed_index'], d['actual_index'], d['reported_km'],
                 d['error_m'], d['error_percent']))
    print('\nEvery distance on the trace scales with that number. Use the')
    print('figure for the fibre actually in the ground, not the default.')

    print('\nE. Bend or splice needs two wavelengths')
    print('%9s | %9s | %8s | %6s | %s'
          % ('1310 nm', '1550 nm', 'delta', 'refl', 'what it is'))
    print('-' * 84)
    for c in a['classify']:
        print('%7.2f   | %7.2f   | %+7.2f | %6s | %s'
              % (c['loss_1310_db'], c['loss_1550_db'], c['delta_db'],
                 'yes' if c['reflective'] else 'no', c['kind']))
    one, two = a['classify'][0], a['classify'][1]
    print('\nRows one and two read %.2f and %.2f dB at 1550 nm --- the same event,'
          % (one['loss_1550_db'], two['loss_1550_db']))
    print('as far as a single trace at that wavelength can tell. At 1310 nm they')
    print('read %.2f and %.2f. One is a splice you can leave alone; the other is'
          % (one['loss_1310_db'], two['loss_1310_db']))
    print('a bend that will get worse and may already be a crush. The second')
    print('wavelength is what separates them, and it costs one more sweep.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        a = analyse()
    except TraceError as e:
        print('trace error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(a, indent=2))
    else:
        report(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
