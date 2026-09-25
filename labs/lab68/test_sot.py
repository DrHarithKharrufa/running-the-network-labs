import unittest
from copy import deepcopy
from render_from_sot import SOT,OBSERVED,NOW,render,reconcile,validate_intent,duplicate_hosts
from netbox_readonly import START,read_pages,fixture_fetcher,checked_url,NoRedirect

class SourceTests(unittest.TestCase):
    def setUp(self):self.s=deepcopy(SOT);self.o=deepcopy(OBSERVED);self.dev='ald-leaf-01'
    def record(self):return self.s[self.dev]
    def test_access_prerequisites(self):
        result=render(self.dev,self.s)
        self.assertIn(' switchport\n switchport mode access\n switchport access vlan 30',result)
    def test_routed_prefix(self):self.assertIn(' no switchport\n ip address 10.200.1.1/31',render(self.dev))
    def test_unsupported_platform(self):
        self.record()['platform']='ios_xe'
        with self.assertRaises(ValueError):render(self.dev,self.s)
    def test_unknown_mode(self):
        self.record()['interfaces']['Ethernet8']['mode']='acess'
        with self.assertRaises(ValueError):render(self.dev,self.s)
    def test_invalid_vlan(self):
        for value in [0,4095,True,'30']:
            self.record()['interfaces']['Ethernet8']['vlan']=value
            with self.subTest(value=value),self.assertRaises(ValueError):render(self.dev,self.s)
    def test_invalid_address(self):
        for value in ['300.1.1.1/24','10.1.1.0/24','10.1.1.255/24','10.1.1.1','::1/128']:
            self.record()['interfaces']['Ethernet1']['ip']=value
            with self.subTest(value=value),self.assertRaises(ValueError):render(self.dev,self.s)
    def test_incompatible_mode_fields(self):
        self.record()['interfaces']['Ethernet8']['ip']='192.0.2.1/24'
        with self.assertRaises(ValueError):render(self.dev,self.s)
    def test_description_cannot_inject_command(self):
        self.record()['interfaces']['Ethernet8']['desc']='server\n shutdown'
        with self.assertRaises(ValueError):render(self.dev,self.s)
    def test_interface_cannot_inject_command(self):
        self.record()['interfaces']['Ethernet8\nshutdown']={'desc':'x','mode':'access','vlan':30}
        with self.assertRaises(ValueError):render(self.dev,self.s)
    def test_detected_drift_requires_review(self):self.assertEqual(reconcile(self.dev)['status'],'REVIEW_REQUIRED')
    def test_unchanged_is_scoped(self):
        self.o[self.dev]['interfaces']=deepcopy(self.record()['interfaces'])
        self.assertEqual(reconcile(self.dev,self.s,self.o)['status'],'NO_DRIFT_IN_SCOPE')
    def test_does_not_mutate_inputs(self):
        old=deepcopy((self.s,self.o));render(self.dev,self.s);reconcile(self.dev,self.s,self.o)
        self.assertEqual(old,(self.s,self.o))
    def test_removed_field_detected(self):
        self.o[self.dev]['interfaces']['Ethernet8']['legacy_field']='old'
        rows=reconcile(self.dev,self.s,self.o)['changes']
        self.assertTrue(any(r.get('field')=='legacy_field' and not r['intended_present'] for r in rows))
    def test_observed_only_interface_detected(self):
        self.o[self.dev]['interfaces']['Ethernet9']={'desc':'unmodelled'}
        self.assertIn('observed_only',[x.get('kind') for x in reconcile(self.dev,self.s,self.o)['changes']])
    def test_missing_interface_detected(self):
        del self.o[self.dev]['interfaces']['Ethernet1']
        self.assertIn('intended_only',[x.get('kind') for x in reconcile(self.dev,self.s,self.o)['changes']])
    def test_version_precondition(self):self.assertEqual(reconcile(self.dev,expected_version=6)['status'],'BLOCKED')
    def test_stale_future_naive_time(self):
        for value in ['2026-09-24T09:00:00Z','2026-09-24T10:01:00Z']:
            self.o[self.dev]['collected_at']=value
            self.assertEqual(reconcile(self.dev,self.s,self.o)['status'],'BLOCKED')
        self.o[self.dev]['collected_at']='2026-09-24T09:59:00'
        with self.assertRaises(ValueError):reconcile(self.dev,self.s,self.o)
    def test_observation_predates_new_approval(self):
        self.record()['approved_at']='2026-09-24T09:59:30Z'
        self.assertEqual(reconcile(self.dev,self.s,self.o)['status'],'BLOCKED')
    def test_emergency_or_conflict_blocks(self):
        self.assertEqual(reconcile(self.dev,emergency=True)['status'],'BLOCKED')
        self.assertEqual(reconcile(self.dev,conflict=True)['status'],'BLOCKED')
    def test_incomplete_observation(self):
        self.o[self.dev]['complete']=False
        self.assertEqual(reconcile(self.dev,self.s,self.o)['status'],'BLOCKED')
    def test_duplicate_host_same_namespace(self):
        rows=[{'namespace':'A','address':'10.1.1.1/24'},{'namespace':'A','address':'10.1.1.1/32'}]
        self.assertEqual(duplicate_hosts(rows,{'A'}),[('A','10.1.1.1')])
        self.assertEqual(duplicate_hosts(rows,set()),[])
    def test_overlap_across_namespaces(self):
        rows=[{'namespace':'A','address':'10.1.1.1/24'},{'namespace':'B','address':'10.1.1.1/24'}]
        self.assertEqual(duplicate_hosts(rows,{'A','B'}),[])
    def test_global_namespace(self):
        rows=[{'namespace':None,'address':'192.0.2.1/24'}]*2
        self.assertEqual(duplicate_hosts(rows,{None}),[(None,'192.0.2.1')])
    def test_nested_prefixes_are_not_duplicate_hosts(self):
        rows=[{'namespace':'A','address':'10.1.1.1/16'},{'namespace':'A','address':'10.1.1.2/24'}]
        self.assertEqual(duplicate_hosts(rows,{'A'}),[])

