#!/usr/bin/env python3
"""Tests for lab 62.3.  Run: python3 test_sampling_limits.py"""
import io
import sys

import sampling_limits as sl

PASS = [0]


def ok(cond, what):
    if not cond:
        raise AssertionError(what)
    PASS[0] += 1


def raises(fn, what):
    try:
        fn()
    except sl.SamplingError:
        PASS[0] += 1
        return
    raise AssertionError('expected SamplingError: %s' % what)


# ---- instantaneous sampling -------------------------------------------------
r = sl.instantaneous_capture(200e-6, 1.0, 1.0)
ok(abs(r['duty_cycle'] - 2e-4) < 1e-12, 'a 200 us burst once a second is 2e-4')
ok(r['p_single_sample'] == r['duty_cycle'],
   'the per-sample probability IS the duty cycle')
ok(abs(r['expected_hits_per_hour'] - 0.72) < 1e-9,
   '0.72 hits an hour at 1 Hz, got %.4f' % r['expected_hits_per_hour'])
ok(abs(r['bursts_per_hour'] - 3600) < 1e-9, 'against 3,600 bursts')
ok(r['fraction_of_bursts_seen'] < 0.0003,
   'so under 0.03 per cent of bursts are seen')
fast = sl.instantaneous_capture(200e-6, 0.01, 1.0)
ok(fast['p_single_sample'] == r['p_single_sample'],
   'THE KEY POINT: sampling faster does not make each sample more likely to '
   'land on a burst')
ok(abs(fast['expected_hits_per_hour'] - r['expected_hits_per_hour'] * 100) < 1e-9,
   'it gives you a hundred times as many chances, and no more')
ok(fast['fraction_of_bursts_seen'] < 0.03,
   'and still sees under 3 per cent of them at 100 Hz')
wide = sl.instantaneous_capture(0.5, 1.0, 1.0)
ok(wide['p_single_sample'] == 0.5,
   'a burst occupying half the second is caught half the time, so the model is '
   'not simply always small')
raises(lambda: sl.instantaneous_capture(0.5, 1.0, 4.0),
       'overlapping bursts exceed the non-overlap model scope')
sat = sl.instantaneous_capture(0.5, 1.0, 2.0)
ok(sat['duty_cycle'] == 1.0, 'a duty cycle cannot exceed one')
ok(sat['p_at_least_one_in_an_hour'] == 1.0, 'and then every sample hits')
raises(lambda: sl.instantaneous_capture(0, 1, 1), 'a zero-length burst')
raises(lambda: sl.instantaneous_capture(1e-3, 0, 1), 'a zero interval')
raises(lambda: sl.instantaneous_capture(1e-3, 1, 0), 'no bursts at all')
raises(lambda: sl.instantaneous_capture(-1, 1, 1), 'a negative burst')

# ---- the counter is an average ---------------------------------------------
c = sl.counter_average(10e9, 5e-3, 1.0, 1.0)
ok(c['peak_utilisation'] == 1.0, 'line rate during the burst')
ok(abs(c['reported_utilisation'] - 0.005) < 1e-12,
   'a one-second counter reports half a per cent')
ok(abs(c['understatement_factor'] - 200) < 1e-9, 'a factor of 200')
minute = sl.counter_average(10e9, 5e-3, 1.0, 60.0)
ok(minute['reported_utilisation'] == c['reported_utilisation'],
   'the interval does not change the mean; both are means, which is the point')
half = sl.counter_average(10e9, 5e-3, 1.0, 1.0, burst_rate_fraction=0.5)
ok(half['peak_utilisation'] == 0.5, 'a burst below line rate is modelled')
raises(lambda: sl.counter_average(0, 1e-3, 1, 1), 'a zero-rate link')
raises(lambda: sl.counter_average(1e9, 1e-3, 0, 1), 'no bursts')
raises(lambda: sl.counter_average(1e9, 1e-3, 1, 1, 0), 'a zero burst rate')
raises(lambda: sl.counter_average(1e9, 1e-3, 1, 1, 1.5), 'above line rate')

# ---- counter wrap, the classic trap ----------------------------------------
w = sl.counter_wrap_seconds(32, 10e9)
ok(abs(w['wrap_seconds'] - (2 ** 32) / 1.25e9) < 1e-9,
   '2^32 octets at 1.25 GB/s')
ok(3.4 < w['wrap_seconds'] < 3.5,
   'a 32-bit octet counter wraps in under 3.5 s at 10 Gb/s, got %.3f'
   % w['wrap_seconds'])
ok(w['safe_poll_interval_seconds'] < 2, 'so no normal poll interval is safe')
ok(sl.counter_wrap_seconds(32, 1e9)['wrap_seconds'] > 30,
   'at 1 Gb/s it survives half a minute')
ok(sl.counter_wrap_seconds(64, 100e9)['wrap_seconds'] > 1e9,
   'a 64-bit counter at 100 Gb/s is effectively immortal')
