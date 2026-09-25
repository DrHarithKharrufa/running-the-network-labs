#!/usr/bin/env python3
"""Lab 59.1 --- candidates from flow data, and the context they still need.

THE DEFECTS THIS REPLACES. The shipped version declared an intrusion from nine
synthetic records, and four separate things were wrong with how it did it.

  1. IT CALLED NORMAL WINDOWS ADMINISTRATION AN ATTACK. It listed
     ("workstation", 445) as forbidden and flagged ws-07 -> dc-01 on SMB as
     lateral movement. EVERY DOMAIN-JOINED WORKSTATION DOES THAT, continuously,
     to fetch group policy from SYSVOL and NETLOGON. Ship that rule and the
     first alert is every laptop in the building.
  2. IT DECIDED WHAT WAS EXTERNAL FROM THE HOSTNAME. `d.startswith(("dc","app",
     "ws"))` --- so a host called `dc.attacker.example` is internal and any
     internal host outside that naming convention is the Internet.
  3. IT READ A BIG NUMBER AS A CRIME. The largest outbound flow was printed as
     "exfil staging". A backup, a software update, a video call and a database
     replica are all larger than most attacks.
  4. IT CALLED THE FIRST RECORD THE START OF THE INCIDENT --- and `min()` over
     an unknown host raised ValueError, so asking about a host with no flows
     crashed the tool rather than answering.

This version produces CANDIDATES with the reason they are candidates and the
observation that would settle them, classifies by address against an inventory,
and states what it cannot know.

    python3 flow_hunt.py
    python3 flow_hunt.py --json
    python3 test_flow_hunt.py

Offline calculation over a synthetic flow log. It queries nothing.
"""
import ipaddress
import json
import sys

from detector_quality import DetectorError, regularity

CANDIDATE, EXPECTED, UNCLASSIFIED = 'CANDIDATE', 'EXPECTED', 'UNCLASSIFIED'


class HuntError(ValueError):
    pass


# ---------------------------------------------------------------------------
# The inventory. Classification is by ADDRESS, and roles carry an explicit
# statement of what each is expected to do --- because a rule about what should
# not happen is only as good as the record of what should.
# ---------------------------------------------------------------------------

INVENTORY = {
    '10.10.1.7':  dict(name='ws-07',  role='workstation', domain_joined=True),
    '10.10.1.9':  dict(name='ws-09',  role='workstation', domain_joined=True),
    '10.20.0.1':  dict(name='dc-01',  role='domain-controller', domain_joined=True),
    '10.20.0.5':  dict(name='app-01', role='application', domain_joined=True),
    '10.20.0.9':  dict(name='bkp-01', role='backup', domain_joined=True),
}
INTERNAL_RANGES = [ipaddress.ip_network('10.0.0.0/8')]

# What each role legitimately initiates, stated once, with the reason. This is
# the artefact the old lab lacked: without it, "should not happen" is a guess.
EXPECTED_SERVICES = {
    ('workstation', 'domain-controller', 445):
        'SMB to SYSVOL and NETLOGON: how a domain-joined machine fetches group '
        'policy. Present on every workstation, continuously',
    ('workstation', 'domain-controller', 88):
        'Kerberos authentication',
    ('workstation', 'domain-controller', 389):
        'LDAP directory lookups',
    ('workstation', 'application', 443):
        'the line-of-business application',
    ('backup', 'application', 445):
        'the nightly backup agent reading application data',
    ('application', 'domain-controller', 389):
        'service account authentication',
}


def classify(addr):
    if addr in INVENTORY:
        return dict(known=True, internal=True, **INVENTORY[addr])
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        raise HuntError('%r is not an IP address. This model classifies by '
                        'address, not by name: the version it replaces decided '
                        'what was external from a hostname prefix' % addr)
    internal = any(ip in n for n in INTERNAL_RANGES)
    return dict(known=False, internal=internal, name=addr,
                role='unknown-internal' if internal else 'external',
                domain_joined=False)


# ---------------------------------------------------------------------------
# Flows
# ---------------------------------------------------------------------------

