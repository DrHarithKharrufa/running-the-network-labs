"""Credential-free, offline checks. No network/device calls."""
import json
from pathlib import Path
from kit import PLATFORMS,selftest,save_atomic
from netconf_edit import MODELS,payload,subtree,owned_value,canonical,NC
import xml.etree.ElementTree as ET
def main():
 results=[selftest(p) for p in PLATFORMS];extra=[]
 for p in MODELS:
  xml=payload(p);root=ET.fromstring(xml);assert root.tag=='{'+NC+'}config';ET.fromstring(subtree(p))
  assert owned_value(p,xml)==(True,'WB-AUT owned label')
  try:owned_value(p,'<data/>')
  except ValueError as e:assert 'OWNED_PARENT' in str(e)
  else:raise AssertionError('missing interface became absent description')
  absent_root=ET.fromstring(xml)
  for owner in absent_root.iter():
   for child in list(owner):
    if child.tag.rsplit('}',1)[-1] in ('description','descr','contact'):owner.remove(child)
  assert owned_value(p,ET.tostring(absent_root,encoding='unicode'))==(False,None)
  deleted=ET.fromstring(payload(p,restore_absent=True));assert any(x.get('{'+NC+'}operation')=='delete' for x in deleted.iter())
  empty=payload(p,'',restore_original=True);assert owned_value(p,empty)==(True,'')
  quoted=payload(p,'original "quoted" & label',restore_original=True);assert owned_value(p,quoted)==(True,'original "quoted" & label')
  assert canonical(payload(p,'two spaces'))!=canonical(payload(p,'two  spaces'))
  extra.append({'platform':p,'checks':8,'result':'PASS','scope':'offline XML wrapper, keyed parent existence, leaf/presence/inverse/escaping; not YANG validation'})
 report={'mode':'SYNTHETIC_OFFLINE','device_execution':False,'platform_guards':results,'xml_checks':extra,'total_checks':sum(x['passed'] for x in results)+sum(x['checks'] for x in extra)}
 save_atomic(Path(__file__).parent/'offline-results.json',report);print(json.dumps({'mode':report['mode'],'device_execution':False,'total_checks':report['total_checks'],'result':'PASS'}))
if __name__=='__main__':main()
