"""Boundaries and counterexamples for the offline model; no network execution."""
import importlib.util
import ipaddress
import json
import tempfile
from pathlib import Path

spec=importlib.util.spec_from_file_location('rov_model',Path(__file__).with_name('validate.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def check(name,condition):
    checks.append({'name':name,'passed':bool(condition)})
    assert condition,name
def reject(name,fn):
    try:fn()
    except (ValueError,KeyError):check(name,True)
    else:check(name,False)
def records(rows):return [(ipaddress.ip_network(p),length,a) for p,length,a in rows]
strict=records([('203.0.113.0/24',24,64501)])
broad=records([('203.0.113.0/24',32,64501)])
for name,prefix,origin,vrps,expected in [
    ('exact','203.0.113.0/24',64501,strict,'valid'),
    ('wrong origin','203.0.113.0/24',64502,strict,'invalid'),
    ('strict length','203.0.113.128/25',64501,strict,'invalid'),
    ('unknown','198.51.100.0/24',64502,strict,'not-found'),
    ('broad authorisation','203.0.113.128/25',64501,broad,'valid'),
    ('one match overrides nonmatches','203.0.113.128/25',64501,broad+records([('203.0.113.128/25',25,64502)])+strict,'valid'),
    ('AS0 cannot match real origin','203.0.113.0/24',64501,records([('203.0.113.0/24',24,0)]),'invalid'),
    ('other valid record with AS0','203.0.113.0/24',64501,strict+records([('203.0.113.0/24',24,0)]),'valid'),
    ('IPv6 exact','2001:db8:3400::/48',64501,records([('2001:db8:3400::/48',48,64501)]),'valid'),
    ('IPv6 too long','2001:db8:3400::/64',64501,records([('2001:db8:3400::/48',48,64501)]),'invalid'),
    ('address families independent','2001:db8::/32',64501,strict,'not-found'),
    ('empty data','203.0.113.0/24',64501,[],'not-found')]:
    check(name,m.validate(prefix,origin,vrps)[0]==expected)
check('all covering records retained',len(m.validate('203.0.113.128/25',64501,broad+strict)[2])==2)
check('rightmost plain sequence origin',m.origin_from_text('64502 64501')==64501)
check('asdot input',m.origin_from_text('64502 1.10')==65546)
check('empty path uses local AS',m.origin_from_text('',64500)==64500)
check('optional AS prefix',m.asn('AS64501')==64501)
for name,path in [('missing',None),('AS_SET','64502 {64501,64503}'),('confederation','(64502 64503) 64501'),('empty without local',''),('invalid text','64502 nope'),('bad asdot','65536.0')]:
    reject(name,lambda path=path:m.origin_from_text(path))
for value in [0,-1,4294967296,True,1.5]:
    reject('invalid origin '+str(value),lambda value=value:m.validate('203.0.113.0/24',value,strict))
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp);vrp=tmp/'vrps.json';bgp=tmp/'bgp.json'
    for name,rows in [('max too short',[['203.0.113.0/24',23,64501]]),('max too long',[['203.0.113.0/24',33,64501]]),('max string',[['203.0.113.0/24','24',64501]]),('host bits',[['203.0.113.1/24',24,64501]]),('bad tuple',[['203.0.113.0/24',24]]),('invalid VRP ASN',[['203.0.113.0/24',24,4294967296]])]:
        vrp.write_text(json.dumps({'records':rows}));reject(name,lambda:m.load_vrps(vrp))
    vrp.write_text(json.dumps({'records':[['203.0.113.0/24',24,64501]]}))
    bgp.write_text(json.dumps({'routes':{'203.0.113.0/24':[{'path':'64501'},{'path':''},{'path':'{64501,64502}'}]}}))
    report=m.report(vrp,bgp,64501)
    check('report counts empty and unsupported separately',report['counts']=={'valid':2,'invalid':0,'not-found':0,'unsupported':1})
    check('unsupported path explains scope','unsupported' in report['paths'][2]['reason'])
subnets=list(ipaddress.ip_network('2001:db8:3400::/46').subnets(new_prefix=48))
check('checkpoint exactly four /48s',[str(n) for n in subnets]==['2001:db8:3400::/48','2001:db8:3401::/48','2001:db8:3402::/48','2001:db8:3403::/48'])
print(json.dumps({'scope':__doc__,'passed':sum(x['passed'] for x in checks),'checks':checks},indent=2))
