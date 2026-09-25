#!/usr/bin/env python3
"""Lab 64.3 --- where a correct control plane still drops your packet.

Chapter 64 used to say that the data plane "only ever does what the control
plane told it to", and therefore that a data-plane symptom "almost always has
a control-plane explanation". The first half is a universal claim, so one
counterexample settles it. This lab builds six, by simulating the stages a
packet actually passes through on its way out of a router:

    route  ->  next-hop resolution  ->  forwarding entry  ->  rewrite
           ->  hardware table  ->  egress treatment  ->  the wire

A control-plane read sees the first two. Everything after them is programmed
state and silicon, and each stage can be wrong on its own while every reading
you can take from the control plane comes back clean.

That does NOT make "check the control plane first" bad advice. It makes it
advice with a scope. The second half of this lab times three different check
orderings against the same fault distribution and shows which symptom each
ordering wins and loses on, so the ordering can be chosen rather than
recited.

    python3 control_vs_data_plane.py
    python3 control_vs_data_plane.py --demo-original
    python3 test_control_vs_data_plane.py

Offline simulation of a stated model, in closed form apart from an exhaustive
enumeration over flow hashes. No device was queried and no NOS was executed:
the pipeline below is a teaching model of forwarding, not a vendor's.
"""
import itertools
import sys
import zlib


class PipelineError(ValueError):
    """Raised when a device state could not exist on real equipment."""


# ---------------------------------------------------------------------------
# The stages, in order, and which of them a control-plane read can see
# ---------------------------------------------------------------------------

STAGES = (
    ('route',
     'a route to the destination exists, learned or configured',
     True),
    ('resolution',
     'its next hop resolves, recursively, to something reachable',
     True),
    ('fib',
     'the resolved result is programmed as a forwarding entry',
     False),
    ('rewrite',
     'the layer-2 rewrite for that next hop is present and correct',
     False),
    ('hardware',
     'the forwarding entry fits in, and is live in, the forwarding silicon',
     False),
    ('egress',
     'the egress port accepts the packet: filters, size, queues, optics',
     False),
)

CONTROL_PLANE_VISIBLE = tuple(name for name, _, seen in STAGES if seen)
BEYOND_CONTROL_PLANE = tuple(name for name, _, seen in STAGES if not seen)


def healthy_device(members=4, egress_mtu=1500):
    """A device on which everything is right. Faults are edits to this."""
    return dict(
        route=True,             # the RIB has the prefix
        resolution=True,        # its next hop resolves
        fib=True,               # the result reached the forwarding table
        rewrite=True,           # the adjacency is present and correct
        hardware=True,          # and it is live in silicon
        hardware_broken_member=None,   # or the index of one dead bundle member
        egress_filter=None,     # or a predicate on the flow
        egress_mtu=egress_mtu,  # the largest packet the egress will carry
        egress_error_rate=0.0,  # sustained corruption on the egress optic
        members=members,        # bundle or equal-cost members
    )


def _check_members(device):
    m = device['members']
    if isinstance(m, bool) or not isinstance(m, int) or m < 1:
        raise PipelineError('a device must have at least one egress member')
    broken = device['hardware_broken_member']
    if broken is not None and not (0 <= broken < m):
        raise PipelineError(f'member {broken} does not exist on a device with '
                            f'{m} members')
    return m


def member_for(flow, members):
    """Which member this flow lands on.

    A checksum, not Python's hash(): hash() is salted per process, so a lab
    whose numbers change between runs would be measuring the interpreter.
    """
    key = '|'.join(str(flow[f]) for f in ('src', 'dst', 'sport', 'dport'))
    return zlib.crc32(key.encode('utf-8')) % members


def forward(device, flow, size=1400):
    """Push one packet through the model. Returns (delivered, stage, why)."""
    members = _check_members(device)
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise PipelineError('a packet has a positive whole size in bytes')

    if not device['route']:
        return False, 'route', 'no route to the destination'
    if not device['resolution']:
        return False, 'resolution', 'the next hop does not resolve'
    if not device['fib']:
        return False, 'fib', ('the route never reached the forwarding table, '
                              'though it is in the routing table')
    if not device['rewrite']:
        return False, 'rewrite', ('no usable layer-2 rewrite for a next hop '
                                  'the control plane considers reachable')
    if not device['hardware']:
        return False, 'hardware', ('the entry did not fit in, or is not live '
                                   'in, the forwarding silicon')

    member = member_for(flow, members)
    if device['hardware_broken_member'] == member:
        return False, 'hardware', (f'this flow hashes to member {member}, '
                                   f'which is not forwarding')

    if device['egress_filter'] is not None and device['egress_filter'](flow):
        return False, 'egress', 'an egress filter matches this flow'
    if size > device['egress_mtu']:
        return False, 'egress', (f'{size} bytes will not fit the egress MTU '
                                 f'of {device["egress_mtu"]}')
    return True, None, 'delivered'


