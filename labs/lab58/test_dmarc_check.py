#!/usr/bin/env python3
"""Tests for dmarc_check.py.

THE PROPERTY THAT MATTERS MOST: arbitrary non-empty text must never count as a
record. The shipped version tested bool(spf) and bool(dkim), and its own example
passed the string "present" as a DKIM record. Most of what follows exists to
keep that impossible.

    python3 test_dmarc_check.py
"""
import io
import sys

import dmarc_check as dc

CHECKS, FAILED = 0, []


def ok(cond, label):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


# -- 1. Arbitrary text is not a record -------------------------------------

for junk in ('present', 'yes', 'we have DKIM', 'true', 'x'):
    ok(dc.parse_dkim(junk)['state'] == dc.INVALID,
       'the DKIM record %r is INVALID, not present' % junk)
    ok(dc.parse_spf(junk)['state'] == dc.INVALID, 'and %r is not an SPF record' % junk)
    ok(dc.parse_dmarc(junk)['state'] == dc.INVALID, 'nor a DMARC record')
a = dc.assess('x', dkim='present', spf='v=spf1 -all',
              dmarc='v=DMARC1; p=reject; rua=mailto:a@b.example')
ok(a['dkim']['state'] == dc.INVALID,
   'THE EXACT INPUT THE OLD LAB ACCEPTED IS NOW INVALID')
ok(dc.parse_dkim(None)['state'] == dc.ABSENT, 'and absent is a third state, not false')
ok(dc.parse_spf(None)['state'] == dc.ABSENT, 'for SPF too')
ok(dc.parse_dmarc(None)['state'] == dc.ABSENT, 'and DMARC')
for fn in (dc.parse_dmarc, dc.parse_spf, dc.parse_dkim):
    try:
        fn(123)
        ok(False, '%s refuses a non-string' % fn.__name__)
    except dc.RecordError:
        ok(True, '%s refuses a non-string' % fn.__name__)


# -- 2. DMARC record structure ---------------------------------------------

good = 'v=DMARC1; p=reject; rua=mailto:d@acme.example'
ok(dc.parse_dmarc(good)['state'] == dc.VALID, 'a well-formed record is valid')
ok(dc.parse_dmarc(good)['tags']['p'] == 'reject', 'and its policy is read')
bad = dc.parse_dmarc('p=reject; v=DMARC1')
ok(bad['state'] == dc.INVALID, 'v= not first is invalid')
ok(any('begin with v=DMARC1' in p for p in bad['problems']), 'and says so')
ok(dc.parse_dmarc('v=DMARC1; rua=mailto:a@b.example')['state'] == dc.INVALID,
   'a record with no p= is invalid')
ok(any('misspelling such as policy=' in p for p in
       dc.parse_dmarc('v=DMARC1; policy=reject')['problems']),
   'and a misspelled policy tag is diagnosed rather than ignored')
dup = dc.parse_dmarc('v=DMARC1; p=none; p=reject')
ok(dup['state'] == dc.INVALID and any('more than once' in p for p in dup['problems']),
   'a duplicate tag is invalid')
for bad_v in ('v=DMARC1; p=block', 'v=DMARC1; p=reject; sp=drop',
              'v=DMARC1; p=reject; adkim=x', 'v=DMARC1; p=reject; aspf=q',
              'v=DMARC1; p=reject; pct=120', 'v=DMARC1; p=reject; pct=abc',
              'v=DMARC1; p=reject; fo=9',
              'v=DMARC1; p=reject; rua=https://example.com/report'):
    ok(dc.parse_dmarc(bad_v)['state'] == dc.INVALID, '%r is invalid' % bad_v[:44])
ok(dc.parse_dmarc('v=DMARC1; p=reject; pct=0')['state'] == dc.VALID,
   'pct=0 is legal, however pointless')
ok(dc.parse_dmarc('v=DMARC1; p=reject; fo=1:d')['state'] == dc.VALID,
   'a colon-separated fo list is legal')


# -- 3. SPF, including the lookup budget -----------------------------------

ok(dc.parse_spf('v=spf1 -all')['state'] == dc.VALID, 'the minimal record is valid')
ok(dc.parse_spf('v=spf1 include:a.example -all')['lookups'] == 1, 'include costs a lookup')
ok(dc.parse_spf('v=spf1 ip4:192.0.2.0/24 -all')['lookups'] == 0, 'ip4 does not')
ten = 'v=spf1 ' + ' '.join('include:%d.example' % i for i in range(10)) + ' -all'
eleven = 'v=spf1 ' + ' '.join('include:%d.example' % i for i in range(11)) + ' -all'
ok(dc.parse_spf(ten)['lookups'] == 10, 'ten lookups are counted')
ok(dc.parse_spf(eleven)['state'] == dc.INVALID, 'eleven top-level terms need review under this conservative linter')
ok(any('does not execute' in p for p in dc.parse_spf(eleven)['problems']),
   'and the problem disclaims evaluation of the actual message path')
