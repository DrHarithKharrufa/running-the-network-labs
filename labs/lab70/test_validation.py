import unittest
from validate_against_model import validate
class Tests(unittest.TestCase):
 def test_valid(self):
  self.assertEqual(validate({'name':'Ethernet1','mode':'access','vlan':30,'enabled':False}),[])
 def test_types(self):
  for obj in [None,[],{'name':4,'mode':'routed'}, {'name':'x','mode':'routed','enabled':'false'},
              {'name':'x','mode':'routed','mtu':True},{'name':'x','mode':[]}]:
   with self.subTest(obj=obj): self.assertTrue(validate(obj))
 def test_conditional(self):
  for obj in [{'name':'x','mode':'access'},{'name':'x','mode':'routed','vlan':1}]:
   self.assertTrue(validate(obj))
 def test_bounds_and_unknown(self):
  for mtu in [67,9217,-1,1.0]: self.assertTrue(validate({'name':'x','mode':'routed','mtu':mtu}))
  for mtu in [68,9216]: self.assertEqual(validate({'name':'x','mode':'routed','mtu':mtu}),[])
  self.assertTrue(validate({'name':'x','mode':'routed','password':'x'}))
if __name__=='__main__': unittest.main(verbosity=2)
