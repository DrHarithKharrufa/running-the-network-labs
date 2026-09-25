#!/usr/bin/env python3
"""Lab 51.2 --- forward secrecy is a claim about ONE compromise, executed.

WHY THIS LAB EXISTS
-------------------
The chapter said forward secrecy means "compromise of the long-term key does
not expose past sessions", and then said TLS 1.3 gives it.  The first statement
is missing its scope and the second is not true of every mode.

  FORWARD SECRECY ANSWERS EXACTLY ONE QUESTION.  It says: if the LONG-TERM key
  is taken LATER, are the sessions already recorded still closed?  It says
  nothing about an endpoint compromised at the time, a broken random number
  generator, session keys written to a log or a decryption appliance, or a
  resumption secret kept for days.  Stated without its scope it is read as "we
  are safe against key compromise", which is a different and much larger claim.

  AND TLS 1.3 HAS THREE KEY-EXCHANGE MODES, NOT ONE.  A full handshake uses
  (EC)DHE and has forward secrecy.  Resumption may use psk_dhe_ke, which mixes
  a fresh (EC)DHE share and keeps it.  Resumption may also use psk_ke, which
  derives everything from the pre-shared secret and has NO forward secrecy at
  all: whoever obtains that secret later opens every session that used it.
  "TLS 1.3 gives you forward secrecy" is true of the first two and false of the
  third, and the third is a resumption mode a deployment may well be using.

WHAT IS EXECUTED HERE AND WHAT IS NOT
-------------------------------------
Sections A and B are LINUX EXECUTION.  Real key agreement runs on this machine
--- ephemeral in one case, static in the other --- a session key is derived, the
keys an attacker would later seize are then handed to a recovery routine, and
whether the session key falls out is OBSERVED rather than asserted.  Section B
does the same for a pre-shared secret, which is the psk_ke shape.

Section C is STATIC REVIEW of the mode taxonomy.  This script does NOT force a
TLS 1.3 handshake into psk_ke: Python's ssl module does not expose that choice,
so the mode behaviour is described from the specification rather than executed,
and it is labelled as such in every output.  Do not read Section C as a
measurement.

    python3 forward_secrecy.py
    python3 forward_secrecy.py --json
    python3 test_forward_secrecy.py
"""
import argparse
import hashlib
import hmac
import json
import os
import sys
import textwrap

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class SecrecyError(ValueError):
    """The described exchange cannot be carried out."""


def derive(shared, label, salt=b''):
    """One session key from one shared secret. Deterministic, so recovery is
    testable: the same inputs must give the same key or the comparison below
    would prove nothing."""
    if not isinstance(shared, bytes) or not shared:
        raise SecrecyError('a shared secret is required')
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=salt,
                info=label).derive(shared)


# ===========================================================================
# A. ephemeral against static, with the same attacker
# ===========================================================================
def ephemeral_session():
    """A session whose key agreement uses keys discarded at the end.

    The long-term keys sign; they do not derive. That separation is the whole
    of forward secrecy, and it is visible in what this function returns: the
    long-term private keys are kept, the ephemeral ones are not.
    """
    server_long = ec.generate_private_key(ec.SECP256R1())
    client_long = ec.generate_private_key(ec.SECP256R1())
    server_eph = ec.generate_private_key(ec.SECP256R1())
    client_eph = ec.generate_private_key(ec.SECP256R1())
    shared = client_eph.exchange(ec.ECDH(), server_eph.public_key())
    key = derive(shared, b'session')
    transcript = os.urandom(16)
    signature = server_long.sign(
        server_eph.public_key().public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint) + transcript,
        ec.ECDSA(hashes.SHA256()))
    return {
        'session_key': key,
        # what an attacker seizes later, when the server is taken:
        'seized_later': {'server_long_term_private': server_long,
                         'client_long_term_private': client_long},
        # what the attacker recorded at the time:
        'recorded': {'server_eph_public': server_eph.public_key(),
                     'client_eph_public': client_eph.public_key(),
                     'signature': signature, 'transcript': transcript},
        # discarded when the session ended, and that is the point:
        'ephemeral_private_kept': False,
    }


