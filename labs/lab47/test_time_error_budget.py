#!/usr/bin/env python3
"""Checks for Lab 47.1.

The script this replaces printed a conclusion its own arithmetic contradicted.
So the first duty of these checks is to reproduce the old claim and show it
false, and the second is to show the new model reaching either verdict on
inputs the reader controls --- not one fixed answer.

    python3 test_time_error_budget.py
"""
import sys

import time_error_budget as T

PASS = 0
FAIL = []


def check(name, cond, detail=''):
    global PASS
    if cond:
        PASS += 1
    else:
        FAIL.append('%s%s' % (name, (' --- ' + detail) if detail else ''))


def close(name, got, want, tol=0.5):
    check(name, abs(got - want) <= tol, 'got %.4f, wanted %.4f' % (got, want))


def raises(name, fn, want):
    try:
        fn()
    except T.BudgetError as e:
        check(name, want.lower() in str(e).lower(),
              'raised %r, wanted something about %r' % (str(e), want))
    except Exception as e:                      # noqa: BLE001
        check(name, False, 'raised %s, not BudgetError' % type(e).__name__)
    else:
        check(name, False, 'did not raise')


# ===========================================================================
# 1. The old claim, reproduced and refuted
# ===========================================================================
# Old model: flat per-element sum, flat 1000 ns holdover, 1500 ns limit.
def old_total(boundary_clocks):
    return 30 + 50 * boundary_clocks + 100 + 1000


close('the old chain totalled 1330 ns in holdover', old_total(4), 1330)
check('one more boundary clock gives 1380 ns', old_total(5) == 1380)
check('and 1380 ns is INSIDE the 1500 ns limit', old_total(5) <= 1500)
check('so the old lab\'s concluding sentence was false', old_total(5) < 1500)
check('it takes four more, not one', old_total(8) > 1500 and old_total(7) <= 1500,
      '7 clocks -> %d, 8 clocks -> %d' % (old_total(7), old_total(8)))

# ===========================================================================
# 2. The four-timestamp result: asymmetry appears as HALF itself
# ===========================================================================
close('200 ns of asymmetry biases the offset by 100 ns',
      T.asymmetry_bias(200.0), 100.0)
close('zero asymmetry biases nothing', T.asymmetry_bias(0.0), 0.0)
check('the bias is exactly half, at every magnitude',
      all(abs(T.asymmetry_bias(a) - a / 2.0) < 1e-12
          for a in (1, 7, 33.5, 200, 1e6)))

# derive it from the timestamps themselves, as the docstring claims
def ptp_estimate(true_offset, d_ms, d_sm):
    """t2-t1 = d_ms + o ; t4-t3 = d_sm - o.  Return the protocol's estimate."""
    fwd = d_ms + true_offset
    rev = d_sm - true_offset
    return (fwd - rev) / 2.0


close('a symmetric path estimates the offset exactly',
      ptp_estimate(250.0, 500.0, 500.0), 250.0)
close('a 200 ns asymmetry puts the estimate 100 ns out',
      ptp_estimate(250.0, 600.0, 400.0), 350.0)
check('and the error equals asymmetry_bias()',
      abs((ptp_estimate(250.0, 600.0, 400.0) - 250.0)
          - T.asymmetry_bias(200.0)) < 1e-9)
check('the sign follows the longer direction',
      ptp_estimate(0.0, 400.0, 600.0) == -100.0)
check('averaging does not remove it --- it is the same every time',
      len({ptp_estimate(250.0, 600.0, 400.0) for _ in range(50)}) == 1)

# ===========================================================================
# 3. Constant and dynamic error are kept apart
# ===========================================================================
els = T.build_chain()
check('the illustrative chain has six elements', len(els) == 6)
s = T.chain_error(els, 'sum')
r = T.chain_error(els, 'rss')
close('constant error adds arithmetically', s['constant_ns'], 150.0)
check('constant error is the same either way',
      s['constant_ns'] == r['constant_ns'])
close('dynamic summed is 100 ns', s['dynamic_ns'], 100.0)
close('dynamic combined in quadrature is 43.59 ns', r['dynamic_ns'], 43.59, 0.01)
check('quadrature is the smaller of the two', r['dynamic_ns'] < s['dynamic_ns'])
check('and the gap widens with chain length',
      (T.chain_error(T.build_chain(12), 'sum')['dynamic_ns'] -
       T.chain_error(T.build_chain(12), 'rss')['dynamic_ns']) >
      (s['dynamic_ns'] - r['dynamic_ns']))
