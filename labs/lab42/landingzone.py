#!/usr/bin/env python3
"""Lab 42.2 --- the landing-zone decisions that are genuinely hard to undo.

WHY THIS VERSION EXISTS
-----------------------
The previous script held two hard-coded dictionaries and called
`ipaddress.overlaps()` on them.  It reported that the plan with deliberately
identical CIDRs overlapped, which it did, and that the plan with different ones
did not.  Nothing you could supply would have taught you anything, because
nothing you supplied was used.

It also checked only the one irreversible decision the chapter named.  The
chapter now names more of them, because "everything else is reversible" was
wrong in a way that costs money: you cannot resize a subnet after you have
created it, so a subnet sized for today's workload is a migration later, and the
account or project hierarchy is painful to restructure once workloads depend on
it.

This version takes a plan you write and checks it against the things that are
expensive to get wrong.  It is meant to fail on a plausible plan --- the shipped
example fails on two counts, on purpose.

    python3 landingzone.py
    python3 landingzone.py --json
    python3 test_landingzone.py

No cloud account and no API call. Addresses on paper, which is the only place
they are cheap to change.
"""
import argparse
import ipaddress
import json
import sys
from itertools import combinations


class PlanError(ValueError):
    """The plan cannot be read as an addressing plan."""


# Ranges that are already spoken for on a typical hybrid estate. Colliding with
# one of these does not show up as a BGP problem; it shows up as one container,
# one instance or one service that cannot reach something, months later.
RESERVED = {
    '169.254.0.0/16': 'link-local, and where cloud instance metadata lives',
    '127.0.0.0/8': 'loopback',
    '224.0.0.0/4': 'multicast',
    '172.17.0.0/16': "the default Docker bridge on most hosts",
    '100.64.0.0/10': 'carrier-grade NAT, used inside several managed services',
}


def parse(plan):
    if not isinstance(plan, dict) or not plan:
        raise PlanError('a plan is a non-empty mapping of name to definition')
    out = {}
    for name, d in plan.items():
        if isinstance(d, str):
            d = {'cidr': d}
        if 'cidr' not in d:
            raise PlanError('%s has no cidr' % name)
        try:
            net = ipaddress.ip_network(d['cidr'], strict=True)
        except ValueError as e:
            raise PlanError('%s: %s' % (name, e))
        subnets = d.get('subnets', {})
        if not isinstance(subnets, dict):
            raise PlanError('%s: subnets must be a mapping of name to size'
                            % name)
        out[name] = {'net': net, 'zones': d.get('zones', 1),
                     'subnets': subnets, 'role': d.get('role', 'vpc'),
                     'growth': d.get('growth', 1.0)}
        if out[name]['zones'] < 1:
            raise PlanError('%s: zones must be at least 1' % name)
        if out[name]['growth'] <= 0:
            raise PlanError('%s: growth must be positive' % name)
    return out


def read_subnet(vpc, sname, spec):
    """A subnet is either a host count, or a host count and the prefix you
    intend to allocate. Stating the prefix is what lets this check disagree
    with you."""
    if isinstance(spec, int):
        hosts, prefix = spec, None
    elif isinstance(spec, dict):
        if 'hosts' not in spec:
            raise PlanError('%s/%s: needs a host count' % (vpc, sname))
        hosts, prefix = spec['hosts'], spec.get('prefix')
    else:
        raise PlanError('%s/%s: expected a host count or a mapping, got %r'
                        % (vpc, sname, spec))
    if not isinstance(hosts, int) or hosts < 1:
        raise PlanError('%s/%s: host count must be a positive integer, got %r'
                        % (vpc, sname, hosts))
    if prefix is not None and not (0 < prefix <= 32):
        raise PlanError('%s/%s: /%r is not a usable prefix length'
                        % (vpc, sname, prefix))
    return hosts, prefix


