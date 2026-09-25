#!/usr/bin/env python3
"""Lab 51.1 --- four claims about primitives, three of them executed.

WHY THIS LAB EXISTS
-------------------
Chapter 51 named the primitives and said what each is for.  Naming a primitive
is not the same as stating the condition under which it delivers anything, and
four of the chapter's statements were missing the condition:

  "ENCRYPTION PROTECTS CONFIDENTIALITY."  On its own it does not protect
  INTEGRITY, and an unauthenticated stream cipher is not merely readable-if-
  broken --- it is EDITABLE without being broken at all.  Section A takes a
  message the attacker cannot read and changes its meaning to an exact value of
  the attacker's choosing, using no key.

  "AEAD GIVES YOU BOTH AT ONCE."  It does, under a condition the chapter never
  stated: ordinary GCM requires nonce uniqueness under each key. This is not
  a universal description of misuse-resistant AEAD designs.  Section B reuses one and
  recovers a plaintext from a ciphertext, again with no key.  The damage is not
  limited to confidentiality; the notes say what else goes.

  "ROUTING PROTOCOLS USE MD5 AUTHENTICATION."  Several different constructions
  travel under that name and they do not have the same properties.  Section C
  forges a valid authenticator for a message the attacker chose --- adding a
  default route with a hostile next hop --- WITHOUT THE KEY, against the
  construction H(key || message).  Then it does the same thing to HMAC, which
  refuses.  The lesson is about the construction, not about MD5 being old.

  "A QUANTUM COMPUTER HALVES HASH SECURITY."  This is one rule applied to two
  different problems, and it is right about one of them.  Section D is
  arithmetic, and it is the only section here that executes nothing.

WHAT IS EXECUTED AND WHAT IS NOT
--------------------------------
Sections A, B and C are LINUX EXECUTION: real ciphertexts, real digests, real
forgeries, produced by this script on this machine, checked against hashlib and
against the cryptography library.  The forgery in Section C is a genuine forgery
--- it is compared byte for byte with the digest the legitimate holder of the key
would have produced.  Section D is OFFLINE CALCULATION over published
complexities; nothing quantum was run and nothing about future hardware is
predicted.

No network device, routing daemon or vendor implementation was involved.  This
demonstrates a property of a CONSTRUCTION; which construction any given product
uses is a question for that product's documentation, and the chapter says so.

    python3 primitives.py
    python3 primitives.py --json
    python3 test_primitives.py
"""
import argparse
import hashlib
import hmac
import json
import math
import os
import struct
import sys
import textwrap

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag


class PrimitiveError(ValueError):
    """The described demonstration cannot be carried out."""


# ===========================================================================
# A. encryption without authentication
# ===========================================================================
def ctr_encrypt(key, nonce, plaintext):
    """AES in counter mode. Confidentiality only, by construction."""
    if len(key) not in (16, 24, 32):
        raise PrimitiveError('AES key must be 16, 24 or 32 bytes, got %d' % len(key))
    if len(nonce) != 16:
        raise PrimitiveError('this counter block must be 16 bytes, got %d' % len(nonce))
    c = Cipher(algorithms.AES(key), modes.CTR(nonce)).encryptor()
    return c.update(plaintext) + c.finalize()


def ctr_decrypt(key, nonce, ciphertext):
    c = Cipher(algorithms.AES(key), modes.CTR(nonce)).decryptor()
    return c.update(ciphertext) + c.finalize()


def targeted_edit(ciphertext, offset, known_plaintext, desired_plaintext):
    """Change a stream ciphertext so it decrypts to text of the attacker's choice.

    Requires no key. It requires only that the attacker knows, or can guess,
    what the plaintext says at a position --- which for a protocol with a fixed
    format is not a guess at all.
    """
    if len(known_plaintext) != len(desired_plaintext):
        raise PrimitiveError('a stream edit cannot change the length: %d against %d'
                             % (len(known_plaintext), len(desired_plaintext)))
    if offset < 0 or offset + len(known_plaintext) > len(ciphertext):
        raise PrimitiveError('edit runs past the end of the ciphertext')
    out = bytearray(ciphertext)
    for i, (k, d) in enumerate(zip(known_plaintext, desired_plaintext)):
        out[offset + i] ^= k ^ d
    return bytes(out)


