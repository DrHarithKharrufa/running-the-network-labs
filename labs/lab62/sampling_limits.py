#!/usr/bin/env python3
"""Lab 62.3 --- what a sample rate can and cannot see.

Chapter 62 said that a one-second sample "catches the microburst". It does
not, and the arithmetic is not close. This lab computes what each kind of
instrument can observe, because the choice between them is the whole of
whether an incident is visible afterwards.

  * AN INSTANTANEOUS SAMPLE SEES A BURST WITH PROBABILITY ROUGHLY
    duration / interval. A 200-microsecond queue excursion, sampled once a
    second, is seen about once in five thousand samples. Sampling ten times
    faster makes it once in five hundred.
  * A COUNTER DELTA IS AN AVERAGE AND HIDES THE PEAK BY CONSTRUCTION. A 10 Gb/s
    port that ran at line rate for 5 ms of every second reads 50 Mb/s --- half
    a per cent utilisation --- while it was dropping packets.
  * THE INSTRUMENT THAT DOES SEE IT IS A DIFFERENT KIND OF INSTRUMENT: a
    hardware high-water mark, a histogram, or an on-device threshold event.
    Each one answers a different question and loses something else.
  * AND THE RATE YOU ASKED FOR IS NOT THE RATE YOU GOT. If the device collects
    internally every ten seconds and exports every second, nine samples in ten
    are copies, and nothing in the stream says so.

    python3 sampling_limits.py
    python3 sampling_limits.py --json
    python3 test_sampling_limits.py

Offline calculation in closed form. No device was sampled and no platform's
behaviour is claimed; the collection intervals and register semantics of your
own hardware are facts to look up, not to assume from this lab.
"""
import json
import math
import sys


class SamplingError(ValueError):
    """Raised when a question cannot be answered from what was given."""


def _positive(name, v):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
        raise SamplingError('%s must be greater than zero' % name)
    return float(v)


def instantaneous_capture(burst_seconds, sample_interval_seconds,
                          bursts_per_second=1.0):
    """Probability an instantaneous sample lands inside a burst.

    The duty cycle of the bursts is their total occupied time per second. A
    sample taken at an arbitrary instant is inside a burst with exactly that
    probability, so the chance of seeing ANY burst in one sample is the duty
    cycle for a random phase with non-overlapping bursts. The any-hit formula
    over n samples additionally assumes independent sample phases. A fixed
    periodic sampler may phase-lock; that formula does not apply to it.
    fraction_of_bursts_seen uses random-phase periodic coverage min(1,b/i),
    not hit count divided by burst count. These are distinct models.
    """
    b = _positive('burst_seconds', burst_seconds)
    i = _positive('sample_interval_seconds', sample_interval_seconds)
    r = _positive('bursts_per_second', bursts_per_second)
    if b * r > 1:
        raise SamplingError('non-overlapping burst model requires b*r <= 1')
    if r <= 0:
        raise SamplingError('bursts_per_second must be greater than zero')
    duty = min(1.0, b * r)
    samples_per_hour = int(math.floor(3600.0 / i + 1e-9))  # complete sample intervals only
    return dict(burst_seconds=b, sample_interval_seconds=i,
                bursts_per_second=r, duty_cycle=duty,
                p_single_sample=duty,
                bursts_per_hour=r * 3600.0,
                samples_per_hour=samples_per_hour,
                expected_hits_per_hour=duty * samples_per_hour,
                p_at_least_one_in_an_hour=1 - (1 - duty) ** samples_per_hour,
                fraction_of_bursts_seen=min(1.0, b / i),
                hits_per_burst=(duty * samples_per_hour) / (r * 3600.0),
                note=('This is the probability of landing ON a burst. It says '
                      'nothing about measuring its height correctly, which an '
                      'averaged counter will still get wrong.'))


