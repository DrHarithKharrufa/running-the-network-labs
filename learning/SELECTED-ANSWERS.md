# Guidance for all 500 chapter exercises

Complete teaching revision, 25 September 2026. These worked answers cover every numbered end-of-chapter exercise in Chapters 1–87. The historical filename SELECTED-ANSWERS.md is retained so existing links continue to work. Attempt each exercise before consulting its answer. START-HERE.md maps the route workbooks, including transport, security/operations, modern automation and design/leadership.

Chapter and exercise numbers identify the questions across print and digital pagination. Worked inputs are teaching assumptions unless explicitly identified as measurements. Open design questions can have several good answers. Assess the mechanism, evidence, recovery and decision, not agreement with a preferred vendor. Practical answers describe methods and acceptance criteria; they do not supply results a learner may claim to have observed. Keep actual records in EVIDENCE-FORM.md, including failed attempts.

## Chapter 1 — Why this book exists

### 1.1 — Choose a route through the book

One defensible beginner route is Chapters 1–9, campus operation in 10–15, then routing in 16–22 before the provider-service material. For an L3VPN chapter, explain ordinary route selection, next-hop reachability and the separation of customer routing contexts before interpreting labels and VPN routes. For a campus service, begin with frame forwarding, VLAN membership, addressing and a return path. The prerequisite follows the service chosen; there is no prize for listing the most chapters.

State one thing you can already demonstrate and one thing you still need to practise. Use Appendix G's entry check and first milestone to test that judgement. A reader can study operations alongside the first lab rather than postpone recovery habits until after advanced routing.

### 1.2 — A one-page service evidence plan

For a fictional branch order service, name the branch users, the application owner and the person accepting the complete service. Draw the client, access network, gateway, WAN, security boundary and server; draw the reply separately. Mark unresolved DNS, identity, time and shared-path dependencies. Put an assumed recovery target beside the diagram and label it as a requirement awaiting owner agreement, not as a measured capability.

A useful plan contains the exact transaction to test, its success condition, client location, observation points, test authority and restoration method. One unverified assumption might be that both WAN circuits use separate last-mile ducts. Request supplier route evidence; two circuit numbers do not resolve that uncertainty. Submit the diagram and plan even when the uncertainty remains, with a named next action.

### 1.3 — Predict, falsify and recover

In an isolated three-router lab, propose changing one route to a known alternate next hop. Predict both the selected route and a successful bounded service probe after the change. A falsifying observation is that the selected next hop changes but the controlled transaction still fails; this contradicts the claim that this route change alone restores the service. Check the return path and policy before adding another change.

Record the original route and the exact inverse operation. Define a rollback trigger such as loss of the previously working management path, unexpected reachability, or failure of the agreed service check by the decision deadline. A negative test can also verify that an explicitly prohibited destination remains unreachable. It must be authorised and bounded, not a destructive test on an unrelated service. Route state, service success and policy isolation are separate evidence.

## Subject within Chapter 1 — Industry and career

### 1.4 — Responsibility from order to incident closure

The following is a model allocation for a fictional business VPN. Actual job titles and authority must be agreed locally.

| Stage | Accountable role | Work and handover evidence |
| --- | --- | --- |
| Requirements and promise | Service owner | Users, sites, service boundary, targets and commercial assumptions; sales records the agreed order. |
| Design | Design authority | Addressing, routing, security, capacity, shared risks and acceptance plan; customer and supplier interfaces are explicit. |
| Delivery | Delivery owner | Engineering configuration, supplier completion records, approved changes and recovery procedure. |
| Acceptance | Service owner | End-to-end results and exceptions; operations confirms that monitoring, support and recovery information are usable. |
| Incident restoration | Incident commander within delegated authority | NOC triage and timeline; engineering, security, supplier and application teams carry named actions. |
| Closure and improvement | Service owner | Restored service verified with users, remaining actions assigned and the incident record retained. |

One person can hold several roles, but a supplier's circuit handover must not silently become acceptance of the whole VPN. Preserve independent review when the change's risk requires it.

### 1.5 — Compare recovery paths, not equipment counts

Use the chapter's four-hour office target and fifteen-minute transaction-site target as stated exercise assumptions. For a central spare, add detection, decision, travel, installation, boot, configuration and service validation. An hour of travel alone excludes that remedy as the sole means of meeting the fifteen-minute target.

For a standby or second active path, examine detection, state availability, surviving capacity, switching behaviour and transaction recovery. Identify shared power, building, duct, chassis and control dependencies. Assign an available person or automated procedure to each necessary action. Compare full costs over one stated period, including standby testing and support. A proposal passes only if the relevant failure case fits the target with credible evidence; neither a fast protocol timer nor the word “redundant” measures the complete restoration time.

### 1.6 — A portfolio that shows judgement

Use a small, sanitised lab example: requirement, topology and version record; a proposed route change; the actual diff; timestamped baseline, fault and recovery observations; and a conclusion. Keep a prediction that failed. For example, an unchanged transaction after a route correction may lead you to discover an independent return-path fault.

Explain the competence demonstrated: interpreting routing evidence, controlling a change, recovering and revising a hypothesis. Also explain what it does not demonstrate: production authority, another NOS release, line-rate hardware behaviour or every possible fault. If you have not run the experiment, submit a test plan under that name. Do not create a polished success transcript to fill a portfolio gap.

## Chapter 2 — Building the lab

### 2.1 — Baseline, fault and recovery

Record the environment, versions, node/interface names and addresses before testing the two-node topology. Inspect the relevant interfaces and route selection. Use an explicitly identified probe source and a bounded number of probes. Establish a successful baseline; predict the consequence of the chapter's isolated fault; apply it; record the failed exchange and relevant state; restore the exact changed state; repeat the original probe.

Keep commands, timestamps, exit status and output together. A successful ping supports reachability for that source, destination, protocol and interval. It does not establish application performance, arbitrary packet size or hardware forwarding. If the wrapper cannot run, report the environmental failure and a plan; do not turn the book's retained Linux results into your own Containerlab results.

### 2.2 — The missing return route

With r1 sending towards r3 across r2, trace both the request and its reply. Before removing r3's return route, check for alternate/default routes and identify the actual source address. In the specified isolated topology, removing its only return route prevents the round trip even though the forward path and the r2–r3 link remain available. Capture or inspect state at both ends to distinguish a request that never arrived from a reply that could not return.

Restore precisely the removed route and repeat the baseline. A plausible packet narrative without observations earns credit for the prediction, not for execution. If an unexpected default route keeps the test working, investigate that result instead of deleting additional routes until the screenshot matches an expectation.

### 2.3 — A lab is a model

Make a table with feature, image/version, platform, configuration accepted, operational state observed, traffic tested and remaining limitation. A virtual image can support bounded protocol or configuration observations while differing from a physical system's interfaces, ASIC pipeline, scale and timing. For example, a claim about physical queue buffer behaviour at line rate needs an appropriate physical platform and load measurement; successful virtual CLI parsing cannot answer it. Identify that gap and the environment needed to close it.

## Chapter 3 — Signals, cables and optics

### 3.1 — A 220-metre 25 Gb/s link

Two candidates are a supported extended-reach multimode pair on a qualified installed channel, or a 25GBASE-LR pair on single-mode fibre. Cisco's cited examples distinguish their reach and required FEC:

| Example part | Published reach at 25G | Relevant condition |
| --- | --- | --- |
| SFP-25G-SR-S | 70 m OM3 / 100 m OM4 | RS-FEC; insufficient for 220 m. |
| SFP-10/25G-CSR-S | Up to 300 m OM3 / 400 m OM4 | Full reach needs RS-FEC and suitable fibre quality. |
| SFP-10/25G-LR-S | 10 km on G.652 SMF | RS-FEC at 25G. |

The average-power screening differences are 2.7 dB for CSR at 25G, `−6 − (−8.7)`, and 6.3 dB for LR, `−7 − (−13.3)`. These are not blanket channel approvals: check separate loss limits, receiver overload, fibre bandwidth, connectors and both hosts' support. [Cisco 25GBASE SFP28 data sheet, Tables 2–4 and module notes](https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/transceiver-modules/datasheet-c78-736950.pdf), checked 25 September 2026.

For a stated illustrative SMF loss allowance, `0.220 km × 0.35 dB/km + 2 × 0.5 dB` is 1.077 dB before splices and design allowance. Those are assumed plant inputs, not a measured link. Obtain installed-channel evidence and current quotations. Compare two optics, host support, fibre work, testing, spares, power and the cost of later recabling over a declared period. No priced winner follows from the supplied information.

### 3.2 — A receiver reading above the LR limit

The stated reading of +1.2 dBm is 0.7 dB above the chapter's +0.5 dBm LR receiver maximum and its listed transmitter maximum. In an ordinary passive link, unexplained receive power above the expected maximum launch is a reason to check the premise: exact part, wavelength, meter mode/calibration, measurement point and any active optical equipment. It is not a reason to select an attenuator by guesswork.

If the actual supported design requires attenuation, calculate both strongest-transmitter/minimum-loss overload and weakest-transmitter/maximum-loss sensitivity cases, including uncertainty. Verify the changed link in both directions. The difference of 0.7 dB identifies a discrepancy; it is not automatically the attenuator rating to buy.

### 3.3 — Forty kilometres with an ER label

Fibre loss is `40 × 0.25 = 10 dB`; connectors add `6 × 0.5 = 3 dB`; splices add `4 × 0.1 = 0.4 dB`. Passive loss is therefore 13.4 dB and the requirement with the 3 dB allowance is **16.4 dB**. The stated ER average-power screening budget is `−4.7 − (−15.8) = 11.1 dB`, a 5.3 dB shortfall against that requirement. Even before the allowance, estimated passive loss exceeds this screen by 2.3 dB.

Do not approve the design from the reach suffix. Review the actual channel, optical constraints and alternative supported parts or architectures, then measure the installed plant. Reducing an allowance on paper does not recover missing optical power. The question's assumptions are sufficient to reject this screening result, not to choose a complete replacement design.

### 3.4 — PoE demand and surviving capacity

The endpoints require `36 × 45 = 1,620 W` at the PDs. A 740 W budget at the PSE cannot supply even that total, before channel loss. The chapter's class-based reservation is 60 W per port, totalling **2,160 W at the PSE**. Do not substitute observed idle draw for the required allocation.

Under the supplied quotations, five-year purchase plus support is A `7,200 + 5 × 360 = 9,000`, B `8,400 + 5 × 420 = 10,500`, and C `9,600 + 5 × 480 = 12,000` fictional currency units. A is lowest in this deliberately limited comparison. Each option's stated surviving allocation covers its assigned PDs, with no extra reserve beyond that model. Test startup, PSU/feed failure, cooling and UPS assumptions before acceptance. A complete switch failure has a different effect from loss of one supply.

For reduced-power operation, establish which AP functions and coverage would be lost, then obtain service-owner acceptance and a supported power mode. Include licences, power conversion, rack space, cabling, maintenance and installation in a real quotation comparison; the exercise does not supply all of those costs.

### 3.5 — Change the worksheet, not just its conclusion

Fibre remains `8 × 0.35 = 2.8 dB`. The two connector pairs now contribute `2 × 0.75 = 1.5 dB`, and eight splices contribute `8 × 0.1 = 0.8 dB`. Total estimated loss is **5.1 dB**, leaving `6.2 − 5.1 = 1.1 dB` above the stated sensitivity screen. It no longer has the original 2.0 dB allowance; if 2.0 dB is required, it misses by 0.9 dB.

Arithmetic does not certify fibre type, connector condition, minimum-loss overload, reflectance, reach, error performance or recovery. Keep the assumptions beside the result and specify the missing measurements.

## Chapter 4 — Ethernet and the local network

### 4.1 — The destination moved, but who told the bridge?

Immediately after B moves from port 2 to port 3, the old eligible FDB entry may still direct A's unicast frames towards port 2. A frame sourced by B on port 3 can update the dynamic source-learning entry, subject to policy; later frames for B can then use port 3. The bridge does not learn B's location merely by receiving A's frames destined for B.

If B's entry ages out first, unknown-unicast handling can flood A's frames to eligible ports 2 and 3, excluding ingress port 1 and blocked port 4. Ageing removes stale knowledge; it does not discover the new port. Static entries, sticky security or movement controls can change this behaviour, so name the forwarding context and inspect the actual policy.

### 4.2 — VXLAN with IPv6 outside and a tag inside

Count from the inner IP packet to the outer IP packet: 40 bytes outer IPv6 base header, 8 UDP, 8 VXLAN, 14 inner Ethernet header and 4 inner VLAN tag. Total overhead is **74 bytes**, so `9000 − 74 = 8926` bytes remain for inner IP. The inner FCS is not carried by VXLAN. Outer Ethernet and its FCS are outside the stated outer IP MTU.

An outer IPv6 extension header or another encapsulation would reduce the result. State the same boundary when configuring and testing the transport; a vendor's “frame size 9000” may describe another boundary.

### 4.3 — Echo payload at a known IPv4 path MTU

With a 20-byte IPv4 header and an 8-byte ICMP echo header, `1500 − 20 − 8 = 1472` bytes remain for the echo payload. IPv4 options consume more space. A small successful probe only demonstrates that its own size traversed its selected path under the tested conditions.

To investigate the boundary, use an authorised lab, prohibit IPv4 fragmentation, record exact sizes, source, direction and route, and preserve returned ICMP information. Probe loss alone can also reflect filtering or congestion; it does not identify the bottleneck interface. Test restoration and other required paths after any correction.

### 4.4 — Turn a counter into a rate and a question

Record device, interface, direction, counter definition, start/end timestamps, counter values, reset marker, relevant traffic count and the failed flow. For synthetic readings of 200 and 260 over 30 seconds, the increment is 60 and the average is **2 events/s**. If, and only if, these 60 events represent distinct erroneous received frames in the same 30,000-frame receive population, the observed fraction is `60/30,000 = 0.2%`. An aggregate event counter without that definition cannot support the percentage.

Hypothesis A is current receive corruption; test whether error deltas coincide with the failing traffic and compare the far-end transmit/channel evidence. No increment during a properly observed failing exchange weakens that explanation. Hypothesis B is an egress queue bottleneck; inspect its occupancy/drop observations and offered load. A different actual path or a reset invalidates the proposed comparison. Preserve the original counters before clearing them.

## Chapter 5 — IP and subnetting

### 5.1 — Work the /26 by hand

The mask is `255.255.255.192`; six address bits remain, giving 64 addresses per block. In the last octet, 77 is `01001101`; masking with `11000000` gives 64. Thus `192.0.2.77/26` belongs to `192.0.2.64/26`, with broadcast `.127` and conventional host range `.65–.126` (62 hosts).

For a separate check, Python's standard library can calculate `ipaddress.ip_interface('192.0.2.77/26').network`. Distinguish that interface input from `ip_network(..., strict=True)`, which deliberately rejects host bits in a proposed network declaration. Verification should explain the result, not merely reproduce the same hand calculation as code.

### 5.2 — Reserved space is not an expanded LAN

The chapter's two /22s, two /23s and four /24s consume `2×1024 + 2×512 + 4×256 = 4096` addresses: one /20. Their boundaries must still be aligned and disjoint. The wireless endpoint demand grows from 950 to 1,045 at 10%, already beyond a conventional /22's 1,022 host addresses before other reservations.

A larger site allocation does not change that LAN's mask. A workable answer identifies available adjacent space or a new segment, the resulting client/DHCP and routing changes, reservations, ACLs, monitoring, migration and rollback. Do not simply write “use the reserve” while retaining the overfull /22.

### 5.3 — Allocate the supplied sparse graph

Use `labs/lab06/sparse-graph.json` as the input. It has 12 routers and 16 edges, not a full mesh. Allocate the 16 /31s from `10.254.0.0/27` in edge order: `10.254.0.0/31`, `.2/31`, `.4/31`, through `.30/31`. The supplied edge list, including the ring and four chords, determines which pair receives each block. Assign the two addresses consistently to the edge's first and second endpoint.

One valid loopback scheme gives r01 through r12 `10.255.0.0/32` through `10.255.0.11/32`. A /32 host route does not use the conventional LAN network/broadcast subtraction. For the four management sites, 20 hosts plus one reserved address fit in a /27's 30 conventional host addresses. Use `10.253.0.0/27`, `.32/27`, `.64/27` and `.96/27`, retaining the rest of the /24 unallocated.

Check unique ownership, alignment, containment, overlap and host capacity. This is a valid address allocation under the supplied assumptions; it does not prove the topology's service resilience or a router's support for an intended interface mode.

### 5.4 — Observe IPv6 configuration

For each Lab 6.1 segment, preserve the router advertisement, DHCPv6 exchanges where present, client addresses, default route and effective resolver state. Record which prefix and advertisement flags permitted SLAAC, what DHCPv6 supplied, and whether DNS came from RDNSS, DHCPv6 or another configured source.

The RA managed flag does not by itself disable SLAAC; prefix information and client behaviour matter. In this lab's normal IPv6 host model the default-router information comes from RA, not from a DHCPv6 address lease. A received DNS option also does not establish that the application's resolver used it. If the userspace resolver integration is unavailable, record that limitation and leave that part of the execution result unproved.

## Chapter 6 — The transport layer

### 6.1 — Bandwidth–delay product

`400,000,000 bit/s × 0.045 s = 18,000,000 bits = 2,250,000 bytes`. This is about 2.146 MiB. It describes the data volume corresponding to that rate and round-trip time; it is not a guarantee of throughput or a universal socket-buffer setting.

Check measured RTT, receiver window, congestion window, loss/retransmission, the application's supply/consumption rate and the actual bottleneck. Account for negotiated window scaling and units. A receive window below the needed in-flight volume is one possible limit, but a large configured buffer does not prove that the effective window or congestion control permits the target rate.

### 6.2 — A large transfer stalls

Three useful competing hypotheses are: a path-MTU problem, receiver/application back-pressure, and loss or congestion. For MTU, compare small and appropriately constructed larger probes with the relevant fragmentation behaviour, inspect error signalling and capture on both sides of the suspected boundary. For back-pressure, correlate advertised-window behaviour and application/socket observations. For congestion/loss, correlate retransmissions and timing with the path's load and queue/drop evidence.

Choose tests that separate explanations. A small successful ping does not disprove a PMTU black hole. A retransmission does not by itself identify a congested router. DNS or application timeout evidence may justify a different hypothesis; preserve what the experiment actually distinguishes.

### 6.3 — Eight streams outperform one

That observation alone does not prove that the single stream was receiver-window limited. Multiple flows can have separate congestion-control states, use different ECMP paths or change the application's work distribution. Compare per-flow windows, RTTs, retransmissions, destinations and path/load observations, and hold the application and total offered workload sufficiently consistent. Report the competing explanations that remain.

### 6.4 — Controlled impairment

Keep a clean baseline, apply the specified impairment in the isolated environment, start a fresh connection, preserve the direction and scope of the impairment, then remove it and repeat the baseline. Adding 80 ms to one egress direction normally adds approximately 80 ms to a round trip crossing it once; adding 80 ms to each direction adds approximately 160 ms. Queueing, processing and measurement variation are additional effects.

Repeat enough trials to show variation and retain both endpoints' observations. Restoring the configuration is not the same as demonstrating restored performance. If a pre-existing connection retains learned state, explain why its result may differ from the fresh-connection experiment.

## Chapter 7 — Network services

### 7.1 — Core ping succeeds; the client transaction fails

| Hypothesis | Least disruptive next observation | What it can distinguish |
| --- | --- | --- |
| The 02:00 change altered DNS answers or resolver selection | Compare the recorded change, client's chosen resolver, A/AAAA response, TTL and a working client | Wrong/stale name data versus a failure after resolving the intended address |
| The client lacks usable addressing or a return path | Inspect its lease/address, mask, selected route, neighbour state and the corresponding return route | A client-path problem that a core-originated ping does not exercise |
| Authentication, authorisation or clock checks fail | Correlate the client's exact error and transaction ID with identity/server records and measured time state | An explicit denial or validity failure versus service unreachability |
| Policy or the application listener fails on the actual flow | Inspect matching policy counters and server/listener records; use an approved application probe with the correct hostname | Failure of the application port or transaction despite ICMP reachability |

Timestamp the observations and change one variable at a time. Do not disable certificate checking to make the service appear healthy. These are testable alternatives, not a probability ranking. A core ping uses another source and may follow another policy and path.

### 7.2 — A record exists, but the negative answer survives

The initial negative lifetime is `min(600, 120) = 120 seconds`. Suppose the cache acquired the negative answer at 11:59:59, the record was created at 12:00:00 and it is queried at 12:01:30. Its ordinary remaining lifetime is **29 seconds**, so an old negative response is compatible with these inputs. Creation time alone does not tell you when that cache acquired its answer.

NXDOMAIN indicates nonexistence of the name; NODATA means the requested type is absent for an existing name. In the basic RFC 2308 model their cache keys differ: the latter includes query type. An old missing AAAA answer can therefore coexist with a valid A answer. Inspect the actual question, response code, SOA and remaining TTL, and compare the relevant authority. [RFC 2308, §§3–5](https://www.rfc-editor.org/rfc/rfc2308.html).

### 7.3 — Four PoPs and a partition

One defensible starting design gives clients two explicitly identified recursive resolvers in separate failure domains and tests how those clients fail over. Place capacity and reachable service within each partition that must remain operational. If using anycast, withdraw an advertisement when the agreed client-level health fails, and test established TCP/TLS/HTTPS sessions as well as new lookups. A resolver process running is insufficient if its required upstream or validation path is broken.

For time, use multiple individually identifiable, authenticated sources where supported, with documented upstream independence. Four servers fed by the same reference, power supply or WAN are not four independent clocks. Define acceptable offset/uncertainty and the client's holdover limit from the protected applications. During a partition, identify which sources remain reachable and what policy applies if their quality cannot be established.

Include power, routing, ACLs, name resolution, credentials, monitoring and recovery access in the dependency map. Test from each PoP and relevant client population; record capacity with one domain lost. The exercise supplies no populations or tolerances, so it does not determine a final server count or universal topology.

### 7.4 — AAA: four different failures

| Case | Controlled stimulus | Expected policy decision and evidence |
| --- | --- | --- |
| Timeout | Make the selected lab server unavailable with emergency access retained | Observe the documented method-list timeout and any explicitly authorised fallback; retain client/device and server-side evidence. |
| Rejection | Submit known-invalid lab credentials to a reachable server | Reject access under the intended policy; show the server's explicit response and that fallback did not silently bypass it. |
| Denied command | Authenticate a restricted test account, then request a prohibited harmless lab action | Deny that action while retaining the allowed-session evidence; record authorisation response and device outcome. |
| Accounting failure | Interrupt the accounting destination while other AAA components remain available | Verify the chosen continue/block/buffer policy and detectable loss or backlog; authentication success does not settle this case. |

Establish the positive baseline and recovery for every row. Declare the intended policy before the test and reconcile it with the exact implementation. Record environment, timestamps, request/session IDs and sanitised outputs, never credentials. An unavailable authorisation server requires its own row if the platform treats it differently from authentication timeout.

### 7.5 — Ten minutes without collector storage

Use a bounded synthetic source that numbers emitted events and records them locally before sending. Retain source identity, sequence, source timestamp, collector arrival time and durable storage state before, during and after the outage. Observe sender/receiver queue sizes, drop counters, reconnects, backpressure and restart markers. Do not infer durability from a TCP acknowledgement alone.

After recovery, compare the emitted sequence set with durably stored events. Missing numbers indicate loss within the observed test; repeated source/sequence pairs identify duplicates if the IDs are stable across restart. Compare sequence order separately from timestamp or arrival order. Account for the source itself stopping, wrapping or losing its local evidence. A quiet collector and an empty disk cannot establish how many events should have arrived. The test does not prove that every unrelated production source has identical buffering semantics.

## Chapter 8 — Following the packet

### 8.1 — Match one flow at four links

First write the prediction: PC/access and access/London carry the PC source and London-gateway destination MAC with TTL 64; London/Reading carries the transit MAC pair with TTL 63; Reading/server carries Reading-LAN and server MACs with TTL 62. The trunk adds VLAN 110 under the stated path. IPv4 source/destination remain the PC and server; routed TTL changes require corresponding IP header-checksum changes.

Then replace role names with actual observed MACs and record the capture point and direction. Match the same flow and TCP segment using addresses, ports, sequence information and payload context where appropriate; timestamps alone can be ambiguous. NIC offload can make a host capture show unfinished checksums or coalesced segments, and VLAN offload can hide tags. Ethernet FCS is often absent from captures. A discrepancy is a reason to establish the capture boundary, not to fabricate the expected row. The reverse path is a separate prediction and observation.

### 8.2 — Two hosts cannot talk locally

Four useful hypotheses are: an incorrect host mask/route, different VLAN membership, deliberate port isolation, and host firewall filtering. Inspect the selected route and neighbour attempt at each host for the first; inspect ingress VLAN, allowed membership and FDB context for the second; inspect isolation policy and its scope for the third; compare endpoint capture and matching host-policy counters for the fourth.

Use a bounded probe and identify whether a request left A, reached B and caused a reply. “Internet works” neither places the hosts in one broadcast domain nor demonstrates an allowed local service. If the hosts actually belong to different subnets, investigate routed policy and return paths instead of forcing the shared-subnet model. More than one fault can coexist.

### 8.3 — A translated tuple is not a person

Record protocol, inside and outside source address/port, destination address/port, translation-device identity, routing or tenant context, mapping lifetime and timestamp uncertainty. Include additional translation stages when present. Join those records to the address-allocation interval and to an authenticated device/session record using compatible times and identifiers. Ports can be reused; a public source address without port, protocol and time is generally insufficient to identify one mapping.

Distinguish a NAT association, an assigned address, an authenticated session and a human action. A shared machine, proxy or application account can break the last inference. Preserve clock-error bounds and ambiguous joins instead of selecting a convenient identity. Handle actual attribution under the organisation's authorised evidence and privacy procedures; the exercise does not establish a person's responsibility.

### 8.4 — Two circuits, both directions and both session ages

Use rows for normal operation, circuit A failed, A restored, circuit B failed and B restored. In every row, observe a connection established before the transition and a new connection started afterwards, in each required client/server direction. Record the five-tuple, selected paths, relevant translation/session state, response correctness, delay/loss and recovery time. A flow can use different paths in the two directions; draw them.

Check the actual platform's state-sharing rules, reverse-path filtering, directional ACLs, MTU and surviving capacity. Keep offered load and acceptance thresholds stated before the test. Stop or recover if an agreed service or management limit is crossed. The matrix is a proposed acceptance plan: no two-circuit test results are supplied by this answer or by the single-path Lab 9.1.

## Chapter 9 — Living on the command line

### 9.1 — Compare the evidence, not the command spelling

Use one row per observed interface and retain the source command/output beside it: product, exact release, CLI mode, interface name, administrative state, operational state, IPv4 addresses, IPv6 addresses, routing context and time. Enter “not shown” for an omitted field. The chapter's ordinary IPv4 brief view does not by its name promise IPv6, VRF membership, optical health or a successful service.

For a documentation-only comparison, the chapter's IOS XE interface configuration display and SR Linux `info from state interface ethernet-1/1` intentionally expose different categories of information. A configuration line requesting an enabled interface does not demonstrate operational link state. Find the supported read-only view for each missing field in the exact-release documentation, then verify it in the lab you actually have. A well-supported two-platform comparison earns credit; seven plausible commands without release or output evidence do not.

### 9.2 — The expected cost of a recovery control

In an explicitly invented model, let an unmitigated error probability be 0.01 per change and its conditional loss 10,000 currency units. Expected loss is 100. Assume a rehearsed control reduces the residual probability to 0.002 at a cost of 20 units per change: expected total becomes `0.002 × 10,000 + 20 = 40`, a reduction of 60. The break-even loss is `20 / (0.01 − 0.002) = 2,500` units under these assumptions.

If conditional loss is only 1,000 units, the same simplified comparison is 10 without the control versus 22 with it. That sensitivity demonstrates dependence on assumptions, not permission to bypass a required control. Include the control's failure modes, collateral disruption, rehearsal and recovery limitations in a real assessment. Invented probabilities are not evidence of an organisation's incident rate, and a rollback timer cannot prevent every failure.

### 9.3 — Eight pre-change checks

1. Confirm device identity, environment and exact image/mode: prevents acting on the wrong target or workflow.
2. Identify service scope, owner and change authority: prevents an unowned or unauthorised impact.
3. Capture current configuration and relevant operational baseline: exposes drift and preserves the recovery starting point.
4. Review the intended diff or immediate-command plan and dependencies: detects unintended scope before application.
5. Verify independent recovery access and the supported restoration procedure: reduces dependence on the path being changed.
6. Establish baseline service and management probes with thresholds: makes post-change comparisons meaningful.
7. State stop conditions, timer units and the latest safe decision time: prevents confirmation merely because time is running out.
8. Record staffing, communications and the transcript/evidence location: enables coordination and handover if the original engineer becomes unavailable.

After applying, observe the agreed checks, accept or restore, then verify persistence separately. These are stages of the operation, not evidence that the pre-change checklist itself made the service safe.

### 9.4 — Immediate edits beside a candidate workflow

Risk one is assuming ordinary IOS XE CLI edits are still pending and can be discarded before affecting service. They generally alter the running configuration as they are accepted. Control this with a reviewed command plan, baseline and tested release-specific recovery mechanism; a subsequent copy to startup does not create the original transaction boundary.

Risk two is confusing candidate acceptance, application and persistence on SR Linux. A rejected commit may leave the intended state unapplied; an applied but unsaved state can be lost after restart. Read the diff and commit result, verify service from the appropriate observation point, and save/verify startup using the configured workflow. These controls address different failure modes. Record the actual state instead of treating the lack of a CLI error as acceptance of the complete service.

### 9.5 — A rollback another operator can execute

For a harmless lab description change, write the exact target interface and original value or absence, the selected platform/mode, the restoration commands, whether a commit is required, and the observed-state and persistence checks. Include the evidence location and a contact. The recipient must be able to distinguish restoring an absent description from setting an empty string if the platform treats them differently.

For a consequential route or policy change, additionally name the service trigger, restoration order, time limit, access path, dependencies and tests for both management and user traffic. Check for concurrent authorised work before restoring a whole snapshot: it could remove unrelated changes. Rehearse in the suitable isolated environment and retain results. If no change has been made recently, submit the plan as a proposed exercise rather than inventing a work history.

## Chapter 10 — VLANs, trunks and the access layer

### 10.1 — Untagged does not mean unclassified

Assume the isolated two-switch service, matching /22 masks, ordinary connected routes, empty neighbour caches and forwarding trunks. Both addresses belong to 10.10.0.0/22. The sender first uses ARP to learn the target's MAC. Its request enters A's port 5 untagged and is classified into VLAN 110. It crosses port 24 tagged 110, enters B's VLAN-110 context and leaves B's port 5 untagged. The reply makes the reverse journey. Each switch learns the source MAC on the receiving attachment within the relevant learning context.

Subsequent unicast follows the learned destination. Neither host needs a default gateway for this exchange, and neither IP address changes on the bridges. VLAN membership is internal forwarding context even on an untagged wire. Inspect host-facing and trunk captures together; account for capture/offload behaviour before treating a missing displayed tag as proof that the wire carried none.

### 10.2 — Add two services without joining them

Create VLANs 120 and 130 on both switches, admit 110/120/130 on both trunk ends and assign separate endpoint attachments. Keep the native-VLAN design consistent and retain loop protection. In this isolated exercise, use 10.10.4.11/22 and 10.10.4.13/22 for VLAN 120, and 198.51.100.11/24 and 198.51.100.13/24 for temporary VLAN 130. The latter is lab-only documentation addressing; it does not replace London's voice allocation of VLAN 210.

For each VLAN, prove local and cross-trunk communication in both directions and confirm MAC-learning/tag context. For isolation, send bounded, uniquely identified Ethernet probes, verify delivery to an eligible same-VLAN receiver and absence at monitored receivers in the other VLANs. Check capture operation with a positive control. A failed cross-subnet ping without routing proves little about bridged isolation. Remove only VLAN 120 from one trunk end, record its failure while the other services remain available, restore it and repeat the baseline. Permitted routing needs its own policy tests.

### 10.3 — A department name is not a flow policy

Ask who owns the devices and service, how many addresses are required now and after growth, where devices attach, which IPv4/IPv6 services they initiate or receive, and which local peer communication is necessary. Identify DHCP/relay, DNS, time, authentication, management, discovery and Internet dependencies. Establish isolation requirements, data sensitivity, tolerable interruption, maintenance arrangements and the person accepting the result.

Choose the prefix, VLAN/VRF mapping, gateway, filters and monitoring from those requirements. Another department might share the same policy role; one department might need several roles for staff, unmanaged devices and guests. Record positive and negative acceptance tests and an owner for future changes. A new VLAN alone does not implement the requested trust boundary.

### 10.4 — Retire a service, not just a number

Reconcile configuration, port/trunk membership, MAC/ARP/ND records, flow observations, address-service records and the asset register. Consult likely owners and examine backup, month-end, failover and maintenance schedules. Choose an observation window that includes the relevant operating cycle; a silent weekend does not rule out a monthly backup or standby controller.

Document the proposed removals and exact restoration, retain a usable management path and agree a window and rollback trigger. Remove an agreed attachment in a controlled stage, observe affected and control services, then progress through access, trunks, gateways, policy and address records as dependencies allow. Do not free the prefix for reuse while unresolved dependencies remain. Keep owner confirmation, change evidence and rollback expiry with the inventory.

### 10.5 — Gateway choice follows the outage requirement

A tagged router/firewall link can suit a small branch when its forwarding and policy capacity, shared uplink and restoration time meet the target. Two SVIs on a redundant switching pair can offer local inter-VLAN routing and gateway survival, provided that the pair, routing, return paths and policy are supported. SVI placement must not bypass required inspection.

An assumed 200 Mb/s inter-VLAN peak may fit a qualified 1 Gb/s tagged attachment, whereas a multi-gigabit workload cannot fit that single directional line-rate limit. A branch accepting replacement within a working day might accept one gateway; continuity during chassis maintenance requires another working path. Count support, power, uplinks, shared defects and recovery labour. Test failure and restoration; equipment count alone does not decide the case.

## Chapter 11 — Spanning tree and the loop problem

### 11.1 — Trace the copies without multiplying them by assertion

Name the A-to-B links L1 and L2. A's host-originated broadcast creates one copy on each. B receives copy 1 on L1 and floods it towards L2 and eligible host ports, never straight back out L1. B receives copy 2 on L2 and forwards it towards L1 and eligible host ports. A receives returning copies on the opposite links and again floods each to the other link and eligible host ports.

With only these two inter-bridge links, no STP protection and no additional branching, each circulating copy has one onward inter-bridge path. This does not establish doubling every lap. Continued input adds frames, extra branches can replicate them, and duplicate delivery and alternating source learning can still make the topology unusable. Ethernet supplies no per-frame hop counter to terminate circulation. Describe the paper trace; do not build an uncontrolled live loop.

### 11.2 — The cheaper route can have more hops

A remains root because bridge-ID ordering is unchanged. B reaches A directly at cost 20,000. C compares direct CA at 60,000 with CB plus B's advertised root cost, 20,000 + 20,000 = 40,000. C chooses CB as its root port; B's BC port is designated. On AC, A advertises superior root information and remains designated. C's CA port is alternate/discarding under RSTP.

If BC fails, C can use CA at cost 60,000; after BC returns, it should prefer 40,000 again. A cost is a protocol metric, not measured latency. Check roles and useful traffic through both transitions.

### 11.3 — One region definition, two intended trees

One example region is name ALDERGATE-CAMPUS, revision 1, VLANs 110/120 in MSTI 1 and 210/305 in MSTI 2, with every other VLAN's mapping explicitly agreed. Unassigned VLANs normally remain in the common/internal instance; verify the target's representation. Match name, revision and complete mapping on every intended region member. A revision number is a matching field, not negotiation that installs the newest mapping.

Choose distribution A as preferred root for MSTI 1 and B for MSTI 2, with the opposite peer secondary; specify the CIST root separately and align gateways where useful. Record expected roles and eligible trunks. In an isolated test, change one mapping, compare digests and boundary status, trace affected and control VLANs, and restore the definition. A mismatch produces a region boundary, not guaranteed total disconnection. It can alter forwarding and load distribution.

### 11.4 — Investigate the guard's evidence

Preserve the port role, host mode, timestamps, BPDU evidence, neighbour information and physical cabling before recovery. Check for an unintended switch, a bridged host/hypervisor, a loop through another socket or a legitimate attachment misclassified as host-only. Receiving a BPDU is a signal; it does not establish motive or prove that every possible loop would be detected.

Remove the unexpected bridge path or redesign an authorised bridge adjacency with proper STP/protection policy. Recover through the platform's documented procedure, verify host startup and the unrelated control service, then monitor recurrence. Do not enable a short automatic recovery cycle while the cause persists. Preserve management access and restore the prior accepted state if the repair fails.

### 11.5 — Compare designs with a shared acceptance sheet

For 1,200 users, record service locations, genuine Layer 2 adjacency requirements, mobility, wired/wireless and PoE demand, fibre routes, traffic direction, growth, maintenance windows and tolerated interruption. Compare a bounded bridged domain with deliberately selected roots against routed access with its actual subnet boundaries, routing adjacencies and ECMP support. Both need admission, policy, address services and a return path.

Price hardware, licences, support, training and migration over the same period. Test access-link loss, an aggregation/root failure, restoration, dependencies and surviving capacity. A bounded Layer 2 design can suit a team with the required skills and limited adjacency needs; routed access can suit requirements for smaller bridged domains and routed path use. Give the measured or still-required evidence that would change the recommendation.

## Chapter 12 — Link aggregation, MLAG and redundant gateways

### 12.1 — Surviving aggregate capacity is only the first check

Four 10 Gb/s members provide a nominal 40 Gb/s in one direction. After one fails, three provide 30 Gb/s, so 24 Gb/s of offered demand is 80% of the surviving line-rate sum, before overhead. That aggregate inequality is necessary in this simple model but insufficient for useful service.

A 12 Gb/s single flow cannot fit a conventional 10 Gb/s member even if the other flows total only 12 Gb/s. Smaller flows can also collide on one member. Check distribution, queue drops, packet mix, endpoints, minimum-links behaviour and restoration. If the threshold requires all four members, the surviving three do not automatically leave an operational bundle. State the threshold and traffic assumptions beside the calculation.

### 12.2 — Hospital upgrades need named evidence

Compare exact stack and MC-LAG products/releases, forwarding/control dependencies, shared power and links, orphan attachments, gateways and supported upgrade procedures. Ask what each clinical service loses during controller failover, peer-link loss, chassis restart, incompatible-version intervals and restoration. A dual-attached server does not protect a single-homed bedside device.

Require a supported version matrix, prerequisite checks, tested rollback and timestamped new/established application observations under representative load. Agree outage and maintenance acceptance with clinical engineering and service owners. “ISSU supported” is an input, not a measured zero-outage result. Record untested steps rather than inheriting a feature label as service acceptance.

### 12.3 — Independence includes the path absent from the VLAN diagram

Draw peer-link data/state and peer-liveness traffic through actual ports, chassis, fibres, patch panels, power and upstream dependencies. A separate VLAN in the same cable does not survive cable loss. Define the platform's documented response to peer-link loss with liveness intact, liveness loss alone, and loss of both in each relevant order.

Use an approved isolated test with management access and recovery steps. Observe port suspension/forwarding, peer state, orphan traffic, gateway behaviour, duplicates, application service and restoration. Keep fault order and timestamps: peer-link-first results need not qualify keepalive-first loss. Do not improvise a production split-brain test from this answer.

### 12.4 — Subtract, compare, then check the election conditions

110 − 5 = 105, still above the healthy peer's priority 100. That tracking decrement alone does not make the lower-priority peer preferable. A decrement greater than 10 makes the first peer strictly lower: 11 gives 99; 30 gives 80. Exactly 10 ties; a VRRP Backup accepts an equal-priority Active's advertisements, so this does not force preemption. Address tie-breaking applies in the appropriate election state, such as competing Active routers.

These numbers assume ordinary non-owner priorities and documented tracking. Verify preemption, effective priorities, advertisements, delays and implementation. If the original Active stops advertising, the peer can take over through failure detection regardless of this arithmetic. Constrain a reachability probe to the path it tests so success through the backup cannot conceal a primary fault.

### 12.5 — Reuse the method, requalify the service

Reuse the inventory, timestamping method, fault definitions and evidence form. The IPv4 test shows those particular components and observations worked then. It does not establish IPv6 VRRP, router advertisements, virtual link-local behaviour, neighbour discovery, IPv6 policy or return routing.

For IPv6, test new address configuration, established traffic, gateway election, RA/ND, tracking and restoration. For a stateful firewall, add state synchronisation, NAT where applicable, session ownership, asymmetric paths, inspection features and new/existing connections. Capture application gaps with enough temporal resolution for the target. Gateway election and session survival are different results.

## Chapter 13 — Wireless: Wi-Fi 6E, Wi-Fi 7 and RF planning

### 13.1 — One quarter of the active laptops moves band

The theatre has 120 active laptops and 30 active phones. Moving one quarter of those laptops sends 30 × 4 = 120 Mb/s to 6 GHz. Remaining laptop demand is 90 × 4 = 360 Mb/s; phones add 30 Mb/s, giving 390 Mb/s at 5 GHz.

Each 5-GHz radio budgets 60 Mb/s and each 6-GHz radio 90 Mb/s. Required counts are ceil(390/60) = 7 and ceil(120/90) = 2. With at most one of each band per AP, the physical lower bound is seven APs. The assumed nine 5-GHz and four 6-GHz channel opportunities do not reject these counts, but still need a valid spatial plan.

For optional one-AP-loss capacity, eight 5-GHz and three 6-GHz radios leave at least seven and two: an eight-AP lower bound under the same pairing assumption. Neither count proves surviving coverage or successful redistribution.

### 13.2 — Separate policy intention from operating permission

A policy decision can precede implementing regulations and technical conditions. A supported channel list describes capability; it does not establish the right to transmit at the site's power, location or device class. Record the regulations in force, current interface requirements, certified product/mode, country configuration and any required AFC authorisation. A foreign channel plan cannot supply missing domestic permission.

The chapter's dated UK sources distinguish lower-band requirements from upper-band policy and implementing consultation. Recheck at deployment rather than converting a publication snapshot into perpetual permission. Consult [Ofcom's 6-GHz decision and implementing documents](https://www.ofcom.org.uk/spectrum/innovative-use-of-spectrum/consultation-expanding-access-to-the-6-ghz-band-for-commercial-mobile-and-wi-fi-services) and [AFC statement](https://www.ofcom.org.uk/spectrum/innovative-use-of-spectrum/enabling-automated-frequency-coordination-afc-in-the-6-ghz-band).

### 13.3 — Measure the roam and the call

Record handset/driver, authentication and FT mode, BSSID/band/channel, location and a common time reference. Walk both directions with a call and representative load. Observe signal in both directions, retries, channel use, candidate discovery, association/FT exchanges, policy, subnet/gateway state and application traffic. Correlate the last useful packet on the old attachment and first on the new, accounting for clock error.

Compare a stationary call at the problem location and another qualified client. A long scan, failed authentication, lost coverage, changed addressing, anchor failure or wired fault can all interrupt a call. Preserve certificate and management-frame security while investigating. Repeat after a justified change and during recovery; association alone does not measure voice continuity.

### 13.4 — A smaller room does not inherit the survey

Assume 200 laptops and 200 phones, with the chapter's fractions and rates. Laptop demand is 200 × 0.4 × 4 = 320 Mb/s; phones add 200 × 0.1 × 1 = 20 Mb/s: 340 Mb/s total. If all use the 5-GHz model, ceil(340/60) = 6 radios; seven are the simple one-radio-loss count.

If half the active laptops use 6 GHz, that band carries 160 Mb/s and 5 GHz carries 180 Mb/s. The bounds are ceil(160/90) = 2 and ceil(180/60) = 3: three dual-band APs before failure. The one-AP-loss counts are three 6-GHz and four 5-GHz radios, a four-AP lower bound.

The precise 180/60 boundary has no additional margin beyond the selected utilisation budget. Validate occupancy, activity, clients, useful capacity, placement, attenuation, interference, channels and redistribution. A canteen's materials and behaviour differ from a theatre; the calculation is portable, its inputs may not be.

### 13.5 — Lose the WAN, then try to join

Agree separate required outcomes for local and Internet services. Establish baseline flows, identity/address/DNS dependencies and management access. Isolate the intended WAN dependency in a controlled test while preserving recovery access. Observe established local sessions, new clients, reauthentication, lease renewal, DNS and portal use, then an AP restart under the approved procedure.

Record remote identity, configuration, licensing and gateway dependencies and elapsed outage duration; cached state may expire later. Local bridging may preserve an established flow while a new client cannot authenticate. Restore the WAN and test reassessment, configuration reconciliation and recovery. Record that difference rather than assigning one pass/fail to the entire WLAN.

## Chapter 14 — Controlling who gets on

### 14.1 — Define privileges and failure states together

One staff role uses managed EAP-TLS identities and permits named staff services. A contractor role uses an approved identity process, sponsor and expiry, and only contracted services. A printer MAB exception has an inventory owner and a restricted flow set: designated print/management systems plus required address/time/update services, not the staff role. Health and authorisation remain separate from possessing a credential.

Explicit rejection denies requested admission. Unknown devices receive only defined onboarding access, if offered. For server unavailability, state whether new access is denied or a narrow critical role is permitted on specified attachments. Established sessions may be retained until defined reauthentication/expiry events; document target behaviour separately. On recovery, reassess temporary sessions, remove stale privileges and check accounting. Test normal, rejection, timeout and recovery for each role.

### 14.2 — A returned attribute is not an installed filter

Correlate the RADIUS transaction with the endpoint, port and session. Inspect effective VLAN/role, host mode, local overrides, installed filter and enforcement direction/address family. Confirm topology, gateway/VRF, routes and firewall policy. Check stale addresses, another active interface, an existing permitted session or a same-segment path around enforcement.

Capture a controlled connection to management and a permitted control flow at relevant boundaries. Determine which rule/path admitted it. VLAN 110 can route to management unless policy forbids it; the attribute does not inherently contain that prohibition. Correct the proven cause and repeat positive/negative tests, including IPv6 and removal of old permissions after role changes.

### 14.3 — Budget the surviving supply

At the PSE allocation boundary, 740 W with a 10% reserve leaves 666 W. floor(666/36) = 18 devices reserve 648 W, leaving 18 W inside that usable allocation and 92 W of the original budget unallocated. A nineteenth requires 684 W and breaks the reserve.

After the assumed surviving budget falls to 370 W, the reserve leaves 333 W. floor(333/36) = 9 devices reserve 324 W, leaving 9 W within usable allocation and 46 W of the surviving budget unallocated. No-reserve counts would be 20 and 10.

If 18 devices were installed, designate nine essential devices and confirm the target's priority/shedding and recovery. Identities and priorities are needed before claiming which nine survive. Confirm surviving coverage and service. These assumed budgets do not describe a particular switch/PSU pair.

### 14.4 — A flow matrix does not sanitise allowed traffic

This is a role-level starting matrix. Substitute supplier-required transports, ports, directions and exact endpoints; recording traffic can use different initiation patterns.

| Initiator | Destination | Purpose | Evidence |
| --- | --- | --- | --- |
| Camera or recorder, as documented | Its paired recorder/camera | Video and control | Required sessions work; unrelated devices cannot use the path. |
| Camera | Approved time/DNS/address services where needed | Supporting services | Only required paths work, including relay behaviour. |
| Approved management host | Named cameras | Administration | Authorised management works; ordinary staff/guest attempts fail. |
| Documented update initiator | Approved update endpoint or camera | Firmware | Update works with broad Internet access denied. |
| Camera | Other cameras, arbitrary corporate/Internet systems | No ordinary permission | Routed and same-segment denied-path checks with controls. |
| Recorder | Explicit storage, management and supporting services | Recorder operation | Required onward flows work; unrelated onward access is denied. |

Add owner, logging and exception expiry to each actual rule. An allowed protocol can carry malicious input. Protect recorder software, credentials, management and onward reachability, and monitor both ends. Apply IPv4/IPv6 and local Layer 2 controls where relevant.

### 14.5 — Repair trust as well as the exposed credential

The client accepted an unintended EAP server because managed trust or expected-server validation failed, was missing, or was bypassed. Captured MSCHAPv2 challenge-response material can support further credential attacks; it is not automatically recovered plaintext. Preserve evidence and scope affected accounts/devices through the incident process.

Contain the rogue attachment, restore managed issuer/name/method settings, and rotate affected credentials and revoke relevant sessions according to the established exposure. Investigate reuse and suspicious authentication. Prove the corrected profile rejects the unintended server while accepting the intended one without user prompts.

EAP-TLS avoids sending a reusable password or an MSCHAPv2 inner exchange. It still needs expected-server validation, protected client keys, authorised identity mapping and certificate lifecycle/revocation handling. A new method name cannot repair a broad role or missing filter. [RFC 9190](https://www.rfc-editor.org/rfc/rfc9190.html) separates certificate validation and authorisation.

## Chapter 15 — Campus architectures and overlays

### 15.1 — A logical edge needs a cabling rule

Four abstract distribution nodes form 4 × 3 / 2 = 6 full-mesh logical edges. Attaching each to both of two core nodes gives 4 × 2 = 8 logical attachment edges, excluding core interconnection.

Now assume each distribution node is a two-chassis block and each chassis has one physical uplink to each core chassis. Four blocks × two chassis × two cores = 16 attachment cables. If each distribution pair has one peer cable and the core pair one cable, that illustrative arrangement totals 16 + 4 + 1 = 21; whether peer links are required depends on the architecture.

For a separate physical mesh example, connecting both chassis of each block to both chassis of every other block requires four cables per inter-block relationship: 6 × 4 = 24, before internal peer links. These are declared rules, not mandatory conversions. Count LAG members, breakout ports, fibre routes and resilience separately.

### 15.2 — First establish why adjacency is required

Identify the application behaviour requiring the same Ethernet domain across blocks: a measured protocol dependency, supported clustering requirement or address-preserving mobility, rather than an inherited diagram. Ask whether a supported application change could use routing, or whether the workload and its failure requirements can be localised within one block.

If extension remains necessary, compare the overlay's underlay, MTU, endpoints, control plane, loop/multihoming controls and operations with alternatives. It can extend fault and broadcast scope alongside connectivity. Price licences, skills, monitoring, upgrade and exit work. Test adjacency, denied flows, a block/underlay failure and restoration. Application redesign cannot be assumed possible without owner and supplier evidence.

### 15.3 — Separate the port-rate ratio from demand

The twelve 2.5 Gb/s AP ports still total 30 Gb/s, so the 15:1 normal and 30:1 failed port-rate ratios for two 1 Gb/s members do not change. At 0.05 Gb/s per AP, demand is 0.6 Gb/s: it fits the 2 Gb/s normal and 1 Gb/s surviving sums before overhead and other traffic. This input does not compel a bandwidth upgrade.

At 0.5 Gb/s per AP, demand is 6 Gb/s, exceeding both sums. Two 10 Gb/s members satisfy this aggregate example after one fails, subject to service checks. An ordinary single flow still fits only its selected member's capacity and competes with co-hashed flows. Measure mix, bursts and dependencies before acceptance.

### 15.4 — The access link still fits; the shared edge does not

Doubling per-AP demand from 0.6 to 1.2 Gb/s gives 44 × 0.2 × 0.1 + 4 × 1.2 = 5.68 Gb/s per access switch. With 25% growth, it is 7.10 Gb/s, or 71% of a surviving 10 Gb/s leg in the nominal line-rate comparison.

Across 20 switches the bound is 142 Gb/s. If all is offered towards the server edge as assumed in this bound, it exceeds the surviving 100 Gb/s link by 42 Gb/s. Normal 200 Gb/s attachment does not fix the failure case. Validate the destination mix; increase surviving capacity, change placement, admit less load or accept a documented restriction. Hashing, overhead, bursts and the single server-edge device remain separate constraints.

### 15.5 — A decision record with an unresolved point

**Decision:** retain the collapsed-core design as a candidate for London's stated services; authorise detailed qualification, not production acceptance.

**Basis:** 20 access blocks each offer a growth-adjusted 4.10 Gb/s bound; a surviving 10 Gb/s leg fits that aggregate by line rate. The 82 Gb/s bound is below one 100 Gb/s server attachment. One firewall must meet the 10 Gb/s inspected requirement with intended features and sessions.

**Alternatives:** compare a separate core for maintenance/service attachments and routed access where adjacency can be local. An overlay needs a named requirement and an operational case.

**Unresolved:** supported MC-LAG/gateway/STP and release pairing; port-speed/breakout and optics; real traffic and application performance; physical path/power independence; RF and failed-PSU PoE; failure/restoration evidence. The single server-edge device needs separate dual-edge engineering if its outage is unacceptable.

**Acceptance and review:** assign the design authority, service owner and operations reviewer; retain tests and rollback. Reopen sizing when measured growth or changed demand exceeds the agreed failed-state budget. Keep the decision conditional until owners accept the evidence.


## Chapter 16 — How a router actually forwards

### 16.1 — Look up installed prefixes

For ordinary destination lookup in the stated table, choose the matching installed prefix with the greatest prefix length.

| Destination | Longest installed match | Why |
| --- | --- | --- |
| 10.10.4.7 | 10.10.4.0/22 | Inside 10.10.4.0–10.10.7.255; outside the /25 |
| 10.10.4.200 | 10.10.4.128/25 | Inside .128–.255 of that /24 |
| 10.10.9.1 | 10.10.0.0/16 | Outside the /22 and /25 |

The /0 and /8 also match all three addresses, but a longer installed match exists. If the /25 is only a rejected candidate, 10.10.4.200 uses the /22. Rejection does not remove that destination from the broader prefix. State the VRF/table first; the same address can produce another result in another context.

### 16.2 — Compare route sources on two platforms

For eligible routes to the **same /24**, Cisco IOS XE's default eBGP distance 20 beats OSPF 110. EOS defaults put OSPF 110 ahead of BGP 200. These defaults do not prove the result on a configured device. Obtain the exact release, effective route preferences, each protocol's candidate and selected status, next-hop eligibility and the routing-table winner. Then inspect the relevant forwarding installation and a representative packet path. Identify whether the display is a protocol table, system RIB, software FIB or hardware view.

A more-specific route is a different question. An installed /25 can win lookup over either /24 without changing these preferences. Do not compare an OSPF metric with an AS-path length as though the two were one numerical scale.

### 16.3 — Improve a transfer limited by one member

One option is a faster usable member and adequate capacity throughout the remaining path. A second is application-supported parallel connections whose hash inputs differ, or an explicitly supported multipath transport. Multiple independent flows may spread across several members; verify actual egress and application goodput. More flows can still collide, and a common bottleneck or application limit can erase the gain.

Adding equal-rate members increases aggregate opportunity for a population of flows. It does not guarantee that the existing transfer stops mapping to one member. Per-packet spraying changes the problem and can introduce reordering; it needs platform and transport qualification rather than a casual substitution for flow hashing. Record the member rate, hash fields and before/after flow distribution before attributing an improvement to the network change.

### 16.4 — Forecast exhaustion and choose a trigger

With present utilisation 0.78 and constant annual growth g, the teaching model is U(t) = 0.78(1+g)^t. Solve t = ln(target/0.78)/ln(1+g), with t in years. Fractional years here interpolate a compound-growth model; they are not a measured demand trajectory.

| Annual growth | Time to 100% | Time to an 85% planning ceiling |
| --- | --- | --- |
| 3% | 8.41 years | 2.91 years |
| 6% | 4.26 years | 1.47 years |
| 10% | 2.61 years | 0.90 years |

For one defensible plan, require migration to finish below 85%, preserving 15 percentage points of capacity, and allow one year from decision to completion. The latest decision times are approximately 1.91, 0.47 and −0.10 years from now. The negative value means the fast-growth scenario has already passed this model's decision deadline; it does not mean capacity is exhausted. Begin procurement or reduce the exposure now if that scenario is credible. Revisit actual entry consumption, growth and delivery time; change the trigger when those assumptions change.

### 16.5 — A visible BGP prefix with failed service

Build competing explanations and give each a discriminating check.

| Hypothesis | Evidence that would support or challenge it |
| --- | --- |
| Receipt passed but the path is not selected | Accepted candidates, best-path reason, configured policy and competing source in the RIB |
| The next hop cannot be resolved | Recursive route chain in the same context/family; evidence of a circular dependency or missing underlay route |
| Selection succeeded but installation failed | Programming status, resource alarms and the relevant software or line-card table |
| Installed forwarding is correct but delivery fails | Ingress/egress captures, neighbour state, ACL/drop counters, MTU and downstream observations |
| Forward delivery succeeds but the reply fails | Server receipt and reply capture; server gateway, reverse routes, policy and stateful-path requirements |

Keep source, destination, protocol, ports, VRF and time fixed while comparing observations. If the server captures the request, that is stronger evidence of forward delivery than another route-table screenshot. Change one justified cause, repeat the controlled transaction and record restoration. A route existing in BGP is compatible with every failure above.

## Chapter 17 — Static routing

### 17.1 — Make the backup less preferred

For the same /24 and otherwise eligible candidates, SR OS static preference 150 beats BGP preference 170, so it is not a floating backup. Static preference 200 is worse than 170 and can act as the backup when the BGP route becomes unusable. Confirm the configured preferences and eligibility on the actual release.

If the static is a /25 and installed, destinations within that /25 use it ahead of the /24 regardless of the latter's better preference. The two routes describe different destination sets. A safe change plan checks both halves of the /24 and tests withdrawal and restoration, rather than proving only that the static line exists in configuration.

### 17.2 — BFD to the near end

In the stated fault, no failure of the near-end BFD path has been detected: it remains healthy while the remote uplink is broken. That is consistent with the session's endpoint scope. Keep near-end BFD if local path detection is useful, but add a test that covers the required remote path. Depending on the requirement and endpoint support, this could be multihop BFD to a controlled remote router or a permitted transaction against the remote service.

Pin the test to the primary path, define its source and return path, and specify failure/recovery thresholds. Distinguish remote-router reachability from DNS, TLS and application success. Test remote-uplink loss with the near link up, near-link loss, endpoint-only failure, backup operation and recovery. Avoid withdrawing a working network solely because one optional server has failed without agreeing that policy with the service owner.

### 17.3 — Follow the independent probe

In Lab 18, the probe destination is 198.19.0.20/32 and its primary next hop is 192.0.2.2. The separate, less-preferred /32 discard prevents a missing primary probe route from falling through to a broader backup or default. A discard /32 does not replace a healthy, preferred /32 forwarding route.

| State | Probe behaviour | Application behaviour |
| --- | --- | --- |
| Primary healthy | Primary /32; source 192.0.2.1; reply on the specified primary path | Preferred service route uses the primary |
| Remote primary path fails | Continues testing that path; times out | After the controller's two consecutive failures, the primary service route is removed and backup is selected |
| Primary probe next-hop route becomes unusable | The /32 discard prevents escape over backup | Backup service route remains independently usable |
| Primary recovers | Independent /32 can succeed before service restoration | After three consecutive successes, the preferred service route is restored |

The lab deliberately returns application replies over its stated backup path; do not silently assume symmetry or add a stateful firewall/NAT requirement absent from the fixture. The controller starts with the primary service route absent and uses at least one-second sampling with a one-second probe timeout. Those settings and scheduling mean the sample counts are not exact outage promises. Verify the actual route, capture and timestamps at each transition; also test the controller stopping.

### 17.4 — Count a finite forwarding loop

Use the chapter's model: a packet arrives at the site with TTL 64, and each router decrements TTL before forwarding. The site sends TTL 63 to the core; the core returns TTL 62. The last successful traversal carries TTL 1 from site to core, where the next forwarding attempt discards it. There are 63 traversals: **32 site-to-core and 31 core-to-site**. Count traversals, not visits or distinct original packets.

For an unconstrained 1 Gb/s stream of equal-sized IP packets, multiplying those counts gives attempted steady-state traversal loads of 32 and 31 Gb/s. A 1 Gb/s full-duplex link can carry at most 1 Gb/s in each direction before considering overhead. Queuing and drops prevent the multiplied demand from being carried; this arithmetic is not a traffic measurement. A correctly scoped aggregate discard terminates unmatched traffic locally and prevents those repeated traversals, while more-specific reachable routes continue to win.

### 17.5 — An inactive route can still have an owner

Inventory prefix/length, family, VRF, next-hop form, preference, tracking dependency, intended primary, service owner, change record and review/expiry date. Record the failure condition under which the route should become active, its authorised use, last test and rollback. Compare the intended object with running configuration, candidate/active state and forwarding dependencies.

A documented backup may be inactive precisely because it is working as designed. An obsolete migration route may have no remaining service or owner; that absence is a reason to investigate, not immediate permission to delete it. Obtain owner confirmation and a controlled removal plan, check hidden failover dependencies, then observe and retain the rollback. An inventory entry saying only “static route, inactive” cannot distinguish the two cases.

## Chapter 18 — OSPF

### 18.1 — Diagnose churn before drawing an area boundary

Measure the origin, types, frequency and content of changed LSAs; flooding fan-out and retransmission queues; SPF/partial calculation invocations and duration; CPU per relevant process/core; database and prefix sizes; route installation and application interruption. Capture a quiet baseline and a controlled fault with timestamps. A flap that changes topology can cost more than an unchanged refresh; implementation throttles and concurrent work also matter.

Repairing the underlying attachment removes the source of churn. An area boundary can contain topology detail but still propagate changed inter-area reachability. Aggregation may hide some component changes if the summary remains advertised, at the price of less precise reachability and potential discard for a missing component. Compare normal paths, failure paths and residual load for each option. “140 routers” and “ten flaps” do not specify the graph, affected routes, algorithm or processor, so they cannot determine CPU seconds.

### 18.2 — Calculate and locate directional costs

With consistent units and the stated inverse-bandwidth model, 400/25 = **16** and 400/40 = **10**. At a 100 Mb/s reference, both faster interfaces reach the usual minimum cost of 1 rather than these intended values, unless explicit costs override the calculation.

The misconfigured router originates its own outgoing costs. Its neighbours calculate from those advertised values; they do not rescale them using their own reference bandwidth. Other routers' originated costs remain unchanged. Inspect the relevant router LSA/interface costs and both directions of affected paths. In the chapter's A–B–C example, A's cost 40 to B plus B's mistakenly advertised cost 1 to C gives 41. Unequal reference settings can produce asymmetric or unintended paths; they do not prove that a steady-state forwarding loop must occur.

### 18.3 — Develop an area design from the service

For an illustrative Aldergate design, put redundant core paths in area 0 and attach a branch area through two ABRs. Choose a normal branch area if branch routers need detailed remote/external reachability; a stub is defensible only if its default behaviour meets the service and no local external redistribution is needed. Use an NSSA deliberately if local redistribution is required and its scope/default behaviour fits. These are proposed assumptions, not a claim about an already deployed Aldergate topology.

List each connected/static/service prefix, who originates it, and why. Limit redistribution to named ASBRs with explicit prefix and provenance policy. Tie default origination to a defined usable exit condition; a neighbour being Full is insufficient. For dual exits, test whether choosing the lowest cost to a default also chooses the desired remote path. Retain selected specific routes when their external costs or service restrictions make that distinction necessary.

Draw normal operation, loss of each ABR, loss of an external exit with the ABR still up, and a backbone partition. For every case predict selected routes, forward/reply paths and survivor capacity. State what a summary suppresses and what happens to unavailable components. Submit this path/evidence table with the area drawing; a neat area diagram without the failure cases is an incomplete design.

### 18.4 — A type 5 absent behind a Full adjacency

In a stub area, absence of type 5 is expected; inspect the intended type-3 default and actual reachability. In an NSSA, type 5 is also absent, while local external information can appear as type 7 and eligible routes can be translated out of the NSSA. An external type 5 in another area is not automatically translated into type 7 on entry. Confirm the intended defaults and import restrictions.

For an ordinary normal area where the type 5 should be flooded, compare the exact LSA identity, sequence, checksum, age and scope on the ABR and branch. A MaxAge withdrawal is different from a current usable advertisement. Check area type/capabilities, flooding and retransmission evidence, and whether the route is present but unselected or has an unusable forwarding address. Full tells you about adjacency synchronisation; it does not convert every absent route into a flooding defect.

### 18.5 — Count the Full relationships

With five routers on one ordinary broadcast LAN, the DR is Full with four others. The BDR is Full with the three DROthers as well; its relationship with the DR was already counted. Total **4 + 3 = 7 unordered Full relationships**, or 14 directed neighbour-table entries if every endpoint is counted. The three DROther-to-DROther pairs normally remain 2-Way. A five-router full mesh would have 5×4/2 = 10 pairs, which is a different adjacency model.

A higher-priority router joining an established DR/BDR election does not simply pre-empt the incumbents. Priority influences election eligibility and selection when election rules require it. Observe actual identities and network type; do not reset a working LAN merely to make the numerically largest priority appear as DR without a change plan.

### 18.6 — Check address families independently

One process label does not establish equal OSPFv3 family support, instance configuration, advertised prefixes, policy or installed routes. IPv4 and IPv6 family state can differ even though OSPFv3 commonly uses IPv6 transport. A successful adjacency or ping in one family cannot certify the other.

Record exact releases, supported address families, instance/family bindings and interface configuration. For each family, verify relevant adjacencies and scoped advertisements, route calculation, next-hop resolution, installation and an endpoint transaction with its return path. Inject the same named link failure and then a family-specific fault, such as suppressing only the IPv6 service prefix. Compare restoration and timers separately. Keep expected results distinct from observations; the second fault should be visible even if the common process stays healthy.

## Chapter 19 — IS-IS

### 19.1 — Construct identifiers and survive a merger

Under the lab's documented decimal-padding convention:

| Loopback | Six-byte system ID | Complete NET |
| --- | --- | --- |
| 10.255.0.11 | 0102.5500.0011 | 49.0001.0102.5500.0011.00 |
| 10.255.0.12 | 0102.5500.0012 | 49.0001.0102.5500.0012.00 |
| 10.255.0.13 | 0102.5500.0013 | 49.0001.0102.5500.0013.00 |
| 10.255.0.14 | 0102.5500.0014 | 49.0001.0102.5500.0014.00 |
| 10.255.0.15 | 0102.5500.0015 | 49.0001.0102.5500.0015.00 |

For .11, padding produces 010.255.000.011; removing the separators and grouping gives 0102.5500.0011. The resulting configuration is hexadecimal digit notation, not the binary IPv4 address. Check the three-byte area address, six-byte system ID, NSEL 00 and uniqueness in the intended domain against inventory and actual advertisements.

A merging network using the same loopbacks and convention can allocate the same IDs. Reconcile both address and system-ID inventories before joining the domains; assign unique replacements and plan the routing disruption. Changing the loopback alone does not change a manually configured NET. Record whether future IP renumbering preserves the existing system ID.

### 19.2 — Choose from the requirement

Three defensible reasons to choose OSPF are demonstrated team competence and recovery procedures; the required feature set being better supported or qualified on the actual estate; and lower migration/interoperability cost with the existing design. Each needs evidence: exercise records, exact-release feature/defect checks, and a tested migration plan with staffing and failure costs.

The same evaluation can favour IS-IS if its required extensions interoperate more reliably on that estate, measured convergence/resource use better meets the requirement, or the operating team and tooling already handle its failure modes well. Compare like-for-like topologies, families, scale and fault injections. “Carriers use it” does not establish superiority, just as a familiar CLI does not prove the current design meets the service objective.

### 19.3 — Reveal enough information to choose the exit

An L1 router using only eligible attached defaults compares 10 to exit A with 30 to exit B, so it chooses A. For the named destination, the complete costs are A: 10+100 = **110** and B: 30+5 = **35**. The destination-specific path through B is better under this metric model.

For a constructed remote prefix 198.18.10.0/24, leak its actual L2 reachability into L1 through the eligible exits, advertising remaining costs 100 and 5 under the stated metric convention. Include any additional configured leak metric in the calculation. The L1 router can then compare totals 110 and 35; a summary or default with unrelated costs does not provide the same information. Use RFC 5302's down indication and the required restrictions against feeding a down-leaked route back into L2, together with explicit prefix policy. Verify both database encodings and route use on the chosen implementations.

Withdraw each exit's reachability and test fallback, recovery and the reply path. The arithmetic assumes both candidates are eligible and the stated costs are used; it does not prove an installed path in a live network.

### 19.4 — Build a compatibility matrix without inventing results

One concrete worksheet can name **FRR 8.4.4 and FRR 10.5.1**, using their respective 8.4 and 10.5 manuals as version-family documentation. Record exact package/build identifiers when obtaining the binaries. Both manuals describe narrow, transition and wide modes; transition sends and accepts both encodings. That documentation does not certify every mixed-version pair or extension combination.

| Target build / mode | Documented encoding intent | Required receive/use checks | Evidence status in this answer |
| --- | --- | --- | --- |
| 8.4.4 / narrow | Legacy narrow | Legacy reachability and representable costs; probe extended input separately | Not newly executed |
| 8.4.4 / transition | Both | Both encodings; duplicate-prefix choice and costs | Not newly executed |
| 8.4.4 / wide | Extended | Extended reachability; probe legacy input separately | Not newly executed |
| 10.5.1 / narrow | Legacy narrow | Same checks; also feature-configuration compatibility | No new run; chapter records rejection with its MT configuration |
| 10.5.1 / transition | Both | Both encodings, route choice and each enabled topology | Not newly executed |
| 10.5.1 / wide | Extended | Extended reachability and each enabled topology | Retained chapter baseline exists; not a complete pairwise test |

Expand these six rows into the nine mixed-build mode pairings and observe both directions. For each, record command acceptance, originating TLVs, received TLVs, selected routes, forwarding and restoration. Keep “documented”, “parser accepted”, “advertised”, “used” and “packet tested” in separate columns. An Up adjacency does not fill any missing route-use cell.

Before dropping legacy encoding, demonstrate a compatible intermediate state across every affected node, with costs representable in that state. Roll back before an incompatible mode isolates a required prefix or before a dependency such as multi-topology makes the proposed fallback unavailable. Retain out-of-band access and complete configuration snapshots. This answer is a completed **test-design guide**, not an executed interoperation matrix: the untested cells deliberately remain unqualified. Sources: [FRR 8.4 IS-IS](https://docs.frrouting.org/en/stable-8.4/isisd.html) and [FRR 10.5 IS-IS](https://docs.frrouting.org/en/stable-10.5/isisd.html).

### 19.5 — Replace a line card with a service plan

Inventory every affected physical port, attachment, local service, transit path, IP family and tunnel/label dependency. Check actual alternative capacity and shared risks. Capture baseline transactions, paths, counters, configurations and recovery access; agree a maintenance window, abort triggers and the person accepting restoration.

Drain or move affected services using the mechanisms each requires. Confirm the correct overload behaviour in every enabled topology, plus BGP, tunnels and attached destinations that an IGP transit decision may not remove. Observe traffic moving and the alternatives carrying it before isolating the card. Replace it under the hardware procedure, validate ports and errors, then restore services in controlled steps. Repeat both-family transactions and failures, check load distribution and remove temporary controls only after acceptance.

The retained FRR example required an IPv6-topology overload action as well as the standard overload behaviour. It does not qualify line-card replacement on commercial hardware. One bit cannot establish spare capacity, protect a directly attached customer, drain every tunnel or demonstrate that the replacement card forwards correctly.

### 19.6 — Compare flat and hierarchical designs

A flat 180-router L2 domain provides shared backbone visibility and a relatively simple level model. Three L1 regions can contain local topology detail but add L1/L2 boundaries, defaults or leaking, boundary capacity and more failure states. Dividing 180 by three gives 60 routers per region only under an explicit equal-allocation assumption; it does not specify how many L1/L2 routers or backbone-only routers are required.

Measure LSP size/count, flooding and retransmissions, calculation duration, control-plane utilisation, route installation, service interruption and operational recovery time under the same workload. Test an internal flap, boundary loss, L2 partition, simultaneous maintenance/failure and a remote-destination change that exposes default-exit suboptimality. Include IPv4/IPv6, extensions and realistic prefix counts. Compare inventory, troubleshooting, leak-policy and training costs alongside performance. Choose the least complicated design that meets measured requirements; 180 alone is not a protocol limit or a reason to add hierarchy.

## Chapter 20 — BGP I: the protocol

### 20.1 — Count sessions once

For n total speakers, the full mesh has n(n−1)/2 unordered sessions. With two of those n acting as reflectors, n−2 clients each have two sessions, and the reflectors have one between them: 2(n−2)+1 = 2n−3.

| Total speakers | Full mesh | Stated two-reflector design |
| --- | --- | --- |
| 8 | 28 | 13 |
| 30 | 435 | 57 |
| 120 | 7,140 | 237 |

Exclude external peers, additional reflection layers and any extra client sessions. These counts describe logical BGP/TCP relationships, not physical cables, paths, per-family sessions or twice-counted neighbour-table entries. Fewer sessions do not automatically mean equivalent route visibility, diverse exits or a sufficient reflector failure design.

### 20.2 — Stop at the first deciding difference

Use the chapter's stated FRR comparison order, eligible candidates and equal attributes before AS-path length. With LOCAL_PREF 100 on both, A's length 3 wins over B's length 4. B's lower MED, 10 versus A's 50, does not undo an earlier deciding difference. MED comparison also has its own scope rules; it is not a global latency score.

Raise B's LOCAL_PREF to 200 and B now wins before AS length is considered. If B's next hop cannot be resolved under the applicable rules, B is ineligible; its attractive LOCAL_PREF cannot repair that failure. Inspect eligible candidates, the implementation's decision reason and installed forwarding. Do not generalise this ordered worked example to every optional best-path knob, or erase the chapter's recorded deterministic-MED experiment that did not establish the expected arrival-order independence.

### 20.3 — The reflector's viewpoint

When earlier policy attributes tie, a reflector's IGP cost to a next hop may favour an exit that is farther from a client. Advertising only that best path can hide the client's preferred alternative. First prove that this stage actually decides the route; different LOCAL_PREF values, for example, can make IGP proximity irrelevant.

Topology-aware reflector placement can align views but changes deployment and failure considerations. Optimal route reflection evaluates from a selected client or group perspective, subject to implementation and design. Add-path can advertise additional selected alternatives so clients have more choice, at extra path/update cost; it does not automatically send every useful path or apply ORR's viewpoint. Compare actual advertised candidates, client choices, traffic paths and failure behaviour before choosing a remedy. These mechanisms address related symptoms with different state and operating costs.

### 20.4 — Diagnose repeated Active state

Start with timestamps and the correct neighbour, source address, family and VRF. Check the route to the peer and its reply to the configured source, not merely a ping from an arbitrary interface. Capture whether TCP SYNs leave, reach the peer and receive an answer. Check TCP/179 filtering, control-plane policing, listening/session configuration, TTL/GTSM scope and the configured TCP authentication at both ends.

If TCP completes, inspect OPEN exchange and NOTIFICATION/reset reasons: AS numbers, capabilities and other session parameters now become relevant. Distinguish a connection that never completes from one that reaches OPEN and is rejected. Consult both endpoints; one side's Active label cannot localise a drop. Save the failed exchange before changing configuration, then verify Established, negotiated families, accepted routes and the controlled service. Established resolves the session problem, not every forwarding obligation.

### 20.5 — A route server is a messenger

Let participant P originate a prefix through non-forwarding route server RS to receiving border B, which advertises internally to I. In the ordinary exchange design, P's advertisement identifies P's forwarding address as next hop. RS passes that participant next hop to B; it must not substitute its own non-forwarding address. B resolves P across the IXP service.

Under the chosen border next-hop-self design, B advertises its reachable internal loopback to I. I recursively resolves B through the underlay. The data path is **I → B → P**, with any intervening underlay hops; it does not traverse RS. If an internal reflector relays the advertisement, that does not insert the reflector into the packet path. Verify exchange neighbour resolution, underlay delivery and return traffic. B does not need a separate bilateral BGP session with P merely to forward a route received via RS.

## Chapter 21 — BGP II: policy, scale and control

### 21.1 — Translate the customer contract

Treat this as an implementation and acceptance exercise. A defensible submission selects two exact commercial images, documents their supported schema and supplies complete attached policies. **The guidance here translates the logic into IOS XR RPL and Junos policy terms; it is not a pair of qualified, paste-ready configurations.** No commercial parser or device execution is supplied by this answer. Pin the exact release/build and hardware before filling the command-level submission; do not replace that field with “latest”.

First define the result independently of syntax. Import only IPv4 unicast from the named AS 64501 customer. Require exactly 203.0.113.0/24 and a nonempty AS sequence consisting solely of 64501 repetitions. Reject Invalid origin validation; this lab's contract does not equate NotFound with Invalid. Retain only permitted requests: large communities 64500:100:1/2/3, 64500:200:0 and 64500:201:64496/64498; preserve the specified NO_EXPORT, NO_ADVERTISE and NO_EXPORT_SUBCONFED standard communities. Remove other received communities, including forged internal provenance and extended communities. Then assign 64500:1:1, 64500:2:11 and LOCAL_PREF 200. Reject every unauthorised route.

| Contract stage | IOS XR RPL translation | Junos translation |
| --- | --- | --- |
| Route scope | Named exact prefix-set and AS-path-set; reject nonmatching inputs | Exact route-filter plus named AS-path match in the authorised term |
| Validation gate | Initial Invalid branch drops | Initial Invalid term rejects |
| Authorisation | Conditional branch admits only the conjunction of prefix and path | Both conditions in the authorised term; no later unconditional accept |
| Sanitisation | Preserve allowed values and remove the rest with family-specific operations before assigning tags | Community definitions/actions for each family; explicitly continue only where needed |
| Trusted attributes | Set local preference and fresh large-community provenance in the authorised branch | Set local preference and add fresh large-community provenance in that term or a guarded continuation |
| Termination | Explicit intended accept/drop on every branch; account for RPL attribute-setting acceptance and nested apply | Terminal accept for authorised input and final reject; inspect the entire policy chain |
| Attachment | Inbound policy on the customer's intended neighbour/address family | Import policy on the intended neighbour/group with the intended family and inherited policy checked |

Write the AS-path rule as an **ASN sequence predicate** first. A raw character regex that accidentally matches 164501 or permits a foreign ASN is not equivalent. Verify the selected engine's anchoring, ASN tokenisation and treatment of AS sets/confederation segments; reject those forms unless explicitly authorised. Similarly, one wildcard community deletion must not be assumed to cover every community family. Junos represents large values with its `large:` notation; RPL has distinct large-community operations. Preserve allowed values without retaining a forged classification. Primary syntax references: [Cisco RPL command reference](https://www.cisco.com/c/en/us/td/docs/routers/asr9000/software/asr9k-r6-7/routing/command/reference/b-routing-cr-asr9000-67x/b-routing-cr-asr9000-67x-chapter-01010.pdf) and [Junos community policy guide](https://www.juniper.net/documentation/us/en/software/junos/bgp/topics/topic-map/routing-policies-communities.html). Check the corresponding documentation for the chosen release as part of the submission.

Minimum test inputs are: exact /24 with one 64501; the same with repeated 64501; Valid /25; Invalid /26; exact /24 with foreign transit ASN; empty path; authorised route carrying forged provenance; authorised route with a permitted action plus an unsupported action; NotFound under the stated policy; and a missing/misattached import policy. Predict the decision and **complete output attributes** for each. Test export and community carriage internally, then external egress removal. Retain parser/commit output separately from observed receipt, acceptance, selection, installation and packets. A syntax translation earns no runtime acceptance until those records exist.

### 21.2 — Valid is not the customer contract

The fixture authorises origin AS 64501 for 203.0.113.0/24 with maximum length /25. Both that /24 and a contained /25 can therefore be Valid, but the original customer prefix filter permits only the exact /24. The /25 fails a separate authorisation gate. Broadening the customer filter to the intended /25s can admit them without changing the validation data, assuming path and other checks also pass. A /26 remains Invalid under that fixture.

Compare the old and new accepted sets, selected routes and the **local, neighbour-specific advertised route set after export policy**. Seeing the /25 in Kestrel's intended export is the relevant export observation. Its absence from a downstream router's RIB is inconclusive because that router may reject it. A service test adds forwarding evidence but cannot replace inspection of what was offered to an external neighbour. Restore the original filter and verify the extra exports disappear.

### 21.3 — Make prepend requests specific to the upstream

For one constructed scheme, allocate 64500:1101:N to transit A, 64500:1102:N to B and 64500:1103:N to C, where N is **1, 2 or 3 extra copies**. Publish which current upstream each ID denotes; do not infer it from a device hostname. Permit these requests only on authorised customer ingress and assign provenance independently.

Within one upstream, choose the largest permitted N when requests conflict. Requests for different upstreams apply independently. Strip unsupported N values, unknown upstream IDs and all forged internal tags; record that this policy strips invalid requests rather than rejecting an otherwise authorised route. A request for two extra copies gives three local-AS copies on ordinary external export when the normal one is included. Confirm actual received AS paths; a vendor's prepend count must match this definition.

On each egress, apply only its request and remove internal/action tags before advertisement. After an acquisition, document an explicit old-to-new mapping, authorise it only for the named legacy customers, and choose one precedence rule—for example, a new-format request overrides the old one for that upstream, then largest N wins within that format. Never add both blindly. Run dual recognition for an agreed interval, observe usage, communicate retirement through the normal customer process, then remove the old scheme under a rollback plan.

### 21.4 — A recovered cache is only the first stage

First verify fresh validation records, serial/session state and route validation classification. Then establish whether the previously rejected path is still retained as pre-policy input. If it is absent, a policy re-evaluation alone cannot invent it; determine whether negotiated route refresh can obtain it. If present, prove whether the validation change actually triggered import re-evaluation on this implementation.

Follow the route through acceptance, BGP selection, system-route selection, next-hop resolution, installation and service. A competing preferred path can explain an unchanged FIB even after acceptance recovers. Preserve logs and timestamps before forcing recovery. Use the least disruptive supported refresh/re-evaluation action justified by the evidence; reset the session only if required and authorised by the change plan. The chapter's retained FRR results include failed automatic recovery cases, so a restored cache connection is not evidence that all rejected routes returned automatically.

### 21.5 — Forecast a shared table limit

The starting count is 840,000 + 190,000 = **1,030,000**. Under the question's deliberately simplified model, N(t) = 1,030,000×1.07^t. Equality with 1,400,000 occurs at ln(1,400,000/1,030,000)/ln(1.07) = **4.5362 years**; the model exceeds the limit immediately afterwards. At the annual samples, year 4 gives about **1,350,120**, while year 5 gives **1,444,628**, so year 5 is the first sample above it.

An eighteen-month lead time puts the latest modelled decision at 4.5362−1.5 = **3.0362 years**, approximately 36.43 months from year zero. Completion exactly at exhaustion leaves no reserve; choose an earlier operational trigger for growth uncertainty, installation limits and procurement risk. Hardware can consume different entry widths for IPv6, partition resources by family, share tables with other functions and install multiple next-hop/backup objects. Measure actual consumption and failure behaviour before using this one-entry-per-prefix model for purchasing.

## Chapter 22 — VRFs, redistribution and leaking

### 22.1 — Add a fourth tenant completely

For a constructed CUST-D, allocate 10.104.0.0/24 and tenant RT 64500:1004. Give its VPN routes an appropriate distinct RD in the deployment's RD plan. Add the VRF, interfaces/attachments, addressing, routing instance and source-of-truth owner. Export only its authorised local prefix under 1004; import 1004 and service RT 64500:9000. Add 1004 to SERVICES' permitted tenant imports and return-route checks. Preserve the restriction against re-exporting imported tenant routes under the service RT.

Extend DNS/NTP and source-validation rules for D without authorising tenant-to-tenant forwarding or arbitrary service access. Include default-route detours, service-host forwarding, route withdrawal, interface recovery, counters, monitoring, inventory and rollback. The logical RT change does not by itself configure any of those packet controls.

With three tenants there are 3×2 = six directed cross-tenant denial cases; four tenants give 4×3 = **12**, adding six. Testing UDP DNS, TCP DNS and UDP NTP once per tenant adds three D service cases, taking that basic transaction set from nine to **12**. Those counts are a minimum matrix, not a complete security test count. Test allowed requests and their replies, denied traffic, unexpected exports and failed return routes.

### 22.2 — Follow withdrawal across two borders

Construct borders X and Y between domains A and B, with prefix P genuinely originating in A. At time zero, X and Y can export P into B. If imported copies are allowed to return to A without trustworthy origin classification, B's copies can become apparent alternatives when A's original P disappears. Record which router receives each withdrawal first and which replacement is eligible and preferred.

A possible bad timeline is: original withdrawal; X selects a returned copy through Y; Y retains or selects a returned copy through X; both forwarding next hops point towards each other until one candidate is invalidated. A forwarding loop requires those mutually dependent routes to be installed concurrently, plus usable next-hop resolution and protocol/policy behaviour that allows the feedback. Some implementations or topologies reject the candidates, select another path, or produce a blackhole instead. State those assumptions before drawing arrows.

Prove prevention by restricting prefix/protocol boundaries and rejecting re-entry of an origin class, then test withdrawal and restoration at both borders. Capture route source, tags, preference, recursive next hops and packets with timestamps. A diagram of two redistribution commands alone does not establish either a loop or its absence.

### 22.3 — Carry provenance across unlike attribute systems

Define an internal origin class such as `branch-static-authorised`, with an owner and permitted prefix set. At the first trusted boundary classify from interface/neighbour/protocol and prefix authorisation; do not trust a tag merely because its value looks internal. An OSPF external route tag, a supported IS-IS prefix administrative tag and a BGP community are different encodings with different scope and propagation behaviour.

Specify a mapping at each redistribution boundary, including route types, tag widths, supported TLVs, defaults and failure actions. Verify that the chosen releases export, retain and match the required attribute; an OSPF intra-area route does not acquire an external route tag just because the policy wishes it had one. If a boundary cannot carry the classification reliably, use explicit prefix/source policy or redesign it rather than pretending the label survived.

Strip or reject external claims to internal provenance, then assign trusted classification after authorisation. Use the class to prevent re-entry to the originating domain and retain explicit final rejection. Test absent, forged, truncated and unknown values as well as withdrawals. Observe actual advertisements and selected routes at each hop; a policy name containing “loop prevention” is not evidence.

### 22.4 — Three ways to serve overlapping tenants

| Design | How the reply stays unambiguous | Principal trade-offs |
| --- | --- | --- |
| Separate tenant service contexts/instances behind one logical DNS offering | Each query is processed in a tenant-specific routing/application context, and the reply leaves that context | Strong separation and tenant-aware logs; more instances, listeners and configuration to maintain |
| Stateful translation or an application proxy at the boundary | Allocate unique translated identities, or terminate and originate separate transactions while retaining tenant context | Centralised service is possible; state capacity, failover, ports and tenant-to-translation logs become critical |
| Renumber to non-overlapping client space | The shared table can return to each distinct tenant prefix | Simpler ordinary return routing; migration, dependencies and organisational cost can dominate |

For translation, DNS over both UDP and TCP and any required DNSSEC behaviour still need application tests; translation does not grant access by itself. Preserve enough logs to associate the original tenant and transaction with the translated flow. For separate contexts, a common DNS name or management plane does not mean the replies share an ambiguous routing table. Different RDs distinguish VPN routes but do not, alone, tell one shared IP service which tenant's identical destination address a reply belongs to.

### 22.5 — Prove the service and the boundary

For every tenant, issue a controlled UDP/53 DNS query, a TCP/53 query and an appropriate UDP/123 NTP transaction to the allowed service. Require a valid application response, not just an open port or transmitted request. Record client context, source, server, timestamps and both directions. Also try an unapproved service port and a forged tenant source where the isolated fixture permits it; inspect the enforcing rule/counter.

Test every ordered pair of distinct tenants and the intended denial points, including a default-route detour through SERVICES. Verify that an unexpected service prefix is rejected at export/import as designed and absent from the relevant FIB; supplement this with packet tests so another route cannot conceal an unintended access path. Then remove one tenant's service return route in the isolated lab: capture the query at the service and the failed reply path, restore the route, and repeat the same transaction successfully.

Keep the local Linux VRF/static-route exercise distinct from the unexecuted two-PE VPN/MPLS fixture. Local packet isolation does not prove RD/RT signalling or label forwarding. A complete submission contains predicted results, observed results, the precise environment, failed cases and restoration—not a list of commands assumed to have worked.


## Chapter 23 — Multicast

### 23.1 — Count copies on the named link

Six separate 20 Mb/s unicast streams require 120 Mb/s of stream traffic on a source-facing uplink that carries all six. That exceeds a 100 Mb/s link before headers or competing traffic. It occupies 0.12% of a 100 Gb/s link before those additions, so capacity alone is a weak reason to add multicast there. One multicast copy needs 20 Mb/s on that same uplink: 20% of 100 Mb/s or 0.02% of 100 Gb/s, under the same byte accounting. Replication farther downstream still consumes capacity on each relevant branch.

Check whether all receivers need the same content at the same time, their locations, application support, loss/recovery behaviour, security and group scope, available multicast operation and hardware, and the actual bottleneck. Headers and bursts make the 20% a starting calculation rather than an admission limit. More bandwidth does not remove an application's need for multicast semantics, and multicast does not turn six different streams into one.

### 23.2 — A shared MAC does not make a shared IP group

IPv4 multicast Ethernet mapping retains the low 23 group-address bits. Both 239.1.0.1 and 239.129.0.1 map to **01:00:5e:01:00:01**; 239.2.0.1 maps to **01:00:5e:02:00:01**. The high bit in the second IPv4 octet is one of the bits discarded by this mapping. There are 28 variable IPv4 multicast group bits and 23 copied bits, so 2^5 = 32 IPv4 groups can share a mapped MAC.

A frame accepted by a NIC or replicated by a bridge has not necessarily been delivered to an application. IP destination, membership/source filtering, socket binding and application handling still matter. Inspect the exact group and source in a capture, the snooping lookup granularity and receiver state. A MAC alias alone proves neither unintended application delivery nor confidentiality.

### 23.3 — Choose the RPF target before judging asymmetry

For an SSM (S,G) tree, inspect the multicast implementation's effective route towards S. For the ASM shared-tree state, inspect the route towards the RP; after source-tree state exists, the source-facing check can differ. Identify the state and forwarding mode actually handling the packet. In the chapter's FRR fixture, use its effective PIM nexthop lookup and state, rather than substituting an unrelated route display.

Consider constructed unicast paths where packets from S arrive on interface A but the multicast RPF lookup towards S selects B. Ordinary unicast could work with this asymmetry while this multicast packet fails its upstream check. Correct the intended route, multicast-specific policy or source path after checking the topology. Asymmetry is not universally fatal: it matters when the arriving interface and the applicable multicast RPF rules disagree. Verify the outgoing interfaces and receiver delivery as well as the incoming check, then restore the deliberately changed route.

### 23.4 — RP resilience is a discovery and state test

For an invented four-PoP ASM service, place RP capacity in distinct failure domains, specify how every router discovers the mapping, and choose a supported redundancy method with consistent group scope and required source-state exchange. A static mapping to one address is not a complete availability design. Anycast-RP variants have protocol-specific requirements; validate the selected construction instead of combining unrelated examples. SSM channels do not need an RP, but receivers and applications must support source-specific membership.

Establish an existing stream and a previously unused group. Fail only the RP attachment while leaving the source-to-receiver transit path intact. Record RP reachability/mapping, Register or Join state, source/shared-tree state, timed sequence-number delivery and new-stream establishment. An existing source-tree stream might continue while a new ASM stream fails; do not score those as the same test. Separately fail a transit link, restore each fault, and repeat membership creation. Set an owner-agreed bound on loss and recovery before testing; the answer supplies a method, not measured convergence.

### 23.5 — Make 50 microseconds a measurable requirement

First define the requirement: for matching sequence numbers, is the absolute difference between arrival times at two receiver interfaces at most 50 μs, or is each feed required to meet a one-way source-to-application limit? Those are different tests. For an illustrative arrival-difference test, allocate at most 30 μs to differential path/queue delay, 10 μs to differential receiver processing and 10 μs to total measurement uncertainty. These are invented design allocations, not established capabilities. If timestamps are taken at interfaces, processing after that point lies outside the measured boundary and must be assessed separately.

Budget synchronisation offset, timestamp accuracy and calibration together; two clocks each within ±5 μs of a common reference can contribute up to 10 μs of relative error in a worst-case bound. With total uncertainty bounded by 10 μs, a measured difference at most 40 μs supports a true difference at most 50 μs for that sample. A result of 45 μs is inconclusive against that bound, not automatically a pass. Record loss, reordering, duplicates and clock health so that missing pairs cannot disappear from the statistics. Agree whether the limit applies to every sample in a finite trial or a stated percentile; do not turn either into an unlimited guarantee.

Test aligned feeds under the agreed load, bursts, path failure/restoration and receiver stress. Verify physical diversity, queue treatment, source sequencing and socket/application behaviour. Collect captures at the chosen boundaries and an uncertainty statement. A mean below 50 μs and two different interface names are insufficient evidence of the promised bound and diversity.

## Chapter 24 — The anatomy of an ISP

### 24.1 — Follow setup and the established flow separately

Draw the subscriber attachment through access/aggregation to the BNG, then the selected core/edge path to a reachable external service. On a fresh session, identify the actual access/session mechanism, subscriber authentication and authorisation if used, address/prefix assignment, policy installation and accounting. The chapter's static topology does not implement all of these services.

For a new hostname lookup, trace the configured resolver and its reply. For a new outbound IPv4 flow requiring CGN, trace the mapping, port allocation, policy and stateful return path. IPv6 need not use that IPv4 translation path. An already established flow may continue during a DNS or AAA outage, subject to caching, session lifetimes and local policy; new sessions or lookups may fail. Conversely, losing the forwarding path or required translation state can break existing traffic. Give each dependency an owner and test new-session creation and a continuing transaction separately.

### 24.2 — Equal exposure totals, different failures

Lab 25's graph attaches an artificial population of 50,000 subscriptions to host-sub and 900 business circuits to host-cust. Removing both represented borders disconnects both populations from the model's general transit exits: 50,900 exposed units. Removing the represented PE and BNG disconnects their respective customer populations, also 50,900. A peering connection is not assumed to provide universal transit.

The border pair fails at the external path; the PE/BNG pair fails at customer/service attachment. Different teams, restoration methods, surviving internal connectivity and state may therefore matter even though the sum matches. These are subscription/circuit units, not a count of unique people or a measured outage. The graph has no route policy, capacity, convergence, AAA, DNS or shared-failure model. Compare every tied maximum and add those dependencies before turning the result into an investment ranking.

### 24.3 — The lightly loaded link may be the rescue path

Eight Gb/s on a 100 Gb/s link is 8% utilisation at the stated boundary and interval. Keep the link if its failure/maintenance role, physical diversity or growth justifies it; resize only if the lower capacity meets normal and survivor demand with agreed headroom, packet-rate and burst requirements; remove only if all required services still have acceptable paths and recovery. Average normal utilisation alone settles none of those choices.

Obtain aligned traffic by direction and class, busy-hour/burst distributions, rerouted demand for each relevant fault, shared duct/site risks, latency, service commitments, contract/termination costs and delivery lead times. Compare equivalent cases with the link, a smaller link and no link. Lab 25's connectivity graph cannot supply the missing capacity or price evidence. Give the recommendation a trigger for review rather than labelling an 8% graph “waste”.

### 24.4 — Billable rate and commit are separate inputs

All figures here are fictional GBP per month, excluding VAT and additional costs. With a 10,000 Mb/s commit costing £1,000 and £0.10 per excess Mb/s, the original 12,000 Mb/s billable rate costs £1,200. If peering reduces that billable input to 9,000 Mb/s, transit remains at the £1,000 minimum. At **£100 peering**, the total is £1,100: a £100 saving against £1,200.

If the commit can instead become 8,000 Mb/s at £0.10 per billed Mb/s with that minimum, 9,000 Mb/s costs £900. Retaining the exercise's £100 peering gives £1,000 total and a £200 saving against the original bill. If the chapter's original **£300 peering** price is used instead, the total is £1,200, which breaks even against the original £1,200; at the unchanged 10,000 commit it would be £1,300. State which peering price is being held constant.

These calculations accept the billable rates as inputs. They do not prove how percentile billing changes from an average traffic reduction, that the commit can be renegotiated, or that peering replaces full transit during failure. Include ports, cross-connects, routing/operations, capacity and contractual obligations in the actual decision.

### 24.5 — Repair the allocation and its reservations

Inside 2001:db8:4000::/36, reserve **2001:db8:4000::/38** for business /48s and **2001:db8:4400::/40** for broadband /56s. The /36 covers third-hextet values 4000–4fff; the /38 covers 4000–43ff and the /40 covers 4400–44ff. They are canonical, contained and disjoint. The originally proposed 4100::/40 would overlap the expanded business block.

The business pool has 2^(48−38) = 1,024 /48s, leaving 124 after 900 allocations before further reservations. That is 12.11% of pool capacity unused, or 13.78% growth relative to the initial 900; label the denominator. Broadband has 2^(56−40) = 65,536 /56s, leaving 15,536 after 50,000. Record infrastructure exclusions, growth, aggregation and allocation ownership. Documentation prefixes illustrate a plan and must be replaced with the operator's legitimate allocation for deployment.

## Chapter 25 — MPLS foundations

### 25.1 — Read the label in its receiving context

For the chapter's constructed transport/service walk:

| Link | Stack, top first | Expected next action |
| --- | --- | --- |
| PE1 → P1 | 1002 (S=0), 24002 (S=1) | P1 uses its incoming-label context for 1002 and swaps the top to 2003. |
| P1 → P2 | 2003 (S=0), 24002 (S=1) | P2 applies the advertised PHP action for this transport FEC. |
| P2 → PE2 | 24002 (S=1) | PE2 interprets its service label and forwards in the resulting service context. |

The values identify entries in the relevant receiving label spaces; they are not globally interchangeable addresses. With IPv4 explicit null for that transport FEC, the last link instead carries **0 (S=0), 24002 (S=1)** under the supported nested-label construction. PE2 removes the explicit-null top and then processes the service label. Label 3 is the signalled implicit-null request and is not put on the wire. Use label 2 where the corresponding IPv6 explicit-null semantics apply; the chosen transport FEC and implementation must match. Preserve the inner label and verify TTL/TC treatment rather than assuming that changing PHP only changes a printed number.

### 25.2 — Four labels and two tags

The stated 1,514-byte Ethernet-frame limit **excludes FCS**. Subtract 14 bytes of base Ethernet header, two 4-byte VLAN tags and four 4-byte MPLS entries: 1,514 − 14 − 8 − 16 = **1,476 bytes** for the complete inner IP packet. With base IPv4 and ICMP Echo headers, the echo data can be 1,476 − 20 − 8 = **1,448 bytes**. A VLAN tag is additional to the base header in this accounting.

If the same numeric frame limit **includes FCS**, subtract another four bytes: **1,472 bytes IP**, **1,444 bytes echo data**. No IP options, extra service header or other encapsulation has been included. A device's MTU command may count a different boundary. Prove the chosen maximum and a just-over-boundary case in both directions, with fragmentation controlled and the active/protection stacks recorded.

### 25.3 — LDP Up is one dependency

Three possible failures are: the underlay resolves the transport FEC along a path without usable label forwarding; a label is learned in the LIB but the required incoming/outgoing action is absent or wrong in the data plane; and the transport reaches the egress but the service label, VRF/attachment, return path or MTU is wrong. An established LDP session does not distinguish these cases.

Record the selected route and adjacency, advertised/received mapping for the FEC, installed LFIB action and interface counters, then capture or probe the service using the actual customer source and size. Check Linux MPLS forwarding prerequisites in the reference fixture and the precise hardware/release prerequisites elsewhere. Stop at the first contradicted prediction. Avoid resetting a healthy signalling session merely because it is the most visible green status on the screen.

### 25.4 — Test synchronisation with a usable alternate

Use an isolated topology with two underlay paths and working labelled service traffic. Establish the baseline, then recover one link while delaying or preventing its required LDP readiness. Predict the IGP cost/selection and labelled packet path with synchronisation enabled. A high metric can keep the recovering link unattractive when a valid alternate exists; it is not an ACL and cannot invent an alternate when every other path has failed.

Measure loss with sequence numbers and timestamps, inspect both route and label state, release the delay, and verify that the link returns to its intended metric and carries service traffic. Repeat restoration and, if appropriate, compare the same bounded fault without synchronisation in the isolated fixture. Define the service loss limit and rollback trigger first. Restore both the injected LDP fault and the original synchronisation configuration; retaining only a successful IGP ping leaves the service untested.

### 25.5 — Return a repaired path to service

Require clean physical/interface state, the intended underlay route/adjacency, correct LDP identity/session and relevant label mappings, installed forwarding actions, and working customer traffic in both directions at the agreed sizes and rates. Check service isolation and error/drop counters against a recorded baseline. Verify recovery after the same fault and that traffic uses the intended normal path without a stale policy or cached endpoint limitation.

Specify a finite observation period and service criteria with the owner. Preserve the original fault and restored state, save the intended configuration through the platform's approved process, verify persistence inputs and hand over residual risks. A quiet error counter without offered traffic is not a clean traffic test; one successful small ping is not acceptance of every frame size or queue class.

### 25.6 — Select visibility and QoS policy independently

Uniform TTL processing can expose more of the provider path to customer TTL expiry; pipe/short-pipe constructions provide different boundaries for propagation and egress handling. Select the precise supported TTL behaviour for the managed service and verify TTL expiry and OAM from both customer and provider perspectives. Hiding hops does not encrypt traffic or remove the need to troubleshoot the transport.

For QoS, separately define how customer markings map to MPLS TC, which queues enforce the contract, and whether egress treatment follows the outer transport treatment or the inner packet's marking in the chosen pipe variant. A plausible service may preserve customer markings while applying provider classes, but that needs classification, scheduling and egress tests. TTL and QoS models are related terminology, not one switch whose setting proves the other. Record normal and congestion/failure observations for the exact platform/release.

## Chapter 26 — Traffic engineering and segment routing

### 26.1 — Two paths do not double survivor capacity

Place the 8 Gb/s sensitive class on the 10 Gb/s Manchester path and 6 Gb/s flexible class on the 10 Gb/s Birmingham path: 80% and 60% nominal utilisation. After either path is lost, 14 Gb/s competes for 10 Gb/s, leaving a 4 Gb/s shortfall. Protecting 8 leaves at most 2 of the flexible 6 before overhead and headroom. With a separate 1 Gb/s headroom allowance, flexible traffic can receive at most 1 Gb/s.

The 9 ms Birmingham path can still violate a sensitive service whose accepted delay limit is below 9 ms, even if rate admission succeeds. A priority label cannot shorten propagation. Specify what is shed/deferred, classify and enforce it, and test service loss and delay under the fault. Quote neither the 20 Gb/s normal sum nor an active policy as the failure-service guarantee.

### 26.2 — Count directed class LSPs

Each of 50 PEs needs 49 remote destinations. That gives 50 × 49 = **2,450 directed primary LSPs** for one per-destination class, or **4,900** for two independently provisioned classes. Reversing a source/destination pair counts another directed LSP.

That is not a count of RSVP state entries at every hop, physical paths, or protection tunnels. Per-LSP backups, shared bypasses, path length and implementation change those totals. Draw the protection scheme before multiplying by two again. An SR design changes where policy/forwarding state is held; it does not eliminate every scaling dimension represented by these services.

### 26.3 — Index 23 across two SRGBs

For this simple contiguous SRGB mapping, index 23 corresponds to **16,023** in a block beginning 16,000 and **24,023** in one beginning 24,000. The sender must use the applicable receiving router's mapping when imposing/swapping the label for that prefix segment. An identical prefix-SID index does not require an identical label at every hop.

Verify advertised SRGB ranges, index support, prefix/algorithm and installed action. Do not apply this arithmetic to a locally significant adjacency SID or BSID merely because it is another MPLS number. Those labels have their own allocation and owning context.

### 26.4 — Require a particular transatlantic link

Resolve the business constraint first: a named physical circuit, a provider path, a jurisdiction or an operational failure domain are different requirements. To require a particular adjacency in a supported SR-MPLS construction, steer to its owner and include that adjacency's SID, followed by the required endpoint/service resolution. A node SID for the far end alone can permit another path. Obtain SID scope, current allocation and depth/MTU limits from the actual domain; this answer does not invent deployable label numbers.

Specify the failure policy. A protected adjacency that repairs over a different link may violate a literal must-use-circuit condition. Likewise, fallback to ordinary shortest-path forwarding can restore reachability while violating the path contract. Require verified acceptable alternates or an explicit fail-closed outcome, and test link failure, withdrawal, controller loss, restoration and the observed packet path. Capacity and delay acceptance remain separate from enforcing the waypoint.

### 26.5 — A waypoint differs from a required adjacency

On the chapter's London–Manchester–Leeds–Birmingham ring, a node segment to Birmingham followed by one to Leeds permits the current shortest path between those nodes. If Birmingham–Leeds fails but Birmingham remains reachable, that second segment may take Birmingham–London–Manchester–Leeds. The repeated London visit is possible because the packet is now executing a later segment; confirm the actual forwarding and remaining constraints.

A sequence reaching Birmingham and then requiring its **unprotected** Birmingham–Leeds adjacency cannot use that failed adjacency. Depending on the tested implementation, the policy may become unusable or remain apparently active while packets drop. Check both policy state and packet delivery. If Birmingham itself fails, both constructions lose their required waypoint unless a separately authorised alternative policy changes the requirement. Record adjacency protection and fallback explicitly before comparing results.

### 26.6 — An SR acceptance contract

Record chassis, forwarding hardware, NOS, licences, IGP/SID capabilities, algorithm and allocation ranges. Test supported label depth and effective MTU for normal and repaired packets; verify SRGB mapping, adjacency/BSID ownership, policy selection and customer steering. Include ECMP, TTL/TC, counters/OAM and required classes under the agreed traffic mix.

Inject link/node failure, an unavailable required SID, stale/withdrawn policy, controller loss and restoration in a controlled pilot. Compare advertised state, selected policy, installed forwarding and observed service path/loss/delay. Define whether fallback is allowed and whether it preserves the service contract. An acceptance record contains measured criteria, failed trials and rollback, not only a list of commands accepted by a parser. The chapter's Linux/FRR observations do not certify the commercial matrix.

### 26.7 — Preserve the service during RSVP-to-SR migration

Inventory what the RSVP service supplies: explicit path constraints, bandwidth admission/priorities, pre-emption, protection, QoS and operational visibility. Map each to a supported SR mechanism or an explicit replacement admission process. Moving path instructions into packets does not automatically recreate RSVP bandwidth reservations.

Establish coexistence and allocation rules, an isolated pilot and a small reversible traffic unit. Compare equivalent normal/fault/maintenance cases, including class enforcement, delay and capacity, with agreed success and rollback thresholds. Move selected traffic, verify the actual path and restoration, observe for the agreed period and retain the old service until acceptance. Remove old LSPs and dependencies only after checking shared users. A controller design must specify stale-state handling and who admits new demand if the controller is unavailable.

## Chapter 27 — SRv6

### 27.1 — Split the SID at declared bit boundaries

With the stated 64-bit locator, 16-bit function and 48-bit argument layout, expand **2001:db8:4500:0023:0100:0000:0000:0000**. The locator is **2001:db8:4500:23::/64**, the function is hexadecimal **0100** (decimal 256), and the last 48 argument bits are zero. The fourth hextet belongs to the locator under this layout; its visible position does not make it a universal function field.

The allocation register must identify the endpoint owner, locator route, behaviour attached to function 0100, permitted arguments, tenant/service binding and version. The address alone does not reveal whether the locally installed behaviour is End, End.DT4 or something else. Verify both the route towards the locator and the endpoint's local SID entry.

### 27.2 — Four /48s and an infrastructure reservation

The canonical aggregate **2001:db8:4500::/40** spans third-hextet values **4500–45ff** and contains 256 /48s. One defensible paper allocation assigns **2001:db8:4501::/48**, **4502::/48**, **4503::/48** and **4504::/48** to four regions (with the unchanged 2001:db8 prefix). Reserve **2001:db8:45f0::/44** for infrastructure; it covers sixteen /48-sized blocks, 45f0–45ff, and overlaps none of the four regions. Mark the other space unallocated rather than silently using it.

Each regional /48 can contain 65,536 /64 locator prefixes before local exclusions. The lab's separate /64 endpoint locators illustrate a smaller construction, not the regional allocation policy. Specify summarisation, failure boundaries, owner and SID layout before choosing a production prefix size. These documentation addresses are teaching allocations, not an operator's assigned address space.

### 27.3 — Compare the same two byte boundaries

For five stored full SIDs, no TLVs and full encapsulation, the overhead is 40 + 8 + 5 × 16 = **128 bytes**. With a 1,500-byte inner IP packet the outer packet is **1,628 bytes**. Overhead/inner size is **8.53%**; overhead/outer size is **7.86%**. On a 1,500-byte outer path, the inner IP budget is **1,372 bytes** under that construction.

Only if the selected compressed instruction sequence fits the supported construction entirely in the outer destination with no SRH or additional headers is the added IP overhead **40 bytes**. The outer packet is then **1,540 bytes**, with ratios **2.67%** of inner and **2.60%** of outer size; a 1,500-byte outer path permits **1,460 inner bytes**. Do not apply the 40-byte result to arbitrary compressed lists. Different blocks, service functions, arguments and supported behaviours can require more containers/headers. Neither calculation includes Ethernet framing.

### 27.4 — Count the service instruction too

With a 32-bit Locator-Block and 16-bit equal-length compressed identifiers, the simple capacity is floor((128−32)/16) = **6**. Six transport instructions plus a separate service instruction require **7** such slots, so they cannot all occupy that one container. With 48/16 and 64/16 layouts the corresponding capacities are **5** and **4**.

At least another supported encoding element is needed in the seven-slot example; choose the exact standard flavour, block transitions, service behaviour and arguments before counting its bytes. For example, a service instruction might be uncompressed or have different requirements, so “two containers” alone is not a complete packet format. A supposed mandatory empty terminator must come from the selected procedure, not an automatic subtraction of one slot from every SRv6 scheme. Validate actual advertisements and the resulting wire image against RFC 9800 and the implementation.

### 27.5 — A five-year comparison that can change its conclusion

Use the same required sites, capacity, availability, service features and support period. The following **invented, undiscounted GBP thousands** illustrate a cost worksheet; they are not quotes or a procurement recommendation. Assume all setup costs at the start, five full years of recurring payments, no tax/VAT, inflation, financing or residual value.

| Incremental cost | Retain/extend SR-MPLS | Migrate to SRv6 |
| --- | ---: | ---: |
| Hardware/licences and integration at start | 120 | 180 |
| Training/migration at start | 20 | 40 |
| Annual support, operation and capacity allowance | 50 | 42 |
| Five-year total | **390** | **430** |

The second option starts £80k higher and saves £8k annually, so under these inputs it reaches simple cost parity only after ten full years, beyond the five-year horizon. If its annual cost were £30k instead, its five-year total would be £370k and parity would occur after four years. Equal capability has not been proved by either arithmetic result.

Obtain dated cost and payment schedules, the actual packet/MTU and hardware performance, failure/service tests, migration risks, skills and vendor support terms. Add sensitivity to those uncertain inputs and, for a real investment decision, use the organisation's approved discount/cash-flow method. Present the lower-cost feasible option conditionally; do not price an unqualified design as though it already met the contract.

### 27.6 — Qualify the packet on the actual forwarding hardware

Record the exact hardware, ports, NOS and enabled behaviours. Exercise required locator/SID layouts, supported flavours and list lengths, encapsulation/reduced modes, decapsulation/tenant bindings, ECMP and service steering. Test smallest and largest required packets, MTU/ICMP handling, line-rate or agreed offered-load performance, packet rate and concurrent features. Watch for punts or recirculation constraints; do not infer ASIC capacity from a Linux namespace result.

Include boundary filtering of SID destinations, including traffic without an SRH, negative tenant-delivery tests, resource exhaustion limits and failure/restoration paths. A denied ping is insufficient isolation evidence if an unauthorised request still reached the tenant. Capture on the receiving side, inspect counters and verify customer service after recovery. State untested combinations explicitly.

### 27.7 — Place the SR-unaware firewall inside a service contract

Select a supported proxy behaviour that presents the traffic form the firewall understands and reinstates the required SR context after processing. Document the proxy's interfaces, state/cache scope, tenant binding and return steering. For a stateful firewall, determine how forward and reverse flows meet the appropriate state and how NAT, fragments, generated packets and failover affect that association.

Test authorised and prohibited flows, service/proxy failure, stale state, asymmetric return paths and restoration. Decide fail-open versus fail-closed behaviour with the service/security owner and verify it; a bypass that restores connectivity can violate the inspection requirement. Keep a reversible pilot and explicit rollback triggers. The cited SRv6 Service Programming document is an active Internet-Draft, not a published RFC as checked on 25 September 2026; treat its behaviours and implementation support accordingly.

## Chapter 28 — MPLS L3VPNs

### 28.1 — Separate customer, transport and service headers

CE1 sends an ordinary IP packet to PE1 on its customer attachment. PE1 classifies it into the intended VRF, selects the remote route and imposes the service label advertised for that route plus the resolved transport stack. Core routers act on the relevant top transport label. With the diagram's PHP construction, the penultimate router removes the final transport label, so PE2 receives the service label and uses its installed action to reach the customer forwarding context/attachment. PE2 sends ordinary IP towards CE2.

With supported explicit null, PE2 first processes that transport label above the service label. Check stack-bottom bits and installed pop/swap/lookup actions on the exact nodes; a per-prefix or per-next-hop service action need not perform exactly the same lookup as a per-VRF label. The RD and RT were route-distribution information, not additional headers in the customer's packet. Draw the return path independently: labels and route policy can differ in that direction.

### 28.2 — Label scale has an allocation policy

For the stated model, 300 VRFs × 150 labelled routes each = **45,000 per-prefix service labels**, compared with **300 per-VRF service labels** if one label is used for each relevant VRF in that scope. Both designs still need the underlying customer routes and their forwarding actions; fewer labels do not remove route state. A per-VRF action typically needs a lookup in that VRF after identifying it.

Record whether the count is per PE, address family or entire network; then include transport, adjacency/next-hop, protection and other label consumers. Measure actual resource allocation and forwarding behaviour on the target, including update and failure load. Do not compare these totals only with the 20-bit label namespace and conclude that hardware capacity is proved. The chapter's FRR reference supports different allocation choices and does not provide a per-prefix hardware-scale benchmark.

### 28.3 — Hub policy with one deliberate exception

One model uses hub-export RT **64500:2911** and spoke-export RT **64500:2912**. Each separately isolated spoke VRF imports the hub RT; the hub imports the spoke RT. The hub service must route the intended traffic through its inspection boundary, with separate pre/post-inspection contexts and correct return steering where needed. If two spokes share one local VRF, local routes can bypass the intended hub regardless of the RT design.

For an authorised direct exception between spokes 1 and 2 only, add RT **64500:2921** solely to spoke 1's approved export prefixes and **64500:2922** solely to spoke 2's approved prefixes. Spoke 1 imports 2922 as well as 2911; spoke 2 imports 2921 as well as 2911. The other ten spokes import neither exception RT. Export filters must prevent re-exporting learned hub or unrelated spoke routes with an exception RT. Use the full RT values with the unchanged 64500 administrator in each configuration.

Route specificity and policy must make the selected exception path direct only for those authorised destinations; the default/other routes must still follow the hub. Inspect route import, selected forwarding and return paths, then test direct S1↔S2 traffic, ordinary hub-inspected traffic and prohibited bypasses involving the other spokes. Decide how failure of the direct exception behaves: hub fallback, outage or another approved path. RTs express route policy; they do not by themselves prove inspection or security acceptance.

### 28.4 — Price and size the replicated Internet state

Let R be the measured accepted Internet-route count per address family and V the number of Internet-bearing customer VRFs **per PE**. A simple fully replicated construction across eight PEs starts at **8 × V × R logical VRF route entries**, subject to the implementation's sharing and actual distribution. Count VPN/BGP path copies, multiple paths, FIB/TCAM, next hops, memory and update/convergence work separately. R is a dated input, not a fixed constant to memorise.

For illustration only, V=20 and R=1,000,000 yield 160,000,000 logical copies across the eight PEs before those qualifications; this is neither today's Internet size nor measured hardware use. Compare default-only service, selected routes, a shared Internet context or the requested full-table service against actual customer requirements and isolation. Test resource headroom and churn/failure convergence at the target scale before selling the service. A design that boots with a small synthetic table has not passed that test.

### 28.5 — Choose an inter-AS boundary that the two operators can run

Option A provides a VRF-level IP handoff between the ASBRs. It makes an explicit per-service boundary and can simplify ownership/policy during a merger, at the cost of per-VRF interfaces/routing state and provisioning at that border. Verify scale, route limits, addressing, loops and failure recovery there.

Option C separates end-to-end VPN route distribution from labelled transport reachability between PEs across the AS boundary. It can avoid per-VPN forwarding state on the ASBRs, but requires compatible labelled reachability, next-hop resolution, policy and agreed control-plane/security responsibilities. It is not automatically the best merger choice because it scales a particular state dimension.

Compare the actual service inventory, trust, releases, skills, visibility, failure containment and migration deadline. Pilot a small service with traffic, isolation and both-direction failure/restoration evidence; retain a rollback handoff and label/route-policy records. A phased Option A boundary can be defensible while the combined operating model matures. Choose Option C only when its required capabilities and ownership are demonstrated, rather than assuming that common corporate ownership has already integrated the networks.

### 28.6 — A self-ping and an overlapping subnet

A router pinging an address it owns can terminate locally. It does not prove CE-to-CE transport, remote service-label processing or the customer return path. Use distinct source/destination endpoints beyond the intended attachments and capture the relevant service boundaries. State packet size and protocol as well as addresses.

If two sites in one ordinary routed VPN both use the same /24, a distinct RD can preserve separate VPN advertisements in BGP but cannot make a destination-only IP lookup know which identical address the application meant. Renumbering, explicitly designed translation, separate routing/service contexts or an application proxy may solve a verified requirement, with their own return-path and operational consequences. Do not advertise both prefixes and call address ambiguity solved. Two different customers using the /24 in isolated VRFs are a legitimate, different construction.

## Chapter 29 — L2VPN and EVPN

### 29.1 — Sessions and service relationships are different resources

Basic full-mesh VPLS with 12 PEs has 12 × 11 / 2 = **66 bidirectional PW relationships** for one service. A full mesh of BGP sessions among the same 12 EVPN PEs also has **66 sessions**, but those sessions can carry many service routes and are not PWs.

If those 12 PEs each peer to **two additional RRs**, there are **24 PE–RR sessions**; add one for an RR–RR session if the design includes it, giving **25**. State whether there are other sessions. If the RRs are counted inside the original twelve-device population, the problem's endpoints and arithmetic change. Reflection distributes control information; the forwarding tunnels, replication state and service attachments still require their own capacity and failure design.

### 29.2 — Establish what the cluster actually needs

Ask the application owner and product support authority for supported site count/topology, maximum RTT and loss, bandwidth/storage replication, address/discovery dependencies and version restrictions. Identify quorum voters and witnesses, fencing behaviour, partition outcomes, split-brain prevention and recovery after sites rejoin. Which failures must preserve writes, reads or neither? What is the data-loss/recovery objective, and who owns its validation?

Map broadcast/unknown/multicast limits, MAC movement, gateway ownership and service MTU to the requested Ethernet boundary. A routed inter-site design, fewer stretched sites or point-to-point services may be preferable only if it preserves the verified application requirement and support. A successful layer-2 ping cannot accept a six-site database consistency or quorum design. Plan the application partition/recovery tests with its owner.

### 29.3 — Explain DF without importing the spanning-tree model

An STP-trained engineer recognises the need to prevent duplicate/looped delivery, but an EVPN DF is not simply a root bridge that blocks every other attachment. For a common all-active E-LAN segment, the applicable election chooses which PE forwards overlay BUM towards the CE for the relevant service. Other eligible PEs can still deliver known unicast and participate in load sharing.

Separately explain matching ESI/service membership, split horizon preventing return to the originating ES, and aliasing that lets remote forwarding use eligible ES paths. Single-active mode restricts forwarding differently. Verify the negotiated election procedure/granularity and captures in the selected encapsulation; a DF status line alone does not prove duplicate prevention or failover.

### 29.4 — Investigate the identity behind a repeated MAC

Same MAC, same intended ESI and compatible advertisements from the two attached PEs can be normal all-active multihoming. Confirm the actual CE LAG, LACP identity/member state, type 1/4 information and remote forwarding group. A host move can instead produce changed attachment/ESI, mobility sequence and withdrawal/update behaviour; compare timestamps and the actual move.

An ESI configuration error can make one physical segment appear as two or unrelated segments appear as one. Compare both devices against the attachment inventory. A duplicate host can present the same MAC or IP at unrelated attachments; capture source traffic and inspect endpoint configuration, ARP/ND and duplicate/mobility detection. The route count alone cannot distinguish these cases. Avoid “fixing” normal multihoming by deleting an eligible path.

### 29.5 — VXLAN inner and outer boundaries

With a 1,500-byte inner IP packet, add a 14-byte untagged inner Ethernet header: the encapsulated inner frame is 1,514 bytes before its ordinary link FCS, which is not included here. Outer IPv4/UDP/VXLAN adds 20 + 8 + 8 = 36 bytes, giving a **1,550-byte outer IP packet**. Outer IPv6/UDP/VXLAN adds 40 + 8 + 8 = 56 bytes, giving **1,570 bytes**. These values exclude the outer Ethernet header and FCS.

One preserved inner VLAN tag adds four bytes: **1,554 IPv4** and **1,574 IPv6**. With an untagged 14-byte outer Ethernet header, the corresponding outer frames before FCS are 1,564/1,584 untagged-inner, or 1,568/1,588 tagged-inner. No options or extension headers are assumed. A 1,500-byte outer IP path permits 1,450-byte inner IP with IPv4 encapsulation or 1,430 with IPv6, reduced by four if the inner tag is preserved. Test both active and protection paths, with fragmentation/PMTUD behaviour recorded.

### 29.6 — Migrate a service and keep the exit route

For four sites, record the agreed service, attachment/VLAN mapping, MAC/route limits, MTU, BUM policy, policing, OAM and redundancy. Capture a working VPLS baseline and define an outage window and decision deadline. Qualify the exact EVPN adapter, RRs and transport in an isolated pilot; choose either a coordinated service cutover or a specifically supported interworking construction with one owner per attachment and explicit loop prevention.

Accept only when known delivery, unknown-traffic treatment and broadcast/multicast match the contract; prohibited cross-service traffic stays undelivered; boundary-sized packets pass both ways; and each required attachment/core failure and restoration meets the agreed loss/duplicate/delay criteria. For multihoming, check LACP, ESI, DF, aliasing and split horizon separately using distinguishable flows and direction-aware captures. Lab 30's retained multihoming failures remain failures and are not acceptance evidence for a migration.

Roll back on any unauthorised delivery, loop/duplicate breach, missing required size, missed recovery limit or the decision deadline without a diagnosis. Restore the saved attachment/service configuration and confirm customer transactions, forwarding tables and endpoint recovery, not just the old object names. Retain old service dependencies until the agreed observation period ends; check other users before deleting shared transport. Record untested combinations and an owner for every exception.

## Chapter 30 — Quality of service

### 30.1 — Preserve the distinctions the service needs

One illustrative E-LSP map uses TC6 for control, TC5 for EF, TC3 for AF31, TC2 for AF32, TC1 for AF33 and TC0 for default. Put TC3/2/1 in the same AF3 scheduling queue, with increasingly aggressive discard treatment from AF31 to AF33. This is a proposed domain contract, not a universal mapping or a qualified device configuration. Test the hardware's actual queue/profile and discard semantics.

For a complete example, accept CS6 only from authorised control sources and EF only within the admitted voice envelope. Accept AF31/32/33 only from authorised attachments. Map every other DSCP, including other AF classes and unsupported requests, to default core treatment; record this service choice. Treat TC4 and TC7 arriving at this domain's authorised boundary as default, with a counter for unsupported markings. Prevent customer markings from obtaining control treatment.

Under the selected pipe model, inner DSCP values can remain distinct even where they share TC0 treatment. Define the egress mapping and subsequent trust decision; do not infer delivered QoS from preserved bits. Inspect all DSCP/ECN combinations, MPLS TC, queue counters and loss under congestion. [RFC 3270](https://www.rfc-editor.org/rfc/rfc3270.html) describes the MPLS model; [RFC 2597](https://www.rfc-editor.org/rfc/rfc2597.html) defines AF's within-class drop precedence.

### 30.2 — Allocate the residual resource

Subtract the priority consumption first: 100 − 8 = 92 Mb/s. The ideal backlogged shares are 0.60 × 92 = **55.2 Mb/s** and 0.40 × 92 = **36.8 Mb/s**. The 60:40 ratio applies to the residual service, not automatically to the whole port.

With work-conserving borrowing, no other competing traffic and no limiting child ceiling, one active residual class could use all 92 Mb/s when the other becomes idle. It does not acquire a permanent 92-Mb/s guarantee. Check parent limits, accounting, packet sizes, shaper eligibility and actual scheduler behaviour. If the surviving bottleneck is 50 Mb/s and priority still uses 8, the corresponding shares are **25.2 and 16.8 Mb/s**. Test the service requirement against that failure case as well as normal operation.

### 30.3 — Derive a buffer estimate and test its assumptions

The bandwidth-delay product is 10¹⁰ bit/s × 0.030 s = 300,000,000 bits. Divide by √400 = 20 to obtain **15,000,000 bits**, then by eight for **1,875,000 bytes**, or **1.875 MB decimal**. At 10 Gb/s, that occupancy represents 15,000,000/10¹⁰ = **0.0015 s = 1.5 ms** in the constant-rate FIFO model.

This is a model estimate, not a setting for every switch. Possible mismatches include synchronised bursts rather than independent flows, a different RTT distribution, congestion-control algorithms outside the model, short flows, and a shared-buffer allocator that gives this queue less memory. A lower service rate raises the waiting time for the same occupancy. State the traffic mix and buffer allocation; measure useful throughput, burst loss and delay before accepting a setting. The academic model is useful because its assumptions give you things to test. See the authors' [buffer-sizing research](https://yuba.stanford.edu/~yganjali/research/bsizing/).

### 30.4 — Equal rates do not make equal traffic contracts

First locate the drops: correlate provider policer counters with CE queue statistics and a packet capture at the handoff. Confirm direction, attachment, effective rate, burst and accounting units on both devices. A configured name is not an operational value.

Use a controlled idle-then-burst test, followed by sustained load. At 200 Mb/s, 250,000 accounted bytes represent 10 ms of rate budget. A sender's larger permitted burst may still exceed the receiver's allowance. Vary packet size while holding payload rate constant: a disproportionate small-packet failure suggests that header/wire accounting or packet-rate limits merit investigation. Compare IP bytes, Ethernet/tag/tunnel overhead and operational rounding. Test a measured lower shaper rate with the same traffic envelope to separate steady-rate mismatch from burst mismatch.

Change one parameter at a time and preserve the original policy. Accept only when intended bursts and sustained traffic meet the agreed loss/delay objective, lower classes retain service and recovery is demonstrated. The paper exercise does not supply a universally correct headroom percentage.

### 30.5 — A four-class acceptance matrix

Record policy versions, bottleneck and accounting before and after the change. Use the same offered-load matrix, measurement points and clock method in both runs. Agree numerical service targets before seeing results.

| Test | Evidence and acceptance question |
| --- | --- |
| Each class alone, then all backlogged | Do classification/marking counters and captures agree? Do priority envelopes and residual shares match the intended contract? |
| Idle and bursting traffic | What is the delay distribution, loss and borrowing behaviour? Include both short bursts and sustained overload. |
| Unauthorised EF/CS6 | Is it remarked or otherwise treated as specified, without taking protected capacity? |
| Mixed small/large packets | Do byte accounting and scheduler behaviour preserve the service target? Record packet rate as well as bit rate. |
| One link failed | Does reduced capacity still satisfy the admitted workload, with management/control reachable? |
| Restore link and policy | Does service return without persistent wrong marking, starvation or stale attachment? |

Inspect lower-priority application completion as well as the priority flow. Include non-ECN and ECN-capable traffic when making ECN claims; the existing UDP fixture alone cannot establish transport feedback behaviour. A failure or unsupported hardware feature remains an explicit exception.

### 30.6 — Give finance a conditional decision

Use one planning horizon, demand forecast and failure-capacity target. As invented three-year, undiscounted examples: an upgrade costing £24,000 initially plus £6,000/year totals **£42,000**; a QoS redesign costing £8,000 plus £4,000/year totals **£20,000**; admission controls costing £3,000 plus £1,000/year total **£6,000**, before the value of rejected or deferred work. These are teaching inputs, not quotations. Identify any common costs excluded from all three.

Admission wins only if deferral/rejection is operationally acceptable. QoS can win when congestion is intermittent and a bounded priority workload fits both normal and failed capacity. An upgrade is needed if the required simultaneous demand cannot fit after reasonable scheduling/admission, provided the purchased capacity survives the relevant failure. Compare combinations too: extra capacity does not remove the need for classification or overload policy.

Show the demand level or business cost that changes the recommendation. Include implementation lead time, staffing, support, service risk and the cost of failure. Apply the organisation's discount rate and dated quotes for a real decision; do not choose solely from these illustrative totals.

## Chapter 31 — The subscriber edge

### 31.1 — Count addresses, ports and reserve separately

For 120,000 simultaneous subscribers at 64 per public address, the raw requirement is ceil(120,000/64) = **1,875 addresses**. Adding 10% of that requirement and rounding up gives ceil(1,875 × 1.10) = **2,063 addresses**, 188 more than the raw count. Define this reserve as spare pool capacity for growth or operational exclusions; it does not automatically survive the loss of a particular CGN site.

If the intended rule is instead “leave 10% of the total pool unused”, calculate ceil(1,875/0.90) = **2,084**. These are different denominator choices. State which one the product uses and whether the spare pool is accessible in the specified failure.

Ports 1024–65535 inclusive give 65535 − 1024 + 1 = **64,512**. Dividing equally among 64 subscribers gives **1,008 ports per protocol per subscriber**, before any extra reservations. TCP and UDP have distinct port spaces; mapping/reuse rules prevent interpreting this mechanically as a universal connection count. Test allocation failures and per-subscriber tail demand as well as aggregate occupancy.

### 31.2 — Specify a product the BNG can enforce

Define “500 Mb/s” precisely: for example, a proposed symmetric product capped at 500,000,000 accounted bit/s in each direction, with a separately agreed burst and queue/delay limit. State whether these are IP bytes or another accounting boundary and what happens to excess traffic. Include static IPv4 persistence, a stable routed /56, source validation, inbound policy, DNS provision and accounting expectations.

RADIUS can carry `Framed-IP-Address`, `Delegated-IPv6-Prefix`, `Filter-Id` and `Class` in their defined roles. Neither a rate nor a platform-specific product object is created merely by naming the product. Record the NAS dictionary, units, attribute-to-profile mapping and exact release; distinguish a delegated-prefix attribute from a successful DHCPv6-PD exchange. [RFC 4818](https://www.rfc-editor.org/rfc/rfc4818.html) defines the delegation attribute.

If a required feature is unsupported, reject activation with a diagnosable reason or enter an explicitly authorised restricted state; never silently deliver unrestricted service. Test both directions, reboot/reconnect persistence, prefix routing from a LAN host, source isolation, live changes and accounting. Compare configured and effective state and verify an unaffected subscriber during rollback.

### 31.3 — Size the record system without choosing retention by arithmetic

Use decimal units and the declared illustrative workload, not a presumed production logging rate.

| Scheme | Raw per day | Raw for 30 days | Three copies, each with 50% indexing allowance |
| --- | ---: | ---: | ---: |
| 120,000 × 2 records/s × 100 bytes | 2.0736 TB | **62.208 TB** | **279.936 TB** |
| 120,000 × 4 records/day × 150 bytes | 72 MB | **2.16 GB** | **9.72 GB** |

The final column multiplies raw storage by 3 × 1.5 = 4.5. It excludes filesystem overhead, spare capacity, backups beyond those copies, exception records and query/workspace requirements. Block assignment records support attribution only with the historical subscriber bindings, allocation rules, versions, times and any dynamic overflow records. These schemes have different evidence requirements; their byte counts alone do not establish equivalent audit capability.

Thirty days is the exercise horizon, not legal advice. Retention follows the applicable purpose, obligations and deletion policy. The [UK Notices Regime Code](https://www.gov.uk/government/publications/notices-regime-code-of-practice/notices-regime-code-of-practice-accessible) and [ICO storage-limitation guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/storage-limitation/) do not make this spreadsheet the authority for a retention period.

### 31.4 — Recover customers rather than count requests

60,000/200 = **300 seconds** assumes 200 successful complete establishments per second throughout processing. Discovery, AAA latency, allocation, retries, backoff and service validation add time or reduce the effective rate. A RADIUS request counter cannot substitute for successfully restored subscribers. If 200 is merely a peak rather than a sustainable rate, even this processing estimate is optimistic.

In an isolated test, establish baseline service, retain an unaffected customer and make one AAA path unavailable. Measure existing-session behaviour and attempted new sessions separately. Restore AAA under a declared retry pattern and concurrent workload; record offered requests, failures, successful sessions, effective policies, addresses/routes, accounting and actual client transactions. Track restoration percentiles and the last unrecovered customers, not just a peak rate. Check retries do not create duplicate bindings or an unrestricted fallback.

Define stop conditions, rollback authority and permitted test load before execution. Repeat under the nominated surviving dependency, including database/accounting contention. Report this as a plan until executed; Lab 32's two static attachments do not certify 60,000-subscriber recovery.

### 31.5 — Make IPv6 a usable household service

One defensible policy is a stable /56 per residential service, allowing **256 conventional /64 LANs**, with an explicit process for customers needing a different size. This is a product choice, not a universal standards mandate. Reserve future allocation capacity and bind the prefix to the trusted subscriber attachment. WAN addressing and the delegated LAN prefix are distinct.

Plan renumbering with old/new preferred and valid lifetimes, overlapping routes and source filters, DNS updates and a supported CPE transition. Explain the stability/privacy trade-off; changing host interface identifiers does not conceal a stable delegated prefix. Apply the intended stateful inbound policy while allowing essential ICMPv6 and return traffic. [RFC 6177](https://www.rfc-editor.org/rfc/rfc6177.html) discusses site assignment, and [RFC 9915](https://www.rfc-editor.org/rfc/rfc9915.html) specifies DHCPv6.

From a device behind the CPE, verify the LAN advertisement, source address, route and return delivery, DNS, a controlled application, path-MTU behaviour and the intended inbound filtering. Test reconnect, renumbering and an unauthorised source prefix. A PD lease or successful WAN ping alone does not accept the household service.

### 31.6 — Follow the first contradiction after Access-Accept

Correlate customer, attachment, session and timestamp first. “No Internet” needs a specific failing transaction and direction.

| Adjacent stages | Observation that separates them |
| --- | --- |
| AAA reply → BNG interpretation | Capture the accepted attributes, then compare the effective subscriber product; unsupported attributes can fail here. |
| Effective product → allocation | Inspect the actual IPv4/PD lease and ownership, rather than only the requested attributes. |
| Allocation → route/source policy | Compare the subscriber prefix with installed forward/return routes and permitted sources. |
| Policy → egress | Observe queue/filter counters and the packet at the next boundary; check the exact subscriber attachment. |
| IPv4 egress → CGN | Where CGN is used, inspect mapping/allocation failure and the translated tuple. Compare IPv6 separately. |
| Network reachability → DNS/application | Use an appropriate controlled endpoint and name-resolution observation; a failed named transaction alone does not locate the fault. |
| Server reply → client | Trace return ingress, subscriber route and CPE filtering with the same flow and time. |

Check MTU and packet size when small probes pass but transactions stall. After the smallest justified repair, repeat the original failure, a prohibited-flow test and the unaffected subscriber check; reconcile accounting. Escalate the unresolved boundary with evidence instead of resetting every session.

## Chapter 32 — Peering and transit economics

### 32.1 — Two peak hours per day

With five-minute aligned samples, a complete 30-day month has **8,640 intervals**. Two hours per day at 14 Gb/s produce 30 × 2 × 12 = **720 high samples**; the other **7,920** are 6 Gb/s. The nearest-rank 95th percentile is at rank ceil(0.95 × 8640) = **8,208**, inside the high group, so the result is **14 Gb/s**. Only 432 ranked intervals are excluded; 60 peak hours exceed that 36-hour count.

For an explicitly invented contract with an 8,000-Mb/s commit at £0.05/Mbps/month and burst at £0.08/Mbps/month, the line charge is 8000 × 0.05 + (14000 − 8000) × 0.08 = **£880/month**. This excludes fixed fees, tax, credits and other clauses. It assumes the stated one-direction sampling and nearest-rank convention; those must come from the real contract before applying the arithmetic to a bill.

### 32.2 — Recompute both commit floors

From `labs/lab33`, run `python -B percentile.py traffic.csv --commit-a 8000 --commit-b 8000 --price 0.05 --burst-price 0.08 --output committed.json`. With the retained synthetic fixture and per-line half-up rounding:

| Scenario | A charge | B charge | Exchange | Total GBP | Saving against current |
| --- | ---: | ---: | ---: | ---: | ---: |
| Current | 596.48 | 453.12 | 1200.00 | **2249.60** | 0.00 |
| No exchange, 50:50 redistribution | 1056.52 | 914.40 | 0.00 | **1970.92** | 278.68 |
| Additional cache, cache costs excluded | 471.01 | 400.00 | 1200.00 | **2071.01** | 201.59 |
| B outage on 12 June | 611.68 | 452.40 | 1200.00 | **2264.08** | −14.48 |

The 15% cache transformation takes B's percentile from 8,664 to 7,364.4 Mb/s, below its 8,000-Mb/s commit, so its £400 base remains payable. A's percentile becomes 8,887.6 Mb/s and still attracts excess charges. The exchange cost does not change. The total reduction is about **7.94%**, not 15%; the transit-only reduction is about **17.02%** because excess and committed Mbps have different prices. These executed Python-model results do not establish real cache performance, market prices or invoice savings.

### 32.3 — A lower percentile can conceal an impossible port

Run `python -B percentile.py traffic.csv --ix-split 0.8 --capacity-a 20000 --capacity-b 20000 --output constrained.json`. Retain the default zero commits, £0.06/Mbps/month and £1,200 exchange cost for comparison; changing those assumptions changes the answer.

In the no-exchange scenario, A receives A + 0.8 IX at each interval and B receives B + 0.2 IX. Their percentiles are **19,697.0 and 10,968.8 Mb/s**, giving rounded charges of **£1,181.82 and £658.13**, total **£1,839.95**, a modelled reduction of **£507.25** against £2,347.20 current.

Yet A exceeds 20,000 Mb/s in **332 intervals**, totalling **27 hours 40 minutes**, with a **52,847-Mb/s offered peak**. B's peak is **17,931 Mb/s** and it has no over-capacity interval. Even the current scenario already exceeds A's capacity in 24 intervals. Thus both the proposal and its baseline require capacity attention. The calculation flags offered demand; it neither simulates drops nor predicts the bill for the lower traffic actually delivered by an overloaded circuit. A percentile below port speed is not a capacity acceptance test.

### 32.4 — Price a complete cache service

Obtain aligned directional upstream and cache streams, catalogue/eligibility limits, hit behaviour, cache-fill traffic, peaks, failures and performance from representative clients. Compare the same periods and workload; separate seasonality or demand growth from cache effect. Recompute the counterfactual transit charge under the actual commits, direction, rank and rounding rules. A cache byte is not necessarily a byte removed from the price-setting intervals.

Add hardware ownership, rack/power, transport, installation, support, replacements, monitoring, fill cost and exit obligations. Record whether equipment or services are supplied by the programme and under what terms. Test origin fallback and surviving upstream capacity when the cache fails or is removed. Measure client loss, delay and application completion alongside pounds saved.

Present sensitivity to hit rate, peak coincidence and contract renewal. Require provenance for real measurements; the chapter's uniform 15% reduction is a teaching transformation, not observed cache effectiveness. Keep commercial, service and failure results separate in the recommendation.

### 32.5 — Review the 36-month obligation

State the discount, committed rate, excess price, installation/fixed charges, indexation, taxes and service-credit rules. Model monthly cash flows over the full term, including growth and a lower-demand scenario. A useful counterexample: an invented 10% unit discount with a 25% larger compulsory commit makes the base charge 0.90 × 1.25 = **1.125 times** the old charge, or 12.5% higher, before other terms.

Check port/backhaul upgrades, capacity after each named failure, physical diversity, support, DDoS options, useful community controls and actual route/service performance. Compare renewals with dated alternatives at the required sites. Examine termination charges, portability, installation lead time, automatic renewal and who owns the calendar reminder. New technology or a traffic shift can strand a commit before the term ends.

Recommend acceptance, negotiation or an alternative subject to explicit decision triggers and an owner. Use the organisation's approved financial method and review contractual obligations with the responsible commercial/legal team; the exercise does not establish that a particular real contract is favourable.

## Chapter 33 — Internet routing security

### 33.1 — Compose the entire transit policy

Specify router, neighbour, address family, import/export attachment and the contracted route service. For an illustrative public full-transit import: reject prohibited special-purpose space, unexpected own prefixes, unacceptable lengths/paths and ROV Invalid routes; permit remaining routes only within the transit contract; reject everything else. Not-found is an explicit risk decision, not an accidental fall-through. Defaults need explicit permission when purchased. Prefix limits protect resources but do not authorise routes.

Export only explicitly authorised own/customer prefixes and paths with the intended communities. Do not export learned peer/provider routes to another provider. Scope any mitigation or other exception by neighbour, prefix, origin, owner and expiry. Test authorised and unauthorised candidates in every feasible validation state, each family and both directions. Observe accepted routes, installed forwarding and controlled application results.

Stage the change on a canary with management access and the approved prior policy available. Test cache change/failure, withdrawals, exceptions and rollback. Confirm affected routes update without relying on manual refresh: [RFC 6811 section 4](https://www.rfc-editor.org/rfc/rfc6811.html#section-4) requires affected-prefix revalidation when mappings change. A plan or accepted CLI is not completed service acceptance.

### 33.2 — Authorise exactly the selected announcements

Let symbolic aggregate P/20 contain /24s numbered 0–15, and suppose only P[2]/24 and P[9]/24 are intended from AS64501. The minimal entries are **(P[2]/24, maximum 24, AS64501)** and **(P[9]/24, maximum 24, AS64501)**. P is symbolic because the ordinary IPv4 documentation blocks are /24s; do not invent a supposedly public-test /20.

A single P/20 maximum /24 authorises 1 + 2 + 4 + 8 + 16 = **31 distinct prefixes** of lengths /20 through /24 from that origin. The two exact entries authorise two; the broad version authorises **29 additional prefixes**, including fourteen other /24s and all fifteen shorter aggregates.

An attacker advertising P[5]/24 with a forged path ending in AS64501 can pass origin validation under the broad record. An independent session-specific exact-prefix allowlist permitting only P[2]/24 and P[9]/24 rejects it even if the origin is Valid. With only the two exact VRPs, P[5]/24 may be Not-found, so ROV Invalid rejection alone is still insufficient. Forging the origin for one of the authorised exact /24s also illustrates the remaining path-authenticity limit. See [RFC 9319](https://www.rfc-editor.org/rfc/rfc9319.html).

### 33.3 — Use the stated denominator

Covered prefixes = 640 + 30 = **670**, or **67%** of 1,000 unique prefixes. Valid prefixes are **64%**; Invalid are **3%** and Not-found **33%**. Among covered prefixes, 640/670 is approximately **95.52% Valid**. That last percentage has a different denominator and must not be presented as global coverage.

None measures users, traffic or service impact. Prefixes have unequal size and use; alternate accepted paths, more-specifics, collector visibility and local policy affect reachability. To estimate rejection impact, compare the actual proposed policy with accepted and installed routes, dependencies and controlled service tests. Preserve the snapshot date, address family, source and deduplication method. These numbers describe the synthetic exercise only.

### 33.4 — Three independent reasons to retain authorisation filters

First, a matching origin does not prove the route arrived through an authorised commercial relationship: a leak can keep the legitimate origin. Test ingress and export scope.

Second, a permissive maximum length can let a forged legitimate origin validate an unintended more-specific. An exact-prefix contract can reject that prefix independently of its origin state.

Third, Not-found means the available VRP set supplies no covering entry, not that the route is authorised or necessarily malicious. A policy accepting Not-found still needs a bounded customer/peer announcement set and path checks. Missing, stale or changing cache data strengthens the need for independent controls.

The three controls answer different questions. An IRR-generated allowlist also needs source/lifecycle review; copying stale registry data does not make it a trustworthy fallback. Record policy order and test that an unconditional accept cannot bypass the earlier intent.

### 33.5 — Distinguish recovered sessions from recovered enforcement

In an isolated environment, record both caches' source freshness, VRPs, timers, serial/session identifiers and the router's effective policy. Seed known authorised/unauthorised routes and the expected application endpoints. Interrupt cache A while B remains current, then reverse the roles. Next interrupt both; test retained data up to the configured expiry, expiry itself and router startup with no usable data. Record behaviour rather than assuming a universal fail-open or fail-closed outcome.

Change an authorisation during the isolation and exercise an exception's expiry. On recovery, observe the new VRPs, automatic route re-evaluation, import/export disposition, installed next hop and service result. Use withdrawals as well as additions. A re-established RTR TCP session alone proves none of those later steps; a successful manual refresh must be labelled separately from automatic recovery.

Check cache disagreement and shared dependencies, preserve management reachability and restore the baseline. Evidence should include a timed route-state/application matrix, cache contents and policy version for every stage. The retained lab did not complete full expiry or dual-cache qualification; this answer is an acceptance design, not newly executed results.

### 33.6 — Make an alert reach a responsible person

Maintain expected prefix/origin pairs, permitted more-specifics and authorised DDoS/third-party origination with owners and expiry times. Compare multiple external collectors with internal route telemetry and service probes. Include prefix, path, origin, validation state, observer, event/receive timestamps and relevant maintenance/exception record in the alert. Missing collector evidence is not proof that an event did not occur.

Route material unexpected announcements to the on-call owner, with acknowledgement and escalation deadlines agreed by the team. Corroborate through another viewpoint and service evidence, contact the authorised origin/resource owner and relevant providers, and preserve the timeline. Avoid automatically withdrawing a legitimate service solely because one feed reports a change.

Test with an isolated route feed or a permitted synthetic event through the monitoring pipeline; do not advertise unauthorised public space. Verify detection, paging, human acknowledgement, exception expiry and closure. Measure event-to-observation and observation-to-acknowledgement separately. Any detection-time claim should match that measured scope and recognise collector delay and visibility gaps.


## Chapter 34 — Data-centre fabric design

### 34.1 — Count paths before naming ECMP

Downlinks total 48 × 25 = 1,200 Gb/s; uplinks total 6 × 100 = 600 Gb/s, giving 2:1. The divisors of six give the complete, equal-link arrangements:

| Spines | Links per spine | Distinct spine choices |
| --- | --- | --- |
| 1 | 6 | 1 |
| 2 | 3 | 2 |
| 3 | 2 | 3 |
| 6 | 1 | 6 |

Six separately routed uplinks can provide six local next hops if routing eligibility and hardware support permit. Aggregating parallel links into a LAG instead presents a logical adjacency; member selection is another hash. Neither count guarantees six times one flow's throughput. Six spines lose only 100 Gb/s on one spine failure, versus 300 Gb/s with two equally connected spines, but cost more boxes, optics and operations. Choose six only if that survivor capacity and expansion justify the cost; record switch radix and cage constraints first.

### 34.2 — A correct ratio with the wrong wiring

Two physical links cannot connect a leaf to eight distinct spines. With the chapter's 24 × 25 Gb/s general leaf, retain 600 Gb/s down and provide eight 25 Gb/s uplinks: 200 Gb/s up, still 3:1. Qualified 4 × 25 breakout consumes six downlink cages and two uplink cages, plus the required reserve. One uplink cage failure removes four links, so assess it separately from one spine failure.

Alternatively use eight native 100 Gb/s uplinks and increase downlinks to 2,400 Gb/s: 96 × 25 Gb/s server interfaces. At four interfaces per downlink cage this needs 24 + 8 = 32 working cages. Four reserved cages raise the requirement to at least 36; a 32-cage switch with that reserve cannot implement it. Obtain a suitable SKU and qualified breakout layout, or change the design. Arithmetic does not qualify port modes.

### 34.3 — Four thousand servers at 3:1

Ceiling(4,000/48) = 84 leaves, providing 4,032 server interfaces. Each leaf has 1,200 Gb/s down, requiring 400 Gb/s up for 3:1. With 100 Gb/s native uplinks and one link per leaf–spine pair, use four spines. Each leaf spends 12 downlink cages plus four uplink cages; with four reserved, 12 of its 32 cages remain free.

Each spine connects 84 leaves; 128 − 8 = 120 ports are available, so one spine tier suffices. The port-count bound is 120 leaves or 5,760 server interfaces in this uniform model. A lost spine leaves 300 Gb/s per leaf, giving 4:1. This is single-NIC server attachment, with no promise of surviving a leaf loss. Without the given server-port density, breakout mode, reserves, uplink speed and spine radix, the question has no unique bill of materials. More downlinks per leaf may reduce leaf count but increase uplink and cage demand.

### 34.4 — Defend fixed switches without promising free operations

Propose repeatable fixed-switch roles, automated configuration and inventory, staged upgrades and a measured replacement procedure. A failed leaf has a bounded attachment set; a spine failure consumes a calculated fraction of uplink capacity. Incremental purchases can follow demand if ports, power and cabling were reserved. Compare this with chassis redundancy and the number of services affected by a chassis or common control-plane failure.

Count everything the director will pay to operate: devices, optics, spare units, rack space, power, software, monitoring, qualified engineers and changes. Fewer chassis may simplify some tasks and complicate a major failure. Submit normal and survivor capacity, recovery targets, a support plan and dated quotations for both alternatives. “More boxes” is a manageable property, not proof that fixed switches are cheaper.

### 34.5 — Power is a bound, not a placement plan

Floor(15/4) = three servers is the power-only upper bound, drawing 12 kW and leaving 3 kW before other loads. Determine whether the stated 15 kW is usable IT capacity or includes local cooling. Subtract switch and auxiliary loads, apply facilities derating and check the surviving-feed rating; dual feeds do not automatically double usable resilient capacity.

For a constructed example, assume four 100 Gb/s NICs per server, all attached to the row fabric: three servers require 12 server interfaces and 1,200 Gb/s of aggregate uplinks at 1:1. That could mean twelve 100 Gb/s or three 400 Gb/s uplinks, but the latter may not fit the required spine count or failure target. With four 400 Gb/s NICs per node instead, both downlink demand and required 1:1 uplink bandwidth quadruple to 4,800 Gb/s. State which NICs carry storage, management and collective traffic before sizing.

### 34.6 — Replica placement follows shared failures

Three replicas in one rack share rack power, maintenance and often a leaf or leaf pair. Put replicas in separate racks and, where the application's latency and quorum rules permit, separate power and fabric failure domains. Verify whether apparently different racks share a PDU, upstream busway, cooling dependency or maintenance event. A second site may improve resilience but changes replication delay and failure semantics.

For a three-member majority quorum, two surviving members can form a majority, subject to the database's actual membership and fencing rules. Test loss of one rack and a network partition without allowing competing writers. Record recovery time, committed-data behaviour and restoration. Merely distributing boxes does not prove the database remains available or consistent.

## Chapter 35 — BGP in the data centre

### 35.1 — A reproducible private-AS plan

One scheme within RFC 6996's four-octet private range is a block per fabric: fabric f uses base 4,200,000,000 + 1,000f, for allocated f values that keep the block within 4,294,967,294. Fabric zero uses 4,200,000,101 through 4,200,000,132 for leaves 1–32 and shared spine AS 4,200,000,000. Sharing the spine ASN is intentional; record the topology assumptions it supports. A unique-spine-AS variant needs its own multipath-policy review.

Reserve blocks in an authoritative inventory, including allocation owner, site, role, decommissioning state and intended inter-fabric connectivity. Validate bounds and collisions before generating configuration. Private ASNs must not leak into public transit policy. A spreadsheet rule remembered by one engineer is not an allocation system.

### 35.2 — Read the path from the receiver

Leaf-02 receives AS_PATH `4200000000 4200000101`: the spine prepends its AS to leaf-01's advertisement. Its own AS, 4200000102, is absent, so this path needs no `allowas-in` exception. If leaf-02 instead also uses 4200000101, its own AS appears in the received path and the ordinary loop check rejects it.

Under that deliberately reused-leaf-AS design, a bounded `allowas-in` exception on the receiving leaf can permit the path. It is not the only design choice: unique leaf ASNs or a supported AS-override policy can avoid that specific exception. Document which safeguard is relaxed, constrain accepted prefixes and test a genuine loop. Do not add the exception to every neighbour as a ritual.

### 35.3 — Unnumbered still has addresses

The adjacent interfaces retain IPv6 link-local addresses, scoped to their links. A suitable BGP implementation can establish the session using them and exchange IPv4 reachability with an IPv6 next hop through the relevant capability. It removes a plan for globally unique point-to-point IPv4 subnets, not all addressing. Loopbacks, management, VTEPs, server networks and any routed services still need an allocation plan.

Check the exact NOS release, interface-neighbour discovery mechanism, extended-next-hop support, address-family configuration, policy defaults and forwarding installation. Link-local diagnostics need an interface scope. Test a link and neighbour restart, resolved next hops and an actual IPv4 packet path. A supported command or an Established session alone does not establish forwarding.

### 35.4 — Four advertisements, one installed path

Identical AS paths are not the differing-AS-path condition that `multipath-relax` addresses; that knob alone is not the explanation. Separate three gates:

1. Received and accepted: inspect each neighbour's accepted routes and inbound policy; an update can be filtered before selection.
2. Eligible: compare local-preference, weight where applicable, MED, origin and next-hop validity under the implementation's multipath rules. Record a concrete differing attribute or unresolved next hop.
3. Installed: inspect the configured/compiled ECMP limit and routing-manager/kernel or ASIC FIB state. Several eligible paths can still be constrained at installation.

FRR commands such as `show bgp ipv4 unicast <prefix>` and neighbour route views help with the first two; the relevant platform's FIB view and controlled multi-flow traffic test address the third. Syntax and output vary by release. Do not alter multiple attributes at once and then claim to know which fixed it.

### 35.5 — Established without permitted exchange

RFC 8212 specifies default rejection when explicit import or export policy is absent for eBGP. On implementations/profiles enforcing it, define inbound and outbound policies for the intended address family and attach them to the neighbour. Permit only the prefixes and attributes the fabric requires; a blanket permit-all workaround loses the safety benefit.

Confirm the effective profile and policy counters on the actual release: Established with zero routes can also mean no originated routes, the wrong address family or an unrelated filter. Verify an intended accepted prefix, an intended advertised prefix and a rejected negative-control prefix. Disabling FRR's policy requirement is not equivalent to writing the policy.

### 35.6 — Summaries buy scale by hiding detail

Hierarchical aggregation reduces route state and churn when an aggregate's reachability promise matches its topology. A small DC underlay can instead benefit from precise loopback routes and rapid withdrawal of the failed endpoint. Advertising a summary while one covered destination is gone can attract traffic into a black hole; retaining specifics avoids that particular concealment.

A /32 can still black-hole when BGP is alive but the forwarding path is broken, when its recursive next hop is unresolved or wrong, or when the endpoint's service has failed without route withdrawal. Inspect the installed next hop and data-plane probe, not just the presence of the prefix. Summarisation is a trade in state and failure visibility, not an inherently good or bad technique.

### 35.7 — Anycast fails at both routing and service boundaries

Packets already travelling to the failed host can be lost. A DNS client may retry a UDP query and reach a survivor after convergence; established TCP connections generally lose their server state if redirected, unless a separately engineered mechanism preserves it. QUIC connection state deserves the same explicit treatment. Resilient hashing can reduce reassignment of unaffected flows but cannot revive state on the failed host.

With perfectly even demand, each survivor's share grows from 1/8 to 1/7, a factor of 8/7, about 14.3% more; actual hashes and demand are uneven. Tie advertisement to meaningful resolver health, with hysteresis and monitoring of withdrawal. For planned maintenance, coordinate service draining before route withdrawal where possible. Waiting after withdrawing a route does not by itself keep established flows on the old server.

## Chapter 36 — VXLAN and EVPN

### 36.1 — Mark the two size boundaries

For ordinary untagged VXLAN over IPv4, the wire layout is outer Ethernet (14 bytes), outer IP (20), UDP (8), VXLAN (8, including its 24-bit VNI), inner Ethernet (14), inner IP packet, then outer Ethernet FCS (4). The original inner FCS is not carried. Outer IP length starts at its IP header and ends at the encapsulated inner payload; it excludes outer Ethernet and its FCS. The outer Ethernet frame includes them. Preamble/SFD and inter-frame gap consume link time but are separate from that frame count.

Thus a 1,500-byte inner IP packet needs 1,550 bytes of outer IPv4 packet and a 1,568-byte untagged frame including FCS. An outer VLAN adds four frame bytes without increasing the outer IP packet; an inner VLAN adds four bytes inside that packet. Confirm the vendor's MTU and frame-size conventions before comparing numbers.

### 36.2 — Work backwards from the underlay MTU

With outer IPv4 and no options: 1,500 − 20 − 8 − 8 − 14 = 1,450 bytes for the inner IP packet. Inner IPv4 ICMP without options leaves 1,450 − 20 − 8 = 1,422 bytes of ICMP data. With outer IPv6 and no extension headers, replace 20 by 40: inner IP maximum 1,430 bytes and inner IPv4 ICMP data 1,402 bytes.

If the inner packet is instead ICMPv6 without extension headers, subtract 40 + 8 internally: 1,402 bytes of data over outer IPv4 and 1,382 over outer IPv6. These are header budgets, not measured path MTUs. Include actual inner tags/extensions, verify all underlay hops and use a bounded size sweep with packet capture. Tiny pings succeeding does not validate a 1,500-byte tenant MTU.

### 36.3 — A local gateway with distributed identity

Participating leaves can present the same gateway IP and MAC in the tenant segment. A locally attached host therefore uses its local leaf as the routing hop, while the fabric distributes the reachability needed to reach remote destinations. “Anycast” describes the shared gateway identity, not one hidden central router.

Migration still depends on endpoint reachability updates, EVPN mobility handling, neighbour state, policies and the application's own connection state. The gateway address staying constant removes one obstacle; it does not prove zero packet loss or invisible migration. Test a long-lived connection and a fresh transaction across the move, plus duplicate-address and stale-location behaviour. State the permitted interruption and rollback trigger before the move.

### 36.4 — Locate the routing operation

In asymmetric IRB, ingress receives the host frame, routes from the source subnet into the destination subnet in the tenant context, rewrites the inner frame towards the destination and bridges it over the destination L2 VNI. Egress decapsulates and bridges to the endpoint; it does not perform the second tenant routing operation of the symmetric design. Ingress consequently needs the destination segment information required by that model.

In symmetric IRB, ingress routes from the source L2 VNI into a tenant IP-VRF, then sends through the tenant's L3 VNI towards the remote routing MAC. Egress decapsulates into its tenant IP-VRF and routes into the locally attached destination subnet/L2 VNI before delivery. That egress tenant lookup is the distinguishing operation. Check tenant associations, router MACs, route types and VNI mappings; the chapter's L2 lab does not by itself qualify symmetric IRB.

### 36.5 — Route targets are one part of isolation

Check (1) actual EVPN import/export RTs and imported routes, including shared-service policies; (2) the mapping from access VLAN/port through bridge domain and L2 VNI to the intended IP-VRF/L3 VNI; and (3) installed forwarding and ACL/firewall treatment in both directions. An RT import error can leak routes; a wrong access mapping can place a host inside the wrong tenant without any RT error.

Use two authorised tenant endpoints with distinct test addresses. Confirm permitted same-tenant traffic and prohibited cross-tenant traffic, then verify that the failure is caused by the intended boundary, rather than a missing route that could later appear. Record explicit shared-service exceptions. RT membership is a control-plane mechanism, not a substitute for testing the complete isolation policy.

### 36.6 — Eliminate hypotheses with evidence

First establish bidirectional underlay reachability between the relevant VTEPs, including selected paths and MTU. Next inspect the EVPN sessions and the relevant accepted advertisements: type 2 for known unicast endpoints, type 3 for the chosen BUM membership mechanism. Then confirm local VLAN–VNI and bridge/VRF mapping on both leaves. Inspect endpoint MAC/IP learning and the remote VTEP association, checking for moves, duplicates and stale entries. Finally follow a controlled packet through encapsulation, transport, decapsulation and local delivery, including the reply.

An Established session eliminates only “session down”; it does not eliminate policy rejection. A received route does not establish ASIC installation. A source capture with outer VXLAN but no matching egress capture narrows the fault to the intervening path; it does not yet identify one switch. Preserve timestamps, packet identifiers and negative controls instead of replacing evidence with a checklist tick.

### 36.7 — Ask what actually needs layer 2

Ask which application behaviour requires an unchanged subnet, address or broadcast adjacency, and what interruption and recovery it tolerates. Propose routed per-site subnets with service discovery, load balancing and application replication, where the application supports them. Compare migration effort with the operational cost of extending the failure domain.

If the requirement is real, constrain the stretched segments and BUM reach; engineer redundant, capacity-qualified inter-site paths with MTU, failure and partition tests; and define endpoint ownership, split-brain prevention and operational authority during a partition. Check latency, stateful inspection and traffic tromboning. A stretched VLAN cannot manufacture application consistency or make two sites behave like one local rack.

## Chapter 37 — Whitebox switching and SONiC

### 37.1 — Four purchases and one accountable system

Separate silicon, hardware platform, NOS and support. For a proposed 200-switch fabric, an example procurement map is a specified merchant ASIC family from its silicon supplier, an exact qualified hardware SKU from an ODM/hardware vendor, a supported SONiC distribution from its provider, and a named integration/support contract covering the complete combination. The operator may buy the assembled switch rather than ASICs directly; the map identifies responsibility, not necessarily four purchase orders.

Record who owns firmware/SAI defects, optical qualification, security updates, replacement stock and escalation across suppliers. Obtain a dated compatibility matrix and end-of-support commitments. Family names and a common faceplate do not establish that two products have interchangeable behaviour or support.

### 37.2 — Installation is not provisioning

Power-on firmware boots the selected environment. ONIE can discover and install a suitable NOS image; normal operation then boots the installed NOS. ONIE is also available for deliberate recovery or reinstallation, not necessarily an action performed on every routine boot. Check boot settings, image compatibility and the recovery path.

The NOS starts its platform services and can use ZTP to obtain authorised device-specific configuration. Verify identity, image/configuration provenance, management reachability and the persisted configuration after restart. ONIE answers “which operating system is installed?”; ZTP answers “how is this device provisioned?” Neither proves BGP policy or packet forwarding is correct.

### 37.3 — Buy a qualified SKU, not an ASIC nickname

List required port rates and breakout combinations, total throughput under enabled features, route and neighbour scale, buffer behaviour under the expected incast, encapsulations, ECMP width, telemetry and failure targets. Add power, cooling, optics, availability and support term. Compare exact ASIC generation, board design, NOS/SAI release and feature-resource trade-offs.

A Trident or Jericho family name suggests a product lineage, not the measured suitability of this spine. A larger buffer may help bursts but does not fix sustained oversubscription; a higher capacity figure may exclude the feature mix you need. Obtain vendor documentation and a repeatable workload test on both candidates. The defensible answer can be either SKU—or neither—depending on those requirements.

### 37.4 — Follow a route through several owners

Begin with the dynamic update in bgpd and its policy/selection result, not CONFIG_DB: CONFIG_DB primarily describes intended configuration, not every learned route. Check transfer to the routing manager and its selected route, publication into the relevant application database/orchestration path, translation through orchagent/SAI/syncd and the ASIC-facing state, then hardware route/next-hop/adjacency installation. Database names, namespaces and commands vary by SONiC release and multi-ASIC architecture.

At each boundary, correlate the same prefix, VRF, next hop and timestamp. A routing-table entry proves that layer's state, not successful SDK programming; an ASIC_DB object expresses requested state, not independent proof that a packet took it. Confirm a bounded forwarding test with matching counters or captures and a return path. Escalate with the last proven boundary and the first failed one.

### 37.5 — Running state is not a reboot contract

Determine which component owns persistent BGP configuration in this SONiC distribution: supported management model/CONFIG_DB, FRR configuration, generated files or another workflow. An interactive `vtysh` change may alter running FRR state without updating that authoritative source. `config save -y` is not a universal promise that every such change will be reconstructed after reboot.

Inspect the intended persisted representation, its generated running result and the documented workflow for the exact release. In a suitable maintenance/lab environment, test reload/reboot, restoration and service reachability, keeping a rollback configuration and management recovery path. Reopening a terminal and seeing Established proves current state only. No new SONiC restart is supplied as evidence by this answer.

### 37.6 — Total cost depends on capability as well as scale

Use a common evaluation period and count switches, optics/cables, spares, licences/support, energy and rack costs, deployment, automation, regression testing, security updates, training, staffing/on-call, incident recovery and exit/migration. Date quotations and salary assumptions; distinguish cash payments from allocated staff time and compare equivalent service targets.

For six switches with no software team, integration and operational coverage can outweigh a hardware saving. For 500 switches with an established team, repeated per-device savings and the marginal effort to qualify another platform may dominate. Neither scale predetermines the winner. As a constructed three-year illustration, £600 saved per switch gives £3,600 at six switches but £300,000 at 500; an added £80,000 per year of staffing costs £240,000. The latter leaves £60,000 before all other differences at 500, but loses badly at six. These are teaching inputs, not market prices or a recommendation to buy.

## Chapter 38 — Programmable data planes

### 38.1 — Firmware has a hardware budget

A firmware update can expose existing parser/action capability, correct software or install a different supported programmable pipeline. It cannot create arbitrary stages, memory bandwidth or physical parsing resources in fixed silicon. Conversely, not every new encapsulation requires new silicon: a target may already support the necessary operations or offer programmable parsing.

Check the exact ASIC and board, target architecture, parser depth, actions/externs, table/stage limits, recirculation requirements, SDK/NOS support and enabled-feature resource sharing. Compile and inspect resource reports, then test correctness and throughput on the target. A software-target success, or a compiler fit alone, does not establish hardware line-rate performance.

### 38.2 — A surviving packet can report its journey

INT can attach hop identity, queue depth and timestamps to selected packets. A 30-second average cannot recover the timing of a brief queue spike; a cumulative drop counter may still record its loss. INT adds finer evidence for the packets observed, subject to sampling, timestamp quality and export capacity.

A packet discarded with its telemetry cannot deliver that record through the same in-band path. Correlate neighbouring packet observations with queue high-watermarks, drop/event counters and captures at suitable boundaries. State clock and sampling uncertainty. A near-full queue on one surviving packet supports a congestion hypothesis; it does not identify which missing packet was dropped or rule out another cause.

### 38.3 — Read what the classifier actually does

VLAN-tagged Ethernet, IPv6 and ARP all have an outer EtherType different from plain IPv4 and pass without a blocklist lookup. Supporting them requires VLAN parsing (including a bounded tag-depth policy), an IPv6 parser/address policy, and an explicit ARP policy respectively. The shipped code does not silently skip all IP options or fragments: after the fixed base-header bounds and IHL-minimum check, it reads the source address, which stays at the same offset in both cases.

An L4 filter must locate transport headers using IHL and decide what to do with fragments lacking those headers. It must also bound all additional reads. This source-address example is not full IPv4 validation. The verifier checks permitted accesses and control flow under kernel rules; it does not infer which traffic your organisation intended to permit. The corrected comments describe the unchanged executable body.

### 38.4 — A functional lab is not a rate benchmark

Run Lab 39.2 only in its supported isolated Linux environment with its stated privileges, and retain the actual kernel, tool versions, selected XDP mode, verifier response, counters and cleanup record. If unavailable, submit the predicted path and a clearly marked unexecuted test plan. No output in this answer is a substitute for that record.

The generic-mode veth lab checks bounded behaviour; it cannot establish native NIC packets/s. A benchmark needs a named NIC/driver, native/offload mode verification, CPU/NUMA/queue settings, packet sizes, flow/map workload, independent traffic generator, offered-versus-delivered counts, loss/latency and competing load. Include warm-up and repeatability. Report a result for those conditions rather than a universal “XDP rate”.

### 38.5 — A DPU relocates work and responsibility

A DPU can offload supported virtual switching, encapsulation, storage, security or cryptographic work onto its own processors and accelerators. This can reclaim host resources and isolate infrastructure from tenants. AWS Nitro combines dedicated hardware, firmware and a small hypervisor as a system architecture; it is not a claim that every DPU offloads the same functions.

Identify residual host work, fallback behaviour, supported feature combinations, firmware lifecycle and DMA/IOMMU isolation. Compare reclaimed capacity with card cost, energy and operational effort. Test loss or upgrade of the offload path. A processor the tenant cannot directly manage still needs patching, monitoring and an accountable operator.

### 38.6 — A problem worth programming

Suppose an isolated research service uses a documented experimental header that the selected fixed pipeline cannot parse, and needs a bounded field match followed by a queue selection at ingress. A suitable P4 target might implement that pipeline; an eBPF host hook may be simpler if the required rate and placement permit it. First verify that ordinary ACLs, supported tunnel termination or an application change cannot meet the requirement.

Specify accepted/malformed packets, resource bounds, counters, recovery to a known pipeline and ownership of compiler/toolchain updates. Test negative cases and the required workload on the selected target. If only a handful of low-rate endpoints need it, custom switch silicon programming may cost more than it solves. A compelling proposal includes the alternative you priced and the evidence that ruled it out.

## Chapter 39 — Server and network boundaries

### 39.1 — Seven gigabits is an observation

On the host, check application throughput and storage waits, per-core utilisation, `ss -ti` for TCP state, `ip -s link`, `ethtool` link speed, `ethtool -S` driver counters, `ethtool -k` features and interrupt/queue distribution. Commands and counters require interpretation for the actual OS/driver. Repeat the corresponding checks at the receiver; a sender cannot outrun a blocked consumer.

Trace routing, each relevant ECMP member, queue drops/high-watermarks, policers, MTU and latency along both directions. Use a bounded single-flow and multi-flow comparison to distinguish a per-flow/CPU limitation from an aggregate limit, while keeping the application/storage path in view. No drops on one sampled port means no drops were reported by those counters in that interval. It excludes neither queueing without loss, hidden microbursts, missing counters nor loss elsewhere. Do not exonerate an entire fabric from that observation.

### 39.2 — Feature flags describe a contract

On a veth, a reported segmentation feature can mean the virtual device accepts a large buffer that the kernel carries onwards; no physical card is needed. GSO defers segmentation in software and GRO commonly aggregates receive traffic in the kernel. The reference lab's LRO refusal says this veth does not permit enabling that feature. `[fixed]` means unchangeable on this device, not “executed in silicon”.

Run the probe in the supported isolated environment and keep its actual output and cleanup record. Feature lists vary with kernel and driver. The supplied historical observation of 60 flags is not a count every reader must reproduce. This edition corrects the interpretation of those flags; it supplies no fresh kernel execution or throughput result.

### 39.3 — Draw the path you actually installed

A conventional example is VM vNIC → hypervisor virtual-switch port → host physical NIC → source leaf → spine → destination leaf → destination NIC → destination virtual switch/vNIC (if the destination is also a VM). A bare-metal destination omits that last virtual switch. Same-host traffic can remain local; same-leaf traffic need not cross a spine.

Label VLAN handling, gateway/routing operations, overlay encapsulation and MTU at the relevant boundaries, then draw the reply. SR-IOV or another bypass changes the path. Validate the drawing with the configured attachment and controlled captures/counters. Listing every possible switch as though every packet crosses it hides the topology you are trying to diagnose.

### 39.4 — Compare modes, not logos

Ask how the chosen Calico or Cilium mode attaches pods, allocates addresses, routes or encapsulates traffic, implements policy and handles Services. A Calico BGP deployment may advertise pod prefixes to the fabric; an encapsulated mode changes the MTU and what the fabric sees. Cilium can use eBPF for selected functions, with overlay or native routing, and kube-proxy replacement only when configured appropriately.

Record the actual version, enabled features, routing peers, tunnel endpoints, encryption and observability ownership. Compare the packet paths for a pod-to-pod flow and a Service connection in that configuration. Neither product name alone tells a fabric engineer whether to expect pod routes, VXLAN, NAT or encrypted traffic.

### 39.5 — Which load balancer, which request, which path?

Ask: (1) What exact client, destination name/address, port and failing transaction are we investigating? (2) Is the entry point a cloud/appliance VIP, Kubernetes Service, Ingress/Gateway controller or another implementation, and who operates it? (3) Which backend was selected and where are its health/readiness, policy and return-path evidence?

For a Service, inspect its selectors and EndpointSlices before assuming the fabric lost a packet. For an HTTP gateway, inspect host/path routing, TLS termination and backend responses. For an external appliance, inspect its pool and session behaviour. These are three bounded questions that turn a product label into an observable connection path.

### 39.6 — Storage requirements must name a supported combination

Ask for exact NICs, firmware, drivers, storage target, NVMe transport, GPU involvement if any, and the supported congestion/loss-recovery mode. If RoCE uses PFC, identify priorities, ECN/CNP/rate-control compatibility, per-port headroom, watchdog behaviour and failure/upgrade requirements. Ask whether a supported lossy mode exists; do not impose PFC merely from the word RDMA.

Compare NVMe/RDMA and NVMe/TCP on the same hardware, dataset, block-size and read/write mix at the intended concurrency. Measure useful throughput, median and tail I/O latency, host CPU, recovery, competing-traffic effects and operational effort. Include loss, congestion and component failures under an authorised plan. A low average latency in an idle benchmark does not choose a production storage fabric.

### 39.7 — One job can contain one flow or many

With ordinary flow-hashed LACP, one TCP connection uses one 25 Gb/s member and achieves less than its line rate after overhead and other limits. A backup job using several independent connections may spread across both members, but hashes can collide and the receiver, storage or CPU can still be limiting. The host's transmit selection and the switch's reverse-direction selection are independent.

Use application-supported parallel connections, then verify per-member counters in both directions and the useful job completion rate. If the requirement is one faster flow, a faster individual link or a deliberately supported multipath transport is a different design. Two member links do not promise 50 Gb/s of backup payload simply because LACP is up.

## Chapter 40 — AI and HPC fabrics

### 40.1 — ECMP does not know which flow is the straggler

A small number of long, synchronised flows can hash onto the same path while other paths remain idle. The collective may wait for its slowest participant, so uneven distribution matters more than the average fabric utilisation. More flows can improve statistical spreading but do not guarantee balance. An all-reduce's actual algorithm, channels and NIC mapping determine whether this situation occurs.

Inspect collective timings, per-path utilisation and competing load before attributing delay to ECMP. Compare placement and supported transport/load-balancing options against the real traffic matrix, including ordering requirements. A web workload can also have elephants; the contrast is workload behaviour, not an intrinsic property of “enterprise” versus “AI” packets.

### 40.2 — Separate marking, signalling, response and pause

In the PFC-enabled model, the switch marks ECN, the receiver sends CNP feedback, the sender's rate-control algorithm reduces injection, and PFC pauses an adjacent sender for a selected priority if buffers require it. ECN is the early feedback mechanism; PFC is hop-by-hop backpressure, with its own reaction-time headroom.

Rising PFC counters show pause activity. They do not prove ECN thresholds are too high. Check the traffic classification and queue, ECN marks, CNP generation/delivery, sender response, offered load and downstream stalls. Read counts with pause duration and the observation interval. A proposed cause must predict a distinguishing observation. Supported lossy RoCE modes are separate designs and should not be judged against an assumed PFC requirement.

### 40.3 — Compatibility can include explicit remapping

The useful part is a consistent treatment of the intended RoCE traffic from sender to receiver. Identical markings simplify the audit; controlled remapping can also preserve the required class and adjacent-link priority agreement. Trace an example packet at every mapping boundary.

Compare each port's speed, available buffer, cable delay and peer response against its thresholds and reserved headroom. Identical numerical settings on identical ports can be valid; on dissimilar ports they require justification and may be unsafe. The audit should test compatibility, feedback behaviour and survivor/failure cases, not make every configuration line equal. A changed constant needs a hypothesis and measured acceptance criteria, not a promise that a particular vendor's default is wrong.

### 40.4 — Derive the crossover with units visible

Choose a constructed 16-rank ring with 200 Gb/s links and α = 5 μs. With B = 25 × 10⁹ bytes/s, equate 2(N−1)α to [2(N−1)/N]S/B. Cancelling gives S = αBN = 2,000,000 bytes, approximately 1.907 MiB. Both terms then equal 150 μs, so total modelled time is 300 μs. If B were expressed in bits/s instead, the conversion factor 1/8 belongs in the formula.

Run `python -B labs/lab41/allreduce.py --ranks 16 --fast 200 --slow 50 --alpha-us 5 --json` from the companion root and retain the actual result. Below the crossover, per-step overhead matters more; far above it, bandwidth dominates. A fourfold link-rate reduction approaches a fourfold slowdown only in that latter regime. This arithmetic omits many real collective effects; it is not a GPU benchmark.

### 40.5 — Challenge a benchmark at its stated boundary

One 400 Gb/s NIC provides 400/8 = 50 GB/s in one direction before overheads. For the specified pure inter-node ring with one NIC per rank, a claim of 350 GB/s per rank cannot be sustained physical transfer through that NIC. At N = 8, the ring factor is 14/8 = 1.75; the ideal large-message algorithm bandwidth bound is about 28.57 GB/s, with normalised bus bandwidth approaching 50 GB/s.

Ask for topology, GPUs/NICs per rank, message size, algorithm, scale-up links, aggregation/in-network reduction, metric definition and raw timings. A multiple-NIC or hierarchical result has a different boundary; “bus bandwidth” is a normalisation, not a port counter. The arithmetic rejects the specified interpretation, not every possible 350 GB/s result.

### 40.6 — Price time actually removed

Using consistent per-GPU-hour inputs, fabric A pays for its premium when fA − fB < (g + fA)c s, under the model's fixed-work assumptions. Here c is exposed communication waiting on B and s is the fraction of that waiting A removes. The 32-node count alone determines neither; GPU count and cost allocation must also be stated.

As a constructed check, g = £4, fA = £0.40 and fB = £0.10 give a £0.30 premium. If c = 0.20 and s = 0.50, the right side is £0.44, so A passes this model; with s = 0.20 it is £0.176 and fails. These are invented rates. Obtain dated quotations and support/staffing allowances; measure c and require a controlled workload comparison for s rather than accepting a vendor promise. Profile overlap and keep GPUs, workload, software and concurrency comparable.

### 40.7 — Trace the rail and its escape path

With four servers and four GPU/NIC pairs each, connect NIC i on each server to rail i: four rails, four server-facing interfaces per rail, 16 total. An exchange between the GPU-2 positions can remain on rail 2's switch in this small design. A GPU-2 to GPU-3 exchange crosses from rail 2 through the spine to rail 3 when the back-end supplies that path.

In a rail-only design, an explicitly supported library may relay via an intra-server scale-up path to the other rail. That consumes additional internal bandwidth and depends on mapping, algorithms and failure support; ordinary IP forwarding does not automatically create it. Draw the selected collective's actual exchanges and test contention and a rail failure. The all-reduce operation name alone does not guarantee rank-aligned traffic.

### 40.8 — Three networks, three demand models

Scale-up carries tightly coupled GPU exchanges within a server or larger scale-up domain; size it from memory/collective traffic and its physical scope. Back-end connects those domains for collective and other GPU exchanges; size it from bytes per step, exposed time, mapping, concurrency and failure capacity. Front-end carries storage, management and external service traffic; size from ingestion/checkpoint/serving rates and the management recovery requirement.

Keep per-direction, per-GPU, per-node and whole-cluster units explicit. Halve a vendor figure only when it is a symmetric bidirectional total. For inference, include time to first token, inter-token latency, their tails and concurrency; KV-cache transfers can create bulk demand. One oversubscription ratio cannot express all three networks' requirements.

## Chapter 41 — Cloud and hybrid networking

### 41.1 — Familiar concepts, different objects

A VPC/VNet is a provider-managed routing/isolation domain; a subnet allocates an address range and attachment scope; route selection chooses a next hop; a stateful firewall tracks allowed connection replies. Those concepts link to Chapters 5, 20, 22 and 53, but the service objects are not identical to a physical VLAN or router VRF in every respect.

AWS subnets belong to one availability zone and associate with route tables. Google Cloud subnets are regional inside a global VPC; subnet routes apply across the VPC, optional tags apply to supported route types, and dynamic-route reach depends on routing mode. Azure NSGs can attach to NICs or subnets, while AWS security groups attach to supported resource interfaces. Identify the exact provider, object and current documentation in a real design; this answer is a comparison, not a claim to have deployed either service.

### 41.2 — Stateless filtering needs a reply rule

For a TCP client using ephemeral source port 53000 to a server's 443, a stateless path must permit both the request and the reversed reply tuple, including destination port 53000 on return. A rule permitting only inbound destination 443 is insufficient for the relevant return boundary. ICMP errors and other protocols need their own considered treatment.

Use the stateful control for ordinary application policy and coarse stateless rules where that reduces operational complexity, but recognise that carefully specified fine-grained stateless policy is possible. Where no stateless subnet layer exists, use the provider's available stateful policies and any explicitly required appliance controls. Test allowed initiation, reply and prohibited new initiation; a successful request alone is not a policy test.

### 41.3 — Separate NAT placement from address-family design

Use the chapter's AWS 10.20.0.0/16 example: public /22 subnets in zones a and b route towards an internet gateway and host zonal public NAT gateways; private /21 subnets route IPv4 egress through their own zone's gateway. Regional NAT is a different AWS service mode without that public-subnet placement requirement. Verify its selected availability mode, expansion behaviour and price before substituting it.

For native IPv6 outbound-only initiation, use an appropriate egress-only internet-gateway route and policy. For an IPv6 client reaching an IPv4-only service, plan DNS64, NAT64 and its translation-prefix route separately. An ordinary internet-gateway route does not bypass security groups or ACLs. Test both address families, DNS answers and failover; “IPv6 enabled” does not describe a complete egress path.

### 41.4 — Count relationships, then qualify the hub

Seven sites/domains have 7 × 6 / 2 = 21 pairwise relationships versus seven logical hub attachments. With six cloud VPCs and an on-premises site, those are 15 cloud pairings plus six hybrid relationships—not 21 literal VPC peerings, since the data centre is not a VPC. Physical redundancy can require several circuits or interfaces within each logical attachment.

A hub is a defensible choice for central policy and growth, subject to route scale, throughput, cost and shared-failure analysis. In an AWS Transit Gateway design, enable attachment subnets in each relevant workload zone and check forward/return routing through inspection. Verify zone loss and circuit loss with service tests. A seven-line hub drawing hides the dependencies unless those tests and capacity limits are documented.

### 41.5 — Preference never compares different prefixes

In Lab 42.1's receiving-router model, install circuit route 10.10.0.0/16 at local-preference 200 and VPN route 10.10.1.0/24 at 50. A packet to 10.10.1.7 matches both, but the /24 wins forwarding; one to 10.10.2.7 uses the /16. Raising the /16's preference cannot change that longest-match decision.

For the intended same-prefix backup design, restrict VPN advertisements to the approved summary or apply a supported receiver filter. Inspect what the neighbour actually accepted, the selected route and installed forwarding entry, then test controlled circuit withdrawal and restoration. Local-preference is receiver-local policy, not a value normally carried across eBGP to instruct a cloud. Lab output models these rules; it does not establish AWS/Azure/Google route-priority behaviour or a real failover time.

### 41.6 — Answer the encryption question with evidence

“The route is private; that fact alone does not establish encryption. We need to identify the enabled protection and its endpoints.” Check application TLS or an IPsec design, and any supported MACsec service on the relevant link. Record the exact segment protected, cipher/key configuration, key ownership and rotation, monitoring and recovery behaviour. MACsec on one circuit segment is not automatically end-to-end application protection.

For the UK business example, map evidence to the organisation's actual data classification and contractual/security requirements with the responsible owner. Do not invent a universal legal requirement from the word “regulated”. Supply configuration and negotiated-session evidence plus a bounded test; absent those, record encryption as unverified rather than answering yes from the order form.

### 41.7 — Price the same month on both sides

Constructed inputs: 40 TB means 40,000 decimal GB of billable cross-zone volume, already counted across the relevant directions; a combined illustrative £0.01/GB gives £400/month. Do not double it again unless the supplied tariff is per endpoint/direction and the flow accounting requires that. Assume collapsing the tier increases expected service downtime by 0.1 hour/month. The break-even downtime value is £400/0.1 = £4,000/hour before other cost differences: above it the £400 transfer saving loses in this model.

Use Lab 42.3 with explicit zone failure, duration, failover-effectiveness and cost inputs; reproduce its expected downtime difference instead of inserting 0.1 as a measured fact. Include survivor capacity and shared failures. First price less raw transfer, compression, cache or replication changes together with CPU, consistency and recovery effects. These are invented teaching inputs, not cloud prices or actuarial forecasts. A low-impact development tier and a revenue-critical service can rationally choose differently.

### 41.8 — Reserve an address plan you can defend

For an AWS example, allocate cloud 172.20.0.0/16, checked against the data centre's 172.16.0.0/16 and the wider organisational inventory, VPN pools and container ranges. Use 172.20.0.0/24 and 172.20.1.0/24 for assumed small public tiers, and 172.20.8.0/23 and 172.20.10.0/23 for private tiers in two zones. All fit and do not overlap. Under the AWS five-reserved-address rule, each /23 offers 507 usable IPv4 addresses: enough for a constructed 200-host tier growing 30% to 260, whereas a /24's 251 would be too small. Account separately for interface counts and service reservations.

Connect through the chosen hub with explicit zone attachments, filtered non-overlapping BGP advertisements and a tested same-prefix backup. Include resolver paths, security and encryption requirements. AWS subnet IPv4 resizing and renumbering are migration decisions; other providers have different expansion rules. Routes, firewall rules and DNS records are more readily changed, but still require service validation and rollback. Never advertise a broad private supernet merely because it contains both sites.


## Chapter 42 — Fibre plant

### 42.1 — Price the spare before the trench closes

Spare capacity is useful at other layers too; the distinction is the cost and delay of changing this one. Constructed example: an additional duct costs £20,000 now. A later return would cost £120,000 in civil work plus £30,000 of delayed-service contribution. With a 25% probability of needing it, the undiscounted expected avoided cost is £37,500, greater than £20,000. At 10% it is £15,000, less. Neither calculation proves the probability, ignores timing safely, or guarantees permission to return. Add discounting, maintenance, route life and the consequence of being unable to expand. Confirm the duct can actually be used and distinguish spare duct from spare installed fibres.

### 42.2 — Choose an interface, not just a family name

For a new coherent long-haul route, start with a qualified G.652.D or suitable G.654 design, using the optical planner's attenuation, effective-area and compatibility requirements. For the bent drop, choose a G.657 category and cable construction whose installation and operating bend limits fit; A-category compliance helps compatibility but does not promise zero splice loss. Investigate the inherited fibre inventory rather than diagnose from its age: G.653's near-zero dispersion can aggravate four-wave mixing, while G.655 is a different dispersion design. Where attenuation dominates, compare appropriate G.654 products and transition losses. Accept against product specifications and measurements, not this list alone.

### 42.3 — Three different budgets

Count four mated connector pairs in the stated example. At 1550 nm, the illustrative typical loss is `60×0.19 + 4×0.05 + 4×0.25 = 12.6 dB`. The illustrative acceptance limit is `60×0.25 + 4×0.15 + 4×0.75 = 18.6 dB`. Three inserted-section repairs add six splices and 90 m of cable; with 1 dB ageing, the design total is `18.6 + 6×0.15 + 0.09×0.25 + 1 = 20.5225 dB`. It exceeds a 16 dB allowance by 4.5225 dB. Use the design total for the modelled lifecycle, the agreed acceptance limit for handover, and actual dated commissioning/incident measurements for diagnosis. A typical estimate is not that fault baseline. All coefficients are teaching inputs.

### 42.4 — A gainer is not an amplifier

The bidirectional estimate is `(-0.09 + 0.49)/2 = 0.20 dB`; the ideal mismatch term is `(-0.09 - 0.49)/2 = -0.29 dB`. Different backscatter properties bias opposite-direction readings in opposite ways. Record both traces, match the event and wavelength, use suitable launch/receive leads and settings, then retain measurement uncertainty when comparing with the contractual limit. A negative apparent event loss does not by itself diagnose a faulty fusion splicer. Check end-to-end insertion loss separately and investigate inconsistent traces rather than averaging mismatched events.

### 42.5 — Convert the trace into a search area

With no launch lead, three 25 m slack allowances measured along the glass and a uniform 0.7% excess fibre length, the model gives `(43,210 − 3×25)/1.007 = 42,835.154 m`, about 42.835 km along the mapped route. The uncorrected reading is roughly 374.846 m farther. The answer assumes the group index is correct, the closures and slack inventory are complete, the helix factor applies throughout and the route origin matches the trace origin. Cable-slack rather than fibre-slack units require a different accounting order. This is a search location to reconcile with as-built records and safe excavation procedures, not permission to dig at one calculated coordinate.

### 42.6 — Resolution costs reach

Use a shorter pulse, appropriate averaging and launch/receive leads, and examine the acquisition settings and reflective-event recovery. The geometric estimate `c×pulse_width/(2n)` is about 10.21 m for 100 ns at `n=1.4682`, versus 1.02 m for 10 ns. Thus the simplified model cannot separate events 5 m apart with the first pulse but can with the second. Real event and attenuation dead zones depend on the instrument, reflectance and acquisition; pulse arithmetic is not an acceptance guarantee. A shorter pulse has less energy and normally less dynamic range, so retain a longer-pulse trace for distant events and compare the two.

### 42.7 — Distinguish the cost envelope from the purchase steps

Over twenty years, the lab's illustrative annual fixed costs are £480,000 for build, £270,000 for IRU and £426,000 for dark fibre. Leased 400G waves cost £240,000 each annually. Their full-utilisation envelope is £600 per carried Gb/s-year, giving equal-cost envelope demands of 800, 450 and 710 Gb/s respectively. Actual purchases are stepped: just above 400 Gb/s requires two waves costing £480,000, already exceeding the IRU price and equalling build. Just above 800 requires three. The IRU remains cheaper than build throughout this model's feasible range; ownership does not automatically win. Add incremental optics, financing, discounting and discrete renewal cash flows before deciding. Verified route control or strategic access could justify building; uncertain demand, unaffordable cash flow, consents or shared hazards could rule it out.

### 42.8 — Plan the consent dependencies

For an England example, establish the operator's powers, highway/street-works requirements, private-land interests and Code agreement, railway owner's approvals and access/possession requirements, and any environmental or planning consents. A wayleave granting Code rights can bind successors; a change of landowner does not automatically erase it. Record owner, required design inputs, submission date, dependencies, decision window and expiry for each approval. Constructed programme: private-land agreement needs four months, railway design acceptance six, followed by the next available possession two months later; if other work completes in parallel, the railway sequence controls an eight-month earliest date. Those durations are assumptions, not UK statutory periods. Confirm them locally and compare an alternative route before committing.

## Chapter 43 — Optical transmission

### 43.1 — Power, distortion and the remaining limits

Attenuation reduces optical power. Chromatic dispersion spreads a signal because propagation depends on wavelength; PMD introduces differential delay between polarisation components and can vary with time. Coherent reception and DSP can compensate substantial dispersion and PMD within their specified ranges. They do not eliminate noise, filtering, nonlinear effects or receiver power limits. Adding optical gain restores power while adding noise; it does not simply reverse every impairment. A useful handover names the measured quantity and its mode-specific limit rather than reporting that “the optics look good”.

### 43.2 — Find the optimum under the model's assumptions

Choose the lab's eight identical amplified sections: 22 dB loss and 5.5 dB amplifier noise figure each, with its fixed nonlinear coefficient. In linear units the model has `SNR(P)=P/(A+ηP³)`, so differentiating gives `P³=A/(2η)`. The supplied 0.01 dB search returns approximately −3.17 dBm launch, 18.299 dB ASE-only OSNR and 16.538 dB effective SNR. At the optimum the nonlinear noise is half the ASE noise: the resulting penalty is `10 log10(1.5)=1.761 dB`. Raising launch beyond this point increases nonlinear noise faster than useful signal. This optimum is specific to the teaching model; real loading, amplifier and transponder constraints require qualified planning and measurement.

### 43.3 — Work both received-power extremes

Minimum received power is `+1−27 = −26 dBm`, 2 dB below the −24 dBm sensitivity: fail. Maximum is `+3−19 = −16 dBm`, 7 dB below the −9 dBm overload limit: pass. The received-power spread is 10 dB, inside the receiver's 15 dB window; that feasibility check passes but does not rescue the present settings. Translating the whole range upward by between 2 and 7 dB would place it inside the window mathematically, without reserved margin. Whether a supported transmitter, amplifier or path change can do so is a separate design question. A fixed attenuator makes the low-power failure worse. OSNR and other impairments remain unqualified.

### 43.4 — Spend coding gain once

Do not subtract 11 dB from fibre loss or add it again to a receiver sensitivity already specified with that FEC. Coding improves the error performance attainable at a given signal quality; under an appropriate comparison it may reduce required OSNR/SNR or improve sensitivity. Obtain thresholds for the actual line mode, FEC and error-rate target and use those once. The lab holds its power threshold fixed and varies a separate OSNR requirement, so its unchanged power margin is a modelling choice. A net coding-gain figure also needs its bandwidth and reference conditions; FEC neither removes physical attenuation nor protects a receiver from overload.

### 43.5 — Give every allowance one home

Start with an allowance register: component tolerances, additional repair splices/cable, ageing, environmental variation, connector degradation, uncertainty and operating reserve. The Chapter 42 example already includes three repairs and 1 dB ageing. Do not add them again under another label; add only justified consumers absent from the model. If starting from commissioning measurements, add future changes and relevant uncertainty not included in those measured losses. Check the transmitter's minimum output and the receiver's threshold conventions too. A generic “3 dB margin” cannot tell you whether something has been counted twice or omitted.

### 43.6 — Zero errors is bounded evidence

FEC can correct substantial raw errors while the post-FEC output remains clean. Trend a defined margin to the applicable threshold, pre-FEC indicators and new post-FEC/uncorrectable increments together. Margin need not fall linearly with time. A cumulative counter already above zero is not automatically a new fault; compare deltas, resets and maintenance context. Under an independent rare-error Poisson model, zero observed errors gives an approximate 95% upper bound of `3/N` per bit. Demonstrating a bound near `10⁻¹⁵` therefore needs about `3×10¹⁵` observed bits: roughly 7,500 seconds at 400 Gb/s. Five minutes supplies about 4% of that exposure. Real burst errors and counter semantics can invalidate this simple statistical model.

### 43.7 — No ramp does not imply no optical fault

A sudden bend, patch disturbance or protection switch can change the path faster than the polling interval. Alternatively, interval averages may hide a short event, or monitoring may have followed the wrong wavelength, direction or path. Ask for the service-to-optical mapping before and after the event, minimum/maximum and event records at the shortest useful interval, loss-of-signal/FEC/uncorrectable deltas, protection actions and concurrent changes. Align timestamps and clock uncertainty with packet loss. These observations discriminate hypotheses; a plausible explanation alone is not a root cause.

### 43.8 — Reply with a testable evidence request

“Packet loss affected service X from A to B between the recorded UTC timestamps; the reverse direction and comparison service Y behaved as attached. Please confirm the wavelength, receiver, line mode and working/protection path carrying X during that interval. Supply short-interval power and margin records, pre-FEC and uncorrectable/post-FEC deltas, counter resets and protection events, including minima/maxima rather than only the current average. Please state the observation interval and whether the instrument could resolve a brief interruption.” Retain joint ownership while comparing the evidence. Clean optical records reduce some hypotheses, but their scope and time resolution determine what they exclude.

## Chapter 44 — DWDM, coherent optics and ROADMs

### 44.1 — Capacity without another civil build

DWDM sends independently modulated carriers through one fibre in separate spectral allocations. The economic gain is more carried traffic from an existing route; another wavelength still needs compatible endpoints, spectrum, optical margin, power and operations. Compare the incremental cost per delivered, protected Gbit/s with a fibre build or lease. A fibre with free spectrum but insufficient OSNR is not spare usable capacity. Neither is one whose remaining allocations cannot fit a channel continuously across the route.

### 44.2 — Two grid numbers

Choose `(n,m)=(4,6)`: centre frequency is `193.1 + 4×0.00625 = 193.125 THz`; width is `6×12.5 = 75 GHz`. Its nominal edges are 193.0875 and 193.1625 THz. The centre lies halfway between the 193.100 and 193.150 THz positions of a 50 GHz plan. That does not permit overlap with active neighbours. Check the entire slot, guard requirements and every traversed filter. A 63 GHz requirement rounds up to the same 75 GHz width, leaving 12 GHz within that allocation; six width increments describe one frequency slot.

### 44.3 — Plenty of spectrum, the wrong shape

The constructed Lab 45 plan fits 85 alternating 37.5/75 GHz services into 4,800 GHz: 43 narrow and 42 wide services use 4,762.5 GHz. Removing all narrow services frees 1,650 GHz including the unused tail, but no contiguous free run exceeds 75 GHz. A 100 GHz request therefore fails. Static repacking places the remaining 3,150 GHz together and the new 100 GHz channel after them, leaving one 1,550 GHz run. This is a new allocation map, not demonstrated live defragmentation. A migration needs spare paths or agreed outages, endpoint/filter retuning and rollback. Check continuity on all links, not only this fibre. The script's 800G label does not qualify a physical mode.

### 44.4 — What coherent detection buys

Mixing the received field with a local oscillator permits recovery of amplitude and phase in two polarisations. A modem can encode more bits per symbol and use DSP for supported dispersion and polarisation impairments. The gain is conditional: higher-order modulation normally needs better signal quality, DSP has finite limits, and noise/nonlinearity cannot simply be computed away. For example, dual-polarisation 16QAM at 118 Gbaud has 944 Gbit/s gross rate; dividing by 1.2 for the stated FEC overhead yields about 786.7 Gbit/s before other framing. Do not label that an 800G client interface without a complete qualified mapping.

### 44.5 — Nodes can outweigh kilometres

In the stated Lab 45 model, 40 km through eight ROADM nodes delivers 21.131 dB effective OSNR; after the 2 dB design margin, 19.131 dB remains. It admits the illustrative 118 Gbaud 8QAM mode at 590 Gbit/s. The 480 km path with two nodes delivers 22.417 dB, leaving 20.417 dB and admitting 118 Gbaud 16QAM at 786.7 Gbit/s. The longer route carries more in this model because the shorter one accumulates more modelled node amplification and filtering. Actual amplifiers and filters must replace these assumptions; node count alone is not an engineering budget.

### 44.6 — A reach claim is an invitation to specify

For a quoted 600 km product, request the exact hardware, firmware, baud rate, modulation, FEC and client mapping; fibre/span loss and dispersion limits; amplifier and ROADM assumptions; launch/receive windows; OSNR reference bandwidth and threshold; channel loading; and reserved margin. Evaluate both directions and every authorised recovery path. Agree pre/post-FEC error and outage acceptance, measurement duration, thermal conditions and supported endpoint pairing. A nameplate distance is neither a procurement acceptance test nor evidence that the design will close.

### 44.7 — Ask what changes in the noise budget

Increasing gain at existing sites does not remove accumulated noise; the simple model leaves OSNR unchanged. In contrast, inserting an amplifier site halfway along *each* 80 km span lowers per-amplifier required gain: the constructed 2,000 km example improves by 4.723 dB, from 15.865 to 20.588 dB. This means 25 added intermediate sites, not one hut for the entire route. Lowering every amplifier's noise figure from 5.5 to 4.5 dB buys 1 dB in the model. Check access, power, nonlinear launch limits and cost before recommending either. Real optimisation needs the line-system design, not these arithmetic gains alone.

### 44.8 — One recovery policy, measured at the service

Assign an owner for optical path establishment, another for packet forwarding, and one accountable service owner. List the fault classes, detection signals, backup resources, timing origins and reversion rules. Choose whether packet recovery starts immediately or waits briefly for a qualified lower-layer mechanism; justify the delay against service loss and capacity. Test a working-path cut, exhausted alternate spectrum, an unusable optical mode, failed protection resources and return to normal. Record customer traffic interruption and packet loss, not only control-plane alarms. Constructed timing calculations guide that test; they do not establish equipment recovery performance.

## Chapter 45 — Open line systems and packet-optical convergence

### 45.1 — Name the interface before assigning it

A transponder maps a client into a line signal; a muxponder aggregates several clients into a higher-rate line signal. The line system transports those optical signals through filters, amplifiers and fibre. A coherent router pluggable moves the line-modem function into the router, subject to its actual client mapping and host support. An alien wavelength originates from a third-party terminal on another supplier's line system. It may be fully planned and supported: “alien” does not mean invisible or unqualified. Assign modem, line and end-to-end service ownership explicitly.

### 45.2 — Six groups of contractual limits

Specify bands/frequencies, grid/filter widths, power limits and reference planes, permitted channel loading, addition/removal transients, and management/provisioning interfaces. Power may be per channel, spectral density or both; record units and bandwidth. The delivered OSNR also depends on route loss, amplifiers, filters and loading. A supplier can guarantee a specified engineered path or supply a qualified planning method, but a product-wide OSNR number cannot replace that calculation and acceptance measurement. Include support escalation and approved terminal combinations in the operational agreement.

### 45.3 — A clear road does not make the endpoints compatible

The line system can carry both terminals' optical envelopes while their framing, baud rate, modulation, FEC, shaping or mode selection differs. Line acceptance is one test; modem interoperability is another. Compare the exact common interface specification and supported implementation profile, then qualify that hardware/firmware pair in both directions. Even compatible modems need enough OSNR and receive-power margin on the selected route. Do not diagnose an incompatible mode by increasing launch power blindly.

### 45.4 — Eligibility includes the host and the recovery process

Check that the exact line mode closes on working and authorised recovery paths; that the router supports its power, thermal and client-mapping requirements; and that provision/monitor/retune operations have an accountable owner. Optical rerouting may need a new frequency because the former allocation is unavailable on another link. If the optical controller cannot retune the router's pluggable, that recovery plan cannot execute as assumed. Either reserve a continuous compatible allocation, implement and qualify coordination, or choose another recovery architecture. Physical distance remains an input to the path budget, not a standalone pass criterion.

### 45.5 — Three digital functions

OPU adapts the client and its rate/mapping; ODU supplies the digital path, multiplexing and path/tandem monitoring; OTU supplies section-related framing and FEC where defined. One reason to retain OTN is to aggregate and monitor rate-guaranteed sub-wavelength services across organisational boundaries. Choose the actual G.709 mapping and interface rather than assuming all higher rates use a fixed number of carriers. Those functions localise digital performance; they do not ensure optical OSNR or eliminate the need to budget fibre and amplifiers.

### 45.6 — State the timing origin

With the exercise's common detection time T and usable backups, packet FRR alone restores at `T + 50 ms`. Holding packets just beyond successful 50 ms optical protection also yields `T + 50 ms`. Holding them for successful 30 s optical restoration yields `T + 30 s`. The 200 ms IGP value applies if IGP recovery is selected instead of FRR; it is not automatically added to a preinstalled FRR action. These are assumed completion times, not measured platform limits. A short optical-protection preference can avoid a needless reroute, but either policy needs failed-backup, latency and capacity tests. If restoration fails, outage becomes detection plus the actual hold-off and packet recovery unless an early-release mechanism applies. The checkpoint's explicit values give 40.211 s versus 0.211 s, a 40 s avoidable delay in that model.

### 45.7 — Follow every optical element

Under the lab's architecture, the direct adjacent-PoP route has one amplified fibre section and no express ROADM pass. The alternate traverses three fibre spans and two express nodes: five modelled amplified sections. Noise adds in linear units, and filters impose further penalties, so a shorter node-rich route can have less margin than a longer route with fewer nodes. The count is not a universal physical rule: replace it with the actual amplifier placement, node losses and filter characteristics. Check both directions and all affected services.

### 45.8 — Sketch the failed state, not only the ring

Draw A–B–C–D–A with lengths 18, 22, 25 and 31 km, and remove A–B for the example fault. An A–B restoration then uses A–D–C–B; reserve a common contiguous allocation on all three links and check the alternate's mode and packet capacity. If the design uses dedicated 1+1 instead, the second copy already occupies its optical resources and the receiver selects it; it is not a fresh restoration allocation. Mark packet hold-off/fallback and fault propagation explicitly. An as-built route/SRLG record showing duct, bridge, building entry and power dependencies is the evidence for physical diversity. A schematic with two lines is insufficient. The record must stay current after route changes.

## Chapter 46 — Timing and synchronisation

### 46.1 — Ask what must agree

Radio carrier generation needs a suitable frequency reference; TDD neighbours also need their relevant phase boundaries aligned. Distributed incident logs need comparable time of day with documented UTC traceability and uncertainty. A scheduled industrial Ethernet application needs phase alignment of its transmission windows; its absolute UTC requirement is application-specific. Regulated trading needs the applicable divergence, granularity and traceability evidence. These categories overlap. Write a quantity, limit, reference point, operating conditions and acceptance method for each; “PTP required” alone supplies none of them.

### 46.2 — Sampling bits versus distributing frequency

An Ethernet receiver recovers timing to sample the incoming signal. Ordinary asynchronous forwarding does not thereby make the switch a network frequency reference. SyncE deliberately disciplines an eligible transmit clock from a selected source and propagates frequency through supported physical links. Qualified clock performance, source selection, ESMC quality signalling and loop prevention are required. SyncE alone does not identify UTC seconds or align time-of-day counters. A recovered link clock and a qualified synchronisation service are different deliverables.

### 46.3 — The missing directional information

For ideal timestamps and a constant offset o during the exchange, let `x=t2−t1=d_forward+o` and `y=t4−t3=d_reverse−o`. Then `(x−y)/2 = o + (d_forward−d_reverse)/2`. A fixed directional difference A therefore adds A/2 to the estimate: 500 ns adds 250 ns. Repeating identical biased measurements does not remove that bias. If directional delay changes, the bias changes too; asymmetry is not intrinsically constant. Timestamp errors, correction-field handling and clock-rate variation add effects omitted from this derivation.

### 46.4 — Four possible asymmetries

Unequal fibre lengths, different wavelengths with different group delays, unequal transmit/receive equipment paths, and a route change in only one direction can create asymmetry. A transparent clock corrects its measured message residence time; peer-to-peer variants also handle link-delay information according to their mechanism. It does not magically discover an unknown directional difference in those physical paths. Calibrate stable contributions at known reference planes, retain uncertainty, and re-evaluate after path or equipment changes.

### 46.5 — Profile agreement is necessary, not sufficient

A profile constrains message transport/addressing and clock-selection behaviour; it may also set message rates and other options. Achieved error additionally depends on the reference's error and path asymmetry, as well as actual clock/servo and timestamp performance. State the edition and supported options at both ends. Full versus partial timing support describes the architecture; neither label alone promises a particular number of nanoseconds. Check the end-to-end budget against the appropriate masks and measure at the application reference point.

### 46.6 — Detected loss versus plausible false time

Detected denial can trigger another reference or holdover, giving the operator a deadline based on the remaining error allowance. Undetected spoofing may leave a receiver reporting lock while the clock follows false time; that error is not bounded by the ordinary holdover model. Spoofing can also be detected and rejected, and denial can outlast holdover. Use independent references and solution monitoring, examine common antenna/receiver dependencies and test source rejection and return. Multiple constellations are useful diversity but do not eliminate every common interference mechanism.

### 46.7 — Turn the error allowance into a deadline

Network allocation is `1500−350−50 = 1100 ns`; subtracting the stipulated 194 ns chain bound leaves 906 ns. Under the exercise's nonnegative constant-offset/constant-drift model, additional error is `0.5t + t²/(2×86400)` ns, with t in seconds. Solve `t²/172800 + 0.5t − 906 = 0`: the positive root is about 1,775.51 s, or 29.59 minutes. That is the model's crossing, not a maintenance deadline with operational reserve. Set an earlier escalation threshold and verify environmental and disciplining assumptions. A smaller chain error would increase the available duration, so holdover is not a property of the oscillator alone.

### 46.8 — Agreement with the wrong reference

A stable uncorrected directional delay difference can bias downstream clocks while local servos report small offsets. A shared false reference can do the same. Compare time error against a suitably independent calibrated reference at the required service interface, over time and under representative load. Two receivers on one compromised antenna feed are not independent for that failure. A time-error trace can distinguish stable bias from variation, but assigning cause needs correlation with route, load, receiver and radio observations. Constant bias alone does not explain why a symptom appears only at busy hours.

## Chapter 47 — Mobile transport: 4G, 5G, backhaul, fronthaul and slicing

### 47.1 — An interface name cannot be tested

Fronthaul, midhaul and backhaul identify portions of the architecture; they do not state one universal service level. Record the functions/products at each endpoint, split and plane, frame-delay definition and limit, loss ratio, variation metric, time/frequency requirement and reference point, peak/average traffic with burst bounds, encapsulation/MTU, and normal and failed-state obligations. Include test duration, load, measurement uncertainty and acceptance ownership. A missing clause remains unresolved; a calculator cannot turn it into a pass.

### 47.2 — Draw the user-plane path

3GPP Release 14 specified control and user-plane separation for EPC nodes. Consequently a 4G deployment can distribute its user plane, while a 5G deployment can retain a central anchor. Determine the actual anchor and breakout locations, applications and traffic destinations. Local breakout may shorten selected paths and reduce central transport, but it also creates edge capacity, availability and operational obligations. Neither a generation label nor an edge box proves application latency; include the full endpoint-to-application route.

### 47.3 — A boundary is not a bandwidth figure

The split identifies which processing functions remain on each side and consequently the kind of representation carried across the interface, such as frequency-domain IQ versus higher-layer traffic. It does not alone determine the numeric bit rate or the application's synchronisation limit. Rate depends on bandwidth, numerology, carried streams, sample/compression format, occupancy and packetisation. Timing depends on the interface and radio functions, including TDD coordination. A 64-element antenna does not necessarily send 64 independent streams across the chosen split.

### 47.4 — Count the first transmission

Using group index 1.4682, propagation costs `1,000,000×1.4682/299792.458 = 4.89739 µs/km`. The propagation-only High 100 ceiling is about 20.419 km. Four store-and-forward switches imply five frame transmissions for the specified first-bit ingress to last-bit egress boundary. Each 1500-byte service frame takes `12000/10¹⁰ = 1.2 µs`. Processing is `4×2 = 8 µs`; serialisation is `5×1.2 = 6 µs`. Thus propagation gets 86 µs and reach is about 17.560 km before queuing or other reserve. Four serialisations would omit the initial transmission. Different measurement boundaries or a switch latency that already includes serialisation require a corresponding model change, not double counting.

### 47.5 — Samples, streams and overhead

There are `273×12 = 3276` subcarriers and `3276×28000 = 91,728,000` resource elements/s per carried stream. With sixteen streams and 16 bits for each I and Q component, payload is `91,728,000×2×16×16 = 46.964736 Gbit/s`. The stipulated 10% overhead gives **51.6612096 Gbit/s**. At 9 bits per component the corresponding figures are 26.417664 and **29.0594304 Gbit/s**, a 43.75% reduction in this model. Compression format, metadata and quality impact need agreement between the radio owner and endpoint suppliers; transport engineers cannot assume a narrower sample preserves radio performance. These full-occupancy rates do not substitute for an active-slot burst envelope or actual packetisation.

### 47.6 — Make variation measurable

Ask for the metric, limit, timestamp reference planes, direction, frame-size/load profile, observation interval and applicable percentile or maximum. Obtain the radio receiver's buffering/scheduling tolerance and specification edition. The cited eCPRI transport document does not supply a general packet-delay-variation number to fill the gap. “Near zero” is neither an acceptance threshold nor a method. A deliberately selected engineering limit is acceptable if identified, justified and agreed; it must not be presented as a requirement copied from a standard that does not state it.

### 47.7 — A sample at the limit has no demonstrated reserve

One 1000 µs measurement equals a 1 ms bound, but does not establish the maximum under other loads, directions or failure paths, especially with measurement uncertainty. The constructed 2400 µs recovery path exceeds that delay requirement by 1400 µs. Also verify loss, time error, variation, traffic envelope and MTU: delay alone cannot pass the contract. Define which failure states are in scope and how temporary recovery interruption is treated; otherwise an apparently successful protection switch may violate the service promise.

### 47.8 — Five service obligations

Specify a measurable objective, map the mobile service/slice to transport treatment, enforce resource admission, provide the promised isolation, and assure the complete service over time. VPNs, QoS and traffic engineering implement parts of those obligations and expose useful counters/OAM. They do not automatically supply end-to-end assurance across radio, transport, core and application. Record who evaluates the evidence, detects a miss and changes or withdraws admission. A slice identifier is a mapping input, not proof of reserved capacity or regulatory separation.

## Chapter 48 — Microwave, satellite and fixed wireless access

### 48.1 — Four reasons to consider radio

Examples include rapid temporary deployment while civil work proceeds, crossing terrain where a trench is impractical, and serving a remote site without economical terrestrial access. A fourth is a service whose latency requirement favours a straighter radio route even though fibre exists. At the stated indices, 100 km of air has about 0.667 ms round-trip propagation, while 130 km of fibre has about 1.273 ms: approximately 0.606 ms less. Surveyed radio hops, equipment processing, availability and usable rate must still satisfy the service. On equal lengths, radio has about 32% less propagation delay, not 46.8% less; the latter comparison describes fibre's extra delay relative to radio.

### 48.2 — Read the particular authorisation

Identify country, band, assignment, licence product, equipment/installation category, channel width, e.i.r.p./conducted power and coordination rules. Ask who assesses interference, what register or priority applies, who resolves a complaint and what operational remedy exists. Check co-channel and adjacent-channel paths, antenna alignment and receiver susceptibility. All legal rights and limits are jurisdiction/product-specific. A licence does not make an interfering transmitter physically impossible; an exemption does not remove enforceable conditions. For the UK examples, use the complete applicable Ofcom row, not a copied power number.

### 48.3 — Availability at a useful rate

For each modulation state, obtain required signal quality, net capacity and the link margin after real losses. A suitable propagation model and local data estimate the fraction of time capacity falls below each threshold; equipment and non-propagation failures also matter to service availability. Choose the highest useful rate that satisfies the stated target and measurement period. The chapter's constructed radio offers 2000 Mbit/s at 99%, 1400 at 99.9%, and 350 at 99.99%; no state meets 99.999%. The 2000-to-350 reduction is 82.5%. Five nines permits 5.256 minutes of unavailability per 365-day year, but a long-run prediction is not a guarantee that every contractual year meets that limit.

### 48.4 — State the fixed quantities

With fixed conducted transmitter power, fixed dish areas/efficiencies and ideal far-field propagation, doubling frequency adds 6.02 dB free-space loss and 6.02 dB gain at each antenna. Net received power improves 6.02 dB. If e.i.r.p. is held fixed instead, the transmitter's permitted conducted power falls as its gain rises; fixed receive aperture then cancels the ideal frequency dependence. With fixed gains at both ends, received power falls 6.02 dB. Real range also depends on available output, noise/coding requirements, atmospheric absorption/rain, Fresnel clearance and alignment. The approximate beam narrows with frequency, increasing installation and mast-stability demands. “Higher frequency is better” is no more universal than “higher frequency is worse.”

### 48.5 — A lower bound can reject a claim

For a ground–satellite–ground request and reply with four ideal vertical legs, `4×20000/299792.458 = 0.266851 s`, or about **266.9 ms** propagation alone. A 120 ms RTT for that geometry is impossible before any processing or queuing. Ask whether the claim uses different endpoints, a one-way metric, another altitude or another path. Do not reject a different explicitly defined measurement by applying the wrong four-leg model to it.

### 48.6 — Protect the bridge case, then rank the remaining risks

A radio path bypassing the bridge can protect against its fibre cut if it has sufficient capacity and failover works. It may still share the equipment room, site power, building fire/flood risk, management credentials, change process, provider control plane and downstream backhaul. Moving the radio feed to independently backed power is a plausible improvement if the shared board dominates the service risk; separating change domains or site entry may be better under other evidence. Obtain as-built routes, power diagrams, failure/repair history, timing overlap and failover results before ranking. Annual probabilities that both paths suffer an outage sometime are not probabilities of simultaneous service loss: January and July outages can both occur while redundancy keeps service available.

## Chapter 49 — A working threat model

### 49.1 — Establish exposure
Inspect reachable management endpoints, known vulnerable versions, weak/reused credentials and configuration errors. For a constructed branch, evidence might be an authorised reachability test, a version/support inventory, an account audit without collecting plaintext passwords, and comparison of intended versus active policy. None establishes frequency across a sector. Incident records need an observation period, estate size and detection limitations; advisories establish plausible techniques. Add local dependencies rather than treating four prompts as exhaustive.

### 49.2 — Classify without assuming attribution
An Internet-wide vulnerability scan suggests opportunistic discovery; restrict exposure and patch, then check externally reachable services. A contractor copying a configuration is not automatically malicious: verify authority and purpose; least privilege and approval reduce misuse, while access logs support detection. Buying a foothold suggests financially motivated organised activity; contain credential scope, investigate the access and test lateral paths. A targeted carrier campaign may involve a state-backed actor, but targeting alone does not prove attribution. Combine prevention, segmentation, detection and protected recovery. State which mechanism each control changes and what evidence supports that effect.

### 49.3 — Count, then inspect effectiveness
A constructed inventory of eight entries has five preventive, two containment and one detection entry: 62.5%, 25%, 12.5%. That distribution is not a spending target; entries differ in coverage and may overlap. Suppose the one detection entry receives no management logs. Repair collection and response ownership, then test an authorised suspicious login before buying another duplicate feed. Retire a control only after checking its unique coverage, dependencies and obligations. Include recovery even though the toy inventory has only three labels.

### 49.4 — Supply-chain mechanisms
Check transit alteration, unauthorised local images, malicious vendor-signed code, signing-key theft, hardware implants and compromised build dependencies. Signature enforcement addresses the first two under its trust assumptions; the others require different evidence. Examples include supplier/build assurance, revocation and trusted recovery, physical provenance, component records and behaviour monitoring. None guarantees closure. Record implementation cost, recurring staffing, outage constraints and residual uncertainty; a universal price cannot be derived from a mechanism name.

### 49.5 — Make a tie-break visible
Use ten constructed (likelihood, impact) entries A=(3,3), B=(2,3), C=(3,2), D=(1,3), E=(3,1), F=(2,2), G=(1,2), H=(2,1), I=(1,1), J=(2,2). Products are 9,6,6,3,3,4,2,2,1,4. Eight rows share a product with another row. Product descending, then impact descending, then stable identifier gives A, B, C, F, J, D, E, G, H, I. The last tie-break is administrative, not evidence that F is riskier than J. Likelihood-first swaps B/C, D/E and G/H. State why your policy matches the decision; do not infer expected money loss from these ordinal scores. Relabelling ordered categories can even reverse product rankings.

### 49.6 — A board decision with limits
“An attacker able to interfere with this routing session could disrupt the connectivity supporting our customer service. Authorise the engineering time and change window to agree session protection with the peer, protect credentials and test rollback; the attached plan gives the cost and owner.” Add the exposure prerequisites and service redundancy instead of implying that absence of authentication proves imminent compromise. Session authentication does not establish the legitimacy of every announced prefix or full AS path; route-policy and origin-validation work remain separate. State untested platform behaviour and the absence of a defensible incident probability rather than inventing an expected loss.

## Chapter 50 — Cryptography for engineers

### 50.1 — Authenticate the reference
If an attacker can replace both the file and its digest, their altered pair remains consistent. Use an approved vendor signature with a separately trusted key, or an authenticated channel/reference whose trust does not depend on the suspect download. Check the exact version and bytes, signing identity, algorithm policy and revocation requirements. A valid digest or signature does not show that the approved software is safe or that the vendor's build system was uncompromised.

### 50.2 — Read the negotiation
TLS_AES_128_GCM_SHA256 specifies AES with a 128-bit key in GCM and SHA-256 for the key schedule; it does not identify the key-establishment group, PSK mode, certificate key/signature, validated service identity, client authentication, early-data use or application authorisation. Use endpoint handshake diagnostics and an authorised capture, with endpoint-side access for encrypted handshake details where needed. Check accepted policy and actual negotiation separately. A configured suite list is not evidence of a particular connection.

### 50.3 — Inspect the construction
TCP-AO is a useful worked example: RFC 5925 defines its message authentication and key management framework, and RFC 5926 specifies HMAC-SHA-1-96 and AES-128-CMAC-96. HMAC and CMAC are not a raw secret-prefix hash; the MD5/SHA-256 continuation demonstrated in Lab 51.1 does not directly forge these tags. Check the actual peer implementation, selected algorithm, truncation, key scope and rollover. This reasoning does not certify an implementation or make every use of SHA-1 interchangeable. Legacy TCP-MD5 follows a different construction in RFC 2385.

### 50.4 — Rollover and revocation failures
Prepare isolated old/new roots and leaves. Before rollover, accept only the intended old hierarchy; during a documented overlap, accept authorised old and new identities; after retirement, reject the old path while accepting the new one. Include wrong names, untrusted issuers, expired leaves and devices that missed the trust-store update. For revocation, distinguish a positive revoked result, a valid non-revoked result, a stale response and an unavailable responder. State which must reject and how any permitted temporary uncertainty is bounded and alerted. Test clocks, cached status and recovery; choose production behaviour from the application's risk and applicable policy rather than copying the lab default.

### 50.5 — Use the governing lifetime
The one-second request carries data needing 15 years of confidentiality. With a three-year migration lead time and a ten-year scenario horizon, 15+3 exceeds 10; waiting for long sessions is irrelevant. The immutable firmware verifier remains active for 12 years, beyond that assumed horizon. Decide its trust or replacement architecture before shipping; an ordinary update cannot fix the stipulated immutable path. Neither conclusion predicts when capable quantum hardware will exist. Archived signed material also needs an authenticity-preservation plan; an old date inside a later forged object is not trustworthy provenance.

### 50.6 — Prove activation
Construct a service with certificate A and renew the stored file to B while deliberately withholding reload. Probe the externally served certificate with the expected hostname and trust policy: require B's expected identity and fingerprint/serial, valid path and sufficient remaining lifetime at every termination point. The stale-A case must alert even though issuance succeeded. In a teaching plan, reserve seven days for repair and two days for escalation, so alert before fewer than nine days remain, plus monitoring uncertainty; derive real thresholds from operational lead times and certificate lifetime. Rehearse safe deployment and reload, validation, failed-reload rollback where still valid, and emergency reissuance. Do not roll back to an expired or revoked certificate.

## Chapter 51 — Identity and management

### 51.1 — Bound privilege
An administrative foothold may change forwarding, weaken filters, create credentials and delete local records, so it can undermine several controls at once. The impact is not categorically greater than every data-plane failure: loss of a critical service can already be severe. Three constructed boundaries are separate access/core identities, per-device emergency credentials and recovery backups in a different administrative trust domain. Verify effective permissions and recovery access rather than assuming a diagram enforces them.

### 51.2 — Build a failure matrix
A management VRF shares selected device, link and power dependencies; it may survive a production routing error that leaves its own path intact. A dedicated port on independent switching avoids some forwarding failures but may still depend on the target OS. A console server with independent access and power can survive loss of the production network, but cannot make an unpowered or wholly unresponsive target accept commands. Remote power control or a site visit may be required. A compromised administrator can affect any controls within that identity's reach, even across physically separate links. Record each site's actual dependencies and controlled test results; do not fill every “physical” cell with a tick.

### 51.3 — Reach the failed infrastructure
A constructed emergency path is an independently authenticated access service to an independently powered console server, then a local device recovery identity with credentials obtainable without the failed bastion or TACACS+ service. Preconfigure access restrictions, credential custody, console mappings, AAA failure behaviour and independent notification. Test an explicit AAA rejection separately from server unreachability: a denied user must not acquire a fallback privilege accidentally. Test command authorisation as well as login. This is a design example, not evidence that a particular platform's fallback works.

### 51.4 — Protect the exchange
Legacy TACACS+ obscures its body using a shared-secret-derived pad but lacks modern transport confidentiality and integrity. Repeated pad inputs expose reuse; known body positions allow controlled alteration in the toy model. Prefer supported, correctly authenticated RFC 9887 TLS transport; otherwise evaluate a supported secure tunnel and strictly restricted path as part of a documented migration. Sharing a production path increases the importance of cryptographic protection, but physical isolation never establishes that protection by itself. Confirm both endpoints and their exact releases.

### 51.5 — Remove one engineer
Disable the named identity and certificate issuance; revoke the person's relevant certificates/keys or authorised principals according to the enforcing server's features. Distribute and verify revocation data, remove alternate raw keys/tokens, terminate existing sessions and check delegated/forwarded access. Test that the departed identity fails while an authorised colleague succeeds on each platform and relevant path, including an initially offline device when it returns. Retain logs and time stamps. No elapsed-time result is claimed here: record the interval from decision to verified enforcement in an authorised exercise. Removing a shared CA is not selective offboarding.

### 51.6 — A sealed vault
Existing sessions or cached credentials may continue until expiry; new retrieval-dependent jobs fail, and sealed-store availability cannot be inferred from process health. Inventory which jobs require a fresh secret and whether cached use is permitted. Escalate through the documented recovery custodians; do not create an undocumented bypass during the incident. Afterwards review quorum custody, geographical/on-call availability, recovery dependencies, limited emergency credentials and monitoring. Auto-unseal may improve one failure mode while adding a KMS dependency; evaluate the whole path.

### 51.7 — Exercise break-glass
For a constructed quarterly test, isolate an agreed test device/path from primary AAA, keep an approved rollback and independent communications available, and use a named emergency procedure. Require successful scoped recovery access, rejection of unauthorised access, recorded commands and an alarm delivered through a tested independent route. Restore primary service, revoke/rotate used emergency material as the policy requires, and record date, scope and evidence. A 90-day interval with a defined scheduling allowance can be a local policy, not a universal standard; material changes require earlier retesting. Deliberately test alarm-path failure too, and assign an owner for missed evidence.

## Chapter 52 — Device and control-plane hardening

### 52.1 — A CPU can fill before the link
A packet requiring slow-path processing can consume CPU, queue or punt-channel capacity even when its byte rate is small. Routing timers may then expire while the high-speed transit link has spare capacity. Filter unnecessary destinations and services before the constrained resource, classify and police legitimate control traffic, and verify scheduling and per-peer isolation. A policer alone is a ceiling, not guaranteed service for BGP. In the retained IOS example, 16,000 bytes at 512,000 bit/s correspond to 16,000×8/512,000=0.25 seconds of token allowance; this is not a measured delay or a recommended setting.

### 52.2 — An infrastructure policy
Permit explicitly authorised peers, management sources and required diagnostic traffic to relevant device addresses; deny other traffic to infrastructure space; handle legitimate transit according to the remaining policy. A clean infrastructure aggregate simplifies a destination deny, not the whole filter. Include return ICMP for applicable path-MTU discovery and IPv6-specific requirements. Test authorised TCP/179 reachability and an actual BGP session separately: Lab 53.3 only performs the former. Also test prohibited sources and router-originated large packets across a smaller MTU.

### 52.3 — Match validation to the path
For a single-homed customer whose legitimate prefixes return through its ingress interface, strict uRPF can fit. Across asymmetric upstream or peer paths, loose uRPF avoids a strict interface mismatch but accepts spoofed sources covered by qualifying routes. Inspect default-route treatment. For multihomed customers, assess supported feasible/enhanced feasible-path behaviour or maintain allocation-based ingress prefix filters. The retained Linux experiment verifies its four traffic classes, not every vendor or IPv6 implementation. Test valid traffic on each failover path and invalid sources outside and, where finer binding exists, inside an allowed aggregate.

### 52.4 — Distance is not identity
With a directly connected GTSM peer sending TTL 255, a packet forwarded through an intervening router normally arrives with a lower value. An injector cannot choose an IPv4 TTL above 255. The receiver's exact acceptance threshold and multihop convention must be verified; tunnels and on-link sources can defeat a simplistic distance inference. A key-based authenticator provides a different check, and legitimate key possession still does not authorise arbitrary route announcements. Test the TTL boundary, wrong key and key rollover independently.

### 52.5 — Maintain a bounded assurance claim
An initial hardening change sets the intended state. Keeping it aligned requires versioned baselines, inventory, change review, exception ownership, periodic/event-driven drift checks and remediation. Missing or unreachable devices are unknown, not compliant. Pair configuration checks with operational evidence such as policer counters under an authorised convergence test, rejected unauthorised sessions and source-validation failover tests. Record the platform, release, date and limits; neither automation nor a passed questionnaire proves an uncompromised device.

## Chapter 53 — Firewalls and segmentation

### 53.1 — Size state as well as bandwidth
New connections consume setup processing and session state even when each carries few bytes. Exhausting either can deny new service below link capacity; some established flows may continue. Measure concurrent sessions, connection attempts/second, setup success, state memory and enabled-inspection capacity. For a constructed stable workload with 2,000 accepted new sessions/s and mean tracked lifetime 60 s, Little's law gives a mean 120,000 entries. This is an average under the stated assumptions, not a burst bound or an attack forecast; include half-open state, timeout behaviour and headroom.

### 53.2 — A directed zone matrix
The exercise gives no actual six rules, so use six explicit teaching flows: inside→DMZ HTTPS to the web service; DMZ→inside TCP/5432 to one database; guest→DMZ HTTPS to a public portal; OT→DMZ TCP/6514 to a log collector; inside→OT SSH from a maintenance bastion; OT→inside DNS only to designated resolvers. All other initiations are denied unless separately justified. These are directed permissions, not all-to-all relationships or a claim that an OT network should generally expose SSH. Preserve exact source/destination objects and services inside each matrix cell, document return-state handling, and verify that traffic crosses the enforcement point. Guest→inside and guest→OT remain denied. Membership changes require review.

### 53.3 — Trace first match and session state
If the broad rule matches the same direction, interfaces, identities, schedule and service, it accepts a new flow before the lower deny can act. Move the specific deny above the broad allow, or narrow the allow so the intended denial is unambiguous. Then check the new rule's identifier with fresh test sessions and the platform's existing-session re-evaluation behaviour. Do not clear every production session merely to test one policy change. Test intended permissions as well as the denial.

### 53.4 — Follow both tuples
In this illustrated IPv4 port-forward design, the client sends to 198.51.100.10:443 and the VIP translates to 10.10.30.10:443. The policy references the VIP in the stated FortiOS mode. Confirm mode, external address ownership/routing, ingress interface, VIP/port mapping, destination route and return path. Use release documentation, policy lookup/session diagnostics and scoped captures to establish which tuple each stage matches. A directly routed public server is a different publication design and may need no VIP. The printed panel is unexecuted on FortiOS.

### 53.5 — Build a workload acceptance envelope
20 Gb/s alone supplies no defensible inspected capacity. Specify packet-size and application distributions, proportion decrypted, cipher/key-exchange work, TLS handshakes/s, concurrent sessions, new-session rate, rule/profile load, logging and the required survivor condition. Compare the relevant published test conditions, then run the actual policy on a qualified platform with service-latency/loss and setup-success criteria. With two identical units each at 60% of the same limiting resource, loss of one would require 120% from the survivor under linear load assumptions. Nonlinear inspection or uneven distribution can be worse; reserve measured headroom rather than halving the headline blindly.

## Chapter 54 — Micro-segmentation and zero trust

### 54.1 — Authorise the resource
Zero trust removes implicit trust based solely on network location and grants scoped resource access using evaluated identity, device and contextual evidence. A packet arriving from the corporate LAN is no longer sufficient authority for access. This does not require an interactive login for every packet or forbid location as one policy signal; define session establishment, re-evaluation and revocation behaviour.

### 54.2 — Three limits
An IdP compromise can issue credible identities: limit token audiences and entitlements, separate privileged controls and rehearse issuer recovery. A stolen session can remain usable after authentication: bind it where supported, bound lifetime, protect endpoints and test revocation propagation. A legacy device may lack a usable identity/posture interface: use a supported gateway or network enforcement point with tightly defined flows and document what cannot be verified. Hardware-bound keys reduce extraction risk, but a compromised endpoint may still invoke them.

### 54.3 — Follow actual workload traffic
For cloud VMs, assess supported host enforcement or cloud-native workload controls, including migration and agent loss. For OT devices that cannot accept an agent, use a verified network/gateway boundary, ensuring local switching cannot bypass it. For physical servers, supported host enforcement may provide process context, while a fabric boundary can protect paths independent of the host. A hypervisor-only control does not automatically cover physical hosts or traffic contained within a guest. Mixed enforcement requires a common intent model and enough telemetry to identify which point denied a flow.

### 54.4 — Generate candidates, preserve intent
Use owned labels, an intended dependency list and observations covering known business cycles. Compare intended-and-seen, intended-but-quiet, seen-but-unapproved and unlabelled endpoints; assign a decision to every bucket. A seven-day trace cannot rule out a monthly billing dependency, and repeated attack traffic does not become authorised because it is frequent. Review candidates, test accepts/denies in a pilot, record rollback and inspect enforcement limits. Authorship, enforcement coverage and operational ownership can each stall a programme; no generator resolves them alone.

### 54.5 — Compare the deployed entitlement
A flat VPN can expose many network destinations; a restricted VPN may permit only the required service. ZTNA can narrow published resources, but broad entitlements, stolen multi-resource tokens or a vulnerable application can still create substantial exposure. Compare token scope, device checks, per-resource permissions, session revocation and application-side reach. Prioritise a ZTNA pilot when it demonstrably reduces the relevant exposure with acceptable application support, latency and failure behaviour; otherwise tighter VPN policy may deliver the immediate benefit. Name the pilot's positive and negative tests rather than awarding an improvement for replacing a product name.

## Chapter 55 — VPNs and encrypted transport

### 55.1 — Name the boundary
Two offices over the Internet: an authenticated IPsec or suitable supported tunnel protects selected site traffic from transit observation/modification; endpoint compromise remains. Leased dark fibre: MACsec between supported endpoints or qualified transport encryption can protect the exposed span; define carrier access, termination trust and recovery. Same-rack servers: application TLS may already protect the relevant data, while host/link controls address other threats; do not infer no threat merely from physical proximity. A developer reaching a cloud VPC needs an authenticated, narrowly authorised access path with device/session controls; VPN or broker choice follows the application and identity requirements. Record exceptions and avoid redundant layers without a purpose.

### 55.2 — Predict an omission, then test it
In an isolated endpoint configuration with no alternate/default objects, omitting the proposal reference can leave the intended policy unusable; inspect the active IKEv2 policy/proposal. Omitting the profile's local keyring reference can prevent the intended PSK lookup; inspect the profile, selected identity and bounded authentication diagnostics. Omitting the tunnel-protection attachment leaves the interface without that intended IPsec binding; inspect the interface and IPsec profile. Symptoms depend on remaining defaults and object selection, so deleting a line is not universally guaranteed to prevent every tunnel. Record parser warnings and running state, then positive/negative negotiation tests. The book's retained run reached IKE establishment but no installed ESP data path; this answer is a test plan, not new execution.

### 55.3 — AH versus ESP
AH authenticates the payload and protected immutable/predictable IP-header fields; address translation changes covered values and invalidates the check. ESP protects its defined payload, and tunnel-mode encrypted ESP protects an encapsulated inner IP header while leaving the new outer header visible. For an inherited AH service, identify its requirement and peers before changing it, check algorithm/support policy and NAT constraints, and plan an interoperable migration with rollback if warranted. “Uncommon” is not equivalent to withdrawn from the standard.

### 55.4 — Routing and selection
A route-based interface can simplify route changes, counters and dynamic routing; its negotiated selectors still constrain traffic. Policy-based protection selects traffic by policy, often requiring coordinated selectors. GRE can carry OSPF messages, with policy-based ESP protecting GRE between tunnel endpoints; dynamic routing is therefore not logically dependent on route-based IPsec. Account for GRE/IPsec mode, overhead, multicast handling, reachability and recursive-route prevention. Operational simplicity is the argument, not an impossibility claim.

### 55.5 — CBC overhead
For outer IPv4 without options: 20-byte outer IP + 8-byte ESP header + 16-byte IV + encrypted inner packet/padding/2-byte trailer + 16-byte truncated HMAC tag. The encrypted portion has at most 1,440 bytes and must be a multiple of 16. The largest inner packet is therefore 1,438 bytes; with fixed 20-byte inner IPv4 and 20-byte TCP headers, MSS=1,398 bytes. An inner packet of 1,439 needs 1,456 encrypted bytes and totals 1,516, exceeding the path. With UDP NAT-T the result would instead be 1,422/1,382. AES key length does not change its 16-byte block size; a different tag, outer IP version or encapsulation changes the answer.

### 55.6 — A directional observation
A rising local outbound counter supports encapsulation of the counted traffic. Zero inbound decapsulation does not identify one root cause: traffic may be lost in transit, rejected at the peer, lack a reply, return incorrectly, fail local authentication/replay checks, or be observed in the wrong SA/counter. Correlate a unique test flow and interval, then check remote underlay receipt and ESP acceptance with the matching SPI; also inspect local inbound errors and SA installation. Aggregate counters may include unrelated traffic. Only an application probe and correlated path evidence can support the intended service claim.

## Chapter 56 — DDoS response

### 56.1 — Locate, do not label
An 80% average link counter does not prove saturation: inspect queue drops, shorter-interval peaks, per-member load, upstream offered rate and application latency. New connections failing while existing ones work suggests setup-rate/state pressure; check table occupancy, allocation failures and policy counters. A search endpoint at 100% CPU with a 5% link suggests application processing pressure, but a bad deployment, slow dependency or legitimate surge can have that symptom. Correlate request cost, queues and a controlled baseline before attributing an attack.

### 56.2 — Filter before the constrained resource
Traffic discarded after a saturated access link has already consumed that link's capacity. A downstream scrubber may still protect application workers or a firewall's state table; it cannot recover the missing upstream bandwidth. Seek a filtering/diversion point before the constrained link, then verify the offered/delivered load and service result independently.

### 56.3 — Make a blackhole effective
Agree the authorised session/customer, covered address space, accepted host-route length, community, import/validation policy, discard installation and propagation scope. The signal must reach an enforcing point before the constrained link. Reconcile host-route exceptions with normal origin-validation policy without globally weakening it. Test an expendable address, observe upstream discard and collateral scope, and test withdrawal/expiry. Local advertisement alone cannot reveal remote rejection or installation failure; those may be silent locally, but upstream telemetry can expose them.

### 56.4 — A constructed serial budget
60+30+60+180+30=360 seconds, so mitigation would arrive after a 35-second burst under this serial model. Removing the 180-second human decision reduces it to 180 seconds, still too late. That is the largest numerical stage, but authorising automation requires safe scope and evidence; it is not automatically the first safe change. Measure actual stage overlap, export behaviour and sample-accumulation delay before selecting a redesign. The alternate 10+5+10+0+15=40-second scenario also misses this burst. An independent 500-packet/s, one-in-4096, ten-second sample has expected count 1.220703125; it is not a request-rate observation unless the packet mapping is stipulated.

### 56.5 — Equal capacity does not mean equal catchments
Without withdrawal, all three sites remain within capacity only while attack A satisfies 0.5A≤C, 0.3A≤C and 0.2A≤C: the largest is 2C. The naive aggregate answer 3C assumes a redistribution you were not given. Under the lab's rule—withdraw overloaded sites and redistribute proportionally—any A>2C first overloads site 1. The remaining shares become 0.6/0.4; site 2 then exceeds C, leaving site 3 with the whole attack, which exceeds C. Thus the full-survival threshold remains 2C; the added model reveals cascading total loss above it, not a different threshold for the same inputs. Equality assumes no headroom requirement and overload only above C. If “survives” means partial service while an overloaded site remains advertised, state that different criterion explicitly.

### 56.6 — Five gates
1. Declare the incident and target when service evidence and resource observations justify it; retain timestamps and uncertainty.
2. Apply a scoped low-collateral mitigation when a sufficiently specific signature, tested action and authority exist; watch legitimate-service probes and install counters.
3. Escalate upstream when the required mitigation point is outside local control or agreed early-warning criteria are met; use the independent contact path.
4. Blackhole only when its loss of the target is authorised and preferable to the wider expected harm; confirm exact prefix, expiry and upstream enforcement.
5. Communicate and preserve evidence according to the service and notification plan, distinguishing confirmed facts from hypotheses. Recovery needs a separate gate: withdraw temporary controls safely and verify service, not merely a quiet graph. These are paper decisions, not authorisation to generate an attack.

## Chapter 57 — DNS and the Internet edge as an attack surface

### 57.1 — The forged banking lookup

The attacker selects the connection destination, sees the arriving attempt and may deny service. Correct TLS name/chain verification still requires a certificate and usable key for the requested name. Plaintext traffic lacks that protection; a compromised trusted CA, attacker-controlled endpoint trust store, accepted warning or successful domain-validation takeover may defeat it. DNSSEC helps only where an authenticated signed chain is expected and validated; it cannot make every unsigned name safe.

### 57.2 — A resolver operated deliberately

An accidental open resolver lacks an intended public service and its operating controls. A deliberate public resolver needs capacity, abuse response, client/rate controls, cookies/TCP handling, patching, monitoring and staffing. Public accessibility is not itself the distinction. Verify your own recursion policy from an authorised external test point and check that authoritative service still works; do not use spoofed traffic against other networks.

### 57.3 — Validation outcomes

Secure: an RRset validates through a trusted chain. Insecure: an authenticated unsigned delegation means no chain extends to that RRset. Bogus: a chain should validate, but its required signature has expired or its DS/key relationship fails. Indeterminate: the resolver cannot establish whether the trusted chain should exist, for example with no suitable trust anchor. These are validation states rather than four DNS RCODEs. Operational examples are a stopped signer, a bad validator clock, and premature retirement of a key still referenced by the parent/caches.

### 57.4 — Delegation and key control

Changing NS redirects lookups after relevant cached data expires. With the genuine DS still present, the attacker's unsigned or mismatching zone fails validating resolution; non-validating clients may still be deceived. Changing DS to a key the attacker controls can create a valid chain to the hostile data; removing it can eventually create an insecure delegation. Cache/TTL and registry processing prevent a universal immediate cutover. Registry lock with an independent verification channel is a preventive control; external NS/DS and certificate monitoring supplies detection. The account's actual permissions decide which changes are possible.

### 57.5 — Forwarded mail

Assume the forwarder is not authorised in the original envelope domain's SPF and does not change that envelope sender: SPF fails at the next receiver. If the signed canonicalised content is unchanged, the original DKIM signature can survive. An aligned verified DKIM signature suffices for DMARC despite SPF failure. Content modification may break DKIM too. Rewriting the envelope to the forwarder's domain can restore SPF but does not establish alignment with the original visible From: domain. Receiver overrides are a separate delivery decision.

### 57.6 — The familiar name on an unfamiliar domain

Constructed paper example: From: “Aldergate Finance” <billing@aldergate-invoices.example>, with SPF and DKIM correctly configured for aldergate-invoices.example. DMARC can pass because those domains align. This authenticates the attacker's domain, not Aldergate's finance team. Monitoring confusable names in CT might expose certificate issuance, but needs a logged certificate and suitable matching; it does not guarantee email detection or blocking. Inspect the full address and verify changed payment details over an established independent channel. These reserved example names are not an instruction to register or send anything.

## Chapter 58 — Detection, response and network forensics

### 58.1 — Draw the blind spots

Constructed inventory: branch WAN egress exports sampled IPFIX at 1:2048 to collector A, with a 60-second active timeout and 30-day retention; a data-centre boundary exports unsampled flows to B. Missing paths include host-to-host traffic within an uninstrumented hypervisor, branch same-VLAN switching that never reaches the WAN router, and a direct cloud-service path with no customer exporter. Add exporter and collector loss counters, tunnel parsing depth, clock uncertainty and retention to the map. These are example entries, not observations of your estate.

### 58.2 — Ten packets

For independent Bernoulli packet sampling at 1:N, probability of at least one selected packet is 1−(1−1/N)^10. At N=2048 this is approximately 0.0048721, or 0.4872%. This excludes uncovered paths and export losses. Report: “No matching record was found in the retained data; a ten-packet exchange would have only about a 0.49% chance of packet selection under the stated model, so this does not rule out that exchange.” Do not use that formula for an unverified deterministic sampling algorithm.

### 58.3 — A detection contract

Example hypothesis: an unauthorised process makes repeated low-volume check-ins. Assumption: its observed inter-arrival gaps are fairly regular and reach the sensor. Blind spots: jitter, a single long-lived connection, permitted cloud destinations, and missing samples. Corroborate with process ancestry, scheduled-task inventory, identity events and destination ownership. Define a benign update-agent fixture and an evading beacon fixture alongside the triggering fixture. Endpoint evidence may itself be incomplete.

### 58.4 — Forty candidates

Enrich by host owner/role, approved scheduled task, process and signer, destination, interval and change history. Group by common deployment rather than treating forty alerts as forty incidents. Verify an inventory match against current host evidence; a familiar task name alone is insufficient. Prioritise unexplained processes, recent credential changes and active harm. The under-an-hour target requires accessible inventory and telemetry, not merely an analyst who works faster.

### 58.5 — Base-rate arithmetic

Let prevalence be π, recall r and false-positive rate f. Expected precision is rπ/[rπ+f(1−π)]. In the chapter's constructed 100,000-host population, r=0.30 and f=0.00005 give 15 true alerts and 4.9975 false alerts at π=0.0005: 75.009% precision, with 35 missed compromises. At π=0.00002 the expectations are 0.6 and 4.9999: 10.714% precision, with 1.4 missed compromises. Fractional values are expectations, not observed fractions of hosts. Prevalence alone or queue size alone cannot identify precision. Estimate from adjudicated cases, audit false negatives through independent discovery, and report uncertainty rather than inventing an estate prevalence. Consider added context and response capacity before raising thresholds.

### 58.6 — Expected services

Constructed pair: staff workstation→domain controller permits the organisation's documented authentication, directory and group-policy services; controller→workstation allows only explicitly required management/response paths. Record protocol, direction, owner, purpose and exceptions rather than assuming a reciprocal blanket permit. Validate against the actual Windows/application design and identity team. Unknown entries identify documentation or design work; they do not prove compromise. A service permitted by role can still be used maliciously.

### 58.7 — Containment decisions

Immediate examples: a non-safety-critical workstation is actively encrypting a shared drive, or a stolen session is exporting confidential records and can be revoked without disrupting life-safety functions. Apply the scoped approved control while preserving available telemetry. Scope-first examples: a historical low-confidence beacon alert with no evidence of active harm, or an uncertain signal on a safety-critical controller where abrupt disconnection could create greater harm. Set a short reassessment interval and involve the system's safety owner; “scope first” is not indefinite observation. The deciding inputs are current harm, confidence, intervention consequences, evidence and delegated authority.

## Chapter 59 — Security governance, compliance and assurance

### 59.1 — Different assurance questions

CSF 2.0 organises cybersecurity outcomes and risk-governance discussion; NIST supplies no CSF certification. A profile documents an organisation's chosen current/target outcomes, not proof that every control works. ISO/IEC 27001:2022 specifies an information security management system; a certificate supports conformity within its stated scope and audit process, not universal network security. CIS Controls v8.1 supplies prioritised safeguards and implementation groups; a mapping or self-assessment needs supporting implementation evidence. These can complement one another.

### 59.2 — Read the evidence

For ISO: check scope/service/legal entity, standard edition, validity/status, certification body/accreditation and relevant exclusions/interfaces in supporting scope material. For SOC 2: check system boundaries, report type/date or period, trust-services categories, opinion/test exceptions, and subservice/complementary user-entity controls. Type 1 design assurance is not Type 2 operating-effectiveness assurance. Neither promises that a future attack cannot succeed. Match the evidence to the actual service and your remaining responsibilities.

### 59.3 — An end-of-life switch

Constructed request: asset SW-17; unsupported firmware and no vendor fix; owner Head of Infrastructure, subject to delegated authority; restricted management VLAN and source ACL with dated verification attached; replacement ordered with delivery and migration milestones; expiry 30 days after the decision; early review on exploit evidence, isolation failure or delay. Credit only controls actually demonstrated. If no evidence exists, record it as pending and assess the unreduced risk. An internal signature cannot waive a binding statutory duty or unilaterally vary a customer contract. Record those shortfalls and refused requests for remediation/escalation; do not remove them from view. Exploitation in the estate requires incident handling.

### 59.4 — The falling average

Ask (1) whether the incident cohort and start/end definitions are comparable, (2) what independent evidence reveals missed or late discoveries, and (3) whether coverage, tail delay and workload improved alongside the mean. Worry about excluded slow incidents, shrinking sensor coverage, changed severity mix, or retrospective discoveries that never enter the dashboard. The lab's 124.9→65.7 hours is a 47.4% decrease, while misses rise 2→24. In reality the total undetected count is unknown; report validation and observed misses without pretending to know it.

### 59.5 — Do not choose a convenient clock

Monday 09:00 is an alert; Tuesday 16:40 is the recorded significance assessment; “Wednesday” lacks the exact time and facts needed for a personal-data-breach assessment. None supplies a universal deadline. A fictional 72-hour period from Monday 09:00 ends Thursday 09:00; one from Tuesday 16:40 ends Friday 16:40. The 31h40 difference illustrates why the legal trigger matters, not a right to select the later date. Record UTC or offset-aware timestamps, facts known at each point, applicable entity/service, threshold reasoning, decision maker, submissions and acknowledgements. Under applicable UK GDPR duties, notification is without undue delay and, where feasible, within 72 hours of awareness unless the reporting exception applies; PECR has its own public-communications-service breach rules. Use the current ICO/Ofcom guidance and Chapter 84 applicability analysis; EU NIS2 and DORA are separately scoped comparisons. Do not delay assessment or wait for root cause.

### 59.6 — First week and first year

Week one: appoint owners and reporting deputies, assess active compromise, restrict exposed management, mitigate applicable exploited vulnerabilities, identify critical services/dependencies, preserve logs and verify a recoverable backup. Start a dated risk/applicability register and a short incident exercise. Over the year, run continuous discovery, supported patch/replacement planning, identity improvement, detection validation, recovery exercises and architecture changes with measurable milestones. A demonstrated recovery path can justify early funding because it supports safe change and incident recovery. Urgent segmentation may still precede a wider recovery programme where it contains a current threat; these are not mutually exclusive investments. Give the board explicit consequences, costs and acceptance criteria rather than a universal order of purchases.

## Chapter 60 — The NOC and the operating model

### 60.1 — Who holds the seven duties?

Constructed hybrid model: monitoring and triage—NOC; urgent-action decision—duty incident lead; production change—authorised engineer within delegated runbooks; customer/regulator commitments—designated communications/reporting owner; unfamiliar diagnosis—engineering on-call; permanent fix—named service owner with a next-day deadline if safe. Every row needs a reachable backup and acknowledgement. Responsibility may be held through an explicit escalation route rather than direct privilege to do everything. An unspecified “engineering team” is not a named overnight route.

### 60.2 — Unknown is not zero

Use the constructed fibre-cut case if no real incident is available. At 02:40 confirmed affected users are unknown, while a credible dependency map exposes up to 18,000. A classifier that substitutes zero can under-escalate; a provisional risk-based rule can justify Sev1 and immediate investigation. At 04:55 evidence bounds impact to 310 users, permitting documented reclassification to Sev3 under the example thresholds. Keep both assessments and reasons. Other organisations' thresholds may differ. The preserved CA-03 correction matters: the percentage of provisional incidents later confirmed cannot by itself prove that a policy misses events.

### 60.3 — Coverage before roster construction

One seat: 168/37.5=4.48 FTE before absence. Example availability=(52−5.6−1)/52×0.97=0.8468846; required FTE=5.290. Five staff therefore leave about 0.290 FTE of average cover unprovided. Two identical seats require 10.58 FTE under these assumptions. Add handover overlap, relief for breaks, non-seat duties and contingency; then prove an actual shift assignment works with leave and skills. Do not round down or treat the average as a staffing guarantee. State whether any shortfall is met by a relief pool, agreed overtime, reduced coverage or unfilled duty.

### 60.4 — A pattern audit is not a legal approval

Record shift start/end times including overtime, consecutive nights/workdays, rotation direction/period, recovery intervals, weekends, handover overlap, workload and relief. A constructed four-consecutive-twelve-hour-night pattern conflicts with the online HSE summary's shorter night/run recommendations; an unstated switching recovery interval is unknown, not a pass. Check the complete guidance and applicable working-time rules with the responsible employer specialists. The arithmetic tool cannot establish worker health, travel, workload or a safe actual roster.

### 60.5 — Half as many pages

Measure nights disturbed, interruption duration and consecutive quiet nights; also review missed incidents and distribution of burden. Halving alerts by disabling a sensor can improve all recorded page statistics while making service detection worse. For independent Poisson arrivals, probability of any page in a night is 1−exp(−λ); reducing λ from 3 to 1.5 changes it from 95.02% to 77.69%, a relative reduction of 18.24%, not 50%. This is an arrival model, not a sleep/health outcome.

### 60.6 — Put a boundary on the runbook

Add entry/exclusion symptoms; devices and releases; pre-authorised actions and approval gates; read-only evidence to collect; expected output and stop criteria; tested rollback with point-of-no-return; escalation recipient/channel; owner; actual rehearsal date and evidence identifier. For a one-transit-down procedure, stop if the surviving path lacks capacity or expected reachability. Use an authorised isolated rehearsal before accepting production commands. A completed template with an invented rehearsal date is not a validated runbook.

### 60.7 — The cause chart

Audit the closure workflow and a representative ticket sample. Separate confirmed attribution from a forced guess, distinguish triggering change from software defect or other contributors, and retain later evidence-based revisions. The constructed 11/24 configuration labels yield 45.83%, but their arithmetic does not establish causation. Publish the distribution over all 24 incidents with unknown/unconfirmed cases shown and a separate confirmed-only distribution with its own denominator. Compare the same cohort after review; do not quietly replace history to make the chart tidier.

## Chapter 61 — Monitoring, telemetry and observability

### 61.1 — Start at the service

Constructed DNS service: latency—completed lookup durations from named client vantage points; traffic—query rate at each resolver; errors—timeouts/SERVFAIL and application-defined failed lookups; saturation—resolver CPU, queue and capacity indicators. State probe cadence, timeouts, interval aggregation and clock source. A 15-second export of a 60-second loss window is not 15-second fault resolution. NXDOMAIN is a legitimate answer for some queries, so do not classify every NXDOMAIN as service failure. Device evidence explains the service signal; it does not replace it.

### 61.2 — Inspect the deployed SNMP profile

Record security model/level and algorithms, access view, allowed manager paths, object identifiers and types, polling interval and interface-identity mapping. Prefer supported strong authPriv for confidential management data. Verify Counter64 objects and discontinuity handling with an authorised restart in a test environment. A negative raw difference may be reset or rollover; discard/rebaseline across a known discontinuity and never infer traffic from an ambiguous multiple wrap. At 10 Gb/s, a 32-bit octet range is exhausted in 2^32×8/10^10=3.4359738368 seconds.

### 61.3 — Five dial-out questions

Ask (1) who initiates transport and the Subscribe RPC, and which tunnel/profile is required; (2) which tested client/target versions interoperate; (3) which model versions, paths and encodings are supported; (4) how both identities and path authorisation are enforced; and (5) how buffering, reconnect, gaps, sampling and heartbeat behave. Require a representative capture and loss/reconnect test. A product label alone is insufficient procurement evidence.

### 61.4 — Count meaningful tuples

The existing full per-interface-queue set is 500×48×8=192,000. If C distinct circuit IDs could independently accompany every tuple, the Cartesian upper bound is 192,000C, but C and the attachment relationship are not supplied. With exactly one attachment per circuit and eight measured queues per circuit, the emitted count is 8C for that metric. With one circuit per interface and no other changes, a fixed circuit label need not increase the 192,000 current tuples; circuit moves create retained old tuples. Circuit ID is an entity label. Accept it if it represents a real measurement and useful queries within a measured budget; refuse copied aggregate counters misrepresented as per-circuit traffic or an unjustified storage burden. There is no automatic refusal from the label name.

### 61.5 — Three alert responsibilities

Specify (1) sustained measured loss above 0.02 with a chosen for-duration, (2) missing/stale measurement for each expected service/vantage pair, and (3) independent health of collection, evaluation and notification delivery. This is a rule design, not a qualified PromQL configuration. A bare absent() across all services cannot enumerate one missing member while others remain: reconcile an expected inventory or generate per-target rules. Test sustained loss, a short non-paging spike, metric disappearance, and recovery; also fault the alert pipeline itself. Record actual evaluation/notification times, not just the nominal duration.

### 61.6 — Page before customer impact

Constructed candidates: a surviving transit is close to its failure-mode capacity; generator fuel is shorter than replenishment lead time; a confirmed compromise is progressing; or independent monitoring shows the alert path is unavailable. Each rule needs an owner, an authorised action and a latest-safe-action time. A low-priority redundancy loss with ample capacity and a booked repair may be a ticket rather than a page. Severity follows consequences and urgency, not the metric's name.

### 61.7 — Four per cent and drops can coexist

Inspect queue occupancy maxima or histograms with known acquisition resolution, queue-specific drop counters, policer drops, physical errors and the affected traffic path. Correlate with short-interval rates and controlled probes. A high-water mark supports that a queue reached a depth during its window; it does not identify the flow, duration or cause by itself. A mean is not a peak, but low average utilisation also permits loss from faults unrelated to bursts. Do not declare the dashboard wrong before checking its interval and measurement point.

## Chapter 62 — Flow, logs and packet capture

### 62.1 — Three chances, not a hard floor

Under independent selection, P=1−(1999/2000)^3=0.001499250125, or 0.149925%. The exchange is missed about 99.850075% of the time even before export loss. A fixed-skip sampler instead selects packet positions congruent to its phase modulo 2000. Conditional on known positions/phase, the outcome is deterministic. Across a uniform random phase, probability is the number of distinct occupied residues divided by 2000; three consecutive packets occupy three residues, but three packets separated by 2000 occupy one. Repeated periodic bursts need not provide independent chances.

### 62.2 — A usage dispute

Identify the contracted measurement point, direction, time zone/window, billable units and handling of headers, retransmissions, duplicates and discarded traffic. Retain raw records, observation-domain/exporter identity, templates, sample-selection/scaling metadata, counter discontinuities, clock uncertainty, loss counters and historical customer/NAT mappings. Reconcile with independent authoritative counters and explain gaps. Sampling precision, rounding and dispute rules must satisfy the accounting agreement; an attractive graph is not an exact invoice ledger.

### 62.3 — Test each delivery boundary

In an isolated authorised pipeline, generate unique event IDs at a known rate; record source acknowledgements separately from receiver receipt, durable persistence and searchable indexing. Interrupt the sink, restore it, and restart selected components to exercise volatile-state loss. Compare ID sets, missing/duplicate IDs and delay distributions, not just equal total counts. At 8000 events/s, 15 minutes creates 7.2 million events; 400 payload bytes each require 2.88 GB before overhead. A 10000 events/s sink has 2000 events/s spare capacity and needs 3600 seconds to drain while input continues. This is constructed arithmetic, not a performed outage test.

### 62.4 — Capture both directions

Worst-case offered wire rate is 20 Gb/s for a full-duplex 10 Gb/s link. One 10 Gb/s mirror output is the first bottleneck in that proposed design. A design with adequate output and receive capacity still needs packet-rate and storage qualification. At 64-byte Ethernet frames plus 20 bytes of wire overhead, aggregate rate is 29.7619 million frames/s; 4096 empty descriptors, one per frame with no service, fill in 137.6256 microseconds. For a separate uniform 800-byte frame workload with 20 wire-overhead bytes and 16 pcap record-header bytes, full capture is about 2.4878 GB/s or 8.9561 TB/hour. A 128-byte snaplen reduces this to 0.4390 GB/s or 1.5805 TB/hour, preserving only 17.65% of full-file bytes. Accept that snaplen only if the required headers fit; full payload investigation needs more. Real frames/FCS, queues, offload and file format must be measured.

### 62.5 — A retransmission label is an inference

At the host, record checksum/segmentation/receive offloads, capture direction, process/interface choice and loss counters; a pre-offload large packet or unfinished checksum may differ from the wire. At the tap, establish both directions, optical/copy budget, capture loss, timestamp uncertainty and truncation. Correlate sequence ranges, acknowledgements and timing across compatible points. A duplicate segment may reflect a genuine retransmission, reordering, a capture duplicate or another observation artefact. A missing original in one trace does not locate the loss without evidence that the trace should have contained it.

## Chapter 63 — Troubleshooting as a discipline

### 63.1 — A test that changes the investigation

Constructed case: a branch HTTPS transfer stalls after a small response, while other sites work. Define source, destination name and resolved IP, VRF, time/clock quality, protocol, sizes and affected application. Hypotheses include a PMTU black hole, server-side limits and selective path loss. Capture both endpoints during an authorised transfer and repeat with a bounded smaller transport size. Repeated large segments with no acknowledgement, a clean smaller transfer and missing/blocked relevant ICMP support the MTU lead; an explicit server error instead redirects the investigation. A ping using the same small size regardless of its result does not discriminate among these three hypotheses. Record any mitigation, rerun the original transfer and check affected peer services. This is an example write-up, not an executed incident.

### 63.2 — Large-transfer failure

Candidates: PMTU/encapsulation mismatch, application or proxy size limit, congestion/loss under sustained load. A synchronised endpoint capture of the failing transfer, with application/server logs, is a strong first test: it distinguishes a protocol-level rejection from transport retransmission or stalled acknowledgements. It may not distinguish MTU loss from a selective policer. A follow-up bounded size sweep and sender adaptation test is then warranted. One successful packet establishes a tested size, not the exact path MTU; ICMP and application traffic may choose different paths. State IPv4 fragmentation/DF behaviour or IPv6 source packetisation explicitly.

### 63.3 — Scope is a weight

One user: compare host stack/authentication and access-port state; a source-specific core ACL or ECMP member remains possible. Test a known-good host on the same access path with controlled identity and policy. One site: compare uplink/gateway and local DNS; shared service policy affecting that site's addresses remains possible. Test direct service reachability with hostname/TLS identity preserved, then DNS. Everywhere: examine shared resolver, authentication and common egress dependencies; a widespread endpoint update is also possible. Compare independent services and vantage points before choosing a shared network cause. Each result changes a ranked list; none of the scopes is a proof.

### 63.4 — Define the window before calculating

For an illustrative rate of 40 changes/day, a preceding 15-minute interval has q=1−exp(−40/96)=0.340759; a symmetric 15 minutes either side has q=1−exp(−40/48)=0.565402. If a causal change always lies in the chosen window, likelihood ratios are 2.9346 and 1.7687. A 70% prior becomes 87.2570% and 80.4949%, respectively. LR=2 occurs at 96ln2=66.5421 changes/day for the preceding interval and 48ln2=33.2711 for the symmetric interval. If causal-window probability is a, LR=a/q. Estimate a relevant service change rate and inspect the actual mechanism; do not substitute a whole-company count as though all changes could affect the service.

### 63.5 — Quiet is conditional evidence

Pre-position remote logs with clock-quality data, link/optical/error counters, device uptime and power/temperature evidence, plus an independently monitored observer. Use a rotating capture or event-triggered collection when it can expose the hypothesised mechanism. Under a stationary Poisson rate of 2/day and complete observation, three quiet days have likelihood exp(−6)=0.00247875 if the fault persists. With prior repair probability 0.5 and guaranteed silence after repair, posterior repair probability is 1/(1+exp(−6))=99.7527%. That prior matters: with prior 0.1 it is 97.8178%. A 95% posterior under the first model needs ln19/2=1.47222 days; a 5% miss-probability criterion needs ln20/2=1.49787 days. Choose and document one criterion, reproduce representative load, and preserve uncertainty if the process or observer assumptions fail.

### 63.6 — Escalate the investigation

Trigger immediately on discovering that the next discriminating test requires access you do not have; escalate major/widening or safety impact in parallel. Constructed handoff: 'BranchB VLAN20 cannot complete HTTPS to the named service since 14:05 UTC. Verified: small requests succeed; repeated larger transfers stall; local link counters show no new errors during the captured interval. Hypotheses: path MTU handling, selective upstream policy, server/proxy limit. Unresolved: provider ingress/egress captures and policy counters; no access to that boundary. Current mitigation: users on the approved alternate path, with capacity being watched. Requested next action: provider compare the supplied flow/time/size against its boundary evidence. Owner and next update time are recorded.' Attach evidence identifiers and clock uncertainty, not credentials or unnecessary personal payload.

## Chapter 64 — Change management

### 64.1 — Workflow and risk are separate

Constructed examples: an already qualified access-port description update within an approved target/version envelope can be standard and low risk; a novel core route-policy migration is normal and high risk; urgent isolation of a compromised management endpoint can be emergency and high risk. A different device release or target invalidates the standard envelope. New export dependencies or missing recovery access invalidate the migration assessment. If the isolation would disable a safety-critical service, the emergency authority must reassess harm and scope. Repetition, urgency and short diffs are not risk ratings by themselves.

### 64.2 — An executable MOP needs a chosen release

Use an isolated authorised topology with identified platform/image hashes, feature licences and interface/VRF inventory. Record the intended prefixes, protected prefixes/services, propagation boundaries, exact rendered policy and digest, executor authority, management path, configuration persistence and recovery method. Capture initial routes and service transactions; apply to the approved first target; read back the configuration; compare route attributes, forwarding entries and end-to-end service results; then either stop/recover or authorise the next stage. Include a latest recovery decision time and independent stop channel. Platform commands are deliberately not invented here: retain release documentation and actual lab output before labelling a command sequence qualified. A textual plan is not a run.

### 64.3 — Extend the acceptance contract

Add a validated forbidden_routes set and reject overlap with required_routes as contradictory policy. For a valid observed route list, its intersection with forbidden_routes must be empty; missing or malformed route data is UNKNOWN. Record baseline and after probe service/vantage identities, sample counts, start/end times, clock basis and collection health. Require comparable declared duration, load and probe scheme; non-overlapping before/after periods are expected, whereas an after probe window that does not cover the intended acceptance period is invalid. Compute d=lost_after/sent_after−lost_before/sent_before only for valid, positive integer counts and matching scope. PASS requires both the absolute loss bound and d<=the approved increase. A 0/1000 baseline and 1/1000 after give an increase 0.001: fail a 0.0005 increase gate even though the absolute 0.001 gate passes. Missing baseline, zero sent, different service or stale evidence is UNKNOWN; unexpected forbidden route is FAIL. Keep both failed and unknown checks visible. Add boundary and malformed-input tests before treating an implementation as complete; these instructions do not claim the extension has been executed.

### 64.4 — Recovery range

Construct a 120-minute window, 2-minute decision, recovery between 18 and 35 minutes, 12-minute verification and 8-minute contingency. Using the defensible 35-minute bound reserves 57 minutes and puts the latest start of the decision process at minute 63. The midpoint 26.5 reserves 48.5 and puts it at 71.5, leaving an 8.5-minute shortfall if recovery takes 35. A range midpoint is not a measured mean, and neither is an upper bound. Explain what evidence supports 35 and what happens beyond it; revise or decline the change if no credible recovery budget fits.

### 64.5 — Shared dependencies

Represent 'fault here may affect there' consistently: DNS service→dependent service, management service→recovery/operation capability where the model represents that consequence. Do not imply that losing management instantly stops forwarding. Distinguish observed inventory/capture/configuration edges, inferred ownership relationships and unknown supplier internals. A supposed route-reflector filter is a scope-control assumption until an authorised test shows intended and forbidden route propagation under relevant normal/failure states. Compute the union of potentially affected service IDs, not a sum along paths that double-counts shared customers. A missing dependency makes the map incomplete, not safe.

### 64.6 — Six-week freeze

Define services, start/expiry, owner, emergency authority and monitoring before the freeze. In week two, assess a critical patch using applicability, exposure, exploitation evidence, compensating controls, vendor qualification, canary coverage and recovery. Compare patch risk with continued exposure; approve a bounded exception if justified, with named authority, target artefact, staged execution and service gates. If deferring, record the residual risk, temporary measures and next review, subject to non-waivable duties. Before expiry, revalidate queued changes against current state and dependencies; schedule capacity-supported batches with recovery time. A thaw is not a single mass deployment.

## Chapter 65 — Incidents, outages and post-incident review

### 65.1 — Declaration under uncertainty

Constructed criterion: independently observed failure of a critical transaction from two sites, credible evidence of severe compromise, or loss of essential redundancy with plausible major impact triggers provisional declaration. A shared collector failure remains a candidate, so mobilisation initially includes an incident coordinator plus monitoring and service/network responders, expanding with evidence. Investigation and pre-authorised protective actions can start before declaration. Stand down the service incident only after independent checks establish the relevant service scope as healthy and no other severe trigger remains; retain a monitoring incident, owner and restoration checks if the collector failed. Record why the provisional severity changed.

### 65.2 — Five people, explicit handover

Assign one commander, one technical lead, one additional technical responder, one communications lead and one scribe. Pre-delegate deputy authority to the technical lead, with a different qualified person taking technical coordination when available. If the commander disappears, the deputy explicitly accepts command under the plan and announces it on the surviving bridge. If production identity fails, use rehearsed, protected emergency identities and an independently reachable access/communications path; another application behind the same SSO is insufficient. Account for workload after losing a person and request relief. Never invent credentials or assume a break-glass login works merely because it is documented.

### 65.3 — Two recovery decisions

For route-policy rollback, compare the last approved artefact, actual partial deployment, propagation and state compatibility; verify independent access, rollback authority and adequate recovery time. Apply a scoped, qualified recovery, then check required routes, forwarding and original service transactions. For a suspected compromised host, reconnecting may restore reachability while restoring attacker access. The incident/security lead and service owner must assess isolation harm, evidence preservation, eradication/rebuild, credentials, lateral exposure and staged service checks. Active harm can require prompt containment before complete scoping. Both actions need authority and result verification, but 'back online' is not an adequate common acceptance criterion.

### 65.4 — Ordering with bounds

The supplied router event interval is [02:39:59,02:40:03]UTC and the probe interval [02:40:02,02:40:04]UTC. They overlap, so strict order is unresolved. A constructed improved router uncertainty of 0.5 seconds around its corrected 02:40:01 time gives[02:40:00.5,02:40:01.5], entirely before the unchanged probe interval. That establishes order only if independent clock/timestamping evidence justifies the tighter bound for the event interval. Do not type 0.5 merely to obtain BEFORE. Causation additionally needs a plausible mechanism, matched affected service, state history and evidence against alternatives; an earlier unrelated log entry is not the cause.

### 65.5 — Renewal is verified where used

Delivery: inventory named production and standby endpoints, hostname/SNI, trust policy, expected fingerprints or authorised key/certificate policy, owner and renewal/activation path. Acceptance: controlled renewal activates at every required endpoint; fresh independent observations validate the intended chain/identity and validity horizon. Negative cases include an old certificate still served, omitted endpoint, stale observation, failed validation and failed alert delivery. A healthy control must not page. Measure detection-to-recipient delay and record evidence, not just successful issuance. Follow up after endpoint or trust-store changes and on a scheduled sample. An undiscovered supplier endpoint remains a justified stated coverage risk, with an owner and discovery action; it cannot be reported as monitored.

### 65.6 — A dated outage and a local test

Meta's5October2021 account reports a backbone-disconnecting command, an audit-tool defect, DNS route withdrawal and impaired normal/out-of-band recovery access. Our inference is that a recovery path must be tested as an end-to-end dependency chain. In an isolated authorised replica, remove the primary identity/DNS/network dependencies while preserving a controlled stop path; attempt the documented emergency access, retrieve recovery artefacts and execute a harmless read-only check. Record which dependency actually failed and the time to usable access. Passing that rehearsal covers its replica and conditions, not the historical outage or every production emergency. Do not disable production identity merely to demonstrate the lesson.

## Chapter 66 — Capacity planning

### 66.1 — Which summary answers the service question?

A daily mean describes average use across that day. A maximum hourly mean identifies the busiest averaged hour but hides its bursts. A busy-hour p95 describes a chosen distribution within a chosen hour; its value depends on sample interval, selection and estimator. None alone gives application latency or survival after a component failure.

Retain aligned time series and examine the binding direction, service class and failure state. Measure the relevant latency/loss objective as well as utilisation. State whether a number is instantaneous, averaged or percentile-based before using it to justify capacity.

### 66.2 — Percentiles do not add

Consider 100 aligned samples on each of two links: each has 95 samples of 20 and five of 80. Under linear interpolation at rank `(n−1)×0.95 = 94.05`, each p95 is 23, and adding their p95s gives 46.

If the five peaks on each link occur at different times, the summed series has 90 samples of 40 and ten of 100: its p95 is 100. If they coincide, it has 95 samples of 40 and five of 160: its p95 is 46, although its maximum is 160. These are explicitly chosen data and an explicitly chosen estimator. A nearest-rank implementation gives different boundary values but does not make percentile addition generally valid. Sum aligned observations first when asking about aggregate demand.

### 66.3 — Growth and decision time

For current load 45, annual compound growth 20% and a load threshold of 70, `t = ln(70/45)/ln(1.2) = 2.42337 years`. If the capacity must be in service by that crossing and the complete delivery allowance is six months, the latest start is `1.92337 years` from now, before any extra contingency.

If 70 is instead defined as the point at which an order is triggered, do not silently reinterpret it as a service limit and subtract the same allowance again. State the actual service limit, required completion date and what the lead time includes. A growth assumption supplies a scenario, not a measured future date.

### 66.4 — Failure and maintenance

Draw the allowed failure/maintenance state before redistributing load. A disconnected demand cannot be carried by adding utilisation figures on an unrelated surviving link. Identify reachable routes, actual traffic movement, class/queue constraints and shared power, transport or device dependencies. Check survivor performance and recovery against the service objective. A table whose total capacity exceeds total demand can still describe an unusable network.

### 66.5 — A deliverable upgrade

One explicit teaching schedule is approval one month, design one, delivery three, installation one and acceptance one, with a two-month permit task running inside the three-month delivery interval. The serial path is seven months, plus a selected one-month contingency: eight. If the permit cannot start until delivery ends, the schedule changes; concurrency is an assumption to verify.

Record owners, prerequisites, committed versus estimated dates, money and staff requirements, acceptance and a trigger for the interim option. Define what happens if the delivery date slips. A diagram with no owner or acceptance time is not an executable plan.

## Chapter 67 — Source of truth: documentation as data

### 67.1 — A small authoritative spreadsheet

Define namespace/VRF, address or prefix, status, assignment, owner, purpose, approval reference and effective/expiry dates in typed columns with controlled values. Separate observed fields and collection times from approved allocations. Restrict editors, review changes, retain version history and backups, and validate address syntax, namespace-specific duplicates and forbidden allocations before publishing a revision. A central allocation process must prevent two concurrent editors reserving the same address; a colour convention is insufficient. Move to a suitable IPAM/API workflow when concurrency, permissions, audit, relationships or consumer integration exceed what the controlled sheet can reliably enforce. Size alone is not the sole trigger.

### 67.2 — Three clocks for one interface

Constructed record: intended description approved at 09:00 UTC in revision 17, effective at 10:00; observed from device/interface ID at 10:03, received by the collector at 10:03:02; database import completed 10:04. Keep all relevant times and clock uncertainty. A later database tag edit at 10:05 does not refresh the device observation or create a new design approval. Distinguish admin-enabled intent from link-operational evidence. Before deployment, confirm the expected revision and observation age against the applicable policy.

### 67.3 — Five useful objects

Device: stable identity, serial/platform and management relationship support replacement and executor selection. Interface: identity and design role support rendering and monitoring joins. Prefix: namespace, reservation and assignment support conflict-free allocation. Circuit: providerID, endpoints and contracted capacity support capacity decisions and escalation. Service: dependency set, owner and acceptance probes support impact assessment. One uncertain field might be the supplier circuit's physical duct route; mark it unknown with the evidence request and owner. An assumed separate duct must not silently become a verified diversity attribute.

### 67.4 — Test the namespace policy

In an isolated instance of the pinned release, with recorded settings, attempt the same ordinary host address twice in one VRF with enforce_unique enabled: expect rejection. Repeat with the setting disabled and document the intentional permissive result. The same host in different VRFs can be legitimate. Repeat the global-table case with ENFORCE_GLOBAL_UNIQUE true/false. For shared-address roles, test both records with permitted non-unique roles and a mixed shared/ordinary pair; inspect the release's actual validation rules. Test repeated identical prefixes separately from nested prefixes, which uniqueness is not a general ban on. These are acceptance cases to execute, not claims that a server was run here.

### 67.5 — Reconciliation by field

Descriptions: compare the managed intended field with a fresh complete observation, then propose a reviewed correction or approved intent revision. Operational state: retain observed value and time; do not overwrite it with desired admin state. Address assignments: require namespace, ownership and current approved revision, and assess service/duplicate-address effects before changing either side. Serial number: treat a discrepancy as possible replacement or collection error requiring evidence, not a reason to rewrite the physical asset automatically. Version conflict, ambiguous identity, incomplete observation or a current emergency exception blocks automatic correction and names an owner. After authorised reconciliation, re-read state and verify the service; retain both prior evidence and the decision.

## Chapter 68 — Configuration management with Ansible and Jinja

### 68.1 — Three distinct properties

An imperative function can read a managed description and issue an exact replacement only when it differs; with a qualified adapter and no competing writer, repeated application leaves that managed description unchanged. A declarative play stating a desired file can still trigger an unconditional service restart on every invocation if other tasks demand it. The file state may be idempotent while session disruption repeats. State the resource, supported initial conditions, side effects and concurrency model; identical render bytes alone establish none of the device behaviour.

### 68.2 — Resolve before applying

Inspect the final inventory, host/group variable precedence, connection plugin, network_os, collection versions and exact platform/release. Match the approved target identity against independently verified transport identity and observed platform capabilities. Split or fail unsupported hosts rather than letting a generic 'leaves' tag select an IOS XE module for SR Linux. Bind the final target list and variables to approval; reject empty, broadened or stale selections. Check-mode output does not establish the remote platform contract.

### 68.3 — Local evidence and the device boundary

Follow the lab in its Linux/WSL controller environment, using a private scratch destination. Record its initial absence, first actual run and file digest/mode, second run with unchanged content/state, deliberate harmless drift, check/diff prediction, actual repair and read-back. Retain command versions and outcomes. For a device also require trusted target identity, supported NOS/module versions, current configuration/context, actual parser acceptance, independent operational read-back, drift/removal/transition tests, failure recovery, persistence and service checks. This answer describes evidence to collect; it does not claim new Ansible or device runs.

### 68.4 — Map the service, not just the strings

The common intent is an untagged attachment. IOS XE/EOS use access mode and a VLAN object; the SR Linux profile uses an untagged bridged subinterface in a mac-vrf; Junos ELS uses an ethernet-switching access membership. The service name VLAN30 in SR Linux is not an ingress tag. A new requirement such as accepting priority-tagged frames, applying a particular ingress policing behaviour or preserving a specific spanning-tree protection needs a capability/semantic decision and platform tests. Swapping the template cannot supply missing hardware or identical default behaviour.

### 68.5 — Removing an address

Identify the owned interface/VRF and exact old address, dependent routing/management sessions and approved replacement. Use a platform-qualified deletion operation; omission from an additive render is not deletion. Precheck independent access, remaining reachability and any necessary ordering. Retain the prior state and a tested recovery route, including the case where re-adding the address cannot restore lost sessions. Read back running state, verify routes and application traffic, then apply the approved persistence step and verify it. A reboot/persistence test belongs in an isolated qualified environment, not an improvised production acceptance step.

## Chapter 69 — Models and management APIs

### 69.1 — A lost reply is an unresolved state

For the third device, possible states include request not received, rejected, accepted but still applying operational effects, or committed with reply lost. If a confirmed commit was used, it may still be pending confirmation or have reverted after session loss/timeout according to its persistence contract. The first two devices may also be on different persistence or service states despite successful commits. Retain operation IDs, request digest, timestamps, target identity and timer state; read authoritative configuration, operation history and independent service observations. Stop expansion. Reconcile the actual state before deciding to confirm, compensate or retry, and preserve safe intermediate routing states. There is no fleet-atomic result implied by three client calls.

### 69.2 — Enabled does not mean usable

The interface may be administratively enabled while its cable is absent, optic incompatible, peer down, VLAN/VRF assignment wrong, route unresolved or policy denying the service. The schema may permit an enabled interface that is simply the wrong target. Check identity, physical/operational state, intended attachment, forwarding and the original transaction from the required vantage point. Configuration read-back and customer-service evidence belong in separate fields.

### 69.3 — A meaningful negative case

For the supplied Python model, submit {'name':'Ethernet 1','enabled':'false','mode':'routed'} and require a type error: a non-empty string must not be silently interpreted as true. Also distinguish bool from an integer MTU in Python. State that these rules apply to this small schema. They do not validate YANG must/when/leafref constraints, model deviations or YANG JSON encoding; in particular, RFC 7951 encodes int64, uint64 and decimal64 as strings. A real adapter must validate the selected model and encoding before server/device/service checks.

## Chapter 70 — Python for network engineers

### 70.1 — A BGP collector contract

Require device identity, NOS/driver version, VRF/routing instance, address family, peer address and AS, local AS, session state, collection time and relevant uptime/reset information. For prefix counts, specify received versus accepted versus installed and per-family scope. A missing unsupported counter is UNKNOWN, not zero. Test empty/partial responses, wrong family, disabled peer, reset during collection, privilege denial, transport failure and unexpected schema. Compare independent device evidence on each qualified platform. A common getter name alone does not establish identical semantics or prove forwarding.

### 70.2 — Truncation can look plausible

Create a synthetic fixture that ends after the first complete interface row while two specific interfaces are expected. A parser may return a valid one-row list; the collector's expected-interface check must reject the missing second port. Also truncate within a row and in trailing text. If all expected ports happened to appear before truncation, the current subset check may pass: it does not prove the entire device output is complete. A broader completeness requirement needs additional framing, expected inventory or an independent structured response contract. Keep the original fixture and label mutations synthetic; do not present a constructed failure as a device capture.

### 70.3 — Same exception, different state

In the in-memory model, timeout before mutation can leave the old state, whereas apply-then-timeout can leave the intended state despite no acknowledgement. Partial mutation can leave one field changed. Compare learner-visible simulator ground truth with what the controller actually observes. If the post-read succeeds, report its scoped result; if it fails, retain UNKNOWN rather than inferring unchanged. A local coroutine cancellation demonstrates that simulator's scheduling, not the cancellation semantics of a remote CLI or NOS.

### 70.4 — Dependency-aware stop rules

For independent read-only collection, permit bounded continuation to other sites while retaining each failure and enforcing an incident/concurrency budget. Even reads can load AAA or device CPUs, so cap retries. For changes to a redundancy pair, one uncertain outcome stops the partner and dependent changes until authoritative state and service checks reconcile it. Acknowledged earlier targets still need their required verification. Preserve the exact target list, not-started entries and mixed versions. Resume only under the approved current scope and recovery budget.

### 70.5 — A maintained tool

Publish a tested Python/OS environment, pinned dependency and parser/template versions, install steps, CLI help, schema/version, synthetic example and expected outputs. Define exit 0 as the documented complete successful operation, 1 as incident/incomplete collection and 2 as invalid invocation if adopting the simulation's convention; parsed 'down' may still be successful collection, so include separate health fields. Retain operation IDs, target/revision, redacted evidence, timestamps, parser versions and per-target outcomes under role-based access and a justified retention period. Protect secrets and raw payload, test upgrade/rollback and name a maintenance owner. A lock file is reproducibility evidence, not a perpetual security guarantee.

## Chapter 71 — Event-driven automation and closed loops

### 71.1 — Outage backlog

State the arrival rate during the ten-minute outage. If it remains 300 events/s with zero processing, the outage alone adds 180000 events. At 2 KiB payload plus an illustrative 512-byte per-record overhead, one stored copy is 460800000 bytes=439.453125 MiB; three copies total about 1.28746 GiB before further indexes/filesystem overhead. If the original 12000-event backlog was already present, use 192000 events:468.75 MiB per copy. After restoration at 100 processed/s and 50 arriving/s, draining 180000 takes 3600 seconds; 192000 takes 3840 seconds. If arrival remains 300, the backlog keeps growing. Choose an age/replay policy because old alarms may no longer authorise action.

### 71.2 — Authenticate the channel, validate the event

Carry producer identity, eventID, schema/type, source time and uncertainty, receipt time, installation/sensor ID, asset mapping revision and original evidence reference. Establish producer identity through a configured authentication mechanism, not a self-asserted JSON field; authorise its scope. A one-hour-old alarm may be valuable history but must not automatically re-execute an old mitigation. Reconcile current sensor/service state and intent/approval versions; retain the old event and the reason for no action. Reject replayed action approvals according to a durable operation record and expiry policy. For PRTG's documented form payload, normalise fields explicitly before applying this internal contract.

### 71.3 — Two counters are not one budget

Two workers independently allowing 3 primary actions per minute can admit 6 total in that minute. If each can also issue one restoration per action, potential writes become 12 unless recovery has a separate enforced budget. Use one transactional shared reservation/fencing boundary for the affected service, with expiry and crash reconciliation that cannot release capacity while an uncertain remote write still consumes it. A local mutex only coordinates its own process. Rate alone does not bound harm from a single core change.

### 71.4 — Stop admission versus stop effects

Before mutation, a verified rejection can establish that the model did not start that action. After mutation, the remote or simulated effect may exist despite a local kill or lost reply; observe and reconcile it. Disable queued/new admissions through all actuator paths and track in-flight operation IDs. If the observer also fails, retain UNKNOWN and invoke the authorised recovery path. The supplied local model's kill points demonstrate its own state transitions, not a distributed stop guarantee. The local suite passed again in the overall review; that is separate from this proposed deployment test.

### 71.5 — A useful first workflow

Use the chapter's PRTG event→authenticated ingress/normalisation→durable operation record→NetBox/Nautobot mapping→bounded read-only evidence→optional AI summary→authorised review record. Cap input/output size, event age, API calls, device concurrency and retries; deduplicate repeated delivery while preserving real state transitions. Minimise model-bound data and retain restricted originals. Verify ticket acceptance separately from paging and service recovery. Include PRTG/API/identity/DNS/queue/model/ticket dependencies and an independent failure alert. Start with no device-write permission. Test duplicates, out-of-order/old events, unmapped sensors, missing evidence, injected instructions in log text, model failure and restart before adding a separately approved remediation operation.

## Chapter 72 — CI/CD, pre-change validation and digital twins

### 72.1 — Reproduce and authorise the release

Record the transaction-consistent source-of-truth snapshot/export and hash, schema, object IDs, template commit, renderer/dependency versions, discovered baseline and target capabilities. Preserve the rendered artefact hash, exact owned fields and target identities, validation scope/results/evidence, authenticated approver, approval expiry/conditions and release window. The execution record adds actor, operation ID, actual targets and observed outcomes. A Git commit or hash alone proves neither approval nor a successful device write. Keep secret references rather than credential values in the release record.

### 72.2 — Words versus configuration state

A description such as `description telnet disabled by policy` contains the word telnet without enabling it. Conversely, `transport input all` enables a prohibited transport without naming it. Test both within complete normalised VTY stanzas, including all required ranges. The supplied teaching parser supports its documented IOS XE profile; arbitrary CLI patches, ranges, defaults or unfamiliar forms must not receive an invented PASS. `transport input none` meets a no-Telnet rule but cannot establish working SSH. Define separate authentication and reachability assertions.

### 72.3 — Ask a bounded forwarding question

Specify source locations/interfaces, source and destination address sets, protocol and ports, allowed/prohibited dispositions, current and candidate snapshot hashes, expected node inventory, external route inputs and failure scenario. Ensure selectors match the intended non-empty objects and review parse/initialisation warnings. A counterexample should retain the exact flow and path so an engineer can investigate it; classify missing model support separately from a policy violation. A single directional TCP trace is not a bidirectional, stateful application test or an exhaustive tenant-isolation proof. State which of these properties the query actually evaluated.

### 72.4 — A canary with a large propagation radius

One route-reflector or border-router policy can alter many downstream paths. Bound prefixes, peers and affected traffic explicitly; evaluate the intermediate routing state before selecting a rollout group. Retain independent management access, route/prefix limits, before/after policy and forwarding observations, application probes and available recovery capacity. Dwell through relevant propagation, session refresh and representative demand. Stop on route leakage, unexplained withdrawals, service regressions or unknown outcomes. A tested restore or roll-forward needs an owner and deadline; a Git revert alone cannot restore lost sessions.

### 72.5 — Three different claims

A local simulation supports assertions about its implemented rules and constructed inputs. A virtual NOS traffic test can support observed protocol/software forwarding behaviour for its images, topology, traffic and host conditions. A hardware load test adds evidence about the tested platform, ASIC, optics, release, scale and traffic mix. None establishes every production condition. For each result retain versions, topology, assertions, unsupported features, input/output evidence and failures; report unrun stages as NOT_RUN. Promotion requires the evidence applicable to the actual change, not simply the most impressive tool name.

## Chapter 73 — Machine learning for network operations: what works

### 73.1 — One dataset, two decision times

Prediction: at 09:00 estimate whether a named uplink will exceed a defined load limit during 09:00–10:00. Only features actually available by 09:00 qualify, including known planned launches. Diagnosis: after an alarm at 09:20 classify its likely fault family using evidence available at that later decision. The 09:10 error counter can be legitimate for diagnosis but leaks future information into the earlier prediction. Resolution notes are unavailable to both if written at 11:00. Retain event, collection and availability times, label uncertainty and incident-grouped evaluation splits.

### 73.2 — Rare positives, many false alarms

The constructed table has p=100/1000000=0.0001, r=90/100=0.9 and f=5000/999900, approximately 0.00500050005. Expected precision is rp/[rp+f(1−p)] = 90/(90+5000) = 0.0176817289, or about 1.7682%. The false-discovery fraction is about 98.2318%, while FPR is about 0.50005%. The denominators differ. Holding those rates fixed as prevalence changes is a modelling assumption; it is not evidence that a detector transports unchanged to a new network.

### 73.3 — Forecast at the procurement horizon

At each successive cutoff train only on then-available history, fit preprocessing inside that training set and forecast the same procurement-relevant horizon. Compare with a seasonal-naive baseline using the same sites, periods, error metric and observation units. Include the launch only to the extent its plan and expected demand were known at each cutoff; do not retrospectively supply its realised demand. Score forecast error and interval coverage/width, including launch and ordinary periods, and retain an untouched final test. Combine the forecast with engineering scenarios for launch uncertainty and failure-state traffic; correlated origins require suitable uncertainty handling.

### 73.4 — One time window, two incidents

A shared branch uplink fails while an unrelated data-centre DNS service fails at nearly the same time. Grouping every alarm within two minutes into the uplink incident can hide the DNS failure, especially if restoration closes the entire group. Preserve member alarms, dependency evidence, competing group assignments and unresolved symptoms; probe DNS independently after the uplink recovers. Evaluate missed concurrent faults, over-grouping, fragmentation, delay and operator effort, not only the ratio of alarms to tickets. These are constructed events, not observations from a deployed detector.

### 73.5 — Make the acceptance decision explicit

Predefine useful detection, severe misses, false-page workload, delay, data rights, total cost and fallback constraints. Use held-out sites/times and incident-aware uncertainty; retain paired outcomes when comparing models. In the chapter's synthetic counts, two fewer misses at 1000 units and twenty fewer false alerts at one unit save 2020 units before extra cost: 1000 extra leaves 1020 benefit; 3000 leaves −980. These hypothetical costs are not a business case by themselves. Run shadow evaluation, inspect high-severity failures, monitor input/label drift and performance, and assign an owner who can revert to a maintained baseline when the evidence or service deteriorates.

## Subject within Chapter 73 — LLMs in the NOC: retrieval, generation and evidence

### 73.6 — A genuine citation can contradict the answer

Source: “The edge BGP session to AS64500 uses TCP-AO keychain BGP-AO.” Candidate: “The edge BGP session to AS64500 does not use TCP-AO keychain BGP-AO.” Both share the technical terms; the added negation reverses the claim. A valid passage ID and exact quote establish structural citation integrity only. Semantic review must check target, time, version, quantity, negation and conditions, followed by source accuracy and applicability. Lab 75.1 returns needs_semantic_review for structurally valid citations; it does not automatically prove entailment.

### 73.7 — Abstain usefully

Require abstention when authorised sources lack necessary evidence, conflict without resolution, concern another device/release, are too stale for the decision, or cannot be retrieved within the contract. State what is missing and the next bounded observation instead of merely saying “unknown”. In a held-out set distinguish answerable, absent-answer, ambiguous and access-denied cases. Measure appropriate abstentions on unanswerable cases and unnecessary abstentions among independently judged answerable cases, alongside harmful unsupported answers, latency and operator effort. An access restriction is not overcome by a model's uncited recollection. Threshold choices depend on the consequence of a wrong answer.

### 73.8 — Evaluate the actual summary task

Hold out whole incident/document families and include conflicting clocks, multiple devices, unconfirmed causes, negation, changed releases, missing records and injected instructions in ticket text. Annotate material facts with source spans, time uncertainty, acceptable summaries and privacy restrictions; do not require one exact wording. Compare a runbook/keyword baseline, retrieval-only view and assistant under the same access and time conditions. Score factual support, omissions, chronology, attribution, uncertainty, inappropriate disclosure, review time and severe errors separately. Retain minimised inputs, model/prompt/index versions, outputs and reviewer corrections with controlled access; no confidential fixture should be uploaded merely to run the test. Repeat after consequential component changes. The proposed evaluation is not a completed model benchmark.

## Chapter 74 — Agents and guardrails

### 74.1 — An assertion inside a ticket is not authority

A syntactically valid /32 and the words “approved by the director” establish neither ownership nor authorisation. Check independently authenticated requester and approver identities, the permitted customer/address scope, the recorded approval for this action and time, exclusions, service impact, current policy and reservation capacity. The decision must use the trusted records and policy boundary described in the chapter, not instructions embedded in ticket text.

Keep the original request as evidence without allowing it to redefine the checker. A refusal should identify the missing or failed condition so that an authorised person can resolve it.

### 74.2 — Timeout is an uncertain outcome

Trace the stable operation identifier, preflight observations, reservation, submitted command/request and authoritative post-state. After a timeout, the absence of a reply cannot distinguish an unapplied change from an applied change with a lost response. Reconcile against the executor/device's state and operation record before choosing recovery.

A blind retry can duplicate a non-idempotent action, consume a second reservation or overwrite an intervening change. Even an idempotent desired-state operation needs correct scope, version and observation. Keep the reservation and operation in an explicit uncertain state according to policy; do not release or reapply solely to make the dashboard green. The chapter's offline checks do not prove a particular commercial executor's retry semantics.

### 74.3 — The last reservation

Arrange two workers so both attempt to obtain the final available reservation concurrently. In a deliberately faulty check-then-record implementation, synchronise them between reading availability and writing: both may pass the stale check. In the protected implementation, the shared transaction boundary must admit at most one committed reservation and leave a consistent count, including on failure/restart according to the implementation's scope.

Preserve transaction outcomes and final state. Several successful sequential runs cannot expose that interleaving. An offline concurrency check is evidence about the tested reservation implementation, not about an untested distributed deployment.

### 74.4 — The observer fails

Design an isolated test where the command is accepted but the independent service observer becomes unavailable. Mark command acceptance separately from service acceptance, which remains unknown. The workflow should stop any automatic promotion requiring verified service health and alert the authorised operator with the last trustworthy evidence and operation ID.

Provide recovery access and escalation independent of the affected service. Decide whether to hold, inspect or roll back using the agreed policy and observed state; automatic rollback is not universally safe when the original outcome is uncertain. This answer defines a test and expected decision boundary, not an executed integration result.

## Subject within Chapter 74 — Intent-based networking and autonomous networks

### 74.5 — An outcome with a refusal condition

For named London and Manchester service endpoints and an agreed traffic class/load, define normal RTT p95 below a strict threshold over a specified sampling window, a separate loss/timeout rule, and packet-service restoration below a separate limit after each declared single fault. Name usable capacity, permitted geography, isolation and independently evidenced shared-risk constraints, measurement uncertainty and allowed evidence age. Assign owner, version and review/withdrawal conditions. Refuse or negotiate if diverse paths, surviving capacity or measurement capability cannot meet all constraints; do not silently relax one to generate configuration. The chapter's numeric values are teaching examples, not recommended SLAs.

### 74.6 — Configuration and outcome are different axes

Change an owned interface description without affecting packet service: the configuration comparison can detect drift while service probes still pass. Conversely, retain the approved configuration and introduce a shared physical failure or overload: configuration can match while the service breaches its intent. Test both with versioned before/after state, authorised perturbations, independent service measurements and recovery. Neither a drift finding alone nor an unchanged template proves the service outcome; retain an UNKNOWN state when the observer fails.

### 74.7 — Scope an autonomy assessment

Choose one scenario, such as transport fault management for a named domain. Record the applicable licensed methodology and scenario tool/version, network and task boundaries, human decisions, exception/recovery paths, test evidence, assessors and date. Apply its actual scoring criteria rather than inventing a book-specific conversion. The public Zain Kuwait energy-efficiency entry illustrates a scoped assessment, not evidence about this reader's network. Pair the resulting capability assessment with measured service performance and operating effort; the book's L1–L5 learning levels are unrelated to TM Forum AN Levels.

### 74.8 — Boundaries mean what the contract says

With 300 sorted samples, nearest-rank p95 is sample ceil(0.95×300)=285. A value of exactly 50 ms violates a strict sub-50 ms requirement; up to 15 larger samples can coexist with a passing p95, so add separate loss and tail requirements where needed. Capacity is inclusive: 70 Gbit/s demand at 70% of a 100 Gbit/s survivor fits exactly; any demand above 70 does not. Restoration trials are separately strict below 50 ms. Missing/stale data cannot earn MET; preserve UNKNOWN, while also reporting a known violation in another check. These are the local model's rules for supplied constructed evidence, not live network measurements.

## Chapter 75 — Governing automation and AI

### 75.1 — Classify actual effects

A bulk telemetry read can expose customer data or saturate device/API resources: limit scope, fields, concurrency, retention and egress. A source-of-truth edit can propagate through later rendering to many devices: enforce ownership, review the downstream diff and bind deployment authority separately. A routing change can affect transit paths and sessions before rollback: assess reach, propagation time, capacity, independent access, verification and recovery. Reversibility and target count do not replace consequence, likelihood/uncertainty, cumulative effect and time-to-harm analysis. Consider the harm of inaction too.

### 75.2 — Record the uncertain write

Retain authenticated requester/executor identities, request and operation IDs, exact parameters/targets, policy/schema/state versions, evidence references and times, approval binding/expiry, reservation, submission time, transport response or timeout, and independent observations. Mark the outcome UNKNOWN until reconciled; do not translate a timeout into failure or success. Record clock uncertainty, gaps, escalation, attempted recovery and final verified state. Protect and minimise records; an integrity hash cannot prove the underlying event was true or that every event was logged.

### 75.3 — Local inference is one stage

Trace data from collection through preprocessing, embedding, vector/search storage, retrieval, model inference, tool calls, displayed citations, conversation/cache state, logs, backups, support and deletion. Potential egress includes remote embeddings, telemetry, connectors, model/package downloads and support sessions. Identify actual endpoints, identities, purposes, fields, tenant boundaries, retention, transfers and contractual roles. Verify paths and revocation behaviour, not just the inference host's location. Avoid placing real secrets in diagnostic prompts or workflow exports.

### 75.4 — Evidence for the next permission increase

For a PRTG/n8n investigation pilot, the monitoring owner validates sensor-to-asset mappings and source freshness; the workflow owner demonstrates deduplication, restart and unavailable-dependency behaviour; security verifies least-privilege tools, prompt-injection handling and review binding; the service owner appoints duty cover and accepts measured outcomes and residual risk. Predefine case quality, severe errors, workload/cost and recovery criteria using representative and adverse cases. Close mapping, recovery and cover gaps before considering broader authority. A maturity score alone cannot authorise production or certify legal compliance. This is a constructed assessment plan, not completed acceptance.

## Chapter 76 — The design method

### 76.1 — Extend the requirement, not just the topology

An illustrative R5 is a named client completing an authenticated HTTPS request to a named service, validating the expected identity and response, within an agreed latency/loss envelope at a stated load. Specify address family, DNS dependency, normal and fault states, observation points, time window, TLS/application setup and acceptance evidence. The present ICMP lab cannot satisfy R5 merely because ping works. Add the application, security design, measurement and recovery before claiming acceptance; the numeric objective must come from the stakeholder's need.

### 76.2 — A changed estimate is not a passed test

If available skills reduce option C's central effort from 18 to 8 hours, reconsider it against B's10, using revised ranges and maintenance costs. C still needs implementation and the same acceptance evidence. If a mandatory condition now requires surviving either router's loss, A–D as drawn all fail: both transits terminate on the same single router at each end. Reject the current designs before scoring cost. Redesign routers, host gateways and failure/recovery tests; do not assume a routing daemon alone supplies chassis redundancy.

### 76.3 — Restore the state that was lost

In the retained exploratory Linux run, administrative interface shutdown removed a static route. Bringing the interface up restored link state but did not recreate that route. The corrected recovery explicitly reapplies both route sets and verifies primary route preference plus bidirectional reachability. This is observed behaviour in the stated Linux environment, not a claim about every NOS. A recovery plan must reconcile relevant routing and service state, not stop at an interface-up indication.

### 76.4 — A decision record that can be revisited

For an illustrative migration from one transit to a bounded two-transit lab design, record requirements R1–R4, constraints, selected option B, rejected A, deferred C and dominated D, with their assumptions. State scope as an isolated IPv4 Linux exercise and retain the historical 31-assertion forwarding/cleanup evidence. Record single-router/shared-host dependence and excluded silent faults, application security, load and hardware qualification. Revisit when a requirement, supported release, cost estimate or failed test changes the decision. A production migration needs its own evidence and owner; copying this ADR does not supply approval.

## Chapter 77 — Reliability engineering

### 77.1 — The availability budget

A 30-day interval contains 43,200 minutes. At 99.99% time availability, the unavailable allowance is `43,200×0.0001 = 4.32 minutes`. A five-minute event exceeds that allowance by 0.68 minutes, or 40.8 seconds, under the question's no-exclusion assumptions. This is a time-based service calculation, not automatically a contractual credit calculation.

### 77.2 — Series and parallel under explicit independence

Six required independent components, each with availability 0.9995, give path availability `a = 0.9995^6 = 0.9970037475`, or 99.70037475%. If either of two such paths is sufficient, their failures are independent and switching/service dependencies introduce no extra failure, the result is `1−(1−a)^2 = 0.99999102247`, or 99.999102247%.

These are model outputs. Independence, sufficiency and the absence of shared dependencies must be justified separately; duplicating a diagram does not establish them.

### 77.3 — A shared hazard

Let the shared hazard's unavailability be 0.001, and let the preceding component/path model apply conditional on that hazard being absent. The single-path result is `0.999×a = 0.99600674375`, or 99.600674375%. The pair is `0.999×[1−(1−a)^2] = 0.99899103145`, or 99.899103145%.

The shared hazard dominates the highly redundant pair. Do not simply add unconditional failure percentages or apply the shared hazard twice. A good answer states the conditioning and whether the hazard is already present in the component data.

### 77.4 — Redundant links with insufficient survivor capacity

Two 100-unit links offer an aggregate 200 only under an actual usable distribution. Against demand 150, that leaves 50 in the healthy state. One link's loss leaves capacity 100 and a shortfall of 50. The service is not fully capacity-resilient merely because a second path exists.

Increase survivor capacity, alter the service/admission requirement, or provide another verified path. Any priority or load-shedding option needs explicit affected services, enforcement and acceptance tests; an unexplained “QoS” label does not manufacture capacity.

### 77.5 — A meaningful failure test

Specify the service transaction, load, observation points, clock resolution and success/recovery objective. Establish the healthy baseline and that the observer detects a known failure. Apply one authorised failure in an isolated or approved test scope, record the transition and customer result, then verify failback and restored capacity.

Include abort conditions, out-of-band recovery, an accepting owner and treatment of unknown intervals. Record slow and failed trials. A passing routing adjacency check alone does not demonstrate the required service's restoration.

## Chapter 78 — Addressing, naming and numbering plans

### 78.1 — Exact cover versus a routing promise

With eight /24 slots at each of 17 contiguous sites, a region uses 136 /24s. Region0's exact cover is 10.0.0.0/17 plus 10.0.128.0/21; four such regions need eight exact-cover prefixes. Each reserved /16 has 120 unused /24 slots. The advertised /16 is a separate policy decision: its origin must have a defined constituent-route condition, discard behaviour and more-specific exceptions. It may remain unchanged while site 17 is added if that reachability contract holds. An exact cover describes allocated address sets, not failure-time forwarding or the correct advertisement policy.

### 78.2 — A delegation is a finite budget

For an illustrative documentation prefix 2001:db8:8100::/48, /56 site blocks provide 256 /64s each. There are 256 such site blocks, numbered 00–ff in the high byte of the fourth hextet. The first two are 2001:db8:8100::/56 and 2001:db8:8100:100::/56. At 200 LANs per site, 56 /64s remain within each site block: 28% growth relative to 200, or 21.875% of the block unused. If all 256 blocks are assigned, no unassigned site block remains in the parent. Reserve additional site blocks if site-count growth requires them, and use the organisation's real delegation in production.

### 78.3 — Reservation and on-link size

An IPv4 /24 can supply 256 loopback /32 identifiers in a dedicated pool; these are routed host addresses, not conventional hosts on one /24 LAN. A separate /24 can provide 128 point-to-point /31 links where both platforms support RFC 3021. For IPv6 reserve a loopback pool and allocate /128s; reserve a /64 per router link if desired while configuring a permitted /127 within it, such as documentation endpoints 2001:db8:8100:1::10 and::11. Respect RFC 6164's special-address restrictions and platform behaviour. Record pool ownership, prefix uniqueness scope, actual versus reserved use, advertisements, anti-spoofing and management reachability.

### 78.4 — Field width before mnemonic numbering

Using documentation ASN 65536, RD type 2 can encode 65536:101 because its local field is 16 bits, but not 65536:81001. A four-octet-AS-specific RT can likewise use administrator 65536 and local value 101, with its own extended-community type/subtype. The similar printed notation does not make the fields interchangeable: an RD distinguishes VPN routes; RT policy selects intended import/export membership. Distinct PE/VRF RDs can preserve separate paths while several routes share an RT. Validate encoding, controlled allocation, uniqueness scope and policy separately; the example ASN is not a live assignment.

### 78.5 — Change names without losing history

Keep a stable asset/site identity and versioned aliases, prefixes and sensor mappings. Inventory DNS/reverse DNS, certificates, DHCP/IPv6 lifetimes, allowlists, routing/next-hop resolution, licences, applications, logs and external dependencies. Stage new state where supported, validate both directions and actual services, move references/clients, and observe explicit exit criteria before retiring old state. Lower DNS TTLs early enough for old cached values to expire, while accounting for longer-lived application sessions. Define stop and recovery conditions and preserve the old allocation for the agreed window. Delayed events must resolve against their historical mapping, not a reused display name.

## Chapter 79 — Scaling: what breaks at ten times the size

### 79.1 — A usable capacity record

Identify exact device SKU/ASIC or line card, NOS release, licence, running resource profile and feature mix. For each resource retain documented scope/limit and source date, measured normal/peak/high-water use, failure and migration-overlap demand, headroom, forecast uncertainty, delivery lead time, action trigger and owner. Separate RIB paths, FIB entries, next hops, ACL/QoS resources and adjacencies. Mark untested simultaneous maxima and exhaustion/recovery behaviour NOT_RUN rather than combining datasheet columns. No actual device data is supplied by the question; a completed record requires inventory and measurements from the chosen device.

### 79.2 — Three reflectors, the same total node count

Keep n nodes, make three mutually peered reflectors, connect each of n−3 clients to all three, and add no client-client edges. Sessions total 3(n−3)+3=3n−6. Each client has degree 3; each reflector has(n−3)+2=n−1. For 24 nodes this gives 66 sessions and 23 peers per reflector; for 240 it gives 714 and 239. If instead three new reflectors are added to n existing clients, the count is 3n+3: state the population. Counts alone do not establish update throughput, path visibility, failure independence or a supported scale.

### 79.3 — Growth of the mix

In the invented one-unit IPv4/two-unit IPv6 table, 40000 IPv4 and 10000 IPv6 consume 60000 units. If IPv4 stays fixed while IPv6 triples, demand becomes 40000+2×30000=100000: the entire invented physical table and 20000 above the 80000 planning ceiling. The 1.5× common-growth forecast instead uses 90000. Neither model is a hardware claim; obtain actual entry widths, shared resources and feature restrictions. Use separate demand scenarios and lead-time triggers when families, tenants or policy sizes grow differently.

### 79.4 — The shared service crosses the shard boundary

Two regional shards may depend on one identity provider or one workflow operation store. In an authorised isolated test, interrupt that dependency while retaining an independent observer and recovery access. Measure which existing services continue, which new operations stop, whether permissions fail closed as specified, queue/retry growth, customer impact and recovery/reconciliation. Define fault duration, load, abort threshold and restoration checks beforehand. Region separation cannot establish independence from the deliberately shared service.

### 79.5 — Turn tenfold growth into evidence

Vary topology density, prefixes/paths, LSA/LSP/update rate, policies, platform/release, CPU/FIB resources and target load across normal, burst, failure, restart and maintenance cases. Observe detection, computation, programming and packet/service restoration, including tails, false failures, incomplete runs and measurement resolution. Compare retention of the present area with hardware/policy changes or partitioning, including migration overlap and operational cost. Record the binding constraint, uncertainty, option rationale, action trigger, owner and lead time. The existing 40-router result cannot by itself select or qualify a 400-router design.

## Chapter 80 — Multi-site, multi-region and hybrid

### 80.1 — Same endpoints, different routes

For sites 800 km apart, construct fibre routes of 1100 and 1500 km. At 200000 km/s and symmetric route lengths, their propagation RTTs are 11 and 15 ms; the geographical fibre floor is 8 ms. Adding assumed other RTT delays of 3 and 1 ms gives 14 and 16 ms. These are explicit model inputs, not measured offers. Compare actual normal and backup path distributions at load, including serialization, processing, queueing and application rounds. An interface-speed upgrade changes serialization, not propagation speed; neither adding component p95s nor quoting endpoint distance yields an end-to-end p95.

### 80.2 — Thirty equivalent branch services

Define each branch's endpoints, committed/burst demand, classes, MTU, addressing, encryption, critical applications, failed-state objective and delivery date. Compare dated Internet/private-VPN/managed-transport offers and any SD-WAN overlay against that same boundary, including access tails, cross-connects, appliances, optics, licences, support, installation, recurring charges and exit costs. Verify shared ducts/wholesale providers and backup capacity. Record surveyed delivery ranges, dependencies and an interim plan; do not treat rapid overlay setup as evidence that a new physical circuit can be delivered quickly. Reject mandatory failures before scoring preferences.

### 80.3 — State a writer contract

For an illustrative single-writer order database with two active frontends, record the authoritative writer, durable acknowledgement condition, voter/data placement, partition response and fencing mechanism. Frontends may accept requests at both sites while only one database side may commit writes. Specify retry/idempotency, session identity, storage/replication, DNS, routes, MTU, firewall symmetry and survivor capacity. A witness is not necessarily a data copy. If ownership or quorum cannot be established, stop or restrict the relevant operations according to the agreed service contract; loss of peer contact alone cannot authorise a second writer.

### 80.4 — Draw the service boundary

Mark a named VLAN/VNI bridged between the migration workloads, the exact VTEPs, gateway location, RT import/export and its termination at routed interfaces/VRFs. The intervening routed underlay does not remove the overlay's shared Ethernet domain. Test relevant BUM/loop, duplicate-MAC, mobility, DCI-loss, gateway and recovery cases at stated load, with limits and independent observation. Keep the stretched scope and residual shared risks explicit; a separate critical application's routed boundary must not secretly depend on that VNI. Remove the stretch only after its workload and rollback exit criteria hold.

### 80.5 — Recovery dependencies can consume the margin

The chapter's sequential allowances total 960 seconds=16 minutes, leaving 840 seconds=14 minutes against a 30-minute objective. If a clean backup restore replaces the 300-second promotion/recovery stage with 1800 seconds, the revised sequence is 2460 seconds=41 minutes before any extra identity delay. Adding an illustrative 600-second identity restoration serially makes 3060 seconds=51 minutes. Parallel work can alter the critical path, but cannot be subtracted without a dependency plan. If identity cannot be restored and no authorised independent recovery access exists, there is no justified finite completion time. Validate recovered data/keys, writer fencing, client access, load and failback; these figures are constructed allowances, not an executed RTO.

## Chapter 81 — Migrations, cutovers and brownfield reality

### 81.1 — A quiet month misses year-end

Add an authorised year-end finance export to an external allowlisted endpoint, even if a recent flow capture is quiet. Confirm its owner, schedule, source/destination identities, ports, DNS/certificate dependencies, data sensitivity and acceptance record. Reconcile configuration, scheduler, contract and prior execution evidence; arrange a bounded rehearsal or a representative test with the application owner. Missing traffic is uncertainty, not proof the job is unnecessary; observed unauthorised traffic is not automatically a requirement. Retain unresolved dependencies and the agreed recovery measure.

### 81.2 — One box order may not fit every prefix

For prefixP use the chapter's old A→B, B→D and new A→D, B→A states: update A before B. For a second destinationQ on D, reverse those desired patterns: old A→D, B→A; new A→B, B→D. Q requires B before A. A possible per-prefix sequence is P at A, Q at B, P at B, then Q at A, verifying each independent forwarding change and return path. A whole-device update that changes both prefixes at once can violate one dependency. Real aggregation, recursive next hops, policy and atomicity may couple prefixes; analyse and test those before using this illustrative sequence.

### 81.3 — Test intended services and denied traffic

List each authorised service with endpoints, address family, identity, direction, protocol/port, NAT and return-path/session assumptions, load, phase, observer and acceptance criteria. Include forbidden tenant/management crossings and prove the observer detects a known failure. Add required but currently unobserved scheduled jobs and dormant recovery paths with owner-approved tests. Evaluate old, coexistence, candidate, fault, rollback and final states; retain failed queries and incomplete coverage as unknown. Ping alone cannot validate a stateful firewall, application correctness or confidentiality.

### 81.4 — Rehearsal changes the deadline

If rollback doubles from 15 to 30 minutes while verification remains 10 and contingency 5, the reserve becomes 45 minutes. With a 03:00 window end, rollback must start by 02:15, fifteen minutes earlier than the original 02:30. Place the decision gate earlier still if deciding or dispatching takes time. Reassess the remaining candidate work at each gate; do not spend the recovery reserve because the cutover appears nearly complete. These are planning figures, not measured production durations.

### 81.5 — Retire responsibility explicitly

Record stable asset/service/circuit IDs, owner, final dependency checks, isolation evidence, stabilisation and rollback-retention conditions, retained-spare purpose/support, data/record retention, credential and certificate revocation, sanitisation method/verification and disposal or reuse. Include DNS/routes/monitoring/automation removal, queued-event handling, inventory and financial updates, contract notice periods and actual termination acceptance. A legitimate supported spare can remain under an approved owner; a factory reset alone does not prove secure erasure. Close against stated exit criteria and record every approved residual responsibility.

## Chapter 82 — Network economics: CAPEX, OPEX and unit cost

### 82.1 — Escalate only the stated component

Choose an explicit illustrative 3% nominal annual energy escalation from year 2, keeping all other base costs fixed. In year y=1…7, energy is £3679.20×1.03^(y−1); the rest of annual cost is £26000. Add £5000 net exit cost only in year 7 and the £140000 initial purchase at time 0. Discount at the chapter's assumed 8%: PV =140000+Σ[(26000+3679.20×1.03^(y−1)+5000×I(y=7))/1.08^y] ≈ £299061.75. This is about £1623.40 above the unrounded base PV, before rounding differences. The escalation and rate are teaching assumptions, not market forecasts.

### 82.2 — Useful capacity versus cash released

Saving 200 internal staff hours at an allocated £40/hour creates an £8000 resource-capacity estimate; cash does not necessarily fall if salaries and other commitments remain. State the work those hours will replace or enable and measure whether it occurs. Cancelling 200 genuinely avoidable purchased hours at £40 can release £8000 cash, subject to minimum commitments, notice, substitution costs and service equivalence. Deduct automation maintenance, review and failures. Do not count both redeployed staff time and an unchanged supplier contract as cash savings.

### 82.3 — Integrate subscriber-months

For an invented base of 10000 active subscribers for six months and 14000 for six, exposure is 60000+84000=144000 subscriber-months. With an unchanged £1.2 million annual pool, unit cost is £8.3333 per subscriber-month. Dividing by the year-end 14000×12 would instead give £7.1429 and understate cost for the actual exposure. Use finer billing/active-period integration when changes occur within months, and retain consistent service scope and quality.

### 82.4 — Separate the central case from the tail

At £10000 per event and a £6000 annual programme, the expected narrow cash benefit is 10000×(frequency_before−frequency_after)−6000. A reduction of 0.1,0.4 or 0.8 events/year yields −£5000,−£2000 or+£2000 respectively; narrow break-even needs 0.6 fewer events/year. These are assumed scenarios. Model a separate severe data-loss outcome with its probability, impact and intervention effect, avoiding overlap with the ordinary event costs. Tail, legal or safety constraints can justify a control even when expected cash benefit is negative; unsupported probabilities must remain uncertain.

### 82.5 — Principal reduces debt

Add an illustrative £70000 loan at time 0, fixed 5% annual interest on opening principal and seven £10000 year-end principal repayments, with no fees or tax. Interest is £3500,£3000,£2500,£2000,£1500,£1000 and £500; total £14000. The loan receipt offsets the initial asset cash payment, but creates a liability. In year 1, depreciation £10000, support £5000 and interest £3500 reduce pre-tax profit by £18500; the £10000 principal payment reduces debt, not profit. Year 1 post-purchase cash outflow is £18500 (support+interest+principal), closing debt £60000 and asset carrying amount £60000. Their equality here is incidental to the chosen schedule. Operating-profit effect remains−£15000 before interest; use finance's actual reporting framework for presentation and reconcile all dated cash flows without double counting financing in a valuation.

## Chapter 83 — Vendor management, RFPs and lifecycle

### 83.1 — Two logos can share a failure

Map exact ASICs, NOS/third-party components, cryptographic libraries/certificates, cloud services, identity/DNS/storage, facilities, carriers, management credentials and automation policy. Identify which common-cause exposure the second supplier removes and which new integration/support work it creates. Retain evidence for exact products/releases rather than inferring independence from brand names. Compare alternatives by role, within one service and across failure domains, including exit cost and staff capability.

### 83.2 — Complete the fixture before measuring

Fix the per-peer/per-VRF route manifest, selected and installed forwarding state, ACLs, telemetry, frame sizes/FCS/rate accounting, addresses and 500 continuously active flow identities with sequence numbers. Offer the stated 40 Gbit/s aggregate across the two candidate 100 Gbit/s paths, and record each of ten faults per direction plus restoration. Verify generator capacity and measurement timing; a coarse sampling gap or lost capture can hide a flow's continuous loss interval exceeding 1second. Record total loss, reordering, duplicates, forbidden-path leakage and uncertainty. A pooled average cannot satisfy an every-flow/every-trial gate. This is a proposed specification, not a test result.

### 83.3 — Anchor each score in evidence

Write distinct performance, lifecycle-cost and operational-task anchors for every score before evaluation. Performance beyond the mandatory gate might use specified load/failure objectives; operations can use reproducible diagnosis/recovery tasks; price requires a disclosed formula or bands over equal scope. The illustrative 40/35/25 weights give A 78 and B 83; 20/35/45 give A 82 and B 75. A one-point uncertainty in B's performance score changes its original total by 8 points, enough to reverse the five-point lead. Record uncertainty and moderation, but do not change award weights after bids to select a preferred winner. A failed mandatory R2 excludes C regardless of score.

### 83.4 — Four hours from which event?

Separate incident start, detection, support request, acknowledgement, qualified engagement, diagnosis, RMA authorisation, dispatch, arrival, installation and verified service restoration. Place the four-hour promise on its actual start/end events and record business hours, site coverage, cut-offs, stock, access, customs and other exclusions. A delivered part may still require firmware, licences, configuration, labour and acceptance. Track time to restored redundancy separately from customer outage; neither an RMA tier nor a response commitment establishes an availability percentage.

### 83.5 — An exception with an exit

Record exact assets/releases and binding support/security milestones, affected services, reason, alternative options, residual exposure, compensating controls, spares/recovery evidence, accountable risk owner and expiry. Add funded procurement, test, migration and rollback steps with dates before that expiry, plus review triggers for new vulnerabilities or failures. Spares can repair some hardware faults but do not supply missing patches. Retain original notices and approvals; an exception cannot waive an applicable legal duty merely because a manager signs it.

## Subject within Chapter 83 — SLAs, SLOs and what you can promise

### 83.6 — Define the packet and the clock

Specify source/destination demarcations, direction, address family, packet size/DSCP, offered load, schedule, timestamp locations/resolution, clock synchronisation and an error bound. Define matching, duplicates, timeout/loss treatment, measurement window and percentile method, including whether lost/late packets are excluded or counted through another requirement. If measured one-way delay is 9.8 ms with a combined absolute error bound 0.5 ms, the supported interval is 9.3–10.3 ms and cannot establish a strict sub-10 ms pass. RTT/2 is not a substitute when paths or responder delay differ. Preserve loss and coverage alongside delivered-packet delay.

### 83.7 — Change an exclusion explicitly

Replace the approved maintenance interval with [1900,2200) seconds, excluding 300 seconds instead of 600. The union of bad intervals remains [1000,2500), 1500 seconds; contractual eligible time E=2591700, bad time D=1200 and unknown U=120. Compute bounds (2591700−1200−120)/2591700 and (2591700−1200)/2591700 before rounding. The 99.95% threshold lies between them, so this result is indeterminate. The no-exclusion customer view remains 99.937500–99.942130%. Altering the fixture does not authorise changing a real maintenance approval.

### 83.8 — Missing evidence can cross the target

Keep the original 600-second exclusion, E=2591400 and D=900. Add a disjoint unresolved interval [4000,4600), 600 seconds, to the existing 120 unknown seconds: U=720. The lower bound is 1−1620/2591400≈99.937486%, while the upper remains 1−900/2591400≈99.965270%. Since 99.95% lies inside, compliance is indeterminate under these unresolved bounds. Do not overlap confirmed bad and unknown classifications, double-count intervals or silently remove unknowns from eligible time.

### 83.9 — A tier function acts on each month

For an illustrative £20000 fee with the chapter's unchanged tiers, model A's 99.95% month gives a 10% credit, £2000 each month. Model B's 99.5% bad month gives 25%, £5000; at 10% bad-month probability its expected credit is £500. Raising that probability to 20% gives £1000 expected credit and changes expected availability to 99.90%, so the former equal-mean comparison no longer holds. Apply exact boundaries, eligibility, claims and caps to each outcome before averaging; do not apply the tier once to mean availability. These are invented terms, not the AWS schedule.

### 83.10 — Equal percentages can leave retained exposure

Map service boundary, window/denominator, exclusions, measurement rules, fee base, credit tiers/caps, claim deadlines, evidence and other remedies for both schedules. Even identical 99.99% thresholds can yield £1000 owed on a £10000 customer fee and only £100 recoverable on a £1000 supplier fee at a 10% tier. A narrower supplier demarcation or accepted maintenance exclusion may prevent any claim. Record retained risk, timing and claim ownership separately from engineering resilience; supplier promises are not measured independent probabilities to multiply.

## Chapter 84 — Regulation, compliance and obligation

### 84.1 — Identify the regulated activity first

For an invented UK employer operating its own private LAN, assess its controller/processor roles, employment and communications data, sector duties and any services offered outside the organisation; do not automatically call it a public communications provider. For a public ISP, identify the legal entity, public network/service, customers, territories and applicable General Conditions, telecoms security and PECR duties. For a cloud provider, establish the actual service, establishment, size and relevant digital-service/sector definitions before deciding whether UK NIS applies. EU customers or infrastructure require a separate territorial and service analysis; NIS2 is not a universal label for every UK network. Ask who provides what to whom, where, under which contract and legal role, on what effective date. A group may contain several differently scoped entities.

### 84.2 — A retention entry is a lifecycle

Example purpose: investigate unauthorised access to a named administrative service. Record the controller, applicable lawful basis and necessity assessment; fields such as pseudonymous account ID, UTC time, source and outcome; authorised investigators; an evidence-based review/deletion period; and the event that starts it. Do not invent a statutory period for all authentication logs. Minimise secrets and unnecessary payloads, protect identity lookup separately, restrict exports and document processor locations and terms. Specify deletion in active stores and how backups expire or regain deletion rules after restoration. A lawful hold names its authority, narrow scope, owner, review date and release procedure; it is not indefinite preservation by default. Test a synthetic record through capture, access, export, deletion and restore, retaining test evidence. A retention notice, if applicable, must be assessed separately against its actual scope.

### 84.3 — State the public service and justify the policy

For an invented UK public Internet service, describe the proposed classification, scheduler, affected users/applications, congestion evidence, duration, customer disclosures and alternatives. Assess the applicable open-internet rules and current Ofcom guidance with the responsible legal owner; neither a QoS feature nor congestion alone grants permission for arbitrary discrimination. Measure throughput, latency, loss and fairness under representative congestion and recovery, including unintended traffic matches. State whether the proposal concerns reasonable traffic management, a retail package, a specialised service or a claimed exception, and test the relevant conditions rather than mixing them. Keep July 2026 public-interest clarification distinct from a change to statute. A private LAN QoS design or another country's rule is not a substitute for this service's assessment.

### 84.4 — Rehearse the clock and the failed route

In the constructed checkpoint, PECR awareness is Saturday 02:00 UTC: Tuesday 02:00 is the outer 72-hour point, subject to reporting without undue delay and feasibility, not a planned wait. Assess customer notification separately. The assumed section 105K facts at 02:20 trigger Ofcom reporting as soon as reasonably practicable; do not borrow the 72-hour allowance. Invoke the documented deputy immediately when the primary is unavailable. Record discovery, assessment, attempted contact and portal failure times, facts known/unknown, authorised decisions and updates. Use the regulator's current documented alternative contact/submission route and retain acknowledgement or evidence of the attempt; an internal ticket saying sent is insufficient. Escalate failed delivery and continue attempts and containment. Use a tabletop or agreed test channel without sending a fictitious live breach report. The scoped PECR report replaces the duplicate UK GDPR breach report; separately scoped data/entities still need assessment.

### 84.5 — Enacted and proposed are different states

As at 25 September 2026, use the PECR breach-notification change effective 20 August 2025 as the enacted example: update the scoped provider's procedure, clock, owner/deputy, training, evidence and review entry against ICO guidance. Use the UK Cyber Security and Resilience Bill, parliamentary bill 4035, as the proposal: retain its version, stage, likely affected services, monitoring owner and next review trigger, with planning scenarios rather than claiming its proposed duties already apply. Check commencement, scope and transitional provisions when a proposal becomes law. Recheck both entries before real use; an enacted rule may have future commencement, and a proposal may change or fall. Sources are the chapter's ICO PECR guidance and Parliament's bill-progress record, checked 25 September 2026.

## Chapter 85 — Leading a team

### 85.1 — The calendar cannot supply missing hours

The chapter starts with 150 gross hours, a 30-hour allowance and 110 hours of planned demand, leaving ten. One explicit extension adds 20 incident hours for the first incident and 15 for a second. Add a 7.5-hour absence **beyond** the allowance already included. Available time becomes 112.5; demand becomes 145; the deficit is 32.5 hours.

State which project/routine scope can move and its consequence, or obtain competent cover. If the absence was already included in the original allowance, do not subtract it again. Even balanced aggregate hours do not prove simultaneous incident cover, the right specialism or a feasible rota.

### 85.2 — Observable progression

Three examples are: diagnose a bounded fault using discriminating evidence; deliver an authorised change with verification and recovery; and produce a handover another engineer can use without reconstructing missing state. Define the expected scope, independence and quality at the relevant level.

Offer equivalent assessment cases, scheduled practice and review opportunities across shifts. Do not make progression depend solely on being present for a rare daytime incident or on a manager's memory. Retain concrete examples, feedback and an opportunity to address a gap.

### 85.3 — Complete the interview rubric

State the prerequisites given to every candidate: topology, relevant addressing, task scope, available observations and whether command syntax recall is being assessed. Give an accessible format and agreed adjustments without changing the underlying evidence/safety standard. Use the same follow-up rules and calibrate reviewers on sample responses before scoring.

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Use of evidence | Asserts a cause without relevant observations | Finds relevant evidence but leaves an important distinction unresolved | Uses observations and a discriminating next test; states limits |
| Revision of hypotheses | Ignores contrary evidence | Changes view with prompting | Updates the explanation explicitly and identifies what remains uncertain |
| Operational safety | Proposes an unjustified disruptive action | Recognises risk but leaves scope or recovery incomplete | Bounds impact, authority, stop conditions and recovery |
| Communication | Leaves impact and next step unclear | Communicates the main issue with important omissions | Separates observation, hypothesis, impact, owner and next step |

A path-MTU black hole can be a supported hypothesis in the chapter's interview scenario; reward the test that would distinguish it, not confident repetition of that phrase. This is a teaching rubric, not a substitute for the chapter's jurisdiction-specific recruitment guidance.

### 85.4 — Readiness for an access-switch change

Require a correct inventory and affected-port/service map, known baseline, reviewed intended change, the necessary authority and supervision, usable backup/recovery access, explicit verification and rollback conditions, and an accepting handover. Ask the engineer to explain what a loss of management access would mean and how recovery would proceed.

Choose a bounded task consistent with demonstrated competence. A certificate or completed reading alone is insufficient; equally, an engineer need not perform an unrelated advanced task to qualify for this particular supervised change.

### 85.5 — Specialist absence

Plan a bounded absence exercise with an alternate, a safe scenario and an observer. Test whether the alternate can find the information, obtain permitted access, make the required authorised decision and reach appropriate support within the chosen objective. Classify actual gaps as knowledge, access, authority, availability or equipment, rather than calling everything “training”.

Record what happened, assign corrective owners/dates, then repeat the failed element. Until the exercise runs, label the deliverable a plan. Do not populate the observation column with these model expectations.

## Chapter 86 — Strategy and roadmaps

### 86.1 — A cloud move changes the decision

Retain the four critical branches' service requirement, but revisit traffic destinations, DNS, identity/trust, internet/cloud dependencies, performance evidence, contract commitments and the nine-month migration timetable. Distinguish the interim service obligation from the target architecture. Do not assume the cloud service removes branch connectivity requirements.

Rewrite the memo with the changed evidence, feasible options, money and staff needs, acceptance, decision date and fallback. Previously proposed work may remain necessary, become temporary or lose value; explain which and why rather than cancelling it solely because the application moves.

### 86.2 — A local technology radar

Example: on 25 September 2026, place a proposed configuration-validation tool in a locally defined “trial” category for one isolated topology. Name the owner and versions, the intended benefit, known limitations and required evidence. Stop the trial if it modifies a target outside scope or if its output cannot be traced to the input/version. Promote it only after predefined positive, negative and recovery cases and an acceptable maintenance burden; review the decision on a stated date.

These categories and thresholds are local decisions. A vendor demonstration or another organisation's radar cannot replace evidence for this service and team.

### 86.3 — Recompute the delivery comparison

Choose a four-year horizon, 10% annual discount and a £15,000 exit payment at the end of year four for each option. Use the chapter's upfront/annual cash inputs: internal £100,000/£25,000; managed £25,000/£52,000; partner £60,000/£38,000. With annual payments at each year-end, calculate `setup + annual×sum(1/1.1^t, t=1..4) + 15,000/1.1^4`.

| Option | Undiscounted cash | Present cost |
|---|---:|---:|
| Internal | £215,000 | £189,491.84 |
| Managed | £248,000 | £200,078.21 |
| Partner | £227,000 | £190,700.09 |

Existing staff capacity is not free simply because its salary is outside this cash comparison. Show hours, displaced commitments and capability separately, and include incremental staffing cash where applicable. These invented assumptions omit tax, inflation and financing; they do not constitute a procurement recommendation.

### 86.4 — Connect the service, not every address

For two acquisitions both using `10.10.0.0/16`, keep their routing contexts distinct and identify the precise application flows that must cross. A scoped service proxy or explicitly designed translation boundary can give those flows unambiguous endpoints. Specify identity, name resolution, permitted directions, return traffic, logging, ownership and failure/recovery behaviour.

Do not import both identical prefixes into one routing context and expect policy alone to identify the intended site. Nor should an answer promise that NAT transparently fixes every protocol. Test the chosen service and preserve a staged renumbering or integration plan where required.

### 86.5 — Resources and the critical path

With one engineer for I, S and D, one valid order is I in weeks 0–2, D in 2–4 and S in 4–6. In parallel, C runs 0–4 and L runs 4–10. P can start when S, D and L finish, so it runs 10–12, followed by W in 12–16. The resource constraint does not delay completion in this schedule because the engineering tasks still finish before L.

Add three weeks to circuit delivery: L now ends at week 13, P runs 13–15 and W runs 15–19. The critical chain remains C–L–P–W under these dependencies. Explain a different feasible ordering if used; do not add a further delay merely because a resource constraint exists. This exercise assumes the task durations and available engineer are as stated.

## Chapter 87 — The CTO dashboard

### 87.1 — Define a metric someone can act on

Example: the proportion of eligible one-minute observation intervals in which a named client population can complete the agreed order transaction within its latency limit. State the client/server scope, interval eligibility, aggregation, treatment of partial failure, source/clock, owner and freshness limit. Preserve numerator, denominator and unknown intervals.

When evidence becomes stale, display its age and an unknown/stale status; start the defined investigation. Do not extend the last green result indefinitely or silently count an unobserved interval as successful. A metric definition also needs the decision it supports and a route to the underlying evidence.

### 87.2 — Time is not population

`43,200×(1−0.9998) = 8.64` unavailable minutes. Customer-minutes need the number of affected customers through time and the definition of affected service. Eight minutes affecting one branch and eight minutes affecting every branch have the same elapsed duration but different population impact. The question excludes unknown intervals; introduce them explicitly if altering the example.

### 87.3 — Put a date on a defined model

“71% utilisation” lacks the resource, direction, denominator, sampling/aggregation, traffic profile, failure state, performance limit, growth assumption and complete delivery allowance. It supplies no unique investment date.

For an explicit variation of the chapter's model, start at 50 units, choose a 70-unit trigger and 3% monthly compound growth. `ln(70/50)/ln(1.03) = 11.38315 months`. Subtract the stated eight-month delivery/contingency allowance to obtain a latest decision in 3.38315 months. Keep monthly and annual growth distinct. Revisiting the assumptions can change the date even if the current dashboard percentage does not move.

### 87.4 — A combined percentage can hide the risky cohort

Invent a fully observed cohort of ten high-risk deployments, six of which fail: success is four of ten, or 40%. Add 990 successful trivial deployments. The combined success rate is 994/1,000 = 99.4%, which conceals the weak high-risk outcome.

Show counts and rates by a predefined risk class and service, alongside observation maturity, rollback and unknown outcomes. Keep comparable failure definitions and windows. A six-failure count without its cohort denominator cannot establish that cohort's rate, and a small cohort needs suitably cautious interpretation.

### 87.5 — A decision for a qualitative risk

Example: a critical service currently depends on one specialist and has no demonstrated alternate. Request an authorised allocation of cover/training time and a named alternate by an explicit date, with the decision owner and consequence of delay. Do not invent a numerical failure probability to make the risk look precise.

Verify the outcome through the alternate's bounded absence exercise: usable documentation, correct access and authority, demonstrated diagnosis/recovery and an accepted handover. Attendance at training is an input; successful performance in the relevant task is stronger evidence of the intended result.
