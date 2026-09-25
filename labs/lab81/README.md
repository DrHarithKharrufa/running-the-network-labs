# Lab 81.1 — Allocation arithmetic and the reachability contract

Run with Python 3, standard library only:

```console
python aggregation.py
python -m unittest discover -v
```

This executes prefix arithmetic, a symbolic longest-prefix lookup model and RD
field packing. It does not configure a kernel, send packets, converge a protocol,
measure a FIB or validate a vendor implementation. Its direct-delivery terminal
states assume that a site route reaches its destination; they do not test a service.

Four regions × 16 sites × eight /24s = 512 allocated prefixes in either plan, at
different addresses. The hierarchical allocation reserves one /16 per region and
one /21 per site. The first 16 sites completely fill its first /17: 128 further /24
slots remain in the reserved /16, not inside the occupied /17. Site 17 adds a /21
in the second half; exact cover now needs two prefixes for that region. A /16
advertisement may stay unchanged only under an explicit reachability/discard policy.

Per-region exact prefix covers have four entries in the hierarchical case and 512
in the interleaved case. Combining all interleaved prefixes at a **single usable
common exit** produces one /15. Thus flat assignment does not forbid aggregation.
These counts are not measured routing-table sizes or convergence results.

The separate forwarding example is C → R → A/B. A is 10.0.0/24, B is 10.0.1/24;
C's summary is 10.0.0/23 toward R. R has the reachable /24 routes, a /23 discard
and a default back to C. Longest-prefix lookup gives these outcomes:

| Case | Destination A | Destination B |
| --- | --- | --- |
| Both child routes present | Delivered | Delivered |
| B missing, retain summary while any child exists | Delivered | Discard at R |
| Same, without discard | Delivered | C–R–C loop |
| Withdraw summary unless all children exist | No route | No route |
| No children, advertise unconditionally | Discard | Discard |
| B missing, usable /24 exception through R2 | Delivered through R | Delivered through R2 |

The `any`, `all` and `always` policies are teaching choices, not claims about default
behaviour on a particular NOS. Discarding prevents the shown loop but cannot restore
reachability. The more-specific exception assumes another genuinely usable path.
Real validation must test how the chosen protocol generates and withdraws summaries,
how next hops resolve, alternate paths, packet loss, timers and service behaviour.

The RD examples use documentation ASNs 64496 and 65536 and IPv4 documentation
address 192.0.2.81. They demonstrate encoding, not permission to use those values
in production. Type 0 has a 32-bit local field; types 1 and 2 have a 16-bit local
field. RD types and RT extended-community types are different identifiers. The
worksheet does not encode RTs or validate administrator ownership/reserved ASNs.

## Exercises

1. Change the dimensions within the validated bounds. Explain the exact cover and
   utilisation rather than predicting a fixed route count.
2. Remove B's child route. Compare retained-summary and withdrawn-summary policies;
   identify whose availability each sacrifices.
3. Add the independent R2 exception; explain why the assumption about its path matters.
4. Draw the actual network on which you would advertise a regional /16, including its
   discard route, constituent routes, exceptions, origination and withdrawal rules.
5. Plan a vendor lab for that design. Record its result separately from this model.

## Historical example

`aggregation_original.py.txt` is the byte-preserved incoming lab. For comparison:

```console
python aggregation.py --demo-original
```

Its route-count, universal convergence and contained-churn claims are incorrect.
Its /17s are fully occupied and the inter-region gaps are outside those /17s.
Its flat allocator hard-codes 512 entries, and removing `r*4` does not make all of
the half-filled /16s contiguous. Do not use that historical output as evidence.
