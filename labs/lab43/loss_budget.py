#!/usr/bin/env python3
"""Lab 43.1 --- a design budget, not a typical one.

WHY THIS VERSION EXISTS
-----------------------
The previous script multiplied a span's length, splice count and connector count
by the chapter's "typical" figures and printed a total.  Every number in it was a
typical value, and typical values are the wrong ones for all three of the jobs a
loss figure is used for:

  DESIGN       needs the worst case the span is allowed to be, because the link
               has to work when every element is at its specification limit, at
               end of life, after the repairs it has not had yet.
  ACCEPTANCE   needs the contractual limit, which is what you test against and
               what you can reject the build for.  "Typical" is not a threshold
               anybody owes you.
  DIAGNOSIS    needs what this span measured when it was commissioned, which is
               neither of the above.

Using typical values for design is how a span passes on paper, passes on the day
it is built, and fails three winters later after two repairs and some ageing ---
by which time the budget that was never there is somebody else's problem.

This version computes all three, from figures you supply, and adds the thing the
old one had no place for: the repairs the span will have during its life.  Each
one adds two splices and some slack, permanently.

    python3 loss_budget.py
    python3 loss_budget.py --json
    python3 test_loss_budget.py

No fibre, no light source, no power meter, no OTDR. Arithmetic on your numbers.
"""
import argparse
import json
import sys


class BudgetError(ValueError):
    """The span description cannot be costed."""


# --------------------------------------------------------------------------
# Per-element figures. THESE ARE ILLUSTRATIVE DEFAULTS, NOT STANDARDS.
#
# Take `typical` from your own commissioning records and `maximum` from the
# cable and component datasheets you are actually buying, which is the only
# place the numbers that bind anybody live. A recommendation's limit, a cable
# maker's specification and what a good splice crew achieves are three
# different numbers, and the gap between them is this lab's whole subject.
# --------------------------------------------------------------------------
ELEMENTS = {
    'fibre_db_per_km': {
        1310: {'typical': 0.34, 'maximum': 0.40},
        1550: {'typical': 0.19, 'maximum': 0.25},
        1625: {'typical': 0.21, 'maximum': 0.28},
    },
    'fusion_splice_db': {'typical': 0.05, 'maximum': 0.15},
    'mechanical_splice_db': {'typical': 0.20, 'maximum': 0.50},
    'connector_pair_db': {'typical': 0.25, 'maximum': 0.75},
}

DEFAULT_MARGINS = {
    'repairs_over_life': 3,       # cuts this span will suffer and have spliced
    'splices_per_repair': 2,      # a repair cuts the cable: two joints, not one
    'slack_per_repair_m': 30.0,   # the loop of cable a repair leaves behind
    'ageing_db': 1.0,             # connector wear, closure ingress, drift
}


def _figure(spec, basis):
    if basis not in ('typical', 'maximum'):
        raise BudgetError("basis is 'typical' or 'maximum', got %r" % (basis,))
    return spec[basis]


def span_loss(km, wavelength_nm, fusion_splices=0, connector_pairs=0,
              mechanical_splices=0, basis='typical', elements=None,
              margins=None, include_repairs=True):
    """Total loss of a span, on one basis, with or without the repair allowance."""
    el = elements or ELEMENTS
    mg = dict(DEFAULT_MARGINS)
    mg.update(margins or {})
    if km < 0:
        raise BudgetError('a span length is not negative, got %r' % (km,))
    if wavelength_nm not in el['fibre_db_per_km']:
        raise BudgetError('no attenuation figure for %r nm; have %s'
                          % (wavelength_nm,
                             ', '.join(str(k) for k in
                                       sorted(el['fibre_db_per_km']))))
    for name, n in (('fusion splices', fusion_splices),
                    ('connector pairs', connector_pairs),
                    ('mechanical splices', mechanical_splices)):
        if not isinstance(n, int) or n < 0:
            raise BudgetError('%s must be a non-negative integer, got %r'
                              % (name, n))
    if mg['repairs_over_life'] < 0 or mg['ageing_db'] < 0:
        raise BudgetError('the repair count and ageing allowance are not negative')

    per_km = _figure(el['fibre_db_per_km'][wavelength_nm], basis)
    fus = _figure(el['fusion_splice_db'], basis)
    mech = _figure(el['mechanical_splice_db'], basis)
    con = _figure(el['connector_pair_db'], basis)

    repairs = mg['repairs_over_life'] if include_repairs else 0
    repair_splices = repairs * mg['splices_per_repair']
    repair_km = repairs * mg['slack_per_repair_m'] / 1000.0
    ageing = mg['ageing_db'] if include_repairs else 0.0

    terms = [
        ('fibre, %g km at %g dB/km' % (km, per_km), km * per_km),
        ('%d fusion splices at %g dB' % (fusion_splices, fus),
         fusion_splices * fus),
        ('%d connector pairs at %g dB' % (connector_pairs, con),
         connector_pairs * con),
    ]
    if mechanical_splices:
        terms.append(('%d mechanical splices at %g dB'
                      % (mechanical_splices, mech), mechanical_splices * mech))
    if repairs:
        terms.append(('%d repairs x %d splices at %g dB'
                      % (repairs, mg['splices_per_repair'], fus),
                      repair_splices * fus))
        terms.append(('%d repairs x %g m of slack cable'
                      % (repairs, mg['slack_per_repair_m']), repair_km * per_km))
    if ageing:
        terms.append(('ageing and drift allowance', ageing))

    total = sum(v for _, v in terms)
    return {'km': km, 'wavelength_nm': wavelength_nm, 'basis': basis,
            'includes_repairs': bool(repairs), 'terms': terms, 'total_db': total}


