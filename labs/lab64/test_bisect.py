"""Tests for lab 64.1.  Run: python3 test_bisect.py

The lab was repaired rather than withdrawn, so these tests cover both what it
always claimed --- that a systematic search beats an unsystematic one --- and
the four things the repair added: that the comparison names its oracles, that
random probing converges, that bisection has preconditions, and that it
returns an answer with the same face whether or not that answer is right.
"""
import io
import math
import unittest

from bisect_vs_guess import (ORACLES, PRECONDITIONS, SEED, SearchError,
                             bisection, comparison, days_to_confidence,
                             demo_original, linear_scan, majority_error,
                             ping_proves_what, prove_the_claims,
                             quiet_interval_proves_what,
                             random_with_replacement,
                             random_without_replacement, report,
                             scan_with_region_oracle,
                             simulate_random_with_replacement, two_faults,
                             unreliable_bisection)


class CostTests(unittest.TestCase):
    """The closed forms, at sizes small enough to check by hand."""

    def test_linear_scan_is_the_mean_position(self):
        self.assertAlmostEqual(linear_scan(1)['expected_probes'], 1.0)
        self.assertAlmostEqual(linear_scan(2)['expected_probes'], 1.5)
        self.assertAlmostEqual(linear_scan(1024)['expected_probes'], 512.5)

    def test_remembering_misses_costs_exactly_a_scan(self):
        for n in (1, 2, 7, 64, 1024):
            self.assertAlmostEqual(
                random_without_replacement(n)['expected_probes'],
                linear_scan(n)['expected_probes'],
                msg=f'at n={n}')

    def test_forgetting_misses_costs_n_not_infinity(self):
        for n in (1, 2, 7, 64, 1024):
            self.assertAlmostEqual(
                random_with_replacement(n)['expected_probes'], float(n))

    def test_bisection_is_the_number_of_halvings(self):
        self.assertAlmostEqual(bisection(1)['expected_probes'], 0.0)
        self.assertAlmostEqual(bisection(2)['expected_probes'], 1.0)
        self.assertAlmostEqual(bisection(1024)['expected_probes'], 10.0)
        self.assertEqual(bisection(1024)['worst_case'], 10)

    def test_bisection_worst_case_on_a_ragged_size(self):
        self.assertEqual(bisection(1000)['worst_case'], 10)
        self.assertLess(bisection(1000)['expected_probes'], 10.0)

    def test_the_oracle_alone_buys_nothing(self):
        """The finding's core point, as an equality rather than a sentence."""
        n = 1024
        self.assertAlmostEqual(scan_with_region_oracle(n)['expected_probes'],
                               linear_scan(n)['expected_probes'])
        self.assertLess(bisection(n)['expected_probes'],
                        scan_with_region_oracle(n)['expected_probes'])

    def test_every_strategy_names_its_oracle(self):
        for row in comparison(64):
            self.assertIn(row['oracle'], ORACLES, msg=row['strategy'])

    def test_two_oracles_are_distinguished(self):
        oracles = {row['oracle'] for row in comparison(64)}
        self.assertEqual(oracles, {'position', 'region'})

    def test_invalid_sizes_are_refused(self):
        for bad in (0, -1, 1.5, True, '8', None):
            with self.subTest(n=bad), self.assertRaises(SearchError):
                linear_scan(bad)
            with self.subTest(n=bad), self.assertRaises(SearchError):
                bisection(bad)


class ConvergenceTests(unittest.TestCase):
    """The claim the original got wrong: guessing does converge."""

    def test_the_simulation_agrees_with_the_closed_form(self):
        n = 64
        observed = simulate_random_with_replacement(n, trials=20000, seed=SEED)
        # Geometric with p = 1/n: mean n, standard deviation about n, so the
        # standard error over t trials is about n/sqrt(t).
        se = n / math.sqrt(20000)
        self.assertLess(abs(observed - n), 6 * se)

    def test_the_simulation_reproduces(self):
        a = simulate_random_with_replacement(64, trials=5000, seed=SEED)
        b = simulate_random_with_replacement(64, trials=5000, seed=SEED)
        self.assertEqual(a, b)

    def test_a_different_seed_gives_a_different_draw(self):
        a = simulate_random_with_replacement(64, trials=5000, seed=SEED)
        b = simulate_random_with_replacement(64, trials=5000, seed=SEED + 1)
        self.assertNotEqual(a, b)

    def test_the_simulation_does_not_depend_on_global_random_state(self):
        import random
        random.seed(1)
        a = simulate_random_with_replacement(64, trials=2000, seed=SEED)
        random.seed(999)
        b = simulate_random_with_replacement(64, trials=2000, seed=SEED)
        self.assertEqual(a, b)


