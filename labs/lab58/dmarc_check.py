#!/usr/bin/env python3
"""Lab 58.1 --- a questionnaire about published records, and what it cannot tell you.

THE DEFECT THIS REPLACES. The version that shipped tested `bool(spf)` and
`bool(dkim)`: any non-empty string counted as a record, and its own example
passed the string \"present\" as the DKIM record. It then printed, for a domain
whose records it had never parsed, \"Enforcing: spoofing of this domain is
actively rejected. Good.\" Three separate falsehoods in one line --- it had not
established that the records were valid, `quarantine` is not rejection, and no
published record rejects anything, because rejection is a receiver's decision.

This version PARSES. It rejects malformed, duplicated and wrongly ordered tags,
checks a deliberately limited set of values, counts top-level SPF lookup terms
as a warning, and distinguishes
ABSENT from INVALID from UNKNOWN. It reports posture and gaps, and it does not
claim any message would be accepted or rejected, because a published record is
a request to receivers, not an outcome.

    python3 dmarc_check.py
    python3 dmarc_check.py --json
    python3 test_dmarc_check.py

Scope: a retained RFC 7489-era syntax/policy linter and selected RFC 7208
checks, NOT full conformance. RFC 9989 supersedes RFC 7489; this tool does not
implement its tree walk or other new rules. It does not resolve recursive SPF
includes/redirects, expand macros or evaluate the actual message path.
Checking a record is not checking a message; lab 58.2 has bounded signing and
alignment examples, not a complete mail receiver.
"""
import json
import re
import sys

ABSENT, VALID, INVALID = 'absent', 'valid', 'invalid'

DMARC_P = ('none', 'quarantine', 'reject')
DMARC_ALIGN = ('r', 's')
DMARC_FO = ('0', '1', 'd', 's')
SPF_QUALIFIERS = '+-~?'
# Mechanisms and modifiers that cost a DNS lookup (RFC 7208 section 4.6.4).
SPF_LOOKUP_TERMS = ('include', 'a', 'mx', 'ptr', 'exists', 'redirect')
SPF_ALL_MECHS = SPF_LOOKUP_TERMS + ('ip4', 'ip6', 'all')


class RecordError(ValueError):
    pass


def _tags(txt, sep=';'):
    """Split a tag-value record, preserving order and duplicates."""
    out = []
    for part in txt.split(sep):
        part = part.strip()
        if not part:
            continue
        if '=' not in part:
            out.append((part, None))
            continue
        k, v = part.split('=', 1)
        out.append((k.strip(), v.strip()))
    return out


def parse_dmarc(txt):
    """Parse a DMARC record strictly. Returns a dict with state and problems."""
    if txt is None:
        return dict(state=ABSENT, problems=[], tags={},
                    note='no DMARC record was supplied for this domain')
    if not isinstance(txt, str):
        raise RecordError('a DMARC record is text; got %s' % type(txt).__name__)
    problems, tags = [], {}
    pairs = _tags(txt)
    if not pairs:
        return dict(state=INVALID, problems=['the record is empty'], tags={})
    if pairs[0][0].lower() != 'v' or pairs[0][1] != 'DMARC1':
        problems.append('the record must begin with v=DMARC1 exactly; it begins '
                        'with %r. A record that does not is not a DMARC record '
                        'at all, and receivers will ignore it silently'
                        % ('='.join(x for x in pairs[0] if x)))
    seen = set()
    for k, v in pairs:
        kl = k.lower()
        if kl in seen:
            problems.append('tag %r appears more than once; the record is '
                            'malformed and how a receiver resolves it is not '
                            'defined' % kl)
        seen.add(kl)
        if v is None:
            problems.append('tag %r has no value' % k)
            continue
        tags[kl] = v
    if 'p' not in tags:
        problems.append('no p= tag: p is REQUIRED, and a record without it does '
                        'not request any policy. Check for a misspelling such '
                        'as policy= before assuming it is deliberate')
    elif tags['p'].lower() not in DMARC_P:
        problems.append('p=%r is not one of %s' % (tags['p'], ', '.join(DMARC_P)))
    for tag, allowed in (('sp', DMARC_P), ('adkim', DMARC_ALIGN), ('aspf', DMARC_ALIGN)):
        if tag in tags and tags[tag].lower() not in allowed:
            problems.append('%s=%r is not one of %s' % (tag, tags[tag], ', '.join(allowed)))
    if 'pct' in tags:
        if not re.fullmatch(r'\d{1,3}', tags['pct']) or not 0 <= int(tags['pct']) <= 100:
            problems.append('pct=%r is not an integer from 0 to 100' % tags['pct'])
    if 'fo' in tags:
        for part in tags['fo'].split(':'):
            if part.strip() not in DMARC_FO:
                problems.append('fo option %r is not one of %s'
                                % (part, ', '.join(DMARC_FO)))
    for tag in ('rua', 'ruf'):
        if tag in tags:
            for uri in tags[tag].split(','):
                if not uri.strip().lower().startswith('mailto:'):
                    problems.append('%s contains %r, which is not a mailto: URI'
                                    % (tag, uri.strip()))
    return dict(state=INVALID if problems else VALID, problems=problems, tags=tags)


