#!/usr/bin/env python3
"""Lab 39.2 --- XDP, actually compiled, verified, attached and dropping.

WHAT THIS IS. A real eBPF/XDP program, built with clang, loaded through libbpf,
rejected or accepted by the kernel verifier, attached to a veth interface, and
then shown dropping the packets it was told to drop and passing the ones it was
not. Every number below is a counter read out of a BPF map after real traffic.

WHAT THIS IS NOT, and this matters more than usual here. It measures NO
throughput and reports NO packets-per-second figure. It runs in GENERIC (SKB)
mode on a veth pair, which is the slowest of the three XDP modes and the least
like a NIC. Any rate measured in this setup would say something about veth and
about generic mode, and nothing about what XDP does on a real NIC in native
driver mode. A lab that cannot measure a thing should not print a number for it.

The three modes, since the lab depends on the distinction:

  generic / SKB   runs after the kernel has allocated an skb. Works anywhere,
                  including here. Slowest.
  native / driver runs in the driver's receive path before the skb. Needs
                  driver support. This is what people mean by "XDP is fast".
  offload         runs on the NIC itself. Needs specific hardware and firmware.

Requires root, clang, gcc, libbpf-dev and iproute2. Run:

    sudo python3 xdp_lab.py
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
BUILD = pathlib.Path('/tmp/lab39-build')
IF, PEER, NS = 'lab39a', 'lab39b', 'lab39peer'
HOST_IP, PEER_IP = '10.99.39.1', '10.99.39.2'

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append({'check': name, 'pass': bool(ok), 'detail': str(detail)[:400]})
    print('  %s  %s%s' % ('PASS' if ok else 'FAIL', name,
                          ('  [%s]' % detail) if detail else ''))
    return bool(ok)


def sh(cmd, check_rc=True, ns=None, timeout=120, env=None):
    if ns:
        cmd = ['ip', 'netns', 'exec', ns] + cmd
    e = dict(os.environ)
    if env:
        e.update(env)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=e)
    if check_rc and r.returncode:
        raise RuntimeError('%s -> rc=%d\n%s\n%s'
                           % (' '.join(cmd), r.returncode, r.stdout[-1200:], r.stderr[-1200:]))
    return r


def arch_include():
    for c in ('/usr/include/x86_64-linux-gnu', '/usr/include/aarch64-linux-gnu'):
        if pathlib.Path(c, 'asm').exists():
            return c
    return None


def compile_bpf(src, out):
    inc = arch_include()
    cmd = ['clang', '-O2', '-g', '-target', 'bpf']
    if inc:
        cmd += ['-I' + inc]
    cmd += ['-c', str(src), '-o', str(out)]
    return sh(cmd, check_rc=False)


def teardown():
    sh(['ip', 'link', 'set', 'dev', IF, 'xdpgeneric', 'off'], check_rc=False)
    sh(['ip', 'link', 'del', IF], check_rc=False)
    sh(['ip', 'netns', 'del', NS], check_rc=False)


def setup():
    teardown()
    sh(['ip', 'netns', 'add', NS])
    sh(['ip', 'link', 'add', IF, 'type', 'veth', 'peer', 'name', PEER])
    sh(['ip', 'link', 'set', PEER, 'netns', NS])
    sh(['ip', 'addr', 'add', HOST_IP + '/24', 'dev', IF])
    sh(['ip', 'link', 'set', IF, 'up'])
    sh(['ip', 'addr', 'add', PEER_IP + '/24', 'dev', PEER], ns=NS)
    sh(['ip', 'link', 'set', PEER, 'up'], ns=NS)
    sh(['ip', 'link', 'set', 'lo', 'up'], ns=NS)


def run_loader(obj, block=None, hold=6, ping=3):
    """Attach, generate traffic from the peer side, read the counters."""
    cmd = [str(BUILD / 'loader'), str(obj), IF] + ([block] if block else [])
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, env=dict(os.environ, HOLD=str(hold)))
    time.sleep(1.5)
    # Ping the peer: the REPLIES arrive on IF, which is where XDP runs.
    ping_ok = subprocess.run(['ping', '-c', str(ping), '-W', '1', PEER_IP],
                             capture_output=True, text=True).returncode == 0
    out = p.communicate(timeout=hold + 30)[0]
    counters = {int(k): int(v) for k, v in re.findall(r'counter\[(\d+)\]=(\d+)', out)}
    return {'ping_ok': ping_ok, 'counters': counters, 'output': out}


def main():
    if os.geteuid() != 0:
        print('This lab needs root (it loads BPF and creates namespaces).')
        return 2
    for tool in ('clang', 'gcc', 'ip', 'ping'):
        if not shutil.which(tool):
            print('%s is required and was not found.' % tool)
            return 2
    if not pathlib.Path('/usr/include/bpf/libbpf.h').exists():
        print('libbpf-dev is required and was not found.')
        return 2

    print('Lab 39.2 --- XDP compiled, verified, attached and dropping')
    print('  kernel : ' + sh(['uname', '-srm']).stdout.strip())
    print('  clang  : ' + sh(['clang', '--version']).stdout.splitlines()[0].strip())
    print('  mode   : generic (SKB) on a veth pair. NO throughput is measured;')
    print('           see the module docstring for why that would be meaningless.\n')

    BUILD.mkdir(parents=True, exist_ok=True)

    print('A. Compile and verify')
    r = compile_bpf(HERE / 'xdp_drop.c', BUILD / 'xdp_drop.o')
    check('A1 the bounds-checked program compiles', r.returncode == 0,
          r.stderr.strip().splitlines()[:1])
    r = compile_bpf(HERE / 'xdp_unsafe.c', BUILD / 'xdp_unsafe.o')
    check('A2 the UNSAFE program also compiles --- clang does not catch this',
          r.returncode == 0, r.stderr.strip().splitlines()[:1])
    r = sh(['gcc', '-O2', str(HERE / 'loader.c'), '-o', str(BUILD / 'loader'),
            '-lbpf', '-lelf', '-lz'], check_rc=False)
    if not check('A3 the libbpf loader builds', r.returncode == 0,
                 r.stderr.strip().splitlines()[:2]):
        return 1

    setup()
    try:
        print('\nB. The verifier')
        r = sh([str(BUILD / 'loader'), str(BUILD / 'xdp_unsafe.o'), IF], check_rc=False)
        log = r.stdout + r.stderr
        check('B1 the kernel REJECTS the unbounded program at load time',
              r.returncode != 0 and 'load/verify FAILED' in log)
        m = re.search(r'invalid access to packet[^\n]*', log)
        check('B2 the refusal names the out-of-bounds packet access',
              m is not None, m.group(0) if m else log.strip().splitlines()[-3:])
        check('B3 ...and the bounds-checked program is accepted',
              sh([str(BUILD / 'loader'), str(BUILD / 'xdp_drop.o'), IF],
                 check_rc=False, env={'HOLD': '1'}).returncode == 0)

        print('\nC. Dropping, with the counters read back from the map')
        blocked = run_loader(BUILD / 'xdp_drop.o', block=PEER_IP, hold=6)
        c = blocked['counters']
        check('C1 with the peer blocked, the ping fails', not blocked['ping_ok'])
        check('C2 the XDP drop counter rose', c.get(0, 0) >= 1,
              'dropped=%s passed=%s malformed=%s' % (c.get(0), c.get(1), c.get(2)))
        check('C3 nothing was counted as malformed', c.get(2, 0) == 0, c.get(2))

        clean = run_loader(BUILD / 'xdp_drop.o', block=None, hold=6)
        c2 = clean['counters']
        check('C4 with an empty blocklist, the ping succeeds', clean['ping_ok'])
        check('C5 nothing was dropped', c2.get(0, 0) == 0, c2.get(0))
        check('C6 packets were seen and passed', c2.get(1, 0) >= 1,
              'passed=%s' % c2.get(1))

        print('\nD. Mode availability is a property of the driver')
        r = sh(['ip', 'link', 'set', 'dev', IF, 'xdpdrv', 'obj',
                str(BUILD / 'xdp_drop.o'), 'sec', 'xdp'], check_rc=False)
        native = r.returncode == 0
        if native:
            sh(['ip', 'link', 'set', 'dev', IF, 'xdpdrv', 'off'], check_rc=False)
        check('D1 native (driver) mode was attempted and the outcome recorded',
              True, 'veth native XDP accepted' if native
              else 'refused here: ' + (r.stderr.strip()[:90] or 'no message'))
        r = sh(['ip', 'link', 'set', 'dev', IF, 'xdpoffload', 'obj',
                str(BUILD / 'xdp_drop.o'), 'sec', 'xdp'], check_rc=False)
        # The refusal comes from map creation: offload needs device-bound maps,
        # which a veth cannot provide. Report the last line, not a truncated
        # middle one, so the reason is legible.
        why = [l for l in (r.stderr + r.stdout).strip().splitlines() if l.strip()]
        check('D2 hardware offload mode is NOT available on a veth, as expected',
              r.returncode != 0, why[-1][:110] if why else 'no message')
    finally:
        teardown()

    passed = sum(1 for x in RESULTS if x['pass'])
    print('\n%d/%d checks passed' % (passed, len(RESULTS)))
    print('\nNOT measured, and therefore not claimed:')
    for line in ('packets per second, in any mode, on anything',
                 'native driver XDP or hardware offload performance',
                 'anything about a real NIC: this ran on a veth pair',
                 'that the program is correct for VLAN-tagged, IPv6, optioned or '
                 'fragmented traffic --- it explicitly is not',
                 'that passing the verifier makes the policy right'):
        print('  - ' + line)
    out = {'kernel': sh(['uname', '-srm']).stdout.strip(),
           'clang': sh(['clang', '--version']).stdout.splitlines()[0].strip(),
           'mode': 'generic (SKB) on veth',
           'scope': ('Real compile, verify, attach and drop. No throughput measured '
                     'and no packets-per-second figure reported: generic mode on a '
                     'veth cannot produce a meaningful one.'),
           'checks': RESULTS, 'passed': passed, 'total': len(RESULTS)}
    pathlib.Path('lab39-results.json').write_text(json.dumps(out, indent=2))
    print('\nResults written to lab39-results.json')
    return 0 if passed == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
