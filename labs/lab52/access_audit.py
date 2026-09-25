#!/usr/bin/env python3
"""Lab 52.1 --- auditing a DESCRIPTION, and what that can and cannot establish.

WHY THIS LAB WAS REBUILT
------------------------
The shipped script read a dictionary describing a management-access design and
printed findings. Three things were wrong with how it read it, and the third is
the one that matters.

  PRESENCE WAS READ AS ADEQUACY.  `if m["break_glass_tested_days_ago"] is None`
  raised a finding when the field was empty --- the right direction --- but ANY
  number silenced it. A break-glass path last tested nine hundred days ago
  audited as satisfactory. The script asked whether a field was POPULATED, not
  whether its value was ACCEPTABLE.

  TRUTHINESS WAS READ AS A CONTROL.  `if m["session_recording"]:` printed an OK
  for any truthy value, so the string "planned" would have been recorded as a
  control in place.

  AND THE WHOLE THING WAS A BLOCKLIST.  `if m["secrets_location"] ==
  "git-repo"` fires on one known-bad value. Write anything else --- "vault",
  "a share everyone can read", "not sure" --- and NO finding fires at all,
  which reads as approval. An audit whose silence means "I did not recognise
  that" and whose output looks like "nothing wrong here" is worse than no
  audit, because it is quoted.

Underneath all three sits the finding this lab is named for: A SCRIPT CANNOT
CERTIFY A CONTROL FROM A LABEL. It is reading a description somebody typed. The
most it can honestly do is sort that description into three piles --- what is
wrong, what the description does not say, and what the description CLAIMS and
would need evidence for --- and then say what evidence would settle each claim.
The rebuilt script does exactly that, and it never prints OK.

    python3 access_audit.py
    python3 access_audit.py --json
    python3 test_access_audit.py

No device, bastion, directory, vault or log was touched. This reads a dictionary.
"""
import argparse
import json
import sys
import textwrap


class AuditError(ValueError):
    """The described access model cannot be audited as given."""


# Verdicts. There is deliberately no PASS and no OK.
BAD = 'FINDING'          # the description states something wrong
UNKNOWN = 'UNSTATED'     # the description does not answer the question
CLAIM = 'CLAIMED'        # the description states something good, unevidenced


class Check:
    """One question, the answers it recognises, and what evidence would settle it.

    `recognised` maps an exact value to (verdict, explanation). Anything not in
    that map is UNSTATED --- never silence, and never approval.
    """

    def __init__(self, field, question, recognised, evidence,
                 grader=None, section=None):
        if not recognised and grader is None:
            raise AuditError('check %r recognises no values and has no grader'
                             % field)
        for v, (verdict, why) in (recognised or {}).items():
            if verdict not in (BAD, UNKNOWN, CLAIM):
                raise AuditError('check %r maps %r to unknown verdict %r'
                                 % (field, v, verdict))
        self.field = field
        self.question = question
        self.recognised = recognised or {}
        self.evidence = evidence
        self.grader = grader
        self.section = section

    def run(self, model):
        if self.field not in model:
            return {'field': self.field, 'question': self.question,
                    'stated': None, 'verdict': UNKNOWN,
                    'why': 'The model does not mention this at all.',
                    'evidence_required': self.evidence}
        value = model[self.field]
        if self.grader is not None:
            verdict, why = self.grader(value)
        else:
            hit = self.recognised.get(value if not isinstance(value, bool)
                                      else bool(value))
            if hit is None:
                verdict, why = UNKNOWN, (
                    'The model says %r, which this check does not recognise. '
                    'That is not approval: an unrecognised answer is an '
                    'unanswered question.' % (value,))
            else:
                verdict, why = hit
        return {'field': self.field, 'question': self.question,
                'stated': value, 'verdict': verdict, 'why': why,
                'evidence_required': self.evidence}


