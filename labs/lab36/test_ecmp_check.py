#!/usr/bin/env python3
"""Checks for ecmp_check.py --- the topology reader, not the network.

The point of these checks is that the reader reports what a file SAYS, including
when the file is wrong. A checker that cannot fail on a broken topology is not a
checker. This executes no network device, no Containerlab topology and no ASIC,
and it predicts no forwarding behaviour.

    python3 test_ecmp_check.py
"""
import io
import contextlib
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import ecmp_check as ec  # noqa: E402

FAILS = []
COUNT = 0

TOPO = pathlib.Path(__file__).parent.parent / 'topologies' / 'anvil.clab.yml'


def check(name, cond, detail=''):
    global COUNT
    COUNT += 1
    if not cond:
        FAILS.append('%s%s' % (name, (' [%s]' % detail) if detail else ''))
        print('FAIL  ' + name + ((' [%s]' % detail) if detail else ''))
    else:
        print('ok    ' + name)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


def write_topo(text):
    f = tempfile.NamedTemporaryFile('w', suffix='.clab.yml', delete=False)
    f.write(text)
    f.close()
    return f.name


FULL = """
name: t
topology:
  nodes:
    sp-spine-01: { kind: nokia_srlinux }
    sp-spine-02: { kind: nokia_srlinux }
    sp-leaf-01:  { kind: nokia_srlinux }
    sp-leaf-02:  { kind: nokia_srlinux }
  links:
    - endpoints: ["sp-spine-01:e1-1", "sp-leaf-01:e1-49"]
    - endpoints: ["sp-spine-01:e1-2", "sp-leaf-02:e1-49"]
    - endpoints: ["sp-spine-02:e1-1", "sp-leaf-01:e1-50"]
    - endpoints: ["sp-spine-02:e1-2", "sp-leaf-02:e1-50"]
"""

# ---- it reads the real shipped topology -----------------------------------
nodes, links = ec.load_topology(TOPO)
spines, leaves, others = ec.classify(nodes)
check('shipped Anvil topology parses', len(nodes) == 10 and len(links) == 12,
      '%d nodes, %d links' % (len(nodes), len(links)))
check('two spines are identified', spines == ['anv-spine-01', 'anv-spine-02'], spines)
check('four leaves are identified', len(leaves) == 4, leaves)
check('four servers are not counted as fabric nodes', len(others) == 4, others)
adj = ec.adjacency(links, spines, leaves)
check('every leaf is wired to both spines',
      all(a == set(spines) for a in adj.values()),
      {k: sorted(v) for k, v in adj.items()})

r, _ = quiet(ec.report, str(TOPO), 8)
check('shipped topology reports 2 candidate paths for every pair',
      all(p['candidate_paths'] == 2 for p in r['pairs']))
check('shipped topology has six leaf pairs', len(r['pairs']) == 6, len(r['pairs']))
check('shipped topology reports no cabling gaps', r['cabling_gaps'] == [])
check('shipped topology passes at maximum-paths 8', r['ok'] is True)

# ---- the reader is not the source of the mesh -----------------------------
# The old script built the mesh it then counted. Remove a link and the count
# must drop; if it does not, the script is inventing the topology again.
broken = write_topo(FULL.replace(
    '    - endpoints: ["sp-spine-02:e1-1", "sp-leaf-01:e1-50"]\n', ''))
rb, _ = quiet(ec.report, broken, 8)
check('a removed leaf-spine link reduces the candidate path count',
      rb['fewest_candidate_paths'] == 1, rb['fewest_candidate_paths'])
check('the missing link is named in the cabling gaps',
      any('sp-leaf-01' in g and 'sp-spine-02' in g for g in rb['cabling_gaps']),
      rb['cabling_gaps'])
check('a broken topology does not report ok', rb['ok'] is False)

full = write_topo(FULL)
rf, _ = quiet(ec.report, full, 8)
check('the intact version of the same file reports 2 paths',
      rf['fewest_candidate_paths'] == 2)
check('the intact version reports no gaps', rf['cabling_gaps'] == [])

# ---- maximum-paths is compared, not assumed -------------------------------
rc_low, _ = quiet(ec.report, str(TOPO), 1)
check('maximum-paths below the candidate count is not ok', rc_low['ok'] is False,
      rc_low['maximum_paths_assumed'])
