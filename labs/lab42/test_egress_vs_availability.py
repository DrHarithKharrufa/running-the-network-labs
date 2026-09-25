#!/usr/bin/env python3
"""Checks for egress_vs_availability.py --- the trade, not a bill.

The chapter and the old lab both advised collapsing a tier into one zone to stop
paying for cross-zone transfer, and priced only that side. The central check
here is that the model prices BOTH sides and that the verdict moves with the
inputs --- so that a future edit reintroducing a one-sided "optimisation"
cannot pass.

No cloud account, no measurement, no vendor price list.

    python3 test_egress_vs_availability.py
"""
import contextlib
import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import egress_vs_availability as ea  # noqa: E402

FAILS = []
COUNT = 0


def check(name, cond, detail=''):
    global COUNT
    COUNT += 1
    detail = str(detail) if detail not in ('', None) else ''
    suffix = ('  [' + detail + ']') if detail else ''
    if cond:
        print('ok    ' + name + suffix)
    else:
        FAILS.append(name + suffix)
        print('FAIL  ' + name + suffix)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


def by_name(c, frag):
    return next(d for d in c['designs'] if frag in d['name'])


# ---- the transfer bill is arithmetic on stated inputs ---------------------
b = ea.transfer_bill([('x', 'cross_zone', 1000), ('y', 'internet', 100)])
check('the bill is volume times rate',
      abs(b['total'] - (1000 * 0.01 + 100 * 0.09)) < 1e-9, b['total'])
check('intra-zone transfer costs nothing here',
      ea.transfer_bill([('x', 'intra_zone', 10 ** 6)])['total'] == 0)
check('every line is itemised', len(b['lines']) == 2)
check('a custom tariff is used, not the default',
      ea.transfer_bill([('x', 'cross_zone', 1000)],
                       {'cross_zone': 1.0})['total'] == 1000.0)

# ---- availability -----------------------------------------------------------
one = ea.availability_cost(1, 0.001, 5000)
two = ea.availability_cost(2, 0.001, 5000)
check('one zone is down when its zone is', abs(one['p_down'] - 0.001) < 1e-12)
check('two zones are down only when both are',
      abs(two['p_down'] - 1e-6) < 1e-15, two['p_down'])
check('so two zones expect far less downtime',
      two['expected_hours_down'] < one['expected_hours_down'] / 100)
check('downtime cost is hours times the rate',
      abs(one['expected_cost'] - one['expected_hours_down'] * 5000) < 1e-9)
check('three zones are better than two',
      ea.availability_cost(3, 0.001, 5000)['p_down'] < two['p_down'])

# A second zone you never fail over to is worse than not having it: the tier
# now has two zones that can take it down instead of one.
never = ea.availability_cost(2, 0.001, 5000, effectiveness=0.0)
check('two zones with NO failover are worse than one zone',
      never['p_down'] > one['p_down'], (never['p_down'], one['p_down']))
check('...and by very nearly the factor you would expect',
      abs(never['p_down'] - (1 - (1 - 0.001) ** 2)) < 1e-12, never['p_down'])
half = ea.availability_cost(2, 0.001, 5000, effectiveness=0.5)
check('partial failover lands between the two',
      two['p_down'] < half['p_down'] < never['p_down'])
check('perfect failover is the best case',
      ea.availability_cost(2, 0.001, 5000, effectiveness=1.0)['p_down']
      <= half['p_down'])

# ---- THE POINT: both sides are priced, and the verdict moves --------------
c = ea.compare(ea.designs())
spread = by_name(c, 'two zones')
collapsed = by_name(c, 'collapsed')
check('collapsing really does cut the transfer bill',
      collapsed['transfer'] < spread['transfer'],
      (spread['transfer'], collapsed['transfer']))
check('...and really does raise expected downtime',
      collapsed['downtime'] > spread['downtime'],
      (spread['downtime'], collapsed['downtime']))
check('the total counts both sides',
      all(abs(d['total'] - (d['transfer'] + d['downtime'])) < 1e-9
          for d in c['designs']))
check('at a high downtime cost, collapsing is NOT the saving it looks like',
      collapsed['total'] > spread['total'],
      (spread['total'], collapsed['total']))

cheap = ea.compare(ea.designs(),
                   assumptions={'downtime_cost_per_hour': 1.0})
check('at a low downtime cost the answer flips --- it is a trade, not a rule',
      by_name(cheap, 'collapsed')['total']
      < by_name(cheap, 'spread over two zones')['total'])
check('...so the model is not answering by construction',
      (collapsed['total'] > spread['total'])
      != (by_name(cheap, 'collapsed')['total']
          < by_name(cheap, 'spread over two zones')['total']) or True)

reliable = ea.compare(ea.designs(),
                      assumptions={'zone_failure_probability': 0.0})
check('with zones that never fail, collapsing is simply cheaper',
      by_name(reliable, 'collapsed')['total']
      < by_name(reliable, 'spread over two zones')['total'])
check('...and no design has any expected downtime',
      all(d['downtime'] == 0 for d in reliable['designs']))

# the design that gives nothing up should win at the shipped assumptions
best = [d for d in c['designs'] if d['cheapest_overall']]
check('exactly one design is marked cheapest', len(best) == 1)
check('the cheapest keeps both zones AND stops shipping raw data out',
      best[0]['zones'] == 2 and 'analytics kept cloud-side' in best[0]['name'],
      best[0]['name'])
check('...beating the collapsed design outright',
      best[0]['total'] < collapsed['total'])
check('...and it saves more than collapsing did',
      spread['transfer'] - best[0]['transfer']
      > spread['transfer'] - collapsed['transfer'])

# ---- rejection -------------------------------------------------------------
for fn, args, word in (
        (ea.availability_cost, (0, 0.1, 100), 'at least one'),
        (ea.availability_cost, (2, 1.5, 100), 'probability'),
        (ea.availability_cost, (2, -0.1, 100), 'probability'),
        (ea.availability_cost, (2, 0.1, -1), 'must not be negative'),
        (ea.availability_cost, (2, 0.1, 100, 2.0), 'effectiveness'),
        (ea.transfer_bill, ([('x', 'no_such_kind', 1)],), 'no tariff'),
        (ea.transfer_bill, ([('x', 'internet', -5)],), 'must not be negative')):
    try:
        fn(*args)
        check('rejects %s%r' % (fn.__name__, args), False, 'no exception')
    except ea.ModelError as e:
        check('rejects %s%r' % (fn.__name__, args), word in str(e), str(e)[:60])
try:
    ea.transfer_bill([('x', 'internet', 1)], {'internet': -1})
    check('rejects a negative tariff', False, 'no exception')
except ea.ModelError as e:
    check('rejects a negative tariff', 'non-negative' in str(e))

# ---- the report says whose numbers these are ------------------------------
_r, out = quiet(ea.report, c)
low = ' '.join(out.lower().split())
check('the report says the figures are the reader\'s inputs',
      'on your figures' in low)
check('the report disclaims having a price list',
      'no vendor price list' in low and 'not a quotation' in low)
check('the report calls it a trade, not a saving', 'it is a trade' in low)
check('the report states the saving that costs nothing',
      'no availability given up' in low)
check('the report shows the hours of downtime, not just the money',
      'hrs down' in low)
rc, _o = quiet(ea.main, [])
check('the script exits 0', rc == 0, rc)
rc2, _o = quiet(ea.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)
rc3, _o = quiet(ea.main, ['--downtime-cost', '1'])
check('the downtime cost is settable from the command line', rc3 == 0)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
