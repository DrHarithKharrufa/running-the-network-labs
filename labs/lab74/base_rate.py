#!/usr/bin/env python3
"""Synthetic rare-event scoring; no detector is trained or evaluated on real telemetry."""
import argparse
import json
import math
from pathlib import Path
import runpy
from statistics import NormalDist

def count(value):
    if type(value) is not int or value<0:raise ValueError('counts must be non-negative integers, excluding bool')
    return value

def ratio(a,b):return a/b if b else None

def wilson(k,n,confidence=0.95):
    count(k);count(n)
    if k>n:raise ValueError('successes exceed trials')
    if type(confidence) not in (int,float) or not math.isfinite(confidence) or not 0<confidence<1:
        raise ValueError('confidence must be finite and strictly between 0 and 1')
    if n==0:return None
    p=k/n;z=NormalDist().inv_cdf((1+confidence)/2);z2=z*z;den=1+z2/n
    centre=(p+z2/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z2/(4*n*n))/den
    return [max(0.0,centre-half),min(1.0,centre+half)]

def score(tp,fp,tn,fn):
    for value in (tp,fp,tn,fn):count(value)
    total=tp+fp+tn+fn
    return {'counts':{'tp':tp,'fp':fp,'tn':tn,'fn':fn},'n':total,
            'prevalence':ratio(tp+fn,total),'accuracy':ratio(tp+tn,total),
            'precision':ratio(tp,tp+fp),'recall':ratio(tp,tp+fn),
            'false_positive_rate':ratio(fp,fp+tn),'false_discovery_fraction':ratio(fp,tp+fp),
            'precision_wilson_95':wilson(tp,tp+fp),'recall_wilson_95':wilson(tp,tp+fn),
            'interval_assumption':'Approximate binomial intervals assuming independent representative trials; not valid uncertainty for correlated operational windows or a paired model difference.'}

def precision_from_rates(prevalence,tpr,fpr):
    for v in (prevalence,tpr,fpr):
        if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1:raise ValueError('rates must be finite probabilities')
    return ratio(tpr*prevalence,tpr*prevalence+fpr*(1-prevalence))

def loss(result,miss_cost,false_alert_cost,operating_cost=0):
    for value in (miss_cost,false_alert_cost,operating_cost):
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:raise ValueError('costs must be finite and non-negative')
    return result['counts']['fn']*miss_cost+result['counts']['fp']*false_alert_cost+operating_cost

def demo():
    normal=999900
    cases={'always_negative':score(0,0,normal,100),'noisy_detector':score(90,5000,normal-5000,10),
           'seasonal_baseline':score(80,400,normal-400,20),'candidate_model':score(82,380,normal-380,18)}
    b=cases['seasonal_baseline'];m=cases['candidate_model'];avoided=loss(b,1000,1)-loss(m,1000,1)
    return {'synthetic':True,'unit':'one labelled interval, not necessarily one incident',
            'results':cases,'base_rate_identity':precision_from_rates(.0001,.9,5000/normal),
            'cost_example':{'arbitrary_units':True,'miss_cost':1000,'false_alert_cost':1,
                'gross_avoided_loss_per_million_intervals':avoided,
                'net_benefit_with_1000_extra_operating_cost':avoided-1000,
                'net_benefit_with_3000_extra_operating_cost':avoided-3000},
            'decision':'Candidate improves both point estimates. Costs and uncertainty decide value; aggregate counts cannot establish paired significance or event-level performance. No universal winner.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--counts',type=int,nargs=4,metavar=('TP','FP','TN','FN'))
    p.add_argument('--demo-original',action='store_true');a=p.parse_args()
    if a.demo_original:
        print('HISTORICAL FLAWED DEMO: synthetic counts; its prescribed baseline winner and undefined-metric handling are incorrect.')
        runpy.run_path(str(Path(__file__).with_name('original_base_rate.py')),run_name='__main__');return 0
    try:result=score(*a.counts) if a.counts is not None else demo()
    except ValueError as e:p.error(str(e))
    print(json.dumps(result,indent=2,allow_nan=False));return 0

if __name__=='__main__':raise SystemExit(main())
