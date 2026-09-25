# Lab 19 — OSPF evidence, faults and area policy

This IPv4 OSPFv2 exercise targets FRR **10.5.1-1ubuntu4.1**. The configurations
have been exercised with extracted binaries in private Linux network/mount
namespaces. The Containerlab/Docker adapter below has not been executed here.
Commercial NOS, OSPFv3, BFD integration, DR elections, key rotation/replay and
hardware convergence are outside this recorded run. See `VALIDATION.md` for
the final evidence reference and exact scope.

Use an isolated disposable lab. All keys are public teaching data. Never
reuse them in production. The daemons run as root inside these lab containers;
this teaching adapter is not a hardened deployment.

## Topology and baseline

Five links create **five bidirectional Full adjacencies**, ten neighbour-table
rows altogether. Transit interfaces use point-to-point OSPF, cost 40,
Hello/dead 1/4 seconds and key chain LAB19, key ID 19, HMAC-SHA-256.
The timers are a lab choice, not a production recommendation.

| Link | Endpoint A | Endpoint B | Area |
|---|---|---|---|
| Branch A | r-a1 eth1 10.1.1.1/30 | abr1 eth1 10.1.1.2/30 | 1 |
| Direct backbone | abr1 eth2 10.0.0.1/30 | abr2 eth2 10.0.0.2/30 | 0 |
| Backbone via core | abr1 eth3 10.0.0.5/30 | core eth1 10.0.0.6/30 | 0 |
| Backbone via core | abr2 eth3 10.0.0.9/30 | core eth2 10.0.0.10/30 | 0 |
| Branch B | abr2 eth1 10.2.1.1/30 | r-b1 eth1 10.2.1.2/30 | 2 |

Loopbacks/router IDs: abr1 10.255.0.11, abr2 .12, core .13, r-a1 .101,
r-b1 .102, each /32. Backbone loopbacks belong to area 0; each branch
loopback to its branch area. Loopbacks are passive. Interface activation is
used consistently; FRR router-level `network` activation is not mixed in.

Core redistributes **only** its 203.0.113.0/24 discard static, selected by a
prefix-list and route-map. This creates a visible type-5 external in normal
areas. It is not a server prefix that should answer a ping.

FRR 10.5 uses Mbit/s for both `bandwidth 10000` and
`auto-cost reference-bandwidth 400000`. The result is 40, not a 10-Gbit/s
throughput guarantee. Older FRR interface-bandwidth syntax used kbit/s.
Inspect `bandwidthMbit` and `cost` in operational output.

## Containerlab adapter (execution pending)

Requirements: Linux, Docker, Containerlab, capacity for five small FRR
containers, and availability of the pinned Ubuntu package. Record the image
digest and `/netbook-package-versions.txt`. If the package has left the mirror,
use a trusted archived package or explicitly revise and revalidate the version;
do not silently change the pin. From this directory:

```bash
docker build -t netbook-frr:10.5.1 -f ../lab18/Dockerfile.frr ../lab18
sudo containerlab deploy -t ospf.clab.yml
bash start.sh
```

The topology configures Linux links/addresses, then `start.sh` starts zebra,
mgmtd, staticd and ospfd and loads each complete configuration. Do not call
`start.sh` twice against running daemons. Changes are live lab state; destroy
and redeploy to reconstruct baseline. Define these helpers in the same Bash shell:

```bash
v() {
  local node="$1"; shift
  local args=()
  for command in "$@"; do args+=(-c "$command"); done
  docker exec "clab-lab19-$node" vtysh "${args[@]}"
}
c() {
  local node="$1"; shift
  v "$node" 'configure terminal' "$@" 'end'
}
for node in abr1 abr2 core r-a1 r-b1; do
  v "$node" 'show ip ospf neighbor json' 'show ip ospf interface json'
  v "$node" 'show ip ospf database json' 'show ip route json'
done
docker exec clab-lab19-r-a1 ping -n -c 5 -I 10.255.0.101 10.255.0.102
```

Expected neighbour counts: 3, 3, 2, 1, 1 respectively, all Full. Check the
OSPF `networkType` field; Linux Ethernet media may still be described as
broadcast elsewhere. Confirm ten transit costs of 40, loopback routes and
source-specific branch delivery. Allow database/flooding/SPF work to finish:
Full alone is not the service-recovery criterion. Record each stage's time.

## 19.1 — One change at a time

