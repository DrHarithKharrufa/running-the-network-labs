# Labs — Running the Network

Two paths through every lab in the book. Pick one, or use both.

| | **Containerlab** | **GNS3** |
|---|---|---|
| Cost | Free. No account, no licence. | Free software, but you supply vendor images. |
| Runs on | Linux, or WSL2 / a Linux VM on Windows and macOS | Linux, Windows, macOS (with the GNS3 VM) |
| Boot time | Seconds | Minutes |
| RAM for the Kestrel topology | ~8 GB | ~24 GB |
| Vendors you can actually run | Nokia SR Linux, FRR, SONiC, VyOS, Cumulus, Arista cEOS | All of the above plus Cisco IOS-XR/IOL, Nokia SR OS, Huawei VRP, Fortinet, Juniper — if you have the images |
| Config as code | Native (`startup-config:`) | By console or Ansible after boot |

**Both paths read the same topology files.** `topologies/*.clab.yml` is the
single source of truth; `gns3/gns3_build.py` renders it into a GNS3 project via
the controller API. Change the topology once and both labs follow.

---

## Lab index

| Lab | Chapter | Topology | What it teaches |
|---|---|---|---|
| 4.1 | 4 — Signals, cables and optics | `lab04/physical.clab.yml` | Where each platform hides interface state, error counters and optics; working an optical budget by hand |
| 5.1 | 5 — Ethernet and the LAN | `lab05/mtu.clab.yml` | Finding an MTU mismatch from pings and counters alone, on a network where everything is "up" |
| 6.1 | 6 — IP addressing and IPv6 | `lab06/ip-plan.clab.yml` | /31 and /127 addressing; SLAAC vs DHCPv6; a rogue router advertisement and why RA Guard exists |
| 7.1 | 7 — The transport layer | `lab07/transport.clab.yml` | Predicting throughput from window ÷ RTT; six impairments and the capture signature of each |
| 8.1 | 8 — Network services | `lab08/services.clab.yml` | DHCP relay and `giaddr`; ranking four service failures by how long they stay invisible |
| 9.1 | 9 — A packet's journey | `lab09/journey.clab.yml` | Predicting every header field on every link, then checking yourself against five simultaneous captures |
| 10.1 / 10.2 | 10 — Living on the CLI | `lab10/rosetta.clab.yml` | The same change on three NOSes; cutting off your own access and recovering three ways |
| 11.1 | 11 — VLANs and access | `lab11/vlans.clab.yml` | VLAN isolation across a trunk, and a working double-tagging attack you then close |
| 12.1 | 12 — Spanning tree | `lab12/stp.clab.yml` | Watching a loop self-amplify with STP off, then breaking it and choosing the root |
| 13.1 | 13 — LAG and gateways | `lab13/lag.clab.yml` | Measuring a failover gap with real traffic vs a ping; the single-flow bundle limit |
| 14.1 | 14 — Wireless | (design exercise) | Capacity-vs-coverage arithmetic for a 300-seat theatre, with and without 6 GHz |
| 15.1 | 15 — Access control | `lab15/dot1x.clab.yml` | A real EAP exchange, then spoofing a MAB MAC — and seeing the containment VLAN still hold |
| 16.1 | 16 — Campus architecture | (design exercise) | Producing and defending a low-level campus design for a real site |
| 17.1 | 17 — How a router forwards | `lab17/forwarding.clab.yml` | Per-flow hashing, a single large flow pinning one path, and making two tiers polarise |
| 18.1 | 18 — Static routing | `lab18/static.clab.yml` | A backup that never activates because the middle of the path failed while both interfaces stayed up |
| 19.1 / 19.2 | 19 — OSPF | `lab19/ospf.clab.yml` | Six deliberate faults and their neighbour states; shrinking a branch to totally stubby |
| 20.1 / 20.2 | 20 — IS-IS | `lab20/isis.clab.yml` | Derived system IDs, a narrow-metric router that silently sees nothing, draining with the overload bit |
| 21.1 / 21.2 / 21.3 | 21 — BGP I | `lab21/bgp.clab.yml` | Build iBGP on a pre-converged IS-IS core; break next-hop-self on purpose; make best-path deterministic |
| 22.1 / 22.2 | 22 — BGP policy | `lab22/kestrel-policy.clab.yml` | The Kestrel community scheme end to end, against three misbehaving neighbours; diffing a policy change |
| 23.1 | 23 — VRFs and leaking | `lab23/vrf.clab.yml` | Three customers on identical addresses; shared services as RT membership; leaking a default by accident |
| 24.1 | 24 — Multicast | `lab24/multicast.clab.yml` | Sparse mode with an RP versus SSM, side by side; causing and finding an RPF failure |
| 25.1 | 25 — Anatomy of an ISP | `topologies/kestrel.clab.yml` | Reading a live operator network: roles, blast radius, and where the money is |
| 26.1 / 26.2 | 26 — MPLS foundations | `lab26/mpls.clab.yml` | Building LSPs and finding PHP; then the LDP–IGP sync blackhole and an MTU failure that ping cannot see |
| 27.1 / 27.2 | 27 — Traffic engineering | `lab27/sr.clab.yml` | Migrating LDP to SR in the safe order; steering off the shortest path with explicit and loose segment lists |
| 28.1 | 28 — SRv6 | `lab28/srv6.clab.yml` | Locators as ordinary routable prefixes; measuring the header cost against SR-MPLS |
| 29.1 / 29.2 | 29 — L3VPN | `lab29/l3vpn.clab.yml` | Two labels in the core; hub-and-spoke as route targets; leaking a default by accident |
| 30.1 / 30.2 | 30 — L2VPN and EVPN | `lab30/evpn.clab.yml` | Counting the flooding three ways; ESI, DF election and aliasing; the MAC-move storm from a missing LAG |
| 31.1 | 31 — QoS | `lab31/qos.clab.yml` | Proving QoS does nothing on an idle link, and what happens with no policer on the priority queue |
| 32.1 | 32 — The subscriber edge | `lab32/bng.clab.yml` | RADIUS profiles as the product catalogue; change of authorisation on a live session; sizing by establishment rate |
| 33.1 | 33 — Peering and transit | `lab33/traffic.csv` | 95th percentile on a real month of samples — and discovering the exchange port may not pay for itself |
| 34.1 | 34 — Routing security | `lab34/rpki.clab.yml` | Implementing RFC 6811 yourself, then watching one wrong maxLength bless a hijack |
| 76.1 / 76.2 | 76 — Agents and guardrails | `lab76/agent/` | Building a pre-execution verifier; twelve attacks against your own automation |

