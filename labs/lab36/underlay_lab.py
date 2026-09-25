#!/usr/bin/env python3
"""Lab 36.2 --- the Anvil eBGP underlay, run for real on Linux.

WHAT THIS IS. Six Linux network namespaces (two spines, four leaves), one FRR
instance per namespace, real eBGP sessions over real veth links, and assertions
read back from BGP and from the kernel routing table. It answers questions the
chapter makes claims about, by measurement rather than assertion:

  A  With a shared spine AS and unique leaf ASNs, does a leaf accept another
     leaf's loopback WITHOUT allowas-in?  (The chapter used to say no.)
  B  With a unique ASN per spine and no multipath-relax, how many paths are
     installed?
  C  Does multipath-relax restore them?
  D  When two leaves share an ASN, what actually happens, and what does
     allowas-in change?
  E  What does an eBGP session with no route policy advertise?
  F  What happens to the installed paths when a spine fails, and when it
     comes back?

WHAT THIS IS NOT. This is Linux forwarding and the FRR control plane. It is not
Containerlab, not a commercial NOS, not an ASIC, and it measures no throughput.
A result here tells you how BGP behaves; it does not tell you how a particular
switch behaves, and it is not a convergence guarantee for any platform.

ONE ENVIRONMENT LIMIT, STATED PLAINLY. Fabric links here are numbered /31s.
BGP unnumbered forms its session over IPv6 link-local and carries IPv4 NLRI with
IPv6 next hops (RFC 8950), so it needs a kernel with IPv6 enabled. If this host
has IPv6 disabled the script says so and skips nothing else: the AS-path,
multipath and policy behaviour under test does not depend on link addressing.
Unnumbered transport does, and this script does not test it.

Requires root, iproute2 and FRR (zebra and bgpd). Run:

    sudo python3 underlay_lab.py
"""
import json
import ipaddress
import os
import pathlib
import shutil
import subprocess
import sys
import time
import uuid

RUN = pathlib.Path('/run/rtn-lab36-' + uuid.uuid4().hex[:12])
NS_PREFIX = RUN.name + '-'

def ns_name(node):
    return NS_PREFIX + node

FRR_BIN = os.environ.get('RTN_FRR_BIN', '/usr/lib/frr')

# The ASN rule, from the front-matter Anvil plan: the spine tier shares
# 4200000000, and leaf N is 4200000100 + N. The per-device alternative gives
# spine N the number 4200000000 + N. Both sit inside the 4-byte private range
# of RFC 6996, which prevents collision with PUBLIC allocations only --- every
# number here still has to be unique within the estate that uses it.
SPINE_SHARED_AS = 4200000000
SPINE_UNIQUE_AS = {'spine-01': 4200000001, 'spine-02': 4200000002}
LEAF_AS = {'leaf-01': 4200000101, 'leaf-02': 4200000102,
           'leaf-03': 4200000103, 'leaf-04': 4200000104}
LOOPBACK = {'spine-01': '10.200.0.11', 'spine-02': '10.200.0.12',
            'leaf-01': '10.200.0.21', 'leaf-02': '10.200.0.22',
            'leaf-03': '10.200.0.23', 'leaf-04': '10.200.0.24'}
SPINES = ['spine-01', 'spine-02']
LEAVES = ['leaf-01', 'leaf-02', 'leaf-03', 'leaf-04']


def link_addrs():
    """One /31 per fabric link: spine end even, leaf end odd."""
    out = {}
    base = 0
    for s in SPINES:
        for l in LEAVES:
            out[(s, l)] = ('10.200.1.%d' % base, '10.200.1.%d' % (base + 1))
            base += 2
    return out


ADDR = link_addrs()


def sh(cmd, ns=None, check=True, timeout=60):
    if ns:
        cmd = ['ip', 'netns', 'exec', ns_name(ns)] + cmd
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode:
        raise RuntimeError('%s -> rc=%d\n%s\n%s'
                           % (' '.join(cmd), r.returncode, r.stdout[-1500:], r.stderr[-1500:]))
    return r


def have_ipv6():
    return pathlib.Path('/proc/sys/net/ipv6').exists()


def frr_version():
    return sh([FRR_BIN + '/bgpd', '-v']).stdout.splitlines()[0].strip()


