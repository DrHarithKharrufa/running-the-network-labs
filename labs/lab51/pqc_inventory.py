#!/usr/bin/env python3
"""Lab 51.3 --- the migration worksheet, with the three quantities kept apart.

WHY THIS LAB WAS REBUILT
------------------------
The shipped worksheet applied one inequality to every row:

    total = lifetime + migration
    if total >= horizon: 'scenario_requires_planning_now'

with a single `lifetime` field, and it produced three wrong answers.

  IT APPLIED A CONFIDENTIALITY INEQUALITY TO SIGNATURES.  Mosca's inequality
  asks whether data recorded TODAY is still secret when the capability arrives:
  it works because ciphertext can be stored now and opened later.  A signature
  has a different exposure: a future forgery can assert an old date or target
  a long-lived verifier. It does not erase a prior trustworthy verification.
  Preservation of long-term authenticity needs trusted timing and renewal too;
  this worksheet considers whether the VERIFIER is still in service then ---
  the root in the silicon, the device that will not take an update.  The old
  model's own rationale string said something close to this while its
  arithmetic did the other thing, which is the defect of a conclusion typed
  under a computation rather than derived from it.

  IT DISCARDED URGENCY ON THE TWO ROWS THAT NEEDED IT MOST.  `aes256` returned
  'separate_symmetric_review' and `unknown` returned 'inventory_required'
  BEFORE any lifetime test ran.  So a payload with a hundred-year
  confidentiality requirement and a one-year horizon came back with a status
  that reads like somebody else's problem.  In the shipped inventory the backup
  payload (aes256, 20 years) and the backup key wrapping (unknown, 20 years)
  are the two most exposed rows, and BOTH returned non-urgent statuses. Between
  them they describe one system, and the worksheet never said it was at risk.

  AND IT HAD NO WAY TO EXPRESS A DEPENDENCY.  AES-256 at rest is exactly as
  post-quantum as whatever wraps its key.  Listing payload and wrapping as two
  independent rows, each reassuring on its own, is how an inventory reports
  green on an exposed system.

WHAT THIS ONE DOES
------------------
Three quantities, never merged: SESSION DURATION (how long a connection lasts
--- almost never the relevant number, and recorded only so that using it is
visibly wrong), DATA CONFIDENTIALITY LIFETIME (how long the plaintext must stay
secret, which is the Mosca quantity), and VERIFIER SERVICE LIFE (how long
something must still check a signature, which is the authenticity quantity).
Each role uses the quantity that governs it and is refused the others.

A fourth attribute decides more than any of them: whether the thing can be
changed in the field at all.  A root of trust burned into silicon cannot wait
for a vendor roadmap, because there will be no update to apply.

    python3 pqc_inventory.py
    python3 pqc_inventory.py --json
    python3 test_pqc_inventory.py

Every horizon here is a STATED SCENARIO, not a forecast. Nothing in this file
predicts when or whether a cryptographically relevant quantum computer exists,
and no output is a compliance decision.
"""
import argparse
import json
import math
import sys
import textwrap

ROLES = ('confidentiality', 'authenticity', 'symmetric_at_rest', 'unclassified')
MECHANISMS = {
    'ecdh': 'confidentiality', 'rsa_kex': 'confidentiality',
    'dh': 'confidentiality',
    'rsa_signature': 'authenticity', 'ecdsa_signature': 'authenticity',
    'ed25519_signature': 'authenticity',
    'ml_kem': 'confidentiality', 'ml_dsa': 'authenticity',
    'hybrid_kex': 'confidentiality',
    'aes128': 'symmetric_at_rest', 'aes256': 'symmetric_at_rest',
    'unknown': 'unclassified',
}
QUANTUM_VULNERABLE = {'ecdh', 'rsa_kex', 'dh', 'rsa_signature',
                      'ecdsa_signature', 'ed25519_signature'}
PQ_CANDIDATE = {'ml_kem', 'ml_dsa', 'hybrid_kex'}


class InventoryError(ValueError):
    """The described system cannot be assessed as stated."""


