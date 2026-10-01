#!/usr/bin/env python3
"""Lab 48.2 --- where fronthaul bandwidth actually comes from.

WHY THIS LAB EXISTS
-------------------
The chapter described low-split fronthaul as needing "huge bandwidth" and left it
there, which is not a number anybody can design with and hides the thing that
actually decides it.  Fronthaul capacity is not a property of the word
"fronthaul".  It is arithmetic on the radio configuration:

    subcarriers x symbols per second x 2 (I and Q) x bits per sample x streams

and every one of those five terms is a choice somebody made.  Double the channel
bandwidth and it doubles.  Double the antenna streams and it doubles again.
Compress the samples from 16 bits to 9 and it falls by nearly half.  A chapter
that says "huge" cannot tell a reader that a 100 MHz cell with four streams needs
a different transport from a 100 MHz cell with sixty-four, which is the single
most consequential fact about carrying it.

This computes the rate from the configuration, so the reader can see which lever
moves it and by how much.

    python3 fronthaul_rate.py
    python3 fronthaul_rate.py --json
    python3 test_fronthaul_rate.py

No radio, no radio unit, no distributed unit and no measurement.  The structure
below --- twelve subcarriers to a resource block, fourteen symbols per normal-cyclic-prefix slot,
subcarrier spacing doubling with the numerology --- is how the frame structure is
defined.  Every other figure, including the resource-block counts, the sample
widths, the compression ratios and the overhead, is a stated input, and no figure
here is any vendor's.
"""
import argparse
import json
import sys
import math

SUBCARRIERS_PER_RB = 12
SYMBOLS_PER_SLOT = 14


class RateError(ValueError):
    """The described radio configuration cannot be evaluated."""


def scs_khz(numerology):
    """Subcarrier spacing: 15 kHz doubling with each step of the numerology."""
    if not isinstance(numerology, int) or isinstance(numerology, bool) or numerology < 0 or numerology > 6:
        raise RateError('numerology is 0..6, got %r' % (numerology,))
    return 15.0 * (2 ** numerology)


def slots_per_second(numerology):
    """One subframe is a millisecond and holds 2^u slots of 14 symbols."""
    return 1000.0 * (2 ** numerology)


def symbols_per_second(numerology):
    return slots_per_second(numerology) * SYMBOLS_PER_SLOT


# ILLUSTRATIVE resource-block counts.  The number of resource blocks that fit in
# a channel depends on the bandwidth AND the subcarrier spacing, and is fixed by
# a table in the radio specification; these entries are plausible values used to
# make the arithmetic concrete, not a reproduction of that table.
RB_COUNT = {
    (20.0, 1): 51,
    (40.0, 1): 106,
    (50.0, 0): 270,
    (100.0, 1): 273,
    (100.0, 3): 66,
    (200.0, 3): 132,
    (400.0, 3): 264,
}


def resource_blocks(bandwidth_mhz, numerology):
    scs_khz(numerology)  # refuse fractional numerology instead of truncating it
    key = (float(bandwidth_mhz), numerology)
    if key not in RB_COUNT:
        raise RateError('no resource-block count recorded for %g MHz at '
                        'numerology %d; the count comes from the radio '
                        'specification\'s channel table, so add it rather than '
                        'guessing' % (bandwidth_mhz, numerology))
    return RB_COUNT[key]


def occupied_bandwidth_mhz(bandwidth_mhz, numerology):
    """How much of the channel the subcarriers actually occupy."""
    rb = resource_blocks(bandwidth_mhz, numerology)
    return rb * SUBCARRIERS_PER_RB * scs_khz(numerology) / 1000.0


