#!/usr/bin/env python3
"""Lab 40.2 --- check an INTENDED bond against an INTENDED switch LAG.

WHAT THIS IS. A validator for a pair of configurations you are about to apply.
It knows the real Linux bonding modes, knows which of them require what from the
switch, and refuses input it does not recognise.

WHAT THIS IS NOT --- and the previous version claimed otherwise. It is not a
running bond. Nothing in this book demonstrates LACP actor and partner state,
because the host these labs were prepared on has no bonding driver (Lab 40.1
reports that rather than hiding it). It cannot tell you what a mismatch will do
on your kit; it tells you that the two sides disagree and what the plausible
outcomes are.

WHAT THE PREVIOUS VERSION GOT WRONG, all of which these checks now prevent:

  * It tested `mode == "802.3ad"` and treated EVERY other string as a valid
    static mode. A typo, or an invented word, passed silently as "static".
  * It said every mismatch produces a bond that "half-works" and "pings fine".
    An LACP/static mismatch can prevent forwarding entirely, or fall back, or
    half-work --- which one depends on configuration you have to look at.
  * It compared a host MTU against a switch MTU as if they measured the same
    thing. Commonly they do not: a host IP MTU is payload, a switch maximum
    frame size usually includes the Ethernet header and sometimes the FCS.

    python3 bondcheck.py [--json]
"""
import argparse
import json
import sys

# The Linux bonding modes, by name and number, and what each needs from the
# switch. Anything not in this table is rejected rather than assumed static.
MODES = {
    'balance-rr':    (0, 'switch-lag', 'Requires a static LAG on the switch; without one, '
                                       'the same MAC appears on several ports.'),
    'active-backup': (1, 'none',       'Needs NO switch aggregation. One member is active; '
                                       'the rest stand by.'),
    'balance-xor':   (2, 'switch-lag', 'Requires a static LAG. The transmit hash is the '
                                       'host\'s own choice.'),
    'broadcast':     (3, 'switch-lag', 'Requires a static LAG. Rarely used.'),
    '802.3ad':       (4, 'lacp',       'Requires an LACP partner on the switch, or a '
                                       'coordinated multi-chassis partner.'),
    'balance-tlb':   (5, 'none',       'Needs no switch aggregation; balances transmit only.'),
    'balance-alb':   (6, 'none',       'Needs no switch aggregation; uses ARP negotiation, '
                                       'which has its own consequences.'),
}
SWITCH_SIDES = {
    'lacp':   'An LACP-speaking LAG.',
    'static': 'A statically configured LAG with no LACP.',
    'access': 'Independent ports with no aggregation at all.',
}
HASH_POLICIES = {'layer2', 'layer2+3', 'layer3+4', 'encap2+3', 'encap3+4', 'vlan+srcmac'}


class BondError(ValueError):
    pass


def validate(server, switch):
    mode = server.get('mode')
    if mode not in MODES:
        raise BondError('unknown bonding mode %r --- valid modes are: %s'
                        % (mode, ', '.join(sorted(MODES))))
    side = switch.get('lag')
    if side not in SWITCH_SIDES:
        raise BondError('unknown switch side %r --- valid values are: %s'
                        % (side, ', '.join(sorted(SWITCH_SIDES))))
    xh = server.get('xmit_hash_policy')
    if xh is not None and xh not in HASH_POLICIES:
        raise BondError('unknown xmit_hash_policy %r --- valid policies are: %s'
                        % (xh, ', '.join(sorted(HASH_POLICIES))))
    for who, d, key in (('server', server, 'mtu_ip'), ('switch', switch, 'mtu_frame')):
        v = d.get(key)
        if not isinstance(v, int) or not 68 <= v <= 65535:
            raise BondError('%s %s must be an integer byte count in range, got %r'
                            % (who, key, v))
    n = server.get('members')
    if not isinstance(n, int) or n < 1:
        raise BondError('members must be a positive integer, got %r' % (n,))
    return mode, side


