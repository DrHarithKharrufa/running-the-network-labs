"""Description-only offline laboratory guard. Never connects to devices."""
from pathlib import Path
import argparse,copy,datetime,hashlib,json,os,re,tempfile
from jinja2 import Environment,FileSystemLoader,StrictUndefined
ROOT=Path(__file__).resolve().parent
PLATFORMS=('iosxe','nxos','eos','junos','srl','vyos')
class Refusal(ValueError):pass
def require(ok,rule):
 if not ok:raise Refusal(rule)
def load(path):return json.loads(Path(path).read_text(encoding='utf8'))
def utc(text):
 value=datetime.datetime.fromisoformat(text.replace('Z','+00:00'))
 require(value.tzinfo is not None,'TIMESTAMP_NEEDS_TIMEZONE')
 return value.astimezone(datetime.timezone.utc)
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
def fixture(platform):
 require(platform in PLATFORMS,'UNKNOWN_PLATFORM')
 return load(ROOT/'fixtures'/f'{platform}-manifest.json'),load(ROOT/'fixtures'/f'{platform}-observed.json')
def proposal(manifest):return {k:manifest[k] for k in manifest['allowed_fields']}
def validate_input(manifest,data):
 require(set(data)==set(manifest['allowed_fields']),'UNKNOWN_OR_MISSING_FIELD')
 for key in ('platform','device','interface'):require(data[key]==manifest[key],'UNOWNED_'+key.upper())
 value=data['description']
 require(isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9 .:_/-]{1,80}',value) is not None,'UNSAFE_DESCRIPTION')
 require(len(value)<=manifest['max_description_length'],'DESCRIPTION_TOO_LONG')
 return data
def render(manifest,data):
 validate_input(manifest,data)
 env=Environment(loader=FileSystemLoader(str(ROOT/'templates')),undefined=StrictUndefined,keep_trailing_newline=True,autoescape=False)
 return env.get_template(manifest['platform']+'.j2').render(**data)
def preflight(manifest,observed,now,expected_baseline):
 for key in ('platform','device','interface'):require(observed.get(key)==manifest[key],'WRONG_OBSERVED_'+key.upper())
 require(observed.get('schema_version'),'MISSING_SCHEMA_VERSION')
 for key in ('management_ok','service_ok','restoration_ready'):require(observed.get(key) is True,'PRECONDITION_'+key.upper())
 require(type(observed.get('description_present')) is bool,'MISSING_PRESENCE')
 require('description' in observed,'MISSING_DESCRIPTION_OBSERVATION')
 age=(now-utc(observed['observed_utc'])).total_seconds()
 require(0<=age<=manifest['max_observation_age_seconds'],'STALE_OR_FUTURE_OBSERVATION')
 require(re.fullmatch('[0-9a-f]{64}',expected_baseline or '') is not None,'INVALID_BASELINE_HASH')
 require(observed.get('baseline_sha256')==expected_baseline,'BASELINE_CHANGED')
 return True
def guard(manifest,data,observed,now,expected_baseline):
 validate_input(manifest,data);preflight(manifest,observed,now,expected_baseline)
 return {'decision':'ALLOW_SCOPED_PROPOSAL','candidate_sha256':digest(data),'baseline_sha256':expected_baseline,'deployment_permission':False}
def golden(manifest,observed,now,expected_baseline):
 preflight(manifest,observed,now,expected_baseline)
 require(observed['description_present'] and observed['description']==manifest['description'],'GOLDEN_DESCRIPTION_DRIFT')
 return {'compliant':True,'scope':'owned description only'}
