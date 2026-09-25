# Lab 30 — EVPN learning, packet delivery and multihoming acceptance

The baseline is Linux/FRR EVPN over VXLAN. It is not MPLS pseudowire or VPLS
execution. Read VALIDATION.md for exact software, passed tests and failed
multihoming acceptance. Do not use the experimental multihoming adapter as a
production reference; duplicate delivery was observed on this local stack.

## Topology and prerequisites

Three PEs form an IPv4 IS-IS triangle. PE loopbacks/VTEPs are 10.255.30.1–3/32;
the pe1–pe2, pe2–pe3 and pe1–pe3 /31s are 10.254.30.0/31, .2/31 and .4/31.
PE eth1/eth2 are transport interfaces, initially MTU 2000. Full-mesh iBGP
AS 64500 carries only EVPN. Each PE has VNI 3000, RT 64500:3000 and its own
loopback:3000 RD. No static remote VTEP/FDB entries seed the overlay.

Each hosts 1–3 connects through eth1 to the corresponding PE eth3. The host
addresses are 10.30.0.1–3/24, MACs 02:00:30:00:00:01–03. Each PE's br30 has
10.30.0.101–103/24 for the explicit binding-learning step, with IP forwarding
disabled on that bridge. VXLAN/bridge dynamic remote learning is disabled;
local attachment learning is enabled. Neighbour suppression starts off.
There is no default route on these hosts and no tenant IRB/type 5 service.
host4 is initially disconnected administratively; its two links are reserved
for the separate experimental MH test. IPv6 is disabled in this IPv4 fixture.

Prerequisites: Linux bridge/VXLAN support and, for the experiment, bonding;
FRR 10.5.1, iproute2, Python 3, tcpdump and iputils ping. Container execution
shares its host kernel. Build the local image described in Lab 29/README.md,
then, from this directory:

```bash
sudo containerlab deploy -t evpn.clab.yml
bash start.sh
docker exec clab-lab30-pe1 vtysh -c 'show bgp l2vpn evpn summary'
docker exec clab-lab30-pe1 vtysh -c 'show evpn vni detail'
docker exec clab-lab30-pe1 bridge fdb show dev vx30
```

The container adapter has been statically reviewed, not deployed here.
The executed reference used isolated Linux namespaces and private FRR
processes with the topology's interface commands and the same .conf files.
Wait for every PE to show two remote VTEPs and stable EVPN sessions. FRR's
EVPN attributes do not require a generic `neighbor ... send-community`
command in this address-family context. In the tested CLI that command
walked to another context; later commands configured the wrong family.
Always inspect the resulting running configuration and advertised routes.

## 30.1 — Baseline, fault and restoration

Commands below run inside the named lab node, for example through
`docker exec clab-lab30-host1 ...`. Capture before sending, wait for tcpdump's
listening message, then stop with SIGINT to flush the capture. Observe both
remote host eth1 interfaces in promiscuous mode. Use EtherType 0x88b5 for the
bounded experimental frames. The sender emits five 100-byte frames by default.

1. Start from a fresh deployment before host3 emits any frame. Confirm its
   MAC is absent from pe1's remote FDB. On host1 run:
   `python3 /lab/send-frame.py eth1 02:00:30:00:00:03 SILENT`.
   Capture with `tcpdump -n -e -i eth1 'ether proto 0x88b5'` on host2 and 3.
   Both attachments should see five frames under the baseline flooding policy.
2. On host3 send five frames to host1's MAC, tag LEARN 3. Wait for pe1's type 2
   route and remote FDB entry for host3 with VTEP 10.255.30.3. Repeat the host1
   transmission with tag KNOWN. Expect zero frames at host2 and five at host3.
   A new unknown destination 02:00:30:00:00:fe should still reach both sites.
   Compare `show bgp l2vpn evpn route type 2`, `show evpn mac vni 3000` and
   `bridge fdb show`. A promiscuous capture observes attachment delivery even
   when the destination MAC is not the local host's MAC.
