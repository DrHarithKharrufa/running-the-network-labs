"""Preview an owned-label XML edit; explicitly gated lab execution is optional."""
from pathlib import Path
import argparse,datetime,hashlib,json,queue,threading,time,xml.etree.ElementTree as ET
NC='urn:ietf:params:xml:ns:netconf:base:1.0'
MODELS={
 'iosxe':('http://cisco.com/ns/yang/Cisco-IOS-XE-native',['native','interface','GigabitEthernet'],{'name':'1/0/1'},'description'),
 'nxos':('http://cisco.com/ns/yang/cisco-nx-os-device',['System','intf-items','aggr-items','AggrIf-list'],{'id':'po5'},'descr'),
 'junos':('http://xml.juniper.net/xnm/1.1/xnm',['configuration','interfaces','interface'],{'name':'ge-0/0/0'},'description'),
 'iosxr':('http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg',['interface-configurations','interface-configuration'],{'active':'act','interface-name':'GigabitEthernet0/0/0/0'},'description'),
 'sros':('urn:nokia.com:sros:ns:yang:sr:conf',['configure','system'],{},'contact')}
def refuse(ok,why):
 if not ok:raise ValueError(why)
def canonical(text):
 root=ET.fromstring(text)
 for node in root.iter():
  if len(node) and node.text is not None and not node.text.strip():node.text=None
  for child in node:
   if child.tail is not None and not child.tail.strip():child.tail=None
 return ET.canonicalize(ET.tostring(root,encoding='unicode'),rewrite_prefixes=True)
def sha(text):return hashlib.sha256(text.encode()).hexdigest()
def payload(platform,value='WB-AUT owned label',restore_absent=False,restore_original=False):
 import re
 refuse(isinstance(value,str) and (len(value)<=1024 and not any(ord(c)<32 for c in value) if restore_original else re.fullmatch(r'[A-Za-z0-9 .:_/-]{1,80}',value) is not None),'UNSAFE_LABEL')
 ns,path,keys,leaf=MODELS[platform];root=ET.Element('{'+NC+'}config');node=root
 for name in path:node=ET.SubElement(node,'{'+ns+'}'+name)
 for key,val in keys.items():ET.SubElement(node,'{'+ns+'}'+key).text=val
 label=ET.SubElement(node,'{'+ns+'}'+leaf)
 if restore_absent:label.set('{'+NC+'}operation','delete')
 else:label.text=value
 return ET.tostring(root,encoding='unicode')
def subtree(platform,parent=False):
 ns,path,keys,leaf=MODELS[platform];root=ET.fromstring(payload(platform));label=next(x for x in root.iter() if x.tag=='{'+ns+'}'+leaf);label.text=None
 if parent:
  owner=next(x for x in root.iter() if label in list(x));owner.remove(label)
  if platform=='sros':
   ET.SubElement(owner,'{'+ns+'}name');ET.SubElement(owner,'{'+ns+'}contact')
 return ET.tostring(list(root)[0],encoding='unicode')
def owner_node(platform,data):
 ns,path,keys,leaf=MODELS[platform];root=ET.fromstring(data)
 nodes=[x for x in root.iter() if x.tag=='{'+ns+'}'+path[0]]
 for name in path[1:]:nodes=[c for n in nodes for c in n if c.tag=='{'+ns+'}'+name]
 nodes=[n for n in nodes if all(any(c.tag=='{'+ns+'}'+k and (c.text or '')==v for c in n) for k,v in keys.items())]
 refuse(len(nodes)==1,'OWNED_PARENT_ABSENT_OR_AMBIGUOUS')
 return nodes[0]
def owned_value(platform,data):
 ns,path,keys,leaf=MODELS[platform];node=owner_node(platform,data)
 matches=[x for x in node if x.tag=='{'+ns+'}'+leaf]
 refuse(len(matches)<=1,'FILTER_RETURNED_MULTIPLE_LABELS')
 return (bool(matches),matches[0].text or '' if matches else None)
def capability(caps,name):return any(':'+name+':' in c for c in caps)
def baseline_record(platform,data,host):
 present,value=owned_value(platform,data)
 return {'platform':platform,'host':host,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'filtered_xml_sha256':sha(canonical(data)),'original_present':present,'original_value':value,'synthetic':False}