class PreconditionTests(unittest.TestCase):
    """What halving needs, and what happens when it does not get it."""

    def test_the_preconditions_are_stated(self):
        self.assertGreaterEqual(len(PRECONDITIONS), 4)
        names = [name for name, _ in PRECONDITIONS]
        self.assertEqual(sorted(names), sorted(set(names)))
        for name, explanation in PRECONDITIONS:
            self.assertTrue(name.strip())
            self.assertGreater(len(explanation), 60,
                               msg=f'{name} is asserted, not explained')

    def test_an_unreliable_oracle_degrades_geometrically(self):
        r = unreliable_bisection(1024, 0.10)
        self.assertEqual(r['depth'], 10)
        self.assertAlmostEqual(r['p_correct'], 0.9 ** 10)
        self.assertLess(r['p_correct'], 0.36)

    def test_a_perfect_oracle_is_always_right(self):
        self.assertAlmostEqual(unreliable_bisection(1024, 0.0)['p_correct'],
                               1.0)

    def test_repeating_probes_helps_and_costs(self):
        one = unreliable_bisection(1024, 0.10, repeats=1)
        three = unreliable_bisection(1024, 0.10, repeats=3)
        self.assertGreater(three['p_correct'], one['p_correct'])
        self.assertEqual(three['probes'], 3 * one['probes'])

    def test_majority_of_three_beats_one(self):
        self.assertAlmostEqual(majority_error(0.10, 1), 0.10)
        self.assertAlmostEqual(majority_error(0.10, 3),
                               3 * 0.1 ** 2 * 0.9 + 0.1 ** 3)
        self.assertLess(majority_error(0.10, 5), majority_error(0.10, 3))

    def test_a_coin_flip_oracle_is_refused(self):
        for bad in (0.5, 0.9, -0.01):
            with self.subTest(q=bad), self.assertRaises(SearchError):
                unreliable_bisection(64, bad)

    def test_even_repeats_are_refused(self):
        for bad in (2, 4, 0, -1, True):
            with self.subTest(k=bad), self.assertRaises(SearchError):
                unreliable_bisection(64, 0.1, repeats=bad)

    def test_two_faults_find_the_first_and_miss_the_second(self):
        r = two_faults(1024, 100, 700)
        self.assertEqual(r['found'], 100)
        self.assertTrue(r['found_the_first'])
        self.assertTrue(r['second_still_present'])

    def test_two_faults_must_be_given_in_order(self):
        with self.assertRaises(SearchError):
            two_faults(1024, 700, 100)
        with self.assertRaises(SearchError):
            two_faults(1024, 100, 100)

    def test_faults_must_lie_inside_the_path(self):
        for first, second in ((-1, 5), (5, 2048), (0, 1024)):
            with self.subTest(pair=(first, second)):
                with self.assertRaises(SearchError):
                    two_faults(1024, first, second)


class ProbeEvidenceTests(unittest.TestCase):
    """What one successful probe across equal-cost members is worth."""

    def test_one_broken_member_of_eight(self):
        r = ping_proves_what(8, 1)
        self.assertAlmostEqual(r['p_probe_looks_healthy'], 0.875)
        self.assertAlmostEqual(r['p_one_probe_traverses_a_broken_member'],
                               0.125)

    def test_confidence_needs_many_probes(self):
        r = ping_proves_what(8, 1)
        self.assertEqual(r['probes_for_90_percent_confidence'],
                         math.ceil(math.log(0.10) / math.log(0.875)))
        self.assertGreaterEqual(r['probes_for_90_percent_confidence'], 17)

    def test_nothing_broken_needs_no_probes(self):
        r = ping_proves_what(8, 0)
        self.assertAlmostEqual(r['p_probe_looks_healthy'], 1.0)
        self.assertIsNone(r['probes_for_90_percent_confidence'])

    def test_everything_broken_is_caught_first_time(self):
        r = ping_proves_what(8, 8)
        self.assertAlmostEqual(r['p_probe_looks_healthy'], 0.0)
        self.assertEqual(r['probes_for_90_percent_confidence'], 1)

    def test_impossible_bundles_are_refused(self):
        for members, broken in ((0, 0), (-1, 0), (4, 5), (4, -1)):
            with self.subTest(pair=(members, broken)):
                with self.assertRaises(SearchError):
                    ping_proves_what(members, broken)


