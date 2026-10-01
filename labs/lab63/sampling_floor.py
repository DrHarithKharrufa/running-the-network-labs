#!/usr/bin/env python3
"""Lab 63.1 --- what 1-in-N sampling can and cannot see, by selection algorithm.

THIS LAB HAS BEEN REPAIRED TWICE AND THE HISTORY IS THE LESSON.

As originally shipped it computed `packets // N` per flow and printed
"INVISIBLE (below the floor)" whenever that came to zero. That is a
deterministic counter reset at the start of every flow, and it manufactures a
hard floor by construction: a 50-packet flow at 1-in-4000 could never be seen,
so the chapter's claim that small flows are invisible was true of the model and
of nothing else. An earlier technical edit replaced it with the correct
independent-selection arithmetic, which is kept below unchanged in substance:
for selection probability p = 1/N and a k-packet flow,

    P(observed at least once) = 1 - (1 - 1/N)^k

so at k = N the answer is about 63.2 per cent and there is no threshold.

What that edit did not supply, and what is added here, is the OTHER half of the
same question. Real exporters do not all select independently, and RFC 3176
(the sFlow architecture) describes a counter-based sampler explicitly:

    "When the counter reaches zero a sample is taken"

with the counter reloaded from a random skip, subject to

    "the sequence of random integers used over time should be such that
     (1) Total_Packets/Total_Samples = Rate"

and the practical note that

    "A uniform distribution random number generator is very effective. The
     range of skip counts (the variance) does not significantly affect
     results; variation of +-10% of the mean value is sufficient."

The randomisation is not decoration. A counter with a FIXED skip is a
systematic sampler: it takes stream position p whenever p is congruent to its
phase modulo N. A periodic flow on a steady link occupies stream positions that
are themselves periodic, and when the two periods share a factor the flow is
either sampled every single time or never sampled at all --- decided by an
arbitrary phase, stable for as long as the rate is stable, and invisible in the
output. This lab computes that, and then shows that the RFC's +-10 per cent of
jitter improves detection in the constructed fixed-seed example. This is
not a guarantee for every traffic sequence or vendor implementation.

    python3 sampling_floor.py
    python3 sampling_floor.py --output result.json
    python3 sampling_floor.py --demo-original
    python3 test_sampling.py

Mathematics and seeded simulation only. No exporter, collector, ASIC or agent
was executed, and no vendor's implementation is claimed: which selector your
platform uses, and whether it jitters, is a question for its documentation.
"""
import argparse
import json
import math
import random


def integer(value, name, minimum):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError('%s must be an integer >= %d' % (name, minimum))
    return value


# ---------------------------------------------------------------------------
# Independent (Bernoulli) selection --- unchanged in substance
# ---------------------------------------------------------------------------

def seen_probability(packets, one_in):
    """P(at least one of `packets` selected) when each is taken with p=1/N."""
    k = integer(packets, 'packets', 0)
    n = integer(one_in, 'one_in', 1)
    if k == 0:
        return 0.0
    if n == 1:
        return 1.0
    return -math.expm1(k * math.log1p(-1.0 / n))


def expected_samples(packets, one_in):
    integer(packets, 'packets', 0)
    integer(one_in, 'one_in', 1)
    return packets / one_in


def monte_carlo(packets, one_in, trials=10000, seed=63):
    """Seeded cross-check of seen_probability by direct simulation."""
    integer(packets, 'packets', 0)
    integer(one_in, 'one_in', 1)
    integer(trials, 'trials', 1)
    rng = random.Random(seed)
    hits = 0
    for _ in range(trials):
        # A selection decision per packet, rather than a deterministic
        # every-Nth counter reset at the start of each flow.
        hits += any(rng.random() < 1.0 / one_in for _ in range(packets))
    return hits / trials


# ---------------------------------------------------------------------------
# Systematic selection, and the phase problem
# ---------------------------------------------------------------------------

def systematic_seen(positions, one_in, phase):
    """Would a fixed-skip sampler take any packet at these stream positions?

    A systematic sampler with period N and phase f selects stream position p
    exactly when p mod N == f. `positions` are the flow's packet positions in
    the interleaved stream of every packet crossing the observation point.
    """
    n = integer(one_in, 'one_in', 1)
    integer(phase, 'phase', 0)
    if phase >= n:
        raise ValueError('phase must be less than the sampling period')
    return any(p % n == phase for p in positions)


