# Lab 26 — MPLS forwarding, LDP and independent service checks

This five-router/two-host lab separates an IP underlay, LDP transport and a
manually assigned inner-label fixture. It is **not** a BGP/MPLS L3VPN: no
MP-BGP, RD/RT or VRF isolation is configured. Customer prefixes stay out of
the core IGP. The two manual service labels identify outgoing host delivery.
Use only a disposable lab. Read VALIDATION.md for actual execution coverage.

## Topology and startup

The preferred path is `lon-pe-01 — lon-p-01 — bhm-p-01 — lds-pe-01`.
The parallel segment is `lon-p-01 — alt-p-01 — bhm-p-01`. Each preferred
link has IS-IS cost 10; each alternate segment has cost 50. Hosts a/b attach
to the PEs and use 10.26.1.10/24 and 10.26.2.10/24. Loopbacks are
10.255.0.23, .11, .13, .24 and .15 respectively. All core interfaces are
2000 bytes initially; Linux MPLS acceptance initially permits core links; the explicit-null test
also enables the egress loopback processing path.
The JSON-formatted .yml file is valid YAML and holds exact endpoint/address maps.

From this directory, build `netbook-frr:10.5.1` using
`docker build -t netbook-frr:10.5.1 -f ../lab18/Dockerfile.frr ../lab18`.
The image must contain FRR zebra, mgmtd, staticd, isisd,
ldpd, vtysh, Python 3, iproute2, iputils ping and tcpdump. A container shares
its host kernel: merely installing FRR does not provide MPLS kernel support.
On the dedicated Linux lab host, check these prerequisites before deployment:

```sh
sudo modprobe mpls_router
sudo modprobe mpls_iptunnel
test -e /proc/sys/net/mpls/platform_labels
sudo containerlab deploy -t mpls.clab.yml
bash start.sh
```

The topology sets platform_labels=65536 and per-core-interface input=1
inside each router namespace. `start.sh` explicitly starts five daemons per
router and loads baseline IS-IS files. No startup file means “converged”.
Check all expected IS-IS adjacencies and both PE loopback directions. Customer
host-to-host traffic should still fail. Save the observed state.

```sh
docker exec clab-lab26-lon-pe-01 vtysh -c 'show isis neighbor'
docker exec clab-lab26-lon-pe-01 ping -c 3 10.255.0.24
bash enable-ldp.sh
docker exec clab-lab26-lon-p-01 vtysh -c 'show mpls ldp neighbor'
docker exec clab-lab26-lon-p-01 vtysh -c 'show mpls ldp ipv4 binding'
docker exec clab-lab26-lon-p-01 vtysh -c 'show mpls table'
docker exec clab-lab26-lon-p-01 ip -f mpls route show
```

Expect five link adjacencies, observed at both endpoints (ten operational
neighbour rows across all routers). Confirm the selected next hop and its
binding for each far-PE loopback. `install-service.sh` reads the actual
transport label; do not hard-code a label from another run. It adds service
labels 24001/24002 only after collision and existing-route checks. A partial
installation must be inspected before retrying. These teaching labels are
not a production allocation mechanism, and dynamic label changes require
re-reading/rebuilding the manually imposed stack.

```sh
bash install-service.sh
docker exec clab-lab26-host-a ping -c 3 10.26.2.10
docker exec clab-lab26-host-b ping -c 3 10.26.1.10
```

Capture on PE1 eth1, P1 eth2 and PE2 eth1. Record actual outer labels, TC,
S bit and TTL. The last link should carry the service label alone under PHP.
Check that P1 has no customer IP prefix. At PE2 request explicit null:

```text
configure terminal
mpls ldp
 address-family ipv4
  label local advertise explicit-null
 exit-address-family
exit
end
```

Read bindings again and capture customer probes on the final link. Compare
the label 0 entry above service 24002. In the recorded Linux 7.0.0-31 guest,
this stack initially failed because loopback MPLS input was disabled.
On PE2, `sysctl -qw net.mpls.conf.lo.input=1` enabled inner-label
processing after explicit-null removal and restored service. A controlled
return to 0 reproduced the failure; 1 restored it again. This requirement is
specific to the demonstrated Linux processing path. A single-label
explicit-null PE-loopback probe had continued working throughout.
Restore PHP with
`no label local advertise explicit-null` in the same address-family context.
Do not claim QoS performance or TTL-model coverage from this capture alone.

## Independent service and forwarding faults