# ---------------------------------------------------------------------------
# graders, for the fields where a VALUE rather than a label decides
# ---------------------------------------------------------------------------
def grade_break_glass(value, stale_after_days=180):
    """Days since the break-glass path was last tested.

    This is the check the old script got backwards. None is a finding, and so
    is a number that is too large --- which is the case it silently passed.
    """
    if value is None:
        return BAD, ('Never tested. A break-glass path that has not been '
                     'exercised is a plan, and you find out whether a plan '
                     'works on the night the primary path is down.')
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return UNKNOWN, ('The model says %r, which is not a number of days.'
                         % (value,))
    if value < 0:
        return UNKNOWN, 'A negative number of days is not an answer.'
    if value > stale_after_days:
        return BAD, ('Last tested %g days ago, which is beyond the %d-day '
                     'threshold this check uses. The old version of this lab '
                     'accepted ANY number here, so a path last exercised '
                     'nine hundred days ago audited as satisfactory.'
                     % (value, stale_after_days))
    return CLAIM, ('Tested %g days ago, within the %d-day threshold. This is '
                   'a claim in a dictionary; the evidence is the test record.'
                   % (value, stale_after_days))


def grade_boolean_control(value, name):
    """A control that is either in place or not --- and only those two.

    The old script used `if m[field]:`, so any truthy value printed an OK.
    Here anything other than a real boolean is UNSTATED.
    """
    if value is True:
        return CLAIM, ('The model says this is in place. That is a claim '
                       'about %s, not evidence of it.' % name)
    if value is False:
        return BAD, 'The model says this is not in place.'
    return UNKNOWN, ('The model says %r rather than true or false. A value '
                     'like "planned" or "partial" is not a control, and the '
                     'old version of this lab would have printed OK for it.'
                     % (value,))