class SilenceTests(unittest.TestCase):
    """The same question in the time domain: what does a quiet week prove?"""

    def test_the_quiet_probability_is_the_exponential_one(self):
        r = quiet_interval_proves_what(2.0, 3.0)
        self.assertAlmostEqual(r['p_quiet_if_still_broken'], math.exp(-6.0))

    def test_no_finite_interval_reaches_certainty(self):
        for days in (1.0, 7.0, 90.0, 365.0, 10000.0):
            r = quiet_interval_proves_what(2.0, days)
            self.assertTrue(math.isfinite(r['log10_residual_doubt']), msg=days)
            self.assertLess(r['log10_residual_doubt'], 0.0, msg=days)

    def test_the_doubt_is_reported_even_where_a_double_saturates(self):
        """Past ninety days the naive figure rounds to 1.0. The log does not."""
        r = quiet_interval_proves_what(2.0, 90.0)
        self.assertTrue(r['saturated'])
        self.assertAlmostEqual(r['p_fixed_given_quiet'], 1.0)
        self.assertLess(r['log10_residual_doubt'], -70.0)
        self.assertTrue(math.isfinite(r['log10_residual_doubt']))

    def test_the_log_agrees_with_the_direct_figure_where_both_work(self):
        for days in (0.5, 1.0, 3.0, 7.0):
            r = quiet_interval_proves_what(2.0, days)
            self.assertFalse(r['saturated'], msg=days)
            self.assertAlmostEqual(r['log10_residual_doubt'],
                                   math.log10(1.0 - r['p_fixed_given_quiet']),
                                   places=9, msg=days)

    def test_the_doubt_shrinks_without_bound(self):
        values = [quiet_interval_proves_what(2.0, d)['log10_residual_doubt']
                  for d in (1.0, 10.0, 100.0, 1000.0)]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_watching_nothing_learns_nothing(self):
        r = quiet_interval_proves_what(2.0, 0.0, prior_fixed=0.4)
        self.assertAlmostEqual(r['p_quiet_if_still_broken'], 1.0)
        self.assertAlmostEqual(r['p_fixed_given_quiet'], 0.4)

    def test_confidence_rises_with_the_watch(self):
        values = [quiet_interval_proves_what(2.0, d)['p_fixed_given_quiet']
                  for d in (0.5, 1.0, 2.0, 3.0, 7.0)]
        self.assertEqual(values, sorted(values))

    def test_a_rarer_fault_demands_a_longer_watch(self):
        rates = [2.0, 1 / 7.0, 1 / 30.0, 2 / 365.0]
        days = [days_to_confidence(r) for r in rates]
        self.assertEqual(days, sorted(days))
        self.assertGreater(days[-1], 300.0)
        self.assertLess(days[0], 3.0)

    def test_the_inverse_agrees_with_the_forward_calculation(self):
        for rate in (2.0, 0.5, 1 / 30.0):
            for confidence in (0.9, 0.95, 0.99):
                with self.subTest(rate=rate, confidence=confidence):
                    days = days_to_confidence(rate, confidence)
                    back = quiet_interval_proves_what(rate, days)
                    self.assertAlmostEqual(back['p_fixed_given_quiet'],
                                           confidence, places=9)

    def test_a_confidence_already_held_needs_no_watch(self):
        self.assertEqual(days_to_confidence(2.0, confidence=0.5,
                                            prior_fixed=0.6), 0.0)

    def test_a_weaker_prior_demands_a_longer_watch(self):
        self.assertGreater(days_to_confidence(2.0, prior_fixed=0.1),
                           days_to_confidence(2.0, prior_fixed=0.8))

    def test_impossible_parameters_are_refused(self):
        for rate in (0.0, -1.0):
            with self.subTest(rate=rate), self.assertRaises(SearchError):
                quiet_interval_proves_what(rate, 1.0)
        with self.assertRaises(SearchError):
            quiet_interval_proves_what(2.0, -1.0)
        for prior in (0.0, 1.0, -0.5, 2.0):
            with self.subTest(prior=prior), self.assertRaises(SearchError):
                quiet_interval_proves_what(2.0, 1.0, prior_fixed=prior)
        for confidence in (0.0, 1.0, -0.1, 1.2):
            with self.subTest(c=confidence), self.assertRaises(SearchError):
                days_to_confidence(2.0, confidence=confidence)


