#!/usr/bin/env python3
"""Lab 48.1 --- the fronthaul latency budget, and the boundary the chapter moved.

WHY THIS LAB EXISTS
-------------------
The chapter said this:

    "The one-way latency budget is on the order of 100 microseconds ... 100 us is
     roughly 20 km of fibre --- and that is the TOTAL budget, most of which the
     radio processing itself consumes, leaving the transport perhaps a few tens
     of microseconds, i.e. a few kilometres of reach"

The first half is right and the second half counts the same microseconds twice.

The eCPRI transport-network requirements define one-way maximum frame delay
classes --- High25, High100, High200 and High500, at 25, 100, 200 and 500
microseconds --- and those figures are the allowance for the TRANSPORT NETWORK.
The document is explicit that the requirement covers fibre propagation and
switching delay, and that giving the transport network a larger budget than the
class specifies leaves a smaller budget for the radio equipment at the ends,
which may degrade the mobile network.  In other words the radio equipment's
processing has its own separate allocation out of the overall latency; it is not
taken out of the transport class.

So subtracting radio processing from a 100 microsecond class is subtracting it
twice, and the "few kilometres" that follows is wrong by roughly a factor of
four.  Worse, it is wrong in the direction that makes engineers build something
unnecessary: it says a distributed unit must be within a couple of kilometres of
its radios when the class it was given actually allows twenty, before switching.

This computes the reach properly, from the class, the fibre, and what the hops
really cost.

    python3 fronthaul_budget.py
    python3 fronthaul_budget.py --json
    python3 test_fronthaul_budget.py

No radio, no radio unit, no distributed unit, no switch and no measurement.  The
delay classes and the frame loss ratios below are from the published eCPRI
transport requirements and are cited in the chapter; everything else --- switch
delays, frame sizes, line rates, fibre index --- is a stated input, and no figure
here is any vendor's.
"""
import argparse
import json
import sys

C_KM_PER_S = 299792.458          # speed of light in vacuum, km/s

# eCPRI transport-network one-way maximum frame delay classes, in microseconds.
# These are TRANSPORT allowances.  See the chapter's standards box for the
# citation.  The radio equipment at each end has its own separate budget.
ECPRI_DELAY_CLASSES = {
    'High25': 25.0,
    'High100': 100.0,
    'High200': 200.0,
    'High500': 500.0,
}

# eCPRI one-way maximum frame loss ratio by class of service, from the same
# document.  Note what is NOT there: the document does not specify a packet
# delay variation figure --- its phase-noise and MTIE sections are marked for
# further study --- so any jitter number you are given comes from the endpoint
# vendor or from your own requirement, not from this specification.
ECPRI_FRAME_LOSS = {'High': 1e-7, 'Medium': 1e-7, 'Low': 1e-6}


class BudgetError(ValueError):
    """The described fronthaul path cannot be evaluated."""


def propagation_us_per_km(group_index=1.4682):
    """Microseconds per kilometre of fibre, computed rather than assumed.

    The often-quoted 5 us/km is this rounded.  The group index of standard
    single-mode fibre near 1550 nm is about 1.468, which gives 4.897, so the
    round number is 2% pessimistic --- immaterial against a 100 us class, and
    worth computing anyway because the same arithmetic with the wrong index is
    how distances get quietly wrong (Chapter 43).
    """
    if group_index <= 1.0:
        raise BudgetError('a group index is greater than 1, got %r'
                          % (group_index,))
    return 1e6 / (C_KM_PER_S / group_index)


def serialisation_us(frame_bytes, line_rate_gbps):
    """Time to clock one frame onto the wire, at a stated rate."""
    if frame_bytes <= 0 or line_rate_gbps <= 0:
        raise BudgetError('frame size and line rate are positive')
    return (frame_bytes * 8.0) / (line_rate_gbps * 1e9) * 1e6


def path_delay_us(km, hops, delay_class='High100', switch_us=2.0,
                  frame_bytes=1500, line_rate_gbps=25.0, group_index=1.4682,
                  other_us=0.0):
    """Total one-way transport delay, against the class's allowance.

    First service-frame bit at ingress UNI to last bit at egress UNI.
    hops is the number of switching elements: hops+1 equal-rate transmissions.
    Each switch adds processing (excluding serialisation) and another
    serialisation relative to a direct link, because
    a store-and-forward device cannot begin transmitting until it has received
    the frame.  That second term is the one people forget, and at low line rates
    it dominates: a 1500-byte frame is 0.48 us at 25 Gb/s and 12 us at 1 Gb/s.
    """
    if delay_class not in ECPRI_DELAY_CLASSES:
        raise BudgetError('unknown delay class %r; known: %s'
                          % (delay_class, ', '.join(sorted(ECPRI_DELAY_CLASSES))))
    if km < 0 or hops < 0 or switch_us < 0 or other_us < 0:
        raise BudgetError('distances, hop counts and delays are not negative')

    per_km = propagation_us_per_km(group_index)
    ser = serialisation_us(frame_bytes, line_rate_gbps)
    prop = km * per_km
    sw = hops * switch_us
    serial = (hops + 1) * ser
    total = prop + sw + serial + other_us
    allowance = ECPRI_DELAY_CLASSES[delay_class]
    return {'delay_class': delay_class, 'allowance_us': allowance,
            'propagation_us': prop, 'switching_us': sw,
            'serialisation_us': serial, 'other_us': other_us,
            'total_us': total, 'margin_us': allowance - total,
            'meets': total <= allowance, 'km': km, 'hops': hops,
            'us_per_km': per_km, 'serialisation_per_hop_us': ser}


