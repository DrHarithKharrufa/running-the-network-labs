#!/usr/bin/env python3
"""Revision teaching-v1: invented capacity cases, not device benchmarks."""
from fractions import Fraction as F
import json
import math


def count(n, minimum=0):
    if type(n) is not int or n < minimum:
        raise ValueError('invalid nonnegative integer count')
    return n


def number(x):
    if isinstance(x, bool) or not isinstance(x, (int, float, F)):
        raise ValueError('invalid nonnegative finite number')
    try:
        valid = math.isfinite(x) and x >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError('invalid nonnegative finite number')
    return F(str(x))


def session_counts(nodes):
    count(nodes, 3)
    clients = nodes-2
    return {'nodes': nodes, 'full_mesh_total': nodes*(nodes-1)//2,
            'full_mesh_per_node': nodes-1, 'two_RR_total': 2*clients+1,
            'two_RR_per_client': 2, 'two_RR_per_RR': clients+1}


def capacity(ipv4, ipv6, growth=1, capacity_units=100000, ceiling=F(4,5)):
    count(ipv4);count(ipv6);count(capacity_units, 1)
    growth, ceiling = number(growth), number(ceiling)
    if not 0 < ceiling <= 1:
        raise ValueError('planning ceiling must be in (0,1]')
    # Invented shared-resource rule: one unit per IPv4, two per IPv6 prefix.
    used = (ipv4+2*ipv6)*growth
    allowed = capacity_units*ceiling
    return {'used_units': used, 'planning_limit': allowed, 'margin': allowed-used,
            'within_planning_limit': used <= allowed, 'within_physical_model_limit': used <= capacity_units}


def fluid_backlog(arrival, service, duration, after_arrival):
    arrival, service, duration, after_arrival = map(number, (arrival, service, duration, after_arrival))
    backlog = max(F(0), (arrival-service)*duration)
    drain = F(0) if not backlog else backlog/(service-after_arrival) if after_arrival < service else None
    return {'backlog': backlog, 'drain_seconds': drain,
            'drains_under_stated_rates': drain is not None}


def operations(incidents=12):
    count(incidents)
    # Invented weekly engineer-hours, not a shift roster or staffing prescription.
    available = 4*F('37.5')-30
    tasks = {'changes':40*F('.75'), 'incidents':incidents*2,
             'projects':F(35), 'automation_maintenance':F(15), 'platform_operations':F(10)}
    total = sum(tasks.values())
    return {'available_hours':available, 'task_hours':tasks, 'total_hours':total,
            'remaining_hours':available-total, 'within_budget':total <= available}


def leaf_limit(ports=64, other=4, reserved=4, links_per_leaf=1):
    count(ports,1);count(other);count(reserved);count(links_per_leaf,1)
    if other+reserved > ports:
        raise ValueError('reservations exceed port count')
    return (ports-other-reserved)//links_per_leaf


def fabric_capacity(spines=4, failed=0, per_link=100, demand=320):
    count(spines,1);count(failed)
    if failed > spines:
        raise ValueError('too many failed spines')
    per_link, demand = number(per_link), number(demand)
    remaining = (spines-failed)*per_link
    return {'remaining_Gbps':remaining,'margin_Gbps':remaining-demand,
            'meets_aggregate_demand':remaining >= demand}


def serialisable(value):
    if isinstance(value, F):return int(value) if value.denominator == 1 else float(value)
    if isinstance(value, dict):return {k:serialisable(v) for k,v in value.items()}
    if isinstance(value, list):return [serialisable(v) for v in value]
    return value


def worksheet():
    return serialisable({
        'revision':'teaching-v1',
        'scope':'Invented workload and resource models. No measured platform scale, NOS, hardware, forwarding or convergence execution.',
        'sessions':[session_counts(n) for n in (24,240)],
        'shared_table_current':capacity(40000,10000),
        'shared_table_projected_1_5x':capacity(40000,10000,F(3,2)),
        'fluid_burst':fluid_backlog(2500,2000,20,1000),
        'operations_normal':operations(), 'operations_peak':operations(24),
        'leaf_limit_single_link':leaf_limit(), 'leaf_limit_double_link':leaf_limit(links_per_leaf=2),
        'fabric_normal':fabric_capacity(), 'fabric_one_spine_failed':fabric_capacity(failed=1),
        'production_combined_scale_validation':'NOT_RUN',
        'production_tail_restoration_validation':'NOT_RUN'})


if __name__ == '__main__':print(json.dumps(worksheet(), indent=2))
