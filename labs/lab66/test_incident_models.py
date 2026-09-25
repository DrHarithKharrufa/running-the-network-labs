"""Behavioural tests, including negative inputs, boundaries and counterexamples."""
import unittest
from dataclasses import replace
from timeline import Event, order, utc
from renewal_gate import assess, fixture, examples


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.a = Event('router:17', '2026-09-24T02:40:05Z', '2026-09-24T02:40:20Z',
                       '2026-09-24T02:41:00Z', 4, 2)
        self.b = replace(self.a, source='probe:31', event_time='2026-09-24T02:40:03Z',
                         clock_offset_s=0, uncertainty_s=1)

    def test_offset_direction_and_bounds(self):
        self.assertEqual(self.a.interval(), (utc('2026-09-24T02:39:59Z'), utc('2026-09-24T02:40:03Z')))

    def test_overlap_does_not_imply_simultaneous_events(self):
        self.assertEqual(order(self.a, self.b), 'OVERLAP')

    def test_zero_uncertainty_can_change_inference(self):
        self.assertEqual(order(replace(self.a, uncertainty_s=0), replace(self.b, uncertainty_s=0)), 'BEFORE')

    def test_opposite_order(self):
        self.assertEqual(order(replace(self.b, uncertainty_s=0), replace(self.a, uncertainty_s=0)), 'AFTER')

    def test_touching_bounds_are_not_strict_order(self):
        self.assertEqual(order(self.a, replace(self.b, uncertainty_s=0)), 'OVERLAP')

    def test_missing_event_is_not_replaced_by_observation(self):
        self.assertEqual(order(self.a, replace(self.b, event_time=None)), 'UNKNOWN')

    def test_unknown_offset(self):
        self.assertEqual(order(self.a, replace(self.b, clock_offset_s=None)), 'UNKNOWN')

    def test_unknown_uncertainty(self):
        self.assertIsNone(replace(self.a, uncertainty_s=None).interval())

    def test_receipt_time_does_not_reorder_events(self):
        self.assertEqual(replace(self.a, reported_at='2026-09-25T02:41:00Z').interval(), self.a.interval())

    def test_equivalent_explicit_timezone(self):
        self.assertEqual(replace(self.a, event_time='2026-09-24T03:40:05+01:00').interval(), self.a.interval())

    def test_unknown_timezone_rejected(self):
        with self.assertRaises(ValueError): replace(self.a, event_time='2026-09-24T02:40:05')

    def test_invalid_timestamp_rejected(self):
        with self.assertRaises(ValueError): replace(self.a, reported_at='2026-02-30T00:00:00Z')

    def test_missing_source_rejected(self):
        with self.assertRaises(ValueError): replace(self.a, source=' ')

    def test_bad_numeric_bounds_rejected(self):
        for value in [-1, float('nan'), float('inf'), True, '2']:
            with self.subTest(value=value), self.assertRaises(ValueError): replace(self.a, uncertainty_s=value)

    def test_negative_offset_is_valid(self):
        self.assertEqual(replace(self.a, clock_offset_s=-4, uncertainty_s=0).interval()[0], utc('2026-09-24T02:40:09Z'))

    def test_order_invariant_under_common_translation(self):
        self.assertEqual(order(self.a, self.b), order(replace(self.a, clock_offset_s=14), replace(self.b, clock_offset_s=10)))


