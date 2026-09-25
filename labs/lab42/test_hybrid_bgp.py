#!/usr/bin/env python3
"""Checks for hybrid_bgp.py --- the route exchange, not a network.

The central check is the one the chapter now makes in print: local-preference
decides between routes FOR THE SAME PREFIX, and forwarding then takes the
longest match, so a more-specific on the backup path wins regardless of how the
preference is set. If a future edit makes best-path compare across prefixes,
these fail.

No router, no cloud account, no BGP session, no packet.

    python3 test_hybrid_bgp.py
"""
import contextlib
import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import hybrid_bgp as hb  # noqa: E402

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


# ---- THE LESSON: preference decides per prefix; forwarding takes the longest -
e = hb.Edge()
e.dc_advertise('10.10.0.0/16', 'circuit', local_pref=200)
e.dc_advertise('10.10.0.0/16', 'vpn', local_pref=50)
r = e.evaluate()
check('for one prefix, the higher preference wins',
      r['table']['10.10.0.0/16']['via'] == 'circuit')
check('...and the loser is recorded, not discarded silently',
      [x['via'] for x in r['table']['10.10.0.0/16']['rejected']] == ['vpn'])
check('a clean design raises no findings', not r['findings'], r['findings'])
check('traffic follows the preferred path',
      hb.lookup(r['table'], '10.10.1.5')['via'] == 'circuit')

e2 = hb.Edge()
e2.dc_advertise('10.10.0.0/16', 'circuit', local_pref=200)
e2.dc_advertise('10.10.1.0/24', 'vpn', local_pref=50)
r2 = e2.evaluate()
check('a more-specific on the WORSE path still wins the forwarding decision',
      hb.lookup(r2['table'], '10.10.1.5')['via'] == 'vpn',
      hb.lookup(r2['table'], '10.10.1.5')['via'])
check('...even though its local-preference is a quarter of the other\'s',
      hb.lookup(r2['table'], '10.10.1.5')['local_pref'] == 50)
check('...while an address outside it still takes the circuit',
      hb.lookup(r2['table'], '10.10.9.5')['via'] == 'circuit')
check('...and the model REPORTS it rather than leaving you to notice',
      any(f['severity'] == 'error' and 'longest match' in f['issue']
          for f in r2['findings']),
      [f['issue'][:50] for f in r2['findings']])
check('the report names both the specific and the summary',
      any('10.10.1.0/24' in f['issue'] and '10.10.0.0/16' in f['issue']
          for f in r2['findings']))

# raising the preference does NOT fix it --- the point of the whole lab
e3 = hb.Edge()
e3.dc_advertise('10.10.0.0/16', 'circuit', local_pref=4000)
e3.dc_advertise('10.10.1.0/24', 'vpn', local_pref=1)
r3 = e3.evaluate()
check('raising the circuit preference to 4000 changes nothing',
      hb.lookup(r3['table'], '10.10.1.5')['via'] == 'vpn')
check('removing the more-specific is what fixes it',
      hb.lookup(hb.Edge()
                .dc_advertise('10.10.0.0/16', 'circuit', local_pref=200)
                .dc_advertise('10.10.0.0/16', 'vpn', local_pref=50)
                .evaluate()['table'], '10.10.1.5')['via'] == 'circuit')

# ---- AS-path breaks a preference tie, and only then ------------------------
e4 = hb.Edge()
e4.dc_advertise('10.10.0.0/16', 'long', local_pref=100, as_path=(1, 1, 1))
e4.dc_advertise('10.10.0.0/16', 'short', local_pref=100, as_path=(1,))
check('on equal preference the shorter AS-path wins',
      e4.evaluate()['table']['10.10.0.0/16']['via'] == 'short')
e5 = hb.Edge()
e5.dc_advertise('10.10.0.0/16', 'long', local_pref=200, as_path=(1, 1, 1))
e5.dc_advertise('10.10.0.0/16', 'short', local_pref=100, as_path=(1,))
check('...but preference is checked first',
      e5.evaluate()['table']['10.10.0.0/16']['via'] == 'long')

# ---- failure ---------------------------------------------------------------
e6 = hb.aldergate(summary_only=True)
r6 = e6.evaluate(fail=('circuit',))
check('with the circuit down the VPN carries the prefix',
      r6['table']['10.10.0.0/16']['via'] == 'vpn')
check('...and everything is still reachable',
      hb.lookup(r6['table'], '10.10.1.5') is not None)
r7 = e6.evaluate(fail=('circuit', 'vpn'))
check('with both down nothing reaches the cloud', not r7['table'])
check('...and that is reported as an error',
      any('every path is down' in f['issue'] for f in r7['findings']))

