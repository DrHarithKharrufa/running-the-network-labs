# Aldergate Harrogate branch — one design, carried all the way through

Appendix C gives three reference networks at design-study depth. This document
does something narrower. It takes **one modest site** and carries it from
requirement to decision to acceptance test to fault test to recovery procedure
to owner to cost, with **one identifier set** the whole way, so any line traces
back to the requirement that caused it and forward to the test written to prove
it.

**What this is and is not.** It is a worked design at high-level-design depth,
plus the port map and platform assumptions you need to build it. **Nothing here
has been built, and nothing here has been applied to a device.** It does not
ship device configuration: the "generated from the source of truth" decision
below describes the intended practice, not a repository you can clone. Every
acceptance test and fault test below is a *written test with an expected
result*; none has been executed, so "pass condition" means what must be observed
before the site is accepted, not something that has been observed. When Chapter
79 asks you to produce a design, this is the level of *connectedness* that
counts as finished — every requirement traced, every rejection costed, every
agreed failure given a written test, every gap named. A written pass condition
is useful. It is not a passed test, and this document is not a claim of
acceptance.

Two checkers sit beside it and both are worth running before you trust a word:

- `check_addressing.py` validates `branch-hgt.json` — canonical, contained,
  disjoint, DHCP inside its own subnet, and every device loopback inside its own
  pool and outside every host LAN — and then **regenerates** the addressing
  block below from the JSON and compares it byte for byte. The addressing block
  is generated output; edit the JSON and run `--write`. The first draft of this
  document failed canonical, contained and disjoint. A later draft passed while
  the checker compared only the LAN prefixes and still reported that "the
  document agrees with the source"; an independent reviewer corrupted the
  loopback assignment, a printed DHCP endpoint and a printed spare block, and
  the checker passed all three. `test_check_addressing.py` keeps those cases.
- `check_traceability.py` checks that every requirement has a decision, an
  acceptance test, a fault test and a recovery procedure, and that none of those
  exists without a requirement. It checks *coverage*, not correctness: it will
  happily pass a design whose decisions do not achieve their requirements. Read
  the design as well. Two reviewers found decisions that did not achieve their
  requirements while this checker was passing.

---

## The site

Aldergate's Harrogate branch. 38 staff, one floor, a leased line and a
broadband backup. Deliberately small: a site you can hold in your head, where
the only reason to leave something out is that it genuinely is not needed.

| | |
|---|---|
| Site code | `HGT` |
| IPv4 allocation | `10.10.64.0/22`, from the `10.10.64.0/18` Appendix C leaves unallocated |
| IPv6 allocation | `2001:db8:a1de:300::/56`, the next /56 after Reading's `:200::/56` |
| AS | 64510 (Aldergate); branches do not run BGP |

**Why not `10.10.24.0/22`.** That would sit inside `10.10.16.0/20`, which
Appendix C reserves for London's growth and explicitly tells you not to consume
without changing the aggregation plan. A new site comes from unallocated space.
This is the most common way a tidy-looking plan quietly breaks summarisation.

### Services this site depends on

A design that does not say where a service lives cannot say what survives a
failure. These four are the whole of what the branch needs.

| Service | Where it runs | How the branch reaches it | Survives RP-03? |
|---|---|---|---|
| CRM, `svc-crm-prod` | A SaaS platform on the public internet, authenticated per user | HTTPS over whichever WAN is up; no VPN needed | **Yes** |
| File service, `fs-hub-01` | Aldergate's hub data centre, private addressing, SMB | Over `hgt-rtr-01`'s IPsec to the hub | **No** |
| Voice platform | Aldergate's hub | Over the same IPsec; SIP from the router's loopback | **No** |
| Guest internet | — | Guest VRF to the internet next hop (D-04) | **No**, VLAN 500 is shut while the router is out |

The two "no" rows are the price of R-01a, and they are the reason R-01a had to
be agreed rather than assumed. A NAT is not a VPN and it is not an authenticated
path to a private service.

### Devices

| Device | Role | Platform assumption |
|---|---|---|
| `hgt-rtr-01` | Branch router: WAN termination, inter-VLAN routing, policy, NAT, VPN | Policy ACLs, VRFs, IP SLA-style tracking; bridge domains with an integrated routed interface and spanning tree on the LAN ports (D-09); **two concurrent IKEv2 SAs to one peer with distinct outer sources, one of them behind NAT** (D-06) |
| `hgt-sw-01`, `hgt-sw-02` | Access switches, PoE | Layer 2 with 802.1X, PoE budget for 2 APs, and **an ingress filter that can be applied to VLAN 400 traffic on every controller port** — a port ACL or a VLAN access-map (D-05) |
| `hgt-ap-01..03` | Wireless | Controller-less or cloud-managed; one uplink each |
| `hgt-bms-01..03` | Building controllers: chiller, access control, lighting | Cannot be hardened, will not be replaced this decade; this is the premise of R-04, not a complaint |
| `hgt-fm-01` | Facilities-management host, `10.10.64.15` | An ordinary managed workstation on VLAN 100 |
| `hgt-cpe-01` | Carrier broadband CPE, routing and NAT capable, DHCP server | Supplied by the broadband carrier; holds the prepared degraded configuration (D-10), see RP-03 |
| `hgt-con-01` | Console server with 4G | Out-of-band access; the only way in when the router is down, see RP-03 and RP-05 |

