#!/usr/bin/env python3
"""Bring up a small routed topology in containers, configure it, and record
exactly what the devices said.

This exists so that a configuration printed in a book can carry a citation to
a transcript rather than to the author's memory. It does three things and
refuses to imply a fourth:

  * it starts one container per node and wires them with veth pairs;
  * it applies configuration through the node's own CLI;
  * it captures named commands and writes a signed evidence record.

What a record from this harness establishes: that these commands were accepted
and produced this output, on this image digest, on this kernel, at this time.
What it does not establish: anything about hardware forwarding, about a vendor
NOS that was not run, about scale, or about behaviour under load. Those remain
in the categories they were already in.

    python3 harness/netlab.py up      topo.yml
    python3 harness/netlab.py capture topo.yml -o evidence/unit-ospf-p2p.json
    python3 harness/netlab.py down    topo.yml

The topology file is deliberately small; see harness/README.md.
"""
import argparse, hashlib, json, os, platform, re, subprocess, sys, time, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
NETNS = '/var/run/netns'


def sh(argv, check=True, timeout=180):
    r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode:
        raise RuntimeError('%s -> %d\n%s%s' % (' '.join(argv), r.returncode,
                                               r.stdout, r.stderr))
    return r


def load(path):
    text = open(path, encoding='utf-8').read()
    try:
        import yaml
        return yaml.safe_load(text)
    except ImportError:
        return json.loads(text)          # a .json topology needs no dependency


def docker_ok():
    try:
        sh(['docker', 'info'], timeout=30)
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------- up
def node_name(topo, n):
    return '%s-%s' % (topo.get('name', 'lab'), n)


def up(topo):
    if not docker_ok():
        sys.exit('the Docker daemon did not answer; nothing was started')
    os.makedirs(NETNS, exist_ok=True)
    for n, spec in topo['nodes'].items():
        c = node_name(topo, n)
        sh(['docker', 'rm', '-f', c], check=False, timeout=60)
        sh(['docker', 'run', '-d', '--name', c, '--privileged', '--network', 'none',
            spec['image'], 'sleep', 'infinity'])
        pid = sh(['docker', 'inspect', '-f', '{{.State.Pid}}', c]).stdout.strip()
        link = os.path.join(NETNS, c)
        if os.path.islink(link) or os.path.exists(link):
            os.remove(link)
        os.symlink('/proc/%s/ns/net' % pid, link)
        sh(['ip', 'netns', 'exec', c, 'ip', 'link', 'set', 'lo', 'up'])

    for i, ln in enumerate(topo.get('links', [])):
        (an, ai), (bn, bi) = [x.split(':') for x in ln['endpoints']]
        a, b = node_name(topo, an), node_name(topo, bn)
        ta, tb = 'h%da' % i, 'h%db' % i
        sh(['ip', 'link', 'del', ta], check=False)
        sh(['ip', 'link', 'add', ta, 'type', 'veth', 'peer', 'name', tb])
        sh(['ip', 'link', 'set', ta, 'netns', a])
        sh(['ip', 'link', 'set', tb, 'netns', b])
        for ns, tmp, want in ((a, ta, ai), (b, tb, bi)):
            sh(['ip', 'netns', 'exec', ns, 'ip', 'link', 'set', tmp, 'name', want])
            sh(['ip', 'netns', 'exec', ns, 'ip', 'link', 'set', want, 'up'])

    for n, spec in topo['nodes'].items():
        c = node_name(topo, n)
        for cmd in spec.get('pre', []):
            r = sh(['docker', 'exec', c, 'sh', '-c', cmd], check=False)
            if r.returncode:
                raise RuntimeError('%s: pre-command failed: %s\n%s%s'
                                   % (n, cmd, r.stdout, r.stderr))
        daemons = spec.get('daemons', [])
        if daemons:
            expr = ';'.join("s/^%s=no/%s=yes/" % (d, d) for d in daemons)
            sh(['docker', 'exec', c, 'sh', '-c',
                "sed -i '%s' /etc/frr/daemons && touch /etc/frr/vtysh.conf && "
                "chown frr:frr /etc/frr/vtysh.conf 2>/dev/null; "
                "/usr/lib/frr/frrinit.sh start >/dev/null 2>&1 || true" % expr])
    time.sleep(topo.get('settle', 3))
    print('up: %d nodes, %d links' % (len(topo['nodes']), len(topo.get('links', []))))


def configure(topo):
    for n, spec in topo['nodes'].items():
        c = node_name(topo, n)
        lines = spec.get('config', [])
        if not lines:
            continue
        argv = ['docker', 'exec', c, 'vtysh']
        for l in lines:
            argv += ['-c', l]
        r = sh(argv, check=False)
        if r.returncode:
            raise RuntimeError('%s rejected its configuration:\n%s%s'
                               % (n, r.stdout, r.stderr))
        # A CLI that prints an error but exits zero is the failure mode that
        # matters here, so look at the text as well as the status.
        bad = [l for l in (r.stdout + r.stderr).splitlines()
               if re.search(r'^%|unknown command|Unknown command|% Invalid', l)]
        if bad:
            raise RuntimeError('%s reported: %s' % (n, ' | '.join(bad[:4])))
    print('configured %d nodes' % len(topo['nodes']))


