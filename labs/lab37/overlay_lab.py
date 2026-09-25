#!/usr/bin/env python3
"""Lab 37.2 --- a two-tenant VXLAN/EVPN overlay, run for real on Linux.

WHAT THIS IS. The Lab 36.2 underlay (two spines, four leaves, eBGP, Linux network
namespaces, FRR) with an EVPN control plane and Linux VXLAN data plane on top, plus
four hosts. The harness reads BGP, the bridge forwarding database and traffic outcomes.
A fresh run must establish its own results; historical observations are in README.md.

It answers, by measurement:

  A  Do the EVPN type-3 routes cross an eBGP spine with the originating leaf's
     loopback still in the next hop? (If the spine rewrote it, no tunnel would form.)
  B  Do two hosts of the same tenant on different racks reach each other, and is
     the remote MAC learned from the right VTEP?
  C  Two tenants using the SAME subnet and the SAME host addresses: does each host
     reach its own tenant's peer and never the other's?
  D  What route target does the implementation actually use, and does isolation
     really rest on route-target membership?
  E  What is the largest ICMP payload that survives a 1500-byte underlay, and does
     it match the byte arithmetic the chapter gives?
  F  When a MAC moves to another leaf, does the EVPN route follow it?

WHAT THIS IS NOT. Linux VXLAN and the FRR control plane. Not Containerlab, not a
commercial NOS, not an ASIC, no throughput measured, no multi-homing (EVPN types 1
and 4), and no symmetric IRB --- see NOT-TESTED at the end of the run.

Requires root, iproute2 (with bridge) and FRR (zebra, bgpd). Run:

    sudo python3 overlay_lab.py
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import uuid

RUN = pathlib.Path('/run/rtn-lab37-' + uuid.uuid4().hex[:12])
NS_PREFIX = RUN.name + '-'

def ns_name(node):
    return NS_PREFIX + node

FRR_BIN = os.environ.get('RTN_FRR_BIN', '/usr/lib/frr')

SPINE_AS = 4200000000
LEAF_AS = {'leaf-01': 4200000101, 'leaf-02': 4200000102,
           'leaf-03': 4200000103, 'leaf-04': 4200000104}
LOOPBACK = {'spine-01': '10.200.0.11', 'spine-02': '10.200.0.12',
            'leaf-01': '10.200.0.21', 'leaf-02': '10.200.0.22',
            'leaf-03': '10.200.0.23', 'leaf-04': '10.200.0.24'}
SPINES = ['spine-01', 'spine-02']
LEAVES = ['leaf-01', 'leaf-02', 'leaf-03', 'leaf-04']

# Two tenants deliberately share a subnet AND host addresses. If the tenants are
# isolated, each host still reaches only its own peer; if they are not, the
# addresses collide and it shows immediately.
VNI = {'red': 10010, 'blue': 10020}
HOSTS = {  # host: (leaf, tenant, address, mac)
    'h-red-a':  ('leaf-01', 'red', '10.50.10.11', '02:00:00:00:00:a1'),
    'h-red-b':  ('leaf-03', 'red',  '10.50.10.12', '02:00:00:00:00:a2'),
    'h-blue-a': ('leaf-02', 'blue', '10.50.10.11', '02:00:00:00:00:b1'),
    'h-blue-b': ('leaf-04', 'blue', '10.50.10.12', '02:00:00:00:00:b2'),
}
TENANT_OF_LEAF = {'leaf-01': 'red', 'leaf-02': 'blue',
                  'leaf-03': 'red', 'leaf-04': 'blue'}

UNDERLAY_MTU_DEFAULT = 9000
# Outer IP packet = outer IPv4 (20) + UDP (8) + VXLAN (8) + inner Ethernet header
# (14, FCS excluded) + inner IP packet. So the underlay must carry 50 bytes more
# than the inner IP packet, and does not include an outer Ethernet header in that IP MTU.
VXLAN_OUTER_OVERHEAD = 20 + 8 + 8 + 14      # 50
INNER_IP_AND_ICMP_HEADERS = 20 + 8          # 28


def sh(cmd, ns=None, check=True, timeout=60):
    if ns:
        cmd = ['ip', 'netns', 'exec', ns_name(ns)] + cmd
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode:
        raise RuntimeError('%s -> rc=%d\n%s\n%s'
                           % (' '.join(cmd), r.returncode, r.stdout[-1500:], r.stderr[-1500:]))
    return r


def tmpname():
    # Never use a name iproute2 could read as a keyword abbreviation ("he" is
    # parsed as "help"). Random hex avoids the whole class of surprise.
    return 'v' + os.urandom(3).hex()


RESULTS = []
OBSERVATIONS = []


def observe(name, text):
    OBSERVATIONS.append({'observation': name, 'detail': text})
    print('  NOTE  %s\n        %s' % (name, text))


def check(name, ok, detail=''):
    RESULTS.append({'check': name, 'pass': bool(ok), 'detail': str(detail)[:400]})
    print('  %s  %s%s' % ('PASS' if ok else 'FAIL', name,
                          ('  [%s]' % detail) if detail else ''))
    return bool(ok)


class Fabric:
    def __init__(self):
        self.owned_nodes = []
        self.switches = SPINES + LEAVES
        self.nodes = self.switches + list(HOSTS)
        self.link_ifaces = []

    # ---- build ------------------------------------------------------
    def up(self, underlay_mtu=UNDERLAY_MTU_DEFAULT):
        RUN.mkdir(parents=True, exist_ok=False)
        for n in self.nodes:
            sh(['ip', 'netns', 'add', ns_name(n)])
            self.owned_nodes.append(n)
            sh(['ip', 'link', 'set', 'lo', 'up'], ns=n)
        for n in self.switches:
            sh(['ip', 'addr', 'add', LOOPBACK[n] + '/32', 'dev', 'lo'], ns=n)
            sh(['sysctl', '-qw', 'net.ipv4.ip_forward=1'], ns=n)
        base = 0
        for s in SPINES:
            for l in LEAVES:
                sip, lip = '10.200.1.%d' % base, '10.200.1.%d' % (base + 1)
                base += 2
                a, b = tmpname(), tmpname()
                sh(['ip', 'link', 'add', a, 'type', 'veth', 'peer', 'name', b])
                sh(['ip', 'link', 'set', a, 'netns', ns_name(s), 'name', 'to-' + l])
                sh(['ip', 'link', 'set', b, 'netns', ns_name(l), 'name', 'to-' + s])
                sh(['ip', 'addr', 'add', sip + '/31', 'dev', 'to-' + l], ns=s)
                sh(['ip', 'addr', 'add', lip + '/31', 'dev', 'to-' + s], ns=l)
                for ns, ifn in ((s, 'to-' + l), (l, 'to-' + s)):
                    sh(['ip', 'link', 'set', ifn, 'mtu', str(underlay_mtu)], ns=ns)
                    sh(['ip', 'link', 'set', ifn, 'up'], ns=ns)
                    self.link_ifaces.append((ns, ifn))
        for leaf in LEAVES:
            self.add_vni(leaf, TENANT_OF_LEAF[leaf], underlay_mtu)
        for host, (leaf, tenant, addr, mac) in HOSTS.items():
            self.attach_host(host, leaf, tenant, addr, mac)

    def add_vni(self, leaf, tenant, underlay_mtu):
        vni = VNI[tenant]
        br, vx = 'br%d' % vni, 'vni%d' % vni
        inner_mtu = min(1500, underlay_mtu - VXLAN_OUTER_OVERHEAD)
        sh(['ip', 'link', 'add', br, 'type', 'bridge'], ns=leaf)
        sh(['ip', 'link', 'add', vx, 'type', 'vxlan', 'id', str(vni),
            'dstport', '4789', 'local', LOOPBACK[leaf], 'nolearning'], ns=leaf)
        sh(['ip', 'link', 'set', vx, 'master', br], ns=leaf)
        for d in (br, vx):
            sh(['ip', 'link', 'set', d, 'mtu', str(inner_mtu)], ns=leaf)
            sh(['ip', 'link', 'set', d, 'up'], ns=leaf)
        # ARP/ND suppression at the VTEP, and no data-plane learning: the control
        # plane is meant to be BGP, not flood-and-learn.
        sh(['bridge', 'link', 'set', 'dev', vx, 'neigh_suppress', 'on',
            'learning', 'off'], ns=leaf)

    def attach_host(self, host, leaf, tenant, addr, mac, ifname='eth0'):
        br = 'br%d' % VNI[tenant]
        a, b = tmpname(), tmpname()
        port = 'to-' + host
        sh(['ip', 'link', 'add', a, 'type', 'veth', 'peer', 'name', b])
        sh(['ip', 'link', 'set', a, 'netns', ns_name(leaf), 'name', port])
        sh(['ip', 'link', 'set', b, 'netns', ns_name(host), 'name', ifname])
        sh(['ip', 'link', 'set', port, 'master', br], ns=leaf)
        inner = self.leaf_inner_mtu(leaf)
        for ns, ifn in ((leaf, port), (host, ifname)):
            sh(['ip', 'link', 'set', ifn, 'mtu', str(inner)], ns=ns)
        sh(['ip', 'link', 'set', port, 'up'], ns=leaf)
        sh(['ip', 'link', 'set', ifname, 'address', mac], ns=host)
        sh(['ip', 'addr', 'add', addr + '/24', 'dev', ifname], ns=host)
        sh(['ip', 'link', 'set', ifname, 'up'], ns=host)

    def leaf_inner_mtu(self, leaf):
        vx = 'vni%d' % VNI[TENANT_OF_LEAF[leaf]]
        out = sh(['ip', '-j', 'link', 'show', vx], ns=leaf).stdout
        return json.loads(out)[0]['mtu']

    def set_underlay_mtu(self, mtu):
        for ns, ifn in self.link_ifaces:
            sh(['ip', 'link', 'set', ifn, 'mtu', str(mtu)], ns=ns)

    def set_overlay_mtu(self, mtu):
        for leaf in LEAVES:
            vni = VNI[TENANT_OF_LEAF[leaf]]
            for d in ('br%d' % vni, 'vni%d' % vni, ):
                sh(['ip', 'link', 'set', d, 'mtu', str(mtu)], ns=leaf)
            for host, (l, t, a, m) in HOSTS.items():
                if l == leaf:
                    sh(['ip', 'link', 'set', 'to-' + host, 'mtu', str(mtu)], ns=leaf)
                    sh(['ip', 'link', 'set', 'eth0', 'mtu', str(mtu)], ns=host)

    # ---- routing ----------------------------------------------------
    def peers_of(self, node):
        base = 0
        out = []
        for s in SPINES:
            for l in LEAVES:
                sip, lip = '10.200.1.%d' % base, '10.200.1.%d' % (base + 1)
                base += 2
                if node == s:
                    out.append(lip)
                elif node == l:
                    out.append(sip)
        return out

    def start_frr(self, node, explicit_rt=False):
        asn = SPINE_AS if node in SPINES else LEAF_AS[node]
        peers = self.peers_of(node)
        L = ['hostname ' + node, '!', 'router bgp %d' % asn,
             ' bgp router-id ' + LOOPBACK[node],
             ' no bgp default ipv4-unicast',
             ' neighbor FABRIC peer-group',
             ' neighbor FABRIC remote-as external',
             ' neighbor FABRIC timers 1 3',
             ' neighbor FABRIC advertisement-interval 0']
        L += [' neighbor %s peer-group FABRIC' % p for p in peers]
        L += [' !', ' address-family ipv4 unicast', '  maximum-paths 8']
        L += ['  neighbor %s activate' % p for p in peers]
        L += ['  neighbor FABRIC route-map UNDERLAY-IN in',
              '  neighbor FABRIC route-map UNDERLAY-OUT out',
              '  redistribute connected route-map LOOPBACKS',
              ' exit-address-family', ' !',
              ' address-family l2vpn evpn']
        L += ['  neighbor %s activate' % p for p in peers]
        # RFC 8212 applies per address family: without policy here, EVPN carries
        # nothing and every VTEP looks isolated while every session looks healthy.
        L += ['  neighbor FABRIC route-map EVPN-IN in',
              '  neighbor FABRIC route-map EVPN-OUT out']
        if node in LEAVES:
            L += ['  advertise-all-vni']
            if explicit_rt:
                tenant = TENANT_OF_LEAF[node]
                vni = VNI[tenant]
                L += ['  vni %d' % vni,
                      '   rd %s:%d' % (LOOPBACK[node], vni),
                      '   route-target import 64500:%d' % vni,
                      '   route-target export 64500:%d' % vni,
                      '  exit-vni']
        L += [' exit-address-family', '!',
              'ip prefix-list LOOPBACK-SPACE seq 10 permit 10.200.0.0/24 ge 32 le 32',
              '!', 'route-map LOOPBACKS permit 10', ' match interface lo', '!',
              'route-map UNDERLAY-IN permit 10',
              ' match ip address prefix-list LOOPBACK-SPACE', '!',
              'route-map UNDERLAY-OUT permit 10',
              ' match ip address prefix-list LOOPBACK-SPACE', '!',
              'route-map EVPN-IN permit 10', '!', 'route-map EVPN-OUT permit 10', '!']
        self.start(node, '\n'.join(L) + '\n')

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

    def ping(self, host, dst, size=None, df=False, count=2, wait=2):
        cmd = ['ping', '-c', str(count), '-W', str(wait)]
        if size is not None:
            cmd += ['-s', str(size)]
        if df:
            cmd += ['-M', 'do']
        cmd.append(dst)
        r = sh(cmd, ns=host, check=False)
        if r.returncode not in (0, 1):
            raise RuntimeError('Ping instrument failed: ' + r.stderr)
        return r.returncode == 0, r.stdout + r.stderr

    def fdb(self, leaf, tenant):
        return sh(['bridge', 'fdb', 'show', 'dev', 'vni%d' % VNI[tenant]],
                  ns=leaf).stdout

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


def wait(fn, timeout=90, interval=0.5):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        v = fn()
        if v:
            return v, time.monotonic() - t0
        time.sleep(interval)
    return None, time.monotonic() - t0


def _walk(obj):
    """Yield every dict in a nested JSON structure."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def evpn_type3_vteps(f, leaf):
    """(originating VTEP, BGP next hop) for each type-3 route from a remote leaf.

    Read from JSON rather than scraped from the table: the text layout wraps
    differently depending on field widths, and a scraper that silently returns
    nothing looks exactly like a fabric that is not working.
    """
    d = f.vty_json(leaf, 'show bgp l2vpn evpn route type 3 json') or {}
    vteps = set()
    for node in _walk(d):
        if node.get('routeType') != 3:
            continue
        origin = node.get('ip')
        nhs = [n.get('ip') for n in node.get('nexthops', []) if n.get('ip')]
        if origin and nhs and origin != LOOPBACK[leaf]:
            vteps.add((origin, nhs[0]))
    return vteps


