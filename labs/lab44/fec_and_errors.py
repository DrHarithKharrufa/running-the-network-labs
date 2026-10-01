#!/usr/bin/env python3
"""Lab 44.3 --- what FEC gain is, and what a pre-FEC error count is worth.

WHY THIS EXISTS
---------------
Chapter 44 made two claims about error correction that lead operators astray.

The first was that FEC "effectively adds several decibels --- often 8 to 11 dB
--- to the budget, which is a vast amount, more than most of the losses"
in the POWER budget.  Coding gain is not a reduction in path attenuation. This model expresses it
as an OSNR requirement change for a specified comparison; other systems may
express coding benefit through SNR, Eb/N0 or receiver sensitivity. It does nothing
about fibre attenuation, splices or connectors.  Putting it in the same sentence
as a list of path losses invites the reader to subtract it from one, which would
approve links that cannot work.  The gain also is not free: FEC adds overhead,
the overhead raises the symbol rate, and a wider signal collects more noise ---
which is why the honest figure is NET coding gain and why this script computes
the deduction rather than mentioning it.

The second was that post-FEC errors "tell you nothing" and that a rising pre-FEC
rate gives "weeks of warning" --- "an outage with a countdown".  Post-FEC errors
are corrupted data reaching the customer and are the one thing you should always
alarm on.  And the countdown exists only if the thing degrading you is slow: the
relationship between OSNR and error rate is so steep that a small, sudden OSNR
loss --- a connector disturbed on a patch, a bend, a protection switch --- takes
a link from comfortable to past threshold with no ramp at all.  The warning is
in the OSNR margin, measured in dB, not in the error rate.

WHAT IS NOT MODELLED
--------------------
No transponder, no FEC implementation, no measurement.  The error-rate curve
here is the textbook expression for one modulation format with no
implementation penalty, used to show the SHAPE of the relationship; a real
transponder's curve is its own and comes from its vendor.  Thresholds,
overheads and gains are inputs. Nothing here validates a configuration.

    python3 fec_and_errors.py
    python3 fec_and_errors.py --json
    python3 test_fec_and_errors.py
"""
import argparse
import json
import math
import sys


class FecError(ValueError):
    """The system described cannot be evaluated."""


def q_from_snr(snr_db):
    return math.sqrt(2.0 * 10.0 ** (snr_db / 10.0))


def erfc(x):
    return math.erfc(x)


def ber_qpsk(snr_db):
    """Textbook QPSK bit error rate against SNR per bit, no implementation penalty.

    Used for its SHAPE only: what matters below is how many orders of magnitude
    the error rate moves for one decibel, and that steepness is the point.
    """
    return 0.5 * erfc(math.sqrt(10.0 ** (snr_db / 10.0)))


# --------------------------------------------------------------------------
# 1. coding gain is an OSNR quantity, and it has a deduction
# --------------------------------------------------------------------------
def net_coding_gain(gross_gain_db, overhead_percent):
    """Illustrative normalisation: gross gain less 10log10(1+overhead).

    Under fixed payload, modulation and the stated noise-bandwidth model,
    FEC overhead raises the symbol rate. Do not subtract this penalty again
    from a vendor net gain or sensitivity already specified with FEC.
    In this constructed comparison, A signal of
    greater bandwidth collects proportionally more noise, so the OSNR
    requirement rises by 10log10(1 + overhead), and that rise comes straight off
    the headline gain.
    """
    if gross_gain_db < 0:
        raise FecError('a coding gain is not negative, got %r' % (gross_gain_db,))
    if overhead_percent < 0:
        raise FecError('an overhead is not negative, got %r' % (overhead_percent,))
    penalty = 10.0 * math.log10(1.0 + overhead_percent / 100.0)
    return {'gross_gain_db': gross_gain_db, 'overhead_percent': overhead_percent,
            'rate_penalty_db': penalty, 'net_gain_db': gross_gain_db - penalty}


def where_gain_applies(power_budget_margin_db, osnr_margin_db, net_gain_db):
    """The category error, made explicit.

    Coding gain reduces the OSNR the receiver requires. It reduces no path loss
    whatsoever, so it changes the OSNR margin and leaves the power margin
    exactly where it was. A budget that subtracts it from the power side is
    approving links that will not work.
    """
    return {
        'power_margin_before_db': power_budget_margin_db,
        'power_margin_after_db': power_budget_margin_db,     # unchanged, on purpose
        'osnr_margin_before_db': osnr_margin_db,
        'osnr_margin_after_db': osnr_margin_db + net_gain_db,
        'if_wrongly_applied_to_power_db': power_budget_margin_db + net_gain_db,
        'note': ('coding gain changes what the RECEIVER needs, not what the '
                 'PATH costs'),
    }


