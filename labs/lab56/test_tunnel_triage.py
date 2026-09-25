#!/usr/bin/env python3
"""Tests for tunnel_triage.py.

THE PROPERTY THAT MATTERS MOST: THE MODEL NEVER DECLARES HEALTH. The shipped
version returned "tunnel healthy -- traffic should pass" whenever none of its
four conditions fired, which is a false all-clear drawn from ignorance. Most of
what follows exists to make that impossible to reintroduce.

Each rule is tested twice --- once on an input that fires it, once on the
nearest input that must not --- because a check that always fires and a check
that never fires both pass a one-sided test.

    python3 test_tunnel_triage.py
"""
import io
import sys

import tunnel_triage as tt

CHECKS = 0
FAILED = []


def ok(cond, label):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


def raises(fn, label, fragment=None):
    global CHECKS
    CHECKS += 1
    try:
        fn()
    except tt.TriageError as exc:
        if fragment and fragment not in str(exc):
            FAILED.append('%s (message lacked %r: %s)' % (label, fragment, exc))
        return
    except Exception as exc:                                     # noqa: BLE001
        FAILED.append('%s (raised %s, not TriageError)' % (label, type(exc).__name__))
        return
    FAILED.append('%s (did not raise)' % label)


def fired(res, rule_id):
    return any(f['id'] == rule_id for f in res['findings'])


# -- 1. There is no clean bill of health, and none can be manufactured -------

ok(not any('healthy' in str(r).lower() for r in tt.RULES),
   'no rule in the model uses the word "healthy"')

res = tt.analyse({}, tt.UNKNOWN)
ok(res['findings'] == [], 'an empty observation set produces no findings')
ok(res['data_path'] == 'NOT CONFIRMED',
   'and it certainly does not produce a positive data-path statement')
ok(len(res['evidence_needed']) == len(tt.RULES),
   'every rule is instead reported as waiting on evidence')

# An observation set with every fault-bearing observation set to the GOOD value
# still does not yield a clean bill of health: good news about the checks the
# model happens to know is not evidence that traffic passes.
allgood = {'ike_sa': True, 'child_sa_out': True, 'child_sa_in': True,
           'selectors_agree': True, 'route_into_tunnel': True,
           'reverse_route_present': True, 'crypto_acl_match': True,
           'post_decrypt_permitted': True, 'nat_exempted': True,
           'small_packets_pass': True, 'large_df_packets_pass': True,
           'ptb_received': True, 'mss_clamped': False}
res = tt.analyse(allgood, tt.ROUTE_BASED)
ok(res['findings'] == [], 'with every known check good, nothing fires')
ok(res['data_path'] == 'NOT CONFIRMED',
   'AND THE DATA PATH IS STILL NOT CONFIRMED --- this is the whole point: the '
   'absence of a detected fault is not evidence that traffic passes')
for k in ('encaps_increasing', 'decaps_increasing', 'tcp_app_works', 'udp_app_works'):
    ok(k in res['data_path_why'], 'the report names %s as still outstanding' % k)

# Only counters in both directions plus a TCP and a non-TCP application do it.
confirmed = dict(allgood, encaps_increasing=True, decaps_increasing=True,
                 tcp_app_works=True, udp_app_works=True)
res = tt.analyse(confirmed, tt.ROUTE_BASED)
ok(res['data_path'] == 'CONFIRMED FOR WHAT WAS TESTED', 'full evidence confirms')
ok('not about the tunnel in general' in res['data_path_why'],
   'and even then it is scoped to what was tested')
for drop in ('encaps_increasing', 'decaps_increasing', 'tcp_app_works', 'udp_app_works'):
    partial = dict(confirmed)
    del partial[drop]
    ok(tt.analyse(partial, tt.ROUTE_BASED)['data_path'] == 'NOT CONFIRMED',
       'dropping %s alone withdraws the confirmation' % drop)


# -- 2. Unknown is not False -------------------------------------------------