class HarnessTests(unittest.TestCase):
    """The verifier can fail open too, so check the checks."""

    def test_all_controls_pass(self):
        proof = prove_the_claims()
        self.assertGreaterEqual(len(proof), 8)
        self.assertTrue(all(proof.values()),
                        msg=f'not proved: {[k for k, v in proof.items() if not v]}')

    def test_the_controls_can_fail(self):
        """A control that cannot fail is decoration. Break one and watch."""
        import bisect_vs_guess as lab
        kept = lab.bisection
        try:
            lab.bisection = lambda n: dict(
                strategy='bisection', oracle='region',
                expected_probes=linear_scan(n)['expected_probes'],
                worst_case=n, note='sabotaged')
            with self.assertRaises(lab.SearchError):
                lab.prove_the_claims()
        finally:
            lab.bisection = kept
        self.assertTrue(all(prove_the_claims().values()))

    def test_the_controls_catch_a_silence_claimed_as_proof(self):
        import bisect_vs_guess as lab
        kept = lab.quiet_interval_proves_what
        try:
            lab.quiet_interval_proves_what = lambda rate, days, \
                prior_fixed=0.5: dict(
                    rate_per_day=rate, watched_days=days,
                    prior_fixed=prior_fixed, p_quiet_if_still_broken=0.0,
                    p_fixed_given_quiet=1.0, note='sabotaged')
            with self.assertRaises(lab.SearchError):
                lab.prove_the_claims()
        finally:
            lab.quiet_interval_proves_what = kept

    def test_the_controls_catch_a_broken_probe_claim(self):
        import bisect_vs_guess as lab
        kept = lab.ping_proves_what
        try:
            lab.ping_proves_what = lambda members=8, broken=1: dict(
                members=members, broken=broken,
                p_one_probe_traverses_a_broken_member=1.0,
                p_probe_looks_healthy=0.0,
                probes_for_90_percent_confidence=1, note='sabotaged')
            with self.assertRaises(lab.SearchError):
                lab.prove_the_claims()
        finally:
            lab.ping_proves_what = kept

    def test_report_runs_and_prints_the_repaired_argument(self):
        buf = io.StringIO()
        report(out=buf)
        text = buf.getvalue()
        for needle in ('oracle', 'bisection', 'region', 'position'):
            self.assertIn(needle, text.lower(), msg=needle)

    def test_report_of_the_original_runs_too(self):
        buf = io.StringIO()
        report(out=buf, original=True)
        self.assertIn('converge', buf.getvalue().lower())

    def test_the_report_prints_no_percent_escapes(self):
        buf = io.StringIO()
        report(out=buf)
        self.assertNotIn('%%', buf.getvalue())

    def test_the_report_does_not_round_silence_into_certainty(self):
        buf = io.StringIO()
        report(out=buf)
        for line in buf.getvalue().splitlines():
            if 'days' in line and 'in ' in line:
                self.assertNotIn('100.000000%', line)

    def test_demo_original_states_what_changed(self):
        d = demo_original()
        self.assertIn('printed', d)
        self.assertIn('defects', d)
        self.assertIn('oracle', d['defects'].lower())
        self.assertIn('converge', d['defects'].lower())


if __name__ == '__main__':
    unittest.main(verbosity=0)
