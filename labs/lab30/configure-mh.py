"""Run only inside the named disposable Lab30 node; experimental multihoming setup."""
import sys,subprocess as sp
node=sys.argv[1]
assert node in ['pe2','pe3','host4']
def ip(*a):sp.run(['ip',*a],check=True)
ip('link','add','bond30','type','bond','mode','802.3ad','miimon','100','lacp_rate','fast','xmit_hash_policy','layer3+4','min_links','1')
if node=='host4':
 ip('link','set','bond30','address','02:00:30:00:00:04')
 ports=['eth1','eth2']
else:
 ip('link','set','bond30','address','02:00:30:ee:00:04')
 ip('link','set','bond30','type','bond','ad_actor_system','02:00:30:ee:00:04')
 ports=['eth4']
for d in ports:
 ip('link','set',d,'down');ip('link','set',d,'master','bond30')
if node=='host4':ip('address','add','10.30.0.4/24','dev','bond30')
else:ip('link','set','bond30','master','br30')
ip('link','set','bond30','mtu','1500','up')
for d in ports:ip('link','set',d,'mtu','1500','up')
