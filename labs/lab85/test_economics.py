import unittest
from decimal import Decimal as D
from economics import *

class EconomicsTests(unittest.TestCase):
    def test_manual_two_date_discount(self): self.assertEqual(present_cost([100,110],'.1'),200)
    def test_receipt_negative(self): self.assertEqual(present_cost([100,-110],'.1'),0)
    def test_zero_rate(self): self.assertEqual(present_cost([100,10,20],0),130)
    def test_cashflow_timing(self): self.assertLess(present_cost([0,100],'.08'),present_cost([100,0],'.08'))
    def test_empty_or_excess_horizon(self):
        for x in [[],[0]*102]:
            with self.assertRaises(ValueError):present_cost(x,0)
    def test_rate_bounds(self):
        for r in [-.01,1.01,True,'nan','Infinity']:
            with self.assertRaises(ValueError):present_cost([100],r)
    def test_bad_cashflow(self):
        for v in [None,True,'NaN','Inf','1e19','x']:
            with self.assertRaises(ValueError):present_cost([v],0)
    def test_original_table_arithmetic_only(self): self.assertEqual(sum([100000,105000,25000,20000,40000,60000]),350000)
    def test_new_total_independent_categories(self):
        self.assertEqual(sum(own_costs()),D(100000)+40000+105000+D('25754.4')+21000+56000+10000-5000)
    def test_terminal_not_every_year(self):
        x=own_costs();self.assertEqual(x[0],140000);self.assertEqual(x[1:7],[D('29679.2')]*6);self.assertEqual(x[7],D('34679.2'))
    def test_service_total(self): self.assertEqual(sum(service_costs()),374000)
    def test_rate_can_reverse_ranking(self):
        self.assertLess(present_cost(own_costs(),0),present_cost(service_costs(),0))
        self.assertGreater(present_cost(own_costs(),'.08'),present_cost(service_costs(),'.08'))
    def test_support_escalation(self):
        x=own_costs('.03');self.assertEqual(x[1],own_costs()[1]);self.assertEqual(x[2]-own_costs()[2],450)
        self.assertGreater(sum(x),sum(own_costs()))
    def test_growth_dates(self):
        base=own_costs();grow=own_costs(extra_capacity=True)
        self.assertEqual([a-b for a,b in zip(grow,base)],[0,0,0,100000,15000,15000,15000,15000])
    def test_bad_scenario(self):
        for value in [-.01,1.01,True]:
            with self.assertRaises(ValueError):own_costs(value)
        with self.assertRaises(ValueError):own_costs(extra_capacity=1)
    def test_checkpoint(self):
        self.assertEqual(sum(support_only(80000,'.2')),192000)
        self.assertEqual(sum(support_only(110000,'.12')),202400)
    def test_checkpoint_breakeven(self):
        diff=present_cost(support_only(110000,'.12'),'.08')-present_cost(support_only(80000,'.2'),'.08')
        saving=diff/present_cost([0]+[1]*7,'.08')
        self.assertLess(abs(present_cost([0]+[saving]*7,'.08')-diff),D('1e-20'))
    def test_units(self):
        self.assertEqual(unit_cost(1200000,120000),10)
        self.assertEqual(unit_cost(1200000,1200),1000)
        self.assertEqual(unit_cost(1200000,3000000),D('.4'))
    def test_denominator(self):
        for v in [0,-1,True,'nan']:
            with self.assertRaises(ValueError):unit_cost(100,v)
    def test_year_count(self):
        for v in [0,-1,1.5,True,101]:
            with self.assertRaises(ValueError):support_only(100,'.1',v)
    def test_event_frequency_is_not_probability(self): self.assertEqual(expected_event_loss(2,10000),20000)
    def test_outage_scenario(self):
        x=worksheet()['outage'];self.assertEqual(x['event_cost'],'10000.00');self.assertEqual(x['net_expected_benefit'],'-2000.00')
    def test_accounting_reconciliation(self):
        x=worksheet()['accounting_bridge'];self.assertEqual(x['year1_cash'],x['year1_operating_profit_plus_depreciation_minus_capex'])
        self.assertEqual(x['year1_closing_asset'],70000-x['annual_straight_line_depreciation'])

if __name__=='__main__':unittest.main()