# --------------------------------------------------------------------------
# 2. the countdown that is not one
# --------------------------------------------------------------------------
def ber_against_snr(snr_points):
    return [{'snr_db': s, 'ber': ber_qpsk(s)} for s in snr_points]


def degradation(start_snr_db, threshold_ber, losses_db):
    """Walk an SNR down in steps and report the error rate at each.

    The column that matters is not the error rate; it is the margin in dB. The
    error rate is an exponential function of it, so it looks flat and then
    looks like a cliff --- which is why it reads as a sudden failure even when
    the underlying degradation was perfectly steady.
    """
    if threshold_ber <= 0 or threshold_ber >= 1:
        raise FecError('a threshold BER is between 0 and 1, got %r'
                       % (threshold_ber,))
    # the SNR at which the error rate reaches the threshold, by bisection
    lo, hi = -10.0, 30.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if ber_qpsk(mid) > threshold_ber:
            lo = mid
        else:
            hi = mid
    threshold_snr = (lo + hi) / 2.0

    rows = []
    for loss in losses_db:
        snr = start_snr_db - loss
        rows.append({'snr_loss_db': loss, 'snr_db': snr, 'ber': ber_qpsk(snr),
                     'margin_db': snr - threshold_snr,
                     'past_threshold': ber_qpsk(snr) > threshold_ber})
    return {'threshold_ber': threshold_ber, 'threshold_snr_db': threshold_snr,
            'rows': rows}


# --------------------------------------------------------------------------
# 3. what a pre-FEC reading is worth statistically
# --------------------------------------------------------------------------
def observation_needed(ber, confidence=0.95):
    """Bits you must observe before 'no errors' means the rate is below `ber`.

    Seeing zero errors in N bits is consistent with any rate low enough to have
    produced none, and the usual bound is N >= -ln(1-confidence)/BER. Below that
    many bits, a clean counter is not evidence of anything.
    """
    if not 0 < ber < 1:
        raise FecError('a BER is between 0 and 1, got %r' % (ber,))
    if not 0 < confidence < 1:
        raise FecError('a confidence is between 0 and 1, got %r' % (confidence,))
    return -math.log(1.0 - confidence) / ber


def seconds_needed(ber, line_rate_gbps, confidence=0.95):
    if line_rate_gbps <= 0:
        raise FecError('a line rate is positive, got %r' % (line_rate_gbps,))
    return observation_needed(ber, confidence) / (line_rate_gbps * 1e9)


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------
def analyse():
    gains = [net_coding_gain(g, o) for g, o in
             ((11.0, 25.0), (11.0, 15.0), (9.0, 7.0), (6.0, 7.0))]
    return {
        'gains': gains,
        'placement': where_gain_applies(1.5, 0.8, gains[0]['net_gain_db']),
        'steepness': ber_against_snr([4, 5, 6, 7, 8, 9, 10, 11, 12]),
        # a deployed link runs a few dB above threshold, not ten: the design
        # margin has already been spent on the path it actually crosses
        'slow': degradation(6.0, 2e-2, [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]),
        'sudden': degradation(6.0, 2e-2, [0, 3.0]),
        'observation': [(b, observation_needed(b), seconds_needed(b, 400.0))
                        for b in (1e-3, 1e-6, 1e-9, 1e-12, 1e-15)],
        'five_minute_fraction': (300.0 * 400e9) / observation_needed(1e-15),
    }


