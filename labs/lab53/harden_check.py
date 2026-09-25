#!/usr/bin/env python3
"""Lab 53.1 --- a hardening questionnaire, and why the shipped one failed OPEN.

WHAT THIS IS, STATED FIRST
--------------------------
This is NOT a compliance scanner. There is no collector, no parser, no session
to a device and no verification of anything. It reads a dictionary that a human
typed, describing what they BELIEVE a device is configured to do, and sorts that
description into three piles. The shipped version's docstring said it "checks a
device's live configuration" and its README said to "run it against a device's
live config". Neither was true, and a reader who believed it would have quoted a
questionnaire as an audit.

WHY THIS LAB WAS REBUILT: IT FAILED OPEN
----------------------------------------
The shipped script had two kinds of check in one file, and only one of them was
sound.

  THE BASELINE LOOP WAS AN ALLOWLIST and it worked. `if dev.get(key) != want`
  raises a finding for the wrong value, for a typo, and for a missing key alike.
  Nothing slips past it silently.

  THE TWO "NUANCE CHECKS" WERE BLOCKLISTS and they failed OPEN:

      if dev.get("urpf_edge") == "loose":            -> MEDIUM
      if dev.get("bgp_authentication") == "md5":     -> LOW

  Each recognises exactly one value, and that value is the MIDDLING one. Set
  `urpf_edge` to "disabled" and `bgp_authentication` to "none" --- make the
  device strictly worse --- and both checks go silent. Measured on the shipped
  script: the described device produced SEVEN findings; the same device with
  uRPF off and BGP unauthenticated produced FIVE. The report improved because
  the device got worse. That is the FR-0050 failure: not a check that cannot
  fail, but a check that returns REASSURANCE from a correct input.

  A blocklist in an audit is silence-as-approval. Its quiet means "I did not
  recognise that string", and it is read as "nothing wrong here".

WHAT ELSE CHANGED
-----------------
  ONE BASELINE FOR EVERY DEVICE WAS WRONG (chapter 53 §1 overstated this).
  A single-homed access edge, a PE facing customers, an internal route
  reflector and an out-of-band management host do not have the same correct
  answers. Strict uRPF belongs on the first and is an outage on the third.
  So baselines here are VERSIONED and selected by ROLE, and a control that does
  not apply to a role is reported as NOT APPLICABLE rather than as a pass.

  A PLATFORM DEFAULT IS NOT AN ABSENT CONTROL. `copp_configured: False` means
  something different on IOS-XR, where LPTS polices punted traffic out of the
  box, than on a platform with no default protection. The record therefore
  carries the platform, and the finding says which case it is.

  A DESCRIPTION IS NOT EVIDENCE. Every control answer carries where it came
  from --- `asserted` (somebody said so), `config` (read out of a stored
  configuration) or `observed` (someone watched the control act) --- and a date.
  An answer sourced from `asserted` can never be reported as anything stronger
  than a claim, and an answer older than the staleness window is reported as
  stale whatever it says.

  THERE IS NO PASS AND NO OK in the output, for the same reason as Lab 52.1.

    python3 harden_check.py
    python3 harden_check.py --json
    python3 harden_check.py --demo-fail-open
    python3 test_harden_check.py

No device was touched. This reads a dictionary.
"""
import argparse
import datetime as _dt
import json
import sys
import textwrap


class RecordError(ValueError):
    """The device record cannot be assessed as given."""


# Verdicts. There is deliberately no PASS and no OK.
BAD = 'FINDING'            # the record states something wrong
UNKNOWN = 'UNSTATED'       # the record does not answer the question
CLAIM = 'CLAIMED'          # the record states something good, unevidenced
NA = 'NOT APPLICABLE'      # the control is not expected for this role

# How much an answer's provenance is worth. A questionnaire cannot promote
# itself: `asserted` is the weakest and is what an unsourced answer gets.
SOURCES = {
    'asserted': 'somebody stated this; nothing was read or watched',
    'config': 'read out of a stored configuration file or backup',
    'observed': 'someone watched the control act, or read a live counter',
}


