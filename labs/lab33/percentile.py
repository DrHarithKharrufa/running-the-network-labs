#!/usr/bin/env python3
"""Lab 33: time-aligned counterfactual billing under an explicit toy contract.

Input columns are synthetic offered rates in Mbps in the same direction (towards
Kestrel), with only that direction billed. They are not per-link maxima of two
directions. Prices are hypothetical GBP inputs. This tool cannot infer a contract.
"""
from __future__ import annotations
import argparse
import calendar
import csv
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
import math
import hashlib
from pathlib import Path

D = Decimal
COLUMNS = ('transit_a_mbps', 'transit_b_mbps', 'ix_mbps')

def p95(values):
    if not values:
        raise ValueError('At least one sample is required')
    if any(not math.isfinite(float(x)) or x < 0 for x in values):
        raise ValueError('Rates must be finite and nonnegative')
    ordered = sorted(values)
    # Nearest rank: ceil(0.95*N), using one-based ranks and integer arithmetic.
    rank = (95 * len(ordered) + 99) // 100
    return ordered[rank - 1]

def read_samples(path, allow_partial=False):
    with Path(path).open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ['timestamp', *COLUMNS]:
            raise ValueError('Expected timestamp,transit_a_mbps,transit_b_mbps,ix_mbps')
        rows=[]
        for line, row in enumerate(reader, 2):
            if None in row or any(row.get(k) is None for k in ['timestamp',*COLUMNS]):
                raise ValueError(f'Expected exactly four fields on row {line}')
            try:
                stamp = datetime.fromisoformat(row['timestamp'])
                rates = {k:D(row[k]) for k in COLUMNS}
            except Exception as exc:
                raise ValueError(f'Invalid row {line}: {exc}') from exc
            if any(not value.is_finite() or value < 0 for value in rates.values()):
                raise ValueError(f'Invalid rate on row {line}')
            if stamp.tzinfo is not None:
                raise ValueError('This fixture uses naive timestamps explicitly interpreted as UTC')
            if stamp.second or stamp.microsecond or stamp.minute % 5:
                raise ValueError(f'Unaligned five-minute timestamp on row {line}')
            if rows and stamp - rows[-1]['timestamp'] != timedelta(minutes=5):
                raise ValueError(f'Missing, duplicate or unordered interval on row {line}')
            rows.append({'timestamp':stamp, **rates})
    if not rows:
        raise ValueError('No samples')
    first=rows[0]['timestamp']
    if not allow_partial:
        expected=calendar.monthrange(first.year,first.month)[1]*24*12
        if first.day != 1 or first.hour or first.minute or len(rows)!=expected:
            raise ValueError('Expected one complete calendar month beginning at 00:00 on day 1')
        if rows[-1]['timestamp'].month != first.month:
            raise ValueError('Samples cross the billing-month boundary')
    return rows

def charge(rate, commit, base_price, burst_price):
    if any(not x.is_finite() or x<0 for x in (rate,commit,base_price,burst_price)):
        raise ValueError('Billing values must be finite and nonnegative')
    return commit*base_price + max(D(0),rate-commit)*burst_price

def money(value):
    return str(value.quantize(D('0.01'),rounding=ROUND_HALF_UP))

def scenarios(rows, ix_split=D('0.5'), cache_fraction=D('0.15')):
    if any(not x.is_finite() or not 0<=x<=1 for x in (ix_split,cache_fraction)):
        raise ValueError('Fractions must be between zero and one')
    daily={}
    for r in rows:
        day=r['timestamp'].date()
        daily[day]=daily.get(day,D(0))+r['transit_a_mbps']+r['transit_b_mbps']
    busy=max(sorted(daily),key=daily.get)
    current={k:[r[k] for r in rows] for k in COLUMNS}
    no_ix={
        'transit_a_mbps':[r['transit_a_mbps']+r['ix_mbps']*ix_split for r in rows],
        'transit_b_mbps':[r['transit_b_mbps']+r['ix_mbps']*(1-ix_split) for r in rows],
        'ix_mbps':[D(0)]*len(rows)}
    cache={k:[v*(1-cache_fraction) if k.startswith('transit_') else v for v in values]
           for k,values in current.items()}
    outage={'transit_a_mbps':[], 'transit_b_mbps':[], 'ix_mbps':current['ix_mbps'][:]}
    for r in rows:
        failed=r['timestamp'].date()==busy
        outage['transit_a_mbps'].append(r['transit_a_mbps']+(r['transit_b_mbps'] if failed else D(0)))
        outage['transit_b_mbps'].append(D(0) if failed else r['transit_b_mbps'])
    return [('Current',current,True),('No exchange',no_ix,False),
            ('Additional cache',cache,True),(f'Transit B outage on {busy}',outage,True)]

