#!/usr/bin/env python3
"""Checks for primitives.py.

This lab makes claims by DOING things, so the tests have a different first duty
from the rest of the book's labs: they must show that each demonstration really
demonstrates, rather than that a model is self-consistent. Three things are
therefore checked before anything else.

  The hand-written MD5 and SHA-256 are really MD5 and SHA-256, at every length
  from 0 to 130 bytes --- which crosses the 55/56 and 119/120 padding
  boundaries where a wrong implementation survives casual testing.

  The forgeries are checked against what the KEY HOLDER would compute, not
  against the forger's own arithmetic. A forgery that only agrees with itself
  proves nothing.

  And each attack is shown to FAIL when its stated precondition is removed: a
  wrong key-length guess, a non-repeated nonce, the HMAC construction. An
  attack that succeeds unconditionally is a bug in the test harness.
"""
import hashlib
import hmac
import json
import math
import os
import subprocess
import sys

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

import primitives as P

CHECKS = 0
FAILED = []


def check(label, cond):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except P.PrimitiveError:
        return True
    except Exception:
        return False
    return False


# ===========================================================================
# the hashes are really the hashes, across every padding boundary
# ===========================================================================
bad_md5 = [n for n in range(0, 131)
           if P.md5_from_state(b'a' * n) != hashlib.md5(b'a' * n).digest()]
check('hand-written MD5 matches hashlib at every length 0-130', not bad_md5)
bad_sha = [n for n in range(0, 131)
           if P.sha256_from_state(b'a' * n) != hashlib.sha256(b'a' * n).digest()]
check('hand-written SHA-256 matches hashlib at every length 0-130', not bad_sha)
for n in (55, 56, 63, 64, 65, 119, 120):
    check('MD5 correct across the %d-byte boundary' % n,
          P.md5_from_state(b'x' * n) == hashlib.md5(b'x' * n).digest())
    check('SHA-256 correct across the %d-byte boundary' % n,
          P.sha256_from_state(b'x' * n) == hashlib.sha256(b'x' * n).digest())
check('MD5 handles random binary',
      all(P.md5_from_state(v) == hashlib.md5(v).digest()
          for v in [os.urandom(k) for k in (1, 17, 63, 64, 200, 1000)]))
check('SHA-256 handles random binary',
      all(P.sha256_from_state(v) == hashlib.sha256(v).digest()
          for v in [os.urandom(k) for k in (1, 17, 63, 64, 200, 1000)]))
check('an MD5 state must be four words', raises(P.md5_from_state, b'x', [1, 2, 3]))
check('a SHA-256 state must be eight words',
      raises(P.sha256_from_state, b'x', [1, 2, 3]))

# padding is the attacker-computable part
check('MD5 padding brings the total to a block multiple',
      all((n + len(P.md5_padding(n))) % 64 == 0 for n in range(0, 200)))
check('SHA-256 padding brings the total to a block multiple',
      all((n + len(P.sha256_padding(n))) % 64 == 0 for n in range(0, 200)))
check('MD5 padding starts with the 0x80 marker',
      all(P.md5_padding(n)[0] == 0x80 for n in range(0, 200)))
check('MD5 padding encodes the length in bits, little-endian',
      P.md5_padding(10)[-8:] == (80).to_bytes(8, 'little'))
check('SHA-256 padding encodes the length in bits, big-endian',
      P.sha256_padding(10)[-8:] == (80).to_bytes(8, 'big'))
check('negative lengths are refused', raises(P.md5_padding, -1))
check('negative lengths are refused for SHA-256', raises(P.sha256_padding, -1))

