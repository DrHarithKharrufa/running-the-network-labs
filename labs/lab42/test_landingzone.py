#!/usr/bin/env python3
"""Checks for landingzone.py --- the plan reader, not a cloud.

The previous script analysed two hard-coded dictionaries, so nothing a reader
supplied could change its answer. These checks feed it plans it has never seen
and require the findings to follow the input: change one prefix and the error
must appear or disappear.

They also pin the claim the chapter now makes in print --- that a subnet cannot
be resized, so its sizing is one of the decisions that is expensive to get
wrong.

No cloud account and no API call.

    python3 test_landingzone.py
"""
import contextlib
import copy
import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import landingzone as lz  # noqa: E402

FAILS = []
COUNT = 0


def check(name, cond, detail=''):
    global COUNT
    COUNT += 1
    detail = str(detail) if detail not in ('', None) else ''
    suffix = ('  [' + detail + ']') if detail else ''
    if cond:
        print('ok    ' + name + suffix)
    else:
        FAILS.append(name + suffix)
        print('FAIL  ' + name + suffix)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


def errs(a):
    return [f['issue'] for f in a['errors']]


def where(a, sev=None):
    return [f['where'] for f in a['findings']
            if sev is None or f['severity'] == sev]


# ---- the shipped plans are a worked before and after ----------------------
draft = lz.analyse(lz.PLAN)
fixed = lz.analyse(lz.FIXED)
check('the shipped draft fails', len(draft['errors']) > 0, len(draft['errors']))
check('the shipped revision passes clean',
      not fixed['errors'] and not fixed['warnings'],
      (errs(fixed), fixed['warnings']))
check('the revision is not simply the draft', lz.PLAN != lz.FIXED)

# ---- 1. overlap, and it must follow the input -----------------------------
ok = {'dc': '10.10.0.0/16', 'vpc': '10.20.0.0/16'}
clash = {'dc': '10.10.0.0/16', 'vpc': '10.10.0.0/16'}
inside = {'dc': '10.10.0.0/16', 'vpc': '10.10.1.0/24'}
check('non-overlapping ranges raise nothing', not lz.analyse(ok)['findings'])
check('identical ranges are an error', len(lz.analyse(clash)['errors']) == 1)
check('a contained range is an error too',
      len(lz.analyse(inside)['errors']) == 1)
check('...and the message names both ranges',
      '10.10.0.0/16' in errs(lz.analyse(inside))[0]
      and '10.10.1.0/24' in errs(lz.analyse(inside))[0])
check('changing one prefix removes the error --- the input is really read',
      not lz.analyse({'dc': '10.10.0.0/16', 'vpc': '10.30.0.0/16'})['errors'])

# ---- 2. ranges something else already uses --------------------------------
for cidr, word in (('172.17.0.0/16', 'Docker'),
                   ('169.254.0.0/16', 'metadata'),
                   ('100.64.0.0/10', 'carrier-grade')):
    a = lz.analyse({'dc': '10.10.0.0/16', 'vpc': cidr})
    check('%s collides with a range already in use' % cidr,
          any(word in e for e in errs(a)), errs(a)[:1])
check('a range not on the list is fine',
      not lz.analyse({'dc': '10.10.0.0/16', 'vpc': '10.90.0.0/16'})['errors'])
check('the reserved list is not empty', len(lz.RESERVED) >= 4)

# ---- 3. subnet sizing, the claim the chapter makes in print ---------------
too_small = {'vpc': {'cidr': '10.20.0.0/16', 'growth': 2.0,
                     'subnets': {'a': {'hosts': 100, 'prefix': 25}}}}
a = lz.analyse(too_small)
check('a prefix too small for the stated growth is an error',
      len(a['errors']) == 1, errs(a))
check('...and the message says a subnet cannot be resized',
      'CANNOT be resized' in errs(a)[0])
check('...and it recommends the prefix that would work',
      '/24' in errs(a)[0], errs(a)[0][-60:])

right = copy.deepcopy(too_small)
right['vpc']['subnets']['a']['prefix'] = 24
check('the recommended prefix passes', not lz.analyse(right)['errors'])

check('lowering the growth also fixes it --- both inputs are used',
      not lz.analyse({'vpc': {'cidr': '10.20.0.0/16', 'growth': 1.0,
                              'subnets': {'a': {'hosts': 100,
                                                'prefix': 25}}}})['errors'])

waste = {'vpc': {'cidr': '10.20.0.0/8' if False else '10.0.0.0/8',
                 'growth': 1.0,
                 'subnets': {'a': {'hosts': 10, 'prefix': 16}}}}
check('a wildly oversized subnet is a warning, not silence',
      any('Oversizing' in f['issue'] for f in lz.analyse(waste)['warnings']),
      [f['issue'][:40] for f in lz.analyse(waste)['findings']])

check('the platform reservation is counted, not ignored',
      len(lz.analyse({'vpc': {'cidr': '10.20.0.0/16', 'growth': 1.0,
                              'subnets': {'a': {'hosts': 32,
                                                'prefix': 27}}}})['errors']) == 1)

