# Lab 33: compute the counterfactual bill from the samples

Treat `traffic.csv` as **synthetic training traffic**. It supplies 8640 five-minute records for June 2026; no source establishes a real operator measurement. Prices below are hypothetical inputs, not market quotes. Each column is a synthetic offered rate in Mbps in the **same direction towards Kestrel**; this model bills that direction alone. Do not feed it independently selected ingress/egress maxima: such summaries lose the direction information needed to redistribute traffic. A bidirectional contract requires separate vectors transformed before its direction/rank rules are applied.

```bash
python3 test_percentile.py
python3 percentile.py traffic.csv --output scenarios.json
```

The default example uses nearest-rank `ceil(0.95*N)`, zero Mbps commits, GBP 0.06 per Mbps/month, a GBP 1200 monthly exchange cost, and two 100,000-Mbps transit capacities. The 40 calculation checks include small sample ranks, ties, invalid inputs and row shapes, direction aggregation, charge-line rounding, commits, the non-additivity of percentiles and capacity failure. They validate the model, not a real invoice or network.

| Scenario | Operation on every aligned interval |
|---|---|
| Current | Leave the supplied streams unchanged |
| No exchange | Add half of IX to A and half to B, then remove IX charge |
| Additional cache | Multiply both transit streams by 0.85; leave IX unchanged; exclude cache costs |
| B outage | On the day with highest summed A+B demand, add B's offered rate to A and set B to zero; retain the monthly commit charge |

Each scenario is computed **before** each circuit's percentile is taken. Adding the standalone IX percentile to transit percentiles is not an equivalent calculation.

Executed default model results:

| Scenario | GBP/month | Saving vs current |
|---|---:|---:|
| Current | 2347.20 | 0.00 |
| No exchange | 1838.19 | 509.01 |
| Additional cache, before cache costs | 2175.12 | 172.08 |
| B outage on 12 June | 2358.06 | -10.86 |

These amounts exclude taxes, credits, one-off fees, alternative direction rules, delivery loss and contract exceptions. The JSON records every assumption and per-circuit percentile/peak. A capacity failure means the offered-traffic scenario is not feasible without loss: the calculator flags it and does not silently clip rates or pretend to know the resulting invoice.

## Experiments

```bash
# Commit floors and a distinct burst rate
python3 percentile.py traffic.csv --commit-a 8000 --commit-b 8000 \
  --price 0.05 --burst-price 0.08 --output committed.json

# Concentrate no-IX traffic on A and test narrower circuits
python3 percentile.py traffic.csv --ix-split 0.8 \
  --capacity-a 20000 --capacity-b 20000 --output constrained.json

# Change assumed cache benefit and IX fixed cost
python3 percentile.py traffic.csv --cache-fraction 0.25 \
  --ix-cost 800 --output alternative.json
```

1. Explain why a 15 percent rate reduction may produce a different percentage bill reduction with commit floors.
2. Read `hours_strictly_above_p95`. With ties it can be less than 36 hours. Excluded intervals are not an unconditional free-burst allowance.
3. Use the test's 20-interval counterexample to show that a short new event can displace an existing excluded sample into the billable set.
4. Add the actual cache programme's fixed and variable costs to the model result before making a recommendation.
5. For a real invoice, first obtain the contract's direction/rank rules, counters, sample boundaries, missing-data handling, commits, burst prices and credits. Then reconcile a known billed month before relying on scenarios.

The loader rejects negative/nonfinite rates, unordered or missing five-minute intervals, unaligned timestamps and incomplete calendar months. `--allow-partial` is available for a deliberately limited experiment; it does not turn partial data into a monthly bill. Timestamps are UTC interval starts, written without a timezone suffix; no daylight-saving transitions apply. Each circuit and IX charge is rounded half-up to pennies before adding the total. Output keys use `_gbp`; the previous `_usd` names were replaced for this UK budgeting exercise. These are invented GBP inputs, not an exchange-rate conversion of market quotes.

## Fresh execution and data scope

On 17 September 2026, all 8,640 rows passed the strict complete-month loader.
The 40 checks and all four command variants above executed with local Python;
see VALIDATION.md. No real invoice, observed traffic or network failover is implied.
The JSON includes the input SHA256, precise assumptions, offered-rate overload
counts and whether a complete calendar month was required.

Default invoice lines reconcile after per-line rounding. With the stated
8,000-Mbps commits and GBP 0.05/0.08 prices, model totals are GBP 2249.60 current,
GBP 1970.92 no exchange, GBP 2071.01 cache and GBP 2264.08 outage. All four constrained
20-Gb/s scenarios are flagged as infeasible, including the current traffic.
Their offered-rate charges must not be treated as invoices for delivered traffic.

The CSV is retained unchanged as synthetic teaching data. It contains no counter
resets, polling-delay evidence, customer identities or direction measurements.
For real data, calculate rates from counter differences using actual elapsed time,
handle discontinuities, and reconcile a known billing period before forecasting.
