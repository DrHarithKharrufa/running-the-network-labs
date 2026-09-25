"""Local structure and call-boundary tests; no GNS3 server or NOS execution."""
from pathlib import Path
import contextlib,copy,io,json,tempfile,unittest
from unittest.mock import patch
import gns3_build as g

class Preflight(unittest.TestCase):
    def setUp(self):
        self.nodes={'a':{'kind':'linux'},'b':{'kind':'linux'}}
        self.links=[(('a','eth1'),('b','eth1'))]
        self.mapping={'kinds':{'linux':{'template':'fixture','scheme':'adapter','offset':1}}}
    def plan(self,links=None,mapping=None):return g.plan_wiring(self.nodes,self.links if links is None else links,self.mapping if mapping is None else mapping)
    def test_valid_scheme(self):self.assertEqual(self.plan()[1],[ [('a',1,0),('b',1,0)] ])
    def test_explicit_breakout(self):
        self.mapping['nodes']={'a':{'template':'fixture','port_map':{'e1-3-2':[5,0]}}}
        self.assertEqual(self.plan([(('a','e1-3-2'),('b','eth1'))])[1][0][0],('a',5,0))
    def test_breakout_not_inferred(self):
        with self.assertRaises(ValueError):self.plan([(('a','e1-3-2'),('b','eth1'))])
    def test_unknown_node(self):
        with self.assertRaises(ValueError):self.plan([(('a','eth1'),('x','eth1'))])
    def test_reused_endpoint(self):
        with self.assertRaises(ValueError):self.plan(self.links*2)
    def test_target_collision(self):
        self.mapping['nodes']={'a':{'template':'fixture','port_map':{'eth1':[0,0],'eth2':[0,0]}}}
        with self.assertRaises(ValueError):self.plan(self.links+[(('a','eth2'),('b','eth2'))])
    def test_missing_template(self):
        with self.assertRaises(ValueError):self.plan(mapping={})
    def test_invalid_mapping_numbers(self):
        for value in [-1,True,1.5,'1']:
            with self.subTest(value=value),self.assertRaises(ValueError):g.resolve_port('eth1',{'offset':value})
    def test_invalid_scheme(self):
        with self.assertRaises(ValueError):g.resolve_port('eth1',{'scheme':'adaptr'})
    def test_self_link(self):
        with self.assertRaises(ValueError):self.plan([(('a','eth1'),('a','eth2'))])
    def test_incomplete_explicit_map(self):
        with self.assertRaises(ValueError):g.resolve_port('eth2',{'port_map':{'eth1':[0,0]}})
    def test_bad_explicit_pair(self):
        for pair in [[0],[-1,0],[True,0],[0,'0']]:
            with self.subTest(pair=pair),self.assertRaises(ValueError):g.resolve_port('eth1',{'port_map':{'eth1':pair}})
    def test_inventory_counts_and_unique_ports(self):
        root=Path(__file__).resolve().parents[1]/'topologies'
        for name,nodes,links in [('aldergate',12,14),('kestrel',14,14),('anvil',10,12)]:
            _,ns,ls=g.load_topology(root/f'{name}.clab.yml')
            mp={'kinds':{kind:{'template':'fixture','scheme':'adapter'} for kind in {v['kind'] for v in ns.values()}}}
            self.assertEqual((len(ns),len(ls)),(nodes,links));g.plan_wiring(ns,ls,mp)
    def test_dry_ids_deterministic_without_requests(self):
        with patch.object(g.urllib.request,'urlopen',side_effect=AssertionError('network forbidden')),contextlib.redirect_stdout(io.StringIO()):
            client=g.GNS3('http://localhost:3080',dry_run=True)
            self.assertEqual(client.add_node('p','t','a',0,0),client.add_node('p','t','a',0,0))
    def test_invalid_plan_makes_no_api_calls(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);top=root/'top.json';mp=root/'map.json'
            top.write_text(json.dumps({'topology':{'nodes':self.nodes,'links':[{'endpoints':['a:eth1','missing:eth1']}]}}));mp.write_text(json.dumps(self.mapping))
            with patch('sys.argv',['gns3_build.py','-t',str(top),'-m',str(mp)]),patch.object(g.GNS3,'_call',side_effect=AssertionError('API forbidden')),self.assertRaises(ValueError):g.main()
    def test_defaults_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'t.json';p.write_text(json.dumps({'topology':{'defaults':{'kind':'linux'},'nodes':self.nodes}}))
            with self.assertRaises(ValueError):g.load_topology(p)
    def test_duplicate_template_names_rejected(self):
        with patch.object(g.GNS3,'_call',return_value=[{'name':'x'},{'name':'x'}]),self.assertRaises(ValueError):g.GNS3('http://localhost').templates()

if __name__=='__main__':unittest.main()