def demo_malleable():
    key, nonce = os.urandom(32), os.urandom(16)
    original = b'AUTH role=operator prefix-limit=00100 peer=198.51.100.7'
    ct = ctr_encrypt(key, nonce, original)
    # The attacker knows the format, not the key. Two targeted edits.
    ct2 = targeted_edit(ct, original.index(b'operator'), b'operator', b'rootadmn')
    ct2 = targeted_edit(ct2, original.index(b'00100'), b'00100', b'99999')
    recovered = ctr_decrypt(key, nonce, ct2)
    return {
        'original': original.decode(),
        'attacker_result': recovered.decode(),
        'key_used_by_attacker': False,
        'ciphertext_length_unchanged': len(ct) == len(ct2),
        'bytes_changed': sum(1 for a, b in zip(ct, ct2) if a != b),
        'decrypts_without_error': True,
    }


# ===========================================================================
# B. AEAD, and the condition nobody states
# ===========================================================================
def gcm_seal(key, nonce, plaintext, aad=b''):
    return AESGCM(key).encrypt(nonce, plaintext, aad)


def gcm_open(key, nonce, sealed, aad=b''):
    return AESGCM(key).decrypt(nonce, sealed, aad)


def demo_aead_correct():
    """AEAD used properly: tampering is detected rather than decrypted."""
    key, nonce = AESGCM.generate_key(bit_length=256), os.urandom(12)
    msg = b'AUTH role=operator prefix-limit=00100 peer=198.51.100.7'
    sealed = gcm_seal(key, nonce, msg)
    tampered = targeted_edit(sealed[:len(msg)], msg.index(b'operator'),
                             b'operator', b'rootadmn') + sealed[len(msg):]
    try:
        gcm_open(key, nonce, tampered)
        detected = False
    except InvalidTag:
        detected = True
    return {'tamper_detected': detected,
            'same_edit_that_succeeded_in_section_a': True}


def demo_nonce_reuse():
    """One repeated nonce, and a plaintext falls out of two ciphertexts."""
    key, nonce = AESGCM.generate_key(bit_length=256), os.urandom(12)
    known = b'GET /status HTTP/1.1\r\nHost: router-01.example\r\n\r\n'
    secret = b'PASS admin:Tr0ub4dor&3 enable:H0rseBattery!!\r\n\r\n\r\n'
    if len(known) != len(secret):
        secret = secret[:len(known)].ljust(len(known), b' ')
    c1 = gcm_seal(key, nonce, known)[:len(known)]
    c2 = gcm_seal(key, nonce, secret)[:len(secret)]
    # Same key, same nonce -> same keystream -> the XOR of ciphertexts is the
    # XOR of plaintexts. Knowing one plaintext yields the other exactly.
    recovered = bytes(a ^ b ^ c for a, b, c in zip(c1, c2, known))
    return {
        'nonce_repeated': True,
        'attacker_knew_one_plaintext': known.decode('latin-1'),
        'recovered_the_other': recovered.decode('latin-1'),
        'recovery_exact': recovered == secret,
        'key_used_by_attacker': False,
        'also_lost': 'GCM authentication. A repeated nonce leaks information '
                     'about the authentication subkey, so an adversary who '
                     'collects enough repeats can forge tags as well as read '
                     'traffic.',
    }


# ===========================================================================
# C. the construction, not the hash
# ===========================================================================
_S = [7, 12, 17, 22] * 4 + [5, 9, 14, 20] * 4 + [4, 11, 16, 23] * 4 + \
     [6, 10, 15, 21] * 4
_K = [int(abs(math.sin(i + 1)) * 2 ** 32) & 0xFFFFFFFF for i in range(64)]
_INIT = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476]


def _rotl(x, c):
    x &= 0xFFFFFFFF
    return ((x << c) | (x >> (32 - c))) & 0xFFFFFFFF


