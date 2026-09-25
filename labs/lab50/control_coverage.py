#!/usr/bin/env python3
"""Lab 50.2 --- "stopped by" is the wrong verb, and coverage is per mechanism.

WHY THIS LAB EXISTS
-------------------
The chapter's attacker-class table ends every row with what stops that class:

    Opportunist  "Stopped by basic hygiene: patch, no exposed management, no
                  default creds"
    Criminal     "Stopped by segmentation, backups, MFA and detection that
                  catches the dwell time"
    Insider      "Stopped by least privilege, separation of duties, audit, and
                  limiting blast radius --- not by a firewall"
    State        "Stopped by assume-breach design, not by hope"

Three things are wrong with that, and they compound.

  NOTHING STOPS A CLASS.  A control does one of three quite different things,
  and they are not interchangeable: it can REDUCE FREQUENCY (fewer attempts get
  anywhere), LIMIT REACH (a foothold reaches less), or SHORTEN DWELL (you find
  out sooner).  A control set can be complete on frequency and empty on reach,
  and the chapter's own assume-breach section says that is precisely the wrong
  shape --- but its class table gives you no way to notice, because it lists the
  three kinds in one breath.  Section B separates them.

  COVERAGE IS PER MECHANISM, NOT PER THREAT.  A threat is not one thing a
  control either handles or does not.  "Supply chain" is at least four distinct
  mechanisms, and image signing addresses two of them.  Counting the threat as
  covered because a control applies to part of it is how an inventory reports
  green on a plane that is open.  Section C does the supply chain in full, which
  is the chapter's own worked example of the plane teams forget.

  AND A TIMEBOX IS NOT ASSURANCE.  The chapter's one-hour method is good advice
  and the chapter then leans on it as though repeating it made the model
  complete.  An hour spent well still returns a list of the mechanisms you
  thought of.  Section D shows what the method returns when a mechanism is
  simply not on the list: zero risk, confidently, for as long as nobody names it.

    python3 control_coverage.py
    python3 control_coverage.py --json
    python3 test_control_coverage.py

No estate, device, scanner or audit was involved.  Every mechanism, control and
coverage claim below is a stated input, written to exercise the method.
"""
import argparse
import json
import textwrap
import sys

EFFECTS = ('reduce frequency', 'limit reach', 'shorten dwell')
CLASSES = ('opportunist', 'criminal', 'insider', 'state')
PLANES = ('management', 'control', 'data', 'supply chain')


class CoverageError(ValueError):
    """The described mechanism, control or estate cannot be evaluated."""


class Mechanism:
    """One concrete way in. Not a category, not a plane, not a threat actor."""

    def __init__(self, ident, plane, classes, description):
        if plane not in PLANES:
            raise CoverageError('unknown plane %r for %r' % (plane, ident))
        bad = [c for c in classes if c not in CLASSES]
        if bad:
            raise CoverageError('unknown attacker class %r for %r' % (bad, ident))
        if not classes:
            raise CoverageError('mechanism %r names no attacker class' % ident)
        self.ident = ident
        self.plane = plane
        self.classes = tuple(classes)
        self.description = description

    def __repr__(self):
        return 'Mechanism(%r)' % self.ident


class Control:
    """A control, the mechanisms it addresses, and WHICH KIND of effect it has."""

    def __init__(self, name, effect, addresses, note=''):
        if effect not in EFFECTS:
            raise CoverageError(
                'control %r claims effect %r; a control reduces frequency, '
                'limits reach or shortens dwell, and conflating them is the '
                'error this lab exists to catch' % (name, effect))
        if not addresses:
            raise CoverageError('control %r addresses no mechanism' % name)
        self.name = name
        self.effect = effect
        self.addresses = tuple(addresses)
        self.note = note

    def __repr__(self):
        return 'Control(%r, %r)' % (self.name, self.effect)


