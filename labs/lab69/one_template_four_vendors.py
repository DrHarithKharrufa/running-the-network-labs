#!/usr/bin/env python3
"""Render a bounded access-port intent with explicit platform mappings.

Local Jinja execution only. Equal renderings establish determinism, not device
application idempotency. Candidate snippets require platform/state validation.
"""
import argparse,json,re,runpy
from pathlib import Path
from jinja2 import Environment,FileSystemLoader,StrictUndefined

ROOT=Path(__file__).resolve().parent
ENV=Environment(loader=FileSystemLoader(ROOT/'templates'),undefined=StrictUndefined,
                autoescape=False,keep_trailing_newline=True,trim_blocks=True,lstrip_blocks=True)
INTENT={'description':'server-07','mode':'access','vlan':30}
TARGETS={
 'Cisco IOS-XE':{'profile':'c9300-iosxe-17.15','interface':'GigabitEthernet1/0/8','template':'iosxe.j2'},
 'Arista EOS':{'profile':'eos-4.36.2F-ethernet','interface':'Ethernet8','template':'eos.j2'},
 'Nokia SR Linux':{'profile':'srl-24.10-7220-ixr','interface':'ethernet-1/8','template':'srlinux.j2'},
 'Juniper Junos':{'profile':'junos-els-ex','interface':'ge-0/0/8','template':'junos.j2'}}
PATTERNS={'c9300-iosxe-17.15':r'GigabitEthernet[1-9][0-9]*/0/[1-9][0-9]*',
 'eos-4.36.2F-ethernet':r'Ethernet[1-9][0-9]*(?:/[1-9][0-9]*){0,2}',
 'srl-24.10-7220-ixr':r'ethernet-[1-9][0-9]*/[1-9][0-9]*',
 'junos-els-ex':r'ge-0/0/[0-9]+'}

def validate(intent,target):
    if not isinstance(intent,dict) or set(intent)!={'description','mode','vlan'}:raise ValueError('Unexpected or missing intent fields')
    if intent['mode']!='access':raise ValueError('This example supports only untagged access intent')
    if type(intent['vlan']) is not int or not 1<=intent['vlan']<=4094:raise ValueError('VLAN must be an integer from 1 to 4094')
    if not isinstance(intent['description'],str) or not re.fullmatch(r'[A-Za-z0-9 ._:/-]{1,80}',intent['description']):
        raise ValueError('Description must use the teaching subset; no quotes, newlines or control syntax')
    if target not in TARGETS:raise ValueError('Unsupported target')
    mapping=TARGETS[target]
    if not re.fullmatch(PATTERNS[mapping['profile']],mapping['interface']):raise ValueError('Interface mapping does not match profile')
    return mapping

def render(target,intent=None):
    data=INTENT if intent is None else intent;mapping=validate(data,target)
    return ENV.get_template(mapping['template']).render(**data,interface=mapping['interface'],service_name=f"VLAN{data['vlan']}")

def render_all(intent=None):return {target:render(target,intent) for target in TARGETS}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--demo-original',action='store_true');p.add_argument('--write',type=Path);a=p.parse_args()
    if a.demo_original:
        print('Historical flawed programme: SR Linux syntax and idempotency claims below are wrong.')
        runpy.run_path(str(ROOT/'original_one_template_four_vendors.py'),run_name='__main__')
        print('Correction: deterministic text is not application idempotency; use the repaired platform mappings.')
        return
    first=render_all()
    for target,text in first.items():print(f'--- {target}: {TARGETS[target]["profile"]} ---\n{text}')
    print('Deterministic rendering:',first==render_all())
    print('No device was contacted; application idempotency and forwarding remain untested.')
    if a.write:
        a.write.mkdir(parents=True,exist_ok=True)
        for target,text in first.items():(a.write/(TARGETS[target]['template'].replace('.j2','.cfg'))).write_text(text,encoding='utf-8')
        (a.write/'intent-manifest.json').write_text(json.dumps({'intent':INTENT,'targets':TARGETS,'scope':'candidate fragments only'},indent=2)+'\n')

if __name__=='__main__':main()
