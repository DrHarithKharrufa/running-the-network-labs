#!/usr/bin/env python3
"""Lab 45.2 --- flexgrid as it is actually defined, and why free spectrum is not free.

WHY THIS EXISTS
---------------
Chapter 45 described flexgrid as dividing the spectrum into "fine 12.5 GHz
slices" that a channel claims as many of as it needs.  That is half the
definition and it hides the half that matters.

The flexible grid has TWO granularities, and they are different numbers:

  the nominal central frequency granularity, 6.25 GHz --- where a channel's
  centre may sit, counted as n steps from 193.1 THz;
  the slot width granularity, 12.5 GHz --- how wide the channel's slot is,
  counted as m of those.

So a channel is (n, m), its centre is 193.1 THz + n x 6.25 GHz, and its slot is
m x 12.5 GHz wide.  The 6.25 GHz centre step is not a detail: it is what lets a
wide channel sit BETWEEN the positions the old fixed grid allowed, which is most
of the point of having a flexible grid at all.

The chapter also said that a colourless, directionless, contentionless ROADM
lets you "assign any wavelength to any router in any direction by software".
CDC removes the patching constraint.  It does not remove the SPECTRUM
constraint, and this lab exists to show the difference: a fibre can have ample
free spectrum and still have nowhere to put a channel, because the free
spectrum is in pieces and a channel needs its slots CONTIGUOUS.

WHAT IS NOT MODELLED
--------------------
No ROADM, no WSS, no line system, no planning tool.  This allocates integers on
a grid.  It has no OSNR, no filtering penalty, no path computation across
several links, and no notion of which wavelengths a given node can actually
reach.  It cannot tell you whether a channel would work --- only whether there
is anywhere to put it.

    python3 spectrum_plan.py
    python3 spectrum_plan.py --json
    python3 test_spectrum_plan.py
"""
import argparse
import json
import sys

ANCHOR_THZ = 193.1
CENTRE_GRANULARITY_GHZ = 6.25      # the n step
SLOT_GRANULARITY_GHZ = 12.5        # the m unit


class GridError(ValueError):
    """The request cannot be expressed on the flexible grid."""


def channel(n, m, label=''):
    """A flexgrid channel, as the grid actually defines one.

    n : centre index, in 6.25 GHz steps from the anchor. May be negative.
    m : slot width, in 12.5 GHz units. At least 1.
    """
    if not isinstance(n, int):
        raise GridError('n is an integer number of 6.25 GHz steps, got %r' % (n,))
    if not isinstance(m, int) or m < 1:
        raise GridError('m is a positive integer number of 12.5 GHz slots, '
                        'got %r' % (m,))
    centre = ANCHOR_THZ * 1000.0 + n * CENTRE_GRANULARITY_GHZ
    width = m * SLOT_GRANULARITY_GHZ
    return {'label': label or 'n=%d m=%d' % (n, m), 'n': n, 'm': m,
            'centre_ghz': centre, 'width_ghz': width,
            'low_ghz': centre - width / 2.0, 'high_ghz': centre + width / 2.0}


def slots_for(width_ghz):
    """The m a channel of this width needs --- rounded UP, because you cannot
    have a fraction of a slot, and the rounding is where spectrum is lost."""
    if width_ghz <= 0:
        raise GridError('a width is positive, got %r' % (width_ghz,))
    m = 1
    while m * SLOT_GRANULARITY_GHZ < width_ghz:
        m += 1
    return {'needed_ghz': width_ghz, 'm': m,
            'allocated_ghz': m * SLOT_GRANULARITY_GHZ,
            'wasted_ghz': m * SLOT_GRANULARITY_GHZ - width_ghz}


