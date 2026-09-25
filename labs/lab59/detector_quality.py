#!/usr/bin/env python3
"""Lab 59.3 --- how good a detection is, measured rather than asserted.

Two claims from the chapter are tested here, and both fail in their strong form.

  \"Beaconing is a machine pattern and nothing a human does looks like it.\"
  That is true of an UNJITTERED beacon and false as soon as the attacker adds
  jitter --- and, worse, legitimate automation is MORE regular than a jittered
  beacon, so any threshold loose enough to catch the beacon catches the backup
  job, the telemetry push and NTP first.

  \"Tune for precision; a noisy detection is worthless.\"
  Precision is not a property of a rule. It is a property of a rule AND the
  prevalence of what it looks for, and at realistic prevalence a rule with
  excellent sensitivity and specificity still produces mostly false positives.
  Raising the threshold buys precision with recall, and both sides have a cost
  you can put a number on.

    python3 detector_quality.py
    python3 detector_quality.py --json
    python3 test_detector_quality.py

Offline calculation over synthetic series with a fixed seed. It measures no real
network and no real product.
"""
import json
import math
import random
import statistics
import sys

SEED = 20260923


class DetectorError(ValueError):
    pass


# ---------------------------------------------------------------------------
# A periodicity detector, deliberately simple and stated in full
# ---------------------------------------------------------------------------

def regularity(times):
    """Coefficient of variation of the inter-arrival gaps. Lower is more regular."""
    if len(times) < 3:
        raise DetectorError('a periodicity judgement needs at least three events, '
                            'which is two gaps; with one gap everything is perfectly '
                            'regular and the answer is meaningless')
    t = sorted(times)
    gaps = [b - a for a, b in zip(t, t[1:])]
    if any(g <= 0 for g in gaps):
        raise DetectorError('two events at the same timestamp, or out of order: '
                            'fix the clock before computing a period')
    mean = statistics.fmean(gaps)
    if mean == 0:
        raise DetectorError('zero mean gap')
    sd = statistics.pstdev(gaps)
    return dict(n=len(t), mean_gap=mean, cv=sd / mean, gaps=gaps)


def flags(times, cv_threshold=0.15):
    return regularity(times)['cv'] <= cv_threshold


# ---------------------------------------------------------------------------
# Series: a beacon with jitter, real automation, and a person
# ---------------------------------------------------------------------------

def beacon(period=60.0, jitter_frac=0.0, n=60, rng=None):
    rng = rng or random.Random(SEED)
    t, out = 0.0, []
    for _ in range(n):
        out.append(t)
        t += period * (1 + rng.uniform(-jitter_frac, jitter_frac))
    return out


def cron_job(period=3600.0, n=24, drift_s=0.8, rng=None):
    """A scheduled job: very regular, with a little scheduler drift."""
    rng = rng or random.Random(SEED + 1)
    t, out = 0.0, []
    for _ in range(n):
        out.append(t)
        t += period + rng.gauss(0, drift_s)
    return out


def telemetry_push(period=60.0, n=60, drift_s=1.5, rng=None):
    rng = rng or random.Random(SEED + 2)
    t, out = 0.0, []
    for _ in range(n):
        out.append(t)
        t += max(1.0, period + rng.gauss(0, drift_s))
    return out


def person(rate_per_hour=40.0, n=60, rng=None):
    """Human-driven requests: exponential gaps, which are very irregular."""
    rng = rng or random.Random(SEED + 3)
    t, out = 0.0, []
    for _ in range(n):
        out.append(t)
        t += rng.expovariate(rate_per_hour / 3600.0)
    return out


def jitter_sweep(threshold=0.15, fractions=(0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8)):
    """At what jitter does the detector lose the beacon --- and what else does it
    catch on the way?"""
    rng = random.Random(SEED)
    benign = {
        'hourly cron job': cron_job(),
        'telemetry push every 60s': telemetry_push(),
        'a person browsing': person(),
    }
    benign_cv = {k: regularity(v)['cv'] for k, v in benign.items()}
    rows = []
    for f in fractions:
        series = beacon(jitter_frac=f, rng=random.Random(SEED + int(f * 1000)))
        cv = regularity(series)['cv']
        rows.append(dict(jitter=f, cv=cv, detected=cv <= threshold,
                         more_regular_than=[k for k, v in benign_cv.items() if cv < v],
                         less_regular_than=[k for k, v in benign_cv.items() if cv > v]))
    return dict(threshold=threshold, benign_cv=benign_cv, rows=rows)


def threshold_to_catch(jitter_frac, rng=None):
    """The CV threshold needed to catch a beacon at this jitter --- and what that
    threshold sweeps up with it."""
    cv = regularity(beacon(jitter_frac=jitter_frac,
                           rng=rng or random.Random(SEED + int(jitter_frac * 1000))))['cv']
    benign = {'hourly cron job': regularity(cron_job())['cv'],
              'telemetry push every 60s': regularity(telemetry_push())['cv'],
              'a person browsing': regularity(person())['cv']}
    return dict(jitter=jitter_frac, required_threshold=cv,
                also_caught=sorted(k for k, v in benign.items() if v <= cv))