def route_targets(f, leaf):
    out = f.vty(leaf, 'show bgp l2vpn evpn')
    return sorted(set(re.findall(r'RT:(\d+:\d+)', out)))


def fdb_match(text, mac, vtep, external=False):
    for line in text.splitlines():
        words = line.split()
        if words and words[0].lower() == mac.lower() and 'dst' in words:
            i = words.index('dst')
            if i + 1 < len(words) and words[i + 1] == vtep and (not external or 'extern_learn' in words):
                return True
    return False


def largest_payload(f, host, dst, lo=1, hi=1500):
    """Binary-search the largest ICMP payload that crosses with DF set."""
    ok_lo, _ = f.ping(host, dst, size=lo, df=True, count=1, wait=2)
    if not ok_lo:
        return None
    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        ok, _ = f.ping(host, dst, size=mid, df=True, count=1, wait=2)
        if ok:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


# --------------------------------------------------------------------------
def scenario_a_to_d(explicit_rt=False, label='auto-derived'):
    print('\nA-D. Overlay with %s route targets' % label)
    f = Fabric()
    try:
        f.up()
        for n in f.switches:
            f.start_frr(n, explicit_rt=explicit_rt)
        vteps, t = wait(lambda: (evpn_type3_vteps(f, 'leaf-03')
                                 if len(evpn_type3_vteps(f, 'leaf-03')) >= 1 else None),
                        timeout=90)
        vteps = vteps or evpn_type3_vteps(f, 'leaf-03')
        if not explicit_rt:
            check('A1 leaf-03 receives EVPN type-3 routes from remote leaves',
                  len(vteps) >= 1, '%d after %.1fs: %s' % (len(vteps), t, sorted(vteps)))
            check('A2 the next hop is the ORIGINATING leaf loopback, not the spine '
                  '(an eBGP spine that rewrote it would break every tunnel)',
                  bool(vteps) and all(o == nh for o, nh in vteps) and
                  all(nh not in (LOOPBACK[s] for s in SPINES) for _, nh in vteps),
                  sorted(vteps))
            d = f.vty_json('leaf-03', 'show evpn vni json') or {}
            v = d.get(str(VNI['red']), {})
            check('A3 leaf-03 has discovered a remote VTEP for its own VNI',
                  int(v.get('numRemoteVteps', 0) or 0) >= 1,
                  'numRemoteVteps=%s' % v.get('numRemoteVteps'))

            ok, _o = wait(lambda: f.ping('h-red-a', '10.50.10.12', count=2)[0] or None,
                          timeout=60)
            check('B1 same tenant, different racks: h-red-a reaches h-red-b', bool(ok))
            fdb = f.fdb('leaf-01', 'red')
            check('B2 the remote MAC is in the VXLAN fdb against the right VTEP',
                  fdb_match(fdb, HOSTS['h-red-b'][3], LOOPBACK['leaf-03']),
                  fdb.strip().splitlines()[:3])
            check('B3 it is marked externally learned, not flood-and-learn',
                  fdb_match(fdb, HOSTS['h-red-b'][3], LOOPBACK['leaf-03'], external=True))

            ok_blue, _o = wait(lambda: f.ping('h-blue-a', '10.50.10.12', count=2)[0] or None,
                               timeout=60)
            check('C1 the other tenant, using the SAME addresses, also works',
                  bool(ok_blue))
            red_fdb = f.fdb('leaf-01', 'red')
            check('C2 the red VTEP never learned a blue MAC',
                  HOSTS['h-blue-b'][3] not in red_fdb and HOSTS['h-blue-a'][3] not in red_fdb)
            blue_fdb = f.fdb('leaf-02', 'blue')
            check('C3 the blue VTEP never learned a red MAC',
                  HOSTS['h-red-a'][3] not in blue_fdb and HOSTS['h-red-b'][3] not in blue_fdb)
            check('C4 h-red-a\'s peer at .12 answers with the RED MAC, '
                  'not the identically addressed blue host',
                  HOSTS['h-red-b'][3] in sh(['ip', 'neigh', 'show', '10.50.10.12'],
                                            ns='h-red-a').stdout,
                  sh(['ip', 'neigh', 'show', '10.50.10.12'], ns='h-red-a').stdout.strip())

        rts = route_targets(f, 'leaf-03')
        if explicit_rt:
            per_vni = {}
            for rt in rts:
                per_vni.setdefault(rt.split(':')[1], set()).add(rt)
            expected = {'64500:' + str(v) for v in VNI.values()}
            check('D3 explicit advertised route targets match the configured set', set(rts) == expected, rts)
            ok, _ = wait(lambda: f.ping('h-red-a', '10.50.10.12', count=2)[0] or None, timeout=60)
            observe('D4 explicit-RT forwarding observation (cause not inferred)',
                    json.dumps({'forwarding_ok': bool(ok), 'advertised_targets': rts,
                                'zebra_vni': f.vty('leaf-01', 'show evpn vni'),
                                'bgp_vni': f.vty('leaf-01', 'show bgp l2vpn evpn vni')}))

        else:
            check('D1 advertised auto-targets match low-16-bit ASN plus local VNI',
                  set(rts) == {str(LEAF_AS[l] & 65535) + ':' + str(VNI[TENANT_OF_LEAF[l]]) for l in LEAVES}, rts)
            check('D2 same-tenant forwarding works with auto-targets on this build; '
                  'a controlled import-policy test is needed to attribute the cause', bool(ok) and bool(ok_blue))
        return f
    finally:
        f.down()


