#!/usr/bin/env python3
"""Lab 46.1 -- constructed recovery timelines, not equipment measurements.

Protection uses pre-established resources; restoration completes establishment
after the fault and can use pre-planned routes. Either can fail to recover if
the needed resources are unavailable. The illustrative durations are inputs.

This model treats alternate paths as independently usable. It derives service
transitions from those inputs; it does not simulate control-plane interaction,
amplifier settling, contention or real packet forwarding. Additional outages
must be supplied explicitly as disturbances. Zero churn is therefore a bounded
model result, not evidence that two real layers cannot interfere.

The succeeds flag represents availability of the recovery action, including
an unusable pre-established backup. Squelch uses an assumed 1 ms indication
delay and no debounce. The horizon filters displayed events, not transitions.

    python3 recovery_policy.py --json
    python3 test_recovery_policy.py
"""
import argparse
import json
import sys


class PolicyError(ValueError):
    """The described policy cannot be evaluated."""


# ---------------------------------------------------------------------------
# the two recovery mechanisms, which are not the same thing
# ---------------------------------------------------------------------------
# ILLUSTRATIVE durations.  None is measured and none is any vendor's.  They are
# here to carry the ORDER OF MAGNITUDE that separates the mechanisms, which is
# what the old script got backwards.  A real figure comes from the equipment,
# the control plane and the path in front of you.
MECHANISMS = {
    'none': {
        'kind': 'none',
        'what': 'the layer does not recover this failure',
        'recover_ms': None,
        'can_fail': False,
    },
    'optical-protection': {
        'kind': 'protection',
        'what': '1+1 line protection: both paths already lit, tail end selects',
        'recover_ms': 50,
        'can_fail': True,
    },
    'optical-restoration': {
        'kind': 'restoration',
        'what': 'compute a path, assign spectrum, re-level gain, re-lock modem',
        'recover_ms': 30000,
        'can_fail': True,
    },
    'packet-frr': {
        'kind': 'protection',
        'what': 'pre-computed loop-free backup installed in the FIB',
        'recover_ms': 50,
        'can_fail': True,
    },
    'packet-igp': {
        'kind': 'restoration',
        'what': 'flood, run SPF, install a new FIB',
        'recover_ms': 200,
        'can_fail': True,
    },
}


def mechanism(name):
    if name not in MECHANISMS:
        raise PolicyError('unknown mechanism %r; known: %s'
                          % (name, ', '.join(sorted(MECHANISMS))))
    return dict(MECHANISMS[name])


# ---------------------------------------------------------------------------
# a layer: how it notices, how long it waits, how it recovers
# ---------------------------------------------------------------------------
def layer(name, detect_ms, mechanism_name, holdoff_ms=0, succeeds=True,
          recover_ms=None):
    """One recovering layer.

    detect_ms    how long before this layer knows the path is gone
    holdoff_ms   how long it then waits before acting
    succeeds     whether its recovery attempt finds a usable path at all
    recover_ms   override the mechanism's illustrative duration
    """
    m = mechanism(mechanism_name)
    if detect_ms < 0 or holdoff_ms < 0:
        raise PolicyError('%s: detection and hold-off are not negative' % name)
    if recover_ms is not None:
        if recover_ms < 0:
            raise PolicyError('%s: recovery time is not negative' % name)
        m['recover_ms'] = recover_ms
    if m['recover_ms'] is None and mechanism_name != 'none':
        raise PolicyError('%s: %s has no recovery time' % (name, mechanism_name))
    if not succeeds and not m['can_fail']:
        raise PolicyError(
            '%s: no recovery mechanism selected (%s)' % (name, mechanism_name))
    return {'name': name, 'detect_ms': detect_ms, 'holdoff_ms': holdoff_ms,
            'mechanism': mechanism_name, 'kind': m['kind'], 'what': m['what'],
            'recover_ms': m['recover_ms'], 'succeeds': succeeds}


# ---------------------------------------------------------------------------
# the client signal: what the router is even allowed to see
# ---------------------------------------------------------------------------
# A router does not see a fibre cut.  It sees whatever the transport equipment
# does to its client port, and that is a configuration choice on the transport
# side which decides how fast the packet layer can react at all.
PROPAGATION = {
    'squelch': 'transport squelches the client port, so the router sees loss of '
               'signal as soon as the line side is declared down',
    'hold': 'transport holds the client laser on while it tries to recover, so '
            'the router learns nothing from the port and must detect the '
            'failure itself',
}