Inside PE2 remove `ip -f mpls route del 24002`. Compare customer probes
with PE1-to-PE2 loopback probes, then restore:
`ip -f mpls route add 24002 via inet 10.26.2.10 dev eth2`.
Separately set `net.mpls.conf.eth1.input=0` on bhm-p-01, compare LDP
neighbour state with failed service probes, and restore input=1.
Do not combine these faults, or the diagnosis becomes ambiguous.

## LDP/IGP readiness gap

Keep the alternate path healthy. Inside P1, block incoming link Hellos using
`iptables-legacy -I INPUT -i eth2 -p udp --dport 646 -j DROP`; on P2 use
the equivalent rule for eth1. Leave LDP configured. IS-IS and the physical
link remain up. The extracted Linux test environment also needs libip4tc/libip6tc
and the xt_tcpudp module for this legacy-iptables match.
Wait for the relevant LDP session to disappear, then save route, binding,
LFIB, interface/IS-IS metric and customer/loopback probe results.
This deliberately sustained fault makes the dependency visible; its duration
is not a measurement of normal recovery convergence.

Enable FRR IS-IS LDP synchronisation on P1/P2 in the router context with
`router isis CORE / mpls ldp-sync`; inspect interface overrides and
`show isis mpls ldp-sync`. Observe the advertised metric and whether the
alternate becomes selected. Remove those exact rules using `-D` instead of `-I`,
wait for operational sessions, and confirm normal path and bidirectional
service recovery. For an actual link-return timing test, collect continuous
sequence-numbered traffic across failure/recovery with a defined sampling
rate; the sustained-gap experiment alone does not establish a loss bound.

## MTU boundary

First verify a 1500-byte customer IPv4 packet (`ping -M do -s 1472`) works.
On lon-p-01 change eth2 to MTU 1500, and on bhm-p-01 change eth1 to 1500.
Wait for the primary IS-IS/LDP adjacency and verify that P1 still selects eth2
for the far PE. Changing only one end can break padded IS-IS Hellos and move
traffic onto the alternate, invalidating the intended boundary test.
The P1 interface forwards two labels;
its Linux MPLS payload budget leaves 1492 bytes for the customer IP packet.
From host-a, probe echo payload 1464 (1492-byte IP), 1465 and a small packet.
Restore both interfaces to 2000, confirm the preferred path, and repeat the
full-size probe.
Record all command output; a received ICMP error can affect cached PMTU.
Keep packet size, ICMP/IP headers, label stack and frame definition distinct.

Destroy only this topology when finished:
`sudo containerlab destroy -t mpls.clab.yml`.

## Primary references

- [MPLS architecture](https://www.rfc-editor.org/rfc/rfc3031.html) and
  [encoding](https://www.rfc-editor.org/rfc/rfc3032.html).
- [Explicit null](https://www.rfc-editor.org/rfc/rfc4182.html),
  [LDP](https://www.rfc-editor.org/rfc/rfc5036.html),
  [IGP synchronisation](https://datatracker.ietf.org/doc/html/rfc5443),
  [LSP OAM](https://www.rfc-editor.org/rfc/rfc8029.html).
- [FRR 10.5 LDP](https://docs.frrouting.org/en/stable-10.5/ldpd.html),
  [10.5.1 IS-IS synchronisation source](https://github.com/FRRouting/frr/blob/frr-10.5.1/isisd/isis_ldp_sync.c),
  [Linux MPLS controls](https://docs.kernel.org/networking/mpls-sysctl.html).
- [Cisco XE 17.x LDP](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/mpls/b-mpls/m_mp-ldp-overview.html),
  [Cisco 8000 XR 7.9.x LDP](https://www.cisco.com/c/en/us/td/docs/iosxr/cisco8000/mpls/79x/b-mpls-cg-cisco8000-79x/implementing-mpls-ldp.html).
- [Nokia SR OS 24.10.R1 MPLS](https://documentation.nokia.com/sr/24-10/7750-sr/pdf/MPLS_Guide_24.10.R1.pdf),
  [SR Linux 24.10 support](https://documentation.nokia.com/srlinux/24-10/books/mpls/overview-mpls.html) and
  [configuration](https://documentation.nokia.com/srlinux/24-10/books/mpls/configuring-ldp.html).
- [Huawei S9300/S9300X V200R021C00/C01 example](https://support.huawei.com/enterprise/en/doc/EDOC1100213172/df02d722/example-for-configuring-synchronization-between-ldp-and-igp).
