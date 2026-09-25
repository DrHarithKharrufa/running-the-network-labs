# Lab 18.1 — Static-route failure, tracking and recovery

This is an isolated IPv4 Linux experiment. A Python ICMP controller and an
actual FRR BFD extension are different tests. Neither is commercial NOS or
ASIC validation. The Containerlab adapters require their own deployment test.

## Topology and prerequisites

```
h1 --- site --- provider bridge --- core --- server
         \--------- backup --------/
```

| Link or role | Addresses |
|---|---|
| Client LAN | h1 198.18.0.10/24, site eth1 198.18.0.1/24 |
| Primary over transparent bridge | site eth2 192.0.2.1/30, core eth1 192.0.2.2/30 |
| Backup | site eth3 198.51.100.1/30, core eth2 198.51.100.2/30 |
| Server LAN | core eth3 203.0.113.1/24, server 203.0.113.20/24 |
| Dedicated probe address on server loopback | 198.19.0.20/32 |

The bridge is one Ethernet service, with no IP hop. The forwarding fault is
100% egress loss on both bridge members, leaving carrier up. Core sends
ordinary client replies over the backup throughout; this deliberate asymmetry
isolates the site's forward-route selection. No stateful firewall/NAT is modelled.
Probe replies to source 192.0.2.1 use the primary connected subnet.

Use a disposable Linux lab host with Docker, Containerlab and NET_ADMIN support.
Build `netbook-linux:local` from `../common` using its README. Run commands from
this directory. The documentation/benchmark addresses must stay inside the lab.
Destroy another lab18 deployment before changing between the two adapters.

## 1. A floating route without detection

```bash
sudo containerlab deploy -t static.clab.yml
docker exec clab-lab18-site ip route show 203.0.113.0/24
docker exec clab-lab18-site ip route get 203.0.113.20
docker exec clab-lab18-h1 ping -c 3 203.0.113.20
bash break-middle.sh break
docker exec clab-lab18-site ip -br link
docker exec clab-lab18-site ip route get 203.0.113.20
docker exec clab-lab18-h1 ping -c 3 -W 1 203.0.113.20
bash break-middle.sh fix
docker exec clab-lab18-h1 ping -c 3 203.0.113.20
```

The metric-10 route remains selected during the fault; the metric-200 backup
does not detect it. Record failed delivery and UP interfaces. Linux route
metrics here order two kernel static routes, not vendor administrative distances.

## 2. Probe tracking with an independent recovery path

The topology supplies a dedicated probe /32 via the primary plus a metric-250
discard for that /32. It stays separate from the controlled service /24. The
discard prevents escape via a less-specific route if the primary /32 disappears.

Run the controller in terminal A, in the foreground:

```bash
docker exec -it clab-lab18-site python3 -u /lab/probe.py
```

It first removes the untracked metric-10 route. Wait for the logged transition
to `"primary": true` after **three successful probes** before injecting a fault.
Otherwise a startup transition can be mistaken for measured failover. The
script withdraws its route after two consecutive failures, restores it after
three successes and logs monotonic times. Its minimum probe-start spacing is
one second, its timeout one second. This is not IP SLA or BFD.

In terminal B:

```bash
docker exec clab-lab18-site ip route get 203.0.113.20
bash break-middle.sh break
# After the controller reports primary=false:
docker exec clab-lab18-site ip route get 203.0.113.20
docker exec clab-lab18-site ip route get 198.19.0.20 from 192.0.2.1
docker exec clab-lab18-h1 ping -c 3 203.0.113.20
docker exec clab-lab18-site ping -c 2 -W 1 -I 192.0.2.1 198.19.0.20
bash break-middle.sh fix
# Wait for primary=true, then repeat the service lookup and ping.
```

Acceptance: application echo succeeds over 198.51.100.2 while the probe stays
on 192.0.2.2 and fails. Successful backup traffic must not restore the primary.
Restoration must follow the configured success threshold. Stop terminal A with
Ctrl-C; its normal shutdown removes its owned service route, leaving the backup.
Do not leave two route controllers running. A forced kill can leave stale state:
the script is a teaching controller without a production watchdog/persistence design.

For timing, timestamp fault-command start, observed route change and first
successful application reply separately. Record sampling intervals and scheduling
overhead. A count of lost pings alone is not the detection interval. Do not
compare timers using a sample taken before the controller reaches its baseline.

