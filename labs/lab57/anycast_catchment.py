#!/usr/bin/env python3
"""Lab 57.3 --- anycast does not divide an attack equally, and withdrawal cascades.

THE CLAIM THIS REPLACES. The chapter's figure showed a botnet split one third,
one third, one third across three anycast sites, and the text concluded that "no
single site sees the whole flood" and that damage "stays regional". Both are
false in the same way: they treat a BGP catchment as though it were a geographic
partition with equal parts.

A catchment is whatever BGP policy makes it. It is set by AS path length, local
preference at every network in between, peering and transit relationships and
the attacker's own distribution --- not by distance, and not equally. Two things
follow, and this lab computes both.

  * SKEW. Real catchments are unequal, often by an order of magnitude, and a
    botnet is not uniformly distributed either. The site with the shortest path
    from the densest part of the botnet takes a share nothing in the design
    chose.
  * CASCADE. When a site is overwhelmed it withdraws --- by an operator, by a
    health check, or by simply falling over. Its share does not disappear: it
    moves to the survivors. If the survivors were already near capacity, the
    withdrawal is what kills them, and the failure runs through the estate in
    seconds. An anycast deployment that survives an attack with every site up
    can be destroyed entirely by the first withdrawal.

    python3 anycast_catchment.py
    python3 anycast_catchment.py --json
    python3 test_anycast_catchment.py
"""
import json
import sys
import math


class AnycastError(ValueError):
    pass


def _check(sites):
    if not isinstance(sites, dict) or not sites:
        raise AnycastError('sites must be a non-empty dict of '
                           'name -> {capacity_bps, share}')
    total = 0.0
    for name, s in sites.items():
        for key in ('capacity_bps', 'share'):
            if key not in s:
                raise AnycastError('site %r is missing %s' % (name, key))
            v = s[key]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
                raise AnycastError('site %r: %s must be a non-negative number, '
                                   'not %r' % (name, key, v))
        if s['capacity_bps'] == 0:
            raise AnycastError('site %r has zero capacity; a site that can carry '
                               'nothing is not a site, it is a withdrawal' % name)
        total += s['share']
    if abs(total - 1.0) > 1e-9:
        raise AnycastError('the shares sum to %.6f, not 1.0. A catchment model '
                           'whose shares do not account for all the traffic is '
                           'silently discarding some of the attack.' % total)
    return total


def load(sites, attack_bps):
    """Per-site offered load, given the catchment shares."""
    _check(sites)
    if isinstance(attack_bps, bool) or not isinstance(attack_bps, (int, float)) \
            or not math.isfinite(attack_bps) or attack_bps < 0:
        raise AnycastError('attack_bps must be a non-negative number')
    return {n: attack_bps * s['share'] for n, s in sites.items()}


def cascade(sites, attack_bps, redistribute='proportional'):
    """Withdraw every overwhelmed site, redistribute its share, and repeat.

    The redistribution policy is stated, not assumed: 'proportional' gives a
    withdrawn site's share to the survivors in proportion to their existing
    shares. This is a scenario assumption, not a consequence guaranteed by
    BGP path selection; real reassignment depends on each source and policy.
    """
    if redistribute != 'proportional':
        raise AnycastError('only the proportional policy is modelled; any other '
                           'behaviour depends on the actual AS paths and must be '
                           'measured, not assumed')
    _check(sites)
    load(sites, attack_bps)  # validate the offered rate as well as the sites
    live = {n: dict(s) for n, s in sites.items()}
    rounds, withdrawn = [], []
    while True:
        if not live:
            rounds.append(dict(round=len(rounds) + 1, live=[], loads={},
                               overwhelmed=[], note='every site has withdrawn'))
            break
        offered = {n: attack_bps * s['share'] for n, s in live.items()}
        over = [n for n in live if offered[n] > live[n]['capacity_bps']]
        rounds.append(dict(
            round=len(rounds) + 1, live=sorted(live),
            loads={n: offered[n] for n in sorted(live)},
            utilisation={n: offered[n] / live[n]['capacity_bps'] for n in sorted(live)},
            overwhelmed=sorted(over)))
        if not over:
            break
        for n in over:
            freed = live[n]['share']
            withdrawn.append(n)
            del live[n]
            rest = sum(s['share'] for s in live.values())
            if rest <= 0:
                # EVERY remaining site had a zero share, so the model has no
                # evidence about where the traffic goes next. Splitting it
                # equally is an ASSUMPTION, and it is recorded as one rather
                # than being made silently.
                rounds[-1]['assumption'] = (
                    'all surviving shares were zero, so the withdrawn share was '
                    'split equally. Real behaviour depends on the AS paths and '
                    'must be measured.')
                for s in live.values():
                    s['share'] = 1.0 / max(len(live), 1)
            else:
                for s in live.values():
                    s['share'] += freed * (s['share'] / rest)
    return dict(rounds=rounds, withdrawn=withdrawn, survivors=sorted(live),
                total_capacity_bps=sum(s['capacity_bps'] for s in sites.values()),
                attack_bps=attack_bps,
                survived=bool(live),
                note=('The estate collapsed entirely even though its total capacity '
                      'is %.3g bit/s against a %.3g bit/s attack.'
                      % (sum(s['capacity_bps'] for s in sites.values()), attack_bps))
                if not live else 'Sites still carrying traffic: %s' % ', '.join(sorted(live)))


