"""Tests for lab 63.1.  Run: python3 test_sampling.py

The first block is the original test suite for the independent-selection model,
kept unchanged in substance. The blocks after it cover the systematic and
jittered selectors added when the lab was repaired a second time.
"""
import math
import unittest

from sampling_floor import (demo_original, expected_samples, export_load,
                            jittered_skip_seen, monte_carlo,
                            periodic_positions, prove_the_models_differ, run,
                            sampler_comparison, seen_probability,
                            systematic_phase_sweep, systematic_seen)


class SamplingTests(unittest.TestCase):
    """Independent selection: a probability, not a floor."""

    def test_empty_flow(self):
        self.assertEqual(seen_probability(0, 4000), 0)

    def test_unsampled(self):
        self.assertEqual(seen_probability(50, 1), 1)

    def test_single_packet(self):
        self.assertAlmostEqual(seen_probability(1, 4000), 1 / 4000)

    def test_exact_small_example(self):
        self.assertAlmostEqual(seen_probability(3, 2), 0.875)

    def test_no_hard_floor(self):
        self.assertGreater(seen_probability(50, 4000), 0)

    def test_n_packets_not_certain(self):
        self.assertTrue(0.63 < seen_probability(4000, 4000) < 0.64)

    def test_expected_count(self):
        self.assertEqual(expected_samples(4000000, 4000), 1000)

    def test_invalid_parameters(self):
        for bad in (-1, 1.5, True, '3'):
            with self.subTest(packets=bad), self.assertRaises(ValueError):
                seen_probability(bad, 100)
        for bad in (0, -1, 1.5, True, '100'):
            with self.subTest(one_in=bad), self.assertRaises(ValueError):
                seen_probability(50, bad)

    def test_simulation_endpoints(self):
        self.assertEqual(monte_carlo(0, 100, 20), 0)
        self.assertEqual(monte_carlo(5, 1, 20), 1)

    def test_seed_repeatability(self):
        self.assertEqual(monte_carlo(10, 20, 100, 1), monte_carlo(10, 20, 100, 1))


class SystematicTests(unittest.TestCase):
    """A fixed-skip sampler gives an outcome, not a probability."""

    def test_selects_its_own_phase(self):
        self.assertTrue(systematic_seen([7], 10, 7))
        self.assertFalse(systematic_seen([7], 10, 6))

    def test_any_matching_packet_suffices(self):
        self.assertTrue(systematic_seen([3, 7, 11], 10, 1))

    def test_phase_must_be_inside_the_period(self):
        with self.assertRaises(ValueError):
            systematic_seen([1], 10, 10)
        with self.assertRaises(ValueError):
            systematic_seen([1], 10, -1)

    def test_positions_are_periodic(self):
        self.assertEqual(periodic_positions(2, 3, 100),
                         [0, 1, 100, 101, 200, 201])
        self.assertEqual(periodic_positions(1, 2, 10, start=5), [5, 15])

    def test_position_validation(self):
        for kwargs in (dict(burst_packets=0), dict(bursts=0),
                       dict(packets_between_bursts=0), dict(start=-1)):
            base = dict(burst_packets=1, bursts=1, packets_between_bursts=10,
                        start=0)
            base.update(kwargs)
            with self.subTest(**kwargs), self.assertRaises(ValueError):
                periodic_positions(**base)

    def test_phase_lock_when_periods_share_a_factor(self):
        sweep = systematic_phase_sweep(3, 144, 6000, 2000)
        self.assertTrue(sweep['phase_locked'])
        self.assertEqual(sweep['distinct_residues'], 3)
        self.assertAlmostEqual(sweep['phases_that_see_it'], 3 / 2000.0)
        self.assertGreater(sweep['phases_that_never_see_it'], 0.99)

    def test_a_successful_phase_catches_every_burst(self):
        sweep = systematic_phase_sweep(3, 144, 6000, 2000)
        self.assertEqual(sweep['packets_caught_by_a_successful_phase']['minimum'],
                         144)

    def test_no_lock_when_periods_are_coprime(self):
        sweep = systematic_phase_sweep(1, 400, 2001, 2000)
        self.assertEqual(sweep['gcd_of_periods'], 1)
        self.assertFalse(sweep['phase_locked'])
        self.assertGreater(sweep['phases_that_see_it'],
                           systematic_phase_sweep(3, 144, 6000,
                                                  2000)['phases_that_see_it'])

    def test_result_is_scale_free(self):
        small = systematic_phase_sweep(3, 144, 6000, 2000)
        large = systematic_phase_sweep(3, 144, 120_000_000, 2000)
        self.assertAlmostEqual(small['phases_that_see_it'],
                               large['phases_that_see_it'])


