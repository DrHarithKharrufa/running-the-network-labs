"""Citation integrity exercise, not semantic entailment or a truth detector."""
PASSAGES={
 'P1':'The edge BGP session to AS64500 uses TCP-AO keychain BGP-AO.',
 'P2':"On a flap, first check the interface, then 'show bgp neighbor'.",
 'P3':'Maintenance windows for the core are Tuesdays 02:00-04:00 UTC.',
 'P4':'For lab-r1 running ExampleNOS 1.2, the command was accepted by the parser. Forwarding was not tested.',
 'P5':'At 03:10 UTC the operator proposed a failed optic as a hypothesis. No cause was confirmed.',
 'P6':'The runbook records 80 Gbit/s load and 100 Gbit/s available capacity on this path.',
 'P7':'This hypothetical advisory affects ExampleNOS 1.2 through 1.4 inclusive; version 1.5 is excluded.',
 'P8':'Maintenance windows for the core are Wednesdays 02:00-04:00 UTC.'}
def check_citation(claim,cited,quotation=None):
 if type(claim) is not str or not claim.strip(): return {'status':'invalid','reason':'nonempty claim required'}
 if type(cited) is not list or not cited or any(type(p) is not str for p in cited):
  return {'status':'missing_or_invalid_citation','reason':'supply passage IDs'}
 if any(p not in PASSAGES for p in cited): return {'status':'unknown_citation','reason':'unknown passage ID'}
 if quotation is not None and (type(quotation) is not str or not quotation or
      not any(quotation in PASSAGES[p] for p in cited)):
  return {'status':'quotation_mismatch','reason':'quotation not found exactly in cited text'}
 return {'status':'needs_semantic_review','reason':'citation exists; support, scope, negation and source accuracy remain unverified'}
def grounded(claim,cited):
 """Compatibility entry point; never certifies semantic support from word overlap."""
 result=check_citation(claim,cited)
 return False,result['status']+': '+result['reason']
if __name__=='__main__':
 for claim,cited in [(PASSAGES['P1'],['P1']),
   ('The edge BGP session to AS64500 does not use TCP-AO.',['P1']),
   ('The session has BFD at50ms.',[]),('Reboot the router.',['missing'])]:
  print(claim,check_citation(claim,cited))
 print('Even an exact quotation may be stale or false. No LLM or semantic judge is executed.')