class Control:
    """One question, the answers it recognises, and what would settle it.

    `answers` maps an exact value to (verdict, explanation). ANYTHING not in
    that map --- an unrecognised string, a typo, None, a missing key --- is
    UNSTATED. That is the whole point: this class cannot go silent. There is
    no code path in `assess` that returns nothing.
    """

    def __init__(self, key, question, answers, evidence,
                 roles=None, section=''):
        if not answers:
            raise RecordError('control %r recognises no answers' % key)
        for value, (verdict, _why) in answers.items():
            if verdict not in (BAD, UNKNOWN, CLAIM):
                raise RecordError(
                    'control %r maps %r to %r, which is not a verdict'
                    % (key, value, verdict))
        self.key = key
        self.question = question
        self.answers = answers
        self.evidence = evidence
        self.roles = frozenset(roles) if roles else None   # None == every role
        self.section = section

    def applies_to(self, role):
        return self.roles is None or role in self.roles

    def assess(self, value):
        """Return (verdict, explanation). Never returns None, never silent."""
        try:
            hashable = value if not isinstance(value, (list, dict, set)) else None
        except TypeError:                                   # pragma: no cover
            hashable = None
        if hashable is not None and hashable in self.answers:
            return self.answers[hashable]
        if value is None:
            return UNKNOWN, 'the record does not answer this'
        return UNKNOWN, ('the record says %r, which this baseline does not '
                         'recognise --- it is neither accepted nor rejected, '
                         'so it is unassessed' % (value,))


# --------------------------------------------------------------------------
# The controls. Every one is an ALLOWLIST: it names the answers it recognises
# and everything else falls through to UNSTATED.
# --------------------------------------------------------------------------

CONTROLS = [
    Control(
        'telnet', 'Is a cleartext admin protocol (Telnet, HTTP) enabled?',
        {'disabled': (CLAIM, 'record states Telnet and HTTP are off'),
         'enabled': (BAD, 'cleartext administration is reachable'),
         'unknown': (UNKNOWN, 'the operator does not know')},
        'a configuration read showing no transport input telnet and no ip http server',
        section='53.1'),

    Control(
        'mgmt_reachable_from', 'From where is the management plane reachable?',
        {'oob-only': (CLAIM, 'record states management answers only on the '
                             'out-of-band network'),
         'inband-restricted': (CLAIM, 'record states in-band management is '
                                      'restricted to named sources'),
         'any-internal': (BAD, 'any internal host can reach management'),
         'internet': (BAD, 'management is reachable from the Internet'),
         'unknown': (UNKNOWN, 'the operator does not know')},
        'a scan from outside and from a user segment, dual-stack, dated '
        '(chapter 53 §7) --- and the expected-exposure record to compare it to',
        section='53.7'),

    Control(
        'secure_boot', 'Does the platform verify the boot chain?',
        {'enforced': (CLAIM, 'record states verified boot is enforced'),
         'logging-only': (BAD, 'boot measurement is recorded but not enforced: '
                               'an unsigned image still runs'),
         'unsupported': (BAD, 'platform cannot verify boot --- treat as a '
                              'higher-risk asset, do not report it as compliant'),
         'disabled': (BAD, 'platform can verify boot and does not'),
         'unknown': (UNKNOWN, 'the operator does not know')},
        'the platform command that reports anchor state and the signing '
        'authority, plus the anti-rollback and revocation position (§53.2)',
        section='53.2'),

    Control(
        'copp', 'Is to-the-CPU traffic policed?',
        {'explicit-policy': (CLAIM, 'record states an explicit control-plane '
                                    'policy is attached'),
         'platform-default': (CLAIM, 'record relies on the platform default '
                                     '(LPTS or equivalent) and has not tuned it'),
         'none': (BAD, 'no control-plane policing, explicit or default'),
         'unknown': (UNKNOWN, 'the operator does not know')},
        'per-class conformed and dropped counters read under load, with the '
        'rates expressed in the unit the platform polices in (§53.3)',
        section='53.3'),

    Control(
        'iacl_exceptions', 'Does the edge filter carry its required exceptions?',
        {'with-exceptions': (CLAIM, 'record states authorised peers, ICMP '
                                    'unreachable/fragmentation-needed and '
                                    'time-exceeded are permitted'),
         'blanket-deny': (BAD, 'a filter denying everything to infrastructure '
                               'space breaks external BGP and black-holes path '
                               'MTU discovery --- see Lab 53.3'),
         'none': (BAD, 'no edge filter protecting infrastructure space'),
         'unknown': (UNKNOWN, 'the operator does not know')},
        'the permit lines themselves, and a test that an authorised peer '
        'establishes while an unauthorised source does not (Lab 53.3)',
        roles=('pe', 'access-edge'), section='53.4'),

    Control(
        'source_validation', 'How is the customer-facing source address validated?',
        {'per-customer-prefix-filter': (CLAIM, 'record states the interface '
                                               'permits only the prefixes the '
                                               'customer is allocated'),
         'urpf-strict': (CLAIM, 'record states strict uRPF, which is sound only '
                                'where the reverse path really is symmetric'),
         'urpf-loose': (BAD, 'loose uRPF tests only that a route exists: a '
                             'spoofed source with a route passes it '
                             '--- measured in Lab 53.2'),
         'urpf-feasible-path': (CLAIM, 'record states feasible-path uRPF '
                                       '(RFC 8704); confirm the platform '
                                       'implements it as specified'),
         'none': (BAD, 'no source-address validation at the customer edge'),
         'unknown': (UNKNOWN, 'the operator does not know')},
        'the measured matrix of Lab 53.2 run against this interface: '
        'legitimate symmetric, legitimate asymmetric, spoofed-but-routed and '
        'unrouted sources',
        roles=('pe', 'access-edge'), section='53.5'),

    Control(
        'routing_authentication', 'Are routing adjacencies authenticated?',
        {'tcp-ao': (CLAIM, 'record states TCP-AO with a keychain attached to '
                           'the neighbour'),
         'tcp-md5': (BAD, 'TCP-MD5 is legacy debt: retire it (§51.4)'),
         'none': (BAD, 'adjacencies accept unauthenticated messages'),
         'not-supported-both-ends': (BAD, 'one end cannot do it --- this is an '
                                          'exception to register and schedule, '
                                          'not a compliant state'),
         'unknown': (UNKNOWN, 'the operator does not know')},
        'both ends of the session showing the same mechanism, plus a rollover '
        'test and a negative test with the wrong key (§53.6)',
        section='53.6'),

    Control(
        'gtsm', 'Is a TTL/hop-limit check configured on the session?',
        {'enforced': (CLAIM, 'record states GTSM with a stated hop count'),
         'none': (BAD, 'no TTL check: an off-path remote source is not filtered'),
         'unknown': (UNKNOWN, 'the operator does not know')},
        'the configured hop count and the platform\'s threshold semantics, '
        'which differ between vendors (RFC 5082, §53.6)',
        section='53.6'),

    Control(
        'logging_offbox', 'Do logs leave the device as they are produced?',
        {'streamed-and-monitored': (CLAIM, 'record states logs stream off-box '
                                           'and a gap in the stream is alerted'),
         'streamed-unmonitored': (BAD, 'logs stream off-box but nothing notices '
                                       'when the stream stops --- silence is '
                                       'indistinguishable from quiet'),
         'local-only': (BAD, 'logs live only where an intruder can edit them'),
         'unknown': (UNKNOWN, 'the operator does not know')},
        'a deliberately dropped collector, and the alert it raised; plus the '
        'clock skew between device and collector (§53.8)',
        section='53.8'),

    Control(
        'drift_check', 'How often is the running configuration re-checked?',
        {'continuous': (CLAIM, 'record states an automated check with a stated '
                               'interval'),
         'on-change': (CLAIM, 'record states a check triggered by change events; '
                              'confirm it catches changes made outside the tool'),
         'manual': (BAD, 'drift is found when somebody looks'),
         'never': (BAD, 'the device is hardened as of the day it was built'),
         'unknown': (UNKNOWN, 'the operator does not know')},
        'the interval, the scope it covers, and the register of accepted '
        'exceptions it is allowed to ignore (§53.9)',
        section='53.9'),
]

