"""Isolated FRR acceptance extensions: physical loss, BFD client, auth, dual stack.

Linux root, Docker and PyYAML required. No physical interface is attached.
Usage: python3 harness/workbook_checks.py --out evidence/workbook-checks
"""
import argparse,copy,json,sys,time
from pathlib import Path
import netlab

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True)
    ap.add_argument('--addresses-only',action='store_true');a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    failures=[]
    def execute(topo,node,commands,cli=True):
        argv=['docker','exec',netlab.node_name(topo,node)]
        if cli:
            argv+=['vtysh']
            for c in commands:argv+=['-c',c]
        else:argv+=commands
        result=netlab.sh(argv,check=False)
        netlab.CONFIG_RECORDS.append({'node':node,'commands':commands,'returncode':result.returncode,
                                     'stdout':result.stdout,'stderr':result.stderr})
        if result.returncode or any(x in (result.stdout+result.stderr).lower() for x in ('unknown command','invalid input')):
            raise RuntimeError(result.stdout+result.stderr)
    def record(topo,name,caps,wait=2):
        current=copy.deepcopy(topo);current['capture']=caps
        result=netlab.capture(current,str(out/(name+'.json')),wait)
        if result:failures.append(name)
    def route(next_hop,distance):
        return {'node':'r1','cmd':'show ip route 10.255.0.2/32',
                'require':['Known via "static"',f'distance {distance}',next_hop]}
    def ping(destination='10.255.0.2',source='10.255.0.1'):
        return {'node':'r1','cli':'shell','cmd':f'ping -c 3 -W 2 -I {source} {destination}',
                'packet_loss':0,'require':['packets transmitted','received']}
    # Complete baseline and capture remain part of every phase's evidence.
    topo=netlab.load(Path(__file__).parent/'topologies/igp-static-bfd.yml');topo['name']='rtncheck-static'
    netlab.CONFIG_RECORDS.clear();topo['_owned']=[]
    try:
        if a.addresses_only: raise SkipEarlier()
        netlab.up(topo);netlab.configure(topo)
        record(topo,'static-before',[route('10.0.12.1',1),ping()],25)
        execute(topo,'r1',['ip','link','set','eth1','down'],False)
        record(topo,'static-failed-link',[route('10.0.13.1',200),ping()],5)
        execute(topo,'r1',['ip','link','set','eth1','up'],False)
        record(topo,'static-restored',[route('10.0.12.1',1),ping()],5)
        for node,prefix,peer in [('r1','10.255.0.2/32','10.0.12.1'),('r2','10.255.0.1/32','10.0.12.0')]:
            execute(topo,node,['configure terminal',f'no ip route {prefix} {peer}',f'ip route {prefix} {peer} bfd'])
        bfd=lambda state:{'node':'r1','cmd':'show bfd static route','require':['10.255.0.2/32',f'status: {state}']}
        record(topo,'bfd-bound-up',[bfd('installed'),route('10.0.12.1',1),ping()],5)
        execute(topo,'r2',['configure terminal','bfd','peer 10.0.12.0','shutdown'])
        record(topo,'bfd-peer-down-link-up',[bfd('uninstalled'),route('10.0.13.1',200),ping(),
            {'node':'r1','cli':'shell','cmd':'ip link show eth1','expect':'LOWER_UP'}],5)
        execute(topo,'r2',['configure terminal','bfd','peer 10.0.12.0','no shutdown'])
        record(topo,'bfd-recovered',[bfd('installed'),route('10.0.12.1',1),ping()],5)
    except SkipEarlier:pass
    finally:netlab.down(topo)
    topo=netlab.load(Path(__file__).parent/'topologies/igp-ospf-areas.yml');topo['name']='rtncheck-auth'
    netlab.CONFIG_RECORDS.clear();topo['_owned']=[]
    neighbour={'node':'r1','cmd':'show ip ospf neighbor','require':['Neighbor ID'],'expect':'Full/-'}
    try:
        if a.addresses_only: raise SkipEarlier()
        netlab.up(topo);netlab.configure(topo)
        record(topo,'auth-before',[neighbour,ping('10.255.1.4')],60)
        execute(topo,'r2',['configure terminal','interface eth1','ip ospf message-digest-key 1 md5 lab-key-wrong'])
        execute(topo,'r2',['clear ip ospf process'])
        record(topo,'auth-wrong-key',[{**neighbour,'expect':r'(?s)^(?!.*Full).*$'}],45)
        execute(topo,'r2',['configure terminal','interface eth1','ip ospf message-digest-key 1 md5 lab-key-one'])
        execute(topo,'r2',['clear ip ospf process'])
        record(topo,'auth-restored',[neighbour,ping('10.255.1.4')],45)
    except SkipEarlier:pass
    finally:netlab.down(topo)
    topo=netlab.load(Path(__file__).parent/'topologies/ospf-p2p.yml');topo['name']='rtncheck-address'
    netlab.CONFIG_RECORDS.clear();topo['_owned']=[]
    try:
        netlab.up(topo);netlab.configure(topo)
        for node,address in [('r1','2001:db8:12::/127'),('r2','2001:db8:12::1/127')]:
            ipv4='10.0.12.0/31' if node=='r1' else '10.0.12.1/31'
            execute(topo,node,['ip','address','replace',ipv4,'dev','eth1'],False)
            execute(topo,node,['sysctl','-w','net.ipv6.conf.eth1.disable_ipv6=0'],False)
            execute(topo,node,['ip','-6','address','replace',address,'dev','eth1'],False)
        caps=[{'node':node,'cli':'shell','cmd':f'ping {family} -c 3 -W 2 {peer}',
               'packet_loss':0,'require':['packets transmitted','received']}
              for node,family,peer in [('r1','-4','10.0.12.1'),('r2','-4','10.0.12.0'),
                                       ('r1','-6','2001:db8:12::1'),('r2','-6','2001:db8:12::')]]
        record(topo,'dual-stack-addresses',caps,5)
    finally:netlab.down(topo)
    (out/'summary.json').write_text(json.dumps({'failed_phases':failures,'scope':'FRR 10.2.1 / Linux virtual forwarding; no hardware timing claim'},indent=2))
    return 1 if failures else 0

class SkipEarlier(Exception):pass

if __name__=='__main__':raise SystemExit(main())
