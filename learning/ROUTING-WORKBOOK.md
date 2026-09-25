# Routing workbook: from a route to an accepted service

Routing revision, 25 September 2026. Seven paper sessions connect Chapters 17–23. Read the chapters in order on a first pass; revisit the matching selected answers after attempting the questions. These sessions extend the learning route from the foundations and campus workbooks. They do not replace lab prerequisites or the wider Appendix G capstone.

**Every observation, address choice and result in this workbook is constructed for teaching. None is a new packet capture, commercial NOS test or measured service acceptance.** Keep predictions and actual observations in separate columns if you later execute a corresponding lab. The small diagrams below omit devices and dependencies deliberately; state the boundary of each model.

You are preparing a fictional branch's routing handover. The service owner wants reliable access to a central order service and shared DNS/NTP. Your first deliverable is an explanation a colleague can inspect; your final deliverable is a proposed acceptance matrix. Use `EVIDENCE-FORM.md` for any real execution. No proprietary image is needed for the paper route.

## Session 1 — The route is there

Read Chapter 17. Assume one VRF, ordinary destination lookup and installed, resolved routes:

| Prefix | Next hop |
| --- | --- |
| 0.0.0.0/0 | 192.0.2.1 |
| 203.0.113.0/24 | 192.0.2.5 |
| 203.0.113.0/26 | 192.0.2.9 |
| 203.0.113.64/26 | 192.0.2.13 |

Predict the next hop for .45, .90 and .200 in 203.0.113.0/24. Then suppose BGP lists a rejected .45/32. Does it change your answer? Draw four boxes: context, installed match, resolved action, observed packet/reply. Beside each box write an observation that can verify it.

**Model reasoning:** .45 uses .9, .90 uses .13, and .200 uses .5. The rejected /32 is absent from the installed lookup. A route display cannot prove the neighbour rewrite, packet egress or reply. If a request is captured at the server but no answer returns, investigate the reply and application as well as the forward routing state. Do not erase a useful counterexample merely because the routing table looks tidy.

**Submit:** the three predictions and one competing-hypothesis table. A reviewer changes .90 to .130; explain why that now uses the /24. For actual practice, Lab 17 needs the environment in its README; these four entries are a separate paper fixture.

## Session 2 — The backup succeeds; the probe must still fail

Read Chapter 18 and the Lab 18 README. In its topology the primary next hop is 192.0.2.2, the backup is 198.51.100.2, and the independent probe is 198.19.0.20/32 sourced from 192.0.2.1. The controller has already reached a healthy baseline. It withdraws the primary service route after two consecutive failed probes and restores it after three successes.

Use this **constructed ordered outcome sequence**: success, failure, failure, failure, success, success, success. Mark primary-service eligibility after each completed sample. Assume no concurrent changes. Explain why sample outcomes do not supply the exact elapsed failover time. Then remove the primary forwarding /32 for the probe while a broader backup route remains. What stops that probe escaping?

**Model reasoning:** starting healthy, the primary remains through the first failure, is withdrawn at the second failure, and stays withdrawn until the third consecutive recovery success. The independent less-preferred /32 discard prevents fallback to a broader route. When the primary /32 is again eligible, it beats that discard. Application replies deliberately use the backup in the lab; probe replies use the primary subnet. There is no stateful firewall or NAT in this model.

For a separate BFD arithmetic check, use Chapter 18's A/B asymmetric settings. The nominal receive detection times are 1,500 ms at A and 300 ms at B. These are neither the controller's timers nor measured application outages.

**Submit:** a state timeline, probe/reply paths and a controller-failure recovery action. For real execution, record fault time, route-change time and first restored transaction separately.

## Session 3 — One map, different roots

Read Chapter 19. Use the simplified undirected triangle A–B = 40, B–C = 40, A–C = 100. From A, list initial candidates, settle the smallest, improve remaining distances and identify the first hop to C. Repeat from B. Next reduce A–C to 60 in both directions and recompute A's result.

**Model reasoning:** A initially sees B at 40 and C at 100; through B, C improves to 80. B reaches A and C directly at 40 each. With A–C at 60, A prefers the direct link. Each router roots its own calculation in the advertised graph. The actual OSPF model includes network vertices and route-type rules beyond this sketch.

A constructed incident report now says “all neighbours Full; one branch lacks a type 5”. List three area-type explanations before proposing a reset. In a stub, the absence is intended; in an NSSA, inspect type 7 and default policy; in a normal area, compare LSA identity, age/scope and flooding evidence, then route eligibility. The ABR's possession of an LSA elsewhere does not prove that this area should contain it.

**Submit:** both calculations and a short next-check plan. For actual Lab 19 work, use the documented fault/recovery procedures and distinguish disruptive process resets from seamless production convergence.

## Session 4 — The cheaper exit is farther away

Read Chapter 20. An L1 router reaches exit A at cost 10 and exit B at 30. The constructed destination 198.18.10.0/24 costs another 100 beyond A and 5 beyond B. First choose with default-only information, then with the stated complete destination costs. Explain which additional advertisement changes the decision.

