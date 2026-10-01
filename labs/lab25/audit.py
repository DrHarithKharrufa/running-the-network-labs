"""Read-only Kestrel configuration inventory and graph/arithmetic models; no NOS execution."""
from pathlib import Path
import argparse,json,re,hashlib,itertools,ipaddress
from decimal import Decimal
import yaml

BASE=Path(__file__).resolve().parent
T=BASE.parent/'topologies'

def inspect():
 data=yaml.safe_load((T/'kestrel.clab.yml').read_text(encoding='utf-8'))['topology']
 nodes=data['nodes'];inventory={};issues=[];allfiles={};checks=[]
 def check(name,value):
  assert value,name
  checks.append({'name':name,'passed':True})
 for name,c in nodes.items():
  files=[]
  if 'startup-config' in c:files.append(T/c['startup-config'])
  files += [T/s.split(':',1)[0] for s in c.get('binds',[])]
  body='\n'.join(p.read_text(encoding='utf-8') for p in files)
  for p in files:allfiles[p.relative_to(T).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
  interfaces={};current=None
  if c['kind']=='nokia_srlinux':
   for line in body.splitlines():
    m=re.match(r'set / interface (\S+) subinterface \d+ ipv4 address (\S+)',line)
    if m:interfaces[m[1].replace('ethernet-1/','e1-')]=m[2]
   neighbors=re.findall(r'protocols bgp neighbor (\S+) peer-group IBGP',body)
  else:
   for line in body.splitlines():
    if line.startswith('interface '):current=line.split()[1]
    m=re.match(r' ip address (\S+)',line)
    if m and current:interfaces[current]=m[1]
   for line in c.get('exec',[]):
    m=re.match(r'ip addr (?:add|replace) (\S+) dev (\S+)',line)
    if m:interfaces[m[2]]=m[1]
   neighbors=re.findall(r' neighbor ([0-9.]+) peer-group',body)
  inventory[name]={'addresses':interfaces,'configured_ibgp_neighbors':neighbors,'files':[p.relative_to(T).as_posix() for p in files]}
  if 'no bgp ebgp-requires-policy' in body:issues.append({'node':name,'issue':'Explicit eBGP policy requirement disabled; inspect import/export safety.'})
  if name.endswith('-p-01') and 'protocols bgp admin-state enable' in body:issues.append({'node':name,'issue':'Core carries BGP in this IPv4 baseline; not a demonstrated BGP-free MPLS core.'})
  if c['kind']=='nokia_srlinux' and '-p-' not in name:
   if 'export-policy' not in body:issues.append({'node':name,'issue':'No explicit external export policy in supplied file.'})
   if 'next-hop' not in body:issues.append({'node':name,'issue':'No explicit next-hop-self handling; validate external next-hop reachability at every internal recipient.'})
   if 'match prefix' not in body and '-IN statement 10 action policy-result accept' in body:issues.append({'node':name,'issue':'Ingress accept statement has no prefix/path eligibility guard.'})
  for prefix in re.findall(r'\b(?:network|ip route) (\d+\.\d+\.\d+\.\d+/\d+)',body):
   if prefix in ['198.20.0.0/16','198.21.0.0/16']:issues.append({'node':name,'issue':prefix+' is not in the 198.18.0.0/15 benchmarking block.'})
 links=[];used=set()
 for item in data['links']:
  ends=item['endpoints'];parsed=[]
  for end in ends:
   check('endpoint unique '+end,end not in used);used.add(end)
   n,iface=end.split(':');addr=inventory[n]['addresses'].get(iface)
   check('address recorded '+end,addr is not None);parsed.append((n,iface,ipaddress.ip_interface(addr)))
  a,b=parsed
  check('same prefix '+','.join(ends),a[2].network==b[2].network and a[2].ip!=b[2].ip)
  links.append({'endpoints':ends,'addresses':[str(a[2]),str(b[2])],'prefix':str(a[2].network)})
 # Session reciprocity is an inventory condition, not a claim that peers establish.
 loopowner={str(ipaddress.ip_interface(v).ip):n for n,d in inventory.items() for k,v in d['addresses'].items() if k in ['lo','system0']}
 for n,d in inventory.items():
  myloop=next((ip for ip,owner in loopowner.items() if owner==n),None)
  for peer in d['configured_ibgp_neighbors']:
   owner=loopowner.get(peer)
   if owner and myloop not in inventory[owner]['configured_ibgp_neighbors']:
    issues.append({'node':n,'issue':f'iBGP declaration towards {owner} is not reciprocated.'})
 for ends in [('lon-pe-01:e1-1','bhm-p-01:e1-3'),('bhm-bng-01:eth1','lds-p-01:e1-3')]:
  if any(set(x['endpoints'])==set(ends) for x in links):issues.append({'node':ends[0].split(':')[0],'issue':'Cross-site-labelled attachment differs from Chapter25 local-edge planning diagram; physical intent must be reconciled.'})
 issues.append({'node':'service model','issue':'No complete subscriber, CGN, IPv6, VPN or MPLS service acceptance evidence is supplied by this IPv4 inventory.'})

 # Undirected reachability only. Both transit endpoints are considered equivalent
 # for the artificial requirement "at least one general transit path".
 adjacency={n:set() for n in nodes}
 for link in links:
  a,b=[x.split(':')[0] for x in link['endpoints']];adjacency[a].add(b);adjacency[b].add(a)
 service={'host-cust':{'unit':'business circuits','count':900},'host-sub':{'unit':'broadband subscriptions','count':50000}}
 def exposure(failed):
  lost=[]
  for host,details in service.items():
   reached=set();todo=[host]
   while todo:
    n=todo.pop()
    if n in failed or n in reached:continue
    reached.add(n);todo.extend(adjacency[n]-reached-set(failed))
   if not reached.intersection({'transit-a','transit-b'}):lost.append({'representative':host,**details})
  return {'failed':list(failed),'exposed':lost,'weighted_service_units':sum(x['count'] for x in lost)}
 internal=[n for n in nodes if n.startswith(('lon-','man-','bhm-','lds-'))]
 cases=[exposure(x) for size in [0,1,2] for x in itertools.combinations(internal,size)]
 check('baseline abstract reachability',cases[0]['weighted_service_units']==0)
 check('worst single weighted exposure',max(x['weighted_service_units'] for x in cases if len(x['failed'])==1)==50000)
 check('paired borders remove general-transit paths',exposure(['lon-pr-01','man-pr-01'])['weighted_service_units']==50900)
 check('paired service edges remove both representatives',exposure(['lon-pe-01','bhm-bng-01'])['weighted_service_units']==50900)

 net=ipaddress.ip_network;parent=net('2001:db8:4000::/36');small=net('2001:db8:4000::/40');business=net('2001:db8:4000::/38');oldbroad=net('2001:db8:4100::/40');broad=net('2001:db8:4400::/40')
 check('undersized business reservation',2**(48-small.prefixlen)==256<900)
 check('expanded business overlaps former broadband',business.overlaps(oldbroad))
 check('corrected reservations contained',business.subnet_of(parent) and broad.subnet_of(parent))
 check('corrected reservations disjoint',not business.overlaps(broad))
 check('corrected reservation capacities',2**(48-business.prefixlen)==1024 and 2**(56-broad.prefixlen)==65536)
 def bill(rate,commit=10000):return Decimal(max(rate,commit))*Decimal('.10')
 economics={'before':str(bill(12000)),'after_transit':str(bill(9000)),'after_with_300_peer':str(bill(9000)+300),'delta':str(bill(9000)+300-bill(12000)),'exercise_peer100':str(bill(9000)+100),'exercise_commit8000_peer300':str(bill(9000,8000)+300)}
 check('marginal bill counterexample',economics['before']=='1200.00' and economics['after_with_300_peer']=='1300.00' and economics['delta']=='100.00')
 return {'scope':__doc__,'topology_sha256':hashlib.sha256((T/'kestrel.clab.yml').read_bytes()).hexdigest(),'source_hashes':allfiles,'inventory':inventory,'links':links,'open_issues':issues,'graph_assumptions':'Undirected physical graph; no protocols, capacity, shared risks, service state or Internet reachability proof. Each host represents an entire fictional population; summed units are not unique customers. Peer does not satisfy general-transit requirement.','graph_cases':cases,'economics_hypothetical_GBP_ex_VAT':economics,'checks':checks}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 result=inspect();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'checks_passed':len(result['checks']),'graph_cases':len(result['graph_cases']),'open_issues':len(result['open_issues']),'report':str(args.output)}))
