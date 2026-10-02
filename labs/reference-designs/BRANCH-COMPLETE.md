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
failure. These are the business services; their supporting dependencies are listed below.

| Service | Where it runs | How the branch reaches it | Survives RP-03? |
|---|---|---|---|
| CRM, `svc-crm-prod` | A SaaS platform on the public internet, authenticated per user | HTTPS over whichever WAN is up; no VPN needed | **Yes** |
| File service, `fs-hub-01` | Aldergate's hub data centre, private addressing, SMB | Over `hgt-rtr-01`'s IPsec to the hub | **No** |
| Voice platform | Aldergate's hub | Phone VLAN 200 addresses over the selected IPsec tunnel; hub replies use the surviving tunnel | **No** |
| Guest internet | — | Guest VRF to the internet next hop (D-04) | **No**, VLAN 500 is shut while the router is out |

The unavailable service rows are the price of R-01a, and they are the reason R-01a had to
be agreed rather than assumed. A NAT is not a VPN and it is not an authenticated
path to a private service.

### Supporting services and management paths

Normal DHCP is local to the router. Degraded DHCP is activated on the CPE only
after router disconnection; identical pool bounds are not lease synchronisation.
Use reviewed reservations for managed clients, or a tested lease-state transfer
with duplicate-address detection; a renewed client may get another free address
if its application contract allows it. AT-09 must include expired leases and a
new client. Never promise the same client address solely from matching scopes.
DNS resolvers named in the source of truth must be reachable through ordinary
internet access and during RP-03; a hub-only resolver cannot support that mode.
SaaS identity/SSO, time and TLS trust must also work without the failed hub VPN.
Degraded service is IPv4-only until IPv6 has a separately qualified profile;
AT-09 tests clients retaining stale IPv6 defaults/DNS, including fresh login.

