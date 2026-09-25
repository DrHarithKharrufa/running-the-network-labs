#!/usr/bin/env python3
"""Tests for urpf_modes.py.

Two halves. The first runs without privilege and checks the parts of the lab
that decide whether a result may be reported at all. The second needs root,
builds the real namespaces and checks the measured matrix --- and is SKIPPED,
loudly, rather than faked, when it cannot run.

    sudo python3 test_urpf_modes.py
    python3 test_urpf_modes.py        # runs the unprivileged half only
"""
import os
import subprocess
import sys

import urpf_modes as um

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
    except um.LabError as exc:
        if fragment and fragment not in str(exc):
            FAILED.append('%s (message lacked %r: %s)' % (label, fragment, exc))
        return
    except Exception as exc:
        FAILED.append('%s (raised %s: %s)' % (label, type(exc).__name__, exc))
        return
    FAILED.append('%s (did not raise)' % label)


# -- Unprivileged: the shape of the experiment -----------------------------

ok(len(um.CLASSES) == 4, 'four traffic classes')
labels = [c[0] for c in um.CLASSES]
ok(len(set(labels)) == 4, 'the class labels are distinct')
expected = {label: exp for label, _s, _d, _n, exp in um.CLASSES}
ok(expected['legitimate symmetric'] == um.PASS,
   'the customer\'s own address on the symmetric link must be delivered')
ok(expected['legitimate ASYMMETRIC'] == um.PASS,
   'the customer\'s own address on the other link must also be delivered --- '
   'it is theirs whichever link it arrives on')
ok(expected['SPOOFED but routed'] == um.DROP,
   'an address the customer does not own must be dropped even though it is '
   'routed')
ok(expected['unrouted source'] == um.DROP, 'an unrouted source must be dropped')

# The spoofed source must genuinely be routed, or the test is not testing what
# it says: loose uRPF would drop it for the wrong reason.
ok(um.SPOOF_ROUTED.startswith('10.99.'),
   'the spoofed-but-routed source is from the prefix the router has a route for')
ok(not um.SPOOF_ROUTED.startswith('10.20.'),
   'the spoofed source is NOT inside the customer allocation')
ok(not um.SPOOF_UNROUTED.startswith(('10.20.', '10.99.')),
   'the unrouted source is in neither routed prefix')
ok(um.LEGIT.startswith('10.20.'),
   'the legitimate source IS inside the customer allocation')

ok(len(um.POSTURES) == 4, 'four postures')
ok([p[0] for p in um.POSTURES][0] == 'no validation',
   'the control case runs first, so a broken topology is caught before any '
   'drop is reported')

# Namespace names are specific to this lab, so it cannot delete somebody
# else's namespaces on teardown.
for ns in um.NAMESPACES:
    ok(ns.startswith('rtn53u'), '%s is namespaced to this lab' % ns)
ok(len(set(um.NAMESPACES)) == 3, 'three distinct namespaces')

# preflight must refuse rather than simulate.
real_geteuid = os.geteuid
try:
    os.geteuid = lambda: 1000
    raises(um.preflight, 'preflight refuses without root', 'will not simulate')
finally:
    os.geteuid = real_geteuid

real_which = um.shutil.which
try:
    um.shutil.which = lambda name: None
    raises(um.preflight, 'preflight refuses without iproute2/nftables',
           'will not simulate')
finally:
    um.shutil.which = real_which

# _run must raise on a failing command rather than returning empty output that
# a later check would read as "nothing there".
raises(lambda: um._run(['false']), 'a failing command raises')
ok(um._run(['true']) == '', 'a succeeding command returns its output')


# -- Privileged: the real measurement --------------------------------------

def _can_run():
    if real_geteuid() != 0:
        return 'not root'
    for tool in ('ip', 'nft'):
        if not real_which(tool):
            return 'no %s' % tool
    probe = subprocess.run(['ip', 'netns', 'add', 'rtn53probe'],
                           capture_output=True, stdin=subprocess.DEVNULL)
    if probe.returncode != 0:
        return 'network namespaces unavailable'
    subprocess.run(['ip', 'netns', 'del', 'rtn53probe'], capture_output=True,
                   stdin=subprocess.DEVNULL)
    return None


reason = _can_run()
if reason:
    SKIPPED.append('the execution half (%s) --- NOT simulated, NOT counted '
                   'as passing' % reason)
