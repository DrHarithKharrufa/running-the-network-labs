import unittest
from capacity_case import pct,combine_aligned,years_to_reach,deadline,critical_path,pair_scenarios,examples

class CapacityTests(unittest.TestCase):
    def test_percentile_estimator(self):self.assertAlmostEqual(pct([0,10],95),9.5)
    def test_single_sample(self):self.assertEqual(pct([3],0),3)
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):pct([],95)
    def test_invalid_samples(self):
        for value in [None,True,-1,float('nan'),float('inf')]:
            with self.subTest(value=value),self.assertRaises(ValueError):pct([value],95)
    def test_invalid_percentile(self):
        for p in [-1,101,True,float('nan')]:
            with self.subTest(p=p),self.assertRaises(ValueError):pct([1,2],p)
    def test_misaligned_series_rejected(self):
        with self.assertRaises(ValueError):combine_aligned([1],[1,2])
    def test_sum_percentiles_is_not_percentile_of_sum(self):
        row=examples()['noncoincident_peaks']
        self.assertAlmostEqual(row['sum_of_p95'],46)
        self.assertEqual(row['p95_of_sum'],100)
        self.assertEqual(row['maximum_sum'],100)
    def test_sustained_overload_hidden_by_p95(self):
        self.assertEqual(examples()['hidden_sustained_tail']['p95'],40)
    def test_identical_series_can_double_quantile(self):
        series=[1,2,8,10]
        self.assertAlmostEqual(pct(combine_aligned(series,series),95),2*pct(series,95))
    def test_zero_growth_no_future_crossing(self):self.assertIsNone(years_to_reach(40,70,0))
    def test_negative_growth_no_future_crossing(self):self.assertIsNone(years_to_reach(40,70,-0.1))
    def test_zero_start_no_future_crossing(self):self.assertIsNone(years_to_reach(0,70,0.2))
    def test_existing_breach_even_when_declining(self):self.assertEqual(years_to_reach(80,70,-0.1),0)
    def test_exact_growth(self):self.assertAlmostEqual(years_to_reach(1,2,1),1)
    def test_doubling_at_24_percent(self):self.assertAlmostEqual(years_to_reach(1,2,0.24),3.222271094138538,places=9)
    def test_growth_domain(self):
        for rate in [-1,-2,float('nan')]:
            with self.subTest(rate=rate),self.assertRaises(ValueError):years_to_reach(40,70,rate)
    def test_current_limit_action(self):self.assertEqual(deadline(70,70,0.2,0.5)['status'],'LIMIT_REACHED')
    def test_delivery_due_at_boundary(self):self.assertEqual(deadline(35,70,1,1)['status'],'ACT_NOW')
    def test_not_due_yet(self):self.assertEqual(deadline(35,70,1,0.5)['begin_in_years'],0.5)
    def test_historical_no_slack_claim_is_false(self):
        self.assertGreater(examples()['historical_reason_check']['begin_in_years'],0.6)
    def test_reasons_change_with_inputs(self):
        a=deadline(80,70,0.2,0.5);b=deadline(35,70,0,0.5)
        self.assertNotEqual(a['status'],b['status']);self.assertNotEqual(a['reason'],b['reason'])
    def test_missing_target_invalid(self):
        with self.assertRaises(ValueError):years_to_reach(1,0,0.1)
    def test_negative_lead_rejected(self):
        with self.assertRaises(ValueError):deadline(40,70,0.2,-1)
    def test_critical_path_parallel_and_sequential(self):
        schedule=examples()['schedule'];self.assertEqual(schedule['months'],7);self.assertEqual(schedule['total_months'],8)
    def test_unknown_predecessor_rejected(self):
        with self.assertRaises(ValueError):critical_path({'a':(1,('missing',))})
    def test_schedule_cycle_rejected(self):
        with self.assertRaises(ValueError):critical_path({'a':(1,('b',)),'b':(1,('a',))})
    def test_schedule_negative_duration_rejected(self):
        with self.assertRaises(ValueError):critical_path({'a':(-1,())})
    def test_empty_schedule_rejected(self):
        with self.assertRaises(ValueError):critical_path({})
    def test_failure_load_includes_both_demands(self):
        row=pair_scenarios([10,20],[20,10],100,70,0.2,0.5)
        self.assertEqual(row['A_failed_B_survives']['start'],30)
    def test_generator_samples_preserved(self):
        row=pair_scenarios(iter([10,20]),iter([20,10]),100,70,0.2,0.5)
        self.assertEqual(row['healthy_A']['start'],20)
        self.assertEqual(row['A_failed_B_survives']['start'],30)
    def test_double_failure_is_disconnection(self):
        row=pair_scenarios([10],[10],100,70,0.2,0.5,include_double_failure=True)
        self.assertEqual(row['both_failed']['status'],'NO_PATH')
    def test_failure_can_be_bad_when_normal_is_within_limit(self):
        row=pair_scenarios([40],[40],100,70,0.2,0.5)
        self.assertEqual(row['A_failed_B_survives']['status'],'LIMIT_REACHED')
        self.assertNotEqual(row['healthy_A']['status'],'LIMIT_REACHED')
    def test_zero_capacity_rejected(self):
        with self.assertRaises(ValueError):pair_scenarios([1],[1],0,70,0.2,0.5)
    def test_invalid_limit_rejected(self):
        with self.assertRaises(ValueError):pair_scenarios([1],[1],100,110,0.2,0.5)

if __name__=='__main__':unittest.main()