class JitteredSkipTests(unittest.TestCase):
    """RFC 3176 asks for a randomised skip; this shows why."""

    def test_no_positions(self):
        self.assertFalse(jittered_skip_seen([], 100, 0.1, 1))

    def test_jitter_must_be_a_proportion(self):
        for bad in (-0.1, 1.0, 2.0):
            with self.subTest(jitter=bad), self.assertRaises(ValueError):
                jittered_skip_seen([1], 100, bad, 1)

    def test_seed_repeatability(self):
        a = jittered_skip_seen(list(range(0, 1000, 7)), 100, 0.1, 5)
        b = jittered_skip_seen(list(range(0, 1000, 7)), 100, 0.1, 5)
        self.assertEqual(a, b)

    def test_unsampled_period_sees_everything(self):
        self.assertTrue(jittered_skip_seen([0, 1, 2], 1, 0.0, 1))

    def test_jitter_beats_a_fixed_skip_on_a_locked_flow(self):
        c = sampler_comparison(3, 144, 6000, 2000, trials=200)
        fixed = c['jittered']['no jitter (fixed skip)']['observed']
        jittered = c['jittered']['RFC 3176 minimum, +-10%']['observed']
        self.assertLess(fixed, 0.02)
        self.assertGreater(jittered, 0.10)
        self.assertLess(fixed, jittered)

    def test_fixed_skip_simulation_matches_the_exact_sweep(self):
        c = sampler_comparison(3, 144, 6000, 2000, trials=400)
        self.assertLess(
            abs(c['jittered']['no jitter (fixed skip)']['observed']
                - c['systematic']['phases_that_see_it']), 0.02)

    def test_ten_per_cent_approaches_independent_selection(self):
        c = sampler_comparison(3, 144, 6000, 2000, trials=400)
        self.assertLess(
            abs(c['jittered']['RFC 3176 minimum, +-10%']['observed']
                - c['bernoulli']), 0.10)


class ExportLoadTests(unittest.TestCase):
    """Sampling divides the samples, not the export."""

    def test_samples_alone_scale_by_n(self):
        e = export_load(200_000, 2000)
        self.assertAlmostEqual(e['reduction_factor'], 2000.0, places=6)

    def test_counters_and_templates_break_the_division(self):
        e = export_load(200_000, 2000, counter_samples_per_second=40,
                        template_bytes_per_minute=64_000)
        self.assertLess(e['reduction_factor'], 2000)
        self.assertGreater(e['reduction_factor'], 1)

    def test_unsampled_has_no_reduction(self):
        self.assertAlmostEqual(export_load(1000, 1)['reduction_factor'], 1.0)

    def test_rate_validation(self):
        with self.assertRaises(ValueError):
            export_load(-1, 100)
        with self.assertRaises(ValueError):
            export_load(100, 0)
        with self.assertRaises(ValueError):
            export_load(100, 100, counter_samples_per_second=-1)


class ProvenanceTests(unittest.TestCase):
    """The lab states what it used to compute, and the controls fire."""

    def test_original_model_produced_a_false_zero(self):
        d = demo_original()
        beacon = [r for r in d['rows'] if '50' in r['flow']][0]
        self.assertEqual(beacon['sampled_by_old_model'], 0)
        self.assertIn('INVISIBLE', beacon['old_verdict'])
        self.assertGreater(beacon['actual_probability'], 0)

    def test_controls_all_pass(self):
        self.assertTrue(all(prove_the_models_differ().values()))

    def test_run_keeps_the_original_contract(self):
        r = run()
        for key in ('scope', 'cases', 'simulation'):
            self.assertIn(key, r)
        self.assertTrue(r['simulation']['within_six_standard_errors'])
        self.assertEqual(r['simulation']['seed'], 63)
        self.assertIn('phase_demonstration', r)
        self.assertTrue(r['scale_check']['identical'])

    def test_simulation_is_within_six_standard_errors(self):
        p = seen_probability(50, 4000)
        observed = monte_carlo(50, 4000, 100000)
        se = math.sqrt(p * (1 - p) / 100000)
        self.assertLessEqual(abs(observed - p), 6 * se)


if __name__ == '__main__':
    unittest.main(verbosity=0)
