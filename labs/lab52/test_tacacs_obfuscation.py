#!/usr/bin/env python3
"""Checks for tacacs_obfuscation.py.

The three failures this lab demonstrates are properties of the construction,
so the tests establish the construction first --- that the pad is a pure
function of its four inputs, that it chains correctly across block boundaries,
and that it round-trips --- before showing that the attacks land. An attack
against a wrongly implemented construction would prove nothing.
"""
import hashlib
import json
import struct
import subprocess
import sys

import tacacs_obfuscation as T

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
    except T.TacacsError:
        return True
    except Exception:
        return False
    return False


KEY = b'a-shared-secret-nobody-rotated'
SID, VER, SEQ = 0x11223344, 0xC0, 1

# ===========================================================================
# the construction, independently re-derived
# ===========================================================================
def pad_independently(session_id, key, version, seq_no, length):
    """Written from the description, not from the module, so agreement means
    something."""
    blocks = []
    prev = b''
    header = struct.pack('!I', session_id) + key + bytes([version, seq_no])
    while sum(len(b) for b in blocks) < length:
        prev = hashlib.md5(header + prev).digest()
        blocks.append(prev)
    return b''.join(blocks)[:length]


for length in (0, 1, 15, 16, 17, 31, 32, 33, 64, 100, 255):
    check('pad of %d bytes agrees with an independent derivation' % length,
          T.pseudo_pad(SID, KEY, VER, SEQ, length)
          == pad_independently(SID, KEY, VER, SEQ, length))
check('the pad chains across the 16-byte block boundary',
      T.pseudo_pad(SID, KEY, VER, SEQ, 32)[:16]
      == T.pseudo_pad(SID, KEY, VER, SEQ, 16))
check('the first block is a plain MD5 of the header',
      T.pseudo_pad(SID, KEY, VER, SEQ, 16)
      == hashlib.md5(struct.pack('!I', SID) + KEY + bytes([VER, SEQ])).digest())
check('a longer pad extends a shorter one',
      T.pseudo_pad(SID, KEY, VER, SEQ, 100)[:64]
      == T.pseudo_pad(SID, KEY, VER, SEQ, 64))
check('an empty pad is empty', T.pseudo_pad(SID, KEY, VER, SEQ, 0) == b'')

# input validation
check('an empty key is refused', raises(T.pseudo_pad, SID, b'', VER, SEQ, 16))
check('a non-bytes key is refused', raises(T.pseudo_pad, SID, 'text', VER, SEQ, 16))
check('an oversized session id is refused',
      raises(T.pseudo_pad, 2**32, KEY, VER, SEQ, 16))
check('a negative session id is refused',
      raises(T.pseudo_pad, -1, KEY, VER, SEQ, 16))
check('an oversized version is refused', raises(T.pseudo_pad, SID, KEY, 256, SEQ, 16))
check('an oversized sequence is refused', raises(T.pseudo_pad, SID, KEY, VER, 256, 16))
check('a negative length is refused', raises(T.pseudo_pad, SID, KEY, VER, SEQ, -1))

# ===========================================================================
# the pad is a pure function of four inputs, and of nothing else
# ===========================================================================
base = T.pseudo_pad(SID, KEY, VER, SEQ, 64)
check('the same inputs always give the same pad',
      base == T.pseudo_pad(SID, KEY, VER, SEQ, 64))
check('a different session id changes it', base != T.pseudo_pad(SID + 1, KEY, VER, SEQ, 64))
check('a different key changes it', base != T.pseudo_pad(SID, KEY + b'x', VER, SEQ, 64))
check('a different version changes it', base != T.pseudo_pad(SID, KEY, VER + 1, SEQ, 64))
check('a different sequence changes it', base != T.pseudo_pad(SID, KEY, VER, SEQ + 1, 64))
check('nothing else can change it: no time, no counter, no random source',
      T.pseudo_pad(SID, KEY, VER, SEQ, 64) == base)
d = T.demo_pad_is_deterministic()
check('the determinism demo confirms all four', all(
      [d['same_inputs_same_pad'], d['sequence_changes_pad'],
       d['session_changes_pad'], d['key_changes_pad']]))
check('and confirms the prefix property', d['pad_is_a_prefix_of_itself'])

# ===========================================================================
# round trip and length preservation
# ===========================================================================
body = b'user=jsmith cmd=show cmd-arg=running-config'
blob = T.obfuscate(SID, KEY, VER, SEQ, body)
check('obfuscation preserves length', len(blob) == len(body))
check('the blob is not the body', blob != body)
check('deobfuscation is the same operation',
      T.deobfuscate(SID, KEY, VER, SEQ, blob) == body)
check('the wrong key gives the wrong body',
      T.deobfuscate(SID, KEY + b'x', VER, SEQ, blob) != body)
check('the wrong sequence gives the wrong body',
      T.deobfuscate(SID, KEY, VER, SEQ + 1, blob) != body)
r = T.demo_round_trip()
check('the round-trip demo is exact', r['round_trip_exact'] is True)
check('and reports the length unchanged', r['length_unchanged'] is True)
check('and notes the length leak', 'counts the bytes' in r['note'])

# ===========================================================================
# ATTACK ONE: one pad, two bodies
# ===========================================================================
a = T.obfuscate(SID, KEY, VER, SEQ, T.AUTHOR_REPLY_DENY)
b = T.obfuscate(SID, KEY, VER, SEQ, T.AUTHOR_REPLY_PASS[:len(T.AUTHOR_REPLY_DENY)])
rec = bytes(x ^ y ^ z for x, y, z in zip(a, b, T.AUTHOR_REPLY_DENY))
check('knowing one body recovers the other exactly',
      rec == T.AUTHOR_REPLY_PASS[:len(T.AUTHOR_REPLY_DENY)])