`hgt-cpe-01` is in this table because RP-03 depends on it, and `hgt-fm-01` and
the three controllers are in it because R-04 and D-05 are about them. A recovery
procedure that needs a device the inventory does not list is a procedure that
will fail on the day; a security control whose subjects are not in the port map
is a control nobody can test.

### Port map

| From | Port | To | Notes |
|---|---|---|---|
| `hgt-rtr-01` | `wan0` | Carrier leased-line NTU | Primary. Public address |
| `hgt-rtr-01` | `wan1` | `hgt-cpe-01` LAN port | Backup. **Private address, translated by the CPE** — this is why D-06 needs two tunnels |
| `hgt-rtr-01` | `lan0` | `hgt-sw-01` `Gi1/0/1` | 802.1Q trunk, VLANs 100/200/400/500/900. Bridge domain per VLAN shared with `lan1` (D-09) |
| `hgt-rtr-01` | `lan1` | `hgt-sw-02` `Gi1/0/1` | Same trunk, same bridge domains, higher spanning-tree cost — **blocked in normal operation** (D-09) |
| `hgt-sw-01` | `Gi1/0/2` | `hgt-sw-02` `Gi1/0/2` | Inter-switch trunk, all five VLANs. **Not a protected port** — see D-05 |
| `hgt-sw-01` | `Gi1/0/5` | `hgt-fm-01` | Access VLAN 100 |
| `hgt-sw-01` | `Gi1/0/10` | `hgt-ap-01` | PoE; trunk, VLANs 100 and 500 |
| `hgt-sw-01` | `Gi1/0/11` | `hgt-ap-02` | PoE; trunk, VLANs 100 and 500 |
| `hgt-sw-01` | `Gi1/0/15` | `hgt-bms-01` chiller | Access VLAN 400, ingress filter per D-05 |
| `hgt-sw-01` | `Gi1/0/16` | `hgt-bms-02` access control | Access VLAN 400, ingress filter per D-05 |
| `hgt-sw-02` | `Gi1/0/10` | `hgt-ap-03` | PoE; trunk, VLANs 100 and 500 |
| `hgt-sw-02` | `Gi1/0/15` | `hgt-bms-03` lighting | Access VLAN 400, ingress filter per D-05. **On the other switch from `bms-01/02`, deliberately** |
| `hgt-sw-02` | `Gi1/0/20` | `hgt-con-01` | Out-of-band |

`hgt-bms-03` sits on the second switch because that is how buildings are wired —
the lighting controller is where the lighting riser is — and because a control
that only works when all the subjects share a switch is a control that fails
the first time somebody patches one somewhere else. D-05 is written against
this port map.

### Addressing

<!-- BEGIN GENERATED addressing -- edit branch-hgt.json, then run: python3 check_addressing.py --write -->

| VLAN | Purpose | IPv4 | IPv6 | DHCPv4 |
|---|---|---|---|---|
| 100 | User | `10.10.64.0/24` | `2001:db8:a1de:300::/64` | `.50`–`.230` |
| 200 | Voice | `10.10.65.0/25` | `2001:db8:a1de:301::/64` | `.20`–`.110` |
| 400 | Building systems | `10.10.65.128/26` | `2001:db8:a1de:302::/64` | `.140`–`.180` |
| 500 | Guest | `10.10.66.0/24` | `2001:db8:a1de:303::/64` | `.50`–`.230` |
| 900 | Infrastructure | `10.10.67.0/28` | `2001:db8:a1de:3ff::/64` | static |

Loopbacks come from their own blocks, `10.10.67.32/27` and `2001:db8:a1de:3fe::/64`, not from the infrastructure LAN: `hgt-rtr-01` is `10.10.67.32/32` and `2001:db8:a1de:3fe::1/128`. A loopback inside a host LAN's /64 works on some platforms and surprises you on others; a distinct pool costs nothing and removes the question.

Genuinely spare: `10.10.65.192/26`, `10.10.67.64/26`, `10.10.67.128/25`, `2001:db8:a1de:304::/64` and `2001:db8:a1de:305::/64`. This program proves they are spare.

<!-- END GENERATED addressing -->

The block above is generated from `branch-hgt.json`. Do not edit it by hand:
edit the JSON and run `python3 check_addressing.py --write`. Run the checker
with no arguments and it regenerates the block in memory and fails if the
document differs. The prose outside the markers is not generated and the
checker does not police it.

