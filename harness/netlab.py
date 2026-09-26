#!/usr/bin/env python3
"""Bring up a small routed topology in containers, configure it, and record
exactly what the devices said.

This exists so that a configuration printed in a book can carry a citation to
a transcript rather than to the author's memory. It does three things and
refuses to imply a fourth:

  * it starts one container per node and wires them with veth pairs;
  * it applies configuration through the node's own CLI;
  * it captures named commands and writes a hashed evidence record.

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
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
NETNS = '/var/run/netns'
CONFIG_RECORDS = []


def sh(argv, check=True, timeout=180):
    r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode:
        raise RuntimeError('%s -> %d\n%s%s' % (' '.join(argv), r.returncode,
                                               r.stdout, r.stderr))
    return r


def load(path):
    text = Path(path).read_text(encoding='utf-8')
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
    # Refuse to replace a pre-existing container, even if its name matches.
    for n in topo['nodes']:
        c = node_name(topo, n)
        if sh(['docker', 'inspect', c], check=False).returncode == 0:
            raise RuntimeError('container already exists: ' + c)
    topo['_owned'] = []
    topo['_host_veth'] = []
    for n, spec in topo['nodes'].items():
        c = node_name(topo, n)
        sh(['docker', 'run', '-d', '--name', c, '--privileged', '--network', 'none',
            '--label', 'rtn.proof=' + topo['name'], spec['image'], 'sleep', 'infinity'])
        topo['_owned'].append(n)
        pid = sh(['docker', 'inspect', '-f', '{{.State.Pid}}', c]).stdout.strip()
        link = os.path.join(NETNS, c)
        if os.path.islink(link) or os.path.exists(link):
            os.remove(link)
        os.symlink('/proc/%s/ns/net' % pid, link)
        sh(['ip', 'netns', 'exec', c, 'ip', 'link', 'set', 'lo', 'up'])
        # Docker's --network none does not enable forwarding. Set it inside
        # each router namespace, never in the host namespace.
        r = sh(['docker', 'exec', c, 'sysctl', '-w', 'net.ipv4.ip_forward=1'])
        CONFIG_RECORDS.append({'node': n, 'commands': ['sysctl -w net.ipv4.ip_forward=1'],
                               'returncode': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr})

    for i, ln in enumerate(topo.get('links', [])):
        (an, ai), (bn, bi) = [x.split(':') for x in ln['endpoints']]
        a, b = node_name(topo, an), node_name(topo, bn)
        stem = hashlib.sha256(topo['name'].encode()).hexdigest()[:6]
        ta, tb = 'rt%s%da' % (stem, i), 'rt%s%db' % (stem, i)
        sh(['ip', 'link', 'add', ta, 'type', 'veth', 'peer', 'name', tb])
        topo['_host_veth'].extend([ta, tb])
        sh(['ip', 'link', 'set', ta, 'netns', a])
        sh(['ip', 'link', 'set', tb, 'netns', b])
        for ns, tmp, want in ((a, ta, ai), (b, tb, bi)):
            sh(['ip', 'netns', 'exec', ns, 'ip', 'link', 'set', tmp, 'name', want])
            sh(['ip', 'netns', 'exec', ns, 'ip', 'link', 'set', want, 'up'])

    for n, spec in topo['nodes'].items():
        c = node_name(topo, n)
        for cmd in spec.get('pre', []):
            r = sh(['docker', 'exec', c, 'sh', '-c', cmd], check=False)
            CONFIG_RECORDS.append({'node': n, 'phase': 'pre', 'commands': [cmd],
                                   'returncode': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr})
            if r.returncode:
                raise RuntimeError('%s: pre-command failed: %s\n%s%s'
                                   % (n, cmd, r.stdout, r.stderr))
        daemons = spec.get('daemons', [])
        if daemons:
            expr = ';'.join("s/^%s=no/%s=yes/" % (d, d) for d in daemons)
            cmd = ("sed -i '%s' /etc/frr/daemons && touch /etc/frr/vtysh.conf && "
                   "chown frr:frr /etc/frr/vtysh.conf && /usr/lib/frr/frrinit.sh start" % expr)
            r = sh(['docker', 'exec', c, 'sh', '-c', cmd], check=False)
            CONFIG_RECORDS.append({'node': n, 'phase': 'daemon-start', 'commands': [cmd],
                                   'returncode': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr})
            if r.returncode:
                raise RuntimeError('%s: daemon startup failed: %s%s' % (n, r.stdout, r.stderr))
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
        CONFIG_RECORDS.append({'node': n, 'commands': lines, 'returncode': r.returncode,
                               'stdout': r.stdout, 'stderr': r.stderr})
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
    # During run, delete only containers this invocation created. Standalone
    # down also requires our exact ownership label; never remove by name alone.
    for n in topo.get('_owned', topo['nodes']):
        c = node_name(topo, n)
        owned = sh(['docker', 'inspect', '-f',
                    '{{index .Config.Labels "rtn.proof"}}', c], check=False)
        if owned.returncode or owned.stdout.strip() != topo['name']:
            continue
        sh(['docker', 'rm', '-f', c], check=False, timeout=60)
        link = os.path.join(NETNS, c)
        if os.path.islink(link):
            os.remove(link)
    # Only this invocation's successfully created endpoints can be removed.
    # A deterministic name alone is not proof of ownership after setup fails.
    for endpoint in topo.get('_host_veth', []):
        sh(['ip', 'link', 'del', endpoint], check=False)
    print('down: owned resources removed')


def validate_capture(cap, result):
    """Validate observation before content. Unknown is a failed observation."""
    body = result.stdout + result.stderr
    reasons = []
    if result.returncode not in cap.get('returncodes', [0]):
        reasons.append('unexpected exit status')
    if not body.strip():
        reasons.append('empty observation')
    if re.search(r'unknown command|invalid input|incomplete command|ambiguous command|'
                 r'permission denied|command not found|failed to connect|cannot connect|'
                 r"can't connect", body, re.I):
        reasons.append('command/transport error')
    if cap.get('cli', 'vtysh') == 'vtysh':
        for line in body.splitlines():
            if line.lstrip().startswith('%') and not any(
                re.fullmatch(pattern, line.strip()) for pattern in cap.get('allow_messages', [])
            ):
                reasons.append('CLI error: ' + line.strip())
    for pattern in cap.get('require', []):
        if not re.search(pattern, body):
            reasons.append('missing response structure: ' + pattern)
    if '(?!' in cap.get('expect', '') and not cap.get('require'):
        reasons.append('negative assertion has no response contract')
    if 'packet_loss' in cap:
        samples = re.findall(r'(?<![\d.])(\d+(?:\.\d+)?)% packet loss', body)
        if len(samples) != 1 or float(samples[0]) != cap['packet_loss']:
            reasons.append('packet loss absent, ambiguous or unexpected')
    if 'expect' in cap:
        # Also defend old topologies that still use the common ping pattern.
        pattern = cap['expect'].replace('0% packet loss', r'(?<![\d.])0% packet loss')
        if not re.search(pattern, body):
            reasons.append('content expectation not met')
    return reasons


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
        'schema_version': 2,
        'hash_contract': 'UTF-8 encoding of stored output, with exact stored newlines; not a signature',
        'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'topology_sha256': hashlib.sha256(json.dumps({k:v for k,v in topo.items() if not k.startswith('_')},
                            sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'topology_definition': {k:v for k,v in topo.items() if not k.startswith('_')},
        'configuration': list(CONFIG_RECORDS),
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
            'output': body,
            'stdout': r.stdout,
            'stderr': r.stderr,
            'sha256': hashlib.sha256(body.encode()).hexdigest(),
        }
        entry['validation_errors'] = validate_capture(cap, r)
        entry['matched'] = not entry['validation_errors']
        entry['contract'] = cap
        if entry['validation_errors']:
            failed += 1
        rec['captures'].append(entry)
    rec['captures_total'] = len(rec['captures'])
    rec['captures_failed'] = failed
    os.makedirs(os.path.dirname(os.path.abspath(outfile)), exist_ok=True)
    body = json.dumps(rec, indent=2, sort_keys=True)
    Path(outfile).write_text(body + '\n', encoding='utf-8')
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
    CONFIG_RECORDS.clear()
    topo['_owned'] = []
    try:
        up(topo)
        configure(topo)
        return capture(topo, a.out or 'evidence.json', a.wait)
    finally:
        if not a.keep:
            original = sys.exc_info()[0]
            try:
                down(topo)
            except Exception as error:
                if original is None:
                    raise
                print('cleanup also failed: ' + str(error), file=sys.stderr)


if __name__ == '__main__':
    raise SystemExit(main())