CONTROLS_BY_KEY = {c.key: c for c in CONTROLS}

ROLES = ('pe', 'access-edge', 'route-reflector', 'oob-management')

# A control the baseline does not list for a role is NOT APPLICABLE, which is
# reported as its own verdict. It is not a pass.
BASELINE_VERSION = '53-baseline-2026.1'


# --------------------------------------------------------------------------
# The record. A dictionary a human typed --- and it says so.
# --------------------------------------------------------------------------

DEVICE = {
    'hostname': 'ald-core-01',
    'role': 'pe',
    'platform': 'ios-xe',
    'record_source': 'asserted',
    'record_date': '2026-03-04',
    'controls': {
        'telnet': 'enabled',
        'mgmt_reachable_from': 'internet',
        'secure_boot': 'enforced',
        'copp': 'none',
        'iacl_exceptions': 'blanket-deny',
        'source_validation': 'urpf-loose',
        'routing_authentication': 'tcp-md5',
        'gtsm': 'none',
        'logging_offbox': 'local-only',
        'drift_check': 'manual',
    },
}

STALE_AFTER_DAYS = 180


def _parse_date(text, what):
    try:
        return _dt.date.fromisoformat(text)
    except (TypeError, ValueError):
        raise RecordError('%s is %r; an ISO date (YYYY-MM-DD) is required so '
                          'the answer can be aged' % (what, text))


