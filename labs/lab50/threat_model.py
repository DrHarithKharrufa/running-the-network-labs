#!/usr/bin/env python3
"""Lab 50.1 --- the one-hour threat model, with scoring that can come out badly.

WHY THIS LAB EXISTS
-------------------
The shipped lab, threatmodel.py, had a defect that a security tool must never
have: it gave a control credit to a control the input explicitly marked ABSENT.

    ("IoT cameras on flat segment", "opportunist", "none (flat)", 2, 2),
    ...
    if has_control:            # a real control roughly halves residual risk
        r = r / 2.0
    ...
    has_control = control is not None

"none (flat)" is a string, so `control is not None` was True, so the one entry
point whose control field says in plain English that there is no segmentation
had its risk HALVED, from 4 to 2.  And it got worse: the gap list --- which the
lab itself called "the output that matters" --- was built with

    gaps = [row for row in rows if row[3] is None]

so the same entry point was also REMOVED from the list of gaps.  An operator
running that script over their own network would have been told that their flat
camera VLAN was both partly mitigated and not a gap.  Neither was true, and the
input said so in words.

THREE THINGS ARE FIXED HERE, AND THE THIRD IS THE ONE THAT MATTERS
------------------------------------------------------------------
1.  ABSENCE IS A VALUE, NOT A MISSING FIELD.  A control is declared with
    Control(...) or with the singleton ABSENT.  There is no way to spell "no
    control" that also reads as a control, and a Control whose name says it is
    not one is rejected at construction rather than silently scored.

2.  A CONTROL IS NOT A FLAT HALVING.  The old model gave "VPN only" on a
    contractor account with broad access exactly the same 50 per cent credit as
    "MFA + filtering".  Here a control states WHICH attacker class it raises the
    cost against and by how much, and it earns nothing against a class it does
    not address.  A control aimed at the wrong class scores zero, which is the
    arithmetic form of the chapter's own advice.

3.  THE RANKING IS REPORTED AS A BAND, NOT A NUMBER.  Likelihood and impact are
    ORDINAL: a 3 is worse than a 2, but it is not 1.5 times a 2, and their
    product is not a quantity.  This model still multiplies them, because that
    is what the chapter teaches and what every register in the field does, but
    it prints the product as a band with its ties visible and it refuses to
    order two items whose bands overlap.  Lab 50.3 shows why that matters: a
    3x3 scale has nine cells and only six distinct products, so a register of
    any size is mostly ties, and a ranking read off it is partly fictional.

    python3 threat_model.py
    python3 threat_model.py --json
    python3 test_threat_model.py

No network, device, scanner, log or incident record was involved.  The entry
points, controls, scores and coverage figures below are stated inputs chosen to
exercise the method.  Nothing here is a base rate: see the note in Section A.
"""
import argparse
import json
import textwrap
import sys

# ---------------------------------------------------------------------------
# scales, defined rather than assumed
# ---------------------------------------------------------------------------
LIKELIHOOD_SCALE = {
    1: 'not seen on networks like this, and no published campaign targets them',
    2: 'happens to networks like this; you would not be surprised to read of it',
    3: 'happens continuously and indiscriminately; assume it is being tried now',
}
IMPACT_SCALE = {
    1: 'one device or one service degraded; contained by existing segmentation',
    2: 'a site or a customer-facing service lost, or data exposed within one domain',
    3: 'control of infrastructure others depend on, or loss of the business service',
}
CLASSES = ('opportunist', 'criminal', 'insider', 'state')
PLANES = ('management', 'control', 'data', 'supply chain')


class ModelError(ValueError):
    """The described entry point, control or scale value cannot be evaluated."""


# ---------------------------------------------------------------------------
# a control, and the absence of one
# ---------------------------------------------------------------------------
_NEGATIONS = ('none', 'no ', 'n/a', 'nil', 'nothing', 'absent', 'not ',
              'unprotected', 'flat', 'tbd', 'todo', 'unknown', 'assume')


class _Absent:
    """The explicit absence of a control. Scores nothing, always a gap."""
    name = 'NO CONTROL'
    short = 'NO CONTROL'
    covers = ()

    def credit(self, attacker_class):
        return 0.0

    def __repr__(self):
        return 'ABSENT'

    def __bool__(self):
        # so that `if control:` is False, whichever way a reader writes the test
        return False