# a host count without a prefix is allocated, not checked
alloc = lz.analyse({'vpc': {'cidr': '10.20.0.0/16', 'growth': 2.0,
                            'subnets': {'a': 100}}})
check('a subnet given only a host count is allocated a prefix',
      alloc['allocation'].get('vpc/a') == '/24', alloc['allocation'])
check('...and raises no error, because nothing was claimed',
      not alloc['errors'])

# ---- 4. the VPC must hold its subnets -------------------------------------
cramped = {'vpc': {'cidr': '10.20.0.0/24', 'growth': 1.0,
                   'subnets': {'a': {'hosts': 100, 'prefix': 25},
                               'b': {'hosts': 100, 'prefix': 25},
                               'c': {'hosts': 100, 'prefix': 25}}}}
a = lz.analyse(cramped)
check('subnets that do not fit the VPC are an error',
      any('holds' in e and 'need' in e for e in errs(a)), errs(a))
check('...and the message says the primary range cannot be enlarged',
      any('enlarge the primary' in e for e in errs(a)))

# 128 + 64 + 32 = 224 of a /24's 256, which is past three-quarters
tight = {'vpc': {'cidr': '10.20.0.0/24', 'growth': 1.0,
                 'subnets': {'a': {'hosts': 100, 'prefix': 25},
                             'b': {'hosts': 50, 'prefix': 26},
                             'c': {'hosts': 20, 'prefix': 27}}}}
check('a VPC filled past three-quarters is a warning',
      any('little room' in f['issue'] for f in lz.analyse(tight)['warnings']),
      [f['issue'][:40] for f in lz.analyse(tight)['findings']])

# ---- 5. zones vs subnet count ---------------------------------------------
lopsided = {'vpc': {'cidr': '10.20.0.0/16', 'zones': 3, 'growth': 1.0,
                    'subnets': {'a': {'hosts': 10, 'prefix': 27},
                                'b': {'hosts': 10, 'prefix': 27}}}}
check('three zones with two subnets is flagged',
      any('not a multi-zone design' in f['issue']
          for f in lz.analyse(lopsided)['warnings']))
even = copy.deepcopy(lopsided)
even['vpc']['subnets']['c'] = {'hosts': 10, 'prefix': 27}
check('...and adding the third subnet clears it',
      not lz.analyse(even)['warnings'], lz.analyse(even)['warnings'])
check('the warning says the model differs by provider',
      any('which model your provider' in f['issue']
          for f in lz.analyse(lopsided)['warnings']))

# ---- 6. estate-level exhaustion -------------------------------------------
greedy = {'a': '10.0.0.0/9', 'b': '10.128.0.0/10'}
check('committing most of a private range is a warning',
      any('has to come from somewhere' in f['issue']
          for f in lz.analyse(greedy)['warnings']),
      [f['where'] for f in lz.analyse(greedy)['findings']])
check('a modest plan is not', not lz.analyse(
    {'a': '10.10.0.0/16', 'b': '10.20.0.0/16'})['warnings'])

# ---- rejection -------------------------------------------------------------
for plan, word in (
        ({}, 'non-empty'),
        ('not a plan', 'non-empty'),
        ({'a': {'zones': 1}}, 'no cidr'),
        ({'a': '10.10.0.1/16'}, 'host bits'),
        ({'a': 'nonsense'}, 'does not appear'),
        ({'a': {'cidr': '10.0.0.0/8', 'zones': 0}}, 'at least 1'),
        ({'a': {'cidr': '10.0.0.0/8', 'growth': 0}}, 'growth must be positive'),
        ({'a': {'cidr': '10.0.0.0/8', 'subnets': []}}, 'mapping'),
        ({'a': {'cidr': '10.0.0.0/8', 'subnets': {'s': 0}}}, 'positive integer'),
        ({'a': {'cidr': '10.0.0.0/8', 'subnets': {'s': 'big'}}}, 'expected a host count'),
        ({'a': {'cidr': '10.0.0.0/8', 'subnets': {'s': {'prefix': 24}}}}, 'host count'),
        ({'a': {'cidr': '10.0.0.0/8',
                'subnets': {'s': {'hosts': 4, 'prefix': 99}}}}, 'not a usable prefix')):
    try:
        lz.analyse(plan)
        check('rejects %.50r' % (plan,), False, 'no exception')
    except lz.PlanError as e:
        check('rejects %.50r' % (plan,), word in str(e), str(e)[:70])

# ---- the report and exit code ---------------------------------------------
_r, out = quiet(lz.report, 'draft', lz.PLAN)
check('the report prints each network', '10.10.0.0/16' in out)
check('the report prints findings', 'ERROR' in out)
_r2, out2 = quiet(lz.report, 'fixed', lz.FIXED)
check('a clean plan says so', 'no findings' in out2)
rc, out3 = quiet(lz.main, [])
check('the script exits 0 when the REVISION is clean', rc == 0, rc)
check('...and says the draft was meant to fail',
      'does not pass' in out3)
rc2, _o = quiet(lz.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