The VLAN 100 gateway is `10.10.64.1`. That address appears twice in this
design — on the router, and in the CPE's prepared degraded configuration (D-10)
— and the second one exists so that clients do not have to change anything
during RP-03.

---

## Requirements

Each has a source and a date, because a requirement nobody can trace to a person
is a preference.

| ID | Requirement | Source | Date |
|---|---|---|---|
| R-01 | Staff reach the CRM and the hub file service during working hours; a single **link or access-switch** failure must not prevent this for more than 5 minutes. Wired service; wireless coverage may be reduced — see D-03 and FT-04 | Branch manager, signed | 2026-02-11 |
| R-01a | A **router** failure is excepted from R-01's five minutes: degraded service on the backup path within **60 minutes**, and full restoration by the **end of the next business day after the replacement arrives**. Degraded means internet and the CRM; the hub file service, voice and guest access are unavailable meanwhile. Exception to R-01, agreed and recorded as BR-EX-04; network team proposed | Branch manager, signed exception BR-EX-04 | 2026-02-19 |
| R-02 | A call in progress survives a primary WAN failure with degraded quality rather than being dropped: the SIP registration does not re-establish, and the media gap stays within the figure agreed with the telephony owner and recorded in AT-05 | Telephony owner | 2026-02-11 |
| R-03 | Guest traffic never reaches an internal subnet | Security policy SEC-004 | 2026-01-08 |
| R-04 | Building controllers are reachable only from the facilities-management host, and cannot reach each other — **including when they are connected to different switches** | Security policy SEC-004, clarified 2026-02-20 | 2026-01-08 |
| R-05 | A failure is detectable from the NOC without a user reporting it | Operations lead | 2026-02-18 |
| R-06 | The site can be rebuilt from the source of truth by one engineer in one day | Operations lead | 2026-02-18 |
| R-07 | Recurring cost stays under £780/month | Finance, budget line BR-2026-HGT | 2026-02-04 |

**On R-01a, and on what a requirement rewrite can quietly lose.** The first
draft left R-01 saying five minutes, provided a next-business-day router
replacement, and called the gap "accepted risk". That is not how Chapter 79 says
to handle an infeasible requirement: you either meet it, or you obtain agreement
to change it, and the changed requirement is what the design is then judged
against. R-01a is that agreement — named, dated, and specific about what the
site does in the meantime. The alternative was priced before it was declined: a
resilient router pair adds about £120/month and breaks R-07.

The second draft then went too far in the other direction. It narrowed R-01 to
**link** failures only, so that R-01a could be the router exception — and in
doing so it silently dropped the commitment to survive an *access-switch*
failure, even though D-03 bought two switches for that purpose, FT-04 still
tested a five-minute wired target and RP-02 still existed. An independent
reviewer caught it. R-01 above names links and access switches explicitly. When
you narrow a requirement to make room for an exception, check what else was
living inside the words you removed.

**On R-04's last clause.** "Including when they are connected to different
switches" was added on 2026-02-20 after D-05's first version turned out not to
achieve it. The clause is in the requirement rather than only in the decision
because it is what the security owner actually wants, and a requirement that
only holds for a particular cabling arrangement is not a requirement.

---

## Decisions, and what each one costs