ok(dc.parse_spf('v=spf1 ' + ' '.join('include:%d.example' % i for i in range(9))
                + ' -all')['state'] == dc.INVALID,
   'nine is flagged as close to the limit, because includes expand')
ok(dc.parse_spf('v=spf1 +all')['state'] == dc.INVALID, '+all is invalid')
ok(any('worse than' in p for p in dc.parse_spf('v=spf1 +all')['problems']),
   'and is explained as worse than publishing nothing')
ok(dc.parse_spf('v=spf1 ptr -all')['state'] == dc.INVALID, 'ptr is flagged')
ok(dc.parse_spf('v=spf1 include:a.example')['state'] == dc.INVALID,
   'a record with no all and no redirect is flagged as ending in neutral')
ok(dc.parse_spf('v=spf1 redirect=other.example')['state'] == dc.VALID,
   'but a redirect is a legitimate ending')
ok(dc.parse_spf('spf1 -all')['state'] == dc.INVALID, 'a missing version is invalid')
two = dc.parse_spf(['v=spf1 -all', 'v=spf1 ~all'])
ok(two['state'] == dc.INVALID and any('permerror' in p.lower() for p in two['problems']),
   'two published SPF records are a permerror')
ok(any('not be satisfied by it' in p for p in two['problems']),
   'and the consequence for DMARC is stated')


# -- 4. DKIM key records ---------------------------------------------------

ok(dc.parse_dkim('v=DKIM1; k=rsa; p=MIIBIjANBgkq')['state'] == dc.VALID,
   'a key record with a key is valid')
rev = dc.parse_dkim('v=DKIM1; k=rsa; p=')
ok(rev['state'] == dc.INVALID and any('REVOKED' in p for p in rev['problems']),
   'an empty p= is a revoked key, and is called that')
ok(dc.parse_dkim('v=DKIM1; k=rsa')['state'] == dc.INVALID, 'no p= at all is invalid')
ok(dc.parse_dkim('v=DKIM2; p=abc')['state'] == dc.INVALID, 'a wrong version is invalid')
ok(dc.parse_dkim('v=DKIM1; k=magic; p=abc')['state'] == dc.INVALID,
   'an unknown key type is invalid')
ok(dc.parse_dkim('v=DKIM1; p=not base64!!')['state'] == dc.INVALID,
   'a non-base64 key is invalid')


# -- 5. Nothing claims an outcome -----------------------------------------

for name, kw in dc.CASES.items():
    a = dc.assess(name, **kw)
    blob = ' '.join(a['findings']).lower()
    for banned in ('actively rejected', 'spoofing of this domain',
                   'will be junked', 'good.'):
        ok(banned not in blob, 'case %r never says %r' % (name[:26], banned))
    ok(a['what_this_cannot_tell_you'], 'every assessment carries its own limits')
q = dc.assess('x', dmarc='v=DMARC1; p=quarantine; rua=mailto:a@b.example')
ok(any('QUARANTINE IS NOT REJECTION' in f for f in q['findings']),
   'quarantine is distinguished from rejection')
rj = dc.assess('x', dmarc='v=DMARC1; p=reject; rua=mailto:a@b.example')
ok(any('It is a REQUEST' in f for f in rj['findings']),
   'and p=reject is described as a request to receivers')
nn = dc.assess('x', dmarc='v=DMARC1; p=none; rua=mailto:a@b.example')
ok(any('correct place to START' in f for f in nn['findings']),
   'p=none is described as the right starting point, not as worthless')
pc = dc.assess('x', dmarc='v=DMARC1; p=reject; pct=20; rua=mailto:a@b.example')
ok(any('pct=20' in f for f in pc['findings']), 'a partial pct is reported')
kk = dc.assess('x', dkim='v=DKIM1; k=rsa; p=MIIBIjANBgkq')
ok(any('says nothing about whether any' in f for f in kk['findings']),
   'a published key is explicitly not a verified signature')
ok(any('lab 58.2' in s for s in kk['what_this_cannot_tell_you']),
   'and the reader is pointed at the lab that does check messages')
ok(any('lookalike' in s for s in kk['what_this_cannot_tell_you']),
   'the lookalike-domain limit is stated')

buf = io.StringIO()
dc.report(buf)
txt = buf.getvalue()
ok('No line above says a message would be accepted or rejected' in txt,
   'the report states its own limit')
ok('INVALID' in txt and 'ABSENT' in txt and 'VALID' in txt, 'all three states appear')
_s = sys.stdout
sys.stdout = io.StringIO()
try:
    rc, rj2 = dc.main([]), dc.main(['--json'])
finally:
    sys.stdout = _s
ok(rc == 0 and rj2 == 0, 'both modes run')

print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
