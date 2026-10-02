# Prepare the network before testing the claim

The 120 tasks provide reviewed changes and evidence contracts. They do not
silently install a vendor image, cable a switch or replace an existing baseline.
Use an independent, owned lab for each task. `preparation.example.json` is the
record to complete before a device phase. Its null fields are deliberate gates;
an unknown image, interface or rollback command is not a successful preparation.

## Three-node IPv4 routed core (VPN-03 through VPN-05)

| Node | Loopback | A–B link | B–C link |
|---|---|---|---|
| A | 192.0.2.1/32 | 198.51.100.0/31 | — |
| B | 192.0.2.2/32 | 198.51.100.1/31 | 198.51.100.2/31 |
| C | 192.0.2.3/32 | — | 198.51.100.3/31 |

Build OSPF or IS-IS using the selected Part 3 panel and the actual interface map.
Advertise all three loopbacks and both links. Prove both directions of loopback
reachability, next hops, MTU and management recovery before adding labels. A
directly connected two-node shortcut does not demonstrate an intermediate label
action. Keep independent capture points on A–B and B–C. Separate background IGP,
ARP and management packets from the bounded task stimulus.

For VPN-03, configure link LDP only on these core links. Record discovery,
session, FEC binding and LFIB separately. Before fault injection, save the exact
image-supported LDP-only disable/removal and inverse, including configuration
context and commit mechanism. Use B–C alone; a platform with only global LDP
controls uses isolated end node C. Preserve carrier, IGP and the A–B session.
An IP echo can succeed through IP fallback after label withdrawal: require
actual label actions, rather than interpreting echo as proof of MPLS continuity.
If supported fault grammar is unavailable, leave that phase NOT_RUN.

For VPN-04, reserve a named A-to-C RSVP-TE LSP on the prepared core. Record both
link capacities, reservable bandwidth, requested reservation, actual path,
admission and outgoing labels. The bounded OAM commands in the panel test that
LSP. OAM alone does not establish application steering or measured throughput.
Record the OAM return path; qualify RSVP, TE and parser support on the actual
model/image. Do not substitute a generic IP ping for a named LSP test.

For VPN-05, bind the remote loopback's advertised prefix-SID to C, not a
convenient unrelated prefix. Record SRGB ranges and the actual installed label
action at each hop, including final-hop PHP/explicit-null behavior. Remove only
the owned SID advertisement for the negative phase, retain IP reachability and
restore the exact advertisement. A successful IP fallback does not pass the
SR-path test.

For VPN-06, use the packet-format qualification table in
`../workbook-automation/PACKET-AND-OBSERVATION-FIXTURES.md`. The supplied classic
End PCAP tests one precisely declared Linux behavior. It is not a universal
fixture for compressed SIDs or flavored endpoints. Replace documentation MACs
with the actual owned link addresses before an isolated replay.
Prepare a separate, explicit IPv6 link/loopback map and prove IPv6 reachability
to each actual SID and next segment. Record that map and the exact full-SID or
compressed-SID variant in the manifest; the IPv4 table above does not qualify
the SRv6 underlay.

## Routed EVPN service (DC-05)

Use a separate fixture from the L2-only DC-03/DC-04 service. A and C are VTEPs
192.0.2.1 and 192.0.2.3 in EVPN AS 64500. Tenant WB-IP uses L3VNI 10001,
effective import/export RT 64500:10001 and a unique RD per leaf. Record the
actual SVI/IRB/NVE/VXLAN/IP-VRF objects and backend requirements for the selected
platform. A route in BGP does not establish a working hardware forwarding path.

| Attachment | Leaf address | Host link address | Host service loopback |
|---|---|---|---|
| A service | 198.51.100.4/31 | 198.51.100.5/31 | 203.0.113.100/32 |
| C service | 198.51.100.6/31 | 198.51.100.7/31 | 203.0.113.200/32 |

Each real host owns its link address and service /32, and routes the remote
service through its local leaf. Each leaf has one owned static service /32 via
its local host, with recorded next hop, distance and owner. Attach an exact
export filter for that service prefix using Part 4 policy syntax. Reject other
prefixes. There must be no forwarding tenant default, aggregate or duplicate route that
covers a withdrawn remote service /32.
A recorded terminal unreachable default is permitted to prevent unintended
VRF fallback; it cannot provide service reachability or mask withdrawal.

For SR OS R-VPLS, also prepare the documented 198.18.0.1/.3 backhaul gateway
binding. Explicitly exclude backhaul subnet and gateway host routes from the
service export filter. Record RT2 gateway resolution as well as RT5 import.

Run a real receiver on the remote service host and send five fresh probes with
the local service loopback as source. `../workbook-automation/SERVICE-TRIAL.md`
provides a bounded TCP/UDP helper. Capture application success and the relevant
forwarding evidence. Remove only the local static service /32; retain host,
underlay and BGP session. Observe RT5 withdrawal and failed remote service
access. Restore the exact static route and verify recovery. A discard route is
never a substitute for the real backing service.

## L2 learning, WJH and observation

DC-04 uses exactly five labelled CE offers from `packet_fixtures.py`. Capture
ingress and destination delivery separately and compare learning/RT2/FDB state.
OPS-05 uses the independently reviewed malformed source-MAC fixture for reason
209. Its two publication windows are bounded by a separate 120-second stop.
Neither generated PCAP is device evidence. OPS-11 supplies a bounded capture
controller; its default is a preview. OPS-12 supplies a counter worksheet that
rejects reset, changed identity, ambiguous wrap and malformed numeric evidence.

## The preparation gate

Complete the manifest from actual observations, not from this example. Save the
image/model, feature licenses, interface map, source hashes, clocks, original
state and exact inverses. Check console access, isolation and a finite stop
bound. Validate commands against the installed parser before a change. A task
may remain READ while its device phase is NOT_RUN. Publish RUN only with dated
commands, actual outputs/captures, outcomes and restored state. Keep credentials
and private management addresses out of a distributable evidence bundle.
