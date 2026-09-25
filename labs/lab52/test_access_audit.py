#!/usr/bin/env python3
"""Checks for access_audit.py.

The shipped version failed OPEN in three ways, so the first block of checks
pins all three shut: a populated-but-stale field must produce a finding, a
truthy-but-not-boolean value must not be read as a control, and an unrecognised
value must come back UNSTATED rather than silently passing. The last block
pins the property the lab is named for --- that nothing is ever certified.
"""
import json
import subprocess
import sys

import access_audit as A

CHECKS = 0
FAILED = []


def check(label, cond):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except A.AuditError:
        return True
    except Exception:
        return False
    return False


def verdict_for(model, field):
    return next(r for r in A.audit(model) if r['field'] == field)['verdict']


BASE = dict(A.MODEL)

# ===========================================================================
# THE THREE FAIL-OPENS, pinned shut
# ===========================================================================
# 1. presence read as adequacy
check('a never-tested break-glass is a finding',
      A.grade_break_glass(None)[0] == A.BAD)
for days in (181, 365, 900, 5000):
    check('a break-glass tested %d days ago is a finding' % days,
          A.grade_break_glass(days)[0] == A.BAD)
for days in (0, 1, 30, 180):
    check('a break-glass tested %d days ago is a claim, not a pass' % days,
          A.grade_break_glass(days)[0] == A.CLAIM)
check('the shipped 900-day value is a finding in the full audit',
      verdict_for(dict(BASE, break_glass_tested_days_ago=900),
                  'break_glass_tested_days_ago') == A.BAD)
check('and it is NOT silently accepted',
      verdict_for(dict(BASE, break_glass_tested_days_ago=900),
                  'break_glass_tested_days_ago') != A.CLAIM)
check('the threshold is a parameter, not a constant',
      A.grade_break_glass(200, stale_after_days=365)[0] == A.CLAIM)
check('a non-numeric answer is unstated',
      A.grade_break_glass('recently')[0] == A.UNKNOWN)
check('a boolean is not a number of days',
      A.grade_break_glass(True)[0] == A.UNKNOWN)
check('a negative number of days is unstated',
      A.grade_break_glass(-5)[0] == A.UNKNOWN)
check('the finding explains the old behaviour',
      'nine hundred days' in A.grade_break_glass(900)[1])

# 2. truthiness read as a control
check('a real True is a claim', A.grade_boolean_control(True, 'x')[0] == A.CLAIM)
check('a real False is a finding', A.grade_boolean_control(False, 'x')[0] == A.BAD)
for truthy in ('planned', 'partial', 'yes', 1, [1], 'in progress'):
    check('the truthy value %r is NOT read as a control' % (truthy,),
          A.grade_boolean_control(truthy, 'x')[0] == A.UNKNOWN)
check('the shipped "planned" value is unstated in the full audit',
      verdict_for(dict(BASE, session_recording='planned'),
                  'session_recording') == A.UNKNOWN)
check('and is not a claim', verdict_for(dict(BASE, session_recording='planned'),
                                        'session_recording') != A.CLAIM)
check('a real True for session recording is a claim',
      verdict_for(dict(BASE, session_recording=True),
                  'session_recording') == A.CLAIM)
check('the explanation names the old OK behaviour',
      'would have printed OK' in A.grade_boolean_control('planned', 'x')[1])

# 3. the blocklist
check('an unrecognised secrets location is unstated, not silent',
      verdict_for(dict(BASE, secrets_location='vault'),
                  'secrets_location') == A.UNKNOWN)
check('an unrecognised value is never a claim',
      verdict_for(dict(BASE, secrets_location='a share everyone can read'),
                  'secrets_location') == A.UNKNOWN)
check('the known-bad value is still a finding',
      verdict_for(dict(BASE, secrets_location='git-repo'),
                  'secrets_location') == A.BAD)
check('a recognised good value is a claim, not a pass',
      verdict_for(dict(BASE, secrets_location='secret-manager'),
                  'secrets_location') == A.CLAIM)
check('the unrecognised explanation says it is not approval',
      'not approval' in next(r for r in A.audit(dict(BASE, secrets_location='vault'))
                             if r['field'] == 'secrets_location')['why'])
check('a missing field is unstated',
      verdict_for({k: v for k, v in BASE.items() if k != 'secrets_location'},
                  'secrets_location') == A.UNKNOWN)
check('a missing field says the model does not mention it',
      'does not mention this at all' in
      next(r for r in A.audit({}) if r['field'] == 'secrets_location')['why'])
check('every check survives a completely empty model',
      all(r['verdict'] == A.UNKNOWN for r in A.audit({})))
check('an empty model certifies nothing',
      A.summarise(A.audit({}))['certified'] == 0)

# ===========================================================================
# the two label-certification defects TE-0521 names
# ===========================================================================
check('TACACS+ alone is unstated, not an OK',
      verdict_for(dict(BASE, device_auth='tacacs+'), 'device_auth') == A.UNKNOWN)
check('and the explanation names what it does not provide',
      'does NOT give' in next(r for r in A.audit(BASE)
                              if r['field'] == 'device_auth')['why'])
check('and it still credits per-command authorisation',
      'per-command authorisation' in next(r for r in A.audit(BASE)
                                          if r['field'] == 'device_auth')['why'])
check('TACACS+ over TLS is a claim',
      verdict_for(dict(BASE, device_auth='tacacs+-over-tls'),
                  'device_auth') == A.CLAIM)
check('RADIUS is a finding',
      verdict_for(dict(BASE, device_auth='radius'), 'device_auth') == A.BAD)
check('local-only accounts are a finding',
      verdict_for(dict(BASE, device_auth='local-only'), 'device_auth') == A.BAD)