def static_session():
    """A session whose key agreement uses the long-term keys themselves.

    This is the shape of static-DH, of RSA key transport, and of any design
    where the key that authenticates is also the key that derives.
    """
    server_long = ec.generate_private_key(ec.SECP256R1())
    client_long = ec.generate_private_key(ec.SECP256R1())
    shared = client_long.exchange(ec.ECDH(), server_long.public_key())
    key = derive(shared, b'session')
    return {
        'session_key': key,
        'seized_later': {'server_long_term_private': server_long,
                         'client_long_term_private': client_long},
        'recorded': {'server_long_public': server_long.public_key(),
                     'client_long_public': client_long.public_key()},
        'ephemeral_private_kept': False,
    }


def attacker_recovers(session):
    """Try EVERY agreement the attacker can actually form, and report the best.

    This deliberately does not shortcut. Returning "not recoverable" because
    the author knows it is not recoverable would make this function an
    assertion dressed as a computation --- the defect this book keeps finding
    in its own labs. So the attacker enumerates every (private, public) pair
    available to them, derives a candidate key from each, and the caller
    compares. No cryptanalysis is attempted: each candidate is the LEGITIMATE
    derivation run by somebody holding that private key.
    """
    seized, recorded = session['seized_later'], session['recorded']
    privates = [(n, v) for n, v in seized.items()
                if hasattr(v, 'exchange')]
    publics = [(n, v) for n, v in recorded.items()
               if hasattr(v, 'public_numbers')]
    # the attacker can also pair a seized private against another seized
    # private's public half
    publics += [(n + '_public_of_seized', v.public_key())
                for n, v in seized.items() if hasattr(v, 'public_key')]
    attempts = []
    for pname, priv in privates:
        for qname, pub in publics:
            try:
                shared = priv.exchange(ec.ECDH(), pub)
            except Exception:
                continue
            attempts.append({'private': pname, 'public': qname,
                             'candidate': derive(shared, b'session')})
    return attempts


def demo_compromise():
    eph, sta = ephemeral_session(), static_session()
    out = {}
    for label, session in (('ephemeral', eph), ('static', sta)):
        attempts = attacker_recovers(session)
        hits = [a for a in attempts if a['candidate'] == session['session_key']]
        out[label] = {
            'attacker_holds': ['server long-term private key',
                               'client long-term private key',
                               'the full recorded handshake'],
            'agreements_attempted': len(attempts),
            'combinations_tried': ['%s x %s' % (a['private'], a['public'])
                                   for a in attempts],
            'recovered_session_key': bool(hits),
            'which_combination_worked': (hits[0]['private'] + ' x '
                                         + hits[0]['public']) if hits else None,
        }
    out['same_attacker_both_times'] = (
        out['ephemeral']['attacker_holds'] == out['static']['attacker_holds'])
    return out


# ===========================================================================
# B. the pre-shared secret, which is the psk_ke shape
# ===========================================================================
def psk_session(psk, context):
    """A session key derived from a pre-shared secret and nothing else.

    This is what psk_ke does: no fresh key agreement contributes, so the
    session key is a function of the PSK and public transcript material.
    """
    if not isinstance(psk, bytes) or len(psk) < 16:
        raise SecrecyError('a pre-shared secret of at least 16 bytes')
    return hmac.new(psk, b'session|' + context, hashlib.sha256).digest()


def psk_dhe_session(psk, context):
    """psk_dhe_ke: the PSK, mixed with a fresh ephemeral agreement.

    The ephemeral private keys are discarded here exactly as in Section A, so
    the PSK alone is no longer sufficient.
    """
    a = ec.generate_private_key(ec.SECP256R1())
    b = ec.generate_private_key(ec.SECP256R1())
    shared = a.exchange(ec.ECDH(), b.public_key())
    return (hmac.new(psk, b'session|' + context + shared,
                     hashlib.sha256).digest(),
            {'a_public': a.public_key(), 'b_public': b.public_key()})