def analyse(plan):
    nets = parse(plan)
    findings = []

    def add(sev, where, issue):
        findings.append({'severity': sev, 'where': where, 'issue': issue})

    # 1. the decision the old script checked: do any two ranges overlap?
    for (an, a), (bn, b) in combinations(nets.items(), 2):
        if a['net'].overlaps(b['net']):
            add('error', '%s + %s' % (an, bn),
                '%s and %s overlap. Routes for both cannot be installed, so one '
                'side is unreachable, and re-addressing a live environment is '
                'the migration this check exists to avoid'
                % (a['net'], b['net']))

    # 2. collisions with ranges something else already uses
    for name, a in nets.items():
        for cidr, why in RESERVED.items():
            r = ipaddress.ip_network(cidr)
            if a['net'].version == r.version and a['net'].overlaps(r):
                add('error', name,
                    '%s overlaps %s (%s). This does not fail at the routing '
                    'layer, which is why it is found late' % (a['net'], r, why))

    # 3. subnets: they fit, they are sized for the growth you stated, and they
    #    cannot be resized afterwards, which is what makes the sizing matter
    for name, a in nets.items():
        if not a['subnets']:
            continue
        need = 0
        allocation = {}
        for sname, spec in a['subnets'].items():
            hosts, stated_prefix = read_subnet(name, sname, spec)
            # a cloud subnet loses several addresses to the platform; five is
            # the common figure and the exact number is per-provider
            required = int(round(hosts * a['growth'])) + 5
            bits = 1
            while (1 << bits) < required:
                bits += 1
            chosen = a['net'].max_prefixlen - bits
            if stated_prefix is not None:
                have = 1 << (a['net'].max_prefixlen - stated_prefix)
                if have < required:
                    add('error', '%s/%s' % (name, sname),
                        'a /%d holds %d addresses; %d hosts at %gx growth plus '
                        'the five the platform takes needs %d, so a /%d. A '
                        'subnet CANNOT be resized after creation --- getting '
                        'this wrong means building a new subnet and migrating '
                        'into it'
                        % (stated_prefix, have, hosts, a['growth'], required,
                           chosen))
                elif have >= required * 8:
                    add('warning', '%s/%s' % (name, sname),
                        'a /%d holds %d addresses for a requirement of %d. '
                        'Oversizing is not free either: it is address space the '
                        'rest of the estate cannot have'
                        % (stated_prefix, have, required))
                bits = a['net'].max_prefixlen - stated_prefix
                chosen = stated_prefix
            allocation['%s/%s' % (name, sname)] = '/%d' % chosen
            need += 1 << bits
        a['allocation'] = allocation
        capacity = a['net'].num_addresses
        if need > capacity:
            add('error', name,
                'the subnets need %d addresses but %s holds %d. Some clouds let '
                'you add a secondary range later and some do not; none let you '
                'enlarge the primary one'
                % (need, a['net'], capacity))
        elif need > capacity * 0.75:
            add('warning', name,
                'the subnets already use %.0f%% of %s, leaving little room for '
                'the workloads nobody has told you about yet'
                % (100.0 * need / capacity, a['net']))

    # 4. zones: a subnet is per-zone on some clouds, so one subnet is one zone
    for name, a in nets.items():
        if a['role'] == 'vpc' and a['subnets'] and a['zones'] > 1:
            if len(a['subnets']) < a['zones']:
                add('warning', name,
                    'declares %d zones but only %d subnets. Where a subnet '
                    'belongs to one zone, that is not a multi-zone design --- '
                    'and where it does not, the zone spread is decided '
                    'somewhere else entirely. Know which model your provider '
                    'uses before claiming resilience'
                    % (a['zones'], len(a['subnets'])))

    # 5. room to grow the estate itself
    supernets = [a['net'] for a in nets.values()]
    for candidate in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'):
        c = ipaddress.ip_network(candidate)
        inside = [n for n in supernets if n.version == 4 and n.subnet_of(c)]
        if inside:
            used = sum(n.num_addresses for n in inside)
            if used > c.num_addresses * 0.5:
                add('warning', candidate,
                    'this plan already commits %.0f%% of %s. The next '
                    'acquisition, region or cloud has to come from somewhere'
                    % (100.0 * used / c.num_addresses, candidate))

    return {'networks': {n: str(a['net']) for n, a in nets.items()},
            'allocation': {k: v for a in nets.values()
                           for k, v in a.get('allocation', {}).items()},
            'findings': findings,
            'errors': [f for f in findings if f['severity'] == 'error'],
            'warnings': [f for f in findings if f['severity'] == 'warning']}


