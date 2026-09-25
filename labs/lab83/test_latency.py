import unittest
from latency_feasibility import *


class MultiSiteTests(unittest.TestCase):
    def test_propagation_units(self):
        self.assertEqual(rtt_ms(100)['propagation_rtt_ms'],1)
        self.assertEqual(rtt_ms(800)['propagation_rtt_ms'],8)
        self.assertEqual(rtt_ms(8000)['propagation_rtt_ms'],80)

    def test_explicit_route_and_additional_time(self):
        self.assertEqual(rtt_ms(1100,additional_rtt_ms=3),{'propagation_rtt_ms':11,'assumed_total_rtt_ms':14})

    def test_zero_route_still_has_processing(self):
        self.assertEqual(rtt_ms(0,additional_rtt_ms=2)['assumed_total_rtt_ms'],2)

    def test_invalid_speed(self):
        for speed in (0,-1,300000):
            with self.subTest(speed=speed),self.assertRaises(ValueError):rtt_ms(1,speed)

    def test_nonfinite_negative_and_type(self):
        for bad in (-1,float('nan'),float('inf'),True,'1',10**1000):
            with self.subTest(kind=type(bad).__name__),self.assertRaises(ValueError):rtt_ms(bad)
            with self.subTest(kind=type(bad).__name__),self.assertRaises(ValueError):replication(8,12,bad)

    def test_overflow(self):
        with self.assertRaises(ValueError):rtt_ms(1e308,1)
        with self.assertRaises(ValueError):transaction('huge',1e308,1000,1,1)
        with self.assertRaises(ValueError):replication(1e308,1e308,1e308)
        with self.assertRaises(ValueError):recovery({'a':1e308,'b':1e308})

    def test_rounds_change_result(self):
        self.assertEqual([transaction('x',14,r,8,40)['assumed_latency_ms'] for r in (1,2,3)],[22,36,50])
        self.assertEqual([transaction('x',14,r,8,40)['within_assumed_budget'] for r in (1,2,3)],[True,True,False])

    def test_no_universal_two_ms_cutoff(self):
        self.assertTrue(transaction('intercontinental',100,1,10,200)['within_assumed_budget'])

    def test_strict_model_input(self):
        for rounds in (-1,True,1.5,1001):
            with self.assertRaises(ValueError):transaction('x',1,rounds,1,1)
        with self.assertRaises(ValueError):transaction('',1,1,1,1)

    def test_budget_boundary_and_no_round(self):
        self.assertTrue(transaction('equal',14,3,8,50)['within_assumed_budget'])
        self.assertEqual(transaction('local',14,0,8,50)['assumed_latency_ms'],8)

    def test_replication_four_minute_outage(self):
        r=replication(8,12,240)
        self.assertEqual(r['backlog_MiB'],1920)
        self.assertEqual(r['catchup_s'],480)
        self.assertTrue(r['within_loss_window_budget'])
        self.assertEqual(12*480-8*480,1920)

    def test_replication_rpo_violation(self):
        r=replication(8,12,360)
        self.assertEqual(r['backlog_MiB'],2880)
        self.assertFalse(r['within_loss_window_budget'])

    def test_replication_cannot_catch_up(self):
        for apply in (0,7,8):
            self.assertIsNone(replication(8,apply,240)['catchup_s'])

    def test_no_writes_or_outage(self):
        self.assertEqual(replication(0,0,360)['backlog_MiB'],0)
        self.assertTrue(replication(0,0,360)['within_loss_window_budget'])
        self.assertEqual(replication(8,12,0)['catchup_s'],0)

    def test_recovery_budget(self):
        r=worksheet()['recovery_budget']
        self.assertEqual(r['assumed_total_s'],960)
        self.assertEqual(r['margin_s'],840)
        self.assertEqual(r['measured_RTO'],'NOT_RUN')

    def test_recovery_overrun(self):
        self.assertFalse(recovery({'detect':60,'restore':1800})['within_budget'])
        self.assertTrue(recovery({'complete':1800})['within_budget'])

    def test_recovery_invalid(self):
        for stages in ({},{'a':-1},{'':1},{1:1},[1,2]):
            with self.subTest(stages=stages),self.assertRaises(ValueError):recovery(stages)


if __name__=='__main__':unittest.main()
