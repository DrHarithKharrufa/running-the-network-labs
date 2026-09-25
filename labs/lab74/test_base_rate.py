import math
import unittest
from base_rate import score,wilson,precision_from_rates,loss,demo

class Tests(unittest.TestCase):
    def test_worked_confusion_matrix(self):
        r=score(90,5000,994900,10)
        self.assertAlmostEqual(r['accuracy'],.99499)
        self.assertAlmostEqual(r['precision'],90/5090)
        self.assertEqual(r['recall'],.9)
        self.assertAlmostEqual(r['false_positive_rate'],5000/999900)
        self.assertAlmostEqual(r['false_discovery_fraction'],5000/5090)
    def test_always_negative_does_not_have_zero_precision(self):
        r=score(0,0,999900,100)
        self.assertEqual(r['accuracy'],.9999);self.assertIsNone(r['precision'])
        self.assertIsNone(r['false_discovery_fraction']);self.assertIsNone(r['precision_wilson_95'])
        self.assertEqual(r['recall'],0);self.assertEqual(r['false_positive_rate'],0)
    def test_no_positive_labels_makes_recall_undefined(self):
        r=score(0,2,8,0);self.assertIsNone(r['recall']);self.assertEqual(r['precision'],0)
    def test_no_negative_labels_makes_fpr_undefined(self):self.assertIsNone(score(8,0,0,2)['false_positive_rate'])
    def test_empty_dataset_all_point_metrics_undefined(self):
        r=score(0,0,0,0)
        for key in ['accuracy','precision','recall','prevalence','false_positive_rate','false_discovery_fraction']:
            self.assertIsNone(r[key])
    def test_invalid_counts(self):
        for index in range(4):
            for bad in [-1,1.0,True,'1',None,math.nan]:
                values=[1,1,1,1];values[index]=bad
                with self.subTest(index=index,bad=bad),self.assertRaises(ValueError):score(*values)
    def test_base_rate_identity(self):
        self.assertAlmostEqual(precision_from_rates(.0001,.9,5000/999900),90/5090)
    def test_prevalence_changes_precision(self):
        self.assertGreater(precision_from_rates(.01,.9,.005),precision_from_rates(.0001,.9,.005))
    def test_no_predicted_positive_rate_undefined(self):self.assertIsNone(precision_from_rates(.1,0,0))
    def test_invalid_rates(self):
        for bad in [-.1,1.1,math.inf,math.nan,True,'0.5']:
            with self.assertRaises(ValueError):precision_from_rates(bad,.9,.01)
    def test_wilson_known_interval(self):
        lo,hi=wilson(80,100)
        self.assertAlmostEqual(lo,.7111708344,places=9);self.assertAlmostEqual(hi,.8666330667,places=9)
    def test_wilson_bounds_and_symmetry(self):
        zero=wilson(0,10);all_=wilson(10,10)
        self.assertAlmostEqual(zero[0],0);self.assertGreater(zero[1],0)
        self.assertAlmostEqual(all_[1],1);self.assertAlmostEqual(zero[1],1-all_[0])
    def test_wilson_empty_and_invalid(self):
        self.assertIsNone(wilson(0,0))
        for k,n in [(2,1),(-1,3),(1,-3),(True,3)]:
            with self.assertRaises(ValueError):wilson(k,n)
        for c in [0,1,math.inf,math.nan,True]:
            with self.assertRaises(ValueError):wilson(1,3,c)
    def test_model_point_estimates_both_improve(self):
        r=demo()['results']
        for key in ['precision','recall']:self.assertGreater(r['candidate_model'][key],r['seasonal_baseline'][key])
    def test_cost_assumptions_reverse_choice(self):
        r=demo()['cost_example']
        self.assertEqual(r['gross_avoided_loss_per_million_intervals'],2020)
        self.assertEqual(r['net_benefit_with_1000_extra_operating_cost'],1020)
        self.assertEqual(r['net_benefit_with_3000_extra_operating_cost'],-980)
    def test_cost_validation(self):
        for bad in [-1,math.inf,math.nan,True,'1']:
            with self.assertRaises(ValueError):loss(score(1,2,3,4),bad,1)

if __name__=='__main__':unittest.main(verbosity=2)
