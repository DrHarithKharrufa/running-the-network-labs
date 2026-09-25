#!/usr/bin/env python3
"""Tests for iacl_exceptions.py.

As with Lab 53.2: an unprivileged half that checks the guards, and a privileged
half that builds the real namespaces and measures. The privileged half is
SKIPPED loudly rather than faked when it cannot run.

    sudo python3 test_iacl_exceptions.py
    python3 test_iacl_exceptions.py        # unprivileged half only
"""
import ipaddress
import os
import subprocess
import sys

import iacl_exceptions as ie

CHECKS = 0
FAILED = []
SKIPPED = []


def ok(condition, label):
    global CHECKS
    CHECKS += 1
    if not condition:
        FAILED.append(label)


def raises(fn, label, fragment=None):
    global CHECKS
    CHECKS += 1
    try:
        fn()
    except ie.LabError as exc:
        if fragment and fragment not in str(exc):
            FAILED.append('%s (message lacked %r: %s)' % (label, fragment, exc))
        return
    except Exception as exc:
        FAILED.append('%s (raised %s: %s)' % (label, type(exc).__name__, exc))
        return
    FAILED.append('%s (did not raise)' % label)


# -- Unprivileged: the shape of the experiment -----------------------------

infra = [ipaddress.ip_network(n) for n in ie.INFRA]
ok(any(ipaddress.ip_address(ie.LOOPBACK) in n for n in infra),
   'the loopback IS in infrastructure space, so the blanket rule covers it')
ok(any(ipaddress.ip_address(ie.LINK_ADDR) in n for n in infra),
   'the link address IS in infrastructure space --- which is exactly why an '
   'external BGP session terminating on it is caught by the one-line rule')
ok(not any(ipaddress.ip_address(ie.FAR_ADDR) in n for n in infra),
   'the far address is outside infrastructure space')
ok(not any(ipaddress.ip_address(ie.OUTSIDER) in n for n in infra),
   'the unauthorised source is outside infrastructure space')
ok(ie.SMALL_MTU < 1500,
   'the narrow hop is narrower than the wide one, or there is no path MTU to '
   'discover')

ok(len(ie.PROBES) == 3, 'three probes')
wanted = dict(ie.PROBES)
ok(wanted['authorised peer -> tcp/179 on link address'] == ie.ALLOWED,
   'the authorised peer must get through')
ok(wanted['unauthorised source -> tcp/179'] == ie.BLOCKED,
   'the unauthorised source must not')
ok(wanted['ICMP frag-needed -> loopback (PMTUD)'] == ie.LEARNED,
   'the path MTU must be learned')

ok(len(ie.POSTURES) == 2, 'two postures')
blanket, fixed = ie.POSTURES
ok(blanket[3] == 1, 'the blanket rule is one rule')
ok(fixed[3] > blanket[3],
   'the deployable rule is the same deny with permits in front of it, so it '
   'has more rules, not fewer')
blanket_rules = [ln.strip() for ln in blanket[2].splitlines()
                 if 'counter' in ln]
ok(len(blanket_rules) == 1 and blanket_rules[0].endswith('drop'),
   'the blanket ruleset carries exactly one rule and it is a deny (the chain '
   'policy is accept, which is not a permit rule)')
ok(not any('accept' in r for r in blanket_rules),
   'the blanket ruleset permits nothing')
ok('frag-needed' in fixed[2], 'the exception list permits fragmentation-needed')
ok('time-exceeded' in fixed[2], 'the exception list permits time-exceeded')
ok('tcp dport %d' % ie.BGP_PORT in fixed[2],
   'the exception list permits the authorised peer to the routing port')
ok(fixed[2].rstrip().rindex('drop') > fixed[2].rstrip().rindex('accept'),
   'the deny is still LAST: the exceptions are in front of it, not instead '
   'of it')

for ns in ie.NAMESPACES:
    ok(ns.startswith('rtn53i'), '%s is namespaced to this lab' % ns)
ok(len(set(ie.NAMESPACES)) == 3, 'three distinct namespaces')

real_geteuid = os.geteuid
try:
    os.geteuid = lambda: 1000
    raises(ie.preflight, 'preflight refuses without root', 'will not simulate')
finally:
    os.geteuid = real_geteuid

real_which = ie.shutil.which
try:
    ie.shutil.which = lambda name: None
    raises(ie.preflight, 'preflight refuses without iproute2/nftables',
           'will not simulate')
finally:
    ie.shutil.which = real_which


# -- Privileged: the real measurement --------------------------------------