**Model reasoning:** defaults select A on the visible cost of 10. Destination-specific information gives totals 110 through A and 35 through B, so B wins if eligible. Leak only the intended reachability with correct metrics and feedback prevention; test withdrawal as well as the improved path. If B's specific disappears, state which remaining candidate or default becomes usable.

Translate one loopback into the lab's NET convention and identify area, system ID and NSEL. Then consider a merger where another router has the same input address. A deterministic allocation rule can deterministically produce a duplicate; check the combined inventory before connecting it.

**Submit:** exit arithmetic, leak/withdrawal expectations and an identifier record. For later lab work, keep IPv4 and IPv6 route/overload observations separate. The retained chapter evidence does not fill every metric-mode interoperability cell in exercise 20.4.

## Session 5 — The messenger is not necessarily on the path

Read Chapter 21. Participant P advertises a prefix through a non-forwarding route server RS to border B. B advertises internally, via reflector R, to client I. Assume B applies next-hop-self on the intended internal advertisement and R preserves that next hop. Draw advertisement and packet arrows separately.

**Model reasoning:** advertisements travel P → RS → B → R → I. The ordinary forwarding path from I resolves B's loopback through the underlay, then B resolves P across the exchange. Neither RS nor R is on that packet path merely because it relayed the route. The external next hop at B is P; the internal next hop at I is B. The return path needs its own evidence.

For two otherwise comparable eligible paths, give A LOCAL_PREF 100, AS length 3 and MED 50; give B LOCAL_PREF 100, length 4 and MED 10. Under the chapter's ordering A wins before MED. Raise B's LOCAL_PREF to 200 and B wins; make B's next hop ineligible and that preference no longer rescues it.

**Submit:** both drawings and the three decisions. Add one observation that distinguishes failed TCP establishment from an OPEN rejection when a session repeatedly reports Active. The word “Active” is no reason to close the ticket.

## Session 6 — A valid route can still be unauthorised

Read Chapter 22. Use its synthetic validation record for 203.0.113.0/24, maximum length /25, origin 64501. The import contract initially permits only the exact /24 from the stub customer, with a nonempty path containing only repeated 64501. Assume other eligibility conditions hold.

Predict these inputs before consulting the table's result column:

| Input | Validation / contract distinction | Model result |
| --- | --- | --- |
| /24, path 64501 | Valid and authorised | Accept after sanitisation and fresh provenance |
| Contained /25, path 64501 | Valid but length not authorised by import | Reject |
| Contained /26, path 64501 | Exceeds validation maximum | Reject as Invalid |
| /24, path 64502 64501 | Origin can be Valid; path violates stub contract | Reject |
| /24, path 64501, forged internal tag plus permitted request | Authorised route; untrusted attributes need treatment | Remove forged classification, retain permitted request, assign fresh provenance |

Now permit the intended /25s in the customer prefix filter. Predict the route-set difference and inspect the local export after outbound policy; downstream rejection can hide an incorrect export. Restore the original policy and require the extra export to disappear. Community actions and export eligibility remain independent conditions.

**Submit:** complete accepted attributes and export expectations, plus one negative test for a missing policy. Keep this paper truth table separate from FRR execution and any commercial translation. Exercise 22.1 explains the command-level submission and evidence still needed for actual platforms.

## Session 7 — Accept the shared service

Read Chapter 23. Use CUST-A on 10.101.0.0/24, CUST-B on 10.102.0.0/24, CUST-C on 10.103.0.0/24 and SERVICES on 10.109.0.0/24. The proposed service host is 10.109.0.53. Tenant exports use RTs 64500:1001/1002/1003; SERVICES exports only its authorised local service prefix under 64500:9000 and imports the tenants for replies. Tenants import their own and the service RT.

Write an acceptance matrix covering UDP DNS, TCP DNS and UDP NTP from each tenant, all six directed cross-tenant denials, an unapproved service port, an unexpected exported prefix and a missing service return route. In an isolated later test, record query receipt at the server separately from reply delivery to the client. Include the default-route detour through a service host that can forward packets.

**Model reasoning:** nine basic allowed transaction cases do not cover all denial or failure conditions. Route membership supplies reachability but does not authorise every port. A missing reply route can allow query receipt while preventing a completed transaction. An absent direct tenant route does not exclude a default detour. Add CUST-D and the basic allowed cases become twelve, while directed cross-tenant pairs also become twelve for a different mathematical reason.

**Submit:** the matrix, owners and restoration criteria. Distinguish the book's local Linux VRF/static-route evidence from its unexecuted VPN/MPLS fixture. RT arithmetic on paper does not demonstrate label forwarding.

## Handover and progression

End with a one-page memo: the service obligation, predicted normal and failed paths, policy boundaries, evidence actually obtained, remaining uncertainty, restoration method and the person accepting the next step. Label this workbook's supplied observations as constructed if you include them. A colleague should be able to change one input and understand which conclusion changes.

Use Appendix G's four-part rubric: mechanism/units, evidence/limits, service/recovery reasoning and communication/ownership, each scored 0–2. Aim for at least 6/8, no zero and no unresolved material technical or recovery error. Self-explanation is useful; it is not independent reader testing or production approval. The next study route follows the service: multicast and provider services, data-centre networking or transport, with the appropriate chapter prerequisites.
