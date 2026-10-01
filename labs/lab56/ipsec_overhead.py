#!/usr/bin/env python3
"""Lab 56.2 --- how much room the encapsulation actually costs, computed.

Chapter 56 used to say that encryption overhead "shrinks the usable MTU" and
leave it there, which leaves the reader with a feeling instead of a number. The
number is knowable exactly: it is fixed framing plus a padding rule, and the
padding rule is why the answer is not a single subtraction.

This computes it from the frame formats rather than quoting a figure, and it
searches for the largest inner packet that fits rather than dividing, because
the padding makes the relationship between inner size and total size a step
function: for tunnel-mode ESP with AES-GCM, inner payloads of 1447, 1448, 1449
and 1450 bytes ALL produce a 1504-byte packet. A subtraction that ignores that
gives you an MTU which is right on average and wrong on the packets that matter.

    python3 ipsec_overhead.py
    python3 ipsec_overhead.py --json
    python3 test_ipsec_overhead.py

WHAT THIS IS: offline calculation from published frame formats (RFC 4303 for
ESP, RFC 4106 for AES-GCM in ESP, RFC 3948 for UDP encapsulation, RFC 2784 for
GRE, IEEE 802.1AE for MACsec). It is arithmetic, not a measurement, and it is
not execution. What your platform actually sets the tunnel MTU to is a separate
question that only that platform can answer, and the two disagree more often
than you would like --- which is why the chapter reports a measured figure from
a real device beside this computed one.
"""
import json
import sys

# (name, iv_or_nonce_bytes, icv_bytes, cipher_block_bytes, note)
TRANSFORMS = {
    'aes-gcm-256': (8, 16, 4,
                    'AEAD; RFC4106 explicit nonce is 8 bytes, ICV 16, and the '
                    'ciphertext is padded to a 4-byte boundary'),
    'aes-gcm-128': (8, 16, 4, 'as above; the key length does not change the framing'),
    'chacha20-poly1305': (8, 16, 4, 'AEAD; RFC7634, same 8-byte IV and 16-byte ICV'),
    'aes-cbc-256+hmac-sha1-96': (16, 12, 16,
                                 'CBC needs a full 16-byte IV and pads to the '
                                 '16-byte cipher block; HMAC-SHA-1-96 is truncated to 12'),
    'aes-cbc-256+hmac-sha256-128': (16, 16, 16,
                                    'as above with a 16-byte truncated HMAC-SHA-256'),
}

OUTER_IP = {4: 20, 6: 40}


class OverheadError(ValueError):
    pass


def esp_overhead(inner_len, transform='aes-gcm-256', outer_ip=4,
                 nat_traversal=False, gre=False):
    """Bytes added to an inner IP packet by tunnel-mode ESP.

    outer IP header + optional UDP (NAT-T) + ESP header (SPI 4 + sequence 4)
    + IV/nonce + padding + pad-length 1 + next-header 1 + ICV.
    Optionally a GRE header and its own IP header inside, for GRE-over-IPsec.
    """
    if transform not in TRANSFORMS:
        raise OverheadError('unknown transform %r; known: %s'
                            % (transform, ', '.join(sorted(TRANSFORMS))))
    if outer_ip not in OUTER_IP:
        raise OverheadError('outer_ip must be 4 or 6, not %r' % (outer_ip,))
    if not isinstance(inner_len, int) or isinstance(inner_len, bool) or inner_len < 0:
        raise OverheadError('inner_len must be a non-negative integer, not %r'
                            % (inner_len,))
    iv, icv, block, _ = TRANSFORMS[transform]
    carried = inner_len + (24 if gre else 0)       # GRE 4 + its own IPv4 header 20
    trailer_fixed = 2                              # pad length + next header
    pad = (-(carried + trailer_fixed)) % block
    return (OUTER_IP[outer_ip]
            + (8 if nat_traversal else 0)
            + 8                                    # ESP SPI + sequence number
            + iv + pad + trailer_fixed + icv
            + (24 if gre else 0))


def largest_inner(path_mtu, **kw):
    """The largest inner IP packet that fits, found by search, not division.

    Padding makes total(inner) a step function, so the naive
    path_mtu - overhead(path_mtu) is wrong for several sizes just below the
    step. Search downwards from path_mtu and take the first that fits.
    """
    if not isinstance(path_mtu, int) or isinstance(path_mtu, bool) or path_mtu < 1:
        raise OverheadError('path_mtu must be a positive integer, not %r' % (path_mtu,))
    for n in range(path_mtu, 0, -1):
        if n + esp_overhead(n, **kw) <= path_mtu:
            return n
    return 0