def periodic_positions(burst_packets, bursts, packets_between_bursts,
                       start=0):
    """Stream positions of a periodic flow on a steady link.

    A beacon that sends `burst_packets` packets every interval, on a link
    carrying `packets_between_bursts` packets per interval, occupies positions
    start, start+1, ... then the same offsets one interval later, and so on.
    """
    integer(burst_packets, 'burst_packets', 1)
    integer(bursts, 'bursts', 1)
    integer(packets_between_bursts, 'packets_between_bursts', 1)
    integer(start, 'start', 0)
    out = []
    for b in range(bursts):
        base = start + b * packets_between_bursts
        out.extend(range(base, base + burst_packets))
    return out


def systematic_phase_sweep(burst_packets, bursts, packets_between_bursts,
                           one_in, start=0):
    """Over every phase a fixed-skip sampler could have, what happens?

    Returns the fraction of phases that see the flow at least once, and ---
    the part that matters --- whether the outcome is all-or-nothing rather
    than a probability that averages out over time.
    """
    n = integer(one_in, 'one_in', 1)
    positions = periodic_positions(burst_packets, bursts,
                                   packets_between_bursts, start)
    residues = {p % n for p in positions}
    seen_phases = len(residues)
    # How many of the flow's OWN packets each successful phase would catch.
    catch = {}
    for p in positions:
        catch[p % n] = catch.get(p % n, 0) + 1
    per_phase = sorted(catch.values())
    period_gcd = math.gcd(packets_between_bursts, n)
    return dict(
        one_in=n, bursts=bursts, burst_packets=burst_packets,
        total_packets=len(positions),
        distinct_residues=seen_phases,
        phases_that_see_it=seen_phases / float(n),
        phases_that_never_see_it=1.0 - seen_phases / float(n),
        packets_caught_by_a_successful_phase=dict(
            minimum=per_phase[0] if per_phase else 0,
            maximum=per_phase[-1] if per_phase else 0),
        gcd_of_periods=period_gcd,
        phase_locked=period_gcd > 1 and seen_phases < len(positions),
        note=('A systematic sampler does not give this flow a probability. It '
              'gives it an outcome, fixed by a phase nobody chose and stable '
              'for as long as the packet rate is. Repeating the measurement '
              'for longer does not help, which is the difference from '
              'independent selection.'))


def jittered_skip_seen(positions, one_in, jitter_fraction, seed,
                       stream_length=None):
    """One run of a counter-based sampler whose skip is randomised.

    This is the RFC 3176 shape: a counter decremented per packet, reloaded on
    each sample with a skip drawn uniformly from the mean plus or minus
    `jitter_fraction`. With jitter_fraction=0 it is exactly the systematic
    sampler with a random initial phase.
    """
    n = integer(one_in, 'one_in', 1)
    if not 0 <= jitter_fraction < 1:
        raise ValueError('jitter_fraction is a proportion below 1')
    if not positions:
        return False
    stream_length = stream_length or (max(positions) + 1)
    rng = random.Random(seed)
    lo = max(1, int(round(n * (1 - jitter_fraction))))
    hi = max(lo, int(round(n * (1 + jitter_fraction))))
    wanted = set(positions)
    p = rng.randint(0, n - 1)          # arbitrary initial phase
    while p < stream_length:
        if p in wanted:
            return True
        p += rng.randint(lo, hi)
    return False


def sampler_comparison(burst_packets, bursts, packets_between_bursts, one_in,
                       trials=1000, seed=63):
    """The three selectors on the same periodic flow.

    Bernoulli is computed in closed form. Systematic is enumerated exactly over
    every phase. The jittered-skip sampler is simulated with a fixed seed,
    because its behaviour depends on the whole sequence of draws.
    """
    positions = periodic_positions(burst_packets, bursts,
                                   packets_between_bursts)
    k = len(positions)
    stream = max(positions) + 1
    bern = seen_probability(k, one_in)
    syst = systematic_phase_sweep(burst_packets, bursts,
                                  packets_between_bursts, one_in)
    out = dict(packets=k, one_in=one_in, stream_length=stream,
               bernoulli=bern, systematic=syst, jittered={})
    for label, frac in (('no jitter (fixed skip)', 0.0),
                        ('RFC 3176 minimum, +-10%', 0.10),
                        ('+-50%', 0.50)):
        hits = sum(jittered_skip_seen(positions, one_in, frac, seed + i, stream)
                   for i in range(trials))
        out['jittered'][label] = dict(jitter_fraction=frac, trials=trials,
                                      observed=hits / float(trials))
    return out


