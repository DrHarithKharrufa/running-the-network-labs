"""Checks of boundary cases and printed examples, not network acceptance."""
import copy
import json
from pathlib import Path
import unittest
from case_math import crossing_months, evaluate, present_cost


class TeachingCaseChecks(unittest.TestCase):
    def setUp(self):
        self.case = json.loads(Path(__file__).with_name("branch-case.json").read_text(encoding="utf-8"))

    def test_printed_address_plan(self):
        a = evaluate(self.case)["addressing"]
        self.assertEqual((a["current_capacity"], a["current_spare"], a["future_required_hosts"]), (126, 5, 145))
        self.assertFalse(a["future_fits_current"])
        self.assertTrue(a["future_fits_expansion"])

    def test_printed_time_scenarios(self):
        for growth, months in ((.10, 16.8122304961), (.25, 7.1809232311), (.40, 4.7622850776)):
            self.assertAlmostEqual(crossing_months(70, 80, growth), months, places=8)

    def test_printed_cash_and_deadline_constraints(self):
        a, b = (evaluate(self.case)["options"][key] for key in ("A", "B"))
        self.assertEqual(a["year_1_cash_gbp"], 115000)
        self.assertEqual(b["year_1_cash_gbp"], 85000)
        self.assertLess(a["growth_scenarios"][1]["latest_decision_months_from_now"], 0)
        self.assertGreater(b["growth_scenarios"][1]["latest_decision_months_from_now"], 0)
        self.assertAlmostEqual(a["present_cost_gbp"], 185969.364426, places=5)
        self.assertAlmostEqual(b["present_cost_gbp"], 187511.304171, places=5)

    def test_price_shock_leaves_only_two_thousand(self):
        self.case["options"]["B"]["annual_gbp"] = 78000
        self.assertEqual(evaluate(self.case)["options"]["B"]["first_year_headroom_before_contingency_gbp"], 2000)

    def test_no_crossing_under_fixed_zero_or_declining_growth(self):
        for growth in (0, -.1):
            self.assertIsNone(crossing_months(70, 80, growth))
        self.assertIsNone(crossing_months(0, 80, .25))

    def test_current_breach_is_not_hidden_by_decline(self):
        self.assertEqual(crossing_months(90, 80, -.1), 0)

    def test_zero_discount_equals_cash_total(self):
        self.assertEqual(present_cost(70000, 45000, 3, 0), 205000)

    def test_host_bits_are_rejected(self):
        self.case["client_subnet"] = "10.10.64.10/25"
        with self.assertRaises(ValueError):
            evaluate(self.case)

    def test_overlapping_management_is_rejected(self):
        self.case["management_subnet"] = "10.10.64.128/27"
        with self.assertRaises(ValueError):
            evaluate(self.case)

    def test_invalid_and_nonfinite_numbers(self):
        for demand in (-1, float("nan"), float("inf"), True):
            with self.subTest(demand=demand), self.assertRaises(ValueError):
                crossing_months(demand, 80, .25)
        for years in (0, 1.5, True, 101):
            with self.subTest(years=years), self.assertRaises(ValueError):
                present_cost(10, 5, years, .08)

    def test_topology_and_traffic_assumptions_are_enforced(self):
        for field, value in (("wan_circuits", 3), ("deferrable_class_mbps", 60),
                             ("survivor_planning_trigger_mbps", 101)):
            case = copy.deepcopy(self.case)
            case[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                evaluate(case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
