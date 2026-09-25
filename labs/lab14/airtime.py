"""Compute an illustrative radio-count bound with explicit workload inputs."""
import argparse,json,math
from pathlib import Path
from fractions import Fraction

def number(value):return Fraction(str(value))
def calculate(model,multiplier,mixed,one_ap_loss):
    budget=number(model['utilisation_budget'])
    if not 0<budget<=1:raise ValueError('utilisation_budget must be in (0,1]')
    demand={'5GHz':Fraction(0),'6GHz':Fraction(0)}
    for group in model['groups']:
        population=number(group['population'])
        activity=number(group['active_fraction'])*multiplier
        rate=number(group['payload_mbps_per_active'])
        eligible=number(group['six_ghz_fraction']) if mixed else Fraction(0)
        if population<0 or rate<0 or not 0<=activity<=1 or not 0<=eligible<=1:
            raise ValueError('Invalid population, activity, rate or eligible fraction')
        offered=population*activity*rate
        demand['6GHz']+=offered*eligible
        demand['5GHz']+=offered*(1-eligible)
    rows={}
    for band,offered in demand.items():
        cfg=model['bands'][band];capacity=number(cfg['useful_payload_capacity_mbps'])
        if capacity<=0:raise ValueError('Useful capacity must be positive')
        required=math.ceil(offered/(budget*capacity))
        if offered>0 and one_ap_loss:required+=1
        available=cfg['qualified_channel_opportunities']
        if not isinstance(available,int) or available<0:raise ValueError('Invalid channel count')
        rows[band]={'offered_payload_mbps':float(offered),'budgeted_payload_mbps_per_radio':float(budget*capacity),
                    'required_radios':required,'assumed_channel_opportunities':available,
                    'fits_assumed_opportunities':required<=available}
    return {'mixed_band':mixed,'one_ap_loss_capacity_reserve':one_ap_loss,
            'activity_multiplier':float(multiplier),'bands':rows,
            'physical_ap_lower_bound':max(r['required_radios'] for r in rows.values()),
            'channel_count_bound_satisfied':all(r['fits_assumed_opportunities'] for r in rows.values()),
            'warning':'A satisfied arithmetic bound does not prove RF coverage, independent airtime, latency or successful client redistribution.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,default=Path(__file__).with_name('model.json'))
    parser.add_argument('--activity-multiplier',default='1')
    args=parser.parse_args()
    try:
        model=json.loads(args.model.read_text(encoding='utf-8'))
        multiplier=number(args.activity_multiplier)
        if multiplier<=0:raise ValueError('Activity multiplier must be positive')
        rows=[calculate(model,multiplier,mixed,loss) for mixed in (False,True) for loss in (False,True)]
    except (ValueError,KeyError,ZeroDivisionError) as exc:parser.error(str(exc))
    print(json.dumps({'scope':model['scope'],'cases':rows},indent=2))