def assess(record, today=None, stale_after_days=STALE_AFTER_DAYS):
    """Assess one device record. Returns a dict; raises RecordError on nonsense.

    Every control in CONTROLS produces exactly one entry, so the output length
    is fixed by the baseline and not by how much the record happened to say.
    """
    if not isinstance(record, dict):
        raise RecordError('a device record must be a dictionary')
    role = record.get('role')
    if role not in ROLES:
        raise RecordError(
            'role is %r; the baseline is selected by role and one of %s is '
            'required. A single baseline applied to unlike devices is the '
            'chapter 53 §1 overstatement this lab exists to correct.'
            % (role, ', '.join(repr(r) for r in ROLES)))
    source = record.get('record_source', 'asserted')
    if source not in SOURCES:
        raise RecordError('record_source is %r; expected one of %s'
                          % (source, ', '.join(sorted(SOURCES))))
    today = today or _dt.date.today()
    taken = _parse_date(record.get('record_date'), 'record_date')
    age = (today - taken).days
    if age < 0:
        raise RecordError('record_date %s is in the future relative to %s'
                          % (taken, today))

    answers = record.get('controls')
    if not isinstance(answers, dict):
        raise RecordError('the record has no "controls" dictionary')

    unknown_keys = sorted(set(answers) - set(CONTROLS_BY_KEY))

    results = []
    for control in CONTROLS:
        if not control.applies_to(role):
            results.append({
                'key': control.key, 'section': control.section,
                'verdict': NA, 'stated': answers.get(control.key),
                'why': 'the %s baseline does not expect this control on a %s'
                       % (BASELINE_VERSION, role),
                'evidence': control.evidence,
            })
            continue
        verdict, why = control.assess(answers.get(control.key))
        results.append({
            'key': control.key, 'section': control.section,
            'verdict': verdict, 'stated': answers.get(control.key),
            'why': why, 'evidence': control.evidence,
        })

    # Platform default note: an absent explicit policy is a different statement
    # on a platform that polices punted traffic by default.
    notes = []
    platform = record.get('platform')
    copp = answers.get('copp')
    if platform == 'ios-xr' and copp in ('none', 'platform-default'):
        notes.append(
            'platform is ios-xr, where LPTS polices punted traffic without an '
            'explicit policy. Confirm the flow rates rather than reading the '
            'absence of a policy as an absent control (§53.3).')
    if platform != 'ios-xr' and copp == 'platform-default':
        notes.append(
            'the record claims a platform default on %r. Name the default and '
            'read its counters; "the vendor protects it" is not a control until '
            'you can show the rate it enforces (§53.3).' % (platform,))
    if age > stale_after_days:
        notes.append(
            'the record is %d days old (limit %d). Hardening is a state that '
            'decays; every CLAIMED answer below is a claim about a device as it '
            'was on %s (§53.9).' % (age, stale_after_days, taken))
    if source == 'asserted':
        notes.append(
            'record_source is "asserted": %s. Nothing below is evidence; the '
            'CLAIMED answers are the ones to go and check first.'
            % SOURCES['asserted'])
    for key in unknown_keys:
        notes.append(
            'the record answers %r, which is not a control in %s. It was NOT '
            'assessed --- an answer this baseline does not know about cannot '
            'count for or against the device.' % (key, BASELINE_VERSION))

    counts = {}
    for r in results:
        counts[r['verdict']] = counts.get(r['verdict'], 0) + 1

    return {
        'hostname': record.get('hostname'), 'role': role, 'platform': platform,
        'baseline': BASELINE_VERSION, 'record_source': source,
        'record_date': taken.isoformat(), 'record_age_days': age,
        'assessed_on': today.isoformat(),
        'results': results, 'notes': notes, 'counts': counts,
        'unassessed_keys': unknown_keys,
    }


# --------------------------------------------------------------------------
# The demonstration: the shipped blocklist beside the rebuilt allowlist.
# --------------------------------------------------------------------------

def _shipped_nuance_checks(controls):
    """The two blocklist checks exactly as the shipped script wrote them."""
    out = []
    if controls.get('source_validation') == 'urpf-loose':
        out.append('uRPF loose where strict may belong')
    if controls.get('routing_authentication') == 'tcp-md5':
        out.append('BGP auth is TCP-MD5 -- legacy debt')
    return out


