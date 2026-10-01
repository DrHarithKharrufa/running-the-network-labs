#!/usr/bin/env python3
"""
Generate the Kestrel device configurations from one data table.

This is the book's own advice applied to its own lab (Chapter 68): the
addressing lives in a structure, the configuration is rendered from it, and
nothing is typed twice.  Render into a separate directory and review the diff; never hand-edit the
generated .cfg files.

    python3 generate.py --out OUTPUT_DIRECTORY
"""
from pathlib import Path
import argparse

AS_KESTREL = 64500
AREA = "49.0001"

# name            loop  isis-sys-id        links: (iface, ip/31-local, peer)
DEVICES = {
    "lon-p-01":  dict(loop=11, sid="0000.0000.0011", role="p",
                      links=[("ethernet-1/1", "10.254.0.0/31", "man-p-01"),
                             ("ethernet-1/2", "10.254.0.2/31", "bhm-p-01"),
                             ("ethernet-1/3", "10.254.1.1/31", "lon-pr-01")]),
    "man-p-01":  dict(loop=12, sid="0000.0000.0012", role="p",
                      links=[("ethernet-1/1", "10.254.0.1/31", "lon-p-01"),
                             ("ethernet-1/2", "10.254.0.4/31", "lds-p-01"),
                             ("ethernet-1/3", "10.254.1.3/31", "man-pr-01")]),
    "bhm-p-01":  dict(loop=13, sid="0000.0000.0013", role="p",
                      links=[("ethernet-1/1", "10.254.0.3/31", "lon-p-01"),
                             ("ethernet-1/2", "10.254.0.6/31", "lds-p-01"),
                             ("ethernet-1/3", "10.254.1.5/31", "lon-pe-01")]),
    "lds-p-01":  dict(loop=14, sid="0000.0000.0014", role="p",
                      links=[("ethernet-1/1", "10.254.0.5/31", "man-p-01"),
                             ("ethernet-1/2", "10.254.0.7/31", "bhm-p-01"),
                             ("ethernet-1/3", "10.254.1.7/31", "bhm-bng-01")]),
    "lon-pr-01": dict(loop=21, sid="0000.0000.0021", role="border",
                      links=[("ethernet-1/1", "10.254.1.0/31", "lon-p-01")],
                      ebgp=[("ethernet-1/2", "192.0.2.0/31", "192.0.2.1", 64496, "transit"),
                            ("ethernet-1/3", "198.51.100.0/31", "198.51.100.1", 64498, "peer")]),
    "man-pr-01": dict(loop=22, sid="0000.0000.0022", role="border",
                      links=[("ethernet-1/1", "10.254.1.2/31", "man-p-01")],
                      ebgp=[("ethernet-1/2", "192.0.2.2/31", "192.0.2.3", 64497, "transit")]),
    "lon-pe-01": dict(loop=23, sid="0000.0000.0023", role="pe",
                      links=[("ethernet-1/1", "10.254.1.4/31", "bhm-p-01")],
                      ebgp=[("ethernet-1/2", "192.0.2.4/31", "192.0.2.5", 64501, "customer")]),
}


# This is a bounded IPv4 candidate, statically reviewed against SR Linux 24.10.
# No NOS acceptance/forwarding or Containerlab run is implied by generation.
IBGP_LOOPS = [11, 12, 13, 14, 21, 22, 23, 24]  # includes the FRR subscriber stand-in
CLASS = {'customer': (200, 1000), 'peer': (150, 2000), 'transit': (100, 3000)}
ALLOWED = {
  '192.0.2.1': ['0.0.0.0/0', '198.18.0.0/17', '198.19.0.0/17'],
  '192.0.2.3': ['0.0.0.0/0', '198.18.128.0/17', '198.19.128.0/17'],
  '198.51.100.1': ['198.51.100.128/25'],
  '192.0.2.5': ['203.0.113.0/24'],
}
CUSTOMER = ['203.0.113.0/24']
EXTERNAL = sorted(set(p for ps in ALLOWED.values() for p in ps))
INTERNAL = EXTERNAL + ['100.64.0.0/24']