def horizon_for(packet, optical, propagation):
    """When the packet layer can first know, given what transport shows it.

    This is the mechanism the old script had no notion of, and it decides more
    than the router's own timers do.

    If transport SQUELCHES the client port, the router gets a hardware
    link-down event.  That pre-empts its liveness check entirely: the router
    does not wait for BFD or for hello timers to expire, because the port told
    it.  So the packet layer learns at the optical layer's detection time plus
    the moment it takes to signal, or at its own detection time, whichever
    comes first.

    If transport HOLDS the client laser on --- which is what equipment does when
    it intends to recover the line itself, so as not to disturb the router ---
    the port says nothing and the router is blind until its own liveness check
    expires.  A router with BFD notices in a fraction of a second; a router
    relying on IGP hellos takes seconds.

    Note that the transport layer detects and squelches whether or not it
    intends to recover anything, so this applies even where the optical layer
    has no recovery mechanism at all.
    """
    if propagation not in PROPAGATION:
        raise PolicyError('unknown propagation %r; known: %s'
                          % (propagation, ', '.join(sorted(PROPAGATION))))
    if propagation == 'squelch':
        return min(max(optical['detect_ms'], 0) + 1, packet['detect_ms'])
    return packet['detect_ms']


# ---------------------------------------------------------------------------
# the timeline
# ---------------------------------------------------------------------------
def simulate(optical, packet, propagation='squelch', repair_ms=None,
             wait_to_restore_ms=300000, revert=True, horizon_ms=600000,
             disturbances=()):
    """Play one fibre cut forward and read the outage off the resulting states.

    Nothing here appends a flap.  The service's up/down transitions are built
    into a list as they are caused, and 'churn' is counted off that list: the
    number of times the service goes DOWN AGAIN after it had come back.  A
    disturbance --- a non-hitless reversion, an untested repair failing, a
    second fault --- is passed in as (t_ms, why) and has to be named.  That is
    the whole difference from the old script, which appended the flap itself.
    """
    if repair_ms is not None and repair_ms < 0:
        raise PolicyError('the repair cannot complete before the cut')
    if wait_to_restore_ms < 0:
        raise PolicyError('wait-to-restore is not negative')

    events = [(0, 'cut', 'fibre cut on the working path; light is gone')]

    # --- optical layer -----------------------------------------------------
    optical_up_at = None
    if optical['kind'] != 'none':
        starts = optical['detect_ms'] + optical['holdoff_ms']
        events.append((optical['detect_ms'], 'detect',
                       'optical layer declares the line down'))
        if optical['holdoff_ms']:
            events.append((starts, 'start',
                           'optical layer begins %s' % optical['mechanism']))
        done = starts + optical['recover_ms']
        if optical['succeeds']:
            optical_up_at = done
            events.append((done, 'recovered',
                           'optical %s completes' % optical['kind']))
        else:
            events.append((done, 'failed',
                           'optical %s unavailable --- recovery resources cannot carry '
                           'the service under the supplied failure assumption'
                           % optical['kind']))

    # --- packet layer ------------------------------------------------------
    packet_up_at = None
    first_knowledge = horizon_for(packet, optical, propagation)
    if packet['kind'] != 'none':
        starts = first_knowledge + packet['holdoff_ms']
        events.append((first_knowledge, 'detect',
                       'packet layer can first know (%s)' % propagation))
        if packet['holdoff_ms']:
            events.append((starts, 'start',
                           'packet hold-off expires; packet layer begins %s'
                           % packet['mechanism']))
        done = starts + packet['recover_ms']
        # A packet reroute that starts after the optical layer has already
        # restored the link has nothing to reroute around: the link is up.
        if optical_up_at is not None and starts >= optical_up_at:
            events.append((starts, 'noop',
                           'packet hold-off expired after the link returned; '
                           'the packet layer has nothing to do'))
        elif packet['succeeds']:
            packet_up_at = done
            events.append((done, 'recovered',
                           'packet layer reroutes onto a surviving path'))
        else:
            events.append((done, 'failed',
                           'packet layer finds no alternate path with capacity'))

    # --- when is the service carrying again? -------------------------------
    candidates = [t for t in (optical_up_at, packet_up_at) if t is not None]
    restored_at = min(candidates) if candidates else None
    by = None
    if restored_at is not None:
        by = 'optical' if restored_at == optical_up_at else 'packet'

    # --- the later layer arriving is not, by itself, an outage -------------
    # It is a second usable path appearing.  Whether traffic MOVES is the
    # reversion policy's business, and whether moving costs anything depends
    # on whether the move is hitless.
    second = None
    if optical_up_at is not None and packet_up_at is not None:
        second = max(optical_up_at, packet_up_at)
        if second > restored_at:
            events.append((second, 'redundant',
                           'the other layer also completes; a second usable '
                           'path now exists --- traffic need not move'))

    # --- repair and reversion ----------------------------------------------
    if repair_ms is not None:
        events.append((repair_ms, 'repair', 'the fibre is spliced and tested'))
        if revert:
            back = repair_ms + wait_to_restore_ms
            events.append((back, 'revert',
                           'wait-to-restore expires; traffic returns to the '
                           'working path'))
    # --- derived, not asserted ---------------------------------------------
    # Build the service's own up/down transitions, then read the answers off
    # them.  The cut puts the service down.  The first successful recovery
    # brings it up.  Each supplied disturbance after that takes it down again
    # and, if it is transient, brings it back.
    transitions = [(0, 'down', 'the cut')]
    if restored_at is not None:
        transitions.append((restored_at, 'up', 'recovered by the %s layer' % by))
    for d in disturbances:
        t, why = d[0], d[1]
        back = d[2] if len(d) > 2 else None
        if restored_at is None or t <= restored_at:
            raise PolicyError('a disturbance at %r is not after the recovery at '
                              '%r; model it as part of the original failure'
                              % (t, restored_at))
        transitions.append((t, 'down', why))
        if back is not None:
            transitions.append((t + back, 'up', 'recovered from: %s' % why))
        events.append((t, 'disturb', why))
    transitions.sort(key=lambda x: x[0])
    events = [e for e in events if e[0] <= horizon_ms]
    events.sort(key=lambda e: (e[0], e[1]))

    down_cycles = len([1 for _, st, _ in transitions if st == 'down'])
    outage_ms = restored_at if restored_at is not None else None

    # total time down, summing every interval that began with a 'down'
    total_down = 0
    open_at = None
    for t, st, _ in transitions:
        if st == 'down' and open_at is None:
            open_at = t
        elif st == 'up' and open_at is not None:
            total_down += t - open_at
            open_at = None
    unfinished = open_at is not None

    return {
        'transitions': [{'t_ms': t, 'state': st, 'why': w}
                        for t, st, w in transitions],
        'total_down_ms': None if unfinished else total_down,
        'events': [{'t_ms': t, 'kind': k, 'what': w} for t, k, w in events],
        'restored_at_ms': restored_at,
        'restored_by': by,
        'outage_ms': outage_ms,
        'optical_up_at_ms': optical_up_at,
        'packet_up_at_ms': packet_up_at,
        'second_path_at_ms': second,
        'down_cycles': down_cycles,
        'churn_cycles': down_cycles - 1,
        'propagation': propagation,
        'unrecovered': restored_at is None,
    }


