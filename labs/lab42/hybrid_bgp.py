#!/usr/bin/env python3
"""Lab 42.1 --- the hybrid edge is a peering router, so model it like one.

WHY THIS EXISTS
---------------
Chapter 42 says the cloud on-ramp runs BGP and that the engineers who see the
hybrid edge as a peering router configure it correctly first time.  The lab that
shipped with the chapter checked two hard-coded CIDRs for overlap and multiplied
some invented tariffs.  It never went near BGP --- the one thing the chapter
says is the skill.

This models the route exchange across a hybrid edge: what the data centre
advertises, what the cloud accepts and re-advertises, which path each destination
actually takes, and what happens when the circuit fails.  It exists to make three
failures visible on paper, because all three are cheap here and expensive live.

THE FAILURE THIS LAB IS REALLY ABOUT
------------------------------------
A private circuit with a VPN backup is usually built by giving the circuit a
higher local-preference.  That works only while both paths carry THE SAME
PREFIX.  Best-path selection compares routes for one prefix at a time;
forwarding then picks the longest match.  So if the VPN advertises 10.10.1.0/24
while the circuit advertises 10.10.0.0/16, every packet for 10.10.1.0/24 takes
the VPN --- at VPN bandwidth, with VPN latency --- no matter how high the
circuit's local-preference is, and no alarm fires because both sessions are up.

That is not a cloud quirk.  It is Chapter 21's best-path algorithm meeting
Chapter 5's longest-prefix match, and it bites people on every hybrid edge ever
built.  A model that cannot show it is not modelling BGP.

WHAT THIS IS NOT
----------------
No router, no cloud account, no BGP session and no packet.  This is a
route-table calculation over prefixes and attributes you supply.  It implements
the tie-breaks that matter for a hybrid edge --- longest match, then
local-preference, then AS-path length, then a stated tie-break --- and not the
full algorithm: no MED, no origin code, no router-ID tie-break, no communities,
no add-path, no route reflection, no dampening.  Real quotas and behaviours are
per-provider and change; check yours.

    python3 hybrid_bgp.py
    python3 hybrid_bgp.py --json
    python3 test_hybrid_bgp.py
"""
import argparse
import ipaddress
import json
import sys


class EdgeError(ValueError):
    """The description does not make a route exchange that can be evaluated."""


# --------------------------------------------------------------------------
# a route as it arrives at one side of the edge
# --------------------------------------------------------------------------
def route(prefix, via, local_pref=100, as_path=(), origin='dc'):
    try:
        net = ipaddress.ip_network(prefix, strict=True)
    except ValueError as e:
        raise EdgeError('%s is not a usable prefix: %s' % (prefix, e))
    if not isinstance(local_pref, (int, float)) or local_pref < 0:
        raise EdgeError('local-preference must be a non-negative number, got %r'
                        % (local_pref,))
    if isinstance(as_path, str):
        raise EdgeError('as_path must be a sequence of ASNs, not a string')
    return {'prefix': str(net), 'network': net, 'via': via,
            'local_pref': local_pref, 'as_path': tuple(as_path),
            'origin': origin}


def best_path(routes):
    """Pick one route per prefix, then report what forwarding will do.

    Two separate steps, and conflating them is the mistake this lab exists for:

      1. BEST PATH runs PER PREFIX. Higher local-preference wins, then shorter
         AS-path, then the tie-break below. Routes for different prefixes never
         compete here at all.
      2. FORWARDING then picks the LONGEST MATCH among the surviving prefixes,
         and knows nothing about local-preference.
    """
    if not routes:
        raise EdgeError('no routes to evaluate')
    by_prefix = {}
    for r in routes:
        by_prefix.setdefault(r['prefix'], []).append(r)
    chosen = {}
    for prefix, cands in by_prefix.items():
        cands = sorted(cands, key=lambda r: (
            -r['local_pref'],
            len(r['as_path']),
            str(r['via']),          # stated tie-break, so results are stable
        ))
        chosen[prefix] = cands[0]
        chosen[prefix] = dict(chosen[prefix], rejected=cands[1:])
    return chosen


