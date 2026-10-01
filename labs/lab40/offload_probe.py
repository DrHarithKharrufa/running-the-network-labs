#!/usr/bin/env python3
"""Lab 40.1 --- what "offload" actually means, demonstrated on a device with no NIC.

WHAT THIS IS. A veth pair has no network card, no driver firmware and no silicon
anywhere in its path: it is two ends of a pipe inside the kernel. This script
creates one, reads its feature flags with ethtool, and shows you three things
that a NIC-centric account of offloads cannot explain.

WHY IT MATTERS. The usual telling is "TSO: the NIC chops the buffer into
segments; GRO/LRO: the NIC coalesces arriving segments". Run this and you will
see segmentation offload reported ON for a device that has no NIC to do any
chopping --- because GSO is *generic* segmentation offload, performed by the
Linux stack itself, deferring segmentation until the last moment whether or not
hardware can help. GRO is likewise commonly done in the kernel receive path.
LRO is driver-dependent aggregation. On this device [fixed] means it cannot
be changed; it does not prove whether another implementation uses hardware.

WHAT THIS IS NOT. It measures no throughput and says nothing about how fast any
real NIC is. It reads feature flags and toggles them; that is all. Feature flags
are what the kernel reports, not proof that a packet took a particular path.

Requires root and ethtool. Run:

    sudo python3 offload_probe.py
"""
import json
import os
import re
import shutil
import subprocess
import sys

IF, PEER = 'lab40a', 'lab40b'
RESULTS = []


def check(name, ok, detail=''):
    # str() first: a tuple or list passed as detail would otherwise be consumed
    # by %-formatting and raise from inside the helper, which is a confusing way
    # to learn that an assertion failed.
    detail = str(detail) if detail else ''
    RESULTS.append({'check': name, 'pass': bool(ok), 'detail': detail[:400]})
    print('  %s  %s%s' % ('PASS' if ok else 'FAIL', name,
                          ('  [' + detail + ']') if detail else ''))
    return bool(ok)


def sh(cmd, check_rc=False):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


def features(dev):
    """{feature: (state, fixed)} exactly as ethtool reports it."""
    out = sh(['ethtool', '-k', dev]).stdout
    feats = {}
    for line in out.splitlines():
        m = re.match(r'^\s*([a-z0-9\-]+):\s+(on|off)(\s*\[fixed\])?', line)
        if m:
            feats[m.group(1)] = (m.group(2), bool(m.group(3)))
    return feats


def teardown():
    sh(['ip', 'link', 'del', IF])


