"""Tests for lab 64.3.  Run: python3 test_control_vs_data_plane.py

The chapter claimed the data plane "only ever does what the control plane told
it to". That is a universal, so these tests check the counterexamples one at a
time: for every stage a control-plane read cannot reach, a device on which
every control-plane reading is clean and the packet is still dropped. They
also check the second half of the finding --- that a fixed check order costs
real time on symptoms that point elsewhere --- against an exhaustive search
over all orderings, so the "best" column is measured rather than asserted.
"""
import itertools
import contextlib
import io
import math
import unittest

import control_vs_data_plane as lab
from control_vs_data_plane import (BEYOND_CONTROL_PLANE, CHECKS,
                                   CONTROL_PLANE_FIRST, CONTROL_PLANE_VISIBLE,
                                   EGRESS_FIRST, FAULT_WEIGHTS, STAGES,
                                   SYMPTOMS, PipelineError, best_possible,
                                   control_plane_coverage,
                                   control_plane_reads_clean, counterexamples,
                                   demo_original, ecmp_blind_spot,
                                   expected_minutes, forward, healthy_device,
                                   member_for, policy_comparison,
                                   prove_the_claims, report, sensitivity,
                                   symptom_directed)

FLOW = dict(src='10.20.30.44', dst='192.0.2.9', sport=51344, dport=443)


class ModelShapeTests(unittest.TestCase):

    def test_the_stages_are_in_forwarding_order(self):
        names = [name for name, _, _ in STAGES]
        self.assertEqual(names[:2], ['route', 'resolution'])
        self.assertEqual(names[-1], 'egress')
        self.assertEqual(len(names), len(set(names)))

    def test_the_two_visibility_sets_partition_the_stages(self):
        self.assertEqual(set(CONTROL_PLANE_VISIBLE) | set(BEYOND_CONTROL_PLANE),
                         {name for name, _, _ in STAGES})
        self.assertFalse(set(CONTROL_PLANE_VISIBLE)
                         & set(BEYOND_CONTROL_PLANE))

    def test_the_control_plane_sees_a_minority_of_stages(self):
        self.assertLess(len(CONTROL_PLANE_VISIBLE), len(STAGES) / 2.0)

    def test_every_stage_is_explained(self):
        for name, description, _ in STAGES:
            self.assertGreater(len(description), 25, msg=name)


class PipelineTests(unittest.TestCase):

    def test_a_healthy_device_forwards(self):
        delivered, stage, why = forward(healthy_device(), FLOW)
        self.assertTrue(delivered)
        self.assertIsNone(stage)
        self.assertEqual(why, 'delivered')

    def test_each_stage_can_stop_the_packet_on_its_own(self):
        for name in ('route', 'resolution', 'fib', 'rewrite', 'hardware'):
            with self.subTest(stage=name):
                d = healthy_device()
                d[name] = False
                delivered, stage, _ = forward(d, FLOW)
                self.assertFalse(delivered)
                self.assertEqual(stage, name)

    def test_the_first_broken_stage_is_the_one_reported(self):
        d = healthy_device()
        d['fib'] = False
        d['rewrite'] = False
        _, stage, _ = forward(d, FLOW)
        self.assertEqual(stage, 'fib')

    def test_the_size_boundary_is_exact(self):
        d = healthy_device(egress_mtu=1400)
        self.assertTrue(forward(d, FLOW, 1399)[0])
        self.assertTrue(forward(d, FLOW, 1400)[0])
        delivered, stage, _ = forward(d, FLOW, 1401)
        self.assertFalse(delivered)
        self.assertEqual(stage, 'egress')

    def test_a_filter_matches_one_source_and_not_another(self):
        d = healthy_device()
        d['egress_filter'] = lambda f: f['src'] == '10.20.30.44'
        self.assertFalse(forward(d, FLOW)[0])
        other = dict(FLOW, src='10.20.30.45')
        self.assertTrue(forward(d, other)[0])

    def test_member_selection_is_stable_across_processes(self):
        """hash() is salted per run; this lab's numbers must not be.

        Re-derived here from the checksum rather than pinned to a number
        copied out of one run, so the test would still catch a silent switch
        back to hash().
        """
        import zlib
        key = '|'.join(str(FLOW[f]) for f in ('src', 'dst', 'sport', 'dport'))
        expected = zlib.crc32(key.encode('utf-8')) % 8
        self.assertEqual(member_for(FLOW, 8), expected)
        self.assertEqual(member_for(FLOW, 8), member_for(dict(FLOW), 8))

    def test_member_selection_stays_inside_the_bundle(self):
        for members in (1, 2, 3, 8, 16):
            for i in range(200):
                f = dict(FLOW, sport=20000 + i)
                self.assertIn(member_for(f, members), range(members))

    def test_impossible_devices_and_packets_are_refused(self):
        for members in (0, -1, 1.5, True, 'four'):
            with self.subTest(members=members), self.assertRaises(PipelineError):
                d = healthy_device(); d['members'] = members
                forward(d, FLOW)
        for broken in (-1, 4, 99):
            with self.subTest(broken=broken), self.assertRaises(PipelineError):
                d = healthy_device(members=4)
                d['hardware_broken_member'] = broken
                forward(d, FLOW)
        for size in (0, -1, 1.5, True, '1500'):
            with self.subTest(size=size), self.assertRaises(PipelineError):
                forward(healthy_device(), FLOW, size)


