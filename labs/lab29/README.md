# Lab 29 — a routed VPN, hub enforcement and an external-service leak

This isolated fixture uses Linux VRFs/MPLS with FRR 10.5.1. IS-IS and LDP
connect pe1–p1–pe2; MP-BGP VPNv4 connects the two PEs. CE routers use eBGP.
It is a small reference network, not the complete Kestrel worked network.
Read VALIDATION.md before interpreting any step as executed evidence.

## Addressing and prerequisites

| Site | PE attachment/context | CE attachment | Site host |
|---|---|---|---|
| 1 / hub | pe1 eth2, site1/table100, 10.29.255.0/31 | ce1 eth1, .1 | host1 10.29.1.10/24, gateway .1 |
| 2 / spoke | pe2 eth2, site2/table200, 10.29.255.2/31 | ce2 eth1, .3 | host2 10.29.2.10/24, gateway .1 |
| 3 / spoke | pe2 eth3, site3/table300, 10.29.255.4/31 | ce3 eth1, .5 | host3 10.29.3.10/24, gateway .1 |
| Hub return | pe1 eth3, hub-return/table101, 10.29.255.6/31 | ce1 eth3, .7 | No separate host |
| Synthetic external | ce1 eth4, 198.51.100.1/30 | external eth1, .2 | Return 10.29.0.0/16 via .1 |

Each CE's eth2 is the site gateway. PE loopbacks are 10.255.0.1/32 and
10.255.0.2/32; p1 is 10.255.0.9/32. Core /31s are 10.254.29.0/31 and
10.254.29.2/31. All CEs use AS64501; both PEs use AS64500. No customer
prefix enters the core IGP. Same-PE spokes have separate VRFs deliberately.

The host kernel must support VRF, MPLS routing and MPLS IP tunnels. Containers
share that kernel. Linux VRF devices, interface membership, IP forwarding,
MPLS input and the label table are configured explicitly in the topology.
Core/CE interconnect MTU is 2000; host-facing MTU is 1500. Unreachable VRF
defaults prevent an unintended fall-through to the main routing table.

```sh
docker build -t netbook-frr:10.5.1 -f ../lab18/Dockerfile.frr ../lab18
sudo modprobe vrf mpls_router mpls_iptunnel
sudo containerlab deploy -t l3vpn.clab.yml
bash start.sh
```

Startup launches the listed daemons and loads baseline files. Wait for four
directed operational LDP rows, the PE VPN BGP session and all three CE BGP
sessions. The second ce1 attachment is addressed but its BGP session starts
only in the hub phase. Configuration loading is not convergence.

## Lab 29.1 — inspect, then enable the service

Inspect `show mpls ldp neighbor`, `show bgp ipv4 vpn`,
`show bgp vrf site1 ipv4 unicast` (pe1), the corresponding site2/site3 tables
(pe2), and `show bgp ipv4 unicast` on each CE. Each local CE exports its exact
site /24. PE policies accept only that site and export only approved remote
routes. Both policy directions are defined in the supplied files.

Before AS override, a remote customer route can reach a PE's VPN table while
the CE rejects the path containing its own AS64501. Capture the received path
and verify that host1 cannot reach host2. Then apply:

```sh
docker exec clab-lab29-pe1 vtysh -f /lab/configs/pe1-override.conf
docker exec clab-lab29-pe2 vtysh -f /lab/configs/pe2-override.conf
docker exec clab-lab29-host1 ping -c 3 10.29.2.10
docker exec clab-lab29-host2 ping -c 3 10.29.1.10
```

Test all six ordered pairs among the three hosts. Override is appropriate
to this single-homed fixture; it is not a substitute for multihoming/SoO and
backdoor loop design. The prefix limits here are eight received prefixes
per CE peer with a defined restart interval, not a universal production value
or a total installed-route limit for the VRF.

For 10.29.2.0/24, correlate RD 10.255.0.2:200, RT64500:2900, VPN next hop,
advertised service label, imported site1 route and kernel forwarding. Labels
are allocated at runtime: do not hard-code an observed number into an answer.
`label vpn export auto` depends on zebra and is explicitly supplied.

Capture pe1 eth1 and p1 eth2 during a host1→host2 probe. This LDP/PHP path
should carry transport plus service at the first capture and service only
at the second. Decode the actual stack, bottom-of-stack bit and inner IP
packet. Check p1's IPv4 routing table: it does not need 10.29.x customer routes.

On pe1, remove only `rt vpn import 64500:2900` from the site1 IPv4 family.
Verify that the remote route and customer delivery disappear while the PE
loopback transport still works. Restore the import and both directions.
Preserve before/fault/after snapshots instead of repeatedly changing several
layers until ping happens to work.

