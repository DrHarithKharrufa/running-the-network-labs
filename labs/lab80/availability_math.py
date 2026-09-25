#!/usr/bin/env python3
"""Analytical availability and capacity worksheet; no network or fault execution."""
import json
import math

def nonnegative(value, name="value"):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(name + " must be a finite nonnegative number")
    try:
        valid = math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(name + " must be a finite nonnegative number")
    return float(value)

def probability(value):
    value = nonnegative(value, "probability")
    if value > 1:
        raise ValueError("probability must be a finite number in [0, 1]")
    return value

def count(value, name="count"):
    if type(value) is not int or not 1 <= value <= 10000:
        raise ValueError(name + " must be an integer from 1 to 10000 (worksheet bound)")
    return value

def serial(avails):
    """Probability all required components are up, assuming independent states."""
    values = [probability(a) for a in avails]
    if not values:
        raise ValueError("at least one component is required")
    return math.prod(values)

def parallel(path_avail, n=2, common_mode=0.0):
    """c is common-outage fraction; a is conditional availability when it is absent.
    Conditional path states are independent. Any one path has sufficient capacity.
    Switching coverage is perfect in this deliberately limited model.
    """
    a, c = probability(path_avail), probability(common_mode)
    count(n)
    if a == 1:
        return 1-c
    return (1-c) * -math.expm1(n*math.log1p(-a))

def r_out_of_n(a, required, total):
    """Independent identical unit-state probability; any required units suffice."""
    a = probability(a); count(required); count(total)
    if required > total:
        raise ValueError("required cannot exceed total")
    if a == 0 or a == 1:
        return a
    terms = [math.exp(math.lgamma(total+1)-math.lgamma(k+1)-math.lgamma(total-k+1)
                      + k*math.log(a)+(total-k)*math.log1p(-a))
             for k in range(required,total+1)]
    return min(1.0, max(0.0, math.fsum(terms)))

def renewal_availability(mean_up_hours, mean_down_hours):
    up, down = nonnegative(mean_up_hours), nonnegative(mean_down_hours)
    scale = max(up, down)
    if scale == 0:
        raise ValueError("cycle duration must be positive")
    return (up/scale)/((up/scale)+(down/scale))

def downtime_minutes(a, days=365):
    a = probability(a)
    days = nonnegative(days, "days")
    if days == 0:
        raise ValueError("period must be positive and finite")
    result = (1-a)*days*24*60
    if not math.isfinite(result):
        raise ValueError("downtime exceeds worksheet floating-point range")
    return result

def observed_bounds(usable, unusable, unknown):
    """Bounds in a fixed eligible period; missing intervals are not silently dropped."""
    up, down, missing = [nonnegative(x) for x in (usable, unusable, unknown)]
    scale = max(up, down, missing)
    if scale == 0:
        raise ValueError("eligible period must be positive")
    up, down, missing = up/scale, down/scale, missing/scale
    total = up+down+missing
    known = up+down
    return {"lower": up/total, "upper": (up+missing)/total,
            "unknown_fraction": missing/total,
            "usable_fraction_of_observed_only": up/known if known else None}

def capacity_case(capacities, demand, unavailable=()):
    """Capacity accounting only; assumes remaining resources can serve all demand."""
    values = list(capacities)
    if not values:
        raise ValueError("empty capacity list")
    values = [nonnegative(x, "capacity") for x in values]
    demand = nonnegative(demand, "demand")
    failed = list(unavailable)
    if any(type(i) is not int or not 0 <= i < len(values) for i in failed) or len(failed) != len(set(failed)):
        raise ValueError("invalid unavailable unit indices")
    remaining = sum(x for i,x in enumerate(values) if i not in failed)
    if not math.isfinite(remaining):
        raise ValueError("aggregate capacity exceeds worksheet floating-point range")
    return dict(demand=demand, remaining=remaining, margin=remaining-demand, meets_demand=remaining >= demand)

def worksheet():
    a = serial([.9995,.999,.9995,.999])
    c = .003
    return {
      "scope": "Analytical teaching models with stated independence, common-hazard and capacity assumptions. No measured SLA, hardware failover or cost estimate.",
      "year_days":365,
      "chain_conditional_availability":a,
      "independent_pair":parallel(a),
      "common_outage_fraction":c,
      "single_with_same_common_hazard":parallel(a,1,c),
      "pair_with_same_common_hazard":parallel(a,2,c),
      "five_nines_downtime_minutes":downtime_minutes(.99999),
      "observed_50_usable_2_unusable_8_unknown":observed_bounds(50,2,8),
      "two_of_three_independent_units_a_0_999":r_out_of_n(.999,2,3),
      "two_N_demand100_four_units50":{
        "normal":capacity_case([50]*4,100),
        "one_whole_set_maintenance":capacity_case([50]*4,100,[0,1]),
        "maintenance_plus_surviving_unit_failure":capacity_case([50]*4,100,[0,1,2])},
      "mean_up10000_down4":renewal_availability(10000,4),
      "double_mean_up":renewal_availability(20000,4),
      "halve_mean_down":renewal_availability(10000,2)
    }

if __name__ == "__main__":
    print(json.dumps(worksheet(), indent=2))