class CounterexampleTests(unittest.TestCase):
    """TE-0623: a correct control plane does not guarantee forwarding."""

    def test_every_counterexample_reads_clean_and_still_drops(self):
        cases = counterexamples()
        self.assertGreaterEqual(len(cases), 6)
        for case in cases:
            with self.subTest(case=case['title']):
                self.assertTrue(case['control_plane_clean'])
                self.assertFalse(case['delivered'])
                self.assertIn(case['stage'], BEYOND_CONTROL_PLANE)

    def test_every_invisible_stage_has_a_counterexample(self):
        stages = {case['stage'] for case in counterexamples()}
        self.assertEqual(stages, set(BEYOND_CONTROL_PLANE))

    def test_each_counterexample_says_what_it_looks_like_in_practice(self):
        for case in counterexamples():
            self.assertGreater(len(case['note']), 40, msg=case['title'])
            self.assertGreater(len(case['why']), 20, msg=case['title'])

    def test_control_plane_reads_clean_is_not_trivially_true(self):
        d = healthy_device()
        self.assertTrue(control_plane_reads_clean(d))
        for name in CONTROL_PLANE_VISIBLE:
            with self.subTest(stage=name):
                broken = healthy_device()
                broken[name] = False
                self.assertFalse(control_plane_reads_clean(broken))

    def test_the_counterexamples_do_not_touch_the_control_plane(self):
        for case in counterexamples():
            for name in CONTROL_PLANE_VISIBLE:
                self.assertTrue(case['device'][name], msg=case['title'])


class BundleTests(unittest.TestCase):
    """TE-0621's companion: what a single successful probe is worth."""

    def test_one_dead_member_of_eight_hides_from_most_flows(self):
        r = ecmp_blind_spot(members=8, trials=4096)
        self.assertAlmostEqual(r['failing_fraction'], 0.125, delta=0.02)
        self.assertAlmostEqual(r['one_probe_looks_healthy'],
                               1.0 - r['failing_fraction'])

    def test_the_result_is_reproducible(self):
        self.assertEqual(ecmp_blind_spot(members=8, trials=1024),
                         ecmp_blind_spot(members=8, trials=1024))

    def test_a_single_member_bundle_hides_nothing(self):
        r = ecmp_blind_spot(members=1, trials=256)
        self.assertAlmostEqual(r['failing_fraction'], 1.0)

    def test_a_wider_bundle_hides_more(self):
        narrow = ecmp_blind_spot(members=2, trials=4096)
        wide = ecmp_blind_spot(members=16, trials=4096)
        self.assertGreater(wide['one_probe_looks_healthy'],
                           narrow['one_probe_looks_healthy'])


