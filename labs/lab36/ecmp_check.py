#!/usr/bin/env python3
"""Lab 36.1 --- count the candidate paths in a topology file.

This reads ../topologies/anvil.clab.yml and counts, for each pair of leaves,
the spines that BOTH leaves are wired to. That count is the number of
*physical candidate paths* the cabling permits.

Read that sentence again, because the previous version of this script did not
do it. It built its own full mesh in a list comprehension and then counted the
mesh it had just built --- so it "proved" a property of its own source code and
would have reported a perfect fabric no matter what the topology said. This
version parses the file, so a missing link shows up as a missing path.

A candidate path count is not a forwarding outcome. Between the cabling and a
packet on the wire sit: BGP session establishment, import and export policy
(RFC 8212 specifies default rejection without explicit eBGP import/export
policy; verify the implementation and configured mode), next-hop
resolution, the multipath configuration, AS-path comparison rules, FIB capacity,
and the hash that picks a member for each flow. This script tests exactly none
of them. Lab 36.2 (underlay_lab.py) tests several of them for real.

    python3 ecmp_check.py [topology.yml] [--multipath N]
"""
import argparse
import json
import pathlib
import re
import sys

DEFAULT_TOPOLOGY = pathlib.Path(__file__).with_name('..') / 'topologies' / 'anvil.clab.yml'


def validate_topology(nodes, entries):
    """Validate the inventory graph before reducing endpoints to node names."""
    if not isinstance(nodes, dict) or not nodes:
        raise ValueError('nodes must be a non-empty mapping')
    if any(not isinstance(n, str) or not n for n in nodes):
        raise ValueError('node names must be non-empty strings')
    if not isinstance(entries, list):
        raise ValueError('links must be a list')
    links, used = [], set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('each link must be an endpoints mapping')
        eps = entry.get('endpoints')
        if not isinstance(eps, list) or len(eps) != 2:
            raise ValueError('a link must have exactly two endpoints: %r' % (eps,))
        ends = []
        for ep in eps:
            if not isinstance(ep, str) or ep.count(':') != 1:
                raise ValueError('endpoint must be node:interface: %r' % (ep,))
            node, interface = ep.split(':')
            if node not in nodes or not interface or any(c.isspace() for c in ep):
                raise ValueError('unknown node or invalid interface: %r' % (ep,))
            if ep in used:
                raise ValueError('an interface occurs on more than one link: %s' % ep)
            used.add(ep)
            ends.append(node)
        if ends[0] == ends[1]:
            raise ValueError('self-links are outside this leaf-spine model')
        links.append(tuple(ends))
    return nodes, links


def load_topology(path):
    """Return (nodes, links). Uses PyYAML when present, else a narrow parser
    for the endpoints list, so the lab runs on a bare Python install."""
    text = pathlib.Path(path).read_text()
    try:
        import yaml
        doc = yaml.safe_load(text)
        topo = doc['topology']
        return validate_topology(topo.get('nodes'), topo.get('links', []))
    except ImportError:
        pass
    nodes = {}
    entries = []
    section = None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        if s.startswith('nodes:'):
            if s != 'nodes:':
                raise ValueError('unsupported nodes syntax; install PyYAML')
            section = 'nodes'
            continue
        if s.startswith('links:'):
            if s != 'links:':
                raise ValueError('unsupported links syntax; install PyYAML')
            section = 'links'
            continue
        if section == 'nodes':
            m = re.fullmatch(r'([A-Za-z0-9_.-]+):\s*\{.*\}\s*(?:#.*)?', s)
            if not m or m.group(1) in nodes:
                raise ValueError('unsupported or duplicate node entry; install PyYAML')
            nodes[m.group(1)] = {}
        elif section == 'links':
            m = re.fullmatch(r'-\s*endpoints:\s*(\[.*\])\s*(?:#.*)?', s)
            if not m:
                raise ValueError('unsupported or malformed link; install PyYAML')
            try:
                eps = json.loads(m.group(1))
            except json.JSONDecodeError as exc:
                raise ValueError('fallback needs a double-quoted endpoint list; install PyYAML') from exc
            entries.append({'endpoints': eps})
    if section != 'links':
        raise ValueError('nodes/links sections required by fallback parser')
    return validate_topology(nodes, entries)