def max_km(delay_class='High100', hops=0, switch_us=2.0, frame_bytes=1500,
           line_rate_gbps=25.0, group_index=1.4682, other_us=0.0):
    """The fibre left after everything else has taken its share.  May be < 0."""
    d = path_delay_us(0.0, hops, delay_class, switch_us, frame_bytes,
                      line_rate_gbps, group_index, other_us)
    return d['margin_us'] / propagation_us_per_km(group_index)


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def section_a():
    print('A. The classes, and the reach each one buys before anything else')
    print('-' * 74)
    per_km = propagation_us_per_km()
    print('  fibre group index 1.4682 gives %.3f us/km (the usual "5" rounded)'
          % per_km)
    print()
    print('%-10s %12s %16s' % ('class', 'allowance', 'direct 25G link'))
    out = {}
    for name in ('High25', 'High100', 'High200', 'High500'):
        km = max_km(name, hops=0)
        out[name] = km
        print('%-10s %9.0f us %13.1f km' % (name, ECPRI_DELAY_CLASSES[name], km))
    print()
    print('  These are the TRANSPORT network\'s allowance.  The radio equipment')
    print('  at each end has its own budget out of the overall latency, which is')
    print('  why the specification warns that giving transport MORE than its')
    print('  class leaves the radio equipment less.  It is not a total from')
    print('  which radio processing is then subtracted.')
    print()
    return out


def section_b():
    print('B. The chapter\'s arithmetic, and the same class done properly')
    print('-' * 74)
    print('  The chapter took the 100 us class as a total, said radio processing')
    print('  consumes "most" of it, left the transport "a few tens of')
    print('  microseconds", and concluded "a few kilometres".  Reading "most" as')
    print('  70 us --- charitable, since "a few tens" left for transport implies')
    print('  at least that --- gives:')
    print()
    print('%-44s %12s' % ('reading', 'reach'))
    wrong = max_km('High100', hops=0, other_us=70.0)
    right = max_km('High100', hops=0)
    print('%-44s %9.1f km' % ('chapter: 100 us less 70 us of radio', wrong))
    print('%-44s %9.1f km' % ('spec: High100 is the transport allowance', right))
    print()
    print('  A factor of %.1f, and it points the wrong way: a design team told'
          % (right / wrong))
    print('  the distributed unit must sit within %.0f km will build hub sites' % wrong)
    print('  it did not need, when the class it was given allows %.0f.' % right)
    print()
    return {'chapter_km': wrong, 'spec_km': right}


def section_c():
    print('C. What the hops actually cost, which is where the reach really goes')
    print('-' * 74)
    print('  High100, 1500-byte frames, 2 us per switch.')
    print()
    print('%6s %14s %14s %14s %12s'
          % ('hops', 'at 1 Gb/s', 'at 10 Gb/s', 'at 25 Gb/s', 'at 100 Gb/s'))
    rows = []
    for hops in (0, 1, 2, 4, 8):
        line = []
        for rate in (1.0, 10.0, 25.0, 100.0):
            line.append(max_km('High100', hops=hops, line_rate_gbps=rate))
        rows.append((hops, line))
        print('%6d %11.1f km %11.1f km %11.1f km %9.1f km'
              % (hops, line[0], line[1], line[2], line[3]))
    print()
    ser1 = serialisation_us(1500, 1.0)
    ser25 = serialisation_us(1500, 25.0)
    print('  One 1500-byte frame takes %.2f us to clock out at 1 Gb/s and %.2f us'
          % (ser1, ser25))
    print('  at 25 Gb/s.  A store-and-forward switch must receive the whole frame')
    print('  before sending: count one initial transmission plus each switch.')
    print('  at 1 Gb/s eight hops spend %.0f us of a %.0f us class on'
          % (9 * ser1 + 8 * 2.0, ECPRI_DELAY_CLASSES['High100']))
    print('  serialisation and switching alone, leaving %.1f km of fibre.'
          % rows[-1][1][0])
    print()
    print('  Which term dominates depends on the distance, rates, architecture')
    print('  and queuing. This table assumes equal rates and zero queuing.')
    print()
    return rows


