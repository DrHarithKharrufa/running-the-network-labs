# Lab 77.1 — Bounded intent assurance

Run with Python 3.12+; standard library only:

```sh
python assurance.py
python -m unittest discover -v
python assurance.py --demo-original
```

The original is preserved byte-for-byte in `assurance_original.py.txt` for comparison. Its printed claims of alerts/remediation did not execute those actions. Its `> 50` check also admitted exactly 50 despite a strict sub-50 description.

## Contract

The exercise consumes **constructed evidence** for LON-probe to MAN-probe, the interactive class, a 300-second window and 300 RTT samples. It calculates nearest-rank p95 (`ceil(.95*n)` in one-based order) and requires **strictly less than 50 ms** in normal operation. It does not calculate one-way delay, packet loss or a confidence interval; a p95 target allows some slower samples. In a live collector, a missing probe needs explicit loss/timeout treatment; this example refuses an incomplete sample set.

Two paths of 100 Gbit/s each are modelled as an ideal, fully redistributable pool. Demand is 60 Gbit/s and the inclusive utilisation ceiling is 70%. Normal usable capacity is 140 Gbit/s; either surviving path provides 70. Each single named path failure and each single declared shared-risk link group (SRLG) is checked. A common duct removes both paths even though the active path count was two. Replacing one path by 50 Gbit/s leaves only 35 usable after loss of the other. This is arithmetic, not validation of ECMP distribution, queues, forwarding, convergence or unrecorded shared dependencies. The completeness flag is a supplied assertion, not an audit of physical diversity.

Restoration time is a **different measurement** from RTT. Each fault key needs a nonempty list of supplied restoration trials, all strictly below 50 ms. These lab trial values are synthetic; this program executes no fault. It checks matching topology revision and an inclusive maximum age of one day. Revision is not authentication and does not bind actual device state. Extra trial keys do not expand the required fault set. No simultaneous independent multiple-fault guarantee follows from these checks.

Snapshot age must lie in [0,60] seconds at the supplied clock, inclusive. Wrong target/class, missing or invalid fields, non-finite numbers, booleans masquerading as measurements, stale/future records and an incomplete SRLG map return UNKNOWN. Bad intent/clock raises ValueError. Valid snapshots with a known breach return VIOLATED even when some trial evidence is unknown; both lists are retained. MET requires all checks to pass **within this declared model and supplied evidence**. It is not a present-time network certificate.

The demo yields MET for the normal fixture, VIOLATED for a down path, common duct, small survivor, RTT equal to 50 and restoration equal to 50, and UNKNOWN for stale evidence. Configuration is not compared or changed. Tests cover exact boundaries, nearest-rank tails, fault capacity, missing evidence and malformed inputs.

## Transfer to an actual network

Write a separately authorised measurement plan: endpoints/direction, packet size and DSCP, offered load, cadence, timeout/loss treatment, synchronisation/clock uncertainty, SRLG inventory provenance, topology/configuration revision, fault injection point, restoration definition, number of trials and confidence/coverage limits. Define restoration as a repeatable packet-service criterion, not merely an adjacency becoming up. Test permitted single faults under representative demand; separately test controller/collector failure and misleading telemetry. Compare the real measurements with this checker only after building and validating the collector/schema adapter. There is no network, device, alert sender, remediation actuator, autonomous controller or TM Forum assessment in this lab.
