#!/usr/bin/env python3
"""Lab 59.2 --- what your telemetry can and cannot have seen, computed.

The chapter used to say the network is the witness that cannot be blinded, that
flow data is every conversation, and that packet capture is the ground truth
containing the content. Each is a statement about coverage, and coverage is
arithmetic. This works it out.

Four numbers decide whether a given connection could possibly be in your data:

  1. Was the PATH covered by an exporter at all?
  2. If sampled, was the flow SAMPLED? A short connection usually is not.
  3. Did the export RECORD survive the transport to the collector?
  4. For capture: was the packet still in the ring buffer when you looked?

Multiply them and the answer for a small connection is often a few parts in a
thousand --- which is the difference between "we have no record of it" and "it
did not happen".

    python3 telemetry_limits.py
    python3 telemetry_limits.py --json
    python3 test_telemetry_limits.py

This is offline calculation from stated inputs. It measures no network.
"""
import json
import math
import sys


class TelemetryError(ValueError):
    pass


def _pos(name, v, allow_zero=False):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise TelemetryError('%s must be a number, not %r' % (name, v))
    if v < 0 or (v == 0 and not allow_zero):
        raise TelemetryError('%s must be %s, got %r'
                             % (name, 'non-negative' if allow_zero else 'positive', v))
    return float(v)


def _prob(name, v):
    v = _pos(name, v, allow_zero=True)
    if v > 1:
        raise TelemetryError('%s is a probability between 0 and 1, got %r --- if you '
                             'meant a percentage, divide it' % (name, v))
    return v


# ---------------------------------------------------------------------------
# 1. Sampling: will a connection appear at all?
# ---------------------------------------------------------------------------

def p_flow_sampled(packets, one_in_n):
    """P(at least one packet) under independent Bernoulli packet sampling at 1/N."""
    packets = _pos('packets', packets)
    one_in_n = _pos('one_in_n', one_in_n)
    if one_in_n < 1:
        raise TelemetryError('one_in_n is a divisor: 1:1 is unsampled, and there '
                             'is no such thing as 1:0.5')
    if packets != int(packets):
        raise TelemetryError('packet count must be integral')
    return 1.0 - (1.0 - 1.0 / one_in_n) ** packets


def estimate_error(packets, one_in_n):
    """Packet-count RSE under independent sampling; byte RSE only for equal lengths.

    Sampled counts are scaled by N. The count of sampled packets is Binomial,
    so the relative standard error of the estimate is sqrt((1-p)/(n*p)) with
    p = 1/N --- which is ENORMOUS for small flows. A byte figure from sampled
    telemetry is an estimate, and for a small flow it is barely even that.
    """
    packets = _pos('packets', packets)
    one_in_n = _pos('one_in_n', one_in_n)
    if one_in_n < 1 or packets != int(packets):
        raise TelemetryError('N must be at least 1 and packet count integral')
    p = 1.0 / one_in_n
    expected = packets * p
    if expected == 0:
        return dict(expected_samples=0.0, relative_standard_error=float('inf'),
                    usable=False)
    rse = math.sqrt((1 - p) / (packets * p))
    return dict(expected_samples=expected, relative_standard_error=rse,
                usable=rse <= 0.10,
                note='usable here means a relative standard error of 10 per cent '
                     'or better, which needs about 100 sampled packets')


# ---------------------------------------------------------------------------
# 2. Timeouts: one record is not one conversation
# ---------------------------------------------------------------------------

def records_for_flow(duration_s, active_timeout_s, idle_gaps=0):
    """Additive teaching proxy: ceil(active duration/timeout) plus stated idle splits.

    Actual record counts depend on segment timings, exporter rules and events;
    this scalar proxy does not simulate idle/active timer interaction."""
    duration_s = _pos('duration_s', duration_s, allow_zero=True)
    active_timeout_s = _pos('active_timeout_s', active_timeout_s)
    if type(idle_gaps) is not int or idle_gaps < 0:
        raise TelemetryError('idle_gaps must be a nonnegative integer')
    return max(1, math.ceil(duration_s / active_timeout_s)) + idle_gaps


# ---------------------------------------------------------------------------
# 3. The chain
# ---------------------------------------------------------------------------

def p_visible(packets, one_in_n=1, path_covered=1.0, export_loss=0.0):
    """P(this connection leaves any trace in the flow data)."""
    p_s = p_flow_sampled(packets, one_in_n)
    cov = _prob('path_covered', path_covered)
    loss = _prob('export_loss', export_loss)
    p = cov * p_s * (1 - loss)
    return dict(p_path=cov, p_sampled=p_s, p_export=1 - loss, p_visible=p,
                p_invisible=1 - p,
                note=('A connection absent from the data had a %.1f%% chance of '
                      'being absent even if it happened. Absence of a record is '
                      'not evidence of absence of a connection.' % (100 * (1 - p))))


# ---------------------------------------------------------------------------
# 4. Capture: how long the ring buffer actually holds
# ---------------------------------------------------------------------------