3. Each host pings its local PE SVI (.101/.102/.103), then all six host pairs.
   Check local/remote IP bindings with `show evpn arp-cache vni 3000` and
   `ip neigh show dev br30`. On pe1 capture ARP on vx30; on host1 capture ARP
   on eth1. Flush only host1's neighbour entries, then ping host3. Repeat after
   `bridge link set dev vx30 neigh_suppress on` on pe1. A valid remote binding
   should give a reply to host1 without that target's request crossing vx30.
   Restore `neigh_suppress off`. This is one IPv4 case, not an ND/DAD suite.
4. On pe1, enter `router bgp 64500`, `address-family l2vpn evpn`, `vni 3000`.
   Add `route-target import 64500:3999`, then remove the authorised import
   with `no route-target import 64500:3000`. Preserve export policy. Verify
   loss of imported service state and failed customer delivery while pe1 can
   still ping 10.255.30.3. Restore by adding 3000 before removing 3999. Confirm
   the actual configured RT list, imported routes/FDB and restored packets.
5. On all PEs set `ip link set vx30 type vxlan df set`. On pe1 set both eth1
   and eth2 to MTU 1500. From host1 use `/usr/bin/ping -M do -s 1422 10.30.0.3`
   and then payload 1423. With base headers, inner IP 1450 produces outer IP 1500;
   inner IP 1451 exceeds it. Capture the real encapsulation and ICMP error.
   Restore pe1 transport MTU 2000. Inspect host1's `ip route get 10.30.0.3`:
   a retained 1450 PMTU can still reject payload 1472 locally. In this disposable
   host, `ip route flush cache` allows the fresh test to demonstrate the restored
   path. This clears that host's cached route exceptions; it is not a general
   production rollback command. Verify inner IP 1500/outer IP 1550 and delivery.
6. Under pe1's VNI 3000 context set `flooding disable`. Unknown destinations
   should no longer cross the overlay while a learned MAC remains reachable
   with the raw sender. This knob also affects other BUM traffic; a silent host
   may become unreachable. Restore `flooding head-end-replication` and repeat
   the unknown-destination capture. Do not use this knob to claim free removal
   of all flooding without a service consequence.

For a real PW/VPLS comparison, supply a separately supported MPLS service
adapter, inspect its signalling/labels and capture known/unknown/BUM traffic.
Disabling EVPN over VXLAN does not turn the resulting network into VPLS.

## 30.2 — Experimental multihoming acceptance

This is a reproducible investigation of the local stack's limits, not a
passed production service. Start from a fresh baseline. Inside pe2, pe3 and
host4, run `python3 /lab/configure-mh.py NODE` with the corresponding name;
load `configs/pe2-mh.conf` and `configs/pe3-mh.conf` with vtysh on those PEs.
host4 forms bond30 across eth1/eth2, address 10.30.0.4/24. Each PE uses its
eth4 in bond30; the two PE LACP actors use 02:00:30:ee:00:04. FRR's ES system
MAC plus discriminator 30 generates ESI 03:02:00:30:ee:00:04:00:00:1e.
DF preferences 200/100 prefer pe2; both core links participate in uplink tracking.

Check `/proc/net/bonding/bond30`, type 1/type 4 routes, `show evpn es detail`,
`show evpn es-evi detail`, `ip nexthop show` and the FDB's nhid. Confirm one
DF, one non-DF, two LACP members and two eligible remote next hops. Then test:

- Multiple distinct UDP source ports to host4; capture each CE member and
  account for every flow. One ping cannot demonstrate MAC-ECMP.
- Eight tagged broadcasts from host1: require eight total arrivals at host4,
  not eight on each member. Check unknown unicast and multicast separately
  before generalising broadcast results.
- Eight broadcasts originating on host4: require no returning copy on either
  member. Direction-filtered captures (`tcpdump -Q in` and `-Q out`) distinguish
  a locally transmitted frame from a frame returned by the other PE.
- One attachment down/up, then both core links on pe2 down/up. Inspect path
  withdrawal, protodown/LACP state, actual service and restoration independently.

The local run distributed 128 flows over both PEs and recovered attachment faults,
but failed the broadcast duplicate/split-horizon requirements. Core-isolation
delivery differed between runs, so consistent recovery is not established. A DF label in
show output was insufficient. Reproduce against a supported complete data
plane before teaching or deploying it as a correct all-active service. Do not
conceal a missing function with static filters and then call dynamic EVPN
multihoming validated. Destroy the disposable lab to restore its fresh baseline.
