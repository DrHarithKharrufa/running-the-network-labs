"""Adapter contract tests with doubles; no Batfish service is called."""
import unittest
from batfish_probe import collect

class Frame:
    def __init__(self,rows=(),nodes=()):self.rows=rows;self.nodes=nodes
    def __len__(self):return len(self.rows)
    def __getitem__(self,key):
        if key!='Node':raise KeyError(key)
        return self.nodes
    def to_string(self,index=False):return str(self.rows)
class Question:
    def __init__(self,frame):self.data=frame
    def answer(self):return self
    def frame(self):return self.data
class Queries:
    def __init__(self):self.trace_args=None;self.trace_frame=Frame(['DENIED_IN'])
    def fileParseStatus(self):return Question(Frame(['PARTIALLY_UNRECOGNIZED']))
    def initIssues(self):return Question(Frame(['unsupported command']))
    def nodeProperties(self):return Question(Frame(['r1'],['r1']))
    def traceroute(self,**kw):self.trace_args=kw;return Question(self.trace_frame)
class Session:
    def __init__(self):self.q=Queries();self.snapshot=None;self.network=None
    def list_networks(self):return ['existing']
    def set_snapshot(self,name):self.snapshot=name
    def get_component_versions(self):return {'test-double':'no server'}
def probe(session,network='existing'):
    return collect(session,lambda **kw:kw,network,'candidate','@enter(r1[eth0])',
                   '192.0.2.1','198.51.100.1',50000,443,['r1','r2'])
class Tests(unittest.TestCase):
    def test_missing_network_not_created(self):
        s=Session()
        with self.assertRaises(ValueError):probe(s,'absent')
        self.assertIsNone(s.network)
    def test_explicit_flow_and_filters(self):
        s=Session();probe(s);args=s.q.trace_args
        self.assertFalse(args['ignoreFilters']);self.assertEqual(args['headers']['ipProtocols'],['TCP'])
        self.assertEqual(args['headers']['srcPorts'],'50000');self.assertEqual(args['headers']['dstPorts'],'443')
    def test_missing_node_and_warnings_retained(self):
        r=probe(Session());self.assertEqual(r['missing_nodes'],['r2'])
        self.assertIn('PARTIALLY_UNRECOGNIZED',r['evidence_tables']['file_parse_status'])
        self.assertIn('unsupported command',r['evidence_tables']['initialisation_issues'])
        self.assertEqual(r['status'],'REVIEW_REQUIRED')
    def test_empty_trace_not_converted_to_pass(self):
        s=Session();s.q.trace_frame=Frame();r=probe(s)
        self.assertEqual(r['row_counts']['traceroute'],0);self.assertEqual(r['status'],'REVIEW_REQUIRED')

if __name__=='__main__':unittest.main(verbosity=2)