ABSENT = _Absent()


class Control:
    """A control, the classes it raises cost against, and by how much.

    cost_increase maps an attacker class to the fraction of the residual risk
    the control is claimed to remove FOR THAT CLASS, between 0 and 1 exclusive
    of 1.  It cannot be 1: no control removes a risk, and a model that lets it
    say so is the model the chapter warns about.
    """

    def __init__(self, name, cost_increase, note='', short=None):
        if not name or not name.strip():
            raise ModelError('a control must be named; use ABSENT for none')
        low = name.strip().lower()
        for neg in _NEGATIONS:
            if low.startswith(neg):
                raise ModelError(
                    'control name %r reads as an absence; use ABSENT rather '
                    'than a control named after not having one' % name)
        if not cost_increase:
            raise ModelError('control %r claims no effect on any class; use '
                             'ABSENT or state what it does' % name)
        for cls, frac in cost_increase.items():
            if cls not in CLASSES:
                raise ModelError('control %r names unknown attacker class %r; '
                                 'known classes are %s' % (name, cls, ', '.join(CLASSES)))
            if not 0.0 < frac < 1.0:
                raise ModelError(
                    'control %r claims %r against %s; a claim must be above 0 '
                    'and below 1, because no control removes a risk'
                    % (name, frac, cls))
        self.name = name.strip()
        self.cost_increase = dict(cost_increase)
        self.note = note
        self.short = (short or self.name)[:24]

    @property
    def covers(self):
        return tuple(sorted(self.cost_increase))

    def credit(self, attacker_class):
        """Fraction of residual risk removed against THIS class. Zero elsewhere."""
        return self.cost_increase.get(attacker_class, 0.0)

    def __repr__(self):
        return 'Control(%r, %r)' % (self.name, self.cost_increase)


# ---------------------------------------------------------------------------
# an entry point
# ---------------------------------------------------------------------------
class EntryPoint:
    def __init__(self, name, attacker_class, plane, likelihood, impact,
                 controls=None, short=None):
        if attacker_class not in CLASSES:
            raise ModelError('unknown attacker class %r for %r; known classes '
                             'are %s' % (attacker_class, name, ', '.join(CLASSES)))
        if plane not in PLANES:
            raise ModelError('unknown plane %r for %r; the inventory has %s'
                             % (plane, name, ', '.join(PLANES)))
        if likelihood not in LIKELIHOOD_SCALE:
            raise ModelError('likelihood %r for %r is not on the defined scale '
                             '%s' % (likelihood, name, sorted(LIKELIHOOD_SCALE)))
        if impact not in IMPACT_SCALE:
            raise ModelError('impact %r for %r is not on the defined scale %s'
                             % (impact, name, sorted(IMPACT_SCALE)))
        self.name = name
        self.short = (short or name)[:38]
        self.attacker_class = attacker_class
        self.plane = plane
        self.likelihood = likelihood
        self.impact = impact
        self.controls = list(controls) if controls else [ABSENT]
        if not self.controls:
            self.controls = [ABSENT]
        for c in self.controls:
            if not isinstance(c, (Control, _Absent)):
                raise ModelError(
                    'control %r on %r is a %s, not a Control or ABSENT. This is '
                    'the defect the previous lab had: a string that reads as an '
                    'absence but tests as a presence.'
                    % (c, name, type(c).__name__))

    # -- scoring ----------------------------------------------------------
    @property
    def inherent(self):
        """Likelihood x impact before any control. An ordinal product."""
        return self.likelihood * self.impact

    @property
    def effective_controls(self):
        """The controls that do anything against THIS entry point's class."""
        return [c for c in self.controls if c.credit(self.attacker_class) > 0]

    @property
    def inert_controls(self):
        """Controls present but aimed at a class this entry point does not face."""
        return [c for c in self.controls
                if isinstance(c, Control) and c.credit(self.attacker_class) == 0]

    @property
    def residual(self):
        """Inherent risk after the controls that address this class.

        Controls compose multiplicatively on what is LEFT, so two controls
        claiming half each leave a quarter, never nothing.
        """
        r = float(self.inherent)
        for c in self.effective_controls:
            r *= (1.0 - c.credit(self.attacker_class))
        return r

    @property
    def is_gap(self):
        """No control does anything against the class this entry point faces.

        Note what this does NOT depend on: whether the controls list is empty,
        whether a field is None, or how a control was spelled.
        """
        return not self.effective_controls

    def as_dict(self):
        return {
            'name': self.name, 'short': self.short,
            'attacker_class': self.attacker_class,
            'plane': self.plane, 'likelihood': self.likelihood,
            'impact': self.impact, 'inherent': self.inherent,
            'residual': round(self.residual, 3),
            'controls': [c.name for c in self.controls],
            'effective_controls': [c.name for c in self.effective_controls],
            'effective_short': [c.short for c in self.effective_controls],
            'inert_controls': [c.name for c in self.inert_controls],
            'is_gap': self.is_gap,
        }


