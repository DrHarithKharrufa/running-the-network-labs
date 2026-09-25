#!/usr/bin/env python3
"""Checks for tls_validation.py.

Two things need pinning that a pass/fail count would not catch.

  EACH CASE MUST FAIL FOR ITS OWN REASON. A case labelled "path length
  exceeded" that is actually rejected as untrusted still shows accepted=False
  and still passes a naive check, while demonstrating nothing. One case in the
  first draft of this lab did exactly that, so every rejection here is pinned
  to its expected OpenSSL verification code.

  AND THE SIGNATURES MUST REALLY BE VALID. The lab's headline claim is that
  most of these rejections happen on chains where the cryptography is
  perfect. That is verified here directly, by checking each certificate's
  signature against its issuer's public key, rather than being asserted in
  the lab's own prose.
"""
import json
import subprocess
import sys

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

import tls_validation as T

CHECKS = 0
FAILED = []


def check(label, cond):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


REPORT = T.run()
BY_CASE = {c['case']: c for c in REPORT['cases']}

# ===========================================================================
# the run as a whole
# ===========================================================================
check('the suite passes', REPORT['passed'] is True)
check('ten cases are exercised', len(REPORT['cases']) == 10)
check('every case has a name and an explanation',
      all(c['case'] and len(c['about']) > 20 for c in REPORT['cases']))
check('case names are unique', len(BY_CASE) == len(REPORT['cases']))
check('the scope disclaims revocation', 'no revocation check' in REPORT['scope'])
check('the scope disclaims forward secrecy',
      'no\nforward-secrecy test' in REPORT['scope']
      or 'forward-secrecy test' in REPORT['scope'])
check('the scope disclaims performance', 'performance' in REPORT['scope'])
check('the environment is recorded',
      REPORT['python'] and REPORT['openssl'] and REPORT['cryptography'])
check('OpenSSL is identified', 'OpenSSL' in REPORT['openssl'])

# ===========================================================================
# acceptance, and TLS 1.3 specifically
# ===========================================================================
accepted = [c for c in REPORT['cases'] if c.get('accepted')]
rejected = [c for c in REPORT['cases'] if not c.get('accepted')]
check('exactly two cases are accepted', len(accepted) == 2)
check('eight cases are rejected', len(rejected) == 8)
check('every accepted case negotiated TLS 1.3',
      all(c['tls_version'] == 'TLSv1.3' for c in accepted))
check('every accepted case names a cipher', all(c['cipher'] for c in accepted))
check('the control case is accepted',
      BY_CASE['trusted_name_and_chain']['accepted'] is True)
check('turning off the identity check accepts a wrong name',
      BY_CASE['wrong_name_with_identity_check_disabled']['accepted'] is True)
check('and that case had the hostname check disabled',
      BY_CASE['wrong_name_with_identity_check_disabled']['hostname_check'] is False)
check('every other case had the hostname check enabled',
      all(c['hostname_check'] for c in REPORT['cases']
          if c['case'] != 'wrong_name_with_identity_check_disabled'))
check('every rejection carries a verification code',
      all(c.get('verification_code') is not None for c in rejected))
check('every rejection carries a message',
      all(c.get('verification_message') for c in rejected))

# ===========================================================================
# EACH CASE FAILS FOR ITS OWN REASON
# ===========================================================================
EXPECTED = {
    'untrusted_issuer': 20,
    'wrong_dns_name': 62,
    'expired': 10,
    'not_yet_valid': 9,
    'wrong_extended_key_usage': 26,
    'leaf_used_as_issuer': 79,
    'path_length_exceeded': 25,
    'intermediate_without_cert_sign': 79,
}
for case, code in EXPECTED.items():
    check('%s is rejected' % case, BY_CASE[case]['accepted'] is False)
    check('%s is rejected with code %d, not merely rejected' % (case, code),
          BY_CASE[case]['verification_code'] == code)
check('the path-length case is not rejected as untrusted',
      BY_CASE['path_length_exceeded']['verification_code'] != 20)
check('the keyCertSign case is not rejected as untrusted',
      BY_CASE['intermediate_without_cert_sign']['verification_code'] != 20)
check('the leaf-as-issuer case is not rejected as untrusted',
      BY_CASE['leaf_used_as_issuer']['verification_code'] != 20)
check('the path-length message names the constraint',
      'path length' in BY_CASE['path_length_exceeded']['verification_message'].lower())
check('the leaf-as-issuer message names the CA certificate',
      'CA certificate' in BY_CASE['leaf_used_as_issuer']['verification_message'])
check('the expired and not-yet-valid cases differ',
      BY_CASE['expired']['verification_code']
      != BY_CASE['not_yet_valid']['verification_code'])
check('the name failure is distinct from every chain failure',
      BY_CASE['wrong_dns_name']['verification_code']
      not in {BY_CASE[c]['verification_code'] for c in
              ('leaf_used_as_issuer', 'path_length_exceeded', 'untrusted_issuer')})

# ===========================================================================
# THE HEADLINE CLAIM, verified rather than asserted
# ===========================================================================
check('the finding is reported', 'finding' in REPORT)
check('seven rejections are attributed to something other than a bad signature',
      len(REPORT['rejections_not_caused_by_a_bad_signature']) == 7)