def demo_psk():
    psk = os.urandom(32)
    ctx = os.urandom(16)
    key_ke = psk_session(psk, ctx)
    key_dhe, recorded = psk_dhe_session(psk, ctx)
    # The attacker obtains the PSK later and holds the recorded transcript.
    # Again, attempt rather than assert: try every derivation the PSK allows.
    attempts_ke = [psk_session(psk, ctx)]
    attempts_dhe = [
        psk_session(psk, ctx),
        hmac.new(psk, b'session|' + ctx, hashlib.sha256).digest(),
        hmac.new(psk, b'session|' + ctx + b'', hashlib.sha256).digest(),
    ]
    # The attacker has the two ephemeral PUBLIC points and no private half, so
    # the only thing they can feed the KDF is public material.
    for name in ('a_public', 'b_public'):
        pub = recorded[name].public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint)
        attempts_dhe.append(
            hmac.new(psk, b'session|' + ctx + pub, hashlib.sha256).digest())
    return {
        'psk_ke': {'attacker_obtained_the_psk_later': True,
                   'derivations_attempted': len(attempts_ke),
                   'recovered': key_ke in attempts_ke,
                   'note': 'The PSK is the whole derivation, so obtaining it '
                           'later opens every session that used it.'},
        'psk_dhe_ke': {'attacker_obtained_the_psk_later': True,
                       'derivations_attempted': len(attempts_dhe),
                       'recovered': key_dhe in attempts_dhe,
                       'note': 'A fresh agreement contributes and its private '
                               'halves were discarded, so the PSK alone is no '
                               'longer sufficient.'},
        'same_psk_both_times': True,
    }


# ===========================================================================
# C. the taxonomy --- described, not executed
# ===========================================================================
TLS13_MODES = [
    {'mode': '(EC)DHE full handshake', 'forward_secret': True,
     'why': 'A fresh key share each time; the private halves are discarded.'},
    {'mode': 'psk_dhe_ke resumption', 'forward_secret': True,
     'why': 'The pre-shared secret is mixed with a fresh (EC)DHE share.'},
    {'mode': 'psk_ke resumption', 'forward_secret': False,
     'why': 'Derived from the pre-shared secret alone. Whoever obtains that '
            'secret later opens every session that used it.'},
]

NOT_COVERED = [
    ('an endpoint compromised at the time',
     'Forward secrecy protects recorded traffic against a LATER key seizure. '
     'An attacker inside the machine while the session is live reads the '
     'plaintext and the session key, and no property of the key exchange '
     'prevents that.'),
    ('a predictable random number generator',
     'The whole construction rests on the ephemeral private half being '
     'unguessable. A weak or duplicated RNG --- an embedded device with no '
     'entropy at boot, a cloned VM image --- makes it guessable, and forward '
     'secrecy fails silently while the handshake looks identical.'),
    ('session keys deliberately exported',
     'Keys written to a log for a monitoring appliance, or escrowed for a '
     'decryption middlebox, are keys that exist after the session. The design '
     'is unchanged and the property is gone.'),
    ('long-lived resumption material',
     'A ticket key or session secret retained for days extends the window in '
     'which one seizure opens many sessions. Forward secrecy is a statement '
     'about a key nobody kept, so a key somebody kept is outside it.'),
    ('traffic analysis',
     'Nothing here hides who spoke to whom, when, how often, or how much. '
     'Recorded metadata stays readable however good the key exchange is.'),
]


def build_report():
    return {
        'executed': {'compromise': demo_compromise(), 'psk': demo_psk()},
        'described': {'tls13_modes': TLS13_MODES, 'not_covered': NOT_COVERED},
        'evidence_categories': {
            'sections_A_B': 'Linux execution on this machine. Real elliptic-'
                            'curve key agreement, real derivation, real '
                            'recovery attempt by an attacker holding the '
                            'seized keys and the recorded transcript.',
            'section_C': 'STATIC REVIEW of the mode taxonomy. No TLS 1.3 '
                         'handshake was forced into psk_ke here, because '
                         'Python\'s ssl module does not expose that choice. '
                         'Treat it as read from the specification, not '
                         'measured.',
        },
        'caveats': [
            'Sections A and B model the KEY AGREEMENT, not TLS. They use the '
            'same primitive TLS 1.3 uses and the same discard discipline, and '
            'they are not a TLS implementation or a test of one.',
            'The attacker here is given the private keys outright, which is '
            'the strongest form of the compromise the property is about. No '
            'cryptanalysis is attempted or implied.',
            'A failure to recover is a failure by THIS attacker with THIS '
            'material. It is evidence about the construction, not a proof that '
            'no attack exists.',
            'Section C is not executed. Which mode a deployment actually '
            'negotiates is a question for that deployment, answered by '
            'capturing a handshake or reading the server configuration.',
            'Nothing here measures any real service, and no claim is made '
            'about what any particular library, server or vendor does by '
            'default.',
        ],
    }


