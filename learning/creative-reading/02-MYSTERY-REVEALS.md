# Network mystery reveals

Keep these away from the first view of each question. They are explanations of supplied fictional evidence, not captured results from the book's laboratory qualification.

## M01 The neighbour nobody could find

With `/24`, the workstation considers the destination on-link and seeks its MAC directly. With the approved `/26`, its subnet is `192.0.2.64/26`, spanning `.64` through `.127`; `.130` is outside it. The default gateway `.66` is inside it. The workstation should send the off-link packet to the gateway's MAC, subject to its routing table.

Correct the host configuration through the normal authority, then check route selection, neighbour resolution and the original application transaction. The repaired mask does not, by itself, prove the downstream policy or return path. **Accept an answer** that identifies the incorrect on-link decision, names the gateway and preserves that final verification.

## M02 The name that arrived early

Both observations can be correct: the authority now has the record while a resolver still holds an unexpired negative answer. The supplied arithmetic is `600 − 180 = 420` seconds. Changing the present positive TTL does not retroactively alter that cached negative answer.

A controlled test can wait for expiry or clear the relevant cache in an authorised test environment. Production cache changes have scope and consequences. Then verify the client's actual name-resolution path and the application transaction, including whatever transport, security and server dependencies that service requires. **Accept** the cached-negative explanation; do not reward an unsupported “DNS is broken” diagnosis.

## M03 The bundle with a favourite chair

Aggregate capacity and single-flow capacity describe different workloads. Under the stated per-flow implementation, that transfer occupies one member and is limited by its path and endpoint conditions. Multiple independent flows can exercise aggregate capacity, but hash collisions and unequal flow sizes can produce imbalance. Four flows are not a mathematical promise of one flow per member.

Choose a test with several independently identified flows, inspect their member placement and compare aggregate throughput with the rest of the path. Do not assume this policy describes every adaptive or packet-spraying implementation. **Accept** the distinction and a measured distribution test; reject “force equal byte counts” as an unexplained repair.

## M04 The neighbours who stayed polite

Ordinary broadcast OSPF does not require every pair of DROthers to reach Full. Their mutual 2-Way state is consistent with the supplied role and adjacency evidence. The sentence is: “These two routers are DROthers, so their mutual 2-Way state is expected here.”

Missing required adjacencies with the DR/BDR, divergent database evidence, missing intended routes or failed forwarding would justify investigation. A role display alone does not establish complete health. **Accept** the normal-state explanation with a meaningful further check; do not reset a healthy adjacency just to improve a status word.

## M05 The route with nowhere to stand

The session has reachability to its peer, but the route needs a usable resolution for its advertised forwarding next hop in the relevant context. The supplied next hop is unresolved. Inspect that lookup and the intended design: IGP reachability, next-hop policy, recursion and context boundaries.

Changing next-hop policy may be appropriate in a particular design; it may also conceal a broken underlay or alter an intended forwarding path. Establish the contract before repairing it. **Accept** an unresolved-next-hop diagnosis conditional on these clues; reject the assumption that Established guarantees every received route enters forwarding.

## M06 The multicast wrong door

The supplied active RPF decision expects the source on B, while the stream arrives on A. Its correlated failure counter and capture identify the failing check in this case. A receiver join establishes interest, not the correctness of the source's incoming path.

Compare the source's actual ingress path with the route and multicast RPF state used by this platform and service. Check why they differ before changing routing or multicast configuration. Other routing-table selection modes exist; do not generalise this toy case to a universal unicast-table rule. **Accept** the path inconsistency and an evidence-based comparison, rather than a receiver reset.

## M07 The last subscriber at the port counter

The inclusive range contains `65535 − 1024 + 1 = 64512` ports. At 64 ports per block, `64512 / 64 = 1008` blocks. All are allocated in the stipulated model. The exhausted resource is a new port-block allocation, not the continued existence of the public address.

Existing flows can continue while new admission fails. Acceptance needs a new subscriber allocation and new-session tests alongside continued service. A real design also needs vendor-specific port exclusions, reservation and mapping rules, headroom and restoration behaviour. **Accept** the inclusive arithmetic and distinction between allocation and existing forwarding.

## M08 The route that stopped at the chip

The supplied evidence places the failure at hardware programming after a resolved control-plane route and an intended request. It does not prove a complete universal SONiC pipeline trace; it identifies this operation's captured resource failure and absent hardware result.

Establish the resource type and actual utilisation, relevant platform/ASIC limits, competing allocations, supported recovery procedure and expected disruption. Retest the affected route and regression cases. Do not manually edit internal databases as an improvised repair. **Accept** the requested-versus-programmed distinction and a scoped resource investigation.

## M09 The margin that left before the ribbon cutting

The specified available budget is `−5 − (−15) = 10 dB`. After 8 dB of loss, 2 dB remains. The required allowance is 3 dB, so this model is short by 1 dB. Today's favourable transmitter reading does not qualify operation at the stated minimum.

Revisit the qualified path, selected optics or requirement through the design process. Do not quietly shrink the allowance or substitute today's launch power. The ribbon can wait for a compliant budget and the other acceptance checks. **Accept** 2 dB remaining and a 1 dB shortfall, with dBm for powers and dB for differences.

## M10 The nameserver with the wrong family papers

Delegation reachability and DNSSEC authentication are separate. The supplied parent DS does not authenticate the new child signing key. Coordinate the parent DS, child DNSKEY/signatures and rollover sequence, including cache lifetimes and the ability to restore a valid chain. The correct sequence depends on the established migration method and current state.

Disabling validation would remove the test's security requirement rather than demonstrate that it was restored. Verify through validating resolvers after the intended state and relevant caches converge. **Accept** the chain mismatch; do not require one universal emergency rollover recipe from these limited clues.

## M11 The five packets that escaped the notebook

Under the explicitly independent model, the probability of no sample is `(999/1000)^5 = 0.995009990005`, about **99.501%**. An empty result is unsurprising. It cannot establish that the exchange never happened.

A suitably scoped packet capture, endpoint transaction record or other appropriate unsampled evidence could answer the specific question, with its own coverage limits. Real sampling may be systematic, flow-based or otherwise correlated; use its actual scheme rather than borrowing this formula. **Accept** the probability and the distinction between lack of observation and absence.

## M12 Four quick repairs and one awkward month

Allowed downtime is `43200 × (1 − 0.9995) = 21.6` minutes. The four outages total 28 minutes. Achieved availability is `(43200 − 28) / 43200 × 100 = 99.935185...%`, below 99.95% under the stated schedule.

The mean restoration time of seven minutes can be accurate while monthly availability misses its target. Frequency, duration, scope, denominator and contractual exclusions all matter. This is a fictional calculation, not interpretation of a real contract. **Accept** the separate metrics and their arithmetic; do not let the attractive mean replace the agreed availability calculation.
