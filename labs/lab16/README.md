# Lab 16 — design and defend Manchester

This is a design exercise, not a claim of an installed or tested campus.
Numerical inputs below are constructed assumptions. Use them for the exercise;
replace them with measured demand, a site survey and an approved service brief
before preparing a real implementation. Record unknowns rather than inventing
platform support or the independence of physical routes.

## Requirements and supplied inputs

- 250 users over two floors; six access switches, three per floor. Each has
  44 × 1 Gb/s endpoint positions and 4 × 2.5 Gb/s AP positions. Phones with
  PC pass-through share an endpoint position; include separate voice/data
  admission policy. The 24 AP positions are a planning allowance, not an RF result.
- Each access switch has two 10 Gb/s uplinks, one to each aggregation/core
  chassis. Assess both supported multichassis LAG and an independent-uplink
  STP design; count only forwarding capacity for the selected mode.
- In the busiest direction, each access switch has 20% simultaneous wired
  activity at 0.1 Gb/s per active port, plus 0.4 Gb/s per AP. Apply 25% demand
  growth. Keep per-flow and burst effects distinct from the aggregate model.
- Ten local servers have 1 Gb/s ports, with assumed growth-adjusted peak
  traffic of 5 Gb/s towards the campus. One server-edge switch has two 25 Gb/s
  uplinks, one to each core. Its loss has a four-hour restoration objective;
  critical services must also be recoverable in London. Document and verify
  application recovery; a network route alone does not provide it.
- London service circuit: 1 Gb/s. Internet service: 2 Gb/s. Nominal rates are
  per direction; design to at most 80% sustained utilisation. Current worst-
  direction London traffic is 0.4 Gb/s; Internet traffic is 0.6 Gb/s. Apply
  25% growth. Critical Internet traffic after growth is 0.3 Gb/s, included
  within the Internet total. Assume supported IPsec failover via the Internet
  to London and Internet egress via London, subject to measured encrypted/
  inspected performance, MTU, policy and provider-path verification.
- Loss of one access uplink or one core must preserve essential service for
  endpoints on other healthy equipment. A single-homed endpoint's own access
  switch remains a failure point. Data/voice interruption targets are five
  seconds for these core/link events and 30 seconds for WAN failover. These
  are acceptance targets, not predicted measurements or protocol guarantees.
- Each access switch is assumed to have 740 W available PSE output normally,
  but only 370 W after a PSU fault. Forty phones reserve 8 W each and four
  APs reserve 40 W each, all measured at the PSE boundary. Retain 10% of the
  available budget as reserve. Requirements ask for all 40 phones and at
  least two APs to remain powered after the fault. Identify and resolve the
  conflict before choosing hardware.
- No campus fabric, stretched server VLAN or wired-IP mobility requirement
  has been identified. WLAN sessions should survive movement between the
  two floors. Specify how the chosen wireless mode supplies that service;
  routed access alone does not preserve a client subnet between access blocks.
- No on-site network engineer. Staff can follow labelled replacement steps;
  a suitable spare and independent remote console path must be available.
  Physical route, coverage, power and credential dependencies require evidence.

## Addressing boundary and one bridged-access answer

The site's existing reservation is **10.10.32.0/20** and the documentation
IPv6 block **2001:db8:a1de:100::/56**, consistent with Lab 6. The latter is an
example, not globally routable production addressing. The following is one
non-overlapping segment allocation for a bridged-access design; it does not
stretch these VLANs to London. IPv6 suffixes are assigned labels, not a
calculation from the decimal VLAN IDs.

| VLAN | Role | IPv4 | IPv6 /64 |
|---|---|---|---|
| 110 | Staff wired | 10.10.32.0/23 | 2001:db8:a1de:110::/64 |
| 120 | Staff WLAN | 10.10.34.0/23 | 2001:db8:a1de:120::/64 |
| 210 | Voice | 10.10.36.0/23 | 2001:db8:a1de:130::/64 |
| 410 | Building equipment | 10.10.38.0/24 | 2001:db8:a1de:140::/64 |
| 305 | Local servers | 10.10.39.0/24 | 2001:db8:a1de:150::/64 |
| 510 | Guest | 10.10.40.0/23 | 2001:db8:a1de:160::/64 |
| 990 | Management | 10.10.42.0/24 | 2001:db8:a1de:170::/64 |