def _md5_compress(state, block):
    a, b, c, d = state
    M = struct.unpack('<16I', block)
    A, B, C, D = a, b, c, d
    for i in range(64):
        if i < 16:
            F = (B & C) | (~B & D); g = i
        elif i < 32:
            F = (D & B) | (~D & C); g = (5 * i + 1) % 16
        elif i < 48:
            F = B ^ C ^ D; g = (3 * i + 5) % 16
        else:
            F = C ^ (B | (~D & 0xFFFFFFFF)); g = (7 * i) % 16
        F = (F + A + _K[i] + M[g]) & 0xFFFFFFFF
        A, D, C = D, C, B
        B = (B + _rotl(F, _S[i])) & 0xFFFFFFFF
    return [(a + A) & 0xFFFFFFFF, (b + B) & 0xFFFFFFFF,
            (c + C) & 0xFFFFFFFF, (d + D) & 0xFFFFFFFF]


def md5_padding(message_length_bytes):
    """The padding a Merkle-Damgard hash appends. Attacker-computable."""
    if message_length_bytes < 0:
        raise PrimitiveError('length cannot be negative')
    pad = b'\x80' + b'\x00' * ((55 - message_length_bytes) % 64)
    return pad + struct.pack('<Q', message_length_bytes * 8)


def md5_from_state(data, state=None, prior_length=0):
    """MD5, resumable from a state lifted out of somebody else's digest.

    This is the whole trick. The full MD5 digest used here exposes the chaining state
    after the last block, so publishing the digest publishes the state, and
    anyone can carry on hashing from there.
    """
    st = list(state) if state is not None else list(_INIT)
    if len(st) != 4:
        raise PrimitiveError('an MD5 state is four words, got %d' % len(st))
    msg = data + md5_padding(prior_length + len(data))
    for i in range(0, len(msg), 64):
        st = _md5_compress(st, msg[i:i + 64])
    return struct.pack('<4I', *st)


def forge_extension(digest, original_length, extension):
    """Forge a valid H(key || message || glue || extension) without the key.

    original_length is len(key) + len(message). The attacker knows the message
    and must guess the key length, which is a small search, not a break.
    """
    if len(digest) != 16:
        raise PrimitiveError('expected a 16-byte MD5 digest, got %d' % len(digest))
    state = list(struct.unpack('<4I', digest))
    glue = md5_padding(original_length)
    forged = md5_from_state(extension, state=state,
                            prior_length=original_length + len(glue))
    return forged, glue


def demo_length_extension():
    key = os.urandom(16)                       # the attacker never sees this
    message = b'prefix=10.0.0.0/8 nexthop=192.0.2.1 metric=10'
    legit = hashlib.md5(key + message).digest()          # H(key || message)
    extension = b' prefix=0.0.0.0/0 nexthop=198.51.100.66 metric=1'
    forged, glue = forge_extension(legit, len(key) + len(message), extension)
    # What the holder of the key would compute for the extended message:
    truth = hashlib.md5(key + message + glue + extension).digest()
    # The same attack against HMAC, which is a different construction:
    hmac_legit = hmac.new(key, message, hashlib.md5).digest()
    hmac_forged, hmac_glue = forge_extension(
        hmac_legit, len(key) + len(message), extension)
    hmac_truth = hmac.new(key, message + hmac_glue + extension,
                          hashlib.md5).digest()
    return {
        'construction_attacked': 'H(key || message)',
        'key_length_assumed_by_attacker': len(key),
        'key_seen_by_attacker': False,
        'original_message': message.decode(),
        'appended_by_attacker': extension.decode(),
        'glue_bytes': len(glue),
        'forged_digest': forged.hex(),
        'digest_the_key_holder_would_compute': truth.hex(),
        'forgery_succeeds': forged == truth,
        'hmac_forgery_succeeds': hmac_forged == hmac_truth,
        'note': 'The forged message is not gibberish: it is the original '
                'message, some padding a parser may ignore or reject, and a '
                'default route pointing at the attacker. Whether that parses '
                'is a question about the protocol; whether the authenticator '
                'verifies is settled above.',
    }


# --- the same property, in the hash everyone reaches for instead -----------
_SHA_K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
    0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
    0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
    0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]
_SHA_INIT = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
             0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]


def _rotr(x, c):
    x &= 0xFFFFFFFF
    return ((x >> c) | (x << (32 - c))) & 0xFFFFFFFF