def parse_spf(txt):
    """Lint selected SPF syntax and top-level lookup terms; no recursive evaluation."""
    if txt is None:
        return dict(state=ABSENT, problems=[], lookups=0, terms=[],
                    note='no SPF record was supplied for this domain')
    if isinstance(txt, (list, tuple)):
        return dict(state=INVALID, lookups=0, terms=[], problems=[
            'more than one SPF record was published (%d). RFC 7208 makes that a '
            'permerror, and an SPF permerror is not a pass --- so a DMARC policy '
            'relying on SPF alignment will not be satisfied by it' % len(txt)])
    if not isinstance(txt, str):
        raise RecordError('an SPF record is text; got %s' % type(txt).__name__)
    problems, terms, lookups = [], [], 0
    parts = txt.split()
    if not parts or parts[0].lower() != 'v=spf1':
        problems.append('an SPF record must begin with v=spf1; this begins with %r'
                        % (parts[0] if parts else ''))
    has_all = False
    for term in parts[1:]:
        raw = term
        qual = ''
        if term[:1] in SPF_QUALIFIERS:
            qual, term = term[0], term[1:]
        name = term.split(':', 1)[0].split('=', 1)[0].lower()
        terms.append(dict(term=raw, mechanism=name, qualifier=qual or '+'))
        if name in SPF_LOOKUP_TERMS:
            lookups += 1
        if name == 'ptr':
            problems.append('ptr is used; RFC 7208 says it SHOULD NOT be published '
                            'and receivers may ignore it')
        if name == 'all':
            has_all = True
            if (qual or '+') == '+':
                problems.append('+all authorises EVERY sender. That is worse than '
                                'publishing no record, because it turns a neutral '
                                'result into an explicit pass')
        if name not in SPF_ALL_MECHS and not raw.lower().startswith(('exp=', 'redirect=')):
            problems.append('%r is not a recognised SPF term' % raw)
    if not has_all and not any(t['mechanism'] == 'redirect' for t in terms):
        problems.append('the record has neither an all mechanism nor a redirect, '
                        'so it ends in neutral --- which is not a fail and gives '
                        'a receiver nothing to act on')
    if lookups > 10:
        problems.append('%d top-level lookup terms: review required. RFC 7208 limits '
                        'the evaluated message path to 10 lookup terms, including '
                        'recursion. This linter does not execute that path' % lookups)
    elif lookups > 8:
        problems.append('%d DNS-lookup terms, against a limit of 10. Each include '
                        'can add more of its own, so this is close to failing and '
                        'may already fail depending on what the includes expand to'
                        % lookups)
    return dict(state=INVALID if problems else VALID, problems=problems,
                lookups=lookups, terms=terms)


def parse_dkim(txt):
    """Parse a DKIM key record. Presence of a key is not a verified signature."""
    if txt is None:
        return dict(state=ABSENT, problems=[], tags={},
                    note='no DKIM key record was supplied for this selector')
    if not isinstance(txt, str):
        raise RecordError('a DKIM key record is text; got %s' % type(txt).__name__)
    problems, tags = [], {}
    pairs = _tags(txt)
    for k, v in pairs:
        if v is None:
            problems.append('tag %r has no value' % k)
            continue
        tags[k.lower().strip()] = v
    if tags.get('v', 'DKIM1') != 'DKIM1':
        problems.append('v=%r is not DKIM1' % tags['v'])
    if 'p' not in tags:
        problems.append('no p= tag: a DKIM key record without a public key is not '
                        'a key. An EMPTY p= is different and means the key has '
                        'been revoked')
    elif tags['p'] == '':
        problems.append('p= is empty, which publishes a REVOKED key: signatures '
                        'using this selector will not verify')
    elif not re.fullmatch(r'[A-Za-z0-9+/=\s]+', tags['p']):
        problems.append('p= is not base64')
    if tags.get('k', 'rsa').lower() not in ('rsa', 'ed25519'):
        problems.append('k=%r is not a key type this check recognises' % tags['k'])
    return dict(state=INVALID if problems else VALID, problems=problems, tags=tags)


