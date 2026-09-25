#!/usr/bin/env python3
"""Lab 38.1 --- the SONiC control-to-forwarding evidence chain, as a checklist.

WHAT THIS IS. A model of the stages a LEARNED BGP route passes through on its
way to the silicon, and the command that gives you evidence at each stage. It
generates a diagnostic checklist and works out what a stop at each stage does
and does not tell you. It is a study aid for the method, run on your laptop.

WHAT THIS IS NOT. It is not a SONiC switch, it does not connect to one, and it
proves nothing about any device. Nothing in this book has been run on SONiC:
this environment has no Docker daemon, so neither the virtual switch nor
Containerlab was available. Take the stage names and Redis layout as a starting
point to verify against your own image, not as gospel --- both vary by release.

WHY IT WAS REWRITTEN. The previous version modelled the chain as
CONFIG_DB -> APPL_DB -> ASIC_DB -> STATE_DB and said a route missing from
CONFIG_DB meant "you never configured it". That is wrong for the case the lab
was about. A route LEARNED from BGP is never expected in CONFIG_DB --- CONFIG_DB
holds intended configuration, so it would hold a static route or the BGP session
you configured, not a prefix a neighbour sent you. It also treated STATE_DB as
the chip's acknowledgement, which it is not: STATE_DB carries operational state
such as port, link, neighbour and transceiver status, not a per-route hardware
receipt. An engineer following the old checklist would start by looking for a
prerequisite that does not exist, and finish by reading a confirmation that is
not there.

    python3 dbwalk.py [--static] [--json]
"""
import argparse
import json
import sys


# Each stage: what it is, the evidence command, and --- the part that matters ---
# what a stop here rules IN and what it does NOT establish.
LEARNED_ROUTE_CHAIN = [
    {
        'stage': 'bgpd RIB',
        'where': 'the bgp container, via vtysh',
        'evidence': "vtysh -c 'show bgp ipv4 unicast <prefix>'",
        'present_means': 'the neighbour sent it and import policy accepted it',
        'absent_means': ('the session is down, the neighbour never sent it, or '
                         'inbound policy dropped it'),
        'does_not_establish': 'that it was selected as best, or that zebra has it',
    },
    {
        'stage': 'bgpd best path',
        'where': 'the bgp container, via vtysh',
        'evidence': "vtysh -c 'show bgp ipv4 unicast <prefix>' (look for the best marker)",
        'present_means': 'BGP selected this path and will offer it to zebra',
        'absent_means': 'another path won, or the next hop did not resolve',
        'does_not_establish': 'anything about the kernel or the ASIC',
    },
    {
        'stage': 'zebra RIB and next-hop resolution',
        'where': 'the bgp container, via vtysh',
        'evidence': "vtysh -c 'show ip route <prefix>'",
        'present_means': 'zebra selected the route and resolved its next hop',
        'absent_means': ('the next hop is unresolved, or another protocol won on '
                         'administrative distance'),
        'does_not_establish': ('THAT THE ASIC HAS IT. This is the software RIB. '
                               'Treating it as hardware proof is the single most '
                               'common mistake in this chain'),
    },
    {
        'stage': 'APPL_DB ROUTE_TABLE',
        'where': 'the database container, Redis',
        'evidence': 'redis-cli -n <APPL_DB> keys "ROUTE_TABLE:<prefix>*"',
        'present_means': 'the FPM path and fpmsyncd delivered the route to SONiC',
        'absent_means': ('fpmsyncd is not running, the FPM connection is down, or '
                         'the route was filtered on the way in'),
        'does_not_establish': 'that orchagent has acted on it',
    },
    {
        'stage': 'ASIC_DB route entry',
        'where': 'the database container, Redis',
        'evidence': ('redis-cli -n <ASIC_DB> keys '
                     '"ASIC_STATE:SAI_OBJECT_TYPE_ROUTE_ENTRY:*"'),
        'present_means': 'orchagent created the SAI object and asked for it to be programmed',
        'absent_means': ('orchagent rejected it --- commonly an unresolved or '
                         'missing next-hop object, or a dependency not yet created'),
        'does_not_establish': ('that syncd programmed it successfully. ASIC_DB is '
                               'the REQUEST, not the receipt'),
    },
    {
        'stage': 'syncd and SAI programming status',
        'where': 'the syncd container: logs and counters',
        'evidence': ('the syncd log and syslog for SAI failures on that object; '
                     'the vendor SAI debug tooling for the image you run'),
        'present_means': 'no SAI error was raised for the object',
        'absent_means': ('a SAI call failed --- resource exhaustion, an unsupported '
                         'attribute, or a driver fault'),
        'does_not_establish': ('that traffic follows the route. Only traffic '
                               'establishes that'),
    },
    {
        'stage': 'forwarding',
        'where': 'the data plane',
        'evidence': 'send traffic and count it at both ends',
        'present_means': 'the route is in use',
        'absent_means': 'something below or beside this chain is wrong',
        'does_not_establish': 'that it will still hold at scale or under load',
    },
]