Labs 4 to 10 need only free images and run on a laptop. Several use
`nicolaka/netshoot`, which carries `iperf3`, `tcpdump`, `dig` and `tc`.

---

## Path 1 — Containerlab (recommended starting point)

### Install

```bash
# Docker first (Docker Engine on Linux, Docker Desktop elsewhere)
bash -c "$(curl -sL https://get.containerlab.dev)"
containerlab version
```

### Images, and where each comes from

| Image | Pull | Licence |
|---|---|---|
| `ghcr.io/nokia/srlinux` | `docker pull ghcr.io/nokia/srlinux:24.10.1` | Free, no account |
| `quay.io/frrouting/frr` | `docker pull quay.io/frrouting/frr:10.2.1` | Free (GPL) |
| `alpine` | `docker pull alpine:3.20` | Free |
| `docker.io/vyos/vyos` | community builds | Free |
| SONiC | build from `sonic-buildimage`, or a community image | Free |
| Arista cEOS | download from arista.com, then `docker import` | Free **with a registered account** |

Nothing in the free path needs a purchase. Cisco, Huawei, Nokia SR OS,
Juniper and Fortinet images all require an entitlement — those belong to the
GNS3 path.

### Bring up the operator reference network

```bash
cd topologies
sudo containerlab deploy -t kestrel.clab.yml

sudo containerlab inspect -t kestrel.clab.yml     # what is running
ssh admin@clab-kestrel-lon-p-01                   # password: NokiaSrl1!
docker exec -it clab-kestrel-transit-a vtysh      # the FRR nodes

sudo containerlab destroy -t kestrel.clab.yml --cleanup
```

The device configurations in `topologies/configs/` are **generated**, not
hand-written — see `configs/generate.py`. Edit the data table at the top of
that script and re-run it; never edit a `.cfg` file directly. This is the
book's own advice from Chapter 68 applied to its own lab.

### The three reference networks

| File | What it is | Chapters |
|---|---|---|
| `topologies/kestrel.clab.yml` | Kestrel Telecom, AS 64500 — four PoPs, two transits, one IX peer, one customer, one BNG | 20–34, 43–49, 57 |
| `topologies/anvil.clab.yml` | Anvil — two spines, four leaves, EVPN/VXLAN | 35–41 |
| `topologies/aldergate.clab.yml` | Aldergate Group — campus, firewall pair, branch | 11–16, 54–56 |

---

## Path 2 — GNS3

### Install

Follow the GNS3 documentation for your platform, then import the appliances
you are entitled to run. You need the GNS3 GUI **and** the controller (the
GNS3 VM on Windows and macOS).

### Sourcing vendor images, legally

| Vendor | Image | How to obtain it |
|---|---|---|
| Cisco | IOL / IOS-XRv 9000 / CSR1000v / C8000v | Cisco Modeling Labs entitlement, or a Cisco DevNet / partner programme |
| Nokia | SR OS (vSIM) | Nokia customer or partner account |
| Huawei | VRP (NE40E, CE) | Huawei customer account or the Huawei eNSP suite |
| Juniper | vMX / vSRX / cRPD | Juniper vLabs or a customer account |
| Fortinet | FortiGate VM | Fortinet support portal; the free evaluation licence limits throughput but works for every lab in this book |
| Arista | vEOS-lab / cEOS | arista.com, free with registration |

This book does not distribute images and does not link to unofficial mirrors.
If you cannot obtain an image, the Containerlab path covers the same concepts.

### Build a project from a book topology

```bash
cd gns3
cp template-map.example.yml template-map.yml
$EDITOR template-map.yml        # point each node at a template you actually have

python3 gns3_build.py -t ../topologies/kestrel.clab.yml -m template-map.yml --dry-run
python3 gns3_build.py -t ../topologies/kestrel.clab.yml -m template-map.yml \
                      -s http://localhost:3080 -p kestrel
```

`--dry-run` prints every API call without making one. Run it first. The script
checks that every template named in your map exists on the controller before it
creates anything.

Startup configurations are **not** pushed — GNS3 appliances differ too much for
that to be reliable. Apply `topologies/configs/*` by console, or with the
Ansible playbooks from Chapter 69.

---

## Requirements

| Topology | Containerlab | GNS3 |
|---|---|---|
| Chapter labs (2–4 nodes) | 2 GB RAM | 8 GB RAM |
| Kestrel (14 nodes) | 8 GB RAM, 4 cores | 24 GB RAM, 8 cores |
| Anvil (10 nodes) | 6 GB RAM | 16 GB RAM |

If you are short of memory, every topology has a `-lite` variant with the
optional nodes removed. The concepts survive; only the scale is smaller.

## Windows note

Keep this folder somewhere short — `C:\netlab\` rather than a deep path under
Documents. Windows' 260-character path limit will otherwise bite you when a
lab writes a nested output file.