| ID | Decision | Serves | Rejected alternative, and what it would have cost |
|---|---|---|---|
| D-01 | Two WAN services on separate physical paths from separate providers: a 200 Mbps leased line and a 500/75 broadband behind `hgt-cpe-01` | R-01, R-01a, R-02 | A second leased line: +£410/month, breaks R-07, and buys availability this site does not need |
| D-02 | Static default via primary, with a tracked floating static via backup. Tracking uses an IP SLA probe to two off-site targets, with a 3-second down delay and a **300-second up delay** so a flapping primary cannot flap the service | R-01, R-02 | Branch BGP: no benefit at one exit pair, and a protocol every NOC engineer must then know to debug a 38-person site |
| D-03 | Two access switches. Each AP has a **single** uplink; the three APs are split two on `hgt-sw-01`, one on `hgt-sw-02` | R-01 | Dual-homing each AP: needs LACP-capable APs and doubles the PoE port count. A stacked switch pair was also rejected: a stack is one failure domain and one upgrade takes both. **D-05 pays for that rejection** — see below |
| D-04 | Guest VLAN 500 terminates in its own VRF whose only route is a default to the internet next hop; no route leak in either direction, and the VRF has no interface in any internal subnet | R-03 | ACLs on a shared routing table: enforceable but one edit away from wrong, and the failure is silent |
| D-05 | Building systems in VLAN 400. The router ACL permits only `hgt-fm-01` (`10.10.64.15`, `2001:db8:a1de:300::15`) to reach the VLAN. Within the VLAN, isolation is enforced by an **ingress filter on every controller access port, on both switches** — a port ACL, or a VLAN access-map applied to VLAN 400 — which drops any packet whose source *and* destination are both inside the VLAN 400 prefixes, and permits only the FM host, DHCP, DNS and NTP | R-04 | **Protected ports: rejected because they do not do this job here** — the reasoning is below, and it is the design decision in this document most worth reading. Private VLANs: £0 if both switches support them and the secondary VLAN is carried across the inter-switch trunk, which these access switches do not list. One subnet per controller, leaving the router ACL as the only path: £0, consumes three of the spare blocks and three DHCP scopes, and renumbers the controllers — the fallback if the chosen switches cannot filter at ingress |
| D-06 | Voice rides IPsec to the hub voice platform over **two IKEv2 tunnels, one per WAN path, both established at all times**, with the router's loopback as the inner source of both. Failover is an inner routing decision between two live tunnels | R-02 | Three alternatives, all rejected, below |
| D-07 | Active monitoring: synthetic HTTPS probe to the CRM from the site every 60 s, plus interface, IP SLA, spanning-tree topology-change and tunnel state on both tunnels | R-05 | Interface-up alarms only: a session can stay up while the service is gone |
| D-08 | All configuration generated from the source of truth; nothing hand-edited on the device | R-06 | Hand-built with a documented runbook: the runbook and the device diverge, and you find out during the rebuild |
| D-09 | The router's two LAN ports are **one bridge domain per VLAN**, each with a single routed interface carrying that VLAN's gateway address, and the router runs spanning tree on both ports. The `rtr`–`sw-02` link has the higher cost and is blocked in normal operation; it unblocks if `hgt-sw-01` or the `rtr`–`sw-01` link fails | R-01 | Two independent routed subinterfaces in the same subnet: not an alternative, a misconfiguration. One router uplink to `hgt-sw-01` only, with `hgt-sw-02` behind the inter-switch trunk: £0 and simpler, but an `hgt-sw-01` failure then takes the gateway with it and R-01's five minutes cannot be met without a human moving a lead. A link aggregation across both switches: needs MLAG or a stack, and D-03 rejected the stack |
| D-10 | `hgt-cpe-01` is managed as part of this site's source of truth and holds a **prepared** degraded configuration: the VLAN 100 gateway address `10.10.64.1`, a DHCP scope identical to the router's, and the same DNS servers. Verified at the monthly out-of-band check | R-01a, R-06 | Configuring the CPE on the day: a configuration nobody wrote down is one somebody invents during an incident, and the gateway address it invents will not be the one every client already holds |

### Why D-05 is an ingress filter and not a protected port

The first version of D-05 said "switch protected ports stop controllers reaching
each other within the VLAN". With two independent switches joined by a trunk,
that is not true, and the reason is worth following because the mistake is easy
and the failure is silent.

Cisco's own documentation for a protected port says that it "does not forward
any traffic (unicast, multicast, or broadcast) to any other port that is also a
protected port", but that "forwarding behavior between a protected port and a
nonprotected port proceeds as usual". It also says that "because a switch stack
represents a single logical switch, Layer 2 traffic is not forwarded between any
protected ports in the switch stack, whether they are on the same or different
switches in the stack".

Read those three sentences against this port map. The inter-switch trunk is not
a protected port. So:

```
hgt-bms-01  →  Gi1/0/15 on sw-01  →  Gi1/0/2 trunk  →  sw-02  →  Gi1/0/15  →  hgt-bms-03
   (protected)                        (not protected)                (protected)
```

No switch in that path is forwarding between two *locally* protected ports, so
no protected-port rule is broken and the frame is delivered. The one arrangement
in which protected ports would cover both controllers is the stack — which D-03
rejected, for availability reasons that remain good. Two decisions in this
document were in direct conflict and the traceability checker passed anyway,
because coverage is not correctness.

An ingress filter on the controller's own access port drops the frame before it
reaches the trunk, which makes the control independent of where the other
controller happens to be patched. That is the property R-04 asks for. Three
consequences to accept:

- The filter is configuration on every controller port, so it belongs in the
  generated configuration (D-08) and a new controller port without it is a hole.
  AT-04 is the test that finds one.
- It is a per-switch control enforced at ingress, not a fabric-wide policy. If a
  controller is ever patched into a port without the filter, the isolation is
  gone and nothing alarms. RP-04 preserves the counters; FT-06 and AT-04 are
  what catch it.
- It needs the platform to filter on VLAN 400 traffic at ingress. If the
  switches finally chosen cannot, the fallback in D-05's rejected column — one
  subnet per controller — moves the control to the router ACL that AT-03 already
  tests, and changes the address plan.

### Why D-06 is two tunnels and not one

The first version of D-06 said the tunnel is sourced from the router's loopback,
"which is reachable over either WAN, so a path change re-routes the tunnel
without re-establishing the SIP registration or changing the media's source
address". The second half of that is right and the first half does not follow.