CASES = (
    ('uRPF loose, BGP MD5',
     {'source_validation': 'urpf-loose', 'routing_authentication': 'tcp-md5'}),
    ('uRPF OFF, BGP UNAUTHENTICATED',
     {'source_validation': 'none', 'routing_authentication': 'none'}),
    ('answers the checks never met',
     {'source_validation': 'we do uRPF I think',
      'routing_authentication': 'the sha one'}),
)


def fail_open_demonstration(cases=CASES):
    """Show the shipped form going quiet where the rebuilt one cannot."""
    rows = []
    for label, controls in cases:
        shipped = _shipped_nuance_checks(controls)
        rebuilt = [CONTROLS_BY_KEY[k].assess(v)
                   for k, v in sorted(controls.items())]
        rows.append({
            'device': label,
            'shipped_said': len(shipped),
            'rebuilt_findings': sum(1 for v, _ in rebuilt if v == BAD),
            'rebuilt_unstated': sum(1 for v, _ in rebuilt if v == UNKNOWN),
        })
    return rows


# --------------------------------------------------------------------------

def _wrap(text, indent):
    # break_on_hyphens=False so that "spoofed-but-routed" and "dual-stack" are
    # not split across lines into what look like separate words.
    return textwrap.fill(text, width=78, initial_indent=indent,
                         subsequent_indent=indent, break_on_hyphens=False)


ORDER = {BAD: 0, UNKNOWN: 1, CLAIM: 2, NA: 3}


def report(result, stream=sys.stdout):
    w = stream.write
    w('Hardening questionnaire --- %s (%s, %s)\n'
      % (result['hostname'], result['role'], result['platform']))
    w('baseline %s | record %s, %s, %d days old | assessed %s\n\n'
      % (result['baseline'], result['record_source'], result['record_date'],
         result['record_age_days'], result['assessed_on']))
    w('This reads a description. It verifies nothing.\n\n')
    for r in sorted(result['results'], key=lambda r: (ORDER[r['verdict']], r['key'])):
        w('  [%-14s] %s  (§%s)\n' % (r['verdict'], r['key'], r['section']))
        w(_wrap('stated: %r --- %s' % (r['stated'], r['why']), '      ') + '\n')
        if r['verdict'] in (BAD, UNKNOWN, CLAIM):
            w(_wrap('would be settled by: %s' % r['evidence'], '      ') + '\n')
        w('\n')
    counts = result['counts']
    w('%d %s, %d %s, %d %s, %d %s.\n'
      % (counts.get(BAD, 0), BAD, counts.get(UNKNOWN, 0), UNKNOWN,
         counts.get(CLAIM, 0), CLAIM, counts.get(NA, 0), NA))
    w('There is no PASS in this vocabulary, and no total that could be read as '
      'a score.\n')
    if result['notes']:
        w('\nNotes:\n')
        for note in result['notes']:
            w(_wrap('- ' + note, '  ') + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--json', action='store_true',
                        help='emit the assessment as JSON')
    parser.add_argument('--demo-fail-open', action='store_true',
                        help='show the shipped blocklist going quiet as the '
                             'described device gets worse')
    args = parser.parse_args(argv)

    if args.demo_fail_open:
        rows = fail_open_demonstration()
        print('Two answers, read by the shipped blocklist and by the rebuilt '
              'allowlist.\nEvery number below is counted by running both, not '
              'typed into this text.\n')
        print('  %-32s %8s   %9s %9s'
              % ('what the record said', 'shipped', 'FINDING', 'UNSTATED'))
        for row in rows:
            print('  %-32s %8d   %9d %9d'
                  % (row['device'], row['shipped_said'],
                     row['rebuilt_findings'], row['rebuilt_unstated']))
        first, worse, unmet = rows
        print()
        print(_wrap(
            'The shipped check reported %d on a device described as middling '
            'and %d on the same device described as having no source '
            'validation and no routing authentication at all. Making the '
            'device worse made the report shorter, because "none" is not the '
            'one string each check recognised.'
            % (first['shipped_said'], worse['shipped_said']), ''))
        print()
        print(_wrap(
            'The rebuilt check reported %d finding(s) on the first and %d on '
            'the second, and on answers it had never met it reported %d '
            'finding(s) and %d unstated --- which is the difference that '
            'matters. An allowlist has nowhere to put an answer it does not '
            'recognise except into the report; a blocklist puts it in the '
            'silence, where it reads as approval.'
            % (first['rebuilt_findings'], worse['rebuilt_findings'],
               unmet['rebuilt_findings'], unmet['rebuilt_unstated']), ''))
        return 0

    result = assess(DEVICE)
    if args.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write('\n')
    else:
        report(result)
    return 0


if __name__ == '__main__':
    sys.exit(main())