Reserve 10.10.43.0/24 for separately designed transit/management attachments,
and 10.10.44.0/22 for growth. For this answer's IPv4 gateway convention, the
first usable address is virtual and the next two are distinct peer addresses.
IPv6 RA/first-hop redundancy requires its own design and execution; copying
IPv4 addresses does not establish it. Keep management access through explicit
authorised paths. Do not advertise an aggregate into a black hole during a
partial failure; establish the routing/summary behaviour for the chosen model.

For routed access, allocate non-overlapping per-access-block subnets inside
the reservation instead. State the capacity per subnet, route counts, DHCP
relays, summarisation and the WLAN anchoring/mobility arrangement. Do not
repeat the same routed client subnet on unrelated access switches.

## Calculated answer guidance

1. **Access ports:** 264 endpoint positions give 14 beyond the 250-user count;
   non-user endpoints or dedicated phones can consume that allowance. The
   access line-rate sum is 44 + 4×2.5 = **54 Gb/s per switch**. A two-active-
   member LAG gives **2.7:1** normally and **5.4:1** after a member/core loss.
   A design with one STP-blocked uplink is already **5.4:1** in normal service.
2. **Demand:** (44×0.2×0.1 + 4×0.4)×1.25 = **3.10 Gb/s per switch**;
   six give **18.6 Gb/s**. A surviving 10 Gb/s link has 31% modelled load.
   Demand distribution and bursts still require validation. The 5 Gb/s local
   server requirement fits the 25 Gb/s surviving attachment and the stated
   10 Gb/s aggregate server-port rate, but no single 1 Gb/s server port can
   deliver 5 Gb/s. Include the application/traffic distribution explicitly.
3. **WAN:** Growth gives **0.50 Gb/s London** and **0.75 Gb/s Internet**.
   With London unavailable, their 1.25 Gb/s sum is below the 1.6 Gb/s target
   on the 2 Gb/s Internet circuit. With Internet unavailable, 1.25 Gb/s
   cannot fit the 0.8 Gb/s target on the London circuit. London plus critical
   Internet demand is 0.50 + 0.30 = **0.80 Gb/s**; prioritisation can preserve
   that constructed essential load but leaves no additional sustained margin.
   Either accept documented noncritical degradation or increase surviving
   capacity. Validate encryption, firewall performance and shared physical paths.
4. **PoE:** Normal allocation is 40×8 + 4×40 = **480 W**, below 666 W usable
   after a 10% reserve. After the PSU fault, usable allocation is **333 W**.
   All phones need 320 W, leaving only 13 W; the required two APs cannot be
   supported. Phones plus two APs require 400 W: a 10% reserve requires at
   least **400/0.9 = 444.45 W** of surviving PSE budget (round hardware capacity
   upwards). Select adequate surviving power, redistribute loads or explicitly
   renegotiate the service requirement. Merely adding a second PSU is not proof.
5. **Architecture:** A collapsed pair is a defensible starting choice for
   this brief if port/feature/maintenance needs fit. A separate core can be
   justified by additional requirements, not ruled out by user count alone.
   Routed access is credible if WLAN mobility and subnet boundaries are
   supplied explicitly. Bridged access with supported multichassis or STP
   behaviour is also defensible; document its shared Layer 2 and peer risks.
   A fabric requires a specific additional benefit that covers its costs.

## Submission and acceptance package

Produce a decision record with requirements, alternatives, assumptions,
arithmetic, residual risks and the conditions that would trigger redesign.
Attach a physical and logical diagram and schedules for every device/release,
port, fibre path, optic, circuit, address, VLAN/VRF, gateway and service.
Provide complete supported configurations, reviewed policy/flow matrices,
management access, backups, monitoring, capacity alarms and rollback.

For wired and wireless roles, record server decisions, effective access state
and positive/negative traffic evidence. Include guest isolation, camera/building
flows, phone/PC host mode and IPv4/IPv6. For resilience, cover each uplink,
core, peer/keepalive partition sequence, PSU, WAN circuit, RADIUS and recovery.
Measure interruption at an established application session and new-session
establishment separately, then verify restored state and capacity.

List acceptance targets and actual observations side by side. Keep source
review, arithmetic, Linux experiments, Containerlab and target execution
distinct. No vendor release, procurement choice, full campus deployment or
failure-duration target has been verified by completing this paper exercise.