def scenario_e():
    print('\nE. MTU: what actually fits')
    f = Fabric()
    try:
        f.up(underlay_mtu=1500)
        for n in f.switches:
            f.start_frr(n)
        wait(lambda: f.ping('h-red-a', '10.50.10.12', count=2)[0] or None, timeout=90)
        inner = f.leaf_inner_mtu('leaf-01')
        check('E1 the VXLAN interface MTU is the underlay MTU minus 50',
              inner == 1500 - VXLAN_OUTER_OVERHEAD,
              '%d = 1500 - %d' % (inner, VXLAN_OUTER_OVERHEAD))
        biggest = largest_payload(f, 'h-red-a', '10.50.10.12', hi=1500)
        predicted = 1500 - VXLAN_OUTER_OVERHEAD - INNER_IP_AND_ICMP_HEADERS
        check('E2 the largest ICMP payload that crosses a 1500-byte underlay is '
              'exactly what the arithmetic predicts',
              biggest == predicted,
              'measured %s, predicted %d (1500 - 50 outer - 28 inner headers)'
              % (biggest, predicted))
        ok_over, _o = f.ping('h-red-a', '10.50.10.12', size=(biggest or 0) + 1,
                             df=True, count=1)
        check('E3 one byte more does not cross with an established lower boundary',
              biggest == predicted and not ok_over)
        ok_small, _o = f.ping('h-red-a', '10.50.10.12', size=56, df=True, count=1)
        check('E4 ...while a small ping still works, which is why this fault is '
              'reported as "the network is fine but transfers hang"', ok_small)

        f.set_underlay_mtu(9000)
        f.set_overlay_mtu(1500)
        ok_full, _o = wait(lambda: f.ping('h-red-a', '10.50.10.12', size=1472,
                                          df=True, count=1)[0] or None, timeout=30)
        check('E5 with underlay and inner MTUs raised, a full 1500-byte inner IP packet crosses',
              bool(ok_full), 'payload 1472 + 28 = 1500-byte inner IP packet')
    finally:
        f.down()