ok('years' in sl.counter_wrap_seconds(64, 100e9)['wrap_readable'],
   'and says so in readable units')
ok('s' in sl.counter_wrap_seconds(32, 10e9)['wrap_readable'],
   'while the 32-bit case is quoted in seconds')
bits = sl.counter_wrap_seconds(32, 10e9, octets=False)
ok(bits['wrap_seconds'] < w['wrap_seconds'],
   'a counter of bits wraps eight times sooner than one of octets')
raises(lambda: sl.counter_wrap_seconds(48, 1e9), 'an unusual counter width')
raises(lambda: sl.counter_wrap_seconds(32, 0), 'a zero rate')

# ---- aliasing between collection and export --------------------------------
a = sl.export_aliasing(10.0, 1.0)
ok(a['effective_resolution_seconds'] == 10.0,
   'the effective resolution is the SLOWER of the two')
ok(abs(a['duplicate_fraction'] - 0.9) < 1e-9, 'nine samples in ten are copies')
ok(a['misleading'] is True, 'and the lab says so')
ok(a['samples_per_refresh'] == 10.0, 'ten exports per refresh')
same = sl.export_aliasing(1.0, 1.0)
ok(same['misleading'] is False and same['duplicate_fraction'] == 0.0,
   'no aliasing is reported where there is none')
slower = sl.export_aliasing(1.0, 10.0)
ok(slower['effective_resolution_seconds'] == 10.0,
   'exporting slower than the device collects is also just the slower number')
ok(slower['misleading'] is False,
   'and is not the misleading case, because nothing is duplicated')
raises(lambda: sl.export_aliasing(0, 1), 'a zero collection interval')
raises(lambda: sl.export_aliasing(1, 0), 'a zero export interval')

# ---- the instruments that do see it ----------------------------------------
rows = sl.instrument_comparison(200e-6, 1.0, 1.0)
ok(len(rows) == 4, 'four instruments')
ok(sum(1 for x in rows if x['catches_every_burst']) == 3,
   'three of the four catch every burst')
ok(rows[0]['catches_every_burst'] is False,
   'and the one that does not is instantaneous sampling')
ok(all(x['gives_up'] for x in rows),
   'every instrument gives something up, and the table says what')
ok('maximum reached since the last read' in rows[1]['answers'],
   'the high-water mark answers a max-since question')

# ---- a probe is a sample, three ways ---------------------------------------
p = sl.probe_coverage(60, 10, 30, vantage_points=4, paths_per_vantage=3,
                      total_paths=40)
ok(p['finest_expressible_loss'] == 0.1, 'ten packets resolve 10 per cent')
ok(p['can_see_one_percent_loss'] is False, 'so one per cent is invisible')
ok(sl.probe_coverage(60, 100, 30)['can_see_one_percent_loss'] is True,
   'a hundred packets can just express it')
ok(abs(p['p_outage_hits_a_probe'] - 0.5) < 1e-12,
   'a 30 s outage against a 60 s interval has an even chance of being missed')
ok(sl.probe_coverage(60, 10, 120)['p_outage_hits_a_probe'] == 1.0,
   'an outage longer than the interval is always caught')
ok(sl.probe_coverage(60, 10, 0)['p_outage_hits_a_probe'] == 0.0,
   'a zero-length outage is never caught')
ok(abs(p['path_coverage'] - 0.3) < 1e-12, '12 of 40 paths are exercised')
ok(p['paths_never_probed'] == 28, 'so 28 are never touched')
ok(sl.probe_coverage(60, 10, 30, 100, 10, 40)['path_coverage'] == 1.0,
   'coverage is capped at all of them')
raises(lambda: sl.probe_coverage(0, 10, 30), 'a zero probe interval')
raises(lambda: sl.probe_coverage(60, 0, 30), 'a probe with no packets')
raises(lambda: sl.probe_coverage(60, 10, -1), 'a negative outage')
raises(lambda: sl.probe_coverage(60, 10, 30, total_paths=0), 'no paths')

# ---- the control ------------------------------------------------------------
c2 = sl.prove_the_limits_are_real()
ok(all(c2.values()), 'every claim the report prints is checked first')
ok(len(c2) == 7, 'seven checked claims')

# ---- the report -------------------------------------------------------------
buf = io.StringIO()
sl.report(buf)
text = buf.getvalue()
flat = ' '.join(text.split())
ok('%%' not in text, 'no literal double percent leaks')
ok('wrong by more than three orders of magnitude' in flat,
   'the chapter\'s microburst claim is refuted with a magnitude')
ok('Shorter actual windows may reduce dilution' in flat,
   'and shorter-window improvement is separated from the steady-mean model')
ok('the subscription is a request, not a measurement' in flat,
   'the aliasing point is stated')
ok('estimate from a sample' in flat, 'and the probe is framed as a sample')
ok('3.44 s' in text or '3.4' in text, 'the 32-bit wrap time is printed')

print('sampling_limits: %d checks passed' % PASS[0])
sys.exit(0)
