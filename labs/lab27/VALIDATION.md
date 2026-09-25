# Lab 27 validation boundary

Run `20260917T013226Z` records **23 passed assertions**, FRR
10.5.1-1ubuntu4.1 and Linux 7.0.0-31-generic, in an isolated QEMU guest.
The namespace adapter executes topology addressing/kernel commands and the
FRR baseline/SR configurations. Policy/steering commands were applied through
the same VTY interfaces; the learner policy file collects those commands.
Containerlab, Docker image build and startup shell adapters remain unexecuted.

Observed:
- LDP/iBGP IPv4 service, four staged SR enablements with sampled delivery,
  LDP removal and SR label 16014 on the ordinary Manchester path.
- Actual label-manager allocation: IS-IS reserves 15000–15999 and
  16000–23999. Binding 30000 is outside allocated chunks; the earlier request
  for binding 15000 failed and that failed run is retained.
- Explicit node-list policy and route-map colour steering send forward
  customer traffic over Birmingham, confirmed by both London uplink captures.
- With Birmingham–Leeds down, the node list still delivers, backtracking
  through London–Manchester. The same path cost is not a delay guarantee.
- A freshly observed unprotected local adjacency SID (15001 in this run)
  forwards in the healthy state but loses service when its link fails.
  The head-end raw-label policy remains **Active**. Replacing it with the
  Leeds node segment recovers service while that link remains down.
- Removing the policy while retaining the route colour preserves ordinary
  SR reachability in this fixture. This is an observation, not an assertion
  of universal fallback semantics. Snapshots preserve the actual route state.
- Steering removal, LDP re-enable followed by SR disable, and bidirectional
  delivery demonstrate an explicit LDP-only rollback of this fixture.

Earlier `20260917T012648Z` has 14 assertions through policy steering;
`20260917T011949Z` retains the rejected binding allocation. Neither replaces
the final fault/recovery run. Counts do not imply test completeness.

No RSVP signalling/reservations, PCEP controller, measured delay/capacity,
timed TI-LFA, IPv6 SR, VPN, ASIC, commercial NOS or Containerlab execution is
implied. Probes sample settled states; they do not establish no transient loss.
The configured MSD is not a measured imposed/forwarded/parsed stack limit.
Raw-label lists are not a dynamic remote-adjacency validity service.

Full evidence lives under publication-revision/runtime-evidence/
20260917T013226Z, including commands, snapshots, results and raw/decoded captures.


## Capture-method follow-up

Run **20260917T025146Z** repeats all 23 assertions successfully with the
filter `icmp or mpls`. The earlier `mpls or icmp` expression can exclude
ordinary IP because the MPLS primitive changes subsequent decoding offsets.
This matters to the Manchester-path absence check, so it was rerun rather
than assumed. The corrected captures again show the steered service on
Birmingham and no tested customer packets on Manchester in that phase.
Node/adjacency failure, restoration and LDP rollback pass again. This does
not broaden the platform, protocol, throughput or timing scope above.
The original run remains preserved. Run identifiers use the guest clock.
See the upstream libpcap pcap-filter documentation for offset semantics.
