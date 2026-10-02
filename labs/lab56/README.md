# Lab 56.1 and 56.2 — the tunnel that is "up", and what the encapsulation costs

```bash
python3 tunnel_triage.py            # what the evidence supports
python3 tunnel_triage.py --prove    # exhaustive reachability of every rule
python3 ipsec_overhead.py           # the framing cost, computed
python3 test_tunnel_triage.py
python3 test_ipsec_overhead.py
```

Nothing here re-derives the cryptography. The AEAD constructions, the key
agreements and the forward-secrecy properties are measured for real in lab 51,
which runs genuine handshakes; this lab is about what happens when you wrap a
packet in one of them and put it on a wire.

## Lab 56.1 — the model that refuses to say "healthy"

The version of this lab that shipped took seven booleans, walked a fixed order,
and printed **`tunnel healthy -- traffic should pass`** when none of its four
conditions fired. Read that sentence again with an operator's eye. Nothing in
its input could establish that traffic passes. "Healthy" was simply what it
said when it ran out of faults it knew how to look for, and an operator reads
that as an all-clear.

Three defects, one shape:

| the defect | what it did |
|---|---|
| health from ignorance | no detected fault was reported as a working tunnel |
| unknown collapsed into false | every field was a plain `bool`, so "I did not check" and "I checked and it is absent" were the same value |
| a mitigation read as a cure | `mss_clamped=True` switched the MTU check **off** |

The third is worth dwelling on, because it is the same family as FR-0050 — a
presence test on one field treated as a positive assertion about something
else. An MSS clamp rewrites the MSS option in the TCP three-way handshake. It
does nothing for UDP, nothing for QUIC, nothing for a tunnel carried inside
this one, and nothing for the path MTU itself. A clamped tunnel with a
black-holed path MTU looked perfect to the old model and still broke the DNS,
the video and the VPN-in-a-VPN.

### What the rebuilt model does instead

Every observation is **tri-state**: `True`, `False`, or `'unknown'`, and
`'unknown'` is the default. A rule fires only when every observation it needs is
*known*; otherwise the rule is reported as waiting, together with the command
that would yield the missing observation. There are three output kinds —
`FAULT`, `HYPOTHESIS`, `WARNING` — and **no fourth kind that means "fine"**.

The only positive statement available is the data-path line, and it needs four
things at once: the outbound ESP counter rising, the inbound ESP counter
rising, a TCP application completing, and a non-TCP application completing.
Even then it says *confirmed for what was tested*, because that is all it is.

It also models the states that **cannot** occur — encapsulation without an
outbound SA, decapsulation without an inbound SA, a Child SA with no IKE SA
under IKEv2, a large DF packet crossing a path that a small one cannot. Those
raise, rather than being diagnosed. An observation set that cannot happen means
the observations were misread, and a diagnosis drawn from misread observations
is worse than none.

### The fourth question: can each check ever fire?

`--prove` enumerates every tri-state assignment over the observations the
impossibility constraints couple together (2,187 of them), keeps the 1,224 that
are consistent, and finds a concrete witness for every rule. A rule with no
witness would be dead code pretending to be a control — the trap chapter 53's
union-shadow detector fell into.

## Lab 56.2 — the number the chapter used to leave out

The old chapter said encryption overhead "shrinks the usable MTU" and stopped
there, which leaves the reader with a feeling rather than a figure. The figure
is exactly knowable, and computing it turns up something a subtraction hides:

```
    inner 1444  ->  total 1500   <- the largest that fits
    inner 1445  ->  total 1500   <- the largest that fits
    inner 1446  ->  total 1500   <- the largest that fits
    inner 1447  ->  total 1504   (too big)
    inner 1448  ->  total 1504   (too big)
    inner 1449  ->  total 1504   (too big)
    inner 1450  ->  total 1504   (too big)
```

ESP pads its ciphertext to the cipher's boundary, so the total is a **step
function** of the inner size. `path_mtu - overhead(path_mtu)` is right on
average and wrong for three sizes in every four, which is why this searches
rather than divides.

On an ordinary 1500-byte path, tunnel-mode ESP with AES-GCM leaves an inner
MTU of **1446** and a TCP MSS of **1406**; behind NAT, where ESP is wrapped in
UDP, **1438** and **1398**; GRE-over-IPsec, **1422**. MACsec is a different
kind of cost — it lands on the Ethernet frame, 32 bytes with the SCI — but it
competes for the same 1500.

This is offline calculation from published frame formats (RFC 4303, RFC 4106,
RFC 3948, RFC 2784, IEEE 802.1AE). It is arithmetic, not a measurement. What
your platform actually sets the tunnel MTU to is a separate question that only
that platform can answer, and the chapter reports a measured figure from a real
Cisco IOS router beside this computed one.

## What to take away

- "Up" is a statement about IKE. The Child SAs, their selectors and their
  counters are where traffic lives, and they are separately observable.
- Report what the evidence supports and name the observation that would decide
  the rest. A model that fills in the gaps with assumptions is worse than one
  that admits them.
- Clamping the MSS is a workaround for TCP, not a fix for the MTU. If you
  cannot say what the inner MTU is, you have not fixed anything.
- Absence of a detected fault is not evidence of health, in a lab script or in
  a monitoring dashboard.