# ---------------------------------------------------------------------------
# Export load, which does not fall by exactly N
# ---------------------------------------------------------------------------

def export_load(packets_per_second, one_in, records_per_datagram=30,
                counter_samples_per_second=0, template_bytes_per_minute=0,
                sample_bytes=144):
    """What sampling actually saves, and what it does not touch.

    The claim that 1-in-N divides the export load by N is true of the sampled
    packet records alone. Counter samples, template re-sends and the datagram
    headers do not scale with the sampling rate at all.
    """
    integer(one_in, 'one_in', 1)
    if packets_per_second < 0 or counter_samples_per_second < 0:
        raise ValueError('rates cannot be negative')
    sampled = packets_per_second / float(one_in)
    sample_bps = sampled * sample_bytes * 8
    counter_bps = counter_samples_per_second * sample_bytes * 8
    template_bps = template_bytes_per_minute * 8 / 60.0
    total = sample_bps + counter_bps + template_bps
    unsampled_total = packets_per_second * sample_bytes * 8 + counter_bps \
        + template_bps
    return dict(one_in=one_in, sampled_records_per_second=sampled,
                sample_bits_per_second=sample_bps,
                counter_bits_per_second=counter_bps,
                template_bits_per_second=template_bps,
                total_bits_per_second=total,
                reduction_factor=unsampled_total / total if total else
                float('inf'),
                naive_expected_factor=float(one_in),
                note=('The reduction is smaller than N whenever anything in '
                      'the export does not scale with the sampling rate. '
                      'Measure the exporter output; do not divide.'))


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

def prove_the_models_differ():
    """FR-0052 inside the lab: the three selectors must actually disagree.

    If a change ever made them agree on the worked case, the chapter would go
    on asserting a difference that the code no longer shows. So the difference
    is measured before it is narrated.
    """
    c = sampler_comparison(3, 144, 6_000, 2000, trials=200)
    if c['systematic']['phases_that_never_see_it'] < 0.5:
        raise ValueError('the systematic sampler did not phase-lock on a case '
                         'built to phase-lock it')
    fixed = c['jittered']['no jitter (fixed skip)']['observed']
    ten = c['jittered']['RFC 3176 minimum, +-10%']['observed']
    if not fixed < ten:
        raise ValueError('jitter did not improve on a fixed skip (%.3f vs '
                         '%.3f)' % (fixed, ten))
    if abs(ten - c['bernoulli']) > 0.10:
        raise ValueError('a +-10%% jittered skip did not approach the '
                         'independent-selection answer (%.3f vs %.3f)'
                         % (ten, c['bernoulli']))
    # And the Bernoulli model itself is still cross-checked against simulation.
    p = seen_probability(50, 4000)
    observed = monte_carlo(50, 4000, 100000)
    se = math.sqrt(p * (1 - p) / 100000)
    if abs(observed - p) > 6 * se:
        raise ValueError('the independent-selection simulation left six '
                         'standard errors of the closed form')
    return dict(systematic_phase_locks=True, jitter_helps=True,
                jitter_approaches_bernoulli=True,
                bernoulli_matches_simulation=True)


