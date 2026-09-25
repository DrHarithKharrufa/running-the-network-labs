# Lab 74.1: rare-event metrics and decision costs

All counts are synthetic. This standard-library Python exercise trains no ML
model, reads no telemetry and provides no production accuracy or vendor benchmark.

```
python -m unittest discover -v
python base_rate.py
python base_rate.py --counts 90 5000 994900 10
python base_rate.py --counts 0 0 0 0
python base_rate.py --demo-original
```

The four count arguments are **TP FP TN FN**. They must be non-negative integers;
Python callers cannot pass booleans or integral-looking floats as counts. Empty
datasets and zero denominators produce JSON `null`, not an invented zero.
Sixteen tests check input boundaries, formulas, base-rate consistency, a known
Wilson interval, boundary intervals and the cost-sensitive decision example.

For one million labelled intervals, 100 positive and 999,900 negative:

| Detector | TP | FP | TN | FN | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|
| Always negative | 0 | 0 | 999900 | 100 | Undefined | 0% |
| Noisy detector | 90 | 5000 | 994900 | 10 | 1.7682% | 90% |
| Seasonal baseline | 80 | 400 | 999500 | 20 | 16.6667% | 80% |
| Candidate model | 82 | 380 | 999520 | 18 | 17.7489% | 82% |

The always-negative detector has 99.99% accuracy and no observed detections.
Accuracy is a valid statistic but insufficient for this task. For the noisy
detector the false-positive rate is about 0.50005%, whereas the false-discovery
fraction (the proportion of alerts that are false) is about 98.2318%. These are
different denominators. `precision_from_rates` reproduces the same precision
from prevalence, true-positive rate and false-positive rate.

The candidate improves both precision and recall point estimates. Under the
illustrative costs of 1,000 arbitrary units per missed positive interval and one
unit per false alert, it avoids 2,020 units per million intervals before extra
operating cost. An additional 1,000 units leaves +1,020; 3,000 leaves −980. This
does not prescribe a winner: severity, operator workload, detection delay and
uncertainty can change the decision. Costs must refer to the same evaluation
period and units as the counts.

The script returns approximate 95% Wilson intervals for precision and recall.
For baseline recall 80/100, the interval is approximately [0.71117, 0.86663]; for
candidate recall 82/100 it is [0.73333, 0.88300]. These assume independent,
representative Bernoulli trials. Correlated intervals from the same incident do
not satisfy that assumption. Synthetic totals contain no evidence of population
generalisation. Overlapping separate intervals neither establish equivalence nor
constitute a significance test for the difference. Retain paired predictions and
incident/site/time groupings for a suitable paired or cluster-aware comparison.

One positive interval is not necessarily one incident. Define onset, matching
window, alert grouping, duplicate handling, missed-incident severity and operator
exposure before evaluating a real detector. Fit preprocessing and choose thresholds
on training/validation data, then assess a held-out period; do not tune on that
test period. A live comparison also needs label review and monitoring for drift.

`original_base_rate.py` preserves the incoming file byte-for-byte. The historical
demo is explicitly labelled: its model counts improved both metrics, its stated
winner was not established, and its zero-denominator handling hid undefined
quantities. Retained for review provenance, not as a current recommendation.

References:
- https://scikit-learn.org/stable/modules/model_evaluation.html
- https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm
- https://scikit-learn.org/stable/common_pitfalls.html