FLOWS = [
    # ws-07 to an external host every ~60s with a little jitter, small bytes
    (0,    '10.10.1.7', '203.0.113.9', 443, 800),
    (62,   '10.10.1.7', '203.0.113.9', 443, 810),
    (119,  '10.10.1.7', '203.0.113.9', 443, 790),
    (181,  '10.10.1.7', '203.0.113.9', 443, 805),
    (238,  '10.10.1.7', '203.0.113.9', 443, 795),
    (301,  '10.10.1.7', '203.0.113.9', 443, 800),
    # ordinary browsing: irregular and large
    (5,    '10.10.1.7', '93.184.216.34', 443, 240000),
    (48,   '10.10.1.7', '93.184.216.34', 443, 510000),
    # group policy: every workstation does this, all day
    (200,  '10.10.1.7', '10.20.0.1', 445, 40000),
    (260,  '10.10.1.9', '10.20.0.1', 445, 38000),
    # an RDP session from a workstation to a DC: NOT in the expected list
    (205,  '10.10.1.7', '10.20.0.1', 3389, 90000),
    # workstation to workstation on SMB: not expected either
    (210,  '10.10.1.7', '10.10.1.9', 445, 12000),
    # the nightly backup, which is expected and is the largest flow in the log
    (400,  '10.20.0.9', '10.20.0.5', 445, 4200000000),
    # a large outbound transfer
    (240,  '10.10.1.7', '203.0.113.9', 443, 900000000),
    # a host not in the inventory at all
    (300,  '10.10.9.99', '10.20.0.1', 445, 15000),
]

WINDOW = (0, 600)


def periodic_candidates(flows, max_bytes=5000, cv_threshold=0.15, min_events=4):
    """Regular small conversations to an external address.

    Reports the coefficient of variation rather than a yes/no, because lab 59.3
    measures what that number costs: a threshold loose enough to catch a
    jittered beacon also catches scheduled jobs.
    """
    by_pair = {}
    for t, s, d, port, b in flows:
        if classify(d)['internal'] or b > max_bytes:
            continue
        by_pair.setdefault((s, d, port), []).append(t)
    out = []
    for (s, d, port), times in sorted(by_pair.items()):
        if len(times) < min_events:
            continue
        try:
            r = regularity(times)
        except DetectorError as exc:
            out.append(dict(src=s, dst=d, port=port, verdict=UNCLASSIFIED,
                            why=str(exc)))
            continue
        out.append(dict(
            src=s, dst=d, port=port, events=len(times), mean_gap=r['mean_gap'],
            cv=r['cv'], verdict=CANDIDATE if r['cv'] <= cv_threshold else 'BELOW THRESHOLD',
            why=('%d small conversations to an external address at a mean gap of '
                 '%.0f s, CV %.3f' % (len(times), r['mean_gap'], r['cv'])),
            needed=('Is this a known scheduled client --- update check, telemetry, '
                    'certificate status? Resolve the destination and check the '
                    'process on the host. A CV this low is also produced by the '
                    'software you bought.')))
    return out


def unexpected_internal(flows):
    """Internal conversations not covered by the expected-service list."""
    out = []
    for t, s, d, port, b in flows:
        cs, cd = classify(s), classify(d)
        if not (cs['internal'] and cd['internal']):
            continue
        if not cs['known'] or not cd['known']:
            out.append(dict(t=t, src=s, dst=d, port=port, bytes=b,
                            verdict=UNCLASSIFIED,
                            why='%s is not in the inventory, so there is no '
                                'statement of what it should do'
                                % (s if not cs['known'] else d),
                            needed='Identify the asset before judging the traffic. '
                                   'An unknown host is an inventory finding first.'))
            continue
        key = (cs['role'], cd['role'], port)
        if key in EXPECTED_SERVICES:
            out.append(dict(t=t, src=s, dst=d, port=port, bytes=b, verdict=EXPECTED,
                            why=EXPECTED_SERVICES[key], needed=None))
        else:
            out.append(dict(
                t=t, src=s, dst=d, port=port, bytes=b, verdict=CANDIDATE,
                why='%s (%s) to %s (%s) on %d is not in the expected-service list'
                    % (cs['name'], cs['role'], cd['name'], cd['role'], port),
                needed=('Was this an authorised administrator doing authorised '
                        'work? Correlate the authentication logs for who held '
                        'the session, and check whether this pair has a history. '
                        'Absence from the list means nobody wrote it down, which '
                        'is not the same as nobody should do it.')))
    return out