CHECKS = [
    Check('shared_admin_account',
          'Is administrative access attributable to an individual?',
          {True: (BAD, 'A shared account. Every action is attributable to '
                       '"admin" and to nobody, which removes attribution from '
                       'the audit trail and from the incident review.'),
           False: (CLAIM, 'The model says accounts are individual. The '
                          'evidence is the account list and the absence of a '
                          'shared credential in the vault.')},
          'The directory export, and a check that no shared credential exists.'),

    Check('oob_reachable_from_production',
          'Is the out-of-band path actually out of band?',
          {True: (BAD, 'A route bridges the out-of-band network to production. '
                       'The separation that justified building it is gone, and '
                       'the path you would use to recover from a compromise '
                       'shares the compromise.'),
           False: (CLAIM, 'The model says the paths are separate. Separation '
                          'is a claim about routing, addressing, physical '
                          'media and power, and it is the one most often '
                          'refuted by a traceroute.')},
          'A traceroute from production to the OOB address that fails, plus '
          'the routing and firewall configuration that makes it fail.'),

    Check('secrets_location',
          'Where do automation credentials live?',
          {'git-repo': (BAD, 'Credentials in the repository: the management '
                             'plane in machine-readable form, copied to every '
                             'clone and every build agent, and present in the '
                             'history after they are deleted.'),
           'secret-manager': (CLAIM, 'The model names a secret manager. That '
                                     'moves the question rather than settling '
                                     'it: what unseals it, who can read it, '
                                     'and what happens when it is unavailable?'),
           'hsm': (CLAIM, 'The model names an HSM. Same follow-up questions, '
                          'plus what happens when the device fails.')},
          'The repository history scanned for secrets, and the access policy '
          'of whatever holds them now.'),

    Check('ssh_model',
          'Can ONE person be removed without removing everyone?',
          {'keys': (BAD, 'Authorised-keys files. Removing a leaver means '
                         'visiting every device that ever held their key.'),
           'certificates': (UNKNOWN, 'Certificates alone do not answer this. '
                                     'Removing the CA relationship revokes '
                                     'EVERY certificate that CA issued --- the '
                                     'whole team. Revoking one person needs a '
                                     'KRL distributed to every device, or '
                                     'lifetimes short enough that waiting is '
                                     'acceptable. State which. See Lab 52.3, '
                                     'which executes all three.'),
           'certificates-with-krl': (CLAIM, 'A KRL is the mechanism that '
                                            'revokes one holder. The evidence '
                                            'is a distribution record showing '
                                            'every device has the current '
                                            'list.'),
           'certificates-short-lived': (CLAIM, 'Short lifetimes revoke by '
                                               'expiry. The evidence is the '
                                               'lifetime, and the availability '
                                               'of the issuing service, which '
                                               'is now on the critical path '
                                               'for every login.')},
          'A rehearsed removal of one named person, timed, with the other '
          'accounts shown still working.'),

    Check('device_auth',
          'What does the device-administration protocol actually protect?',
          {'tacacs+': (UNKNOWN, 'TACACS+ gives per-command authorisation, '
                                'which is a real advantage and is why it is '
                                'the right choice here. What it does NOT give '
                                'is encryption: the body is obfuscated with a '
                                'keystream derived from the session, key, '
                                'version and sequence, it is malleable, and '
                                'there is no integrity field. Lab 52.2 '
                                'executes all three. State the transport.'),
           'tacacs+-over-tls': (CLAIM, 'The transport supplies the '
                                       'confidentiality and integrity the '
                                       'protocol does not. Evidence is the '
                                       'negotiated TLS parameters.'),
           'radius': (BAD, 'RADIUS obfuscates only the password attribute and '
                           'leaves the rest in clear, and gives no per-command '
                           'authorisation.'),
           'local-only': (BAD, 'Local accounts on every device: no central '
                               'revocation, no central audit, and a password '
                               'list that ages.')},
          'A packet capture on the management path, and the TLS parameters if '
          'any.'),

    Check('break_glass_tested_days_ago',
          'When was the break-glass path last exercised?',
          None,
          'The dated test record, naming who ran it and what failed.',
          grader=grade_break_glass),

    Check('session_recording',
          'Are administrative sessions recorded?',
          None,
          'A recording retrieved for a named session, and the policy that '
          'stops an administrator deleting their own.',
          grader=lambda v: grade_boolean_control(v, 'session recording')),

    Check('mfa_on_admin_access',
          'Is a second factor required for administrative access?',
          None,
          'An authentication log showing the factor, for the bastion and for '
          'any path that bypasses it.',
          grader=lambda v: grade_boolean_control(v, 'MFA')),
]


# The described model. The old version of this lab shipped the first seven of
# these fields; mfa_on_admin_access is deliberately ABSENT, so the report has
# something to be honest about not knowing.
MODEL = {
    'shared_admin_account': True,
    'oob_reachable_from_production': True,
    'device_auth': 'tacacs+',
    'secrets_location': 'git-repo',
    'ssh_model': 'certificates',
    'break_glass_tested_days_ago': 900,
    'session_recording': 'planned',
}


def audit(model, checks=None):
    if not isinstance(model, dict):
        raise AuditError('an access model is a dictionary of stated answers')
    return [c.run(model) for c in (checks or CHECKS)]


def summarise(results):
    out = {BAD: [], UNKNOWN: [], CLAIM: []}
    for r in results:
        out[r['verdict']].append(r)
    return {'findings': out[BAD], 'unstated': out[UNKNOWN],
            'claimed': out[CLAIM],
            'counts': {k: len(v) for k, v in out.items()},
            'certified': 0}


