#!/usr/bin/env python3
"""Checks for forward_secrecy.py.

A negative result is only evidence if a positive one was possible, so the
first duty of these checks is to establish that the recovery machinery WORKS:
that the derivation is deterministic, that the attacker really enumerates
several agreements, and that the same machinery succeeds against the static
design. Only then does its failure against the ephemeral design mean anything.
"""
import hashlib
import hmac
import json
import os
import subprocess
import sys

from cryptography.hazmat.primitives.asymmetric import ec

import forward_secrecy as F

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
    except F.SecrecyError:
        return True
    except Exception:
        return False
    return False


# ===========================================================================
# the machinery must be capable of succeeding, or a failure proves nothing
# ===========================================================================
shared = os.urandom(32)
check('derivation is deterministic',
      F.derive(shared, b'session') == F.derive(shared, b'session'))
check('a different secret gives a different key',
      F.derive(shared, b'session') != F.derive(os.urandom(32), b'session'))
check('a different label gives a different key',
      F.derive(shared, b'session') != F.derive(shared, b'other'))
check('a different salt gives a different key',
      F.derive(shared, b'session') != F.derive(shared, b'session', salt=b'x'))
check('derivation returns 32 bytes', len(F.derive(shared, b'session')) == 32)
check('an empty secret is refused', raises(F.derive, b'', b'session'))
check('a non-bytes secret is refused', raises(F.derive, 'text', b'session'))

# ECDH itself is symmetric, which is why the recovery could work at all
a, b = ec.generate_private_key(ec.SECP256R1()), ec.generate_private_key(ec.SECP256R1())
check('ECDH agrees from either side',
      a.exchange(ec.ECDH(), b.public_key()) == b.exchange(ec.ECDH(), a.public_key()))

# ===========================================================================
# the attacker really enumerates, and really succeeds where it should
# ===========================================================================
for trial in range(10):
    sta = F.static_session()
    attempts = F.attacker_recovers(sta)
    hits = [x for x in attempts if x['candidate'] == sta['session_key']]
    check('static trial %d tries more than one agreement' % trial, len(attempts) > 1)
    check('static trial %d recovers the session key' % trial, len(hits) >= 1)
    check('static trial %d names the winning combination' % trial,
          hits and hits[0]['private'] and hits[0]['public'])
    check('static trial %d candidates are all 32 bytes' % trial,
          all(len(x['candidate']) == 32 for x in attempts))

for trial in range(10):
    eph = F.ephemeral_session()
    attempts = F.attacker_recovers(eph)
    hits = [x for x in attempts if x['candidate'] == eph['session_key']]
    check('ephemeral trial %d tries more than one agreement' % trial,
          len(attempts) > 1)
    check('ephemeral trial %d recovers nothing' % trial, not hits)
    check('ephemeral trial %d still produced real candidates' % trial,
          all(len(x['candidate']) == 32 for x in attempts))
    check('ephemeral trial %d candidates are distinct from each other' % trial,
          len({x['candidate'] for x in attempts}) > 1)

check('both designs give the attacker the same number of agreements',
      len(F.attacker_recovers(F.ephemeral_session()))
      == len(F.attacker_recovers(F.static_session())))
check('the ephemeral session did not keep its ephemeral privates',
      F.ephemeral_session()['ephemeral_private_kept'] is False)
check('the ephemeral session records only PUBLIC ephemeral material',
      all(not hasattr(v, 'exchange')
          for k, v in F.ephemeral_session()['recorded'].items()
          if hasattr(v, 'public_numbers')))
check('the ephemeral session still holds long-term privates to seize',
      all(hasattr(v, 'exchange')
          for v in F.ephemeral_session()['seized_later'].values()))

# ===========================================================================
# the demo, repeatedly
# ===========================================================================
for i in range(6):
    d = F.demo_compromise()
    check('demo %d: static is recovered' % i,
          d['static']['recovered_session_key'] is True)
    check('demo %d: ephemeral is not' % i,
          d['ephemeral']['recovered_session_key'] is False)
    check('demo %d: the attacker held the same material both times' % i,
          d['same_attacker_both_times'] is True)
    check('demo %d: several agreements were attempted' % i,
          d['ephemeral']['agreements_attempted'] > 1)
    check('demo %d: the winning combination is named for static' % i,
          d['static']['which_combination_worked'] is not None)
    check('demo %d: no combination is named for ephemeral' % i,
          d['ephemeral']['which_combination_worked'] is None)
    check('demo %d lists the combinations tried' % i,
          len(d['ephemeral']['combinations_tried'])
          == d['ephemeral']['agreements_attempted'])

# ===========================================================================
# the pre-shared secret
# ===========================================================================
psk, ctx = os.urandom(32), os.urandom(16)
check('psk derivation is deterministic',
      F.psk_session(psk, ctx) == F.psk_session(psk, ctx))