def event_plan(manifest,event,ledger,now):
 require(set(event)=={'event_id','device','interface','received_utc','kind'},'EVENT_SCHEMA')
 require(isinstance(event['event_id'],str) and re.fullmatch('[A-Za-z0-9_-]{1,64}',event['event_id']) is not None,'EVENT_ID')
 require(event['device']==manifest['device'] and event['interface']==manifest['interface'],'EVENT_UNOWNED_TARGET')
 require(event['kind']=='interface-observation','EVENT_UNSUPPORTED_KIND')
 age=(now-utc(event['received_utc'])).total_seconds();require(0<=age<=60,'EVENT_STALE_OR_FUTURE')
 require(event['event_id'] not in ledger['seen'],'EVENT_DUPLICATE')
 previous=ledger.get('last_accepted_utc')
 require(previous is None or (now-utc(previous)).total_seconds()>=30,'EVENT_COOLDOWN')
 ledger['seen'].append(event['event_id']);ledger['last_accepted_utc']=now.isoformat()
 # Bound retained IDs; use a durable external store for a long-lived real receiver.
 require(len(ledger['seen'])<=1000,'EVENT_LEDGER_CAPACITY')
 return {'action':'READ_OWNED_INTERFACE','device':manifest['device'],'interface':manifest['interface'],'write':False,'event_id':event['event_id']}
