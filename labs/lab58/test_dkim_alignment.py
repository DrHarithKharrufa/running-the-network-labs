#!/usr/bin/env python3
"""Tests for dkim_alignment.py.

The point of this lab is that a passing signature is a narrow claim, so the
tests check the boundary of that claim in both directions: what a signature
does protect, and what it demonstrably does not.

    python3 test_dkim_alignment.py
"""
import io
import sys

from cryptography.hazmat.primitives.asymmetric import rsa

import dkim_alignment as da

CHECKS, FAILED = 0, []


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
    except da.DkimError as exc:
        if fragment and fragment not in str(exc):
            FAILED.append('%s (message lacked %r)' % (label, fragment))
        return
    except Exception as exc:                                    # noqa: BLE001
        FAILED.append('%s (raised %s)' % (label, type(exc).__name__))
        return
    FAILED.append('%s (did not raise)' % label)


KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER = rsa.generate_private_key(public_exponent=65537, key_size=2048)
HDRS = [('From', 'a@acme.example'), ('To', 'b@c.example'),
        ('Subject', 'Hello'), ('Date', 'Tue, 23 Sep 2026 10:00:00 +0000')]
BODY = b'line one\r\nline two\r\n'
H = ['from', 'to', 'subject', 'date']


# -- 1. Canonicalisation matches the specification -------------------------

ok(da.canon_body_relaxed(b'a  b\t\tc \r\n\r\n\r\n') == b'a b c\r\n',
   'relaxed body canonicalisation folds whitespace and drops trailing blank lines')
ok(da.canon_body_relaxed(b'') == b'', 'an empty body canonicalises to empty')
ok(da.canon_body_relaxed(b'\r\n\r\n') == b'', 'a body of blank lines too')
ok(da.canon_body_relaxed(b'x') == b'x\r\n', 'a body without a final CRLF gains one')
ok(da.canon_header_relaxed('SuBjEcT', '  Hello   world  ') == b'subject:Hello world\r\n',
   'relaxed header canonicalisation lowercases the name and folds the value')
ok(da.canon_header_relaxed('X', 'a\r\n  b') == b'x:a b\r\n', 'and unfolds')
ok(da.canon_body_relaxed(b'abcdef\r\n', l=3) == b'abc',
   'l= truncates the canonical body')
raises(lambda: da.canon_body_relaxed('a str'), 'a str body is refused', 'octets')
raises(lambda: da.canon_body_relaxed(b'x', l=-1), 'a negative l= is refused')
raises(lambda: da.canon_body_relaxed(b'x', l=True), 'a bool l= is refused')


# -- 2. A signature verifies, and every tamper breaks it -------------------

sig = da.sign(HDRS, BODY, KEY, 'acme.example', 'sel1', H)
good, why = da.verify(HDRS, BODY, sig, KEY.public_key())
ok(good, 'the signature verifies (%s)' % why)
ok('bh=' in sig and 'b=' in sig and 'h=from:to:subject:date' in sig,
   'the signature carries the tags it must')

bad, why = da.verify(HDRS, BODY + b'extra\r\n', sig, KEY.public_key())
ok(not bad and 'body hash' in why, 'appending to the body breaks the body hash')
bad, why = da.verify(HDRS, b'line one\r\nline TWO\r\n', sig, KEY.public_key())
ok(not bad and 'body hash' in why, 'changing one character breaks it')
alt = [(n, 'Goodbye' if n == 'Subject' else v) for n, v in HDRS]
bad, why = da.verify(alt, BODY, sig, KEY.public_key())
ok(not bad and 'signature does not verify' in why, 'changing a signed header breaks it')
bad, why = da.verify(HDRS, BODY, sig, OTHER.public_key())
ok(not bad, 'another key does not verify it')
bad, why = da.verify(HDRS[:3], BODY, sig, KEY.public_key())
ok(not bad and 'not present' in why, 'removing a signed header is detected and named')
bad, why = da.verify(HDRS, BODY, sig.replace('a=rsa-sha256', 'a=rsa-sha1'),
                     KEY.public_key())
ok(not bad and 'unsupported algorithm' in why, 'an unsupported algorithm is refused')
for tag in ('bh', 'h', 'd', 's', 'b'):
    stripped = '; '.join(p for p in sig.split('; ')
                         if not p.strip().startswith(tag + '='))
    bad, why = da.verify(HDRS, BODY, stripped, KEY.public_key())
    ok(not bad, 'a signature missing %s= does not verify' % tag)
raises(lambda: da.sign(HDRS, BODY, KEY, 'd', 's', ['from', 'x-absent']),
       'signing an absent header is refused', 'not present')


# -- 3. What a signature does NOT protect, demonstrated -------------------

canon_len = len(da.canon_body_relaxed(BODY))
sig_l = da.sign(HDRS, BODY, KEY, 'acme.example', 'sel1', H, l=canon_len)
appended, why = da.verify(HDRS, BODY + b'PS: pay a different account\r\n',
                          sig_l, KEY.public_key())
ok(appended,
   'WITH l= SET, APPENDED TEXT STILL VERIFIES --- the loophole this lab exists '
   'to show (%s)' % why)