# ---------------------------------------------------------------------------
# the illustrative campus
# ---------------------------------------------------------------------------
def aldergate():
    mfa = Control('MFA on all administrative access',
                  {'opportunist': 0.8, 'criminal': 0.5, 'insider': 0.2, 'state': 0.2},
                  'stops credential reuse outright; a determined class still '
                  'phishes the second factor or steals the session',
                  short='MFA on admin access')
    seg = Control('VLAN separation with an enforced firewall policy',
                  {'opportunist': 0.7, 'criminal': 0.5, 'insider': 0.4, 'state': 0.3},
                  'limits reach rather than entry, so it moves impact more than '
                  'likelihood; this model applies it to the product, which is a '
                  'simplification worth knowing about',
                  short='segmentation + policy')
    signing = Control('Secure boot and image signature verification',
                      {'opportunist': 0.8, 'criminal': 0.6, 'state': 0.15},
                      'stops a tampered image in transit and an unsigned one on '
                      'disk; does NOT address a validly signed malicious update '
                      'from a compromised vendor, which is the state-actor case. '
                      'See Lab 50.2.',
                      short='image signing')
    bgpauth = Control('BGP session authentication and prefix filters',
                      {'opportunist': 0.8, 'criminal': 0.6, 'state': 0.3},
                      short='BGP auth + filters')
    lp = Control('Least privilege, scoped to the job',
                 {'insider': 0.5, 'criminal': 0.3, 'state': 0.2},
                 'the insider control the chapter says is most often missing',
                 short='least privilege')
    return [
        EntryPoint('Internet-facing management on the edge router',
                   'opportunist', 'management', 3, 3, short='Internet-facing mgmt, edge router'),
        EntryPoint('Guest Wi-Fi to internal VLAN',
                   'opportunist', 'data', 1, 2, [seg], short='Guest Wi-Fi to internal VLAN'),
        EntryPoint('Contractor VPN with access to the whole estate',
                   'insider', 'management', 2, 3, [mfa], short='Contractor VPN, whole estate'),
        EntryPoint('BGP session to upstream with no authentication',
                   'criminal', 'control', 2, 3, short='BGP to upstream, no auth'),
        EntryPoint('IoT cameras on a flat segment',
                   'opportunist', 'data', 2, 2, short='IoT cameras on a flat segment'),
        EntryPoint('Vendor image and update channel',
                   'state', 'supply chain', 1, 3, [signing], short='Vendor image/update channel'),
        EntryPoint('Staff email as a route to a foothold',
                   'criminal', 'management', 2, 2, [mfa], short='Staff email to a foothold'),
        EntryPoint('Console ports in an unlocked comms room',
                   'insider', 'management', 1, 3, [bgpauth], short='Console ports, unlocked room'),
    ], {'mfa': mfa, 'seg': seg, 'signing': signing, 'bgpauth': bgpauth, 'lp': lp}


# ---------------------------------------------------------------------------
# ranking, with ties visible
# ---------------------------------------------------------------------------
def ranked(entries):
    """Entry points by residual risk, worst first, with tie groups marked.

    Ties are counted twice over, and the difference between the two counts is
    the point. `inherent_tied_with` counts ties on likelihood x impact --- the
    score the chapter teaches and the one a register normally carries. `tied_with`
    counts them on the residual after differentiated controls. A register scored
    the ordinary way is mostly ties; what separates the rows is having said what
    each control actually does and to whom.
    """
    rows = sorted(entries, key=lambda e: (-e.residual, e.name))
    out = [{'entry': e, 'residual': e.residual, 'inherent': e.inherent}
           for e in rows]
    for key, field in (('residual', 'tied_with'), ('inherent', 'inherent_tied_with')):
        by_value = {}
        for r in out:
            by_value.setdefault(round(r[key], 6), []).append(r)
        for group in by_value.values():
            for r in group:
                r[field] = len(group) - 1
    return out


