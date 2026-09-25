#!/usr/bin/env python3
"""Local teaching model: validate, render a candidate and report drift. No writes.

The output is a small Arista EOS syntax illustration, not a complete deployable
configuration or a NetBox implementation. See README for prerequisites and scope.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import re
import runpy

SOT={'ald-leaf-01':{'platform':'arista_eos','role':'leaf','site':'lon',
    'owner':'campus-network','version':7,'approved_at':'2026-09-24T09:00:00Z',
    'interfaces':{'Ethernet1':{'desc':'to-spine-1','mode':'routed','ip':'10.200.1.1/31'},
                  'Ethernet8':{'desc':'server-07','mode':'access','vlan':30}}}}
OBSERVED={'ald-leaf-01':{'collected_at':'2026-09-24T09:59:00Z','source':'synthetic-fixture',
    'complete':True,'interfaces':deepcopy(SOT['ald-leaf-01']['interfaces'])}}
OBSERVED['ald-leaf-01']['interfaces']['Ethernet8']['desc']='TEMP hand-edit'
NOW='2026-09-24T10:00:00Z'

def timestamp(text):
    if not isinstance(text,str):raise ValueError('Timestamp must be text')
    try:value=datetime.fromisoformat(text.replace('Z','+00:00'))
    except ValueError as exc:raise ValueError('Invalid timestamp') from exc
    if value.tzinfo is None:raise ValueError('Timezone required')
    return value.astimezone(timezone.utc)

def clean_text(value,label):
    if not isinstance(value,str) or not value or any(ord(c)<32 or ord(c)>126 for c in value):
        raise ValueError(label+' must be non-empty, single-line ASCII in this model')
    return value

def validate_intent(record):
    if record.get('platform')!='arista_eos':raise ValueError('Unsupported platform')
    clean_text(record.get('owner'),'owner')
    if type(record.get('version')) is not int or record['version']<1:raise ValueError('Invalid version')
    timestamp(record.get('approved_at'))
    interfaces=record.get('interfaces')
    if not isinstance(interfaces,dict) or not interfaces:raise ValueError('Interfaces required')
    for name,port in interfaces.items():
        if not isinstance(name,str) or not re.fullmatch(r'Ethernet[1-9][0-9]*(?:/[1-9][0-9]*){0,2}',name):
            raise ValueError('Unsupported interface name')
        if not isinstance(port,dict):raise ValueError('Port must be an object')
        clean_text(port.get('desc'),'description')
        mode=port.get('mode')
        keys={'desc','mode','ip'} if mode=='routed' else {'desc','mode','vlan'}
        if mode not in {'routed','access'} or set(port)!=keys:raise ValueError('Unknown mode or incompatible fields')
        if mode=='access':
            if type(port['vlan']) is not int or not 1<=port['vlan']<=4094:raise ValueError('Invalid VLAN')
        else:
            if not isinstance(port['ip'],str) or '/' not in port['ip']:raise ValueError('Explicit IPv4 prefix required')
            address=ipaddress.ip_interface(port['ip'])
            if address.version!=4 or address.network.prefixlen==0:raise ValueError('Only non-default IPv4 prefixes here')
            if address.network.prefixlen<31 and address.ip in (address.network.network_address,address.network.broadcast_address):
                raise ValueError('Network/broadcast address is not a host here')
    return record

def render(device,source=None):
    record=validate_intent((SOT if source is None else source)[device])
    lines=['! Candidate only: verify platform, VLAN existence and existing state.']
    for name,port in sorted(record['interfaces'].items()):
        lines.extend([f'interface {name}',f" description {port['desc']}"])
        if port['mode']=='access':
            lines.extend([' switchport',' switchport mode access',f" switchport access vlan {port['vlan']}"])
        else:lines.extend([' no switchport',f" ip address {ipaddress.ip_interface(port['ip'])}"])
        lines.append('!')
    return '\n'.join(lines)

def reconcile(device,source=None,observed=None,*,now=NOW,expected_version=7,
              max_age_seconds=300,emergency=False,conflict=False):
    intended=validate_intent((SOT if source is None else source)[device])
    actual=(OBSERVED if observed is None else observed)[device]
    if type(max_age_seconds) not in (int,float) or not 0<max_age_seconds<float('inf'):
        raise ValueError('Freshness limit must be finite and positive')
    current=timestamp(now);collected=timestamp(actual.get('collected_at'))
    approved=timestamp(intended['approved_at'])
    blocks=[]
    if intended['version']!=expected_version:blocks.append('intent version changed')
    if approved>current:blocks.append('approval timestamp is in the future')
    if not 0<=(current-collected).total_seconds()<=max_age_seconds:blocks.append('stale or future observation')
    if collected<approved:blocks.append('observation predates approved intent')
    if actual.get('complete') is not True:blocks.append('incomplete observation')
    if not actual.get('source'):blocks.append('missing observation provenance')
    if emergency:blocks.append('emergency exception requires reconciliation')
    if conflict:blocks.append('conflicting evidence')
    have=actual.get('interfaces')
    if not isinstance(have,dict) or any(not isinstance(v,dict) for v in have.values()):raise ValueError('Invalid observation shape')
    want=intended['interfaces'];changes=[]
    for name in sorted(set(want)|set(have)):
        if name not in want or name not in have:
            changes.append({'interface':name,'kind':'observed_only' if name not in want else 'intended_only',
                            'intended':want.get(name),'observed':have.get(name)})
            continue
        for field in sorted(set(want[name])|set(have[name])):
            w_present=field in want[name];h_present=field in have[name]
            if w_present!=h_present or want[name].get(field)!=have[name].get(field):
                changes.append({'interface':name,'field':field,'intended_present':w_present,'observed_present':h_present,
                                'intended':want[name].get(field),'observed':have[name].get(field)})
    status='BLOCKED' if blocks else ('REVIEW_REQUIRED' if changes else 'NO_DRIFT_IN_SCOPE')
    return {'status':status,'block_reasons':blocks,'changes':changes,'owner':intended['owner'],
            'intent_version':intended['version'],'approved_at':intended['approved_at'],
            'collected_at':actual['collected_at'],'source':actual.get('source'),
            'action':'No writes. Owner assesses intent, observation, service impact and approved change path.'}

def duplicate_hosts(rows,unique_namespaces):
    """Local allocation policy for ordinary unicast hosts; not NetBox's validator.

    Namespace None is global. Shared-address roles require a separate design and
    are deliberately not implemented here. Prefix nesting is not host duplication.
    """
    seen=set();duplicates=[]
    for row in rows:
        namespace=row['namespace'];host=str(ipaddress.ip_interface(row['address']).ip)
        key=(namespace,host)
        if namespace in unique_namespaces and key in seen:duplicates.append(key)
        seen.add(key)
    return duplicates

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--demo-original',action='store_true');args=parser.parse_args()
    if args.demo_original:
        print('Historical flawed model; its re-push advice is not approved reconciliation.')
        runpy.run_path(str(Path(__file__).with_name('original_render_from_sot.py')),run_name='__main__')
        print('Correction: compare both sides, preserve provenance and require a reviewed decision; never push here.')
        return
    print(render('ald-leaf-01'));print(json.dumps(reconcile('ald-leaf-01'),indent=2))

if __name__=='__main__':main()
