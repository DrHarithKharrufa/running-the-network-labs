"""Reproduce Appendix G's invented arithmetic; never connect to a device.

Python 3.10+, standard library only. All rates and costs are teaching inputs.
This is not a topology, queue, application, delivery or risk-probability model.
"""
import argparse
import ipaddress
import json
import math
from pathlib import Path


def number(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    if not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name} must be finite and at least {minimum}")
    return value


def crossing_months(demand, trigger, annual_growth):
    demand = number(demand, "demand")
    trigger = number(trigger, "trigger")
    growth = number(annual_growth, "annual growth", -0.99)
    if trigger <= 0:
        raise ValueError("trigger must be positive")
    if demand >= trigger:
        return 0.0
    if demand == 0 or growth <= 0:
        return None
    return 12 * math.log(trigger / demand) / math.log1p(growth)


def present_cost(setup, annual, years, rate):
    setup = number(setup, "setup")
    annual = number(annual, "annual")
    rate = number(rate, "discount rate")
    if isinstance(years, bool) or not isinstance(years, int) or not 1 <= years <= 100:
        raise ValueError("years must be an integer from 1 to 100")
    result = setup + math.fsum(annual / (1 + rate) ** k for k in range(1, years + 1))
    if not math.isfinite(result):
        raise ValueError("present cost exceeds the numeric range")
    return result


def evaluate(case):
    networks = {key: ipaddress.IPv4Network(case[key], strict=True) for key in
                ("client_subnet", "expanded_client_subnet", "management_subnet")}
    current = networks["client_subnet"]
    expanded = networks["expanded_client_subnet"]
    management = networks["management_subnet"]
    if any(n.prefixlen > 30 for n in networks.values()):
        raise ValueError("This host-capacity exercise uses ordinary LAN prefixes, not /31 or /32")
    if not current.subnet_of(expanded) or expanded.overlaps(management):
        raise ValueError("Client expansion must contain the client LAN and not overlap management")
    for key in ("staff_endpoints", "gateway_addresses", "wan_circuits", "horizon_years"):
        v = case[key]
        if isinstance(v, bool) or not isinstance(v, int) or v < 1:
            raise ValueError(f"{key} must be a positive integer")
    if case["wan_circuits"] != 2:
        raise ValueError("This scenario models exactly two links and one survivor")
    growth = number(case["endpoint_growth_fraction"], "endpoint growth")
    endpoints = math.ceil(case["staff_endpoints"] * (1 + growth))
    now = case["staff_endpoints"] + case["gateway_addresses"]
    future = endpoints + case["gateway_addresses"]
    demand = number(case["total_demand_mbps"], "total demand")
    critical = number(case["critical_class_mbps"], "critical class")
    deferrable = number(case["deferrable_class_mbps"], "deferrable class")
    if not math.isclose(critical + deferrable, demand, rel_tol=0, abs_tol=1e-9):
        raise ValueError("Traffic classes must sum to the stated demand")
    capacity = number(case["usable_mbps_per_circuit"], "capacity")
    trigger = number(case["survivor_planning_trigger_mbps"], "trigger")
    if not 0 < trigger <= capacity:
        raise ValueError("Planning trigger must be positive and no greater than usable capacity")
    ceiling = number(case["first_year_cash_ceiling_gbp"], "cash ceiling")
    options = {}
    for name, option in case["options"].items():
        setup = number(option["setup_gbp"], "setup")
        annual = number(option["annual_gbp"], "annual")
        lead = number(option["complete_delivery_months"], "delivery months")
        scenarios = []
        for rate in case["annual_growth_scenarios"]:
            crossing = crossing_months(demand, trigger, rate)
            scenarios.append({"annual_growth": rate, "crossing_months": crossing,
                              "latest_decision_months_from_now": None if crossing is None else crossing - lead})
        options[name] = {"year_1_cash_gbp": setup + annual,
                         "undiscounted_cost_gbp": setup + annual * case["horizon_years"],
                         "present_cost_gbp": present_cost(setup, annual, case["horizon_years"], case["discount_rate"]),
                         "first_year_headroom_before_contingency_gbp": ceiling - setup - annual,
                         "growth_scenarios": scenarios}
    return {"scope": case["scope"], "cash_timing": case["cash_timing"],
            "addressing": {"current_required_hosts": now, "current_capacity": current.num_addresses - 2,
                           "current_spare": current.num_addresses - 2 - now,
                           "future_endpoints": endpoints, "future_required_hosts": future,
                           "future_fits_current": future <= current.num_addresses - 2,
                           "expanded_capacity": expanded.num_addresses - 2,
                           "future_fits_expansion": future <= expanded.num_addresses - 2},
            "normal_mbps_per_link_assuming_equal_split": demand / 2,
            "survivor_mbps_assuming_successful_reroute": demand,
            "critical_mbps_if_deferral_is_agreed_and_enforced": critical,
            "options": options}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(__file__).with_name("branch-case.json"))
    args = parser.parse_args()
    result = evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
