"""Add the static SRv6 fixture inside ONE freshly started Lab28 router.

Run as root in the node, after underlay convergence. Stop on any error;
inspect partial state or recreate the disposable topology before retrying.
This file does not implement BGP service signalling or access control.
"""
import sys,subprocess,json
n=sys.argv[1]
if n not in ['r1','r2','r3','r4']:raise SystemExit('Expected r1, r2, r3 or r4')
def run(*args):
 result=subprocess.run(['ip',*args],capture_output=True,text=True)
 print(json.dumps({'command':['ip',*args],'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}),flush=True)
 result.check_returncode()
if n=='r2':
 run('-6','route','add','2001:db8:4500:2:100::/128','encap','seg6local','action','End','count','dev','eth2')
elif n=='r3':
 run('-6','route','add','2001:db8:4500:3:200::/128','encap','seg6local','action','End.X','nh6','2001:db8:4500:ff34::1','count','dev','eth2')
else:
 i=1 if n=='r1' else 4
 via='2001:db8:4500:ff12::1' if i==1 else '2001:db8:4500:ff34::0'
 for colour,table,func in [('blue','100','400'),('red','200','401')]:
  run('-6','route','add',f'2001:db8:4500:{i}:{func}::/128','encap','seg6local','action','End.DT4','vrftable',table,'count','dev',colour)
  run('-6','route','add','2001:db8:4500::/48','vrf',colour,'via',via,'dev','eth1','onlink')
  segs=f'2001:db8:4500:2:100::,2001:db8:4500:3:200::,2001:db8:4500:4:{func}::' if i==1 else f'2001:db8:4500:1:{func}::'
  run('route','add',f'10.28.{2 if i==1 else 1}.0/24','vrf',colour,'encap','seg6','mode','encap','segs',segs,'dev','eth1')
