# Lab 13 — aggregation, gateway redundancy and multihoming

These are separate experiments. Linux bonding does not implement MC-LAG.
Use a disposable Linux host, preserve control access, build the common image
using ../common/README.md and record its digest, packages and host kernel.

## 13.1 — two LACP partners

`lag.clab.yml` connects a:eth1 to b:eth1 and a:eth2 to b:eth2. Both use
802.3ad bonding, miimon 100 ms, fast LACP, layer3+4 hashing and min_links 1.
Their bond addresses are 192.0.2.1/30 and 192.0.2.2/30. There is no MC-LAG.

```sh
sudo containerlab deploy -t lag.clab.yml
docker exec clab-lab13-lacp-a cat /proc/net/bonding/bond0
docker exec clab-lab13-lacp-b cat /proc/net/bonding/bond0
docker exec clab-lab13-lacp-a ping -n -c 5 -W 1 192.0.2.2
```

Check partner IDs, selected aggregator and collecting/distributing members.
Inside a, disable eth1 with `ip link set eth1 down`. Verify one selected
member and service through it. Disable eth2 as well; verify failure. Restore
eth2 and service, then eth1 and both members. Bound each recovery check to
15 seconds, record the polling interval and preserve both bond states. A
reported member count can precede service recovery. Always restore both
links before investigating an unexpected result.

For optional hashing trials, start a bounded server and run separate tests:

```sh
docker exec -d clab-lab13-lacp-b timeout 45 iperf3 -s
docker exec clab-lab13-lacp-a iperf3 -c 192.0.2.2 -t 10 -P 1
docker exec clab-lab13-lacp-a iperf3 -c 192.0.2.2 -t 10 -P 8
sudo containerlab destroy -t lag.clab.yml --cleanup
```

Take `ip -s link show eth1` and eth2 counter snapshots on a before and after
each trial. Eight flows may distribute unevenly. Record that observation
and host CPU constraints. Virtual links do not demonstrate physical 10 Gb/s
limits. These throughput trials are not recorded local throughput results.

## 13.2 — a complete IPv4 gateway service

`vrrp.clab.yml` supplies two shared LANs, R1/R2 on both, a client and server.
The client prefix is London's 10.10.0.0/22: VIP .1, real peers .2/.3,
client .10. The server LAN is 198.51.100.0/24: VIP .1, peers .2/.3, server .10.
The client routes the server prefix through its VIP and the server routes
the client prefix through its own VIP. There is no NAT or external route.
The LAN bridges and endpoints remain single points of failure.

Complete files r1.conf/r2.conf select VRRPv3, virtual MACs and one-second
advertisements. R1 is priority 110, R2 100, with normal pre-emption. CLIENT
(VRID 110) and SERVER (VRID 113) use a Keepalived sync group. Each instance
automatically tracks its primary interface; FAULT propagates through the
group. Do not add duplicate group trackers for those same interfaces. This
coupling is a Keepalived extension, not a VRRP wire-protocol guarantee.

```sh
sudo containerlab deploy -t vrrp.clab.yml
bash vrrp-process.sh start r1
bash vrrp-process.sh start r2
docker exec clab-lab13-vrrp-r1 ip -4 address show
docker exec clab-lab13-vrrp-r2 ip -4 address show
docker exec clab-lab13-vrrp-client ping -n -c 5 -W 1 198.51.100.10
```

Within 12 seconds both VIPs should belong only to R1's virtual MAC interfaces.
Check routes, neighbours and logs. `no_accept` blocks ordinary traffic *to*
a non-owner VIP; test the routed server. Capture actual VRRPv3 advertisements.
The wrapper copies the configuration to a non-executable file in the container
before starting Keepalived; this matters when sources came from a Windows mount.

For one pre-existing application connection, start:

```sh
docker exec -d clab-lab13-vrrp-server python3 /lab/tcp-echo.py server
docker exec clab-lab13-vrrp-client python3 /lab/tcp-echo.py client
```

The client records successful echo sequence numbers and response times for
60 seconds using one socket; it does not silently reconnect. The server has
finite accept/session timeouts. In another host terminal, inject one fault
at a time while recording the application output:

1. Disable R1 eth2. Verify both VIPs on R2 and routed service. Restore eth2;
   verify R1's pre-emption **and service recovery** before the next event.
2. `bash vrrp-process.sh stop r1` performs a graceful shutdown. Verify R2 and
   service. Restart R1 and recheck. A graceful stop may explicitly relinquish;
   it is not evidence for abrupt power-loss timing.
3. With service stable through R1, fail and restore R2 eth2. Record standby
   state and any application disruption; do not assume it must be invisible.

Allow at most 12 seconds for each expected ownership/service recovery. Stop
if both peers claim active ownership or the route does not recover. Restore
links and investigate logs instead of continuing from an unknown state.
Use `bash vrrp-process.sh logs r1` or r2. Finish with:

```sh
bash vrrp-process.sh stop r1
bash vrrp-process.sh stop r2
sudo containerlab destroy -t vrrp.clab.yml --cleanup
```

Abrupt node loss, IPv6, remote-path tracking and stateful services need
additional tests. Define IPv6 link-local/RA/ND behaviour separately.

## 13.3 — a supported MC-LAG or EVPN target

Choose a licensed model/image pairing. Document partner identity, coordination,
keepalive path, orphan-port policy and recovery. Build its complete two-peer
design, not two unrelated Linux bonds. Test member, peer-link, keepalive and
peer power loss, both coordination failures in each order, and restoration.
This target-dependent exercise has not been executed on this review PC.

## Recorded local evidence

Linux 6.18.33.2 / iproute2 6.19.0 LACP: 9 assertions passed in isolated
namespaces (runtime-evidence/20260916T205337Z/results.json). Earlier attempts
showed member selection can precede restored service and are retained.

Keepalived 2.3.4 IPv4 VRRPv3: 17 assertions passed in isolated namespaces
(runtime-evidence/20260916T205929Z/results.json), with both-LAN captures,
address/route snapshots and one TCP connection surviving the tested events.
405 successful echo samples were recorded; the maximum observed response
time was about 3.34 seconds. This is workload-specific, not a lossless result
or SLA. Earlier failed configuration/test attempts remain in the archive.

Docker image builds, these host wrappers, Containerlab deployment, IPv6 and
commercial MC-LAG/EVPN execution are separate pending validation cases.