# ---------------------------------------------------------------------------
# the supply chain, taken apart
# ---------------------------------------------------------------------------
SUPPLY_CHAIN = [
    Mechanism('image-tampered-in-transit', 'supply chain', ('criminal', 'state'),
              'the image is altered between the vendor and you'),
    Mechanism('image-unsigned-on-disk', 'supply chain', ('opportunist', 'criminal', 'insider'),
              'an unsigned or locally modified image is installed'),
    Mechanism('vendor-compromised-signs-malice', 'supply chain', ('state',),
              'the vendor is compromised and signs a malicious update with its '
              'own real key; every signature verifies'),
    Mechanism('signing-key-stolen', 'supply chain', ('state',),
              'the signing key is stolen and used; every signature verifies'),
    Mechanism('hardware-implant-at-odm', 'supply chain', ('state',),
              'the component arrives altered, before any software runs'),
    Mechanism('dependency-in-vendor-build', 'supply chain', ('criminal', 'state'),
              'a third-party component inside the vendor build is the way in'),
]

OTHER_PLANES = [
    Mechanism('exposed-mgmt-interface', 'management', ('opportunist', 'criminal'),
              'the management interface answers from the Internet'),
    Mechanism('default-or-reused-credential', 'management', ('opportunist', 'criminal'),
              'the credential is known, guessable or reused from a breach dump'),
    Mechanism('known-cve-unpatched', 'management', ('opportunist', 'criminal', 'state'),
              'a catalogued vulnerability is still present'),
    Mechanism('standing-admin-privilege', 'management', ('insider', 'criminal'),
              'an account holds more access than the job needs, permanently'),
    Mechanism('unauthenticated-routing-peer', 'control', ('criminal', 'state'),
              'a routing adjacency is accepted without authentication'),
    Mechanism('control-plane-exhaustion', 'control', ('opportunist', 'criminal'),
              'the control plane is overwhelmed rather than subverted'),
    Mechanism('flat-segment-lateral-movement', 'data', ('criminal', 'insider', 'state'),
              'a foothold reaches everything the segment reaches'),
    Mechanism('unlogged-administrative-action', 'management', ('insider',),
              'an action happens with nothing attributable recorded'),
]

ALL_MECHANISMS = SUPPLY_CHAIN + OTHER_PLANES


def estate_controls():
    """A plausible, and deliberately uneven, set of controls."""
    return [
        Control('secure boot and image signature verification', 'reduce frequency',
                ('image-tampered-in-transit', 'image-unsigned-on-disk'),
                'verifies that the image is the one the vendor signed. That is '
                'a statement about the signature, not about the vendor.'),
        Control('management plane off the Internet, jump host only', 'reduce frequency',
                ('exposed-mgmt-interface',)),
        Control('MFA on administrative access', 'reduce frequency',
                ('default-or-reused-credential',)),
        Control('patch pipeline with a published SLA', 'reduce frequency',
                ('known-cve-unpatched',)),
        Control('routing session authentication and prefix filters', 'reduce frequency',
                ('unauthenticated-routing-peer',)),
        Control('control-plane policing', 'limit reach',
                ('control-plane-exhaustion',)),
        Control('segmentation with an enforced policy', 'limit reach',
                ('flat-segment-lateral-movement',)),
        Control('central logging with tamper-evident retention', 'shorten dwell',
                ('unlogged-administrative-action',)),
    ]


# ---------------------------------------------------------------------------
# coverage
# ---------------------------------------------------------------------------
def coverage(mechanisms, controls):
    """Per mechanism, which controls address it and with which effect."""
    out = []
    for m in mechanisms:
        acting = [c for c in controls if m.ident in c.addresses]
        out.append({
            'mechanism': m.ident, 'plane': m.plane, 'classes': list(m.classes),
            'description': m.description,
            'controls': [c.name for c in acting],
            'effects': sorted({c.effect for c in acting}),
            'covered': bool(acting),
        })
    return out


def by_class(mechanisms, controls):
    """For each attacker class, how many of its mechanisms anything addresses."""
    cov = {r['mechanism']: r for r in coverage(mechanisms, controls)}
    out = {}
    for cls in CLASSES:
        mine = [m for m in mechanisms if cls in m.classes]
        got = [m for m in mine if cov[m.ident]['covered']]
        effects = {e: 0 for e in EFFECTS}
        for m in got:
            for e in cov[m.ident]['effects']:
                effects[e] += 1
        out[cls] = {
            'mechanisms': len(mine), 'covered': len(got),
            'uncovered': [m.ident for m in mine if not cov[m.ident]['covered']],
            'fraction': round(len(got) / len(mine), 3) if mine else None,
            'effects': effects,
        }
    return out