Save effective configuration, neighbour/interface state, relevant LSA
instances and routes. Capture packets where required. Restore **all five
adjacencies stably for at least five seconds and source-specific branch
delivery** before the next case. This five-second observation is a small-lab
acceptance window, not proof of long-term stability.

### MTU field mismatch

Start capture in a second terminal and stop it with Ctrl-C after the test:

```bash
docker exec -it clab-lab19-abr1 tcpdump -n -vvv -s 0 -i eth2 'ip proto 89'
```

In the first terminal:

```bash
docker exec clab-lab19-abr1 ip link set eth2 mtu 1400
v abr1 'clear ip ospf neighbor 10.255.0.12'
v abr1 'show ip ospf neighbor json' 'show ip ospf interface json'
v abr2 'show ip ospf neighbor json'
# Restore, then wait for stable Full AND delivery:
docker exec clab-lab19-abr1 ip link set eth2 mtu 1500
v abr1 'clear ip ospf neighbor 10.255.0.12'
```

Observe DBDs advertising 1400 and 1500 and compare actual packet lengths.
A small received DBD can be rejected because of its advertised MTU. Do not
infer a large-packet drop from ExStart alone. A decoder may label type 2 as
“MD5” even with a 32-byte HMAC-SHA-256 digest: type 2 is the cryptographic
authentication container, not sufficient evidence of the algorithm. Check
operational key-chain configuration.

### Hello interval mismatch

```bash
c abr1 'interface eth2' 'ip ospf hello-interval 2'
# Wait beyond four-second dead interval; compare both peers and Hellos.
v abr2 'show ip ospf neighbor json'
c abr1 'interface eth2' 'ip ospf hello-interval 1'
```

Expect the target adjacency to fail. An immediate display can retain stale
Full state until timeout. Other backbone adjacencies need not fail.

### Duplicate router ID

```bash
c abr2 'router ospf' 'ospf router-id 10.255.0.11'
v abr2 'clear ip ospf process'
v abr1 'show ip ospf neighbor json' 'show ip ospf database json'
v abr2 'show ip ospf neighbor json' 'show ip ospf database json'
v core 'show ip ospf neighbor json' 'show ip ospf database json'
# Restore the unique ID and restart this disposable OSPF process:
c abr2 'router ospf' 'ospf router-id 10.255.0.12'
v abr2 'clear ip ospf process'
```

The loopback remains .12 while the effective ID changes. Collect logs and
LSA identity/sequence evidence. Do not require one universal state signature:
duplicate IDs can cause several conflicting effects. Process clear is an
isolated experiment here, not default production troubleshooting.

### Area capability mismatch

```bash
c abr2 'router ospf' 'area 2 stub'
# r-b1 remains normal: inspect lost adjacency and Hello options.
v r-b1 'show ip ospf neighbor json'
c abr2 'router ospf' 'no area 2 stub'
```

This changes area capability at one end, not its numeric area ID. Wait for
route/service recovery after restoring matching normal areas.

### Wrong authentication key on one interface

```bash
c abr1 'key chain WRONG' 'key 19' \
  'key-string LAB19-INTENTIONAL-WRONG-KEY' \
  'cryptographic-algorithm hmac-sha-256' 'exit' 'exit' \
  'interface eth2' 'ip ospf authentication key-chain WRONG'
# Wait beyond dead interval; inspect abr2's missing target adjacency.
v abr2 'show ip ospf neighbor json'
c abr1 'interface eth2' 'ip ospf authentication key-chain LAB19'
```

A separate chain isolates the wrong key to eth2. Editing the shared LAB19
key affects every referencing interface. Distinguish received-but-rejected
packets from loss. Matching keys do not prove rotation or replay protection.

### Different reference bandwidth: an adjacency counterexample

```bash
c core 'router ospf' 'auto-cost reference-bandwidth 100'
v core 'show ip ospf interface json' 'show ip ospf neighbor json'
for node in abr1 abr2 core; do
  v "$node" 'show ip ospf database router json'
done
c core 'router ospf' 'auto-cost reference-bandwidth 400000'
```

All five adjacencies remain Full. Core's outgoing transit costs become one;
ABR costs towards it remain 40. Compare core's area-0 Router LSA across all
three observers: sequence/checksum and link contents should converge, while
ages may differ. Receivers do not reinterpret costs with their local reference.
Restore cost 40 and delivery. This is not an adjacency-formation fault.