check('a different context gives a different key',
      F.psk_session(psk, ctx) != F.psk_session(psk, os.urandom(16)))
check('a different psk gives a different key',
      F.psk_session(psk, ctx) != F.psk_session(os.urandom(32), ctx))
check('a short psk is refused', raises(F.psk_session, b'short', ctx))
check('a non-bytes psk is refused', raises(F.psk_session, 'text' * 8, ctx))
k1, rec1 = F.psk_dhe_session(psk, ctx)
k2, rec2 = F.psk_dhe_session(psk, ctx)
check('psk_dhe gives a different key each time, same psk and context', k1 != k2)
check('psk_ke gives the SAME key each time, same psk and context',
      F.psk_session(psk, ctx) == F.psk_session(psk, ctx))
check('psk_dhe records two public points',
      set(rec1) == {'a_public', 'b_public'})
check('psk_dhe records no private half',
      all(not hasattr(v, 'exchange') for v in rec1.values()))
for i in range(6):
    p = F.demo_psk()
    check('psk demo %d: psk_ke is recovered' % i, p['psk_ke']['recovered'] is True)
    check('psk demo %d: psk_dhe_ke is not' % i,
          p['psk_dhe_ke']['recovered'] is False)
    check('psk demo %d tried several derivations against psk_dhe' % i,
          p['psk_dhe_ke']['derivations_attempted'] > 1)
    check('psk demo %d used the same psk both times' % i,
          p['same_psk_both_times'] is True)

# ===========================================================================
# the taxonomy, and its honesty about not being executed
# ===========================================================================
check('three TLS 1.3 modes are described', len(F.TLS13_MODES) == 3)
check('exactly one lacks forward secrecy',
      sum(1 for m in F.TLS13_MODES if not m['forward_secret']) == 1)
check('the one that lacks it is psk_ke',
      next(m for m in F.TLS13_MODES if not m['forward_secret'])['mode']
      .startswith('psk_ke'))
check('every mode explains itself',
      all(len(m['why']) > 30 for m in F.TLS13_MODES))
check('at least five things are listed as not covered', len(F.NOT_COVERED) >= 5)
for title, body in F.NOT_COVERED:
    check('%r is explained' % title[:28], len(body) > 60)
check('the endpoint compromise is listed',
      any('endpoint' in t for t, _ in F.NOT_COVERED))
check('the random number generator is listed',
      any('random number' in t for t, _ in F.NOT_COVERED))
check('deliberate key export is listed',
      any('exported' in t for t, _ in F.NOT_COVERED))
check('traffic analysis is listed',
      any('traffic analysis' in t for t, _ in F.NOT_COVERED))

rep = F.build_report()
check('the report separates executed from described',
      'executed' in rep and 'described' in rep)
check('section C is labelled static review',
      'STATIC REVIEW' in rep['evidence_categories']['section_C'])
check('sections A and B are labelled Linux execution',
      'Linux execution' in rep['evidence_categories']['sections_A_B'])
check('the report says psk_ke was not forced',
      'does not expose that choice' in rep['evidence_categories']['section_C'])
check('report carries caveats', len(rep['caveats']) >= 5)
check('a caveat says this is not a TLS implementation',
      any('not a TLS implementation' in c for c in rep['caveats']))
check('a caveat says a failure to recover is not a proof',
      any('not a proof that' in c for c in rep['caveats']))
check('a caveat says the attacker was handed the keys outright',
      any('given the private keys outright' in c for c in rep['caveats']))
check('report JSON-serialises with no key material',
      isinstance(json.dumps(rep), str))
text = F.report_text(rep)
check('the text names four sections',
      all(x in text for x in ('A.', 'B.', 'C.', 'D.')))
check('the text says section C was not measured',
      'DID NOT MEASURE' in text)
check('the text says nothing is asserted unrecoverable',
      'asserted to be unrecoverable' in text)
check('the text says the attempts are made and compared',
      'the attempts are made and compared' in text)
check('the text discloses what it does not establish', 'does NOT establish' in text)
check('no report line exceeds eighty characters',
      all(len(x) <= 80 for x in text.splitlines()))

out = subprocess.run([sys.executable, 'forward_secrecy.py', '--json'],
                     capture_output=True, text=True)
check('--json exits zero', out.returncode == 0)
check('--json parses', isinstance(json.loads(out.stdout), dict))
plain = subprocess.run([sys.executable, 'forward_secrecy.py'],
                       capture_output=True, text=True)
check('plain run exits zero', plain.returncode == 0)
check('plain run is not JSON', not plain.stdout.lstrip().startswith('{'))

print('forward_secrecy: %d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: ' + f)
sys.exit(1 if FAILED else 0)