def scenario_f():
    print('\nF. A MAC moves to another leaf')
    f = Fabric()
    try:
        f.up()
        for n in f.switches:
            f.start_frr(n)
        wait(lambda: f.ping('h-red-a', '10.50.10.12', count=2)[0] or None, timeout=90)
        before = f.fdb('leaf-01', 'red')
        check('F1 before: h-red-b\'s MAC is reachable via leaf-03',
              fdb_match(before, HOSTS['h-red-b'][3], LOOPBACK['leaf-03']))
        # Detach the host from leaf-03 and reattach the same MAC and address
        # under leaf-01's other red peer... leaf-03 is the only other red leaf,
        # so move it to leaf-01 itself, which is the honest local-move case.
        sh(['ip', 'netns', 'del', ns_name('h-red-b')])
        f.owned_nodes.remove('h-red-b')
        f.nodes.remove('h-red-b')
        sh(['ip', 'netns', 'add', ns_name('h-red-b')])
        f.owned_nodes.append('h-red-b')
        f.nodes.append('h-red-b')
        sh(['ip', 'link', 'set', 'lo', 'up'], ns='h-red-b')
        f.attach_host('h-red-b', 'leaf-01', 'red', '10.50.10.12',
                      HOSTS['h-red-b'][3], ifname='eth0')
        mac = HOSTS['h-red-b'][3]

        def mac_lines(leaf):
            # The WHOLE bridge, not just the VXLAN device: once the host is local
            # its MAC sits on the access port, and looking only at the VXLAN
            # device would show nothing and read as a failure.
            out = sh(['bridge', 'fdb', 'show', 'br', 'br%d' % VNI['red']],
                     ns=leaf).stdout
            return [l for l in out.splitlines() if mac in l]

        def learned_local():
            return any('to-h-red-b' in l for l in mac_lines('leaf-01')) or None

        # A bridge learns a MAC when it sees a frame from it. The moved host has
        # sent nothing yet, so prompt it --- otherwise this measures how long an
        # idle host stays invisible, which is not the question.
        f.ping('h-red-b', '10.50.10.11', count=2)
        local, t = wait(learned_local, timeout=60)
        check('F2 after the move, leaf-01 has the MAC on its own access port',
              bool(local), 'observed %.1fs after reattachment' % t)

        stale = [l for l in mac_lines('leaf-01') if LOOPBACK['leaf-03'] in l]
        observe('F2b remote-entry snapshot after local learning (not a withdrawal-time measurement)',
                json.dumps({'poll_elapsed_s': t, 'stale_entries': stale,
                            'local_entries': mac_lines('leaf-01')}))
        ok, _o = wait(lambda: f.ping('h-red-a', '10.50.10.12', count=2)[0] or None,
                      timeout=30)
        check('F3 connectivity to the moved host is restored', bool(ok))
    finally:
        f.down()