def analyse(server, switch, l2_header=18):
    """l2_header: bytes the switch's frame figure includes beyond the IP payload.
    18 = 14 Ethernet header + 4 for one VLAN tag. Set it to what your platform
    actually counts; the point is that you must know, not that 18 is right."""
    mode, side = validate(server, switch)
    num, needs, note = MODES[mode]
    findings = []

    # --- aggregation agreement ------------------------------------------
    if needs == 'lacp' and side != 'lacp':
        findings.append({'severity': 'error', 'issue':
            'Server is %s (mode %d), which needs an LACP partner; the switch side is "%s".'
            % (mode, num, side),
            'outcomes': ['With no LACP partner, members may never reach the collecting and '
                         'distributing state and the bond may forward nothing.',
                         'Some configurations fall back to a single active member.',
                         'If the switch ports are independent and the bond transmits on '
                         'both, the same MAC appears on two ports and the switch will '
                         'move it back and forth.'],
            'what_to_look_at': ['actor and partner state on both sides',
                                'member collecting/distributing flags',
                                'whether a fallback or lacp-bypass option is configured']})
    elif needs == 'switch-lag' and side not in ('lacp', 'static'):
        findings.append({'severity': 'error', 'issue':
            'Server is %s (mode %d), which needs a switch-side LAG; the switch side is "%s".'
            % (mode, num, side),
            'outcomes': ['The same MAC appears on several switch ports.',
                         'The switch relearns it on whichever port last sent, and frames '
                         'to that MAC follow the last learn.'],
            'what_to_look_at': ['the switch MAC table for that address, sampled repeatedly']})
    elif needs == 'switch-lag' and side == 'lacp':
        findings.append({'severity': 'warning', 'issue':
            'Server is %s (a static mode); the switch is running LACP.' % mode,
            'outcomes': ['The switch may hold its members down waiting for LACP that the '
                         'host will never send.',
                         'If the switch falls back to individual ports, the static-mode '
                         'outcomes above apply instead.'],
            'what_to_look_at': ['switch LAG member state', 'whether LACP fallback is enabled']})
    elif needs == 'none' and side in ('lacp', 'static'):
        findings.append({'severity': 'error', 'issue':
            'Server is %s, which expects independent ports; the switch has them aggregated '
            'as "%s".' % (mode, side),
            'outcomes': ['The switch treats both ports as one link and may forward frames '
                         'to the standby member, which is not listening for them.'],
            'what_to_look_at': ['switch LAG membership', 'which member the host considers active']})
    elif needs == 'lacp' and side == 'lacp':
        findings.append({'severity': 'info', 'issue':
            'Aggregation intent agrees: %s against an LACP partner.' % mode,
            'outcomes': ['Agreement of intent is not a working bond. Confirm it on the kit.'],
            'what_to_look_at': ['actor and partner state', 'aggregator ID on both sides',
                                'that both members are collecting AND distributing']})

    # --- bandwidth expectation -------------------------------------------
    if server['members'] > 1 and mode in ('802.3ad', 'balance-xor'):
        findings.append({'severity': 'info', 'issue':
            'Per-flow hashing: a bond of %d members does not make one flow faster.'
            % server['members'],
            'outcomes': ['A single TCP flow normally rides one member and is limited to '
                         'that member\'s rate.',
                         'The host\'s transmit hash and the switch\'s hash are chosen '
                         'independently and need not match; traffic can be even in one '
                         'direction and uneven in the other.'],
            'what_to_look_at': ['per-member counters in BOTH directions, under real traffic']})

    # --- MTU, with the units made explicit --------------------------------
    host_frame = server['mtu_ip'] + l2_header
    if host_frame > switch['mtu_frame']:
        findings.append({'severity': 'error', 'issue':
            'A full-size host packet does not fit: host IP MTU %d + %d bytes of L2 header '
            '= %d, against a switch maximum frame of %d.'
            % (server['mtu_ip'], l2_header, host_frame, switch['mtu_frame']),
            'outcomes': ['Small packets pass and large ones are dropped.',
                         'The symptom reaches you as "it pings fine but transfers hang".'],
            'what_to_look_at': ['what your switch\'s figure actually counts --- payload, '
                                'frame with header, or frame including FCS',
                                'ping with the do-not-fragment bit at increasing sizes, to '
                                'find the real threshold']})
    else:
        findings.append({'severity': 'info', 'issue':
            'Size fits as configured: host IP MTU %d + %d = %d, switch frame %d.'
            % (server['mtu_ip'], l2_header, host_frame, switch['mtu_frame']),
            'outcomes': ['This arithmetic assumes %d bytes of L2 header. Confirm what your '
                         'platform counts before relying on it.' % l2_header],
            'what_to_look_at': ['the platform\'s own definition of its MTU figure']})

    worst = ('error' if any(f['severity'] == 'error' for f in findings)
             else 'warning' if any(f['severity'] == 'warning' for f in findings) else 'info')
    return {'mode': mode, 'mode_number': num, 'switch_side': side,
            'switch_requirement': needs, 'mode_note': note,
            'l2_header_bytes_assumed': l2_header,
            'findings': findings, 'worst': worst,
            'scope': ('Agreement of two INTENDED configurations. Not a running bond, not '
                      'LACP state, and not a prediction of what your kit will do.')}


