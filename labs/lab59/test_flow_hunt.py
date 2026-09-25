#!/usr/bin/env python3
"""Tests for flow_hunt.py.

THE PROPERTY THAT MATTERS MOST: normal Windows administration must not be
reported as an attack, and nothing must be reported as confirmed. The version
this replaces did both.

    python3 test_flow_hunt.py
"""
import io
import sys

import flow_hunt as fh

CHECKS, FAILED = 0, []


def ok(c, l):
    global CHECKS
    CHECKS += 1
    if not c:
        FAILED.append(l)


def raises(fn, label, fragment=None, exc=fh.HuntError):
    global CHECKS
    CHECKS += 1
    try:
        fn()
    except exc as e:
        if fragment and fragment not in str(e):
            FAILED.append('%s (message lacked %r)' % (label, fragment))
        return
    except Exception as e:                                       # noqa: BLE001
        FAILED.append('%s (raised %s)' % (label, type(e).__name__))
        return
    FAILED.append('%s (did not raise)' % label)


# -- 1. Group policy is not lateral movement -------------------------------

res = {(c['src'], c['dst'], c['port']): c for c in fh.unexpected_internal(fh.FLOWS)}
gp = res[('10.10.1.7', '10.20.0.1', 445)]
ok(gp['verdict'] == fh.EXPECTED,
   'WORKSTATION SMB TO THE DOMAIN CONTROLLER IS EXPECTED, not an alert')
ok('SYSVOL' in gp['why'] and 'group\npolicy' in gp['why'] or 'group policy' in gp['why'],
   'and the reason names what it actually is')
ok(res[('10.10.1.9', '10.20.0.1', 445)]['verdict'] == fh.EXPECTED,
   'for every workstation, not just the one in the story')
ok(res[('10.10.1.7', '10.20.0.1', 3389)]['verdict'] == fh.CANDIDATE,
   'RDP from a workstation to a DC is a candidate, because it is not on the list')
ok(res[('10.10.1.7', '10.10.1.9', 445)]['verdict'] == fh.CANDIDATE,
   'and so is workstation-to-workstation SMB')
ok(('workstation', 'domain-controller', 445) in fh.EXPECTED_SERVICES,
   'the expected-service list says so explicitly')
ok(all(v for v in fh.EXPECTED_SERVICES.values()),
   'and every entry carries its reason, so the list can be reviewed')
cand = res[('10.10.1.7', '10.20.0.1', 3389)]
ok('nobody wrote it down' in cand['needed'],
   'a candidate says that absence from the list is not proof of wrongness')
ok('authentication logs' in cand['needed'],
   'and names the correlating evidence the flow data cannot supply')


# -- 2. Classification is by address, not by name --------------------------

ok(fh.classify('10.10.1.7')['known'] and fh.classify('10.10.1.7')['internal'],
   'an inventoried address is known and internal')
ok(fh.classify('10.10.9.99')['internal'] and not fh.classify('10.10.9.99')['known'],
   'an internal address not in the inventory is internal but unknown')
ok(not fh.classify('203.0.113.9')['internal'], 'a public address is external')
ok(fh.classify('203.0.113.9')['role'] == 'external', 'and is labelled so')
raises(lambda: fh.classify('dc-01'), 'a hostname is refused', 'not an IP address')
raises(lambda: fh.classify('dc.attacker.example'),
       'including one that would have fooled the prefix test')
unknown = [c for c in fh.unexpected_internal(fh.FLOWS) if c['verdict'] == fh.UNCLASSIFIED]
ok(len(unknown) == 1, 'the host absent from the inventory is UNCLASSIFIED')
ok('inventory finding first' in unknown[0]['needed'],
   'and is treated as an inventory problem before a security one')


# -- 3. Periodicity is reported with its number, not as a verdict ----------

