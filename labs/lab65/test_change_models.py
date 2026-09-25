"""Counterexamples and boundary checks for the three offline Chapter 65 models."""
import unittest
from change_gate import evaluate, fixture, scenarios
from recovery_budget import RecoveryPlan
from blast_radius import exposure, fixture as graph_fixture


class GateTests(unittest.TestCase):
    def setUp(self):
        self.before,self.after,self.policy=fixture()
    def check(self, changes, expected):
        result=evaluate(self.before,dict(self.after,**changes),**self.policy)
        self.assertEqual(result['verdict'],expected)
        return result
    def test_healthy_changed_counter_passes(self):
        self.assertNotEqual(self.before['rx_errors'],self.after['rx_errors'])
        self.check({},'PASS')
    def test_no_probe_is_not_zero_loss(self): self.check({'probe_sent':None},'UNKNOWN')
    def test_zero_traffic_is_not_success(self): self.check({'probe_sent':0},'UNKNOWN')
    def test_missing_loss_is_unknown(self): self.check({'probe_lost':None},'UNKNOWN')
    def test_loss_exceeds_threshold(self): self.check({'probe_lost':2},'FAIL')
    def test_loss_at_threshold(self): self.check({'probe_lost':1},'PASS')
    def test_short_observation(self): self.check({'probe_window_s':119},'UNKNOWN')
    def test_stale(self): self.check({'age_s':31},'UNKNOWN')
    def test_freshness_boundary(self): self.check({'age_s':30},'PASS')
    def test_collector_failed(self): self.check({'collector_ok':False},'UNKNOWN')
    def test_truthy_string_not_health(self): self.check({'collector_ok':'false'},'UNKNOWN')
    def test_wrong_target(self): self.check({'target':'edge-02'},'UNKNOWN')
    def test_wrong_baseline_target(self):
        self.before['target']='edge-02'; self.check({},'UNKNOWN')
    def test_wrong_render(self): self.check({'config_digest':'wrong'},'FAIL')
    def test_missing_readback(self): self.check({'config_digest':None},'UNKNOWN')
    def test_equal_route_counts_can_hide_loss(self):
        self.check({'routes':['service-A','service-C']},'FAIL')
    def test_missing_route_observation(self): self.check({'routes':None},'UNKNOWN')
    def test_extra_route_is_not_prohibited_by_this_policy(self):
        self.check({'routes':['service-A','service-B','service-C']},'PASS')
    def test_reset_below_previous_counter(self): self.check({'rx_errors':3},'UNKNOWN')
    def test_reset_even_above_previous_counter(self):
        self.check({'counter_epoch':'new','rx_errors':101},'UNKNOWN')
    def test_reboot(self): self.check({'boot_id':'new'},'UNKNOWN')
    def test_zero_interval(self): self.check({'at_s':0},'UNKNOWN')
    def test_counter_rate_boundary(self): self.check({'rx_errors':112},'PASS')
    def test_counter_rate_above_boundary(self): self.check({'rx_errors':113},'FAIL')
    def test_invalid_observations_never_pass(self):
        for key in ['age_s','at_s','rx_errors','probe_window_s']:
            for value in [float('nan'),float('inf'),-1,True,'0',None]:
                with self.subTest(key=key,value=value): self.check({key:value},'UNKNOWN')
    def test_impossible_probe_counts(self):
        for changes in [{'probe_lost':1001},{'probe_lost':-1},{'probe_sent':True},{'probe_lost':0.5}]:
            with self.subTest(changes=changes): self.check(changes,'UNKNOWN')
    def test_known_failure_keeps_unknowns_visible(self):
        r=self.check({'probe_lost':2,'age_s':31},'FAIL')
        self.assertIn('UNKNOWN',[x['state'] for x in r['checks']])
    def test_invalid_policy_is_rejected(self):
        for option in [{'required_routes':[]},{'max_loss_fraction':2},{'min_window_s':0},{'max_age_s':float('nan')}]:
            with self.subTest(option=option), self.assertRaises(ValueError):
                evaluate(self.before,self.after,**dict(self.policy,**option))
    def test_all_verdicts_reachable(self):
        self.assertEqual({x['verdict'] for x in scenarios().values()},{'PASS','FAIL','UNKNOWN'})