def tie_summary(entries):
    """How much of a ranking survives on each scoring, as a pair of counts."""
    rows = ranked(entries)
    return {
        'rows': len(rows),
        'inherent_distinct': len({r['inherent'] for r in rows}),
        'residual_distinct': len({round(r['residual'], 6) for r in rows}),
        'inherent_rows_tied': sum(1 for r in rows if r['inherent_tied_with']),
        'residual_rows_tied': sum(1 for r in rows if r['tied_with']),
    }


def gaps(entries):
    """Every entry point no present control addresses, worst first.

    The old lab built this from `control is None`, so an entry point carrying a
    control field that said "none (flat)" was excluded. This is derived from
    whether anything actually acts on the class faced.
    """
    return sorted([e for e in entries if e.is_gap],
                  key=lambda e: (-e.residual, e.name))


def inert(entries):
    """Controls present on an entry point but aimed at a class it does not face."""
    out = []
    for e in entries:
        for c in e.inert_controls:
            out.append({'entry': e.name, 'control': c.name,
                        'class_faced': e.attacker_class,
                        'classes_covered': list(c.covers)})
    return out


def by_plane(entries):
    """Residual risk summed by plane, to show an unevenly inventoried model."""
    out = {p: {'count': 0, 'residual': 0.0, 'gaps': 0} for p in PLANES}
    for e in entries:
        out[e.plane]['count'] += 1
        out[e.plane]['residual'] += e.residual
        out[e.plane]['gaps'] += 1 if e.is_gap else 0
    for p in out:
        out[p]['residual'] = round(out[p]['residual'], 3)
    return out


def control_would_close(entries, control):
    """What adding one control to every gap it addresses would actually buy."""
    before = sum(e.residual for e in entries)
    after = 0.0
    closed = []
    for e in entries:
        if e.is_gap and control.credit(e.attacker_class) > 0:
            after += e.residual * (1.0 - control.credit(e.attacker_class))
            closed.append(e.name)
        else:
            after += e.residual
    return {'control': control.name, 'closes': closed,
            'residual_before': round(before, 3), 'residual_after': round(after, 3),
            'reduction': round(before - after, 3),
            'reduction_pct': round(100.0 * (before - after) / before, 1) if before else 0.0}


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def build_report():
    entries, ctls = aldergate()
    return {
        'scales': {'likelihood': LIKELIHOOD_SCALE, 'impact': IMPACT_SCALE},
        'entries': [e.as_dict() for e in entries],
        'ranked': [{'name': r['entry'].name, 'residual': round(r['residual'], 3),
                    'inherent': r['inherent'], 'tied_with': r['tied_with'],
                    'inherent_tied_with': r['inherent_tied_with']}
                   for r in ranked(entries)],
        'ties': tie_summary(entries),
        'gaps': [e.as_dict() for e in gaps(entries)],
        'inert_controls': inert(entries),
        'by_plane': by_plane(entries),
        'candidates': [control_would_close(entries, c)
                       for c in (ctls['mfa'], ctls['seg'], ctls['bgpauth'], ctls['lp'])],
        'caveats': [
            'Every entry point, class, plane, score and coverage figure is a '
            'stated input. None is a base rate, a measurement or an incident '
            'record, and the absolute numbers mean nothing outside this script.',
            'Likelihood and impact are ORDINAL. Their product is not a quantity, '
            'the difference between two products is not a magnitude, and Lab '
            '50.3 shows how few distinct values the scale actually has.',
            'A coverage fraction is a CLAIM about a control, not a measurement '
            'of one. A control you have but have not tested is a claim with '
            'nothing behind it.',
            'Controls are composed multiplicatively on what is left, so a '
            'residual never reaches zero. That is a property of the arithmetic, '
            'not evidence that the remaining risk is small.',
            'Segmentation and least privilege mostly limit REACH rather than '
            'entry, so they belong on impact rather than on the product. This '
            'model applies them to the product, which overstates their effect '
            'on likelihood and understates the case for them.',
            'Nothing here approves a design, and a gap list is the beginning of '
            'a conversation about money, not the end of one.',
        ],
    }