def _sha256_compress(state, block):
    w = list(struct.unpack('>16I', block))
    for i in range(16, 64):
        s0 = _rotr(w[i - 15], 7) ^ _rotr(w[i - 15], 18) ^ (w[i - 15] >> 3)
        s1 = _rotr(w[i - 2], 17) ^ _rotr(w[i - 2], 19) ^ (w[i - 2] >> 10)
        w.append((w[i - 16] + s0 + w[i - 7] + s1) & 0xFFFFFFFF)
    a, b, c, d, e, f, g, h = state
    for i in range(64):
        S1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
        ch = (e & f) ^ (~e & g)
        t1 = (h + S1 + ch + _SHA_K[i] + w[i]) & 0xFFFFFFFF
        S0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
        mj = (a & b) ^ (a & c) ^ (b & c)
        t2 = (S0 + mj) & 0xFFFFFFFF
        h, g, f, e = g, f, e, (d + t1) & 0xFFFFFFFF
        d, c, b, a = c, b, a, (t1 + t2) & 0xFFFFFFFF
    return [(x + y) & 0xFFFFFFFF for x, y in
            zip(state, (a, b, c, d, e, f, g, h))]


def sha256_padding(message_length_bytes):
    """SHA-256 pads the same way MD5 does, big-endian. Attacker-computable."""
    if message_length_bytes < 0:
        raise PrimitiveError('length cannot be negative')
    pad = b'\x80' + b'\x00' * ((55 - message_length_bytes) % 64)
    return pad + struct.pack('>Q', message_length_bytes * 8)


def sha256_from_state(data, state=None, prior_length=0):
    """SHA-256, resumable from a state lifted out of somebody else's digest."""
    st = list(state) if state is not None else list(_SHA_INIT)
    if len(st) != 8:
        raise PrimitiveError('a SHA-256 state is eight words, got %d' % len(st))
    msg = data + sha256_padding(prior_length + len(data))
    for i in range(0, len(msg), 64):
        st = _sha256_compress(st, msg[i:i + 64])
    return struct.pack('>8I', *st)


def forge_extension_sha256(digest, original_length, extension):
    """The same forgery against H(key || message) built on SHA-256."""
    if len(digest) != 32:
        raise PrimitiveError('expected a 32-byte SHA-256 digest, got %d'
                             % len(digest))
    state = list(struct.unpack('>8I', digest))
    glue = sha256_padding(original_length)
    forged = sha256_from_state(extension, state=state,
                               prior_length=original_length + len(glue))
    return forged, glue


def demo_sha256_does_not_help():
    """The upgrade a reader will reach for first, and what it fixes here.

    Nothing for these full-output MD5 and SHA-256 secret-prefix constructions.
    Truncated-output variants and other hash constructions need separate analysis.
    """
    key = os.urandom(20)
    message = b'prefix=10.0.0.0/8 nexthop=192.0.2.1 metric=10'
    legit = hashlib.sha256(key + message).digest()
    extension = b' prefix=0.0.0.0/0 nexthop=198.51.100.66 metric=1'
    forged, glue = forge_extension_sha256(legit, len(key) + len(message),
                                          extension)
    truth = hashlib.sha256(key + message + glue + extension).digest()
    hm = hmac.new(key, message, hashlib.sha256).digest()
    hm_forged, hm_glue = forge_extension_sha256(hm, len(key) + len(message),
                                                extension)
    hm_truth = hmac.new(key, message + hm_glue + extension,
                        hashlib.sha256).digest()
    return {
        'hash': 'SHA-256',
        'construction': 'H(key || message)',
        'forgery_succeeds': forged == truth,
        'hmac_sha256_forgery_succeeds': hm_forged == hm_truth,
        'forged_digest': forged.hex(),
        'digest_the_key_holder_would_compute': truth.hex(),
    }


def sha256_self_check():
    vectors = [b'', b'a', b'abc', b'message digest', b'x' * 55, b'x' * 56,
               b'x' * 64, b'y' * 119, b'z' * 1000]
    return {'vectors': len(vectors),
            'all_match_hashlib': all(
                sha256_from_state(v) == hashlib.sha256(v).digest()
                for v in vectors)}


def md5_self_check():
    """Prove the hand-written MD5 is MD5 before relying on it for a forgery."""
    vectors = [b'', b'a', b'abc', b'message digest',
               b'abcdefghijklmnopqrstuvwxyz', b'x' * 55, b'x' * 56, b'x' * 64,
               b'y' * 119, b'z' * 1000]
    return {'vectors': len(vectors),
            'all_match_hashlib': all(
                md5_from_state(v) == hashlib.md5(v).digest() for v in vectors)}