def main():
    if os.geteuid() != 0:
        print('This lab needs root (it creates network namespaces).')
        return 2
    if not shutil.which('vtysh') or not pathlib.Path(FRR_BIN + '/bgpd').exists():
        print('FRR (zebra, bgpd, vtysh) is required and was not found.')
        return 2
    if not shutil.which('bridge'):
        print('iproute2 with the bridge utility is required.')
        return 2
    print('Lab 37.2 --- two-tenant VXLAN/EVPN overlay on Linux namespaces')
    print('  kernel : ' + sh(['uname', '-srm']).stdout.strip())
    print('  FRR    : ' + sh([FRR_BIN + '/bgpd', '-v']).stdout.splitlines()[0].strip())
    print('  scope  : Linux VXLAN and the FRR control plane. Not Containerlab,')
    print('           not a commercial NOS, not an ASIC, no throughput measured.')
    scenario_a_to_d(explicit_rt=False, label='auto-derived')
    scenario_a_to_d(explicit_rt=True, label='explicitly configured')
    scenario_e()
    scenario_f()
    passed = sum(1 for r in RESULTS if r['pass'])
    print('\n%d/%d checks passed, %d recorded observation(s)'
          % (passed, len(RESULTS), len(OBSERVATIONS)))
    print('\nNOT TESTED by this lab, and therefore not claimed:')
    for line in ('explicit route-target causality: D4 records the current outcome; no release-wide conclusion',
                 'symmetric IRB: no IP-VRF, no L3 VNI and no router MAC are configured here',
                 'EVPN multi-homing (route types 1 and 4) and any ESI behaviour',
                 'data centre interconnect of any kind',
                 'Containerlab, commercial NOS, ASIC behaviour or throughput',
                 'anything about a platform other than this Linux kernel and this FRR build'):
        print('  - ' + line)
    out = {'kernel': sh(['uname', '-srm']).stdout.strip(),
           'frr': sh([FRR_BIN + '/bgpd', '-v']).stdout.splitlines()[0].strip(),
           'scope': ('Linux VXLAN data plane and FRR EVPN control plane only. No '
                     'Containerlab, no commercial NOS, no ASIC, no throughput, no '
                     'symmetric IRB, no multi-homing, no DCI.'),
           'checks': RESULTS, 'passed': passed, 'total': len(RESULTS),
           'observations': OBSERVATIONS,
           'not_established': [
               'Explicit-RT forwarding: current outcome is in D4; its cause is not isolated by this harness',
               'Symmetric IRB: no IP-VRF, L3 VNI or router MAC is configured here',
               'EVPN multi-homing (types 1 and 4) and ESI behaviour',
               'Data centre interconnect of any kind',
               'Containerlab, commercial NOS, ASIC behaviour and throughput']}
    pathlib.Path('lab37-results.json').write_text(json.dumps(out, indent=2))
    print('\nResults written to lab37-results.json')
    return 0 if passed == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