def report(name, server, switch, **kw):
    print('[%s]' % name)
    try:
        r = analyse(server, switch, **kw)
    except BondError as e:
        print('    REJECTED: %s\n' % e)
        return None
    print('    server: mode=%-14s (%d) members=%d  IP MTU=%d'
          % (r['mode'], r['mode_number'], server['members'], server['mtu_ip']))
    print('    switch: side=%-14s              max frame=%d'
          % (r['switch_side'], switch['mtu_frame']))
    print('    mode needs: %s --- %s' % (r['switch_requirement'], r['mode_note']))
    for f in r['findings']:
        print('    [%-7s] %s' % (f['severity'], f['issue']))
        for o in f['outcomes']:
            print('              possible outcome: ' + o)
        for w in f['what_to_look_at']:
            print('              look at: ' + w)
    print('    worst: %s\n' % r['worst'])
    return r


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--json', action='store_true')
    a = p.parse_args(argv)
    print('Intended bond vs intended switch LAG\n')
    out = []
    out.append(report('agreed: LACP both sides, size fits',
        dict(mode='802.3ad', members=2, mtu_ip=9000, xmit_hash_policy='layer3+4'),
        dict(lag='lacp', mtu_frame=9216)))
    out.append(report('mismatch: server LACP, switch ports not aggregated',
        dict(mode='802.3ad', members=2, mtu_ip=1500),
        dict(lag='access', mtu_frame=1518)))
    out.append(report('mismatch: server static hash mode, switch running LACP',
        dict(mode='balance-xor', members=2, mtu_ip=1500),
        dict(lag='lacp', mtu_frame=1518)))
    out.append(report('mismatch: active-backup against an aggregated switch',
        dict(mode='active-backup', members=2, mtu_ip=1500),
        dict(lag='static', mtu_frame=1518)))
    out.append(report('size trap: 9000 host IP MTU against a 9000-byte switch frame',
        dict(mode='802.3ad', members=2, mtu_ip=9000),
        dict(lag='lacp', mtu_frame=9000)))
    out.append(report('rejected: a mode that does not exist',
        dict(mode='lacp-active', members=2, mtu_ip=1500),
        dict(lag='lacp', mtu_frame=1518)))
    out.append(report('rejected: a switch side that does not exist',
        dict(mode='802.3ad', members=2, mtu_ip=1500),
        dict(lag='port-channel', mtu_frame=1518)))
    print('None of the above is a running bond. Agreement of intent is the cheapest')
    print('check available and the weakest: confirm actor/partner state, member')
    print('collecting and distributing flags, and per-member counters in BOTH')
    print('directions on the actual kit before you believe any of it.')
    if a.json:
        print(json.dumps([r for r in out if r], indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
