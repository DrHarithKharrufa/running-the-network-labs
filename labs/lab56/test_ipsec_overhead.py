#!/usr/bin/env python3
"""Tests for ipsec_overhead.py.

The arithmetic is checked against the frame formats field by field, and the
step function --- the reason this is a search and not a subtraction --- is
checked explicitly, because a naive implementation passes every other test here
and is wrong for three sizes out of every four.

    python3 test_ipsec_overhead.py
"""
import sys

import ipsec_overhead as io_

CHECKS = 0
FAILED = []


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
    except io_.OverheadError as exc:
        if fragment and fragment not in str(exc):
            FAILED.append('%s (message lacked %r)' % (label, fragment))
        return
    except Exception as exc:                                     # noqa: BLE001
        FAILED.append('%s (raised %s)' % (label, type(exc).__name__))
        return
    FAILED.append('%s (did not raise)' % label)


# -- 1. The overhead, field by field ----------------------------------------

# AES-GCM, inner length 1446: 1448 is a multiple of 4, so no padding at all.
# 20 outer IP + 8 ESP header + 8 nonce + 0 pad + 2 trailer + 16 ICV = 54.
ok(io_.esp_overhead(1446) == 54, 'AES-GCM tunnel-mode overhead is 54 with no padding')
ok(io_.esp_overhead(1446, nat_traversal=True) == 62,
   'UDP encapsulation for NAT traversal adds exactly 8')
ok(io_.esp_overhead(1446, outer_ip=6) == 74, 'an IPv6 outer header adds 20 more')
ok(io_.esp_overhead(1446, gre=True) == 54 + 24,
   'GRE-over-IPsec adds a GRE header and its own IPv4 header: 24')

# Padding: the ciphertext must reach a 4-byte boundary for AES-GCM.
for inner, pad in ((1446, 0), (1447, 3), (1448, 2), (1449, 1), (1450, 0)):
    ok(io_.esp_overhead(inner) == 54 + pad,
       'inner %d pads by %d' % (inner, pad))
# ... and a 16-byte boundary for CBC.
for inner in range(100, 116):
    total = inner + io_.esp_overhead(inner, transform='aes-cbc-256+hmac-sha1-96')
    ciphertext = total - 20 - 8 - 16 - 12      # minus outer IP, ESP hdr, IV, ICV
    ok(ciphertext % 16 == 0,
       'CBC pads inner %d to a whole 16-byte block (got %d)' % (inner, ciphertext))


# -- 2. The step function, which is the whole point -------------------------

totals = {n: n + io_.esp_overhead(n) for n in range(1443, 1452)}
ok(totals[1444] == totals[1445] == totals[1446] == 1500,
   'THREE different inner sizes all produce exactly 1500 --- this is why the '
   'answer is a search and not a subtraction')
ok(totals[1447] == totals[1448] == totals[1449] == totals[1450] == 1504,
   'and the next four all produce 1504')
ok(io_.largest_inner(1500) == 1446, 'the largest inner packet that fits is 1446')
# The naive subtraction gives a different, wrong answer for this transform.
naive = 1500 - io_.esp_overhead(1500)
ok(naive != io_.largest_inner(1500),
   'the naive path_mtu - overhead(path_mtu) gives %d, not 1446 --- the test that '
   'a wrong implementation fails' % naive)
# Whatever largest_inner returns must actually fit, and one more must not.
for mtu in (576, 1280, 1492, 1500, 1520, 9000):
    for kw in ({}, {'nat_traversal': True}, {'gre': True},
               {'transform': 'aes-cbc-256+hmac-sha1-96'}):
        n = io_.largest_inner(mtu, **kw)
        ok(n + io_.esp_overhead(n, **kw) <= mtu,
           'largest_inner(%d, %s) = %d fits' % (mtu, kw, n))
        ok(n + 1 + io_.esp_overhead(n + 1, **kw) > mtu,
           'and one byte more does not')


# -- 3. The published figures the chapter quotes ----------------------------

ok(io_.largest_inner(1500) == 1446, '1500-byte path, AES-GCM: inner MTU 1446')
ok(io_.tcp_mss(1446) == 1406, 'which leaves a TCP MSS of 1406')
ok(io_.largest_inner(1500, nat_traversal=True) == 1438,
   'behind NAT the inner MTU is 1438')
ok(io_.tcp_mss(1438) == 1398, 'and the MSS 1398')
ok(io_.largest_inner(1500, gre=True) == 1422,
   'GRE-over-IPsec on a 1500-byte path leaves 1422')
ok(io_.macsec_overhead(True) == 32, 'MACsec with SCI costs 32 bytes per frame')
ok(io_.macsec_overhead(False) == 24,
   'and 24 without it --- the SecTAG loses its 8-byte SCI, the 16-byte ICV stays')
ok(io_.tcp_mss(1446, inner_ip=6) == 1386, 'an IPv6 inner packet loses 20 more')


# -- 4. It refuses what it cannot compute ------------------------------------

raises(lambda: io_.esp_overhead(1400, transform='des'), 'an unknown transform is refused',
       'unknown transform')
raises(lambda: io_.esp_overhead(1400, outer_ip=5), 'a bad IP version is refused')
raises(lambda: io_.esp_overhead(-1), 'a negative inner length is refused')
raises(lambda: io_.esp_overhead(1.5), 'a non-integer length is refused')
raises(lambda: io_.esp_overhead(True), 'a bool is not an integer here')
raises(lambda: io_.largest_inner(0), 'a zero path MTU is refused')
raises(lambda: io_.largest_inner('1500'), 'a string path MTU is refused')

# Every declared transform is usable and produces a sane figure.
for name in io_.TRANSFORMS:
    n = io_.largest_inner(1500, transform=name)
    ok(1300 < n < 1500, '%s yields a plausible inner MTU (%d)' % (name, n))
    ok(io_.TRANSFORMS[name][3], '%s carries a note explaining its framing' % name)

# AEAD and CBC must not accidentally agree: if they did, the padding rule would
# be doing nothing and the whole point of the search would be untested.
ok(io_.largest_inner(1500, transform='aes-gcm-256')
   != io_.largest_inner(1500, transform='aes-cbc-256+hmac-sha1-96'),
   'the AEAD and CBC answers differ, so the block size is actually applied')

ok(io_.main([]) == 0, 'the module runs')
ok(io_.main(['--json']) == 0, 'the JSON form runs')

print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
