#!/usr/bin/env python3
"""Lab 49.3 --- what a different medium does and does not remove.

WHY THIS LAB EXISTS
-------------------
The chapter closed the whole transport part on this claim:

    "a wireless or LEO backup to a fibre primary CANNOT be cut by the digger
     that cuts the fibre, is not in the fibre's duct, and does not share the
     fibre's regional civil failures --- so it provides diversity that a second
     fibre, however carefully routed, struggles to match."

The first three clauses are true and the conclusion does not follow from them,
which is the most dangerous shape an argument can have in a resilience chapter.
A different medium removes the failures that belong to the medium.  It removes
none of the others, and the others are where paired outages usually come from:

  the same building, and the same room in it
  the same power feed, and the same generator and battery
  the same terrestrial backhaul beyond the first hop
  the same gateway or teleport for a satellite service
  the same management system, the same credentials, the same change window
  the same provider, the same billing relationship, the same control plane
  the same weather event, at a scale that covers both
  the same people, arriving in the same van, on the same night

A backup whose radio sits on the roof of the building the fibre enters, powered
from the same board, managed by the same NMS, shares four of those before anyone
mentions the digger.  It is still worth having.  It is not the strongest
diversity there is, and calling it that is how a disaster-recovery plan gets
approved that has never been tested against the event it is for.

So this makes shared dependencies countable: describe each path by what it
actually depends on, and the model reports what the pair survives, what takes
both, and what the combination is worth against the single path.

    python3 shared_risk.py
    python3 shared_risk.py --json
    python3 test_shared_risk.py

No network, no site survey, no records and no measurement.  The dependencies and
failure rates below are invented to make the arithmetic concrete.  A real answer
comes from the actual records --- duct and route data, power single-line
diagrams, building entries, provider and gateway detail --- and is then TESTED by
failing the primary.
"""
import argparse
import json
import sys

# Failure classes, each with an illustrative annual probability.  None of these
# is a measurement; they exist so that the combination arithmetic has something
# to combine.
FAILURE_CLASSES = {
    'duct or digger': 0.15,
    'building entry': 0.02,
    'site power': 0.05,
    'terrestrial backhaul': 0.08,
    'gateway or teleport': 0.04,
    'management system': 0.03,
    'provider control plane': 0.03,
    'regional weather': 0.06,
    'change or human error': 0.10,
    'medium-specific fade': 0.12,
}


class RiskError(ValueError):
    """The described path or pair cannot be evaluated."""


def path(name, medium, depends_on):
    """A path, described by what it actually depends on.

    depends_on maps a failure class to the IDENTITY of the thing depended on.
    Two paths share a risk when they name the same identity for the same class
    --- not when they merely both have power, but when they are on the same
    board. That distinction is the whole model, and it is the one a logical
    diagram cannot show.
    """
    unknown = set(depends_on) - set(FAILURE_CLASSES)
    if unknown:
        raise RiskError('%s: unknown failure class(es) %s; known: %s'
                        % (name, ', '.join(sorted(unknown)),
                           ', '.join(sorted(FAILURE_CLASSES))))
    if not depends_on:
        raise RiskError('%s: a path with no dependencies is not a path, it is '
                        'an assumption' % name)
    return {'name': name, 'medium': medium, 'depends_on': dict(depends_on)}


def shared(a, b):
    """Failure classes where the two paths depend on the SAME thing."""
    out = {}
    for cls, ident in a['depends_on'].items():
        if b['depends_on'].get(cls) == ident:
            out[cls] = ident
    return out


def independent(a, b):
    """Failure classes each path has that the other does not share."""
    s = shared(a, b)
    return {'a_only': {k: v for k, v in a['depends_on'].items() if k not in s},
            'b_only': {k: v for k, v in b['depends_on'].items() if k not in s}}


def annual_outage_probability(p):
    """Probability this path has AT LEAST ONE outage in a year.

    Not an unavailability: it says nothing about how long the outage lasts.
    Two paths can have the same figure here and very different downtime, and a
    resilience argument needs both. This model has only the first.
    """
    up = 1.0
    for cls in p['depends_on']:
        up *= (1.0 - FAILURE_CLASSES[cls])
    return 1.0 - up