def demo_original():
    """What this lab computed as originally shipped, and why it was wrong."""
    rows = []
    for label, pkts in (('bulk transfer (elephant)', 4_000_000),
                        ('C2 beacon, ~50 packets in the window', 50)):
        sampled = pkts // 4000
        rows.append(dict(flow=label, packets=pkts, sampled_by_old_model=sampled,
                         old_verdict=('INVISIBLE (below the floor)' if sampled == 0
                                      else 'estimated %d' % (sampled * 4000)),
                         actual_probability=seen_probability(pkts, 4000)))
    return dict(
        model='sampled = packets // N, evaluated per flow',
        rows=rows,
        defect=('Integer division of a per-flow packet count by N is a counter '
                'reset at the start of every flow. It returns zero for every '
                'flow shorter than N, so "anything smaller than roughly N '
                'packets is statistically invisible" was a property of the '
                'arithmetic and not of sampling. Under independent selection '
                'the 50-packet flow is seen with probability %.4f --- small, '
                'and not zero, and the difference is the whole of whether an '
                'empty result is evidence.'
                % seen_probability(50, 4000)))


def run():
    """The original JSON contract, extended. Existing keys keep their meaning."""
    rows = []
    for k, n in ((0, 4000), (3, 2000), (50, 4000), (4000, 4000),
                 (4000000, 4000), (50, 1)):
        rows.append(dict(packets=k, one_in=n,
                         expected_samples=expected_samples(k, n),
                         probability_seen=seen_probability(k, n)))
    p = seen_probability(50, 4000)
    observed = monte_carlo(50, 4000, 100000)
    se = math.sqrt(p * (1 - p) / 100000)
    phase = sampler_comparison(3, 144, 6_000, 2000, trials=1000)
    # The systematic outcome depends on gcd(period, N) and on residues, not on
    # the absolute scale, so the same sweep at a realistic spacing must agree.
    big = systematic_phase_sweep(3, 144, 120_000_000, 2000)
    scale_free = (abs(big['phases_that_see_it']
                      - phase['systematic']['phases_that_see_it']) < 1e-12)
    return dict(
        scope=('Independent and systematic selection arithmetic plus seeded '
               'simulation; no exporter, collector or hardware execution.'),
        cases=rows,
        simulation=dict(packets=50, one_in=4000, trials=100000, seed=63,
                        expected=p, observed=observed, standard_error=se,
                        within_six_standard_errors=abs(observed - p) <= 6 * se),
        beacon_over_one_day=dict(
            packets=432, one_in=2000,
            probability_seen=seen_probability(432, 2000),
            description=('three packets every ten minutes for twenty-four '
                         'hours, under independent selection')),
        phase_demonstration=phase,
        scale_check=dict(
            small_spacing=6_000, large_spacing=120_000_000,
            phases_that_see_it_small=phase['systematic']['phases_that_see_it'],
            phases_that_see_it_large=big['phases_that_see_it'],
            identical=scale_free,
            note=('The phase demonstration is run at a small packet spacing so '
                  'that it completes in a second. The systematic result '
                  'depends only on the residues the flow occupies modulo N, so '
                  'it is unchanged at a realistic spacing --- which this '
                  'checks rather than asserts.')),
        export_load=dict(
            naive=export_load(200_000, 2000),
            with_counters_and_templates=export_load(
                200_000, 2000, counter_samples_per_second=40,
                template_bytes_per_minute=64_000)),
        controls=prove_the_models_differ())


def _wrap(text, indent, width=78):
    words, lines, cur = text.split(), [], ''
    for word in words:
        if cur and len(cur) + len(word) + 1 > width - indent:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + ' ' + word).strip()
    lines.append(cur)
    return ('\n' + ' ' * indent).join(lines)


