import itertools
import unittest
from fractions import Fraction as F
from scaling import *


class ScalingTests(unittest.TestCase):
    def test_mesh_by_enumeration(self):
        for n in range(3,12):
            self.assertEqual(session_counts(n)['full_mesh_total'], len(list(itertools.combinations(range(n),2))))

    def test_RR_graph_degrees(self):
        for n in (3,24,240):
            edges={(0,1)} | {(r,c) for r in (0,1) for c in range(2,n)}
            degrees=[sum(i in edge for edge in edges) for i in range(n)]
            result=session_counts(n)
            self.assertEqual(len(edges),result['two_RR_total'])
            self.assertEqual(degrees[:2],[result['two_RR_per_RR']]*2)
            self.assertEqual(degrees[2:],[2]*(n-2))

    def test_published_sessions(self):
        self.assertEqual(session_counts(24)['full_mesh_total'],276)
        self.assertEqual(session_counts(240)['full_mesh_total'],28680)
        self.assertEqual(session_counts(24)['two_RR_total'],45)
        self.assertEqual(session_counts(240)['two_RR_total'],477)

    def test_no_universal_session_limit(self):
        self.assertEqual(session_counts(25)['full_mesh_total'],300)
        self.assertNotIn('supported',session_counts(25))

    def test_current_and_projected_headroom(self):
        current=capacity(40000,10000);future=capacity(40000,10000,F(3,2))
        self.assertEqual(current['margin'],20000)
        self.assertEqual(future['margin'],-10000)
        self.assertFalse(future['within_planning_limit'])
        self.assertTrue(future['within_physical_model_limit'])

    def test_capacity_boundary(self):
        self.assertEqual(capacity(40000,10000,F(4,3))['margin'],0)
        self.assertTrue(capacity(40000,10000,F(4,3))['within_planning_limit'])
        self.assertFalse(capacity(40001,10000,F(4,3))['within_planning_limit'])

    def test_joint_resources(self):
        self.assertTrue(capacity(75000,0)['within_planning_limit'])
        self.assertTrue(capacity(0,10000)['within_planning_limit'])
        self.assertFalse(capacity(75000,10000)['within_planning_limit'])

    def test_fluid_burst_balance(self):
        r=fluid_backlog(2500,2000,20,1000)
        self.assertEqual(r['backlog'],10000)
        self.assertEqual(r['drain_seconds'],10)
        self.assertEqual(2500*20-2000*20, r['backlog'])

    def test_no_drain_at_equal_or_higher_arrival(self):
        for a in (2000,2500):
            self.assertIsNone(fluid_backlog(2500,2000,20,a)['drain_seconds'])

    def test_no_backlog(self):
        self.assertEqual(fluid_backlog(1000,2000,20,1000)['backlog'],0)
        self.assertEqual(fluid_backlog(2500,2000,0,1000)['drain_seconds'],0)

    def test_operations(self):
        self.assertEqual(operations()['total_hours'],114)
        self.assertEqual(operations()['remaining_hours'],6)
        self.assertEqual(operations(24)['total_hours'],138)
        self.assertEqual(operations(24)['remaining_hours'],-18)

    def test_port_budget(self):
        self.assertEqual(leaf_limit(),56)
        self.assertEqual(leaf_limit(links_per_leaf=2),28)
        self.assertEqual(leaf_limit(ports=65,links_per_leaf=2),28)

    def test_port_exhaustion_and_reservation(self):
        self.assertEqual(leaf_limit(8,4,4),0)
        with self.assertRaises(ValueError):leaf_limit(7,4,4)

    def test_survivor_capacity(self):
        self.assertTrue(fabric_capacity()['meets_aggregate_demand'])
        self.assertFalse(fabric_capacity(failed=1)['meets_aggregate_demand'])
        self.assertEqual(fabric_capacity(failed=1)['margin_Gbps'],-20)

    def test_survivor_boundary(self):
        self.assertTrue(fabric_capacity(failed=1,demand=300)['meets_aggregate_demand'])
        self.assertEqual(fabric_capacity(failed=4)['remaining_Gbps'],0)
        with self.assertRaises(ValueError):fabric_capacity(failed=5)

    def test_bad_counts(self):
        for n in (True,-1,2.5,'4'):
            with self.subTest(n=n),self.assertRaises(ValueError):session_counts(n)
        with self.assertRaises(ValueError):session_counts(2)

    def test_bad_numeric_inputs(self):
        for n in (True,-1,float('nan'),float('inf'),'4',10**1000):
            with self.subTest(n=type(n).__name__),self.assertRaises(ValueError):fluid_backlog(n,2,3,1)
        for ceiling in (0,F(11,10)):
            with self.assertRaises(ValueError):capacity(1,1,ceiling=ceiling)

    def test_evidence_is_not_benchmark(self):
        result=worksheet()
        self.assertEqual(result['production_combined_scale_validation'],'NOT_RUN')
        self.assertEqual(result['production_tail_restoration_validation'],'NOT_RUN')


if __name__ == '__main__':unittest.main()
