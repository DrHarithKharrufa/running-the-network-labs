#!/usr/bin/env python3
"""Offline capacity scenarios, not measured congestion or a funding decision.

The retained entry point models two equal-rate parallel paths with aligned,
equal-duration samples. It assumes all demand can transfer to either survivor.
Planning uses the maximum observed hourly average; p95 is descriptive only.
Use --demo-original to reproduce the preserved, flawed historical programme.
"""
import argparse
import json
import math
from pathlib import Path
import runpy

CAPACITY_G = 100.0
IN_SERVICE_LIMIT_PCT = 70.0  # Illustrative acceptance limit, NOT an order trigger.
GROWTH_PER_YEAR = 0.25
HOURLY_G = [18,15,14,14,16,22,35,46,52,55,54,56,58,57,55,58,63,71,78,80,77,66,44,28]


def number(value, *, minimum=0, strict=False):
    if type(value) not in (int,float) or not math.isfinite(value):
        raise ValueError('Expected a finite number, not a boolean')
    if value < minimum or (strict and value == minimum):
        raise ValueError('Number outside permitted domain')
    return value


def samples(values):
    result=list(values)
    if not result:
        raise ValueError('Empty samples cannot establish capacity')
    for value in result:number(value)
    return result


def pct(values,p):
    """Linear interpolation at rank (n-1)*p/100; all samples equally weighted."""
    ordered=sorted(samples(values));number(p)
    if p>100:raise ValueError('Percentile must be in [0,100]')
    rank=(len(ordered)-1)*p/100
    low,high=math.floor(rank),math.ceil(rank)
    return ordered[low]+(ordered[high]-ordered[low])*(rank-low)


def combine_aligned(left,right):
    left,right=samples(left),samples(right)
    if len(left)!=len(right):raise ValueError('Aligned series must have equal length')
    return [a+b for a,b in zip(left,right)]


def years_to_reach(start_pct,target_pct,g):
    """None means no crossing under this fixed compound scenario, not certainty."""
    number(start_pct);number(target_pct,strict=True);number(g,minimum=-1,strict=True)
    if start_pct>=target_pct:return 0.0
    if start_pct==0 or g<=0:return None
    return math.log(target_pct/start_pct)/math.log1p(g)


def deadline(start,limit,growth,lead_years):
    number(lead_years)
    crossing=years_to_reach(start,limit,growth)
    order=None if crossing is None else crossing-lead_years
    if start>=limit:
        status='LIMIT_REACHED';reason='Current model load is at or above the in-service limit; assess interim relief now.'
    elif order is not None and order<=0:
        status='ACT_NOW';reason='The forecast limit is within the delivery schedule; assess accelerated delivery or interim relief.'
    elif order is None:
        status='NO_CROSSING_IN_MODEL';reason='This fixed growth scenario does not reach the limit; recheck demand and assumptions.'
    else:
        status='PLAN_BY_DATE';reason='Begin the delivery schedule by the calculated deadline, subject to uncertainty.'
    return {'status':status,'start':start,'limit':limit,'growth_per_year':growth,'lead_years':lead_years,
            'limit_in_years':crossing,'begin_in_years':order,'reason':reason}


def critical_path(tasks):
    """tasks maps name to (non-negative months, predecessor names)."""
    if not tasks:raise ValueError('Empty schedule')
    active=set();finished={}
    def finish(task):
        if task not in tasks:raise ValueError('Unknown predecessor: '+task)
        if task in active:raise ValueError('Cyclic schedule')
        if task not in finished:
            active.add(task)
            duration,predecessors=tasks[task];number(duration)
            finished[task]=duration+max((finish(p) for p in predecessors),default=0)
            active.remove(task)
        return finished[task]
    for task in tasks:finish(task)
    return {'months':max(finished.values()),'finish_months':finished}


def pair_scenarios(left,right,capacity,limit_pct,growth,lead_years, *, include_double_failure=False):
    number(capacity,strict=True);number(limit_pct,strict=True)
    if limit_pct>100:raise ValueError('In-service utilisation limit cannot exceed 100% here')
    left,right=samples(left),samples(right)
    combined=combine_aligned(left,right)
    limit=capacity*limit_pct/100
    # Explicit topology assumption: each workload can use either complete path.
    loads={'healthy_A':max(left),'healthy_B':max(right),'A_failed_B_survives':max(combined),'B_failed_A_survives':max(combined)}
    result={key:deadline(load,limit,growth,lead_years) for key,load in loads.items()}
    if include_double_failure:
        result['both_failed']={'status':'NO_PATH','reason':'Neither path exists; more bandwidth on either failed path does not restore connectivity.'}
    return result


def examples():
    tasks={'approval':(1,()),'design':(1,('approval',)),
           'delivery':(3,('design',)),'permit':(2,('design',)),
           'installation':(1,('delivery','permit')),'acceptance':(1,('installation',))}
    schedule=critical_path(tasks)
    contingency=1
    left=[80]*5+[20]*95
    right=[20]*5+[80]*5+[20]*90
    legacy_p95=pct(HOURLY_G,95)
    return {'scope':'Synthetic offline calculations; no queue, router, forwarding or performance measurement',
      'sampling':'24 hourly averages for one synthetic day, in Gbit/s',
      'one_day':{'mean':sum(HOURLY_G)/len(HOURLY_G),'p95':legacy_p95,'maximum_hourly_average':max(HOURLY_G)},
      'historical_reason_check':deadline(legacy_p95,100,0.25,0.5),
      'noncoincident_peaks':{'p95_A':pct(left,95),'p95_B':pct(right,95),'sum_of_p95':pct(left,95)+pct(right,95),'p95_of_sum':pct(combine_aligned(left,right),95),'maximum_sum':max(combine_aligned(left,right))},
      'hidden_sustained_tail':{'sample_minutes':1,'period_minutes':100,'high_run_minutes':4,'p95':pct([40]*96+[120]*4,95),'maximum_offered_load':120},
      'doubling_at_24_percent_years':years_to_reach(1,2,0.24),
      'schedule':{**schedule,'contingency_months':contingency,'total_months':schedule['months']+contingency},
      'original_demands_with_new_policy':pair_scenarios(HOURLY_G,HOURLY_G,100,70,0.25,(schedule['months']+contingency)/12,include_double_failure=True),
      'lower_load_planning_case':pair_scenarios([20]*24,[20]*24,100,70,0.25,(schedule['months']+contingency)/12),
      'exercise_45_to_70':deadline(45,70,0.20,0.5)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo-original',action='store_true')
    args=parser.parse_args()
    if args.demo_original:
        print('HISTORICAL DEMONSTRATION: the following output is intentionally flawed.')
        runpy.run_path(str(Path(__file__).with_name('original_capacity_case.py')),run_name='__main__')
        print('CORRECTIONS: these are 24 hourly averages, not a week or a busy-hour distribution.')
        print('A percentile cannot prove loss or latency. The old no-slack reason is false:')
        print(json.dumps(examples()['historical_reason_check'],indent=2,allow_nan=False))
        return
    print(json.dumps(examples(),indent=2,allow_nan=False))


if __name__=='__main__':main()
