# From a failed order to a useful handover

Foundations revision, 25 September 2026. This paper exercise connects Chapters 1–9 before the larger Appendix G capstone. It needs no vendor image and makes no device changes. Every observation below is **constructed teaching data**, not output from a lab run. Keep your own reasoning separate from the supplied observations.

Work in five sessions, stopping when you have a reviewable submission rather than after a fixed number of minutes. Read the corresponding chapters, attempt the task, then use the model discussion at the end. The chapter answer key is `SELECTED-ANSWERS.md`.

## The service and path

This standalone fictional branch has client `10.10.64.20/25`, gateway `10.10.64.1`, resolver `10.10.65.10` and order server `10.10.80.20/24`. The resolver is reached through the gateway. Two routers connect the client and server LANs over an isolated `192.0.2.0/30` teaching link: the branch router uses `.1`, the remote router `.2`, and the server gateway is `10.10.80.1`. This example does not modify Appendix C or assume that documentation addresses make a lab isolated.

The normal packet path has two routers and an ordinary access bridge. Assume Ethernet throughout, no tunnel, NAT, proxy or remarking, and an initial IPv4 TTL of 64 in each direction. Configuration, policy and reachability are requirements to investigate, not facts established by the diagram. The service owner wants a correct order response, not merely a successful ping.

## Session 1: specify the result (Chapters 1–2)

Write one sentence defining the transaction, one proposed success condition and the person who must approve it. Draw both directions and mark the DNS dependency. Make three columns: supplied observation, inference and unknown. Put “the topology diagram shows a path” in the appropriate column without converting it into a claim that the path forwards traffic.

Submit a one-page evidence plan: client, exact flow, observations needed, authorised test scope, recovery and the next person to contact. Identify which work you can do on paper and which work needs execution.

## Session 2: predict the fields (Chapters 3–6)

Calculate the client's network and conventional host range. Decide which neighbour the client needs for the remote server. Use role names for MACs until measured values exist; inventing realistic-looking hexadecimal values adds no evidence.

Draw a table at the client/access link, router-to-router link and remote-router/server link. Predict source and destination MAC roles, source/destination IP and TTL. Repeat for the reply. Calculate the largest ordinary ICMP echo payload if the IPv4 path MTU is 1500 with no IP options. State one thing a successful 64-byte-payload ping would leave untested.

## Session 3: interpret two different failures (Chapters 7–8)

Treat these cards as separate scenarios, not a single incident with a hidden combined cause.

**Card A — a stale negative answer.** The resolver cached an NXDOMAIN response at 11:59:59 for the name `orders.branch.example`. Its initial negative lifetime was 120 seconds. The authoritative data was changed at 12:00:00 to include an A record for `10.10.80.20`. At 12:01:30 this resolver still answers NXDOMAIN with 29 seconds remaining. A query to the correct authority returns the new A record. Assume ordinary TTL-respecting caching, no serve-stale policy and comparable clocks for this arithmetic.

Explain why both answers fit the supplied timeline. Identify what a failed application attempt has and has not tested if it could not resolve the name. Propose a bounded application check that preserves the intended hostname and certificate validation while selecting the intended address. Do not describe that proposal as an executed result.

**Card B — evidence stops at the route lookup.** DNS returns the intended address. A local route query on the client selects gateway `10.10.64.1`, and a neighbour entry exists for that gateway. No packet capture or service response has been supplied.

Write three remaining hypotheses and one discriminating observation for each. Explain why the route query does not prove a packet crossed either router. Distinguish a missing observation from an observed absence at a verified capture point.

## Session 4: order events and govern a change (Chapters 7 and 9)

A firewall event is timestamped 12:00:00.100 with an estimated error of ±40 ms. A server event is timestamped 12:00:00.130 with ±20 ms. Calculate both possible UTC intervals and their overlap. Decide whether the timestamps alone establish event order.

Now propose a harmless lab interface-description change on one platform. Record whether its ordinary CLI applies immediately or uses a candidate. Write the pre-change value, proposed difference, application check, recovery and separate persistence check. If a timed trial is available, explain what to do when its deadline approaches with an acceptance check still inconclusive. Do not invent a universal confirmation command or timer unit.

## Session 5: hand over an unresolved incident

Write five lines: affected service and users; bounded observations and time; current explanation and alternatives; next discriminating test; and named owner/next update. State what would make the next operator abandon your preferred explanation. An unresolved but well-bounded handover can be better engineering evidence than a confident diagnosis unsupported by the cards.

## Model discussion — consult after your attempt

The client's network is `10.10.64.0/25`, broadcast `.127`, and conventional host range `.1–.126`. The server is outside that network. Under the supplied default-path assumption, the next-hop MAC is the branch gateway's, not the remote server's.

| Forward observation | Source MAC role | Destination MAC role | IPv4 source → destination | TTL |
| --- | --- | --- | --- | --- |
| Client/access | Client | Branch gateway | 10.10.64.20 → 10.10.80.20 | 64 |
| Between routers | Branch transit | Remote transit | Same | 63 |
| Remote router/server | Remote LAN | Server | Same | 62 |

The bridge does not decrement IP TTL. For a reply starting at 64, the roles reverse: server to remote gateway at 64, remote transit to branch transit at 63, and branch gateway to client at 62. Required return routes and policy still need proof. With the stated headers, ICMP payload allowance is `1500 − 20 − 8 = 1472` bytes. A small ping does not establish the large-packet boundary, application success, all ECMP paths or recovery.

Card A has elapsed cache age 91 seconds and 29 seconds left. Updating authority does not retrospectively edit that cache entry. A failure before name resolution completes need not send any application connection to the new server. A controlled hostname-preserving address override, as explained in Chapter 7, can investigate the later connection separately; it does not prove that normal DNS access works. Do not clear a shared production resolver merely to produce a cleaner teaching example.

For Card B, useful alternatives include gateway forwarding/policy failure, a missing or denied return path, and a stopped or rejecting server listener. Use matching counters and bounded captures at the relevant boundary, inspect the server and correlate a real transaction. A route lookup is a prediction using supplied routing inputs. Neighbour state indicates a mapping with its recorded state and age; it is not an end-to-end service test.

The firewall interval is `.060–.140` seconds and the server interval `.110–.150`; their overlap is 30 ms. Either order is compatible with those bounds. A shared transaction identifier and protocol causality can add evidence; merely sorting timestamps cannot.

A change plan should state the actual workflow, its original value and the condition for restoring it. If the trial deadline arrives without sufficient acceptance evidence, follow the rehearsed recovery procedure instead of confirming on hope. Verify the resulting state: expiry is an expected mechanism until observed. Persistence and user service require their own checks.

Use the Appendix G rubric: mechanism/units, evidence/limits, service/recovery reasoning and communication/ownership, each 0–2. Aim for at least 6/8, no zero and no unresolved material technical or recovery error. This is a teaching threshold, not a professional certification. For another attempt change one input: use a `/26` client mask with a different host address, an IPv6 outer tunnel budget, a shorter cache lifetime or a failed recovery path. Recalculate the affected conclusion and keep the original attempt.
