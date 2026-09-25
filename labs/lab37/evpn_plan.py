#!/usr/bin/env python3
"""Lab 37.1 --- a route-membership plan, and what it is not.

This builds the control-plane distribution plan for an EVPN fabric: which bridge
domains and IP-VRFs exist on which leaf, what route targets each EXPORTS, what
each IMPORTS, and therefore which routes end up where. It then reports the things
that are worth finding before you build: one-way relationships, route targets
nobody imports, imports that match nothing, and pairs that can exchange routes
without anyone having said they should.

WHAT THIS IS NOT, and the earlier version of this script got this wrong:

  * It is NOT a reachability test. No traffic exists here. Two bridge domains
    that import each other's targets may still not pass a packet: the VTEPs may
    not reach each other, the MTU may be wrong, the workload may be silent, or
    the platform may not have the resources.
  * It is NOT a security policy. Route targets decide what a VRF LEARNS. They
    say nothing about what a workload may do with what it learns. Isolation in a
    real fabric is route targets plus filtering plus what the platform enforces.
  * It does NOT tell you what the devices are actually doing. Several
    implementations auto-derive a route target when none is configured, and the
    derivation can include the local ASN --- so in an eBGP fabric every leaf can
    end up with a different target for the same VNI. Lab 37.2 shows exactly that.
    Check the operational state, not the intent.

The earlier version derived the route target from the VNI and then declared two
things reachable if they shared a VNI and a target. Since the target came from
the VNI, that test could only ever agree with itself. Here imports and exports
are independent inputs, so a mistake in either shows up.

    python3 evpn_plan.py [--json]
"""
import argparse
import json
import sys


# --------------------------------------------------------------------------
# The plan. Imports and exports are stated separately, on purpose: that is the
# only way a one-way relationship can be represented, and one-way relationships
# are where the interesting mistakes live.
# --------------------------------------------------------------------------
PLAN = {
    'fabric': 'anvil',
    'route_target_convention': (
        'Explicitly configured as 64500:<VNI>. Explicit, not auto-derived: an '
        'auto-derived target can differ per leaf in an eBGP fabric.'),
    'services': {
        # --- tenant red: two subnets, one IP-VRF -------------------------
        'red-web': {
            'kind': 'bridge-domain', 'tenant': 'red', 'vni': 10010,
            'leaves': ['leaf-01', 'leaf-03'],
            'export': ['64500:10010'], 'import': ['64500:10010'],
        },
        'red-db': {
            'kind': 'bridge-domain', 'tenant': 'red', 'vni': 10011,
            'leaves': ['leaf-01'],
            'export': ['64500:10011'], 'import': ['64500:10011'],
        },
        'red-vrf': {
            'kind': 'ip-vrf', 'tenant': 'red', 'vni': 50010,
            'leaves': ['leaf-01', 'leaf-03'],
            'export': ['64500:50010'],
            # The shared-services import is deliberate and is the only path
            # out of this tenant. It is one-way by design: red imports from
            # shared, shared does not import from red.
            'import': ['64500:50010', '64500:50099'],
        },
        # --- tenant blue: same shape, no relationship to red --------------
        'blue-web': {
            'kind': 'bridge-domain', 'tenant': 'blue', 'vni': 10020,
            'leaves': ['leaf-02', 'leaf-04'],
            'export': ['64500:10020'], 'import': ['64500:10020'],
        },
        'blue-vrf': {
            'kind': 'ip-vrf', 'tenant': 'blue', 'vni': 50020,
            'leaves': ['leaf-02', 'leaf-04'],
            'export': ['64500:50020'],
            'import': ['64500:50020', '64500:50099'],
        },
        # --- shared services: exports to everyone, imports from nobody ----
        'shared-vrf': {
            'kind': 'ip-vrf', 'tenant': 'shared', 'vni': 50099,
            'leaves': ['leaf-01', 'leaf-02'],
            'export': ['64500:50099'],
            'import': ['64500:50099'],
        },
    },
}


class PlanError(ValueError):
    pass


def validate(plan):
    services = plan.get('services')
    if not isinstance(services, dict) or not services:
        raise PlanError('plan has no services')
    for name, s in services.items():
        for field in ('kind', 'tenant', 'vni', 'leaves', 'export', 'import'):
            if field not in s:
                raise PlanError('%s is missing %r' % (name, field))
        if s['kind'] not in ('bridge-domain', 'ip-vrf'):
            raise PlanError('%s has unknown kind %r' % (name, s['kind']))
        if not isinstance(s['vni'], int) or not 1 <= s['vni'] <= 0xFFFFFF:
            raise PlanError('%s has a VNI outside the 24-bit range: %r'
                            % (name, s['vni']))
        if not s['leaves']:
            raise PlanError('%s is on no leaves' % name)
        for rt in list(s['export']) + list(s['import']):
            if not isinstance(rt, str) or rt.count(':') != 1:
                raise PlanError('%s has a malformed route target %r' % (name, rt))
    vnis = {}
    for name, s in services.items():
        vnis.setdefault(s['vni'], []).append(name)
    dupes = {v: n for v, n in vnis.items() if len(n) > 1}
    if dupes:
        raise PlanError('a VNI identifies one service; reused: %r' % dupes)
    return services