def pair_outage_probability(a, b):
    """Probability each path suffers at least one event during the year.

    This annual joint event is NOT simultaneous service loss. Independent
    events can occur months apart; their product does not supply temporal
    overlap. Shared events affect both, but no event durations, repair or
    failover actions are represented. Legacy result keys retain their names.
    Distinct cause identities are assumed independent for this calculation.
    """
    sh = shared(a, b)
    ind = independent(a, b)

    # at least one shared cause fires: takes both
    up_shared = 1.0
    for cls in sh:
        up_shared *= (1.0 - FAILURE_CLASSES[cls])
    p_shared_kills_both = 1.0 - up_shared

    # neither shared cause fires, but each path's own causes both fire
    a_own = 1.0
    for cls in ind['a_only']:
        a_own *= (1.0 - FAILURE_CLASSES[cls])
    b_own = 1.0
    for cls in ind['b_only']:
        b_own *= (1.0 - FAILURE_CLASSES[cls])
    p_both_own = (1.0 - a_own) * (1.0 - b_own)

    both = p_shared_kills_both + up_shared * p_both_own
    naive = annual_outage_probability(a) * annual_outage_probability(b)
    return {'shared_classes': sorted(sh), 'shared_count': len(sh),
            'p_shared_kills_both': p_shared_kills_both,
            'p_both_independently': up_shared * p_both_own,
            'pair_outage_probability': both,
            'naive_if_independent': naive,
            'understatement_factor': (both / naive) if naive > 0 else None,
            'a_alone': annual_outage_probability(a),
            'b_alone': annual_outage_probability(b),
            'improvement_over_a': annual_outage_probability(a) / both if both > 0 else None}


# ---------------------------------------------------------------------------
# the paths
# ---------------------------------------------------------------------------
FIBRE_A = path('fibre, north route', 'fibre', {
    'duct or digger': 'duct-north',
    'building entry': 'entry-east',
    'site power': 'board-A',
    'management system': 'nms-1',
    'provider control plane': 'provider-X',
    'change or human error': 'team-1',
    'regional weather': 'region-1',
})

FIBRE_B = path('fibre, south route', 'fibre', {
    'duct or digger': 'duct-south',
    'building entry': 'entry-east',          # SAME entry
    'site power': 'board-A',                 # SAME board
    'management system': 'nms-1',            # SAME NMS
    'provider control plane': 'provider-X',  # SAME provider
    'change or human error': 'team-1',       # SAME team
    'regional weather': 'region-1',
})

MICROWAVE_LAZY = path('microwave, roof of the same building', 'radio', {
    'building entry': 'entry-east',          # the radio comes in the same way
    'site power': 'board-A',                 # off the same board
    'management system': 'nms-1',
    'provider control plane': 'provider-X',
    'change or human error': 'team-1',
    'regional weather': 'region-1',
    'medium-specific fade': 'rain-1',
})

MICROWAVE_GOOD = path('microwave, second building, own power', 'radio', {
    'building entry': 'entry-west',
    'site power': 'board-B',
    'management system': 'nms-2',
    'provider control plane': 'provider-Y',
    'change or human error': 'team-2',
    'regional weather': 'region-1',          # weather is still shared
    'medium-specific fade': 'rain-1',
})

LEO = path('LEO satellite service', 'satellite', {
    'building entry': 'entry-west',
    'site power': 'board-B',
    'terrestrial backhaul': 'backhaul-Z',
    'gateway or teleport': 'gateway-1',
    'provider control plane': 'provider-Z',
    'change or human error': 'team-2',
    'regional weather': 'region-1',
    'medium-specific fade': 'rain-1',
})


def section_a():
    print('A. The claim, and what the records say')
    print('-' * 74)
    print('  "A wireless backup cannot be cut by the digger that cuts the')
    print('  fibre." True, and here is everything it leaves:')
    print()
    pairs = [('two fibre routes', FIBRE_A, FIBRE_B),
             ('fibre + microwave on the same roof', FIBRE_A, MICROWAVE_LAZY),
             ('fibre + microwave done properly', FIBRE_A, MICROWAVE_GOOD),
             ('fibre + LEO', FIBRE_A, LEO)]
    import textwrap
    out = []
    for label, a, b in pairs:
        r = pair_outage_probability(a, b)
        out.append((label, a, b, r))
        print('  %-40s %d shared' % (label, r['shared_count']))
        for line in textwrap.wrap(', '.join(r['shared_classes']), 62):
            print('      %s' % line)
    print()
    lazy = out[1][3]
    print('  The microwave on the same roof removes the digger and keeps %d'
          % lazy['shared_count'])
    print('  shared dependencies --- the building entry, the power board, the')
    print('  management system, the provider, the team and the weather. It is')
    print('  worth having. It is not "diversity a second fibre struggles to')
    print('  match": on this description the two fibre routes share %d and the'
          % out[0][3]['shared_count'])
    print('  lazy microwave shares %d.' % lazy['shared_count'])
    print()
    return out


def section_b(rows):
    print('B. What the pair is actually worth')
    print('-' * 74)
    print('%-38s %10s %10s %11s'
          % ('pair', 'both in year', 'if indep.', 'understated'))
    for label, a, b, r in rows:
        print('%-38s %9.4f%% %9.4f%% %10.1fx'
              % (label, 100 * r['pair_outage_probability'],
                 100 * r['naive_if_independent'], r['understatement_factor']))
    print()
    print('  Each path has AT LEAST ONE outage in the year. These joint events')
    print('  are not simultaneous outage probabilities or unavailabilities.')
    print('  Independent events can occur months apart without service loss.')
    print()
    print('  The middle column is what "we have two paths" assumes: that the')
    print('  two fail independently, so the pair\'s risk is the product. The')
    print('  left column is what the shared dependencies actually give. The')
    print('  ratio is how far the assumption is out.')
    print()
    worst = max(rows, key=lambda r: r[3]['understatement_factor'])
    best = min(rows, key=lambda r: r[3]['understatement_factor'])
    print('  Worst here: %s, understated %.1f times.'
          % (worst[0], worst[3]['understatement_factor']))
    print('  Best here:  %s, understated %.1f times --- and still not 1.0,'
          % (best[0], best[3]['understatement_factor']))
    print('  because the weather is shared and nothing about the medium changes')
    print('  that.')
    print()
    return {'worst': worst[0], 'best': best[0]}


