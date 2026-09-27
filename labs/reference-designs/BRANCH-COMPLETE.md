# Aldergate Harrogate branch — one design, carried all the way through

Appendix C gives three reference networks at design-study depth. This document
does something narrower. It takes **one modest site** and carries it from
requirement to decision to acceptance test to fault test to recovery procedure
to owner to cost, with **one identifier set** the whole way, so any line traces
back to the requirement that caused it and forward to the test that proves it.

**What this is and is not.** It is a worked design at high-level-design depth,
plus the port map and platform assumptions you need to build it. Nothing here
has been applied to a device, and it does not ship device configuration: the
"generated from the source of truth" decision below describes the intended
practice, not a repository you can clone. When Chapter 79 asks you to produce a
design, this is the level of *connectedness* that counts as finished — every
requirement traced, every rejection costed, every failure tested, every gap
named. It is not a promise that every line is buildable without judgement.

Two checkers sit beside it and both are worth running before you trust a word:

- `check_addressing.py` validates `branch-hgt.json` — canonical, contained,
  disjoint, DHCP inside its own subnet — and checks the table below still
  agrees with it. The first draft of this document failed all three properties.
- `check_traceability.py` checks that every requirement has a decision, an
  acceptance test, a fault test and a recovery procedure, and that none of those
  exists without a requirement. It checks *coverage*, not correctness: it will
  happily pass a design whose decisions do not achieve their requirements. Read
  the design as well.

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

### Devices

| Device | Role | Platform assumption |
|---|---|---|
| `hgt-rtr-01` | Branch router: WAN termination, inter-VLAN routing, policy, NAT, VPN | Any router with policy-based ACLs, VRFs, IP SLA-style tracking and IPsec |
| `hgt-sw-01`, `hgt-sw-02` | Access switches, PoE | Layer 2 with 802.1X, protected/isolated ports and PoE budget for 2 APs |
| `hgt-ap-01..03` | Wireless | Controller-less or cloud-managed; one uplink each |
| `hgt-cpe-01` | Carrier broadband CPE, routing and NAT capable | Supplied by the broadband carrier; see RP-03 |
| `hgt-con-01` | Console server with 4G | Out-of-band access; see RP-05 |

`hgt-cpe-01` is in this table because RP-03 depends on it. A recovery procedure
that needs a device the inventory does not list is a procedure that will fail on
the day.

### Port map

| From | Port | To | Notes |
|---|---|---|---|
| `hgt-rtr-01` | `wan0` | Carrier leased-line NTU | Primary |
| `hgt-rtr-01` | `wan1` | `hgt-cpe-01` LAN port | Backup path; CPE does NAT |
| `hgt-rtr-01` | `lan0` | `hgt-sw-01` `Gi1/0/1` | 802.1Q trunk, VLANs 100/200/400/500/900 |
| `hgt-rtr-01` | `lan1` | `hgt-sw-02` `Gi1/0/1` | Second trunk |
| `hgt-sw-01` | `Gi1/0/2` | `hgt-sw-02` `Gi1/0/2` | Inter-switch trunk |
| `hgt-sw-01` | `Gi1/0/10` | `hgt-ap-01` | PoE |
| `hgt-sw-01` | `Gi1/0/11` | `hgt-ap-02` | PoE |
| `hgt-sw-02` | `Gi1/0/10` | `hgt-ap-03` | PoE |
| `hgt-sw-02` | `Gi1/0/20` | `hgt-con-01` | Out-of-band |

### Addressing

Generated from `branch-hgt.json`. Do not edit this table by hand; edit the JSON
and re-run `check_addressing.py`, which fails if the two disagree.

| VLAN | Purpose | IPv4 | IPv6 | DHCPv4 |
|---|---|---|---|---|
| 100 | User | `10.10.64.0/24` | `2001:db8:a1de:300::/64` | `.50`–`.230` |
| 200 | Voice | `10.10.65.0/25` | `2001:db8:a1de:301::/64` | `.20`–`.110` |
| 400 | Building systems | `10.10.65.128/26` | `2001:db8:a1de:302::/64` | `.140`–`.180` |
| 500 | Guest | `10.10.66.0/24` | `2001:db8:a1de:303::/64` | `.50`–`.230` |
| 900 | Infrastructure | `10.10.67.0/28` | `2001:db8:a1de:3ff::/64` | static |

