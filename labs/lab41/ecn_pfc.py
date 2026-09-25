#!/usr/bin/env python3
"""Lab 41.2 --- why the ECN threshold that works depends on the fabric, not the vendor.

WHY THIS VERSION EXISTS
-----------------------
The previous script marked the queue and cut the sender's rate in the SAME time
step.  With no delay between the mark and the response, the queue could overrun
its ECN threshold by at most one step's worth of arrivals --- 0.6 packets --- so
PFC never fired for any threshold below 99.4% of the PAUSE line.  It reported
that as "ECN carries it, PFC quiet" and presented it as the tuning lesson.

It was not a lesson.  It was the model's arithmetic.  A control loop with zero
feedback delay cannot overshoot, so that script could only ever say the
configuration was fine, whatever you set.  Worse, it contradicted the chapter it
was illustrating, which says the parameters interact and the safe region is
narrow.  In that model the safe region was everything.

The delay is not a detail of the model.  The delay IS the problem.  Between the
switch marking a packet and the sender slowing down sit: the rest of the path to
the receiver, the receiver noticing, the congestion notification travelling back,
and the sender acting on it.  The queue grows for all of it.  Everything hard
about lossless Ethernet lives in that interval.

WHAT IS MODELLED
----------------
One switch egress port, as a fluid queue, in dimensionless steps where one step
drains one packet.

  * A burst of senders offers more than the port can drain (incast).
  * The switch marks with RED/WRED thresholds: nothing below kmin, everything
    above kmax, and a linear probability between them --- the three numbers a
    switch actually takes, not a single "threshold".
  * A mark becomes a rate cut at the sender only after `delay` steps.  The
    receiver also rate-limits how often it may signal, as NICs do.
  * PFC is separate and lower down: the switch asserts PAUSE above `xoff` and
    releases below `xon`, and the upstream device needs `pfc_delay` steps to
    react.  Bytes keep arriving for that whole interval.
  * Above `capacity` the switch drops.  That is the fabric failing to be
    lossless, and it is counted separately from PFC firing.

WHAT IS NOT MODELLED
--------------------
This is NOT DCQCN.  DCQCN is a specific algorithm with a smoothed alpha, byte
and timer counters, and fast-recovery, additive-increase and hyper-increase
stages; none of that is here.  The cut factor and the increase step below are
ARBITRARY CONSTANTS chosen to make the feedback loop visible, not measured
parameters and not any vendor's defaults.  There is no switch, no NIC, no RoCE
traffic and no hardware anywhere in this file.  It cannot validate a
configuration, and no number it prints should be typed into a device.

What it can do --- and what the old script could not --- is FAIL, and show you
which way the safe region moves when the fabric changes.

    python3 ecn_pfc.py
    python3 ecn_pfc.py --json
    python3 test_ecn_pfc.py
"""
import argparse
import json
import sys


class ModelError(ValueError):
    """The parameters do not describe a queue that can be simulated."""


DEFAULTS = dict(
    steps=4000,
    service=1.0,        # packets drained per step, by definition
    offered=4.0,        # peak offered rate: a 4:1 incast onto one egress port
    r_min=0.25,         # the senders never stop entirely on a mark alone
    cut=0.55,           # ARBITRARY multiplicative decrease on a notification
    ai=0.06,            # ARBITRARY additive increase per recovery tick
    ai_period=8,        # steps between increases
    cnp_period=12,      # the receiver may signal at most this often
    delay=24,           # steps from mark to rate change: THE feedback delay
    kmin=None,          # set per run
    kmax=None,          # default: kmin + kspan
    kspan=40.0,         # width of the WRED ramp
    pmax=1.0,           # marking probability at kmax
    xoff=200.0,         # PFC asserts above this
    xon=150.0,          # PFC releases below this
    pfc_delay=16,       # steps before the upstream device actually stops
    capacity=260.0,     # buffer ceiling: above this the switch DROPS
)


