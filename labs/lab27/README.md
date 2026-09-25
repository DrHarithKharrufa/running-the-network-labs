# Lab 27 — SR-MPLS migration, steering and instruction failure

Four FRR routers form a ring. Each individual link has symmetric IS-IS costs:
London–Manchester–Leeds costs 10+10; London–Birmingham–Leeds costs 40+40.
Two hosts attach to London and Leeds at 10.27.1.10 and 10.27.2.10.
The two edge routers exchange these IPv4 prefixes over iBGP AS 64500.
Intermediate routers have no customer routes. This is a plain IPv4 service
fixture, **not** a VPN. The .clab.yml file is JSON-formatted valid YAML with
the exact addresses, interface map, MPLS sysctls and 2,000-byte core MTUs.
Read VALIDATION.md before interpreting a suggested exercise as executed.

## Start the LDP baseline

Use a disposable Linux host with MPLS routing/encapsulation kernel support.
A container shares its host kernel. The image needs FRR 10.5.1 with zebra,
mgmtd, staticd, isisd, ldpd, bgpd and pathd; it also needs iproute2, Python 3,
iputils ping and tcpdump. Build the supplied lab18 image from this directory:

```sh
docker build -t netbook-frr:10.5.1 -f ../lab18/Dockerfile.frr ../lab18
sudo modprobe mpls_router
sudo modprobe mpls_iptunnel
test -e /proc/sys/net/mpls/platform_labels
sudo containerlab deploy -t sr.clab.yml
bash start.sh
```

The script starts daemons and loads configuration; it does not declare
convergence. Check each router's `show isis neighbor`, `show mpls ldp neighbor`,
`show mpls table` and kernel routes. There should be four physical core
adjacencies and eight directed operational LDP neighbour rows. Check the
London/Leeds BGP session, installed customer routes and both host directions:

```sh
docker exec clab-lab27-lon-p-01 vtysh -c 'show bgp ipv4 unicast summary'
docker exec clab-lab27-host-a ping -c 3 10.27.2.10
docker exec clab-lab27-host-b ping -c 3 10.27.1.10
```

Capture London eth1 and save the selected route, label bindings and kernel
encapsulation. Do not infer label ownership from its numeric value alone.

## Enable SR one router at a time

Loopbacks 10.255.0.11–14 use indexes 11–14 in SRGB 16000–23999. The configured
node MSD of 8 is an advertised lab assumption, not a measured hardware limit.
For each of lon-p-01, man-p-01, bhm-p-01 and lds-p-01, load that node's file:

```sh
docker exec clab-lab27-lon-p-01 vtysh -f /lab/configs/lon-p-01-sr.conf
```

After **each** node, inspect IS-IS/SR state, route recursion and service probes.
`enable-sr.sh` loads all four files for a repeatable prepared lab; use the
individual commands for this staged exercise. Save the coexistence state.
FRR's release documentation describes this IS-IS SR implementation as experimental.

In this disposable fixture only, remove `mpls ldp` through each router's
configuration context. Confirm no LDP peers remain, inspect the LFIB and
capture traffic again. The recorded primary path uses node SID 16014 towards
Leeds. Verify the route protocol/owner and packet action, not just the number.
Production removal would first need the service/interworking dependency
inventory in the chapter; this fixture contains no pseudowires or VPNs.

## Install and observe a local policy

On London inspect `show debugging label-table json`. The recorded allocation
contains IS-IS chunks 15000–15999 and 16000–23999. A request for binding label
15000 fails because it overlaps a reserved chunk. Verify that **30000** is
available before using the supplied policy; it is an intentional lab value,
not a universally safe production assignment.

```sh
docker exec clab-lab27-lon-p-01 vtysh -c 'show debugging label-table json'
docker exec clab-lab27-lon-p-01 vtysh -f /lab/configs/lon-policy.conf
docker exec clab-lab27-lon-p-01 vtysh -c 'clear bgp ipv4 unicast 10.255.0.14 soft in'
docker exec clab-lab27-lon-p-01 vtysh -c 'show sr-te policy detail'
```