def by_effect(controls):
    """The shape of the control set: how much of it does each kind of work."""
    out = {e: [] for e in EFFECTS}
    for c in controls:
        out[c.effect].append(c.name)
    return out


def plane_coverage(mechanisms, controls):
    cov = {r['mechanism']: r for r in coverage(mechanisms, controls)}
    out = {}
    for p in PLANES:
        mine = [m for m in mechanisms if m.plane == p]
        got = [m for m in mine if cov[m.ident]['covered']]
        out[p] = {'mechanisms': len(mine), 'covered': len(got),
                  'fraction': round(len(got) / len(mine), 3) if mine else None}
    return out


def unnamed_mechanism_effect(mechanisms, controls, drop):
    """What the method reports when a mechanism is simply not on the list.

    This is the timebox question. Removing a mechanism from the inventory does
    not reduce the risk; it reduces the reported risk, to zero, silently.
    """
    kept = [m for m in mechanisms if m.ident != drop]
    if len(kept) == len(mechanisms):
        raise CoverageError('mechanism %r is not in the inventory to drop' % drop)
    full = by_class(mechanisms, controls)
    less = by_class(kept, controls)
    return {
        'dropped': drop,
        'with_it': {c: {'mechanisms': full[c]['mechanisms'],
                        'uncovered': len(full[c]['uncovered'])} for c in CLASSES},
        'without_it': {c: {'mechanisms': less[c]['mechanisms'],
                           'uncovered': len(less[c]['uncovered'])} for c in CLASSES},
    }


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def build_report():
    ctls = estate_controls()
    return {
        'effects': list(EFFECTS),
        'controls': [{'name': c.name, 'effect': c.effect,
                      'addresses': list(c.addresses), 'note': c.note} for c in ctls],
        'by_effect': by_effect(ctls),
        'by_class': by_class(ALL_MECHANISMS, ctls),
        'by_plane': plane_coverage(ALL_MECHANISMS, ctls),
        'supply_chain': coverage(SUPPLY_CHAIN, ctls),
        'timebox': unnamed_mechanism_effect(
            ALL_MECHANISMS, ctls, 'hardware-implant-at-odm'),
        'caveats': [
            'Every mechanism, control and coverage claim is a stated input. '
            'This is not an audit of anything and the fractions mean nothing '
            'outside this script.',
            'COVERED HERE MEANS A CONTROL IS NAMED AGAINST THE MECHANISM. It '
            'does not mean the control is deployed everywhere, configured '
            'correctly, monitored, or tested. An untested control is a claim.',
            'The mechanism list is a starting point and is deliberately '
            'incomplete, which is the subject of Section D. Its own gaps are '
            'the honest demonstration of its limit.',
            'The three effects are treated as separate and uncombined. In '
            'reality they interact --- shorter dwell limits reach, and limited '
            'reach makes detection easier --- and none of that is modelled.',
            'Nothing here scores or ranks. Coverage is not risk: a fully '
            'covered mechanism of high impact may still deserve more attention '
            'than an uncovered trivial one.',
        ],
    }


