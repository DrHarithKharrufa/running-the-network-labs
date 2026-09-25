# Lab 67.1: a capacity case with inspectable assumptions

The shipped `capacity_case.py` is repaired in place. Its previous source is
preserved unchanged as `original_capacity_case.py` and in the review backup.
Standard-library Python 3.10+; no network access or device execution:

```text
python -B capacity_case.py
python -B capacity_case.py --demo-original
python -B -m unittest -v test_capacity_case.py
```

The original 24 values are synthetic hourly averages for ONE DAY, not a week of
busy-hour samples. Their mean is 47.1667, p95 is 77.85 and maximum hourly average
is 80 Gbit/s. The estimator linearly interpolates at rank `(n-1)*p/100` with
equally weighted samples. None demonstrates loss, delay or packet-scale bursts.

The repaired planning scenario uses the maximum observed hourly average. A 70%
in-service limit is an illustrative input, NOT a physical utilisation knee or an
order trigger. Two equal-rate 100 Gbit/s paths have identical aligned demand;
all demand is assumed able to use either survivor. Normal peak demand is 80 and
single-survivor demand is 160. Both paths failed means NO_PATH. This is a narrow
scenario, not a topology solver, simulation of convergence, or general N-2 model.

Approval (1 month) precedes design (1); delivery (3) and permitting (2) then run
in parallel; installation (1) waits for both and acceptance (1) follows. Critical
path: 7 months, plus 1 month contingency = 8 months. In the lower-load case each
path carries 20: survivor demand 40 reaches 70 in 2.507873 years at 25% growth,
giving 1.841207 years to begin the eight-month schedule. The function returns
current-limit, act-now, future-deadline or no-crossing-under-model states with
reasons derived from inputs. These are arithmetic scenarios, not purchase advice.

Negative controls:

- 96 one-minute samples at 40 and 4 consecutive samples at offered load 120 give
  p95=40. The percentile hides a sustained high-load interval.
- Two 100-sample series, each with five samples at 80 and 95 at 20, place peaks
  in disjoint intervals. Their p95 values sum to 46; p95 of aligned sums is 100.
- The historical fixture p95 reaches 100 after 1.122086 years at 25% growth.
  Subtracting six months leaves 0.622086 years: the old printed "no slack" reason
  was false, despite immediate need under its separate trigger/failure assumptions.
- A current breach remains actionable with declining growth. Zero/declining
  growth below the limit, or a zero starting demand, has no future crossing under
  the fixed compound model. Future demand steps invalidate that conclusion.
- Empty/invalid/non-finite inputs, mismatched sample counts, invalid schedule
  dependencies and cycles are rejected. Equal-length samples alone do NOT prove
  timestamp alignment; the caller must establish it from the observation record.

The tests check boundaries, input failures and counterexamples. Production work
also requires measurement quality, actual service thresholds, demand uncertainty,
rerouting, flow hashing, queue behaviour, supplier schedules and tested relief.