res = tt.analyse({'ike_sa': tt.UNKNOWN}, tt.ROUTE_BASED)
ok(not fired(res, 'no-ike-sa'),
   'an UNKNOWN IKE SA does not fire the no-IKE-SA rule --- unknown is not absent')
ok(any(b['rule_id'] == 'no-ike-sa' for b in res['evidence_needed']),
   'it is reported as evidence needed instead')
ok(fired(tt.analyse({'ike_sa': False}, tt.ROUTE_BASED), 'no-ike-sa'),
   'an observed-absent IKE SA does fire it')
ok(any('show crypto ikev2 sa' in b['how'] for b in res['evidence_needed']),
   'and the report says which command yields the missing observation')

raises(lambda: tt.analyse({'ike_sa': 'no'}, tt.ROUTE_BASED),
       'a string observation is refused', 'no fourth state')
raises(lambda: tt.analyse({'ike_sa': 0}, tt.ROUTE_BASED),
       'an integer observation is refused')
raises(lambda: tt.analyse({'ike_up': True}, tt.ROUTE_BASED),
       'a misspelt observation is refused, not ignored', 'unrecognised')
raises(lambda: tt.analyse([], tt.ROUTE_BASED), 'a non-dict is refused')


# -- 3. An unrecognised mode cannot silently skip a check --------------------

raises(lambda: tt.analyse({'route_into_tunnel': False}, 'policy'),
       'an unrecognised mode is refused', 'silently skip')
raises(lambda: tt.analyse({}, 'vti'), 'another unrecognised mode is refused')
res = tt.analyse({'route_into_tunnel': False}, tt.UNKNOWN)
ok(not fired(res, 'no-route-into-tunnel'),
   'with the mode unknown the route check does not fire')
ok(any(b['rule_id'] == 'no-route-into-tunnel' and 'mode' in b['missing']
       for b in res['evidence_needed']),
   'and the mode itself is reported as the missing evidence')
ok(fired(tt.analyse({'route_into_tunnel': False}, tt.ROUTE_BASED),
         'no-route-into-tunnel'), 'with the mode known it fires')
ok(not fired(tt.analyse({'crypto_acl_match': False}, tt.ROUTE_BASED),
             'crypto-acl-mismatch'),
   'a policy-based check does not fire on a route-based design')


# -- 4. An MSS clamp is a mitigation, never evidence the fault is gone -------

mtu_fault = {'small_packets_pass': True, 'large_df_packets_pass': False}
ok(fired(tt.analyse(mtu_fault, tt.ROUTE_BASED), 'mtu-black-hole'),
   'an MTU black hole is detected')
ok(fired(tt.analyse(dict(mtu_fault, mss_clamped=True), tt.ROUTE_BASED),
         'mtu-black-hole'),
   'AND IT IS STILL DETECTED WITH A CLAMP CONFIGURED --- the shipped lab '
   'switched this check off when mss_clamped was true')
ok(fired(tt.analyse(dict(mtu_fault, mss_clamped=True), tt.ROUTE_BASED),
         'clamp-hides-mtu-fault'),
   'and the clamp earns its own warning')
ok(not fired(tt.analyse(dict(mtu_fault, mss_clamped=False), tt.ROUTE_BASED),
             'clamp-hides-mtu-fault'),
   'which does not fire when there is no clamp')
res = tt.analyse({'mss_clamped': True, 'tcp_app_works': True, 'udp_app_works': False},
                 tt.ROUTE_BASED)
ok(fired(res, 'clamp-only-tcp-fixed'), 'TCP working while UDP fails is called out')
ok(not fired(tt.analyse({'mss_clamped': True, 'tcp_app_works': True,
                         'udp_app_works': True}, tt.ROUTE_BASED),
             'clamp-only-tcp-fixed'),
   'and not when UDP works too')
says = [f['says'] for f in res['findings'] if f['id'] == 'clamp-only-tcp-fixed'][0]
ok('negotiates a segment size' in says, 'the explanation says why, not just what')


