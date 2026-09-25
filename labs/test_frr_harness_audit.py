import importlib.util,unittest,json,subprocess
from unittest.mock import patch
from pathlib import Path
B=Path(__file__).resolve().parents[1]
def load(n,name):
 spec=importlib.util.spec_from_file_location('lab'+str(n),B/f'labs/lab{n}'/name);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
u=load(36,'underlay_lab.py');o=load(37,'overlay_lab.py')
class InstrumentationTests(unittest.TestCase):
 def test_invalid_json_is_not_route_absence(self):
  for m in [u,o]:
   with self.subTest(m=m.__name__),patch.object(m.Fabric,'vty',return_value='not JSON'):
    with self.assertRaises(json.JSONDecodeError):m.Fabric().vty_json('leaf-01','show something json')
 def test_list_json_is_not_expected_object(self):
  for m in [u,o]:
   with self.subTest(m=m.__name__),patch.object(m.Fabric,'vty',return_value='[]'):
    with self.assertRaises(RuntimeError):m.Fabric().vty_json('leaf-01','show something json')
 def test_cli_failure_is_not_empty_state(self):
  for m in [u,o]:
   with self.subTest(m=m.__name__),patch.object(m,'sh',side_effect=RuntimeError('CLI unavailable')):
    with self.assertRaises(RuntimeError):m.Fabric().vty('leaf-01','show running-config')
 def test_empty_cli_is_not_clean_configuration(self):
  for m in [u,o]:
   with self.subTest(m=m.__name__),patch.object(m,'sh',return_value=subprocess.CompletedProcess([],0,'','')):
    with self.assertRaises(RuntimeError):m.Fabric().vty('leaf-01','show running-config')
 def test_wait_does_not_hide_instrument_failure(self):
  for m in [u,o]:
   with self.subTest(m=m.__name__):
    with self.assertRaisesRegex(RuntimeError,'broken'):
     m.wait(lambda:(_ for _ in ()).throw(RuntimeError('broken')))
 def test_ping_invocation_error_is_not_negative_delivery(self):
  for m,args in [(u,('leaf-01','10.200.0.21','10.200.0.22')),(o,('h-red-a','10.50.10.12'))]:
   with self.subTest(m=m.__name__),patch.object(m,'sh',return_value=subprocess.CompletedProcess([],2,'','invalid option')):
    with self.assertRaises(RuntimeError):m.Fabric().ping(*args)
 def test_fib_reads_actual_kernel(self):
  rows=[{'dst':'10.200.0.21','nexthops':[{'gateway':'10.200.1.2','dev':'to-spine-01'},{'gateway':'10.200.1.10','dev':'to-spine-02'}]}]
  with patch.object(u,'sh',return_value=subprocess.CompletedProcess([],0,json.dumps(rows),'') ) as run:
   self.assertEqual(len(u.kernel_nexthops(None,'leaf-02','10.200.0.21/32')),2)
   self.assertEqual(run.call_args.args[0][:4],['ip','-j','-4','route'])
 def test_unrelated_or_dead_fib_path_excluded(self):
  rows=[{'dst':'10.200.0.22/32','gateway':'10.200.1.2'},{'dst':'10.200.0.21/32','nexthops':[{'gateway':'10.200.1.10','flags':['linkdown']}]}]
  with patch.object(u,'sh',return_value=subprocess.CompletedProcess([],0,json.dumps(rows),'')):
   self.assertEqual(u.kernel_nexthops(None,'leaf-02','10.200.0.21/32'),[])
 def test_wrong_peer_set_is_not_healthy(self):
  f=u.Fabric()
  with patch.object(f,'vty_json',return_value={'peers':{'192.0.2.1':{'state':'Established'},'192.0.2.2':{'state':'Established'}}}):
   self.assertIsNone(u.established(f,'leaf-02',2))
 def test_exact_peer_set_is_healthy(self):
  f=u.Fabric();peers=u.peers_of('leaf-02')
  with patch.object(f,'vty_json',return_value={'peers':{p:{'state':'Established'} for p in peers}}):
   self.assertEqual(set(u.established(f,'leaf-02',2)),set(peers))
 def test_fdb_requires_mac_and_vtep_on_same_row(self):
  text='02:00:00:00:00:a2 dev vx dst 10.200.0.99 extern_learn\n02:00:00:00:00:b2 dev vx dst 10.200.0.23 extern_learn'
  self.assertFalse(o.fdb_match(text,'02:00:00:00:00:a2','10.200.0.23'))
 def test_fdb_external_flag_belongs_to_matched_row(self):
  text='02:00:00:00:00:a2 dev vx dst 10.200.0.23\n02:00:00:00:00:b2 dev vx dst 10.200.0.23 extern_learn'
  self.assertTrue(o.fdb_match(text,'02:00:00:00:00:a2','10.200.0.23'))
  self.assertFalse(o.fdb_match(text,'02:00:00:00:00:a2','10.200.0.23',True))
 def test_fdb_exact_row_passes(self):
  self.assertTrue(o.fdb_match('02:00:00:00:00:a2 dev vx dst 10.200.0.23 extern_learn','02:00:00:00:00:a2','10.200.0.23',True))
 def test_cleanup_does_not_touch_unowned_namespaces(self):
  for m in [u,o]:
   with self.subTest(m=m.__name__),patch.object(m,'sh') as run,patch.object(Path,'exists',return_value=False):
    m.Fabric().down();run.assert_not_called()
 def test_namespaces_are_distinct_between_labs(self):
  self.assertNotEqual(u.ns_name('leaf-01'),o.ns_name('leaf-01'))
  self.assertNotEqual(u.ns_name('leaf-01'),'leaf-01')
 def test_setup_error_calls_owned_cleanup(self):
  with patch.object(u.Fabric,'up',side_effect=RuntimeError('partial setup')),patch.object(u.Fabric,'down') as down:
   with self.assertRaises(RuntimeError):u.build(u.SPINE_SHARED_AS)
   down.assert_called_once()
if __name__=='__main__':unittest.main(verbosity=2)