The intended four-port console server has serial port 1 to the router console,
port 2 to sw-01 console, port 3 to sw-02 console and port 4 to the CPE management
console **if that CPE supports it**. Its Ethernet sw-02 attachment is for normal
management; it is not the recovery transport. Recovery uses independent 4G and
serial access, with separately protected power, approved credentials and no
dependence on VLAN 900, production DNS or SSO. Verify carrier permission and CPE
console/profile support before ordering; otherwise price a managed replacement.
Monthly checks and AT-09 test both switch consoles with the router off, and
reachability with sw-02 off. A label saying out-of-band is not a tested path.

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
| `hgt-rtr-01` | `lan1` | `hgt-sw-02` `Gi1/0/1` | Same trunk/bridge domains; **sw-02’s receiving port is alternate/discarding**, router lan1 is designated/forwarding (D-09) |
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
| R-07 | Monthly equivalent network cost, including recurring cash charges and capital allocated over 60 months, stays under £780/month; capital/cash reported separately | Finance, illustrative budget definition BR-2026-HGT | 2026-02-04 |

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
| D-02 | Primary tracked default and worse-preference backup default. Two authorised off-site probe targets each have a primary-only host route and a less-preferred discard route preventing escape through the backup; verify egress and reply paths. Withdraw when both targets fail their declared timeout; reinstate only after both recover for 300 seconds. A 3-second down delay follows the failed probe decision, not the start of the outage. Probe interval, timeout and forwarding-programming time belong in the tested service budget | R-01, R-02 | Branch BGP: no assumed benefit for this small service; compare if supplier routing requirements change |
| D-03 | Two access switches; APs split two/one with single uplinks. Reserve enough correctly configured access ports and PoE capacity on each surviving switch for the other switch’s wired clients and required devices. A named onsite responder, accessible labelled patching and timed repatching must demonstrate R-01’s five-minute target before acceptance; two switches alone do not preserve singly attached clients | R-01 | Dual-homing suitable endpoints needs endpoint/platform support. A stack can share control/software failure domains; qualify actual upgrade and failover behaviour rather than assuming every stack upgrade takes both members down |
| D-04 | Guest VLAN 500 terminates in its own VRF whose only route is a default to the internet next hop; no route leak in either direction, and the VRF has no interface in any internal subnet | R-03 | ACLs on a shared routing table: enforceable but one edit away from wrong, and the failure is silent |
| D-05 | VLAN 400 router policy permits only the FM host to initiate controller management, with explicit necessary infrastructure flows. Bind the FM address/MAC to its authorised managed port and reject spoofed FM sources at other user/controller ingress ports; validate both address families. Controller-port ingress policy is default-deny, validates each controller’s allowed source identity, and denies controller-to-controller traffic for IPv4, IPv6 global/link-local and unapproved non-IP frames. Ordered rules and ARP/ND handling must be qualified on the chosen switches by AT-04; a deny matching only the allocated prefixes is insufficient | R-04 | Protected ports alone fail across this unprotected trunk. Supported fabric-wide private VLANs are an alternative. Separate routed subnet per controller is the fallback if ingress policy cannot meet the full boundary; it requires an amended address plan, DHCP scopes and controller renumbering before deployment |
| D-06 | Two continuously established route-based IKEv2/IPsec tunnels to the hub VPN gateway, one pinned to each WAN outer path. Phones retain their VLAN 200 inner addresses; no loopback source-NAT or SBC is assumed. The router loopback is a routing/management identity. Branch and hub select the surviving inner route, with return-path failover and liveness tested under the agreed voice-load/media-gap target | R-02 | Single tunnel with an unchanging inner address alone does not move its outer SA. Negotiated MOBIKE is a possible separately qualified design; direct carrier SIP with changing public NAT identity needs its own session-continuity qualification |
| D-07 | Active monitoring: synthetic HTTPS probe to the CRM from the site every 60 s, plus interface, IP SLA, spanning-tree topology-change and tunnel state on both tunnels | R-05 | Interface-up alarms only: a session can stay up while the service is gone |
| D-08 | All configuration generated from the source of truth; nothing hand-edited on the device | R-06 | Hand-built with a documented runbook: the runbook and the device diverge, and you find out during the rebuild |
| D-09 | Bridge domain and one routed gateway per VLAN across both router LAN ports. Use a mutually supported rapid spanning-tree profile: router root priority 4096, sw-01 priority 8192, sw-02 priority 12288 for every mapped instance. With long path costs, router-facing sw-01 and inter-switch ports cost 20000; sw-02’s router-facing port costs 60000. Router ports are designated/forwarding; sw-01 uses its router port as root; sw-02 uses its inter-switch port as root (total 40000) and its router-facing port is alternate/discarding. Failures of sw-01 or router–sw-01 cause sw-02’s direct router port to become root/forwarding | R-01 | Separate routed interfaces in one subnet are not an alternative. A single router uplink loses gateway access on its access-switch failure. Cross-switch LAG needs a qualified stack/MLAG design |
| D-10 | CPE normal profile: dedicated nonoverlapping transit 192.0.2.0/30 (documentation addresses), CPE .1 and router WAN1 .2, NAT to broadband; no user DHCP on the transit. Store an inactive degraded profile with VLAN 100 gateway 10.10.64.1/24, approved internet-reachable DNS and DHCP reservations or verified lease-state transfer. Authorised out-of-band activation/deactivation, carrier permission and collision-free leases are pre-order gates. The profiles are intended artefacts, not supplied configurations | R-01a, R-06 | Inventing a profile during the incident is unacceptable; a carrier CPE that cannot be managed/reprofiled requires a separately priced managed recovery gateway |

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

A fully qualified controller-port ingress policy can reject prohibited traffic
before the trunk. The old allocated-prefix-only deny does not cover link-local
IPv6, source spoofing or non-IP traffic. Separate IPv4, IPv6 and MAC/Layer2
handling, required ARP/ND and source binding must be tested together. If the
selected switches cannot meet AT-04 without opening peer communication, use
the separately routed fallback and regenerate the amended address plan. Three
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
address". Neither claim follows from assigning a loopback alone. Ordinary phone addresses
remain stable inside the tunnels; the loopback is not their SIP/media source.

| | Primary path | Backup path |
|---|---|---|
| Outer source | `wan0`, public | `wan1`, **private**, translated by `hgt-cpe-01` |
| Outer destination | the voice platform's public IPsec endpoint | the same endpoint |
| Encapsulation | ESP, IKEv2 | ESP in UDP 4500, IKEv2 with NAT traversal |
| Inner source | Phone address from VLAN 200; no source rewrite assumed | Same phone address |
| Return route | Hub selected primary inner route | Hub selected backup inner route |
| Loopback role | Routing/management identity, not the phone's media source | Same identity |

