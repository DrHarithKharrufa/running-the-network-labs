#!/usr/bin/env python3
"""Lab 58.2 --- what DKIM actually proves, signed and broken for real.

The chapter used to say DKIM \"proves the message came from you\". It does not.
It proves that whoever holds the private key for one selector under one domain
signed the headers listed in h= and as much of the body as l= covers --- and
DMARC then asks a further question the chapter never asked: does that domain
ALIGN with the domain in the From: header the reader sees?

Everything below is executed, not asserted. Real RSA keys are generated, real
RFC 6376 relaxed/relaxed canonicalisation is applied, real signatures are made
and verified, and every tamper case is run.

    python3 dkim_alignment.py
    python3 dkim_alignment.py --json
    python3 test_dkim_alignment.py

WHAT THIS IS: offline execution of the DKIM signing and verification algorithms
and of the DMARC alignment rules, in this container. It is NOT a test against
any real mail provider, and no message was sent anywhere. Where a receiver's
behaviour is involved --- whether it honours p=reject, how it treats a forwarded
message --- that is policy, not arithmetic, and this lab says so rather than
guessing.
"""
import base64
import hashlib
import json
import re
import sys

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

CRLF = b'\r\n'


class DkimError(ValueError):
    pass


# ---------------------------------------------------------------------------
# RFC 6376 relaxed canonicalisation
# ---------------------------------------------------------------------------

def canon_body_relaxed(body, l=None):
    """Relaxed body canonicalisation; l truncates, which is the loophole."""
    if not isinstance(body, bytes):
        raise DkimError('the body must be bytes: canonicalisation is defined '
                        'over octets, and a str would hide an encoding choice')
    body = body.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    out = [re.sub(rb'[ \t]+', b' ', ln).rstrip(b' \t') for ln in body.split(b'\n')]
    while out and out[-1] == b'':
        out.pop()
    canon = (CRLF.join(out) + CRLF) if out else b''
    if l is not None:
        if not isinstance(l, int) or isinstance(l, bool) or l < 0:
            raise DkimError('l= must be a non-negative integer')
        canon = canon[:l]
    return canon


def canon_header_relaxed(name, value):
    v = re.sub(r'\r\n[ \t]+', ' ', value)
    v = re.sub(r'[ \t]+', ' ', v)
    return (name.lower().strip() + ':' + v.strip()).encode() + CRLF


def _sig_for_signing(tags):
    v = re.sub(r'\r\n[ \t]+', ' ', tags)
    v = re.sub(r'[ \t]+', ' ', v)
    return b'dkim-signature:' + v.strip().encode()


def sign(headers, body, key, d, s, h_list, l=None):
    """Produce a DKIM-Signature field value. Real RSA, real canonicalisation."""
    hdrs = {k.lower(): v for k, v in headers}
    missing = [n for n in h_list if n.lower() not in hdrs]
    if missing:
        raise DkimError('cannot sign headers that are not present: %s'
                        % ', '.join(missing))
    bh = base64.b64encode(hashlib.sha256(canon_body_relaxed(body, l)).digest()).decode()
    tags = ('v=1; a=rsa-sha256; c=relaxed/relaxed; d=%s; s=%s; h=%s; bh=%s;%s b='
            % (d, s, ':'.join(h_list), bh, (' l=%d;' % l) if l is not None else ''))
    signed = b''.join(canon_header_relaxed(n, hdrs[n.lower()]) for n in h_list)
    signed += _sig_for_signing(tags)
    return tags + base64.b64encode(
        key.sign(signed, padding.PKCS1v15(), hashes.SHA256())).decode()


def verify(headers, body, sig_value, pub):
    """Return (ok, reason). Every failure names which check failed."""
    tags = {}
    for part in sig_value.split(';'):
        if '=' in part:
            k, v = part.split('=', 1)
            tags[k.strip()] = v.strip()
    for required in ('v', 'a', 'd', 's', 'h', 'bh', 'b'):
        if required not in tags:
            return False, 'the signature has no %s= tag' % required
    if tags['a'] != 'rsa-sha256':
        return False, 'unsupported algorithm %r (this lab implements rsa-sha256 only)' % tags['a']
    l = int(tags['l']) if 'l' in tags else None
    bh = base64.b64encode(hashlib.sha256(canon_body_relaxed(body, l)).digest()).decode()
    if bh != re.sub(r'\s+', '', tags['bh']):
        return False, 'body hash mismatch: the body changed under the signature'
    hdrs = {k.lower(): v for k, v in headers}
    signed = b''
    for n in tags['h'].split(':'):
        if n.lower() not in hdrs:
            return False, 'a signed header (%s) is not present in the message' % n
        signed += canon_header_relaxed(n, hdrs[n.lower()])
    signed += _sig_for_signing(re.sub(r'b=[^;]*', 'b=', sig_value))
    try:
        pub.verify(base64.b64decode(re.sub(r'\s+', '', tags['b'])), signed,
                   padding.PKCS1v15(), hashes.SHA256())
    except Exception:                                            # noqa: BLE001
        return False, 'signature does not verify against this key'
    return True, 'signature verifies'