Loopbacks come from their own blocks, `10.10.67.32/27` and
`2001:db8:a1de:3fe::/64`, not from the infrastructure LAN. `hgt-rtr-01` is
`10.10.67.32/32` and `2001:db8:a1de:3fe::1/128`. A loopback inside a host LAN's
/64 works on some platforms and surprises you on others; a distinct pool costs
nothing and removes the question.

Genuinely spare: `10.10.65.192/26`, `10.10.67.64/26`, `10.10.67.128/25`,
`2001:db8:a1de:304::/64` and `:305::/64`. The checker proves they are spare.

---

## Requirements

Each has a source and a date, because a requirement nobody can trace to a person
is a preference.

| ID | Requirement | Source | Date |
|---|---|---|---|
| R-01 | Staff reach the CRM and file services during working hours; a single **link** failure must not prevent this for more than 5 minutes | Branch manager, signed | 2026-02-11 |
| R-01a | A **router** failure may take up to one business day to restore, with the site running degraded on the backup path meanwhile. Exception to R-01, agreed and recorded | Branch manager, signed exception BR-EX-04; network team proposed | 2026-02-19 |
| R-02 | A call in progress survives a primary WAN failure with degraded quality rather than being dropped | Telephony owner | 2026-02-11 |
| R-03 | Guest traffic never reaches an internal subnet | Security policy SEC-004 | 2026-01-08 |
| R-04 | Building controllers are reachable only from the facilities-management host, and cannot reach each other | Security policy SEC-004, clarified 2026-02-20 | 2026-01-08 |
| R-05 | A failure is detectable from the NOC without a user reporting it | Operations lead | 2026-02-18 |
| R-06 | The site can be rebuilt from the source of truth by one engineer in one day | Operations lead | 2026-02-18 |
| R-07 | Recurring cost stays under £780/month | Finance, budget line BR-2026-HGT | 2026-02-04 |

**On R-01a.** The first draft of this design left R-01 saying five minutes,
provided a next-business-day router replacement, and called the gap "accepted
risk". That is not how Chapter 79 says to handle an infeasible requirement: you
either meet it, or you obtain agreement to change it, and the changed
requirement is what the design is then judged against. R-01a is that agreement —
named, dated, and specific about what the site does in the meantime. The
alternative was priced before it was declined: a resilient router pair adds
about £120/month and breaks R-07.

---

## Decisions, and what each one costs

| ID | Decision | Serves | Rejected alternative, and what it would have cost |
|---|---|---|---|
| D-01 | Two WAN services on separate physical paths from separate providers: a 200 Mbps leased line and a 500/75 broadband behind `hgt-cpe-01` | R-01, R-01a, R-02 | A second leased line: +£410/month, breaks R-07, and buys availability this site does not need |
| D-02 | Static default via primary, with a tracked floating static via backup. Tracking uses an IP SLA probe to two off-site targets, with a 3-second down delay and a **300-second up delay** so a flapping primary cannot flap the service | R-01, R-02 | Branch BGP: no benefit at one exit pair, and a protocol every NOC engineer must then know to debug a 38-person site |
| D-03 | Two access switches. Each AP has a **single** uplink; the three APs are split two on `hgt-sw-01`, one on `hgt-sw-02` | R-01 | Dual-homing each AP: needs LACP-capable APs and doubles the PoE port count. A stacked switch pair was also rejected: a stack is one failure domain and one upgrade takes both |
| D-04 | Guest VLAN 500 terminates in its own VRF whose only route is a default to the internet next hop; no route leak in either direction, and the VRF has no interface in any internal subnet | R-03 | ACLs on a shared routing table: enforceable but one edit away from wrong, and the failure is silent |
| D-05 | Building systems in VLAN 400. Router ACL permits only `10.10.64.15` and `2001:db8:a1de:300::15` (the FM host) inbound; switch **protected ports** stop controllers reaching each other within the VLAN | R-04 | Device-side hardening: these controllers cannot be hardened and will not be replaced this decade |
| D-06 | Voice rides an IPsec tunnel from `hgt-rtr-01`'s loopback to the voice platform. The loopback is reachable over either WAN, so a path change re-routes the tunnel without re-establishing the SIP registration or changing the media's source address | R-02 | SIP direct to the carrier over each WAN: the public source address changes on failover, which drops the call — the failure R-02 exists to prevent |
| D-07 | Active monitoring: synthetic HTTPS probe to the CRM from the site every 60 s, plus interface, IP SLA and tunnel state | R-05 | Interface-up alarms only: a session can stay up while the service is gone |
| D-08 | All configuration generated from the source of truth; nothing hand-edited on the device | R-06 | Hand-built with a documented runbook: the runbook and the device diverge, and you find out during the rebuild |