class PaginationTests(unittest.TestCase):
    def test_two_pages(self):self.assertEqual([r['id'] for r in read_pages(START,fixture_fetcher())],[11,18])
    def test_cross_origin_blocked_before_fetch(self):
        called=[]
        def fake(url):called.append(url);return {'count':0,'results':[],'next':'https://other.example/api/dcim/interfaces/'}
        with self.assertRaises(ValueError):read_pages(START,fake)
        self.assertEqual(called,[START])
    def test_cycle(self):
        with self.assertRaises(ValueError):read_pages(START,lambda u:{'count':0,'results':[],'next':START})
    def test_incomplete_count(self):
        with self.assertRaises(ValueError):read_pages(START,lambda u:{'count':1,'results':[],'next':None})
    def test_duplicate_ids(self):
        with self.assertRaises(ValueError):read_pages(START,lambda u:{'count':2,'results':[{'id':1},{'id':1}],'next':None})
    def test_changed_count(self):
        f=fixture_fetcher()
        def fake(url):
            row=deepcopy(f(url))
            if 'offset' in url:row['count']=3
            return row
        with self.assertRaises(ValueError):read_pages(START,fake)
    def test_page_bound(self):
        with self.assertRaises(ValueError):read_pages(START,fixture_fetcher(),max_pages=1)
    def test_https_and_endpoint_required(self):
        for url in [START.replace('https','http'),START.replace('/interfaces/','/devices/'),START.replace('netbox.example','user:pass@netbox.example')]:
            with self.subTest(url=url),self.assertRaises(ValueError):checked_url(url,START)
    def test_redirect_refused(self):
        with self.assertRaises(ValueError):NoRedirect().redirect_request(None,None,302,'',{},START)

if __name__=='__main__':unittest.main()