def report(out=None, original=False):
    import sys
    out = sys.stdout if out is None else out
    res = run()
    out.write('Lab 63.1 --- what 1-in-N sampling can see, by selector\n')
    out.write('=' * 74 + '\n')
    out.write('controls: %s\n\n'
              % ', '.join(sorted(k for k, v in res['controls'].items() if v)))

    if original:
        d = demo_original()
        out.write('WHAT THIS LAB COMPUTED AS ORIGINALLY SHIPPED\n\n')
        out.write('  model: %s\n\n' % d['model'])
        for r in d['rows']:
            out.write('  %-40s %s\n' % (r['flow'], r['old_verdict']))
        out.write('\n  %s\n\n' % _wrap(d['defect'], 2))

    out.write('INDEPENDENT SELECTION: A PROBABILITY, NOT A FLOOR\n\n')
    out.write('  %-12s %-10s %14s %16s\n'
              % ('packets', '1-in-N', 'expected', 'P(seen at least once)'))
    for r in res['cases']:
        out.write('  %-12s %-10s %14.4f %15.4f%%\n'
                  % ('{:,}'.format(r['packets']), '{:,}'.format(r['one_in']),
                     r['expected_samples'], 100 * r['probability_seen']))
    s = res['simulation']
    out.write('\n  %s\n\n' % _wrap(
        'Cross-checked by simulation: %d trials of a 50-packet flow at 1-in-%d '
        'observed %.5f against a closed form of %.6f, standard error %.6f.'
        % (s['trials'], s['one_in'], s['observed'], s['expected'],
           s['standard_error']), 2))

    bd = res['beacon_over_one_day']
    out.write('A BEACON OVER A DAY, UNDER INDEPENDENT SELECTION\n\n')
    out.write('  %s: %.1f%% chance of being seen at least once.\n\n'
              % (bd['description'], 100 * bd['probability_seen']))

    b = res['phase_demonstration']
    sy = b['systematic']
    sc = res['scale_check']
    out.write('THE SAME PERIODIC FLOW, THREE SELECTORS\n\n')
    out.write('  %d packets in bursts of %d, one burst every %s packets of\n'
              '  link traffic, sampled 1-in-%d\n\n'
              % (b['packets'], sy['burst_packets'],
                 '{:,}'.format(6000), b['one_in']))
    out.write('  %-34s %s\n' % ('independent selection (Bernoulli)',
                                '%.1f%% chance of being seen' % (100 * b['bernoulli'])))
    out.write('  %-34s %s\n'
              % ('systematic, fixed skip',
                 '%.1f%% of phases see it, %.1f%% never do'
                 % (100 * sy['phases_that_see_it'],
                    100 * sy['phases_that_never_see_it'])))
    for label in ('no jitter (fixed skip)', 'RFC 3176 minimum, +-10%', '+-50%'):
        j = b['jittered'][label]
        out.write('  %-34s %s\n'
                  % ('counter skip, ' + label,
                     '%.1f%% of %d simulated runs'
                     % (100 * j['observed'], j['trials'])))
    out.write('\n  %s\n\n' % _wrap(sy['note'], 2))
    out.write('  %s\n\n' % _wrap(sc['note'] + ' At a spacing of %s packets '
                                  'the figure is %.4f; at %s it is %.4f.'
                                  % ('{:,}'.format(sc['small_spacing']),
                                     sc['phases_that_see_it_small'],
                                     '{:,}'.format(sc['large_spacing']),
                                     sc['phases_that_see_it_large']), 2))
    out.write('  %s\n\n' % _wrap(
        'The fixed-skip row is the one to sit with. It is not a low '
        'probability; it is a coin that was flipped once, before the beacon '
        'existed, and never flipped again. RFC 3176 asks for a randomised '
        'skip and says variation of about ten per cent of the mean is '
        'sufficient --- and ten per cent is enough here to take the outcome '
        'back to roughly the independent-selection answer. If your platform '
        'documents a fixed skip, that is a fact about what your flow data can '
        'never tell you.', 2))

    e = res['export_load']
    out.write('AND THE LOAD DOES NOT FALL BY EXACTLY N\n\n')
    out.write('  %-44s %10.2f\n' % ('packet samples alone, reduction factor',
                                    e['naive']['reduction_factor']))
    out.write('  %-44s %10.2f\n' % ('with counter samples and templates',
                                    e['with_counters_and_templates']['reduction_factor']))
    out.write('  %-44s %10d\n' % ('what dividing by N would predict',
                                  int(e['naive']['naive_expected_factor'])))
    out.write('\n  %s\n' % _wrap(e['with_counters_and_templates']['note'], 2))


def main():
    import sys
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output')
    ap.add_argument('--json', action='store_true',
                    help='print the JSON result rather than the report')
    ap.add_argument('--demo-original', action='store_true',
                    help='show what this lab computed as originally shipped')
    args = ap.parse_args()
    result = run()
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(json.dumps(result, indent=2) + '\n',
                                     encoding='utf8')
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        report(original=args.demo_original)
    return 0 if result['simulation']['within_six_standard_errors'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