def churn_cycles(sim):
    """How many times the service went down AFTER it had come back.

    Read off the transition list the simulation built.  A single cut with a
    successful recovery gives zero, however many layers reacted to it --- which
    is the result the old script could not produce, because it appended the
    flap unconditionally whenever the timers compared a particular way.
    """
    return sim['churn_cycles']


def ms(v):
    if v is None:
        return '   never'
    if v >= 1000:
        return '%7.1f s' % (v / 1000.0)
    return '%6d ms' % v


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def section_a():
    print('A. The two mechanisms the chapter used to call by one name')
    print('-' * 74)
    print('%-22s %-12s %-10s %s' % ('mechanism', 'kind', 'recovers', 'can fail to recover'))
    for name in ('optical-protection', 'optical-restoration',
                 'packet-frr', 'packet-igp'):
        m = MECHANISMS[name]
        print('%-22s %-12s %-10s %s'
              % (name, m['kind'],
                 ms(m['recover_ms']).strip(),
                 'yes' if m['can_fail'] else 'no'))
    print()
    print('Protection pre-establishes resources; restoration may pre-plan a route')
    print('but completes establishment after the fault. Both can fail to recover.')
    print('These are illustrative timings and independent-path assumptions,')
    print('so "optical is fast" and "packet is fast" are both true and both useless')
    print('until you say WHICH mechanism.')
    print()