# ===========================================================================
# THE FORGERIES, checked against the key holder
# ===========================================================================
for trial in range(8):
    key = os.urandom(8 + trial * 3)
    msg = b'prefix=10.0.0.0/8 nexthop=192.0.2.1' + b'!' * trial
    ext = b' prefix=0.0.0.0/0 nexthop=198.51.100.66'
    legit = hashlib.md5(key + msg).digest()
    forged, glue = P.forge_extension(legit, len(key) + len(msg), ext)
    truth = hashlib.md5(key + msg + glue + ext).digest()
    check('MD5 forgery %d matches what the key holder would compute' % trial,
          forged == truth)
    check('MD5 forgery %d differs from the original digest' % trial,
          forged != legit)
    s_legit = hashlib.sha256(key + msg).digest()
    s_forged, s_glue = P.forge_extension_sha256(s_legit, len(key) + len(msg), ext)
    s_truth = hashlib.sha256(key + msg + s_glue + ext).digest()
    check('SHA-256 forgery %d matches the key holder' % trial,
          s_forged == s_truth)

# the precondition: the attacker must guess the key length
key = os.urandom(16)
msg = b'prefix=10.0.0.0/8'
ext = b' prefix=0.0.0.0/0'
legit = hashlib.md5(key + msg).digest()
right, glue = P.forge_extension(legit, len(key) + len(msg), ext)
truth = hashlib.md5(key + msg + glue + ext).digest()
check('with the right key length the forgery succeeds', right == truth)
for wrong in (8, 12, 15, 17, 24, 32):
    w_forged, w_glue = P.forge_extension(legit, wrong + len(msg), ext)
    w_truth = hashlib.md5(key + msg + w_glue + ext).digest()
    check('with a key length of %d instead of 16 the forgery fails' % wrong,
          w_forged != w_truth)

# HMAC is a different construction and refuses
for h in (hashlib.md5, hashlib.sha256):
    forger = P.forge_extension if h is hashlib.md5 else P.forge_extension_sha256
    hm = hmac.new(key, msg, h).digest()
    f, g = forger(hm, len(key) + len(msg), ext)
    t = hmac.new(key, msg + g + ext, h).digest()
    check('HMAC-%s refuses the extension forgery' % h().name, f != t)
check('a wrong-sized digest is refused', raises(P.forge_extension, b'short', 16, b'x'))
check('a wrong-sized SHA-256 digest is refused',
      raises(P.forge_extension_sha256, b'short', 16, b'x'))

# the demos themselves, several times, so nothing is a lucky draw
for i in range(5):
    d = P.demo_length_extension()
    check('demo forgery %d succeeds' % i, d['forgery_succeeds'] is True)
    check('demo forgery %d leaves HMAC intact' % i,
          d['hmac_forgery_succeeds'] is False)
    check('demo forgery %d never used the key' % i,
          d['key_seen_by_attacker'] is False)
    check('demo forgery %d reports the two digests as equal' % i,
          d['forged_digest'] == d['digest_the_key_holder_would_compute'])
    q = P.demo_sha256_does_not_help()
    check('SHA-256 demo %d still forges' % i, q['forgery_succeeds'] is True)
    check('HMAC-SHA-256 demo %d refuses' % i,
          q['hmac_sha256_forgery_succeeds'] is False)
check('the MD5 self-check passes', P.md5_self_check()['all_match_hashlib'])
check('the SHA-256 self-check passes', P.sha256_self_check()['all_match_hashlib'])
check('the self-checks use several vectors', P.md5_self_check()['vectors'] >= 8)

# ===========================================================================
# A. malleability, and that the edit lands exactly
# ===========================================================================
k, n = os.urandom(32), os.urandom(16)
pt = b'AUTH role=operator limit=00100'
ct = P.ctr_encrypt(k, n, pt)
check('CTR ciphertext is the same length as the plaintext', len(ct) == len(pt))
check('CTR round-trips', P.ctr_decrypt(k, n, ct) == pt)
edited = P.targeted_edit(ct, pt.index(b'operator'), b'operator', b'rootadmn')
out = P.ctr_decrypt(k, n, edited)
check('the targeted edit lands exactly where intended',
      out == b'AUTH role=rootadmn limit=00100')
check('the edit changed only the intended bytes',
      sum(1 for a, b in zip(ct, edited) if a != b)
      == sum(1 for a, b in zip(b'operator', b'rootadmn') if a != b))
