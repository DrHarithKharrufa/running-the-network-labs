#!/usr/bin/env python3
"""Tests for lab 62.1.  Run: python3 test_cardinality_check.py"""
import io
import sys

import cardinality_check as cm

PASS = [0]


def ok(cond, what):
    if not cond:
        raise AssertionError(what)
    PASS[0] += 1


def raises(fn, what):
    try:
        fn()
    except cm.CardinalityError:
        PASS[0] += 1
        return
    raise AssertionError('expected CardinalityError: %s' % what)


# ---- the product is an upper bound, and is computed correctly --------------
ok(cm.product_upper_bound({'a': 2, 'b': 3}) == 6, 'the product is the product')
ok(cm.product_upper_bound({'device': 500, 'interface': 48, 'queue': 8})
   == 192000, 'the chapter arithmetic checks out')
ok(cm.product_upper_bound({'a': 1}) == 1, 'a single-valued label is one series')
raises(lambda: cm.product_upper_bound({}), 'no labels at all')
raises(lambda: cm.product_upper_bound({'a': 0}), 'a label with no values')
raises(lambda: cm.product_upper_bound({'a': -1}), 'a negative count')
raises(lambda: cm.product_upper_bound({'a': True}), 'a bool is not a count')
raises(lambda: cm.product_upper_bound({'a': 2.5}), 'a fractional count')

# ---- emitted tuples under stated relationships -----------------------------
base = cm.emitted_series(cm.BASE_SCHEMA)
ok(base['series'] == 192000, 'nesting gives the same answer for the bounded set')
ok(len(base['trace']) == 3, 'the trace shows each level')
ok(base['trace'][-1]['running'] == 192000, 'and the running total')
raises(lambda: cm.emitted_series([]), 'an empty schema')
raises(lambda: cm.emitted_series([{'name': 'x'}]), 'a level with no per_parent')
raises(lambda: cm.emitted_series([{'name': 'x', 'per_parent': 0}]), 'zero')
raises(lambda: cm.emitted_series([{'per_parent': 2}]), 'a level with no name')

# ---- the correction this lab exists for ------------------------------------
attached = cm.attach(cm.BASE_SCHEMA, 'subscriber_id', 50000,
                     rides_on='interface')
emitted = cm.emitted_series(attached)['series']
ok(emitted == 400000,
   'a subscriber riding on an interface costs 50,000 x 8 queues = 400,000, '
   'got %d' % emitted)
product = cm.product_upper_bound({'device': 500, 'interface': 48, 'queue': 8,
                                  'subscriber_id': 50000})
