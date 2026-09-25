# Lab 34 validation — 17 September 2026

## Executed Linux fixture

Run `20260917T101942Z`, retained under publication-revision/runtime-evidence:
15/15 assertions passed. WSL Ubuntu 26.04, Linux 6.18.33.2-microsoft-standard-WSL2,
FRR 10.5.1-1ubuntu4.1 with its RPKI module, private extracted dependencies,
four owned network namespaces and a loopback-only synthetic RTRv1 server.
No public repository, signed ROA or certificate chain was validated.

Evidence retains exact topology/configs/RTR code, runner/adapters, commands,
pre-policy received routes, cache records/connections, accepted tables, kernel
route lookups and distinct HTTP responses. Confirmed observations:

- Two Valid baseline announcements and legitimate HTTP.
- Wrong-origin `64502` and forged `64502 64501` candidates actually received
  before policy; strict maximum length rejects both and preserves service.
- Broad maximum 32 makes the forged `/25` Valid and sends HTTP to the neighbour.
- A matching broad VRP still wins with conflicting more-specific and strict VRPs.
- Exact restoration and explicit refresh recover legitimate service.
- Invalid `/25` at local preference 10 still diverts HTTP despite the `/24` at 200.
- Restoring Invalid rejection restores legitimate forwarding.
- Missing victim VRP permits Not-found attack under the broad candidate filter;
  the exact independent prefix contract blocks it while legitimate Not-found works.
- Original VRPs restore Valid state. A three-second cache outage retains acquired
  data and service; restart shows actual RTR reconnection and legitimate forwarding.

The runner waits for exact cache-record content before explicit soft-in. This
does not test automatic policy revalidation. Previous Lab 22 observations found
transitions needing explicit refresh; that discrepancy remains relevant.
Initial run `20260917T101735Z` passed 13 checks, but lacked explicit pre-policy
candidate assertions and exact cache-content waiting. It is retained; the
15-check run is the stronger evidence. Neither is a full conformance suite.

## Offline execution

37 parser/coverage/arithmetic checks passed in model-evidence/lab34-20260917T102358Z.
A CLI run against the saved forged-path FRR table reports three Valid paths
under the broad synthetic set. The first test attempt exposed numeric float
1.5 being reinterpreted as asdot; input types were corrected before the retained
pass. AS_SET/confederation text remains deliberately unsupported, not silently
approximated. This model does not compute router policy or cryptographic validity.

## Unexecuted scope

Docker build, start.sh/load-config.py container startup and Containerlab deployment;
commercial NOS; dual caches, full cache expiry/empty startup in this fixture;
IPv6 RTR/forwarding; hostile/malformed RTR protocol cases; automatic revalidation;
signed public RPKI validation; Internet route propagation and hardware scale/timing.
The offline model does include IPv6 prefix arithmetic. The RTR fixture is IPv4 only.
The container image tag is not a reproducibility pin; record the resolved digest
and package versions when building. No host package repair or service installation
was performed for the recorded Linux runs.