# ---------------------------------------------------------------------------
# DMARC alignment (RFC 7489). A pass needs an ALIGNED pass, not any pass.
# ---------------------------------------------------------------------------

PUBLIC_SUFFIXES = ('example', 'com', 'co.uk', 'org', 'net')


def organisational_domain(domain):
    """A deliberately small stand-in for the public-suffix list."""
    d = domain.lower().strip('.')
    for suf in sorted(PUBLIC_SUFFIXES, key=len, reverse=True):
        if d == suf:
            return d
        if d.endswith('.' + suf):
            labels = d[: -len(suf) - 1].split('.')
            return labels[-1] + '.' + suf
    return d


def aligned(auth_domain, from_domain, mode='r'):
    if mode not in ('r', 's'):
        raise DkimError("alignment mode must be 'r' (relaxed) or 's' (strict)")
    if auth_domain is None:
        return False
    a, f = auth_domain.lower(), from_domain.lower()
    if mode == 's':
        return a == f
    return organisational_domain(a) == organisational_domain(f)


def dmarc_result(from_domain, spf=None, dkim=None, aspf='r', adkim='r'):
    """spf/dkim are dicts {'result': 'pass'|..., 'domain': ...} or None."""
    spf_ok = bool(spf) and spf.get('result') == 'pass' \
        and aligned(spf.get('domain'), from_domain, aspf)
    dkim_ok = bool(dkim) and dkim.get('result') == 'pass' \
        and aligned(dkim.get('domain'), from_domain, adkim)
    why = []
    if spf and spf.get('result') == 'pass' and not spf_ok:
        why.append('SPF passed for %s, which does not align with %s'
                   % (spf.get('domain'), from_domain))
    if dkim and dkim.get('result') == 'pass' and not dkim_ok:
        why.append('DKIM verified for d=%s, which does not align with %s'
                   % (dkim.get('domain'), from_domain))
    if spf and spf.get('result') != 'pass':
        why.append('SPF result was %s' % spf.get('result'))
    if dkim and dkim.get('result') != 'pass':
        why.append('DKIM result was %s' % dkim.get('result'))
    return dict(dmarc='pass' if (spf_ok or dkim_ok) else 'fail',
                aligned_spf=spf_ok, aligned_dkim=dkim_ok, why=why,
                note=('DMARC passes on an ALIGNED SPF pass or an ALIGNED DKIM pass. '
                      'Neither a bare pass nor the presence of a record is enough.'))


# ---------------------------------------------------------------------------
# The demonstrations, all executed
# ---------------------------------------------------------------------------

FROM = 'Finance <billing@acme.example>'
HEADERS = [('From', FROM), ('To', 'payables@customer.example'),
           ('Subject', 'Invoice 4471'), ('Date', 'Tue, 23 Sep 2026 10:00:00 +0000')]
BODY = (b'Please pay invoice 4471 by 30 September.\r\n'
        b'Account: 12-34-56 / 87654321\r\n')
H = ['from', 'to', 'subject', 'date']


