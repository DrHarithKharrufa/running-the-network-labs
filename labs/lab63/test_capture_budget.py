"""Tests for lab 63.2.  Run: python3 test_capture_budget.py"""
import unittest

import capture_budget as cb


class FrameRateTests(unittest.TestCase):
    def test_line_rate_minimum_frames(self):
        self.assertAlmostEqual(cb.packets_per_second(10e9, 64),
                               10e9 / ((64 + 20) * 8), places=3)

    def test_larger_frames_are_fewer(self):
        self.assertLess(cb.packets_per_second(10e9, 1500),
                        cb.packets_per_second(10e9, 64))

    def test_runt_rejected(self):
        with self.assertRaises(cb.CaptureError):
            cb.packets_per_second(10e9, 32)

    def test_zero_rate_rejected(self):
        with self.assertRaises(cb.CaptureError):
            cb.packets_per_second(0, 64)


class SpanTests(unittest.TestCase):
    def test_one_direction_fits(self):
        self.assertTrue(cb.span_offer(10e9, directions=1,
                                      monitor_bits_per_second=10e9)['fits'])

    def test_both_directions_do_not(self):
        s = cb.span_offer(10e9, directions=2, monitor_bits_per_second=10e9)
        self.assertFalse(s['fits'])
        self.assertAlmostEqual(s['oversubscription'], 2.0)

    def test_two_links_both_ways_is_four_times(self):
        s = cb.span_offer(10e9, links_mirrored=2, directions=2,
                          monitor_bits_per_second=10e9)
        self.assertAlmostEqual(s['oversubscription'], 4.0)

    def test_utilisation_is_where_it_fits_until(self):
        s = cb.span_offer(10e9, directions=2, monitor_bits_per_second=10e9)
        self.assertAlmostEqual(s['max_utilisation_that_fits'], 0.5)
        self.assertTrue(cb.span_offer(10e9, directions=2,
                                      monitor_bits_per_second=10e9,
                                      utilisation=0.4)['fits'])

    def test_validation(self):
        for kw in (dict(directions=3), dict(links_mirrored=0),
                   dict(utilisation=0.0), dict(utilisation=1.5)):
            with self.subTest(**kw), self.assertRaises(cb.CaptureError):
                cb.span_offer(10e9, monitor_bits_per_second=10e9, **kw)


class OpticalTests(unittest.TestCase):
    def test_fifty_fifty_costs_about_three_db_each_way(self):
        b = cb.optical_tap_budget(-3.0, -14.4, 4.0, monitor_split=0.5,
                                  excess_loss_db=0.0)
        self.assertAlmostEqual(b['through_split_loss_db'], 3.0103, places=3)
        self.assertAlmostEqual(b['monitor_split_loss_db'], 3.0103, places=3)

    def test_asymmetric_split_favours_one_path(self):
        b = cb.optical_tap_budget(-3.0, -14.4, 4.0, monitor_split=0.30)
        self.assertGreater(b['through_path_receive_dbm'],
                           b['monitor_path_receive_dbm'])
        self.assertAlmostEqual(b['through_split_loss_db'], 1.5490, places=3)
        self.assertAlmostEqual(b['monitor_split_loss_db'], 5.2288, places=3)

    def test_a_small_tap_can_starve_the_monitor(self):
        b = cb.optical_tap_budget(-3.0, -14.4, 4.0, monitor_split=0.10)
        self.assertTrue(b['production_link_closes'])
        self.assertFalse(b['monitor_link_closes'])

    def test_tap_always_costs_the_through_path(self):
        b = cb.optical_tap_budget(-3.0, -14.4, 4.0, monitor_split=0.30)
        self.assertLess(b['through_path_receive_dbm'],
                        b['receive_power_without_tap_dbm'])

    def test_a_thin_margin_link_cannot_take_a_tap(self):
        b = cb.optical_tap_budget(-3.0, -14.4, 10.0, monitor_split=0.50)
        self.assertFalse(b['production_link_closes'])

    def test_validation(self):
        with self.assertRaises(cb.CaptureError):
            cb.optical_tap_budget(-3.0, -14.4, 4.0, monitor_split=0.0)
        with self.assertRaises(cb.CaptureError):
            cb.optical_tap_budget(-3.0, -14.4, 4.0, monitor_split=1.0)
        with self.assertRaises(cb.CaptureError):
            cb.optical_tap_budget(-3.0, -14.4, -1.0)
        with self.assertRaises(cb.CaptureError):
            cb.optical_tap_budget(-3.0, -14.4, 4.0, excess_loss_db=-1)