else:
    um.build()
    try:
        # The ingress counters must be live; without them a non-delivery could
        # not be told from a packet that never left the customer.
        counters = um._counters()
        ok(set(counters) == {'link-a', 'link-b'},
           'both ingress counters are live before any trial')
        um._verify_counters_present()
        CHECKS += 1

        results = um.measure()
        ok(len(results) == 4, 'four postures measured')
        by = {r['posture']: {c['label']: c for c in r['classes']}
              for r in results}

        # Every trial must have reached the router, or its outcome means
        # nothing at all.
        for posture, classes in by.items():
            for label, c in classes.items():
                ok(c['sent'] == um.PROBES,
                   '%s / %s: all probes were sent' % (posture, label))
                ok(c['arrived_at_router'] > 0,
                   '%s / %s: the probes reached the router, so its outcome is '
                   'about filtering' % (posture, label))

        # The control case.
        for label in (c[0] for c in um.CLASSES):
            ok(by['no validation'][label]['outcome'] == um.PASS,
               'with no validation, %s is delivered' % label)

        # The two findings this lab exists for.
        ok(by['uRPF strict']['legitimate ASYMMETRIC']['outcome'] == um.DROP,
           'strict uRPF DROPS the customer\'s own address arriving on the link '
           'the best route does not point at')
        ok(by['uRPF strict']['legitimate symmetric']['outcome'] == um.PASS,
           'strict uRPF passes the same address on the symmetric link, so the '
           'drop above is about the path and not the address')
        ok(by['uRPF loose']['SPOOFED but routed']['outcome'] == um.PASS,
           'loose uRPF DELIVERS a spoofed source that has a route: '
           'reachability is not authorisation')
        ok(by['uRPF loose']['unrouted source']['outcome'] == um.DROP,
           'loose uRPF does drop a source with no route at all, which is the '
           'only thing it actually checks')

        # And the posture that gets it right.
        for label in (c[0] for c in um.CLASSES):
            c = by['per-customer prefix filter'][label]
            ok(c['correct'],
               'the per-customer prefix filter handles %s correctly' % label)

        correct = {p: sum(1 for c in cs.values() if c['correct'])
                   for p, cs in by.items()}
        ok(correct['per-customer prefix filter'] == 4,
           'the prefix filter is the only posture with all four right')
        ok(correct['uRPF strict'] < 4, 'strict uRPF is not all four')
        ok(correct['uRPF loose'] < 4, 'loose uRPF is not all four')

        # The delivered datagrams carried the source we sent, so the counting
        # is of the right packets.
        c = by['uRPF loose']['SPOOFED but routed']
        ok(c['sources_seen'] == [um.SPOOF_ROUTED],
           'the far namespace saw the spoofed source itself, not something else')

        # The guards. A control case that does not deliver must abort the run
        # rather than be reported as filtering.
        real_trial = um.trial
        try:
            um.trial = lambda *a, **k: {'sent': um.PROBES,
                                        'arrived_at_router': 3,
                                        'delivered': 0, 'sources_seen': []}
            raises(um.measure,
                   'a control case that delivers nothing aborts the run',
                   'control case must deliver everything')
            um.trial = lambda *a, **k: {'sent': um.PROBES,
                                        'arrived_at_router': 0,
                                        'delivered': 0, 'sources_seen': []}
            raises(um.measure,
                   'a probe that never reached the router aborts the run',
                   'fabricated result')
            um.trial = lambda *a, **k: {'sent': 1, 'arrived_at_router': 1,
                                        'delivered': 1, 'sources_seen': []}
            raises(um.measure, 'a short send aborts the run', 'cannot be read')
        finally:
            um.trial = real_trial

        # A posture whose sysctl did not take must be refused.
        real_run = um._run
        try:
            def fake(argv, check=True, ns=None):
                if argv[:2] == ['sysctl', '-n']:
                    return '9\n'
                return real_run(argv, check=check, ns=ns)
            um._run = fake
            raises(lambda: um.apply_posture('uRPF strict'),
                   'a posture the kernel did not accept is refused',
                   'kernel reports')
        finally:
            um._run = real_run

        # The counter guard fires when the table is gone.
        subprocess.run(['ip', 'netns', 'exec', um.RTR, 'nft', 'delete', 'table',
                        'ip', 'rtn53count'], capture_output=True,
                       stdin=subprocess.DEVNULL)
        raises(um._verify_counters_present,
               'a missing ingress counter is refused',
               'cannot be told from a packet that never left')
    finally:
        um.teardown()

    # Teardown really removes them.
    listed = subprocess.run(['ip', 'netns', 'list'], capture_output=True,
                            text=True, stdin=subprocess.DEVNULL).stdout
    for ns in um.NAMESPACES:
        ok(ns not in listed, '%s was cleaned up' % ns)


print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for s in SKIPPED:
    print('  SKIPPED: %s' % s)
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