def control_plane_reads_clean(device):
    """Everything a control-plane read can tell you, and nothing it cannot."""
    return all(device[name] for name in CONTROL_PLANE_VISIBLE)


# ---------------------------------------------------------------------------
# Six devices whose control plane is perfect and whose traffic fails
# ---------------------------------------------------------------------------

def _match_one_host(flow):
    return flow['src'] == '10.20.30.44'


def counterexamples():
    """One per stage the control plane cannot see. Each is constructed, run
    and checked, not asserted."""
    flow = dict(src='10.20.30.44', dst='192.0.2.9', sport=51344, dport=443)
    other = dict(src='10.20.30.45', dst='192.0.2.9', sport=51344, dport=443)
    cases = []

    d = healthy_device(); d['fib'] = False
    cases.append(('the route is in the routing table and not in the '
                  'forwarding table',
                  d, flow, 1400,
                  'a programming failure, a resource exhaustion, or a route '
                  'that lost a race with a churn event'))

    d = healthy_device(); d['rewrite'] = False
    cases.append(('the next hop is reachable and has no usable rewrite',
                  d, flow, 1400,
                  'the neighbour entry expired, or points at a MAC that has '
                  'moved, while the routing protocol adjacency stays up'))

    d = healthy_device(); d['hardware'] = False
    cases.append(('the entry is programmed and the silicon is not carrying it',
                  d, flow, 1400,
                  'the hardware table is full, or the entry failed to install '
                  'below the level the routing table reports'))

    d = healthy_device(members=4); d['hardware_broken_member'] = \
        member_for(flow, 4)
    cases.append(('every path is up and one member of the bundle is dead',
                  d, flow, 1400,
                  'the flows that hash to that member fail and the rest do '
                  'not, so any test using a different flow passes'))

    d = healthy_device(); d['egress_filter'] = _match_one_host
    cases.append(('the route is perfect and a filter matches one source',
                  d, flow, 1400,
                  'one address is denied in the core, which presents as a '
                  'single user with a broken desk'))

    d = healthy_device(egress_mtu=1400)
    cases.append(('the path is correct and the packet is too big for it',
                  d, flow, 1500,
                  'a tunnel or a mismatched link reduced the usable size; '
                  'small packets pass and real transfers stall'))

    results = []
    for title, device, f, size, note in cases:
        clean = control_plane_reads_clean(device)
        delivered, stage, why = forward(device, f, size)
        results.append(dict(title=title, control_plane_clean=clean,
                            delivered=delivered, stage=stage, why=why,
                            note=note, device=device, flow=f, size=size,
                            other=other))
    return results


def ecmp_blind_spot(members=8, trials=4096):
    """How often a single probe misses one dead member of a bundle.

    Enumerated over flows rather than sampled, so this is a count and not an
    estimate.
    """
    device = healthy_device(members=members)
    device['hardware_broken_member'] = 0
    hit = 0
    for i in range(trials):
        f = dict(src='10.20.30.44', dst='192.0.2.9', sport=30000 + i,
                 dport=443)
        delivered, _, _ = forward(device, f)
        hit += 0 if delivered else 1
    return dict(members=members, trials=trials, failing_flows=hit,
                failing_fraction=hit / trials,
                one_probe_looks_healthy=1.0 - hit / trials)


# ---------------------------------------------------------------------------
# What a control-plane-only check can and cannot see
# ---------------------------------------------------------------------------

# Illustrative weights for where a forwarding failure actually sits, stated
# here and swept in sensitivity(). They are not a survey.
FAULT_WEIGHTS = {
    'route':      0.30,
    'resolution': 0.16,
    'fib':        0.07,
    'rewrite':    0.09,
    'hardware':   0.12,
    'egress':     0.26,
}


