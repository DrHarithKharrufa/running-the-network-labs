# Lab 65: change decisions and their evidence

These are new offline teaching models. Chapter 65 originally supplied no lab.
They need only Python 3.10 or newer and the standard library; no privileges,
network, vendor image or device is used. Run from this directory:

```
python change_gate.py
python recovery_budget.py
python blast_radius.py
python -m unittest -v test_change_models
```

`change_gate.py` distinguishes PASS, FAIL and UNKNOWN for declared synthetic
observations. Both FAIL and UNKNOWN prevent progression. It intentionally checks
only required-route presence, not every unexpected route: extend the contract when
that matters. The fixture's artefact IDs are labels, not cryptographic hashes.
Times are synthetic monotonic seconds; `age_s` is freshness at each capture.
Boot and counter epoch must identify a continuous counter. Reset/wrap/discontinuity
requires a new baseline. The example thresholds are not production recommendations.
The model trusts the supplied observations and is not an operational collector,
approval system or production release controller.

`recovery_budget.py` subtracts the decision, recovery, verification and contingency
reserves from the window. Its inputs must be justified timing bounds, not unqualified
averages. It cannot establish that a recovery route works. The worked 120-minute
window reserves 40 minutes and reaches its decision deadline at minute 80. A
15-minute stage fits at minute 65; a 16-minute stage does not. Recovery at minute
110 overruns the full budget by 30 minutes.

`blast_radius.py` follows possible propagation across a declared graph. In the
fixture, 40 edges and two route reflectors serve 40 disjoint populations of 1,000.
One edge exposes 1,000; a shared reflector can expose all 40,000. Restricting its
outgoing graph edges is an ASSUMPTION about an independently verified containment
control, not a router configuration applied by the model. Reachability is potential
exposure, not measured outage. No routing selection, redundant-path logic, packet
forwarding or probability of failure is simulated. Incomplete maps can understate
exposure, and overlapping real customer populations must not be summed as disjoint.

All three models have counterexamples and boundary tests. The tests deliberately
exercise absent data, stale collectors, resets, non-finite numbers, target mismatch,
an unchanged route count hiding a missing service, deadlines, unknown nodes, cycles
and duplicate propagation paths. Passing them establishes only offline code behaviour.
