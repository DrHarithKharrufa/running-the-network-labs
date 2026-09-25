import math
import unittest
from assurance import Intent, assure, fixture, scenarios


class AssuranceTests(unittest.TestCase):
    def check(self, obs, expected, intent=None, now=1000):
        result = assure(intent or Intent(), obs, now=now)
        self.assertEqual(expected, result["status"], result)
        return result

    def test_normal_capacity_arithmetic(self):
        r = self.check(fixture(), "MET")
        self.assertEqual(140, r["checks"]["usable_capacity_gbps"]["normal"])
        self.assertEqual(70, r["checks"]["usable_capacity_gbps"]["path:A"])

    def test_all_demonstration_scenarios(self):
        expected = ["MET", "VIOLATED", "VIOLATED", "VIOLATED", "VIOLATED", "VIOLATED", "UNKNOWN"]
        for obs, result in zip(scenarios().values(), expected):
            with self.subTest(result=result): self.check(obs, result)

    def test_rtt_boundary(self):
        for value, expected in [(49.999, "MET"), (50, "VIOLATED"), (50.001, "VIOLATED")]:
            o = fixture(); o["rtt_samples_ms"] = [value] * 300
            with self.subTest(value=value): self.check(o, expected)

    def test_nearest_rank_95th(self):
        o = fixture(); o["rtt_samples_ms"] = [22] * 285 + [100] * 15
        self.assertEqual(22, self.check(o, "MET")["checks"]["normal_rtt_p95_ms"])
        o["rtt_samples_ms"][284] = 100
        self.check(o, "VIOLATED")

    def test_restoration_independent_from_rtt(self):
        o = fixture(); o["fault_trials"]["path:A"]["restoration_ms"] = [80]
        r = self.check(o, "VIOLATED")
        self.assertEqual(22, r["checks"]["normal_rtt_p95_ms"])

    def test_capacity_equality_allowed(self):
        self.check(fixture(), "MET", Intent(demand_gbps=70))
        self.check(fixture(), "VIOLATED", Intent(demand_gbps=70.001))

    def test_shared_risk_not_path_count(self):
        r = self.check(scenarios()["shared duct"], "VIOLATED")
        self.assertEqual(2, r["checks"]["active_paths"])
        self.assertEqual(0, r["checks"]["usable_capacity_gbps"]["srlg:shared-duct"])

    def test_stale_and_future_snapshot(self):
        for now in (969, 1031):
            with self.subTest(now=now): self.check(fixture(), "UNKNOWN", now=now)
        self.check(fixture(), "MET", now=1030)

    def test_wrong_window(self):
        o = fixture(); o["window_start"] = 671; self.check(o, "UNKNOWN")

    def test_wrong_target_or_class(self):
        for field, value in [("endpoints", ["LON-probe", "BHM-probe"]), ("traffic_class", "bulk")]:
            o = fixture(); o[field] = value
            with self.subTest(field=field): self.check(o, "UNKNOWN")

    def test_bad_rtt_types(self):
        for value in (None, True, "22", math.nan, math.inf, -1):
            o = fixture(); o["rtt_samples_ms"][0] = value
            with self.subTest(value=value): self.check(o, "UNKNOWN")

    def test_missing_sample_is_unknown(self):
        o = fixture(); o["rtt_samples_ms"].pop(); self.check(o, "UNKNOWN")

    def test_missing_required_fields(self):
        for field in fixture():
            o = fixture(); del o[field]
            with self.subTest(field=field): self.check(o, "UNKNOWN")

    def test_duplicate_path_id(self):
        o = fixture(); o["paths"][1]["id"] = "A"; self.check(o, "UNKNOWN")

    def test_empty_or_incomplete_srlg(self):
        o = fixture(); o["srlg_inventory_complete"] = False; self.check(o, "UNKNOWN")
        o = fixture(); o["paths"][0]["srlgs"] = []; self.check(o, "UNKNOWN")

    def test_invalid_path_values(self):
        for field, value in [("up", 1), ("capacity_gbps", 0), ("capacity_gbps", math.nan), ("srlgs", "duct-a")]:
            o = fixture(); o["paths"][0][field] = value
            with self.subTest(field=field, value=value): self.check(o, "UNKNOWN")

    def test_trial_revision_and_age(self):
        for field, value in [("topology_revision", "r0"), ("at", 1001), ("at", 0)]:
            o = fixture(); o["fault_trials"]["path:A"][field] = value
            with self.subTest(field=field, value=value):
                self.check(o, "UNKNOWN", Intent(trial_max_age=999))

    def test_invalid_or_absent_trial(self):
        for value in (None, [], [True], [math.nan], [-1]):
            o = fixture(); o["fault_trials"]["path:A"]["restoration_ms"] = value
            with self.subTest(value=value): self.check(o, "UNKNOWN")
        o = fixture(); del o["fault_trials"]["path:A"]; self.check(o, "UNKNOWN")

    def test_known_breach_and_missing_trial_reported(self):
        o = fixture(); o["rtt_samples_ms"] = [71] * 300; del o["fault_trials"]
        r = self.check(o, "VIOLATED")
        self.assertTrue(r["unknowns"])

    def test_invalid_observation_types(self):
        for value in (None, [], True, "good"):
            with self.subTest(value=value): self.check(value, "UNKNOWN")

    def test_invalid_intent(self):
        for kwargs in ({"rtt_limit_ms": math.nan}, {"demand_gbps": -1}, {"sample_count": True},
                       {"utilisation_limit": 1.1}, {"restoration_limit_ms": 0}, {"endpoints": ("A", "A")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): Intent(**kwargs)

    def test_invalid_clock(self):
        for now in (True, math.nan, math.inf, -1):
            with self.subTest(now=now), self.assertRaises(ValueError): assure(Intent(), fixture(), now=now)

    def test_input_is_not_mutated(self):
        o = fixture(); self.check(o, "MET"); self.assertEqual(fixture(), o)


if __name__ == "__main__": unittest.main()