def report_text(rep):
    L = []
    L.append('What a control set actually covers (Chapter 50)')
    L.append('Coverage is counted per mechanism. Every figure is a stated input.')
    L.append('')
    L.append('A. A control does one of three things, and they are not '
             'interchangeable')
    L.append('-' * 74)
    for e in EFFECTS:
        names = rep['by_effect'][e]
        L.append('  %-18s %d control(s)' % (e, len(names)))
        for n in names:
            L.append('       %s' % n)
    counts = {e: len(rep['by_effect'][e]) for e in EFFECTS}
    total = sum(counts.values())
    L.append('')
    L.append('  Shape of this set: %s.'
             % ', '.join('%d%% %s' % (round(100.0 * counts[e] / total), e)
                         for e in EFFECTS))
    worst = min(EFFECTS, key=lambda e: counts[e])
    L.append('  The thinnest kind here is "%s", with %d of %d.'
             % (worst, counts[worst], total))
    L.append('  The chapter\'s own assume-breach section asks for the opposite '
             'emphasis:')
    L.append('  when prevention fails, what decides the outcome is how far a '
             'foothold')
    L.append('  reaches and how fast you know. A control set weighted towards '
             'frequency')
    L.append('  is a set built for the world where prevention works, and the '
             'class table')
    L.append('  gives no way to see that, because it lists all three kinds in '
             'one breath')
    L.append('  under the word "stopped".')
    L.append('')
    L.append('B. Per attacker class, and what is left uncovered')
    L.append('-' * 74)
    L.append('%-14s %6s %8s %9s  %s' % ('class', 'mechs', 'covered', 'fraction',
                                        'uncovered'))
    for cls, v in rep['by_class'].items():
        L.append('%-14s %6d %8d %9.2f  %s'
                 % (cls, v['mechanisms'], v['covered'], v['fraction'],
                    ', '.join(v['uncovered'])[:36] or '--'))
    st = rep['by_class']['state']
    L.append('')
    L.append('  The state row is the one to read carefully: %d of %d '
             'mechanisms covered.'
             % (st['covered'], st['mechanisms']))
    L.append('  The chapter says that class is "stopped by assume-breach '
             'design, not by')
    L.append('  hope". Assume-breach is a design posture, not a control, and '
             'it does not')
    L.append('  appear in a coverage table at all --- which means a table like '
             'this one')
    L.append('  will always look worst against the class the chapter says you '
             'cannot')
    L.append('  prevent anyway. That is the correct answer and it is easy to '
             'misread as a')
    L.append('  shopping list.')
    L.append('')
    L.append('C. The supply chain, taken apart')
    L.append('-' * 74)
    for r in rep['supply_chain']:
        mark = 'covered   ' if r['covered'] else 'UNCOVERED '
        L.append('  %s %s' % (mark, r['mechanism']))
        L.extend(textwrap.wrap(r['description'], width=72,
                               initial_indent='             ',
                               subsequent_indent='             '))
        if r['controls']:
            L.extend(textwrap.wrap('by: ' + '; '.join(r['controls']), width=72,
                                   initial_indent='             ',
                                   subsequent_indent='                 '))
    got = sum(1 for r in rep['supply_chain'] if r['covered'])
    L.append('')
    L.append('  Image signing covers %d of %d supply-chain mechanisms here.'
             % (got, len(rep['supply_chain'])))
    L.append('  Read what it does NOT cover: a compromised vendor signing '
             'malice with')
    L.append('  its own real key, a stolen signing key, an implant that arrives '
             'before')
    L.append('  any software runs, and a third-party component inside the '
             'vendor build.')
    L.append('  In every one of those the signature verifies. Signing answers '
             '"is this')
    L.append('  the image the vendor signed?" and the supply-chain question is '
             '"should I')
    L.append('  trust what the vendor signed?" --- and those are different '
             'questions.')
    L.append('  An inventory that marks the supply-chain plane green because '
             'signing is')
    L.append('  in place has answered the first and reported the second.')
    L.append('')
    L.append('D. What the timebox does not buy')
    L.append('-' * 74)
    tb = rep['timebox']
    L.append('  Take one mechanism off the inventory and re-run:')
    L.append('      %s' % tb['dropped'])
    L.append('')
    L.append('%-14s %22s %22s' % ('class', 'with it named', 'with it unnamed'))
    for cls in CLASSES:
        a, b = tb['with_it'][cls], tb['without_it'][cls]
        L.append('%-14s %10d mech, %2d open %10d mech, %2d open'
                 % (cls, a['mechanisms'], a['uncovered'],
                    b['mechanisms'], b['uncovered']))
    L.append('')
    L.append('  The risk did not change. The report did. A mechanism nobody '
             'names scores')
    L.append('  zero, and it scores zero confidently, for as long as nobody '
             'names it ---')
    L.append('  and an hour spent well returns exactly the mechanisms you '
             'thought of in')
    L.append('  that hour. The timebox is good advice about REPETITION, which '
             'is a real')
    L.append('  defence against a changing estate. It is not evidence of '
             'completeness,')
    L.append('  and the two get conflated because the same sentence carries '
             'both.')
    L.append('  What bounds this is not more time: it is a list someone else '
             'wrote ---')
    L.append('  a published technique catalogue, an advisory for your sector, '
             'another')
    L.append('  operator\'s incident write-up --- checked against yours to find '
             'what you')
    L.append('  would never have thought of.')
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
    except CoverageError as exc:
        print('cannot evaluate: %s' % exc, file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=2) if a.json else report_text(rep))
    return 0


if __name__ == '__main__':
    sys.exit(main())