def _wrap(lines, text, indent='  '):
    lines.extend(textwrap.wrap(text, width=74, initial_indent=indent,
                               subsequent_indent=indent))


def report_text(rep):
    L = []
    c = rep['executed']['compromise']
    L.append('Forward secrecy is a claim about ONE compromise (Chapter 51)')
    L.append('Sections A and B ran here. Section C is read, not measured.')
    L.append('')
    L.append('A. The same attacker, against two designs')
    L.append('-' * 74)
    L.append('  The attacker is handed, in both cases:')
    for h in c['ephemeral']['attacker_holds']:
        L.append('    - %s' % h)
    L.append('')
    L.append('  %-20s %s agreements tried, recovered: %s'
             % ('ephemeral agreement', c['ephemeral']['agreements_attempted'],
                c['ephemeral']['recovered_session_key']))
    L.append('  %-20s %s agreements tried, recovered: %s'
             % ('static agreement', c['static']['agreements_attempted'],
                c['static']['recovered_session_key']))
    if c['static']['which_combination_worked']:
        L.append('      the static one fell to: %s'
                 % c['static']['which_combination_worked'])
    L.append('')
    _wrap(L, 'Both rows enumerate every key agreement the attacker can '
             'actually form from what they hold and derive a candidate from '
             'each. Nothing is asserted to be unrecoverable: the attempts are '
             'made and compared.')
    L.append('')
    _wrap(L, 'Same attacker, same material, opposite outcomes. In the static '
             'design the key that authenticates is also the key that derives, '
             'so seizing it later opens everything recorded earlier. In the '
             'ephemeral design the long-term key only SIGNS: it proves who was '
             'speaking and contributes nothing to the secret, and the halves '
             'that did contribute were discarded when the session ended.')
    L.append('')
    _wrap(L, 'That is the whole property, and it is narrower than it sounds. '
             'The question it answers is: if the long-term key is taken LATER, '
             'is the traffic recorded EARLIER still closed? It answers nothing '
             'else.')
    L.append('')
    L.append('B. A pre-shared secret, which is the resumption case')
    L.append('-' * 74)
    p = rep['executed']['psk']
    L.append('  psk_ke      (PSK alone)         %d derivations tried, '
             'recovered: %s'
             % (p['psk_ke']['derivations_attempted'], p['psk_ke']['recovered']))
    L.append('  psk_dhe_ke  (PSK + fresh share)  %d derivations tried, '
             'recovered: %s'
             % (p['psk_dhe_ke']['derivations_attempted'],
                p['psk_dhe_ke']['recovered']))
    L.append('')
    _wrap(L, p['psk_ke']['note'])
    _wrap(L, p['psk_dhe_ke']['note'])
    L.append('')
    L.append('C. The three TLS 1.3 modes --- read from the specification')
    L.append('-' * 74)
    for m in rep['described']['tls13_modes']:
        L.append('  %-26s forward secrecy: %s'
                 % (m['mode'], 'YES' if m['forward_secret'] else 'NO'))
        _wrap(L, m['why'], indent='      ')
    L.append('')
    _wrap(L, 'So "TLS 1.3 gives you forward secrecy" is true of two modes and '
             'false of the third, and the third is a resumption mode a '
             'deployment may be using without anyone having chosen it. The '
             'question to ask is not which TLS version you run; it is which '
             'resumption mode your servers accept, which is answered by the '
             'configuration or by a captured handshake rather than by a '
             'version number. THIS SCRIPT DID NOT MEASURE THAT --- Python\'s '
             'ssl module does not expose the choice, so the table above is '
             'read from the specification.')
    L.append('')
    L.append('D. What forward secrecy does not cover')
    L.append('-' * 74)
    for title, body in rep['described']['not_covered']:
        L.append('  %s' % title)
        _wrap(L, body, indent='      ')
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
    except SecrecyError as exc:
        print('cannot evaluate: %s' % exc, file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(rep, indent=2))
    else:
        print(report_text(rep))
    return 0


if __name__ == '__main__':
    sys.exit(main())