---

## Acceptance tests — run before the site is accepted

| ID | Test | Serves | Pass condition |
|---|---|---|---|
| AT-01 | From a VLAN 100 host, HTTPS to the CRM and SMB to the file service | R-01, R-01a | Both succeed; TLS chain validates |
| AT-02 | From a VLAN 500 guest host, attempt each internal subnet in turn, v4 and v6 | R-03 | Every attempt fails. The guest VRF's table is inspected and shown to contain **only** the default route and its connected guest subnets — the default matches internal addresses, so isolation comes from the next hop being an internet router with no path back, plus an egress ACL on the guest interface dropping RFC 1918 and the enterprise's v6 /48. Both the VRF table and the ACL counters are recorded |
| AT-03 | From a host that is not the FM host, reach a VLAN 400 controller over v4 and over v6; then repeat from the FM host | R-04 | Both non-FM attempts fail with the router ACL counter incrementing; both FM attempts succeed |
| AT-04 | Controller-to-controller: from one VLAN 400 device, reach another in the same VLAN | R-04 | Fails at the switch. Protected-port configuration recorded on both switches |
| AT-05 | Voice call in progress; record MOS and jitter for 5 minutes, and the tunnel's SA lifetime | R-02 | Baseline recorded for comparison in FT-02; an agreed MOS floor is written down before acceptance |
| AT-06 | Disable the synthetic probe target; confirm the NOC receives the alert | R-05 | Alert raised within 180 s, routed to the on-call queue, acknowledged by a human |
| AT-07 | Rebuild `hgt-sw-02` from the source of truth onto a factory-reset unit | R-06 | Resulting configuration byte-identical to the generated file; AT-01 passes afterwards |
| AT-08 | Sum the monthly recurring charges from the signed orders | R-07 | Total ≤ £780 |

---

## Fault tests — what is deliberately broken, and what should happen

An acceptance test proves the design works. A fault test proves it fails the way
you said it would, which is the half most designs never check.

| ID | Fault injected | Serves | Expected observable | Limit |
|---|---|---|---|---|
| FT-01 | Shut the primary WAN at the carrier demarcation | R-01 | IP SLA fails, floating static installs, AT-01 passes again | ≤ 120 s |
| FT-02 | Repeat FT-01 with a call in progress | R-02 | Tunnel re-routes over `wan1`; the SIP registration does not re-establish and the media source address does not change; the call continues. MOS drops from the AT-05 baseline but stays above the agreed floor | call not dropped |
| FT-03 | Restore the primary and flap it three times in five minutes | R-01 | The 300-second up delay holds the service on the backup; the primary is reinstated once, after it has been stable for that period | one transition |
| FT-04 | Power off `hgt-sw-01` | R-01 | `hgt-ap-03` stays up; the two APs on `hgt-sw-01` are lost until their patch leads are moved; AT-01 passes from a host on `hgt-sw-02`. **Wireless coverage is reduced, not maintained** — record which areas lose signal | ≤ 300 s for wired |
| FT-05 | Remove the guest VRF's default route | R-03 | Guest loses internet; **no** internal subnet becomes reachable. A control that fails must fail closed |
| FT-06 | From a user VLAN, attempt VLAN 400 over v4 and v6 with the FM host offline | R-04 | Denied in both families, counters increment, alert raised |
| FT-07 | Black-hole the probe's return path without taking the service down | R-05 | The probe alerts, and the alert says it is about reachability *from this site*, not about the service. An alert that cannot distinguish these is worse than none |
| FT-08 | Corrupt one generated file in the source of truth, then rebuild `hgt-sw-02` | R-06 | The rebuild fails loudly at validation rather than producing a working-looking switch with the wrong policy | fails before deployment |
| FT-09 | Power off `hgt-rtr-01` | R-01a | Service degrades to the CPE path per RP-03. Record what actually works: internet and CRM via CPE NAT, no VPN, no inter-VLAN policy, voice down. This is the agreed exception being exercised, not a failure of the design | within one business day |

