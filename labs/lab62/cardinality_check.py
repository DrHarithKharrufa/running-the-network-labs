#!/usr/bin/env python3
"""Lab 62.1 --- what a label actually costs, counted instead of multiplied.

THIS LAB WAS REPAIRED, NOT WITHDRAWN. As it first shipped it multiplied every
label's value count together, called the product the series count, added a
subscriber_id label, printed 9.6 billion series and concluded that the ingester
would run out of memory. Its purpose and its entry point are unchanged, because
the advice it was written to support is right and only its argument was wrong.
Every step after the multiplication, however, was not:

  * THE PRODUCT IS AN UPPER BOUND, not a count. It is reached only if every
    combination of label values is actually emitted. A subscriber is attached to
    exactly one device and one interface, so subscriber_id does not multiply the
    interface count --- it rides on it.
  * COUNTED PROPERLY, the same label costs 400,000 series, not 9,600,000,000: a
    factor of 24,000 smaller, and comfortably INSIDE the budget this
    script itself used to declare it over.
  * SO THE CONCLUSION WAS FALSE AT THAT SCALE. That does not make the advice
    wrong; it makes the ARGUMENT wrong, and an argument that is wrong by four
    orders of magnitude will be dismantled by the first engineer who checks it,
    taking the sound advice with it.

What it computes now: the upper bound, the emitted tuple count under
stated label relationships, the historical series accumulated by churn over a
retention window, and a budget from those numbers rather than from a slogan.

    python3 cardinality_check.py
    python3 cardinality_check.py --demo-original
    python3 cardinality_check.py --json
    python3 test_cardinality_check.py

Offline calculation in closed form. No store was run, no memory was measured,
and no figure here is a benchmark of any product. Per-series memory and
per-sample bytes are INPUTS you must measure on your own stack.
"""
import json
import sys

# Illustrative only: every real store differs, and both figures should be
# measured on yours before any budget built on them is believed.
BYTES_PER_ACTIVE_SERIES = 3500      # index + in-memory head block, order of magnitude
BYTES_PER_SAMPLE = 2.0              # after compression, order of magnitude


class CardinalityError(ValueError):
    """Raised when a schema cannot be counted honestly from what was given."""


def product_upper_bound(labels):
    """The Cartesian product of the label value counts.

    This is the number the chapter used to print. It is a genuine UPPER BOUND
    and it is correct as one; it is wrong only when it is presented as the
    series count, which is what the first edition did.
    """
    if not labels:
        raise CardinalityError('a metric with no labels still has one series; '
                               'pass at least one label to bound')
    total = 1
    for name, n in labels.items():
        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            raise CardinalityError('%s must be a positive whole number of '
                                   'distinct values' % name)
        total *= n
    return total


def emitted_series(schema):
    """Distinct label tuples actually emitted, given how the labels relate.

    A schema is a list of levels, each one a dict with:
        name        the label
        per_parent  how many values exist PER value of the level above
                    (or, for the first level, in total)
        independent True if this label varies freely against every other ---
                    a queue number is independent of which interface it is on;
                    an interface is not independent of its device.

    Nesting multiplies counts the way containment does, which is the same
    arithmetic as the product for genuinely independent labels and much less
    than the product for dependent ones. The distinction is the whole lab.
    """
    if not schema:
        raise CardinalityError('an empty schema emits nothing; that is not a '
                               'small answer, it is no answer')
    count = 1
    trace = []
    for level in schema:
        for field in ('name', 'per_parent'):
            if field not in level:
                raise CardinalityError('every level needs a %r' % field)
        n = level['per_parent']
        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            raise CardinalityError('%s: per_parent must be a positive whole '
                                   'number' % level['name'])
        count *= n
        trace.append(dict(name=level['name'], per_parent=n, running=count,
                          independent=bool(level.get('independent'))))
    return dict(series=count, trace=trace)


