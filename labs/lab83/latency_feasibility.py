#!/usr/bin/env python3
"""Explicit hypothetical workload budgets, not application or replication tests."""
import argparse
import json
import math
from pathlib import Path
import runpy


def nonnegative(value, name):
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise ValueError(name+' must be finite and nonnegative')
    try:
        valid=math.isfinite(value) and value >= 0
    except OverflowError:
        valid=False
    if not valid:raise ValueError(name+' must be finite and nonnegative')
    return float(value)


def finite_result(value):
    if not math.isfinite(value):raise ValueError('result exceeds floating-point range')
    return value


def rtt_ms(route_km, speed_km_s=200000, additional_rtt_ms=0):
    route=nonnegative(route_km,'route length');speed=nonnegative(speed_km_s,'speed')
    additional=nonnegative(additional_rtt_ms,'additional RTT')
    if not 0 < speed <= 299792.458:raise ValueError('speed must be positive and no greater than c')
    propagation=finite_result(route/speed*2000)
    return {'propagation_rtt_ms':propagation,'assumed_total_rtt_ms':finite_result(propagation+additional)}


def transaction(name, rtt, sequential_rounds, local_ms, budget_ms):
    if not isinstance(name,str) or not name.strip():raise ValueError('named workload required')
    rtt=nonnegative(rtt,'RTT');local=nonnegative(local_ms,'local time');budget=nonnegative(budget_ms,'budget')
    if type(sequential_rounds) is not int or not 0 <= sequential_rounds <= 1000:
        raise ValueError('rounds must be integer 0..1000 (worksheet bound)')
    elapsed=finite_result(sequential_rounds*rtt+local)
    return {'workload':name,'assumed_latency_ms':elapsed,'budget_ms':budget,
            'within_assumed_budget':elapsed <= budget,
            'scope':'Deterministic teaching budget, not a percentile, quorum implementation or application benchmark.'}


def replication(write_mib_s, apply_mib_s, outage_s, rpo_s=300):
    write,apply,outage,rpo=[nonnegative(v,n) for v,n in ((write_mib_s,'write rate'),(apply_mib_s,'effective apply rate'),(outage_s,'outage'),(rpo_s,'RPO'))]
    backlog=finite_result(write*outage)
    catchup=0.0 if backlog==0 else finite_result(backlog/(apply-write)) if apply>write else None
    # Writes are constant, replica initially current, FIFO durable apply, no compression.
    # lag is the span of acknowledged writes absent at the replica, not measured age.
    loss_span=outage if write>0 else 0.0
    return {'backlog_MiB':backlog,'catchup_s':catchup,'unreplicated_write_span_s':loss_span,
            'within_loss_window_budget':loss_span <= rpo,
            'scope':'Constant-rate analytical loss window; real RPO requires recovered commit IDs/timestamps and failure-boundary evidence.'}


def recovery(stages, objective_s=1800):
    if not isinstance(stages,dict) or not stages or any(not isinstance(k,str) or not k for k in stages):
        raise ValueError('named sequential stages required')
    values=[nonnegative(v,k) for k,v in stages.items()]
    try:total=math.fsum(values)
    except OverflowError:raise ValueError('recovery total overflow') from None
    objective=nonnegative(objective_s,'RTO')
    finite_result(total)
    return {'stages_s':stages,'assumed_total_s':total,'margin_s':objective-total,
            'within_budget':total <= objective,'measured_RTO':'NOT_RUN'}


def worksheet():
    path=rtt_ms(1100,additional_rtt_ms=3)
    return {'scope':'Local arithmetic only; no WAN, cloud, database, BGP, DNS, EVPN or DR execution.',
            'geographic_800km_ideal_rtt':rtt_ms(800),
            'assumed_route_1100km_plus_3ms':path,
            'workloads':[transaction('Aldergate one-round durable commit',14,1,8,40),
                         transaction('Aldergate two-round variant',14,2,8,40),
                         transaction('Aldergate three-round variant',14,3,8,40),
                         transaction('Intercontinental one-round reporting commit',rtt_ms(8000,additional_rtt_ms=20)['assumed_total_rtt_ms'],1,10,200)],
            'async_four_minute_link_outage':replication(8,12,240),
            'async_six_minute_link_outage':replication(8,12,360),
            'recovery_budget':recovery({'detect':60,'fence_old_writer':120,'promote_and_recover':300,'steer_clients':180,'validate_service_and_data':300})}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo-original',action='store_true',help='show preserved flawed threshold model')
    args=parser.parse_args()
    if args.demo_original:
        print('HISTORICAL FLAWED MODEL: universal application limits below are superseded.')
        runpy.run_path(str(Path(__file__).with_name('latency_feasibility_original.py.txt')),run_name='__main__')
    else:print(json.dumps(worksheet(),indent=2))
