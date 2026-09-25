"""Synthetic, manually adjudicated examples; expected labels are data, not judge output."""
import hashlib,json
from rag_grounding import PASSAGES,check_citation
CASES=[
 {'id':'exact','claim':PASSAGES['P1'],'cited':['P1'],'quotation':PASSAGES['P1'],
  'expected_support':'SUPPORTED_BY_TEXT','reason':'Exact source statement. Truth and freshness of the source remain unknown.'},
 {'id':'negation','claim':'The edge BGP session to AS64500 does not use TCP-AO.','cited':['P1'],
  'expected_support':'CONTRADICTED','reason':'Source explicitly says the named session uses TCP-AO.'},
 {'id':'wrong_target','claim':'The edge BGP session to AS64501 uses TCP-AO keychain BGP-AO.','cited':['P1'],
  'expected_support':'NOT_SUPPORTED','reason':'Evidence is about AS64500; it supplies no assertion about AS64501.'},
 {'id':'wrong_number','claim':'Maintenance windows for the core are Tuesdays 03:00-05:00 UTC.','cited':['P3'],
  'expected_support':'CONTRADICTED','reason':'The stated interval differs from 02:00-04:00 UTC.'},
 {'id':'missing_qualification','claim':'The lab command passed forwarding validation.','cited':['P4'],
  'expected_support':'CONTRADICTED','reason':'Only parser acceptance is reported; forwarding explicitly was not tested.'},
 {'id':'wrong_device','claim':'The command was accepted on lab-r2 running ExampleNOS 1.2.','cited':['P4'],
  'expected_support':'NOT_SUPPORTED','reason':'The source names lab-r1, not lab-r2.'},
 {'id':'wrong_release','claim':'The hypothetical advisory affects ExampleNOS 1.5.','cited':['P7'],
  'expected_support':'CONTRADICTED','reason':'Version 1.5 is explicitly excluded.'},
 {'id':'hypothesis_as_cause','claim':'A failed optic was the confirmed cause.','cited':['P5'],
  'expected_support':'CONTRADICTED','reason':'The source explicitly says no cause was confirmed; the optic was a hypothesis.'},
 {'id':'derived_calculation','claim':'Available capacity minus recorded load is 20 Gbit/s.','cited':['P6'],
  'expected_support':'DERIVATION_REQUIRED','reason':'Subtract 80 from 100 in matching units; this is capacity difference, not a safe operating limit or a current measurement.'},
 {'id':'conflicting_sources','claim':'The core maintenance window is definitely Tuesday.','cited':['P3','P8'],
  'expected_support':'CONFLICT_REQUIRES_RESOLUTION','reason':'Two synthetic sources disagree; no version precedence or owner resolution is supplied.'},
 {'id':'fabricated_quote','claim':'The session does not use TCP-AO.','cited':['P1'],'quotation':'does not use TCP-AO',
  'expected_support':'CITATION_INTEGRITY_FAILURE','reason':'The alleged exact quotation does not occur in the cited text.'},
 {'id':'absent_source','claim':'Reboot the router.','cited':['missing'],
  'expected_support':'CITATION_INTEGRITY_FAILURE','reason':'The passage ID does not exist.'},
]
def run():
 return {'synthetic':True,'fixture_version':'2026-09-24-v1',
         'adjudication':'Expected labels and reasons manually reviewed as text relationships, independently of the citation checker. No external reviewer, LLM or semantic judge is claimed.',
         'passage_sha256':{key:hashlib.sha256(value.encode()).hexdigest() for key,value in PASSAGES.items()},
         'cases':[dict(case,observed_integrity=check_citation(case['claim'],case['cited'],case.get('quotation'))) for case in CASES],
         'scope':'Structural citation/quotation integrity only. Expected support labels are fixture annotations, never computed verdicts or live-network truth.'}
if __name__=='__main__':print(json.dumps(run(),indent=2))