## 19.2 — Normal, stub and summary suppression

Save the branch JSON database at each converged stage. Count semantic LSA
records, not display lines. The helper excludes reported MaxAge records.

```bash
v r-b1 'show ip ospf database json' > normal.json
python3 count-lsas.py normal.json
c abr2 'router ospf' 'area 2 stub'
c r-b1 'router ospf' 'area 2 stub'
# Wait for stable adjacency, routes and successful delivery.
v r-b1 'show ip ospf database json' > stub-live-before-reset.json
v r-b1 'show ip route json' > stub-live-before-reset-routes.json
# Explicit disruptive reset of this isolated branch, then reconverge:
v r-b1 'clear ip ospf process'
v r-b1 'show ip ospf database json' > stub.json
python3 count-lsas.py stub.json
c abr2 'router ospf' 'area 2 stub no-summary'
v r-b1 'show ip ospf database json' > suppression-live-before-reset.json
# Explicit disruptive recalculation on this isolated ABR, then reconverge:
v abr2 'clear ip ospf process'
# Wait for stable adjacencies/delivery and old summaries to be flushed.
v r-b1 'show ip ospf database json' > total-stub.json
python3 count-lsas.py total-stub.json
```

Normal area 2 has two Router LSAs, inter-area summaries, an ASBR summary and
the external discard prefix. Stub removes type 5 and the ASBR summary while
retaining inter-area summaries plus a type-3 default. Summary suppression
leaves local Router LSAs and just the default summary. Record counts and
identities. These are not memory/CPU benchmarks or evidence of scale.

In the recorded FRR10.5.1 live conversion, an old type-5 record remained in
the branch AS-scoped database after conversion to stub, while its explicit
external route was absent. A type-4 record at age 3600 was pending removal.
Applying no-summary did not remove the old non-default summaries within the
observed 45-second window. The explicit resets above separate these retained
states from fresh process behaviour. They are disruptive teaching steps;
they do not demonstrate a non-disruptive production migration. Preserve the
before-reset evidence and check actual routes as well as database records.

```bash
docker exec clab-lab19-abr1 ip link set eth3 down
# Allow convergence: the direct abr1--abr2 path remains.
v r-b1 'show ip ospf database json' 'show ip route json'
docker exec clab-lab19-r-b1 ping -n -c 5 -I 10.255.0.102 10.255.0.101
docker exec clab-lab19-abr1 ip link set eth3 up
# Restore all adjacencies and delivery, then fail the sole branch exit.
docker exec clab-lab19-abr2 ip link set eth1 down
# After detection/calculation, default and remote delivery should be lost.
v r-b1 'show ip route json'
docker exec clab-lab19-r-b1 ping -n -c 5 -I 10.255.0.102 10.255.0.101
docker exec clab-lab19-abr2 ip link set eth1 up
# Verify stable Full, default reinstallation and successful delivery.
c abr2 'router ospf' 'no area 2 stub'
c r-b1 'router ospf' 'no area 2 stub'
v r-b1 'show ip ospf database json' > normal-rollback-before-reset.json
v abr2 'clear ip ospf process'
v r-b1 'clear ip ospf process'
# Wait for stable Full, the external advertisement and successful delivery.
```

Restore normal-area external propagation and service. When finished:

```bash
sudo containerlab destroy -t ospf.clab.yml --cleanup
```

## Submission and extension

Submit baseline/fault/recovery evidence with timestamps, effective settings,
neighbours, relevant LSAs, route changes, delivery and limitations. Separate
detection time from first successful packet. Explain why Full can precede
service recovery and why 2-Way DROthers on a broadcast LAN can be healthy.

A commercial adapter must specify product, release, hardware, CLI mode,
instance/VRF, addresses, reference units, cost overrides, authentication,
timers and commit/save/rollback. Repeat the acceptance observations. FRR
syntax is not interchangeable with IOS XE/XR, SR OS/SR Linux, VRP, EOS or FortiOS.

Sources: [FRR 10.5 OSPF](https://docs.frrouting.org/en/stable-10.5/ospfd.html),
[Zebra units](https://docs.frrouting.org/en/stable-10.5/zebra.html),
[RFC 2328](https://www.rfc-editor.org/rfc/rfc2328.html),
[RFC 5709](https://www.rfc-editor.org/rfc/rfc5709.html) and
[RFC 7474](https://www.rfc-editor.org/rfc/rfc7474.html).