class CoverageTests(unittest.TestCase):

    def test_the_two_shares_add_to_one(self):
        cov = control_plane_coverage()
        self.assertAlmostEqual(cov['visible'] + cov['invisible'], 1.0)

    def test_the_conditional_distribution_is_a_distribution(self):
        cov = control_plane_coverage()
        self.assertAlmostEqual(sum(cov['given_clean'].values()), 1.0)
        self.assertEqual(set(cov['given_clean']), set(BEYOND_CONTROL_PLANE))

    def test_a_control_plane_read_reaches_under_half_the_stated_weight(self):
        self.assertLess(control_plane_coverage()['visible'], 0.5)

    def test_coverage_rises_with_the_weight_on_a_missing_route(self):
        rows = sensitivity()
        visible = [v for _, v, _ in rows]
        self.assertEqual(visible, sorted(visible))

    def test_no_weighting_in_the_sweep_supports_almost_always(self):
        self.assertLess(max(v for _, v, _ in sensitivity()), 0.9)

    def test_the_invisible_share_is_never_empty(self):
        for _, _, invisible in sensitivity():
            self.assertGreater(invisible, 0.0)

    def test_incomplete_or_empty_weights_are_refused(self):
        short = {k: v for k, v in FAULT_WEIGHTS.items() if k != 'egress'}
        with self.assertRaises(PipelineError):
            control_plane_coverage(short)
        with self.assertRaises(PipelineError):
            control_plane_coverage({k: 0.0 for k in FAULT_WEIGHTS})


class OrderingTests(unittest.TestCase):
    """TE-0623's second half: a mandatory sequence can waste time."""

    def test_every_check_localises_a_real_stage(self):
        covered = set()
        for name, (cost, covers) in CHECKS.items():
            self.assertGreater(cost, 0.0, msg=name)
            for stage in covers:
                self.assertIn(stage, {s for s, _, _ in STAGES}, msg=name)
                covered.add(stage)
        self.assertEqual(covered, {s for s, _, _ in STAGES})

    def test_both_fixed_orders_are_permutations_of_the_checks(self):
        self.assertEqual(sorted(CONTROL_PLANE_FIRST), sorted(CHECKS))
        self.assertEqual(sorted(EGRESS_FIRST), sorted(CHECKS))
        self.assertEqual(tuple(reversed(EGRESS_FIRST)), CONTROL_PLANE_FIRST)

    def test_the_directed_order_matches_the_exhaustive_optimum(self):
        for symptom, weights in SYMPTOMS.items():
            with self.subTest(symptom=symptom):
                directed = expected_minutes(symptom_directed(weights), weights)
                best, _ = best_possible(weights)
                self.assertAlmostEqual(directed, best, places=9)

    def test_the_exhaustive_search_really_is_exhaustive(self):
        self.assertEqual(math.factorial(len(CHECKS)), 720)
        weights = SYMPTOMS['small packets pass and large ones do not']
        best, order = best_possible(weights)
        for candidate in itertools.permutations(CHECKS):
            self.assertLessEqual(best - 1e-9,
                                 expected_minutes(candidate, weights))
        self.assertEqual(len(set(order)), len(CHECKS))

    def test_a_fixed_order_wins_where_the_symptom_points_at_it(self):
        rows = {r['symptom']: r for r in policy_comparison()}
        row = rows['nothing reaches this prefix from anywhere']
        self.assertLess(row['control_first'] - row['best'], 1.0)
        self.assertLess(row['control_first'], row['egress_first'])

    def test_and_costs_real_time_where_it_does_not(self):
        rows = {r['symptom']: r for r in policy_comparison()}
        for symptom in ('the port shows errors and the light is flapping',
                        'small packets pass and large ones do not'):
            with self.subTest(symptom=symptom):
                row = rows[symptom]
                self.assertGreater(row['control_first'] - row['best'], 5.0)
                self.assertLess(row['egress_first'], row['control_first'])

    def test_neither_fixed_order_wins_everywhere(self):
        rows = policy_comparison()
        self.assertTrue(any(r['control_first'] < r['egress_first']
                            for r in rows))
        self.assertTrue(any(r['egress_first'] < r['control_first']
                            for r in rows))

    def test_expected_minutes_is_bounded_by_the_full_sweep(self):
        for weights in SYMPTOMS.values():
            total = sum(cost for cost, _ in CHECKS.values())
            cost = expected_minutes(CONTROL_PLANE_FIRST, weights)
            self.assertGreater(cost, 0.0)
            self.assertLessEqual(cost, total + 1e-9)

    def test_a_partial_order_is_charged_for_what_it_cannot_find(self):
        weights = SYMPTOMS['the port shows errors and the light is flapping']
        partial = ('read the routing table',)
        full = expected_minutes(CONTROL_PLANE_FIRST, weights)
        self.assertGreater(expected_minutes(partial, weights), 0.0)
        self.assertGreater(expected_minutes(partial, weights) / full, 0.0)

    def test_every_symptom_weight_set_is_a_distribution_over_stages(self):
        for symptom, weights in SYMPTOMS.items():
            with self.subTest(symptom=symptom):
                self.assertEqual(set(weights), {s for s, _, _ in STAGES})
                self.assertAlmostEqual(sum(weights.values()), 1.0)

    def test_an_unknown_check_is_refused(self):
        with self.assertRaises(PipelineError):
            expected_minutes(('stare at it',), FAULT_WEIGHTS)
        with self.assertRaises(PipelineError):
            expected_minutes(CONTROL_PLANE_FIRST,
                             {k: 0.0 for k in FAULT_WEIGHTS})