def tcp_mss(inner_mtu, inner_ip=4):
    """The MSS that fits in that inner MTU: minus the IP and TCP headers.

    NOTE WHAT THIS IS FOR. An MSS clamp constrains TCP and nothing else. It is
    a workaround for the segment sizes TCP chooses, not a fix for the path MTU,
    and the same tunnel will still discard an oversized UDP datagram, a QUIC
    packet, or a tunnel carried inside this one.
    """
    return inner_mtu - OUTER_IP[inner_ip] - 20


# MACsec (IEEE 802.1AE) is link-layer and its overhead lands on the Ethernet
# frame, not on the IP packet. Whether it reduces the usable IP MTU depends
# on the permitted frame size and the platform accounting convention.
MACSEC_SECTAG_NO_SCI = 8
MACSEC_SECTAG_WITH_SCI = 16
MACSEC_ICV = 16


def macsec_overhead(include_sci=True):
    return (MACSEC_SECTAG_WITH_SCI if include_sci else MACSEC_SECTAG_NO_SCI) + MACSEC_ICV


def table(path_mtu=1500):
    rows = []
    for name in ('aes-gcm-256', 'chacha20-poly1305', 'aes-cbc-256+hmac-sha1-96',
                 'aes-cbc-256+hmac-sha256-128'):
        for nat in (False, True):
            inner = largest_inner(path_mtu, transform=name, nat_traversal=nat)
            rows.append(dict(transform=name, nat_traversal=nat, inner_mtu=inner,
                             overhead=esp_overhead(inner, transform=name,
                                                   nat_traversal=nat),
                             tcp_mss=tcp_mss(inner)))
    return rows


def step_function_demo(transform='aes-gcm-256', path_mtu=1500):
    """Show the step: several inner sizes that produce an identical total."""
    out = []
    for n in range(path_mtu - 56, path_mtu - 48):
        out.append(dict(inner=n, total=n + esp_overhead(n, transform=transform)))
    return out


def report(out=None, path_mtu=1500):
    out = sys.stdout if out is None else out
    out.write('Lab 56.2 --- tunnel-mode ESP overhead, computed from the frame '
              'formats\n')
    out.write('=' * 72 + '\n\n')
    out.write('Path MTU assumed: %d bytes (the ordinary Ethernet case).\n\n' % path_mtu)
    out.write('  %-30s %-7s %8s %9s %8s\n'
              % ('transform', 'NAT-T', 'overhead', 'inner MTU', 'TCP MSS'))
    for r in table(path_mtu):
        out.write('  %-30s %-7s %8d %9d %8d\n'
                  % (r['transform'], 'yes' if r['nat_traversal'] else 'no',
                     r['overhead'], r['inner_mtu'], r['tcp_mss']))
    out.write('\nWhy this is a search and not a subtraction. ESP pads the '
              'ciphertext to the\ncipher\'s boundary, so several different inner '
              'sizes produce the SAME total:\n\n')
    for d in step_function_demo(path_mtu=path_mtu):
        out.write('    inner %4d  ->  total %4d%s\n'
                  % (d['inner'], d['total'],
                     '   <- the largest that fits' if d['total'] == path_mtu else
                     ('   (too big)' if d['total'] > path_mtu else '')))
    out.write('\nMACsec, for comparison, is link-layer and its cost lands on the\n')
    out.write('Ethernet frame: SecTAG %d bytes with SCI (%d without) plus a %d-byte\n'
              % (MACSEC_SECTAG_WITH_SCI, MACSEC_SECTAG_NO_SCI, MACSEC_ICV))
    out.write('ICV, so %d bytes in the common case. A switch that cannot carry an\n'
              % macsec_overhead(True))
    out.write('oversized frame passes that cost straight on to the IP MTU.\n')
    out.write('\nAn MSS clamp set from the inner MTU protects TCP and only TCP.\n')


def main(argv):
    if '--json' in argv:
        print(json.dumps(dict(table=table(), step=step_function_demo(),
                              macsec_with_sci=macsec_overhead(True),
                              macsec_without_sci=macsec_overhead(False)),
                         indent=1))
        return 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