def build_cases():
    """Five policies for one fibre cut on a metro ring."""
    cases = []

    cases.append((
        'packet only, no optical recovery',
        layer('optical', detect_ms=10, mechanism_name='none'),
        layer('packet', detect_ms=150, mechanism_name='packet-igp'),
        'squelch', {}))

    cases.append((
        "the chapter's advice: optical restores, IP holds off",
        layer('optical', detect_ms=10, mechanism_name='optical-restoration'),
        layer('packet', detect_ms=150, mechanism_name='packet-igp',
              holdoff_ms=35000),
        'squelch', {}))

    cases.append((
        'both act, uncoordinated',
        layer('optical', detect_ms=10, mechanism_name='optical-restoration'),
        layer('packet', detect_ms=150, mechanism_name='packet-igp'),
        'squelch', {}))

    cases.append((
        'optical 1+1 protection, short IP hold-off',
        layer('optical', detect_ms=10, mechanism_name='optical-protection'),
        layer('packet', detect_ms=150, mechanism_name='packet-igp',
              holdoff_ms=250),
        'squelch', {}))

    cases.append((
        'same cut, transport HOLDS the client up, no BFD',
        layer('optical', detect_ms=10, mechanism_name='optical-restoration'),
        layer('packet', detect_ms=3000, mechanism_name='packet-igp'),
        'hold', {}))

    return cases


def section_b(cases):
    print('B. One fibre cut, five policies --- outage read off the timeline')
    print('-' * 74)
    print('%-52s %9s  %-8s %s'
          % ('policy', 'outage', 'restored', 'down again afterwards?'))
    rows = []
    for label, opt, pkt, prop, extra in cases:
        sim = simulate(opt, pkt, propagation=prop, **extra)
        rows.append((label, sim))
        print('%-52s %9s  %-8s %s'
              % (label, ms(sim['outage_ms']).strip(),
                 sim['restored_by'] or '--',
                 'no' if churn_cycles(sim) == 0 else
                 '%d more' % churn_cycles(sim)))
    print()
    base = rows[0][1]['outage_ms']
    advised = rows[1][1]['outage_ms']
    print('The packet layer alone is back in %s.  Holding it off for the optical'
          % ms(base).strip())
    print('layer takes %s --- %.0f times longer --- for the same cut.  The'
          % (ms(advised).strip(), advised / float(base)))
    print('hold-off did not coordinate anything; it chose the longer outage.')
    print()
    print('Nothing flapped in any of the five.  Churn is the service going down')
    print('AFTER it came back, counted off the transition list, and one cut with a')
    print('successful recovery produces none UNDER THIS MODEL. Real interaction')
    print('requires separate failure tests; the model does not simulate it.')
    print('Row 3 is the case the old lab called CHURN.  It is %s and clean.'
          % ms(rows[2][1]['outage_ms']).strip())
    print()
    print('The last row is the hold-off nobody configured.  Transport that holds')
    print('the client port up while it tries to recover leaves the router with')
    print('nothing to see, so the packet layer waits for its own liveness check:')
    print('%s here, against %s for the same cut when transport squelches.'
          % (ms(rows[4][1]['outage_ms']).strip(), ms(rows[2][1]['outage_ms']).strip()))
    print()
    print('The model assumes a squelched indication can trigger packet detection')
    print('after 1 ms, without debounce. Actual fault propagation and configured')
    print('hold timers must be measured; no universal timing priority follows.')
    print('Before choosing any')
    print('recovery policy, find out what your client ports actually do.')
    print()
    return rows


def section_c():
    print('C. What the hold-off is risking: restoration can fail')
    print('-' * 74)
    opt_fail = layer('optical', detect_ms=10,
                     mechanism_name='optical-restoration', succeeds=False)
    variants = [
        ('IP holds off 35 s, optical restoration fails',
         opt_fail, layer('packet', detect_ms=150, mechanism_name='packet-igp',
                         holdoff_ms=35000)),
        ('IP does not hold off, optical restoration fails',
         opt_fail, layer('packet', detect_ms=150, mechanism_name='packet-igp')),
        ('IP holds off, and has no alternate path either',
         opt_fail, layer('packet', detect_ms=150, mechanism_name='packet-igp',
                         holdoff_ms=35000, succeeds=False)),
    ]
    print('%-52s %9s  %s' % ('case', 'outage', 'restored by'))
    out = []
    for label, opt, pkt in variants:
        sim = simulate(opt, pkt)
        out.append((label, sim))
        print('%-52s %9s  %s'
              % (label, ms(sim['outage_ms']).strip(), sim['restored_by'] or '--'))
    print()
    print('The alternate route had no contiguous spectrum, or was long enough')
    print('that the mode stopped closing --- Lab 45.2 and Lab 46.2 respectively.')
    print('These are constructed unavailable-resource cases, not field frequency')
    print('estimates. The hold-off spent 35 seconds waiting for a mechanism')
    print('that was never going to succeed, while the packet layer had a path the')
    print('whole time and had been told not to use it.  The third row is the one')
    print('worth designing against: when neither layer can recover, no timer')
    print('helps until usable resources or another recovery action become available.')
    print()
    return out