def _years(value, name, allow_none=False):
    if value is None:
        if allow_none:
            return None
        raise InventoryError('%s must be given' % name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InventoryError('%s must be a finite non-negative number, got %r'
                             % (name, value))
    if not math.isfinite(value) or value < 0:
        raise InventoryError('%s must be a finite non-negative number, got %r'
                             % (name, value))
    return float(value)


def classify(mechanism):
    """The role a mechanism plays. Not a judgement, a lookup."""
    if mechanism not in MECHANISMS:
        raise InventoryError(
            'mechanism %r is not classified; use one of %s, or "unknown" if it '
            'is genuinely unresolved --- but "unknown" is a finding, not a '
            'default' % (mechanism, ', '.join(sorted(MECHANISMS))))
    return MECHANISMS[mechanism]


def assess(item, horizon_years, inventory=None):
    """Assess one system against one stated horizon.

    The role decides which quantity is used, and asking for the wrong one is
    an error rather than a silently accepted number.
    """
    name = item.get('system')
    if not isinstance(name, str) or not name.strip():
        raise InventoryError('every system must have a name')
    role = classify(item.get('mechanism'))
    horizon = _years(horizon_years, 'horizon')
    if horizon == 0:
        raise InventoryError('horizon must be positive')
    migration = _years(item.get('migration_years'), 'migration_years')
    migratable = item.get('migratable', True)
    if not isinstance(migratable, bool):
        raise InventoryError('migratable must be true or false, got %r'
                             % (migratable,))
    session = _years(item.get('session_duration_years'), 'session_duration_years',
                     allow_none=True)
    data_life = _years(item.get('data_confidentiality_years'),
                       'data_confidentiality_years', allow_none=True)
    verifier_life = _years(item.get('verifier_service_years'),
                           'verifier_service_years', allow_none=True)

    out = {
        'system': name, 'mechanism': item['mechanism'], 'role': role,
        'assumed_horizon_years': horizon, 'migration_years': migration,
        'migratable': migratable,
        'session_duration_years': session,
        'data_confidentiality_years': data_life,
        'verifier_service_years': verifier_life,
        'depends_on': list(item.get('depends_on', ())),
    }

    if role == 'confidentiality':
        if data_life is None:
            raise InventoryError(
                '%r is a confidentiality mechanism, so it needs '
                'data_confidentiality_years --- how long the PLAINTEXT must '
                'stay secret. Session duration is not that number and this '
                'model will not substitute it.' % name)
        exposure = data_life + migration
        out.update(
            quantity_used='data_confidentiality_years + migration_years',
            exposure_years=exposure,
            recording_exposure=True,
            at_risk=(item['mechanism'] in QUANTUM_VULNERABLE
                     and exposure >= horizon),
            why=('Traffic recorded today can be opened once the capability '
                 'exists, so the clock started when the data was first sent.'))
        if session is not None and data_life is not None and session < data_life:
            out['session_note'] = (
                'The session lasts %g years and the data must stay secret for '
                '%g. The short number is the tempting one and it is not the '
                'one that governs.' % (session, data_life))
    elif role == 'authenticity':
        # Diagnose the WRONG quantity before the missing one: being told you
        # used the wrong clock is more useful than being told you omitted the
        # right one, and supplying both is how the old worksheet went astray.
        if data_life is not None:
            raise InventoryError(
                '%r is a signature mechanism and was given '
                'data_confidentiality_years. Confidentiality lifetime does not '
                'govern this signature worksheet: future forgery is an authenticity '
                'risk, distinct from stored-ciphertext decryption. State '
                'verifier_service_years instead --- how long something must '
                'still VERIFY.' % name)
        if verifier_life is None:
            raise InventoryError(
                '%r is a signature mechanism, so it needs '
                'verifier_service_years --- how long something must still '
                'VERIFY. A signature has no recording exposure, so '
                'data_confidentiality_years does not govern it.' % name)
        out.update(
            quantity_used='verifier_service_years',
            exposure_years=verifier_life,
            recording_exposure=False,
            at_risk=(item['mechanism'] in QUANTUM_VULNERABLE
                     and verifier_life >= horizon),
            why=('Future forgery can claim an old date or target a remaining verifier. '
                 'Previously trusted verification is not undone. This simplified '
                 'model uses verifier life; preservation/timestamp renewal needs '
                 'a separate assessment, not the confidentiality inequality.'))
        if not migratable:
            out['decision_deadline_years'] = 0.0
            out['why'] += (' And this one cannot be changed in the field, so '
                           'the decision is made before it ships, not when the '
                           'roadmap arrives.')
        else:
            out['decision_deadline_years'] = max(0.0, horizon - migration)
    elif role == 'symmetric_at_rest':
        out.update(
            quantity_used='data_confidentiality_years (for the wrapping, not '
                          'the cipher)',
            exposure_years=(data_life + migration) if data_life is not None
                           else None,
            recording_exposure=True,
            at_risk=False,
            why=('A symmetric cipher of adequate width is not the exposed part. '
                 'What is exposed is whatever establishes or wraps its key, '
                 'which is a separate row and is resolved through depends_on.'))
        if data_life is None:
            raise InventoryError(
                '%r is symmetric at rest and still needs '
                'data_confidentiality_years. The cipher may be fine; the '
                'question is how long the data it protects must stay secret, '
                'because that is what the key wrapping has to survive.' % name)
    else:
        if data_life is None and verifier_life is None:
            raise InventoryError(
                '%r is unclassified and states no lifetime at all. An '
                'unresolved mechanism with an unknown lifetime is the least '
                'informative row an inventory can contain; state whichever '
                'lifetime you do know.' % name)
        horizon_relevant = max(x for x in (data_life, verifier_life)
                               if x is not None)
        out.update(
            quantity_used='whichever lifetime is known, pending classification',
            exposure_years=horizon_relevant + migration,
            recording_exposure=None,
            at_risk=None,
            why=('The mechanism is unresolved, so no inequality can be applied '
                 'yet. The lifetime is retained rather than discarded, because '
                 'it decides how urgent the identification is.'))

    out['status'] = _status(out)
    return out


def _status(a):
    """A status derived from the fields, with urgency never discarded."""
    urgent = (a['exposure_years'] is not None
              and a['exposure_years'] >= a['assumed_horizon_years'])
    if a['role'] == 'unclassified':
        return ('identify_now_exposure_exceeds_horizon' if urgent
                else 'identify_this_mechanism')
    if a['role'] == 'symmetric_at_rest':
        return ('cipher_adequate_check_wrapping_urgently' if urgent
                else 'cipher_adequate_check_wrapping')
    if a['role'] == 'authenticity':
        if not a['migratable'] and a['at_risk']:
            return 'decide_before_shipping_cannot_be_updated'
        if not a['migratable']:
            return 'not_updatable_review_before_shipping'
        return ('plan_now_verifier_outlives_horizon' if a['at_risk']
                else 'no_overlap_in_this_scenario')
    if a['at_risk']:
        return 'plan_now_recorded_traffic_is_exposed'
    if a['mechanism'] in PQ_CANDIDATE:
        return 'already_migrated_in_this_scenario'
    return 'no_overlap_in_this_scenario'


def resolve_dependencies(assessed):
    """A system is no better protected than what it depends on.

    The old worksheet had no way to say this, so a payload row and a wrapping
    row could both look calm while describing one exposed system.
    """
    by_name = {a['system']: a for a in assessed}
    out = []
    for a in assessed:
        worst = []
        for dep in a['depends_on']:
            if dep not in by_name:
                raise InventoryError(
                    '%r depends on %r, which is not in the inventory. A '
                    'dependency you have not listed is not a dependency you do '
                    'not have.' % (a['system'], dep))
            d = by_name[dep]
            if d['at_risk'] or d['at_risk'] is None or d['role'] == 'unclassified':
                worst.append(dep)
        b = dict(a)
        b['inherited_risk_from'] = worst
        if worst and not b['at_risk']:
            b['effective_status'] = 'exposed_through_dependency'
            b['effective_note'] = (
                'This row is calm on its own and its protection rests on %s, '
                'which is not. The system is exposed.' % ', '.join(worst))
        else:
            b['effective_status'] = b['status']
            b['effective_note'] = ''
        out.append(b)
    return out


# ---------------------------------------------------------------------------
# an illustrative estate
# ---------------------------------------------------------------------------
INVENTORY = [
    dict(system='VPN carrying patient records', mechanism='ecdh',
         session_duration_years=0.001, data_confidentiality_years=15,
         migration_years=3),
    dict(system='Firmware verification root in silicon',
         mechanism='rsa_signature', verifier_service_years=12,
         migration_years=4, migratable=False),
    dict(system='Software update signing service', mechanism='ecdsa_signature',
         verifier_service_years=8, migration_years=2),
    dict(system='Management API long-lived secrets', mechanism='ecdh',
         session_duration_years=0.02, data_confidentiality_years=10,
         migration_years=2),
    dict(system='Backup payload encryption', mechanism='aes256',
         data_confidentiality_years=20, migration_years=2,
         depends_on=['Backup key wrapping']),
    dict(system='Backup key wrapping', mechanism='unknown',
         data_confidentiality_years=20, migration_years=2),
    dict(system='MACsec key establishment', mechanism='unknown',
         data_confidentiality_years=10, migration_years=3),
    dict(system='Short-lived non-sensitive test traffic', mechanism='ecdh',
         session_duration_years=0.0001, data_confidentiality_years=1,
         migration_years=1),
    dict(system='Peering session authentication', mechanism='hybrid_kex',
         session_duration_years=1, data_confidentiality_years=2,
         migration_years=1),
]


def run(inventory=None, horizons=(5, 10, 15)):
    inventory = INVENTORY if inventory is None else inventory
    out = {}
    for h in horizons:
        assessed = [assess(i, h) for i in inventory]
        out[h] = resolve_dependencies(assessed)
    return out


def contrast_with_session_duration(inventory=None, horizon=10):
    """What the answer would be if somebody used the session duration.

    The point of the old model's confusion, made countable: scoring the
    confidentiality rows on how long a connection lasts rather than on how long
    the data must stay secret.
    """
    inventory = INVENTORY if inventory is None else inventory
    rows = []
    for item in inventory:
        if classify(item['mechanism']) != 'confidentiality':
            continue
        if item.get('session_duration_years') is None:
            continue
        correct = assess(item, horizon)
        wrong_exposure = item['session_duration_years'] + item['migration_years']
        rows.append({
            'system': item['system'],
            'session_duration_years': item['session_duration_years'],
            'data_confidentiality_years': item['data_confidentiality_years'],
            'correct_exposure': correct['exposure_years'],
            'exposure_if_session_used': wrong_exposure,
            'correct_at_risk': correct['at_risk'],
            'at_risk_if_session_used': (item['mechanism'] in QUANTUM_VULNERABLE
                                        and wrong_exposure >= horizon),
        })
    return rows


def build_report():
    scenarios = run()
    return {
        'scope': 'Stated sensitivity scenarios at 5, 10 and 15 years. NOT a '
                 'forecast of when a cryptographically relevant quantum '
                 'computer exists, and no output is a compliance decision.',
        'scenarios': {str(k): v for k, v in scenarios.items()},
        'session_contrast': contrast_with_session_duration(),
        'caveats': [
            'Every horizon is a stated scenario. This file predicts nothing '
            'about quantum hardware, and a horizon you disagree with is an '
            'input you should change rather than an argument with the model.',
            'Every lifetime, migration time and dependency is a stated input '
            'about a fictional estate. None is measured and none is advice '
            'about a real system.',
            'A mechanism label is a claim about what a product does. Products '
            'that say "AES-256" frequently establish or wrap that key with '
            'something else entirely, and that something else is the row that '
            'matters --- which is what depends_on exists to record.',
            'The model says nothing about WHICH post-quantum algorithm to '
            'adopt, about parameter sets, or about whether a hybrid '
            'construction is required in your jurisdiction. Those are '
            'decisions for the standards and the regulator that apply to you.',
            'A signature row with no recording exposure is not a safe row. It '
            'means the exposure starts later rather than now, and if the '
            'verifier cannot be updated, later is too late to start.',
            'Nothing here is a migration plan. It is the arithmetic a '
            'migration plan has to survive.',
        ],
    }


def _wrap(lines, text, indent='  '):
    lines.extend(textwrap.wrap(text, width=74, initial_indent=indent,
                               subsequent_indent=indent))


def report_text(rep):
    L = []
    L.append('Migration exposure, with the three quantities kept apart (Ch 51)')
    L.append('Every horizon is a stated scenario. Nothing here is a forecast.')
    L.append('')
    L.append('A. The quantity that governs depends on the ROLE')
    L.append('-' * 74)
    _wrap(L, 'A confidentiality mechanism is governed by how long the '
             'PLAINTEXT must stay secret, because recorded traffic can be '
             'opened later. A signature is governed by how long something must '
             'still VERIFY; forged material may assert an old date. These are '
             'different clocks and the model refuses '
             'to accept one in place of the other.')
    L.append('')
    for h in ('10',):
        L.append('  At a stated %s-year horizon:' % h)
        L.append('')
        L.append('  %-38s %-13s %8s' % ('system', 'quantity', 'exposure'))
        for a in rep['scenarios'][h]:
            q = {'confidentiality': 'data life',
                 'authenticity': 'verifier life',
                 'symmetric_at_rest': 'wrapping',
                 'unclassified': 'unresolved'}[a['role']]
            ex = ('%8.1f' % a['exposure_years']) if a['exposure_years'] is not None else '      --'
            L.append('  %-38s %-13s %s' % (a['system'][:38], q, ex))
            L.append('      -> %s' % a['effective_status'])
    L.append('')
    L.append('B. Using the session duration, which is the tempting number')
    L.append('-' * 74)
    L.append('  %-34s %8s %9s %8s %8s' % ('system', 'session', 'data life',
                                          'correct', 'if session'))
    for r in rep['session_contrast']:
        L.append('  %-34s %8.4f %9.1f %8s %8s'
                 % (r['system'][:34], r['session_duration_years'],
                    r['data_confidentiality_years'],
                    'AT RISK' if r['correct_at_risk'] else 'ok',
                    'AT RISK' if r['at_risk_if_session_used'] else 'ok'))
    flipped = [r for r in rep['session_contrast']
               if r['correct_at_risk'] and not r['at_risk_if_session_used']]
    L.append('')
    if flipped:
        _wrap(L, '%d of %d confidentiality rows flip from AT RISK to ok if the '
                 'session duration is used instead of the confidentiality '
                 'lifetime. Every one of those is a system whose recorded '
                 'traffic is exposed and whose worksheet says it is fine.'
                 % (len(flipped), len(rep['session_contrast'])))
    L.append('')
    L.append('C. The two rows that describe one system')
    L.append('-' * 74)
    for a in rep['scenarios']['10']:
        if a['inherited_risk_from'] or a['role'] == 'symmetric_at_rest':
            L.append('  %s' % a['system'])
            L.append('    mechanism %s, status %s' % (a['mechanism'], a['status']))
            if a['depends_on']:
                L.append('    depends on: %s' % ', '.join(a['depends_on']))
            if a['effective_note']:
                _wrap(L, a['effective_note'], indent='    ')
    L.append('')
    _wrap(L, 'The old worksheet had no way to say this. Backup payload and '
             'backup key wrapping were two independent rows, one returning '
             '"separate symmetric review" and the other "inventory required", '
             'and neither said the system was exposed. AES-256 at rest is '
             'exactly as post-quantum as whatever wraps its key.')
    L.append('')
    L.append('D. What cannot wait for a vendor')
    L.append('-' * 74)
    stuck = [a for a in rep['scenarios']['10'] if not a['migratable']]
    for a in stuck:
        L.append('  %s' % a['system'])
        L.append('    %s, verifier in service %g years, horizon %g'
                 % (a['mechanism'], a['verifier_service_years'],
                    a['assumed_horizon_years']))
        L.append('    status: %s' % a['status'])
        L.append('    decision deadline: %g years from now'
                 % a['decision_deadline_years'])
    L.append('')
    _wrap(L, 'The advice to wait for vendor support assumes there will be '
             'something to apply the support to. A verification root fixed in '
             'silicon at manufacture has no update path, so the choice is made '
             'when the part is specified, and every device shipped before the '
             'decision carries it for its whole service life. "Wait for the '
             'vendors" is sound for the things that can be changed later and '
             'is not available for the things that cannot.')
    L.append('')
    L.append('What this does NOT establish')
    L.append('-' * 74)
    for c in rep['caveats']:
        L.extend(textwrap.wrap(c, width=74, initial_indent='- ',
                               subsequent_indent='  '))
    return '\n'.join(L)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--json', action='store_true', help='emit the report as JSON')
    a = p.parse_args(argv)
    try:
        rep = build_report()
    except InventoryError as exc:
        print('cannot evaluate: %s' % exc, file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=2) if a.json else report_text(rep))
    return 0


if __name__ == '__main__':
    sys.exit(main())
