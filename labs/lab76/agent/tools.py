"""Offline proposal types. No function here can configure a device."""
from dataclasses import dataclass,field
from typing import Any
@dataclass
class Action:
 tool:str
 params:dict[str,Any]
 targets:list[str]=field(default_factory=list)
 ticket:str|None=None
 evidence:list[str]=field(default_factory=list)
 provenance:list[str]=field(default_factory=list) # Untrusted planner claim; not authority.
 request_id:str=''
 approval_id:str|None=None
 state_revision:int=0
 requester:str='noc-operator' # Claim checked against the separately supplied harness identity.
 policy_revision:int=5
@dataclass
class Verdict:
 allowed:bool
 stage:str
 reason:str
 rule:str|None=None