def save_atomic(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix=path.name+'.',dir=path.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf8') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def selftest(platform):
 m,o=fixture(platform);data=proposal(m);now=utc('2026-10-02T00:00:30Z');checks=[]
 def positive(name,fn):fn();checks.append({'test':name,'result':'PASS'})
 def negative(name,fn,expected):
  try:fn()
  except Refusal as e:require(str(e)==expected,'WRONG_REFUSAL_'+name);checks.append({'test':name,'result':'PASS','refusal':str(e)})
  else:raise AssertionError('dangerous fixture accepted: '+name)
 positive('owned proposal',lambda:guard(m,data,o,now,'a'*64))
 positive('deterministic render',lambda:require(render(m,data)==render(m,data),'NONDETERMINISTIC'))
 for name,change,rule in [('newline',{'description':'ok\nshutdown'},'UNSAFE_DESCRIPTION'),('single quote',{'description':"a'b"},'UNSAFE_DESCRIPTION'),('double quote',{'description':'a"b'},'UNSAFE_DESCRIPTION'),('backslash',{'description':'a\\b'},'UNSAFE_DESCRIPTION'),('yaml marker',{'description':'!!python/object'},'UNSAFE_DESCRIPTION'),('control byte',{'description':'a\x00b'},'UNSAFE_DESCRIPTION'),('unowned interface',{'interface':'unowned0'},'UNOWNED_INTERFACE'),('unowned device',{'device':'other'},'UNOWNED_DEVICE'),('extra field',{'shutdown':True},'UNKNOWN_OR_MISSING_FIELD')]:
  altered={**data,**change};negative(name,lambda a=altered:guard(m,a,o,now,'a'*64),rule)
 missing=copy.deepcopy(data);del missing['description'];negative('missing variable',lambda:render(m,missing),'UNKNOWN_OR_MISSING_FIELD')
 for key in ('management_ok','service_ok','restoration_ready'):
  altered={**o,key:False};negative(key,lambda a=altered:guard(m,data,a,now,'a'*64),'PRECONDITION_'+key.upper())
 negative('stale baseline',lambda:guard(m,data,o,now,'b'*64),'BASELINE_CHANGED')
 stale={**o,'observed_utc':'2026-10-01T00:00:00Z'};negative('stale observation',lambda:guard(m,data,stale,now,'a'*64),'STALE_OR_FUTURE_OBSERVATION')
 compliant={**o,'description':m['description']};positive('golden positive',lambda:golden(m,compliant,now,'a'*64))
 negative('golden drift',lambda:golden(m,o,now,'a'*64),'GOLDEN_DESCRIPTION_DRIFT')
 absent={**compliant,'description_present':False,'description':None};negative('golden absent',lambda:golden(m,absent,now,'a'*64),'GOLDEN_DESCRIPTION_DRIFT')
 e={'event_id':'fixture-001','device':m['device'],'interface':m['interface'],'received_utc':now.isoformat(),'kind':'interface-observation'};ledger={'seen':[],'last_accepted_utc':None}
 positive('fresh event read-only',lambda:require(event_plan(m,e,ledger,now)['write'] is False,'EVENT_WRITE'))
 negative('event replay',lambda:event_plan(m,e,ledger,now),'EVENT_DUPLICATE')
 negative('event burst',lambda:event_plan(m,{**e,'event_id':'fixture-002'},ledger,now),'EVENT_COOLDOWN')
 negative('event command injection',lambda:event_plan(m,{**e,'command':'shutdown'},ledger,now),'EVENT_SCHEMA')
 negative('event wrong target',lambda:event_plan(m,{**e,'device':'other'},ledger,now),'EVENT_UNOWNED_TARGET')
 negative('event stale',lambda:event_plan(m,{**e,'received_utc':'2026-10-01T00:00:00Z'},ledger,now),'EVENT_STALE_OR_FUTURE')
 return {'mode':'SYNTHETIC_OFFLINE','platform':platform,'checks':checks,'passed':len(checks),'device_execution':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['render','preflight','ci','golden','event','guard','diff','rollback']);p.add_argument('--platform',choices=PLATFORMS,required=True);p.add_argument('--proposal');p.add_argument('--observed');p.add_argument('--expected-baseline');p.add_argument('--event');p.add_argument('--ledger');p.add_argument('--out');args=p.parse_args()
 m,o=fixture(args.platform);data=load(args.proposal) if args.proposal else proposal(m)
 if args.observed:
  o=load(args.observed);require(o.get('synthetic') is False,'SYNTHETIC_IS_NOT_LIVE_EVIDENCE');now=datetime.datetime.now(datetime.timezone.utc);require(args.expected_baseline,'REVIEWED_BASELINE_REQUIRED')
 else:now=utc('2026-10-02T00:00:30Z')
 expected=args.expected_baseline or 'a'*64
 if args.action=='render':result={'mode':'OFFLINE_RENDER','text':render(m,data),'candidate_sha256':digest(data),'device_execution':False}
 elif args.action=='ci' or not args.observed:result=selftest(args.platform)
 elif args.action=='guard':result=guard(m,data,o,now,expected)
 elif args.action=='preflight':preflight(m,o,now,expected);result={'preconditions':True,'write':False}
 elif args.action=='golden':result=golden(m,o,now,expected)
 elif args.action=='event':
  require(args.event and args.ledger,'EVENT_AND_LEDGER_REQUIRED')
  lock=Path(args.ledger+'.lock');lock.parent.mkdir(parents=True,exist_ok=True)
  try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
  except FileExistsError:raise Refusal('EVENT_LEDGER_BUSY')
  try:
   os.close(fd);ledger=load(args.ledger) if Path(args.ledger).exists() else {'seen':[],'last_accepted_utc':None};result=event_plan(m,load(args.event),ledger,now);save_atomic(args.ledger,ledger)
  finally:lock.unlink()
 else:
  import difflib
  preflight(m,o,now,expected);validate_input(m,data)
  # Compare an exact state projection, not guessed serialization of old CLI text.
  before=json.dumps({'present':o['description_present'],'description':o['description']},indent=2,ensure_ascii=True)+'\n'
  after=json.dumps({'present':True,'description':data['description']},indent=2,ensure_ascii=True)+'\n'
  if args.action=='rollback':
   before,after=after,before
   result={'mode':'SCOPED_RESTORATION_PLAN','diff':''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='proposed-current',tofile='original')),'restore_presence':o['description_present'],'restore_description':o['description'],'inverse_kind':'SET_ORIGINAL' if o['description_present'] else 'DELETE_OWNED_LEAF','write':False}
  else:result={'mode':'SCOPED_OFFLINE_PLAN','diff':''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='observed',tofile='proposed')),'original_presence':o['description_present'],'original_description':o['description'],'write':False}
 if args.out:save_atomic(args.out,result)
 print(json.dumps(result,indent=2))
if __name__=='__main__':
 try:main()
 except (Refusal,ValueError,KeyError,OSError) as e:print(json.dumps({'decision':'REFUSE','reason':str(e),'write':False}));raise SystemExit(2)
