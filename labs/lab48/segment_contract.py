#!/usr/bin/env python3
"""Lab 48.3 --- a mobile transport contract, instead of a table of adjectives.

WHY THIS VERSION EXISTS
-----------------------
The script this replaces checked a path against three hard-coded "segments" and
then printed a fixed closing paragraph.  Run it and the contradiction is on the
screen at once:

      [FAIL] midhaul:
               - sync 'frequency' weaker than required 'phase'
    ...
    The shared backhaul-grade path carries backhaul and (barely) midhaul,

It printed FAIL for midhaul and then said the path carries midhaul.  The
paragraph was not computed from the result; it was typed underneath it.

Three things beneath that are worse than the slip.

  THE REQUIREMENTS WERE INVENTED.  A 1 us jitter limit for fronthaul, 50 us for
  midhaul, 500 us for backhaul: none of those comes from anywhere.  The eCPRI
  transport requirements do not specify a packet delay variation figure at all
  (Lab 48.1).  A number a reader cannot trace is worse than no number, because
  they will design to it.

  SYNCHRONISATION WAS A RANK.  frequency=1, phase=2, phase-tight=3, compared with
  "<".  Frequency and phase are different QUANTITIES, not three amounts of one
  (Chapter 47), and "phase-tight" is not a thing a requirement says.  A real
  requirement states a time error, at a reference point, as an absolute or a
  relative figure.

  THE SEGMENT NAME WAS TREATED AS A SPECIFICATION.  "Fronthaul" is not a
  requirement.  What the transport has to meet comes from the split option, the
  plane, the interface at each end, the delay class, the loss ratio, the time
  error, the capacity and the failure state --- and two deployments both called
  fronthaul can differ in every one of those.

So this takes an explicit contract, checks a path against it clause by clause,
and refuses to score a clause the contract did not state.

    python3 segment_contract.py
    python3 segment_contract.py --json
    python3 test_segment_contract.py

No radio, no transport equipment, no measurement.  The example contracts below
are illustrative and are not any operator's or any vendor's; the eCPRI delay
classes and frame loss ratios they reference come from Lab 48.1.
"""
import argparse
import json
import sys

from fronthaul_budget import ECPRI_DELAY_CLASSES, ECPRI_FRAME_LOSS


class ContractError(ValueError):
    """The contract or the path is not well formed."""


SPLITS = ('integrated', 'split 2 (higher layer)', 'split 7.2x (lower layer)',
          'split 8 (CPRI)')
PLANES = ('user', 'control', 'management', 'synchronisation')


def contract(name, split, plane, endpoint_a, endpoint_b,
             delay_class=None, max_delay_us=None, frame_loss_ratio=None,
             pdv_us=None, absolute_te_ns=None, relative_te_ns=None,
             capacity_gbps=None, failure_state=None, mtu_bytes=None):
    """What the transport is actually required to do, stated.

    Every requirement is optional and defaults to None, which means NOT STATED.
    That is the point: a contract with holes in it is the normal case, and a
    checker that silently passes an unstated clause is how a design gets
    approved against requirements nobody wrote down.  Unstated comes back as
    unstated.
    """
    if split not in SPLITS:
        raise ContractError('%s: unknown split %r; known: %s'
                            % (name, split, ', '.join(SPLITS)))
    if plane not in PLANES:
        raise ContractError('%s: unknown plane %r; known: %s'
                            % (name, plane, ', '.join(PLANES)))
    if delay_class is not None and delay_class not in ECPRI_DELAY_CLASSES:
        raise ContractError('%s: unknown delay class %r' % (name, delay_class))
    if delay_class is not None and max_delay_us is not None:
        raise ContractError('%s: state the delay as a class OR a figure, not '
                            'both --- they are the same requirement and two '
                            'copies of it will diverge' % name)
    if absolute_te_ns is not None and relative_te_ns is not None:
        raise ContractError('%s: absolute and relative time error are different '
                            'requirements measured differently; state which one '
                            'applies' % name)
    if delay_class is not None:
        max_delay_us = ECPRI_DELAY_CLASSES[delay_class]
    return {'name': name, 'split': split, 'plane': plane,
            'endpoint_a': endpoint_a, 'endpoint_b': endpoint_b,
            'delay_class': delay_class, 'max_delay_us': max_delay_us,
            'frame_loss_ratio': frame_loss_ratio, 'pdv_us': pdv_us,
            'absolute_te_ns': absolute_te_ns, 'relative_te_ns': relative_te_ns,
            'capacity_gbps': capacity_gbps, 'failure_state': failure_state,
            'mtu_bytes': mtu_bytes}