Stable inner phone addresses do not move an established outer SA after its
address/NAT mapping changes. Both route-based tunnels therefore stay up, each
with its outer route pinned to its own WAN; the backup NAT mapping needs
qualified keepalives. Branch and hub liveness and route selection must move
both directions of the voice flow. Millisecond route programming is not a
measured service-gap promise: detection, loss and application behaviour belong
in FT-02. Check traffic selectors and simultaneous SAs at the **hub VPN gateway**,
not merely whether the voice application accepts a registration.

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
behind NAT; that the hub VPN gateway accepts two SAs from one identity; that
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
| AT-03 | From a host that is not the FM host, reach a VLAN 400 controller over v4 and over v6; then repeat from `hgt-fm-01` | R-04 | Ordinary non-FM attempts fail with router ACL evidence; repeat from another user port spoofing the FM identity, including with FM offline, and require source-validation denial. Genuine FM attempts succeed in both families |
| AT-04 | Same-switch and cross-switch controller pairs over IPv4, IPv6 global and link-local; repeat with spoofed FM/controller sources and unapproved non-IP frames. Then FM to each controller and each required DHCP/DNS/NTP flow | R-04 | Prohibited sessions fail with source-port policy evidence; necessary ARP/ND and named infrastructure flows work without opening controller-to-controller communication. Verify ordered IPv4/IPv6/MAC rules and source binding on both switches. Unsupported behaviour blocks purchase/acceptance and selects the separately routed fallback |
| AT-05 | Voice call in progress; record MOS and jitter for 5 minutes, the SA pair on **both** tunnels, and which inner route is selected. **Agree and write down the maximum media gap and the MOS floor before acceptance** | R-02 | Baseline recorded for comparison in FT-02, and the two agreed figures written into R-02's row before the test is accepted; without them FT-02 cannot fail |
| AT-06 | Disable the synthetic probe target; confirm the NOC receives the alert | R-05 | Alert raised within 180 s, routed to the on-call queue, acknowledged by a human |
| AT-07 | Rebuild each switch and the router from reviewed intended artefacts on factory-reset replacements; retain per-platform observations | R-06 | Rendered artefact digest matches approval; release-qualified canonical/semantic read-back has no unapproved changes, including controller policy. Verify persistence/reboot, both WAN and hub reply paths, management access and original service tests. Device-specific identifiers/default ordering are documented exemptions from literal byte comparison; time the complete site rebuild against one working day |
| AT-08 | Reconcile supplier orders and capital allocation against the defined monthly-equivalent budget | R-07 | Recurring cash £580 plus £6720 capital allocated over 60 months (£112) gives £692/month equivalent, at or below £780. Record capital and cash separately; taxes/financing and a changed asset basis need a revised decision |
| AT-09 | Bench or approved maintenance rehearsal: power down router, use both switch serial consoles, activate CPE degraded profile and execute RP-03 steps 1–6 | R-01a | Existing/expired leases, a fresh client and simultaneous renewals show no duplicate addresses and valid gateway/DNS. Fresh uncached DNS, TLS and SaaS login succeed over CPE. Record IPv4-only degraded scope and client behaviour with stale IPv6 configuration; VLAN 200/400/500/900 are shut. Time from injected failure to CRM restoration, including detection; revert CPE to normal, restore router and repeat AT-01 |

---

## Fault tests — what is deliberately broken, and what should happen

An acceptance test says what must be observed before the site is accepted. A
fault test says what must be observed when something is deliberately broken,
which is the half most designs never write down. Neither is evidence until it
has been run, and none of these has been run.