def analyse(plan):
    services = validate(plan)
    exported = {}
    for name, s in services.items():
        for rt in s['export']:
            exported.setdefault(rt, set()).add(name)

    # Who learns whose routes. Deliberately directional.
    learns = {}
    for a, sa in services.items():
        for b, sb in services.items():
            if a == b:
                continue
            shared = sorted(set(sa['import']) & set(sb['export']))
            if shared:
                learns.setdefault(a, {})[b] = shared

    findings = []
    for name, s in services.items():
        for rt in s['import']:
            if rt not in exported:
                findings.append({'severity': 'error', 'service': name,
                                 'issue': 'imports %s, which nothing exports' % rt})
        for rt in s['export']:
            importers = [n for n, o in services.items()
                         if rt in o['import'] and n != name]
            if importers:
                continue
            # A service spanning several leaves consumes its own exported target
            # on its remote instances: that is the ordinary case, not a fault.
            if rt in s['import'] and len(s['leaves']) > 1:
                continue
            if rt in s['import']:
                findings.append({'severity': 'info', 'service': name,
                                 'issue': 'exports %s and is on one leaf only, so '
                                          'nothing remote consumes it yet' % rt})
            else:
                findings.append({'severity': 'warning', 'service': name,
                                 'issue': 'exports %s, which nothing imports --- '
                                          'not even itself' % rt})
    seen = set()
    for a, targets in learns.items():
        for b in targets:
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            seen.add(key)
            back = learns.get(b, {}).get(a)
            ta, tb = services[a]['tenant'], services[b]['tenant']
            if back and ta != tb:
                findings.append({
                    'severity': 'review', 'service': '%s <-> %s' % (a, b),
                    'issue': 'tenants %s and %s learn each other\'s routes in '
                             'BOTH directions --- a mutual path between tenants'
                             % (ta, tb)})
            elif not back and ta != tb:
                findings.append({
                    'severity': 'info', 'service': '%s -> %s' % (a, b),
                    'issue': '%s learns from %s one way only (tenants %s and %s)'
                             % (a, b, ta, tb)})

    return {'services': services, 'exported_by': {k: sorted(v) for k, v
                                                  in exported.items()},
            'learns': {a: {b: rts for b, rts in t.items()}
                       for a, t in learns.items()},
            'findings': findings,
            'scope': ('Control-plane route-target membership only. Not '
                      'reachability, not forwarding, not security policy, and '
                      'not what the devices are actually doing.')}


def report(plan):
    r = analyse(plan)
    services = r['services']
    print('Fabric          : %s' % plan.get('fabric', '(unnamed)'))
    print('RT convention   : %s\n' % plan.get('route_target_convention', '(none stated)'))
    print('%-12s %-15s %-8s %-8s %s' % ('SERVICE', 'KIND', 'TENANT', 'VNI', 'LEAVES'))
    for name, s in sorted(services.items()):
        print('%-12s %-15s %-8s %-8s %s'
              % (name, s['kind'], s['tenant'], s['vni'], ', '.join(s['leaves'])))

    print('\nRoute targets, stated separately in each direction:')
    for name, s in sorted(services.items()):
        print('  %-12s export %-28s import %s'
              % (name, ', '.join(s['export']), ', '.join(s['import'])))

    print('\nWho learns whose routes (directional):')
    for a in sorted(services):
        for b, rts in sorted(r['learns'].get(a, {}).items()):
            mutual = a in r['learns'].get(b, {})
            print('  %-12s learns from %-12s via %-14s %s'
                  % (a, b, ', '.join(rts), '' if mutual else '(one way)'))

    print('\nFindings:')
    if not r['findings']:
        print('  none')
    for f in r['findings']:
        print('  [%-7s] %-24s %s' % (f['severity'], f['service'], f['issue']))

    print('\n' + r['scope'])
    print('Verify the live fabric against this plan with a show command; do not '
          'assume\nthe configured target is the one in use.')
    return r


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--json', action='store_true', help='print the analysis as JSON')
    a = p.parse_args(argv)
    r = report(PLAN)
    if a.json:
        out = dict(r)
        out.pop('services', None)
        print(json.dumps(out, indent=2))
    errors = [f for f in r['findings'] if f['severity'] == 'error']
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
