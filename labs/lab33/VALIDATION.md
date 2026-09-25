# Lab33 calculation validation — 17 September 2026

Evidence: `work/publication/full-review/model-evidence/lab33-20260917T100327Z`.
Local Python only; no network execution, commercial invoice, observed market
price or real traffic dataset is claimed. Exact calculator/tests/CSV, source
hashes, command output, interpreter version and scenario JSON are retained.

40 checks passed. They cover ranks/ties, invalid rates, commit/burst arithmetic,
non-additivity, short-event displacement, direction-aggregation differences,
per-line rounding reconciliation, malformed CSV fields, duplicates/gaps,
timestamp alignment, timezone suffix rejection and explicit partial-month mode.
All8,640 UTC interval-start rows of June2026 passed the complete-month loader.
Default, committed, constrained and alternative CLI scenarios executed.

Default GBP model:2347.20 /1838.19 /2175.12 /2358.06 (current/noIX/cache/outage).
Committed:2249.60 /1970.92 /2071.01 /2264.08.
Constrained20Gb/s: all four scenarios exceed at least one capacity. These are
offered rates; the model does not calculate dropped traffic or its invoice.
Alternative25% cache andGBP800 IX:1947.20 /1838.19 /1660.40 /1958.06.

All prices are hypothetical GBP inputs. The previous revision's USD example
has been reframed for UK budgeting without making a currency-conversion claim.
Separate directional/counter data, tax/credit clauses, real capacity/traffic
redistribution and cache costs require a different, evidence-based input model.
