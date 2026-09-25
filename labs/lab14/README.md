# Lab 14 — a capacity bound that can be checked

This is arithmetic with assumed inputs, not an RF emulator or a site survey.
Use Python 3, with no third-party modules:

```sh
python3 airtime.py
python3 airtime.py --activity-multiplier 2
```

The model.json populations, rates, activity, band eligibility and useful
capacities reproduce Chapter 14. Rates combine upstream/downstream payload.
Capacity already includes the assumed protocol efficiency; do not subtract
the same overhead again. The 60% budget reserves additional room for load
variation and latency. It is a design assumption, not an industry guarantee.
The channel-opportunity counts are hypothetical site inputs, not regulatory
channel tables. No power, propagation or association algorithm is simulated.

At the base activity level:

| Case | 5 GHz demand | 6 GHz demand | Required 5/6 GHz radios | AP lower bound |
| --- | ---: | ---: | ---: | ---: |
| 5 GHz only | 510 Mb/s | 0 | 9 / 0 | 9 |
| 5 GHz only, one-AP capacity reserve | 510 | 0 | 10 / 0 | 10 |
| Mixed | 270 | 240 | 5 / 3 | 5 |
| Mixed, one-AP capacity reserve | 270 | 240 | 6 / 4 | 6 |

The ten-radio 5-GHz-only case exceeds the assumed nine independent channel
opportunities. Adding an AP on the same contention domain does not supply
another independent radio's capacity. Revisit reuse, coverage, channel width,
admission, wired offload or the requirement. A cold spare is a different
design with its own detection, channel-selection and recovery tests.

At twice the activity, demand is 1020 Mb/s. The 5-GHz-only bound is 17 radios;
mixed-band demand is 540/480 Mb/s, requiring 9/6 radios. The latter exceeds
the assumed four 6-GHz opportunities. Failure-reserve counts rise to 18/0
and 10/7 respectively. A numerically feasible count still needs validation.

Answer guidance for chapter extensions:
- One-quarter laptop offload: demand 390/120 Mb/s, radios 7/2, AP lower bound 7;
  one-AP capacity reserve gives 8/3, lower bound 8.
- 200-seat canteen with the same mix and fractions: 340 Mb/s total; mixed
  demand 180/160, radios 3/2, AP lower bound 3. One-AP reserve gives 4/3.
  The audience, applications, client capabilities and occupancy pattern need
  new observations before those theatre assumptions can be reused.

For every input, name its source or the measurement needed: active-client
distribution, useful throughput with representative traffic, occupied RF
survey, lawful channels/device class, PoE/uplink limits, retries and latency.
Test coverage and client redistribution after one AP fails. The computed
physical count assumes one useful radio per band per AP; co-location and
placement constraints may require more APs or invalidate the design.
