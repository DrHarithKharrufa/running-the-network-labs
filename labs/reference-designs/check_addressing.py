#!/usr/bin/env python3
"""Validate the branch address plan, and keep the document's table generated.

    python3 check_addressing.py            # validate, and diff the document
    python3 check_addressing.py --write    # regenerate the document's block
    python3 check_addressing.py --emit     # print the block to stdout

branch-hgt.json is the single source. This program does two separate jobs and
reports them separately, because conflating them is how a checker comes to
claim more than it tested.

JOB 1 --- the plan itself. Every prefix canonical (no host bits set); every
LAN, loopback pool, loopback assignment and spare block inside the site
allocation; the site allocation inside the enterprise's genuinely unallocated
pool rather than another site's reservation; nothing overlapping anything else;
every DHCP range inside its own subnet and not inverted; every device loopback
inside its own pool and outside every host LAN.

JOB 2 --- the document. The addressing block in BRANCH-COMPLETE.md is
*generated* from the JSON, between the two generated-block markers. This
program regenerates it and compares the two byte for byte, so the document
cannot drift from its source in any field: not the prefixes, not the DHCP
ranges, not the loopback assignments, not the spare list. Earlier versions of
this program compared only the LAN prefixes while reporting that "the document
agrees with the source", which was wider than what it checked --- an
independent reviewer corrupted three other fields and this program passed all
three. test_check_addressing.py keeps those three cases, and others, as a
regression suite.

What it still does not establish: that the plan is a good plan, that the
devices exist, or that anything has been configured. It checks arithmetic and
agreement. Read the design as well.

Chapter 6 teaches canonical, contained and disjoint. A reference design that
does not pass its own book's test is worse than no reference design.
"""
import ipaddress as ip
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, 'branch-hgt.json')
DOC = os.path.join(HERE, 'BRANCH-COMPLETE.md')

BEGIN = '<!-- BEGIN GENERATED addressing -- edit branch-hgt.json, then run: python3 check_addressing.py --write -->'
END = '<!-- END GENERATED addressing -->'
NDASH = '–'


def net(s):
    return ip.ip_network(s, strict=True)      # strict: host bits set is an error


# --------------------------------------------------------------- the generator
def short(addr, prefix):
    """`10.10.64.50` inside 10.10.64.0/24 prints as `.50`; otherwise in full.

    The shorthand is only safe when the host part fits the last octet, so the
    rule is explicit rather than assumed.
    """
    n = ip.ip_network(prefix, strict=False)
    a = ip.ip_address(addr)
    if n.version == 4 and n.prefixlen >= 24 and a in n:
        return '.%d' % (int(a) & 0xff)
    return str(a)


def emit(d):
    """The addressing block, generated from the source. One authority."""
    lines = []
    lines.append('| VLAN | Purpose | IPv4 | IPv6 | DHCPv4 |')
    lines.append('|---|---|---|---|---|')
    for lan in d['lans']:
        if lan.get('dhcp4'):
            lo, hi = lan['dhcp4'].split('-')
            dhcp = '`%s`%s`%s`' % (short(lo, lan['ipv4']), NDASH,
                                   short(hi, lan['ipv4']))
        else:
            dhcp = 'static'
        lines.append('| %d | %s | `%s` | `%s` | %s |'
                     % (lan['vlan'], lan['purpose'], lan['ipv4'], lan['ipv6'],
                        dhcp))
    lines.append('')
    lb = d['loopbacks']
    devices = sorted(k for k in lb if k not in ('ipv4_pool', 'ipv6_pool'))
    assigned = ', '.join(
        '`%s` is `%s` and `%s`' % (name, lb[name]['ipv4'], lb[name]['ipv6'])
        for name in devices)
    lines.append('Loopbacks come from their own blocks, `%s` and `%s`, not from '
                 'the infrastructure LAN: %s. A loopback inside a host LAN\'s '
                 '/64 works on some platforms and surprises you on others; a '
                 'distinct pool costs nothing and removes the question.'
                 % (lb['ipv4_pool'], lb['ipv6_pool'], assigned))
    lines.append('')
    spares = ['`%s`' % s for s in d['spare']['ipv4'] + d['spare']['ipv6']]
    lines.append('Genuinely spare: %s and %s. This program proves they are '
                 'spare.' % (', '.join(spares[:-1]), spares[-1]))
    return '\n'.join(lines)