raises('an unknown combination rule is refused',
       lambda: T.chain_error(els, 'average'), "'sum' or 'rss'")
raises('an empty chain is refused', lambda: T.chain_error([], 'sum'),
       'at least one element')
raises('a negative dynamic error is refused',
       lambda: T.element('x', dte_ns=-1), 'magnitudes')
raises('a negative asymmetry is refused',
       lambda: T.element('x', asymmetry_ns=-1), 'magnitudes')

# a constant error that is genuinely negative still adds as a magnitude
neg = T.chain_error([T.element('a', cte_ns=-40), T.element('b', cte_ns=40)], 'sum')
close('worst-case constant error adds magnitudes, it does not cancel',
      neg['constant_ns'], 80.0)

# ===========================================================================
# 4. The requirement has a reference point and prior allocations
# ===========================================================================
close('the network gets what is left after the endpoint and the measurement',
      T.REQ['network_allocation_ns'], 1100.0)
check('which is less than the stated limit',
      T.REQ['network_allocation_ns'] < T.REQ['limit_ns'])
check('the reference point is recorded',
      T.REQ['reference_point'] == 'air interface')
raises('a requirement with no reference point is refused',
       lambda: T.requirement('x', 1500, 'somewhere'), 'reference point')
raises('a non-positive limit is refused',
       lambda: T.requirement('x', 0, 'air interface'), 'positive')
raises('allocations that consume the whole limit are refused',
       lambda: T.requirement('x', 100, 'air interface',
                             endpoint_allocation_ns=80,
                             measurement_uncertainty_ns=30),
       'consume the whole limit')
ok = T.requirement('relative', 260, 'relative between radios',
                   endpoint_allocation_ns=60)
close('a relative requirement is expressible too', ok['network_allocation_ns'], 200.0)

# ===========================================================================
# 5. The model reaches BOTH verdicts, on the reader's inputs
# ===========================================================================
a = T.assess(T.REQ, r)
check('the illustrative chain meets the requirement', a['meets'])
check('with a stated margin', a['margin_ns'] > 0)
big = T.assess(T.REQ, T.chain_error(T.build_chain(asymmetry_ns=500), 'rss'))
check('500 ns of asymmetry per link fails it', not big['meets'])
check('and it fails on constant error, not dynamic',
      T.chain_error(T.build_chain(asymmetry_ns=500), 'rss')['asymmetry_bias_ns']
      > T.chain_error(T.build_chain(asymmetry_ns=500), 'rss')['dynamic_ns'])
check('the verdict flips somewhere between 200 and 500 ns of asymmetry',
      T.assess(T.REQ, T.chain_error(T.build_chain(asymmetry_ns=200),
                                    'rss'))['meets'] and not big['meets'])
check('holdover is carried separately from the chain',
      T.assess(T.REQ, r, holdover_ns=2000)['meets'] is False and
      T.assess(T.REQ, r, holdover_ns=0)['meets'] is True)
check('the assessment records the reference point it used',
      a['reference_point'] == T.REQ['reference_point'])

# ===========================================================================
# 6. Holdover is a curve, and the answer is a duration
# ===========================================================================
close('1 ppb accumulates 1 ns per second',
      T.holdover_error_ns(1, frequency_offset_ppb=1.0), 1.0, 1e-9)
close('and 3600 ns in an hour',
      T.holdover_error_ns(3600, frequency_offset_ppb=1.0), 3600.0, 1e-6)
check('the drift term is quadratic, so doubling the time more than doubles it',
      T.holdover_error_ns(7200, drift_ppb_per_day=1.0) >
      2 * T.holdover_error_ns(3600, drift_ppb_per_day=1.0))
close('the quadratic term is (1/2).rate.t^2',
      T.holdover_error_ns(86400, drift_ppb_per_day=1.0), 0.5 * 1.0 * 86400,
      1e-6)
check('an initial offset is carried',
      T.holdover_error_ns(0, initial_ns=25.0) == 25.0)
check('holdover error never decreases with time',
      all(T.holdover_error_ns(t, frequency_offset_ppb=0.5,
                              drift_ppb_per_day=1.0) <=
          T.holdover_error_ns(t + 1, frequency_offset_ppb=0.5,
                              drift_ppb_per_day=1.0)
          for t in (0, 10, 1000, 86400)))
