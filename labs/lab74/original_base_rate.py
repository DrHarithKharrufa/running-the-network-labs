#!/usr/bin/env python3
"""
Lab 74.1 -- why accuracy lies when failures are rare.

Chapter 74 sec 4: a rare-event detector can be 99.99%% accurate and useless.
This computes accuracy, precision and recall for two "detectors" on a realistic
base rate, and shows the naive one winning on accuracy while catching nothing --
then shows a simple baseline beating a fancy model that cannot clear it.

    python3 base_rate.py
"""

def score(tp, fp, tn, fn):
    total = tp + fp + tn + fn
    acc  = (tp + tn) / total
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    return acc, prec, rec

def report(name, tp, fp, tn, fn):
    acc, prec, rec = score(tp, fp, tn, fn)
    print(f"{name}")
    print(f"    accuracy={acc*100:6.2f}%   precision={prec*100:6.2f}%   "
          f"recall={rec*100:6.2f}%")
    return acc, prec, rec

if __name__ == "__main__":
    N = 1_000_000            # intervals observed
    FAULTS = 100            # real faults: 1 in 10,000 -- rare
    NORMAL = N - FAULTS

    print(f"{N:,} intervals, {FAULTS} real faults (base rate 1 in "
          f"{N//FAULTS:,})\n")

    # Detector A: the "lazy" detector -- always says 'no fault'
    report("A: always says 'no fault'",
           tp=0, fp=0, tn=NORMAL, fn=FAULTS)
    print("    -> 99.99% accurate and catches ZERO faults. Accuracy is a lie here.\n")

    # Detector B: catches 90 of 100 faults, but fires 5,000 false alarms
    report("B: real detector (90/100 caught, 5000 false alarms)",
           tp=90, fp=5000, tn=NORMAL - 5000, fn=10)
    print("    -> lower 'accuracy' feel, but it actually finds faults; note precision:")
    print("       of ~5090 alerts only 90 are real -- the base-rate tax (sec 4).\n")

    # Baseline vs model: a model must BEAT the baseline to be worth its cost (sec 8)
    print("Baseline vs model (must beat baseline to justify complexity, sec 8):")
    _, bp, br = score(80, 400, NORMAL - 400, 20)     # seasonal baseline
    _, mp, mr = score(82, 380, NORMAL - 380, 18)     # fancy model
    print(f"    seasonal baseline : precision={bp*100:5.1f}% recall={br*100:5.1f}%")
    print(f"    fancy ML model    : precision={mp*100:5.1f}% recall={mr*100:5.1f}%")
    print("    -> the model barely moves the numbers; ship the baseline (sec 8),")
    print("       and demand precision/recall + base rate from any vendor (sec 9).")