def attach(schema, name, total_values, rides_on=None):
    """Add a label whose values are attached to something that already exists.

    `rides_on` names the level this label is bound to --- a subscriber is bound
    to one access interface, a BGP neighbour to one router. A label that rides
    on an existing level does NOT multiply the levels above it; it replaces
    them, because naming the subscriber already determines the device and the
    interface.
    """
    if rides_on is None:
        return list(schema) + [dict(name=name, per_parent=total_values,
                                    independent=True)]
    names = [level['name'] for level in schema]
    if rides_on not in names:
        raise CardinalityError('%s cannot ride on %r, which is not in the '
                               'schema (%s)' % (name, rides_on,
                                                ', '.join(names)))
    idx = names.index(rides_on)
    kept = [level for level in schema[idx + 1:]
            if level.get('independent')]
    return ([dict(name=name, per_parent=total_values, independent=True)]
            + [dict(level) for level in kept])


def historical_series(active, churn_per_year, retention_years):
    """Series that exist in the store, not series that are currently emitting.

    A time-series store keeps a series for as long as its samples are retained,
    so an identity label accumulates: every subscriber who ever existed inside
    the retention window has a series, whether or not they are still a
    customer. THIS is the real growth mechanism for an identity label, and it
    is the one the product argument never mentions.
    """
    for name, v in (('active', active), ('churn_per_year', churn_per_year)):
        if v < 0:
            raise CardinalityError('%s cannot be negative' % name)
    if retention_years < 0:
        raise CardinalityError('retention cannot be negative')
    departed = churn_per_year * retention_years
    return dict(active=active, departed_still_stored=departed,
                total=active + departed,
                growth_factor=(active + departed) / active if active else
                float('inf'),
                note=('Departed identities keep their series until their last '
                      'sample falls out of retention. An identity label grows '
                      'with CHURN, not with the number of other labels.'))


def budget(series, samples_per_series_per_day, retention_days,
           bytes_per_active_series=BYTES_PER_ACTIVE_SERIES,
           bytes_per_sample=BYTES_PER_SAMPLE):
    """Memory and disk from a series count, stated as inputs you must measure.

    Note what is NOT here: any claim about what a particular product will do
    when these numbers are exceeded. The old script asserted an out-of-memory
    from one number. This returns the numbers and leaves the conclusion to
    somebody who knows the stack.
    """
    if series < 1:
        raise CardinalityError('series must be at least 1')
    if samples_per_series_per_day < 0 or retention_days < 0:
        raise CardinalityError('sample rate and retention cannot be negative')
    mem = series * bytes_per_active_series
    samples = series * samples_per_series_per_day * retention_days
    disk = samples * bytes_per_sample
    return dict(series=series,
                index_memory_bytes=mem,
                index_memory_gib=mem / 2 ** 30,
                samples_retained=samples,
                disk_bytes=disk, disk_gib=disk / 2 ** 30,
                inputs=dict(bytes_per_active_series=bytes_per_active_series,
                            bytes_per_sample=bytes_per_sample),
                note=('Both byte figures are ORDER-OF-MAGNITUDE inputs, not '
                      'measurements of any product. Measure them on your own '
                      'store before believing any total built from them.'))


def classify_label(name, value_source, known_bound=None):
    """Why a label is risky, which is not always 'it multiplies'.

    Three different things get called high cardinality and they need three
    different answers:
      bounded      the value set is fixed and small (queue, severity)
      entity       one value per thing you own, so it grows with your estate
                   and with churn, and you can count it (subscriber, circuit)
      open         the value set is chosen by the outside world and has no
                   bound you control (source IP, URL, session, user agent)
    """
    if value_source not in ('bounded', 'entity', 'open'):
        raise CardinalityError('value_source must be bounded, entity or open')
    if value_source == 'open' and known_bound is not None:
        raise CardinalityError('a label whose values come from outside has no '
                               'bound you control; remove known_bound or '
                               'reclassify it')
    if value_source in ('bounded', 'entity') and known_bound is None:
        raise CardinalityError('%s is claimed to be bounded, so state the '
                               'bound' % name)
    advice = {
        'bounded': 'Safe in a metric label. Count it and move on.',
        'entity': ('Countable, and usually affordable --- but it accumulates '
                   'with churn, and it is a LOOKUP dimension rather than an '
                   'aggregation one, which is the real argument for putting it '
                   'in flow and logs instead.'),
        'open': ('The only genuinely unbounded case. You cannot budget it '
                 'because you do not choose its values. This is the label that '
                 'belongs nowhere near a metric store.'),
    }[value_source]
    return dict(label=name, value_source=value_source, known_bound=known_bound,
                budgetable=value_source != 'open', advice=advice)