check('the edit preserved the length', len(edited) == len(ct))
check('decryption raised no error', isinstance(out, bytes))
check('an edit of a different length is refused',
      raises(P.targeted_edit, ct, 0, b'abc', b'abcd'))
check('an edit past the end is refused',
      raises(P.targeted_edit, ct, len(ct) - 2, b'abcd', b'efgh'))
check('a negative offset is refused', raises(P.targeted_edit, ct, -1, b'a', b'b'))
check('a bad AES key size is refused', raises(P.ctr_encrypt, b'short', n, pt))
check('a bad counter block is refused', raises(P.ctr_encrypt, k, b'short', pt))
for i in range(4):
    m = P.demo_malleable()
    check('malleability demo %d changed the role' % i,
          'rootadmn' in m['attacker_result'])
    check('malleability demo %d changed the limit' % i,
          '99999' in m['attacker_result'])
    check('malleability demo %d used no key' % i,
          m['key_used_by_attacker'] is False)
    check('malleability demo %d kept the length' % i,
          m['ciphertext_length_unchanged'] is True)

# ===========================================================================
# B. AEAD
# ===========================================================================
gk, gn = AESGCM.generate_key(bit_length=256), os.urandom(12)
sealed = P.gcm_seal(gk, gn, pt)
check('AEAD output is longer than the plaintext by a tag', len(sealed) == len(pt) + 16)
check('AEAD round-trips', P.gcm_open(gk, gn, sealed) == pt)
bad = P.targeted_edit(sealed[:len(pt)], 0, pt[:4], b'XXXX') + sealed[len(pt):]
try:
    P.gcm_open(gk, gn, bad); rejected = False
except InvalidTag:
    rejected = True
check('AEAD rejects the edit that CTR accepted', rejected)
try:
    P.gcm_open(gk, os.urandom(12), sealed); wrong_nonce_ok = True
except InvalidTag:
    wrong_nonce_ok = False
check('AEAD rejects a wrong nonce', not wrong_nonce_ok)
try:
    P.gcm_open(gk, gn, sealed, aad=b'different'); aad_ok = True
except InvalidTag:
    aad_ok = False
check('AEAD binds the associated data', not aad_ok)
for i in range(4):
    a = P.demo_aead_correct()
    check('AEAD demo %d detects the tamper' % i, a['tamper_detected'] is True)
    r = P.demo_nonce_reuse()
    check('nonce-reuse demo %d recovers exactly' % i, r['recovery_exact'] is True)
    check('nonce-reuse demo %d used no key' % i, r['key_used_by_attacker'] is False)
    check('nonce-reuse demo %d names what else is lost' % i,
          'authentication' in r['also_lost'])

# and the precondition: DIFFERENT nonces defeat the recovery
k2 = AESGCM.generate_key(bit_length=256)
p1, p2 = b'A' * 40, b'B' * 40
c1 = P.gcm_seal(k2, os.urandom(12), p1)[:40]
c2 = P.gcm_seal(k2, os.urandom(12), p2)[:40]
rec = bytes(a ^ b ^ c for a, b, c in zip(c1, c2, p1))
check('with distinct nonces the XOR recovery fails', rec != p2)
same = os.urandom(12)
c1s = P.gcm_seal(k2, same, p1)[:40]
c2s = P.gcm_seal(k2, same, p2)[:40]
recs = bytes(a ^ b ^ c for a, b, c in zip(c1s, c2s, p1))
check('with a repeated nonce the XOR recovery is exact', recs == p2)

# ===========================================================================
# D. the arithmetic
# ===========================================================================
c256 = P.hash_attack_costs(256)
check('classical preimage is the full width', c256['preimage_classical'] == 256)
check('Grover halves the preimage exponent', close(c256['preimage_grover'], 128))
check('classical collision is already half', close(c256['collision_classical'], 128))
check('the quantum collision exponent is a third', close(c256['collision_bht'], 256 / 3))
check('BHT memory is of the same order as its time',
      close(c256['collision_bht'], c256['bht_memory_exponent']))