# ===========================================================================
# D. Grover, and the rule that is right about one thing
# ===========================================================================
def hash_attack_costs(bits):
    """Published complexities for one hash output size. Offline arithmetic.

    Nothing here is a prediction about hardware. These are the exponents the
    algorithms carry; whether any machine ever runs them is a separate
    question this lab does not touch.
    """
    if bits <= 0 or bits % 8:
        raise PrimitiveError('a hash size in whole bytes, got %r bits' % bits)
    return {
        'bits': bits,
        'preimage_classical': bits,
        'preimage_grover': bits / 2.0,
        'collision_classical': bits / 2.0,
        'collision_bht': bits / 3.0,
        'bht_memory_exponent': bits / 3.0,
    }


def grover_parallel_penalty(bits, processors):
    """Grover across P machines costs 2^(n/2)/sqrt(P), not /P.

    This is the part the halving rule hides. Classical search parallelises
    linearly; Grover does not, so the advantage erodes exactly where an
    attacker would spend money.
    """
    if processors < 1:
        raise PrimitiveError('at least one processor, got %r' % processors)
    quantum = bits / 2.0 - math.log2(math.sqrt(processors))
    classical = bits - math.log2(processors)
    return {'processors': processors,
            'grover_exponent': quantum,
            'classical_exponent': classical,
            'advantage_bits': classical - quantum}


def demo_quantum_arithmetic():
    sizes = [hash_attack_costs(n) for n in (128, 256, 384, 512)]
    scaling = [grover_parallel_penalty(256, p) for p in (1, 2 ** 10, 2 ** 20, 2 ** 40)]
    return {'sizes': sizes, 'grover_scaling': scaling}


# ===========================================================================
# report
# ===========================================================================
def build_report():
    return {
        'executed': {
            'malleable': demo_malleable(),
            'aead_correct': demo_aead_correct(),
            'nonce_reuse': demo_nonce_reuse(),
            'md5_self_check': md5_self_check(),
            'sha256_self_check': sha256_self_check(),
            'length_extension': demo_length_extension(),
            'sha256_no_help': demo_sha256_does_not_help(),
        },
        'calculated': demo_quantum_arithmetic(),
        'evidence_categories': {
            'sections_A_B_C': 'Linux execution on this machine. Real keys, real '
                              'ciphertexts, real digests, a real forgery checked '
                              'byte for byte against what the key holder would '
                              'have produced.',
            'section_D': 'Offline calculation over published algorithmic '
                         'complexities. Nothing quantum was run and no claim is '
                         'made about when or whether any machine will run it.',
        },
        'caveats': [
            'This demonstrates properties of CONSTRUCTIONS, not of any vendor '
            'product. Which construction a given implementation uses is a '
            'question for its documentation and its source, and several '
            'different ones travel under the name "MD5 authentication".',
            'The length-extension forgery produces a valid AUTHENTICATOR. '
            'Whether the extended message is then accepted depends on the '
            'protocol parser, the length fields and any replay protection --- '
            'none of which is modelled here. A forged authenticator is a '
            'necessary step, not a completed attack.',
            'The attacker is assumed to know the key LENGTH. In practice that '
            'is a short search over plausible lengths, repeated until one '
            'verifies, and it is not a cryptographic break.',
            'MD5 is used here because it is what the protocols named. The '
            'length-extension property belongs to the Merkle-Damgard '
            'construction and applies equally to SHA-1 and SHA-256; it does '
            'NOT apply to SHA-3 or to HMAC built on any of them. Replacing MD5 '
            'with SHA-256 in an H(key || message) construction fixes nothing '
            'about this attack.',
            'Section D quotes exponents, not costs. It says nothing about qubit '
            'counts, error correction, wall-clock time or money, and a security '
            'level expressed in bits is not a schedule.',
            'Nothing here is an assessment of any deployed network, and no '
            'network device, routing daemon or vendor implementation was '
            'involved.',
        ],
    }