def lookup(table, address):
    """Longest-match forwarding lookup, the way the data plane does it."""
    try:
        addr = ipaddress.ip_address(address)
    except ValueError as e:
        raise EdgeError('%s is not an address: %s' % (address, e))
    hits = [r for r in table.values() if addr in r['network']]
    if not hits:
        return None
    return max(hits, key=lambda r: r['network'].prefixlen)


# --------------------------------------------------------------------------
# the edge
# --------------------------------------------------------------------------
class Edge:
    """One hybrid edge: what each side advertises and what the other accepts.

    `accept_limit` is the cloud side's cap on prefixes received over the
    circuit. Every provider has one, the number differs and changes, and
    exceeding it does not degrade gracefully --- the session typically drops.
    Set it to what your provider's current quota says, not to what this file
    happens to default to.
    """

    def __init__(self, dc_asn=64510, cloud_asn=64512, accept_limit=100):
        if dc_asn == cloud_asn:
            raise EdgeError('the two sides need different ASNs for eBGP '
                            '(both are %s)' % dc_asn)
        if accept_limit < 1:
            raise EdgeError('the accept limit must be at least 1')
        self.dc_asn, self.cloud_asn = dc_asn, cloud_asn
        self.accept_limit = accept_limit
        self.dc_advertises = []
        self.cloud_advertises = []

    def dc_advertise(self, prefix, via, local_pref=100, as_path=()):
        self.dc_advertises.append(
            route(prefix, via, local_pref, as_path, origin='dc'))
        return self

    def cloud_advertise(self, prefix, via, local_pref=100, as_path=()):
        self.cloud_advertises.append(
            route(prefix, via, local_pref, as_path, origin='cloud'))
        return self

    # -- what the cloud ends up with, and what it does with it --------------
    def evaluate(self, fail=()):
        """fail: names of paths that are down, e.g. ('circuit',)."""
        fail = set(fail)
        received = [r for r in self.dc_advertises if r['via'] not in fail]
        findings = []

        over_limit = len(received) > self.accept_limit
        if over_limit:
            findings.append({
                'severity': 'error',
                'issue': ('the cloud side received %d prefixes against a limit '
                          'of %d. The session DROPS --- it does not trim to the '
                          'limit and keep going, so the consequence is total '
                          'loss of that path, not partial reachability'
                          % (len(received), self.accept_limit))})
            # and model that consequence rather than only warning about it
            received = [r for r in received if r['via'] in fail or False]

        table = best_path(received) if received else {}

        # the real trap: a more-specific on a lower-preference path
        for prefix, r in table.items():
            for other_prefix, other in table.items():
                if other_prefix == prefix:
                    continue
                if (other['network'].subnet_of(r['network'])
                        and other['via'] != r['via']
                        and other['local_pref'] < r['local_pref']):
                    findings.append({
                        'severity': 'error',
                        'issue': ('%s is a more-specific of %s and arrives via '
                                  '%s, whose local-preference (%g) is LOWER '
                                  'than %s (%g). Local-preference will not save '
                                  'you: forwarding takes the longest match, so '
                                  'that traffic uses %s while both sessions sit '
                                  'up and quiet'
                                  % (other_prefix, prefix, other['via'],
                                     other['local_pref'], r['via'],
                                     r['local_pref'], other['via']))})

        # advertising a supernet of a cloud range back into the cloud
        for r in table.values():
            for own in self.cloud_advertises:
                if own['network'].subnet_of(r['network']):
                    findings.append({
                        'severity': 'warning',
                        'issue': ('the data centre advertises %s, which contains '
                                  'the cloud\'s own %s. The cloud prefers its '
                                  'local route, but anything inside %s that the '
                                  'cloud has NOT allocated is now pulled '
                                  'on-premises'
                                  % (r['prefix'], own['prefix'], r['prefix']))})

        if not received and not over_limit:
            findings.append({
                'severity': 'error',
                'issue': 'no prefixes reach the cloud at all --- every path is down'})

        return {'received': len(received), 'over_limit': over_limit,
                'table': table, 'findings': findings,
                'failed': sorted(fail)}


