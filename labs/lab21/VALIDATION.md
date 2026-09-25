# Validation record — Lab 21

Review date: 17 September 2026 local time. Run timestamps are UTC.

Core run 20260916T232124Z passed 22 assertions using actual extracted
FRR 10.5.1-1ubuntu4.1 on Ubuntu 26.04 / WSL Linux 6.18.33.2. Eight private
network/mount/UTS namespaces used the lab's addresses and configuration files.
The observed scope comprises: IS-IS loopback transport; 13 full-mesh/external
sessions; all three service prefixes on all five internal routers; customer
requests and return traffic to both transit services; no provider-to-provider
route export; next-hop failure with all sessions Established and recovery;
seven internal reflector sessions plus three external sessions; originator
and cluster state; one RR-session failure and restoration; controlled client/
non-client reflection; restoration; missing-import-policy rejection while
Established; and policy/service recovery.

Selection run 20260916T232253Z records 23 cases in four private namespaces,
with an explicit maximum-paths 1 setting. It records all candidate attributes,
effective receiver configuration, overall best path and kernel next hop.
Every recorded kernel next hop matched that case's overall selected peer.
Two equal-path arrival orders selected the first-arriving peer; router-ID
comparison selected a2 in both orders. Always-compare MED selected a1's
MED 0 in all six three-peer orders. Original equal-path behaviour was restored.

There are eight passing assertions in that run, but one verifies only that
deterministic MED was configured and six complete candidate sets were
recorded. **The grouped decision model did not pass its behavioural expectation.**
Do not describe the assertion total as proof that deterministic MED worked.
With router-ID comparison enabled, the observed overall winners were:

| Arrival order | Default MED | Deterministic MED configured | Always compare MED |
|---|---|---|---|
| a1,a2,b | b | b | a1 |
| a1,b,a2 | a2 | a2 | a1 |
| a2,a1,b | b | b | a1 |
| a2,b,a1 | a1 | a1 | a1 |
| b,a1,a2 | a2 | a2 | a1 |
| b,a2,a1 | a1 | a1 | a1 |

Inputs: a1/a2 AS 64496, MED 0/100, router IDs 10.96.0.3/10.96.0.1; b AS 64497,
MED 50, router ID 10.96.0.2. Other eligibility/early selection inputs were equal.
The grouped model predicts b for all six deterministic-MED cases, while this
build matched it only twice. The effective command and per-AS best markers
were present. This is a recorded implementation discrepancy, not a universal
claim about other FRR releases, commercial NOSs or deterministic MED as a
design concept. No upstream report or fix was submitted as part of the review.

Earlier unsuccessful attempts are retained. They exposed a reset of a
non-existent BGP instance, a collector expecting the wrong JSON summary level,
an unsuitable test NLRI equal to its own underlay next-hop address, and
forwarding multipath obscuring a single-advertisement selection experiment.
The final core run uses distinct test prefixes; the final selection run sets
maximum-paths 1 and distinguishes bestpath.overall from per-AS best markers.
These corrections do not turn failed attempts into passing evidence.

Evidence is under outputs/publication-revision/runtime-evidence/RUN-ID in the
review project: results.json, observations, commands and selection-cases.json
for the selection run. Host configuration, accounts and services were not
modified; no commercial equipment or Containerlab was executed. The Docker
image and deployment/start adapters have static checks only. No IPv6, VPN
family, route-server forwarding, ORR/add-path, confederation, authentication,
scale or hardware-convergence validation is implied.
