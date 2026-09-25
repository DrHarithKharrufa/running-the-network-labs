#!/usr/bin/env python3
"""Offline address arithmetic and symbolic forwarding, not a router emulator."""
import argparse
import ipaddress as ip
import json
from pathlib import Path
import runpy
import struct


def dimensions(regions, sites, functions):
    for value, bound in ((regions, 16), (sites, 32), (functions, 8)):
        if type(value) is not int or not 1 <= value <= bound:
            raise ValueError('worksheet bounds: 1..16 regions, 1..32 sites, 1..8 functions')


def allocate(regions=4, sites=16, functions=8, interleaved=False):
    """Region /16; each site reserves a /21 with eight /24 slots.

    Alternative interleaved plan assigns a contiguous pool round-robin by region.
    Both allocate exactly regions*sites*functions /24s, but at different addresses.
    """
    dimensions(regions, sites, functions)
    if type(interleaved) is not bool:
        raise ValueError('interleaved must be boolean')
    result = {r: [] for r in range(regions)}
    if interleaved:
        base = int(ip.IPv4Address('10.64.0.0'))
        for i in range(regions*sites*functions):
            result[i % regions].append(ip.IPv4Network((base+i*256, 24)))
    else:
        for r in range(regions):
            for s in range(sites):
                for f in range(functions):
                    result[r].append(ip.IPv4Network(f'10.{r}.{8*s+f}.0/24'))
    return result


def exact_cover(per_region):
    return {str(r): [str(n) for n in ip.collapse_addresses(nets)]
            for r, nets in per_region.items()}


def topology(up=('A', 'B'), policy='any', discard=True, exception=False):
    """C -> R -> A/B. R also has a default back to C.

    A=10.0.0/24, B=10.0.1/24, aggregate=10.0.0/23.
    'up' means R has the corresponding site route, not measured service health.
    An optional C -> R2 -> B exception is assumed independently usable.
    """
    if policy not in ('any', 'all', 'always') or type(discard) is not bool or type(exception) is not bool:
        raise ValueError('invalid policy or flag')
    up = list(up)
    if any(x not in ('A', 'B') for x in up) or len(set(up)) != len(up):
        raise ValueError('up must contain unique A/B entries')
    advertise = policy == 'always' or (policy == 'any' and bool(up)) or (policy == 'all' and len(up) == 2)
    routes = {'C': [('10.0.0.0/23', 'R')] if advertise else [],
              'R': [('0.0.0.0/0', 'C')], 'R2': []}
    for site, prefix in (('A', '10.0.0.0/24'), ('B', '10.0.1.0/24')):
        if site in up:
            routes['R'].append((prefix, 'DELIVERED:'+site))
    if discard:
        routes['R'].append(('10.0.0.0/23', 'DISCARD'))
    if exception:
        routes['C'].append(('10.0.1.0/24', 'R2'))
        routes['R2'].append(('10.0.1.0/24', 'DELIVERED:B'))
    return routes


def trace(routes, destination):
    destination = ip.IPv4Address(destination)
    node, visited = 'C', []
    while node not in visited:
        visited.append(node)
        matches = [(ip.IPv4Network(prefix), target) for prefix, target in routes[node]
                   if destination in ip.IPv4Network(prefix)]
        if not matches:
            return {'path': visited, 'result': 'NO_ROUTE'}
        network, target = max(matches, key=lambda item: item[0].prefixlen)
        if target == 'DISCARD' or target.startswith('DELIVERED:'):
            return {'path': visited, 'result': target}
        node = target
    return {'path': visited+[node], 'result': 'LOOP'}


def rd_encoding(kind, administrator, local):
    """RD field-width example only; no allocation entitlement or NOS validation."""
    if type(kind) is not int or kind not in (0, 1, 2) or type(local) is not int:
        raise ValueError('invalid RD type or local number')
    limit = 2**32 if kind == 0 else 2**16
    if not 0 <= local < limit:
        raise ValueError('local number exceeds encoding')
    if kind == 1:
        if not isinstance(administrator, str):
            raise ValueError('type 1 administrator must be IPv4 text')
        return struct.pack('!H4sH', kind, ip.IPv4Address(administrator).packed, local).hex()
    bound = 2**16 if kind == 0 else 2**32
    if type(administrator) is not int or not 0 <= administrator < bound:
        raise ValueError('administrator exceeds encoding')
    return struct.pack('!HHI' if kind == 0 else '!HIH', kind, administrator, local).hex()


def worksheet():
    hierarchical = allocate()
    interleaved = allocate(interleaved=True)
    scenario_args = {
        'normal': {}, 'B_missing_retain_any': {'up': ('A',)},
        'B_missing_without_discard': {'up': ('A',), 'discard': False},
        'B_missing_withdraw_all_policy': {'up': ('A',), 'policy': 'all'},
        'both_missing_any_policy': {'up': ()},
        'both_missing_always_policy': {'up': (), 'policy': 'always'},
        'B_missing_exception_via_R2': {'up': ('A',), 'exception': True}}
    scenarios = {}
    for name, args in scenario_args.items():
        routes = topology(**args)
        scenarios[name] = {'routes': routes, 'A': trace(routes, '10.0.0.10'),
                           'B': trace(routes, '10.0.1.10')}
    return {
        'scope': 'Offline exact prefix cover and symbolic longest-prefix forwarding only. No RIB/FIB, packets, routing protocol, timer, vendor or hardware execution.',
        'allocated_24s_per_plan': 512,
        'regional_exact_cover_hierarchical': exact_cover(hierarchical),
        'regional_exact_cover_interleaved_counts': {r: len(n) for r, n in exact_cover(interleaved).items()},
        'common_exit_interleaved_exact_cover': [str(n) for n in ip.collapse_addresses([n for nets in interleaved.values() for n in nets])],
        'region_zero_reservation': '10.0.0.0/16',
        'region_zero_16_sites_allocated_24s': len(hierarchical[0]),
        'region_zero_unused_24_slots': 256-len(hierarchical[0]),
        'region_zero_17_sites_exact_cover': exact_cover(allocate(sites=17))['0'],
        'scenarios': scenarios,
        'documentation_RD_examples': {str(k): rd_encoding(k, a, n) for k, a, n in
                                     ((0, 64496, 81001), (1, '192.0.2.81', 101), (2, 65536, 101))}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo-original', action='store_true', help='show preserved flawed historical output')
    args = parser.parse_args()
    if args.demo_original:
        print('HISTORICAL FLAWED DEMONSTRATION: conclusions below are superseded; see README.')
        runpy.run_path(str(Path(__file__).with_name('aggregation_original.py.txt')), run_name='__main__')
    else:
        print(json.dumps(worksheet(), indent=2))
