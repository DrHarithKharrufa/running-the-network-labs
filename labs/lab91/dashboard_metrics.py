"""Original Chapter 91 offline examples. Synthetic complete data, never live telemetry."""
from fractions import Fraction
import json
import math
import statistics


def count(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, int) or value < (1 if positive else 0):
        raise ValueError(f'{name} must be an integer {"above zero" if positive else "at least zero"}')
    return value


def number(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be finite')
    if value < 0 or (positive and value == 0):
        raise ValueError(f'{name} must be {"positive" if positive else "non-negative"}')
    return value


def union_minutes(intervals, window):
    """Half-open integer-minute intervals, all wholly within the observation window."""
    count(window, 'window', True)
    checked = []
    for start, end in intervals:
        count(start, 'start'); count(end, 'end')
        if not 0 <= start < end <= window:
            raise ValueError('interval is empty, reversed or outside the observation window')
        checked.append((start, end))
    total = 0
    previous_end = 0
    for start, end in sorted(checked):
        total += max(0, end - max(start, previous_end))
        previous_end = max(previous_end, end)
    return total


def impact(events, customers, window, *, complete_evidence=False):
    """Equal-weight, fixed eligible population; explicit complete evidence required.

    An empty event list means available only within this synthetic complete-log model.
    It is not a production inference rule. Dynamic eligibility and unknown data need
    a different implementation, such as the interval reporting method in lab87.
    """
    if complete_evidence is not True:
        raise ValueError('complete evidence must be explicitly declared for this fixture model')
    if not customers or any(not isinstance(c, str) or not c for c in customers):
        raise ValueError('a non-empty named population is required')
    if len(set(customers)) != len(customers):
        raise ValueError('duplicate customer')
    count(window, 'window', True)
    if set(events) - set(customers):
        raise ValueError('event customer outside eligible population')
    per_customer = {c: union_minutes(events.get(c, []), window) for c in customers}
    unavailable = sum(per_customer.values())
    eligible = len(customers)*window
    elapsed = union_minutes([e for values in events.values() for e in values], window)
    return {'unavailable_customer_minutes': unavailable, 'eligible_customer_minutes': eligible,
            'customer_time_availability': Fraction(eligible-unavailable, eligible),
            'elapsed_any_impact_minutes': elapsed,
            'all_customers_simultaneously_up_time_availability': Fraction(window-elapsed, window)}


def capacity(load, trigger, growth, lead, contingency):
    """Constant monthly compound growth to a supplied planning trigger, not forecast assurance."""
    for name, val in [('load',load),('trigger',trigger)]: number(val,name,True)
    for name, val in [('growth',growth),('lead',lead),('contingency',contingency)]: number(val,name)
    if load >= trigger:
        return {'state':'REACHED' if load == trigger else 'BREACHED', 'months_to_trigger':0.0,
                'latest_decision_in_months': -(lead+contingency)}
    if growth == 0:
        return {'state':'NO_FINITE_CROSSING_IN_MODEL','months_to_trigger':None,'latest_decision_in_months':None}
    time = math.log(trigger/load)/math.log1p(growth)
    return {'state':'BELOW_TRIGGER','months_to_trigger':time,'latest_decision_in_months':time-lead-contingency}


def changes(success, failure, unresolved):
    for name,value in [('success',success),('failure',failure),('unresolved',unresolved)]: count(value,name)
    total=success+failure+unresolved
    if not total: return {'state':'NOT_MEASURED'}
    known=success+failure
    return {'state':'MEASURED','success_lower':Fraction(success,total),
            'success_upper':Fraction(success+unresolved,total),'outcome_coverage':Fraction(known,total),
            'known_outcome_success':Fraction(success,known) if known else None}


def restoration(completed_minutes, unresolved_ages):
    for t in completed_minutes+unresolved_ages: number(t,'duration')
    values=sorted(completed_minutes)
    return {'completed_count':len(values), 'mean_minutes':statistics.mean(values) if values else None,
            'median_minutes':statistics.median(values) if values else None,
            'nearest_rank_p95_minutes':values[math.ceil(.95*len(values))-1] if values else None,
            'unresolved_ages_minutes':unresolved_ages}


def effort(tasks, old_minutes, new_minutes, maintenance_hours, rework_hours, initial_hours):
    """Non-overlapping labour components. Released capacity is not payroll saving."""
    count(tasks,'tasks')
    for name,val in [('old',old_minutes),('new',new_minutes),('maintenance',maintenance_hours),
                     ('rework',rework_hours),('initial',initial_hours)]: count(val,name)
    old=Fraction(tasks*old_minutes,60)
    new=Fraction(tasks*new_minutes,60)+maintenance_hours+rework_hours
    saved=old-new
    return {'old_hours':old,'ongoing_hours':new,'net_released_hours':saved,
            'effort_break_even_months':Fraction(initial_hours)/saved if saved>0 else None}


def examples():
    return {'scope':'Synthetic complete fixtures and calculations only; no telemetry, trial or NOS execution.',
            'impact':impact({'A':[(0,10),(5,15)],'B':[(5,15)]},['A','B','C','D'],60,complete_evidence=True),
            'capacity_2_percent':capacity(50,70,.02,6,2), 'capacity_5_percent':capacity(50,70,.05,6,2),
            'change':changes(90,6,4),'restoration':restoration([5,10,15,20,150],[180]),
            'effort':effort(100,30,5,12,10,80),
            'exercise_unavailable_minutes':Fraction(30*24*60)*Fraction(2,10000)}


if __name__=='__main__':
    print(json.dumps(examples(),indent=2,default=lambda x: {'exact':str(x),'decimal':float(x)} if isinstance(x,Fraction) else str(x)))