def section_d():
    print('D. A path evaluated against its class')
    print('-' * 74)
    cases = [
        ('12 km, 2 hops at 25G', dict(km=12.0, hops=2, line_rate_gbps=25.0)),
        ('the same path against the High25 class',
         dict(km=12.0, hops=2, line_rate_gbps=25.0, delay_class='High25')),
        ('15 km, 4 hops at 10G', dict(km=15.0, hops=4, line_rate_gbps=10.0)),
        ('the same path at 1G', dict(km=15.0, hops=4, line_rate_gbps=1.0)),
        ('40 km, 1 hop at 100G, High200 class',
         dict(km=40.0, hops=1, line_rate_gbps=100.0, delay_class='High200')),
    ]
    print('%-40s %8s %9s %9s %8s'
          % ('path', 'total', 'allowance', 'margin', 'verdict'))
    out = []
    for label, kw in cases:
        d = path_delay_us(**kw)
        out.append((label, d))
        print('%-40s %6.1f us %6.0f us %6.1f us %8s'
              % (label, d['total_us'], d['allowance_us'], d['margin_us'],
                 'meets' if d['meets'] else 'FAILS'))
    print()
    # commentary derived from the rows, not asserted alongside them
    fast, slow = out[2][1], out[3][1]
    if fast['meets'] and not slow['meets']:
        print('  The same %.0f km path meets its class at 10 Gb/s and fails it at'
              % fast['km'])
        print('  1 Gb/s.  Nothing about the fibre changed: %.1f us of the'
              % (slow['serialisation_us'] - fast['serialisation_us']))
        print('  difference is serialisation, because a store-and-forward hop')
        print('  cannot start sending a frame until it has received all of it.')
    else:
        print('  Rows three and four differ only in line rate; compare their')
        print('  serialisation columns.')
    tight, tighter = out[0][1], out[1][1]
    print()
    print('  And the path that meets High100 with %.0f us to spare misses High25'
          % tight['margin_us'])
    print('  by %.0f us --- the same path, the same fibre, a different class.'
          % abs(tighter['margin_us']))
    print('  The class is part of the requirement, not a detail of it.')
    print()
    return out


def section_e():
    print('E. What the transport specification does not give you')
    print('-' * 74)
    print('  one-way maximum frame loss ratio, by class of service:')
    for k in ('High', 'Medium', 'Low'):
        print('      %-8s %.0e' % (k, ECPRI_FRAME_LOSS[k]))
    print()
    print('  and packet delay variation: NOT SPECIFIED by that document, whose')
    print('  phase-noise and MTIE sections are marked for further study.')
    print()
    print('  This matters because the chapter said fronthaul needs "near-zero')
    print('  jitter" and the old lab enforced a 1 us limit, neither of which')
    print('  comes from anywhere.  A delay variation requirement for your link')
    print('  comes from the radio equipment vendor at the ends, or from your own')
    print('  engineering, and it has to be stated as a number with a measurement')
    print('  method --- not asserted as a property of fronthaul.')
    print()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    if args.json:
        json.dump({'classes': ECPRI_DELAY_CLASSES, 'frame_loss': ECPRI_FRAME_LOSS,
                   'us_per_km': propagation_us_per_km(),
                   'reach_km': {k: max_km(k) for k in ECPRI_DELAY_CLASSES}},
                  sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write('\n')
        return 0
    print('Fronthaul latency budget (Chapter 48, the fronthaul section)')
    print('Delay classes and frame loss ratios are from the published eCPRI')
    print('transport requirements; everything else is a stated input.')
    print()
    section_a()
    section_b()
    section_c()
    section_d()
    section_e()
    print('What this does NOT establish')
    print('-' * 74)
    print('- No radio, radio unit, distributed unit, switch or measurement of')
    print('  any kind. Switch delays, frame sizes and line rates are inputs.')
    print('- A real switch\'s delay depends on its architecture, its load and')
    print('  the frame size, and is not one number. Two microseconds is a')
    print('  placeholder for whatever yours is measured to be.')
    print('- Cut-through switching changes the serialisation term materially,')
    print('  and is not modelled here.')
    print('- Queuing behind other traffic is not modelled at all; it is the')
    print('  reason fronthaul gets scheduling treatment. Add a justified bound')
    print('  through other_us and verify it by measurement under load.')
    print('- Meeting the class is necessary, not sufficient: the radio')
    print('  equipment at the ends has its own budget, and the service works')
    print('  when the whole thing is measured end to end.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
