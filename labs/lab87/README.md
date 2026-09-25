# Lab 87.1 — synthetic SLA reporting

Run `python sla_report.py` and `python -m unittest discover -v` (standard library).
No network is contacted and no real contract is evaluated or claim submitted.

Intervals are integer seconds relative to a 30-day UTC-duration window, half-open [a,b).
This is a **complete synthetic event log**: unspecified time is known up by construction.
Do not apply that assumption to incomplete real telemetry. Down and unknown categories
must not overlap; contradictory inputs are rejected. Duplicate/overlapping events of the
same kind are merged. Out-of-window intervals are clipped. Approved exclusions remove
both denominator and relevant numerator duration only under this invented schedule.

Raw down intervals [1000,1900) and [1600,2500) have union 1500 seconds. Exclusion
[1900,2500) leaves 2591400 eligible seconds, 900 bad; unknown [3000,3120) contributes120.
Report lower/upper availability, coverage and exact rational threshold decisions; no
eligible time produces NOT_MEASURABLE. The all-time customer view retains maintenance.

The credit schedule is invented and **is not AWS's schedule**: monthly GBP10000,
availability >=99.99%:0; >=99.9% and below99.99%:10%; >=99% and below99.9%:25%;
below99%:100%. Non-cumulative tiers capped at one fee; all claims assumed accepted.
Same mean99.95%: A has99.95% every month; B has100% with probability.9 and99.5% with.1.
Expected credits1000 versus250 illustrate why mean availability does not determine cost.

23 tests cover interval union, duplicates, clipping, exclusion intersections, unknown
bounds, contradictions, zero denominator, exact boundary classification, month lengths,
burn-rate arithmetic, invalid inputs and credit-distribution normalisation. This does
not validate a production monitoring system, measurement clocks or legal entitlement.