def splice(text, block):
    i, j = text.find(BEGIN), text.find(END)
    if i < 0 or j < 0 or j < i:
        return None
    return text[:i] + BEGIN + '\n\n' + block + '\n\n' + text[j:]


# ---------------------------------------------------------------- job 1: plan
def validate(d):
    problems = []

    def check(cond, msg):
        if not cond:
            problems.append(msg)

    try:
        v4 = net(d['site_allocation']['ipv4'])
        v6 = net(d['site_allocation']['ipv6'])
    except ValueError as e:
        return None, None, ['site allocation is not canonical: %s' % e], 0
    pool = net(d['parents']['ipv4_unallocated_pool'])
    ent6 = net(d['parents']['ipv6_enterprise'])
    check(v4.subnet_of(pool),
          '%s is not inside the unallocated pool %s' % (v4, pool))
    check(v6.subnet_of(ent6), '%s is not inside %s' % (v6, ent6))

    blocks = []                                   # (label, network)
    host_lans = []                                # LANs only, for the loopbacks
    for lan in d['lans']:
        for fam in ('ipv4', 'ipv6'):
            try:
                n = net(lan[fam])
            except ValueError as e:
                problems.append('VLAN %s %s: %s' % (lan['vlan'], fam, e))
                continue
            parent = v4 if fam == 'ipv4' else v6
            check(n.subnet_of(parent), 'VLAN %s %s %s is not inside %s'
                  % (lan['vlan'], fam, n, parent))
            blocks.append(('VLAN %s %s' % (lan['vlan'], fam), n))
            host_lans.append(('VLAN %s' % lan['vlan'], n))

    pools = {}
    for label, key, parent in (('loopback pool v4', 'ipv4_pool', v4),
                               ('loopback pool v6', 'ipv6_pool', v6)):
        try:
            n = net(d['loopbacks'][key])
            check(n.subnet_of(parent), '%s %s is not inside %s'
                  % (label, n, parent))
            blocks.append((label, n))
            pools[key] = n
        except ValueError as e:
            problems.append('%s: %s' % (label, e))

    # Every device loopback: canonical, a host route, inside its own pool, and
    # outside every host LAN. The earlier version checked the pools and ignored
    # the assignments, so a loopback in 192.0.2.0/24 passed.
    for name, a in sorted(d['loopbacks'].items()):
        if name in ('ipv4_pool', 'ipv6_pool'):
            continue
        for fam, key, want in (('ipv4', 'ipv4_pool', 32),
                               ('ipv6', 'ipv6_pool', 128)):
            try:
                n = net(a[fam])
            except (ValueError, KeyError, TypeError) as e:
                problems.append('%s %s loopback: %s' % (name, fam, e))
                continue
            check(n.prefixlen == want,
                  '%s %s loopback %s is not a /%d host route'
                  % (name, fam, n, want))
            if key in pools:
                check(n.subnet_of(pools[key]),
                      '%s %s loopback %s is not inside its pool %s'
                      % (name, fam, n, pools[key]))
            for lan_label, lan_net in host_lans:
                if lan_net.version == n.version and lan_net.overlaps(n):
                    problems.append('%s %s loopback %s sits inside host %s (%s)'
                                    % (name, fam, n, lan_label, lan_net))

    for fam, parent in (('ipv4', v4), ('ipv6', v6)):
        for s in d['spare'][fam]:
            try:
                n = net(s)
                check(n.subnet_of(parent), 'spare %s is not inside %s'
                      % (n, parent))
                blocks.append(('spare %s' % n, n))
            except ValueError as e:
                problems.append('spare %s: %s' % (s, e))

    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            (la, a), (lb_, b) = blocks[i], blocks[j]
            if a.version == b.version and a.overlaps(b):
                problems.append('%s (%s) overlaps %s (%s)' % (la, a, lb_, b))

    for lan in d['lans']:
        if not lan.get('dhcp4'):
            continue
        try:
            lo, hi = (ip.ip_address(x) for x in lan['dhcp4'].split('-'))
        except ValueError as e:
            problems.append('VLAN %s DHCP range %r: %s'
                            % (lan['vlan'], lan['dhcp4'], e))
            continue
        n = ip.ip_network(lan['ipv4'], strict=False)
        check(lo in n and hi in n, 'VLAN %s DHCP range %s is not inside %s'
              % (lan['vlan'], lan['dhcp4'], n))
        check(lo < hi, 'VLAN %s DHCP range is inverted' % lan['vlan'])
        check(lo != n.network_address and hi != n.broadcast_address,
              'VLAN %s DHCP range includes the network or broadcast address'
              % lan['vlan'])

    return v4, v6, problems, len(blocks)


