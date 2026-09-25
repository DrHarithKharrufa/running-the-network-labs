#!/usr/bin/env python3
"""Checks for fec_and_errors.py --- where the gain applies, and what a counter proves.

Two central checks. Coding gain must move the OSNR margin and leave the POWER
margin exactly where it was, because a budget that subtracts it from the power
side approves links that cannot work. And a sudden SNR loss must be able to
cross the FEC threshold with no intermediate reading, because "weeks of warning"
is a property of slow degradation and not of the error rate.

No transponder, no FEC implementation, no measurement.

    python3 test_fec_and_errors.py
"""
import contextlib, io, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fec_and_errors as fe  # noqa: E402

FAILS, COUNT = [], 0


def check(name, cond, detail=''):
    global COUNT
    COUNT += 1
    detail = str(detail) if detail not in ('', None) else ''
    suffix = ('  [' + detail + ']') if detail else ''
    (print('ok    ' + name + suffix) if cond
     else (FAILS.append(name + suffix), print('FAIL  ' + name + suffix)))


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


# ---- coding gain is not free ----------------------------------------------
g = fe.net_coding_gain(11.0, 25.0)
check('the overhead costs 10log10(1+overhead) in OSNR',
      abs(g['rate_penalty_db'] - 10 * math.log10(1.25)) < 1e-12,
      g['rate_penalty_db'])
check('the net gain is the gross less that penalty',
      abs(g['net_gain_db'] - (11.0 - g['rate_penalty_db'])) < 1e-12)
check('net is always below gross for a real overhead',
      g['net_gain_db'] < g['gross_gain_db'])
check('a bigger overhead costs more',
      fe.net_coding_gain(11.0, 50.0)['net_gain_db'] < g['net_gain_db'])
check('zero overhead costs nothing',
      abs(fe.net_coding_gain(11.0, 0.0)['net_gain_db'] - 11.0) < 1e-12)
check('the penalty does not depend on the gross gain',
      abs(fe.net_coding_gain(6.0, 25.0)['rate_penalty_db']
          - g['rate_penalty_db']) < 1e-12)

# ---- THE CATEGORY ERROR ----------------------------------------------------
p = fe.where_gain_applies(1.5, 0.8, g['net_gain_db'])
check('coding gain leaves the POWER margin exactly where it was',
      p['power_margin_after_db'] == p['power_margin_before_db'],
      (p['power_margin_before_db'], p['power_margin_after_db']))
check('...and moves the OSNR margin by the net gain',
      abs(p['osnr_margin_after_db']
          - (p['osnr_margin_before_db'] + g['net_gain_db'])) < 1e-12)
check('applying it to the power side invents margin that is not there',
      p['if_wrongly_applied_to_power_db'] > p['power_margin_before_db'] + 9,
      p['if_wrongly_applied_to_power_db'])
check('...by exactly the net gain',
      abs((p['if_wrongly_applied_to_power_db'] - p['power_margin_before_db'])
          - g['net_gain_db']) < 1e-12)
check('the note says what the gain changes',
      'RECEIVER needs' in p['note'] and 'PATH costs' in p['note'])

# ---- the curve is steep, and it steepens ----------------------------------
check('the error rate falls as SNR rises',
      fe.ber_qpsk(10.0) < fe.ber_qpsk(6.0) < fe.ber_qpsk(3.0))
slopes = [math.log10(fe.ber_qpsk(s + 1) / fe.ber_qpsk(s)) for s in (4, 7, 10)]
check('one decibel is worth a large fraction of a decade',
      all(s < -0.25 for s in slopes), [round(s, 2) for s in slopes])
check('...and the slope steepens as the SNR rises',
      slopes[0] > slopes[1] > slopes[2], [round(s, 2) for s in slopes])