def scope(flows, host, window=WINDOW):
    """What the flow log shows about a host, with its own limits attached."""
    if window[1] <= window[0]:
        raise HuntError('the observation window must have positive length')
    mine = [f for f in flows if f[1] == host or f[2] == host]
    if not mine:
        return dict(host=host, in_inventory=host in INVENTORY, flows=0,
                    peers=[], first_observed=None, largest_flow_bytes=None,
                    why='No flows for this host in the log. That is not evidence '
                        'the host was quiet: it may be outside the export '
                        'coverage, below the sampling rate, or named differently '
                        '(lab 59.2).')
    peers = sorted({d for _, s, d, _, _ in mine if s == host}
                   | {s for _, s, d, _, _ in mine if d == host})
    first = min(t for t, _, _, _, _ in mine)
    largest = max((b for _, s, _, _, b in mine if s == host), default=None)
    return dict(
        host=host, in_inventory=host in INVENTORY, flows=len(mine), peers=peers,
        first_observed=first, window=window,
        at_window_edge=(first <= window[0]),
        largest_flow_bytes=largest,
        limits=[
            ('first_observed is the first record IN THIS WINDOW, not the start of '
             'anything. The window opens at t=%d, and this host\'s first record is '
             'at t=%d%s.'
             % (window[0], first,
                ' --- which is the edge of the window, so activity before it is '
                'simply not in view' if first <= window[0] else '')),
            ('largest_flow_bytes is the largest flow observed. A backup, a software '
             'update, a video call and a database replica are all larger than most '
             'exfiltration. Size ranks flows; it does not classify them.'),
            ('peers are the peers VISIBLE HERE. Traffic that never crossed an '
             'exporter is absent by construction, not by innocence.'),
        ])


def _w(t, i, width=78):
    words, lines, cur = t.split(), [], ''
    for x in words:
        if len(cur) + len(x) + 1 > width - i:
            lines.append(cur); cur = x
        else:
            cur = (cur + ' ' + x).strip()
    lines.append(cur)
    return ('\n' + ' ' * i).join(lines)


def report(out=None):
    out = sys.stdout if out is None else out
    out.write('Lab 59.1 --- candidates from flow data, and what they still need\n')
    out.write('=' * 74 + '\n\n')
    out.write('REGULAR SMALL CONVERSATIONS TO EXTERNAL ADDRESSES\n\n')
    for c in periodic_candidates(FLOWS):
        out.write('  %-12s %s -> %s:%d\n' % (c['verdict'], c['src'], c['dst'], c['port']))
        out.write('      %s\n' % _w(c['why'], 6))
        if c.get('needed'):
            out.write('      still needed: %s\n' % _w(c['needed'], 20))
    out.write('\nINTERNAL CONVERSATIONS AGAINST THE EXPECTED-SERVICE LIST\n\n')
    for c in unexpected_internal(FLOWS):
        out.write('  %-12s t=%-4d %s -> %s:%d\n'
                  % (c['verdict'], c['t'], classify(c['src'])['name'],
                     classify(c['dst'])['name'], c['port']))
        out.write('      %s\n' % _w(c['why'], 6))
        if c.get('needed'):
            out.write('      still needed: %s\n' % _w(c['needed'], 20))
    out.write('\n  Note the two SMB flows to the domain controller. The version of\n')
    out.write('  this lab that shipped called them lateral movement. They are how\n')
    out.write('  a domain-joined machine fetches group policy, and every\n')
    out.write('  workstation does it all day.\n\n')
    out.write('SCOPING A HOST\n\n')
    for host in ('10.10.1.7', '10.10.4.4'):
        s = scope(FLOWS, host)
        out.write('  %s (%s)\n' % (host, 'in inventory' if s['in_inventory']
                                   else 'NOT in inventory'))
        if not s['flows']:
            out.write('    %s\n' % _w(s['why'], 4))
            continue
        out.write('    flows %d   peers %s\n' % (s['flows'], ', '.join(s['peers'])))
        out.write('    first observed t=%s   largest flow %.0f MB\n'
                  % (s['first_observed'], s['largest_flow_bytes'] / 1e6))
        for lim in s['limits']:
            out.write('    - %s\n' % _w(lim, 6))
    out.write('\nNothing above is a confirmed intrusion. Every line is a candidate\n')
    out.write('with the observation that would settle it, and two of the lines are\n')
    out.write('there to show what a correct list of expected services keeps OUT.\n')


def main(argv):
    if '--json' in argv:
        print(json.dumps({
            'periodic': periodic_candidates(FLOWS),
            'internal': unexpected_internal(FLOWS),
            'scope': {h: scope(FLOWS, h) for h in ('10.10.1.7', '10.10.4.4')},
        }, indent=1))
        return 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