def simulate(kmin, **over):
    """Run one configuration. Returns a dict of what happened.

    Deterministic: the marking probability is applied to the fluid arrival rate
    rather than sampled, so the same inputs always give the same answer and the
    checks can assert on it.
    """
    p = dict(DEFAULTS)
    p.update(over)
    p['kmin'] = float(kmin)
    if p['kmax'] is None:
        p['kmax'] = p['kmin'] + p['kspan']
    for name in ('service', 'offered', 'capacity', 'xoff', 'xon'):
        if p[name] <= 0:
            raise ModelError('%s must be positive, got %r' % (name, p[name]))
    if p['kmin'] < 0:
        raise ModelError('kmin must not be negative, got %r' % (p['kmin'],))
    if p['kmax'] < p['kmin']:
        raise ModelError('kmax (%r) must not be below kmin (%r)'
                         % (p['kmax'], p['kmin']))
    if p['xon'] >= p['xoff']:
        raise ModelError('xon (%r) must be below xoff (%r) or PFC chatters'
                         % (p['xon'], p['xoff']))
    if p['xoff'] > p['capacity']:
        raise ModelError('xoff (%r) above capacity (%r): PAUSE could never be '
                         'sent before the buffer overflows'
                         % (p['xoff'], p['capacity']))
    if p['delay'] < 0 or p['pfc_delay'] < 0:
        raise ModelError('delays must not be negative')
    if not 0 < p['cut'] < 1:
        raise ModelError('the decrease factor must be between 0 and 1')

    q = 0.0
    rate = p['offered']
    pause_active = False
    asserted_at = None      # step at which PAUSE was asserted
    released_at = None      # step at which PAUSE was released
    pending = []            # notifications in flight, by arrival step
    last_signal = -10 ** 9
    pause_asserts = 0
    paused_steps = 0
    dropped = 0.0
    maxq = 0.0
    overshoot = 0.0         # how far above xoff the queue went after a PAUSE
    marked_steps = 0
    last_increase = 0

    def upstream_stopped(t):
        """Is the upstream device actually not sending at step t?

        PAUSE does not take effect when it is asserted; it takes effect
        pfc_delay steps later, once it has propagated and the peer has acted.
        Arrivals continue for that whole interval --- which is the entire
        reason buffer headroom above xoff has to exist. Release is delayed
        the same way, which is why xon sits well below xoff.
        """
        if asserted_at is None:
            return False
        if t < asserted_at + p['pfc_delay']:
            return False            # asserted, but not yet in effect
        if released_at is not None and released_at >= asserted_at:
            return t < released_at + p['pfc_delay']
        return True

    for t in range(int(p['steps'])):
        # ---- the sender acts on notifications that have arrived -------------
        due = [s for s in pending if s <= t]
        if due:
            pending = [s for s in pending if s > t]
            rate = max(p['r_min'], rate * p['cut'])
            last_increase = t
        elif t - last_increase >= p['ai_period']:
            rate = min(p['offered'], rate + p['ai'])
            last_increase = t

        # ---- arrivals, unless PFC has actually stopped the upstream ---------
        arrivals = 0.0 if upstream_stopped(t) else rate
        q += arrivals
        if q > p['xoff']:
            overshoot = max(overshoot, q - p['xoff'])

        # ---- the switch drops if the buffer is exceeded ---------------------
        if q > p['capacity']:
            dropped += q - p['capacity']
            q = p['capacity']

        # ---- ECN marking: RED ramp between kmin and kmax --------------------
        if q > p['kmin'] and arrivals > 0:
            if q >= p['kmax']:
                prob = p['pmax']
            else:
                prob = p['pmax'] * (q - p['kmin']) / (p['kmax'] - p['kmin'])
            if prob > 0:
                marked_steps += 1
                # the receiver may only signal so often
                if t - last_signal >= p['cnp_period'] / max(prob, 1e-9):
                    last_signal = t
                    pending.append(t + p['delay'])

        # ---- PFC: assert above xoff, release below xon, both with delay -----
        if not pause_active and q > p['xoff']:
            pause_active = True
            pause_asserts += 1
            asserted_at = t
            released_at = None
        elif pause_active and q < p['xon']:
            pause_active = False
            released_at = t
        if pause_active:
            paused_steps += 1

        # ---- drain ----------------------------------------------------------
        q = max(0.0, q - p['service'])
        maxq = max(maxq, q)

    lossless = dropped == 0.0
    return {
        'kmin': p['kmin'],
        'kmax': p['kmax'],
        'delay': p['delay'],
        'xoff': p['xoff'],
        'xon': p['xon'],
        'capacity': p['capacity'],
        'pause_asserts': pause_asserts,
        'paused_steps': paused_steps,
        'max_queue': maxq,
        'overshoot': overshoot,
        'dropped': dropped,
        'lossless': lossless,
        'marked_steps': marked_steps,
        # two ways to state the same requirement. The net figure is what the
        # queue actually accumulates while PAUSE is in flight, and the model
        # reproduces it exactly; the gross figure is the conservative one an
        # engineer uses when the drain cannot be relied on.
        'headroom_needed_net': (p['offered'] - p['service']) * p['pfc_delay'],
        'headroom_needed_gross': p['offered'] * p['pfc_delay'],
        'headroom_available': p['capacity'] - p['xoff'],
        'verdict': verdict(pause_asserts, dropped),
    }