The policy requires Birmingham and then Leeds. The inbound route-map steers
only 10.27.2.0/24 by colour 100; its final permit clause preserves other
eligible routes. Read BGP, IP recursion, the binding label and kernel LFIB.
Capture **both** London uplinks while probing from host-a: forward customer
traffic should use eth2 towards Birmingham, not eth1 towards Manchester.
Return traffic is a separate direction and is not given the same policy here.
The configured raw-label list is not a live constraint-validation controller.

## Distinguish node and pinned-adjacency instructions

1. With the node list active, bring **Birmingham eth2** down. Wait for IS-IS
   convergence and inspect both London captures again. In the recorded case,
   packets still visit Birmingham, then return through London and Manchester
   to reach Leeds. This longer path is reachable; it proves no delay bound.
2. Restore that interface and adjacency. Read Birmingham's current local
   label for the Leeds-facing unprotected adjacency. Correlate `show mpls table`
   (next hop 10.254.0.7) with the owner's LSDB adjacency advertisement, flags and
   SR local allocation. In the recorded run it was 15001; **read it again**
   instead of treating that sample number as permanent.
3. In London's `segment-routing / traffic-eng / segment-list VIA-BHM`
   context, replace index 20 with `index 20 mpls label CURRENT_ADJ_LABEL`.
   Substitute the observed numeric value; the capitalised token is not CLI.
   Confirm customer delivery before faulting anything.
4. Bring Birmingham eth2 down again. The recorded pinned list loses customer
   delivery while London's policy still reports **Active**. This list does
   not automatically validate the remote adjacency's lifetime. Inspect the
   owner LFIB and service probes rather than trusting the head-end status.
5. With the link still down, restore `index 20 mpls label 16014`. The node-list
   instruction can use the surviving path and service recovers. Restore the
   link, confirm adjacencies and both service directions.

The link commands for this topology are:

```sh
docker exec clab-lab27-bhm-p-01 ip link set eth2 down
# Observe the selected test case, then restore explicitly:
docker exec clab-lab27-bhm-p-01 ip link set eth2 up
```

Do not claim TI-LFA or a 50 ms result from these post-convergence probes.
This experiment deliberately distinguishes instructions, not recovery timing.

## Policy absence, fallback and rollback

With colour steering still attached, remove the policy using
`no policy color 100 endpoint 10.255.0.14` in the traffic-eng context.
Save policy, BGP and kernel state and probe. The recorded FRR fixture retains
reachability through ordinary SR resolution. That fallback could violate an
exclusion requirement in a different service. Define the intended behaviour
and test it on the actual release; neither loss nor safe fallback is universal.

Explicit rollback removes the inbound STEER route-map from neighbour
10.255.0.14 under London's BGP IPv4-unicast context, then performs the same
inbound soft refresh. Verify ordinary SR delivery. Reload each node's baseline
.conf to restore LDP, wait for all eight operational rows, and only then use
`no segment-routing on` under each `router isis CORE`. Check both host directions,
LDP ownership and the resulting stack. Remove unused policy/list/route-map
objects after checking their references, or destroy this disposable topology:

```sh
sudo containerlab destroy -t sr.clab.yml
```

## Primary references

- [SR architecture](https://www.rfc-editor.org/rfc/rfc8402.html),
  [SR-MPLS](https://www.rfc-editor.org/rfc/rfc8660.html),
  [IS-IS extensions](https://www.rfc-editor.org/rfc/rfc8667.html),
  [SR policies](https://www.rfc-editor.org/rfc/rfc9256.html).
- [LDP interworking](https://www.rfc-editor.org/rfc/rfc8661.html),
  [TI-LFA and its convergence boundaries](https://www.rfc-editor.org/rfc/rfc9855.html).
- [FRR 10.5 IS-IS](https://docs.frrouting.org/en/stable-10.5/isisd.html),
  [pathd](https://docs.frrouting.org/en/stable-10.5/pathd.html),
  [10.5.1 label manager](https://github.com/FRRouting/frr/blob/frr-10.5.1/zebra/label_manager.c).

RSVP-TE, PCEP control and commercial NOS implementations need their own
fixtures and evidence; this lab does not execute them.