p = fh.periodic_candidates(fh.FLOWS)
ok(len(p) == 1, 'one regular external conversation is found')
ok(p[0]['verdict'] == fh.CANDIDATE, 'and it is a candidate')
ok(0 < p[0]['cv'] < 0.15, 'with its coefficient of variation reported (%.3f)' % p[0]['cv'])
ok(abs(p[0]['mean_gap'] - 60) < 5, 'and the mean gap')
ok('software you bought' in p[0]['needed'],
   'AND THE WARNING THAT LEGITIMATE SOFTWARE PRODUCES THE SAME NUMBER')
big = [f for f in fh.FLOWS if f[4] > 1e8]
ok(big, 'the log contains large flows')
ok(not any(c['dst'] == '203.0.113.9' and c.get('events', 0) > 6 for c in p),
   'the large transfer to the same host does not join the periodic set')
few = fh.periodic_candidates(fh.FLOWS[:2])
ok(few == [], 'two events are not enough to call anything periodic')


# -- 4. Scoping states its own limits and never crashes --------------------

s = fh.scope(fh.FLOWS, '10.10.1.7')
ok(s['flows'] == 12, 'the host has flows')
ok(s['first_observed'] == 0, 'the first record is at t=0')
ok(s['at_window_edge'] is True, 'WHICH IS THE EDGE OF THE WINDOW, and it says so')
ok(any('not the start of anything' in lim for lim in s['limits']),
   'first_observed is explicitly not the start of the incident')
ok(any('does not classify them' in lim for lim in s['limits']),
   'the largest flow is explicitly not classified as exfiltration')
ok(any('absent by construction' in lim for lim in s['limits']),
   'and the peer list is bounded by what crossed an exporter')
missing = fh.scope(fh.FLOWS, '10.10.4.4')
ok(missing['flows'] == 0, 'A HOST WITH NO FLOWS RETURNS CLEANLY --- the version '
                          'this replaces raised ValueError from min()')
ok(missing['first_observed'] is None, 'with no invented first-seen time')
ok('not evidence the host was quiet' in missing['why'],
   'and silence is explicitly not evidence')
ok('sampling rate' in missing['why'], 'pointing at the telemetry limits')
ok(fh.scope([], 'anything')['flows'] == 0, 'an empty log is handled too')
raises(lambda: fh.scope(fh.FLOWS, '10.10.1.7', window=(600, 0)),
       'a backwards window is refused')


# -- 5. Nothing is confirmed ----------------------------------------------

# The accusing words must never appear in a verdict or its reason. They may
# appear in a LIMIT, where the point is to deny them.
verdicts = [c.get('verdict', '') + ' ' + str(c.get('why', ''))
            for c in fh.periodic_candidates(fh.FLOWS) + fh.unexpected_internal(fh.FLOWS)]
blob = ' '.join(verdicts).lower()
for banned in ('exfil', 'c2', 'compromised', 'intrusion', 'attacker', 'malicious'):
    ok(banned not in blob, 'no verdict or reason ever says %r' % banned)
lims = ' '.join(fh.scope(fh.FLOWS, '10.10.1.7')['limits']).lower()
ok('exfiltration' in lims,
   'the word appears only where the model is denying it applies')
buf = io.StringIO()
fh.report(buf)
txt = buf.getvalue()
ok('Nothing above is a confirmed intrusion' in txt, 'the report says so in words')
ok('called them lateral movement' in txt,
   'and points out the false positive the old version produced')
ok('lateral movement' not in txt.replace('called them lateral movement', ''),
   'without using the phrase as a verdict anywhere else')
_s = sys.stdout
sys.stdout = io.StringIO()
try:
    rc, rj = fh.main([]), fh.main(['--json'])
finally:
    sys.stdout = _s
ok(rc == 0 and rj == 0, 'both modes run')
ok(fh.periodic_candidates(fh.FLOWS) == fh.periodic_candidates(fh.FLOWS),
   'the analysis is deterministic')

print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
