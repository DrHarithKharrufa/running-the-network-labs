"""Tests for lab 63.3.  Run: python3 test_log_delivery.py"""
import unittest

import log_delivery as ld


class GuaranteeTests(unittest.TestCase):
    def test_every_transport_states_what_it_does_not_do(self):
        for name in ld.TRANSPORTS:
            with self.subTest(name=name):
                self.assertTrue(ld.transport(name)['does_not'].strip())

    def test_udp_promises_nothing(self):
        t = ld.transport('syslog over UDP')
        self.assertFalse(t['delivery_acknowledged'])
        self.assertFalse(t['detects_loss'])

    def test_tcp_acknowledges_but_is_not_durable(self):
        t = ld.transport('syslog over TCP')
        self.assertTrue(t['delivery_acknowledged'])
        self.assertFalse(t['receiver_process_receipt'])
        self.assertFalse(t['durable_commit'])

    def test_tls_adds_nothing_to_durability(self):
        tcp = ld.transport('syslog over TCP')
        tls = ld.transport('syslog over TLS/TCP')
        for prop in ld.PROPERTIES:
            self.assertEqual(tcp[prop], tls[prop], prop)

    def test_disk_queue_is_durable_but_not_replicated(self):
        t = ld.transport('relay with disk queue')
        self.assertTrue(t['durable_commit'])
        self.assertFalse(t['replicated'])

    def test_only_acks_all_is_replicated(self):
        replicated = [n for n in ld.TRANSPORTS if ld.transport(n)['replicated']]
        self.assertEqual(replicated, ['Kafka, acks=all, min.insync=2 of 3'])

    def test_unknown_transport_names_the_known_ones(self):
        with self.assertRaises(ld.DeliveryError) as ctx:
            ld.transport('carrier pigeon')
        self.assertIn('syslog over UDP', str(ctx.exception))


class BufferTests(unittest.TestCase):
    def test_a_default_queue_does_not_survive_a_quarter_hour(self):
        b = ld.buffer_survival(8000, 50_000, 900)
        self.assertFalse(b['holds'])
        self.assertAlmostEqual(b['seconds_of_headroom'], 6.25)
        self.assertAlmostEqual(b['events_lost'], 8000 * 900 - 50_000)

    def test_an_exactly_sized_queue_holds(self):
        self.assertTrue(ld.buffer_survival(8000, 7_200_000, 900)['holds'])

    def test_one_more_second_overflows_it(self):
        self.assertFalse(ld.buffer_survival(8000, 7_200_000, 901)['holds'])

    def test_sizing_matches_survival(self):
        z = ld.buffer_sizing(8000, 900)
        self.assertEqual(z['events_required'], 7_200_000)
        self.assertAlmostEqual(z['gigabytes_required'], 2.88, places=6)

    def test_validation(self):
        with self.assertRaises(ld.DeliveryError):
            ld.buffer_survival(-1, 10, 10)
        with self.assertRaises(ld.DeliveryError):
            ld.buffer_sizing(0, 900)
        with self.assertRaises(ld.DeliveryError):
            ld.buffer_sizing(8000, 0)


class DrainTests(unittest.TestCase):
    def test_a_sink_no_faster_than_the_source_never_drains(self):
        for sink in (7_000, 8_000):
            with self.subTest(sink=sink):
                d = ld.drain_time(8000, sink, 7_200_000)
                self.assertFalse(d['drains'])
                self.assertIsNone(d['seconds_to_drain'])

    def test_the_surplus_is_the_divisor_not_the_sink_rate(self):
        d = ld.drain_time(8000, 10_000, 7_200_000)
        self.assertTrue(d['drains'])
        self.assertAlmostEqual(d['seconds_to_drain'], 3600.0)
        self.assertAlmostEqual(d['naive_seconds'], 720.0)
        self.assertAlmostEqual(d['optimism_factor'], 5.0)

    def test_a_much_faster_sink_approaches_the_naive_answer(self):
        d = ld.drain_time(8000, 800_000, 7_200_000)
        self.assertLess(d['optimism_factor'], 1.02)

    def test_validation(self):
        with self.assertRaises(ld.DeliveryError):
            ld.drain_time(8000, 0, 100)
        with self.assertRaises(ld.DeliveryError):
            ld.drain_time(-1, 100, 100)
        with self.assertRaises(ld.DeliveryError):
            ld.drain_time(100, 200, -1)


class KafkaTests(unittest.TestCase):
    def test_acks_zero_survives_nothing(self):
        k = ld.kafka_durability(0, 3, 2)
        self.assertEqual(k['copies_at_acknowledgement'], 0)
        self.assertFalse(k['survives'])

    def test_acks_one_does_not_survive_losing_the_leader(self):
        self.assertFalse(ld.kafka_durability(1, 3, 2)['survives'])

    def test_acks_all_with_two_in_sync_survives_one_broker(self):
        self.assertTrue(ld.kafka_durability('all', 3, 2)['survives'])

    def test_acks_all_with_one_in_sync_is_acks_one(self):
        self.assertFalse(ld.kafka_durability('all', 3, 1)['survives'])

    def test_two_brokers_lost_defeats_two_in_sync_copies(self):
        self.assertFalse(ld.kafka_durability('all', 3, 2,
                                             brokers_lost=2)['survives'])

    def test_unclean_election_defeats_the_safe_setting(self):
        k = ld.kafka_durability('all', 3, 2, unclean_leader_election=True)
        self.assertFalse(k['survives'])
        self.assertTrue(any('unclean' in r for r in k['reasons']))

    def test_retention_is_named_as_a_separate_risk(self):
        self.assertIn('retention', ld.kafka_durability('all', 3, 2)['note'])

    def test_validation(self):
        with self.assertRaises(ld.DeliveryError):
            ld.kafka_durability(2, 3, 2)
        with self.assertRaises(ld.DeliveryError):
            ld.kafka_durability('all', 2, 3)
        with self.assertRaises(ld.DeliveryError):
            ld.kafka_durability('all', 3, 0)


class AccountingTests(unittest.TestCase):
    def test_three_gaps_with_three_causes(self):
        a = ld.accounting(1000, 994, 961, 947)
        self.assertEqual([g['lost'] for g in a['gaps']], [6, 33, 14])
        self.assertEqual(a['total_lost'], 53)
        self.assertEqual(len({g['means'] for g in a['gaps']}), 3)

    def test_a_perfect_pipeline_reports_no_gaps(self):
        a = ld.accounting(100, 100, 100, 100)
        self.assertEqual(a['total_lost'], 0)
        self.assertEqual(a['end_to_end_fraction'], 1.0)

    def test_counts_must_not_increase_along_the_pipeline(self):
        with self.assertRaises(ld.DeliveryError) as ctx:
            ld.accounting(100, 120, 100, 100)
        self.assertIn('duplicating', str(ctx.exception))

    def test_negative_counts_rejected(self):
        with self.assertRaises(ld.DeliveryError):
            ld.accounting(-1, 0, 0, 0)


class ControlTests(unittest.TestCase):
    def test_all_controls_pass(self):
        self.assertTrue(all(ld.prove_the_distinctions_bite().values()))

    def test_every_property_column_separates_something(self):
        for prop in ld.PROPERTIES:
            with self.subTest(prop=prop):
                values = {t[prop] for t in ld.TRANSPORTS.values()}
                self.assertEqual(len(values), 2)


if __name__ == '__main__':
    unittest.main(verbosity=0)