def section_c(rows):
    print('C. Lower joint annual-event probability, not service availability')
    print('-' * 74)
    print('%-38s %12s %12s %10s'
          % ('pair', 'primary alone', 'pair', 'better by'))
    for label, a, b, r in rows:
        print('%-38s %11.3f%% %11.4f%% %9.1fx'
              % (label, 100 * r['a_alone'], 100 * r['pair_outage_probability'],
                 r['improvement_over_a']))
    print()
    print('  Every joint annual event is less probable than the primary event.')
    print('  That follows from event inclusion; it does not quantify how much')
    print('  service availability a backup buys. Add timing, duration, capacity')
    print('  and failover behaviour before predicting customer downtime.')
    print()
    print('  What it is not is protection against the classes it DOES share,')
    print('  and a plan that says "we have a diverse backup" without naming')
    print('  which classes has not said what it protects against. Both partial')
    print('  diversity and residual shared risk can be true at once.')
    print()


def section_d():
    print('D. Fixing it one dependency at a time')
    print('-' * 74)
    base = pair_outage_probability(FIBRE_A, MICROWAVE_LAZY)
    print('  Starting from the microwave on the same roof: %.4f%% chance both'
          % (100 * base['pair_outage_probability']))
    print('  see an outage in a year, %d shared classes.' % base['shared_count'])
    print()
    print('%-30s %12s %10s' % ('separate this', 'both in year', 'reduction'))
    fixes = [('site power', 'board-B'),
             ('building entry', 'entry-west'),
             ('management system', 'nms-2'),
             ('provider control plane', 'provider-Y'),
             ('change or human error', 'team-2'),
             ('regional weather', 'region-2')]
    cur = dict(MICROWAVE_LAZY['depends_on'])
    out = []
    for cls, new in fixes:
        trial = dict(cur)
        trial[cls] = new
        p = path('trial', 'radio', trial)
        r = pair_outage_probability(FIBRE_A, p)
        out.append((cls, r['pair_outage_probability']))
        print('%-30s %11.4f%% %9.2fx'
              % (cls, 100 * r['pair_outage_probability'],
                 base['pair_outage_probability'] / r['pair_outage_probability']))
    print()
    best = min(out, key=lambda x: x[1])
    print('  The single most valuable separation here is %s.' % best[0])
    print('  Which one it is for YOUR pair depends on your own dependency list')
    print('  and your own failure rates, and that is exactly why the list has')
    print('  to exist. A medium is one row of it.')
    print()
    print('  And note the last row: separating the weather means a site far')
    print('  enough away to be under different weather, which is a different')
    print('  and much more expensive decision than moving a power feed. The')
    print('  model does not price that change or calculate its downtime benefit.')
    print()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    if args.json:
        json.dump({'classes': FAILURE_CLASSES,
                   'pairs': {n: pair_outage_probability(a, b) for n, a, b in
                             (('fibre+fibre', FIBRE_A, FIBRE_B),
                              ('fibre+microwave-lazy', FIBRE_A, MICROWAVE_LAZY),
                              ('fibre+microwave-good', FIBRE_A, MICROWAVE_GOOD),
                              ('fibre+leo', FIBRE_A, LEO))}},
                  sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write('\n')
        return 0
    print('Shared risk between two paths (Chapter 49)')
    print('Dependencies and failure rates are invented. The method is the point.')
    print()
    rows = section_a()
    section_b(rows)
    section_c(rows)
    section_d()
    print('What this does NOT establish')
    print('-' * 74)
    print('- No survey, no records, no measurement. Every dependency and every')
    print('  failure rate is an invented input, and the absolute percentages')
    print('  mean nothing outside this script.')
    print('- The classes are a starting list, not a complete one. Shared')
    print('  software, shared spares, shared contracts, shared staff on call')
    print('  and shared upstream transit are all missing.')
    print('- Failure classes are treated as independent of each other when they')
    print('  are not: a storm causes power failures and human error at once.')
    print('- These are outage PROBABILITIES, not unavailabilities. Duration is')
    print('  absent, and two pairs with the same figure can differ entirely in')
    print('  how long the outages last.')
    print('- A dependency list is a claim about records. It is worth what the')
    print('  records are worth, and the records are often wrong --- which is why')
    print('  failing the primary tests only that injected failure, not every risk.')
    print('- Nothing here approves a design. It makes the shared dependencies')
    print('  countable so that a resilience claim can name what it protects.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