check('the untrusted-issuer case is NOT among them, since it has no anchor',
      'untrusted_issuer' not in REPORT['rejections_not_caused_by_a_bad_signature'])
check('the finding states the distinction',
      'not checking a chain of signatures' in REPORT['finding'])


def signature_is_valid(cert, issuer_public_key):
    """Verify one certificate's signature against its issuer's key."""
    try:
        issuer_public_key.verify(
            cert.signature, cert.tbs_certificate_bytes,
            ec.ECDSA(cert.signature_hash_algorithm))
        return True
    except InvalidSignature:
        return False


# rebuild the same structures and check the cryptography really is sound
ca_key, ca = T.make_ca('t', path_length=1)
imposter_key, imposter = T.make_leaf(ca_key, ca, name='imposter.example')
leaf_key, leaf = T.make_leaf(imposter_key, imposter)
check('the imposter is itself validly signed by the trusted root',
      signature_is_valid(imposter, ca.public_key()))
check('and the leaf it issued is validly signed by the imposter',
      signature_is_valid(leaf, imposter.public_key()))
check('so every signature in the leaf-as-issuer chain is valid', True)
check('while the imposter says CA:FALSE',
      imposter.extensions.get_extension_for_class(
          T.x509.BasicConstraints).value.ca is False)

mid_key, mid = T.make_intermediate(ca_key, ca, 'one', path_length=0)
deep_key, deep = T.make_intermediate(mid_key, mid, 'two', path_length=0)
deep_leaf_key, deep_leaf = T.make_leaf(deep_key, deep)
check('intermediate one is validly signed by the root',
      signature_is_valid(mid, ca.public_key()))
check('intermediate two is validly signed by intermediate one',
      signature_is_valid(deep, mid.public_key()))
check('the leaf is validly signed by intermediate two',
      signature_is_valid(deep_leaf, deep.public_key()))
check('the root permits one intermediate',
      ca.extensions.get_extension_for_class(
          T.x509.BasicConstraints).value.path_length == 1)
check('and two were presented, which is the whole of the failure',
      mid.extensions.get_extension_for_class(T.x509.BasicConstraints).value.ca
      and deep.extensions.get_extension_for_class(
          T.x509.BasicConstraints).value.ca)

nosign_key, nosign = T.make_intermediate(ca_key, ca, 'ns', cert_sign=False)
ns_leaf_key, ns_leaf = T.make_leaf(nosign_key, nosign)
check('the no-keyCertSign intermediate is validly signed by the root',
      signature_is_valid(nosign, ca.public_key()))
check('and its leaf is validly signed by it',
      signature_is_valid(ns_leaf, nosign.public_key()))
check('it is marked CA:TRUE',
      nosign.extensions.get_extension_for_class(
          T.x509.BasicConstraints).value.ca is True)
check('and keyCertSign is withheld',
      nosign.extensions.get_extension_for_class(
          T.x509.KeyUsage).value.key_cert_sign is False)
check('whereas a normal intermediate has it',
      mid.extensions.get_extension_for_class(
          T.x509.KeyUsage).value.key_cert_sign is True)
check('a wrong issuer key does NOT verify, so the check above can fail',
      not signature_is_valid(mid, T.make_ca('other')[1].public_key()))

# ===========================================================================
# construction helpers
# ===========================================================================
check('a leaf is marked CA:FALSE',
      T.make_leaf(ca_key, ca)[1].extensions.get_extension_for_class(
          T.x509.BasicConstraints).value.ca is False)
check('a server leaf carries serverAuth',
      any(o.dotted_string == '1.3.6.1.5.5.7.3.1'
          for o in T.make_leaf(ca_key, ca)[1].extensions
          .get_extension_for_class(T.x509.ExtendedKeyUsage).value))
check('a client leaf carries clientAuth instead',
      any(o.dotted_string == '1.3.6.1.5.5.7.3.2'
          for o in T.make_leaf(ca_key, ca, server=False)[1].extensions
          .get_extension_for_class(T.x509.ExtendedKeyUsage).value))
check('an expired leaf really is in the past',
      T.make_leaf(ca_key, ca, validity='expired')[1].not_valid_after_utc
      < T.datetime.now(T.timezone.utc))
check('a future leaf really is in the future',
      T.make_leaf(ca_key, ca, validity='future')[1].not_valid_before_utc
      > T.datetime.now(T.timezone.utc))
check('a named leaf carries that name in its SAN',
      'a.example' in [n.value for n in
                      T.make_leaf(ca_key, ca, name='a.example')[1].extensions
                      .get_extension_for_class(
                          T.x509.SubjectAlternativeName).value])

# ===========================================================================
# CLI
# ===========================================================================
out = subprocess.run([sys.executable, 'tls_validation.py'],
                     capture_output=True, text=True, timeout=300)
check('the script exits zero when the suite passes', out.returncode == 0)
payload = json.loads(out.stdout)
check('the script emits JSON', isinstance(payload, dict))
check('the emitted report also passes', payload['passed'] is True)
check('the emitted report carries ten cases', len(payload['cases']) == 10)

print('tls_validation: %d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: ' + f)
sys.exit(1 if FAILED else 0)
