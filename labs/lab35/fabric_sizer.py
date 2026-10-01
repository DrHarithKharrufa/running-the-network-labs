#!/usr/bin/env python3
"""Capacity/port arithmetic for a complete leaf-spine graph, not a performance guarantee.

Rates are decimal Gb/s in one direction. Logical interfaces and physical cages
are counted separately. Breakout modes must be qualified on the real platform.
"""
import json
import math


def positive_int(name,value,zero=False):
    if type(value) is not int or value < (0 if zero else 1):
        raise ValueError(name+' must be '+('nonnegative' if zero else 'positive')+' integer')
    return value


def rate(name,value):
    if type(value) not in (int,float) or not math.isfinite(value) or value<=0:
        raise ValueError(name+' must be a positive finite rate')
    return value


def cages(logical_ports,lanes_per_cage):
    positive_int('logical_ports',logical_ports,zero=True)
    positive_int('lanes_per_cage',lanes_per_cage)
    return (logical_ports+lanes_per_cage-1)//lanes_per_cage


def size(leaf_ports_down,leaf_speed_down,leaf_ports_up,leaf_speed_up,n_spines,failed_spines=0):
    """Equal numbers/rates of links to every spine; no ECMP throughput prediction."""
    for name,value in [('downlinks',leaf_ports_down),('uplinks',leaf_ports_up),('spines',n_spines)]:
        positive_int(name,value)
    positive_int('failed_spines',failed_spines,zero=True)
    for name,value in [('downlink rate',leaf_speed_down),('uplink rate',leaf_speed_up)]:rate(name,value)
    if leaf_ports_up%n_spines:
        raise ValueError('Uplink count must be a positive multiple of spine count')
    if failed_spines>n_spines:raise ValueError('Cannot fail more spines than exist')
    per_spine=leaf_ports_up//n_spines
    down_bw=leaf_ports_down*leaf_speed_down
    up_bw=leaf_ports_up*leaf_speed_up
    remaining_up=(n_spines-failed_spines)*per_spine*leaf_speed_up
    return dict(down_bw_gbps=down_bw,up_bw_gbps=up_bw,oversubscription=down_bw/up_bw,
                links_per_spine=per_spine,remaining_up_gbps=remaining_up,
                failure_oversubscription=down_bw/remaining_up if remaining_up else None,
                isolated=remaining_up==0,
                no_leaf_uplink_oversubscription=down_bw<=up_bw)


def uniform_fabric(n_leaves,n_spines,leaf_ports_down,leaf_speed_down,leaf_ports_up,leaf_speed_up,
                   leaf_cages,leaf_reserved,down_breakout,up_breakout,
                   spine_cages,spine_reserved,spine_breakout,nics_per_server=1,failed_spines=0):
    for name,value in [('leaves',n_leaves),('leaf cages',leaf_cages),('spine cages',spine_cages),('NICs per server',nics_per_server)]:positive_int(name,value)
    for name,value in [('leaf reserve',leaf_reserved),('spine reserve',spine_reserved)]:positive_int(name,value,zero=True)
    positive_int('spine breakout',spine_breakout)
    s=size(leaf_ports_down,leaf_speed_down,leaf_ports_up,leaf_speed_up,n_spines,failed_spines)
    leaf_used=cages(leaf_ports_down,down_breakout)+cages(leaf_ports_up,up_breakout)
    if leaf_used+leaf_reserved>leaf_cages:raise ValueError('Leaf physical cage budget exceeded')
    spine_used=cages(n_leaves*s['links_per_spine'],spine_breakout)
    if spine_used+spine_reserved>spine_cages:raise ValueError('Spine physical cage budget exceeded')
    if leaf_ports_down%nics_per_server:raise ValueError('Downlink ports must cover whole homogeneous server attachments')
    s.update(leaves=n_leaves,spines=n_spines,leaf_used_cages=leaf_used,
             leaf_reserved_cages=leaf_reserved,leaf_free_cages=leaf_cages-leaf_reserved-leaf_used,
             spine_used_cages=spine_used,spine_reserved_cages=spine_reserved,
             spine_free_cages=spine_cages-spine_reserved-spine_used,
             max_uniform_leaves=(spine_cages-spine_reserved)*spine_breakout//s['links_per_spine'],
             server_interfaces=n_leaves*leaf_ports_down,
             homogeneous_single_leaf_servers=n_leaves*leaf_ports_down//nics_per_server,
             logical_fabric_links=n_leaves*leaf_ports_up,
             aggregate_server_capacity_gbps=n_leaves*s['down_bw_gbps'])
    return s


def anvil_hall():
    """Explicit one-hall arithmetic assumption, not a qualified BOM or HA design."""
    spines=8
    pools={}
    for name,n,down_count,down_rate,up_rate,down_breakout,up_breakout in [
        ('general',20,24,25,25,4,4),('storage',4,16,25,25,4,4),('gpu_service',8,8,100,100,1,1)]:
        s=size(down_count,down_rate,8,up_rate,spines,failed_spines=1)
        used=cages(down_count,down_breakout)+cages(8,up_breakout)
        assert used+4<=32
        s.update(leaves=n,server_interfaces=n*down_count,leaf_used_cages=used,
                 leaf_reserved_cages=4,leaf_free_cages=32-4-used,
                 uplink_lanes_per_cage=up_breakout,
                 one_uplink_cage_loss_ratio=s['down_bw_gbps']/((8-up_breakout)*up_rate))
        pools[name]=s
    # General and storage have the same rate/breakout mode and may share groups.
    spine_used=cages(24,4)+8
    return {'scope':anvil_hall.__doc__,'spines':8,'leaves':32,'logical_fabric_links':256,
            'server_interfaces':608,'gpu_nodes':64,'pools':pools,
            'per_spine':{'logical_links':32,'used_cages':spine_used,'reserved_cages':4,
                         'free_cages':32-4-spine_used,'aggregate_link_capacity_gbps':24*25+8*100},
            'server_facing_gbps':20*600+4*400+8*800,
            'uplink_gbps':24*200+8*800}


def examples():
    return {'scope':__doc__,
            'worked_leaf':size(48,25,8,100,8,failed_spines=1),
            'two_links_per_spine':size(48,25,8,100,4,failed_spines=1),
            'exercise_2000':uniform_fabric(42,4,48,25,4,100,32,4,4,1,64,4,1),
            'exercise_4000':uniform_fabric(84,4,48,25,4,100,32,4,4,1,128,8,1),
            'anvil_hall':anvil_hall()}


if __name__=='__main__':print(json.dumps(examples(),indent=2,allow_nan=False))
