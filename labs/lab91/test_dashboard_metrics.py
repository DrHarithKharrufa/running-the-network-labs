import unittest
from fractions import Fraction as F
import dashboard_metrics as d


class DashboardTests(unittest.TestCase):
    def test_overlap_and_population(self):
        r=d.impact({'A':[(0,10),(5,15)],'B':[(5,15)]},['A','B','C','D'],60,complete_evidence=True)
        self.assertEqual(r['unavailable_customer_minutes'],25)
        self.assertEqual(r['eligible_customer_minutes'],240)
        self.assertEqual(r['customer_time_availability'],F(43,48))
        self.assertEqual(r['elapsed_any_impact_minutes'],15)
        self.assertEqual(r['all_customers_simultaneously_up_time_availability'],F(3,4))
    def test_interval_union_against_minute_set_oracle(self):
        cases=[[],[(1,8),(2,4)],[(4,7),(0,4),(7,9)],[(5,8),(1,3),(2,6),(2,6)]]
        for intervals in cases:
            expected=len({m for a,b in intervals for m in range(a,b)})
            self.assertEqual(d.union_minutes(intervals,10),expected)
    def test_invalid_interval_boundaries(self):
        for intervals in [[(-1,5)],[(1,11)],[(4,4)],[(8,2)],[(True,5)],[(1,2.5)]]:
            with self.subTest(intervals=intervals),self.assertRaises(ValueError): d.union_minutes(intervals,10)
    def test_incomplete_evidence_not_green(self):
        for complete in [False,None,'yes',1]:
            with self.subTest(complete=complete),self.assertRaises(ValueError):d.impact({},['A'],60,complete_evidence=complete)
    def test_invalid_population(self):
        for customers,events in [([],{}),(['A','A'],{}),(['A'],{'B':[(0,2)]}),([''],{})]:
            with self.assertRaises(ValueError):d.impact(events,customers,60,complete_evidence=True)
    def test_complete_empty_fixture(self):
        self.assertEqual(d.impact({},['A'],60,complete_evidence=True)['customer_time_availability'],1)
    def test_capacity_scenarios(self):
        low=d.capacity(50,70,.02,6,2);high=d.capacity(50,70,.05,6,2)
        self.assertAlmostEqual(50*1.02**low['months_to_trigger'],70)
        self.assertAlmostEqual(50*1.05**high['months_to_trigger'],70)
        self.assertLess(50*1.02**16.99,70)
        self.assertGreater(50*1.02**17,70)
        self.assertTrue(16.99<low['months_to_trigger']<17)
        self.assertLess(high['latest_decision_in_months'],0)
    def test_capacity_reached_breached_and_no_growth(self):
        self.assertEqual(d.capacity(70,70,.02,6,2)['state'],'REACHED')
        self.assertEqual(d.capacity(71,70,0,6,2)['state'],'BREACHED')
        self.assertIsNone(d.capacity(50,70,0,6,2)['months_to_trigger'])
    def test_capacity_missing_nonfinite_negative(self):
        for load in [None,float('inf'),float('nan'),True,0,-1]:
            with self.assertRaises(ValueError):d.capacity(load,70,.02,6,2)
        with self.assertRaises(ValueError):d.capacity(50,70,-.02,6,2)
    def test_change_bounds_and_coverage(self):
        r=d.changes(90,6,4)
        self.assertEqual(r['success_lower'],F(9,10));self.assertEqual(r['success_upper'],F(47,50))
        self.assertEqual(r['outcome_coverage'],F(24,25));self.assertEqual(r['known_outcome_success'],F(15,16))
        self.assertLess(r['success_upper'],F(95,100))
    def test_no_change_and_all_unknown(self):
        self.assertEqual(d.changes(0,0,0)['state'],'NOT_MEASURED')
        r=d.changes(0,0,4);self.assertEqual(r['success_lower'],0);self.assertEqual(r['success_upper'],1)
        self.assertIsNone(r['known_outcome_success'])
    def test_change_invalid_counts(self):
        for v in [True,-1,2.5,None]:
            with self.assertRaises(ValueError):d.changes(v,0,0)
    def test_restoration_tail_and_unresolved(self):
        r=d.restoration([5,10,15,20,150],[180])
        self.assertEqual(r['mean_minutes'],40);self.assertEqual(r['median_minutes'],15)
        self.assertEqual(r['nearest_rank_p95_minutes'],150);self.assertEqual(r['completed_count'],5)
        self.assertEqual(r['unresolved_ages_minutes'],[180])
    def test_no_completed_restorations(self):
        r=d.restoration([],[180]);self.assertIsNone(r['mean_minutes']);self.assertEqual(r['completed_count'],0)
        with self.assertRaises(ValueError):d.restoration([-1],[])
    def test_effort_net_not_gross(self):
        r=d.effort(100,30,5,12,10,80)
        self.assertEqual(r['old_hours'],50);self.assertEqual(r['ongoing_hours'],F(91,3))
        self.assertEqual(r['net_released_hours'],F(59,3));self.assertEqual(r['effort_break_even_months'],F(240,59))
    def test_effort_no_positive_release(self):
        r=d.effort(100,30,30,12,10,80)
        self.assertEqual(r['net_released_hours'],-22);self.assertIsNone(r['effort_break_even_months'])
    def test_exercise_time_not_customer_minutes(self):
        self.assertEqual(d.examples()['exercise_unavailable_minutes'],F(216,25))


if __name__=='__main__':unittest.main()