def verdict(pause_asserts, dropped):
    if dropped > 0:
        return 'DROPPED --- not lossless at all'
    if pause_asserts == 0:
        return 'ECN held it; PFC never fired'
    return ('PFC fired once --- ECN was too late' if pause_asserts == 1
            else 'PFC fired %d times --- ECN was too late' % pause_asserts)


def highest_safe_kmin(lo=5.0, hi=None, tol=0.5, **over):
    """The largest ECN kmin that still keeps PFC quiet, by bisection.

    This is the number the old model could not produce, because in it every
    kmin below xoff was safe. Here the edge is real and it MOVES with the
    feedback delay, which is the point.
    """
    p = dict(DEFAULTS)
    p.update(over)
    if hi is None:
        hi = p['xoff']
    if simulate(lo, **over)['pause_asserts'] > 0:
        return None                       # not even the lowest threshold holds
    if simulate(hi, **over)['pause_asserts'] == 0:
        return hi                         # everything holds; say so honestly
    while hi - lo > tol:
        mid = (lo + hi) / 2.0
        if simulate(mid, **over)['pause_asserts'] == 0:
            lo = mid
        else:
            hi = mid
    return lo


def analyse():
    thresholds = [20, 60, 120, 180]
    rows = [simulate(k) for k in thresholds]
    delays = [0, 8, 24, 48]
    edges = [{'delay': d, 'highest_safe_kmin': highest_safe_kmin(delay=d)}
             for d in delays]
    # headroom only means anything once PFC actually fires, so use a threshold
    # that makes it fire, and shrink the buffer above xoff until the switch drops.
    caps = [300.0, 260.0, 250.0, 240.0, 220.0]
    head = [simulate(180, capacity=c) for c in caps]
    # and the worst case: no ECN at all, so the rate is never cut and the full
    # offered rate is still arriving throughout the PFC reaction time.
    noecn = [simulate(10 ** 6, capacity=c, xoff=200.0, xon=150.0)
             for c in (300.0, 260.0)]
    return {'rows': rows, 'edges': edges, 'headroom': head, 'no_ecn': noecn,
            'defaults': {k: v for k, v in DEFAULTS.items() if k != 'kmin'}}


