#!/usr/bin/env python3
"""Lab 53.3 --- what a blanket infrastructure ACL breaks, measured.

WHAT THIS RUNS
--------------
Three Linux network namespaces, a real forwarding hop with a smaller MTU, real
nftables rules and real packets. Nothing is modelled.

    router ns ---- 10.0.4.0/30 ---- mid ns ---- 203.0.113.0/30 ---- far ns
    loopback 10.53.0.1/32           forwards        MTU 1400

The router's INFRASTRUCTURE SPACE is 10.53.0.0/24 (loopbacks) and 10.0.4.0/22
(link addresses). Chapter 53 §4 says: at the edge, deny any packet from outside
whose destination is infrastructure space. This lab applies exactly that rule,
and then applies the same rule with the exceptions a working network needs, and
measures three things against both.

THE THREE PROBES
----------------
  authorised peer -> tcp/179 on the link address
      A real external BGP session terminates ON an infrastructure address.
      Here only generic TCP/179 reachability is tested, not BGP. This is
      the traffic the blanket rule was never meant to catch.

  unauthorised source -> tcp/179 on the link address
      Must be refused under both postures. If it is not, the filter is not
      doing its job and nothing else in the run means anything.

  ICMP fragmentation-needed -> the loopback
      The router itself has a TCP or UDP session sourced from its loopback
      crossing a smaller-MTU path. Path MTU discovery depends on an ICMP
      type 3 code 4 coming BACK to that loopback --- an infrastructure
      destination, from outside. Drop it and the session black-holes silently:
      no error, no log, just large packets vanishing.

      The lab reads the kernel's own route cache to decide. If the ICMP
      arrived, the cache carries "mtu 1400". If it did not, there is no mtu in
      the cache and the router will keep sending packets too big to deliver.

WHY THIS LAB EXISTS
-------------------
Chapter 53 §4 said an attacker who cannot address your control plane "cannot
attack it directly at all, whatever cleverness they had planned". The filter
that achieves that also severs every external routing session that terminates
on an infrastructure address, and blinds path MTU discovery for the router's own
traffic. The rule is right; the one-line version of it is an outage. What makes
it deployable is the exception list, and the exception list is the part the
chapter did not show.

    sudo python3 iacl_exceptions.py
    sudo python3 iacl_exceptions.py --json
    sudo python3 test_iacl_exceptions.py

Requires root, iproute2 and nftables. It refuses to run without them rather
than printing a simulated result.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

PREFIX = 'rtn53i'
RTR, MID, FAR = PREFIX + 'r', PREFIX + 'm', PREFIX + 'f'
NAMESPACES = (RTR, MID, FAR)

LOOPBACK = '10.53.0.1'
LINK_ADDR = '10.0.4.1'
PEER = '10.0.4.2'
OUTSIDER = '198.51.100.7'
FAR_ADDR = '203.0.113.2'
SMALL_MTU = 1400
BGP_PORT = 179
PMTU_PORT = 9054
INFRA = ('10.53.0.0/24', '10.0.4.0/22')

ALLOWED, BLOCKED = 'allowed', 'blocked'
LEARNED, BLACKHOLE = 'PMTU learned', 'silent black hole'


class LabError(RuntimeError):
    """The lab cannot run, or its own measurement is not trustworthy."""


def _run(argv, check=True, ns=None):
    if ns:
        argv = ['ip', 'netns', 'exec', ns] + list(argv)
    proc = subprocess.run(argv, capture_output=True, text=True,
                          stdin=subprocess.DEVNULL)
    if check and proc.returncode != 0:
        raise LabError('%s failed (%d): %s'
                       % (' '.join(argv), proc.returncode,
                          (proc.stderr or proc.stdout).strip()))
    return proc.stdout


def preflight():
    missing = [t for t in ('ip', 'nft') if not shutil.which(t)]
    if missing:
        raise LabError('this lab builds real network namespaces and needs %s '
                       'on PATH. It will not simulate the result.'
                       % ' and '.join(missing))
    if os.geteuid() != 0:
        raise LabError('this lab creates network namespaces and needs root. '
                       'Re-run with sudo. It will not simulate the result.')
    _run(['ip', 'netns', 'list'])


def teardown():
    for ns in NAMESPACES:
        subprocess.run(['ip', 'netns', 'del', ns], capture_output=True,
                       stdin=subprocess.DEVNULL)


def build():
    teardown()
    for ns in NAMESPACES:
        _run(['ip', 'netns', 'add', ns])
    _run(['ip', 'link', 'add', 'rm', 'type', 'veth', 'peer', 'name', 'mr'])
    _run(['ip', 'link', 'add', 'ms', 'type', 'veth', 'peer', 'name', 'fm'])
    for link, ns in (('rm', RTR), ('mr', MID), ('ms', MID), ('fm', FAR)):
        _run(['ip', 'link', 'set', link, 'netns', ns])

    _run(['ip', '-n', RTR, 'addr', 'add', LINK_ADDR + '/30', 'dev', 'rm'])
    _run(['ip', '-n', RTR, 'addr', 'add', LOOPBACK + '/32', 'dev', 'lo'])
    _run(['ip', '-n', RTR, 'link', 'set', 'rm', 'up'])
    _run(['ip', '-n', RTR, 'link', 'set', 'lo', 'up'])
    # The router reaches the far side through the narrow hop, sourced from its
    # own loopback: an infrastructure address, which is the whole point.
    _run(['ip', '-n', RTR, 'route', 'add', '203.0.113.0/30', 'via', PEER,
          'src', LOOPBACK])
    _run(['ip', '-n', RTR, 'route', 'add', OUTSIDER + '/32', 'via', PEER])

    _run(['ip', '-n', MID, 'addr', 'add', PEER + '/30', 'dev', 'mr'])
    _run(['ip', '-n', MID, 'addr', 'add', OUTSIDER + '/32', 'dev', 'mr'])
    _run(['ip', '-n', MID, 'link', 'set', 'mr', 'up'])
    _run(['ip', '-n', MID, 'addr', 'add', '203.0.113.1/30', 'dev', 'ms'])
    _run(['ip', '-n', MID, 'link', 'set', 'ms', 'up', 'mtu', str(SMALL_MTU)])
    _run(['sysctl', '-qw', 'net.ipv4.ip_forward=1'], ns=MID)
    _run(['ip', '-n', MID, 'route', 'add', LOOPBACK + '/32', 'via', LINK_ADDR])

    _run(['ip', '-n', FAR, 'addr', 'add', FAR_ADDR + '/30', 'dev', 'fm'])
    _run(['ip', '-n', FAR, 'link', 'set', 'fm', 'up', 'mtu', str(SMALL_MTU)])
    _run(['ip', '-n', FAR, 'route', 'add', 'default', 'via', '203.0.113.1'])

    got = _run(['ip', '-n', MID, 'link', 'show', 'ms'])
    if 'mtu %d' % SMALL_MTU not in got:
        raise LabError('the narrow hop is not at MTU %d, so there is no path '
                       'MTU to discover and the PMTUD probe would be '
                       'meaningless' % SMALL_MTU)


# --------------------------------------------------------------------------
# The two filters
# --------------------------------------------------------------------------

_BLANKET = '''table ip rtn53iacl {
  chain edge {
    type filter hook prerouting priority -150; policy accept;
    iif "rm" ip daddr { %s } counter drop
  }
}
''' % ', '.join(INFRA)

_WITH_EXCEPTIONS = '''table ip rtn53iacl {
  chain edge {
    type filter hook prerouting priority -150; policy accept;
    iif "rm" icmp type destination-unreachable icmp code frag-needed counter accept
    iif "rm" icmp type time-exceeded counter accept
    iif "rm" ip saddr %s ip daddr %s tcp dport %d counter accept
    iif "rm" ip daddr { %s } counter drop
  }
}
''' % (PEER, LINK_ADDR, BGP_PORT, ', '.join(INFRA))

POSTURES = (
    ('blanket deny to infrastructure',
     'the chapter\'s one-line rule, exactly as written', _BLANKET, 1),
    ('deny with the required exceptions',
     'the same rule after the authorised peer and the ICMP a network needs',
     _WITH_EXCEPTIONS, 4),
)


def apply_filter(ruleset, expected_rules):
    """Load a ruleset and CHECK it is live. A filter that silently failed to
    load would make every probe below look permitted."""
    subprocess.run(['ip', 'netns', 'exec', RTR, 'nft', 'delete', 'table', 'ip',
                    'rtn53iacl'], capture_output=True, stdin=subprocess.DEVNULL)
    proc = subprocess.run(['ip', 'netns', 'exec', RTR, 'nft', '-f', '-'],
                          input=ruleset, capture_output=True, text=True)
    if proc.returncode != 0:
        raise LabError('the filter would not load, so every probe would have '
                       'run against an OPEN router and reported success: %s'
                       % proc.stderr.strip())
    live = _run(['nft', 'list', 'table', 'ip', 'rtn53iacl'], ns=RTR)
    rules = [ln for ln in live.splitlines() if 'counter' in ln]
    if len(rules) != expected_rules:
        raise LabError('expected %d rules in the live ruleset, found %d. The '
                       'measurement below would not be of the filter this lab '
                       'thinks it applied.' % (expected_rules, len(rules)))
    return rules


# --------------------------------------------------------------------------
# The three probes
# --------------------------------------------------------------------------

_LISTENER = r'''
import socket, sys
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((%r, %d)); s.listen(4); s.settimeout(3.0)
sys.stderr.write("ready\n"); sys.stderr.flush()
try:
    c, a = s.accept(); print("ACCEPTED " + a[0]); c.close()
except socket.timeout:
    print("NONE")
''' % (LINK_ADDR, BGP_PORT)

_CONNECT = r'''
import socket, sys
s = socket.socket(); s.settimeout(2.0); s.bind((sys.argv[1], 0))
try:
    s.connect((%r, %d)); print("ESTABLISHED")
except Exception as exc:
    print("FAILED " + type(exc).__name__)
''' % (LINK_ADDR, BGP_PORT)

_BIG_DATAGRAM = r'''
import socket
IP_MTU_DISCOVER, IP_PMTUDISC_DO = 10, 2
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.IPPROTO_IP, IP_MTU_DISCOVER, IP_PMTUDISC_DO)
s.bind((%r, 0))
try:
    print("sent %%d" %% s.sendto(b"A" * 1400, (%r, %d)))
except OSError as exc:
    print("refused " + str(exc))
''' % (LOOPBACK, FAR_ADDR, PMTU_PORT)


def probe_bgp(source):
    """Open a TCP socket on port 179; no BGP OPEN, KEEPALIVE or daemon is used."""
    listener = subprocess.Popen(
        ['ip', 'netns', 'exec', RTR, 'python3', '-c', _LISTENER],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        stdin=subprocess.DEVNULL)
    if listener.stderr.readline().strip() != 'ready':
        listener.kill()
        raise LabError('the listener did not start; no probe can be read')
    time.sleep(0.15)
    client = _run(['ip', 'netns', 'exec', MID, 'python3', '-c', _CONNECT,
                   source]).strip()
    server, _ = listener.communicate(timeout=8)
    server = server.strip()
    established = client == 'ESTABLISHED'
    accepted = server.startswith('ACCEPTED')
    if established != accepted:
        raise LabError('the two ends disagree: client says %r, router says %r'
                       % (client, server))
    return {'source': source, 'client': client, 'router': server,
            'outcome': ALLOWED if established else BLOCKED}


def probe_pmtud():
    """Send one oversized datagram from the loopback and see whether the ICMP
    that comes back is allowed to teach the kernel the path MTU."""
    _run(['ip', '-n', RTR, 'route', 'flush', 'cache'])
    sent = _run(['ip', 'netns', 'exec', RTR, 'python3', '-c',
                 _BIG_DATAGRAM]).strip()
    if not sent.startswith('sent'):
        raise LabError('the oversized datagram was not sent (%s); the PMTUD '
                       'probe cannot be read' % sent)
    time.sleep(0.5)
    cache = _run(['ip', '-n', RTR, 'route', 'get', FAR_ADDR, 'from', LOOPBACK])
    learned = 'mtu %d' % SMALL_MTU in cache
    return {'sent': sent, 'route_cache': ' '.join(cache.split()),
            'outcome': LEARNED if learned else BLACKHOLE}


PROBES = (
    ('authorised peer -> tcp/%d on link address' % BGP_PORT, ALLOWED),
    ('unauthorised source -> tcp/%d' % BGP_PORT, BLOCKED),
    ('ICMP frag-needed -> loopback (PMTUD)', LEARNED),
)


def measure():
    results = []
    for name, description, ruleset, expected_rules in POSTURES:
        rules = apply_filter(ruleset, expected_rules)
        peer = probe_bgp(PEER)
        outsider = probe_bgp(OUTSIDER)
        pmtud = probe_pmtud()
        row = {'posture': name, 'description': description,
               'live_rules': len(rules),
               'probes': [
                   dict(peer, label=PROBES[0][0], expected=PROBES[0][1]),
                   dict(outsider, label=PROBES[1][0], expected=PROBES[1][1]),
                   dict(pmtud, label=PROBES[2][0], expected=PROBES[2][1]),
               ]}
        for p in row['probes']:
            p['correct'] = p['outcome'] == p['expected']
        results.append(row)
        # The filter must at least block the outsider, under every posture. If
        # it does not, nothing else in this run is evidence of anything.
        if outsider['outcome'] != BLOCKED:
            raise LabError(
                'under %r the unauthorised source reached tcp/%d on an '
                'infrastructure address. The filter is not in force, so the '
                'other probes would be measuring an open router.'
                % (name, BGP_PORT))
    return results


# --------------------------------------------------------------------------

def report(results, stream=sys.stdout):
    w = stream.write
    w('Lab 53.3 --- an infrastructure ACL, with and without its exceptions\n')
    w('infrastructure space: %s\n\n' % ', '.join(INFRA))
    width = max(len(p[0]) for p in PROBES) + 2
    w('%-36s%s\n' % ('posture', ''.join('%-*s' % (width, p[0]) for p in PROBES)))
    w('-' * (36 + width * len(PROBES)) + '\n')
    for row in results:
        line = '%-36s' % row['posture']
        for p in row['probes']:
            line += '%-*s' % (width, p['outcome'] +
                              ('' if p['correct'] else '  <-- WRONG'))
        w(line.rstrip() + '\n')
    w('\nWanted: %s\n'
      % '; '.join('%s = %s' % (label, want) for label, want in PROBES))

    blanket, fixed = results
    wrong = [p for p in blanket['probes'] if not p['correct']]
    right = [p for p in fixed['probes'] if p['correct']]
    w('\n')
    w('The one-line rule got %d of %d probes wrong.\n'
      % (len(wrong), len(PROBES)))
    for p in wrong:
        w('  %s: %s, wanted %s\n' % (p['label'], p['outcome'], p['expected']))
    w('\nBoth of those are outages, not security. The external session simply\n'
      'does not come up; and the path MTU is never learned, so the router\n'
      'keeps sending packets the narrow hop cannot carry, with no error\n'
      'anywhere. The route cache after the blanket rule reads:\n')
    pm = next(p for p in blanket['probes'] if p['label'] == PROBES[2][0])
    w('  %s\n' % pm['route_cache'])
    pm2 = next(p for p in fixed['probes'] if p['label'] == PROBES[2][0])
    w('and after the exceptions:\n  %s\n' % pm2['route_cache'])
    w('\nWith the exceptions in place, %d of %d probes came out as wanted, and\n'
      'the unauthorised source is refused under both. The deny line did not\n'
      'get weaker --- it got the permits it always needed in front of it.\n'
      % (len(right), len(PROBES)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--keep', action='store_true',
                        help='leave the namespaces up for inspection')
    args = parser.parse_args(argv)
    try:
        preflight()
    except LabError as exc:
        sys.stderr.write('cannot run: %s\n' % exc)
        return 2
    try:
        build()
        results = measure()
    except LabError as exc:
        sys.stderr.write('lab aborted: %s\n' % exc)
        teardown()
        return 1
    try:
        if args.json:
            json.dump(results, sys.stdout, indent=2)
            sys.stdout.write('\n')
        else:
            report(results)
    finally:
        if not args.keep:
            teardown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
