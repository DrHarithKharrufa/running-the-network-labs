# Lab 82.1 — Scaling worksheet, revision teaching-v1

```console
python scaling.py
python -m unittest discover -v
```

Python 3 standard library. All resource, workload, time and staffing numbers are
invented teaching inputs. The session counts are graph arithmetic. No device scale,
forwarding, protocol timing, real incident rate or staffing sufficiency is measured.
The 18 tests check these calculations and their boundaries. Production combined-scale
and tail-restoration fields deliberately remain `NOT_RUN`.

- Two RRs are included in the total node count. Every other node peers with both;
  the RRs peer with each other; clients do not peer with each other. The reduced
  total does not reduce the RR's maximum session count or prove its path capacity.
- The hypothetical table holds 100,000 units: IPv4 uses one unit and IPv6 two. The
  planning ceiling is 80,000. At 40,000 IPv4 and 10,000 IPv6 prefixes, usage is
  60,000; proportional 1.5× growth gives 90,000. This crosses the planning ceiling
  before the invented physical limit. It is not a Cisco or Nokia capacity model.
- The fluid backlog model has constant arrival/service rates within each phase,
  unlimited queue, no loss, coalescing or priority, and no feedback. A 20-second
  burst at 2,500 units/s served at 2,000/s leaves 10,000 units. At 1,000 arrivals/s
  afterwards, drainage takes 10 seconds. This is not a measured convergence time.
- Four people × 37.5 hours minus 30 aggregate hours unavailable = 120 hours. Normal
  workload totals 114; doubling incidents yields 138. These totals cannot prove
  simultaneous skill coverage, sustainable on-call, legal compliance or shift cover.
- A hypothetical 64-port spine with four other uses and four reserved ports has 56
  leaf-facing ports. One/two links to each leaf allows 56/28 leaves. Link speeds,
  supported breakouts, oversubscription and the rest of the topology still matter.
- Four independent 100-Gbit/s uplinks provide 400 nominal Gbit/s, or 300 after one
  spine loss. Demand 320 then exceeds aggregate capacity even before hashing/skew.

## Carry the model into a real scaling record

For every resource record exact SKU/ASIC/line card/NOS release, feature/profile,
published combined limit and source revision, observed current usage, peak/migration
overlap, planning margin, forecast, trigger, owner and procurement/migration lead time.
An individual data-sheet maximum is not proof that every maximum works concurrently.

Record a test matrix with scale, feature mix, traffic and churn, failed component,
measurement method and repetitions. Measure both normal and tail restoration, loss,
resource high-water marks, alarms and recovery after exhaustion. Preserve the raw
evidence and mark untested cells `NOT_RUN`; do not convert this worksheet's pass into
a product-scale pass. Real NOS/hardware scale validation is pending for this chapter.