def analyse(rows, price=D('0.06'), burst_price=D('0.06'), commit_a=D(0), commit_b=D(0),
            ix_cost=D('1200'), ix_split=D('0.5'), cache_fraction=D('0.15'),
            capacity_a=D('100000'), capacity_b=D('100000')):
    if any(not x.is_finite() or x<0 for x in (price,burst_price,commit_a,commit_b,ix_cost,capacity_a,capacity_b)):
        raise ValueError('Billing and capacity parameters must be finite and nonnegative')
    output=[]
    for name,streams,keep_ix in scenarios(rows,ix_split,cache_fraction):
        metrics={}
        for k,values in streams.items():
            level=p95(values)
            metrics[k]={'p95_mbps':str(level),'peak_mbps':str(max(values)),
                        'hours_strictly_above_p95':str(D(sum(v>level for v in values))/12)}
        a=D(metrics['transit_a_mbps']['p95_mbps'])
        b=D(metrics['transit_b_mbps']['p95_mbps'])
        cost_a=charge(a,commit_a,price,burst_price)
        cost_b=charge(b,commit_b,price,burst_price)
        circuit_cost=ix_cost if keep_ix else D(0)
        overload={k:sum(v>cap for v in streams[k]) for k,cap in
                  [('transit_a_mbps',capacity_a),('transit_b_mbps',capacity_b)]}
        # Contract assumption: round each charge first, then sum displayed lines.
        cost_a,cost_b,circuit_cost=[D(money(v)) for v in (cost_a,cost_b,circuit_cost)]
        total=cost_a+cost_b+circuit_cost
        output.append({'scenario':name,'metrics':metrics,'transit_a_gbp':money(cost_a),
                       'transit_b_gbp':money(cost_b),'exchange_gbp':money(circuit_cost),
                       'monthly_total_gbp':money(total),'over_capacity_intervals':overload,
                       'capacity_feasible':not any(overload.values())})
    baseline=D(output[0]['monthly_total_gbp'])
    for result in output:
        result['saving_vs_current_gbp']=money(baseline-D(result['monthly_total_gbp']))
    return {'scope':'Hypothetical contract and synthetic training traffic; no market quote or invoice validation.',
            'sample_count':len(rows),'start':rows[0]['timestamp'].isoformat(),
            'end':rows[-1]['timestamp'].isoformat(),
            'assumptions':{
                'percentile':'nearest-rank ceil(0.95*N), calculated per transformed circuit stream',
                'units':'Mbps offered rates and hypothetical GBP/month',
                'direction':'one consistent direction towards Kestrel, billed alone; not maxima of ingress/egress',
                'timestamps':'UTC interval starts, represented without a timezone suffix; no DST transitions',
                'rounding':'each transit and IX charge rounded half-up to pennies, then summed',
                'commit_a_mbps':str(commit_a),'commit_b_mbps':str(commit_b),
                'commit_unit_price':str(price),'burst_unit_price':str(burst_price),'ix_monthly_cost':str(ix_cost),
                'no_ix_fraction_to_a':str(ix_split),'cache_fraction_of_transit_rates':str(cache_fraction),
                'cache_cost':'excluded; saving is before cache costs, fill traffic and support',
                'outage':'B unavailable for the full busiest aggregate-transit day; all its offered traffic rerouted to A; monthly commits remain payable',
                'capacity_a_mbps':str(capacity_a),'capacity_b_mbps':str(capacity_b),
                'capacity':'flags offered rates above capacity; does not simulate drops or billable delivered traffic',
                'excluded':'taxes, one-off charges, burst clauses, direction alternatives, sampling loss and other contract terms'},
            'results':output}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('csv',nargs='?',default='traffic.csv',type=Path)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--allow-partial',action='store_true')
    for flag,default in [('price','0.06'),('burst-price','0.06'),('commit-a','0'),('commit-b','0'),
                         ('ix-cost','1200'),('ix-split','0.5'),('cache-fraction','0.15'),
                         ('capacity-a','100000'),('capacity-b','100000')]:
        ap.add_argument('--'+flag,type=D,default=D(default))
    args=ap.parse_args()
    kwargs={k:getattr(args,k) for k in ('price','burst_price','commit_a','commit_b','ix_cost','ix_split','cache_fraction','capacity_a','capacity_b')}
    if any(not value.is_finite() or value<0 for value in kwargs.values()):
        ap.error('All numeric arguments must be finite and nonnegative')
    result=analyse(read_samples(args.csv,args.allow_partial),**kwargs)
    result['input_sha256']=hashlib.sha256(args.csv.read_bytes()).hexdigest()
    result['complete_month_required']=not args.allow_partial
    if args.output:
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('Hypothetical monthly charges; cache costs excluded. Capacity failure invalidates a lossless scenario.')
    print(f'{"Scenario":<34} {"GBP/month":>12} {"Saving":>12} {"Capacity OK":>12}')
    for r in result['results']:
        print(f'{r["scenario"]:<34} {r["monthly_total_gbp"]:>12} {r["saving_vs_current_gbp"]:>12} {str(r["capacity_feasible"]):>12}')
    print('Full assumptions and per-circuit metrics are included with --output.')

if __name__=='__main__':
    main()