def counter_average(link_bits_per_second, burst_seconds, bursts_per_second,
                    interval_seconds, burst_rate_fraction=1.0):
    """Steady duty-cycle mean, not an individual counter-window peak.

    interval_seconds is reported but this model averages complete burst cycles;
    it does not simulate placement of bursts within that chosen interval.

    A counter is a total. Divide it by the interval and you get the mean rate
    over that interval, which is the correct answer to a question nobody asked
    during a microburst incident.
    """
    link = _positive('link_bits_per_second', link_bits_per_second)
    b = _positive('burst_seconds', burst_seconds)
    i = _positive('interval_seconds', interval_seconds)
    if bursts_per_second <= 0:
        raise SamplingError('bursts_per_second must be greater than zero')
    if not 0 < burst_rate_fraction <= 1:
        raise SamplingError('burst_rate_fraction is a proportion of line rate')
    duty = min(1.0, b * bursts_per_second)
    peak = link * burst_rate_fraction
    mean = peak * duty
    return dict(peak_bits_per_second=peak, mean_bits_per_second=mean,
                duty_cycle=duty,
                reported_utilisation=mean / link,
                peak_utilisation=peak / link,
                understatement_factor=peak / mean if mean else float('inf'),
                interval_seconds=i,
                note=('Shorter actual windows may reduce dilution or lie inside a burst. '
                      'This steady duty-cycle model cannot predict that effect; '
                      'a window mean alone does not recover arbitrary sub-window peaks.'))


def counter_wrap_seconds(counter_bits, rate_bits_per_second, octets=True):
    """How long a counter takes to wrap at a given rate.

    The classic trap: a 32-bit octet counter on a fast port wraps between
    polls, and every delta after that is wrong in a way that looks like a
    plausible number rather than an error.
    """
    if counter_bits not in (32, 64):
        raise SamplingError('counter_bits is 32 or 64 in practice; state it')
    rate = _positive('rate_bits_per_second', rate_bits_per_second)
    span = float(2 ** counter_bits)
    per_second = rate / 8.0 if octets else rate
    seconds = span / per_second
    return dict(counter_bits=counter_bits, rate_bits_per_second=rate,
                counts_octets=octets, wrap_seconds=seconds,
                wrap_readable=('%.2f s' % seconds if seconds < 600 else
                               '%.1f days' % (seconds / 86400.0) if seconds
                               < 86400 * 400 else '%.1f years'
                               % (seconds / (86400.0 * 365))),
                safe_poll_interval_seconds=seconds / 2.0,
                note=('Modulo subtraction is unambiguous only with an independently '
                      'bounded true increment below 2^counter_bits and no reset. '
                      'Use a maximum-rate/time bound, discontinuity evidence '
                      'and preferably 64-bit counters.'))


def export_aliasing(device_collection_seconds, requested_export_seconds):
    """What you actually receive when the device collects slower than it sends.

    The subscription says one second. The platform may refresh the underlying
    value every ten. You then receive ten samples per refresh, nine of which
    are copies, and nothing in the stream distinguishes a repeated value from a
    genuinely steady one.
    """
    d = _positive('device_collection_seconds', device_collection_seconds)
    e = _positive('requested_export_seconds', requested_export_seconds)
    effective = max(d, e)
    duplicates = max(0.0, d / e - 1.0) if e < d else 0.0
    return dict(device_collection_seconds=d, requested_export_seconds=e,
                effective_resolution_seconds=effective,
                duplicate_fraction=duplicates / (duplicates + 1)
                if duplicates else 0.0,
                samples_per_refresh=max(1.0, d / e),
                misleading=e < d,
                note=('Record the device collection interval, the export '
                      'interval, and any batching and loss SEPARATELY. The '
                      'requested rate is a request.'))


