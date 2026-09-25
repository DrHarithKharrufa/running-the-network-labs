import unittest
from rag_grounding import check_citation,grounded,PASSAGES
from citation_cases import CASES,run
class Tests(unittest.TestCase):
 def test_negation_not_certified(self):
  self.assertFalse(grounded('The edge BGP session to AS64500 does not use TCP-AO.',['P1'])[0])
 def test_exact_is_not_truth(self):
  self.assertEqual(check_citation(PASSAGES['P1'],['P1'],PASSAGES['P1'])['status'],'needs_semantic_review')
 def test_unknown(self): self.assertEqual(check_citation('x',['bad'])['status'],'unknown_citation')
 def test_missing(self): self.assertEqual(check_citation('x',[])['status'],'missing_or_invalid_citation')
 def test_fabricated_quote(self): self.assertEqual(check_citation('x',['P1'],'does not use')['status'],'quotation_mismatch')
 def test_wrong_target_number_device_release_and_qualification_not_certified(self):
  for case in CASES:
   if case['id'] in {'wrong_target','wrong_number','wrong_device','wrong_release','missing_qualification','hypothesis_as_cause'}:
    with self.subTest(case=case['id']):
     self.assertEqual(check_citation(case['claim'],case['cited'])['status'],'needs_semantic_review')
     self.assertFalse(grounded(case['claim'],case['cited'])[0])
 def test_conflict_not_resolved_by_citation_count(self):
  self.assertEqual(check_citation('Tuesday definitely',['P3','P8'])['status'],'needs_semantic_review')
 def test_derived_claim_requires_review_even_with_inputs(self):
  self.assertEqual(check_citation('20 Gbit/s',['P6'])['status'],'needs_semantic_review')
 def test_invalid_claim_types(self):
  for claim in ['', '  ',None,[],42]:self.assertEqual(check_citation(claim,['P1'])['status'],'invalid')
 def test_invalid_citation_types(self):
  for cited in [None,'P1',('P1',),[1],[]]:self.assertEqual(check_citation('x',cited)['status'],'missing_or_invalid_citation')
 def test_invalid_quotes(self):
  for quote in ['',[],42]:self.assertEqual(check_citation('x',['P1'],quote)['status'],'quotation_mismatch')
 def test_corpus_labels_are_annotations_and_hashes_bind_passages(self):
  import hashlib
  report=run();self.assertEqual(len(report['cases']),12)
  self.assertEqual(report['passage_sha256']['P1'],hashlib.sha256(PASSAGES['P1'].encode()).hexdigest())
  for case in report['cases']:
   self.assertNotEqual(case['observed_integrity']['status'],case['expected_support'])
   self.assertTrue(case['reason'])
 def test_no_case_returns_semantic_success(self):
  allowed={'needs_semantic_review','quotation_mismatch','unknown_citation'}
  self.assertTrue(all(case['observed_integrity']['status'] in allowed for case in run()['cases']))
if __name__=='__main__': unittest.main(verbosity=2)
