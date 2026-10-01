import unittest,copy,datetime as dt,tempfile
from pathlib import Path
import yaml
from tools import Action
from verifier import Verifier,fingerprint
BASE=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def setUp(self):
  self.w=yaml.safe_load((BASE/'world.yaml').read_text());self.now=dt.datetime.fromisoformat(self.w['now'].replace('Z','+00:00'))
  self.ap={};self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'decisions.sqlite'
  self.v=Verifier(BASE/'policy/agent-netops.yaml',self.w,self.now,self.ap,self.path,principal='noc-operator')
 def tearDown(self): self.v.close();self.tmp.cleanup()
 def action(self,tool='shut_interface',rid='request1'):
  params={'shut_interface':{'device':'lon-pe-01','interface':'ethernet-1/2'},
   'clear_bgp_session_soft':{'device':'lon-pe-01','neighbour':'192.0.2.5','direction':'in'},
   'announce_blackhole':{'device':'lon-pr-01','prefix':'198.51.100.7/32','peer':'192.0.2.1','expires_at':(self.now+dt.timedelta(seconds=300)).isoformat()}}[tool]
  params['ticket']='INC-4471';sub=next(params[k] for k in ('interface','neighbour','prefix') if k in params)
  return Action(tool,params,[params['device']+':'+sub],'INC-4471',['obs-1'] if tool=='shut_interface' else [],[],rid,None,1)
 def approve(self,a,aid='approval1'):
  a.approval_id=aid;self.ap[aid]={'role':'on_call_engineer','approver':'engineer-1','requester':'noc-operator','digest':fingerprint(a),'issued_at':self.now.isoformat(),'expires_at':(self.now+dt.timedelta(seconds=300)).isoformat()}
 def deny(self,a,stage=None):
  v=self.v.authorise_and_record(a);self.assertFalse(v.allowed,v)
  if stage: self.assertEqual(v.stage,stage)
 def test_approved_shutdown(self):
  a=self.action();self.approve(a);self.assertTrue(self.v.authorise_and_record(a).allowed)
 def test_missing_approval(self): self.deny(self.action(),'approval')
 def test_forged_provenance(self):
  a=self.action();a.provenance=['trusted'];self.deny(a,'approval')
 def test_wrong_targets(self):
  a=self.action();a.targets=['OTHER:OTHER'];self.deny(a,'scope')
 def test_duplicate_targets(self):
  a=self.action();a.targets*=2;self.deny(a,'scope')
 def test_parameter_type(self):
  a=self.action();a.params['interface']=True;self.deny(a,'schema')
 def test_ticket_mismatch(self):
  a=self.action();a.params['ticket']='X';self.deny(a,'schema')
 def test_unknown_parameter(self):
  a=self.action();a.params['command']='anything';self.deny(a,'schema')
 def test_unknown_tool(self):
  a=self.action();a.tool='shell';self.deny(a,'schema')
 def test_revision_change(self):
  a=self.action();self.w['revision']=2;self.deny(a,'preconditions')
 def test_bool_revision(self):
  a=self.action();a.state_revision=True;self.deny(a,'preconditions')
 def test_stale_snapshot(self):
  self.w['observed_at']='2026-09-15T14:03:00Z';self.deny(self.action(),'preconditions')
 def test_future_snapshot(self):
  self.w['observed_at']='2026-09-15T14:06:00Z';self.deny(self.action(),'preconditions')
 def test_missing_evidence(self):
  a=self.action();a.evidence=[];self.deny(a,'preconditions')
 def test_wrong_evidence_target(self):
  a=self.action();a.evidence=['obs-2'];self.deny(a,'preconditions')
 def test_stale_evidence(self):
  a=self.action();a.evidence=['obs-stale'];self.deny(a,'preconditions')
 def test_future_evidence(self):
  self.w['observations']['obs-1']['at']='2026-09-15T14:06:00Z';self.deny(self.action(),'preconditions')
 def test_untrusted_evidence_source(self):
  self.w['observations']['obs-1']['source']='ticket';self.deny(self.action(),'preconditions')
 def test_condition_cleared(self):
  self.w['interfaces']['lon-pe-01']['ethernet-1/2']['mac_flaps_5m']=0;self.deny(self.action(),'preconditions')
 def test_core_port(self):
  a=self.action();a.params['interface']='ethernet-1/1';a.targets=['lon-pe-01:ethernet-1/1'];self.deny(a,'policy')
 def test_wrong_approval_binding(self):
  a=self.action();self.approve(a);a.request_id='different';self.deny(a,'approval')
 def test_revoked_approval(self):
  a=self.action();self.approve(a);self.ap['approval1']['revoked']=True;self.deny(a,'approval')
 def test_expired_approval(self):
  a=self.action();self.approve(a);self.ap['approval1']['expires_at']=self.now.isoformat();self.deny(a,'approval')
 def test_future_approval(self):
  a=self.action();self.approve(a);self.ap['approval1']['issued_at']=(self.now+dt.timedelta(seconds=1)).isoformat();self.deny(a,'approval')
 def test_ttl_too_long(self):
  a=self.action();self.approve(a);self.ap['approval1']['expires_at']=(self.now+dt.timedelta(seconds=901)).isoformat();self.deny(a,'approval')
 def test_replay(self):
  a=self.action();self.approve(a);self.assertTrue(self.v.authorise_and_record(a).allowed);self.deny(a,'replay')
 def test_invalid_direction(self):
  a=self.action('clear_bgp_session_soft');a.params['direction']='INVALID';self.deny(a,'schema')
 def test_soft_clear(self): self.assertTrue(self.v.authorise_and_record(self.action('clear_bgp_session_soft')).allowed)
 def test_transit_session(self):
  a=self.action('clear_bgp_session_soft');a.params.update(device='lon-pr-01',neighbour='192.0.2.1');a.targets=['lon-pr-01:192.0.2.1'];self.deny(a,'policy')
 def test_foreign_blackhole(self):
  a=self.action('announce_blackhole');a.params['prefix']='192.0.2.77/32';a.targets=['lon-pr-01:192.0.2.77/32'];self.deny(a,'policy')
 def test_malformed_blackhole(self):
  a=self.action('announce_blackhole');a.params['prefix']='bad';a.targets=['lon-pr-01:bad'];self.deny(a,'schema')
 def test_too_broad_blackhole(self):
  a=self.action('announce_blackhole');a.params['prefix']='198.51.100.0/24';a.targets=['lon-pr-01:198.51.100.0/24'];self.deny(a,'policy')
 def test_blackhole_requires_approval(self): self.deny(self.action('announce_blackhole'),'approval')
 def test_ipv4_blackhole(self):
  a=self.action('announce_blackhole');self.approve(a);self.assertTrue(self.v.authorise_and_record(a).allowed)
 def test_ipv6_blackhole(self):
  a=self.action('announce_blackhole');a.params['prefix']='2001:db8:4000::7/128';a.targets=['lon-pr-01:'+a.params['prefix']];self.approve(a);self.assertTrue(self.v.authorise_and_record(a).allowed)
 def test_blackhole_requires_attack(self):
  self.w['attacks']['lon-pr-01']=[];self.deny(self.action('announce_blackhole'),'preconditions')
 def test_freeze(self):
  self.v.policy['freeze_windows']=[{'start':self.now.isoformat(),'end':(self.now+dt.timedelta(hours=1)).isoformat()}];self.deny(self.action(),'policy')
 def test_rate_persists_across_instances(self):
  for i in range(6): self.assertTrue(self.v.authorise_and_record(self.action('clear_bgp_session_soft',str(i))).allowed)
  self.v.close();self.v=Verifier(BASE/'policy/agent-netops.yaml',self.w,self.now,self.ap,self.path,principal='noc-operator')
  self.deny(self.action('clear_bgp_session_soft','seventh'),'rate')
 def test_denied_does_not_consume(self):
  self.deny(self.action(),'approval');a=self.action();self.approve(a);self.assertTrue(self.v.authorise_and_record(a).allowed)
 def test_preflight_not_reservation(self):
  a=self.action('clear_bgp_session_soft');self.assertTrue(self.v.verify(a).allowed);self.assertTrue(self.v.authorise_and_record(a).allowed);self.deny(a,'replay')
 def test_forged_requester(self):
  a=self.action();a.requester='administrator';self.approve(a);self.deny(a,'identity')
 def test_requester_device_scope(self):
  self.w['principals']['noc-operator']['devices']=[];self.deny(self.action(),'identity')
 def test_requester_tool_scope(self):
  self.w['principals']['noc-operator']['tools']=[];self.deny(self.action(),'identity')
 def test_unrecognised_approver(self):
  a=self.action();self.approve(a);self.ap['approval1']['approver']='forged';self.deny(a,'approval')
 def test_approval_requester_mismatch(self):
  a=self.action();self.approve(a);self.ap['approval1']['requester']='somebody-else';self.deny(a,'approval')
 def test_blackhole_requester_delegation(self):
  self.w['principals']['noc-operator']['blackhole_prefixes']=[];self.deny(self.action('announce_blackhole'),'identity')
 def test_blackhole_export_peer(self):
  a=self.action('announce_blackhole');a.params['peer']='198.51.100.1';self.deny(a,'policy')
 def test_blackhole_peer_afi(self):
  self.w['blackhole_peers']['lon-pr-01']['192.0.2.1']['afis']=[6];self.deny(self.action('announce_blackhole'),'policy')
 def test_blackhole_expiry_bounds(self):
  for seconds in [0,-1,901]:
   a=self.action('announce_blackhole');a.params['expires_at']=(self.now+dt.timedelta(seconds=seconds)).isoformat();self.deny(a,'policy')
 def test_oversized_parameter(self):
  a=self.action();a.params['device']='x'*257;self.deny(a,'schema')
 def test_callable_clock_refresh_and_rate_window_expiry(self):
  clock=[self.now];self.v.clock_source=lambda:clock[0]
  for i in range(6):self.assertTrue(self.v.authorise_and_record(self.action('clear_bgp_session_soft',str(i))).allowed)
  self.deny(self.action('clear_bgp_session_soft','before-expiry'),'rate')
  clock[0]+=dt.timedelta(seconds=3600);self.w['observed_at']=clock[0].isoformat()
  self.assertTrue(self.v.authorise_and_record(self.action('clear_bgp_session_soft','after-expiry')).allowed)
 def test_backward_clock_after_reopen_denied(self):
  self.assertTrue(self.v.authorise_and_record(self.action('clear_bgp_session_soft','first')).allowed)
  self.v.close();earlier=self.now-dt.timedelta(seconds=1);self.w['observed_at']=earlier.isoformat()
  self.v=Verifier(BASE/'policy/agent-netops.yaml',self.w,earlier,self.ap,self.path,principal='noc-operator')
  self.deny(self.action('clear_bgp_session_soft','second'),'clock')
 def test_concurrent_workers_share_budget(self):
  from concurrent.futures import ThreadPoolExecutor
  from threading import Barrier
  barrier=Barrier(12)
  def worker(i):
   verifier=Verifier(BASE/'policy/agent-netops.yaml',copy.deepcopy(self.w),self.now,{},self.path,principal='noc-operator')
   try:
    barrier.wait(timeout=15)
    return verifier.authorise_and_record(self.action('clear_bgp_session_soft',f'worker-{i}'))
   finally:verifier.close()
  with ThreadPoolExecutor(max_workers=12) as pool:results=list(pool.map(worker,range(12)))
  self.assertEqual(sum(v.allowed for v in results),6)
  self.assertTrue(all(v.allowed or v.stage=='rate' for v in results))
  self.assertEqual(self.v.db.execute('SELECT count(*) FROM decisions').fetchone()[0],6)
 def test_unavailable_database_fails_closed(self):
  self.v.close();self.deny(self.action('clear_bgp_session_soft'),'storage')
 def test_malformed_trusted_fixture_fails_closed(self):
  self.w['devices']=[];self.deny(self.action(),'schema')
 def test_reserved_verdict_does_not_say_executed(self):
  v=self.v.authorise_and_record(self.action('clear_bgp_session_soft'))
  self.assertTrue(v.allowed);self.assertEqual(v.stage,'reserved');self.assertIn('no device execution',v.reason)
 def test_policy_revision_binding(self):
  a=self.action();self.approve(a);self.v.policy['version']=6;self.deny(a,'preconditions')
 def test_revoke_between_preflight_and_reservation(self):
  a=self.action();self.approve(a);self.assertTrue(self.v.verify(a).allowed)
  self.ap['approval1']['revoked']=True;self.deny(a,'approval')
 def test_changed_approved_prefix(self):
  a=self.action('announce_blackhole');self.approve(a)
  a.params['prefix']='198.51.100.8/32';a.targets=['lon-pr-01:198.51.100.8/32']
  self.w['attacks']['lon-pr-01'].append(a.params['prefix']);self.deny(a,'approval')
 def test_consumed_approval_cannot_be_reissued_under_same_id(self):
  a=self.action();self.approve(a);self.assertTrue(self.v.authorise_and_record(a).allowed)
  b=self.action(rid='second');self.approve(b);self.deny(b,'replay')
 def test_ephemeral_database_rejected(self):
  for database in [None,'',':memory:']:
   with self.assertRaises(ValueError):Verifier(BASE/'policy/agent-netops.yaml',self.w,self.now,self.ap,database,principal='noc-operator')
 def test_no_default_trusted_identity(self):
  v=Verifier(BASE/'policy/agent-netops.yaml',self.w,self.now,self.ap,self.path)
  try:self.assertEqual(v.authorise_and_record(self.action('clear_bgp_session_soft')).stage,'identity')
  finally:v.close()
 def test_reversed_freeze_window_denied(self):
  self.v.policy['freeze_windows']=[{'start':(self.now+dt.timedelta(hours=1)).isoformat(),'end':self.now.isoformat()}]
  self.deny(self.action(),'policy')
 def test_invalid_counter_types_denied(self):
  for value in [True,float('nan'),float('inf'),'214']:
   self.w['interfaces']['lon-pe-01']['ethernet-1/2']['mac_flaps_5m']=value
   self.deny(self.action(),'preconditions')
  self.w['interfaces']['lon-pe-01']['ethernet-1/2']['mac_flaps_5m']=214
  self.w['observations']['obs-1']['mac_flaps_5m']=float('nan');self.deny(self.action(),'preconditions')
if __name__=='__main__': unittest.main(verbosity=2)