# ---- the prefix limit drops the session; it does not trim ------------------
e8 = hb.Edge(accept_limit=3)
for i in range(5):
    e8.dc_advertise('10.10.%d.0/24' % i, 'circuit', local_pref=200)
r8 = e8.evaluate()
check('exceeding the accept limit is an error', r8['over_limit'])
check('...and the consequence modelled is TOTAL loss, not a trimmed table',
      not r8['table'], sorted(r8['table']))
check('...with the count and the limit both named',
      any('5 prefixes against a limit of 3' in f['issue']
          for f in r8['findings']))
e9 = hb.Edge(accept_limit=5)
for i in range(5):
    e9.dc_advertise('10.10.%d.0/24' % i, 'circuit', local_pref=200)
check('exactly at the limit is fine', not e9.evaluate()['over_limit'])

# ---- advertising a supernet of the cloud's own range -----------------------
e10 = hb.Edge()
e10.dc_advertise('10.0.0.0/8', 'circuit', local_pref=200)
e10.cloud_advertise('10.20.0.0/16', 'vpc-hub')
r10 = e10.evaluate()
check('a supernet swallowing the cloud range is flagged',
      any(f['severity'] == 'warning' and '10.20.0.0/16' in f['issue']
          for f in r10['findings']),
      [f['issue'][:60] for f in r10['findings']])
e11 = hb.Edge()
e11.dc_advertise('10.10.0.0/16', 'circuit', local_pref=200)
e11.cloud_advertise('10.20.0.0/16', 'vpc-hub')
check('a properly scoped advertisement is not flagged',
      not e11.evaluate()['findings'])

# ---- best_path never compares across prefixes -----------------------------
table = hb.best_path([hb.route('10.1.0.0/16', 'a', 200),
                      hb.route('10.2.0.0/16', 'b', 50)])
check('two different prefixes both survive best path', len(table) == 2)
check('...each keeping its own path',
      table['10.1.0.0/16']['via'] == 'a' and table['10.2.0.0/16']['via'] == 'b')

# ---- rejection -------------------------------------------------------------
for args, word in (
        (('10.10.0.1/16', 'x'), 'not a usable prefix'),
        (('not-a-prefix', 'x'), 'not a usable prefix')):
    try:
        hb.route(*args)
        check('rejects %r' % (args,), False, 'no exception')
    except hb.EdgeError as ex:
        check('rejects %r' % (args,), word in str(ex), str(ex)[:60])
try:
    hb.route('10.0.0.0/8', 'x', local_pref=-1)
    check('rejects a negative local-preference', False, 'no exception')
except hb.EdgeError as ex:
    check('rejects a negative local-preference', 'non-negative' in str(ex))
try:
    hb.route('10.0.0.0/8', 'x', as_path='64510')
    check('rejects an AS-path given as a string', False, 'no exception')
except hb.EdgeError as ex:
    check('rejects an AS-path given as a string', 'sequence' in str(ex))
try:
    hb.Edge(dc_asn=64510, cloud_asn=64510)
    check('rejects identical ASNs on both sides', False, 'no exception')
except hb.EdgeError as ex:
    check('rejects identical ASNs on both sides', 'different ASNs' in str(ex))
try:
    hb.Edge(accept_limit=0)
    check('rejects an accept limit of zero', False, 'no exception')
except hb.EdgeError as ex:
    check('rejects an accept limit of zero', 'at least 1' in str(ex))
try:
    hb.lookup({}, 'not-an-address')
    check('rejects a malformed probe address', False, 'no exception')
except hb.EdgeError as ex:
    check('rejects a malformed probe address', 'not an address' in str(ex))
try:
    hb.best_path([])
    check('rejects an empty route set', False, 'no exception')
except hb.EdgeError as ex:
    check('rejects an empty route set', 'no routes' in str(ex))
check('a lookup that matches nothing returns None',
      hb.lookup(hb.best_path([hb.route('10.1.0.0/16', 'a')]), '192.0.2.1')
      is None)

# ---- the report states the lesson and the fix -----------------------------
_r, out = quiet(hb.report, hb.analyse())
low = ' '.join(out.lower().split())
check('the report says both sessions stay up', 'both sessions are up' in low)
check('the report names the fix as advertisement policy',
      'policy on what you advertise' in low)
check('the report disclaims being a router',
      'no router' in low and 'no bgp session' in low)
check('the report shows the same preference producing two answers',
      'in one, 10.10.1.5 takes the circuit' in low)
rc, _o = quiet(hb.main, [])
check('the script exits 0', rc == 0, rc)
rc2, _o = quiet(hb.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
