# Aldergate Harrogate branch — one design, carried all the way through

Appendix C gives three reference networks at design-study depth: requirements,
functional bills of materials, acceptance considerations. This document does
something narrower and more useful. It takes **one modest site** and carries it
from requirement to configuration to acceptance test to fault test to recovery
procedure to owner to cost, with **one identifier set** the whole way, so you
can trace any line back to the requirement that caused it and forward to the
test that proves it.

It is a worked design, not a deployment. Nothing here has been applied to a
device. What it is for is the standard: when Chapter 79 asks you to produce a
design, this is the level of completeness that counts as finished.

`check_traceability.py` in this directory parses the tables below and fails if
any requirement lacks a decision, an acceptance test, a fault test or a recovery
procedure. Run it before you believe the word "traceable".

---

## The site

Aldergate's Harrogate branch. 38 staff, one floor, a leased line and a
broadband backup. It is deliberately small: a site anybody can hold in their
head, where the only reason to leave something out is that it genuinely is not
needed.

| | |
|---|---|
| Site code | `HGT` |
| IPv4 allocation | `10.10.24.0/22` (from Aldergate's `10.10.0.0/16`) |
| IPv6 allocation | `2001:db8:a1de:18::/56` |
| AS | 64510 (Aldergate), branches do not run BGP |
| Devices | 1 × router `hgt-rtr-01`, 2 × switch `hgt-sw-01/02`, 3 × AP `hgt-ap-01..03` |

### Addressing, allocated once and referenced everywhere

| VLAN | Purpose | IPv4 | IPv6 | DHCP |
|---|---|---|---|---|
| 100 | User | `10.10.24.0/24` | `2001:db8:a1de:1800::/64` | v4 pool `.50–.230`; v6 SLAAC + stateless DHCPv6 |
| 200 | Voice | `10.10.25.0/25` | `2001:db8:a1de:1801::/64` | v4 pool `.20–.110`, option 66 |
| 400 | IoT / building | `10.10.25.128/26` | `2001:db8:a1de:1802::/64` | v4 pool `.140–.180` |
| 500 | Guest | `10.10.26.0/24` | `2001:db8:a1de:1803::/64` | v4 pool `.50–.230` |
| 900 | Infrastructure | `10.10.27.0/28` | `2001:db8:a1de:18ff::/64` | static |
| — | Loopback | `10.10.27.32/32` (`hgt-rtr-01`) | `2001:db8:a1de:18ff::1/128` | static |
| — | WAN primary | `/31` from the carrier | carrier-assigned | static |
| — | WAN backup | DHCP from the broadband service | — | — |

`10.10.26.128/25` and `2001:db8:a1de:1804::/64` are left unallocated on purpose.
A site with no spare subnet is a site whose next requirement is a renumbering.

---

## Requirements

Each has a source and a date, because a requirement nobody can trace to a person
is a preference.

| ID | Requirement | Source | Date |
|---|---|---|---|
| R-01 | Staff reach the CRM and file services during working hours; a single device or link failure must not prevent this for more than 5 minutes | Branch manager, signed | 2026-02-11 |
| R-02 | Voice calls survive a primary WAN failure with degraded quality, not a dropped call | Telephony owner | 2026-02-11 |
| R-03 | Guest traffic never reaches an internal subnet | Security policy SEC-004 | 2026-01-08 |
| R-04 | Building systems (HVAC, door controllers) are reachable only from the facilities management host | Security policy SEC-004 | 2026-01-08 |
| R-05 | A failure is detectable from the NOC without a user reporting it | Operations lead | 2026-02-18 |
| R-06 | The site can be rebuilt from the source of truth by one engineer in one day | Operations lead | 2026-02-18 |
| R-07 | Recurring cost stays under £780/month | Finance, budget line BR-2026-HGT | 2026-02-04 |

---

## Decisions, and what each one costs

| ID | Decision | Serves | Rejected alternative, and what it would have cost |
|---|---|---|---|
| D-01 | Two WAN services: a 200 Mbps leased line and a 500/75 Mbps broadband, on separate physical paths from separate providers | R-01, R-02 | A second leased line: +£410/month, breaks R-07, and buys availability the site does not need |
| D-02 | Static default via primary with an IP SLA tracked floating static via backup; no dynamic routing to the branch | R-01, R-06 | Branch BGP: no benefit at one exit pair, and a protocol every NOC engineer must then know to debug a 38-person site |
| D-03 | Two access switches, each AP dual-homed by a single uplink to a different switch | R-01 | Stacked pair: simpler logically, but a stack is one failure domain and a single software upgrade takes both |
| D-04 | Guest VLAN 500 terminates in a separate VRF with a route only to the internet next hop | R-03 | ACLs on a shared routing table: enforceable but one edit away from wrong, and the failure is silent |
| D-05 | Building systems in VLAN 400, reachable only from `10.10.4.15` (FM host), enforced at the router and not on the devices | R-04 | Device-side hardening: these controllers cannot be hardened and will not be replaced this decade |
| D-06 | Active monitoring: synthetic HTTPS probe to the CRM from the site every 60 s, plus interface and IP SLA state | R-05 | Interface-up alarms only: the 14 March incident showed a session staying up while the service was gone |
| D-07 | All configuration generated from the source of truth; nothing hand-edited on the device | R-06 | Hand-built with a documented runbook: the runbook and the device diverge, and you find out during the rebuild |

---

## Acceptance tests — what is run before the site is accepted

| ID | Test | Serves | Pass condition |
|---|---|---|---|
| AT-01 | From a VLAN 100 host, HTTPS to the CRM and SMB to the file service | R-01 | Both succeed; TLS certificate chain validates |
| AT-02 | From a VLAN 500 guest host, attempt each internal subnet in turn | R-03 | Every attempt fails; counters on the VRF boundary increment; no path exists in the guest VRF's table |
| AT-03 | From a host that is not `10.10.4.15`, reach a VLAN 400 controller | R-04 | Fails; the router's ACL counter increments. Then repeat from `10.10.4.15`: succeeds |
| AT-04 | Voice call in progress; observe MOS and jitter for 5 minutes | R-02 | Baseline recorded, for comparison in FT-02 |
| AT-05 | Disable the synthetic probe target; confirm the NOC receives the alert | R-05 | Alert raised within 180 s, routed to the on-call queue, and acknowledged by a human |
| AT-06 | Rebuild `hgt-sw-02` from the source of truth onto a factory-reset unit | R-06 | Resulting configuration is byte-identical to the generated file; AT-01 passes afterwards |
| AT-07 | Sum the monthly recurring charges from the signed orders | R-07 | Total ≤ £780 |

---

## Fault tests — what is deliberately broken, and what should happen

An acceptance test proves the design works. A fault test proves it fails the way
you said it would, which is the half most designs never check.

| ID | Fault injected | Serves | Expected observable | Time limit |
|---|---|---|---|---|
| FT-01 | Shut the primary WAN interface at the carrier demarcation | R-01 | IP SLA fails, floating static installs, AT-01 passes again | ≤ 120 s |
| FT-02 | Repeat FT-01 with a call in progress | R-02 | Call survives; MOS drops from the AT-04 baseline but no call is dropped | call not dropped |
| FT-03 | Power off `hgt-sw-01` | R-01 | APs on `hgt-sw-02` stay up; users on `hgt-sw-01` ports move to `hgt-sw-02` ports; AT-01 passes from a VLAN 100 host | ≤ 300 s |
| FT-04 | Remove the VRF route-leak entry for guest internet | R-03 | Guest loses internet; **no** internal subnet becomes reachable. A failure must not open the boundary |
| FT-05 | Disconnect the FM host and attempt VLAN 400 access from a user VLAN | R-04 | Denied, counter increments, alert raised |
| FT-06 | Black-hole the synthetic probe's return path without taking the service down | R-05 | The probe alerts, and the record notes the alert is about reachability from this site, not about the service. An alert that cannot distinguish these is worse than none |
| FT-07 | Corrupt one generated file in the source of truth, then rebuild `hgt-sw-02` from it | R-06 | The rebuild fails loudly at validation rather than producing a working-looking switch with the wrong policy | fails before deployment |

**Declared exemption.** R-07 has no fault test. It is a commercial constraint,
not a behaviour, and there is nothing to break: AT-07 checks it and the residual
risk section says what happens when it binds. Every other requirement has one,
and `check_traceability.py` will not accept a silent omission.

FT-04 and FT-06 exist because of the two failure shapes this book keeps
returning to: a control that fails **open**, and an instrument that reports
confidently about something it cannot see.

---

## Recovery procedures

| ID | For | Serves | Procedure | Tested by |
|---|---|---|---|---|
| RP-01 | Primary WAN failure | R-01, R-02 | Automatic. Confirm the backup carried the service, raise the carrier ticket, and do **not** fail back until the carrier confirms a fix — a flapping primary is worse than a stable backup | FT-01 |
| RP-02 | Switch failure | R-01, R-06 | Replace the unit, rebuild from the source of truth (D-07), run AT-06 then AT-01. Spare held on site | FT-03, AT-06 |
| RP-03 | Router failure | R-01 | Cold spare shipped next business day; site runs on the backup broadband and a temporary firewall rule set held in the source of truth as `hgt-rtr-01-degraded`. **This is the design's weakest point and it is deliberate** — see residual risk | not tested; see below |
| RP-04 | Guest boundary breach suspected | R-03, R-04 | Shut VLAN 500 at the switch, preserve the VRF tables and counters before any change, then investigate. The evidence is gone once you reconfigure | FT-04 |
| RP-05 | Site unreachable, cause unknown | R-05 | Out-of-band: 4G dongle on the router console server. Confirm it is reachable monthly, because an untested out-of-band path is a story people tell themselves | monthly check |
| RP-06 | Cost overrun on renewal | R-07 | Re-price against the residual-risk note before renewing; if the leased line rises, D-01 is the decision to revisit, not the support contract | annual review |

---

## Ownership

| Element | Owner | Escalation |
|---|---|---|
| Router, switches, WAN | Network team, `net-ops@` | On-call rota |
| APs and wireless | Network team | On-call rota |
| VLAN 400 controllers | Facilities, with network providing the path only | Facilities duty manager |
| Guest portal terms | Legal and marketing | — |
| Source of truth for this site | Network team, repo `aldergate-sot`, path `sites/hgt/` | — |

Nothing in this table is shared. A jointly owned element is an unowned element.

---

## Cost

| Line | Monthly | Serves |
|---|---|---|
| Leased line, 200 Mbps, 4-hour fix | £395 | R-01, D-01 |
| Broadband 500/75, next business day | £64 | R-01, R-02, D-01 |
| Hardware amortised over 5 years (router £2,400, 2 × switch £1,900, 3 × AP £1,050) | £89 | R-01 |
| Support contract, next business day | £71 | RP-02, RP-03 |
| Out-of-band 4G data | £18 | RP-05 |
| Monitoring (per-site licence) | £32 | R-05, D-06 |
| **Total** | **£669** | R-07 (limit £780) |

£111/month of headroom. If R-01 tightened to require a 4-hour router
replacement, RP-03 changes to a hot spare and the headroom is gone — which is
the conversation to have with the branch manager, not a change to make quietly.

---

## Residual risk, stated rather than buried

1. **The router is a single point of failure.** RP-03 is a next-business-day
   procedure against R-01's 5-minute target, and it does not meet it. This is
   accepted deliberately: a resilient pair costs roughly £120/month more and
   R-07 does not allow it. The risk is recorded in the branch's own register and
   reviewed annually. **It should be reviewed the moment R-01 changes or the
   site grows past about 60 staff.**
2. **FT-02's quality threshold is a judgement.** "Degraded but not dropped" is
   not a number. Agree a MOS floor with the telephony owner before acceptance,
   or the test cannot fail.
3. **The 5-minute target in R-01 has never been measured against FT-03.** The
   300-second limit in FT-03 is the design intent, not an observation.

---

## Tracing one line, forwards and backwards

Pick the guest VRF. It exists because of **D-04**, which exists because of
**R-03**, which came from security policy SEC-004 on 8 January and has a named
owner. It is proved by **AT-02**, which must fail every internal destination.
It is proved to fail safely by **FT-04**, which removes the route leak and
requires that no internal subnet becomes reachable. When it goes wrong,
**RP-04** says to preserve the counters before reconfiguring. It costs nothing
on its own line, because it is a configuration choice rather than a purchase.

That chain is what "worked" should mean. If you can do the same for every line
of your own design, it is finished. If you cannot, the gap is where the next
incident will start.
