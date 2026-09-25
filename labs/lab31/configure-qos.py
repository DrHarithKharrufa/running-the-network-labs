#!/usr/bin/env python3
"""Disposable Lab31 router only. Replaces eth2 root and eth1 ingress qdiscs."""
import argparse,subprocess,json

def tc(*args,check=True):
    cmd=['tc',*map(str,args)]
    r=subprocess.run(cmd,text=True,capture_output=True)
    print(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}),flush=True)
    if check and r.returncode: raise SystemExit(r.returncode)

def htb_class(cid,parent,rate,ceil,prio=0,quantum=1514):
    tc('class','add','dev','eth2','parent',parent,'classid',cid,'htb',
       'rate',rate,'ceil',ceil,'burst','16000','cburst','16000','prio',prio,'quantum',quantum)

def match(parent,pref,tos,flow):
    tc('filter','add','dev','eth2','protocol','ip','parent',parent,'pref',pref,
       'u32','match','ip','tos',tos,'0xfc','flowid',flow)

def configure(mode):
    tc('qdisc','del','dev','eth2','root',check=False)
    tc('qdisc','del','dev','eth1','ingress',check=False)
    if mode=='clear': return
    tc('qdisc','add','dev','eth2','root','handle','1:','htb','default','40' if mode=='fourclass' else '1')
    htb_class('1:1','1:','2mbit' if mode=='shaper' else '10mbit','2mbit' if mode=='shaper' else '10mbit')
    if mode=='fourclass':
        # HTB guarantees and ceilings: these are shapers, not strict-priority policers.
        for cid,rate,ceil,prio,q in [('10','500kbit','500kbit',0,1514),('20','2mbit','2mbit',1,1514),('30','4500kbit','10mbit',2,9084),('40','3mbit','10mbit',2,6056)]:
            htb_class('1:'+cid,'1:1',rate,ceil,prio,q)
            tc('qdisc','add','dev','eth2','parent','1:'+cid,'handle',cid+':',
               'fq_codel','limit','200','target','5ms','interval','100ms','noecn')
        for pref,tos,cid in [(1,'0xc0','10'),(2,'0xb8','20'),(3,'0x68','30')]:
            match('1:',pref,tos,'1:'+cid)
    elif mode.startswith('priority'):
        # Explicit default prevents the legacy TOS priomap from choosing a band.
        tc('qdisc','add','dev','eth2','parent','1:1','handle','10:','prio','bands','3','priomap',*([2]*16))
        for band in range(1,4):
            tc('qdisc','add','dev','eth2','parent','10:'+str(band),'handle',str(10+band)+':','pfifo','limit','200')
        match('10:',1,'0xb8','10:1')
    else:
        args=['fq_codel','limit','200','target','5ms','interval','100ms','noecn'] if mode=='fq' else ['pfifo','limit','200']
        tc('qdisc','add','dev','eth2','parent','1:1','handle','10:',*args)
    if mode in ['policer','priority-policed']:
        tc('qdisc','add','dev','eth1','handle','ffff:','ingress')
        tc('filter','add','dev','eth1','parent','ffff:','protocol','ip','pref','1','u32',
           'match','ip','tos','0xb8','0xfc','action','police','rate','2mbit','burst','16000',
           'mtu','1500','conform-exceed','drop/ok')
    for kind in ['qdisc','class','filter']:
        tc('-s','-d',kind,'show','dev','eth2')
    tc('-s','-d','filter','show','dev','eth1','parent','ffff:')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['clear','fifo','fq','fourclass','priority','priority-policed','shaper','policer'])
    configure(p.parse_args().mode)