class RenewalTests(unittest.TestCase):
    def setUp(self):
        self.targets, self.rows, self.policy = fixture()

    def verdict(self, rows=None, **policy):
        return assess(self.targets, self.rows if rows is None else rows, **(self.policy | policy))['verdict']

    def changed(self, **fields):
        return [self.rows[0], replace(self.rows[1], **fields)]

    def test_complete_fixture_passes(self):
        self.assertEqual(self.verdict(), 'PASS')

    def test_renewal_without_activation_fails(self):
        self.assertEqual(self.verdict(self.changed(served_fingerprint='b'*64)), 'FAIL')

    def test_missing_target_cannot_pass(self):
        self.assertEqual(self.verdict(self.rows[:1]), 'UNKNOWN')

    def test_no_samples_cannot_pass(self):
        self.assertEqual(self.verdict([]), 'UNKNOWN')

    def test_tls_failure(self):
        self.assertEqual(self.verdict(self.changed(tls_validated=False)), 'FAIL')

    def test_tls_unknown(self):
        self.assertEqual(self.verdict(self.changed(tls_validated=None)), 'UNKNOWN')

    def test_fail_dominates_missing(self):
        self.assertEqual(self.verdict([replace(self.rows[0], tls_validated=False)]), 'FAIL')

    def test_stale(self):
        self.assertEqual(self.verdict(self.changed(sampled_at='2026-09-24T02:58:59Z')), 'UNKNOWN')

    def test_future_sample(self):
        self.assertEqual(self.verdict(self.changed(sampled_at='2026-09-24T03:00:01Z')), 'UNKNOWN')

    def test_freshness_boundary(self):
        self.assertEqual(self.verdict(self.changed(sampled_at='2026-09-24T02:59:00Z')), 'PASS')

    def test_expired(self):
        self.assertEqual(self.verdict(self.changed(not_after='2026-09-24T03:00:00Z')), 'FAIL')

    def test_sub_microsecond_reserve_cannot_admit_expired(self):
        self.assertEqual(self.verdict(self.changed(not_after='2026-09-24T03:00:00Z'), min_remaining_s=1e-7), 'FAIL')

    def test_reserve_boundary(self):
        self.assertEqual(self.verdict(self.changed(not_after='2026-10-01T03:00:00Z')), 'PASS')

    def test_just_under_reserve(self):
        self.assertEqual(self.verdict(self.changed(not_after='2026-10-01T02:59:59Z')), 'FAIL')

    def test_not_yet_valid_at_sample(self):
        self.assertEqual(self.verdict(self.changed(not_before='2026-09-24T02:59:31Z')), 'FAIL')

    def test_empty_scope_rejected(self):
        with self.assertRaises(ValueError): assess({}, [], **self.policy)

    def test_duplicate_target_rejected(self):
        with self.assertRaises(ValueError): self.verdict(self.rows + self.rows[:1])

    def test_unexpected_target_rejected(self):
        with self.assertRaises(ValueError): self.verdict(self.rows + [replace(self.rows[0], target='other')])

    def test_bad_policy_rejected(self):
        for field in ['max_age_s', 'min_remaining_s']:
            for value in [0, -1, True, float('inf'), float('nan')]:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError): self.verdict(**{field:value})

    def test_invalid_boolean_rejected(self):
        for value in ['true', 1, 0]:
            with self.subTest(value=value), self.assertRaises(ValueError): self.changed(tls_validated=value)

    def test_invalid_certificate_period_rejected(self):
        with self.assertRaises(ValueError): self.changed(not_after=self.rows[1].not_before)

    def test_bad_fingerprint_rejected(self):
        with self.assertRaises(ValueError): self.changed(served_fingerprint='certificate-issued')

    def test_no_timezone_rejected(self):
        with self.assertRaises(ValueError): self.verdict(now='2026-09-24T03:00:00')

    def test_sample_order_does_not_change_result(self):
        self.assertEqual(assess(self.targets, self.rows, **self.policy), assess(self.targets, list(reversed(self.rows)), **self.policy))

    def test_book_scenario_verdicts(self):
        self.assertEqual({key:value['verdict'] for key,value in examples()['cases'].items()},
                         {'issued_but_second_target_still_old':'FAIL', 'second_target_not_sampled':'UNKNOWN',
                          'both_targets_checked':'PASS', 'validation_failed':'FAIL', 'stale_observation':'UNKNOWN'})


if __name__ == '__main__':
    unittest.main()