class RingTests(unittest.TestCase):
    def test_small_ring_at_line_rate_is_microseconds(self):
        pps = cb.packets_per_second(10e9, 64) * 2
        r = cb.ring_drain_time(4096, pps)
        self.assertLess(r['drain_microseconds'], 200)
        self.assertGreater(r['drain_microseconds'], 100)

    def test_bigger_ring_is_proportionally_longer(self):
        pps = cb.packets_per_second(10e9, 64) * 2
        a = cb.ring_drain_time(4096, pps)['drain_seconds']
        b = cb.ring_drain_time(16384, pps)['drain_seconds']
        self.assertAlmostEqual(b / a, 4.0, places=6)

    def test_larger_frames_give_more_time(self):
        small = cb.ring_drain_time(4096, cb.packets_per_second(10e9, 64))
        large = cb.ring_drain_time(4096, cb.packets_per_second(10e9, 1500))
        self.assertGreater(large['drain_seconds'], small['drain_seconds'])

    def test_validation(self):
        with self.assertRaises(cb.CaptureError):
            cb.ring_drain_time(0, 1000)
        with self.assertRaises(cb.CaptureError):
            cb.ring_drain_time(10, 0)


class DiskTests(unittest.TestCase):
    def test_full_capture_of_one_direction(self):
        # The chapter's 1.25 GB/s and 4.5 TB/hour: the 16-byte pcap record
        # header nearly offsets the 20 bytes of inter-frame overhead that is
        # not captured, which is why the round figure survives.
        d = cb.bytes_on_disk(10e9, 1500, None, directions=1)
        self.assertAlmostEqual(d['gigabytes_per_second'], 1.25, places=2)
        self.assertAlmostEqual(d['terabytes_per_hour'], 4.49, places=2)

    def test_both_directions_double_it(self):
        one = cb.bytes_on_disk(10e9, 800, None, 1)['bytes_per_second']
        two = cb.bytes_on_disk(10e9, 800, None, 2)['bytes_per_second']
        self.assertAlmostEqual(two / one, 2.0, places=9)

    def test_snaplen_reduces_and_is_reported_as_a_fraction(self):
        d = cb.bytes_on_disk(10e9, 800, 128, 2)
        self.assertLess(d['fraction_of_full_capture'], 0.25)
        self.assertGreater(d['fraction_of_full_capture'], 0.15)

    def test_snaplen_longer_than_the_frame_changes_nothing(self):
        a = cb.bytes_on_disk(10e9, 800, None, 2)['bytes_per_second']
        b = cb.bytes_on_disk(10e9, 800, 9000, 2)['bytes_per_second']
        self.assertAlmostEqual(a, b)

    def test_record_header_is_counted(self):
        d = cb.bytes_on_disk(10e9, 800, 64, 1)
        self.assertEqual(d['captured_bytes_per_packet'], 64)
        self.assertEqual(d['record_header_bytes'], cb.PCAP_RECORD_HEADER_BYTES)


class ChainTests(unittest.TestCase):
    def test_every_component_can_be_the_first_to_fail(self):
        p = cb.prove_every_component_can_fail()
        self.assertTrue(p['all_reachable'])
        self.assertTrue(p['clean_case_reachable'])
        self.assertEqual(p['branches'], 3)

    def test_a_tap_removes_the_mirror_finding_but_not_the_others(self):
        mirror = cb.first_bottleneck(10e9, 800, 10e9, 4096, 200e-6, 1e9,
                                     use_tap=False, links_mirrored=2)
        tap = cb.first_bottleneck(10e9, 800, 10e9, 4096, 200e-6, 1e9,
                                  use_tap=True, links_mirrored=2)
        names = {f['component'] for f in mirror['failing_components']}
        tapnames = {f['component'] for f in tap['failing_components']}
        self.assertIn('mirror destination', names)
        self.assertNotIn('mirror destination', tapnames)
        self.assertTrue(tapnames)

    def test_a_well_specified_path_reports_clean(self):
        r = cb.first_bottleneck(1e9, 1500, 10e9, 1 << 20, 1e-9, 1e12,
                                use_tap=True)
        self.assertTrue(r['lossless_on_these_numbers'])
        self.assertIsNone(r['first_to_discard'])
        self.assertIn('on these numbers', r['note'])

    def test_snaplen_can_rescue_the_storage_finding(self):
        full = cb.first_bottleneck(10e9, 800, 10e9, 1 << 20, 1e-9, 1e9,
                                   use_tap=True)
        snapped = cb.first_bottleneck(10e9, 800, 10e9, 1 << 20, 1e-9, 1e9,
                                      use_tap=True, snaplen=128)
        self.assertEqual(full['first_to_discard'], 'storage')
        self.assertIsNone(snapped['first_to_discard'])


if __name__ == '__main__':
    unittest.main(verbosity=0)