def render(name, d):
    out=[f'# {name}: generated IPv4 teaching candidate, SR Linux 24.10; NOT runtime validated.']
    a=out.append; lo=f"10.255.0.{d['loop']}"
    ni='set / network-instance default'; rp='set / routing-policy'; bg=ni+' protocols bgp'
    def pset(n, prefixes):
        for p in prefixes:a(f'{rp} prefix-set {n} prefix {p} mask-length-range exact')
    def policy(n,prefixes,extra=None,nh=False):
        pset(n,prefixes)
        a(f'{rp} policy {n} statement 10 match prefix-set {n}')
        a(f'{rp} policy {n} statement 10 match protocol bgp')
        if extra:a(f'{rp} policy {n} statement 10 match bgp community-set {extra}')
        a(f'{rp} policy {n} statement 10 action policy-result accept')
        if nh:a(f'{rp} policy {n} statement 10 action bgp next-hop set self')
        a(f'{rp} policy {n} default-action policy-result reject')
    a(f'set / system name host-name {name}')
    a(f'{ni} type default');a(f'{ni} admin-state enable')
    for iface,addr in [('system0',lo+'/32')]+[(i,ad) for i,ad,*_ in d['links']+d.get('ebgp',[])]:
        a(f'set / interface {iface} admin-state enable')
        a(f'set / interface {iface} subinterface 0 admin-state enable')
        a(f'set / interface {iface} subinterface 0 ipv4 admin-state enable')
        a(f'set / interface {iface} subinterface 0 ipv4 address {addr}')
        a(f'{ni} interface {iface}.0')
    igp=ni+' protocols isis instance core'
    a(f'{igp} admin-state enable');a(f'{igp} net [ {AREA}.{d["sid"]}.00 ]')
    a(f'{igp} level-capability L2');a(f'{igp} ipv4-unicast admin-state enable')
    a(f'{igp} ipv6-unicast admin-state disable')
    a(f'{igp} interface system0.0 passive true')
    for iface,*_ in d['links']:
        a(f'{igp} interface {iface}.0 circuit-type point-to-point')
        a(f'{igp} interface {iface}.0 ipv4-unicast admin-state enable')
    for klass,(_,tag) in CLASS.items():
        a(f'{rp} community-set TAG-{klass.upper()} member [ {AS_KESTREL}:{tag} ]')
    a(f'{rp} community-set LOCAL-CLASS member [ 64500:1000 64500:2000 64500:3000 ]')
    policy('IBGP-IN',INTERNAL)
    # Full mesh: only locally originated/eBGP-learned routes are exported by BGP.
    # Explicit next-hop-self avoids relying on external link prefixes in IS-IS.
    policy('IBGP-OUT',INTERNAL,nh=True)
    policy('TO-UPSTREAM',CUSTOMER,'TAG-CUSTOMER')
    policy('TO-CUSTOMER',EXTERNAL)
    a(f'{bg} admin-state enable');a(f'{bg} autonomous-system {AS_KESTREL}')
    a(f'{bg} router-id {lo}');a(f'{bg} afi-safi ipv4-unicast admin-state enable')
    a(f'{bg} group IBGP peer-as {AS_KESTREL}')
    a(f'{bg} group IBGP transport local-address {lo}')
    a(f'{bg} group IBGP import-policy [ IBGP-IN ]')
    a(f'{bg} group IBGP export-policy [ IBGP-OUT ]')
    for loop in IBGP_LOOPS:
        if loop!=d['loop']:a(f'{bg} neighbor 10.255.0.{loop} peer-group IBGP')
    for iface,addr,peer,asn,klass in d.get('ebgp',[]):
        key=f'FROM-{asn}';lp,tag=CLASS[klass]
        pset(key,ALLOWED[peer]);a(f'{rp} as-path-set {key} expression "^{asn}$"')
        # Remove only local provenance tags, preserving well-known communities.
        a(f'{rp} policy {key} statement 5 action bgp communities remove LOCAL-CLASS')
        a(f'{rp} policy {key} statement 5 action policy-result next-statement')
        a(f'{rp} policy {key} statement 10 match prefix-set {key}')
        a(f'{rp} policy {key} statement 10 match bgp as-path-set {key}')
        a(f'{rp} policy {key} statement 10 action bgp local-preference set {lp}')
        a(f'{rp} policy {key} statement 10 action bgp communities add TAG-{klass.upper()}')
        a(f'{rp} policy {key} statement 10 action policy-result accept')
        a(f'{rp} policy {key} default-action policy-result reject')
        a(f'{bg} group {key} peer-as {asn}')
        a(f'{bg} group {key} import-policy [ {key} ]')
        export='TO-CUSTOMER' if klass=='customer' else 'TO-UPSTREAM'
        a(f'{bg} group {key} export-policy [ {export} ]')
        a(f'{bg} neighbor {peer} peer-group {key}')
    return '\n'.join(out)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    for name,d in DEVICES.items():
        dest=args.out/(name+'.cfg')
        if dest.exists():raise SystemExit(f'Refusing to overwrite {dest}; use a fresh output directory')
    for name,d in DEVICES.items():(args.out/(name+'.cfg')).write_text(render(name,d),encoding='utf-8')
    print('Seven candidates rendered; device validation remains required.')