def ask_with_deadline(prompt,seconds):
 q=queue.Queue()
 def read():
  try:q.put(input(prompt))
  except EOFError:q.put('')
 threading.Thread(target=read,daemon=True).start()
 try:return q.get(timeout=seconds)
 except queue.Empty:return ''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--platform',choices=MODELS,required=True);p.add_argument('--value',default='WB-AUT owned label');p.add_argument('--out');p.add_argument('--capture-baseline',action='store_true');p.add_argument('--apply-lab',action='store_true');p.add_argument('--restore',action='store_true');p.add_argument('--inventory');p.add_argument('--baseline');p.add_argument('--approved-sha256');args=p.parse_args()
 xml=payload(args.platform,args.value)
 if args.restore:
  refuse(args.baseline,'RESTORE_BASELINE_REQUIRED');original=json.loads(Path(args.baseline).read_text(encoding='utf8'))
  refuse(original['platform']==args.platform and type(original['original_present']) is bool,'RESTORE_BASELINE_IDENTITY')
  xml=payload(args.platform,original['original_value'] if original['original_present'] else 'WB-AUT owned label',restore_absent=not original['original_present'],restore_original=True)
 report={'mode':'OFFLINE_XML_PREVIEW','platform':args.platform,'xml':xml,'xml_sha256':sha(xml),'filter_xml':subtree(args.platform,parent=True),'well_formed':True,'yang_validated':False,'device_execution':False}
 if not (args.apply_lab or args.capture_baseline):
  if args.out:Path(args.out).write_text(xml+'\n',encoding='utf8')
  print(json.dumps(report,indent=2));return
 refuse(args.inventory and args.baseline,'PROTECTED_INVENTORY_AND_BASELINE_REQUIRED')
 inventory=json.loads(Path(args.inventory).read_text(encoding='utf8'))
 refuse(inventory.get('platform')==args.platform and inventory.get('lab_owned') is True,'IDENTITY_OR_OWNERSHIP_GATE')
 refuse(inventory.get('expected_model_revision') and inventory.get('known_host_key_verified') is True,'MODEL_AND_HOST_KEY_GATE')
 # Credentials are environment references, never embedded in shared inventory.
 import os
 from ncclient import manager
 username=os.environ[inventory['username_env']];password=os.environ[inventory['password_env']]
 with manager.connect(host=inventory['host'],port=inventory.get('port',830),username=username,password=password,hostkey_verify=True,allow_agent=False,look_for_keys=False,timeout=15) as m:
  filter_spec=('subtree',subtree(args.platform,parent=True));live=m.get_config(source='running',filter=filter_spec).data_xml
  owner_node(args.platform,live)
  if args.capture_baseline:
   Path(args.baseline).write_text(json.dumps(baseline_record(args.platform,live,inventory['host']),indent=2)+'\n',encoding='utf8');print('Captured read-only owned baseline; protect this file.');return
  baseline=json.loads(Path(args.baseline).read_text(encoding='utf8'))
  refuse(baseline.get('synthetic') is False and baseline['platform']==args.platform and baseline['host']==inventory['host'],'BASELINE_IDENTITY_GATE')
  stamp=datetime.datetime.fromisoformat(baseline['observed_utc'].replace('Z','+00:00'));age=(datetime.datetime.now(datetime.timezone.utc)-stamp).total_seconds()
  refuse(0<=age<=300,'STALE_BASELINE')
  if args.restore:
   xml=payload(args.platform,baseline['original_value'] if baseline['original_present'] else 'WB-AUT owned label',restore_absent=not baseline['original_present'],restore_original=True)
  refuse(args.approved_sha256==sha(xml),'REVIEWED_PAYLOAD_HASH_REQUIRED')
  refuse(inventory.get('independent_service_check_ready') is True and inventory.get('restoration_tested') is True,'SERVICE_AND_RECOVERY_GATE')
  caps=list(m.server_capabilities)
  for name in ['candidate','validate','confirmed-commit']:refuse(capability(caps,name),'MISSING_CAPABILITY_'+name)
  if not args.restore:refuse(sha(canonical(live))==baseline['filtered_xml_sha256'],'BASELINE_CHANGED')
  else:refuse(inventory.get('expected_current_label_sha256')==sha(canonical(live)),'RESTORE_CONCURRENT_CHANGE_GATE')
  with m.locked('candidate'):
   # Preserve someone else's candidate: refuse instead of discarding it.
   running=m.get_config(source='running').data_xml;candidate=m.get_config(source='candidate').data_xml
   refuse(canonical(running)==canonical(candidate),'CANDIDATE_NOT_CLEAN')
   recheck=m.get_config(source='running',filter=filter_spec).data_xml
   refuse(canonical(live)==canonical(recheck),'CONCURRENT_RUNNING_CHANGE')
   staged=False;confirmed=False
   try:
    m.edit_config(target='candidate',config=xml,default_operation='merge');staged=True
    m.validate(source='candidate')
    m.commit(confirmed=True,timeout='120');confirmed=True
    after=m.get_config(source='running',filter=filter_spec).data_xml
    expected=(baseline['original_present'],baseline['original_value']) if args.restore else (True,args.value)
    refuse(owned_value(args.platform,after)==expected,'READBACK_MISMATCH')
    # Keep THIS session alive until the operator independently verifies service.
    # No generic command can establish every platform's customer path.
    token=ask_with_deadline('Verify service independently. Type CONFIRM-'+sha(xml)[:12]+' within 60s, or leave blank to revert: ',60)
    if token=='CONFIRM-'+sha(xml)[:12]:m.commit();confirmed=False;print('Confirmed after explicit independent service-check acknowledgement. Record that evidence separately.')
    else:print('Not confirmed. Session close reverts the nonpersistent confirmed commit; verify recovery independently.')
   except Exception:
    if staged and not confirmed:m.discard_changes()
    raise
   # Session lifetime is part of the transaction: closing before confirmation reverts.
 print('Session closed. No implicit permanent configuration save was requested.')
if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,OSError,ET.ParseError) as e:print(json.dumps({'decision':'REFUSE','reason':str(e)}));raise SystemExit(2)