## 3. The default/summary loop

Stop the probe controller and restore the bridge before this part. Leave the
working service on its backup. These commands add two **static** routes; no
routing-protocol advertisement takes place.

```bash
docker exec clab-lab18-site ip route add default via 198.51.100.2
docker exec clab-lab18-core ip route add 198.18.0.0/15 via 198.51.100.1
```

In terminal A capture only requests to the unused target:

```bash
docker exec -it clab-lab18-site tcpdump -nn -vv -i eth3 \
  'icmp and dst host 198.18.99.1'
```

In terminal B send one packet:

```bash
docker exec clab-lab18-h1 ping -c 1 -t 8 -W 2 198.18.99.1
docker exec clab-lab18-site ip route add blackhole 198.18.0.0/15
docker exec clab-lab18-site ip route show type blackhole
docker exec clab-lab18-h1 ping -c 1 -t 8 -W 2 198.18.99.1
docker exec clab-lab18-h1 ping -c 3 203.0.113.20
```

Before discard, expect requests with TTLs 7,6,5,4,3,2,1 on the site-core link,
then expiration at core. After discard, the unused destination must not cross
that link; the live /24 client LAN and server service must still work. Stop capture.
With input TTL T at site, the constructed loop has T−1 inter-router traversals.
At T=64 this is 32 towards core and 31 back. Multiplying a 1 Gb/s input gives
unconstrained offered rates; actual carried rates remain bounded by each link's
capacity and overhead. Do not generate a high-rate loop to demonstrate this.

```bash
docker exec clab-lab18-site ip route del blackhole 198.18.0.0/15
docker exec clab-lab18-core ip route del 198.18.0.0/15 via 198.51.100.1
docker exec clab-lab18-site ip route del default via 198.51.100.2
sudo containerlab destroy -t static.clab.yml
```

## 4. Actual BFD extension: FRR 10.5.1

Use a fresh topology. `Dockerfile.frr` selects FRR 10.5.1; the exact package
build and base-image digest must be recorded in an executed deployment. The
local evidence used extracted Ubuntu 26.04 package 10.5.1-1ubuntu4.1. It did
not build this image or execute Containerlab. Image/package availability is
an external prerequisite, not a successful build claim.

```bash
docker build -f Dockerfile.frr -t netbook-frr:10.5.1 .
sudo containerlab deploy -t bfd.clab.yml
docker exec clab-lab18-site ip route del 203.0.113.0/24 via 192.0.2.2 dev eth2 metric 10
docker exec clab-lab18-site ip route del 203.0.113.0/24 via 198.51.100.2 dev eth3 metric 200
docker exec clab-lab18-site bash /lab/frr-start.sh site
docker exec clab-lab18-core bash /lab/frr-start.sh core
docker exec clab-lab18-site vtysh -c 'show bfd peers json'
docker exec clab-lab18-core vtysh -c 'show bfd peers json'
docker exec clab-lab18-site vtysh -c 'show ip route 203.0.113.0/24'
```

`bfd-site.conf` and `bfd-core.conf` provide both peers, IPv4, default VRF,
single-hop asynchronous mode, local addresses and interfaces. Desired transmit
and required receive are 300 **milliseconds**, detection multiplier 3, echo
mode left disabled. Site's primary static is BFD-bound; its alternative has
distance 200. FRR may omit explicit default timer values in running output;
inspect the operational peer report for actual local/remote values.

Wait for both sessions Up, the primary selected, and client echo success.
Repeat the middle fault and restoration using `break-middle.sh`. Require Down,
primary withdrawal, backup delivery, then Up and restored primary delivery.
Capture `udp port 3784` on the primary for packet-level evidence. Because the
provider is a bridge, it does not decrement the single-hop BFD packet's TTL.
This test does not establish that BFD detects a failure beyond core: a blocked
server can fail while the BFD session remains Up. Test and record that distinction.

Preserve version, peer, route and capture evidence before cleanup:

```bash
docker exec clab-lab18-site vtysh -c 'show version'
docker exec clab-lab18-site vtysh -c 'show running-config'
sudo containerlab destroy -t bfd.clab.yml
```

The extension loads deliberate runtime configuration on a disposable topology.
Reload/persistence, IPv6, multihop BFD, loaded-host timing and commercial devices
need separate tests. Do not run the Python controller during the BFD extension.