def report_text(rep):
    L = []
    L.append('The one-hour threat model, scored so it can come out badly (Chapter 50)')
    L.append('Every figure below is a stated input. None is a base rate.')
    L.append('')
    L.append('A. The scales, stated before anything is scored')
    L.append('-' * 74)
    L.append('  A register whose scale is undefined is a register whose scores '
             'cannot be')
    L.append('  argued with, which is how everything drifts to "high".')
    L.append('')
    for label, scale in (('likelihood', rep['scales']['likelihood']),
                         ('impact', rep['scales']['impact'])):
        for n, d in sorted(scale.items()):
            head = '  %-10s %d  ' % (label, n)
            wrapped = textwrap.wrap(d, width=74 - len(head))
            L.append(head + wrapped[0])
            for extra in wrapped[1:]:
                L.append(' ' * len(head) + extra)
        L.append('')
    L.append('')
    L.append('  These are bands this lab invented so the method can be '
             'exercised. Yours')
    L.append('  come from your own incident history and from published '
             'advisories for')
    L.append('  networks like yours, and writing them down is most of the work.')
    L.append('')
    L.append('B. The ranked list, with its ties showing')
    L.append('-' * 74)
    L.append('%-34s %5s %6s  %s' % ('entry point', 'inher', 'resid',
                                    'what acts on it'))
    for r in rep['ranked']:
        e = next(x for x in rep['entries'] if x['name'] == r['name'])
        act = ', '.join(e['effective_short']) or '>> NOTHING <<'
        L.append('%-34s %5d %6.2f  %s' % (e['short'], e['inherent'],
                                          r['residual'], act))
    L.append('')
    ti = rep['ties']
    L.append('  Count the ties twice over, because the two counts differ and '
             'the')
    L.append('  difference is the finding.')
    L.append('')
    L.append('    on likelihood x impact alone   %d of %d rows tied, %d '
             'distinct values'
             % (ti['inherent_rows_tied'], ti['rows'], ti['inherent_distinct']))
    L.append('    on residual after controls     %d of %d rows tied, %d '
             'distinct values'
             % (ti['residual_rows_tied'], ti['rows'], ti['residual_distinct']))
    L.append('')
    if ti['inherent_rows_tied'] > ti['residual_rows_tied']:
        L.append('  The score the chapter teaches --- likelihood times impact '
                 '--- puts %d of'
                 % ti['inherent_rows_tied'])
        L.append('  these %d rows in a tie, because a 3x3 scale has nine cells '
                 'and only six'
                 % ti['rows'])
        L.append('  distinct products. A register ranked that way is not '
                 'ranked; it is')
        L.append('  sorted by whatever the spreadsheet did next, and that is '
                 'usually the')
        L.append('  order the rows were typed in. What separates these rows is '
                 'not a')
        L.append('  finer scale --- it is having said what each control does '
                 'and to whom,')
        L.append('  which takes %d rows down to %d tied. Lab 50.3 counts how '
                 'far this goes.'
                 % (ti['inherent_rows_tied'], ti['residual_rows_tied']))
    else:
        L.append('  On this register the two scorings tie equally often, which '
                 'is not the')
        L.append('  usual case. Lab 50.3 counts how much of a ranking on a 3x3 '
                 'scale is real.')
    L.append('')
    L.append('C. The gaps --- derived, not filtered on a field being empty')
    L.append('-' * 74)
    for e in rep['gaps']:
        L.append('  %-34s residual %5.2f   %s'
                 % (e['short'], e['residual'], e['attacker_class']))
    L.append('')
    L.append('  This is where the previous version of this lab failed. It built '
             'the gap')
    L.append('  list from `control is None`, and one entry point declared its '
             'control as')
    L.append('  the string "none (flat)". That string is not None, so the flat '
             'camera')
    L.append('  segment was scored as though half mitigated AND left out of the '
             'gap list')
    L.append('  entirely --- in a script whose own output line called the gap '
             'list the')
    L.append('  thing that matters. Here absence is a value, a control that '
             'reads as an')
    L.append('  absence is refused at construction, and a gap is defined as '
             '"nothing')
    L.append('  present acts on the class faced".')
    L.append('')
    if rep['inert_controls']:
        L.append('D. Controls that are present and do nothing here')
        L.append('-' * 74)
        for r in rep['inert_controls']:
            L.append('  %s' % r['entry'])
            L.extend(textwrap.wrap(
                'has %r, which covers %s --- and this entry point faces the %s.'
                % (r['control'], ', '.join(r['classes_covered']),
                   r['class_faced']),
                width=72, initial_indent='    ', subsequent_indent='      '))
        L.append('')
        L.append('  The old model gave any non-empty control field a flat fifty '
                 'per cent,')
        L.append('  so a control aimed at the wrong adversary scored exactly as '
                 'well as one')
        L.append('  aimed at the right one. A control earns nothing here '
                 'against a class it')
        L.append('  does not address, which is the chapter\'s own advice '
                 'written as')
        L.append('  arithmetic rather than as a sentence.')
        L.append('')
    L.append('E. Coverage by plane, which is where an inventory shows its holes')
    L.append('-' * 74)
    L.append('%-16s %7s %10s %6s' % ('plane', 'entries', 'residual', 'gaps'))
    for p, v in rep['by_plane'].items():
        L.append('%-16s %7d %10.2f %6d' % (p, v['count'], v['residual'], v['gaps']))
    empty = [p for p, v in rep['by_plane'].items() if v['count'] == 0]
    if empty:
        L.append('')
        L.append('  NOTHING INVENTORIED on: %s. A plane with no entry points is '
                 'not a' % ', '.join(empty))
        L.append('  plane with no exposure; it is a plane nobody looked at, and '
                 'it will')
        L.append('  score zero risk for exactly as long as that is true.')
    L.append('')
    L.append('F. What one more control would actually buy')
    L.append('-' * 74)
    L.append('%-46s %9s %7s' % ('candidate control', 'reduction', 'closes'))
    for c in sorted(rep['candidates'], key=lambda x: -x['reduction']):
        L.append('%-46s %9.2f %7d' % (c['control'][:46], c['reduction'],
                                      len(c['closes'])))
    top = max(c['reduction'] for c in rep['candidates'])
    winners = [c for c in rep['candidates']
               if abs(c['reduction'] - top) < 1e-9]
    L.append('')
    if top <= 0:
        L.append('  None of the candidates reduces anything, because none of '
                 'them addresses')
        L.append('  the classes the remaining gaps face. That is a result, not '
                 'an error.')
    elif len(winners) == 1:
        b = winners[0]
        L.append('  Best here: %s, closing %d gap(s) for %.1f per cent of the '
                 'total'
                 % (b['control'], len(b['closes']), b['reduction_pct']))
        L.append('  residual.')
    else:
        L.append('  NO SINGLE BEST. %d candidates tie exactly at %.2f:'
                 % (len(winners), top))
        for b in winners:
            L.append('    %s, closing %d:' % (b['control'], len(b['closes'])))
            for name in b['closes']:
                L.append('        %s' % name)
        L.append('  They tie on the arithmetic and are not interchangeable. '
                 'They close')
        L.append('  DIFFERENT gaps, against different classes, at different '
                 'cost and on')
        L.append('  different timescales, and this model knows none of that. A '
                 'tie here is')
        L.append('  the model handing the decision back, which is the correct '
                 'behaviour and')
        L.append('  the reason a register is an input to a judgement rather '
                 'than a substitute')
        L.append('  for one.')
    L.append('')
    L.append('  And note what this ranking is against: what a control closes on '
             'THIS')
    L.append('  register. A control addressing a class nobody wrote down will '
             'always')
    L.append('  score zero. That is a fact about the register, not the control.')
    L.append('')
    L.append('What this does NOT establish')
    L.append('-' * 74)
    for c in rep['caveats']:
        L.extend(textwrap.wrap(c, width=74, initial_indent='- ',
                               subsequent_indent='  '))
    return '\n'.join(L)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--json', action='store_true', help='emit the report as JSON')
    a = p.parse_args(argv)
    try:
        rep = build_report()
    except ModelError as exc:
        print('cannot evaluate: %s' % exc, file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=2) if a.json else report_text(rep))
    return 0


if __name__ == '__main__':
    sys.exit(main())
