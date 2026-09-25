"""Small route-visibility model; neither a NOS parser nor a forwarding simulator."""
from ipaddress import ip_network
from collections import defaultdict
import json
from pathlib import Path

TENANTS = {'CUST-A': (1001, '10.101.0.0/24'),
           'CUST-B': (1002, '10.102.0.0/24'),
           'CUST-C': (1003, '10.103.0.0/24')}
EXPORTS = {**{v: {prefix} for v, (_, prefix) in TENANTS.items()},
           'SERVICES': {'10.109.0.0/24'}}
IMPORTS = {**{v: {f'64500:{rt}', '64500:9000'} for v, (rt, _) in TENANTS.items()},
           'SERVICES': {f'64500:{rt}' for rt, _ in TENANTS.values()}}

def export(origin, prefix, rts):
    prefix = str(ip_network(prefix, strict=True))
    if prefix not in EXPORTS[origin]:
        return None
    return {'origin': origin, 'prefix': prefix, 'rts': set(rts)}

def eligible(route, vrf):
    return route is not None and bool(route['rts'] & IMPORTS[vrf])

def run():
    results=[]
    def check(name, actual, expected):
        if actual != expected:
            raise AssertionError(f'{name}: {actual!r} != {expected!r}')
        results.append({'case':name,'actual':actual,'expected':expected,'passed':True})
    service=export('SERVICES','10.109.0.0/24',{'64500:9000'})
    routes={v:export(v,p,{f'64500:{rt}'}) for v,(rt,p) in TENANTS.items()}
    for tenant in TENANTS:
        check(f'{tenant} imports services',eligible(service,tenant),True)
        check(f'SERVICES imports {tenant}',eligible(routes[tenant],'SERVICES'),True)
        for other in TENANTS:
            if other!=tenant:
                check(f'{tenant} does not import {other}',eligible(routes[other],tenant),False)
    for prefix in ['0.0.0.0/0','10.109.0.0/25','10.109.0.0/16','10.101.0.0/24']:
        check(f'service export rejects {prefix}',export('SERVICES',prefix,{'64500:9000'}),None)
    # VPN uniqueness versus ambiguity after import into one IPv4 context.
    vpn=[{'rd':f'10.255.0.1:{rt}','prefix':'10.0.0.0/24','tenant':v}
         for v,(rt,_) in TENANTS.items()]
    check('three distinct VPN route identities',len({(r['rd'],r['prefix']) for r in vpn}),3)
    choices=defaultdict(list)
    for r in vpn:
        choices[r['prefix']].append(r['tenant'])
    check('one shared IP destination has three tenant candidates',len(choices['10.0.0.0/24']),3)
    return {'scope':'Handwritten exact-prefix and RT-set model. Does not parse configuration, select BGP paths, establish labels, enforce ports, or prove packet isolation.',
            'cases':results,'passed':len(results)}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=run()
    rendered=json.dumps(result,indent=2)
    if args.output:
        args.output.write_text(rendered+'\n',encoding='utf8')
    print(rendered)