def report(a):
    print('FEC arithmetic. No transponder, no FEC implementation, no')
    print('measurement --- a textbook curve used for its shape, and inputs.\n')

    print('A. Coding gain is not free, and the overhead comes off it')
    print('%12s | %10s | %12s | %s'
          % ('gross gain', 'overhead', 'rate penalty', 'net coding gain'))
    print('-' * 62)
    for g in a['gains']:
        print('%9.1f dB | %8.0f%%  | %10.2f dB | %12.2f dB'
              % (g['gross_gain_db'], g['overhead_percent'],
                 g['rate_penalty_db'], g['net_gain_db']))
    print('\nThe overhead raises the symbol rate, a wider signal collects more')
    print('noise, and the OSNR requirement rises by 10log10(1+overhead). That')
    print('deduction is why the honest figure is NET coding gain, and why a')
    print('headline gain quoted without its overhead is not a number you can use.')

    p = a['placement']
    print('\nB. Where the gain applies --- and where it does not')
    print('%34s | %10s | %10s' % ('', 'power margin', 'OSNR margin'))
    print('-' * 60)
    print('%34s | %8.2f dB | %8.2f dB'
          % ('before FEC is considered', p['power_margin_before_db'],
             p['osnr_margin_before_db']))
    print('%34s | %8.2f dB | %8.2f dB'
          % ('after applying the net gain', p['power_margin_after_db'],
             p['osnr_margin_after_db']))
    print('\nThe power margin does not move, because coding gain reduces what the')
    print('RECEIVER needs and reduces no fibre attenuation, no splice and no')
    print('connector. Apply it to the power side by mistake and the same link')
    print('shows %.2f dB of margin it does not have --- which is how a span that'
          % (p['if_wrongly_applied_to_power_db'] - p['power_margin_before_db']))
    print('cannot work gets approved.')

    st = a['steepness']
    print('\nC. Why the error rate looks like a cliff')
    print('%9s | %14s | %s' % ('SNR', 'error rate', 'orders of magnitude per dB'))
    print('-' * 58)
    prev = None
    for r in st:
        delta = ('%+.1f' % math.log10(r['ber'] / prev['ber'])
                 if prev and prev['ber'] > 0 and r['ber'] > 0 else '--')
        print('%6.1f dB | %14.2e | %s' % (r['snr_db'], r['ber'], delta))
        prev = r
    print('\nThe last column is what one decibel is worth, and notice that it')
    print('GROWS: a third of an order of magnitude near the threshold, more than')
    print('one and a half further up. So an error rate is a poor thing to trend.')
    print('It looks flat while the margin drains and then it looks like a cliff,')
    print('and the cliff is not an event --- it is the same steady decline seen')
    print('through a logarithm.')

    slow, sudden = a['slow'], a['sudden']
    print('\nD. A countdown, and the same link with no countdown at all')
    print('threshold error rate %.0e, reached at %.2f dB'
          % (slow['threshold_ber'], slow['threshold_snr_db']))
    print('%12s | %9s | %12s | %9s | %s'
          % ('SNR lost', 'SNR', 'error rate', 'margin', 'state'))
    print('-' * 64)
    for r in slow['rows']:
        print('%9.1f dB | %7.2f   | %12.2e | %7.2f  | %s'
              % (r['snr_loss_db'], r['snr_db'], r['ber'], r['margin_db'],
                 'PAST THRESHOLD' if r['past_threshold'] else 'correcting'))
    print('\nThat is the ramp the chapter described, and it is real when the')
    print('cause is ageing: seven readings, each one a warning you could have')
    print('acted on. Now the SAME link losing 3 dB at a stroke, because somebody')
    print('disturbed a connector on a patch or a bend appeared:')
    print('%12s | %9s | %12s | %9s | %s'
          % ('SNR lost', 'SNR', 'error rate', 'margin', 'state'))
    print('-' * 64)
    for r in sudden['rows']:
        print('%9.1f dB | %7.2f   | %12.2e | %7.2f  | %s'
              % (r['snr_loss_db'], r['snr_db'], r['ber'], r['margin_db'],
                 'PAST THRESHOLD' if r['past_threshold'] else 'correcting'))
    print('\nTwo readings: before, and past threshold. No ramp, no weeks, and no')
    print('intermediate value anybody could have trended. The countdown was')
    print('never in the error rate. It was in the margin, and it only looks like')
    print('a countdown when the thing spending that margin is slow --- so trend')
    print('the MARGIN in dB, and treat a sudden loss as the thing it is.')

    print('\nE. And a clean counter is not evidence until you have watched enough')
    print('%14s | %18s | %s'
          % ('rate to prove', 'bits to observe', 'at 400 Gb/s that is'))
    print('-' * 62)
    for ber, bits, secs in a['observation']:
        if secs < 1:
            when = '%.3g ms' % (secs * 1000.0)
        elif secs < 60:
            when = '%.2f s' % secs
        elif secs < 86400:
            when = '%.1f hours' % (secs / 3600.0)
        else:
            when = '%.1f days' % (secs / 86400.0)
        print('%14.0e | %18.3e | %s' % (ber, bits, when))
    print('\nA post-FEC counter reading zero over a five-minute poll says little')
    print('about a 1e-15 error rate: at 400 Gb/s you have watched %.0f%% of the'
          % (a['five_minute_fraction'] * 100.0))
    print('traffic you would need. That is an argument for watching it over long')
    print('windows and alarming on ANY non-zero count, not for ignoring it:')
    print('a post-FEC error is corrupted data that reached the customer.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        a = analyse()
    except FecError as e:
        print('fec error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(a, indent=2))
    else:
        report(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