# ---- THE COUNTDOWN THAT IS NOT ONE ----------------------------------------
slow = fe.degradation(6.0, 2e-2, [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
sudden = fe.degradation(6.0, 2e-2, [0, 3.0])
check('the slow case starts healthy', not slow['rows'][0]['past_threshold'])
check('...and ends past the threshold', slow['rows'][-1]['past_threshold'])
check('...with intermediate readings you could have trended',
      len([r for r in slow['rows'] if not r['past_threshold']]) >= 5)
check('the sudden case reaches the SAME end state',
      sudden['rows'][-1]['past_threshold']
      and abs(sudden['rows'][-1]['snr_db'] - slow['rows'][-1]['snr_db']) < 1e-9)
check('...with NO intermediate reading at all',
      len([r for r in sudden['rows'] if not r['past_threshold']]) == 1,
      len(sudden['rows']))
check('so the warning is not a property of the error rate',
      sudden['rows'][0]['ber'] == slow['rows'][0]['ber'])
check('the margin in dB is what separates the two stories',
      all('margin_db' in r for r in slow['rows']))
check('the margin falls linearly while the error rate does not',
      abs((slow['rows'][0]['margin_db'] - slow['rows'][1]['margin_db'])
          - (slow['rows'][1]['margin_db'] - slow['rows'][2]['margin_db'])) < 1e-9)
check('the threshold SNR is derived, not asserted',
      abs(fe.ber_qpsk(slow['threshold_snr_db']) - 2e-2) < 1e-4,
      slow['threshold_snr_db'])
check('a lower threshold BER demands a higher SNR',
      fe.degradation(6.0, 1e-3, [0])['threshold_snr_db']
      > slow['threshold_snr_db'])

# ---- what a clean counter proves -------------------------------------------
n = fe.observation_needed(1e-15)
check('proving a low rate needs many bits', n > 1e15, n)
check('the bound is -ln(1-confidence)/BER',
      abs(n - (-math.log(0.05) / 1e-15)) < 1e6)
check('a higher confidence needs more bits',
      fe.observation_needed(1e-15, 0.99) > n)
check('a higher rate is proved sooner',
      fe.observation_needed(1e-9) < n)
check('at 400 Gb/s a 1e-15 rate takes hours to establish',
      3600 < fe.seconds_needed(1e-15, 400.0) < 86400,
      fe.seconds_needed(1e-15, 400.0))
check('a faster line establishes it sooner',
      fe.seconds_needed(1e-15, 800.0) < fe.seconds_needed(1e-15, 400.0))
a = fe.analyse()
check('a five-minute poll is a small fraction of what is needed',
      a['five_minute_fraction'] < 0.2, a['five_minute_fraction'])

# ---- rejection -------------------------------------------------------------
for fn, args, word in (
        (fe.net_coding_gain, (-1.0, 25.0), 'not negative'),
        (fe.net_coding_gain, (11.0, -5.0), 'not negative'),
        (fe.observation_needed, (0.0,), 'between 0 and 1'),
        (fe.observation_needed, (1.5,), 'between 0 and 1'),
        (fe.observation_needed, (1e-9, 1.5), 'between 0 and 1'),
        (fe.seconds_needed, (1e-9, 0.0), 'positive'),
        (fe.degradation, (6.0, 0.0, [0]), 'between 0 and 1'),
        (fe.degradation, (6.0, 1.0, [0]), 'between 0 and 1')):
    try:
        fn(*args)
        check('rejects %s%r' % (fn.__name__, args), False, 'no exception')
    except fe.FecError as e:
        check('rejects %s%r' % (fn.__name__, args), word in str(e), str(e)[:60])

# ---- the report makes the corrections in its own words -------------------
_r, out = quiet(fe.report, a)
low = ' '.join(out.lower().split())
check('the report says the power margin does not move',
      'the power margin does not move' in low)
check('the report says a post-FEC error is corrupted data',
      'corrupted data that reached the customer' in low)
check('the report tells you to alarm on any non-zero post-FEC count',
      'alarming on any non-zero count' in low)
check('the report says to trend the margin in dB',
      'trend the margin in db' in low)
check('the report shows the sudden case with no ramp',
      'no ramp, no weeks' in low)
check('the report disclaims being a transponder measurement',
      'no transponder' in low and 'no measurement' in low)
rc, _o = quiet(fe.main, [])
check('the script exits 0', rc == 0, rc)
rc2, _o = quiet(fe.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