def control_plane_coverage(weights=None):
    """The share of failures a control-plane read can even reach."""
    weights = dict(weights or FAULT_WEIGHTS)
    missing = set(w for w, _, _ in STAGES) - set(weights)
    if missing:
        raise PipelineError(f'no weight given for: {sorted(missing)}')
    total = sum(weights.values())
    if total <= 0:
        raise PipelineError('the weights must sum to something positive')
    seen = sum(weights[name] for name in CONTROL_PLANE_VISIBLE) / total
    unseen = 1.0 - seen
    beyond = {name: weights[name] / total / unseen
              for name in BEYOND_CONTROL_PLANE} if unseen > 0 else {}
    return dict(visible=seen, invisible=unseen, given_clean=beyond)


# ---------------------------------------------------------------------------
# Ordering the checks: three policies, timed against the same faults
# ---------------------------------------------------------------------------

# minutes to run, and the stages it can localise
CHECKS = {
    'read the routing table':      (2.0, ('route',)),
    'follow the next-hop resolution': (3.0, ('resolution',)),
    'compare the forwarding entry with the route': (4.0, ('fib',)),
    'read the rewrite for that next hop': (3.0, ('rewrite',)),
    'read the hardware table state and install errors': (6.0, ('hardware',)),
    'read the egress port: filters, drops, errors, size': (3.0, ('egress',)),
}

CONTROL_PLANE_FIRST = (
    'read the routing table',
    'follow the next-hop resolution',
    'compare the forwarding entry with the route',
    'read the rewrite for that next hop',
    'read the hardware table state and install errors',
    'read the egress port: filters, drops, errors, size',
)

EGRESS_FIRST = tuple(reversed(CONTROL_PLANE_FIRST))

# What the desk actually tells you, and where it puts its money.
SYMPTOMS = {
    'nothing reaches this prefix from anywhere': {
        'route': 0.52, 'resolution': 0.26, 'fib': 0.07, 'rewrite': 0.07,
        'hardware': 0.04, 'egress': 0.04},
    'the port shows errors and the light is flapping': {
        'route': 0.02, 'resolution': 0.02, 'fib': 0.02, 'rewrite': 0.04,
        'hardware': 0.10, 'egress': 0.80},
    'small packets pass and large ones do not': {
        'route': 0.01, 'resolution': 0.01, 'fib': 0.02, 'rewrite': 0.02,
        'hardware': 0.09, 'egress': 0.85},
    'some flows to this prefix work and others do not': {
        'route': 0.02, 'resolution': 0.04, 'fib': 0.08, 'rewrite': 0.10,
        'hardware': 0.46, 'egress': 0.30},
}


def expected_minutes(order, weights):
    """Time to reach the stage that is actually broken, following `order`."""
    unknown = set(order) - set(CHECKS)
    if unknown:
        raise PipelineError(f'no such check: {sorted(unknown)}')
    total = sum(weights.values())
    if total <= 0:
        raise PipelineError('the weights must sum to something positive')
    elapsed = 0.0
    expected = 0.0
    found = 0.0
    for name in order:
        cost, covers = CHECKS[name]
        elapsed += cost
        share = sum(weights.get(stage, 0.0) for stage in covers) / total
        expected += share * elapsed
        found += share
    if found < 0.999:
        # A policy that cannot find every fault must be charged for the ones
        # it misses, not quietly credited with finding them free.
        expected += (1.0 - found) * elapsed
    return expected


def symptom_directed(weights):
    """Cheapest-first by minutes per unit of probability. No fixed order."""
    total = sum(weights.values())
    scored = sorted(
        CHECKS,
        key=lambda name: (CHECKS[name][0]
                          / max(sum(weights.get(s, 0.0)
                                    for s in CHECKS[name][1]) / total, 1e-9),
                          name))
    return tuple(scored)


def best_possible(weights):
    """The cheapest of all 720 orderings, found by exhaustion.

    Ordering by cost divided by probability is the classic answer to this
    shape of problem, but an argument this lab is making about unchecked
    reasoning had better check its own.
    """
    orders = itertools.permutations(CHECKS)
    return min((expected_minutes(o, weights), o) for o in orders)


def policy_comparison():
    rows = []
    for symptom, weights in SYMPTOMS.items():
        directed = symptom_directed(weights)
        best_cost, best_order = best_possible(weights)
        rows.append(dict(
            symptom=symptom,
            control_first=expected_minutes(CONTROL_PLANE_FIRST, weights),
            egress_first=expected_minutes(EGRESS_FIRST, weights),
            directed=expected_minutes(directed, weights),
            directed_order=directed,
            best=best_cost, best_order=best_order))
    return rows


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