raises('negative time is refused', lambda: T.holdover_error_ns(-1),
       'does not run backwards')

t = T.holdover_seconds_until(906.0, frequency_offset_ppb=0.5,
                             drift_ppb_per_day=1.0)
check('an ordinary OCXO holds 906 ns for about half an hour',
      1500 < t < 2100, '%.0f s' % t)
check('a perfect oscillator never leaves the budget',
      T.holdover_seconds_until(906.0) is None)
check('an oscillator already outside the budget has no time at all',
      T.holdover_seconds_until(100.0, initial_ns=200.0) == 0.0)
check('a better oscillator holds longer',
      T.holdover_seconds_until(906.0, frequency_offset_ppb=0.05,
                               drift_ppb_per_day=0.1) >
      T.holdover_seconds_until(906.0, frequency_offset_ppb=0.5,
                               drift_ppb_per_day=1.0))

close('crossing between previous doubling steps and 30-day horizon is retained',
      T.holdover_seconds_until(20 * 86400, frequency_offset_ppb=1), 20 * 86400)
close('a crossing exactly at the horizon is retained',
      T.holdover_seconds_until(30 * 86400, frequency_offset_ppb=1), 30 * 86400)
check('None means beyond the horizon, not never',
      T.holdover_seconds_until(31 * 86400, frequency_offset_ppb=1) is None)
raises('negative offset is not a magnitude bound',
       lambda: T.holdover_seconds_until(100, frequency_offset_ppb=-1), 'nonnegative')
raises('NaN is refused', lambda: T.holdover_seconds_until(float('nan')), 'finite')

# the four grades must actually differ by orders of magnitude, or the table
# teaches nothing
times = {k: T.holdover_seconds_until(906.0, **o)
         for k, o in T.OSCILLATORS.items()}
check('every grade has a finite holdover time', all(v for v in times.values()))
check('the range spans more than two orders of magnitude',
      max(times.values()) / min(times.values()) > 100,
      'factor %.0f' % (max(times.values()) / min(times.values())))
check('the cheapest grade holds for minutes, not hours',
      times['disciplined TCXO'] < 600)
check('only the rubidium holds for a day',
      times['rubidium'] > 86400 and
      all(v < 86400 for k, v in times.items() if k != 'rubidium'))
check('the ordering follows the oscillator quality',
      times['disciplined TCXO'] < times['ordinary OCXO']
      < times['temperature-controlled OCXO'] < times['rubidium'])

# ===========================================================================
# 7. Adding hops is a constant-error problem
# ===========================================================================
lengths = [2, 4, 8, 16, 32]
totals = [T.chain_error(T.build_chain(n), 'rss')['total_ns'] for n in lengths]
check('a longer chain always has more total error',
      all(b > a for a, b in zip(totals, totals[1:])))
consts = [T.chain_error(T.build_chain(n), 'rss')['constant_ns'] for n in lengths]
dyns = [T.chain_error(T.build_chain(n), 'rss')['dynamic_ns'] for n in lengths]
check('constant error grows linearly with hops',
      abs((consts[3] - consts[0]) - 20.0 * (lengths[3] - lengths[0])) < 1e-9)
check('dynamic error grows only as the square root',
      dyns[3] / dyns[0] < (lengths[3] / float(lengths[0])) ** 0.5 + 0.2)
check('so constant error dominates a long chain',
      consts[-1] > 4 * dyns[-1])
fails = [n for n in (2, 4, 8, 16, 32, 64)
         if not T.assess(T.REQ, T.chain_error(T.build_chain(n), 'rss'))['meets']]
check('the chain does eventually fail the requirement', bool(fails))
check('and it takes a lot of hops on these figures', min(fails) >= 32,
      'first failure at %d' % min(fails))

# ===========================================================================
# 8. The report is consistent with the model
# ===========================================================================
import io                                                     # noqa: E402
import contextlib                                             # noqa: E402

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    T.main([])
out = buf.getvalue()
check('the report runs', 'A. The requirement' in out)
check('it states the reference point', 'air interface' in out)
check('it shows the network allocation, not the raw limit',
      'LEFT FOR THE NETWORK' in out and '1100 ns' in out)
check('it names both combination rules', 'sum' in out and 'rss' in out)
check('it evaluates the old claim instead of repeating it',
      'old model, 5 boundary clocks' in out and 'passes' in out)