def classify(nodes):
    """Roles come from the inventory's own names. If a topology uses different
    names, pass them in rather than letting the script guess silently."""
    spines = sorted(n for n in nodes if 'spine' in n)
    leaves = sorted(n for n in nodes if 'leaf' in n)
    others = sorted(n for n in nodes if n not in spines and n not in leaves)
    return spines, leaves, others


def adjacency(links, spines, leaves):
    """{leaf: {spines it is wired to}} --- built from the file, not assumed."""
    adj = {l: set() for l in leaves}
    for a, b in links:
        if a in leaves and b in spines:
            adj[a].add(b)
        elif b in leaves and a in spines:
            adj[b].add(a)
    return adj


def report(path, multipath):
    nodes, links = load_topology(path)
    spines, leaves, others = classify(nodes)
    adj = adjacency(links, spines, leaves)

    print('Topology   : %s' % path)
    print('Spines     : %d  %s' % (len(spines), ', '.join(spines)))
    print('Leaves     : %d  %s' % (len(leaves), ', '.join(leaves)))
    if others:
        print('Other nodes: %d  %s' % (len(others), ', '.join(others)))
    print('Links read : %d\n' % len(links))

    findings = []
    for l in leaves:
        missing = sorted(set(spines) - adj[l])
        if missing:
            findings.append('%s is not wired to %s' % (l, ', '.join(missing)))

    pairs = []
    for i, a in enumerate(leaves):
        for b in leaves[i + 1:]:
            common = sorted(adj[a] & adj[b])
            pairs.append({'a': a, 'b': b, 'candidate_paths': len(common),
                          'via': common})
            flag = '' if len(common) == len(spines) else '   <-- fewer than the spine count'
            print('    %s <-> %s: %d candidate path(s) via %s%s'
                  % (a, b, len(common), ', '.join(common) or '(none)', flag))

    worst = min((p['candidate_paths'] for p in pairs), default=0)
    print('\nSpine count                      : %d' % len(spines))
    print('Fewest candidate paths, any pair : %d' % worst)
    print('BGP maximum-paths assumed        : %d' % multipath)

    if findings:
        print('\nCabling gaps found in the file:')
        for f in findings:
            print('  - ' + f)
    if multipath < worst:
        print('\nmaximum-paths (%d) is below the candidate path count (%d): the '
              'configuration cannot use all the cabling.' % (multipath, worst))
    elif not findings:
        print('\nEvery leaf pair has one candidate path per spine, and '
              'maximum-paths does not cap them.')

    print('\nWhat this does NOT establish: that any session is up, that policy '
          'permits the prefixes,\nthat the next hops resolve, that the FIB has '
          'room, or that a given flow uses a given\npath. Run Lab 36.2 for the '
          'parts that can actually be measured.')

    ok = (not findings) and multipath >= worst and worst > 0
    result = {'topology': str(path), 'spines': spines, 'leaves': leaves,
              'links_read': len(links), 'pairs': pairs,
              'fewest_candidate_paths': worst, 'maximum_paths_assumed': multipath,
              'cabling_gaps': findings,
              'scope': ('Physical candidate paths read from a topology file. '
                        'No protocol, policy, FIB or forwarding behaviour is tested.'),
              'ok': ok}
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('topology', nargs='?', default=str(DEFAULT_TOPOLOGY.resolve()))
    p.add_argument('--multipath', type=int, default=8,
                   help='the maximum-paths value to compare against (default 8)')
    p.add_argument('--json', action='store_true', help='print the result as JSON')
    a = p.parse_args(argv)
    if a.multipath < 1:
        p.error('--multipath must be at least 1')
    r = report(a.topology, a.multipath)
    if a.json:
        print(json.dumps(r, indent=2))
    return 0 if r['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