# --------------------------------------------------------------------------
# a fibre's spectrum, as a set of 12.5 GHz slots
# --------------------------------------------------------------------------
class Spectrum:
    """One fibre's usable band, tracked in 12.5 GHz slots.

    Slots are indexed from 0 at the low edge. A channel occupies a contiguous
    run of them, which is the constraint the chapter's account leaves out.
    """

    def __init__(self, band_ghz=4800.0):
        if band_ghz <= 0:
            raise GridError('a band is positive, got %r' % (band_ghz,))
        self.slots = int(band_ghz // SLOT_GRANULARITY_GHZ)
        self.occupied = {}          # slot index -> label

    def free_slots(self):
        return [i for i in range(self.slots) if i not in self.occupied]

    def free_ghz(self):
        return len(self.free_slots()) * SLOT_GRANULARITY_GHZ

    def runs(self):
        """Contiguous free runs, as (start, length) --- longest first."""
        out, start = [], None
        for i in range(self.slots + 1):
            free = i < self.slots and i not in self.occupied
            if free and start is None:
                start = i
            elif not free and start is not None:
                out.append((start, i - start))
                start = None
        return sorted(out, key=lambda r: -r[1])

    def largest_run_ghz(self):
        r = self.runs()
        return r[0][1] * SLOT_GRANULARITY_GHZ if r else 0.0

    def place(self, m, label, at=None):
        """First-fit placement of m contiguous slots. Returns the start, or None.

        None is not an error and is the whole point: the request was legal, the
        fibre has room, and there is nowhere to put it.
        """
        if not isinstance(m, int) or m < 1:
            raise GridError('m is a positive integer, got %r' % (m,))
        if at is not None:
            if at < 0 or at + m > self.slots:
                raise GridError('slots %d..%d are outside the band'
                                % (at, at + m - 1))
            if any(i in self.occupied for i in range(at, at + m)):
                return None
            for i in range(at, at + m):
                self.occupied[i] = label
            return at
        for start, length in sorted(self.runs()):
            if length >= m:
                for i in range(start, start + m):
                    self.occupied[i] = label
                return start
        return None

    def release(self, label):
        n = len([i for i, l in self.occupied.items() if l == label])
        self.occupied = {i: l for i, l in self.occupied.items() if l != label}
        return n

    def fragmentation(self):
        """How broken up the free spectrum is: 0 is one clean block, 1 is dust."""
        free = len(self.free_slots())
        if free == 0:
            return 0.0
        return 1.0 - (max(r[1] for r in self.runs()) / float(free))


# --------------------------------------------------------------------------
# the worked scenario
# --------------------------------------------------------------------------
def build():
    """Fill a band, take some channels down, then try to add a wide one.

    This is a constructed allocation history, not an observed network.
    It demonstrates fragmentation and a static repacking calculation.
    """
    sp = Spectrum(4800.0)
    events = []

    def note(what, ok=None, plan=None):
        plan = sp if plan is None else plan
        events.append({'event': what, 'free_ghz': plan.free_ghz(),
                       'largest_run_ghz': plan.largest_run_ghz(),
                       'fragmentation': plan.fragmentation(), 'result': ok})

    note('empty band')
    # a long-lived mix, filling the band as a working fibre does: narrow
    # 37.5 GHz services interleaved with wider 75 GHz ones
    k = 0
    while True:
        m = 3 if k % 2 == 0 else 6
        if sp.place(m, 'svc-%03d' % k) is None:
            break
        k += 1
    note('%d services placed, alternating 37.5 and 75 GHz, band nearly full' % k)

    # over a few years the narrow ones are decommissioned, one by one
    for j in range(0, k, 2):
        sp.release('svc-%03d' % j)
    note('every 37.5 GHz service is decommissioned over the following years')

    # Abstract width request: the label is not a qualified 800G mode.
    # It wants 100 GHz: eight contiguous width increments.
    want = slots_for(100.0)
    start = sp.place(want['m'], 'new-800G')
    note('an 800G channel asks for %.1f GHz (%d slots)'
         % (want['needed_ghz'], want['m']),
         ok=('placed at slot %d' % start) if start is not None
         else 'NO ROOM --- the free spectrum is not contiguous')

    # defragment: rebuild from scratch in width order
    remaining = sorted(set(sp.occupied.values()))
    widths = {}
    for lbl in remaining:
        widths[lbl] = len([i for i, l in sp.occupied.items() if l == lbl])
    sp2 = Spectrum(4800.0)
    for lbl in sorted(remaining, key=lambda l: -widths[l]):
        sp2.place(widths[lbl], lbl)
    start2 = sp2.place(want['m'], 'new-800G')
    note('after defragmenting the static plan (no live service moved)',
         ok=('placed at slot %d' % start2) if start2 is not None
         else 'still no room', plan=sp2)
    return {'events': events, 'want': want,
            'fragmented_free_ghz': events[3]['free_ghz'],
            'fragmented_largest_ghz': events[3]['largest_run_ghz']}


def analyse():
    widths = [slots_for(w) for w in (37.5, 50.0, 62.5, 75.0, 87.5, 100.0)]
    examples = [channel(0, 4, 'centred on the anchor'),
                channel(3, 4, 'centred between two old 50 GHz slots'),
                channel(-8, 8, 'a wide channel, low in the band')]
    return {'granularities': {'centre_ghz': CENTRE_GRANULARITY_GHZ,
                              'slot_ghz': SLOT_GRANULARITY_GHZ},
            'widths': widths, 'examples': examples, 'scenario': build()}


def report(a):
    print('Flexgrid allocation. Integers on a grid --- no ROADM, no WSS, no line')
    print('system, no planning tool, and no OSNR anywhere in this file.\n')

    g = a['granularities']
    print('The grid has TWO granularities, and they are different numbers:')
    print('    centre frequency   %.2f GHz steps   (the n index)' % g['centre_ghz'])
    print('    slot width         %.2f GHz units   (the m count)' % g['slot_ghz'])
    print('A channel is (n, m): centre = 193.1 THz + n x 6.25 GHz, slot width =')
    print('m x 12.5 GHz. Quoting only the 12.5 leaves out the step that lets a')
    print('wide channel sit between the positions the old fixed grid allowed.\n')

    print('%34s | %5s | %5s | %14s | %s'
          % ('channel', 'n', 'm', 'centre (GHz)', 'occupies (GHz)'))
    print('-' * 86)
    for c in a['examples']:
        print('%34s | %5d | %5d | %14.2f | %.2f to %.2f'
              % (c['label'], c['n'], c['m'], c['centre_ghz'],
                 c['low_ghz'], c['high_ghz']))

    print('\nSlot widths round UP, and the rounding is spectrum you have bought')
    print('and cannot use:')
    print('%14s | %4s | %12s | %s' % ('channel needs', 'm', 'allocated', 'wasted'))
    print('-' * 52)
    for w in a['widths']:
        print('%11.1f GHz | %4d | %9.1f GHz | %.1f GHz'
              % (w['needed_ghz'], w['m'], w['allocated_ghz'], w['wasted_ghz']))

    print('\nAnd now the constraint a "colourless, directionless, contentionless"')
    print('ROADM does not remove.\n')
    print('%66s | %10s | %12s | %6s'
          % ('', 'free', 'largest run', 'frag'))
    print('-' * 104)
    for e in a['scenario']['events']:
        print('%66s | %7.1f GHz | %9.1f GHz | %5.0f%%'
              % (e['event'][:66], e['free_ghz'], e['largest_run_ghz'],
                 e['fragmentation'] * 100))
        if e['result']:
            print('%66s   -> %s' % ('', e['result']))

    s = a['scenario']
    print('\nAt the moment of the request the fibre had %.1f GHz free and could'
          % s['fragmented_free_ghz'])
    print('not accept a %.1f GHz channel, because the largest contiguous run was'
          % s['want']['needed_ghz'])
    print('%.1f GHz. The spectrum was there; it was in the wrong shape.'
          % s['fragmented_largest_ghz'])
    print('\nCDC removes the constraint that a given add/drop port is wired to a')
    print('given wavelength and a given direction. It does not create contiguous')
    print('spectrum, it does not create free spectrum on the OTHER links of the')
    print('path --- which must all have the same slots free, since nothing')
    print('converts the wavelength in between --- and it does not supply the')
    print('OSNR. "Any wavelength to any router in any direction by software" is')
    print('a statement about patching, and the interesting constraints are')
    print('elsewhere.')
    print('\nThe defragmentation row is the honest ending: the spectrum can be')
    print('made to fit in a fresh static plan. No live service was moved.')
    print('Executing that plan needs a qualified migration procedure, spare')
    print('resources or an agreed maintenance window; software alone does not')
    print('prove a hitless migration. The 800G label is illustrative, not a mode.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        a = analyse()
    except GridError as e:
        print('grid error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(a, indent=2))
    else:
        report(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
