"""Synthetic Chapter87 reporting arithmetic; no live SLA or probe measurements.
Time is integer seconds relative to a fixed window, half-open [start,end).
Fixture down/unknown states are mutually exclusive; unspecified time is known up
ONLY under this synthetic fixture's complete-event-log assumption.
"""
from fractions import Fraction as F
import json

def fraction(value, low=0, high=1):
    if isinstance(value,bool): raise ValueError('fraction')
    try:r=F(str(value))
    except (ValueError,ZeroDivisionError):raise ValueError('finite fraction') from None
    if not low<=r<=high: raise ValueError('fraction range')
    return r

def count(value, name='seconds', positive=False):
    if type(value) is not int or abs(value)>10**12 or (positive and value<=0):raise ValueError(name)
    return value

def intervals(rows,window):
    count(window,positive=True);clipped=[]
    for row in rows:
        if not isinstance(row,(tuple,list)) or len(row)!=2:raise ValueError('interval')
        a,b=(count(v) for v in row)
        if a>=b:raise ValueError('interval order')
        a,b=max(0,a),min(window,b)
        if a<b:clipped.append((a,b))
    merged=[]
    for a,b in sorted(clipped):
        if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:merged.append((a,b))
    return merged

def duration(rows):return sum(b-a for a,b in rows)

def overlap(left,right):
    return sum(max(0,min(b,d)-max(a,c)) for a,b in left for c,d in right)

def report(window,down=(),unknown=(),excluded=()):
    d,u,e=(intervals(rows,window) for rows in [down,unknown,excluded])
    if overlap(d,u):raise ValueError('contradictory down and unknown states')
    eligible=window-duration(e);bad=duration(d)-overlap(d,e);missing=duration(u)-overlap(u,e)
    if eligible==0:return {'eligible':0,'bad':0,'unknown':0,'lower':None,'upper':None,'coverage':None}
    return {'eligible':eligible,'bad':bad,'unknown':missing,
            'lower':F(eligible-bad-missing,eligible),'upper':F(eligible-bad,eligible),
            'coverage':F(eligible-missing,eligible)}

def objective(result,target):
    t=fraction(target)
    if result['lower'] is None:return 'NOT_MEASURABLE'
    if result['lower']>=t:return 'MET_WITHIN_BOUNDS'
    if result['upper']<t:return 'VIOLATED_WITHIN_BOUNDS'
    return 'INDETERMINATE'

def error_budget(seconds,target):
    return count(seconds,positive=True)*(1-fraction(target))

def burn_rate(bad,eligible,target):
    count(bad);count(eligible,positive=True)
    if not 0<=bad<=eligible:raise ValueError('bad seconds')
    t=fraction(target)
    if t==1:raise ValueError('zero error budget has no finite burn ratio')
    return F(bad,eligible)/(1-t)

def credit_fraction(availability):
    a=fraction(availability)
    # Invented non-cumulative monthly tiers, not AWS or any supplier contract.
    if a>=F('0.9999'):return F(0)
    if a>=F('0.999'):return F('0.10')
    if a>=F('0.99'):return F('0.25')
    return F(1)

def expected_credit(distribution,monthly_fee):
    fee=fraction(monthly_fee,0,10**12);rows=[(fraction(p),fraction(a)) for p,a in distribution]
    if sum(p for p,a in rows)!=1:raise ValueError('probabilities must sum exactly to one')
    return sum((p*fee*credit_fraction(a) for p,a in rows),F(0))

def value(x):
    return None if x is None else float(x)

def public(result):
    return {k:(value(v)*100 if v is not None else None) if k in ('lower','upper','coverage') else v for k,v in result.items()}

def worksheet():
    w=30*86400;d=[(1000,1900),(1600,2500)];u=[(3000,3120)];e=[(1900,2500)]
    eligible=report(w,d,u,e);customer=report(w,d,u)
    a=[(1,'0.9995')];b=[('.9',1),('.1','.995')]
    return {'scope':'Synthetic complete event log and invented contract. Local exact rational calculations, no live measurement or claim.',
        'window_seconds':w,'down_intervals':d,'unknown_intervals':u,'approved_exclusions':e,
        'contract_excluded_view':public(eligible),'all_time_customer_view':public(customer),
        'objective_99_95':objective(eligible,'.9995'),'objective_99_99':objective(eligible,'.9999'),
        'budgets_minutes_99_9':{str(days):value(error_budget(days*86400,'.999')/60) for days in [28,29,30,31]},
        'burn_90_bad_seconds_of_hour':value(burn_rate(90,3600,'.999')),
        'monthly_budget_fraction_used':value(F(90)/error_budget(w,'.999')),
        'equal_mean_models':{'mean_A':value(sum(F(str(p))*F(str(v)) for p,v in a)),
            'mean_B':value(sum(F(str(p))*F(str(v)) for p,v in b)),
            'A_breach_probability_99_99':1,'B_breach_probability_99_99':.1,
            'A_expected_GBP_credit':value(expected_credit(a,10000)),
            'B_expected_GBP_credit':value(expected_credit(b,10000))}}

if __name__=='__main__':print(json.dumps(worksheet(),indent=2))