def instrument_comparison(burst_seconds, bursts_per_second,
                          interval_seconds=1.0):
    """Idealised instruments; real refresh, accuracy, reset, loss and scope need tests.

    catches_every_burst describes the ideal model, not product qualification.
    """
    inst = instantaneous_capture(burst_seconds, interval_seconds,
                                 bursts_per_second)
    return [
        dict(instrument='instantaneous sample of queue depth',
             sees_the_burst='%.4f of samples' % inst['p_single_sample'],
             answers='what the depth was at one instant',
             gives_up='everything between samples',
             catches_every_burst=False),
        dict(instrument='hardware high-water mark, read and cleared',
             sees_the_burst='every burst in the window',
             answers='the maximum reached since the last read',
             gives_up='how many there were, how long they lasted, and when',
             catches_every_burst=True),
        dict(instrument='on-device histogram of depth or latency',
             sees_the_burst='every burst, as a bucket count',
             answers='the distribution, including the tail',
             gives_up='the time ordering within the window',
             catches_every_burst=True),
        dict(instrument='on-device threshold event',
             sees_the_burst='every crossing of the threshold you set',
             answers='when it crossed, and how often',
             gives_up='anything below the threshold, and the shape',
             catches_every_burst=True),
    ]


def probe_coverage(probe_interval_seconds, packets_per_probe,
                   outage_seconds, vantage_points=1, paths_per_vantage=1,
                   total_paths=1):
    """What a synthetic probe is a sample OF.

    Three separate limits, which get conflated: how often it runs (whether a
    short outage falls between probes), how many packets it sends (the finest
    loss ratio it can express at all), and where it runs from (the fraction of
    real paths it exercises).
    """
    i = _positive('probe_interval_seconds', probe_interval_seconds)
    if packets_per_probe < 1:
        raise SamplingError('a probe sends at least one packet')
    if outage_seconds < 0:
        raise SamplingError('an outage cannot last a negative time')
    if total_paths < 1 or paths_per_vantage < 1 or vantage_points < 1:
        raise SamplingError('paths and vantage points are positive counts')
    covered = min(total_paths, vantage_points * paths_per_vantage)
    return dict(
        probe_interval_seconds=i, packets_per_probe=packets_per_probe,
        p_outage_hits_a_probe=min(1.0, outage_seconds / i),
        expected_probes_during_outage=outage_seconds / i,
        finest_expressible_loss=1.0 / packets_per_probe,
        can_see_one_percent_loss=(1.0 / packets_per_probe) <= 0.01,
        detection_delay_worst_case_seconds=i,
        path_coverage=covered / float(total_paths),
        paths_never_probed=total_paths - covered,
        note=('A probe result is an estimate from a sample, with a resolution '
              'of 1/packets and a blind window of one interval. It is the best '
              'proxy for customer experience available and it is still a '
              'sample; say so when quoting it.'))


def prove_the_limits_are_real():
    """FR-0052 inside the lab: the claims must be reproducible from the code.

    Each assertion here is the numeric form of a sentence the chapter prints.
    If a later edit made any of them untrue, the chapter would still print the
    sentence, so they are checked before it does.
    """
    fast = instantaneous_capture(200e-6, 1.0, 1.0)
    if fast['p_single_sample'] > 0.001:
        raise SamplingError('a 200 us burst is not rare at 1 Hz; the model is '
                            'wrong')
    faster = instantaneous_capture(200e-6, 0.1, 1.0)
    if not faster['p_single_sample'] == fast['p_single_sample']:
        raise SamplingError('the per-sample probability should not depend on '
                            'the interval; only the number of samples does')
    if faster['expected_hits_per_hour'] <= fast['expected_hits_per_hour']:
        raise SamplingError('sampling ten times faster did not find more')
    c = counter_average(10e9, 5e-3, 1.0, 1.0)
    if c['understatement_factor'] < 100:
        raise SamplingError('the averaging effect vanished; check the model')
    w32 = counter_wrap_seconds(32, 10e9)
    w64 = counter_wrap_seconds(64, 100e9)
    if not (w32['wrap_seconds'] < 10 < w64['wrap_seconds']):
        raise SamplingError('the counter-wrap contrast is gone')
    a = export_aliasing(10.0, 1.0)
    if not a['misleading'] or a['effective_resolution_seconds'] != 10.0:
        raise SamplingError('aliasing is not being detected')
    b = export_aliasing(1.0, 1.0)
    if b['misleading'] or b['duplicate_fraction'] != 0.0:
        raise SamplingError('aliasing is reported where there is none')
    p = probe_coverage(60, 10, 30, vantage_points=4, paths_per_vantage=3,
                       total_paths=40)
    if p['can_see_one_percent_loss']:
        raise SamplingError('ten packets cannot express one per cent loss')
    return dict(instantaneous_is_rare=True, faster_sampling_finds_more=True,
                averaging_hides_peaks=True, wrap_contrast=True,
                aliasing_detected=True, aliasing_not_invented=True,
                probe_resolution_bounded=True)


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