# --------------------------------------------------------------------------
# The worked comparison: the chapter's own example, both ways
# --------------------------------------------------------------------------

BASE_SCHEMA = [
    dict(name='device', per_parent=500),
    dict(name='interface', per_parent=48),
    dict(name='queue', per_parent=8, independent=True),
]
SUBSCRIBERS = 50_000
OLD_BUDGET = 2_000_000          # the budget figure this lab originally used


def comparison():
    base = emitted_series(BASE_SCHEMA)
    old_labels = {'device': 500, 'interface': 48, 'queue': 8,
                  'subscriber_id': SUBSCRIBERS}
    old = product_upper_bound(old_labels)
    with_subs = emitted_series(attach(BASE_SCHEMA, 'subscriber_id',
                                      SUBSCRIBERS, rides_on='interface'))
    hist = historical_series(with_subs['series'], churn_per_year=0.15
                             * SUBSCRIBERS * 8, retention_years=1)
    return dict(
        base_series=base['series'],
        product_with_subscriber=old,
        emitted_with_subscriber=with_subs['series'],
        overstatement=old / float(with_subs['series']),
        old_budget=OLD_BUDGET,
        old_verdict='OVER BUDGET' if old > OLD_BUDGET else 'within budget',
        true_verdict=('OVER BUDGET' if with_subs['series'] > OLD_BUDGET
                      else 'within budget'),
        historical=hist,
        budget_active=budget(with_subs['series'], 8640, 7),
        budget_historical=budget(int(hist['total']), 8640, 365))


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