rc_eq, _ = quiet(ec.report, str(TOPO), 2)
check('maximum-paths equal to the candidate count is ok', rc_eq['ok'] is True)

# ---- a leaf wired to nothing ----------------------------------------------
no_sp = write_topo("""
name: t
topology:
  nodes:
    sp-spine-01: { kind: nokia_srlinux }
    sp-leaf-01:  { kind: nokia_srlinux }
    sp-leaf-02:  { kind: nokia_srlinux }
  links:
    - endpoints: ["sp-spine-01:e1-1", "sp-leaf-01:e1-49"]
""")
rn, _ = quiet(ec.report, no_sp, 8)
check('a leaf with no spine link yields zero candidate paths',
      rn['fewest_candidate_paths'] == 0, rn['fewest_candidate_paths'])
check('zero candidate paths is not ok', rn['ok'] is False)

# ---- both parsers agree ---------------------------------------------------
class _Block:
    def find_spec(self, name, path=None, target=None):
        if name == 'yaml':
            raise ImportError('blocked for this check')
        return None


saved = sys.modules.pop('yaml', None)
sys.meta_path.insert(0, _Block())
try:
    n2, l2 = ec.load_topology(TOPO)
finally:
    sys.meta_path.pop(0)
    if saved is not None:
        sys.modules['yaml'] = saved
check('the fallback parser finds the same links as PyYAML',
      sorted(l2) == sorted(links), '%d vs %d' % (len(l2), len(links)))
check('the fallback parser finds the same nodes as PyYAML',
      sorted(n2) == sorted(nodes), '%d vs %d' % (len(n2), len(nodes)))

# ---- input validation ------------------------------------------------------
try:
    ec.main(['--multipath', '0'])
    check('--multipath 0 is rejected', False, 'no SystemExit')
except SystemExit as e:
    check('--multipath 0 is rejected', e.code != 0, 'exit %s' % e.code)

bad = write_topo(FULL.replace('"sp-spine-01:e1-1", "sp-leaf-01:e1-49"',
                              '"sp-spine-01:e1-1"'))
try:
    ec.load_topology(bad)
    check('a one-endpoint link is rejected', False, 'no exception')
except Exception as e:
    check('a one-endpoint link is rejected', isinstance(e, ValueError), type(e).__name__)

# Exercise malformed inputs with PyYAML available AND explicitly blocked.
# Otherwise an installed dependency can hide the bare-Python failure branch.
invalid = {
    'one endpoint': FULL.replace('"sp-spine-01:e1-1", "sp-leaf-01:e1-49"', '"sp-spine-01:e1-1"'),
    'three endpoints': FULL.replace('"sp-spine-01:e1-1", "sp-leaf-01:e1-49"', '"sp-spine-01:e1-1", "sp-leaf-01:e1-49", "sp-leaf-02:e9"'),
    'unknown node': FULL.replace('sp-leaf-01:e1-49', 'absent:e1-49'),
    'missing interface': FULL.replace('sp-leaf-01:e1-49', 'sp-leaf-01:'),
    'no interface separator': FULL.replace('sp-leaf-01:e1-49', 'sp-leaf-01'),
    'reused interface': FULL.replace('sp-spine-01:e1-2', 'sp-spine-01:e1-1'),
    'self link': FULL.replace('sp-leaf-01:e1-49', 'sp-spine-01:e9'),
    'numeric endpoint': FULL.replace('"sp-leaf-01:e1-49"', '42'),
}
for forced in (False, True):
    saved = sys.modules.pop('yaml', None) if forced else None
    if forced:
        sys.meta_path.insert(0, _Block())
    try:
        for label, text in invalid.items():
            with tempfile.TemporaryDirectory() as td:
                p = pathlib.Path(td) / 'bad.yml'; p.write_text(text)
                try:
                    ec.load_topology(p)
                    check(('fallback ' if forced else 'available parser ') + label, False)
                except ValueError:
                    check(('fallback ' if forced else 'available parser ') + label, True)
    finally:
        if forced:
            sys.meta_path.pop(0)
            if saved is not None:
                sys.modules['yaml'] = saved

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