| ID | Fault injected | Serves | Expected observable | Limit |
|---|---|---|---|---|
| FT-01 | Shut the primary WAN at the carrier demarcation | R-01 | IP SLA fails, floating static installs, AT-01 passes again | ≤ 120 s |
| FT-02 | Fail primary WAN during active call at expected survivor load; restore/flap primary three times, and separately test backup loss | R-02 | Capture at branch and hub: both outer routes/SA pairs, phone inner identities, selected inner routes and hub replies. Voice survives without forced re-registration, gap and MOS meet AT-05. Derive milliseconds from capture timestamps/RTP clock rate with sequence continuity; sequence numbers alone are not elapsed time. Keep surviving tunnel outer traffic on its own WAN | call maintained; agreed gap/MOS limits |
| FT-03 | Restore the primary and flap it three times in five minutes | R-01 | The 300-second up delay holds the service on the backup; the primary is reinstated once, after it has been stable for that period | one transition |
| FT-04 | Power off each access switch separately | R-01 | Surviving-switch clients regain gateway/service within 300 s. Start affected-client timing at failure; named onsite responder repatches every required singly attached wired client to reserved correctly configured ports within the same 300 s, and each completes AT-01. Record PoE load and unavailable wireless areas/controllers. Passing one already-surviving client does not pass R-01 | ≤ 300 s for all required wired clients; failed repatching gate blocks acceptance |
| FT-05 | Remove the guest VRF's default route | R-03 | Guest loses internet; **no** internal subnet becomes reachable. A control that fails must fail closed |
| FT-06 | From a user VLAN, attempt VLAN 400 over v4 and v6 with the FM host offline; then patch a spare controller into a VLAN 400 port that has **no** ingress filter and repeat AT-04 | R-04 | The first case is denied in both families, counters increment, alert raised. The second case **succeeds**, which is the point: it demonstrates that D-05's control is per-port configuration and that a port without it is a hole. Record it, then fix the port | — |
| FT-07 | Black-hole the probe's return path without taking the service down | R-05 | The probe alerts, and the alert says it is about reachability *from this site*, not about the service. An alert that cannot distinguish these is worse than none |
| FT-08 | Corrupt one generated file in the source of truth, then rebuild `hgt-sw-02` | R-06 | The rebuild fails loudly at validation rather than producing a working-looking switch with the wrong policy | fails before deployment |
| FT-09 | Power off `hgt-rtr-01` — in a maintenance window, or on the bench pair used for AT-09 | R-01a | Service degrades to the CPE path per RP-03. Record what actually works: internet and the CRM through CPE NAT; **no file service, no voice, no inter-VLAN policy, no guest**. This is the agreed exception being exercised, not a failure of the design | degraded service ≤ 60 min (separately: full restoration by end of the next business day after the spare arrives) |
| FT-10 | Pull router–sw-01 LAN link, leaving switches up; separately blackhole primary WAN beyond the demarcation with carrier up | R-01 | LAN: sw-02 direct router-facing alternate becomes root/forwarding; sw-01 reaches router through sw-02; capture every instance’s roles and service. WAN: both probes remain on primary and cannot succeed through backup; primary stays withdrawn until tested recovery and hold-up delay | LAN forwarding ≤ 30 s and AT-01 ≤ 300 s; WAN AT-01 ≤ 120 s |

**Declared exemption.** R-07 has no fault test. It is a commercial constraint,
not a behaviour, and there is nothing to break: AT-08 checks it and the residual
risk section says what happens when it binds. Every other requirement has one,
and `check_traceability.py` does not accept a silent omission.

---

## Recovery procedures

| ID | For | Serves | Procedure | Tested by |
|---|---|---|---|---|
| RP-01 | Primary WAN failure | R-01, R-02 | Automatic. Confirm the backup carried the service and that the inner route moved to the second tunnel. Raise the carrier ticket. Failback is held by D-02's 300-second up delay; if the primary is flapping, disable the tracked static manually and fail back by hand only after the carrier confirms a fix | FT-01, FT-03 |
| RP-02 | Switch failure | R-01, R-06 | Named onsite responder repatches affected required wired endpoints within the pre-tested five-minute budget to reserved VLAN/PoE/controller-filter ports; remote engineer verifies each client service. If staff/capacity/timing gate cannot be met, escalate and obtain an explicit revised requirement rather than claiming compliance. Replace from onsite spare and execute AT-07, AT-04 and AT-01 | FT-04, AT-07 |
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
2. **Isolate, then reconfigure the port.** Disconnect both router LAN leads and
   its CPE/WAN1 attachment before activating any replacement gateway; a restart
   must not introduce duplicate gateway/DHCP ownership. On `hgt-sw-01`, change `Gi1/0/1` from an 802.1Q
   trunk to an **untagged access port in VLAN 100**. `hgt-cpe-01`'s LAN port is
   an ordinary untagged Ethernet port and does not terminate 802.1Q; if a
   future CPE does, record that instead and leave the port tagged for VLAN 100
   only. Before acceptance, D-08 must generate and AT-09 must qualify both
   named port profiles. They are required deliverables, not configurations
   supplied by this teaching document; the incident must select a tested profile.