def fronthaul_gbps(bandwidth_mhz, numerology, streams, bits_per_sample=16,
                   overhead_percent=10.0, duty_cycle=1.0):
    """Frequency-domain IQ rate for one carrier, before and after overhead.

    This is the shape of a lower-layer split that carries frequency-domain IQ
    after precoding: what goes on the wire is the resource elements, twice (I
    and Q), per stream.

    streams is the number of spatial streams or antenna ports actually carried
    --- and this is the term people get wrong, because a sixty-four element
    array does not necessarily carry sixty-four streams.  How many it carries
    is a property of the split and the radio's internal architecture, and it is
    the difference between a link you can build and one you cannot.

    duty_cycle scales the AVERAGE across a time-division pattern. It does not
    reduce the instantaneous active-slot rate or prove a burst can meet delay.
    Normal cyclic prefix and full resource-element occupancy are assumed.
    Compression overhead and actual packetisation must be specified separately.
    """
    if not isinstance(streams, int) or isinstance(streams, bool) or streams < 1:
        raise RateError('a carrier has at least one stream, got %r' % (streams,))
    if not isinstance(bits_per_sample, int) or isinstance(bits_per_sample, bool) or bits_per_sample < 1:
        raise RateError('samples have at least one bit')
    if not math.isfinite(overhead_percent) or overhead_percent < 0:
        raise RateError('overhead is not negative')
    if not 0 < duty_cycle <= 1:
        raise RateError('a duty cycle is in (0, 1], got %r' % (duty_cycle,))

    rb = resource_blocks(bandwidth_mhz, numerology)
    subcarriers = rb * SUBCARRIERS_PER_RB
    re_per_s = subcarriers * symbols_per_second(numerology) * duty_cycle
    payload_bps = re_per_s * 2.0 * bits_per_sample * streams
    with_overhead = payload_bps * (1.0 + overhead_percent / 100.0)
    return {
        'bandwidth_mhz': bandwidth_mhz, 'numerology': numerology,
        'scs_khz': scs_khz(numerology), 'resource_blocks': rb,
        'subcarriers': subcarriers,
        'symbols_per_second': symbols_per_second(numerology),
        'streams': streams, 'bits_per_sample': bits_per_sample,
        'duty_cycle': duty_cycle,
        'resource_elements_per_s': re_per_s,
        'payload_gbps': payload_bps / 1e9,
        'with_overhead_gbps': with_overhead / 1e9,
        'overhead_percent': overhead_percent,
    }


def links_needed(gbps, link_rate_gbps, usable_fraction=0.9):
    """Aggregate capacity lower bound, assuming traffic can be distributed.

    This is not proof that a LAG/ECMP hash can divide a single fronthaul flow.
    """
    if link_rate_gbps <= 0:
        raise RateError('a link rate is positive')
    if not 0 < usable_fraction <= 1:
        raise RateError('the usable fraction is in (0, 1]')
    import math
    return int(math.ceil(gbps / (link_rate_gbps * usable_fraction)))


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def section_a():
    print('A. The five terms, and what each one is')
    print('-' * 74)
    r = fronthaul_gbps(100.0, 1, streams=4)
    print('  100 MHz, 30 kHz subcarrier spacing, 4 streams, 16-bit samples:')
    print('    %-34s %s' % ('resource blocks', r['resource_blocks']))
    print('    %-34s %s' % ('subcarriers (12 per block)', r['subcarriers']))
    print('    %-34s %.0f' % ('symbols per second', r['symbols_per_second']))
    print('    %-34s %.1f M' % ('resource elements per second',
                                r['resource_elements_per_s'] / 1e6))
    print('    %-34s x2 (I and Q) x%d bits x%d streams'
          % ('each element carries', r['bits_per_sample'], r['streams']))
    print('    %-34s %.2f Gb/s' % ('payload', r['payload_gbps']))
    print('    %-34s %.2f Gb/s' % ('with %g%% overhead' % r['overhead_percent'],
                                   r['with_overhead_gbps']))
    print()
    print('  That is the whole calculation.  Nothing about it is specific to')
    print('  fronthaul except which five numbers you are handed.')
    print()
    return r


