# Changelog

Editions of the companion, newest first. A tagged release is frozen; this file
in the repository's current state records what moved between tags. Corrections
made after an edition was printed go in `ERRATA.md`.

## RTN-2026-09-27

Corrections from a second independent reader and publication review.

- `labs/reference-designs/BRANCH-COMPLETE.md` rebuilt. The address plan moves to
  `10.10.64.0/22` and `2001:db8:a1de:300::/56`, from the space Appendix C leaves
  unallocated rather than from London's growth reservation. The IPv6 site prefix
  is now canonical — the previous `2001:db8:a1de:18::/56` had host bits set and
  did not contain its own LANs. The "spare" IPv4 block is genuinely spare; the
  previous one sat inside the guest subnet. Loopbacks move to their own pool.
- `labs/reference-designs/branch-hgt.json` is now the single source for those
  allocations, and `check_addressing.py` validates it and checks the printed
  table still matches.
- The same design gained a requirement exception (R-01a) rather than accepting a
  failure against R-01, a forwarding device for the router-failure fallback,
  a stated voice-continuity mechanism, intra-VLAN isolation and an IPv6 policy
  for the building systems, a failback hold-down, a port map, and a bill of
  materials with quantity, unit price and extended total stated separately.
- `learning/ASSESSING-YOUR-ANSWER.md`: the capacity standard is rebuilt from
  Chapter 67's exercise as printed — six months of delivery time, not four — and
  the added-conditions version is separated out and made internally consistent.
  The architecture decision now rejects its alternative against the requirement
  that actually excludes it. The incident record distinguishes a clock offset
  from an uncertainty bound. Several rubric absolutes are softened to match what
  the book teaches about bounded evidence.
- Lab introductions for 42, 44, 53, 62 and 64 present their flawed comparisons
  as counterexamples rather than as the author's earlier drafts.

## RTN-2026-09-26

First public release. 84 laboratory exercises, 252 Python programs, 35
Containerlab topologies, the execution harness and the eight-session graded
practical route.

Note on the tag: an earlier `RTN-2026-09-26` tag was published, then deleted and
recut against the final build because the page count changed after it was cut
and its recorded PDF hashes no longer matched. If you hold a copy fetched
between those two points, `EDITION.json` will disagree with your PDFs; fetch the
release again. A tag should not be recut, which is why this edition takes a new
identifier instead.
