#!/usr/bin/env python3
"""Validate the branch address plan, and check the document matches it.

    python3 check_addressing.py

branch-hgt.json is the single source. This checks that every prefix is
canonical (no host bits set), that every LAN, loopback pool and spare block sits
inside the site allocation, that the site allocation sits inside the
enterprise's genuinely unallocated pool rather than another site's reservation,
that nothing overlaps anything else, and that every DHCP range sits inside its
own subnet. It then checks that the address table printed in
BRANCH-COMPLETE.md agrees with the JSON, because a document and its source
diverge the moment somebody edits one of them.

Chapter 6 teaches canonical, contained and disjoint. A reference design that
does not pass its own book's test is worse than no reference design.
"""
import ipaddress as ip
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def net(s):
    return ip.ip_network(s, strict=True)   # strict: host bits set is an error


def main():
    d = json.load(open(os.path.join(HERE, 'branch-hgt.json'), encoding='utf-8'))
    problems = []

    def check(cond, msg):
        if not cond:
            problems.append(msg)

    # --- canonical, and the site sits in unallocated space ---
    try:
        v4 = net(d['site_allocation']['ipv4'])
        v6 = net(d['site_allocation']['ipv6'])
    except ValueError as e:
        print('site allocation is not canonical: %s' % e)
        return 2
    pool = net(d['parents']['ipv4_unallocated_pool'])
    ent6 = net(d['parents']['ipv6_enterprise'])
    check(v4.subnet_of(pool), '%s is not inside the unallocated pool %s' % (v4, pool))
    check(v6.subnet_of(ent6), '%s is not inside %s' % (v6, ent6))

    # --- every block canonical, contained, and disjoint ---
    blocks = []   # (label, network)
    for lan in d['lans']:
        for fam in ('ipv4', 'ipv6'):
            try:
                n = net(lan[fam])
            except ValueError as e:
                problems.append('VLAN %s %s: %s' % (lan['vlan'], fam, e)); continue
            parent = v4 if fam == 'ipv4' else v6
            check(n.subnet_of(parent), 'VLAN %s %s %s is not inside %s' % (lan['vlan'], fam, n, parent))
            blocks.append(('VLAN %s %s' % (lan['vlan'], fam), n))
    for label, key, parent in (('loopback pool v4', 'ipv4_pool', v4), ('loopback pool v6', 'ipv6_pool', v6)):
        try:
            n = net(d['loopbacks'][key])
            check(n.subnet_of(parent), '%s %s is not inside %s' % (label, n, parent))
            blocks.append((label, n))
        except ValueError as e:
            problems.append('%s: %s' % (label, e))
    for fam, parent in (('ipv4', v4), ('ipv6', v6)):
        for s in d['spare'][fam]:
            try:
                n = net(s)
                check(n.subnet_of(parent), 'spare %s is not inside %s' % (n, parent))
                blocks.append(('spare %s' % n, n))
            except ValueError as e:
                problems.append('spare %s: %s' % (s, e))

    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            (la, a), (lb, b) = blocks[i], blocks[j]
            if a.version == b.version and a.overlaps(b):
                problems.append('%s (%s) overlaps %s (%s)' % (la, a, lb, b))

    # --- DHCP ranges inside their own subnet ---
    for lan in d['lans']:
        if not lan.get('dhcp4'):
            continue
        lo, hi = (ip.ip_address(x) for x in lan['dhcp4'].split('-'))
        n = ip.ip_network(lan['ipv4'], strict=False)
        check(lo in n and hi in n, 'VLAN %s DHCP range %s is not inside %s' % (lan['vlan'], lan['dhcp4'], n))
        check(lo < hi, 'VLAN %s DHCP range is inverted' % lan['vlan'])

    # --- the printed table must agree with the source ---
    doc = os.path.join(HERE, 'BRANCH-COMPLETE.md')
    if os.path.exists(doc):
        text = open(doc, encoding='utf-8').read()
        for lan in d['lans']:
            row = re.search(r'^\|\s*%d\s*\|([^\n]*)$' % lan['vlan'], text, re.M)
            if not row:
                problems.append('VLAN %s has no row in BRANCH-COMPLETE.md' % lan['vlan']); continue
            cells = row.group(1)
            for fam in ('ipv4', 'ipv6'):
                if lan[fam].replace('/', '/') not in cells:
                    problems.append('VLAN %s: the document does not print %s' % (lan['vlan'], lan[fam]))
        for want in (d['site_allocation']['ipv4'], d['site_allocation']['ipv6']):
            check(want in text, 'the document does not print the site allocation %s' % want)
    else:
        problems.append('BRANCH-COMPLETE.md not found beside this script')

    print('%d LANs, %d spare blocks checked against %s / %s'
          % (len(d['lans']), len(d['spare']['ipv4']) + len(d['spare']['ipv6']), v4, v6))
    if problems:
        for p in problems:
            print('    %s' % p)
        print('\n%d problem(s). The plan is not canonical, contained and disjoint.' % len(problems))
        return 2
    print('canonical, contained, disjoint; DHCP ranges inside their subnets; '
          'the document agrees with the source.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
