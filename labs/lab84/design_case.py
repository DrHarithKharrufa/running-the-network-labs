#!/usr/bin/env python3
"""Lab84: isolated Linux next-hop migration, unsafe order, link fault and rollback.

Static routes reproduce selected forwarding states; no OSPF/IS-IS process runs.
Requires root, iproute2 and iputils. Creates only four owned namespaces/veth pairs.
"""
import argparse
import json
import os
import platform
import subprocess
import time
import uuid


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if not args.run:
        print(json.dumps({'status':'NOT_RUN','scope':__doc__}));return 0
    if not hasattr(os,'geteuid') or os.geteuid()!=0:
        raise SystemExit('Linux root required; no namespace created.')
    prefix='rtn84-'+uuid.uuid4().hex[:8]
    ns={k:prefix+'-'+k for k in ('h','a','b','d')}
    owned=[];commands=[];assertions=[];phases=[]
    report={'status':'FAILED','scope':'Actual isolated Linux static-route forwarding. No routing daemons, commercial NOS, hardware, firewall/stateful application or production migration execution.',
            'kernel':platform.release(),'python':platform.python_version(),'namespaces':ns,
            'commands':commands,'assertions':assertions,'phases':phases}
    env=dict(os.environ,LC_ALL='C')

    def command(argv,check=True,timeout=10):
        result=subprocess.run(argv,capture_output=True,text=True,timeout=timeout,env=env)
        commands.append({'argv':argv,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        if check and result.returncode:raise RuntimeError(str(argv)+': '+result.stderr)
        return result

    def ip(key,*arguments,**kw):return command(['ip','-n',ns[key],*arguments],**kw)
    def execute(key,*arguments,**kw):return command(['ip','netns','exec',ns[key],*arguments],**kw)

    def expect(name,condition):
        assertions.append({'name':name,'passed':bool(condition)})
        if not condition:raise AssertionError(name)

    def pair(a,ia,aa,b,ib,ab):
        ip(a,'link','add','name',ia,'type','veth','peer','name',ib,'netns',ns[b])
        for key,interface,address in ((a,ia,aa),(b,ib,ab)):
            ip(key,'address','add',address,'dev',interface);ip(key,'link','set','dev',interface,'up')

    def choose(key,state):
        next_hop,device={('a','old'):('10.84.0.6','ab'),('a','new'):('10.84.0.2','ad'),
                         ('b','old'):('10.84.0.10','bd'),('b','new'):('10.84.0.5','ba')}[(key,state)]
        ip(key,'route','replace','10.84.255.1/32','via',next_hop,'dev',device)
        selected=json.loads(ip(key,'-j','route','get','10.84.255.1').stdout)[0]
        expect(key+' selected '+state,selected.get('gateway')==next_hop and selected['dev']==device)

    def probe(key='h',success=True,ttl=None):
        argv=['ping','-n','-c','3','-i','0.1','-W','1']
        if key=='b':argv+=['-I','10.84.0.6']
        if ttl is not None:argv+=['-t',str(ttl)]
        p=execute(key,*argv,'10.84.255.1',check=False)
        expect(key+(' reaches D' if success else ' fails to reach D'),p.returncode==(0 if success else 1))
        if success:expect(key+' all three probes received',' 0% packet loss' in p.stdout)
        return p

    def snapshot(name):
        phases.append({'name':name,'monotonic_s':time.monotonic(),
                       'routes':{k:json.loads(ip(k,'-j','route').stdout) for k in ns}})

    try:
        report['iproute2']=command(['ip','-Version']).stdout.strip()
        report['ping']=command(['ping','-V']).stdout.strip()
        for key in ns:
            command(['ip','netns','add',ns[key]]);owned.append(ns[key]);ip(key,'link','set','lo','up')
        pair('h','eth0','10.84.10.10/24','a','lan','10.84.10.1/24')
        pair('a','ad','10.84.0.1/30','d','da','10.84.0.2/30')
        pair('a','ab','10.84.0.5/30','b','ba','10.84.0.6/30')
        pair('b','bd','10.84.0.9/30','d','db','10.84.0.10/30')
        ip('d','address','add','10.84.255.1/32','dev','lo')
        for key,interfaces in {'a':('lan','ad','ab'),'b':('ba','bd'),'d':('da','db')}.items():
            execute(key,'sysctl','-qw','net.ipv4.ip_forward=1')
            for interface in ('all','default',*interfaces):
                for setting,value in (('rp_filter','0'),('send_redirects','0'),('ignore_routes_with_linkdown','1')):
                    execute(key,'sysctl','-qw',f'net.ipv4.conf.{interface}.{setting}={value}')
        ip('h','route','add','default','via','10.84.10.1')
        # Stable return routing D -> B -> A -> H, even when request path is A -> D.
        ip('b','route','add','10.84.10.0/24','via','10.84.0.5','dev','ba')
        ip('d','route','add','10.84.10.0/24','via','10.84.0.9','dev','db')
        ip('d','route','add','10.84.0.4/30','via','10.84.0.9','dev','db')
        choose('a','old');choose('b','old');snapshot('P0 old A->B->D')
        report['addresses']={k:json.loads(ip(k,'-j','address').stdout) for k in ns}
        for key in ('a','b','d'):
            expect(key+' no default route',all(r['dst']!='default' for r in phases[-1]['routes'][key]))
        probe();probe('b')

        # Deliberately unsafe test only inside the isolated lab, TTL bounds circulation.
        choose('b','new');snapshot('X1 unsafe B-first A->B->A')
        bad=probe(success=False,ttl=4)
        expect('TTL exceeded demonstrates forwarding loop','time to live exceeded' in bad.stdout.lower() or 'ttl exceeded' in bad.stdout.lower())
        choose('b','old');probe();snapshot('P0 restored after unsafe-order test')

        choose('a','new');probe();probe('b');snapshot('P1 A first, both direct to D')
        choose('b','new');probe();probe('b');snapshot('P2 new B->A->D')

        start=time.monotonic()
        ip('a','link','set','dev','ad','down');probe(success=False);snapshot('F1 candidate A-D fault')
        # Reverse safe order. B must cease using A before A returns to using B.
        choose('b','old');probe('b');snapshot('R1 B restored to direct D')
        choose('a','old');probe();probe('b');snapshot('R2 old service restored with A-D still down')
        report['fault_through_rollback_checks_seconds']=time.monotonic()-start
        expect('fault and recovery checks below 15-second lab allowance',report['fault_through_rollback_checks_seconds']<15)
        ip('a','link','set','dev','ad','up')
        # Interface-up does not reapply a deleted static route; choose() does so explicitly.
        choose('a','new');probe();choose('b','new');probe();probe('b');snapshot('P2 reapplied and verified')
        choose('b','old');choose('a','old');probe();snapshot('P0 final controlled rollback')
        report['status']='PASSED'
    except Exception as exc:
        report['error']=repr(exc)
    finally:
        report['cleanup']=[]
        for name in reversed(owned):
            try:
                result=command(['ip','netns','del',name],check=False)
                report['cleanup'].append({'namespace':name,'returncode':result.returncode})
            except Exception as exc:
                report['cleanup'].append({'namespace':name,'returncode':-1,'error':repr(exc)})
        try:
            remaining={line.split()[0] for line in command(['ip','netns','list']).stdout.splitlines() if line}
            report['owned_namespaces_removed']=all(name not in remaining for name in owned)
        except Exception as exc:
            report['owned_namespaces_removed']=False;report['cleanup_error']=repr(exc)
        if not report['owned_namespaces_removed'] or any(row['returncode'] for row in report['cleanup']):report['status']='FAILED'
        print(json.dumps(report,indent=2))
    return 0 if report['status']=='PASSED' else 1


if __name__=='__main__':raise SystemExit(main())