check('Grover does NOT halve collision resistance',
      c256['collision_classical'] != c256['collision_bht'] / 1.0
      and c256['collision_classical'] > c256['collision_bht'])
check('collision resistance is already half of preimage, before any quantum',
      close(c256['collision_classical'], c256['preimage_classical'] / 2))
check('so the same halving rule gives two different answers',
      close(c256['preimage_grover'], c256['collision_classical']))
for bits in (128, 256, 384, 512):
    cc = P.hash_attack_costs(bits)
    check('%d-bit costs are internally consistent' % bits,
          cc['preimage_grover'] * 2 == cc['preimage_classical'])
check('a non-byte-aligned size is refused', raises(P.hash_attack_costs, 100))
check('a zero size is refused', raises(P.hash_attack_costs, 0))
check('a negative size is refused', raises(P.hash_attack_costs, -8))

g1 = P.grover_parallel_penalty(256, 1)
check('one machine leaves the plain exponents',
      close(g1['grover_exponent'], 128) and close(g1['classical_exponent'], 256))
for pnum in (2, 2 ** 10, 2 ** 20, 2 ** 40):
    g = P.grover_parallel_penalty(256, pnum)
    check('classical divides by P at %d machines' % pnum,
          close(g['classical_exponent'], 256 - math.log2(pnum)))
    check('Grover divides by sqrt(P) at %d machines' % pnum,
          close(g['grover_exponent'], 128 - math.log2(pnum) / 2))
    check('the advantage equals the remaining Grover exponent at %d' % pnum,
          close(g['advantage_bits'], g['grover_exponent']))
check('the advantage shrinks as machines are added',
      P.grover_parallel_penalty(256, 2 ** 40)['advantage_bits']
      < P.grover_parallel_penalty(256, 1)['advantage_bits'])
check('zero machines is refused', raises(P.grover_parallel_penalty, 256, 0))

# ===========================================================================
# report and CLI
# ===========================================================================
rep = P.build_report()
check('report separates executed from calculated',
      'executed' in rep and 'calculated' in rep)
check('report states its evidence categories',
      'Linux execution' in rep['evidence_categories']['sections_A_B_C'])
check('report says section D executed nothing',
      'Offline calculation' in rep['evidence_categories']['section_D'])
check('report carries caveats', len(rep['caveats']) >= 5)
check('a caveat says a forged authenticator is not a completed attack',
      any('not a completed attack' in c for c in rep['caveats']))
check('a caveat says the key length is assumed',
      any('key LENGTH' in c for c in rep['caveats']))
check('a caveat says SHA-256 does not fix the construction',
      any('fixes nothing about this attack' in c for c in rep['caveats']))
check('a caveat says exponents are not costs',
      any('not a schedule' in c for c in rep['caveats']))
check('a caveat says no device was involved',
      any('no network device' in c.lower() for c in rep['caveats']))
check('report JSON-serialises', isinstance(json.dumps(rep), str))
text = P.report_text(rep)
check('the text names the four sections',
      all(x in text for x in ('A.', 'B.', 'C.', 'D.')))
check('the text shows the forgery succeeding', 'FORGERY SUCCEEDS            True' in text)
check('the text shows HMAC refusing', 'same attack against HMAC    False' in text)
check('the text names the identity in section D', 'identity rather than a coincidence' in text)
check('the text discloses what it does not establish', 'does NOT establish' in text)
check('no report line exceeds eighty characters',
      all(len(x) <= 80 for x in text.splitlines()))

out = subprocess.run([sys.executable, 'primitives.py', '--json'],
                     capture_output=True, text=True)
check('--json exits zero', out.returncode == 0)
check('--json parses', isinstance(json.loads(out.stdout), dict))
plain = subprocess.run([sys.executable, 'primitives.py'],
                       capture_output=True, text=True)
check('plain run exits zero', plain.returncode == 0)
check('plain run is not JSON', not plain.stdout.lstrip().startswith('{'))

print('primitives: %d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: ' + f)
sys.exit(1 if FAILED else 0)
