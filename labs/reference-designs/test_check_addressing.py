#!/usr/bin/env python3
"""Negative tests for check_addressing.py. Run: python3 test_check_addressing.py

A checker that has never been shown a bad input is a checker nobody has tested.
Each case below copies the real plan and document into a temporary directory,
breaks exactly one thing, and requires the checker to fail. The last case
requires it to pass unbroken, because a checker that fails everything is no
better than one that passes everything.

Three of these cases came from an independent reviewer who corrupted the router's
loopback assignment, a printed DHCP endpoint and a printed spare block, and
found that the checker passed all three while reporting that "the document agrees
with the source". They are kept here so that cannot happen again quietly.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ('check_addressing.py', 'branch-hgt.json', 'BRANCH-COMPLETE.md')


def stage(tmp):
    d = tempfile.mkdtemp(dir=tmp)
    for f in FILES:
        shutil.copy2(os.path.join(HERE, f), d)
    return d


def run(d):
    r = subprocess.run([sys.executable, 'check_addressing.py'], cwd=d,
                       capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout + r.stderr


def edit_json(d, fn):
    p = os.path.join(d, 'branch-hgt.json')
    data = json.load(open(p, encoding='utf-8'))
    fn(data)
    json.dump(data, open(p, 'w', encoding='utf-8'), indent=2)


def edit_doc(d, old, new):
    p = os.path.join(d, 'BRANCH-COMPLETE.md')
    s = io.open(p, encoding='utf-8').read()
    if old not in s:
        raise AssertionError('test fixture is stale: %r is not in the document'
                             % old[:60])
    io.open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))


# --------------------------------------------------------------------- cases
def case_site_prefix_host_bits(d):
    """The original defect: an IPv6 site prefix with host bits set."""
    edit_json(d, lambda x: x['site_allocation'].__setitem__(
        'ipv6', '2001:db8:a1de:18::/56'))


def case_spare_inside_a_lan(d):
    """A 'spare' block that is really part of the guest subnet."""
    edit_json(d, lambda x: x['spare']['ipv4'].append('10.10.66.128/25'))


def case_site_in_londons_reservation(d):
    """Taking a site prefix out of another site's reserved growth space."""
    edit_json(d, lambda x: x['site_allocation'].__setitem__(
        'ipv4', '10.10.24.0/22'))


def case_loopback_outside_its_pool(d):
    """Reviewer case 1: the assignment, not the pool, is wrong."""
    edit_json(d, lambda x: x['loopbacks']['hgt-rtr-01'].__setitem__(
        'ipv4', '192.0.2.1/32'))


def case_loopback_inside_a_host_lan(d):
    """A loopback that is inside a LAN it should never be inside."""
    edit_json(d, lambda x: x['loopbacks']['hgt-rtr-01'].__setitem__(
        'ipv4', '10.10.64.200/32'))


def case_loopback_not_a_host_route(d):
    edit_json(d, lambda x: x['loopbacks']['hgt-rtr-01'].__setitem__(
        'ipv4', '10.10.67.32/27'))


def case_dhcp_outside_its_subnet(d):
    edit_json(d, lambda x: x['lans'][0].__setitem__(
        'dhcp4', '10.10.68.50-10.10.68.230'))


def case_dhcp_inverted(d):
    edit_json(d, lambda x: x['lans'][0].__setitem__(
        'dhcp4', '10.10.64.230-10.10.64.50'))


def case_dhcp_includes_broadcast(d):
    edit_json(d, lambda x: x['lans'][0].__setitem__(
        'dhcp4', '10.10.64.50-10.10.64.255'))


def case_printed_lan_prefix_changed(d):
    """Reviewer case: the document says one thing, the source another."""
    edit_doc(d, '| 100 | User | `10.10.64.0/24` |',
             '| 100 | User | `10.10.68.0/24` |')


def case_printed_dhcp_endpoint_invalid(d):
    """Reviewer case 2: an impossible printed DHCP endpoint."""
    edit_doc(d, '`.50`–`.230` |\n| 200 ', '`.50`–`.999` |\n| 200 ')


def case_printed_spare_overlaps_a_lan(d):
    """Reviewer case 3: the printed spare list disagrees with the source."""
    edit_doc(d, 'Genuinely spare: `10.10.65.192/26`',
             'Genuinely spare: `10.10.66.128/25`')


def case_printed_loopback_changed(d):
    edit_doc(d, '`hgt-rtr-01` is `10.10.67.32/32`',
             '`hgt-rtr-01` is `10.10.67.40/32`')


def case_markers_removed(d):
    """If the generated block is not marked, the document cannot be checked,
    and the checker must say so instead of silently checking nothing."""
    p = os.path.join(d, 'BRANCH-COMPLETE.md')
    s = io.open(p, encoding='utf-8').read()
    s = s.replace('<!-- BEGIN GENERATED addressing', '<!-- was generated')
    io.open(p, 'w', encoding='utf-8').write(s)


MUST_FAIL = [
    ('site prefix has host bits set', case_site_prefix_host_bits),
    ('a spare block sits inside a LAN', case_spare_inside_a_lan),
    ("site taken from another site's reservation", case_site_in_londons_reservation),
    ('router loopback outside its pool and site', case_loopback_outside_its_pool),
    ('router loopback inside a host LAN', case_loopback_inside_a_host_lan),
    ('router loopback is not a host route', case_loopback_not_a_host_route),
    ('DHCP range outside its own subnet', case_dhcp_outside_its_subnet),
    ('DHCP range inverted', case_dhcp_inverted),
    ('DHCP range includes the broadcast address', case_dhcp_includes_broadcast),
    ('printed LAN prefix differs from the source', case_printed_lan_prefix_changed),
    ('printed DHCP endpoint is impossible', case_printed_dhcp_endpoint_invalid),
    ('printed spare list differs from the source', case_printed_spare_overlaps_a_lan),
    ('printed loopback differs from the source', case_printed_loopback_changed),
    ('generated-block markers removed', case_markers_removed),
]


def main():
    tmp = tempfile.mkdtemp(prefix='rtn-addr-test-')
    failures = []
    try:
        d = stage(tmp)
        rc, out = run(d)
        if rc != 0:
            failures.append('the unbroken plan does not pass: rc=%d\n%s'
                            % (rc, out))
        else:
            print('  ok    unbroken plan passes')

        for name, breaker in MUST_FAIL:
            d = stage(tmp)
            breaker(d)
            rc, out = run(d)
            if rc == 0:
                failures.append('NOT DETECTED: %s\n%s' % (name, out))
                print('  FAIL  %s' % name)
            else:
                print('  ok    rejected: %s' % name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print('\n%d case(s), %d failure(s)' % (len(MUST_FAIL) + 1, len(failures)))
    for f in failures:
        print('\n%s' % f)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
