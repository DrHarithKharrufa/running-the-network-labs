# Lab 35.1 — A fabric's shape is arithmetic

Chapter 35 argues that a Clos fabric is designed, not guessed: the switch radix,
the physical cage budget and the oversubscription the workload needs together
decide how many servers a hall holds. This lab makes that arithmetic runnable.

**Scope.** These are offline calculators. They compute capacity, port and cage
budgets. They execute no device, no Containerlab topology and no ASIC, and they
predict no achieved throughput. Nothing here is a hardware bill of materials, a
redundant host design, or a performance guarantee for a training cluster.

```bash
python3 fabric_sizer.py          # prints the worked examples as JSON
python3 test_fabric_sizer.py     # 64 offline checks; exits non-zero on failure
```

## What the model enforces

The calculator refuses designs the prose used to describe. In particular the
complete, equally provisioned model requires the uplink count to divide evenly
among the spines. This is a model assumption, not a universal routing law:

```python
>>> size(48, 25, 2, 100, 8)        # 2 uplinks, 8 spines
ValueError: Uplink count must be a positive multiple of spine count
>>> size(48, 25, 8, 100, 8)['links_per_spine']
1
```

A leaf with two uplinks cannot reach eight distinct spines, however correct its
bandwidth ratio looks. Bandwidth and link count are separate constraints.

It also refuses designs that exceed the physical cage budget, and counts cages
separately from logical ports, because a cage spent on uplinks cannot carry
servers and every breakout mode must be qualified on the real platform.

## The Anvil hall

`anvil_hall()` encodes the one-hall sizing worked through in the chapter: 8
spines and 32 leaves serving single-homed servers — 20 general, 4 storage, 8 GPU service —
carrying 256 logical fabric links and 608 server interfaces, of which 64 are the
GPU nodes named in the front-matter reference network.

For a general leaf it reports:

```
down_bw_gbps               600      24 x 25 Gb/s of servers
up_bw_gbps                 200      8 x 25 Gb/s, one link per spine
oversubscription           3.0      the designed 3:1
links_per_spine            1
remaining_up_gbps          175      after one spine of eight is lost
failure_oversubscription   3.4286   24:7
one_uplink_cage_loss_ratio 6.0      losing one 4x25 breakout cage
```

The last two lines are the point of the exercise. Losing a whole spine degrades
the leaf from 3:1 to 24:7. Losing a single breakout **cage** — four uplinks that
share one physical port, optic and fan-out cable — degrades it to 6:1, which is
markedly worse. Storage behaves the same way (2:1 → 16:7 on a spine loss, 4:1 on
a cage loss). The GPU leaves, whose uplinks are native one-per-cage, degrade to
8:7 either way.

If you quote only the spine-loss figure, you have quoted the kinder failure.

## The design questions this encodes

- **Oversubscription is a workload decision.** 1:1 at the leaf uplink for a
  back-end carrying synchronised collectives; ~3:1 for general compute; 2:1 for
  storage. Pick it from the workload, then size to it.
- **Radix and cages set hall size.** Downlink cages set servers-per-leaf; uplink
  cages set how many spines you can spread across and at what width.
- **1:1 at the leaf is necessary, not sufficient**, for a GPU back-end. NIC
  count, rail assignment and collective topology decide the result — Chapter 41,
  not this one.
- **You grow by adding spines** (Lab 36.1), which adds capacity and ECMP width
  when leaves have spare uplink capacity and new links are installed to every
  leaf. Spine radix separately limits the number of leaves.

## The shipped topology is smaller than the hall you sized

```bash
sudo containerlab deploy -t ../topologies/anvil.clab.yml
```

That inventory is **two spines and four leaves, SR Linux on every node**, and it
ships with **no underlay or overlay configuration**. It is a shape to inspect,
not a routed fabric: equal-cost paths are only observable once Chapter 36 builds
the underlay and Chapter 37 the overlay. It is deliberately not the 8-spine hall
sized above, and it is not a qualified multi-vendor deployment.

## Make it yours

Change the pool definitions in `anvil_hall()`, or call `uniform_fabric()` with
your own radix, cage budget and breakout modes. Try to build a 3:1 general leaf
against 8 spines using native 100 Gb/s uplinks and watch the cage budget, not
the bandwidth, become the binding constraint.

## September 2026 correction

The 4,000-server example now implements the exercise's 3:1 requirement: 84 leaves, four 100 Gb/s uplinks per leaf and four spines. The earlier six-uplink example gave 2:1. This is a corrected arithmetic example, not a new fabric execution.