# -- 5. Impossible observation sets are refused, not diagnosed --------------

raises(lambda: tt.analyse({'encaps_increasing': True, 'child_sa_out': False},
                          tt.ROUTE_BASED),
       'encapsulation without an outbound SA is refused', 'cannot be encapsulated')
raises(lambda: tt.analyse({'decaps_increasing': True, 'child_sa_in': False},
                          tt.ROUTE_BASED),
       'decapsulation without an inbound SA is refused')
raises(lambda: tt.analyse({'ike_sa': False, 'child_sa_out': True}, tt.ROUTE_BASED),
       'a Child SA without IKE is outside this fresh fixture', 'snapshots')
raises(lambda: tt.analyse({'small_packets_pass': False, 'large_df_packets_pass': True},
                          tt.ROUTE_BASED),
       'large passing while small fails is refused')
# ... and the possible ones are not.
tt.analyse({'encaps_increasing': True, 'child_sa_out': True}, tt.ROUTE_BASED)
tt.analyse({'small_packets_pass': True, 'large_df_packets_pass': False}, tt.ROUTE_BASED)
ok(True, 'the legitimate neighbours of those combinations are accepted')


# -- 6. Each rule fires on its own case and not on the near miss -------------

for rule in tt.RULES:
    mode = rule.get('mode') or tt.ROUTE_BASED
    res = tt.analyse(dict(rule['needs']), mode)
    ok(fired(res, rule['id']), 'rule %s fires on its own requirement set' % rule['id'])
    for k, v in rule['needs'].items():
        flipped = dict(rule['needs'])
        flipped[k] = not v
        try:
            res2 = tt.analyse(flipped, mode)
        except tt.TriageError:
            continue                       # the flip is an impossible state
        ok(not fired(res2, rule['id']),
           'rule %s does NOT fire when %s is flipped' % (rule['id'], k))

ok(len({r['id'] for r in tt.RULES}) == len(tt.RULES), 'rule ids are unique')
for rule in tt.RULES:
    ok(set(rule['needs']) <= set(tt.OBSERVATIONS),
       'rule %s only requires declared observations' % rule['id'])


# -- 7. The fourth question: can every check ever fire? ----------------------

p = tt.prove_every_rule_can_fire()
ok(p['enumerated'] == 3 ** len(tt.COUPLED), 'the proof enumerates the whole space')
ok(0 < p['consistent_states'] < p['enumerated'],
   'the impossibility constraints actually exclude some of it')
dead = [r['rule_id'] for r in p['rules'] if not r['can_fire']]
ok(not dead, 'no rule is dead code: %s' % dead)
ok(len(p['rules']) == len(tt.RULES), 'every rule was examined')
for r in p['rules']:
    ok(r['witness'] is not None, 'rule %s has a concrete witness' % r['rule_id'])


# -- 8. The report says what it is, and what it is not -----------------------

buf = io.StringIO()
tt.report(buf)
out = buf.getvalue()
ok('no verdict in' in out and 'healthy' in out,
   'the report states in words that it has no healthy verdict')
ok('NOT CONFIRMED' in out, 'and shows the data path as unconfirmed for the cases')
for banned in ('tunnel healthy', 'should pass', 'all clear', 'no problems found'):
    ok(banned not in out.lower(), 'the report never says %r' % banned)
ok('lab 56.2' in out.lower() or 'compute the real figure' in out,
   'the MTU finding points at the calculation rather than asserting a number')
_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    rc_plain, rc_json, rc_prove = tt.main([]), tt.main(['--json']), tt.main(['--prove'])
finally:
    sys.stdout = _stdout
ok(rc_plain == 0, 'the module runs')
ok(rc_json == 0, 'the JSON form runs')
ok(rc_prove == 0, 'the proof runs and reports no dead rules')
ok(tt.analyse(allgood, tt.ROUTE_BASED) == tt.analyse(allgood, tt.ROUTE_BASED),
   'the analysis is deterministic')

print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