class Fabric:
    """Six namespaces wired as a complete bipartite graph, one FRR each."""

    def __init__(self):
        self.owned_nodes = []
        self.nodes = SPINES + LEAVES

    def up(self):
        RUN.mkdir(parents=True, exist_ok=False)
        for n in self.nodes:
            sh(['ip', 'netns', 'add', ns_name(n)])
            self.owned_nodes.append(n)
            sh(['ip', 'link', 'set', 'lo', 'up'], ns=n)
            sh(['ip', 'addr', 'add', LOOPBACK[n] + '/32', 'dev', 'lo'], ns=n)
            sh(['sysctl', '-qw', 'net.ipv4.ip_forward=1'], ns=n)
        for (s, l), (sip, lip) in ADDR.items():
            ta, tb = 'v' + os.urandom(3).hex(), 'v' + os.urandom(3).hex()
            sh(['ip', 'link', 'add', ta, 'type', 'veth', 'peer', 'name', tb])
            sh(['ip', 'link', 'set', ta, 'netns', ns_name(s), 'name', 'to-' + l])
            sh(['ip', 'link', 'set', tb, 'netns', ns_name(l), 'name', 'to-' + s])
            sh(['ip', 'addr', 'add', sip + '/31', 'dev', 'to-' + l], ns=s)
            sh(['ip', 'addr', 'add', lip + '/31', 'dev', 'to-' + s], ns=l)
            sh(['ip', 'link', 'set', 'to-' + l, 'up'], ns=s)
            sh(['ip', 'link', 'set', 'to-' + s, 'up'], ns=l)

    def start(self, node, conf):
        d = RUN / node
        d.mkdir(parents=True, exist_ok=False)
        (d / 'frr.conf').write_text(conf)
        os.chmod(d, 0o777)
        for daemon in ('zebra', 'bgpd'):
            sh(['ip', 'netns', 'exec', ns_name(node), FRR_BIN + '/' + daemon, '-d',
                '-f', str(d / 'frr.conf'), '-i', str(d / (daemon + '.pid')),
                '-z', str(d / 'zserv.api'), '--vty_socket', str(d), '-N', node])
            time.sleep(0.3)

    def vty(self, node, cmd):
        # No -N here: vtysh would then look for /etc/frr/<name>/vtysh.conf.
        out = sh(['vtysh', '--vty_socket', str(RUN / node), '-c', cmd],
                 ns=node).stdout
        if not out.strip() or any(x in out.lower() for x in ('unknown command', 'ambiguous command', 'command incomplete', '% error')):
            raise RuntimeError('Invalid CLI response: ' + repr(out))
        return out

    def vty_json(self, node, cmd):
        value = json.loads(self.vty(node, cmd))
        if not isinstance(value, dict):
            raise RuntimeError('Expected a JSON object from ' + cmd)
        return value

    def iface(self, node, ifname, state):
        sh(['ip', 'link', 'set', ifname, state], ns=node)

    def ping(self, node, src, dst, count=2):
        r = sh(['ping', '-c', str(count), '-W', '2', '-I', src, dst], ns=node, check=False)
        if r.returncode not in (0, 1):
            raise RuntimeError('Ping instrument failed: ' + r.stderr)
        return r.returncode == 0, r.stdout

    def down(self):
        for n in reversed(self.owned_nodes):
            # Enumerate only a namespace this object successfully created.
            r = sh(['ip', 'netns', 'pids', ns_name(n)], check=False)
            for pid in r.stdout.split():
                try:
                    os.kill(int(pid), 15)
                except ProcessLookupError:
                    pass
            sh(['ip', 'netns', 'del', ns_name(n)])
        self.owned_nodes.clear()
        if RUN.exists():
            shutil.rmtree(RUN)