def assess(km, wavelength_nm, system_budget_db, **kw):
    """The three numbers a span needs, and the verdict that follows from one."""
    kw.pop('basis', None)
    kw.pop('include_repairs', None)
    if system_budget_db <= 0:
        raise BudgetError('the system budget is positive, got %r'
                          % (system_budget_db,))
    typ = span_loss(km, wavelength_nm, basis='typical',
                    include_repairs=False, **kw)
    acc = span_loss(km, wavelength_nm, basis='maximum',
                    include_repairs=False, **kw)
    des = span_loss(km, wavelength_nm, basis='maximum',
                    include_repairs=True, **kw)
    return {
        'system_budget_db': system_budget_db,
        'typical_db': typ['total_db'],
        'acceptance_limit_db': acc['total_db'],
        'design_db': des['total_db'],
        'design_terms': des['terms'],
        'headroom_on_typical_db': system_budget_db - typ['total_db'],
        'headroom_on_design_db': system_budget_db - des['total_db'],
        'passes_on_typical': typ['total_db'] <= system_budget_db,
        'passes_on_design': des['total_db'] <= system_budget_db,
        'the_gap_db': des['total_db'] - typ['total_db'],
    }


# --------------------------------------------------------------------------
# the chapter's own example span
# --------------------------------------------------------------------------
SPANS = [
    # name, km, nm, fusion, connector pairs, system budget dB
    ("the chapter's 60 km example", 60, 1550, 4, 4, 16.0),
    ('...with two patch panels taken out', 60, 1550, 4, 2, 16.0),
    ('...on optics with a 22 dB budget', 60, 1550, 4, 4, 22.0),
    ('long span, spliced straight through', 120, 1550, 8, 2, 36.0),
    ('short metro hop', 8, 1310, 2, 4, 11.0),
]


def report(rows):
    print('Three loss figures for one span, and only one of them designs it.')
    print('Every per-element figure is an ILLUSTRATIVE DEFAULT --- replace them')
    print('with your cable and component datasheets, which are what bind.\n')
    print('%38s | %8s | %10s | %8s | %8s | %s'
          % ('span', 'typical', 'acceptance', 'design', 'budget', 'verdict'))
    print('-' * 104)
    for name, a in rows:
        if a['passes_on_design']:
            v = 'fits, %.1f dB spare' % a['headroom_on_design_db']
        elif a['passes_on_typical']:
            v = 'PASSES ON TYPICAL, FAILS ON DESIGN by %.1f dB' % -a['headroom_on_design_db']
        else:
            v = 'fails on any basis'
        print('%38s | %7.2f  | %9.2f  | %7.2f  | %7.1f  | %s'
              % (name, a['typical_db'], a['acceptance_limit_db'],
                 a['design_db'], a['system_budget_db'], v))

    first = rows[0][1]
    print('\nThe chapter\'s own worked span is the case in point. On typical')
    print('figures it loses %.2f dB and fits a %.0f dB budget with %.2f dB to'
          % (first['typical_db'], first['system_budget_db'],
             first['headroom_on_typical_db']))
    print('spare. On the figures you would actually design to it loses %.2f dB'
          % first['design_db'])
    print('and does not fit at all. The difference is %.2f dB --- more than the'
          % first['the_gap_db'])
    print('entire connector allowance --- and none of it is exotic:\n')
    for label, v in first['design_terms']:
        print('    %-44s %6.2f dB' % (label, v))
    print('\nNothing there is a surprise. Specification limits rather than good')
    print('days, and the repairs a buried cable will have over twenty years.')
    print('A span designed on typical figures works on the day it is built and')
    print('is the incident nobody can explain three winters later.')
    trimmed, better = rows[1][1], rows[2][1]
    print('\nNote which fix works. Taking out two patch panels --- the obvious')
    print('move, and a real saving of %.2f dB --- still leaves the span %.1f dB'
          % (first['design_db'] - trimmed['design_db'],
             -trimmed['headroom_on_design_db']))
    print('short. What fits it is optics with a %.0f dB budget, which is a'
          % better['system_budget_db'])
    print('procurement decision you have to make before the glass goes in the')
    print('ground rather than after. The last two spans fit as designed: a')
    print('design basis is not a way of failing everything, it is a way of')
    print('finding out on paper.')
    print('\nUse typical figures for one thing only: comparing what you measured')
    print('at commissioning with what you measure today.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        rows = [(n, assess(km, nm, budget, fusion_splices=f,
                           connector_pairs=c))
                for n, km, nm, f, c, budget in SPANS]
    except BudgetError as e:
        print('budget error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps([{**a, 'name': n} for n, a in rows], indent=2))
    else:
        report(rows)
    return 0


if __name__ == '__main__':
    sys.exit(main())
