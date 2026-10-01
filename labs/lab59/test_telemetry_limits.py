#!/usr/bin/env python3
"""Tests for telemetry_limits.py. The chapter quotes these numbers, so they are
checked against the closed forms they come from.

    python3 test_telemetry_limits.py
"""
import io
import math
import sys

import telemetry_limits as tl

CHECKS, FAILED = 0, []


def ok(c, l):
    global CHECKS
    CHECKS += 1
    if not c:
        FAILED.append(l)


def raises(fn, label, fragment=None):
    global CHECKS
    CHECKS += 1
    try:
        fn()
    except tl.TelemetryError as e:
        if fragment and fragment not in str(e):
            FAILED.append('%s (message lacked %r)' % (label, fragment))
        return
    except Exception as e:                                       # noqa: BLE001
        FAILED.append('%s (raised %s)' % (label, type(e).__name__))
        return
    FAILED.append('%s (did not raise)' % label)


# -- 1. Sampling ------------------------------------------------------------

ok(tl.p_flow_sampled(1, 1) == 1.0, 'unsampled telemetry sees every flow')
ok(abs(tl.p_flow_sampled(1, 2) - 0.5) < 1e-12, '1:2 sees a one-packet flow half the time')
ok(abs(tl.p_flow_sampled(4, 2048) - (1 - (1 - 1 / 2048) ** 4)) < 1e-15,
   'the closed form is 1-(1-1/N)^k')
ok(tl.p_flow_sampled(4, 2048) < 0.003,
   'A FOUR-PACKET DNS EXCHANGE AT 1:2048 IS SEEN LESS THAN 0.3%% OF THE TIME (%.5f)'
   % tl.p_flow_sampled(4, 2048))
ok(tl.p_flow_sampled(70000, 2048) > 0.9999, 'a large download is certain to be seen')
ok(tl.p_flow_sampled(20, 2048) < tl.p_flow_sampled(500, 2048) < tl.p_flow_sampled(70000, 2048),
   'the probability rises monotonically with flow length')
raises(lambda: tl.p_flow_sampled(0, 2048), 'a zero-packet flow is refused')
raises(lambda: tl.p_flow_sampled(4, 0.5), 'a sub-1 divisor is refused', 'no such thing')
raises(lambda: tl.p_flow_sampled(True, 10), 'a bool is not a packet count')

e = tl.estimate_error(4, 2048)
ok(e['expected_samples'] < 0.01, 'a short flow expects far less than one sample')
ok(e['relative_standard_error'] > 10, 'so its scaled estimate is meaningless')
ok(e['usable'] is False, 'and it is marked unusable')
big = tl.estimate_error(1000000, 2048)
ok(big['usable'] is True, 'a very large flow gives a usable estimate')
ok(abs(big['relative_standard_error'] - math.sqrt((1 - 1 / 2048) / (1000000 / 2048)))
   < 1e-12, 'the relative standard error matches the binomial form')
ok(tl.estimate_error(1, 10 ** 9)['relative_standard_error'] > 100,
   'an extreme sampling rate makes any estimate absurd')


# -- 2. Records are not conversations --------------------------------------

ok(tl.records_for_flow(30, 60) == 1, 'a short transfer is one record')
ok(tl.records_for_flow(600, 60) == 10, 'a ten-minute transfer at a 60s timeout is ten')
ok(tl.records_for_flow(3600, 60) == 60, 'an hour is sixty')
ok(tl.records_for_flow(3600, 300) == 12, 'a longer timeout makes fewer records')
ok(tl.records_for_flow(0, 60) == 1, 'a zero-length flow is still one record')
ok(tl.records_for_flow(600, 60, idle_gaps=3) == 13, 'idle gaps add records too')
raises(lambda: tl.records_for_flow(60, 0), 'a zero timeout is refused')


# -- 3. The chain ----------------------------------------------------------

v = tl.p_visible(8, one_in_n=2048, path_covered=0.7, export_loss=0.01)
ok(abs(v['p_visible'] - 0.7 * tl.p_flow_sampled(8, 2048) * 0.99) < 1e-12,
   'the chain multiplies its three terms')
ok(v['p_visible'] < 0.01, 'a sampled beacon check-in is very unlikely to appear')
ok('not evidence of absence' in v['note'], 'and the note says what that means')
full = tl.p_visible(8, one_in_n=1, path_covered=1.0, export_loss=0.01)
ok(abs(full['p_visible'] - 0.99) < 1e-12, 'unsampled full coverage is limited only by loss')
none = tl.p_visible(8, one_in_n=1, path_covered=0.0)
ok(none['p_visible'] == 0.0, 'traffic that never crosses an exporter is never visible')
ok(none['p_invisible'] == 1.0, 'and is certainly invisible')
raises(lambda: tl.p_visible(8, path_covered=1.5), 'a coverage above 1 is refused',
       'divide it')
raises(lambda: tl.p_visible(8, export_loss=-0.1), 'a negative loss is refused')


# -- 4. Capture windows ----------------------------------------------------

c = tl.capture_window(5e9, 1e12)
ok(abs(c['seconds'] - 1e12 * 8 / 5e9) < 1e-6, 'the window is buffer bits over rate')
ok(25 < c['minutes'] < 28, 'A 1 TB BUFFER AT 5 Gb/s HOLDS UNDER HALF AN HOUR (%.1f min)'
   % c['minutes'])
snap = tl.capture_window(5e9, 1e12, snaplen=128, avg_packet_bytes=900)
ok(snap['minutes'] > c['minutes'], 'a snaplen extends it')
ok(abs(snap['truncation_factor'] - 128 / 900) < 1e-12, 'by exactly the truncation ratio')
ok('truncate headers' in snap['note'], 'and the note says what it costs')
ok(tl.capture_window(30e9, 1e14)['minutes'] > 400, 'a bigger buffer at 100G still hours')
raises(lambda: tl.capture_window(5e9, 1e12, snaplen=128),
       'a snaplen without an average packet size is refused', 'average packet size')
raises(lambda: tl.capture_window(0, 1e12), 'a zero rate is refused')


# -- 5. The report ---------------------------------------------------------

buf = io.StringIO()
tl.report(buf)
t = buf.getvalue()
ok('not evidence' in t.lower() or 'property of the sampling rate' in t,
   'the report states what absence does and does not mean')
ok('Counting records counts timeouts' in t, 'and that records are not conversations')
ok('already gone' in t, 'and that pre-alert packets are lost')
_s = sys.stdout
sys.stdout = io.StringIO()
try:
    rc, rj = tl.main([]), tl.main(['--json'])
finally:
    sys.stdout = _s
ok(rc == 0 and rj == 0, 'both modes run')

print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