class HarnessTests(unittest.TestCase):
    """FR-0054: the controls are an instrument. Check the instrument."""

    def test_all_controls_pass(self):
        results = prove_the_claims()
        self.assertGreaterEqual(len(results), 9)
        failed = [claim for claim, ok, _ in results if not ok]
        self.assertEqual(failed, [], msg=f'failing controls: {failed}')

    def test_every_control_reports_a_detail(self):
        for claim, _, detail in prove_the_claims():
            self.assertTrue(claim.strip())
            self.assertTrue(detail.strip(), msg=claim)

    def test_the_controls_notice_a_pipeline_that_always_delivers(self):
        kept = lab.forward
        try:
            lab.forward = lambda device, flow, size=1400: (True, None,
                                                           'sabotaged')
            failed = [claim for claim, ok, _ in lab.prove_the_claims()
                      if not ok]
            self.assertTrue(failed, 'the controls passed a pipeline that '
                                    'never drops anything')
        finally:
            lab.forward = kept
        self.assertEqual([c for c, ok, _ in prove_the_claims() if not ok], [])

    def test_the_controls_notice_a_control_plane_claiming_more_than_it_sees(self):
        kept = lab.CONTROL_PLANE_VISIBLE
        try:
            lab.CONTROL_PLANE_VISIBLE = ('route', 'resolution', 'fib',
                                         'rewrite', 'hardware')
            failed = [claim for claim, ok, _ in lab.prove_the_claims()
                      if not ok]
            self.assertTrue(failed, 'the controls passed a control plane that '
                                    'claims to see programmed state')
        finally:
            lab.CONTROL_PLANE_VISIBLE = kept
        self.assertEqual([c for c, ok, _ in prove_the_claims() if not ok], [])

    def test_report_runs_clean(self):
        lines = []
        self.assertEqual(report(out=lines.append), 0)
        text = ' '.join(lines).lower()
        for needle in ('control plane', 'egress',
                       'whose traffic fails', 'controls', '720',
                       'clean', 'dropped at'):
            self.assertIn(needle, text, msg=needle)

    def test_report_of_the_original_states_the_claim_being_refuted(self):
        lines = []
        demo_original(out=lines.append)
        text = ' '.join(lines).lower()
        self.assertIn('only ever does what the control plane told it', text)
        self.assertIn('almost always', text)

    def test_main_accepts_only_its_own_flag(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lab.main([]), 0)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lab.main(['--demo-original']), 0)
        with self.assertRaises(SystemExit):
            lab.main(['--nonsense'])


if __name__ == '__main__':
    unittest.main(verbosity=0)