# --------------------------------------------------------------------------
# the worked edge: Aldergate, with a circuit and a VPN backup
# --------------------------------------------------------------------------
def aldergate(summary_only=True):
    """The intended design: circuit preferred, VPN as backup.

    summary_only=False adds the mistake --- the VPN advertising a more-specific
    --- so the two can be compared side by side.
    """
    e = Edge(dc_asn=64510, cloud_asn=64512, accept_limit=100)
    e.dc_advertise('10.10.0.0/16', 'circuit', local_pref=200, as_path=(64510,))
    e.dc_advertise('10.10.0.0/16', 'vpn', local_pref=50,
                   as_path=(64510, 64510, 64510))
    if not summary_only:
        # The VPN device was configured from the branch template, which
        # advertises each site's /24 rather than the site summary.
        e.dc_advertise('10.10.1.0/24', 'vpn', local_pref=50,
                       as_path=(64510, 64510, 64510))
    e.cloud_advertise('10.20.0.0/16', 'vpc-hub')
    e.cloud_advertise('10.21.0.0/16', 'vpc-app')
    return e


PROBES = ['10.10.1.5', '10.10.9.5']


def analyse():
    out = {'scenarios': []}
    for label, summary_only, fail in (
            ('intended: circuit preferred, VPN standby', True, ()),
            ('circuit down: VPN carries everything', True, ('circuit',)),
            ('the mistake: VPN advertises a more-specific', False, ()),
            ('the mistake, circuit down', False, ('circuit',)),
    ):
        e = aldergate(summary_only)
        r = e.evaluate(fail)
        r['label'] = label
        r['paths'] = {}
        for p in PROBES:
            hit = lookup(r['table'], p)
            r['paths'][p] = {
                'via': hit['via'] if hit else None,
                'matched': hit['prefix'] if hit else None,
                'local_pref': hit['local_pref'] if hit else None,
            }
        out['scenarios'].append(r)

    # a fifth scenario: too many prefixes
    e = Edge(dc_asn=64510, cloud_asn=64512, accept_limit=4)
    for i in range(6):
        e.dc_advertise('10.10.%d.0/24' % i, 'circuit', local_pref=200)
    e.cloud_advertise('10.20.0.0/16', 'vpc-hub')
    r = e.evaluate()
    r['label'] = 'de-aggregated: 6 prefixes against a limit of 4'
    r['paths'] = {}
    out['scenarios'].append(r)
    return out


def report(a):
    print('Hybrid edge route exchange. Arithmetic on prefixes and attributes')
    print('you supply --- no router, no cloud account, no BGP session.\n')
    for s in a['scenarios']:
        print('--- %s' % s['label'])
        if s['failed']:
            print('    down: %s' % ', '.join(s['failed']))
        for prefix in sorted(s['table'], key=lambda p: (
                ipaddress.ip_network(p).network_address,
                ipaddress.ip_network(p).prefixlen)):
            r = s['table'][prefix]
            alt = (' (beat %s)' % ', '.join(x['via'] for x in r['rejected'])
                   if r['rejected'] else '')
            print('    best %-16s via %-8s lp=%-4g%s'
                  % (prefix, r['via'], r['local_pref'], alt))
        for probe, p in s['paths'].items():
            if p['via'] is None:
                print('    %-12s UNREACHABLE' % probe)
            else:
                print('    %-12s -> %-8s (longest match %s, lp=%g)'
                      % (probe, p['via'], p['matched'], p['local_pref']))
        for f in s['findings']:
            print('    %-8s %s' % (f['severity'].upper(), f['issue']))
        print()

    a_ok = a['scenarios'][0]['paths']['10.10.1.5']['via']
    a_bad = a['scenarios'][2]['paths']['10.10.1.5']['via']
    print('Read scenario one against scenario three. The circuit\'s '
          'local-preference')
    print('is 200 against the VPN\'s 50 in BOTH. In one, 10.10.1.5 takes the %s.'
          % a_ok)
    print('In the other it takes the %s --- because a /24 and a /16 are '
          'different' % a_bad)
    print('prefixes, they never compete for best path, and forwarding takes the')
    print('longest match. Both sessions are up. No counter moves. The only')
    print('symptom is that some traffic is mysteriously slow.')
    print('\nThe fix is a prefix-list on the VPN session that permits the '
          'summary and')
    print('nothing longer --- policy on what you ADVERTISE, not a preference on')
    print('what you receive.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        a = analyse()
    except EdgeError as e:
        print('edge error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(a, indent=2, default=str))
    else:
        report(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
