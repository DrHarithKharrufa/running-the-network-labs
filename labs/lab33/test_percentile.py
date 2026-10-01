"""Boundary/counterfactual checks for the lab33 billing calculation."""
import importlib.util
from pathlib import Path
from decimal import Decimal as D
from datetime import datetime,timedelta
import tempfile
import argparse
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('billing',root/'percentile.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cases=[]
def check(name,actual,expected):
    assert actual==expected,(name,actual,expected)
    cases.append(name)
check('one sample',m.p95([D(7)]),D(7))
check('20 samples discard the largest',m.p95(list(map(D,range(1,21)))),D(19))
check('21 samples use ceiling rank',m.p95(list(map(D,range(1,22)))),D(20))
check('constant rate has no higher samples',m.p95([D(7)]*20),D(7))
for value in [[],[D(-1)],[D('NaN')],[D('Infinity')]]:
    try:m.p95(value)
    except ValueError:cases.append('reject invalid percentile input '+str(value))
    else:raise AssertionError(value)
# Separate one-interval peaks are each discarded, but their sum has two peaks.
a=[D(100)]+[D(0)]*19;b=[D(0),D(100)]+[D(0)]*18
check('non-additive percentile counterexample',m.p95([x+y for x,y in zip(a,b)]),D(100))
check('sum of standalone percentiles differs',m.p95(a)+m.p95(b),D(0))
# A short extra event can displace a different discarded peak into the billed set.
check('one-interval event can raise billing',m.p95([D(1000),D(100)]+[D(10)]*18),D(100))
check('baseline billed level',m.p95([D(1000)]+[D(10)]*19),D(10))
# Direction aggregation is a contract operation, not a interchangeable summary.
check('separate direction percentile maximum',max(m.p95(a),m.p95(b)),D(0))
check('per-interval direction maximum percentile',m.p95([max(x,y) for x,y in zip(a,b)]),D(100))
inbound=[D(100)]*10+[D(0)]*10;outbound=inbound[::-1]
check('maximum directional percentiles',max(m.p95(inbound),m.p95(outbound)),D(100))
check('sum of directional percentiles',m.p95(inbound)+m.p95(outbound),D(200))
check('below commit still pays commit',m.charge(D(50),D(100),D('.06'),D('.08')),D(6))
check('above commit uses burst rate',m.charge(D(150),D(100),D('.06'),D('.08')),D(10))
rows=[{'timestamp':datetime(2026,6,1)+timedelta(minutes=5*i),'transit_a_mbps':D(10),'transit_b_mbps':D(20),'ix_mbps':D(8)} for i in range(20)]
s=m.scenarios(rows)
check('no-IX redistributes each interval to A',s[1][1]['transit_a_mbps'][0],D(14))
check('no-IX conserves total offered traffic',sum(s[1][1][k][0] for k in m.COLUMNS),D(38))
check('cache scales transit only',s[2][1]['ix_mbps'][0],D(8))
check('outage reroutes B to A',s[3][1]['transit_a_mbps'][0],D(30))
result=m.analyse(rows,capacity_a=D(25))
check('overloaded failover flagged',result['results'][3]['capacity_feasible'],False)
tiny=[{**row,'transit_a_mbps':D(1),'transit_b_mbps':D(1),'ix_mbps':D(0)} for row in rows]
rounded=m.analyse(tiny,price=D('.005'),burst_price=D('.005'),ix_cost=D(0))['results'][0]
check('round individual charge lines before sum',rounded['monthly_total_gbp'],'0.02')
check('displayed lines reconcile to total',D(rounded['transit_a_gbp'])+D(rounded['transit_b_gbp'])+D(rounded['exchange_gbp']),D(rounded['monthly_total_gbp']))
for name,call in [('NaN charge',lambda:m.charge(D('NaN'),D(0),D(0),D(0))),('NaN split',lambda:m.scenarios(rows,ix_split=D('NaN'))),('negative IX charge',lambda:m.analyse(rows,ix_cost=D(-1))),('NaN capacity',lambda:m.analyse(rows,capacity_a=D('NaN')))]:
    try:call()
    except ValueError:cases.append('reject '+name)
    else:raise AssertionError(name)
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'bad.csv'
    p.write_text('timestamp,transit_a_mbps,transit_b_mbps,ix_mbps\n2026-06-01 00:00,1,2,3\n2026-06-01 00:10,1,2,3\n')
    try:m.read_samples(p,allow_partial=True)
    except ValueError:cases.append('missing interval rejected')
    else:raise AssertionError('Missing interval accepted')
    header='timestamp,transit_a_mbps,transit_b_mbps,ix_mbps\n'
    for name,body in [
        ('extra field','2026-06-01 00:00,1,2,3,4\n'),
        ('missing field','2026-06-01 00:00,1,2\n'),
        ('empty rate','2026-06-01 00:00,1,,3\n'),
        ('NaN rate','2026-06-01 00:00,1,NaN,3\n'),
        ('negative rate','2026-06-01 00:00,1,-2,3\n'),
        ('duplicate timestamp','2026-06-01 00:00,1,2,3\n2026-06-01 00:00,1,2,3\n'),
        ('unaligned timestamp','2026-06-01 00:01,1,2,3\n'),
        ('timezone suffix','2026-06-01 00:00+01:00,1,2,3\n')]:
        p.write_text(header+body)
        try:m.read_samples(p,allow_partial=True)
        except ValueError:cases.append('reject CSV '+name)
        else:raise AssertionError(name)
    p.write_text(header+'2026-06-01 00:00,1,2,3\n')
    try:m.read_samples(p)
    except ValueError:cases.append('reject incomplete calendar month')
    else:raise AssertionError('Partial month accepted as complete')
    check('explicit partial experiment',len(m.read_samples(p,allow_partial=True)),1)
import json
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=root/'test-results.json');out=parser.parse_args().output
out.write_text(json.dumps({'passed':len(cases),'cases':cases},indent=2)+'\n',encoding='utf8')
print(f'{len(cases)} billing boundary and scenario checks passed.')
