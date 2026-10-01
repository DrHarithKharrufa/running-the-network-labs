#!/usr/bin/env python3
"""Lab 60.1 --- why mean time to detect improves when detection gets worse.

Chapter 60 recommends MTTD and MTTR as the metrics that replace vanity
measures. They become vanity measures themselves the moment you compute them
the obvious way, and this lab shows exactly how, with arithmetic rather than
argument.

  * A MEAN OVER DETECTED INCIDENTS IS A SURVIVORSHIP STATISTIC. The incidents
    you never detected are not in it. Lose your ability to find the slow, quiet
    ones and the mean FALLS --- the dashboard improves while the programme
    degrades.
  * A MEAN HIDES THE TAIL. Detection times are long-tailed: the median and the
    95th percentile move independently of each other, and it is the tail that
    ends up in the incident report.
  * A RATE NEEDS A DENOMINATOR YOU TRUST. "Coverage: 94 per cent" is a
    statement about the asset register, not about the estate, and the gap
    between them is exactly where the unmonitored things live.

    python3 metric_honesty.py
    python3 metric_honesty.py --json
    python3 test_metric_honesty.py

Offline calculation over a synthetic incident population with a fixed seed. It
measures no real programme, and no figure it prints is a benchmark. The
complete incident population is known only because this fixture constructs it;
a production team cannot count all undetected incidents from its detection
log alone. Independent evaluation and uncertainty remain necessary.
"""
import json
import random
import statistics
import sys

SEED = 20260923


class MetricError(ValueError):
    """Raised when a figure cannot be computed honestly from what was given."""


