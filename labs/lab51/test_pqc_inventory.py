#!/usr/bin/env python3
"""Checks for pqc_inventory.py.

The worksheet this replaces merged three quantities into one field and applied
one inequality to every role. The first block of checks is therefore about
REFUSAL: the model must reject the wrong quantity for a role rather than quietly
accept a number, because quietly accepting it is exactly what went wrong. The
second block shows that urgency survives on the rows where the old model
discarded it, and the third that a dependency can make a calm row exposed.
"""
import json
import subprocess
import sys

import pqc_inventory as Q

CHECKS = 0
FAILED = []


def check(label, cond):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except Q.InventoryError:
        return True
    except Exception:
        return False
    return False


KEX = dict(system='kex', mechanism='ecdh', data_confidentiality_years=15,
           migration_years=3)
SIG = dict(system='sig', mechanism='rsa_signature', verifier_service_years=12,
           migration_years=4)

# ===========================================================================
# THE REFUSALS: a role may not be assessed on another role's quantity
# ===========================================================================
check('a confidentiality mechanism without a data lifetime is refused',
      raises(Q.assess, dict(system='x', mechanism='ecdh', migration_years=1), 10))
try:
    Q.assess(dict(system='x', mechanism='ecdh', migration_years=1), 10)
    msg = ''
except Q.InventoryError as exc:
    msg = str(exc)
check('the refusal names the missing quantity', 'data_confidentiality_years' in msg)
check('the refusal rejects session duration explicitly',
      'Session duration is not that number' in msg)

check('a signature without a verifier lifetime is refused',
      raises(Q.assess, dict(system='s', mechanism='rsa_signature',
                            migration_years=1), 10))
try:
    Q.assess(dict(system='s', mechanism='rsa_signature',
                  data_confidentiality_years=12, migration_years=1), 10)
    msg2 = ''
except Q.InventoryError as exc:
    msg2 = str(exc)
check('a signature given a CONFIDENTIALITY lifetime is refused', msg2 != '')
check('the refusal distinguishes future forgery from stored-ciphertext exposure',
      'future forgery' in msg2 and 'stored-ciphertext' in msg2)

check('symmetric at rest still needs a data lifetime',
      raises(Q.assess, dict(system='b', mechanism='aes256',
                            migration_years=1), 10))
check('an unclassified row with no lifetime at all is refused',
      raises(Q.assess, dict(system='u', mechanism='unknown',
                            migration_years=1), 10))
check('an unknown mechanism label is refused',
      raises(Q.assess, dict(system='x', mechanism='VPN',
                            data_confidentiality_years=1, migration_years=1), 10))
try:
    Q.assess(dict(system='x', mechanism='VPN', migration_years=1), 10)
    msg3 = ''
except Q.InventoryError as exc:
    msg3 = str(exc)
check('and the error says unknown is a finding rather than a default',
      'a finding, not a' in msg3)
check('an unnamed system is refused',
      raises(Q.assess, dict(system='  ', mechanism='ecdh',
                            data_confidentiality_years=1, migration_years=1), 10))
check('a zero horizon is refused', raises(Q.assess, KEX, 0))
check('a negative horizon is refused', raises(Q.assess, KEX, -5))
for bad in (-1, float('nan'), float('inf'), True, '10'):
    check('migration_years rejects %r' % (bad,),
          raises(Q.assess, dict(KEX, migration_years=bad), 10))
    check('the horizon rejects %r' % (bad,), raises(Q.assess, KEX, bad))
check('migratable must be a boolean',
      raises(Q.assess, dict(SIG, migratable='yes'), 10))

# ===========================================================================
# the role decides the clock
# ===========================================================================
k = Q.assess(KEX, 10)
check('a KEX is classified as confidentiality', k['role'] == 'confidentiality')
check('a KEX has recording exposure', k['recording_exposure'] is True)
check('a KEX exposure is data life plus migration', close(k['exposure_years'], 18))
check('a KEX over the horizon is at risk', k['at_risk'] is True)
check('and says so in its status', k['status'] == 'plan_now_recorded_traffic_is_exposed')
check('the KEX names the quantity it used',
      'data_confidentiality_years' in k['quantity_used'])

