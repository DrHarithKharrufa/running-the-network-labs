import unittest
from fractions import Fraction as F
from sla_report import *

class ReportingTests(unittest.TestCase):
    def test_overlap_not_double_counted(self):self.assertEqual(report(100,[(0,20),(10,30)])['bad'],30)
    def test_duplicates_adjacent(self):self.assertEqual(intervals([(0,10),(0,10),(10,20)],100),[(0,20)])
    def test_clip_at_window(self):self.assertEqual(intervals([(-5,10),(90,200),(200,300)],100),[(0,10),(90,100)])
    def test_empty_is_known_up_only_in_fixture(self):self.assertEqual(report(100)['lower'],1)
    def test_exclusions_remove_both(self):
        r=report(100,[(10,40)],excluded=[(30,50)]);self.assertEqual((r['eligible'],r['bad']),(80,20));self.assertEqual(r['upper'],F(3,4))
    def test_excluded_overlap_union(self):self.assertEqual(report(100,excluded=[(0,20),(10,30)])['eligible'],70)
    def test_unknown_bounds(self):
        r=report(100,[(0,10)],[(10,30)]);self.assertEqual((r['lower'],r['upper'],r['coverage']),(F(7,10),F(9,10),F(4,5)))
    def test_unknown_excluded(self):self.assertEqual(report(100,unknown=[(0,30)],excluded=[(10,20)])['unknown'],20)
    def test_contradictory_states(self):
        with self.assertRaises(ValueError):report(100,[(0,20)],[(10,30)])
    def test_all_excluded(self):self.assertEqual(objective(report(100,excluded=[(0,100)]),'.999'),'NOT_MEASURABLE')
    def test_gate_boundaries(self):
        r=report(100,[(0,10)],[(10,20)])
        self.assertEqual(objective(r,'.8'),'MET_WITHIN_BOUNDS');self.assertEqual(objective(r,'.85'),'INDETERMINATE');self.assertEqual(objective(r,'.91'),'VIOLATED_WITHIN_BOUNDS')
    def test_invalid_interval(self):
        for v in [[(1,1)],[(2,1)],[(True,10)],[(0,1.5)],[(0,10,20)]]:
            with self.assertRaises(ValueError):report(100,v)
    def test_invalid_window(self):
        for v in [0,-1,True,1.5,10**13]:
            with self.assertRaises(ValueError):report(v)
    def test_invalid_fraction(self):
        for v in [-1,2,True,'nan','inf',None]:
            with self.assertRaises(ValueError):error_budget(100,v)
    def test_month_lengths(self):
        self.assertEqual(error_budget(30*86400,'.999')/60,F('43.2'))
        self.assertEqual(error_budget(28*86400,'.999')/60,F('40.32'))
        self.assertEqual(error_budget(31*86400,'.999')/60,F('44.64'))
    def test_burn(self):self.assertEqual(burn_rate(90,3600,'.999'),25)
    def test_zero_budget_and_bad_burn(self):
        for args in [(0,100,1),(-1,100,'.999'),(101,100,'.999')]:
            with self.assertRaises(ValueError):burn_rate(*args)
    def test_credit_thresholds(self):
        self.assertEqual(credit_fraction('.9999'),0);self.assertEqual(credit_fraction('.999'),F('.1'));self.assertEqual(credit_fraction('.99'),F('.25'));self.assertEqual(credit_fraction('.989999'),1)
    def test_equal_means_different_expected_credits(self):
        self.assertEqual(F('.9')+F('.1')*F('.995'),F('.9995'))
        self.assertEqual(expected_credit([(1,'.9995')],10000),1000)
        self.assertEqual(expected_credit([('.9',1),('.1','.995')],10000),250)
    def test_invalid_distribution(self):
        for rows in [[],[('.9',1)],[('-1',1),(2,1)]]:
            with self.assertRaises(ValueError):expected_credit(rows,100)
    def test_synthetic_month(self):
        x=worksheet()['contract_excluded_view'];self.assertEqual((x['eligible'],x['bad'],x['unknown']),(2591400,900,120))
    def test_classification_without_rounding(self):
        r=report(100000,[(0,11)]);self.assertEqual(objective(r,'.9999'),'VIOLATED_WITHIN_BOUNDS')
    def test_order_independent(self):self.assertEqual(report(100,[(0,5),(20,40)]),report(100,[(20,40),(0,5)]))

if __name__=='__main__':unittest.main()
