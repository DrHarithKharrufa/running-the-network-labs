#!/usr/bin/env python3
"""Run every test program in the repository and summarise.

    python3 run-all-tests.py            # all of them
    python3 run-all-tests.py --quick    # skip anything that needs Docker
"""
import argparse, collections, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
LABS = os.path.join(HERE, 'labs')

ap = argparse.ArgumentParser()
ap.add_argument('--quick', action='store_true')
ap.add_argument('--timeout', type=int, default=300)
args = ap.parse_args()

tests = sorted(os.path.join(dp, f)
               for dp, dn, fn in os.walk(LABS)
               for f in fn if f.startswith('test_') and f.endswith('.py'))
if not tests:
    sys.exit('No test programs found. Run this from the repository root.')

res = collections.OrderedDict()
started = time.time()
for t in tests:
    rel = os.path.relpath(t, HERE)
    if args.quick and any(f.endswith('.clab.yml') for f in os.listdir(os.path.dirname(t))):
        res[rel] = ('skipped', 'needs Docker')
        continue
    try:
        r = subprocess.run([sys.executable, os.path.basename(t)],
                           cwd=os.path.dirname(t), capture_output=True,
                           text=True, timeout=args.timeout)
        out = ((r.stderr or '') + (r.stdout or '')).strip().splitlines()
        res[rel] = ('pass' if r.returncode == 0 else 'FAIL',
                    out[-1][:90] if out else '')
    except subprocess.TimeoutExpired:
        res[rel] = ('FAIL', 'exceeded %ds' % args.timeout)
    except Exception as e:
        res[rel] = ('FAIL', str(e)[:90])

c = collections.Counter(v[0] for v in res.values())
print('%d programs in %.1fs: %s' % (len(res), time.time() - started, dict(c)))
bad = [(k, v) for k, v in res.items() if v[0] == 'FAIL']
if bad:
    print('\nnot passing:')
    for k, v in bad:
        print('  %-52s %s' % (k, v[1]))
    print('\nIf one of these fails on your machine but you have the prerequisites,')
    print('please open an issue with the output. See README.md.')
sys.exit(1 if bad else 0)