def section_d():
    print('D. Where churn does come from, once you have to name a cause')
    print('-' * 74)
    opt = layer('optical', detect_ms=10, mechanism_name='optical-protection')
    pkt = layer('packet', detect_ms=150, mechanism_name='packet-igp')

    four_hours = 14400000
    wtr = 300000
    clean = simulate(opt, pkt, repair_ms=four_hours, wait_to_restore_ms=wtr)

    causes = [
        (four_hours + wtr, 'reversion is not hitless: the switch back drops '
                           'traffic for 40 ms', 40),
        (four_hours + wtr + 60000, 'the repaired splice was not tested before '
                                   'traffic returned, and it fails again', 50),
    ]
    dirty = simulate(opt, pkt, repair_ms=four_hours, wait_to_restore_ms=wtr,
                     disturbances=causes, horizon_ms=four_hours + 1200000)

    print('one cut, optical 1+1 protection, repaired at 4 h, 5 min wait-to-restore')
    print('  %-44s %s' % ('churn with no cause supplied', churn_cycles(clean)))
    print('  %-44s %s' % ('churn with two causes supplied', churn_cycles(dirty)))
    print('  %-44s %s' % ('total time down, no cause',
                          ms(clean['total_down_ms']).strip()))
    print('  %-44s %s' % ('total time down, two causes',
                          ms(dirty['total_down_ms']).strip()))
    print()
    for t, why, _ in causes:
        print('    t=%.2f h  %s' % (t / 3600000.0, why))
    print()
    print('Both causes are real and both are worth designing against --- and')
    print('neither of them is "two layers reacted to one cut".  The fix for the')
    print('first is a non-revertive policy or a hitless switch; for the second it')
    print('is proving the repair before traffic goes back on it.  Neither fix is')
    print('a hold-off timer, which is why the old lab\'s single recommendation')
    print('addressed none of the ways a converged network actually churns.')
    print()
    return {'clean': churn_cycles(clean), 'dirty': churn_cycles(dirty),
            'clean_down_ms': clean['total_down_ms'],
            'dirty_down_ms': dirty['total_down_ms']}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true',
                    help='emit the computed cases as JSON')
    args = ap.parse_args(argv)

    cases = build_cases()

    if args.json:
        payload = {
            'mechanisms': MECHANISMS,
            'cases': [{'label': lb, 'result': simulate(o, p, propagation=pr, **ex)}
                      for lb, o, p, pr, ex in cases],
        }
        json.dump(payload, sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write('\n')
        return 0

    print('Multi-layer recovery for one fibre cut (Chapter 46, section 6)')
    print('Durations are stated inputs.  No network, no optical equipment, no')
    print('control plane: this is a state list and some arithmetic.')
    print()
    section_a()
    section_b(cases)
    section_c()
    section_d()
    print('What this does NOT establish')
    print('-' * 74)
    print('- No measurement of any kind.  Every duration is an input, and real')
    print('  ones vary by equipment, control plane, path and channel loading.')
    print('- Restoration times in particular are not a constant: the 30 s here')
    print('  stands for "seconds to minutes" and a loaded line system with many')
    print('  channels to re-level can be well outside it.')
    print('- The model has one service on one link.  A real ring has many, they')
    print('  share the alternate capacity, and whether they all fit is Lab 46.2')
    print('  and the capacity question this script does not ask.')
    print('- Nothing here says which policy is right for your network.  It says')
    print('  the answer follows from the mechanisms and their times, and that a')
    print('  hold-off buys nothing unless the layer it waits for is both faster')
    print('  and more likely to succeed than the layer it delays.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
