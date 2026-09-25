import asyncio
import time
import unittest
from copy import deepcopy
from unittest.mock import patch, MagicMock
from robust_run import Device, run_fleet, BASELINE, DESIRED, demonstration_fleet
from collect import validate_records, parse_fixture, collect_one

class FailureTests(unittest.IsolatedAsyncioTestCase):
    async def test_success(self):
        r=await run_fleet([Device('a')]);self.assertEqual(r['results'][0]['status'],'VERIFIED_SCOPE')
    async def test_apply_then_timeout_is_reconciled(self):
        d=Device('a','after-timeout');r=await run_fleet([d]);x=r['results'][0]
        self.assertIn('UNKNOWN',x['history']);self.assertEqual(x['observed'],DESIRED);self.assertEqual(d.writes,1)
    async def test_partial_write_is_visible(self):
        r=await run_fleet([Device('a','partial-timeout')]);x=r['results'][0]
        self.assertEqual(x['status'],'PARTIAL_OBSERVED');self.assertEqual(x['observed'],{'description':'after','mtu':1500})
    async def test_unknown_not_reported_untouched(self):
        r=await run_fleet([Device('a','unobservable')]);x=r['results'][0]
        self.assertEqual(x['status'],'UNKNOWN');self.assertIsNone(x['observed']);self.assertEqual(r['simulator_truth']['a'],DESIRED)
    async def test_pre_write_timeout_observed(self):
        r=await run_fleet([Device('a','before-timeout')]);self.assertEqual(r['results'][0]['observed'],BASELINE)
    async def test_rejection_observed(self):
        r=await run_fleet([Device('a','reject')]);self.assertIn('REJECTED',r['results'][0]['history']);self.assertEqual(r['results'][0]['observed'],BASELINE)
    async def test_dependent_stops_after_uncertainty(self):
        r=await run_fleet([Device('a','after-timeout'),Device('b')]);self.assertEqual(r['write_attempts']['b'],0);self.assertEqual(r['results'][1]['status'],'NOT_STARTED')
    async def test_independent_budget(self):
        r=await run_fleet([Device('a','after-timeout'),Device('b'),Device('c','reject'),Device('d')],policy='independent',max_incidents=2)
        self.assertEqual([x['status'] for x in r['results']],['VERIFIED_SCOPE','VERIFIED_SCOPE','BASELINE_OBSERVED','NOT_STARTED'])
    async def test_restore_is_explicit_and_observed(self):
        r=await run_fleet([Device('a','partial-timeout')],restore_partial=True);self.assertEqual(r['results'][0]['status'],'ROLLED_BACK_SCOPE');self.assertEqual(r['simulator_truth']['a'],BASELINE)
    async def test_actual_deadline_bounds_local_wait(self):
        start=time.monotonic();await run_fleet([Device('a','unobservable')],timeout=.02);self.assertLess(time.monotonic()-start,2)
    async def test_final_mixed_state(self):
        r=await run_fleet(demonstration_fleet(),policy='independent',max_incidents=6)
        self.assertEqual(r['incidents'],5);self.assertEqual(r['simulator_truth']['leaf-02'],DESIRED)
        self.assertEqual(r['simulator_truth']['leaf-03'],{'description':'after','mtu':1500});self.assertEqual(r['simulator_truth']['leaf-05'],BASELINE)
    async def test_invalid_policy_and_budget(self):
        for kw in [{'policy':'force'},{'timeout':float('nan')},{'timeout':0},{'max_incidents':True},{'max_incidents':0}]:
            with self.subTest(kw=kw), self.assertRaises(ValueError):await run_fleet([Device('a')],**kw)

class ParserTests(unittest.TestCase):
    def setUp(self):self.rows=[{'interface':'Gi0/0','ip_address':'192.0.2.1','status':'up','proto':'up'}]
    def test_actual_textfsm_fixture(self):
        rows=parse_fixture();self.assertEqual(len(rows),2);self.assertEqual(rows[1]['status'],'administratively down')
    def test_actual_netmiko_missing_template(self):
        from netmiko.utilities import get_structured_data_textfsm
        from netmiko.exceptions import NetmikoParsingException
        text='synthetic unsupported command output'
        raw=get_structured_data_textfsm(text,platform='cisco_ios',command='show unsupported-lab-command',raise_parsing_error=False)
        self.assertIsInstance(raw,str)
        with self.assertRaises(ValueError):validate_records(raw,['Gi0/0'])
        with self.assertRaises(NetmikoParsingException):
            get_structured_data_textfsm(text,platform='cisco_ios',command='show unsupported-lab-command',raise_parsing_error=True)
    def test_raw_empty_and_error_outputs(self):
        for obj in ['% Invalid input',[],{},None]:
            with self.subTest(obj=obj),self.assertRaises(ValueError):validate_records(obj,['Gi0/0'])
    def test_missing_wrong_and_invalid_fields(self):
        for key,value in [('interface',3),('ip_address','999.1.1.1'),('status','unknown'),('proto','')]:
            rows=deepcopy(self.rows);rows[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_records(rows,['Gi0/0'])
        rows=deepcopy(self.rows);del rows[0]['proto']
        with self.assertRaises(ValueError):validate_records(rows,['Gi0/0'])
    def test_missing_and_duplicate_interface(self):
        with self.assertRaises(ValueError):validate_records(self.rows,['Gi0/1'])
        with self.assertRaises(ValueError):validate_records(self.rows*2,['Gi0/0'])
    def test_down_is_valid_data_not_health(self):
        self.rows[0].update(status='down',proto='down');self.assertEqual(validate_records(self.rows,['Gi0/0'])[0]['status'],'down')
    def test_live_adapter_options_with_fake_connection(self):
        conn=MagicMock();conn.send_command.return_value=self.rows
        context=MagicMock();context.__enter__.return_value=conn
        with patch('netmiko.ConnectHandler',return_value=context) as connect:
            collect_one('192.0.2.2','test','dummy','verified_keys',['Gi0/0'])
        self.assertTrue(connect.call_args.kwargs['ssh_strict']);self.assertTrue(connect.call_args.kwargs['alt_host_keys'])
        self.assertEqual(conn.send_command.call_args.kwargs['read_timeout'],20)
        self.assertTrue(conn.send_command.call_args.kwargs['raise_parsing_error'])
        self.assertTrue(context.__exit__.called)

if __name__=='__main__':unittest.main(verbosity=2)
