#!/usr/bin/env python3
"""Tests for harden_check.py --- chiefly, that it cannot go quiet.

The shipped script's defect was silence: two checks recognised one bad value
each and said nothing about every other answer, including the worse ones. So
most of what follows is about absence of output being impossible.

    python3 test_harden_check.py
"""
import datetime as _dt
import io
import itertools
import re
import sys

import harden_check as hc

CHECKS = 0
FAILED = []


def ok(condition, label):
    global CHECKS
    CHECKS += 1
    if not condition:
        FAILED.append(label)


def raises(fn, label, fragment=None):
    global CHECKS
    CHECKS += 1
    try:
        fn()
    except hc.RecordError as exc:
        if fragment and fragment not in str(exc):
            FAILED.append('%s (message lacked %r: %s)' % (label, fragment, exc))
        return
    except Exception as exc:                                # pragma: no cover
        FAILED.append('%s (raised %s, not RecordError)' % (label, type(exc).__name__))
        return
    FAILED.append('%s (did not raise)' % label)


TODAY = _dt.date(2026, 9, 19)


def record(**over):
    base = {
        'hostname': 'test-01', 'role': 'pe', 'platform': 'ios-xe',
        'record_source': 'config', 'record_date': '2026-09-01',
        'controls': dict(hc.DEVICE['controls']),
    }
    controls = over.pop('controls', None)
    base.update(over)
    if controls is not None:
        base['controls'] = controls
    return base


# -- 1. No control can be silent -------------------------------------------
# Every control, given every answer it knows plus a pile it does not, must
# return a verdict from the three. There is no code path that returns None.

STRANGE = ['', 'none (flat)', 'NONE', 'None', 'yes', 'true', 0, 1, True, False,
           None, 3.5, ('a',), 'n/a', 'tbd', 'we think so', 'disabled',
           'not applicable', 'see wiki']

for control in hc.CONTROLS:
    for value in itertools.chain(control.answers, STRANGE):
        result = control.assess(value)
        ok(isinstance(result, tuple) and len(result) == 2,
           '%s.assess(%r) returned a pair' % (control.key, value))
        verdict, why = result
        ok(verdict in (hc.BAD, hc.UNKNOWN, hc.CLAIM),
           '%s.assess(%r) gave a real verdict, got %r'
           % (control.key, value, verdict))
        ok(isinstance(why, str) and why,
           '%s.assess(%r) explained itself' % (control.key, value))

# Unhashable answers must not raise; they must be UNSTATED.
for value in ([], {}, set(), ['a', 'b'], {'x': 1}):
    for control in hc.CONTROLS:
        verdict, _ = control.assess(value)
        ok(verdict == hc.UNKNOWN,
           '%s.assess(%r) is UNSTATED, not a crash' % (control.key, value))

# Every control recognises at least one bad answer and at least one good one,
# so none of them is decorative.
for control in hc.CONTROLS:
    verdicts = {v for v, _ in control.answers.values()}
    ok(hc.BAD in verdicts, '%s can produce a FINDING' % control.key)
    ok(hc.CLAIM in verdicts or control.key == 'telnet',
       '%s can produce a CLAIMED' % control.key)
    ok(control.evidence, '%s says what would settle it' % control.key)
    ok(control.section, '%s cites a section' % control.key)

ok(len({c.key for c in hc.CONTROLS}) == len(hc.CONTROLS),
   'control keys are unique')

# A control whose answer table maps to something that is not a verdict is a
# programming error and must be refused at construction.
raises(lambda: hc.Control('x', 'q?', {'a': ('GREAT', 'why')}, 'evidence'),
       'a bogus verdict is rejected at construction', 'not a verdict')
raises(lambda: hc.Control('x', 'q?', {}, 'evidence'),
       'a control with no answers is rejected', 'recognises no answers')


# -- 2. The regression: a worse device must not produce a shorter report ----

def findings(controls, **over):
    result = hc.assess(record(controls=controls, **over), today=TODAY)
    return result['counts'].get(hc.BAD, 0)


middling = dict(hc.DEVICE['controls'])
middling.update(source_validation='urpf-loose', routing_authentication='tcp-md5')
worse = dict(middling)
worse.update(source_validation='none', routing_authentication='none')

ok(findings(worse) >= findings(middling),
   'a strictly worse device does not produce fewer findings '
   '(%d vs %d)' % (findings(worse), findings(middling)))