def run():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = key.public_key()
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    out = {'key_bits': 2048, 'cases': []}

    def case(name, headers, body, sig, pubkey, expect, comment):
        ok, why = verify(headers, body, sig, pubkey)
        out['cases'].append(dict(case=name, verifies=ok, reason=why,
                                 expected=expect, as_expected=(ok is expect),
                                 comment=comment))
        return ok

    sig = sign(HEADERS, BODY, key, 'acme.example', 'sel1', H)
    case('the message as signed', HEADERS, BODY, sig, pub, True,
         'the baseline: this must verify, or nothing below means anything')

    case('one digit of the bank account changed', HEADERS,
         BODY.replace(b'87654321', b'99999999'), sig, pub, False,
         'the body hash covers the body, so a single changed digit is caught')

    tampered = [(n, 'Invoice 9999' if n == 'Subject' else v) for n, v in HEADERS]
    case('the Subject changed', tampered, BODY, sig, pub, False,
         'Subject was in h=, so changing it breaks the signature')

    case('signed by a different key', HEADERS, BODY, sig, other.public_key(), False,
         'the selector in s= and d= determines which key must verify it')

    # The l= loophole, executed.
    sig_l = sign(HEADERS, BODY, key, 'acme.example', 'sel1', H, l=len(canon_body_relaxed(BODY)))
    appended = BODY + b'\r\nPS: our bank has changed. Pay 11-22-33 / 44556677.\r\n'
    case('l= covers the original body, and text is APPENDED', HEADERS, appended,
         sig_l, pub, True,
         'THIS ONE VERIFIES. l= tells the verifier to hash only the first n '
         'octets, so anything appended after them is unsigned and still passes. '
         'That is why l= should not be used, and why "DKIM passed" is not the '
         'same as "the message you are reading was signed"')

    # An unsigned header is not protected, even though the message verifies.
    plus_reply = HEADERS + [('Reply-To', 'billing@acme-invoices.example')]
    case('a Reply-To added that was never in h=', plus_reply, BODY, sig, pub, True,
         'also verifies. h= listed four headers; anything not in that list can '
         'be added or altered by anyone on the path')

    # ---- alignment -------------------------------------------------------
    al = []

    def scen(name, **kw):
        r = dmarc_result('acme.example', **kw)
        al.append(dict(scenario=name, **r))
        return r

    scen('sent directly from an authorised server',
         spf={'result': 'pass', 'domain': 'acme.example'},
         dkim={'result': 'pass', 'domain': 'acme.example'})
    scen('forwarded by the recipient to another address',
         spf={'result': 'fail', 'domain': 'acme.example'},
         dkim={'result': 'pass', 'domain': 'acme.example'})
    scen('through a mailing list that rewrites the Subject and adds a footer',
         spf={'result': 'pass', 'domain': 'lists.forum.example'},
         dkim={'result': 'fail', 'domain': 'acme.example'})
    scen('sent by a bulk provider signing with its own domain',
         spf={'result': 'pass', 'domain': 'bounce.provider.example'},
         dkim={'result': 'pass', 'domain': 'provider.example'})
    scen('the same, with the provider signing on the customer\'s behalf',
         spf={'result': 'pass', 'domain': 'bounce.provider.example'},
         dkim={'result': 'pass', 'domain': 'mail.acme.example'})
    scen('subdomain signing under a strict policy', adkim='s',
         spf={'result': 'fail', 'domain': 'acme.example'},
         dkim={'result': 'pass', 'domain': 'mail.acme.example'})
    out['alignment'] = al

    # The lookalike: everything passes, for the wrong domain.
    look = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    look_hdrs = [('From', 'Acme Finance <billing@acme-invoices.example>')] + HEADERS[1:]
    look_sig = sign(look_hdrs, BODY, look, 'acme-invoices.example', 's1', H)
    ok, why = verify(look_hdrs, BODY, look_sig, look.public_key())
    look_dmarc = dmarc_result('acme-invoices.example',
                              spf={'result': 'pass', 'domain': 'acme-invoices.example'},
                              dkim={'result': 'pass', 'domain': 'acme-invoices.example'})
    out['lookalike'] = dict(
        from_header=look_hdrs[0][1], dkim_verifies=ok, dkim_reason=why,
        dmarc=look_dmarc['dmarc'],
        comment=('Every check passes, because they all evaluate the domain the '
                 'attacker chose. acme.example may publish p=reject and it is '
                 'not consulted: nothing in this message claims to be '
                 'acme.example. A reader sees "Acme Finance". This is what '
                 '"p=reject stops spoofing" leaves out.'))

    # Display-name spoofing, where the From domain is not even similar.
    dn_hdrs = [('From', 'Acme Finance <billing@mailer.unrelated.example>')] + HEADERS[1:]
    dn_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    dn_sig = sign(dn_hdrs, BODY, dn_key, 'mailer.unrelated.example', 's1', H)
    dn_ok, _ = verify(dn_hdrs, BODY, dn_sig, dn_key.public_key())
    out['display_name'] = dict(
        from_header=dn_hdrs[0][1], dkim_verifies=dn_ok,
        dmarc=dmarc_result('mailer.unrelated.example',
                           dkim={'result': 'pass',
                                 'domain': 'mailer.unrelated.example'})['dmarc'],
        comment=('The signed From field includes this display-name text, but '
                 'neither DKIM nor DMARC proves that the sender is entitled to '
                 'the claimed human/brand identity. Some clients hide the address.'))
    return out


