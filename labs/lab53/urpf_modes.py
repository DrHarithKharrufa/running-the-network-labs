#!/usr/bin/env python3
"""Lab 53.2 --- uRPF strict, loose and a prefix filter, measured on real kernels.

WHAT THIS RUNS
--------------
Four Linux network namespaces joined by veth pairs, a real forwarding router in
the middle, and real UDP datagrams. Nothing here is modelled: `rp_filter` is the
kernel's own reverse-path check, mode 1 is RFC 3704 strict and mode 2 is RFC 3704
loose, and the datagrams either arrive at the far namespace or they do not.

    customer ns ---- link A (ra) ----\\
        |                             router ns ---- transit ---- server ns
        \\-------- link B (rb) -------/

The customer is allocated 10.20.0.0/24 and the router's best route to it points
out LINK A. The customer also has LINK B, and sends some traffic in on it: a
multihomed or asymmetric edge, which is the ordinary case the chapter's table
waves at.

WHAT IT MEASURES
----------------
Four traffic classes, against four postures:

  legitimate symmetric      10.20.0.5 arriving on link A   (must always pass)
  legitimate ASYMMETRIC     10.20.0.5 arriving on link B   (must pass; it is
                                                            the customer's own
                                                            allocated address)
  SPOOFED but routed        10.99.0.5 arriving on link B   (must be dropped; the
                                                            customer does not own
                                                            it, but the router has
                                                            a route for it)
  unrouted source           10.77.0.5 arriving on link B   (must be dropped)

WHY THIS LAB EXISTS
-------------------
Chapter 53 §5 said loose uRPF "still kills obviously spoofed sources". It does
not kill a spoofed source that has a route, and on the Internet almost every
address has a route. Loose uRPF answers "is this source reachable?" --- and
REACHABILITY IS NOT AUTHORISATION. The only posture in the matrix below that
gets all four classes right is the one that states which prefixes the customer
is allowed to use (RFC 8704 §4, and the per-customer filter operators actually
deploy).

HONESTY ABOUT THE MEASUREMENT
-----------------------------
A test that reports "dropped" when the packet was never sent is worthless, and
worse than worthless because it looks like a pass. So two guards:

  Every trial counts arrivals at the ROUTER's ingress with an nftables counter
  placed before the routing decision. "Did not reach the server" is therefore
  distinguished from "never left the customer".

  The no-validation posture is run FIRST and all four classes must be
  delivered. If they are not, the topology is broken and the script aborts
  rather than reporting the breakage as filtering.

    sudo python3 urpf_modes.py
    sudo python3 urpf_modes.py --json
    sudo python3 test_urpf_modes.py

Requires root and iproute2 and nftables, because it builds real namespaces. It
refuses to run without them rather than printing a simulated result.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

PREFIX = 'rtn53u'
CUST, RTR, SRV = PREFIX + 'c', PREFIX + 'r', PREFIX + 's'
NAMESPACES = (CUST, RTR, SRV)

CUSTOMER_PREFIX = '10.20.0.0/24'
LEGIT = '10.20.0.5'          # inside the customer's allocation
SPOOF_ROUTED = '10.99.0.5'   # not the customer's; the router has a route
SPOOF_UNROUTED = '10.77.0.5'  # not the customer's; no route anywhere
SERVER = '10.0.2.2'
PORT = 9053
PROBES = 3

PASS, DROP = 'delivered', 'dropped'


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
        raise LabError(
            'this lab builds real network namespaces and needs %s on PATH. It '
            'will not simulate the result.' % ' and '.join(missing))
    if os.geteuid() != 0:
        raise LabError(
            'this lab creates network namespaces and needs root. Re-run with '
            'sudo. It will not simulate the result.')
    _run(['ip', 'netns', 'list'])


def teardown():
    for ns in NAMESPACES:
        subprocess.run(['ip', 'netns', 'del', ns], capture_output=True,
                       stdin=subprocess.DEVNULL)


def build():
    """Create the topology. Raises LabError if anything does not come up."""
    teardown()
    for ns in NAMESPACES:
        _run(['ip', 'netns', 'add', ns])
    for a, b in (('ca', 'ra'), ('cb', 'rb'), ('st', 'rt')):
        _run(['ip', 'link', 'add', a, 'type', 'veth', 'peer', 'name', b])
    for link, ns in (('ca', CUST), ('cb', CUST), ('ra', RTR), ('rb', RTR),
                     ('rt', RTR), ('st', SRV)):
        _run(['ip', 'link', 'set', link, 'netns', ns])

    # Customer: two links to the same provider, and three source addresses.
    _run(['ip', '-n', CUST, 'addr', 'add', '10.0.1.2/30', 'dev', 'ca'])
    _run(['ip', '-n', CUST, 'addr', 'add', '10.0.3.2/30', 'dev', 'cb'])
    for addr in (LEGIT, SPOOF_ROUTED, SPOOF_UNROUTED):
        _run(['ip', '-n', CUST, 'addr', 'add', addr + '/32', 'dev', 'lo'])
    for link in ('ca', 'cb', 'lo'):
        _run(['ip', '-n', CUST, 'link', 'set', link, 'up'])

    # Router: two customer links and a transit link.
    for addr, link in (('10.0.1.1/30', 'ra'), ('10.0.3.1/30', 'rb'),
                       ('10.0.2.1/30', 'rt')):
        _run(['ip', '-n', RTR, 'addr', 'add', addr, 'dev', link])
        _run(['ip', '-n', RTR, 'link', 'set', link, 'up'])
    _run(['ip', '-n', RTR, 'link', 'set', 'lo', 'up'])
    _run(['sysctl', '-qw', 'net.ipv4.ip_forward=1'], ns=RTR)
    # The customer's allocated prefix is reached over LINK A. This is what
    # makes link B the asymmetric one, and it is the only thing strict uRPF
    # consults.
    _run(['ip', '-n', RTR, 'route', 'add', CUSTOMER_PREFIX,
          'via', '10.0.1.2', 'dev', 'ra'])
    # Somebody else's address, routed out of transit. Loose uRPF accepts it
    # from anywhere precisely because this route exists.
    _run(['ip', '-n', RTR, 'route', 'add', '10.99.0.0/24',
          'via', '10.0.2.2', 'dev', 'rt'])

    _run(['ip', '-n', SRV, 'addr', 'add', SERVER + '/30', 'dev', 'st'])
    _run(['ip', '-n', SRV, 'link', 'set', 'st', 'up'])
    _run(['ip', '-n', SRV, 'route', 'add', 'default', 'via', '10.0.2.1'])

    # Ingress counters, before the routing decision, so a packet rp_filter is
    # about to discard is still counted as having arrived.
    ruleset = '''table ip rtn53count {
  chain ingress {
    type filter hook prerouting priority -300; policy accept;
    iif "ra" udp dport %d counter comment "link-a"
    iif "rb" udp dport %d counter comment "link-b"
  }
}
''' % (PORT, PORT)
    proc = subprocess.run(['ip', 'netns', 'exec', RTR, 'nft', '-f', '-'],
                          input=ruleset, capture_output=True, text=True)
    if proc.returncode != 0:
        raise LabError('the ingress counters would not load, so no result from '
                       'this lab could be trusted: %s' % proc.stderr.strip())
    _verify_counters_present()


def _counters():
    """Return {'link-a': n, 'link-b': n} read out of the live ruleset.

    A missing table returns {} rather than raising here, so the caller can say
    WHY an empty read is fatal instead of surfacing an nft error.
    """
    out = _run(['nft', 'list', 'table', 'ip', 'rtn53count'], ns=RTR, check=False)
    found = {}
    for line in out.splitlines():
        m = re.search(r'counter packets (\d+) .*comment "([a-z-]+)"', line)
        if m:
            found[m.group(2)] = int(m.group(1))
    return found


def _verify_counters_present():
    found = _counters()
    if set(found) != {'link-a', 'link-b'}:
        raise LabError('expected ingress counters for link-a and link-b, found '
                       '%r. Without them a non-delivery cannot be told from a '
                       'packet that never left.' % sorted(found))


# --------------------------------------------------------------------------
# Postures
# --------------------------------------------------------------------------

POSTURES = (
    ('no validation', 'rp_filter=0 on both customer links, no filter'),
    ('uRPF strict', 'rp_filter=1 --- RFC 3704 strict, against the BEST route'),
    ('uRPF loose', 'rp_filter=2 --- RFC 3704 loose, any route will do'),
    ('per-customer prefix filter',
     'rp_filter=0; nftables permits only %s as a source on the customer links'
     % CUSTOMER_PREFIX),
)


def _clear_prefix_filter():
    subprocess.run(['ip', 'netns', 'exec', RTR, 'nft', 'delete', 'table',
                    'ip', 'rtn53sav'], capture_output=True,
                   stdin=subprocess.DEVNULL)


def apply_posture(name):
    _clear_prefix_filter()
    mode = {'no validation': '0', 'uRPF strict': '1', 'uRPF loose': '2',
            'per-customer prefix filter': '0'}[name]
    for link in ('ra', 'rb'):
        _run(['sysctl', '-qw', 'net.ipv4.conf.%s.rp_filter=%s' % (link, mode)],
             ns=RTR)
    _run(['sysctl', '-qw', 'net.ipv4.conf.all.rp_filter=0'], ns=RTR)
    if name == 'per-customer prefix filter':
        ruleset = '''table ip rtn53sav {
  chain sav {
    type filter hook prerouting priority -100; policy accept;
    iif { "ra", "rb" } ip saddr != %s counter drop
  }
}
''' % CUSTOMER_PREFIX
        proc = subprocess.run(['ip', 'netns', 'exec', RTR, 'nft', '-f', '-'],
                              input=ruleset, capture_output=True, text=True)
        if proc.returncode != 0:
            raise LabError('the prefix filter would not load, so this posture '
                           'would have been measured with NO filter in place '
                           'and every class would have looked delivered: %s'
                           % proc.stderr.strip())
        if 'rtn53sav' not in _run(['nft', 'list', 'tables'], ns=RTR):
            raise LabError('the prefix filter loaded without error but is not '
                           'in the live ruleset')
    # Verify what we actually set, rather than trusting that we set it.
    effective = {}
    for link in ('ra', 'rb'):
        out = _run(['sysctl', '-n', 'net.ipv4.conf.%s.rp_filter' % link], ns=RTR)
        effective[link] = out.strip()
    if set(effective.values()) != {mode}:
        raise LabError('asked for rp_filter=%s, kernel reports %r'
                       % (mode, effective))
    return effective


# --------------------------------------------------------------------------
# Traffic
# --------------------------------------------------------------------------

CLASSES = (
    ('legitimate symmetric', LEGIT, 'ca', '10.0.1.1', PASS),
    ('legitimate ASYMMETRIC', LEGIT, 'cb', '10.0.3.1', PASS),
    ('SPOOFED but routed', SPOOF_ROUTED, 'cb', '10.0.3.1', DROP),
    ('unrouted source', SPOOF_UNROUTED, 'cb', '10.0.3.1', DROP),
)

_RECEIVER = r'''
import socket, sys, time
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((%r, %d))
s.settimeout(0.6)
sys.stderr.write("ready\n"); sys.stderr.flush()
seen = []
end = time.time() + 2.0
while time.time() < end:
    try:
        _, addr = s.recvfrom(256); seen.append(addr[0])
    except socket.timeout:
        if seen: break
print(",".join(seen))
''' % (SERVER, PORT)

_SENDER = r'''
import socket, sys
src, dev = sys.argv[1], sys.argv[2]
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, dev.encode() + b"\0")
s.bind((src, 0))
sent = 0
for _ in range(%d):
    sent += 1 if s.sendto(b"probe", (%r, %d)) else 0
print(sent)
''' % (PROBES, SERVER, PORT)


def trial(source, device, nexthop):
    """Send PROBES datagrams and report what arrived where."""
    # Point the customer's route to the server out of the chosen link, so the
    # datagram really does arrive on that interface.
    _run(['ip', '-n', CUST, 'route', 'replace', '10.0.2.0/30',
          'via', nexthop, 'dev', device])
    before = _counters()
    if set(before) != {'link-a', 'link-b'}:
        raise LabError('the ingress counters are not live, so a non-delivery '
                       'cannot be told from a packet that never left the '
                       'customer. Refusing to report this trial.')
    receiver = subprocess.Popen(
        ['ip', 'netns', 'exec', SRV, 'python3', '-c', _RECEIVER],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        stdin=subprocess.DEVNULL)
    if receiver.stderr.readline().strip() != 'ready':
        receiver.kill()
        raise LabError('the receiver did not start; no trial can be read')
    time.sleep(0.15)
    sent = _run(['ip', 'netns', 'exec', CUST, 'python3', '-c', _SENDER,
                 source, device]).strip()
    stdout, _ = receiver.communicate(timeout=6)
    after = _counters()
    arrived = sum(after[k] - before[k] for k in after)
    received = [a for a in stdout.strip().split(',') if a]
    return {
        'sent': int(sent), 'arrived_at_router': arrived,
        'delivered': len(received), 'sources_seen': sorted(set(received)),
    }


def measure():
    results = []
    for posture, description in POSTURES:
        effective = apply_posture(posture)
        row = {'posture': posture, 'description': description,
               'rp_filter': effective, 'classes': []}
        for label, source, device, nexthop, expected in CLASSES:
            t = trial(source, device, nexthop)
            if t['sent'] != PROBES:
                raise LabError('sent %d of %d datagrams for %r; the trial '
                               'cannot be read' % (t['sent'], PROBES, label))
            if t['arrived_at_router'] == 0:
                raise LabError(
                    'no datagram from %s reached the router at all during the '
                    '%r trial. Nothing was filtered --- the topology is broken, '
                    'and reporting this as a drop would be a fabricated result.'
                    % (source, posture))
            t.update(label=label, source=source, ingress_link=device,
                     outcome=PASS if t['delivered'] else DROP,
                     expected=expected)
            t['correct'] = (t['outcome'] == expected)
            row['classes'].append(t)
        results.append(row)
        if posture == 'no validation':
            wrong = [c['label'] for c in row['classes'] if c['outcome'] != PASS]
            if wrong:
                raise LabError(
                    'with no source validation configured, %s did not reach the '
                    'server. The control case must deliver everything or no '
                    'later drop means anything. Aborting rather than reporting '
                    'a broken topology as a working filter.'
                    % ', '.join(repr(w) for w in wrong))
    return results


# --------------------------------------------------------------------------

def report(results, stream=sys.stdout):
    w = stream.write
    w('Lab 53.2 --- source validation, measured on Linux namespaces\n')
    w('%d UDP datagrams per trial; "delivered" means they reached the far '
      'namespace.\n\n' % PROBES)
    head = '%-28s' % 'posture'
    for label, _s, _d, _n, _e in CLASSES:
        head += '%-24s' % label
    w(head.rstrip() + '\n')
    w('-' * len(head.rstrip()) + '\n')
    for row in results:
        line = '%-28s' % row['posture']
        for c in row['classes']:
            mark = '' if c['correct'] else '  <-- WRONG'
            line += '%-24s' % (c['outcome'] + mark)
        w(line.rstrip() + '\n')
    w('\nExpected, for an edge that both works and validates:\n  ')
    w('   '.join('%s = %s' % (label, expected)
                 for label, _s, _d, _n, expected in CLASSES) + '\n')

    correct = {row['posture']: sum(1 for c in row['classes'] if c['correct'])
               for row in results}
    total = len(CLASSES)
    w('\nClasses handled correctly, out of %d:\n' % total)
    for row in results:
        w('  %-28s %d\n' % (row['posture'], correct[row['posture']]))

    best = [p for p, n in correct.items() if n == total]
    strict = next(r for r in results if r['posture'] == 'uRPF strict')
    loose = next(r for r in results if r['posture'] == 'uRPF loose')
    asym = next(c for c in strict['classes']
                if c['label'] == 'legitimate ASYMMETRIC')
    spoof = next(c for c in loose['classes']
                 if c['label'] == 'SPOOFED but routed')
    w('\n')
    w('Strict uRPF %s the customer\'s own address %s when it arrived on the\n'
      'link the best route does not point at: strict mode consults the best\n'
      'route, not the set of paths that would be feasible (RFC 8704 §3).\n'
      % ('dropped' if asym['outcome'] == DROP else 'delivered', asym['source']))
    w('Loose uRPF %s %s, which the customer does not own, because the\n'
      'router has a route for it. Loose mode asks whether the source is\n'
      'reachable. Reachability is not authorisation.\n'
      % ('delivered' if spoof['outcome'] == PASS else 'dropped',
         spoof['source']))
    if best:
        w('\nOnly %s handled all %d classes correctly. It is the only posture\n'
          'that was told which prefixes the customer is entitled to use.\n'
          % (' and '.join(best), total))
    else:
        w('\nNo posture handled all %d classes correctly in this run.\n' % total)


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