def path(name, delay_us, frame_loss_ratio=None, pdv_us=None,
         absolute_te_ns=None, relative_te_ns=None, capacity_gbps=None,
         mtu_bytes=None, delay_us_on_failure=None,
         capacity_gbps_on_failure=None):
    """What the transport actually delivers, measured or engineered.

    delay_us_on_failure and capacity_gbps_on_failure are what it delivers on the
    protection path.  A design checked only in its working state has not been
    checked: the failure path is where the requirement is usually missed, and it
    is the state the network will be in at the worst moment.
    """
    if delay_us < 0:
        raise ContractError('%s: delay is not negative' % name)
    return {'name': name, 'delay_us': delay_us,
            'frame_loss_ratio': frame_loss_ratio, 'pdv_us': pdv_us,
            'absolute_te_ns': absolute_te_ns, 'relative_te_ns': relative_te_ns,
            'capacity_gbps': capacity_gbps, 'mtu_bytes': mtu_bytes,
            'delay_us_on_failure': delay_us_on_failure,
            'capacity_gbps_on_failure': capacity_gbps_on_failure}


def _cmp(required, delivered, smaller_is_better=True):
    """Return True, False or None --- None meaning the clause was not stated."""
    if required is None:
        return None
    if delivered is None:
        return None
    return delivered <= required if smaller_is_better else delivered >= required


def check(ctr, pth, state='working'):
    """Compare one path with one contract, clause by clause.

    state is 'working' or 'failure'.  Checking the failure state uses the
    path's failure figures where it has them.
    """
    if state not in ('working', 'failure'):
        raise ContractError("state is 'working' or 'failure', got %r" % (state,))
    delay = pth['delay_us']
    cap = pth['capacity_gbps']
    if state == 'failure':
        if pth['delay_us_on_failure'] is None and pth['capacity_gbps_on_failure'] is None:
            raise ContractError('%s: no failure-state figures were supplied, so '
                                'the failure state cannot be checked. That is a '
                                'gap in the design, not a pass.' % pth['name'])
        if pth['delay_us_on_failure'] is not None:
            delay = pth['delay_us_on_failure']
        if pth['capacity_gbps_on_failure'] is not None:
            cap = pth['capacity_gbps_on_failure']

    clauses = [
        ('one-way delay', _cmp(ctr['max_delay_us'], delay),
         '%s us delivered against %s us required'
         % (_fmt(delay), _fmt(ctr['max_delay_us']))),
        ('frame loss ratio', _cmp(ctr['frame_loss_ratio'], pth['frame_loss_ratio']),
         '%s delivered against %s required'
         % (_fmt(pth['frame_loss_ratio']), _fmt(ctr['frame_loss_ratio']))),
        ('packet delay variation', _cmp(ctr['pdv_us'], pth['pdv_us']),
         '%s us delivered against %s us required'
         % (_fmt(pth['pdv_us']), _fmt(ctr['pdv_us']))),
        ('absolute time error', _cmp(ctr['absolute_te_ns'], pth['absolute_te_ns']),
         '%s ns delivered against %s ns required'
         % (_fmt(pth['absolute_te_ns']), _fmt(ctr['absolute_te_ns']))),
        ('relative time error', _cmp(ctr['relative_te_ns'], pth['relative_te_ns']),
         '%s ns delivered against %s ns required'
         % (_fmt(pth['relative_te_ns']), _fmt(ctr['relative_te_ns']))),
        ('capacity', _cmp(ctr['capacity_gbps'], cap, smaller_is_better=False),
         '%s Gb/s delivered against %s Gb/s required'
         % (_fmt(cap), _fmt(ctr['capacity_gbps']))),
        ('MTU', _cmp(ctr['mtu_bytes'], pth['mtu_bytes'], smaller_is_better=False),
         '%s delivered against %s required'
         % (_fmt(pth['mtu_bytes']), _fmt(ctr['mtu_bytes']))),
    ]
    failed = [c[0] for c in clauses if c[1] is False]
    unstated = [c[0] for c in clauses if c[1] is None]
    return {'contract': ctr['name'], 'path': pth['name'], 'state': state,
            'clauses': clauses, 'failed': failed, 'unstated': unstated,
            'meets': not failed, 'complete': not unstated}