# ------------------------------------------------------------------------ main
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    write = '--write' in argv
    only_emit = '--emit' in argv
    for a in argv:
        if a not in ('--write', '--emit'):
            print('unrecognised argument: %s' % a)
            return 2

    d = json.load(open(SOURCE, encoding='utf-8'))
    block = emit(d)
    if only_emit:
        print(block)
        return 0

    v4, v6, problems, nblocks = validate(d)
    if v4 is None:
        for p in problems:
            print('    %s' % p)
        return 2

    # --- job 2: the document is generated, so regenerate and compare ---
    doc_state = 'checked'
    if not os.path.exists(DOC):
        problems.append('BRANCH-COMPLETE.md not found beside this program')
        doc_state = 'absent'
    else:
        text = open(DOC, encoding='utf-8').read()
        spliced = splice(text, block)
        if spliced is None:
            problems.append('BRANCH-COMPLETE.md has no generated-block markers; '
                            'the table cannot be checked against the source')
            doc_state = 'unmarked'
        elif write:
            if spliced != text:
                open(DOC, 'w', encoding='utf-8').write(spliced)
                print('BRANCH-COMPLETE.md: generated block rewritten from %s'
                      % os.path.basename(SOURCE))
            else:
                print('BRANCH-COMPLETE.md: generated block already current')
        elif spliced != text:
            want = block.splitlines()
            have = text[text.find(BEGIN) + len(BEGIN):text.find(END)]
            have = have.strip('\n').splitlines()
            problems.append('the generated block in BRANCH-COMPLETE.md does '
                            'not match the source. Run --write to regenerate '
                            'it, or fix branch-hgt.json.')
            import difflib
            for line in list(difflib.unified_diff(
                    have, want, 'BRANCH-COMPLETE.md', 'generated from JSON',
                    lineterm='', n=0))[:24]:
                problems.append('  %s' % line)

    print('%d LANs, %d device loopbacks, %d spare blocks, %d blocks checked '
          'for overlap, against %s / %s'
          % (len(d['lans']),
             len([k for k in d['loopbacks'] if not k.endswith('_pool')]),
             len(d['spare']['ipv4']) + len(d['spare']['ipv6']),
             nblocks, v4, v6))
    if problems:
        for p in problems:
            print('    %s' % p)
        print('\n%d problem(s).' % len(problems))
        return 2
    print('PLAN:     canonical, contained, disjoint; DHCP ranges inside their '
          'own subnets; loopbacks inside their pool and outside every host LAN.')
    if doc_state == 'checked' and not write:
        print('DOCUMENT: the generated block in BRANCH-COMPLETE.md is '
              'byte-identical to the block generated from branch-hgt.json.')
        print('          Prose outside that block is not generated and is not '
              'checked here.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