# --------------------------------------------------------------------------
# The shipped plan. It is a plausible first draft and it does NOT pass.
# --------------------------------------------------------------------------
PLAN = {
    'aldergate-dc': {'cidr': '10.10.0.0/16', 'role': 'on-prem'},
    # A hub sized by counting today's appliances, in a /24 because a hub
    # "does not need much".
    'cloud-hub': {'cidr': '10.20.0.0/24', 'zones': 3, 'growth': 2.0,
                  'subnets': {'tgw-a': {'hosts': 16, 'prefix': 28},
                              'tgw-b': {'hosts': 16, 'prefix': 28},
                              'fw-a': {'hosts': 32, 'prefix': 27},
                              'fw-b': {'hosts': 32, 'prefix': 27},
                              'resolver-a': {'hosts': 16, 'prefix': 28},
                              'resolver-b': {'hosts': 16, 'prefix': 28}}},
    # Two zones' worth of subnets in a three-zone VPC, and a private tier
    # sized for the workload that exists today.
    'cloud-app': {'cidr': '10.21.0.0/16', 'zones': 3, 'growth': 3.0,
                  'subnets': {'public-a': {'hosts': 250, 'prefix': 24},
                              'public-b': {'hosts': 250, 'prefix': 24},
                              'private-a': {'hosts': 500, 'prefix': 23},
                              'private-b': {'hosts': 500, 'prefix': 23}}},
    # A range nobody thought to check against what the hosts already use.
    'cloud-data': {'cidr': '172.17.0.0/16', 'zones': 2, 'growth': 1.5,
                   'subnets': {'db-a': {'hosts': 60, 'prefix': 25},
                               'db-b': {'hosts': 60, 'prefix': 25}}},
}

FIXED = {
    'aldergate-dc': {'cidr': '10.10.0.0/16', 'role': 'on-prem'},
    # Sized from hosts x growth + the platform's five, one subnet per zone,
    # in a hub with room left for the services nobody has asked for yet.
    'cloud-hub': {'cidr': '10.20.0.0/21', 'zones': 3, 'growth': 2.0,
                  'subnets': {'tgw-a': {'hosts': 16, 'prefix': 26},
                              'tgw-b': {'hosts': 16, 'prefix': 26},
                              'tgw-c': {'hosts': 16, 'prefix': 26},
                              'fw-a': {'hosts': 32, 'prefix': 25},
                              'fw-b': {'hosts': 32, 'prefix': 25},
                              'fw-c': {'hosts': 32, 'prefix': 25},
                              'resolver-a': {'hosts': 16, 'prefix': 26},
                              'resolver-b': {'hosts': 16, 'prefix': 26},
                              'resolver-c': {'hosts': 16, 'prefix': 26}}},
    'cloud-app': {'cidr': '10.21.0.0/16', 'zones': 3, 'growth': 3.0,
                  'subnets': {'public-a': {'hosts': 250, 'prefix': 22},
                              'public-b': {'hosts': 250, 'prefix': 22},
                              'public-c': {'hosts': 250, 'prefix': 22},
                              'private-a': {'hosts': 500, 'prefix': 21},
                              'private-b': {'hosts': 500, 'prefix': 21},
                              'private-c': {'hosts': 500, 'prefix': 21}}},
    'cloud-data': {'cidr': '10.22.0.0/16', 'zones': 3, 'growth': 1.5,
                   'subnets': {'db-a': {'hosts': 60, 'prefix': 25},
                               'db-b': {'hosts': 60, 'prefix': 25},
                               'db-c': {'hosts': 60, 'prefix': 25}}},
}


def report(label, plan):
    a = analyse(plan)
    print('[%s]' % label)
    for n, c in a['networks'].items():
        print('    %-16s %s' % (n, c))
    if not a['findings']:
        print('    no findings\n')
        return a
    for f in a['findings']:
        print('    %-8s %-14s %s' % (f['severity'].upper(), f['where'],
                                     f['issue']))
    print()
    return a


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        if args.json:
            print(json.dumps({'draft': analyse(PLAN), 'revised': analyse(FIXED)},
                             indent=2))
            return 0
        print('Landing-zone addressing. The plan below is a plausible first')
        print('draft, and it does not pass --- which is the point of checking\n')
        print('it here rather than after the workloads arrive.\n')
        draft = report('first draft', PLAN)
        revised = report('after the findings are addressed', FIXED)
    except PlanError as e:
        print('plan error: %s' % e, file=sys.stderr)
        return 2
    print('The draft has %d errors and %d warnings; the revision has %d and %d.'
          % (len(draft['errors']), len(draft['warnings']),
             len(revised['errors']), len(revised['warnings'])))
    print('\nNone of the draft\'s faults is a typo. Each is a decision that')
    print('looks harmless on the day and is a migration a year later: a range')
    print('that collides with something nobody mentioned, a hub too small for')
    print('the zone it will need, and subnets sized for the workload that')
    print('happens to exist today.')
    # The draft is MEANT to fail, so its errors are the demonstration, not a
    # problem. The revision being clean is what says the lab did its job.
    return 0 if not revised['errors'] else 1


if __name__ == '__main__':
    sys.exit(main())
