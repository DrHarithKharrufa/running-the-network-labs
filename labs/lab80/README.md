# Lab80 — Availability with explicit assumptions

Run with Python 3.12; standard library only:

```sh
python availability_math.py
python -m unittest -v test_availability.py
```

This is a mathematical worksheet, not a failover benchmark or SLA prediction.
Series/parallel products assume independent component states. In the common-hazard
example, `common_mode=c` is the fraction/probability of a common outage at an observation
time, and `path_avail` is conditional on that outage being absent. Then
`A=(1-c)*(1-(1-a)**n)`. Compare a single path and a pair under the SAME common hazard;
adding a hazard only to the pair is not a fair measure of redundancy benefit.

The r-out-of-n model assumes identical independent units and that any required units
can serve demand. The capacity worksheet is deterministic and says nothing about
switching success, traffic distribution or common dependencies.

For demand100 and four50-unit resources in two complete100-unit sets, taking one
entire set down leaves100capacity with zero spare margin. One more unit failure
leaves50and fails demand. This is why2N alone does not preserve full redundancy
during whole-set maintenance. Model switching/distribution paths separately.

The calendar basis is 365 days. Five nines allows 5.256 minutes in that period.
The 24 unit tests include the 13 incoming checks, re-executed before amendment.
They cover numerical examples, probability boundaries, common-event weighting,
maintenance plus failure, every downtime-table entry and consistent time units.
Independent exact rational calculations check small binomial cases; a symmetric
large case checks numerical evaluation without huge binomial coefficients.

`observed_bounds(50,2,8)` gives lower availability 83.333%, upper 96.667%, unknown
fraction 13.333%, and observed-only usable fraction 96.154%. The units must match.
The last result excludes unknown intervals and is not the whole eligible-period
availability. All-unknown data gives [0,1] and an undefined observed-only result.
These bounds do not select the treatment required by a particular SLA.

The functions reject booleans, non-finite/negative numbers, invalid failed-unit
indices and non-integral/out-of-range counts. Unit counts are bounded to 1–10,000
for this worksheet. Very large duration ratios are scaled before division;
parallel probability uses log1p/expm1 and binomial terms use log-gamma plus fsum.
Aggregate/output overflow is rejected. Floating-point results are approximations:
extreme tails can round or underflow; this is not arbitrary-precision analysis.

Extend the exercise with a service failure-mode table: fault, affected traffic,
expected recovery, survivor capacity, shared dependencies, measurement point,
abort condition and owner. Real fault injection needs its own approved procedure;
this script never changes a network.