s = Q.assess(SIG, 10)
check('a signature is classified as authenticity', s['role'] == 'authenticity')
check('a signature has NO recording exposure', s['recording_exposure'] is False)
check('a signature exposure is the verifier life alone',
      close(s['exposure_years'], 12))
check('migration is NOT added to a signature exposure',
      not close(s['exposure_years'], 12 + 4))
check('a verifier outliving the horizon is at risk', s['at_risk'] is True)
check('the signature explains backdating and preservation boundaries',
      'old date' in s['why'] and 'preservation' in s['why'])
check('a signature under the horizon is not at risk',
      Q.assess(dict(SIG, verifier_service_years=3), 10)['at_risk'] is False)
check('a post-quantum KEX is not at risk in any scenario',
      Q.assess(dict(system='p', mechanism='ml_kem',
                    data_confidentiality_years=50, migration_years=5),
               5)['at_risk'] is False)
check('and is reported as already migrated',
      Q.assess(dict(system='p', mechanism='hybrid_kex',
                    data_confidentiality_years=50, migration_years=5),
               5)['status'] == 'already_migrated_in_this_scenario')
check('a post-quantum signature is not at risk',
      Q.assess(dict(system='p', mechanism='ml_dsa',
                    verifier_service_years=50, migration_years=5),
               5)['at_risk'] is False)

# ===========================================================================
# session duration is recorded and never used
# ===========================================================================
with_session = Q.assess(dict(KEX, session_duration_years=0.001), 10)
check('the session duration is recorded',
      close(with_session['session_duration_years'], 0.001))
check('but the exposure is unchanged by it',
      close(with_session['exposure_years'], k['exposure_years']))
check('and the model remarks on the gap', 'session_note' in with_session)
check('the remark names both numbers',
      '0.001' in with_session['session_note']
      and '15' in with_session['session_note'])
check('a session longer than the data life draws no remark',
      'session_note' not in Q.assess(
          dict(system='x', mechanism='ecdh', session_duration_years=5,
               data_confidentiality_years=1, migration_years=1), 10))

contrast = Q.contrast_with_session_duration()
check('the contrast covers only confidentiality rows',
      all('data_confidentiality_years' in r for r in contrast))
check('every contrast row also records the session duration',
      all('session_duration_years' in r for r in contrast))
check('the contrast is not empty', len(contrast) >= 3)
flipped = [r for r in contrast
           if r['correct_at_risk'] and not r['at_risk_if_session_used']]
check('some rows flip from at-risk to ok on the wrong quantity', len(flipped) >= 2)
check('no row flips the other way',
      not [r for r in contrast
           if r['at_risk_if_session_used'] and not r['correct_at_risk']])
check('every flipped row has a data life far above its session',
      all(r['data_confidentiality_years'] > r['session_duration_years'] * 100
          for r in flipped))

# ===========================================================================
# urgency is not discarded on the rows the old model short-circuited
# ===========================================================================
aes_urgent = Q.assess(dict(system='b', mechanism='aes256',
                           data_confidentiality_years=100,
                           migration_years=50), 1)
check('AES-256 with a huge lifetime keeps its exposure figure',
      close(aes_urgent['exposure_years'], 150))
check('and is flagged urgent rather than deferred',
      aes_urgent['status'] == 'cipher_adequate_check_wrapping_urgently')
check('AES-256 within the horizon is the calm variant',
      Q.assess(dict(system='b', mechanism='aes256',
                    data_confidentiality_years=1, migration_years=1),
               10)['status'] == 'cipher_adequate_check_wrapping')
check('the cipher itself is never marked at risk', aes_urgent['at_risk'] is False)
check('and the model says what IS exposed', 'wraps its key' in aes_urgent['why'])

