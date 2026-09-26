#!/usr/bin/env python3
"""Count what the repository actually contains, so the printed numbers cannot drift.

The book's cover said "89 laboratory exercises". There are 89 directories under
labs/, but five of them -- common, gns3, reference-designs, standards and
topologies -- are shared material, not exercises. The real figure is 84. A book
about measuring things carefully should not miscount its own labs.
"""
import os, re, json, sys

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '.'
ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
labs = os.path.join(ROOT, 'labs')

def walk(root, pred):
    n = 0
    for dp, dn, fn in os.walk(root):
        if '.git' in dp or '__pycache__' in dp:
            continue
        n += sum(1 for f in fn if pred(f))
    return n

lab_dirs = sorted(d for d in os.listdir(labs)
                  if os.path.isdir(os.path.join(labs, d)) and re.fullmatch(r'lab\d+', d))
support = sorted(d for d in os.listdir(labs)
                 if os.path.isdir(os.path.join(labs, d)) and not re.fullmatch(r'lab\d+', d))
counts = {
    'laboratory_exercises': len(lab_dirs),
    'support_directories': len(support),
    'support_names': support,
    'python_programs': walk(labs, lambda f: f.endswith('.py')),
    'test_programs': walk(labs, lambda f: f.startswith('test_') and f.endswith('.py')),
    'containerlab_topologies': walk(labs, lambda f: f.endswith('.clab.yml')),
    'harness_topologies': walk(os.path.join(ROOT, 'harness'),
                               lambda f: f.endswith('.yml')),
    'device_config_files': walk(labs, lambda f: f.endswith(('.conf', '.cfg'))),
    'evidence_records': walk(os.path.join(ROOT, 'evidence'),
                             lambda f: f.endswith('.json')),
}
print(json.dumps(counts, indent=2))
