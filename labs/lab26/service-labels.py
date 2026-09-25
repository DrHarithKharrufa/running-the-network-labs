"""Install a manual two-label fixture inside a fresh, isolated Lab26 PE only."""
import json,subprocess as sp,sys
def run(*args):return sp.check_output(args,text=True)
side=sys.argv[1]
assert side in ['left','right']
local,remote,lo,via,label,remote_label=(1,2,24,'10.254.1.5',24001,24002) if side=='left' else (2,1,23,'10.254.1.6',24002,24001)
routes=json.loads(run('ip','-j','route','show',f'10.255.0.{lo}/32'))
assert len(routes)==1,routes
enc=routes[0].get('encap',{})
assert enc.get('encap_type',enc.get('type'))=='mpls',routes
transport=int(str(enc.get('dst',enc.get('labels'))).split('/')[0])
assert 15<transport<65536
assert not json.loads(run('ip','-j','-f','mpls','route','show',str(label))), 'Service label already installed; inspect before retrying'
bindings=run('vtysh','-c','show mpls ldp ipv4 binding')
assert str(label) not in bindings, 'Reserved teaching label appears in an LDP binding; inspect allocation'
assert not json.loads(run('ip','-j','route','show',f'10.26.{remote}.10/32')), 'Service route already installed'
run('ip','-f','mpls','route','add',str(label),'via','inet',f'10.26.{local}.10','dev','eth2')
run('ip','route','add',f'10.26.{remote}.10/32','encap','mpls',f'{transport}/{remote_label}','via',via,'dev','eth1')
print(json.dumps({'side':side,'transport':transport,'outgoing_service':remote_label,'incoming_service':label}))