class RecoveryTests(unittest.TestCase):
    def setUp(self): self.plan=RecoveryPlan(120,2,18,12,8)
    def test_reserve(self): self.assertEqual(self.plan.reserve,40)
    def test_latest_abort(self): self.assertEqual(self.plan.latest_abort,80)
    def test_stage_fits_exactly(self): self.assertEqual(self.plan.assess(65,15),'STAGE FITS TIME BUDGET')
    def test_stage_does_not_fit(self): self.assertEqual(self.plan.assess(65,16),'DO NOT START NEXT STAGE')
    def test_deadline_requires_recovery_decision(self): self.assertEqual(self.plan.assess(80,0),'RECOVERY DECISION NOW')
    def test_late(self): self.assertEqual(self.plan.assess(90,0),'RECOVERY DECISION NOW')
    def test_plan_exceeds_whole_window(self): self.assertEqual(RecoveryPlan(30,2,18,12,8).assess(0,1),'DO NOT START')
    def test_no_time_for_forward_work(self): self.assertEqual(RecoveryPlan(40,2,18,12,8).assess(0,1),'RECOVERY DECISION NOW')
    def test_naive_deadline_overruns(self): self.assertEqual(110+self.plan.reserve-120,30)
    def test_unknown_recovery_is_not_free(self):
        for bad in [None,-1,True,float('inf'),float('nan')]:
            with self.subTest(bad=bad),self.assertRaises(ValueError): RecoveryPlan(120,2,bad,12,8)
    def test_unrecognised_recovery(self):
        with self.assertRaises(ValueError): RecoveryPlan(120,2,18,12,8,'hope')
    def test_forward_recovery_uses_its_own_duration(self):
        self.assertEqual(RecoveryPlan(120,2,35,12,8,'forward recovery').latest_abort,63)
    def test_longer_recovery_never_increases_time(self):
        self.assertTrue(all(RecoveryPlan(120,2,d,12,8).latest_abort<=80 for d in range(18,121)))
    def test_stage_invalid(self):
        with self.assertRaises(ValueError): self.plan.assess(65,float('nan'))


class ExposureTests(unittest.TestCase):
    def setUp(self): self.graph,self.pop=graph_fixture()
    def test_one_edge(self): self.assertEqual(exposure(self.graph,['edge-01'],self.pop)['potential_population'],1000)
    def test_shared_rr(self): self.assertEqual(exposure(self.graph,['rr-A'],self.pop)['potential_population'],40000)
    def test_duplicate_start_does_not_double_count(self): self.assertEqual(exposure(self.graph,['rr-A','rr-A'],self.pop)['potential_population'],40000)
    def test_overlapping_paths_do_not_double_count(self): self.assertEqual(exposure(self.graph,['rr-A','rr-B'],self.pop)['potential_population'],40000)
    def test_cycle_terminates(self):
        self.graph['edge-01'].append('rr-A')
        self.assertEqual(exposure(self.graph,['edge-01'],self.pop)['potential_population'],40000)
    def test_no_dependency_exposes_nobody(self):
        self.graph['rr-A']=[]
        self.assertEqual(exposure(self.graph,['rr-A'],self.pop)['potential_population'],0)
    def test_scope_control_requires_graph_change(self):
        self.graph['rr-A']=['edge-01']
        self.assertEqual(exposure(self.graph,['rr-A'],self.pop)['potential_population'],1000)
    def test_unknown_node_rejected(self):
        with self.assertRaises(ValueError): exposure(self.graph,['typo'],self.pop)
    def test_dangling_dependency_rejected(self):
        self.graph['rr-A'].append('unknown')
        with self.assertRaises(ValueError): exposure(self.graph,['rr-A'],self.pop)
    def test_population_required(self):
        with self.assertRaises(ValueError): exposure(self.graph,['rr-A'],{})
    def test_negative_population_rejected(self):
        self.pop['service-01']=-1
        with self.assertRaises(ValueError): exposure(self.graph,['rr-A'],self.pop)
    def test_more_exposed_edges_never_reduce_scope(self):
        totals=[]
        for n in range(1,41):
            self.graph['rr-A']=[f'edge-{i:02d}' for i in range(1,n+1)]
            totals.append(exposure(self.graph,['rr-A'],self.pop)['potential_population'])
        self.assertEqual(totals,list(range(1000,40001,1000)))


if __name__=='__main__': unittest.main(verbosity=2)