def _can_run():
    if real_geteuid() != 0:
        return 'not root'
    for tool in ('ip', 'nft'):
        if not real_which(tool):
            return 'no %s' % tool
    probe = subprocess.run(['ip', 'netns', 'add', 'rtn53iprobe'],
                           capture_output=True, stdin=subprocess.DEVNULL)
    if probe.returncode != 0:
        return 'network namespaces unavailable'
    subprocess.run(['ip', 'netns', 'del', 'rtn53iprobe'], capture_output=True,
                   stdin=subprocess.DEVNULL)
    return None


reason = _can_run()
if reason:
    SKIPPED.append('the execution half (%s) --- NOT simulated, NOT counted '
                   'as passing' % reason)
else:
    ie.build()
    try:
        results = ie.measure()
        ok(len(results) == 2, 'both postures measured')
        by = {r['posture']: {p['label']: p for p in r['probes']}
              for r in results}
        one_line = by['blanket deny to infrastructure']
        deployable = by['deny with the required exceptions']

        # The two failures this lab exists for.
        ok(one_line['authorised peer -> tcp/179 on link address']['outcome']
           == ie.BLOCKED,
           'the one-line rule BLOCKS the authorised external peer, because the '
           'session terminates on an infrastructure address')
        ok(one_line['ICMP frag-needed -> loopback (PMTUD)']['outcome']
           == ie.BLACKHOLE,
           'the one-line rule black-holes path MTU discovery for the router\'s '
           'own traffic')
        ok('mtu' not in one_line['ICMP frag-needed -> loopback (PMTUD)']
           ['route_cache'],
           'and the kernel\'s route cache proves it: no path MTU was learned')

        # It does do the job it was written for, under both postures.
        for posture, probes in by.items():
            ok(probes['unauthorised source -> tcp/179']['outcome'] == ie.BLOCKED,
               'under %s the unauthorised source is refused' % posture)

        # The exceptions fix both without weakening the deny.
        ok(deployable['authorised peer -> tcp/179 on link address']['outcome']
           == ie.ALLOWED, 'with exceptions, the authorised peer establishes')
        ok(deployable['ICMP frag-needed -> loopback (PMTUD)']['outcome']
           == ie.LEARNED, 'with exceptions, the path MTU is learned')
        ok('mtu %d' % ie.SMALL_MTU in
           deployable['ICMP frag-needed -> loopback (PMTUD)']['route_cache'],
           'and the route cache carries the narrow hop\'s MTU')
        ok(all(p['correct'] for p in deployable.values()),
           'the deployable filter gets all three probes right')
        ok(sum(1 for p in one_line.values() if not p['correct']) == 2,
           'the one-line rule gets exactly two wrong, and both are outages')

        # Both ends of the TCP probe must agree, or the probe is not measuring
        # a connection.
        for posture, probes in by.items():
            for label in ('authorised peer -> tcp/179 on link address',
                          'unauthorised source -> tcp/179'):
                p = probes[label]
                ok((p['client'] == 'ESTABLISHED') ==
                   p['router'].startswith('ACCEPTED'),
                   '%s / %s: the two ends agree' % (posture, label))

        # The guards. A ruleset that does not load must abort, because every
        # probe would then run against an open router.
        raises(lambda: ie.apply_filter('table ip rtn53iacl { nonsense }', 1),
               'a ruleset that will not parse aborts the run',
               'would have run against an OPEN router')
        raises(lambda: ie.apply_filter(ie._BLANKET, 99),
               'a ruleset with the wrong number of live rules aborts the run',
               'live ruleset')
        # And the sanity check inside measure(): if the outsider gets through,
        # the run is refused.
        real_probe = ie.probe_bgp
        try:
            ie.probe_bgp = lambda source: {'source': source,
                                           'client': 'ESTABLISHED',
                                           'router': 'ACCEPTED ' + source,
                                           'outcome': ie.ALLOWED}
            raises(ie.measure,
                   'an unauthorised source that gets through aborts the run',
                   'filter is not in force')
        finally:
            ie.probe_bgp = real_probe

        # And the PMTUD probe refuses to report if the datagram never left.
        real_run = ie._run
        try:
            def fake(argv, check=True, ns=None):
                if argv[-1] == ie._BIG_DATAGRAM:
                    return 'refused something\n'
                return real_run(argv, check=check, ns=ns)
            ie._run = fake
            raises(ie.probe_pmtud,
                   'a datagram that was not sent aborts the PMTUD probe',
                   'cannot be read')
        finally:
            ie._run = real_run
    finally:
        ie.teardown()

    listed = subprocess.run(['ip', 'netns', 'list'], capture_output=True,
                            text=True, stdin=subprocess.DEVNULL).stdout
    for ns in ie.NAMESPACES:
        ok(ns not in listed, '%s was cleaned up' % ns)


print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for s in SKIPPED:
    print('  SKIPPED: %s' % s)
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
