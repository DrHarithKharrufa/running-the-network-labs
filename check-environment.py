#!/usr/bin/env python3
"""Report which labs this machine can run. Changes nothing.

    python3 check-environment.py
    python3 check-environment.py --chapter 64
"""
import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LABS = os.path.join(HERE, 'labs')


def have_module(name):
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def have_binary(name):
    return shutil.which(name) is not None


def docker_usable():
    if not have_binary('docker'):
        return False, 'not installed'
    try:
        r = subprocess.run(['docker', 'info'], capture_output=True, timeout=15)
        return (r.returncode == 0,
                'installed and running' if r.returncode == 0
                else 'installed, but the daemon did not answer')
    except Exception:
        return False, 'installed, but did not respond'


def lab_needs(path):
    """What a lab directory requires, from what it actually contains."""
    needs = set()
    for dp, dn, fn in os.walk(path):
        for f in fn:
            if f.endswith('.clab.yml'):
                needs |= {'linux', 'docker', 'containerlab'}
            elif f.endswith('.sh'):
                needs.add('linux')
            elif f.endswith('.py'):
                needs.add('python')
        for f in fn:
            if f == 'requirements.txt':
                try:
                    for line in open(os.path.join(dp, f), encoding='utf-8'):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            needs.add('pip:' + line.split('=')[0].split('>')[0]
                                      .split('<')[0].split('[')[0].strip())
                except Exception:
                    pass
    return needs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chapter', type=int, help='report on one chapter only')
    ap.add_argument('--json', action='store_true', help='machine-readable output')
    args = ap.parse_args()

    is_linux = platform.system() == 'Linux'
    docker_ok, docker_why = docker_usable()
    clab_ok = have_binary('containerlab') or have_binary('clab')
    env = {
        'python': '%d.%d.%d' % sys.version_info[:3],
        'python_ok': sys.version_info >= (3, 10),
        'platform': platform.platform(),
        'linux': is_linux,
        'root': hasattr(os, 'geteuid') and os.geteuid() == 0,
        'docker': docker_ok, 'docker_detail': docker_why,
        'containerlab': clab_ok,
    }

    if not os.path.isdir(LABS):
        print('No labs/ directory here. Run this from the repository root.')
        return 2

    results = {}
    for name in sorted(os.listdir(LABS)):
        d = os.path.join(LABS, name)
        if not os.path.isdir(d):
            continue
        if args.chapter is not None and name != 'lab%02d' % args.chapter:
            continue
        needs = lab_needs(d)
        missing = []
        if 'linux' in needs and not is_linux:
            missing.append('Linux')
        if 'docker' in needs and not docker_ok:
            missing.append('Docker')
        if 'containerlab' in needs and not clab_ok:
            missing.append('Containerlab')
        for n in sorted(x for x in needs if x.startswith('pip:')):
            mod = n[4:].replace('-', '_').lower()
            alias = {'pyyaml': 'yaml', 'netmiko': 'netmiko', 'jinja2': 'jinja2'}.get(mod, mod)
            if not have_module(alias):
                missing.append('python package ' + n[4:])
        results[name] = missing

    if args.json:
        print(json.dumps({'environment': env, 'labs': results}, indent=2))
        return 0

    print('Running the Network — environment check')
    print('=' * 52)
    print('  Python        %s  %s' % (env['python'],
          'ok' if env['python_ok'] else 'TOO OLD, 3.10 or newer needed'))
    print('  Platform      %s' % env['platform'])
    print('  Linux         %s' % ('yes' if is_linux else
          'no — Python labs still run; namespace and Containerlab labs need a Linux host'))
    print('  Docker        %s' % docker_why)
    print('  Containerlab  %s' % ('found' if clab_ok else 'not installed'))
    print()
    ready = [k for k, v in results.items() if not v]
    blocked = {k: v for k, v in results.items() if v}
    print('  %d of %d labs run on this machine right now.' % (len(ready), len(results)))
    if blocked:
        print()
        print('  The rest need something installed:')
        by_need = {}
        for lab, miss in blocked.items():
            by_need.setdefault(', '.join(miss), []).append(lab)
        for need, labs in sorted(by_need.items(), key=lambda kv: -len(kv[1])):
            shown = ' '.join(sorted(labs)[:10])
            more = '' if len(labs) <= 10 else ' (+%d more)' % (len(labs) - 10)
            print('    %-44s %s%s' % (need, shown, more))
    print()
    print('  Nothing was installed or changed. See INDEX.md for what each lab does.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