def report(a):
    d = a['defaults']
    print('One egress port, fluid model, dimensionless steps (1 step drains 1 packet).')
    print('offered %.1f  service %.1f  xoff %.0f  xon %.0f  capacity %.0f  '
          'feedback delay %d steps'
          % (d['offered'], d['service'], d['xoff'], d['xon'], d['capacity'],
             d['delay']))
    print('The decrease factor and increase step are arbitrary. This is NOT '
          'DCQCN and NOT a device.\n')

    print('A. Where the ECN ramp starts, at a fixed feedback delay of %d steps'
          % d['delay'])
    print('%8s | %8s | %9s | %7s | %s'
          % ('kmin', 'kmax', 'max queue', 'drops', 'verdict'))
    print('-' * 76)
    for r in a['rows']:
        print('%8.0f | %8.0f | %9.1f | %7.1f | %s'
              % (r['kmin'], r['kmax'], r['max_queue'], r['dropped'],
                 r['verdict']))
    print('\nMark early and the senders are already slowing while the queue is')
    print('small. Mark late and the queue keeps climbing for the whole feedback')
    print('interval after the first mark --- straight through the PFC line.')

    print('\nB. The safe threshold is a property of the FABRIC, not the vendor')
    print('%14s | %s' % ('feedback delay', 'highest kmin that keeps PFC quiet'))
    print('-' * 56)
    for e in a['edges']:
        v = ('%.1f' % e['highest_safe_kmin']) if e['highest_safe_kmin'] is not None \
            else 'none --- no threshold works'
        note = '  (instant feedback: the old model lived here)' if e['delay'] == 0 else ''
        print('%11d st | %s%s' % (e['delay'], v, note))
    print('\nLonger paths, slower notification, more hops --- the usable region')
    print('shrinks. A threshold copied from someone else\'s fabric is a guess.')

    print('\nC. Headroom is a separate requirement from the threshold')
    print('When PAUSE is asserted the upstream device does not stop; it stops')
    print('%d steps later, and keeps sending for all of them. The queue must'
          % d['pfc_delay'])
    print('have room above xoff for what arrives in that window, net of what')
    print('drains: (%.1f - %.1f) x %d = %.0f packets.'
          % (d['offered'], d['service'], d['pfc_delay'],
             (d['offered'] - d['service']) * d['pfc_delay']))
    print('\nSame ECN setting (kmin=180, so PFC does fire), shrinking the buffer:')
    print('%9s | %9s | %9s | %7s | %s'
          % ('capacity', 'headroom', 'overshoot', 'drops', 'lossless'))
    print('-' * 62)
    for r in a['headroom']:
        print('%9.0f | %9.0f | %9.1f | %7.1f | %s'
              % (r['capacity'], r['headroom_available'], r['overshoot'],
                 r['dropped'], 'yes' if r['lossless'] else 'NO'))
    need = a['headroom'][0]['headroom_needed_net']
    print('\nThe overshoot never exceeds the predicted %.0f packets --- it sits'
          % need)
    print('just under, because ECN had already trimmed the rate --- and the')
    print('switch drops as soon as the headroom falls below it. PFC asserting')
    print('is not the failure. Asserting without the buffer to cover its own')
    print('reaction time is the failure, and it presents as loss on a fabric')
    print('everyone believes is lossless.')
    print('\nWith ECN off entirely the senders are never slowed, so the full')
    print('offered rate is still arriving throughout that window:')
    print('%9s | %9s | %9s | %7s | %s'
          % ('capacity', 'headroom', 'overshoot', 'drops', 'lossless'))
    print('-' * 62)
    for r in a['no_ecn']:
        print('%9.0f | %9.0f | %9.1f | %7.1f | %s'
              % (r['capacity'], r['headroom_available'], r['overshoot'],
                 r['dropped'], 'yes' if r['lossless'] else 'NO'))
    print('\nECN and headroom are not two spellings of one setting. ECN decides')
    print('whether PFC fires at all; headroom decides whether PFC firing costs')
    print('you the losslessness you bought it for.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        a = analyse()
    except ModelError as e:
        print('model error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(a, indent=2))
    else:
        report(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