def _wrap(lines, text, indent='  '):
    lines.extend(textwrap.wrap(text, width=74, initial_indent=indent,
                               subsequent_indent=indent))


def report_text(rep):
    L = []
    e = rep['executed']
    L.append('Four claims about primitives, three of them executed (Chapter 51)')
    L.append('Sections A, B and C ran on this machine. Section D is arithmetic.')
    L.append('')
    L.append('A. Encryption alone does not protect what the message SAYS')
    L.append('-' * 74)
    m = e['malleable']
    L.append('  before  %s' % m['original'])
    L.append('  after   %s' % m['attacker_result'])
    L.append('')
    _wrap(L, 'The attacker had no key, changed %d bytes of ciphertext, left the '
             'length identical, and the recipient decrypted it without any '
             'error at all. A stream cipher turns a known plaintext position '
             'into an editable one: flip a bit of ciphertext and the same bit '
             'flips in the plaintext, so knowing the FORMAT is enough to '
             'choose the result exactly.' % m['bytes_changed'])
    L.append('')
    _wrap(L, 'This is why "we encrypt it" answers a question nobody asked when '
             'the risk is forgery. Confidentiality and integrity are separate '
             'properties and one does not imply the other.')
    L.append('')
    L.append('B. AEAD gives you both --- on one condition')
    L.append('-' * 74)
    a = e['aead_correct']
    L.append('  The same edit, against AES-GCM: %s'
             % ('REJECTED' if a['tamper_detected'] else 'ACCEPTED'))
    L.append('')
    n = e['nonce_reuse']
    L.append('  Now repeat a nonce under the same key, twice:')
    L.append('    attacker already knew  %r' % n['attacker_knew_one_plaintext'][:46])
    L.append('    attacker recovered     %r' % n['recovered_the_other'][:46])
    L.append('    recovery exact: %s, key used: %s'
             % (n['recovery_exact'], n['key_used_by_attacker']))
    L.append('')
    _wrap(L, 'Same key and same nonce means the same keystream, so the XOR of '
             'the two ciphertexts is the XOR of the two plaintexts. One known '
             'message hands over the other, exactly, with no key and no '
             'cryptanalysis.')
    L.append('')
    _wrap(L, 'And confidentiality is the first thing to go rather than the '
             'only thing. What else goes: ' + n['also_lost'])
    L.append('')
    _wrap(L, 'This demonstration uses ordinary AES-GCM, whose security requires '
             'nonce uniqueness and the other construction limits. Misuse-resistant '
             'AEAD has different repeat-nonce consequences. This makes nonce '
             'management a design requirement, and makes random nonces a '
             'question about birthday bounds and counters a question about '
             'what happens when a device reboots.')
    L.append('')
    L.append('C. "MD5 authentication" is several constructions, and one forges')
    L.append('-' * 74)
    sc = e['md5_self_check']
    L.append('  Self-check first: hand-written MD5 matches hashlib on %d/%d '
             'vectors: %s'
             % (sc['vectors'], sc['vectors'], sc['all_match_hashlib']))
    L.append('')
    x = e['length_extension']
    L.append('  construction under attack   %s' % x['construction_attacked'])
    L.append('  attacker saw the key        %s' % x['key_seen_by_attacker'])
    L.append('  original message            %s' % x['original_message'])
    L.append('  attacker appended           %s' % x['appended_by_attacker'])
    L.append('  forged authenticator        %s' % x['forged_digest'])
    L.append('  key holder would compute    %s' % x['digest_the_key_holder_would_compute'])
    L.append('  FORGERY SUCCEEDS            %s' % x['forgery_succeeds'])
    L.append('  same attack against HMAC    %s' % x['hmac_forgery_succeeds'])
    L.append('')
    _wrap(L, 'The full MD5 digest here exposes the chaining state '
             'after the last block, so publishing the digest publishes the '
             'state and anyone can carry on hashing from it. The attacker '
             'resumes, appends a default route pointing at themselves, and '
             'produces an authenticator that verifies --- having never held '
             'the key.')
    L.append('')
    _wrap(L, 'HMAC refuses, and not because it is newer: it is a different '
             'construction, hashing twice with two derived keys so that the '
             'published digest is not a resumable state.')
    L.append('')
    L.append('  The upgrade a reader reaches for first, executed rather than '
             'assumed:')
    q = e['sha256_no_help']
    sc2 = e['sha256_self_check']
    L.append('    hand-written SHA-256 matches hashlib on %d/%d vectors: %s'
             % (sc2['vectors'], sc2['vectors'], sc2['all_match_hashlib']))
    L.append('    SHA-256 in H(key || message), forgery succeeds: %s'
             % q['forgery_succeeds'])
    L.append('    HMAC-SHA-256, forgery succeeds:                 %s'
             % q['hmac_sha256_forgery_succeeds'])
    L.append('')
    _wrap(L, 'Swapping MD5 for SHA-256 inside the same construction fixes '
             'NOTHING here. The property belongs to Merkle-Damgard, not to '
             'the hash, and SHA-256 is Merkle-Damgard too. What fixes it is '
             'changing the CONSTRUCTION --- to HMAC, or to a sponge such as '
             'SHA-3 whose digest is not its resumable state.')
    L.append('')
    _wrap(L, 'Which is why "the routing protocol uses MD5 authentication" does '
             'not tell you what you need to know. Ask which construction, and '
             'read the specification rather than the marketing: the answer '
             'varies between protocols and between implementations of the same '
             'protocol.')
    L.append('')
    L.append('D. Quantum computers do not halve hash security, once')
    L.append('-' * 74)
    L.append('%-8s %11s %9s %11s %9s' % ('output', 'preimage', 'w/Grover',
                                         'collision', 'w/BHT'))
    for s in rep['calculated']['sizes']:
        L.append('%-8s %10.0f %9.0f %10.0f %8.0f'
                 % ('%d-bit' % s['bits'], s['preimage_classical'],
                    s['preimage_grover'], s['collision_classical'],
                    s['collision_bht']))
    L.append('  (figures are exponents: 2^n operations)')
    L.append('')
    _wrap(L, 'The halving rule describes the PREIMAGE column and nothing else. '
             'Collision resistance was already n/2 classically, from the '
             'birthday bound, so a 256-bit hash offers 128 bits against '
             'collisions before anyone builds anything. The quantum collision '
             'query model reaches n/3 with substantial storage and coherent-access '
             'requirements. The table is asymptotic query arithmetic, not a '
             'hardware cost prediction or a universal quantum-memory lower bound.')
    L.append('')
    L.append('  And Grover does not parallelise the way money does:')
    L.append('')
    L.append('%14s %12s %12s %10s' % ('machines', 'classical', 'Grover', 'advantage'))
    for g in rep['calculated']['grover_scaling']:
        L.append('%14s %11.1f %12.1f %10.1f'
                 % ('2^%d' % round(math.log2(g['processors'])),
                    g['classical_exponent'], g['grover_exponent'],
                    g['advantage_bits']))
    L.append('  (exponents for a 256-bit preimage search)')
    L.append('')
    _wrap(L, 'Classical search divides by the number of machines; Grover '
             'divides by the SQUARE ROOT of it. So the quantum advantage '
             'shrinks as an attacker scales up, which is exactly the regime a '
             'well-resourced attacker operates in.')
    L.append('')
    _wrap(L, 'The two right-hand columns are identical in every row, and that '
             'is an identity rather than a coincidence: the advantage is '
             '(n - log2 P) - (n/2 - (1/2) log2 P), which simplifies to '
             'n/2 - (1/2) log2 P --- the Grover exponent itself. The quantum '
             'advantage in bits always equals the work Grover still has left '
             'to do, so the two numbers fall together and no amount of '
             'hardware separates them.')
    L.append('')
    _wrap(L, 'The rule of thumb is not so much wrong as applied to three '
             'different questions and correct for one of them.')
    L.append('')
    L.append('What this does NOT establish')
    L.append('-' * 74)
    for c in rep['caveats']:
        L.extend(textwrap.wrap(c, width=74, initial_indent='- ',
                               subsequent_indent='  '))
    return '\n'.join(L)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--json', action='store_true', help='emit the report as JSON')
    a = p.parse_args(argv)
    try:
        rep = build_report()
    except PrimitiveError as exc:
        print('cannot evaluate: %s' % exc, file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=2) if a.json else report_text(rep))
    return 0


if __name__ == '__main__':
    sys.exit(main())
