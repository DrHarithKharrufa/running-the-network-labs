"""Offline inventory and policy-text checks. This is not a NOS parser or runtime."""
from pathlib import Path
import re, shlex, unittest, ipaddress
import yaml

ROOT=Path(__file__).resolve().parent

def parse_policy(text):
    sets={};paths={};communities={};policies={}
    for line in text.splitlines():
        if not line.startswith('set / routing-policy '):continue
        t=shlex.split(line)[3:]
        if t[0]=='prefix-set':sets.setdefault(t[1],set()).add(t[3])
        elif t[0]=='as-path-set':paths[t[1]]=t[3]
        elif t[0]=='community-set':communities[t[1]]=set(t[4:-1])
        elif t[0]=='policy':
            p=policies.setdefault(t[1],{'statements':{},'default':None})
            if t[2]=='default-action':p['default']=t[-1]
            else:p['statements'].setdefault(int(t[3]),[]).append(t[4:])
    return sets,paths,communities,policies

def evaluate(text,name,prefix,path,comms=()):
    sets,paths,cs,pols=parse_policy(text);c=set(comms);lp=None
    for _,items in sorted(pols[name]['statements'].items()):
        matches=True
        for t in items:
            if t[0]!='match':continue
            if t[1]=='prefix-set':matches &= prefix in sets[t[2]]
            elif t[1:3]==['bgp','as-path-set']:matches &= re.fullmatch(paths[t[3]],path) is not None
            elif t[1:3]==['bgp','community-set']:matches &= cs[t[3]].issubset(c)
            elif t[1:]!=['protocol','bgp']:raise ValueError(f'unsupported match {t}')
        if not matches:continue
        result=None
        for t in items:
            if t[:2]==['action','policy-result']:result=t[2]
            elif t[:3]==['action','bgp','communities']:
                if t[3]=='remove':c-=cs[t[4]]
                elif t[3]=='add':c|=cs[t[4]]
                else:raise ValueError(t)
            elif t[:4]==['action','bgp','local-preference','set']:lp=int(t[4])
        if result in ['accept','reject']:return result,c,lp
    return pols[name]['default'],c,lp

class Inventory(unittest.TestCase):
    def test_endpoint_uniqueness_and_documented_port_range(self):
        for name,nodes,links in [('aldergate',12,14),('kestrel',14,14),('anvil',10,12)]:
            doc=yaml.safe_load((ROOT/(name+'.clab.yml')).read_text());t=doc['topology'];self.assertEqual(len(t['nodes']),nodes);self.assertEqual(len(t['links']),links);seen=set()
            for link in t['links']:
                for e in link['endpoints']:
                    node,iface=e.split(':');self.assertIn(node,t['nodes']);self.assertNotIn(e,seen);seen.add(e)
                    if t['nodes'][node]['kind']=='nokia_srlinux':
                        model=t['kinds']['nokia_srlinux']['type'];self.assertIn(model,['ixr-d2','ixr-d3']);self.assertRegex(iface,r'^e1-\d+$');self.assertLessEqual(int(iface.split('-')[1]),56 if model=='ixr-d2' else 32)
    def test_ibgp_complete_symmetric_eight_node_graph(self):
        graph={}
        for p in (ROOT/'configs').glob('*.cfg'):
            s=p.read_text();lo=re.search(r'interface system0 subinterface 0 ipv4 address (\S+)/32',s).group(1)
            graph[lo]=set(re.findall(r'protocols bgp neighbor (\S+) peer-group IBGP',s))
        s=(ROOT/'configs/bhm-bng-01/frr.conf').read_text();graph['10.255.0.24']=set(re.findall(r'neighbor (10\.255\.\S+) peer-group KESTREL',s))
        self.assertEqual(len(graph),8)
        for node,peers in graph.items():self.assertEqual(peers,set(graph)-{node})
        self.assertEqual(sum(map(len,graph.values())),56)
    def test_bound_files_exist(self):
        d=yaml.safe_load((ROOT/'kestrel.clab.yml').read_text())
        for spec in d['topology']['nodes'].values():
            for mount in spec.get('binds',[]):self.assertTrue((ROOT/mount.split(':')[0]).is_file())
            if 'startup-config' in spec:self.assertTrue((ROOT/spec['startup-config']).is_file())
    def test_all_external_policies_attached(self):
        for node,asn in [('lon-pr-01',64496),('lon-pr-01',64498),('man-pr-01',64497),('lon-pe-01',64501)]:
            s=(ROOT/'configs'/f'{node}.cfg').read_text();self.assertIn(f'group FROM-{asn} import-policy [ FROM-{asn} ]',s)
            self.assertIn(f'group FROM-{asn} export-policy [ TO-'+('CUSTOMER' if asn==64501 else 'UPSTREAM')+' ]',s)
    def test_customer_eligibility_and_more_specific_rejection(self):
        s=(ROOT/'configs/lon-pe-01.cfg').read_text()
        self.assertEqual(evaluate(s,'FROM-64501','203.0.113.0/24','64501')[0],'accept')
        for p,path in [('10.0.0.0/8','64501'),('203.0.113.0/25','64501'),('0.0.0.0/0','64501'),('203.0.113.0/24','64498'),('203.0.113.0/24','64501 64502')]:self.assertEqual(evaluate(s,'FROM-64501',p,path)[0],'reject')
    def test_forged_provenance_removed_well_known_preserved(self):
        s=(ROOT/'configs/lon-pr-01.cfg').read_text();r,c,lp=evaluate(s,'FROM-64498','198.51.100.128/25','64498',['64500:1000','64500:3000','no-export'])
        self.assertEqual(r,'accept');self.assertEqual(c,{'64500:2000','no-export'});self.assertEqual(lp,150)
        self.assertEqual(evaluate(s,'TO-UPSTREAM','198.51.100.128/25','64498',c)[0],'reject')
    def test_external_exports_are_customer_only(self):
        s=(ROOT/'configs/lon-pr-01.cfg').read_text()
        self.assertEqual(evaluate(s,'TO-UPSTREAM','203.0.113.0/24','64501',['64500:1000'])[0],'accept')
        for p in ['0.0.0.0/0','10.255.0.11/32','100.64.0.0/24','198.18.0.0/17','198.19.128.0/17','198.51.100.128/25','203.0.113.0/25']:
            self.assertEqual(evaluate(s,'TO-UPSTREAM',p,'64501',['64500:1000'])[0],'reject')
        self.assertEqual(evaluate(s,'TO-UPSTREAM','203.0.113.0/24','64501',[])[0],'reject')
    def test_synthetic_origins_use_reserved_ranges(self):
        allowed=[ipaddress.ip_network(s) for s in ['0.0.0.0/0','198.18.0.0/15','198.51.100.0/24','203.0.113.0/24','10.0.0.0/8','100.64.0.0/10']]
        for p in (ROOT/'configs').glob('*/frr.conf'):
            for n in re.findall(r'^\s+network (\S+)',p.read_text(),re.M):
                net=ipaddress.ip_network(n);self.assertTrue(net==allowed[0] or any(net.subnet_of(a) for a in allowed[1:]))

if __name__=='__main__':unittest.main(verbosity=2)