def build_report(model=None):
    model = MODEL if model is None else model
    results = audit(model)
    s = summarise(results)
    return {
        'model': model,
        'results': results,
        'summary': s,
        'evidence_category':
            'STATIC REVIEW of a dictionary. No device, bastion, directory, '
            'vault, log or network was touched, and nothing was measured.',
        'caveats': [
            'THIS AUDITS A DESCRIPTION, NOT AN ESTATE. Everything it calls '
            'CLAIMED is a sentence somebody typed. The script cannot tell a '
            'true claim from a hopeful one, which is why it certifies nothing '
            'and prints no OK.',
            'An UNSTATED verdict means the model did not answer the question '
            'or gave an answer this check does not recognise. It is not a '
            'pass, and it is not a fail either --- it is the honest output of '
            'a check that was not given enough to decide.',
            'The staleness threshold for the break-glass test is a stated '
            'input, not a standard. Choose your own and defend it; the point '
            'is that a threshold exists at all, because the version this '
            'replaces accepted any number.',
            'The recognised values are a starting list. A real estate will '
            'have answers none of these checks knows, and those come back '
            'UNSTATED by design rather than silently passing.',
            'Nothing here is a maturity score, a percentage or a grade. A '
            'count of findings against a count of questions is not a '
            'percentage of security, and turning it into one would be the '
            'same mistake in a different font.',
        ],
    }


def _wrap(lines, text, indent='  '):
    lines.extend(textwrap.wrap(text, width=74, initial_indent=indent,
                               subsequent_indent=indent))


def report_text(rep):
    L = []
    s = rep['summary']
    L.append('Management access, as DESCRIBED (Chapter 52)')
    L.append('This reads a dictionary. It certifies nothing and prints no OK.')
    L.append('')
    L.append('A. What the description gets wrong')
    L.append('-' * 74)
    for r in s['findings']:
        L.append('  %s' % r['question'])
        L.append('      stated: %r' % (r['stated'],))
        _wrap(L, r['why'], indent='      ')
        _wrap(L, 'evidence that would settle it: ' + r['evidence_required'],
              indent='      ')
        L.append('')
    if not s['findings']:
        L.append('  Nothing in the description is stated wrongly.')
        L.append('')
    L.append('B. What the description does not say')
    L.append('-' * 74)
    for r in s['unstated']:
        L.append('  %s' % r['question'])
        L.append('      stated: %r' % (r['stated'],))
        _wrap(L, r['why'], indent='      ')
        L.append('')
    L.append('C. What the description claims, and what would evidence it')
    L.append('-' * 74)
    for r in s['claimed']:
        L.append('  %s' % r['question'])
        L.append('      stated: %r' % (r['stated'],))
        _wrap(L, r['why'], indent='      ')
        _wrap(L, 'evidence: ' + r['evidence_required'], indent='      ')
        L.append('')
    if not s['claimed']:
        L.append('  The description claims nothing this audit recognises.')
        L.append('')
    L.append('D. The count, and what it is not')
    L.append('-' * 74)
    c = s['counts']
    L.append('  %d finding(s), %d unanswered, %d claimed, %d CERTIFIED'
             % (c[BAD], c[UNKNOWN], c[CLAIM], s['certified']))
    L.append('')
    _wrap(L, 'The last number is zero and will always be zero. A script '
             'reading a dictionary cannot certify a control; it can only sort '
             'what it was told. The version of this lab that this replaces '
             'printed OK for two rows --- TACACS+ because the label said '
             'tacacs+, and session recording because the value was truthy --- '
             'and printed nothing at all for values it did not recognise, '
             'which reads as approval and is how an audit becomes a document '
             'quoted in a board pack.')
    L.append('')
    _wrap(L, 'Note especially the two rows above that used to be silent. '
             '"break_glass_tested_days_ago: 900" was accepted by the old '
             'script because 900 is not None. "ssh_model: certificates" '
             'removed the old finding entirely, awarding a clean bill to a '
             'model that still cannot remove one person without removing '
             'everybody.')
    L.append('')
    L.append('What this does NOT establish')
    L.append('-' * 74)
    for x in rep['caveats']:
        L.extend(textwrap.wrap(x, width=74, initial_indent='- ',
                               subsequent_indent='  '))
    return '\n'.join(L)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--json', action='store_true', help='emit the report as JSON')
    a = p.parse_args(argv)
    try:
        rep = build_report()
    except AuditError as exc:
        print('cannot evaluate: %s' % exc, file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=2) if a.json else report_text(rep))
    return 0


if __name__ == '__main__':
    sys.exit(main())