def survival_threshold(sites, lo=0.0, hi=1e15, tol=1e6):
    """The largest attack this estate survives, found by bisection on the model."""
    _check(sites)
    if not all(math.isfinite(x) for x in (lo, hi, tol)) or lo < 0 or hi <= lo or tol <= 0:
        raise AnycastError('bisection bounds must be finite, ordered, and tolerance positive')
    if not cascade(sites, lo)['survived']:
        return 0.0
    if cascade(sites, hi)['survived']:
        raise AnycastError('the estate survives the upper bound; raise hi')
    while hi - lo > tol:
        mid = (lo + hi) / 2.0
        if cascade(sites, mid)['survived']:
            lo = mid
        else:
            hi = mid
    return lo


# Three sites of equal capacity. The shares are NOT equal, because BGP policy
# and the botnet's own distribution decided them, and nothing in the design did.
SKEWED = {
    'site-A': dict(capacity_bps=400e9, share=0.62),
    'site-B': dict(capacity_bps=400e9, share=0.27),
    'site-C': dict(capacity_bps=400e9, share=0.11),
}
EQUAL = {
    'site-A': dict(capacity_bps=400e9, share=1 / 3),
    'site-B': dict(capacity_bps=400e9, share=1 / 3),
    'site-C': dict(capacity_bps=400e9, share=1 / 3),
}
TARGETED = {
    'site-A': dict(capacity_bps=400e9, share=1.0),
    'site-B': dict(capacity_bps=400e9, share=0.0),
    'site-C': dict(capacity_bps=400e9, share=0.0),
}


def report(out=None):
    out = sys.stdout if out is None else out
    out.write('Lab 57.3 --- catchment skew and the withdrawal cascade\n')
    out.write('=' * 74 + '\n\n')
    total = sum(s['capacity_bps'] for s in SKEWED.values())
    out.write('Three sites, 400 Gb/s each: %.0f Gb/s of capacity in total.\n\n'
              % (total / 1e9))
    out.write('  %-34s %14s %s\n' % ('catchment', 'survives up to', 'which is'))
    for label, sites in (('equal thirds, as the old figure drew it', EQUAL),
                         ('measured skew 62 / 27 / 11', SKEWED),
                         ('a botnet inside one catchment', TARGETED)):
        t = survival_threshold(sites)
        out.write('  %-34s %11.0f Gb/s %6.0f%% of the estate\n'
                  % (label, t / 1e9, 100 * t / total))
    out.write('\nThe equal case is the only one that gets near the total, and it is\n')
    out.write('the one case a designer does not control.\n\n')
    out.write('THE CASCADE, STEP BY STEP\n\n')
    atk = 900e9
    out.write('A %.0f Gb/s attack against the skewed estate --- %.0f Gb/s LESS than\n'
              % (atk / 1e9, (total - atk) / 1e9))
    out.write('the estate\'s total capacity:\n\n')
    c = cascade(SKEWED, atk)
    for r in c['rounds']:
        if not r['live']:
            out.write('  round %d: %s\n' % (r['round'], r['note']))
            continue
        out.write('  round %d: ' % r['round'])
        out.write(', '.join('%s %.0f%%' % (n, 100 * r['utilisation'][n])
                            for n in r['live']))
        out.write('   -> withdraws: %s\n' % (', '.join(r['overwhelmed']) or 'none'))
    out.write('\n  The estate collapsed entirely even though its total capacity,\n')
    out.write('  %.0f Gb/s, is larger than the %.0f Gb/s attack.\n'
              % (c['total_capacity_bps'] / 1e9, c['attack_bps'] / 1e9))
    out.write('\n  Note what happened to the survivors. Site C was at 25 per cent in\n')
    out.write('  round one --- comfortable, nothing to report on a dashboard --- and\n')
    out.write('  it was killed by the withdrawal of the sites that were failing,\n')
    out.write('  not by the attack it was itself receiving. "Damage stays regional"\n')
    out.write('  is true only until the first site leaves.\n')


def main(argv):
    if '--json' in argv:
        print(json.dumps({
            'equal': cascade(EQUAL, 900e9), 'skewed': cascade(SKEWED, 900e9),
            'targeted': cascade(TARGETED, 900e9),
            'thresholds_bps': {k: survival_threshold(v) for k, v in
                               (('equal', EQUAL), ('skewed', SKEWED),
                                ('targeted', TARGETED))},
        }, indent=1))
        return 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