def report(out=None):
    out = sys.stdout if out is None else out
    proof = prove_the_limits_are_real()
    out.write('Lab 62.3 --- what a sample rate can and cannot see\n')
    out.write('=' * 74 + '\n')
    out.write('claims checked before they are printed: %d\n\n' % len(proof))

    out.write('A 200-MICROSECOND QUEUE EXCURSION, ONCE A SECOND\n\n')
    out.write('  %-22s %12s %14s %16s\n'
              % ('sampled every', 'per sample', 'hits per hour',
                 'of 3,600 bursts'))
    for interval in (60.0, 10.0, 1.0, 0.1, 0.01):
        r = instantaneous_capture(200e-6, interval, 1.0)
        out.write('  %-22s %12.6f %14.2f %15.2f%%\n'
                  % ('%g s' % interval, r['p_single_sample'],
                     r['expected_hits_per_hour'],
                     100 * r['fraction_of_bursts_seen']))
    one = instantaneous_capture(200e-6, 1.0, 1.0)
    ten = instantaneous_capture(200e-6, 0.1, 1.0)
    out.write('\n  %s\n\n' % _wrap(
        'One-second sampling expects %.2f hits an hour out of %.0f bursts: it '
        'sees %.2f per cent of them. Ten samples a second sees %.1f per cent. '
        'The per-sample probability never changes, because it is the duty '
        'cycle; only the number of chances does, so you would need a sample '
        'every %.0f microseconds to expect to catch each burst once. There is '
        'no practical rate at which instantaneous sampling becomes a reliable '
        'way to observe a microburst, and the claim that a one-second sample '
        '"catches the microburst" was wrong by more than three orders of '
        'magnitude.'
        % (one['expected_hits_per_hour'], one['bursts_per_hour'],
           100 * one['fraction_of_bursts_seen'],
           100 * ten['fraction_of_bursts_seen'], 200e-6 * 1e6), 2))

    c = counter_average(10e9, 5e-3, 1.0, 1.0)
    out.write('AND THE COUNTER DOES NOT HELP, BECAUSE IT IS AN AVERAGE\n\n')
    out.write('  %-40s %s\n' % ('port', '10 Gb/s'))
    out.write('  %-40s %s\n' % ('behaviour', 'line rate for 5 ms of every '
                                'second'))
    out.write('  %-40s %.1f%%\n' % ('peak utilisation',
                                    100 * c['peak_utilisation']))
    out.write('  %-40s %.1f%%\n' % ('what a one-second counter delta reports',
                                    100 * c['reported_utilisation']))
    out.write('  %-40s %.0fx\n' % ('understatement',
                                   c['understatement_factor']))
    out.write('\n  %s\n\n' % _wrap(c['note'], 2))

    out.write('THE INSTRUMENTS THAT DO SEE IT, AND WHAT EACH GIVES UP\n\n')
    for row in instrument_comparison(200e-6, 1.0, 1.0):
        out.write('  %s\n' % row['instrument'])
        out.write('    sees: %-28s answers: %s\n'
                  % (row['sees_the_burst'], row['answers']))
        out.write('    gives up: %s\n\n' % row['gives_up'])
    out.write('  %s\n\n' % _wrap(
        'In these ideal instrument models, three catch every burst; none '
        'gives you everything. The question is not "how fast can I sample" but '
        '"which of these does my platform actually implement, and what does '
        'its register mean" --- and that is a datasheet question with a '
        'different answer on every line card.', 2))

    out.write('COUNTERS WRAP, AND A WRAPPED DELTA LOOKS LIKE A NUMBER\n\n')
    out.write('  %-14s %-16s %16s %20s\n'
              % ('counter', 'link rate', 'wraps after', 'safe poll interval'))
    for bits, rate, label in ((32, 1e9, '1 Gb/s'), (32, 10e9, '10 Gb/s'),
                              (32, 100e9, '100 Gb/s'), (64, 100e9, '100 Gb/s'),
                              (64, 800e9, '800 Gb/s')):
        w = counter_wrap_seconds(bits, rate)
        out.write('  %-14s %-16s %16s %19.1fs\n'
                  % ('%d-bit' % bits, label, w['wrap_readable'],
                     w['safe_poll_interval_seconds']))
    out.write('\n  %s\n\n' % _wrap(
        'A 32-bit octet counter on a 10 Gb/s port wraps in under four seconds '
        'at line rate. Every SNMP interval in normal use is longer than that, '
        'so the delta is not merely imprecise, it is undefined --- and it '
        'still produces a plausible-looking number. This is a counter '
        'SEMANTICS question and it belongs beside the storage arithmetic, '
        'because both are consequences of what a counter is.', 2))

    out.write('THE RATE YOU ASKED FOR IS NOT THE RATE YOU GOT\n\n')
    for dev, exp in ((1.0, 1.0), (10.0, 1.0), (30.0, 1.0)):
        a = export_aliasing(dev, exp)
        out.write('  device refreshes every %-5g s, exports every %-4g s  ->  '
                  'effective %-5g s, %.0f%% duplicates\n'
                  % (dev, exp, a['effective_resolution_seconds'],
                     100 * a['duplicate_fraction']))
    out.write('\n  %s\n\n' % _wrap(
        'Nothing in the stream distinguishes a repeated value from a steady '
        'one, so a dashboard built on the middle row is drawing ten-second '
        'data and calling it one-second data. Record the device collection '
        'interval, the export interval, and any batching, loss or backpressure '
        'as separate facts --- the subscription is a request, not a '
        'measurement.', 2))

    p = probe_coverage(60, 10, 30, vantage_points=4, paths_per_vantage=3,
                       total_paths=40)
    out.write('A SYNTHETIC PROBE IS A SAMPLE, IN THREE SEPARATE WAYS\n\n')
    out.write('  %-40s %s\n' % ('finest loss ratio 10 packets can express',
                                '%.0f%%' % (100 * p['finest_expressible_loss'])))
    out.write('  %-40s %s\n' % ('can it see 1 per cent loss at all?',
                                'yes' if p['can_see_one_percent_loss'] else 'no'))
    out.write('  %-40s %.0f s\n' % ('worst-case delay before any probe runs',
                                    p['detection_delay_worst_case_seconds']))
    out.write('  %-40s %.0f%%\n' % ('of 40 customer paths actually exercised',
                                    100 * p['path_coverage']))
    out.write('  %-40s %d\n' % ('paths no probe ever traverses',
                                p['paths_never_probed']))
    out.write('\n  %s\n' % _wrap(
        'A probe every minute with ten packets from four sites is a good '
        'system and it cannot express one per cent loss, cannot see a '
        'thirty-second outage that falls between runs, and never touches 28 of '
        'the 40 paths customers use. It remains the closest available proxy '
        'for customer experience --- which is the reason to run it and the '
        'reason to quote it as an estimate from a sample rather than as the '
        'customer experience itself.', 2))


def main(argv):
    if '--json' in argv:
        print(json.dumps(dict(
            controls=prove_the_limits_are_real(),
            capture={('%gs' % i): instantaneous_capture(200e-6, i, 1.0)
                     for i in (60.0, 10.0, 1.0, 0.1, 0.01)},
            counter=counter_average(10e9, 5e-3, 1.0, 1.0),
            wrap={('%d-bit@%gG' % (b, r / 1e9)): counter_wrap_seconds(b, r)
                  for b, r in ((32, 1e9), (32, 10e9), (32, 100e9),
                               (64, 100e9), (64, 800e9))},
            aliasing=[export_aliasing(d, 1.0) for d in (1.0, 10.0, 30.0)],
            instruments=instrument_comparison(200e-6, 1.0, 1.0),
            probe=probe_coverage(60, 10, 30, 4, 3, 40)), indent=1))
        return 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