check('it says how many more clocks the old model really needed',
      'FOUR more boundary clocks' in out)
check('it gives holdover as a duration', 'time to limit' in out)
check('it distinguishes holdover from following a bad reference',
      'never enters holdover at all' in out)
check('it discloses what it does not establish',
      'does NOT establish' in out and 'no measurement' in out.lower())
check('it does not claim conformance',
      'conformance assessment' in out and 'MEASURED' in out)
check('no line of the report is absurdly wide',
      max(len(l) for l in out.splitlines()) <= 82,
      'widest %d' % max(len(l) for l in out.splitlines()))

# ===========================================================================
# 9. The sourced oscillator table, and the vendor's own two numbers
# ===========================================================================
check('the vendor table has four grades', len(T.VENDOR_OSCILLATORS) == 4)
check('each grade has both terms',
      all({'frequency_offset_ppb', 'drift_ppb_per_day'} == set(o)
          for o in T.VENDOR_OSCILLATORS.values()))
check('the grades name their ITU/Stratum class',
      all(('G.812' in k) for k in T.VENDOR_OSCILLATORS))
check('the illustrative set is kept separate',
      set(T.OSCILLATORS) & set(T.VENDOR_OSCILLATORS) == set())

vt = {k: T.holdover_seconds_until(906.0, **o)
      for k, o in T.VENDOR_OSCILLATORS.items()}
check('every sourced grade has a finite holdover time', all(vt.values()))
check('the plain OCXO is the shortest',
      min(vt, key=vt.get).startswith('OCXO'))
best_aging = min(T.VENDOR_OSCILLATORS,
                 key=lambda k: T.VENDOR_OSCILLATORS[k]['drift_ppb_per_day'])
best_offset = min(T.VENDOR_OSCILLATORS,
                  key=lambda k: T.VENDOR_OSCILLATORS[k]['frequency_offset_ppb'])
check('the best aging and best offset are different grades',
      best_aging != best_offset, '%s vs %s' % (best_aging, best_offset))
check('yet their holdover times are within ten per cent',
      abs(vt[best_aging] - vt[best_offset]) / max(vt.values()) < 0.10,
      '%.0f%%' % (100 * abs(vt[best_aging] - vt[best_offset]) / max(vt.values())))
check('the two sensitivity roots are close; no causal/product ranking follows',
      vt[best_offset] > 0.8 * vt[best_aging])

# the datasheet's own end-to-end claim against its own specification page
c = T.VENDOR_EPRTC_CLAIM
implied = c['ns'] / (c['days'] * 86400.0)
best_free = min(o['frequency_offset_ppb'] for o in T.VENDOR_OSCILLATORS.values())
close('100 ns over 100 days implies 1.157e-5 ppb', implied * 1e5, 1.157, 0.01)
check('which is far below the best figure on the specification page',
      implied < best_free / 100)
check('by between two and four orders of magnitude',
      100 < best_free / implied < 10000, 'factor %.0f' % (best_free / implied))
check('at the specification figure the clock passes 100 ns in hours, not days',
      T.holdover_seconds_until(c['ns'], frequency_offset_ppb=best_free) < 86400)
check('the improved claim implies an even smaller residual',
      c['ns'] / (c['improved_days'] * 86400.0) < implied)
check('the claim is recorded as a claim, not as a grade',
      'ns' in c and 'days' in c and 'frequency_offset_ppb' not in c)

buf2 = io.StringIO()
with contextlib.redirect_stdout(buf2):
    T.main([])
out2 = buf2.getvalue()
check('the report runs section F', 'F. The same arithmetic on a real datasheet' in out2)
check('it names the datasheet', 'OSA 5412' in out2)
check('it prints the equivalent constant offset', '1.157e-05 ppb' in out2)
check('it prints the ratio', 'ratio between them' in out2)
check('it says a front-page figure answers a different question',
      'answering a different question' in out2)
check('it says what to ask the vendor for instead',
      'after a stated lock time' in out2)
check('it calls a datasheet figure a manufacturer claim',
      'MANUFACTURER CLAIM' in out2)

# ===========================================================================
if __name__ == '__main__':
    total = PASS + len(FAIL)
    for f in FAIL:
        print('FAIL: %s' % f)
    print('%d/%d checks passed' % (PASS, total))
    sys.exit(1 if FAIL else 0)