def config(node, asn, peers, *, multipath_relax=False, allowas_in=0,
           policy=True, max_paths=8):
    """One role-shaped template. The only per-device values are the ASN, the
    router-id and the neighbour list --- and the neighbour list is derived from
    the wiring, not hand-written."""
    lines = ['hostname ' + node, '!', 'router bgp %d' % asn,
             ' bgp router-id ' + LOOPBACK[node],
             ' bgp ebgp-requires-policy',
             ' no bgp default ipv4-unicast',
             ' neighbor FABRIC peer-group',
             ' neighbor FABRIC remote-as external',
             ' neighbor FABRIC timers 1 3',
             ' neighbor FABRIC advertisement-interval 0']
    if multipath_relax:
        lines.insert(3, ' bgp bestpath as-path multipath-relax')
    lines += [' neighbor %s peer-group FABRIC' % p for p in peers]
    lines += [' !', ' address-family ipv4 unicast',
              '  maximum-paths %d' % max_paths]
    lines += ['  neighbor %s activate' % p for p in peers]
    if policy:
        lines += ['  neighbor FABRIC route-map FABRIC-IN in',
                  '  neighbor FABRIC route-map FABRIC-OUT out']
    if allowas_in:
        lines += ['  neighbor FABRIC allowas-in %d' % allowas_in]
    lines += ['  redistribute connected route-map LOOPBACKS',
              ' exit-address-family', '!',
              'ip prefix-list LOOPBACK-SPACE seq 10 permit 10.200.0.0/24 ge 32 le 32',
              '!', 'route-map LOOPBACKS permit 10', ' match interface lo', '!',
              'route-map FABRIC-IN permit 10',
              ' match ip address prefix-list LOOPBACK-SPACE', '!',
              'route-map FABRIC-OUT permit 10',
              ' match ip address prefix-list LOOPBACK-SPACE', '!']
    return '\n'.join(lines) + '\n'


def peers_of(node):
    if node in SPINES:
        return [ADDR[(node, l)][1] for l in LEAVES]
    return [ADDR[(s, node)][0] for s in SPINES]


def wait(fn, timeout=60, interval=0.4):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        v = fn()
        if v:
            return v, time.monotonic() - t0
        time.sleep(interval)
    return None, time.monotonic() - t0


# --------------------------------------------------------------------------
RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append({'check': name, 'pass': bool(ok), 'detail': str(detail)[:400]})
    print('  %s  %s%s' % ('PASS' if ok else 'FAIL', name,
                          ('  [%s]' % detail) if detail else ''))
    return bool(ok)


def bgp_paths(f, node, prefix):
    d = f.vty_json(node, 'show bgp ipv4 unicast %s json' % prefix)
    paths = d.get('paths', [])
    if not isinstance(paths, list):
        raise RuntimeError('Unrecognised BGP paths schema')
    return paths


def kernel_nexthops(f, node, prefix):
    rows = json.loads(sh(['ip', '-j', '-4', 'route', 'show', 'exact', prefix], ns=node).stdout)
    if not isinstance(rows, list):
        raise RuntimeError('Unrecognised Linux route JSON')
    out = []
    for route in rows:
        if ipaddress.ip_network(route.get('dst', '0.0.0.0/0'), strict=False) != ipaddress.ip_network(prefix, strict=False):
            continue
        for nh in route.get('nexthops', [route]):
            if nh.get('gateway') and not set(nh.get('flags', [])) & {'dead', 'linkdown'}:
                out.append({'ip': nh['gateway'], 'dev': nh.get('dev')})
    return out


def build(spine_as, *, multipath_relax=False, allowas_in=0, policy=True,
          leaf_as=None, timeout=60):
    leaf_as = leaf_as or LEAF_AS
    f = Fabric()
    try:
        f.up()
        for s in SPINES:
            f.start(s, config(s, spine_as[s] if isinstance(spine_as, dict) else spine_as,
                              peers_of(s), multipath_relax=multipath_relax,
                              allowas_in=allowas_in, policy=policy))
        for l in LEAVES:
            f.start(l, config(l, leaf_as[l], peers_of(l),
                              multipath_relax=multipath_relax,
                              allowas_in=allowas_in, policy=policy))
    except BaseException:
        f.down()
        raise
    return f


def established(f, node, expect):
    d = f.vty_json(node, 'show bgp ipv4 unicast summary json')
    if not d:
        return None
    peers = d.get('peers', {})
    up = [p for p, v in peers.items() if v.get('state') == 'Established']
    return up if set(up) == set(peers_of(node)) and len(up) == expect else None