def prove_the_claims():
    out = []

    cases = counterexamples()
    all_clean = all(c['control_plane_clean'] for c in cases)
    all_fail = all(not c['delivered'] for c in cases)
    out.append(('a correct control plane does not guarantee forwarding',
                all_clean and all_fail,
                f'{len(cases)} constructed devices read clean on every '
                f'control-plane stage and drop the packet anyway'))

    stages_hit = {c['stage'] for c in cases}
    out.append(('every stage the control plane cannot see can fail alone',
                stages_hit == set(BEYOND_CONTROL_PLANE),
                f'drops occurred at {sorted(stages_hit)}, which is every '
                f'stage beyond the control plane'))

    good = healthy_device()
    delivered, stage, _ = forward(good, dict(src='a', dst='b', sport=1,
                                             dport=2))
    out.append(('and the model does deliver when nothing is wrong',
                delivered and stage is None,
                'the healthy device forwards'))

    ecmp = ecmp_blind_spot(members=8)
    expected = 1.0 / 8
    out.append(('one dead member of eight hides from seven flows in eight',
                abs(ecmp['failing_fraction'] - expected) < 0.02,
                f'{ecmp["failing_flows"]} of {ecmp["trials"]} enumerated flows '
                f'fail ({ecmp["failing_fraction"]:.1%}); a single probe looks '
                f'healthy {ecmp["one_probe_looks_healthy"]:.1%} of the time'))

    cov = control_plane_coverage()
    out.append(('a control-plane read reaches under half the stated failure '
                'weight',
                cov['visible'] < 0.5
                and abs(cov['visible'] + cov['invisible'] - 1.0) < 1e-12,
                f'{cov["visible"]:.1%} of the stated weight is visible, '
                f'{cov["invisible"]:.1%} is not'))
    out.append(('and no weighting in the sweep gets it to "almost always"',
                all(v < 0.9 for _, v, _ in sensitivity()),
                f'the highest coverage reached is '
                f'{max(v for _, v, _ in sensitivity()):.1%}, at a prior that '
                f'assumes four faults in five are simply a missing route'))

    rows = policy_comparison()
    out.append(('ordering by cost over probability really is the cheapest '
                'order available',
                all(abs(r['directed'] - r['best']) < 1e-9 for r in rows),
                f'it matches the best of all 720 orderings on all '
                f'{len(rows)} symptoms, checked by exhaustion'))

    near = [r for r in rows if r['control_first'] - r['best'] < 1.0]
    far = [r for r in rows if r['control_first'] - r['best'] >= 5.0]
    out.append(('control-plane-first is within a minute of optimal when the '
                'symptom points at the control plane',
                len(near) >= 1,
                '; '.join(f'"{r["symptom"]}" costs {r["control_first"]:.1f} '
                          f'min against the best {r["best"]:.1f}'
                          for r in near)))
    out.append(('and costs five minutes or more when it does not',
                len(far) >= 1,
                '; '.join(f'"{r["symptom"]}" {r["control_first"]:.1f} against '
                          f'{r["best"]:.1f}' for r in far)))

    # A model that could not produce a delivered packet would prove nothing.
    size_ok, _, _ = forward(healthy_device(egress_mtu=1400),
                            dict(src='a', dst='b', sport=1, dport=2), 1400)
    size_bad, stage_bad, _ = forward(healthy_device(egress_mtu=1400),
                                     dict(src='a', dst='b', sport=1, dport=2),
                                     1401)
    out.append(('the size boundary is where it is said to be, not one either '
                'side',
                size_ok and not size_bad and stage_bad == 'egress',
                '1400 passes and 1401 does not on a 1400-byte egress'))

    refused = False
    try:
        forward(healthy_device(), dict(src='a', dst='b', sport=1, dport=2),
                size=0)
    except PipelineError:
        refused = True
    out.append(('an impossible packet is refused rather than forwarded',
                refused, 'a zero-byte packet raises PipelineError'))
    return out


def sensitivity(steps=7):
    """How much of the coverage result depends on the weights stated above."""
    rows = []
    for i in range(steps):
        share = 0.05 + i * (0.80 - 0.05) / (steps - 1)
        w = dict(FAULT_WEIGHTS)
        rest = 1.0 - share
        others = {k: v for k, v in w.items() if k != 'route'}
        scale = rest / sum(others.values())
        w = {k: v * scale for k, v in others.items()}
        w['route'] = share
        cov = control_plane_coverage(w)
        rows.append((share, cov['visible'], cov['invisible']))
    return rows