def _wrap(t, indent, width=78):
    words, lines, cur = t.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > width - indent:
            lines.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
    lines.append(cur)
    return ('\n' + ' ' * indent).join(lines)


def report(out=None):
    o = run()
    out = sys.stdout if out is None else out
    out.write('Lab 58.2 --- DKIM signed and broken, and DMARC alignment\n')
    out.write('=' * 74 + '\n\n')
    out.write('SIGNATURE CASES (2048-bit RSA, rsa-sha256, relaxed/relaxed)\n\n')
    for c in o['cases']:
        out.write('  %-52s %s\n' % (c['case'], 'VERIFIES' if c['verifies'] else 'fails'))
        out.write('      %s\n' % _wrap(c['comment'], 6))
        if not c['as_expected']:
            out.write('      *** NOT AS EXPECTED ***\n')
    out.write('\nDMARC ALIGNMENT --- From: acme.example\n\n')
    out.write('  %-56s %s\n' % ('scenario', 'DMARC'))
    for a in o['alignment']:
        out.write('  %-56s %s\n' % (a['scenario'][:56], a['dmarc'].upper()))
        for w in a['why']:
            out.write('      %s\n' % _wrap(w, 6))
    out.write('\nTHE PART "p=reject STOPS SPOOFING" LEAVES OUT\n\n')
    lk = o['lookalike']
    out.write('  From: %s\n' % lk['from_header'])
    out.write('  DKIM verifies: %s    DMARC: %s\n' % (lk['dkim_verifies'], lk['dmarc'].upper()))
    out.write('  %s\n\n' % _wrap(lk['comment'], 2))
    dn = o['display_name']
    out.write('  From: %s\n' % dn['from_header'])
    out.write('  DKIM verifies: %s    DMARC: %s\n' % (dn['dkim_verifies'], dn['dmarc'].upper()))
    out.write('  %s\n' % _wrap(dn['comment'], 2))
    out.write('\nWhat a passing DKIM signature establishes: that the holder of the\n')
    out.write('key for s= under d= signed the headers in h= and the first l= octets\n')
    out.write('of the body. Not who wrote it, not that it is true, and --- without\n')
    out.write('alignment --- not that it has anything to do with the From: address.\n')
    return o




# ---------------------------------------------------------------------------
# Cross-implementation check. An implementation that only agrees with itself
# has proved nothing about DKIM; it has proved something about itself.
# ---------------------------------------------------------------------------

def crosscheck():
    """Verify OUR signature with dkimpy, an independent implementation.

    Skips cleanly when dkimpy is not installed --- and says it skipped, rather
    than reporting a pass it did not perform.
    """
    try:
        import dkim as dkimpy                                    # noqa: F401
    except ImportError:
        return dict(ran=False,
                    why='dkimpy is not installed; pip install dkimpy to run this. '
                        'A skipped check is not a passed one.')
    from cryptography.hazmat.primitives import serialization
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    der = key.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    txt = b'v=DKIM1; k=rsa; p=' + base64.b64encode(der)
    sig = sign(HEADERS, BODY, key, 'acme.example', 'sel1', H)
    msg = (b'DKIM-Signature: ' + sig.encode() + CRLF
           + b''.join(('%s: %s\r\n' % (n, v)).encode() for n, v in HEADERS)
           + CRLF + BODY)

    def dnsfunc(name, timeout=5):
        return txt

    good = dkimpy.verify(msg, dnsfunc=dnsfunc)
    bad = dkimpy.verify(msg.replace(b'87654321', b'99999999'), dnsfunc=dnsfunc)
    return dict(ran=True, dkimpy_accepts_our_signature=bool(good),
                dkimpy_rejects_tampered_body=not bool(bad),
                agreed=bool(good) and not bool(bad),
                why=('Our signature was produced by this lab and verified by an '
                     'independent implementation, and the tampered copy was '
                     'rejected by both. That is what makes the demonstrations '
                     'above evidence about DKIM rather than about this file.'))


def main(argv):
    if '--crosscheck' in argv:
        print(json.dumps(crosscheck(), indent=1))
        return 0
    if '--json' in argv:
        print(json.dumps(dict(run(), crosscheck=crosscheck()), indent=1))
        return 0
    o = report()
    c = crosscheck()
    print()
    if c['ran']:
        print('Cross-checked against dkimpy: it accepts our signature (%s) and '
              'rejects\nthe tampered body (%s).'
              % (c['dkimpy_accepts_our_signature'], c['dkimpy_rejects_tampered_body']))
    else:
        print('Cross-check SKIPPED: %s' % c['why'])
    return 0



if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