def capture_window(rate_bps, buffer_bytes, snaplen=None, avg_packet_bytes=None):
    """Retention arithmetic; snaplen assumes every packet has the supplied length.

    The legacy avg_packet_bytes name is retained. For variable lengths use
    their distribution: E[min(length,snaplen)] is not min(E[length],snaplen)."""
    rate_bps = _pos('rate_bps', rate_bps)
    buffer_bytes = _pos('buffer_bytes', buffer_bytes)
    write_bps = rate_bps
    truncation = None
    if snaplen is not None:
        snaplen = _pos('snaplen', snaplen)
        if not avg_packet_bytes:
            raise TelemetryError('a snaplen needs an average packet size to be '
                                 'turned into a reduction in bytes written; '
                                 'supply avg_packet_bytes')
        avg_packet_bytes = _pos('avg_packet_bytes', avg_packet_bytes)
        kept = min(snaplen, avg_packet_bytes)
        truncation = kept / avg_packet_bytes
        write_bps = rate_bps * truncation
    seconds = buffer_bytes * 8.0 / write_bps
    return dict(seconds=seconds, minutes=seconds / 60.0, hours=seconds / 3600.0,
                truncation_factor=truncation,
                note=('A snaplen discards bytes beyond the limit and may truncate headers '
                      'as well as payload. This estimate assumes equal packet lengths.' if truncation else
                      'No snaplen: full packets, so the buffer is the shortest it '
                      'can be.'))


SCENARIOS = {
    'a DNS query and response (4 packets)': dict(packets=4, one_in_n=2048),
    'a short TLS handshake and one request (20 packets)': dict(packets=20, one_in_n=2048),
    'an interactive SSH session (500 packets)': dict(packets=500, one_in_n=2048),
    'a 100 MB download (70,000 packets)': dict(packets=70000, one_in_n=2048),
    'the same DNS query, unsampled NetFlow': dict(packets=4, one_in_n=1),
}

CHAIN = {
    'a beacon check-in, sampled, partial coverage': dict(
        packets=8, one_in_n=2048, path_covered=0.7, export_loss=0.01),
    'the same, unsampled flow export at every egress': dict(
        packets=8, one_in_n=1, path_covered=1.0, export_loss=0.01),
    'host-to-host inside one hypervisor, never crossing an exporter': dict(
        packets=8, one_in_n=1, path_covered=0.0, export_loss=0.0),
}

CAPTURE = {
    '10 Gb/s link at 50 per cent, 1 TB buffer, full packets':
        dict(rate_bps=5e9, buffer_bytes=1e12),
    'the same with a 128-byte snaplen on 900-byte packets':
        dict(rate_bps=5e9, buffer_bytes=1e12, snaplen=128, avg_packet_bytes=900),
    '100 Gb/s at 30 per cent, 100 TB buffer, full packets':
        dict(rate_bps=30e9, buffer_bytes=1e14),
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
    out.write('Lab 59.2 --- what the telemetry could possibly have seen\n')
    out.write('=' * 74 + '\n\n')
    out.write('WILL A CONNECTION APPEAR AT ALL? (1:2048 packet sampling)\n\n')
    out.write('  %-52s %10s %10s\n' % ('connection', 'P(sampled)', 'byte est.'))
    for name, kw in SCENARIOS.items():
        p = p_flow_sampled(**kw)
        e = estimate_error(**kw)
        out.write('  %-52s %9.4f  %9s\n'
                  % (name, p, 'usable' if e['usable'] else
                     ('+-%.0f%%' % (100 * e['relative_standard_error'])
                      if e['relative_standard_error'] != float('inf') else 'none')))
    out.write('\n  Read the first row again. A DNS lookup has roughly a two in a\n')
    out.write('  thousand chance of appearing in sampled telemetry. An investigator\n')
    out.write('  who concludes "this host never resolved that name" from its absence\n')
    out.write('  is reading a property of the sampling rate.\n\n')
    out.write('THE WHOLE CHAIN\n\n')
    for name, kw in CHAIN.items():
        v = p_visible(**kw)
        out.write('  %s\n' % name)
        out.write('    path %.2f  x  sampling %.4f  x  export %.2f  =  %.4f visible\n'
                  % (v['p_path'], v['p_sampled'], v['p_export'], v['p_visible']))
    out.write('\n')
    out.write('ONE CONVERSATION IS NOT ONE RECORD\n\n')
    for dur, to in ((30, 60), (600, 60), (3600, 60), (3600, 300)):
        out.write('  a %-5s second transfer, %3ds active timeout -> %d records\n'
                  % (dur, to, records_for_flow(dur, to)))
    out.write('\n  Counting records counts timeouts. A "top talkers" list built by\n')
    out.write('  record count ranks long conversations, not large ones.\n\n')
    out.write('HOW FAR BACK DOES FULL CAPTURE REACH?\n\n')
    for name, kw in CAPTURE.items():
        c = capture_window(**kw)
        out.write('  %-52s %6.1f min\n' % (name, c['minutes']))
    out.write('\n  Full packet capture at any real rate is a window measured in\n')
    out.write('  minutes, not a record. "Capture on alert" preserves what happens\n')
    out.write('  after the alert; the packets before it were already gone.\n')


def main(argv):
    if '--json' in argv:
        print(json.dumps({
            'sampling': {n: dict(p_sampled=p_flow_sampled(**k), **estimate_error(**k))
                         for n, k in SCENARIOS.items()},
            'chain': {n: p_visible(**k) for n, k in CHAIN.items()},
            'capture': {n: capture_window(**k) for n, k in CAPTURE.items()},
            'records': {'%ds/%ds' % (d, t): records_for_flow(d, t)
                        for d, t in ((30, 60), (600, 60), (3600, 60), (3600, 300))},
        }, indent=1))
        return 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
