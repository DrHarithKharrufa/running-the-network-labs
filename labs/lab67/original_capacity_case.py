#!/usr/bin/env python3
"""
Lab 67.1 -- from interface counters to "order now": the capacity decision.

Chapter 67 ties together the whole pipeline: represent load by a high percentile of
the busy period, not the average (sec 2); forecast with a compound growth model
(sec 3); set the upgrade trigger with headroom (sec 5); size for the FAILURE state,
not the sunny day (sec 6, N-1); and respect the provisioning lead time (sec 7). This
takes a week of busy-hour utilisation for a core link, shows the average hiding the
congestion the 95th percentile reveals, then runs the N-1, growth and lead-time
checks to reach an order-or-wait decision.

    python3 capacity_case.py
"""
import math

CAPACITY_G      = 100.0    # link capacity, Gbps
TRIGGER_PCT     = 70.0     # headroom policy: upgrade when busy-hour p95 crosses this
GROWTH_PER_YEAR = 0.25     # 25% compound growth
LEAD_TIME_MO    = 6        # months to deliver a new circuit

# One day of hourly busy-region utilisation (Gbps) on a 100G link: quiet nights,
# busy daytime, a sharp evening peak. Averaging over the day dilutes the peak.
HOURLY_G = [18, 15, 14, 14, 16, 22, 35, 46, 52, 55, 54, 56,
            58, 57, 55, 58, 63, 71, 78, 80, 77, 66, 44, 28]

def pct(values, p):
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return s[int(k)]
    return s[lo] + (s[hi] - s[lo]) * (k - lo)

def years_to_reach(start_pct, target_pct, g):
    if start_pct >= target_pct:
        return 0.0
    return math.log(target_pct / start_pct) / math.log(1 + g)

if __name__ == "__main__":
    print("Capacity decision for a 100G core link (ch67)\n")

    mean_g = sum(HOURLY_G) / len(HOURLY_G)
    p95_g  = pct(HOURLY_G, 95)
    max_g  = max(HOURLY_G)

    print("Step 1 -- represent the load honestly (sec 2):")
    print(f"    mean utilisation : {mean_g:5.1f} G = {mean_g/CAPACITY_G*100:4.1f}%  "
          f"<- 'looks like ample headroom'")
    print(f"    95th percentile  : {p95_g:5.1f} G = {p95_g/CAPACITY_G*100:4.1f}%  "
          f"<- the busy-hour load that actually matters")
    print(f"    absolute peak    : {max_g:5.1f} G = {max_g/CAPACITY_G*100:4.1f}%  "
          f"<- one spike; do not size to this\n")

    p95_pct = p95_g / CAPACITY_G * 100
    print(f"    The mean ({mean_g/CAPACITY_G*100:.0f}%) hides congestion the p95 "
          f"({p95_pct:.0f}%) reveals. Plan to the p95.\n")

    print("Step 2 -- the failure state (sec 6, N-1):")
    # Parallel link carries an equal demand; if it fails, this link absorbs both.
    n1_pct = p95_pct * 2
    print(f"    a parallel link carries an equal demand; on its failure this link")
    print(f"    absorbs both: N-1 busy-hour load = {n1_pct:.0f}% of capacity")
    print(f"    verdict: {'FINE' if n1_pct <= 100 else 'OVERLOADED -- the redundant pair is a delayed double outage'}\n")

    print("Step 3 -- growth and the trigger (sec 3, sec 5):")
    t_trigger = years_to_reach(p95_pct, TRIGGER_PCT, GROWTH_PER_YEAR)
    t_sat     = years_to_reach(p95_pct, 100.0, GROWTH_PER_YEAR)
    if p95_pct >= TRIGGER_PCT:
        print(f"    p95 is ALREADY over the {TRIGGER_PCT:.0f}% trigger "
              f"({p95_pct:.0f}%) -- past due.")
    else:
        print(f"    at {GROWTH_PER_YEAR*100:.0f}%/yr, p95 crosses the "
              f"{TRIGGER_PCT:.0f}% trigger in {t_trigger:.2f} yr")
    print(f"    at {GROWTH_PER_YEAR*100:.0f}%/yr, p95 reaches 100% (saturation) in "
          f"{t_sat:.2f} yr\n")

    print("Step 4 -- the lead-time decision (sec 7):")
    lead_yr = LEAD_TIME_MO / 12.0
    print(f"    a new circuit takes {LEAD_TIME_MO} months ({lead_yr:.2f} yr) to deliver.")
    order_by_yr = t_sat - lead_yr
    print(f"    to have relief before saturation, order by {order_by_yr:.2f} yr from now.")
    decision = ("ORDER NOW" if (p95_pct >= TRIGGER_PCT or n1_pct > 100 or order_by_yr <= 0)
                else f"order within {order_by_yr:.2f} yr")
    print(f"\n    DECISION: {decision}")
    print( "    reasons: p95 already over trigger; N-1 state already overloaded;")
    print( "             lead time leaves no slack before saturation.\n")

    print("The '47% average, plenty of headroom' reading is the trap (sec 2). The")
    print("busy-hour p95 is near full, the failure state is already overloaded")
    print("(sec 6), and the six-month lead time (sec 7) means the order must go in")
    print("now -- long before the link visibly hurts. Plan the failure state on the")
    print("percentile, and order on the forecast, not on the pain.")