| | Primary path | Backup path |
|---|---|---|
| Outer source | `wan0`, public | `wan1`, **private**, translated by `hgt-cpe-01` |
| Outer destination | the voice platform's public IPsec endpoint | the same endpoint |
| Encapsulation | ESP, IKEv2 | ESP in UDP 4500, IKEv2 with NAT traversal |
| Inner source | `10.10.67.32` (the loopback) | `10.10.67.32`, **the same** |
| What the phone sees | registration and media source unchanged | unchanged |

A loopback keeps the *inner* addresses stable, which is what the SIP
registration and the media source depend on. It does nothing for the *outer*
endpoint: the outer source address and, on the backup path, its NAT mapping both
change when the path changes, and an established IKE/IPsec security association
does not follow an address change by itself.

So D-06 establishes both tunnels and keeps them both up. Failover is then an
inner routing decision between two live tunnels, which is a thing the router
does in milliseconds, rather than a key exchange, which is not.

**Rejected: one tunnel, relying on the loopback.** The failure above.

**Rejected: one tunnel with IKEv2 MOBIKE.** This is the function that genuinely
does what the first version assumed: RFC 4555 "allows the IP addresses
associated with IKEv2 and tunnel mode IPsec Security Associations to change",
and "updates only the outer (tunnel header) addresses of IPsec SAs, [while] the
addresses and other traffic selectors used inside the tunnel stay unchanged".
The topology fits its assumptions — the branch is the initiator and the branch
is the side behind the NAT, which is the case the RFC supports; it says the
responder's addresses changing "is not fully supported". MOBIKE is therefore a
legitimate single-tunnel design **if both ends negotiate it**, and it is a
capability to specify in the order, not a consequence of the loopback. It is
rejected here only because it makes the design depend on one negotiated
extension at both ends, where two tunnels depend on ordinary IKEv2.

**Rejected: SIP direct to the carrier over each WAN.** The public source address
changes on failover, which drops the call — the failure R-02 exists to prevent.

What is still an assumption, and what FT-02 is for: that the branch router
sustains two concurrent IKEv2 SAs to one peer with distinct outer sources, one
behind NAT; that the voice platform accepts two SAs from one identity; that
liveness detection on the failed tunnel fires inside the agreed media gap; and
that the 75 Mbps backup upstream carries the call *and* the site's other traffic
at the same time. None of those has been measured. Three of them are questions
for the platform vendor before the order, not for the engineer on the day.

---

## Acceptance tests — written before the site is accepted, and not yet run

| ID | Test | Serves | Pass condition |
|---|---|---|---|
| AT-01 | From a VLAN 100 host, HTTPS to the CRM and SMB to `fs-hub-01` | R-01 | Both succeed; TLS chain validates; the SMB session is shown to be inside the IPsec tunnel rather than reaching the hub some other way |
| AT-02 | From a VLAN 500 guest host, attempt each internal subnet in turn, v4 and v6; then reach a permitted site on the public internet | R-03 | Every internal attempt fails and the internet attempt **succeeds** — a control that blocks everything is not the control R-03 asked for. The guest VRF's table is inspected and shown to contain only the default route and its connected guest subnets, so isolation comes from the next hop being an internet router with no path back, plus an ACL applied **inbound on the guest-facing interface** — the direction in which guest-originated packets arrive — dropping RFC 1918 destinations and the enterprise's own v6 /48. Both the VRF table and the ACL counters are recorded |
| AT-03 | From a host that is not the FM host, reach a VLAN 400 controller over v4 and over v6; then repeat from `hgt-fm-01` | R-04 | Both non-FM attempts fail with the router ACL counter incrementing; both FM attempts succeed |
| AT-04 | Controller to controller, **four cases**: `bms-01`→`bms-02` (same switch) and `bms-01`→`bms-03` (across the inter-switch trunk), each over v4 and v6. Then `hgt-fm-01` to all three | R-04 | All four controller-to-controller attempts fail, with the ingress-filter counters incrementing **on the source's own switch**; all three FM attempts still succeed. The single same-switch test the first version of this document specified would have passed while the cross-switch path was wide open |
| AT-05 | Voice call in progress; record MOS and jitter for 5 minutes, the SA pair on **both** tunnels, and which inner route is selected. **Agree and write down the maximum media gap and the MOS floor before acceptance** | R-02 | Baseline recorded for comparison in FT-02, and the two agreed figures written into R-02's row before the test is accepted; without them FT-02 cannot fail |
| AT-06 | Disable the synthetic probe target; confirm the NOC receives the alert | R-05 | Alert raised within 180 s, routed to the on-call queue, acknowledged by a human |
| AT-07 | Rebuild `hgt-sw-02` from the source of truth onto a factory-reset unit | R-06 | Resulting configuration byte-identical to the generated file, **including the D-05 ingress filter on `Gi1/0/15`**; AT-01 passes afterwards |
| AT-08 | Sum the monthly recurring charges from the signed orders | R-07 | Total ≤ £780 |
| AT-09 | Exercise the prepared degraded path before acceptance: in a maintenance window, or on a bench pair of the same models, power down the router, run RP-03 steps 1–6, and time them | R-01a | The CRM is reachable from a VLAN 100 host over the CPE path; a client that releases and renews gets the same address, gateway and DNS; VLANs 200/400/500/900 are confirmed shut; the elapsed time is recorded as the figure R-01a's 60 minutes is judged against. Then revert and re-run AT-01 |