unk_urgent = Q.assess(dict(system='u', mechanism='unknown',
                           data_confidentiality_years=100,
                           migration_years=50), 1)
check('an unresolved mechanism keeps its exposure figure',
      close(unk_urgent['exposure_years'], 150))
check('and is flagged urgent rather than merely unidentified',
      unk_urgent['status'] == 'identify_now_exposure_exceeds_horizon')
check('an unresolved mechanism inside the horizon is the calm variant',
      Q.assess(dict(system='u', mechanism='unknown',
                    data_confidentiality_years=1, migration_years=1),
               10)['status'] == 'identify_this_mechanism')
check('an unresolved row has no at_risk verdict either way',
      unk_urgent['at_risk'] is None)
check('and says no inequality can be applied yet',
      'no inequality can be applied' in unk_urgent['why'])

# ===========================================================================
# dependencies
# ===========================================================================
pair = [dict(system='payload', mechanism='aes256',
             data_confidentiality_years=20, migration_years=2,
             depends_on=['wrap']),
        dict(system='wrap', mechanism='rsa_kex',
             data_confidentiality_years=20, migration_years=2)]
res = Q.resolve_dependencies([Q.assess(i, 10) for i in pair])
payload = next(r for r in res if r['system'] == 'payload')
wrap = next(r for r in res if r['system'] == 'wrap')
check('the wrapping is at risk', wrap['at_risk'] is True)
check('the payload cipher is not itself at risk', payload['at_risk'] is False)
check('but the payload inherits the exposure',
      payload['effective_status'] == 'exposed_through_dependency')
check('and names what it inherited from',
      payload['inherited_risk_from'] == ['wrap'])
check('the note explains the inheritance', 'The system is exposed' in payload['effective_note'])
safe = [dict(system='payload', mechanism='aes256',
             data_confidentiality_years=2, migration_years=1,
             depends_on=['wrap']),
        dict(system='wrap', mechanism='ml_kem',
             data_confidentiality_years=2, migration_years=1)]
res2 = Q.resolve_dependencies([Q.assess(i, 10) for i in safe])
p2 = next(r for r in res2 if r['system'] == 'payload')
check('a payload wrapped post-quantum inherits nothing',
      p2['inherited_risk_from'] == [])
check('and keeps its own status', p2['effective_status'] == p2['status'])
check('an unresolved dependency also taints',
      Q.resolve_dependencies([
          Q.assess(dict(system='a', mechanism='aes256',
                        data_confidentiality_years=1, migration_years=1,
                        depends_on=['b']), 10),
          Q.assess(dict(system='b', mechanism='unknown',
                        data_confidentiality_years=1, migration_years=1), 10),
      ])[0]['effective_status'] == 'exposed_through_dependency')
check('a dependency not in the inventory is refused',
      raises(Q.resolve_dependencies,
             [Q.assess(dict(KEX, depends_on=['missing']), 10)]))
check('rows with no dependencies resolve unchanged',
      Q.resolve_dependencies([Q.assess(KEX, 10)])[0]['effective_status']
      == Q.assess(KEX, 10)['status'])

# ===========================================================================
# what cannot wait for a vendor
# ===========================================================================
stuck = Q.assess(dict(SIG, migratable=False), 10)
check('a non-migratable at-risk signature says decide before shipping',
      stuck['status'] == 'decide_before_shipping_cannot_be_updated')
check('its decision deadline is now', close(stuck['decision_deadline_years'], 0))
check('and the reason says there will be no update to apply',
      'cannot be changed in the field' in stuck['why'])
ok_stuck = Q.assess(dict(SIG, verifier_service_years=2, migratable=False), 10)
check('a non-migratable signature inside the horizon still gets reviewed',
      ok_stuck['status'] == 'not_updatable_review_before_shipping')
mig = Q.assess(SIG, 10)
check('a migratable signature gets a deadline of horizon minus migration',
      close(mig['decision_deadline_years'], 6))