check('plain certificates are UNSTATED, not a pass',
      verdict_for(dict(BASE, ssh_model='certificates'), 'ssh_model') == A.UNKNOWN)
check('and the explanation says the CA removal revokes everyone',
      'EVERY certificate' in next(r for r in A.audit(BASE)
                                  if r['field'] == 'ssh_model')['why'])
check('and it points at the lab that executes it',
      'Lab 52.3' in next(r for r in A.audit(BASE)
                         if r['field'] == 'ssh_model')['why'])
check('raw keys are a finding',
      verdict_for(dict(BASE, ssh_model='keys'), 'ssh_model') == A.BAD)
check('certificates with a KRL are a claim',
      verdict_for(dict(BASE, ssh_model='certificates-with-krl'),
                  'ssh_model') == A.CLAIM)
check('short-lived certificates are a claim',
      verdict_for(dict(BASE, ssh_model='certificates-short-lived'),
                  'ssh_model') == A.CLAIM)

# ===========================================================================
# nothing is ever certified, and there is no OK
# ===========================================================================
check('the module defines no PASS verdict', not hasattr(A, 'PASS'))
check('the module defines no OK verdict', not hasattr(A, 'OK'))
check('the three verdicts are distinct',
      len({A.BAD, A.UNKNOWN, A.CLAIM}) == 3)
perfect = {'shared_admin_account': False,
           'oob_reachable_from_production': False,
           'secrets_location': 'hsm',
           'ssh_model': 'certificates-with-krl',
           'device_auth': 'tacacs+-over-tls',
           'break_glass_tested_days_ago': 1,
           'session_recording': True,
           'mfa_on_admin_access': True}
s = A.summarise(A.audit(perfect))
check('even a flawless description yields no findings', s['counts'][A.BAD] == 0)
check('and still certifies nothing', s['certified'] == 0)
check('and every row is a CLAIM rather than a pass',
      s['counts'][A.CLAIM] == len(A.CHECKS))
check('every claim carries the evidence that would settle it',
      all(len(r['evidence_required']) > 20 for r in s['claimed']))
worst = {k: (True if isinstance(v, bool) else v) for k, v in perfect.items()}
worst.update({'shared_admin_account': True,
              'oob_reachable_from_production': True,
              'secrets_location': 'git-repo', 'ssh_model': 'keys',
              'device_auth': 'radius', 'break_glass_tested_days_ago': None,
              'session_recording': False, 'mfa_on_admin_access': False})
sw = A.summarise(A.audit(worst))
check('a thoroughly bad description yields findings on every row',
      sw['counts'][A.BAD] == len(A.CHECKS))
check('and still certifies nothing', sw['certified'] == 0)
check('the model can therefore come out either way',
      s['counts'][A.BAD] == 0 and sw['counts'][A.BAD] == len(A.CHECKS))

# ===========================================================================
# structure
# ===========================================================================
check('every check has a question', all(c.question.endswith('?') for c in A.CHECKS))
check('every check states required evidence',
      all(len(c.evidence) > 20 for c in A.CHECKS))
check('every check has a field', all(c.field for c in A.CHECKS))
check('check fields are unique', len({c.field for c in A.CHECKS}) == len(A.CHECKS))
check('a check with neither recognised values nor a grader is refused',
      raises(A.Check, 'x', 'q?', None, 'evidence'))
check('a check mapping a value to an unknown verdict is refused',
      raises(A.Check, 'x', 'q?', {'a': ('EXCELLENT', 'why')}, 'evidence'))
check('a non-dictionary model is refused', raises(A.audit, ['not', 'a', 'dict']))
check('the shipped model omits MFA, so the report has an honest unknown',
      'mfa_on_admin_access' not in A.MODEL)
check('summarise partitions every result',
      sum(A.summarise(A.audit(BASE))['counts'].values()) == len(A.CHECKS))

rep = A.build_report()
check('the report records the evidence category',
      'STATIC REVIEW' in rep['evidence_category'])
check('the report says nothing was touched',
      'No device' in rep['evidence_category'])
check('the report carries caveats', len(rep['caveats']) >= 5)
check('a caveat says it audits a description',
      any('AUDITS A DESCRIPTION' in c for c in rep['caveats']))
check('a caveat says unstated is not a pass',
      any('It is not a pass' in c for c in rep['caveats']))
check('a caveat refuses a maturity score',
      any('maturity score' in c for c in rep['caveats']))
check('the report JSON-serialises', isinstance(json.dumps(rep), str))
text = A.report_text(rep)
check('the text names four sections',
      all(x in text for x in ('A.', 'B.', 'C.', 'D.')))
check('the text states zero certified', '0 CERTIFIED' in text)
check('the text says the number will always be zero',
      'always be zero' in text)
check('the text names the two rows that used to be silent',
      'break_glass_tested_days_ago: 900' in text and 'ssh_model: certificates' in text)
check('the text never prints an OK verdict line', '[OK' not in text)
check('the text discloses what it does not establish', 'does NOT establish' in text)
check('no report line exceeds eighty characters',
      all(len(x) <= 80 for x in text.splitlines()))

out = subprocess.run([sys.executable, 'access_audit.py', '--json'],
                     capture_output=True, text=True, timeout=120)
check('--json exits zero', out.returncode == 0)
check('--json parses', isinstance(json.loads(out.stdout), dict))
plain = subprocess.run([sys.executable, 'access_audit.py'],
                       capture_output=True, text=True, timeout=120)
check('plain run exits zero', plain.returncode == 0)
check('plain run is not JSON', not plain.stdout.lstrip().startswith('{'))

print('access_audit: %d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: ' + f)
sys.exit(1 if FAILED else 0)