---

## Fault tests — what is deliberately broken, and what should happen

An acceptance test says what must be observed before the site is accepted. A
fault test says what must be observed when something is deliberately broken,
which is the half most designs never write down. Neither is evidence until it
has been run, and none of these has been run.

| ID | Fault injected | Serves | Expected observable | Limit |
|---|---|---|---|---|
| FT-01 | Shut the primary WAN at the carrier demarcation | R-01 | IP SLA fails, floating static installs, AT-01 passes again | ≤ 120 s |
| FT-02 | Repeat FT-01 with a call in progress, under the backup's expected load | R-02 | The inner route moves to the second tunnel; the SIP registration does not re-establish and the media source address does not change; the call continues. **Record, before and after: the outer source address on each side, which SA pair is carrying traffic, the inner route chosen, the media gap in milliseconds from the RTP sequence numbers, and the MOS against the AT-05 baseline.** Then restore the primary and repeat with the primary flapping three times | call not dropped; media gap within the AT-05 figure; MOS above the agreed floor |
| FT-03 | Restore the primary and flap it three times in five minutes | R-01 | The 300-second up delay holds the service on the backup; the primary is reinstated once, after it has been stable for that period | one transition |
| FT-04 | Power off `hgt-sw-01` | R-01 | `hgt-ap-03` stays up; the two APs on `hgt-sw-01` are lost until their patch leads are moved; the `rtr`–`sw-02` link unblocks (D-09) and AT-01 passes from a host on `hgt-sw-02`. **Wireless coverage is reduced, not maintained** — record which areas lose signal. `hgt-bms-01` and `hgt-bms-02` are also lost; that is accepted, R-04 is about reachability, not availability | ≤ 300 s for wired |
| FT-05 | Remove the guest VRF's default route | R-03 | Guest loses internet; **no** internal subnet becomes reachable. A control that fails must fail closed |
| FT-06 | From a user VLAN, attempt VLAN 400 over v4 and v6 with the FM host offline; then patch a spare controller into a VLAN 400 port that has **no** ingress filter and repeat AT-04 | R-04 | The first case is denied in both families, counters increment, alert raised. The second case **succeeds**, which is the point: it demonstrates that D-05's control is per-port configuration and that a port without it is a hole. Record it, then fix the port | — |
| FT-07 | Black-hole the probe's return path without taking the service down | R-05 | The probe alerts, and the alert says it is about reachability *from this site*, not about the service. An alert that cannot distinguish these is worse than none |
| FT-08 | Corrupt one generated file in the source of truth, then rebuild `hgt-sw-02` | R-06 | The rebuild fails loudly at validation rather than producing a working-looking switch with the wrong policy | fails before deployment |
| FT-09 | Power off `hgt-rtr-01` — in a maintenance window, or on the bench pair used for AT-09 | R-01a | Service degrades to the CPE path per RP-03. Record what actually works: internet and the CRM through CPE NAT; **no file service, no voice, no inter-VLAN policy, no guest**. This is the agreed exception being exercised, not a failure of the design | degraded service ≤ 60 min (separately: full restoration by end of the next business day after the spare arrives) |
| FT-10 | Pull the `hgt-rtr-01`–`hgt-sw-01` LAN link, leaving both switches up | R-01 | The blocked `rtr`–`sw-02` link unblocks; the VLAN gateways stay reachable from hosts on both switches; the topology change is logged and alerted (D-07) | ≤ 30 s to forwarding; AT-01 passes within 300 s |

**Declared exemption.** R-07 has no fault test. It is a commercial constraint,
not a behaviour, and there is nothing to break: AT-08 checks it and the residual
risk section says what happens when it binds. Every other requirement has one,
and `check_traceability.py` does not accept a silent omission.

---

## Recovery procedures