FRR 10.5 offers `label vpn export allocation-mode per-vrf|per-nexthop`.
Do not use the original lab's unsupported per-prefix command. In this fixture
each site VRF has one customer next hop, so changing those two modes is not
expected to create a useful scale comparison; a multi-next-hop fixture would
be needed. Label-count exercises in the chapter are resource models.

## Lab 29.2 — two hub contexts and an enforced path

Apply this phase only after the any-to-any baseline passes:

```sh
docker exec clab-lab29-pe1 vtysh -f /lab/configs/pe1-hub.conf
docker exec clab-lab29-pe2 vtysh -f /lab/configs/pe2-hub.conf
docker exec clab-lab29-ce1 vtysh -f /lab/configs/ce1-hub.conf
```

The inspectable files change the policy as follows:

- Spokes export their /24s with RT64500:2912. Hub-return imports those routes
  and advertises them to ce1 on the second attachment.
- ce1 originates 10.29.0.0/16 towards hub ingress, with a high-distance Null0
  route behind it. Its learned, more-specific spoke routes forward real site
  traffic through the return attachment. The aggregate's unused destinations
  are deliberately discarded; it is not proof that every address is served.
- Hub ingress exports the aggregate and its own site with RT64500:2911.
  Both spokes import that RT; neither normally imports RT64500:2912.
- ce1 also originates a default. Hub export policy gives it only
  RT64500:2999. Site2 imports this additional RT; site3 does not.

Thus host2→host3 uses pe2/site2 → pe1/site1 → ce1 → pe1/hub-return →
pe2/site3. Capture the same forward packet on ce1 eth1 and eth3. Check the
reverse path as well. Inspect each specific route and the summary; traceroute
alone is insufficient to prove inspection. This CE represents the hub routing
and packet-control function, not a certified commercial firewall.

In ce1's isolated namespace/container, apply this deliberately simple rule:

```sh
iptables-legacy -A FORWARD -s 10.29.2.0/24 -d 10.29.3.0/24 -j DROP
iptables-legacy -nvL FORWARD
```

host2→host3 must fail and the rule counter must increase. Leave the rule
present while deliberately changing site2's import list on pe2 to
`rt vpn import 64500:2911 64500:2999 64500:2912`. This command replaces the
list in this FRR interface; it is not a one-value append. The more-specific
site3 route creates a local bypass around the hub. Observe delivery and the
changed path, then restore the **complete** healthy list with
`rt vpn import 64500:2911 64500:2999`. Verify the hub summary remains and the
direct site3 /24 disappears. Clear this lab rule's counter, repeat the failed
probe and confirm the counter increases: loss caused by a missing route is
not proof of restored inspection. Remove the exact rule with `-D` in place of `-A`,
then verify restored service. Never apply these commands to the host's
production firewall.

## Default-route authorisation, with a complete synthetic path

The external endpoint 198.51.100.2 is a documentation-address host on a
private link. It is **not the public Internet**. It has explicit return
routing to the customer aggregate; this fixture requires no NAT.

With hub policy installed, host2 should reach it and host3 should not.
Confirm that site2 has the hub default, site3 lacks it, and the private
site-to-site path still works. Deliberately set site3's import list to
`rt vpn import 64500:2911 64500:2999`:
the complete existing forward/return path now allows an unauthorised customer
to reach the endpoint. Restore `rt vpn import 64500:2911` and repeat both
customer tests, including permitted private connectivity.

The policy error is visible in the route table before a packet test. Actual
external delivery is a separate assertion. A production shared exit additionally
needs the real upstream contract, public addressing or translation, stateful
security, capacity and failure design. Overlapping customers need a return
context that can distinguish them.

## Rollback and questions

For a clean return to the any-to-any phase, destroy and redeploy **only this
disposable topology**. Reapplying a baseline file does not reliably remove
every added command: `sudo containerlab destroy -t l3vpn.clab.yml`.

1. Which observation distinguishes own-AS rejection from an RT import fault?
2. Why do the two spoke attachments have separate VRFs even on the same PE?
3. Which test proves a hub deny cannot be bypassed in the corrected state?
4. What makes the synthetic default-route leak deliver packets in both directions?
5. Which transport and service-label observations change after PHP?

Primary references: [RFC4364](https://www.rfc-editor.org/rfc/rfc4364.html),
[RFC8277](https://www.rfc-editor.org/rfc/rfc8277.html),
[FRR 10.5 L3VPN](https://docs.frrouting.org/en/stable-10.5/bgp.html#l3vpn-vrfs).