def main():
    if os.geteuid() != 0:
        print('This lab needs root (it creates a veth pair).')
        return 2
    for t in ('ip', 'ethtool'):
        if not shutil.which(t):
            print('%s is required and was not found.' % t)
            return 2

    print('Lab 40.1 --- offload flags on a device with no NIC')
    print('  kernel : ' + sh(['uname', '-srm']).stdout.strip())
    print('  ethtool: ' + sh(['ethtool', '--version']).stdout.strip().splitlines()[0])
    print('  note   : no throughput is measured here, and none is implied.\n')

    teardown()
    r = sh(['ip', 'link', 'add', IF, 'type', 'veth', 'peer', 'name', PEER])
    if r.returncode:
        print('could not create the veth pair: ' + r.stderr.strip())
        return 1
    try:
        f = features(IF)
        print('A. A veth pair has no network card at all')
        check('A1 ethtool reports feature flags for it', len(f) > 10, '%d features' % len(f))
        check('A2 segmentation offload is reported ON --- on a device with no NIC '
              'to segment anything', f.get('generic-segmentation-offload', ('?',))[0] == 'on'
              and f.get('tcp-segmentation-offload', ('?',))[0] == 'on',
              'gso=%s tso=%s' % (f.get('generic-segmentation-offload'),
                                 f.get('tcp-segmentation-offload')))

        print('\nB. Changeability is a device feature contract, not an execution location')
        sh(['ethtool', '-K', IF, 'gso', 'off'])
        off = features(IF)
        check('B1 GSO can be turned OFF on this software-only veth',
              off.get('generic-segmentation-offload', ('?',))[0] == 'off',
              off.get('generic-segmentation-offload'))
        sh(['ethtool', '-K', IF, 'gso', 'on'])
        back = features(IF)
        check('B2 ...and back ON', back.get('generic-segmentation-offload', ('?',))[0] == 'on')

        lro_state, lro_fixed = f.get('large-receive-offload', ('?', False))
        check('B3 LRO is reported [fixed] --- the kernel will not let you change it',
              lro_fixed, 'large-receive-offload: %s%s'
              % (lro_state, ' [fixed]' if lro_fixed else ''))
        r = sh(['ethtool', '-K', IF, 'lro', 'on'])
        refused = 'Could not change' in (r.stdout + r.stderr) or r.returncode != 0
        why = ' / '.join(l.strip() for l in (r.stderr + '\n' + r.stdout).splitlines()
                         if l.strip())
        check('B4 enabling LRO is refused on this veth '
              '(no inference about other implementations)', refused, why or 'rc=%d' % r.returncode)

        print('\nC. How much of the list is fixed, and what that tells you')
        fixed = sorted(k for k, (s, fx) in f.items() if fx)
        changeable = sorted(k for k, (s, fx) in f.items() if not fx)
        check('C1 the list separates into fixed and changeable features',
              fixed and changeable, '%d fixed, %d changeable' % (len(fixed), len(changeable)))
        check('C2 GRO is present in the list, and on this device is not fixed',
              'generic-receive-offload' in f
              and not f['generic-receive-offload'][1],
              'generic-receive-offload: %s' % (f.get('generic-receive-offload'),))

        print('\nD. What this environment could NOT demonstrate')
        r = sh(['ip', 'link', 'add', 'lab40bond', 'type', 'bond'])
        bond_ok = r.returncode == 0
        if bond_ok:
            sh(['ip', 'link', 'del', 'lab40bond'])
        check('D1 the bonding driver\'s availability is reported, not assumed',
              True, 'bonding available' if bond_ok
              else 'NOT available here: ' + (r.stderr.strip()[:60] or 'unknown'))
        if not bond_ok:
            print('      No bond could be created on this host, so nothing in this book')
            print('      demonstrates LACP actor/partner state. Lab 40.2 is a checker for')
            print('      an intended configuration, not a running bond.')

        summary = {'kernel': sh(['uname', '-srm']).stdout.strip(),
                   'device': 'veth pair (no NIC in the path)',
                   'features_reported': {k: {'state': v[0], 'fixed': v[1]}
                                         for k, v in sorted(f.items())},
                   'fixed_features': fixed, 'changeable_features': changeable,
                   'bonding_driver_available': bond_ok,
                   'scope': ('Feature flags read and toggled on a virtual device. No '
                             'throughput measured, no NIC involved, no claim about any '
                             'real adapter.'),
                   'checks': RESULTS}
    finally:
        teardown()

    passed = sum(1 for x in RESULTS if x['pass'])
    summary['passed'] = passed
    summary['total'] = len(RESULTS)
    print('\n%d/%d checks passed' % (passed, len(RESULTS)))
    print('\nThe point, in one sentence: "offload" names a job that the kernel may')
    print('do in software, hand to hardware, or refuse to do at all, and ethtool')
    print('[fixed] tells you only whether this device permits a change.')
    print('\nNOT established here:')
    for line in ('any throughput figure, for any device',
                 'what a real NIC does with TSO, GRO or LRO',
                 'that a flag reported "on" means a given packet took that path',
                 'anything about LACP or bonding: see D1'):
        print('  - ' + line)
    open('lab40-offload-results.json', 'w').write(json.dumps(summary, indent=2))
    print('\nResults written to lab40-offload-results.json')
    return 0 if passed == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