def _fmt(v):
    if v is None:
        return '--'
    if isinstance(v, float) and v < 0.01:
        return '%.0e' % v
    if isinstance(v, float):
        return ('%.1f' % v).rstrip('0').rstrip('.')
    return str(v)


def verdict(r):
    if r['failed']:
        return 'FAILS: ' + ', '.join(r['failed'])
    if r['unstated']:
        return 'meets what was stated (%d clause%s unstated)' % (
            len(r['unstated']), '' if len(r['unstated']) == 1 else 's')
    return 'meets, complete'


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
FH = contract('open fronthaul, user', 'split 7.2x (lower layer)', 'user',
              'radio unit', 'distributed unit', delay_class='High100',
              frame_loss_ratio=ECPRI_FRAME_LOSS['High'], pdv_us=None,
              relative_te_ns=130, capacity_gbps=25.0, mtu_bytes=1500,
              failure_state='no protection; the site is down')

MH = contract('DU to CU, user',
              'split 2 (higher layer)', 'user', 'distributed unit',
              'central unit', max_delay_us=1000.0, frame_loss_ratio=1e-6,
              capacity_gbps=10.0, mtu_bytes=9000,
              failure_state='protected; must still meet delay and capacity')

BH = contract('CU to core, user', 'split 2 (higher layer)',
              'user', 'central unit', 'user plane function',
              max_delay_us=5000.0, frame_loss_ratio=1e-5, capacity_gbps=10.0,
              mtu_bytes=9000, failure_state='protected')

SHARED = path('one shared IP/MPLS path, 1 ms grade',
              delay_us=1000.0, frame_loss_ratio=1e-6, pdv_us=50.0,
              relative_te_ns=None, capacity_gbps=10.0, mtu_bytes=9000,
              delay_us_on_failure=2400.0, capacity_gbps_on_failure=10.0)

ENGINEERED = path('engineered shared metro, fronthaul prioritised',
                  delay_us=64.0, frame_loss_ratio=1e-8, pdv_us=3.0,
                  relative_te_ns=90, capacity_gbps=25.0, mtu_bytes=1500,
                  delay_us_on_failure=88.0, capacity_gbps_on_failure=25.0)


def section_a():
    print('A. What a contract has to say before a path can be checked')
    print('-' * 74)
    for k in ('split', 'plane', 'endpoint_a', 'endpoint_b', 'delay_class',
              'max_delay_us', 'frame_loss_ratio', 'pdv_us', 'relative_te_ns',
              'absolute_te_ns', 'capacity_gbps', 'mtu_bytes', 'failure_state'):
        print('  %-22s %s' % (k.replace('_', ' '), _fmt(FH[k])))
    print()
    print('  Note the packet delay variation clause: NOT STATED.  The transport')
    print('  specification does not give one (Lab 48.1), so this contract leaves')
    print('  it open rather than inventing the 1 us the old lab enforced.  An')
    print('  unstated clause is a question for the radio vendor, not a pass.')
    print()
    print('  Note also the time error clause: a RELATIVE figure, in nanoseconds,')
    print('  because that is what a requirement says. A word like "phase-tight"')
    print('  is not a requirement and cannot be checked.')
    print()


def section_b():
    print('B. The shared path the checkpoint proposes')
    print('-' * 74)
    print('%-26s %s' % ('contract', 'verdict'))
    out = []
    for ctr in (FH, MH, BH):
        r = check(ctr, SHARED)
        out.append(r)
        print('%-26s %s' % (ctr['name'][:26], verdict(r)))
    print()
    for r in out:
        if not r['failed']:
            continue
        print('  %s' % r['contract'])
        for n, ok, detail in r['clauses']:
            if ok is False:
                print('      %-24s %s' % (n, detail))
    print()
    fh = out[0]
    print('  The fronthaul contract fails on %d of the %d clauses it states.'
          % (len(fh['failed']), len(fh['clauses']) - len(fh['unstated'])))
    print('  The midhaul and backhaul contracts are met --- and the old lab said')
    print('  midhaul failed, on a synchronisation rank it had invented.  There is')
    print('  no phase requirement in the midhaul contract to fail: whether one')
    print('  exists depends on the split and the radio features, which is what')
    print('  the contract is for.')
    print()
    return out