def section_b():
    print('B. Which lever moves it, and by how much')
    print('-' * 74)
    base = fronthaul_gbps(100.0, 1, streams=4)['with_overhead_gbps']
    rows = [
        ('the configuration above', dict(bandwidth_mhz=100.0, numerology=1, streams=4)),
        ('half the channel bandwidth', dict(bandwidth_mhz=50.0, numerology=0, streams=4)),
        ('twice the streams', dict(bandwidth_mhz=100.0, numerology=1, streams=8)),
        ('sixteen streams', dict(bandwidth_mhz=100.0, numerology=1, streams=16)),
        ('sixty-four streams', dict(bandwidth_mhz=100.0, numerology=1, streams=64)),
        ('9-bit compressed samples',
         dict(bandwidth_mhz=100.0, numerology=1, streams=4, bits_per_sample=9)),
        ('400 MHz at 120 kHz spacing, 2 streams',
         dict(bandwidth_mhz=400.0, numerology=3, streams=2)),
    ]
    print('%-40s %12s %10s' % ('configuration', 'rate', 'vs base'))
    out = []
    for label, kw in rows:
        r = fronthaul_gbps(**kw)
        out.append((label, r))
        print('%-40s %9.2f Gb/s %9.2fx'
              % (label, r['with_overhead_gbps'], r['with_overhead_gbps'] / base))
    print()
    print('  Streams are the term that runs away: the same 100 MHz cell needs')
    print('  %.1f Gb/s at four and %.1f Gb/s at sixty-four.  That is the'
          % (out[0][1]['with_overhead_gbps'], out[4][1]['with_overhead_gbps']))
    print('  difference between one link and a bundle of them, and it is decided')
    print('  by the radio architecture rather than by anything a transport')
    print('  engineer controls --- which is exactly why it has to be ASKED, and')
    print('  why "huge bandwidth" is not an answer.')
    print()
    print('  Compression is the one lever that is negotiable: %d bits to %d'
          % (out[0][1]['bits_per_sample'], out[5][1]['bits_per_sample']))
    print('  takes %.2f Gb/s to %.2f, a %.0f%% saving, at a cost in signal'
          % (out[0][1]['with_overhead_gbps'], out[5][1]['with_overhead_gbps'],
             100 * (1 - out[5][1]['with_overhead_gbps']
                    / out[0][1]['with_overhead_gbps'])))
    print('  quality that the radio team owns and must agree to.')
    print()
    return out


def section_c():
    print('C. What that means in links')
    print('-' * 74)
    print('%-34s %11s %8s %8s %9s'
          % ('configuration', 'rate', 'at 10G', 'at 25G', 'at 100G'))
    for label, kw in (('100 MHz, 4 streams', dict(bandwidth_mhz=100.0, numerology=1, streams=4)),
                      ('100 MHz, 16 streams', dict(bandwidth_mhz=100.0, numerology=1, streams=16)),
                      ('100 MHz, 64 streams', dict(bandwidth_mhz=100.0, numerology=1, streams=64)),
                      ('100 MHz, 64 streams, 9-bit',
                       dict(bandwidth_mhz=100.0, numerology=1, streams=64,
                            bits_per_sample=9))):
        r = fronthaul_gbps(**kw)
        g = r['with_overhead_gbps']
        print('%-34s %8.1f Gb/s %6d %8d %9d'
              % (label, g, links_needed(g, 10.0), links_needed(g, 25.0),
                 links_needed(g, 100.0)))
    print()
    print('  Aggregate lower bounds at 90% usable, assuming feasible distribution.')
    print('  LAG hashing does not split one flow automatically. Three identical cells')
    print('  triple the aggregate demand, before any protection path. This helps')
    print('  decides whether a site needs a fibre pair, a wavelength or a')
    print('  bundle --- and it comes from the radio configuration, which means')
    print('  a transport design that has not been given it is not a design.')
    print()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    if args.json:
        json.dump({'base': fronthaul_gbps(100.0, 1, streams=4),
                   'sweep': {s: fronthaul_gbps(100.0, 1, streams=s)['with_overhead_gbps']
                             for s in (2, 4, 8, 16, 32, 64)}},
                  sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write('\n')
        return 0
    print('Fronthaul capacity from the radio configuration (Chapter 48)')
    print('Frame structure is as specified; every other figure is an input.')
    print()
    section_a()
    section_b()
    section_c()
    print('What this does NOT establish')
    print('-' * 74)
    print('- No radio, radio unit, distributed unit or measurement of any kind.')
    print('- The resource-block counts are plausible values, not a reproduction')
    print('  of the specification\'s channel table. Take yours from the table.')
    print('- Sample widths, compression ratios and the overhead percentage are')
    print('  stated inputs. A real split\'s framing, control and management')
    print('  traffic, and its compression scheme, come from the interface')
    print('  specification and the equipment at both ends.')
    print('- Streams are not antenna elements. How many streams a given radio')
    print('  puts on the wire is a property of its architecture and the split,')
    print('  and it is the question to ask first.')
    print('- Nothing here sizes a real link. It shows which five numbers decide')
    print('  the answer, so that a transport engineer can ask for them.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