def report(out=None, demo_original=False):
    out = sys.stdout if out is None else out
    c = comparison()
    out.write('Lab 62.1 --- what a label costs, counted instead of multiplied\n')
    out.write('=' * 74 + '\n\n')

    if demo_original:
        out.write('THE MODEL THIS LAB SHIPPED WITH, AND WHY IT WAS REPAIRED\n\n')
        out.write('  device(500) x interface(48) x queue(8) x subscriber_id'
                  '(50,000)\n')
        out.write('  = %s time series\n' % f"{c['product_with_subscriber']:,}")
        out.write('  budget %s  ->  verdict: %s, "ingester OOMs, queries '
                  'crawl"\n\n' % (f'{OLD_BUDGET:,}', c['old_verdict']))
        out.write('  %s\n\n' % _wrap(
            'Every arithmetic step there is correct and the conclusion is '
            'still false, because the first line is not a series count. It is '
            'the count you would get if every subscriber appeared on every '
            'interface of every device, which is not a network.', 2))

    out.write('THE SAME METRIC, COUNTED\n\n')
    out.write('  %-46s %14s\n' % ('bounded labels: device, interface, queue',
                                  f"{c['base_series']:,}"))
    out.write('  %-46s %14s\n' % ('+ subscriber_id, as a product (upper bound)',
                                  f"{c['product_with_subscriber']:,}"))
    out.write('  %-46s %14s\n' % ('+ subscriber_id, tuples actually emitted',
                                  f"{c['emitted_with_subscriber']:,}"))
    out.write('\n  %s\n\n' % _wrap(
        'A subscriber is attached to one interface on one device, so naming '
        'the subscriber already determines both. The label rides on the '
        'interface rather than multiplying it, and the honest figure is %s '
        'series --- smaller than the product by a factor of %s, and %s the '
        'very budget this lab originally used to declare it over.'
        % (f"{c['emitted_with_subscriber']:,}",
           f"{int(c['overstatement']):,}",
           'comfortably inside' if c['true_verdict'] == 'within budget'
           else 'still outside'), 2))

    h = c['historical']
    out.write('WHAT ACTUALLY GROWS: CHURN, NOT MULTIPLICATION\n\n')
    out.write('  %-46s %14s\n' % ('series emitting today',
                                  f"{int(h['active']):,}"))
    out.write('  %-46s %14s\n' % ('series from departed subscribers, 1 year',
                                  f"{int(h['departed_still_stored']):,}"))
    out.write('  %-46s %14s\n' % ('total series held in the store',
                                  f"{int(h['total']):,}"))
    out.write('\n  %s\n\n' % _wrap(
        'An identity label accumulates: a subscriber who left in March still '
        'has a series until their last sample falls out of retention. That is '
        'the growth mechanism, it is proportional to churn and retention '
        'rather than to the other labels, and the product argument never '
        'mentions it.', 2))

    out.write('AND WHAT THAT COSTS --- WHICH IS A FUNCTION OF SAMPLE RATE\n\n')
    out.write('  %-30s %10s %12s %12s\n'
              % ('tier', 'interval', 'samples', 'disk GiB'))
    total_disk = 0.0
    for label, interval_s, days in (('forensic', 1, 7),
                                    ('operational', 60, 90),
                                    ('capacity trend', 3600, 730)):
        per_day = 86400 // interval_s
        t = budget(int(h['total']), per_day, days)
        total_disk += t['disk_gib']
        out.write('  %-30s %9ds %12s %12.1f\n'
                  % (label, interval_s,
                     '%.2fe9' % (t['samples_retained'] / 1e9), t['disk_gib']))
    flat = budget(int(h['total']), 86400, 730)
    out.write('  %-30s %9s %12s %12.1f\n'
              % ('all of it at 1 s for 2 years', '1s', '%.2fe9'
                 % (flat['samples_retained'] / 1e9), flat['disk_gib']))
    out.write('\n  %s\n\n' % _wrap(
        'Three tiers come to %.0f GiB; the same series kept at one-second '
        'resolution for two years come to %.0f GiB, a factor of %.0f. That is '
        'the retention argument in one line, and notice that it is driven by '
        'SAMPLE INTERVAL rather than by the label count --- which is why "we '
        'reduced cardinality" and "the storage bill fell" are two different '
        'claims. Both byte figures behind these totals are order-of-magnitude '
        'INPUTS, not measurements of any product; measure them on your own '
        'store before believing any total built from them.'
        % (total_disk, flat['disk_gib'], flat['disk_gib'] / total_disk), 2))

    out.write('THREE THINGS CALLED HIGH CARDINALITY, NEEDING THREE ANSWERS\n\n')
    for label, src, bound in (('queue', 'bounded', 8),
                              ('subscriber_id', 'entity', SUBSCRIBERS),
                              ('src_ip', 'open', None)):
        k = classify_label(label, src, bound)
        out.write('  %-16s %-9s %s\n'
                  % (k['label'], k['value_source'], _wrap(k['advice'], 28)))
    out.write('\n  %s\n' % _wrap(
        'The chapter and this lab used to put subscriber_id and src_ip in one '
        'and give them the same answer. They are different problems. One is '
        'countable and usually affordable and belongs elsewhere for reasons of '
        'query shape; the other has no bound you control, which is the only '
        'case where "unbounded" is literally true.', 2))
    out.write('\n  %s\n' % _wrap(
        'None of this makes per-subscriber metric labels a good idea. It '
        'changes the argument from a false one --- that the store will run out '
        'of memory --- to a true one: you would be using an aggregation store '
        'as a lookup table, the data you want is already in flow records at '
        'better fidelity, and the cost, while affordable here, scales with '
        'subscribers times churn times retention, all three of which grow.', 2))


def main(argv):
    if '--json' in argv:
        print(json.dumps(dict(
            comparison=comparison(),
            classifications=[classify_label(*a) for a in
                             (('queue', 'bounded', 8),
                              ('subscriber_id', 'entity', SUBSCRIBERS),
                              ('src_ip', 'open', None))]), indent=1))
        return 0
    report(demo_original='--demo-original' in argv)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