def section_c():
    print('C. The same three contracts, against an engineered shared path')
    print('-' * 74)
    print('%-26s %s' % ('contract', 'verdict'))
    out = []
    for ctr in (FH, MH, BH):
        r = check(ctr, ENGINEERED)
        out.append(r)
        print('%-26s %s' % (ctr['name'][:26], verdict(r)))
    print()
    for r in out:
        if not r['failed']:
            continue
        print('  %s' % r['contract'])
        for n, ok, detail in r['clauses']:
            if ok is False:
                print('      %-24s %s' % (n, detail))
    print()
    fh = out[0]
    if fh['meets']:
        print('  The FRONTHAUL contract is met --- on a shared path.  That is the')
        print('  finding the old framing could not produce: it treated')
        print('  "dedicated" and "ordinary IP/MPLS" as the only two options and')
        print('  concluded from the segment NAME that fronthaul cannot share.')
        print('  What decides it is whether the contract is met under load and on')
        print('  the failure path, and an engineered path that gives fronthaul its')
        print('  own class can meet a fronthaul contract while carrying other')
        print('  traffic.')
    print()
    mtu_fails = [r for r in out if 'MTU' in r['failed']]
    if mtu_fails:
        print('  And the model found the real tension, which is not latency at')
        print('  all.  The path was engineered for fronthaul with a %d-byte MTU'
              % ENGINEERED['mtu_bytes'])
        print('  --- small frames keep serialisation down, which is what Lab 48.1')
        print('  showed costs the reach --- and %d of the contracts need %d bytes,'
              % (len(mtu_fails), MH['mtu_bytes']))
        print('  because midhaul and backhaul carry tunnelled traffic whose')
        print('  encapsulation has to fit.  So a single shared path serves all')
        print('  three only if it can carry both frame sizes, which is a')
        print('  configuration question nobody asks when the segments are')
        print('  described as three rows of adjectives.')
    print()
    print('  None of this is a design that works.  It is a design that might.')
    print('  Every figure in the engineered path is an assumption until it is')
    print('  measured under peak load, and the clause the contract leaves')
    print('  unstated is still unstated.')
    print()
    return out


def section_d():
    print('D. The state the design is in at the worst moment')
    print('-' * 74)
    print('%-26s %-10s %s' % ('contract', 'working', 'after a failure'))
    out = []
    for ctr, pth in ((FH, ENGINEERED), (MH, SHARED), (BH, SHARED)):
        w = check(ctr, pth, 'working')
        f = check(ctr, pth, 'failure')
        out.append((w, f))
        print('%-26s %-10s %s'
              % (ctr['name'][:26],
                 'meets' if w['meets'] else 'FAILS',
                 'meets' if f['meets'] else 'FAILS: ' + ', '.join(f['failed'])))
    print()
    print('  The midhaul contract is met in the working state and missed on the')
    print('  protection path, where the delay goes from %.0f to %.0f us against'
          % (SHARED['delay_us'], SHARED['delay_us_on_failure']))
    print('  a %.0f us requirement.  Nothing in a working-state check finds that,'
          % MH['max_delay_us'])
    print('  and it is the state the network is in on the day it matters.')
    print()
    try:
        check(FH, path('a path with no failure figures', delay_us=50.0),
              'failure')
    except ContractError as e:
        import textwrap
        print('  A path that supplies no failure figures cannot be checked in')
        print('  that state, and the model says so rather than passing it:')
        for line in textwrap.wrap(str(e), 68):
            print('      %s' % line)
    print()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    if args.json:
        json.dump({'contracts': [FH, MH, BH],
                   'shared': [check(c, SHARED) for c in (FH, MH, BH)],
                   'engineered': [check(c, ENGINEERED) for c in (FH, MH, BH)]},
                  sys.stdout, indent=1, sort_keys=True, default=str)
        sys.stdout.write('\n')
        return 0
    print('Mobile transport as a contract (Chapter 48)')
    print('Contracts and paths below are illustrative and are nobody\'s real')
    print('requirements. Nothing was measured.')
    print()
    section_a()
    section_b()
    section_c()
    section_d()
    print('What this does NOT establish')
    print('-' * 74)
    print('- No radio, no transport equipment, no measurement. Every figure in')
    print('  every contract and every path is a stated input.')
    print('- The contracts are illustrative. A real one comes from the radio')
    print('  vendor, the split and the operator\'s own service definition, and')
    print('  two deployments both called fronthaul can differ in every clause.')
    print('- The clause list is not complete: security, management-plane')
    print('  reachability, MTU across every encapsulation, and the assurance')
    print('  that the contract is met over time are all missing.')
    print('- Meeting a contract on paper is not meeting it. These figures stand')
    print('  in for measurements taken under peak load, on the working path and')
    print('  on the failure path, at the stated reference points.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
