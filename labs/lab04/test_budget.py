from decimal import Decimal as D
import json
from pathlib import Path
import unittest
from check_budget import evaluate

CASES=json.loads(Path(__file__).with_name('optical-cases.json').read_text())['cases']
BASE=CASES[0]

class BudgetTests(unittest.TestCase):
    def test_retained_five_decisions(self):
        for c in CASES:
            with self.subTest(case=c['name']):self.assertEqual(evaluate(c)['screen_pass'],c['expected_screen_pass'])
    def test_exact_boundary_and_small_margin_failure(self):
        r=evaluate(BASE);self.assertEqual(D(r['estimated_max_loss_db']),D('4.2'))
        self.assertEqual(D(r['headroom_before_allowance_db']),D('2'))
        self.assertFalse(evaluate(BASE|{'required_margin_db':'2.00001'})['screen_pass'])
    def test_nonfinite_rejected_every_numeric_field(self):
        keys=[k for k,v in BASE.items() if isinstance(v,(int,float)) and not isinstance(v,bool)]
        for k in keys:
            for v in ['NaN','sNaN','Infinity','-Infinity',float('nan'),float('inf')]:
                with self.subTest(key=k,value=v),self.assertRaises(ValueError):evaluate(BASE|{k:v})
    def test_missing_not_zero(self):
        c=BASE.copy();del c['minimum_loss_db']
        with self.assertRaises(KeyError):evaluate(c)
    def test_bad_types_and_boolean(self):
        for v in [True,False,None,{},[],'unknown']:
            with self.subTest(v=v),self.assertRaises(ValueError):evaluate(BASE|{'distance_km':v})
    def test_nonnegative_constraints(self):
        for k in ['distance_km','rated_reach_km','loss_db_per_km','connector_pairs','loss_db_per_pair','splices','loss_db_per_splice','minimum_loss_db','required_margin_db']:
            with self.subTest(key=k),self.assertRaises(ValueError):evaluate(BASE|{k:-1})
    def test_whole_counts_and_positive_rated_reach(self):
        for update in [{'connector_pairs':1.5},{'splices':.25},{'rated_reach_km':0}]:
            with self.assertRaises(ValueError):evaluate(BASE|update)
    def test_inconsistent_limits(self):
        for update in [{'tx_min_dbm':1},{'rx_sensitivity_dbm':1},{'minimum_loss_db':5}]:
            with self.assertRaises(ValueError):evaluate(BASE|update)
    def test_overload_is_independent_of_weak_signal(self):
        c=BASE|{'rx_max_dbm':0}
        r=evaluate(c);self.assertIn('possible receiver overload',r['failure_reasons'])
        self.assertEqual(D(r['headroom_before_allowance_db']),2)
    def test_diagnostic_and_worksheet_arithmetic(self):
        loss=D('11.8')*D('.35')+2*D('.5')+2*D('.1')
        self.assertEqual(loss,D('5.33'));self.assertEqual(D('-2')-loss,D('-7.33'))
        self.assertEqual((D('-2')-D('-9.4'))-loss,D('2.07'))
        r=evaluate(BASE|{'splices':8,'loss_db_per_pair':'.75'})
        self.assertEqual(D(r['headroom_before_allowance_db']),D('1.1'))
    def test_long_span_exercise_and_checkpoint(self):
        self.assertEqual(D(40)*D('.25')+6*D('.5')+4*D('.1')+3,D('16.4'))
        self.assertEqual(D('-4.7')-D('-15.8'),D('11.1'))
        self.assertEqual(D('-5.9')-D('-15.1'),D('9.2'))
        self.assertEqual(D('-11.2')-D('-15.1'),D('3.9'))
    def test_poe_and_breakout(self):
        self.assertEqual(36*45,1620);self.assertEqual(36*60,2160)
        self.assertEqual([a+5*b for a,b in [(7200,360),(8400,420),(9600,480)]],[9000,10500,12000])
        ports=(32-8)*4;self.assertEqual(ports,96);self.assertEqual(ports*25/(8*100),3)

if __name__=='__main__':unittest.main()
