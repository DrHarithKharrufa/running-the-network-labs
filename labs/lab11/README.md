# Lab 11 — VLAN classification, isolation and a bounded tag experiment

This is an isolated Linux bridge lab. It does not establish commercial-switch
tag handling or implement DTP. Build `netbook-services:20260916` from ../common
before deploying. Record the resulting image ID, package versions, kernel and
Containerlab version. Image build and Containerlab execution need their own
validation; the namespace evidence is a separate test of Linux behaviour.

Each bridge starts with `vlan_default_pvid 0`: no implicit VLAN 1 membership.
eth1 is untagged VLAN 110, eth2 untagged VLAN 120, and eth3 admits tagged
110/120. At baseline the node named attacker is an ordinary VLAN-120 endpoint;
the name does not give it native-VLAN membership. There is one inter-switch
link and no L2 loop. Management interfaces are outside these bridges.

```sh
docker build -t netbook-services:20260916 ../common
sudo containerlab deploy -t vlans.clab.yml
docker exec clab-lab11-sw1 bridge -d vlan show
docker exec clab-lab11-sw2 bridge -d vlan show
docker exec clab-lab11-h1-v110 ping -I 10.10.0.11 -c 3 -W 1 10.10.0.13
docker exec clab-lab11-attacker ping -I 10.10.4.99 -c 3 -W 1 10.10.4.12
```

Remove VLAN 110 from sw1 eth3, require the first test to fail, then restore it
with `bridge vlan add dev eth3 vid 110` and require recovery. Keep VLAN 120's
working test as a control. Save bridge state and FDB output for the diagnosis.
Destroy the lab even after a failed test; do not leave the test state active.

## Prove a layer-2 boundary

In terminal 1 run the finite receiver below; wait for READY. In terminal 2 send
the matching token from h1-v110. The sender emits only three short broadcast
frames using experimental EtherType 0x88b5. It neither scans nor starts a flood.

```sh
# Terminal 1
docker exec clab-lab11-h2-v120 python3 /lab/frame_probe.py receive eth1 NBK-LAB11-ISOLATION
# Terminal 2, after READY
docker exec clab-lab11-h1-v110 python3 /lab/frame_probe.py send eth1 NBK-LAB11-ISOLATION
```

The receiver must report zero matching frames. Repeat with a new token and the
sender `attacker`, on the same VLAN as h2-v120: the receiver must report delivery.
Without that positive control, a broken sender/receiver could look like isolation.
A failed ping to another subnet, without a route, is not evidence of L2 filtering.

## Observe double tagging under explicit preconditions

Start from the verified baseline. `bash tag-mode.sh experiment` moves sw2 eth2
from VLAN 120 to untagged VLAN 1 and permits VLAN 1 untagged on both trunks.
It leaves the legitimate 110/120 memberships in place. Save before/after state.
The attacker's old IPv4 address is irrelevant to this raw Ethernet experiment;
no ARP resolution or reply route is assumed.

Capture both trunk directions and h2-v120 with a finite five-second tcpdump run
before sending. Use `-e -nn -s 256 -c 100`, interface eth3 on switches and eth1
on the receiver. An unfiltered short capture avoids missing a frame because a
BPF `vlan` expression assumes the wrong tag depth. Offloads can expose tags as
metadata; record offload state and compare endpoint receipt with trunk capture.

```sh
bash tag-mode.sh experiment
# Terminal 1
docker exec clab-lab11-h2-v120 python3 /lab/frame_probe.py receive eth1 NBK-LAB11-DOUBLE
# Terminal 2, after READY: outer native tag 1, inner target tag 120
docker exec clab-lab11-attacker python3 /lab/frame_probe.py send eth1 NBK-LAB11-DOUBLE 1 120
```

Record the observed result. If delivery occurs, identify which wire carries
which tag and why the receiver gets the marked frame. If it does not occur,
locate the rejection; do not claim a successful attack from the diagram alone.
Either outcome is specific to the tested implementation. Receipt proves a
one-way frame path, not a bidirectional IP connection or application exploit.

Run `bash tag-mode.sh restore`. The same double-tagged probe must now fail to
reach h2-v120, while ordinary VLAN-120 traffic and the VLAN-110 cross-trunk
baseline must pass. Inspect both bridges for absence of VLAN 1 membership.
Retain receiver JSON, captures, state and failed attempts, then destroy only
this topology with `sudo containerlab destroy -t vlans.clab.yml`.

Reference: https://docs.kernel.org/networking/bridge.html. Actual run evidence
and remaining validation are tracked in the publication resolution ledger.
