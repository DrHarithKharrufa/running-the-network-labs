"""Offline authorisation model. SQLite records decisions, NOT device execution.

World, policy and approval records are supplied by the trusted test harness.
An LLM must not be able to write them or select the database. This program is
not an authenticated service, remote executor, rollback engine or digital twin.
"""
from dataclasses import asdict
from pathlib import Path
import datetime as dt,hashlib,ipaddress,json,sqlite3
import yaml
from tools import Action,Verdict
def stamp(x):
 t=dt.datetime.fromisoformat(x.replace('Z','+00:00'))
 if t.tzinfo is None: raise ValueError('timezone required')
 return t.timestamp()
def fingerprint(a):
 d=asdict(a);d.pop('approval_id');d.pop('provenance')
 return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
class Verifier:
 def __init__(self,policy_path,world,clock=None,approvals=None,database=None,principal=None):
  self.policy=yaml.safe_load(Path(policy_path).read_text())
  self.world=world;self.approvals=approvals if approvals is not None else {}
  self.clock_source=clock if callable(clock) else (lambda: clock) if clock is not None else (lambda: dt.datetime.now(dt.timezone.utc))
  self.clock=self.clock_source();self.principal=principal
  if not isinstance(self.clock,dt.datetime) or self.clock.tzinfo is None: raise ValueError('timezone-aware clock required')
  if database is None or str(database) in ('',':memory:'):raise ValueError('explicit persistent database file required')
  self.db=sqlite3.connect(database,timeout=5,isolation_level=None)
  self.db.execute('CREATE TABLE IF NOT EXISTS decisions(request TEXT PRIMARY KEY, digest TEXT, tool TEXT, at REAL, approval TEXT UNIQUE)')
 def close(self): self.db.close()
 def reject(self,stage,why): return Verdict(False,stage,why)
 def _fresh(self,at,limit): return 0<=self.clock.timestamp()-stamp(at)<=limit
 def _check(self,a):
  schemas={'shut_interface':{'device','interface','ticket'},
    'clear_bgp_session_soft':{'device','neighbour','direction','ticket'},
    'announce_blackhole':{'device','prefix','peer','expires_at','ticket'}}
  if not isinstance(a,Action) or type(a.tool) is not str or a.tool not in schemas:
   return self.reject('schema','unknown action')
  if type(a.params) is not dict or set(a.params)!=schemas[a.tool] or any(type(v) is not str or not v.strip() or len(v)>256 for v in a.params.values()):
   return self.reject('schema','exact named, bounded nonempty string parameters required')
  principal=self.world['principals'].get(self.principal)
  if type(a.requester) is not str or a.requester!=self.principal or not principal or a.tool not in principal['tools']:
   return self.reject('identity','requester/operation not permitted by trusted harness identity')
  if a.params['device'] not in principal['devices']:return self.reject('identity','device outside requester scope')
  if type(a.request_id) is not str or not a.request_id or len(a.request_id)>128:
   return self.reject('schema','bounded nonempty request ID required')
  if type(a.ticket) is not str or a.ticket!=a.params['ticket'] or a.ticket not in self.world['tickets']:
   return self.reject('schema','known, matching ticket required')
  if type(a.evidence) is not list or any(type(x) is not str for x in a.evidence):
   return self.reject('schema','evidence must be IDs')
  if a.approval_id is not None and type(a.approval_id) is not str:
   return self.reject('schema','invalid approval ID')
  if type(a.state_revision) is not int or a.state_revision!=self.world['revision']:
   return self.reject('preconditions','state revision changed')
  if type(a.policy_revision) is not int or a.policy_revision!=self.policy['version']:
   return self.reject('preconditions','policy revision changed')
  latest=self.db.execute('SELECT max(at) FROM decisions').fetchone()[0]
  if latest is not None and self.clock.timestamp()<latest:return self.reject('clock','wall clock predates a durable reservation; reconcile time before proceeding')
  if not self._fresh(self.world['observed_at'],60): return self.reject('preconditions','stale/future trusted snapshot')
  device=a.params['device'];dev=self.world['devices'].get(device)
  if dev is None: return self.reject('preconditions','unknown device')
  if a.tool=='shut_interface': target=device+':'+a.params['interface'];limit=2;approval=True;ttl=900
  elif a.tool=='clear_bgp_session_soft': target=device+':'+a.params['neighbour'];limit=6;approval=False;ttl=0
  else: target=device+':'+a.params['prefix'];limit=4;approval=True;ttl=600
  if type(a.targets) is not list or a.targets!=[target]: return self.reject('scope','targets must exactly equal the one derived from parameters')
  for window in self.policy.get('freeze_windows',[]):
   start,end=stamp(window['start']),stamp(window['end'])
   if start>end:return self.reject('policy','invalid freeze interval; fail closed')
   if start<=self.clock.timestamp()<=end: return self.reject('policy','change freeze')
  if a.tool=='shut_interface':
   iface=self.world['interfaces'].get(device,{}).get(a.params['interface'])
   if not iface or dev['role'] not in ('access','pe') or iface['type']!='customer-facing':
    return self.reject('policy','only declared customer-facing ports on access/PE')
   if iface['admin_state']!='enable' or type(iface['mac_flaps_5m']) is not int or iface['mac_flaps_5m']<=0:
    return self.reject('preconditions','current fixture does not show an enabled flapping port')
   if not a.evidence: return self.reject('preconditions','observation required')
   for oid in a.evidence:
    obs=self.world['observations'].get(oid)
    if not obs or obs.get('source')!='collector' or obs.get('tool')!='get_interface_state' or obs.get('device')!=device or obs.get('interface')!=a.params['interface'] or type(obs.get('mac_flaps_5m')) is not int or obs.get('mac_flaps_5m',0)<=0 or not self._fresh(obs['at'],600):
     return self.reject('preconditions','evidence source/target/age/condition invalid')
  elif a.tool=='clear_bgp_session_soft':
   if a.params['direction'] not in ('in','out'): return self.reject('schema','direction must be in or out')
   neighbour=ipaddress.ip_address(a.params['neighbour'])
   if str(neighbour)!=a.params['neighbour']:return self.reject('schema','canonical neighbour address required')
   nb=self.world['bgp'].get(device,{}).get(a.params['neighbour'])
   if dev['role'] not in ('pe','border') or dev['region'] not in ('uk-north','uk-south') or not nb or nb['type']!='customer':
    return self.reject('policy','only known customer sessions in permitted regions')
   if nb['state']!='established': return self.reject('preconditions','session not established')
  else:
   net=ipaddress.ip_network(a.params['prefix'],strict=True)
   if str(net)!=a.params['prefix'] or net.prefixlen!=(32 if net.version==4 else 128):
    return self.reject('policy','this exercise permits canonical host routes only')
   parents=[ipaddress.ip_network(p) for p in self.world['authorised_blackholes'].get(device,[])]
   if dev['role']!='border' or not any(net.version==p.version and net.subnet_of(p) for p in parents):
    return self.reject('policy','prefix outside trusted authorisation')
   delegated=[ipaddress.ip_network(p) for p in principal.get('blackhole_prefixes',[])]
   if not any(net.version==p.version and net.subnet_of(p) for p in delegated):return self.reject('identity','prefix outside requester delegation')
   peer=self.world['blackhole_peers'].get(device,{}).get(a.params['peer'])
   if not peer or net.version not in peer['afis']:return self.reject('policy','peer/AFI not authorised for this blackhole service')
   duration=stamp(a.params['expires_at'])-self.clock.timestamp()
   if not 0<duration<=900:return self.reject('policy','blackhole intent must expire within 900 seconds')
   if str(net) not in self.world['attacks'].get(device,[]): return self.reject('preconditions','no trusted active attack fixture')
  digest=fingerprint(a)
  if self.db.execute('SELECT 1 FROM decisions WHERE request=?',(a.request_id,)).fetchone(): return self.reject('replay','request already reserved')
  if self.db.execute('SELECT count(*) FROM decisions WHERE tool=? AND at>?',(a.tool,self.clock.timestamp()-3600)).fetchone()[0]>=limit:
   return self.reject('rate','hourly reservation limit')
  if approval:
   auth=self.approvals.get(a.approval_id)
   if not auth or auth.get('role')!='on_call_engineer' or auth.get('approver') not in self.world['approvers'] or auth.get('requester')!=self.principal or auth.get('digest')!=digest or auth.get('revoked',False):
    return self.reject('approval','trusted approval missing, revoked or bound to another request')
   age=self.clock.timestamp()-stamp(auth['issued_at']);expiry=stamp(auth['expires_at'])
   if not 0<=age<=ttl or self.clock.timestamp()>=expiry or expiry-stamp(auth['issued_at'])>ttl:
    return self.reject('approval','approval future, expired or beyond policy TTL')
   if self.db.execute('SELECT 1 FROM decisions WHERE approval=?',(a.approval_id,)).fetchone(): return self.reject('replay','approval consumed')
  elif a.approval_id is not None: return self.reject('schema','unexpected approval for this action')
  return Verdict(True,'preflight','offline model permits reservation; no execution or outcome claimed')
 def verify(self,a):
  try:
   self.clock=self.clock_source()
   if not isinstance(self.clock,dt.datetime) or self.clock.tzinfo is None:raise ValueError('timezone-aware clock required')
   return self._check(a)
  except (ValueError,TypeError,KeyError,AttributeError,OverflowError): return self.reject('schema','malformed input or trusted fixture; fail closed')
  except sqlite3.Error:return self.reject('storage','durable decision store unavailable')
 def authorise_and_record(self,a):
  # A single SQLite transaction makes this local reservation atomic across workers.
  # It does NOT make a future remote device change atomic with this database.
  try:self.db.execute('BEGIN IMMEDIATE')
  except sqlite3.Error:return self.reject('storage','cannot acquire durable reservation transaction')
  try:
   verdict=self.verify(a)
   if verdict.allowed:
    self.db.execute('INSERT INTO decisions VALUES(?,?,?,?,?)',(a.request_id,fingerprint(a),a.tool,self.clock.timestamp(),a.approval_id))
   self.db.execute('COMMIT')
   return Verdict(True,'reserved','durable local reservation recorded; no device execution claimed') if verdict.allowed else verdict
  except sqlite3.Error:
   try:self.db.execute('ROLLBACK')
   except sqlite3.Error:pass
   return self.reject('storage','reservation transaction failed; no device execution attempted')
  except BaseException:
   self.db.execute('ROLLBACK');raise