# ---------------------------------------------------------------------------
# What the chapter used to say
# ---------------------------------------------------------------------------

def demo_original(out=print):
    out('WHAT THE CHAPTER USED TO CLAIM, AND WHAT IT COSTS YOU')
    out('')
    out('  "The data plane only ever does what the control plane told it to,')
    out('   so a data-plane symptom almost always has a control-plane')
    out('   explanation."')
    out('')
    out('  The first clause is a universal. Here are the devices that refute')
    out('  it --- every one of them reads clean on every control-plane stage:')
    out('')
    for case in counterexamples():
        out(f'    {case["title"]}')
        out(f'      control plane reads clean: {case["control_plane_clean"]}; '
            f'packet delivered: {case["delivered"]}')
        out(f'      dropped at: {case["stage"]} --- {case["why"]}')
        out('')
    cov = control_plane_coverage()
    reach = max(v for _, v, _ in sensitivity())
    out('  The second clause is a frequency claim, and it needs numbers. On')
    out(f'  the weights stated in this file, {cov["visible"]:.0%} of forwarding '
        f'failures are visible')
    out(f'  to a control-plane read and {cov["invisible"]:.0%} are not. Even '
        f'assuming four faults')
    out(f'  in five are simply a missing route, coverage only reaches '
        f'{reach:.0%}. So')
    out('  "often" is fair, "almost always" is not on any weighting tried')
    out('  here, and the remainder is precisely the set of faults that waste')
    out('  a whole afternoon.')
    out('')
    out('  The advice that survives: read the control plane first when the')
    out('  symptom points there. The advice that does not: read it first')
    out('  always, including on a port that is telling you it has errors.')


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def report(out=print, original=False):
    if original:
        demo_original(out)
        return 0

    out('=' * 74)
    out('LAB 64.3 --- WHERE A CORRECT CONTROL PLANE STILL DROPS YOUR PACKET')
    out('=' * 74)
    out('')
    out('THE STAGES A PACKET PASSES, AND WHAT YOU CAN READ')
    out('-' * 49)
    for name, description, seen in STAGES:
        mark = 'control plane' if seen else 'programmed state or silicon'
        out(f'  {name:11s} {description}')
        out(f'              [{mark}]')
    out('')
    out(f'  A control-plane read covers {len(CONTROL_PLANE_VISIBLE)} of '
        f'{len(STAGES)} stages: '
        f'{", ".join(CONTROL_PLANE_VISIBLE)}.')
    out(f'  It cannot reach {", ".join(BEYOND_CONTROL_PLANE)}.')
    out('')

    out('SIX DEVICES WHOSE CONTROL PLANE IS PERFECT AND WHOSE TRAFFIC FAILS')
    out('-' * 66)
    for case in counterexamples():
        out(f'  {case["title"]}')
        out(f'      control plane clean: {str(case["control_plane_clean"]):5s} '
            f'delivered: {str(case["delivered"]):5s} '
            f'dropped at: {case["stage"]}')
        out(f'      {case["why"]}')
        out(f'      in practice: {case["note"]}')
        out('')
    out('  Each of those is one device, constructed and run, not a story. The')
    out('  claim being refuted was a universal, so six is five more than the')
    out('  argument needed.')
    out('')

    ecmp = ecmp_blind_spot(members=8)
    out('WHY THE PROBE THAT PASSED PROVED LESS THAN YOU THINK')
    out('-' * 51)
    out(f'  One member of {ecmp["members"]} is dead. Enumerating '
        f'{ecmp["trials"]} flows across the bundle,')
    out(f'  {ecmp["failing_flows"]} fail --- {ecmp["failing_fraction"]:.1%}. '
        f'A single probe therefore comes back')
    out(f'  healthy {ecmp["one_probe_looks_healthy"]:.1%} of the time, and '
        f'reports a bundle with a dead')
    out('  member as a bundle that is fine. The control plane, meanwhile,')
    out('  shows every path up, because every path is up.')
    out('')

    cov = control_plane_coverage()
    out('HOW MUCH OF THE FAILURE SPACE A CONTROL-PLANE READ REACHES')
    out('-' * 58)
    out(f'  On the weights stated in this file: {cov["visible"]:.1%} visible, '
        f'{cov["invisible"]:.1%} not.')
    out('')
    out('  And when the control plane does read clean, what is left is not')
    out('  evenly spread. Conditional on a clean control plane, the fault is:')
    for stage, share in sorted(cov['given_clean'].items(),
                               key=lambda kv: -kv[1]):
        description = next(d for n, d, _ in STAGES if n == stage)
        out(f'      {share:6.1%}  {stage:10s} {description}')
    out('')

    out('THREE ORDERINGS, TIMED AGAINST THE SAME FAULTS')
    out('-' * 46)
    out('  Expected minutes to reach the broken stage, by symptom:')
    out('')
    out(f'  {"symptom":48s} {"ctrl-1st":>9s} {"egress-1st":>11s} '
        f'{"directed":>9s} {"best":>6s}')
    rows = policy_comparison()
    for row in rows:
        out(f'  {row["symptom"]:48s} {row["control_first"]:>9.1f} '
            f'{row["egress_first"]:>11.1f} {row["directed"]:>9.1f} '
            f'{row["best"]:>6.1f}')
    out('')
    out('  The last column is the cheapest of all 720 orderings, found by')
    out('  trying all 720. The directed order matches it everywhere, which is')
    out('  what a cost-over-probability ordering is supposed to do and is')
    out('  checked here rather than assumed.')
    out('')
    worst = max(rows, key=lambda r: r['control_first'] - r['best'])
    best = min(rows, key=lambda r: r['control_first'] - r['best'])
    out(f'  Control-plane-first costs {best["control_first"]:.1f} minutes on '
        f'"{best["symptom"]}"')
    out(f'  against the best available {best["best"]:.1f} --- '
        f'{best["control_first"] - best["best"]:.1f} of a minute wasted, '
        f'which is nothing.')
    out('  When the symptom points at the routing table, the fixed order is')
    out('  as good as thinking about it.')
    out('')
    out(f'  On "{worst["symptom"]}" it costs')
    out(f'  {worst["control_first"]:.1f} minutes against '
        f'{worst["best"]:.1f}: {worst["control_first"] - worst["best"]:.1f} '
        f'minutes spent reading a routing')
    out('  table that the symptom had already exonerated. The order that')
    out('  symptom deserves begins:')
    for name in worst['directed_order'][:2]:
        out(f'      {name} ({CHECKS[name][0]:.0f} min)')
    out('')

    out('DOES THE COVERAGE RESULT SURVIVE CHANGING THE WEIGHTS?')
    out('-' * 53)
    out('    weight on "no route"   visible to control plane   invisible')
    for share, visible, invisible in sensitivity():
        out(f'    {share:>18.0%}   {visible:>22.1%}   {invisible:>9.1%}')
    out('')
    out('  The share the control plane can see rises with how often the')
    out('  fault is simply a missing route, which is exactly as it should be.')
    out('  What does not change is that the rest of the space stays non-empty')
    out('  at every weight, because the six devices above exist whatever you')
    out('  believe about frequencies.')
    out('')

    out('CONTROLS')
    out('-' * 8)
    failed = 0
    for claim, ok, detail in prove_the_claims():
        out(f'  [{"ok" if ok else "FAIL"}] {claim}')
        out(f'         {detail}')
        failed += 0 if ok else 1
    out('')
    out(f'  {failed} failed.')
    out('')
    out('WHAT TO TAKE FROM THIS')
    out('-' * 22)
    cov = control_plane_coverage()
    out('  Ask the network what it believes. It is the cheapest read you can')
    out(f'  take and on these weights it names the fault {cov["visible"]:.0%} '
        f'of the time,')
    out('  which is why it belongs near the front. Then remember that you')
    out('  have read two stages out of six, and that a clean control plane is')
    out('  a result, not an all-clear.')
    out('  Compare what is routed with what is programmed, what is programmed')
    out('  with what the hardware holds, and what the hardware holds with')
    out('  what the egress port is actually doing. And when the symptom')
    out('  points at a port with errors on it, start at the port.')
    return failed


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    original = '--demo-original' in argv
    for arg in argv:
        if arg != '--demo-original':
            raise SystemExit(f'unrecognised argument: {arg}')
    return 0 if not report(original=original) else 1


if __name__ == '__main__':
    raise SystemExit(main())