# And the specific pair the shipped script went quiet on.
for key, bad_value in (('source_validation', 'none'),
                       ('routing_authentication', 'none')):
    verdict, _ = hc.CONTROLS_BY_KEY[key].assess(bad_value)
    ok(verdict == hc.BAD, '%s=%r is a FINDING, not silence' % (key, bad_value))

# The demonstration the module prints must be computed, not asserted.
rows = hc.fail_open_demonstration()
ok(len(rows) == len(hc.CASES), 'the demonstration covers every case')
by_label = {r['device']: r for r in rows}
ok(by_label['uRPF loose, BGP MD5']['shipped_said'] == 2,
   'the shipped blocklist fired on the middling device')
ok(by_label['uRPF OFF, BGP UNAUTHENTICATED']['shipped_said'] == 0,
   'the shipped blocklist went silent on the worse device')
ok(by_label['uRPF OFF, BGP UNAUTHENTICATED']['rebuilt_findings'] == 2,
   'the rebuilt allowlist did not')
ok(by_label['answers the checks never met']['rebuilt_unstated'] == 2,
   'answers the baseline never met are UNSTATED, not silent')
ok(by_label['answers the checks never met']['shipped_said'] == 0,
   'the shipped blocklist was silent on answers it never met')


# -- 3. Every control produces exactly one line, whatever the record says ---

result = hc.assess(record(controls={}), today=TODAY)
ok(len(result['results']) == len(hc.CONTROLS),
   'an EMPTY record still produces one entry per control')
ok(all(r['verdict'] in (hc.UNKNOWN, hc.NA) for r in result['results']),
   'an empty record is UNSTATED or NOT APPLICABLE throughout, never a pass')
ok(result['counts'].get(hc.CLAIM, 0) == 0,
   'an empty record claims nothing')

full = hc.assess(record(), today=TODAY)
ok(len(full['results']) == len(hc.CONTROLS),
   'a full record produces one entry per control too')


# -- 4. Role selects the baseline ------------------------------------------

for role in hc.ROLES:
    r = hc.assess(record(role=role), today=TODAY)
    ok(len(r['results']) == len(hc.CONTROLS), 'role %s is assessable' % role)

rr = hc.assess(record(role='route-reflector'), today=TODAY)
na = {r['key'] for r in rr['results'] if r['verdict'] == hc.NA}
ok('source_validation' in na,
   'a route reflector is not asked for a customer-edge source filter')
ok('iacl_exceptions' in na,
   'a route reflector is not asked for an edge ACL')
ok('routing_authentication' not in na,
   'a route reflector IS asked to authenticate its adjacencies')
pe = hc.assess(record(role='pe'), today=TODAY)
ok(not any(r['verdict'] == hc.NA for r in pe['results']),
   'a PE is asked for every control in the baseline')
ok(hc.NA not in (hc.BAD, hc.UNKNOWN, hc.CLAIM),
   'NOT APPLICABLE is its own verdict and not a pass')

raises(lambda: hc.assess(record(role='switch'), today=TODAY),
       'an unknown role is refused', 'selected by role')
raises(lambda: hc.assess(record(role=None), today=TODAY),
       'a missing role is refused')


# -- 5. Provenance and age -------------------------------------------------

asserted = hc.assess(record(record_source='asserted'), today=TODAY)
ok(any('asserted' in n for n in asserted['notes']),
   'an asserted record says so in its notes')
observed = hc.assess(record(record_source='observed'), today=TODAY)
ok(not any(n.startswith('record_source is "asserted"') for n in observed['notes']),
   'an observed record does not carry the asserted note')
raises(lambda: hc.assess(record(record_source='vibes'), today=TODAY),
       'an unknown provenance is refused', 'record_source')

stale = hc.assess(record(record_date='2025-01-01'), today=TODAY)
ok(any('days old' in n for n in stale['notes']), 'a stale record says so')
ok(stale['record_age_days'] > hc.STALE_AFTER_DAYS, 'age is computed')
fresh = hc.assess(record(record_date='2026-09-18'), today=TODAY)
ok(fresh['record_age_days'] == 1, 'a one-day-old record is one day old')
ok(not any('days old' in n for n in fresh['notes']),
   'a fresh record carries no staleness note')

raises(lambda: hc.assess(record(record_date='last Tuesday'), today=TODAY),
       'a non-ISO date is refused', 'ISO date')
raises(lambda: hc.assess(record(record_date=None), today=TODAY),
       'a missing date is refused')
raises(lambda: hc.assess(record(record_date='2027-01-01'), today=TODAY),
       'a future date is refused', 'future')