def down(topo):
    for n in topo['nodes']:
        c = node_name(topo, n)
        sh(['docker', 'rm', '-f', c], check=False, timeout=60)
        link = os.path.join(NETNS, c)
        if os.path.islink(link):
            os.remove(link)
    print('down: %d nodes removed' % len(topo['nodes']))


# ---------------------------------------------------------------------- capture
def image_facts(topo):
    out = {}
    for n, spec in topo['nodes'].items():
        img = spec['image']
        if img in out:
            continue
        r = sh(['docker', 'image', 'inspect', img, '-f',
                '{{index .RepoDigests 0}}|{{.Id}}|{{.Created}}'], check=False)
        d, i, cr = (r.stdout.strip().split('|') + ['', '', ''])[:3]
        out[img] = {'repo_digest': d, 'image_id': i, 'image_created': cr}
    return out


def capture(topo, outfile, wait=None):
    wait = topo.get('converge', 45) if wait is None else wait
    if wait:
        print('waiting %ds for the protocols to settle' % wait)
        time.sleep(wait)
    rec = {
        'scope': ('Commands accepted and output produced by these container '
                  'images on this kernel at this time. Not hardware execution, '
                  'not a claim about any NOS not run here, not a scale result.'),
        'harness': 'harness/netlab.py',
        'topology': topo.get('name'),
        'captured_utc': datetime.datetime.now(datetime.timezone.utc)
                        .replace(microsecond=0).isoformat(),
        'kernel': platform.platform(),
        'images': image_facts(topo),
        'captures': [],
    }
    failed = 0
    for cap in topo.get('capture', []):
        n, cmd = cap['node'], cap['cmd']
        c = node_name(topo, n)
        argv = (['docker', 'exec', c, 'vtysh', '-c', cmd] if cap.get('cli', 'vtysh') == 'vtysh'
                else ['docker', 'exec', c, 'sh', '-c', cmd])
        t0 = time.time()
        r = sh(argv, check=False, timeout=cap.get('timeout', 120))
        # Always keep both streams. An earlier version took stdout alone when
        # the command exited zero, which silently dropped 'ping: sendto:
        # Network unreachable' -- the very line a negative capture depends on.
        body = r.stdout + r.stderr
        entry = {
            'id': cap.get('id') or '%s: %s' % (n, cmd),
            'node': n, 'cli': cap.get('cli', 'vtysh'), 'cmd': cmd,
            'returncode': r.returncode,
            'elapsed_s': round(time.time() - t0, 3),
            'output': body.rstrip('\n'),
            'stdout': r.stdout.rstrip('\n'),
            'stderr': r.stderr.rstrip('\n'),
            'sha256': hashlib.sha256(body.encode()).hexdigest(),
        }
        # One capture counts once. A command that exits non-zero AND misses its
        # expectation is one failure, not two -- the first version of this
        # reported four failures for two problems.
        if 'expect' in cap:
            entry['expect'] = cap['expect']
            entry['matched'] = bool(re.search(cap['expect'], body))
        if r.returncode or entry.get('matched') is False:
            failed += 1
        rec['captures'].append(entry)
    rec['captures_total'] = len(rec['captures'])
    rec['captures_failed'] = failed
    os.makedirs(os.path.dirname(os.path.abspath(outfile)), exist_ok=True)
    body = json.dumps(rec, indent=2, sort_keys=True)
    open(outfile, 'w', encoding='utf-8').write(body + '\n')
    print('%d captures, %d did not meet their expectation -> %s'
          % (rec['captures_total'], failed, outfile))
    return 2 if failed else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['up', 'config', 'capture', 'down', 'run'])
    ap.add_argument('topology')
    ap.add_argument('-o', '--out', help='evidence record path (capture/run)')
    ap.add_argument('--wait', type=int, help='seconds to let protocols settle')
    ap.add_argument('--keep', action='store_true', help='leave the lab up after run')
    a = ap.parse_args()
    topo = load(a.topology)
    if a.action == 'up':
        up(topo); return 0
    if a.action == 'config':
        configure(topo); return 0
    if a.action == 'down':
        down(topo); return 0
    if a.action == 'capture':
        return capture(topo, a.out or 'evidence.json', a.wait)
    up(topo); configure(topo)
    try:
        return capture(topo, a.out or 'evidence.json', a.wait)
    finally:
        if not a.keep:
            down(topo)


if __name__ == '__main__':
    raise SystemExit(main())