| ID | For | Serves | Procedure | Tested by |
|---|---|---|---|---|
| RP-01 | Primary WAN failure | R-01, R-02 | Automatic. Confirm the backup carried the service and that the inner route moved to the second tunnel. Raise the carrier ticket. Failback is held by D-02's 300-second up delay; if the primary is flapping, disable the tracked static manually and fail back by hand only after the carrier confirms a fix | FT-01, FT-03 |
| RP-02 | Switch failure | R-01, R-06 | Move the affected patch leads to spare ports on the surviving switch — **including any VLAN 400 controller lead, which must go to a port carrying the D-05 ingress filter, not simply a free port**. Then replace the unit from the on-site spare, rebuild from the source of truth, run AT-07, AT-04 and AT-01 | FT-04, AT-07 |
| RP-03 | Router failure | R-01a | Eight steps, prepared in advance by D-10 and rehearsed by AT-09 — set out in full below | FT-09, AT-09 |
| RP-04 | Either enforced boundary breached: guest reaching an internal subnet, or a controller reachable from anywhere but the FM host | R-03, R-04 | Shut the offending VLAN at both switches — 500 for the guest boundary, 400 for the controllers. Preserve the VRF table, the router ACL counters and **the ingress-filter counters on both switches** *before* any change, then investigate. The evidence is gone once you reconfigure | FT-05, FT-06 |
| RP-05 | Site unreachable, cause unknown | R-05 | Out-of-band to `hgt-con-01` over 4G. Confirm it is reachable monthly, because an untested out-of-band path is a story people tell themselves — and because RP-03 cannot start without it | monthly check |
| RP-06 | Cost overrun on renewal | R-07 | Re-price against the residual-risk note before renewing; if the leased line rises, D-01 is the decision to revisit, not the support contract | annual review |

### RP-03 in full — router failure

The procedure the second review found incomplete. It was incomplete in four
specific ways: the switch port's LAN configuration was undefined, the clients'
gateway and DNS in the degraded state were unstated, the list of surviving
services contradicted itself in three places, and one deadline was being used to
satisfy a different one.

1. **Get in.** Reach `hgt-con-01` over 4G. Switch management lives in VLAN 900,
   whose gateway is the router that has just failed, so the console server is
   the only way to configure the switches. This is why RP-05's monthly check is
   a dependency of RP-03 and not a nicety.
2. **Reconfigure the port.** On `hgt-sw-01`, change `Gi1/0/1` from an 802.1Q
   trunk to an **untagged access port in VLAN 100**. `hgt-cpe-01`'s LAN port is
   an ordinary untagged Ethernet port and does not terminate 802.1Q; if a
   future CPE does, record that instead and leave the port tagged for VLAN 100
   only. The generated configuration (D-08) holds both variants as named
   degraded profiles so this is a profile selection, not improvisation.
3. **Re-patch.** Move `Gi1/0/1` to the CPE's LAN port.
4. **Addressing continues to work because it was prepared.** The CPE already
   holds, from the source of truth (D-10), the VLAN 100 gateway address
   `10.10.64.1`, a DHCP scope matching the router's `.50`–`.230`, and the same
   DNS servers. Clients holding leases keep working; clients that renew get the
   same values. Nothing is reconfigured on a single workstation.
5. **Shut what is no longer policed.** Shut VLANs 200, 400, 500 and 900 at both
   switches. Without the router there is no inter-VLAN policy and no guest VRF,
   and an unpoliced guest VLAN behind a NAT is worse than no guest VLAN. The
   controllers are off the network for the duration; R-04 is about who may reach
   them, and nobody reaching them satisfies it.
6. **Verify, and record the time.** From a VLAN 100 host: HTTPS to the CRM
   succeeds. SMB to `fs-hub-01` **fails, and is expected to fail** — it is
   reached over the router's IPsec, and a CPE supplies NAT, not a VPN and not
   an authenticated path to a private service. Voice is down. Record the elapsed
   time from the failure being declared: **this is the measurement R-01a's
   60 minutes is about.**
7. **Order the replacement.** The support contract ships a cold spare next
   business day. Shipping is not restoration.
8. **Restore.** When the spare arrives: rebuild from the source of truth, run
   AT-07, revert `Gi1/0/1` to its trunk profile, re-patch to the router,
   un-shut the four VLANs, then run AT-01, AT-04 and AT-05. **This** is what
   R-01a's second deadline measures: complete by the end of the next business
   day after the spare arrives.

**Two deadlines, measured separately, because they are different
commitments.** Degraded service — steps 1 to 6 — within 60 minutes of the
failure being declared. Full restoration — step 8, with AT-01, AT-04 and AT-05
passing — by the end of the next business day after the spare arrives. The
earlier version of this design used "the spare ships next business day" as
though it established "restored within one business day". It does not: shipping,
arrival, configuration and acceptance are four steps and only the first is in
the carrier's gift.

**Who can do this.** Steps 1 to 6 need somebody on site to move a patch lead
and somebody with console-server access to change the port. At a 38-person
branch those are usually different people, so name both in the on-call rota
rather than assuming the engineer is in the building.

---

## Ownership

| Element | Owner | Escalation |
|---|---|---|
| Router, switches, WAN, CPE | Network team, `net-ops@` | On-call rota |
| APs and wireless | Network team | On-call rota |
| VLAN 400 controllers | Facilities; network provides the path and the policy only | Facilities duty manager |
| `hgt-fm-01`, the FM host | Facilities, built to the standard workstation image | Facilities duty manager |
| Guest portal terms | Legal and marketing | — |
| Source of truth for this site, including the CPE's degraded profiles | Network team, repo `aldergate-sot`, path `sites/hgt/` | — |

