# Lab 37 — the Anvil overlay

Two parts, separated by what each can establish.

| | What it does | What it proves |
|---|---|---|
| 37.1 `evpn_plan.py` | Builds a route-target **membership plan** from a tenant definition and reports one-way relationships, orphaned targets and mutual cross-tenant paths | Membership relationships implied by this input **model** |
| 37.2 `overlay_lab.py` | Runs an EVPN control plane and a Linux VXLAN data plane on the Chapter 36 underlay, with two tenants and four hosts | What BGP, the bridge and the traffic **actually did**, on this host, on this run |

Neither runs Containerlab, a commercial NOS or an ASIC. Neither measures
throughput, and neither builds symmetric IRB.

## Lab 37.1 — the route-membership plan

```bash
python3 evpn_plan.py            # human-readable
python3 evpn_plan.py --json     # the analysis as JSON
python3 test_evpn_plan.py       # 28 checks, exit 0
```

The plan holds six services: two bridge domains and an IP-VRF for tenant *red*,
one bridge domain and an IP-VRF for *blue*, and a shared-services VRF that both
tenants import from and that imports from neither. Imports and exports are stated
**separately** for every service, which is the whole point — a one-way
relationship cannot be represented any other way, and one-way relationships are
where the interesting mistakes live.

**Why this version exists.** The previous script derived the route target from
the VNI, then declared two servers reachable if they shared a VNI *and* a route
target. Since the target came from the VNI, that test could only ever agree with
itself; it would have reported a perfect plan for any input. It also called its
output "reachability", which it was not.

The checks feed it mismatched imports and exports on purpose: add a single import
to `blue-vrf` and the analysis must newly report that blue learns red's routes,
one way. Mistype a target and it must become an error rather than a silent no-op.

**What it does not tell you.** Not reachability — no traffic exists here. Not
security policy — route targets decide what a VRF *learns*, not what a workload
may do with it. And not what the devices are actually doing: see D1 below.

## Lab 37.2 — the overlay, running

Needs root, `iproute2` (with `bridge`) and FRR (`zebra`, `bgpd`, `vtysh`).

```bash
sudo python3 overlay_lab.py
```

Two spines, four leaves, two tenants and four hosts in Linux network namespaces.
Tenants *red* and *blue* deliberately use **the same subnet and the same host
addresses** — if isolation failed, the collision would be immediate and obvious.

- **A — the control plane crosses the fabric.** leaf-03 receives EVPN type-3
  routes from the remote leaves, and the next hop is the **originating leaf's
  loopback**, not the spine. An eBGP spine that rewrote the next hop would leave
  every VTEP trying to tunnel to a switch that is not a VTEP.
- **B — same tenant, different racks.** `h-red-a` reaches `h-red-b`; the remote
  MAC is in the VXLAN forwarding database against leaf-03's loopback and marked
  `extern_learn`, not learned by flooding.
- **C — isolation, with colliding addresses.** The blue tenant works identically
  on the same addresses; the red VTEP never learns a blue MAC and vice versa; and
  `h-red-a`'s ARP entry for `.12` holds the **red** MAC.
- **D — route-target observations.** Check the exact four automatically
  advertised targets and same-tenant forwarding, then the two explicit targets
  `64500:10010` and `64500:10020`. Record explicit-target forwarding and both
  zebra and BGP VNI state. Different export targets alone do not prove the
  cause of successful import or all tenant-isolation properties.
- **E — configured MTU boundary.** The underlay is 1500 and the VXLAN,
  bridge and host interfaces are explicitly 1450. A 1422-byte DF-marked ICMP
  payload crosses; 1423 does not. The local 1450-byte limit already enforces
  this threshold. It is not an isolated measurement of the underlay's path MTU,
  outer fragmentation or the dropping hop. Raising both underlay to 9000 and
  inner interfaces to 8950 permits a 1472-byte payload, but changes two variables.
- **F — a MAC moves.** Check local learning and restored connectivity; record
  a post-learning FDB snapshot. Poll elapsed time is not packet loss duration.

The revised harness passed **21/21 checks, with two additional observations**
on 24 September 2026 UTC using FRR 10.5.1 and Linux
6.18.33.2-microsoft-standard-WSL2. Results go to `lab37-results.json`.
The qualification adapter used uniquely owned network namespaces and private
mount namespaces with retained FRR binaries. It captured requested/running
configs, daemon logs and command results before owned cleanup.

### Historical observations and limits

In the fresh run, explicit targets forwarded and no stale remote FDB entry was
present in the snapshot after local learning. The earlier FRR 8.4.4 harness
recorded non-forwarding with explicit targets and a local/remote entry pair after
a move. These are different releases, hosts and harnesses: no single-variable
comparison establishes a cause. The earlier snapshot does not establish why the
entry persisted or prove that traffic remained correct continuously.

## Not tested, and therefore not claimed

- **Symmetric IRB.** No IP-VRF, no L3 VNI and no router MAC is configured. Nothing
  in this book demonstrates symmetric IRB working.
- EVPN multi-homing (route types 1 and 4) and any ESI behaviour.
- Data centre interconnect of any kind. The second lab in the chapter is a design
  exercise on paper, and says so.
- Containerlab, commercial NOS, ASIC behaviour and throughput.
- Anything about a platform other than this Linux kernel and this FRR build.

## The shipped Containerlab inventory

`../topologies/anvil.clab.yml` is an inventory of six SR Linux nodes and four
hosts with **no** startup configuration. Deploying it gives you devices, not a
fabric, and no run of it is recorded anywhere in this book.

## Instrumentation checks and retained evidence

`../test_frr_harness_audit.py` contains 16 offline tests of invalid/empty CLI,
malformed JSON, wrong peers, FIB filtering, FDB row association and owned cleanup.
Mocks check the test instrumentation; they are not device or forwarding tests.
The qualification record stores the executed source hash and environment adapter.
Use the edition's evidence catalogue to locate that record; future reruns must
record their own environment, source hash, commands, failures and cleanup.
