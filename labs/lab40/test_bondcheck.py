#!/usr/bin/env python3
"""Checks for bondcheck.py --- that it validates rather than assumes.

The previous version treated every string that was not "802.3ad" as a valid
static mode, said every mismatch merely "half-works", and compared a host MTU
against a switch MTU as if they measured the same thing. These checks exist to
stop each of those coming back.

This executes no network device and creates no bond.

    python3 test_bondcheck.py
"""
import io
import contextlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bondcheck as bc  # noqa: E402

FAILS = []
COUNT = 0


def check(name, cond, detail=''):
    global COUNT
    COUNT += 1
    detail = str(detail) if detail else ''
    suffix = ('  [' + detail + ']') if detail else ''
    if not cond:
        FAILS.append(name + suffix)
        print('FAIL  ' + name + suffix)
    else:
        print('ok    ' + name)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


def srv(**kw):
    d = dict(mode='802.3ad', members=2, mtu_ip=1500)
    d.update(kw)
    return d


def sw(**kw):
    d = dict(lag='lacp', mtu_frame=1518)
    d.update(kw)
    return d


def sev(r, s):
    return [f for f in r['findings'] if f['severity'] == s]


# ---- the central correction: unknown input is REJECTED, not assumed --------
for bad in ('lacp-active', 'static', 'LACP', '802.3AD', 'mode4', '', None, 4):
    try:
        bc.analyse(srv(mode=bad), sw())
        check('rejects bonding mode %r' % (bad,), False, 'accepted it')
    except bc.BondError as e:
        check('rejects bonding mode %r' % (bad,), 'unknown bonding mode' in str(e))
for bad in ('port-channel', 'LACP', 'trunk', None, 1):
    try:
        bc.analyse(srv(), sw(lag=bad))
        check('rejects switch side %r' % (bad,), False, 'accepted it')
    except bc.BondError as e:
        check('rejects switch side %r' % (bad,), 'unknown switch side' in str(e))
try:
    bc.analyse(srv(xmit_hash_policy='layer4'), sw())
    check('rejects an unknown xmit_hash_policy', False, 'accepted it')
except bc.BondError as e:
    check('rejects an unknown xmit_hash_policy', 'xmit_hash_policy' in str(e))

# ---- all seven real modes are known, with their numbers --------------------
check('all seven Linux bonding modes are known', len(bc.MODES) == 7, sorted(bc.MODES))
check('mode numbers are 0 to 6',
      sorted(n for n, _, _ in bc.MODES.values()) == list(range(7)))
check('802.3ad is mode 4 and needs lacp', bc.MODES['802.3ad'][:2] == (4, 'lacp'))
check('active-backup needs NO switch aggregation',
      bc.MODES['active-backup'][1] == 'none')
check('balance-xor needs a switch LAG', bc.MODES['balance-xor'][1] == 'switch-lag')

# ---- agreement and disagreement ------------------------------------------
r = bc.analyse(srv(), sw())
check('LACP against LACP raises no error', not sev(r, 'error'), sev(r, 'error'))
check('...but still says agreement of intent is not a working bond',
      any('not a working bond' in o for f in r['findings'] for o in f['outcomes']))

r = bc.analyse(srv(), sw(lag='access'))
check('LACP against unaggregated ports is an ERROR', sev(r, 'error'))
check('...and offers more than one possible outcome, not one prediction',
      len(sev(r, 'error')[0]['outcomes']) >= 3, len(sev(r, 'error')[0]['outcomes']))
check('...including that it may forward nothing at all',
      any('forward nothing' in o for o in sev(r, 'error')[0]['outcomes']))
check('...and names what to look at on the kit',
      sev(r, 'error')[0]['what_to_look_at'])

r = bc.analyse(srv(mode='balance-xor'), sw(lag='lacp'))
check('a static host mode against an LACP switch is raised', sev(r, 'warning') or sev(r, 'error'))
r = bc.analyse(srv(mode='active-backup'), sw(lag='static'))
check('active-backup against an aggregated switch is an ERROR', sev(r, 'error'))
r = bc.analyse(srv(mode='active-backup'), sw(lag='access'))
check('active-backup against independent ports raises no error',
      not sev(r, 'error'), sev(r, 'error'))

# ---- per-flow hashing is stated, not assumed away -------------------------
r = bc.analyse(srv(), sw())
check('a multi-member hashing bond warns that one flow is not faster',
      any('does not make one flow faster' in f['issue'] for f in r['findings']))
check('...and says the two sides hash independently',
      any('need not match' in o for f in r['findings'] for o in f['outcomes']))
r = bc.analyse(srv(mode='active-backup'), sw(lag='access'))
check('active-backup gets no per-flow hashing finding',
      not any('one flow faster' in f['issue'] for f in r['findings']))

# ---- MTU units are the correction, not a plain comparison ------------------
r = bc.analyse(srv(mtu_ip=9000), sw(mtu_frame=9000))
check('equal NUMBERS are still an error, because they measure different things',
      sev(r, 'error') and '9018' in sev(r, 'error')[0]['issue'],
      sev(r, 'error')[0]['issue'] if sev(r, 'error') else 'no error raised')
r = bc.analyse(srv(mtu_ip=9000), sw(mtu_frame=9216))
check('a switch frame with room for the header is fine', not sev(r, 'error'))
r = bc.analyse(srv(mtu_ip=9000), sw(mtu_frame=9000), l2_header=0)
check('the header allowance is a parameter, not a constant',
      not sev(r, 'error'), 'l2_header=0 makes 9000 vs 9000 fit')
check('the assumed header size is reported in the result',
      bc.analyse(srv(), sw())['l2_header_bytes_assumed'] == 18)

for bad in (0, 67, 70000, '9000', None, 1500.0):
    try:
        bc.analyse(srv(mtu_ip=bad), sw())
        check('rejects host MTU %r' % (bad,), False, 'accepted it')
    except bc.BondError as e:
        check('rejects host MTU %r' % (bad,), 'mtu_ip' in str(e))
for bad in (0, -2, '2', None):
    try:
        bc.analyse(srv(members=bad), sw())
        check('rejects member count %r' % (bad,), False, 'accepted it')
    except bc.BondError as e:
        check('rejects member count %r' % (bad,), 'members' in str(e))

# ---- the honesty guarantees ------------------------------------------------
r = bc.analyse(srv(), sw())
check('the result declares it is not a running bond',
      'Not a running bond' in r['scope'])
check('the docstring says nothing in the book demonstrates LACP state',
      'demonstrates LACP actor and partner state' in bc.__doc__)
check('the docstring names all three previous errors',
      'passed silently as "static"' in bc.__doc__
      and 'half-works' in bc.__doc__ and 'do not' in bc.__doc__)
rc, out = quiet(bc.main, [])
check('the CLI exits 0', rc == 0, rc)
check('the CLI shows a rejection, not a silent pass',
      'REJECTED' in out and 'unknown bonding mode' in out)
check('the CLI closes by telling the reader to confirm on the kit',
      'before you believe any of it' in out)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