without_l, _ = da.verify(HDRS, BODY + b'PS: pay a different account\r\n',
                         sig, KEY.public_key())
ok(not without_l, 'and without l= the same append is caught, which is the contrast')

extra, _ = da.verify(HDRS + [('Reply-To', 'evil@elsewhere.example')], BODY,
                     sig, KEY.public_key())
ok(extra, 'an added header that was never in h= does not break the signature')
ok('reply-to' not in sig.lower(), 'because h= never listed it')


# -- 4. Alignment is the question DMARC actually asks ----------------------

ok(da.organisational_domain('mail.acme.example') == 'acme.example',
   'the organisational domain of a subdomain is the registrable domain')
ok(da.organisational_domain('acme.example') == 'acme.example', 'and of itself')
ok(da.organisational_domain('a.b.c.co.uk') == 'c.co.uk', 'multi-label suffixes work')
ok(da.aligned('mail.acme.example', 'acme.example', 'r'), 'relaxed alignment allows a subdomain')
ok(not da.aligned('mail.acme.example', 'acme.example', 's'), 'strict alignment does not')
ok(not da.aligned('acme-invoices.example', 'acme.example', 'r'),
   'a lookalike domain does not align')
ok(not da.aligned(None, 'acme.example'), 'no domain never aligns')
raises(lambda: da.aligned('a', 'b', 'x'), 'an unknown alignment mode is refused')

r = da.dmarc_result('acme.example', spf={'result': 'pass', 'domain': 'bounce.provider.example'})
ok(r['dmarc'] == 'fail',
   'AN SPF PASS FOR AN UNALIGNED DOMAIN DOES NOT PASS DMARC --- the core of TE-0576')
ok(any('does not align' in w for w in r['why']), 'and the report says why')
r = da.dmarc_result('acme.example', dkim={'result': 'pass', 'domain': 'provider.example'})
ok(r['dmarc'] == 'fail', 'nor does an unaligned DKIM pass')
r = da.dmarc_result('acme.example', spf={'result': 'fail', 'domain': 'acme.example'},
                    dkim={'result': 'pass', 'domain': 'acme.example'})
ok(r['dmarc'] == 'pass', 'one aligned pass is enough --- the forwarding case')
ok(r['aligned_dkim'] and not r['aligned_spf'], 'and the report says which one carried it')
r = da.dmarc_result('acme.example', spf={'result': 'pass', 'domain': 'acme.example'},
                    dkim={'result': 'fail', 'domain': 'acme.example'})
ok(r['dmarc'] == 'pass', 'either one will do --- the mailing-list case in reverse')
r = da.dmarc_result('acme.example')
ok(r['dmarc'] == 'fail', 'with no results at all, DMARC does not pass')
r = da.dmarc_result('acme.example', adkim='s',
                    dkim={'result': 'pass', 'domain': 'mail.acme.example'})
ok(r['dmarc'] == 'fail', 'strict alignment rejects a subdomain signature')


# -- 5. The run, and the two things p=reject does not stop -----------------

o = da.run()
ok(all(c['as_expected'] for c in o['cases']),
   'every signature case behaved as the lab says it does')
ok(len(o['cases']) == 6, 'all six cases ran')
ok(o['lookalike']['dkim_verifies'] is True,
   'the lookalike message is correctly signed for ITS OWN domain')
ok(o['lookalike']['dmarc'] == 'pass',
   'AND IT PASSES DMARC --- which is why p=reject on the real domain does not stop it')
ok('not consulted' in o['lookalike']['comment'],
   'and the comment explains that the real domain\'s policy is never consulted')
ok(o['display_name']['dmarc'] == 'pass',
   'display-name spoofing passes everything too')
ok('signed From field' in o['display_name']['comment'] and
   'human/brand identity' in o['display_name']['comment'],
   'signed display-name bytes are distinguished from asserted human identity')
al = {a['scenario']: a for a in o['alignment']}
ok(any(a['dmarc'] == 'fail' for a in o['alignment']),
   'at least one shipped scenario fails, so the table is not decorative')
ok(any(a['dmarc'] == 'pass' for a in o['alignment']), 'and at least one passes')

c = da.crosscheck()
ok(c['ran'] is False or c['agreed'] is True,
   'the cross-check either ran and agreed, or was skipped and said so')
ok('not a passed one' in c['why'] or c['ran'],
   'a skipped cross-check is not reported as a pass')

buf = io.StringIO()
_s = sys.stdout
sys.stdout = io.StringIO()
try:
    o2 = da.report(buf)
    rc, rj = da.main([]), da.main(['--json'])
finally:
    sys.stdout = _s
txt = buf.getvalue()
ok('Not who wrote it' in txt, 'the report states what a signature does not establish')
ok('VERIFIES' in txt and 'fails' in txt, 'and shows both outcomes')
for banned in ('proves the message came from you', 'actively rejected'):
    ok(banned not in txt.lower(), 'the report never says %r' % banned)
ok(txt.lower().count('stops spoofing') <= 2,
   'the claim appears only where it is being refuted')
ok('LEAVES OUT' in txt and 'stops spoofing' in txt.lower(),
   'and where it appears it is the heading of the section that refutes it')
ok(rc == 0 and rj == 0, 'both modes run')

print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