# ---------------------------------------------------------------------------
# The base rate, which is where precision actually comes from
# ---------------------------------------------------------------------------

def alert_economics(population, prevalence, recall, false_positive_rate,
                    minutes_per_investigation=20, cost_of_a_miss=None):
    """Precision is a property of the rule AND the prevalence."""
    for n, v in (('population', population), ('minutes_per_investigation',
                                              minutes_per_investigation)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
            raise DetectorError('%s must be positive, got %r' % (n, v))
    for n, v in (('prevalence', prevalence), ('recall', recall),
                 ('false_positive_rate', false_positive_rate)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 1:
            raise DetectorError('%s is a probability between 0 and 1, got %r' % (n, v))
    positives = population * prevalence
    negatives = population - positives
    tp = positives * recall
    fn = positives - tp
    fp = negatives * false_positive_rate
    alerts = tp + fp
    ppv = (tp / alerts) if alerts else float('nan')
    hours = alerts * minutes_per_investigation / 60.0
    return dict(population=population, prevalence=prevalence, true_positives=tp,
                false_negatives=fn, false_positives=fp, alerts=alerts,
                precision=ppv, recall=recall, analyst_hours=hours,
                missed=fn, cost_of_misses=(fn * cost_of_a_miss) if cost_of_a_miss else None,
                note=('Precision here is %.1f%% --- the SAME rule at a different '
                      'prevalence gives a different number, because precision is '
                      'not a property of the rule.'
                      % (100 * ppv) if alerts else 'no alerts at all'))


TUNINGS = {
    'sensitive':   dict(recall=0.95, false_positive_rate=0.01),
    'balanced':    dict(recall=0.70, false_positive_rate=0.001),
    'precise':     dict(recall=0.30, false_positive_rate=0.00005),
}


def _w(t, i, width=78):
    words, lines, cur = t.split(), [], ''
    for x in words:
        if len(cur) + len(x) + 1 > width - i:
            lines.append(cur); cur = x
        else:
            cur = (cur + ' ' + x).strip()
    lines.append(cur)
    return ('\n' + ' ' * i).join(lines)


def report(out=None):
    out = sys.stdout if out is None else out
    out.write('Lab 59.3 --- what a detection is actually worth\n')
    out.write('=' * 74 + '\n\n')
    s = jitter_sweep()
    out.write('PERIODICITY: WHAT JITTER DOES, AND WHAT ELSE IS REGULAR\n\n')
    out.write('  benign traffic, for comparison:\n')
    for k, v in sorted(s['benign_cv'].items(), key=lambda kv: kv[1]):
        out.write('    %-28s CV %.3f\n' % (k, v))
    out.write('\n  %-10s %8s %10s\n' % ('jitter', 'CV', 'detected?'))
    for r in s['rows']:
        out.write('  %-10s %8.3f %10s\n'
                  % ('+-%d%%' % (100 * r['jitter']), r['cv'],
                     'yes' if r['detected'] else 'NO'))
    out.write('\n  (threshold CV <= %.2f)\n\n' % s['threshold'])
    worst = [r for r in s['rows'] if not r['detected']]
    if worst:
        j = worst[0]['jitter']
        t = threshold_to_catch(j)
        out.write('  %s\n' % _w(
            'The first jitter this detector misses is +-%d%%. To catch it the '
            'threshold must be loosened to CV <= %.3f --- which also sweeps up: %s. '
            'That is the trade in one line: there is no threshold that catches a '
            'jittered beacon and leaves the scheduled jobs alone.'
            % (100 * j, t['required_threshold'],
               ', '.join(t['also_caught']) or 'nothing, at this sample size'), 2))
    out.write('\n\nPRECISION IS NOT A PROPERTY OF THE RULE\n\n')
    out.write('  100,000 hosts. The same three tunings, at two prevalences.\n\n')
    for prev, label in ((0.0005, '50 compromised hosts'), (0.00002, '2 compromised hosts')):
        out.write('  %s (prevalence %.5f)\n' % (label, prev))
        out.write('    %-12s %8s %9s %9s %10s\n'
                  % ('tuning', 'alerts', 'true', 'precision', 'missed'))
        for name, kw in TUNINGS.items():
            e = alert_economics(100000, prev, **kw)
            out.write('    %-12s %8.0f %9.1f %8.1f%% %10.1f\n'
                      % (name, e['alerts'], e['true_positives'],
                         100 * e['precision'], e['missed']))
        out.write('\n')
    out.write('  %s\n' % _w(
        'The same "precise" rule looks respectable at one prevalence and is '
        'still mostly noise at the other, and it misses seven in ten either '
        'way. Tuning for precision alone is choosing to miss most of what you '
        'were looking for in exchange for a shorter queue. The queue length is '
        'real and the misses are real; price both.', 2))
    out.write('\n')


def main(argv):
    if '--json' in argv:
        print(json.dumps({
            'jitter': jitter_sweep(),
            'thresholds': [threshold_to_catch(f) for f in (0.1, 0.2, 0.3, 0.5)],
            'economics': {'%s@%s' % (n, p): alert_economics(100000, p, **kw)
                          for p in (0.0005, 0.00002)
                          for n, kw in TUNINGS.items()},
        }, indent=1))
        return 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