check('a deadline never goes negative',
      Q.assess(dict(SIG, migration_years=50), 10)['decision_deadline_years'] == 0.0)
check('migratable defaults to true', Q.assess(SIG, 10)['migratable'] is True)

# ===========================================================================
# classification
# ===========================================================================
check('every mechanism maps to a known role',
      all(r in Q.ROLES for r in Q.MECHANISMS.values()))
check('every quantum-vulnerable mechanism is classified',
      all(m in Q.MECHANISMS for m in Q.QUANTUM_VULNERABLE))
check('every post-quantum candidate is classified',
      all(m in Q.MECHANISMS for m in Q.PQ_CANDIDATE))
check('no mechanism is both vulnerable and a candidate',
      not (Q.QUANTUM_VULNERABLE & Q.PQ_CANDIDATE))
check('symmetric mechanisms are not in the vulnerable set',
      'aes256' not in Q.QUANTUM_VULNERABLE)
check('classify refuses an unknown label', raises(Q.classify, 'magic'))
for m, r in Q.MECHANISMS.items():
    check('classify(%s) is %s' % (m, r), Q.classify(m) == r)

# ===========================================================================
# the illustrative estate and the report
# ===========================================================================
rep = Q.build_report()
check('report runs three horizons', len(rep['scenarios']) == 3)
check('every horizon assesses every system',
      all(len(v) == len(Q.INVENTORY) for v in rep['scenarios'].values()))
check('the scope refuses to be a forecast', 'NOT a' in rep['scope'])
check('the scope refuses to be a compliance decision',
      'compliance decision' in rep['scope'])
check('report carries the session contrast', len(rep['session_contrast']) >= 3)
check('report carries caveats', len(rep['caveats']) >= 5)
check('a caveat says a mechanism label is a claim',
      any('claim about what a product does' in c for c in rep['caveats']))
check('a caveat refuses to name an algorithm',
      any('WHICH post-quantum algorithm' in c for c in rep['caveats']))
check('a caveat says a signature row is not a safe row',
      any('later is too late' in c for c in rep['caveats']))
ten = rep['scenarios']['10']
check('the backup payload is exposed through its wrapping',
      next(a for a in ten if a['system'] == 'Backup payload encryption')
      ['effective_status'] == 'exposed_through_dependency')
check('the silicon root cannot wait',
      next(a for a in ten if 'silicon' in a['system'])['status']
      == 'decide_before_shipping_cannot_be_updated')
check('the short-lived test traffic is genuinely fine',
      next(a for a in ten if 'test traffic' in a['system'])['at_risk'] is False)
check('a longer horizon puts fewer rows at risk',
      sum(1 for a in rep['scenarios']['15'] if a['at_risk'])
      <= sum(1 for a in rep['scenarios']['5'] if a['at_risk']))
check('report JSON-serialises', isinstance(json.dumps(rep), str))
text = Q.report_text(rep)
check('the text names the four sections',
      all(x in text for x in ('A.', 'B.', 'C.', 'D.')))
check('the text shows rows flipping on the wrong quantity', 'flip from AT RISK' in text)
check('the text explains the dependency', 'exactly as post-quantum as' in text)
check('the text discloses what it does not establish', 'does NOT establish' in text)
check('no report line exceeds eighty characters',
      all(len(x) <= 80 for x in text.splitlines()))

out = subprocess.run([sys.executable, 'pqc_inventory.py', '--json'],
                     capture_output=True, text=True)
check('--json exits zero', out.returncode == 0)
check('--json parses', isinstance(json.loads(out.stdout), dict))
plain = subprocess.run([sys.executable, 'pqc_inventory.py'],
                       capture_output=True, text=True)
check('plain run exits zero', plain.returncode == 0)
check('plain run is not JSON', not plain.stdout.lstrip().startswith('{'))

print('pqc_inventory: %d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: ' + f)
sys.exit(1 if FAILED else 0)
