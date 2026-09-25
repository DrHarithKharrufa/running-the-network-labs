"""Address-plan checks; this is arithmetic, not a running-network test."""
from ipaddress import ip_network
import json
from pathlib import Path

def validate_allocations(parent, allocations):
    parent = ip_network(parent, strict=True)
    networks = []
    for name, prefix in allocations.items():
        child = ip_network(prefix, strict=True)
        if child.version != parent.version or not child.subnet_of(parent):
            raise ValueError(f'{name}: {prefix} is outside {parent}')
        for other_name, other in networks:
            if child.overlaps(other):
                raise ValueError(f'{name} overlaps {other_name}')
        networks.append((name, child))
    return networks

def conventional_ipv4_capacity(prefix, reserved_hosts=0):
    network = ip_network(prefix, strict=True)
    if network.version != 4 or network.prefixlen > 30:
        raise ValueError('Use only conventional IPv4 LAN prefixes of /30 or shorter')
    if type(reserved_hosts) is not int or reserved_hosts < 0:
        raise ValueError('Reserved hosts must be a non-negative integer')
    count = network.num_addresses - 2 - reserved_hosts
    if count < 0:
        raise ValueError('Reservations exceed host capacity')
    return count

def child_count(parent, child_prefix_length):
    network = ip_network(parent, strict=True)
    if type(child_prefix_length) is not int or not network.prefixlen <= child_prefix_length <= network.max_prefixlen:
        raise ValueError('Child prefix length outside parent/address-family bounds')
    return 1 << (child_prefix_length - network.prefixlen)

def load_plan():
    return json.loads(Path(__file__).with_name('aldergate-plan.json').read_text())

if __name__ == '__main__':
    plan = load_plan()
    for family in ['ipv4', 'ipv6']:
        validate_allocations(plan[family]['parent'], plan[family]['site_blocks'])
    print('PASS: site allocations are canonical, contained and disjoint.')
    print('London wireless /22 conventional capacity:', conventional_ipv4_capacity('10.10.4.0/22'))
    print('Aldergate /48 contains /56 site blocks:', child_count('2001:db8:a1de::/48',56))