ok(product == 9600000000, 'the old model produced 9.6 billion')
ok(product // emitted == 24000,
   'THE RESULT: the product overstates by a factor of 24,000, got %d'
   % (product // emitted))
ok(emitted < cm.OLD_BUDGET,
   'and the honest figure is INSIDE the budget the old script called it over')
ok(product > cm.OLD_BUDGET, 'while the product was outside it')
free = cm.emitted_series(cm.attach(cm.BASE_SCHEMA, 'region', 4))['series']
ok(free == 192000 * 4,
   'a genuinely independent label does multiply, so the model is not just '
   'refusing to multiply')
raises(lambda: cm.attach(cm.BASE_SCHEMA, 'x', 5, rides_on='nonexistent'),
       'riding on a level that is not in the schema')

# ---- churn is the real growth mechanism ------------------------------------
h = cm.historical_series(400000, churn_per_year=60000, retention_years=1)
ok(h['total'] == 460000, 'a year of churn adds its departures')
ok(abs(h['growth_factor'] - 1.15) < 1e-9, 'a 15 per cent growth factor')
ok(cm.historical_series(100, 0, 5)['total'] == 100,
   'no churn, no growth, however long the retention')
ok(cm.historical_series(100, 50, 0)['total'] == 100,
   'no retention, no accumulation')
ok(cm.historical_series(100, 50, 4)['total'] == 300, 'four years of churn')
raises(lambda: cm.historical_series(-1, 1, 1), 'a negative active count')
raises(lambda: cm.historical_series(1, -1, 1), 'negative churn')
raises(lambda: cm.historical_series(1, 1, -1), 'negative retention')

# ---- the budget states its inputs and claims nothing about products --------
b = cm.budget(400000, 86400, 7)
ok(b['samples_retained'] == 400000 * 86400 * 7, 'samples are series x rate x days')
ok(b['index_memory_bytes'] == 400000 * cm.BYTES_PER_ACTIVE_SERIES,
   'memory is series x bytes per series')
ok('inputs' in b and 'bytes_per_sample' in b['inputs'],
   'the inputs are returned alongside the totals')
ok('order-of-magnitude' in b['note'].lower() or 'ORDER-OF-MAGNITUDE' in b['note'],
   'and are labelled as inputs rather than measurements')
_b = repr(b).lower()
ok('oom' not in _b and 'out of memory' not in _b and 'crawl' not in _b,
   'the budget makes no claim about what a store will do when exceeded')
half = cm.budget(400000, 43200, 7)
ok(abs(half['disk_bytes'] - b['disk_bytes'] / 2) < 1e-6,
   'halving the sample rate halves the disk, which is the retention argument')
ok(cm.budget(1, 0, 0)['samples_retained'] == 0, 'no samples, no disk')
raises(lambda: cm.budget(0, 1, 1), 'a store with no series')
raises(lambda: cm.budget(1, -1, 1), 'a negative sample rate')
raises(lambda: cm.budget(1, 1, -1), 'negative retention')

# ---- three kinds of high cardinality ---------------------------------------
q = cm.classify_label('queue', 'bounded', 8)
e = cm.classify_label('subscriber_id', 'entity', 50000)
o = cm.classify_label('src_ip', 'open', None)
ok(q['budgetable'] and e['budgetable'], 'bounded and entity labels are budgetable')
ok(not o['budgetable'], 'an open label is not')
ok('LOOKUP' in e['advice'], 'the entity case is about query shape')
ok('unbounded' in o['advice'], 'the open case is the genuinely unbounded one')
ok(q['known_bound'] == 8 and e['known_bound'] == 50000, 'bounds are carried')
raises(lambda: cm.classify_label('x', 'huge', 1), 'an unknown value_source')
raises(lambda: cm.classify_label('x', 'open', 1000),
       'an open label cannot be given a bound you control')
raises(lambda: cm.classify_label('x', 'entity', None),
       'an entity label must state its bound')

# ---- the worked comparison --------------------------------------------------
c = cm.comparison()
ok(c['base_series'] == 192000, 'base series')
ok(c['emitted_with_subscriber'] == 400000, 'emitted with subscriber')
ok(int(c['overstatement']) == 24000, 'the overstatement factor')
ok(c['old_verdict'] == 'OVER BUDGET' and c['true_verdict'] == 'within budget',
   'the two verdicts disagree, which is the point of the comparison')
ok(c['historical']['total'] == 460000, 'the historical total')

# ---- the report -------------------------------------------------------------
buf = io.StringIO()
cm.report(buf, demo_original=True)
text = buf.getvalue()
flat = ' '.join(text.split())
ok('%%' not in text, 'no literal double percent leaks')
ok('9,600,000,000' in text and '400,000' in text, 'both figures are printed')
ok('24,000' in text, 'and the ratio between them')
ok('is not a network' in flat, 'the old model is refuted, not just replaced')
ok('measure them on your own store' in flat.lower(), 'the inputs are flagged')
ok('None of this makes per-subscriber metric labels a good idea' in flat,
   'the advice survives the correction to its argument')
buf2 = io.StringIO()
cm.report(buf2)
ok('THE MODEL THIS LAB SHIPPED WITH' in text,
   'the repaired lab can still show what it originally did')
ok('THE MODEL THIS LAB SHIPPED WITH' not in buf2.getvalue(),
   'and that demonstration is opt-in')

print('cardinality_check: %d checks passed' % PASS[0])
sys.exit(0)