STATIC_ROUTE_PREFIX = [
    {
        'stage': 'CONFIG_DB',
        'where': 'the database container, Redis',
        'evidence': 'redis-cli -n <CONFIG_DB> keys "STATIC_ROUTE*"',
        'present_means': 'the intended configuration contains this route',
        'absent_means': 'you did not configure it, or it did not persist',
        'does_not_establish': 'that anything downstream accepted it',
    },
]

NOT_IN_THE_CHAIN = {
    'STATE_DB': ('Operational state --- ports, links, neighbours, transceivers, '
                 'and per-feature status. It is genuinely useful, and it is NOT a '
                 'per-route acknowledgement from the ASIC. Do not end a route '
                 'investigation here.'),
    'COUNTERS_DB': ('Per-port and per-queue counters. Where telemetry reads, and '
                    'where you look for drops once the route is programmed.'),
}


def chain(static=False):
    return (STATIC_ROUTE_PREFIX if static else []) + LEARNED_ROUTE_CHAIN


def checklist(static=False):
    kind = 'static' if static else 'learned BGP'
    out = {'route_kind': kind, 'stages': chain(static),
           'not_in_the_chain': NOT_IN_THE_CHAIN,
           'scope': ('A model of the evidence chain and the commands that supply '
                     'it. No device was contacted. Redis database numbers are read '
                     'from database_config.json on the switch, not assumed.'),
           'caveats': [
               'A learned route is NOT expected in CONFIG_DB.',
               'zebra\'s "show ip route" is the software RIB, not hardware proof.',
               'ASIC_DB holds the request; syncd and SAI hold the outcome.',
               'STATE_DB is not a per-route hardware receipt.',
               'Stage names, database numbers and tooling vary by SONiC release '
               'and distribution: verify against the image you run.',
               'A virtual switch does not reproduce a physical ASIC\'s table '
               'capacity, buffering or SAI resource limits. Do not stage a '
               'capacity-exhaustion exercise on one and call the result silicon '
               'behaviour.']}
    return out


def report(static=False):
    c = checklist(static)
    print('SONiC evidence chain for a %s route\n' % c['route_kind'].upper())
    for i, s in enumerate(c['stages'], 1):
        print('%d. %s  (%s)' % (i, s['stage'], s['where']))
        print('     evidence : %s' % s['evidence'])
        print('     present  : %s' % s['present_means'])
        print('     absent   : %s' % s['absent_means'])
        print('     does NOT : %s\n' % s['does_not_establish'])
    print('Present in SONiC, but NOT stages of this chain:')
    for k, v in c['not_in_the_chain'].items():
        print('  %-12s %s' % (k, v))
    print('\nCaveats:')
    for x in c['caveats']:
        print('  - ' + x)
    print('\n' + c['scope'])
    return c


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--static', action='store_true',
                   help='show the chain for a statically configured route instead')
    p.add_argument('--json', action='store_true', help='print the checklist as JSON')
    a = p.parse_args(argv)
    c = report(a.static)
    if a.json:
        print(json.dumps(c, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except BrokenPipeError:
        # Readers will pipe this into head; exit quietly rather than spewing a
        # traceback that looks like a fault in the lab.
        try:
            sys.stdout.close()
        finally:
            sys.exit(0)