Name one accountable owner for each element even where the work is shared. A
row with two names is a row where an escalation stalls while both check whether
it was theirs.

---

## Cost

Capital, with quantity, unit price and extended total stated separately,
amortised over 60 months. These are planning assumptions, not quotations, and
they assume the platform assumptions above are met at these prices — which is
exactly the kind of assumption a procurement exercise overturns.

| Item | Qty | Unit | Extended |
|---|---|---|---|
| Router `hgt-rtr-01` | 1 | £2,400 | £2,400 |
| Switch `hgt-sw-01/02` | 2 | £950 | £1,900 |
| Access point | 3 | £350 | £1,050 |
| Spare switch, held on site (RP-02) | 1 | £950 | £950 |
| Console server with 4G (RP-05) | 1 | £420 | £420 |
| **Capital total** | | | **£6,720** |
| **Amortised** | | | **£112.00 / month** |

| Recurring line | Monthly | Serves |
|---|---|---|
| Leased line, 200 Mbps, 4-hour fix | £395 | R-01, D-01 |
| Broadband 500/75 with CPE, next business day | £64 | R-01a, R-02, D-01 |
| Hardware amortised | £112 | R-01, R-01a |
| Support contract, next business day | £71 | RP-02, RP-03 |
| Out-of-band 4G data | £18 | RP-05 |
| Monitoring, per-site licence | £32 | R-05, D-07 |
| **Total** | **£692** | R-07 (limit £780) |

£88/month of headroom. If R-01a were withdrawn and R-01's five minutes applied
to the router as well, a resilient pair adds about £120/month and the headroom
is gone — which is the conversation to have with the branch manager, not a
change to make quietly.

---

## Residual risk, stated rather than buried

1. **The router remains a single point of failure**, and R-01a is the agreed
   exception that makes the design compliant rather than merely apologetic.
   Review it the moment R-01a is questioned, the site grows past about 60 staff,
   or voice becomes business-critical at this site — RP-03 has no voice and no
   file service.
2. **FT-02's quality threshold is a judgement until somebody writes a number.**
   "Degraded but not dropped" is not a figure. AT-05 requires the maximum media
   gap and the MOS floor to be agreed with the telephony owner before
   acceptance, or FT-02 cannot fail.
3. **FT-04's and FT-10's limits are design intent, not observations**, and
   FT-04 covers wired service only. Wireless coverage is genuinely reduced until
   somebody moves two patch leads.
4. **RP-03 has not been exercised, and AT-09 exists to exercise it.** Until
   AT-09 has been run, the 60-minute figure in RP-03 is an estimate. It does not
   need a day-long production outage to test: a maintenance window, or a bench
   pair of the same router, switch and CPE models, is enough, and a design that
   can only be validated by an outage is a design nobody will ever validate.
5. **D-05 and D-09 both depend on platform features that no specific product
   has yet been selected against.** If the switches cannot filter VLAN 400
   traffic at ingress, D-05's fallback renumbers the controllers into separate
   subnets and the address plan changes. If the router cannot bridge its two
   LAN ports with spanning tree, D-09's rejected single-uplink alternative
   returns and R-01's switch-failure commitment goes back to the branch manager.
   Resolve both before the order, not during the build.
6. **D-06's two-tunnel design has not been tested anywhere**, and three of its
   assumptions belong to vendors rather than to this document: two concurrent
   IKEv2 SAs from one router to one peer with distinct outer sources, the
   platform's acceptance of two SAs from one identity, and liveness detection
   fast enough for the agreed media gap.

---

## Tracing one line, forwards and backwards

Pick the guest VRF. It exists because of **D-04**, which exists because of
**R-03**, which came from security policy SEC-004 on 8 January and has a named
owner. It is proved by **AT-02**, which inspects the VRF's table and the ACL's
direction and counters rather than asserting that no path exists, and which
requires a permitted flow to succeed as well as the forbidden ones to fail. It
is proved to fail safely by **FT-05**, which removes the default route and
requires that no internal subnet becomes reachable. When it goes wrong,
**RP-04** says to preserve the counters before reconfiguring. It costs nothing
on its own line, because it is a configuration choice rather than a purchase.

Now pick the controller isolation and notice the difference. **R-04 → D-05 →
AT-04 → FT-06 → RP-04** traces just as neatly, and the first version of D-05
did not achieve R-04 at all. The chain was complete and the design was wrong.
That is the limit of traceability as a check, and the reason both checkers beside
this document say so in their own output: coverage is cheap, correctness is
read by a person.

If you can trace every line of your own design, it is finished in the sense this
chapter means. Whether each decision achieves its requirement is a separate
question, and the only way to answer it is to have somebody who knows the
mechanism read the design and try to break it on paper. Two readers did that to
this one and both found real defects. Budget for that step.