def assess(domain, spf=None, dkim=None, dmarc=None):
    s, k, d = parse_spf(spf), parse_dkim(dkim), parse_dmarc(dmarc)
    p = d['tags'].get('p', '').lower() if d['state'] == VALID else None
    pct = int(d['tags'].get('pct', 100)) if d['state'] == VALID else None
    findings = []
    if d['state'] == ABSENT:
        findings.append('No DMARC record. Receivers have no requested disposition '
                        'and no reporting address, so you also have no visibility.')
    elif d['state'] == INVALID:
        findings.append('The DMARC record does not parse. An unparseable record is '
                        'treated as absent, which is the same outcome as publishing '
                        'nothing while believing you are protected.')
    else:
        if p == 'none':
            findings.append('p=none requests no action. It is the correct place to '
                            'START --- it produces the reports you need to find your '
                            'own legitimate senders before you tighten.')
        elif p == 'quarantine':
            findings.append('p=quarantine asks receivers to treat failing mail as '
                            'suspicious. QUARANTINE IS NOT REJECTION: the message is '
                            'usually still delivered, to a spam folder.')
        elif p == 'reject':
            findings.append('p=reject asks receivers to reject failing mail. It is a '
                            'REQUEST: large receivers generally honour it, some do '
                            'not, and local allowlists override it.')
        if pct is not None and pct < 100:
            findings.append('pct=%d applies the policy to only that percentage of '
                            'failing messages; the rest get the next weaker policy.'
                            % pct)
    if s['state'] == VALID and s['lookups'] > 0:
        findings.append('SPF has %d top-level lookup terms; recursive path budget unverified.' % s['lookups'])
    if k['state'] == VALID:
        findings.append('A DKIM key is published for the selector supplied. That '
                        'says a key exists; it says nothing about whether any '
                        'message was signed with it, whether the signature '
                        'verifies, or whether d= aligns with the From: domain.')
    return dict(
        domain=domain, spf=s, dkim=k, dmarc=d, policy=p, findings=findings,
        what_this_cannot_tell_you=[
            'whether any real message passes: that needs a message, not a record '
            '(lab 58.2)',
            'whether every legitimate sender is covered --- the reports do that, '
            'and only over time',
            'what any particular receiver will do, since policy is a request and '
            'receivers override it',
            'whether a lookalike domain is sending in your name: your policy is '
            'not consulted for a domain that is not yours',
        ])


CASES = {
    'nothing published': dict(),
    'the string "present", which the old lab accepted as a DKIM record':
        dict(spf='v=spf1 include:_spf.example -all', dkim='present',
             dmarc='v=DMARC1; p=reject; rua=mailto:d@acme.example'),
    'a DMARC record with the version tag not first':
        dict(dmarc='p=reject; v=DMARC1; rua=mailto:d@acme.example'),
    'a misspelled policy tag':
        dict(dmarc='v=DMARC1; policy=reject; rua=mailto:d@acme.example'),
    'a duplicate tag':
        dict(dmarc='v=DMARC1; p=none; p=reject; rua=mailto:d@acme.example'),
    'SPF over the lookup limit':
        dict(spf='v=spf1 include:a.example include:b.example include:c.example '
                 'include:d.example include:e.example include:f.example '
                 'include:g.example include:h.example include:i.example '
                 'include:j.example include:k.example -all',
             dmarc='v=DMARC1; p=reject; rua=mailto:d@acme.example'),
    'two SPF records published at once':
        dict(spf=['v=spf1 include:a.example -all', 'v=spf1 include:b.example ~all']),
    'a revoked DKIM key':
        dict(dkim='v=DKIM1; k=rsa; p=',
             dmarc='v=DMARC1; p=reject; rua=mailto:d@acme.example'),
    'a careful domain at the start of the journey':
        dict(spf='v=spf1 include:_spf.example -all',
             dkim='v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A',
             dmarc='v=DMARC1; p=none; pct=100; rua=mailto:d@acme.example; fo=1'),
    'the same domain, enforcing':
        dict(spf='v=spf1 include:_spf.example -all',
             dkim='v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A',
             dmarc='v=DMARC1; p=reject; adkim=s; aspf=s; rua=mailto:d@acme.example'),
}


def _w(t, i, width=78):
    words, lines, cur = t.split(), [], ''
    for x in words:
        if len(cur) + len(x) + 1 > width - i:
            lines.append(cur); cur = x
        else:
            cur = (cur + ' ' + x).strip()
    lines.append(cur)
    return ('\n' + ' ' * i).join(lines)


def report(out=None):
    out = sys.stdout if out is None else out
    out.write('Lab 58.1 --- what the published records say, and what they do not\n')
    out.write('=' * 74 + '\n\n')
    for name, kw in CASES.items():
        a = assess(name, **kw)
        out.write('CASE: %s\n' % name)
        for label, r in (('SPF', a['spf']), ('DKIM', a['dkim']), ('DMARC', a['dmarc'])):
            out.write('  %-6s %s\n' % (label + ':', r['state'].upper()))
            for p in r['problems']:
                out.write('         - %s\n' % _w(p, 11))
        for f in a['findings']:
            out.write('     %s\n' % _w(f, 5))
        out.write('\n')
    out.write('No line above says a message would be accepted or rejected. A\n')
    out.write('published record is a request to receivers and a statement about\n')
    out.write('DNS. Whether a message passes is a question about a message.\n')


def main(argv):
    if '--json' in argv:
        print(json.dumps({n: assess(n, **kw) for n, kw in CASES.items()}, indent=1))
        return 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