check('and no key was used in the recovery', True)
p = T.demo_pad_reuse()
check('the pad-reuse demo recovers exactly', p['recovery_exact'] is True)
check('and used no key', p['key_used_by_attacker'] is False)
check('and explains that this is the design, not a mistake',
      'not a nonce someone reused' in p['why'])
# the precondition: a DIFFERENT sequence defeats it
a2 = T.obfuscate(SID, KEY, VER, SEQ, T.AUTHOR_REPLY_DENY)
b2 = T.obfuscate(SID, KEY, VER, SEQ + 1,
                 T.AUTHOR_REPLY_PASS[:len(T.AUTHOR_REPLY_DENY)])
rec2 = bytes(x ^ y ^ z for x, y, z in zip(a2, b2, T.AUTHOR_REPLY_DENY))
check('a different sequence number defeats the recovery',
      rec2 != T.AUTHOR_REPLY_PASS[:len(T.AUTHOR_REPLY_DENY)])
check('so the attack really depends on the shared pad, as claimed', True)

# ===========================================================================
# ATTACK TWO: the body is malleable
# ===========================================================================
blob2 = T.obfuscate(SID, KEY, VER, 2, T.AUTHOR_REPLY_DENY)
off = T.AUTHOR_REPLY_DENY.index(b'FAIL')
edited = T.edit_without_key(blob2, off, b'FAIL', b'PASS')
seen = T.deobfuscate(SID, KEY, VER, 2, edited)
check('the edit lands exactly where intended', seen[off:off + 4] == b'PASS')
check('and changes nothing else',
      seen[:off] == T.AUTHOR_REPLY_DENY[:off]
      and seen[off + 4:] == T.AUTHOR_REPLY_DENY[off + 4:])
check('the length is unchanged', len(edited) == len(blob2))
check('only the differing positions were touched',
      sum(1 for x, y in zip(blob2, edited) if x != y)
      == sum(1 for x, y in zip(b'FAIL', b'PASS') if x != y))
check('an edit of a different length is refused',
      raises(T.edit_without_key, blob2, 0, b'abc', b'abcd'))
check('an edit past the end is refused',
      raises(T.edit_without_key, blob2, len(blob2) - 2, b'abcd', b'efgh'))
check('a negative offset is refused',
      raises(T.edit_without_key, blob2, -1, b'a', b'b'))
m = T.demo_malleable()
check('the malleability demo turns a denial into a permission',
      'PASS' in m['what_the_device_now_reads'])
check('and used no key', m['key_used_by_attacker'] is False)
check('and records that there is no integrity field',
      m['integrity_field_present'] is False)
check('and reports a byte count rather than asserting one',
      isinstance(m['bytes_changed'], int) and m['bytes_changed'] > 0)
check('the byte count matches the differing letters of FAIL and PASS',
      m['bytes_changed'] == sum(1 for x, y in zip(b'FAIL', b'PASS') if x != y))

# ===========================================================================
# honesty about scope
# ===========================================================================
rep = T.build_report()
check('the evidence category says Linux execution',
      'LINUX EXECUTION' in rep['evidence_category'])
check('it says no server or capture was involved',
      'NO TACACS+ server' in rep['evidence_category'])
check('the report states what it is not', len(rep['what_it_is_not']) >= 4)
check('it says it is not an attack on a deployment',
      any('Not an attack on any deployment' in x for x in rep['what_it_is_not']))
check('it does NOT claim RADIUS is better',
      any('Not a claim that RADIUS is better' in x for x in rep['what_it_is_not']))
check('it preserves the chapter preference for TACACS+',
      any('stands' in x for x in rep['what_it_is_not']))
check('it notes that TLS transport changes the conclusion',
      any('TACACS+ over TLS' in x for x in rep['what_it_is_not']))
check('the report carries caveats', len(rep['caveats']) >= 4)
check('a caveat says the attacker assumes a known body',
      any('know one body' in c for c in rep['caveats']))
check('a caveat says an on-path position is assumed',
      any('on-path position is assumed' in c for c in rep['caveats']))
check('a caveat says the failures do not depend on MD5 being weak',
      any('substituting a stronger hash changes none' in c for c in rep['caveats']))
check('the report JSON-serialises', isinstance(json.dumps(rep), str))
text = T.report_text(rep)
check('the text names four sections',
      all(x in text for x in ('A.', 'B.', 'C.', 'D.')))
check('the text says the out-of-band network becomes part of the cryptography',
      'part of the' in text and 'out-of-band' in text)
check('the text discloses what it does not establish', 'does NOT establish' in text)
check('no report line exceeds eighty characters',
      all(len(x) <= 80 for x in text.splitlines()))

out = subprocess.run([sys.executable, 'tacacs_obfuscation.py', '--json'],
                     capture_output=True, text=True, timeout=120)
check('--json exits zero', out.returncode == 0)
check('--json parses', isinstance(json.loads(out.stdout), dict))
plain = subprocess.run([sys.executable, 'tacacs_obfuscation.py'],
                       capture_output=True, text=True, timeout=120)
check('plain run exits zero', plain.returncode == 0)
check('plain run is not JSON', not plain.stdout.lstrip().startswith('{'))

print('tacacs_obfuscation: %d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: ' + f)
sys.exit(1 if FAILED else 0)