# --------------------------------------------------------------------------
def scenario_a():
    print('\nA. Shared spine AS, unique leaf ASNs, NO allowas-in, NO multipath-relax')
    f = build(SPINE_SHARED_AS)
    try:
        up, t = wait(lambda: established(f, 'leaf-02', 2), timeout=60)
        # t is time from the first poll, which happens after every daemon has
        # been started; it is not a session-establishment measurement.
        check('A1 leaf-02 has both spine sessions Established', up is not None,
              'seen %.1fs into polling; not a convergence measurement' % t)
        paths, t = wait(lambda: bgp_paths(f, 'leaf-02', '10.200.0.21/32') or None, timeout=60)
        paths = paths or []
        check('A2 leaf-02 receives leaf-01 loopback with no allowas-in anywhere',
              len(paths) >= 1, '%d path(s) after %.1fs' % (len(paths), t))
        aspaths = sorted({p.get('aspath', {}).get('string', '') for p in paths})
        expected = '%d %d' % (SPINE_SHARED_AS, LEAF_AS['leaf-01'])
        check('A3 AS-path is "<spine AS> <origin leaf AS>", leaf-02 ASN absent',
              aspaths == [expected], aspaths)
        nh, t = wait(lambda: (kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')
                              if len(kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')) >= 2
                              else None), timeout=60)
        nh = nh or kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')
        check('A4 two ECMP next-hops installed WITHOUT multipath-relax '
              '(identical AS-paths via a shared spine AS)', len(nh) == 2,
              '%d next-hop(s): %s' % (len(nh), [n.get('ip') for n in nh]))
        ok, _out = f.ping('leaf-02', LOOPBACK['leaf-02'], LOOPBACK['leaf-01'])
        check('A5 loopback-to-loopback forwarding works', ok)
        # every leaf pair
        seen = []
        for a in LEAVES:
            for b in LEAVES:
                if a != b:
                    n = len(kernel_nexthops(f, a, LOOPBACK[b] + '/32'))
                    seen.append((a, b, n))
        check('A6 all 12 directed leaf pairs have 2 installed next-hops',
              len(seen) == 12 and all(n == 2 for _, _, n in seen),
              ', '.join('%s->%s:%d' % x for x in seen))
        cfg = f.vty('leaf-02', 'show running-config')
        check('A7 no allowas-in appears in the running configuration',
              'allowas-in' not in cfg)
    finally:
        f.down()


def scenario_bc():
    print('\nB. Unique ASN per spine, NO multipath-relax')
    f = build(SPINE_UNIQUE_AS)
    try:
        wait(lambda: established(f, 'leaf-02', 2), timeout=60)
        paths, _ = wait(lambda: (bgp_paths(f, 'leaf-02', '10.200.0.21/32') or None)
                        if len(bgp_paths(f, 'leaf-02', '10.200.0.21/32')) >= 2 else None,
                        timeout=60)
        paths = paths or bgp_paths(f, 'leaf-02', '10.200.0.21/32')
        aspaths = sorted({p.get('aspath', {}).get('string', '') for p in paths})
        check('B1 leaf-02 receives two paths with DIFFERENT AS-paths',
              len(aspaths) == 2, aspaths)
        nh = kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')
        check('B2 only ONE next-hop is installed without multipath-relax',
              len(nh) == 1, '%d next-hop(s): %s' % (len(nh), [n.get('ip') for n in nh]))
    finally:
        f.down()

    print('\nC. Unique ASN per spine, WITH multipath-relax')
    f = build(SPINE_UNIQUE_AS, multipath_relax=True)
    try:
        wait(lambda: established(f, 'leaf-02', 2), timeout=60)
        nh, t = wait(lambda: (kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')
                              if len(kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')) >= 2
                              else None), timeout=60)
        nh = nh or kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')
        check('C1 multipath-relax restores two installed next-hops',
              len(nh) == 2, '%d next-hop(s) after %.1fs' % (len(nh), t))
    finally:
        f.down()


def scenario_d():
    print('\nD. Two leaves SHARING an ASN --- where allowas-in actually belongs')
    shared = dict(LEAF_AS, **{'leaf-02': LEAF_AS['leaf-01']})
    f = build(SPINE_SHARED_AS, leaf_as=shared)
    try:
        wait(lambda: established(f, 'leaf-02', 2), timeout=60)
        time.sleep(8)
        paths = bgp_paths(f, 'leaf-02', '10.200.0.21/32')
        check('D1 leaf-02 does NOT accept leaf-01 loopback when they share an ASN',
              established(f, 'leaf-02', 2) is not None and len(paths) == 0,
              '%d path(s); sessions checked independently' % len(paths))
    finally:
        f.down()

    f = build(SPINE_SHARED_AS, leaf_as=shared, allowas_in=1)
    try:
        wait(lambda: established(f, 'leaf-02', 2), timeout=60)
        paths, t = wait(lambda: bgp_paths(f, 'leaf-02', '10.200.0.21/32') or None, timeout=60)
        paths = paths or []
        check('D2 allowas-in 1 makes the shared-leaf-ASN route acceptable',
              len(paths) >= 1, '%d path(s) after %.1fs' % (len(paths), t))
        aspaths = sorted({p.get('aspath', {}).get('string', '') for p in paths})
        check('D3 the accepted AS-path does contain leaf-02\'s own ASN',
              bool(aspaths) and all(str(shared['leaf-02']) in a.split() for a in aspaths), aspaths)
    finally:
        f.down()


def scenario_e():
    print('\nE. An eBGP session with no route policy (RFC 8212)')
    f = build(SPINE_SHARED_AS, policy=False)
    try:
        wait(lambda: established(f, 'leaf-02', 2), timeout=60)
        time.sleep(8)
        paths = bgp_paths(f, 'leaf-02', '10.200.0.21/32')
        check('E1 no prefixes cross an eBGP session with no import/export policy',
              established(f, 'leaf-02', 2) is not None and len(paths) == 0,
              '%d path(s); sessions checked independently' % len(paths))
        summary = f.vty('leaf-02', 'show bgp ipv4 unicast summary')
        # The session is up; it is policy, not a session failure, that stops the
        # prefixes. FRR prints (Policy) in the received/sent columns to say so.
        sessions_up = established(f, 'leaf-02', 2)
        check('E2 the sessions are up and the summary marks them (Policy)',
              '(Policy)' in summary and sessions_up is not None,
              'policy marker %s, sessions up %s'
              % ('(Policy)' in summary, len(sessions_up or [])))
    finally:
        f.down()


def scenario_f():
    print('\nF. Spine failure and recovery')
    f = build(SPINE_SHARED_AS)
    try:
        wait(lambda: established(f, 'leaf-02', 2), timeout=60)
        nh, _ = wait(lambda: (kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')
                              if len(kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')) >= 2
                              else None), timeout=60)
        check('F1 baseline: two next-hops', len(nh or []) == 2)
        for l in LEAVES:
            f.iface('spine-01', 'to-' + l, 'down')
        t0 = time.monotonic()
        one, t = wait(lambda: (kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')
                               if len(kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')) == 1
                               else None), timeout=60)
        check('F2 one spine lost: the route survives on one next-hop',
              one is not None, 'observed %.2fs after the link-down command' % t)
        ok, _o = f.ping('leaf-02', LOOPBACK['leaf-02'], LOOPBACK['leaf-01'])
        check('F3 forwarding continues through the surviving spine', ok)
        for l in LEAVES:
            f.iface('spine-01', 'to-' + l, 'up')
        two, t = wait(lambda: (kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')
                               if len(kernel_nexthops(f, 'leaf-02', '10.200.0.21/32')) == 2
                               else None), timeout=90)
        check('F4 spine restored: both next-hops return',
              two is not None, 'observed %.2fs after the link-up command' % t)
    finally:
        f.down()


def main():
    if os.geteuid() != 0:
        print('This lab needs root (it creates network namespaces).')
        return 2
    if not shutil.which('vtysh') or not pathlib.Path(FRR_BIN + '/bgpd').exists():
        print('FRR (zebra, bgpd, vtysh) is required and was not found.')
        return 2
    print('Lab 36.2 --- Anvil eBGP underlay on Linux namespaces')
    print('  kernel : ' + sh(['uname', '-srm']).stdout.strip())
    print('  FRR    : ' + frr_version())
    print('  IPv6   : ' + ('available' if have_ipv6()
                           else 'DISABLED in this kernel --- BGP unnumbered is NOT tested here'))
    print('  scope  : Linux control plane and forwarding only. Not Containerlab,')
    print('           not a commercial NOS, not an ASIC, no throughput measured.')
    for fn in (scenario_a, scenario_bc, scenario_d, scenario_e, scenario_f):
        fn()
    passed = sum(1 for r in RESULTS if r['pass'])
    print('\n%d/%d checks passed' % (passed, len(RESULTS)))
    out = {'frr': frr_version(), 'kernel': sh(['uname', '-srm']).stdout.strip(),
           'ipv6_available': have_ipv6(),
           'scope': ('Linux namespaces and FRR only. No Containerlab, no commercial NOS, '
                     'no ASIC, no throughput measurement. BGP unnumbered transport is not '
                     'tested when IPv6 is unavailable.'),
           'checks': RESULTS, 'passed': passed, 'total': len(RESULTS)}
    pathlib.Path('lab36-results.json').write_text(json.dumps(out, indent=2))
    print('Results written to lab36-results.json')
    return 0 if passed == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