**Declared exemption.** R-07 has no fault test. It is a commercial constraint,
not a behaviour, and there is nothing to break: AT-08 checks it and the residual
risk section says what happens when it binds. Every other requirement has one,
and `check_traceability.py` does not accept a silent omission.

---

## Recovery procedures

| ID | For | Serves | Procedure | Tested by |
|---|---|---|---|---|
| RP-01 | Primary WAN failure | R-01, R-02 | Automatic. Confirm the backup carried the service and the tunnel re-routed. Raise the carrier ticket. Failback is held by D-02's 300-second up delay; if the primary is flapping, disable the tracked static manually and fail back by hand only after the carrier confirms a fix | FT-01, FT-03 |
| RP-02 | Switch failure | R-01, R-06 | Move the affected patch leads to spare ports on the surviving switch, then replace the unit from the on-site spare, rebuild from the source of truth, run AT-07 then AT-01 | FT-04, AT-07 |
| RP-03 | Router failure | R-01a | Re-patch `hgt-sw-01 Gi1/0/1` to `hgt-cpe-01`'s LAN port. The CPE routes and NATs VLAN 100 to the internet: staff reach the CRM and file services over the internet path, with **no VPN, no inter-VLAN policy, no voice and no guest separation** — so VLAN 500 stays shut until the router returns. Cold spare ships next business day; rebuild from the source of truth | FT-09 |
| RP-04 | Either enforced boundary breached: guest reaching an internal subnet, or a controller reachable from outside the FM host | R-03, R-04 | Shut the offending VLAN at both switches — 500 for the guest boundary, 400 for the controllers. Preserve the VRF table, the router ACL counters and the switch protected-port state *before* any change, then investigate. The evidence is gone once you reconfigure | FT-05, FT-06 |
| RP-05 | Site unreachable, cause unknown | R-05 | Out-of-band to `hgt-con-01` over 4G. Confirm it is reachable monthly, because an untested out-of-band path is a story people tell themselves | monthly check |
| RP-06 | Cost overrun on renewal | R-07 | Re-price against the residual-risk note before renewing; if the leased line rises, D-01 is the decision to revisit, not the support contract | annual review |

---

## Ownership

| Element | Owner | Escalation |
|---|---|---|
| Router, switches, WAN, CPE | Network team, `net-ops@` | On-call rota |
| APs and wireless | Network team | On-call rota |
| VLAN 400 controllers | Facilities; network provides the path and the policy only | Facilities duty manager |
| Guest portal terms | Legal and marketing | — |
| Source of truth for this site | Network team, repo `aldergate-sot`, path `sites/hgt/` | — |

Name one accountable owner for each element even where the work is shared. A
row with two names is a row where an escalation stalls while both check whether
it was theirs.

---

## Cost

Capital, with quantity, unit price and extended total stated separately,
amortised over 60 months:

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
   or voice becomes business-critical at this site — RP-03 has no voice.
2. **FT-02's quality threshold is a judgement.** "Degraded but not dropped" is
   not a number. Agree a MOS floor with the telephony owner before acceptance,
   or the test cannot fail.
3. **FT-04's 300-second limit is design intent, not an observation**, and it
   covers wired service only. Wireless coverage is genuinely reduced until
   somebody moves two patch leads.
4. **RP-03 has not been exercised end to end.** FT-09 is written; it has not
   been run, because running it means taking the site down for a day.

---

## Tracing one line, forwards and backwards

Pick the guest VRF. It exists because of **D-04**, which exists because of
**R-03**, which came from security policy SEC-004 on 8 January and has a named
owner. It is proved by **AT-02**, which inspects the VRF's table and the egress
ACL rather than asserting that no path exists. It is proved to fail safely by
**FT-05**, which removes the default route and requires that no internal subnet
becomes reachable. When it goes wrong, **RP-04** says to preserve the counters
before reconfiguring. It costs nothing on its own line, because it is a
configuration choice rather than a purchase.

That chain is what "worked" should mean. If you can do the same for every line
of your own design, it is finished. If you cannot, the gap is where the next
incident will start.