3. **Re-patch.** Move `Gi1/0/1` to the CPE's LAN port.
4. **Activate the qualified degraded profile.** First confirm both router LAN
   leads and its CPE/WAN1 attachment are disconnected, preventing duplicate
   gateway/DHCP ownership if it restarts. Through the qualified independent CPE
   management path, replace the normal transit profile with the stored VLAN 100
   profile. Enable gateway 10.10.64.1/24, approved DNS and collision-safe DHCP
   reservations/lease-state procedure. Confirm existing leases, expired leases
   and new clients; matching pool bounds alone are insufficient. Verify the
   IPv4-only degraded client behaviour accepted in AT-09.
5. **Shut what is no longer policed.** Shut VLANs 200, 400, 500 and 900 at both
   switches. Without the router there is no inter-VLAN policy and no guest VRF,
   and an unpoliced guest VLAN behind a NAT is worse than no guest VLAN. The
   controllers are off the network for the duration; R-04 is about who may reach
   them, and nobody reaching them satisfies it.
6. **Verify, and record the time.** From a VLAN 100 host: HTTPS to the CRM
   succeeds. SMB to `fs-hub-01` **fails, and is expected to fail** — it is
   reached over the router's IPsec, and a CPE supplies NAT, not a VPN and not
   an authenticated path to a private service. Voice is down. Record the elapsed
   time from the injected or first observed service failure, including detection: **this is the measurement R-01a's
   60 minutes is about.**
7. **Order the replacement.** The support contract ships a cold spare next
   business day. Shipping is not restoration.
8. **Restore.** When the spare arrives: rebuild from the source of truth, run
   the router portion of AT-07. Disable degraded gateway/DHCP and revert the CPE
   to its normal transit profile before restoring either router LAN connection;
   revert `Gi1/0/1` to its trunk profile; reconnect both router LAN leads and
   WAN1 to the CPE transit, checking expected spanning-tree roles and WAN routes;
   un-shut the four VLANs, then run AT-01, AT-04 and AT-05. **This** is what
   R-01a's second deadline measures: complete by the end of the next business
   day after the spare arrives.

**Two deadlines, measured separately, because they are different
commitments.** Degraded service — steps 1 to 6 — within 60 minutes of the
router failure, including detection and declaration delays; if occurrence is
unknown, report that uncertainty and both first-observation/declaration times. Full restoration — step 8, with AT-01, AT-04 and AT-05
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
allocated over 60 months for this planning comparison. These are assumptions, not quotations, and
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
| **Allocated capital** | | | **£112.00 / month** |

| Monthly equivalent line (cash or allocated capital as labelled) | Monthly | Serves |
|---|---|---|
| Leased line, 200 Mbps, 4-hour fix | £395 | R-01, D-01 |
| Broadband 500/75 with CPE, next business day | £64 | R-01a, R-02, D-01 |
| Allocated capital | £112 | R-01, R-01a |
| Support contract, next business day | £71 | RP-02, RP-03 |
| Out-of-band 4G data | £18 | RP-05 |
| Monitoring, per-site licence | £32 | R-05, D-07 |
| **Total** | **£692** | R-07 (limit £780) |

R-07 now defines a monthly-equivalent planning cap rather than calling the
capital allocation a supplier recurring charge. In a real project, finance must
approve that definition before it is used to reject or accept an alternative.
These requirement signatures/dates are fictional case details, not observed
authorisations from this review.

Recurring cash is £580/month; the £112 capital allocation makes the defined
monthly equivalent £692. This is a planning convention, not an assertion about
financial accounting or supplier instalments. £88/month of equivalent headroom. If R-01a were withdrawn and R-01's five minutes applied
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

Traceability makes the design reviewable; it does not make it accepted or
ready to build. Whether each decision achieves its requirement is a separate
question, and the only way to answer it is to have somebody who knows the
mechanism read the design and try to break it on paper. Two readers did that to
this one and both found real defects. Budget for that step.