raises(lambda: hc.assess(record(controls='lots'), today=TODAY),
       'a non-dictionary controls block is refused', 'controls')
raises(lambda: hc.assess('a device', today=TODAY),
       'a non-dictionary record is refused', 'dictionary')


# -- 6. Platform defaults --------------------------------------------------

xr = dict(hc.DEVICE['controls']); xr['copp'] = 'none'
r = hc.assess(record(platform='ios-xr', controls=xr), today=TODAY)
ok(any('LPTS' in n for n in r['notes']),
   'an XR box with no explicit policy gets the LPTS note')
xe = hc.assess(record(platform='ios-xe', controls=xr), today=TODAY)
ok(not any('LPTS' in n for n in xe['notes']),
   'a non-XR box does not get the LPTS note')
claimed_default = dict(hc.DEVICE['controls']); claimed_default['copp'] = 'platform-default'
r = hc.assess(record(platform='ios-xe', controls=claimed_default), today=TODAY)
ok(any('Name the default' in n for n in r['notes']),
   'a claimed platform default on a non-XR box must be named')
# The control itself still reports on copp='none' regardless of platform.
for platform in ('ios-xr', 'ios-xe', 'sr-os'):
    r = hc.assess(record(platform=platform, controls=xr), today=TODAY)
    entry = next(e for e in r['results'] if e['key'] == 'copp')
    ok(entry['verdict'] == hc.BAD,
       'copp=none is still a finding on %s; the note explains, it does not '
       'excuse' % platform)


# -- 7. Unrecognised keys are reported, not counted -------------------------

extra = dict(hc.DEVICE['controls']); extra['quantum_resistant'] = 'yes'
r = hc.assess(record(controls=extra), today=TODAY)
ok('quantum_resistant' in r['unassessed_keys'], 'an unknown key is listed')
ok(any('quantum_resistant' in n for n in r['notes']),
   'an unknown key is called out in the notes')
ok(len(r['results']) == len(hc.CONTROLS),
   'an unknown key does not add a result line')


# -- 8. The output vocabulary has no pass ----------------------------------

buf = io.StringIO()
hc.report(hc.assess(hc.DEVICE, today=TODAY), buf)
text = buf.getvalue()

# No verdict may be a word of approval. The verdict is the bracketed label at
# the head of each entry, so read those rather than scanning the prose --- the
# report DOES contain the word PASS, once, in the sentence saying there is no
# such verdict, and a test that failed on that would be testing the wrong thing.
labels = set(re.findall(r'^  \[([A-Z ]+?)\s*\]', text, re.M))
ok(labels, 'the report prints verdict labels')
for label in labels:
    ok(label in (hc.BAD, hc.UNKNOWN, hc.CLAIM, hc.NA),
       'verdict %r is one of the four' % label)
    for word in ('PASS', 'OK', 'COMPLIANT', 'SECURE', 'GOOD'):
        ok(word not in label, 'verdict %r is not a word of approval' % label)
pass_lines = [ln for ln in text.splitlines() if 'PASS' in ln]
ok(pass_lines == ['There is no PASS in this vocabulary, and no total that '
                  'could be read as a score.'],
   'the only mention of PASS is the sentence denying it, got %r' % pass_lines)
ok('verifies nothing' in text, 'the report says what it is')
for control in hc.CONTROLS:
    ok(control.key in text, '%s appears in the report' % control.key)

# Every FINDING and CLAIMED line carries the evidence that would settle it.
# The report wraps to 78 columns, so compare with whitespace collapsed.
flat = ' '.join(text.split())
assessment = hc.assess(hc.DEVICE, today=TODAY)
for entry in assessment['results']:
    if entry['verdict'] in (hc.BAD, hc.UNKNOWN, hc.CLAIM):
        ok(' '.join(entry['evidence'].split()) in flat,
           '%s prints what would settle it' % entry['key'])

# The shipped device is a PE with a real record, so it should have findings.
ok(assessment['counts'].get(hc.BAD, 0) >= 8,
   'the shipped device description produces findings, not reassurance')

# Determinism: same input, same output.
ok(hc.assess(hc.DEVICE, today=TODAY) == hc.assess(hc.DEVICE, today=TODAY),
   'the assessment is deterministic')

# The entry point runs.
ok(hc.main([]) == 0, 'the module runs')
ok(hc.main(['--json']) == 0, 'the JSON form runs')
ok(hc.main(['--demo-fail-open']) == 0, 'the demonstration runs')


print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
