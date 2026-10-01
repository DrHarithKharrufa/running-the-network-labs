import unittest
import math
from availability_math import *

class AvailabilityTests(unittest.TestCase):
    def test_series(self):
        self.assertAlmostEqual(serial([.99,.99]),.9801)
    def test_parallel_independent(self):
        self.assertAlmostEqual(parallel(.99),.9999)
    def test_common_event_union(self):
        # c + (1-c)*U^n is the unavailable fraction.
        self.assertAlmostEqual(parallel(.9,2,.2),1-(.2+.8*.1**2))
    def test_common_boundary(self):
        self.assertEqual(parallel(.7,3,1),0)
        self.assertAlmostEqual(parallel(1,2,.2),.8)
    def test_same_hazard_comparison(self):
        self.assertGreater(parallel(.99,2,.1),parallel(.99,1,.1))
        self.assertLessEqual(parallel(.99,2,.1),.9)
    def test_parallel_boundary(self):
        self.assertEqual(parallel(0,3),0)
        self.assertEqual(parallel(1,3),1)
    def test_r_of_n(self):
        self.assertAlmostEqual(r_out_of_n(.9,2,3),.972)
        self.assertAlmostEqual(r_out_of_n(.9,3,3),serial([.9]*3))
        self.assertAlmostEqual(r_out_of_n(.9,1,3),parallel(.9,3))
    def test_recovery_equivalence(self):
        self.assertEqual(renewal_availability(20000,4),renewal_availability(10000,2))
    def test_calendar_basis(self):
        self.assertAlmostEqual(downtime_minutes(.99999),5.256)
        self.assertAlmostEqual(downtime_minutes(.99999,30),.432)
    def test_maintenance_is_not_redundant(self):
        case=capacity_case([50]*4,100,[0,1])
        self.assertTrue(case['meets_demand']);self.assertEqual(case['margin'],0)
        self.assertFalse(capacity_case([50]*4,100,[0,1,2])['meets_demand'])
    def test_bad_probabilities(self):
        for a in (-.1,1.1,True,float('nan'),float('inf'),'0.9'):
            with self.subTest(a=a), self.assertRaises(ValueError): parallel(a)
    def test_bad_counts_and_times(self):
        for n in (0,-1,1.5,True):
            with self.subTest(n=n), self.assertRaises(ValueError): parallel(.9,n)
        with self.assertRaises(ValueError):r_out_of_n(.9,3,2)
        with self.assertRaises(ValueError):serial([])
        with self.assertRaises(ValueError):renewal_availability(0,0)
        with self.assertRaises(ValueError):downtime_minutes(.9,0)
    def test_bad_capacity(self):
        for failed in ([0,0],[4],[-1],[True]):
            with self.subTest(failed=failed),self.assertRaises(ValueError):capacity_case([50]*4,100,failed)
        with self.assertRaises(ValueError):capacity_case([50,float('nan')],100)

    def test_unknown_observation_bounds(self):
        result=observed_bounds(50,2,8)
        self.assertAlmostEqual(result['lower'],50/60)
        self.assertAlmostEqual(result['upper'],58/60)
        self.assertAlmostEqual(result['usable_fraction_of_observed_only'],50/52)
        self.assertAlmostEqual(result['unknown_fraction'],8/60)

    def test_all_unknown(self):
        self.assertEqual(observed_bounds(0,0,60),{'lower':0,'upper':1,'unknown_fraction':1,'usable_fraction_of_observed_only':None})

    def test_no_unknown_bounds_coincide(self):
        result=observed_bounds(99,1,0)
        self.assertEqual(result['lower'],result['upper'])
        self.assertEqual(result['lower'],.99)

    def test_bad_observations(self):
        for inputs in ((0,0,0),(-1,0,1),(True,0,1),(1,float('nan'),1)):
            with self.subTest(inputs=inputs),self.assertRaises(ValueError):observed_bounds(*inputs)

    def test_very_small_path_probability(self):
        self.assertAlmostEqual(parallel(1e-20,2)/2e-20,1)

    def test_scaled_duration_avoids_sum_overflow(self):
        self.assertEqual(renewal_availability(1e308,1e308),.5)
        self.assertEqual(observed_bounds(1e308,1e308,1e308)['unknown_fraction'],1/3)

    def test_reject_output_overflow(self):
        with self.assertRaises(ValueError):downtime_minutes(0,1e308)
        with self.assertRaises(ValueError):capacity_case([1e308]*2,1)
        with self.assertRaises(ValueError):probability(10**1000)

    def test_unhashable_failed_index(self):
        with self.assertRaises(ValueError):capacity_case([50,50],80,[[0]])

    def test_binomial_against_exact_small_enumeration(self):
        from fractions import Fraction
        for n in range(1,9):
            for r in range(1,n+1):
                a=Fraction(2,5)
                expected=sum(math.comb(n,k)*a**k*(1-a)**(n-k) for k in range(r,n+1))
                with self.subTest(n=n,r=r):self.assertAlmostEqual(r_out_of_n(float(a),r,n),float(expected),places=12)

    def test_large_binomial_and_bound(self):
        # For odd n and p=.5, strict majority has exactly one-half probability.
        self.assertAlmostEqual(r_out_of_n(.5,1001,2001),.5,places=10)
        with self.assertRaises(ValueError):r_out_of_n(.5,1,10001)

    def test_all_table_values(self):
        for target,annual,monthly in ((.99,5256,432),(.999,525.6,43.2),(.9999,52.56,4.32),(.99999,5.256,.432),(.999999,.5256,.0432)):
            with self.subTest(target=target):
                self.assertAlmostEqual(downtime_minutes(target),annual,places=7)
                self.assertAlmostEqual(downtime_minutes(target,30),monthly,places=7)

if __name__ == '__main__':unittest.main()