def percentile(sorted_values, p):
    """Nearest-rank percentile: the smallest value at or above which p of the
    sample falls.  Index ceil(p*n)-1, clamped.  Stated because percentile
    definitions differ by about one rank and a metric you cannot reproduce is
    not a metric.
    """
    if not sorted_values:
        raise MetricError('no percentile exists for an empty sample')
    if not 0 < p <= 1:
        raise MetricError('p must be greater than 0 and at most 1')
    n = len(sorted_values)
    rank = -(-int(round(p * n * 1000)) // 1000)      # ceil(p*n) without float drift
    return sorted_values[max(0, min(n - 1, rank - 1))]


def summarise(values, label='hours'):
    """Never a mean alone: the distribution, or nothing.

    An empty cohort returns a dict with NO mean key, so a caller that wants a
    number has to notice the cohort was empty rather than reading a zero.
    """
    if not values:
        return dict(n=0, unit=label,
                    note='no incidents in this cohort; a metric over an empty '
                         'cohort is not a small number, it is no number')
    v = sorted(float(x) for x in values)
    if any(x < 0 for x in v):
        raise MetricError('a duration cannot be negative: check the timestamps '
                          'and the clocks before computing anything')
    return dict(n=len(v), unit=label, mean=statistics.fmean(v),
                median=statistics.median(v),
                p90=percentile(v, 0.90), p95=percentile(v, 0.95),
                worst=v[-1])


def population(n=200, rng=None):
    """A synthetic year of incidents.

    Detection time is long-tailed: most are found quickly by a rule built for
    them, and a minority --- the quiet, patient, novel ones --- take months.
    That shape is the whole reason a mean misleads.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise MetricError('n must be a positive integer number of incidents')
    rng = rng or random.Random(SEED)
    out = []
    for i in range(n):
        if rng.random() < 0.80:
            hours = rng.lognormvariate(1.0, 0.8)         # noisy, quickly found
            kind = 'loud'
        else:
            hours = rng.lognormvariate(6.0, 1.1)         # quiet, slow to find
            kind = 'quiet'
        out.append(dict(id=i, kind=kind, detect_hours=hours,
                        respond_hours=max(0.5, rng.lognormvariate(1.5, 0.7)),
                        severity=('high' if rng.random() < 0.15 else 'routine')))
    return out


def detected_subset(incidents, quiet_detection_rate):
    """Which incidents this programme actually finds.

    The loud ones are always found.  The quiet ones are found at the stated
    rate, and THE ONES NOT FOUND SIMPLY DO NOT APPEAR IN THE STATISTICS.  The
    draw uses a fixed seed so the two programmes are compared on the same
    incidents rather than on two different random years.
    """
    if isinstance(quiet_detection_rate, bool):
        raise MetricError('quiet_detection_rate is a probability between 0 and 1')
    if not 0 <= quiet_detection_rate <= 1:
        raise MetricError('quiet_detection_rate is a probability between 0 and 1')
    rng = random.Random(SEED + 99)
    seen, missed = [], []
    for inc in incidents:
        if inc['kind'] == 'loud' or rng.random() < quiet_detection_rate:
            seen.append(inc)
        else:
            missed.append(inc)
    return seen, missed


def programme(incidents, quiet_detection_rate, label=''):
    seen, missed = detected_subset(incidents, quiet_detection_rate)
    d = summarise([i['detect_hours'] for i in seen])
    r = summarise([i['respond_hours'] for i in seen])
    return dict(label=label, quiet_detection_rate=quiet_detection_rate,
                detected=len(seen), undetected=len(missed),
                detection=d, response=r,
                undetected_share=(len(missed) / len(incidents)
                                  if incidents else 0.0),
                honest_note=('%d of %d incidents were never detected and are in '
                             'NONE of the figures above.'
                             % (len(missed), len(incidents))))


def check_demonstration(good, bad):
    """Positive control for the claim this lab is about to print.

    The prose says the worse programme misses more incidents AND reports a
    lower mean time to detect.  If a change to the population or the rates ever
    made that untrue, the report would print a confident sentence that its own
    numbers contradict.  So the direction is measured, not assumed, and the
    report refuses to run when it does not hold (FR-0052 inside the lab).
    """
    if bad['undetected'] <= good['undetected']:
        raise MetricError('the "worse" programme did not miss more incidents, '
                          'so there is no survivorship effect to demonstrate')
    if 'mean' not in bad['detection'] or 'mean' not in good['detection']:
        raise MetricError('a programme detected nothing; there is no mean to compare')
    if bad['detection']['mean'] >= good['detection']['mean']:
        raise MetricError('the worse programme did not report a lower MTTD in '
                          'this run, so the demonstration does not hold and '
                          'must not be narrated as though it did')
    return dict(extra_missed=bad['undetected'] - good['undetected'],
                mttd_drop_percent=100 * (1 - bad['detection']['mean']
                                         / good['detection']['mean']))


def sweep(incidents, rates=(1.0, 0.9, 0.7, 0.5, 0.3, 0.2, 0.1, 0.0)):
    """MTTD against detection capability, so the reader sees the whole curve
    rather than two points chosen to make an argument."""
    rows = []
    for r in rates:
        p = programme(incidents, r)
        rows.append(dict(rate=r, detected=p['detected'],
                         undetected=p['undetected'],
                         mean=p['detection'].get('mean'),
                         median=p['detection'].get('median'),
                         p95=p['detection'].get('p95')))
    return rows


def coverage(monitored, in_register, discovered_by_scan):
    """A rate needs a denominator you trust."""
    for name, v in (('monitored', monitored), ('in_register', in_register),
                    ('discovered_by_scan', discovered_by_scan)):
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise MetricError('%s must be a non-negative integer' % name)
    if monitored > in_register:
        raise MetricError('more assets are monitored than are in the register; '
                          'one of the two numbers is wrong, and that is the finding')
    if in_register == 0:
        raise MetricError('an empty register gives no coverage rate at all, '
                          'which is a louder finding than any percentage')
    best = max(in_register, discovered_by_scan)
    unregistered = max(0, discovered_by_scan - in_register)
    return dict(
        against_register=monitored / in_register,
        against_discovered=monitored / best,
        register_gap=discovered_by_scan - in_register,
        note=('The headline number is coverage against the REGISTER. Coverage '
              'against what a scan actually found is %.1f per cent --- and the '
              '%d assets the register does not contain are, by construction, '
              'the ones nobody is watching.'
              % (100 * monitored / best, unregistered)))


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
    pop = population()
    good = programme(pop, 0.90, 'finds 90% of the quiet ones')
    bad = programme(pop, 0.20, 'finds 20% of the quiet ones')
    proof = check_demonstration(good, bad)

    out.write('Lab 60.1 --- metrics that improve while the programme gets worse\n')
    out.write('=' * 74 + '\n\n')
    out.write('THE SAME %d INCIDENTS, TWO PROGRAMMES\n\n' % len(pop))
    out.write('  %-30s %8s %8s %8s %9s %7s\n'
              % ('programme', 'detected', 'MTTD', 'median', 'p95', 'missed'))
    for p in (good, bad):
        out.write('  %-30s %8d %8.1f %8.1f %9.1f %7d\n'
                  % (p['label'], p['detected'], p['detection']['mean'],
                     p['detection']['median'], p['detection']['p95'],
                     p['undetected']))
    out.write('\n  %s\n' % _wrap(
        'The second programme is far worse --- it misses %d incidents the first '
        'one finds --- and its MEAN TIME TO DETECT IS %.0f PER CENT LOWER. Every '
        'incident it failed to find was one of the slow ones, so removing them '
        'from the sample improved the average. A dashboard showing MTTD alone '
        'would report this as progress, and the board would approve the budget '
        'cut that caused it.'
        % (proof['extra_missed'], proof['mttd_drop_percent']), 2))

    out.write('\n\nTHE WHOLE CURVE, NOT TWO CHOSEN POINTS\n\n')
    out.write('  %-12s %9s %9s %9s %10s\n'
              % ('quiet found', 'detected', 'MTTD', 'median', 'missed'))
    for row in sweep(pop):
        out.write('  %-12s %9d %9.1f %9.1f %10d\n'
                  % ('%.0f%%' % (100 * row['rate']), row['detected'],
                     row['mean'], row['median'], row['undetected']))
    out.write('\n  %s\n' % _wrap(
        'MTTD is not monotonic in capability, it is monotonic in what you '
        'stopped being able to see. Report it beside the undetected count or '
        'do not report it.', 2))

    out.write('\n\nSEVERITY COHORTS, WHICH THE AGGREGATE HIDES\n\n')
    seen, _ = detected_subset(pop, 0.90)
    for sev in ('high', 'routine'):
        s = summarise([i['detect_hours'] for i in seen if i['severity'] == sev])
        if s['n'] == 0:
            out.write('  %-10s %s\n' % (sev, s['note']))
            continue
        out.write('  %-10s n=%-4d mean %7.1f  median %6.1f  p95 %8.1f  worst %8.1f\n'
                  % (sev, s['n'], s['mean'], s['median'], s['p95'], s['worst']))

    out.write('\nCOVERAGE NEEDS A DENOMINATOR YOU TRUST\n\n')
    c = coverage(monitored=940, in_register=1000, discovered_by_scan=1180)
    out.write('  monitored 940, register 1000  ->  %.1f per cent "coverage"\n'
              % (100 * c['against_register']))
    out.write('  %s\n' % _wrap(c['note'], 2))
    out.write('\nNo figure here is reportable on its own. Each needs its cohort,\n')
    out.write('its denominator, its distribution and its known gaps beside it.\n')


def main(argv):
    if '--json' in argv:
        pop = population()
        good = programme(pop, 0.90, 'finds 90% of the quiet ones')
        bad = programme(pop, 0.20, 'finds 20% of the quiet ones')
        print(json.dumps({'good': good, 'bad': bad,
                          'demonstration': check_demonstration(good, bad),
                          'sweep': sweep(pop),
                          'coverage': coverage(940, 1000, 1180)}, indent=1))
        return 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
