"""Contract and real loopback HTTP tests; uses temporary SQLite and simulated devices."""
import copy
import importlib
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request,urlopen
from http.server import ThreadingHTTPServer
from unittest.mock import patch
import common
import lab_service
import agent_advisor

class RouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.sqlite'
        self.store=lab_service.Store(self.path)
        self.event={'event_id':'event-1','sensor_id':'sensor-r1-eth2','status':'Down',
                    'observed_at':1000,'sequence':1}
    def tearDown(self):self.tmp.cleanup()
    def test_inventory_and_duplicates(self):
        fn=importlib.import_module('02_addresses').validate_inventory
        rows=[{'asset_id':'a','management_ip':'192.0.2.1','prefix':'192.0.2.0/24','owner':'noc'}]
        self.assertEqual(fn(rows),rows)
        with self.assertRaises(ValueError):fn(rows*2)
        for field,value in [('management_ip','198.51.100.1'),('prefix','192.0.2.1/24'),('owner','')]:
            with self.subTest(field=field),self.assertRaises(ValueError):fn([{**rows[0],field:value}])
    def test_snapshot_missing_and_duplicate(self):
        state=self.store.device('r1')
        self.assertEqual(common.validate_snapshot(state),state)
        for rows in ([],state['interfaces'][:1],state['interfaces']*2):
            with self.assertRaises(ValueError):common.validate_snapshot({**state,'interfaces':rows})
    def test_snapshot_types(self):
        for value in ('% Unknown command',{},None):
            with self.assertRaises(ValueError):common.validate_snapshot(value)
        for value in (-1,True,'0'):
            state=self.store.device('r1');state['interfaces'][0]['errors']=value
            with self.assertRaises(ValueError):common.validate_snapshot(state)
    def test_zero_denominator_unknown(self):
        state=self.store.device('r1');state['interfaces'][0]['packets']=0
        result=importlib.import_module('03_report').report(state)
        self.assertIsNone(result['interfaces'][0]['error_ratio'])
        self.assertEqual(result['interfaces'][1]['error_ratio'],.04)
    def test_dry_plan_does_not_write(self):
        state=self.store.device('r1');plan=importlib.import_module('05_plan').plan(state,'reviewed')
        self.assertTrue(plan['change_required']);self.assertEqual(self.store.device('r1'),state)
    def test_generation_compare_and_swap(self):
        result=self.store.change('r1',{'description':'new','expected_generation':0})
        self.assertEqual(result['generation'],1)
        with self.assertRaises(lab_service.Problem) as error:
            self.store.change('r1',{'description':'stale','expected_generation':0})
        self.assertEqual(error.exception.status,409)
        self.assertEqual(self.store.device('r1')['description'],'new')
    def test_normal_event_and_duplicate(self):
        a=self.store.event(self.event,1001);b=self.store.event(self.event,1002)
        self.assertEqual(a['case_id'],b['case_id']);self.assertTrue(b['duplicate'])
        case=self.store.case(a['case_id']);self.assertEqual(case['status'],'AWAITING_REVIEW')
        self.assertIn('Cause is not established',case['summary'])
    def test_conflicting_id(self):
        self.store.event(self.event,1001)
        with self.assertRaises(lab_service.Problem):self.store.event({**self.event,'status':'Up'},1001)
    def test_restart_deduplicates(self):
        self.store.event(self.event,1001)
        reopened=lab_service.Store(self.path)
        self.assertTrue(reopened.event(self.event,1002)['duplicate'])
    def test_stale_and_out_of_order(self):
        self.assertEqual(self.store.event(self.event,1400)['status'],'STALE')
        fresh={**self.event,'event_id':'fresh','observed_at':1400,'sequence':4}
        self.store.event(fresh,1401)
        self.assertEqual(self.store.event({**fresh,'event_id':'old','sequence':3},1401)['status'],'STALE')
    def test_future_nonfinite_and_boolean(self):
        for value in (2000,float('nan'),float('inf'),True):
            with self.assertRaises(lab_service.Problem):self.store.event({**self.event,'observed_at':value},1001)
    def test_unknown_mapping_and_injected_url(self):
        for change in ({'sensor_id':'unknown'},{'url':'http://elsewhere/'},{'cmd':'erase config'}):
            with self.assertRaises(lab_service.Problem):self.store.event({**self.event,**change},1001)
    def test_collector_failure_is_retryable_not_healthy(self):
        for fault in ('unavailable','malformed'):
            self.store.fault=fault
            with self.assertRaises(lab_service.Problem):self.store.event(self.event,1001)
        self.store.fault='none'
        self.assertEqual(self.store.event(self.event,1001)['status'],'DRAFT_CREATED')
    def test_concurrent_duplicate(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda _:self.store.event(self.event,1001),range(4)))
        self.assertEqual(sum(not r['duplicate'] for r in results),1)
    def test_clear_is_separate_observation(self):
        a=self.store.event(self.event,1001)
        b=self.store.event({**self.event,'event_id':'clear','status':'Up','sequence':2},1002)
        self.assertNotEqual(a['case_id'],b['case_id'])
        self.assertEqual(self.store.case(a['case_id'])['status'],'AWAITING_REVIEW')
    def test_human_decision_and_replay(self):
        cid=self.store.event(self.event,1001)['case_id']
        result=self.store.decide(cid,{'decision':'investigate','expected_revision':1})
        self.assertEqual(result['status'],'REVIEWED')
        self.assertEqual(result['decisions'][0]['reviewer'],'local-token-holder')
        with self.assertRaises(lab_service.Problem):self.store.decide(cid,{'decision':'dismiss','expected_revision':1})
    def test_no_containment_action(self):
        cid=self.store.event(self.event,1001)['case_id']
        with self.assertRaises(lab_service.Problem):self.store.decide(cid,{'decision':'isolate','expected_revision':1})
    def test_advice_schema_and_citation(self):
        advice={'hypothesis':'Link fault is possible','next_check':'Check peer state','evidence_ids':['ev-1']}
        self.assertEqual(agent_advisor.validate_advice(advice,{'ev-1'}),advice)
        for update in ({'evidence_ids':['fabricated']},{'action':'shutdown'},{'hypothesis':''}):
            with self.assertRaises(ValueError):agent_advisor.validate_advice({**advice,**update},{'ev-1'})
    def test_ai_unavailable_keeps_case(self):
        case=self.store.case(self.store.event(self.event,1001)['case_id'])
        with patch.object(agent_advisor,'urlopen',side_effect=TimeoutError):
            self.assertEqual(agent_advisor.advise(case,'unavailable')['status'],'DETERMINISTIC_FALLBACK')
        self.assertEqual(self.store.case(case['case_id'])['status'],'AWAITING_REVIEW')


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.store=lab_service.Store(Path(cls.tmp.name)/'state.sqlite')
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),lab_service.handler(cls.store,'test-token-24-characters-long'))
        cls.base='http://127.0.0.1:'+str(cls.server.server_port)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.tmp.cleanup()
    def send(self,path,body=None,token='test-token-24-characters-long',content_type='application/json'):
        headers={'Authorization':'Bearer '+token,'Content-Type':content_type}
        req=Request(self.base+path,data=None if body is None else body.encode(),headers=headers)
        with urlopen(req,timeout=3) as response:return json.load(response)
    def test_real_http_read(self):
        self.assertEqual(self.send('/api/devices/r1')['asset_id'],'r1')
    def test_authentication_failure(self):
        with self.assertRaises(HTTPError) as error:self.send('/events','{}',token='wrong')
        self.assertEqual(error.exception.code,401)
    def test_form_wire_conversion(self):
        body=f'event_id=form-1&sensor_id=sensor-r1-eth2&status=Down&observed_at={int(time.time())}&sequence=1'
        self.assertEqual(self.send('/events',body,content_type='application/x-www-form-urlencoded')['status'],'DRAFT_CREATED')
    def test_duplicate_form_fields(self):
        with self.assertRaises(HTTPError):self.send('/events','event_id=a&event_id=b',content_type='application/x-www-form-urlencoded')
    def test_oversized_and_malformed(self):
        for body in ('{','x'*8200,'{"observed_at":NaN}'):
            with self.assertRaises(HTTPError):self.send('/events',body)
    def test_apply_verify_and_rollback(self):
        module=importlib.import_module('07_change')
        with patch.object(common,'BASE',self.base),patch.dict('os.environ',{'RTN_LAB_TOKEN':'test-token-24-characters-long'}):
            self.assertEqual(module.execute('test description')['status'],'DRY_RUN')
            self.assertEqual(self.store.device('r1')['generation'],0)
            self.assertEqual(module.execute('test description',True)['status'],'VERIFIED')
            self.assertEqual(module.execute('rejected by service check',True,True)['status'],'ROLLED_BACK')
            self.assertEqual(self.store.device('r1')['description'],'test description')
    def test_lost_write_response_not_retried(self):
        module=importlib.import_module('07_change');calls=[]
        def fake(path,method='GET',data=None):
            calls.append(method)
            if method=='PUT':
                self.store.change('r2',data);raise TimeoutError('reply lost after commit')
            return self.store.device('r2')
        with patch.object(module,'request',side_effect=fake):result=module.execute('lost reply',True)
        self.assertEqual(result['status'],'UNKNOWN_WRITE');self.assertEqual(calls.count('PUT'),1)
        self.assertEqual(result['observed']['description'],'lost reply')

    def test_failed_readback_is_explicitly_unknown(self):
        module=importlib.import_module('07_change')
        before=self.store.device('r1')
        with patch.object(module,'request',side_effect=[before,{'generation':before['generation']+1},TimeoutError()]):
            self.assertEqual(module.execute('uncertain verification',True)['status'],'UNKNOWN_VERIFICATION')

    def test_fixed_local_client_rejects_redirect(self):
        with self.assertRaisesRegex(ValueError,'must not redirect'):
            common.NoRedirect().redirect_request(None,None,302,'Found',{},'http://untrusted.invalid/')

    def test_restored_configuration_requires_recovered_service(self):
        module=importlib.import_module('07_change');before=self.store.device('r1')
        after={**before,'description':'changed','generation':before['generation']+1}
        restored={**before,'generation':before['generation']+2}
        responses=[before,{'generation':after['generation']},after,{'healthy':False},
                   {'generation':restored['generation']},restored,{'healthy':False}]
        with patch.object(module,'request',side_effect=responses):
            self.assertEqual(module.execute('changed',True)['status'],'RECOVERY_SERVICE_FAILED')

    def test_unknown_recovery_service_never_reports_success(self):
        module=importlib.import_module('07_change');before=self.store.device('r1')
        after={**before,'description':'changed','generation':before['generation']+1}
        restored={**before,'generation':before['generation']+2}
        for service in ({}, {'healthy':'yes'}, TimeoutError()):
            responses=[before,{'generation':after['generation']},after,{'healthy':False},
                       {'generation':restored['generation']},restored,service]
            with self.subTest(service=service),patch.object(module,'request',side_effect=responses):
                self.assertEqual(module.execute('changed',True)['status'],'RECOVERY_UNKNOWN')


if __name__=='__main__':unittest.main(verbosity=2)
