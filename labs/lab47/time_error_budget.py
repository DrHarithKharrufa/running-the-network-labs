#!/usr/bin/env python3
"""Lab 47.1 -- illustrative timing budgets and holdover sensitivity.

No equipment, reference receiver or time-error measurement is represented.
Constant magnitudes add as a conservative bound. The optional RSS calculation
is statistical sensitivity only: uncorrelated compatible measures are needed,
and arbitrary peak errors do not acquire a worst-case bound by using RSS.
Actual clock filtering and applicable standard masks are not simulated.
Stable directional asymmetry gives a fixed half-asymmetry bias in the ideal
four-timestamp model; time-varying asymmetry need not behave as a constant.

Holdover uses nonnegative error bounds, constant initial frequency offset and
constant frequency-drift rate. Real environmental histories need another model.
The vendor-inspired table substitutes temperature-stability values for offsets
as a sensitivity exercise only; it does not predict product holdover. The ePRTC
headline uses a different reference arrangement including a caesium clock.
"""
import argparse
import json
import math
import sys


class BudgetError(ValueError):
    """The described chain or requirement cannot be evaluated."""


# ---------------------------------------------------------------------------
# an element of the chain
# ---------------------------------------------------------------------------
def element(name, cte_ns=0.0, dte_ns=0.0, asymmetry_ns=0.0):
    """One element, with its error split the way a budget has to split it.

    cte_ns        constant time error: this element's own systematic offset
    dte_ns        dynamic time error: the varying part it contributes
    asymmetry_ns  uncompensated forward/reverse path asymmetry on the link
                  INTO this element.  Half of it appears as offset --- see
                  asymmetry_bias() below, which is the single most misunderstood
                  number in PTP engineering.
    """
    if dte_ns < 0 or asymmetry_ns < 0:
        raise BudgetError('%s: dynamic error and asymmetry are magnitudes' % name)
    return {'name': name, 'cte_ns': float(cte_ns), 'dte_ns': float(dte_ns),
            'asymmetry_ns': float(asymmetry_ns)}


def asymmetry_bias(asymmetry_ns):
    """The offset error produced by an uncompensated path asymmetry.

    PTP estimates the offset from four timestamps: t1 (master sends Sync), t2
    (slave receives it), t3 (slave sends Delay_Req), t4 (master receives it).
    Writing the one-way delays as d_ms and d_sm and the true offset as o,

        t2 - t1 = d_ms + o          t4 - t3 = d_sm - o

    The protocol computes

        mean path delay = ((t2-t1) + (t4-t3)) / 2 = (d_ms + d_sm) / 2
        estimated offset = ((t2-t1) - (t4-t3)) / 2 = o + (d_ms - d_sm) / 2

    So the estimate is wrong by exactly HALF the asymmetry, and no amount of
    averaging removes it, because it is not noise --- it is the same every time.
    That is why asymmetry is a CONSTANT error and why a fibre pair with a 200 ns
    difference between its directions puts 100 ns of bias into every clock
    downstream of it until somebody measures and compensates it.
    """
    return asymmetry_ns / 2.0


# ---------------------------------------------------------------------------
# the chain
# ---------------------------------------------------------------------------
def chain_error(elements, dynamic_combination='rss'):
    """Add constant magnitudes and explicitly select a dynamic combination.

    RSS is an illustrative statistical assumption, not a maximum-error bound.
    The sum can conservatively bound absolute contributions. Neither option
    models the clock transfer functions or proves standards conformance.
    """
    if dynamic_combination not in ('sum', 'rss'):
        raise BudgetError("dynamic_combination is 'sum' or 'rss', got %r"
                          % (dynamic_combination,))
    if not elements:
        raise BudgetError('a chain has at least one element')

    cte = sum(abs(e['cte_ns']) for e in elements)
    bias = sum(asymmetry_bias(e['asymmetry_ns']) for e in elements)
    dtes = [e['dte_ns'] for e in elements]
    if dynamic_combination == 'sum':
        dte = sum(dtes)
    else:
        dte = math.sqrt(sum(d * d for d in dtes))
    return {'constant_ns': cte, 'asymmetry_bias_ns': bias, 'dynamic_ns': dte,
            'total_ns': cte + bias + dte, 'elements': len(elements),
            'dynamic_combination': dynamic_combination}


# ---------------------------------------------------------------------------
# holdover, which is a curve and not a number
# ---------------------------------------------------------------------------
def holdover_error_ns(seconds, initial_ns=0.0, frequency_offset_ppb=0.0,
                      drift_ppb_per_day=0.0):
    """Phase error accumulated by a free-running oscillator after t seconds.

    A frequency offset of f parts per billion accumulates f nanoseconds of phase
    every second --- that is what a part per billion IS.  On top of that the
    offset itself drifts, mostly with ageing and temperature, which integrates
    to a quadratic term.  So

        error(t) = initial + f.t + (1/2).(drift rate).t^2

    with the drift rate converted from per-day to per-second.  The shape is what
    matters: holdover error is small and roughly linear at first and then turns
    upward, so a chain that is fine after an hour can be far outside the budget
    after a day, and quoting "the holdover penalty" as one number says nothing
    about which.
    """
    if seconds < 0:
        raise BudgetError('holdover does not run backwards')
    drift_per_s2 = drift_ppb_per_day / 86400.0
    return (initial_ns + frequency_offset_ppb * seconds
            + 0.5 * drift_per_s2 * seconds * seconds)


def holdover_seconds_until(limit_ns, initial_ns=0.0, frequency_offset_ppb=0.0,
                           drift_ppb_per_day=0.0, cap_s=30 * 86400):
    """First crossing within cap_s; None means no crossing within that horizon.

    Nonnegative magnitude inputs define the monotone envelope used here.
    No extrapolated guarantee is made beyond the supplied horizon.
    """
    vals = (limit_ns, initial_ns, frequency_offset_ppb, drift_ppb_per_day, cap_s)
    if not all(math.isfinite(v) for v in vals):
        raise BudgetError('holdover bounds must be finite')
    if min(initial_ns, frequency_offset_ppb, drift_ppb_per_day) < 0 or cap_s <= 0:
        raise BudgetError('holdover magnitudes are nonnegative and horizon positive')
    if limit_ns <= initial_ns:
        return 0.0
    if holdover_error_ns(cap_s, initial_ns, frequency_offset_ppb,
                         drift_ppb_per_day) < limit_ns:
        return None
    lo, hi = 0.0, cap_s
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if holdover_error_ns(mid, initial_ns, frequency_offset_ppb,
                             drift_ppb_per_day) < limit_ns:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ---------------------------------------------------------------------------
# the requirement, which has to say what it is measured against
# ---------------------------------------------------------------------------
def requirement(name, limit_ns, reference_point, measurement_uncertainty_ns=0.0,
                endpoint_allocation_ns=0.0):
    """A budget without a reference point is not a budget.

    'Within 1.5 microseconds' is meaningless until you say 1.5 microseconds of
    WHAT, measured WHERE.  Absolute time error at the air interface and relative
    alignment between two radios are different requirements with different
    allocations, and the network's share is what is left after the endpoint's
    share and the uncertainty of your own measurement are taken out.
    """
    if limit_ns <= 0:
        raise BudgetError('%s: a limit is positive' % name)
    if reference_point not in ('air interface', 'network interface',
                              'relative between radios'):
        raise BudgetError('%s: state the reference point' % name)
    net = limit_ns - endpoint_allocation_ns - measurement_uncertainty_ns
    if net <= 0:
        raise BudgetError('%s: the endpoint and measurement allocations already '
                          'consume the whole limit (%g ns of %g ns)'
                          % (name, endpoint_allocation_ns +
                             measurement_uncertainty_ns, limit_ns))
    return {'name': name, 'limit_ns': float(limit_ns),
            'reference_point': reference_point,
            'measurement_uncertainty_ns': float(measurement_uncertainty_ns),
            'endpoint_allocation_ns': float(endpoint_allocation_ns),
            'network_allocation_ns': net}


def assess(req, chain, holdover_ns=0.0):
    """Compare a chain against a requirement.  The verdict is computed."""
    total = chain['total_ns'] + holdover_ns
    margin = req['network_allocation_ns'] - total
    return {'requirement': req['name'], 'reference_point': req['reference_point'],
            'network_allocation_ns': req['network_allocation_ns'],
            'chain_total_ns': chain['total_ns'], 'holdover_ns': holdover_ns,
            'total_ns': total, 'margin_ns': margin, 'meets': margin >= 0}


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
# ILLUSTRATIVE chain.  No device here exists and no figure is any vendor's.
def build_chain(boundary_clocks=4, asymmetry_ns=0.0):
    els = [element('grandmaster, reference locked', cte_ns=20, dte_ns=10)]
    for i in range(boundary_clocks):
        els.append(element('boundary clock %d' % (i + 1), cte_ns=20, dte_ns=15,
                           asymmetry_ns=asymmetry_ns))
    els.append(element('cell site clock', cte_ns=50, dte_ns=30))
    return els


REQ = requirement('phase alignment to the radio', 1500, 'air interface',
                  measurement_uncertainty_ns=50, endpoint_allocation_ns=350)

# ILLUSTRATIVE oscillator grades.  Not products, not measured, not specified
# limits: they are here to show the SHAPE of holdover, which is the point.
# Two sets. The illustrative one keeps the shape of the lesson visible; the
# sourced one comes from a real datasheet, and the two say different things.
#
# ILLUSTRATIVE --- residual figures, invented to show the spread.
OSCILLATORS = {
    'disciplined TCXO': {'frequency_offset_ppb': 5.0, 'drift_ppb_per_day': 20.0},
    'ordinary OCXO': {'frequency_offset_ppb': 0.5, 'drift_ppb_per_day': 1.0},
    'temperature-controlled OCXO': {'frequency_offset_ppb': 0.05,
                                    'drift_ppb_per_day': 0.1},
    'rubidium': {'frequency_offset_ppb': 0.005, 'drift_ppb_per_day': 0.01},
}

# SOURCED --- the holdover performance table of the Oscilloquartz OSA 5412
# datasheet (Adtran/ADVA), retrieved 18 September 2026 and cited in the chapter.
# Sensitivity substitution ONLY: temperature stability is used as a constant
# offset bound, not a measured residual. Selected table entries mix raw ageing
# with compensated rubidium temperature stability; conditions are not uniform.
# Do not rank or predict actual products from this table (1e-9 = 1 ppb).
VENDOR_OSCILLATORS = {
    'OCXO (Stratum 3 / G.812 Type III)':
        {'frequency_offset_ppb': 5.0, 'drift_ppb_per_day': 0.5},
    'HQ+ OCXO (G.812 Type I)':
        {'frequency_offset_ppb': 0.2, 'drift_ppb_per_day': 0.2},
    'HQ++ DOCXO (Stratum 2 / G.812 Type II)':
        {'frequency_offset_ppb': 0.01, 'drift_ppb_per_day': 0.05},
    'rubidium (Stratum 2 / G.812 Type II)':
        {'frequency_offset_ppb': 0.02, 'drift_ppb_per_day': 0.005},
}

# The same datasheet also makes an end-to-end claim for its enhanced primary
# reference time clock: holdover within 100 ns for up to 100 days, and up to
# 150 days with the improved algorithm. That claim is not one of the grades
# above --- it is what the product achieves with a caesium clock and an
# algorithm that has learned the oscillator against GNSS --- and comparing the
# two is the point of section F.
VENDOR_EPRTC_CLAIM = {'ns': 100.0, 'days': 100.0, 'improved_days': 150.0}


def hms(s):
    if s is None:
        return 'longer than 30 days'
    if s < 90:
        return '%.0f s' % s
    if s < 5400:
        return '%.1f min' % (s / 60.0)
    if s < 172800:
        return '%.1f h' % (s / 3600.0)
    return '%.1f days' % (s / 86400.0)


def section_a():
    print('A. The requirement, before any chain is added to it')
    print('-' * 74)
    print('  %-34s %s' % ('requirement', REQ['name']))
    print('  %-34s %s' % ('reference point', REQ['reference_point']))
    print('  %-34s %.0f ns' % ('stated limit', REQ['limit_ns']))
    print('  %-34s %.0f ns' % ('endpoint allocation', REQ['endpoint_allocation_ns']))
    print('  %-34s %.0f ns' % ('measurement uncertainty', REQ['measurement_uncertainty_ns']))
    print('  %-34s %.0f ns' % ('LEFT FOR THE NETWORK', REQ['network_allocation_ns']))
    print()
    over = 100.0 * (REQ['limit_ns'] / REQ['network_allocation_ns'] - 1.0)
    print('  The old lab budgeted the chain against the whole %.0f ns.  The radio'
          % REQ['limit_ns'])
    print('  and the measurement have shares first, and what the network may')
    print('  spend is what remains.  A budget that skips this step gives itself')
    print('  %.0f%% more room than it is entitled to --- which is exactly the size'
          % over)
    print('  of error that makes a chain pass on paper and fail on site.')
    print()


def section_b():
    print('B. The chain, with the two kinds of error kept apart')
    print('-' * 74)
    print('%-26s %10s %10s %11s' % ('element', 'constant', 'dynamic', 'asymmetry'))
    for e in build_chain():
        print('%-26s %8.0f ns %8.0f ns %9.0f ns'
              % (e['name'], e['cte_ns'], e['dte_ns'], e['asymmetry_ns']))
    print()
    print('%-26s %10s %10s %10s %9s'
          % ('combination', 'constant', 'dynamic', 'total', 'verdict'))
    out = {}
    for comb in ('sum', 'rss'):
        ch = chain_error(build_chain(), comb)
        a = assess(REQ, ch)
        out[comb] = (ch, a)
        print('%-26s %8.0f ns %8.0f ns %8.0f ns %9s'
              % ('dynamic combined by ' + comb, ch['constant_ns'],
                 ch['dynamic_ns'], ch['total_ns'],
                 'meets' if a['meets'] else 'FAILS'))
    print()
    print('  The two differ by %.0f ns on a six-element chain, and the gap widens'
          % (out['sum'][0]['total_ns'] - out['rss'][0]['total_ns']))
    print('  with every element added.  Neither is "the answer": the applicable')
    print('  standard says how to combine, and a budget has to declare which rule')
    print('  it used. RSS needs compatible uncorrelated statistical measures;')
    print('  summing absolute bounds can be conservative and legitimate.')
    print()
    return out


def section_c():
    print('C. Asymmetry: the error that halves itself and never averages out')
    print('-' * 74)
    print('%-44s %10s %9s' % ('uncompensated asymmetry per link', 'bias', 'total'))
    rows = []
    for asym in (0, 20, 100, 200, 500):
        ch = chain_error(build_chain(asymmetry_ns=asym), 'rss')
        a = assess(REQ, ch)
        rows.append((asym, ch, a))
        print('%-44s %8.0f ns %7.0f ns  %s'
              % ('%d ns difference between the two directions' % asym,
                 asymmetry_bias(asym), ch['total_ns'],
                 'meets' if a['meets'] else 'FAILS'))
    print()
    print('  Four links with 500 ns of asymmetry each put %.0f ns of constant'
          % rows[-1][1]['asymmetry_bias_ns'])
    print('  bias into the chain --- half of each, four times --- and the budget')
    print('  fails when that bias is ADDED to the roughly 194 ns baseline.')
    print('  the estimate comes out wrong by exactly half the difference between')
    print('  them, every single time, which is why no amount of filtering helps.')
    print()
    print('  Asymmetry comes from ordinary things: fibre pairs of unequal length')
    print('  in the same cable, an amplifier or regenerator in one direction only,')
    print('  different transmit and receive paths through a device, a protection')
    print('  switch that moved one direction and not the other. Stable bias can')
    print('  be calibrated with uncertainty; changes need renewed evaluation.')
    print()
    return rows


def section_d():
    print('D. Holdover is a curve, so the answer is a duration')
    print('-' * 74)
    ch = chain_error(build_chain(), 'rss')
    budget_for_holdover = REQ['network_allocation_ns'] - ch['total_ns']
    print('  chain uses %.0f ns of the %.0f ns the network may spend, so holdover'
          % (ch['total_ns'], REQ['network_allocation_ns']))
    print('  has %.0f ns before the budget is exceeded.' % budget_for_holdover)
    print()
    print('%-28s %11s %11s %11s %14s'
          % ('oscillator', 'at 1 h', 'at 8 h', 'at 24 h', 'time to limit'))
    out = {}
    for name, o in OSCILLATORS.items():
        e1 = holdover_error_ns(3600, **o)
        e8 = holdover_error_ns(8 * 3600, **o)
        e24 = holdover_error_ns(24 * 3600, **o)
        t = holdover_seconds_until(budget_for_holdover, **o)
        out[name] = (e1, e8, e24, t)
        print('%-28s %9.0f ns %9.0f ns %9.0f ns %14s'
              % (name, e1, e8, e24, hms(t)))
    print()
    ok1 = [n for n, v in out.items() if v[0] <= budget_for_holdover]
    ok24 = [n for n, v in out.items() if v[2] <= budget_for_holdover]
    print('  %d of the %d are still inside the budget after an hour and %d after'
          % (len(ok1), len(out), len(ok24)))
    print('  twenty-four.  Holding this budget for a day is a %s requirement,'
          % sorted(ok24)[0] if ok24 else '  twenty-four.  Nothing here holds it for a day,')
    print('  for these invented residuals and this remaining chain budget.')
    print('  Better chain margin can extend the available holdover duration.')
    print()
    print('  "A holdover penalty of 1000 ns" describes none of these, because the')
    print('  question was never how much error holdover adds.  It is how long you')
    times = [v[3] for v in out.values() if v[3]]
    print('  have: %s against %s, a factor of %.0f between the'
          % (hms(min(times)), hms(max(times)), max(times) / min(times)))
    print('  illustrative residual models, not quoted products or prices. A')
    print('  second reference is a nice-to-have or the difference between a')
    print('  maintenance window and an outage.')
    print()
    print('  Note also what holdover is NOT.  It begins when the clock REJECTS a')
    print('  reference and coasts on its own, which means it has correctly')
    print('  noticed something is wrong.  A clock that keeps following a')
    print('  reference that has gone bad --- a spoofed signal, a receiver')
    print('  reporting lock on a bad solution --- never enters holdover at all,')
    print('  and this holdover envelope does not bound the resulting error.')
    print('  Detection may reject spoofing; undetected false time may drift slowly.')
    print()
    return out


def section_e():
    print('E. The claim the old lab printed, evaluated instead of asserted')
    print('-' * 74)
    print('  It said: "add one more boundary clock and it would fail ONLY during')
    print('  holdover".  On its own figures --- 330 ns chain, 1000 ns holdover,')
    print('  1500 ns limit --- one more 50 ns clock gives 1380 ns.')
    print()
    print('%-34s %10s %10s %9s' % ('chain', 'total', 'limit', 'verdict'))
    for n in (4, 5, 6, 8, 12):
        old_total = 330 + 50 * (n - 4) + 1000
        print('%-34s %8d ns %8d ns %9s'
              % ('old model, %d boundary clocks' % n, old_total, 1500,
                 'passes' if old_total <= 1500 else 'fails'))
    print()
    print('  It takes FOUR more boundary clocks, not one, before the old model')
    print('  fails.  The sentence was printed unconditionally and the program')
    print('  never checked it.')
    print()
    print('  With the requirement and the error kinds handled properly the answer')
    print('  is different again, and more useful:')
    print()
    print('%-34s %10s %10s %9s' % ('chain', 'total', 'allowed', 'verdict'))
    limit_n = None
    for n in (2, 4, 6, 8, 10, 12, 16):
        ch = chain_error(build_chain(n), 'rss')
        a = assess(REQ, ch)
        if not a['meets'] and limit_n is None:
            limit_n = n
        print('%-34s %8.0f ns %8.0f ns %9s'
              % ('%d boundary clocks' % n, ch['total_ns'],
                 a['network_allocation_ns'], 'meets' if a['meets'] else 'FAILS'))
    print()
    print('  The chain stops meeting the requirement at %s boundary clocks ---'
          % (limit_n if limit_n else 'more than 16'))
    print('  and it is the CONSTANT error that takes it there, since that is what')
    print('  dominates these selected inputs. In another chain dynamic error')
    print('  may dominate; use its measured behaviour and applicable limits.')
    print()
    return limit_n


def section_f():
    print('F. The same arithmetic on a real datasheet: sensitivity, not prediction')
    print('  OSA 5412 temperature stability is not a measured residual offset.')
    ch = chain_error(build_chain(), 'rss')
    budget = REQ['network_allocation_ns'] - ch['total_ns']
    out = {name: holdover_seconds_until(budget, **o)
           for name, o in VENDOR_OSCILLATORS.items()}
    for name, t in out.items():
        print('  %-45s %s' % (name, hms(t)))
    c = VENDOR_EPRTC_CLAIM
    implied = c['ns'] / (c['days'] * 86400.0)
    best_free_run = min(o['frequency_offset_ppb'] for o in VENDOR_OSCILLATORS.values())
    print('  Equivalent CONSTANT offset for 100 ns over 100 days: %.3e ppb' % implied)
    print('  Arithmetic ratio between them: %.0f x' % (best_free_run / implied))
    print('  This is not an instantaneous residual bound or a product prediction.')
    print('  The ePRTC claim uses an additional caesium reference arrangement.')
    print('  A temperature-stability substitution is answering a different question.')
    print('  The typical table has stated temperature, lock and confidence conditions.')
    print('  Ask for a complete bound after a stated lock time, with initial error,')
    print('  temperature history and reference arrangement. MANUFACTURER CLAIM only.')
    return {'implied_ppb': implied, 'best_free_run_ppb': best_free_run,
            'ratio': best_free_run / implied, 'times': out}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)

    if args.json:
        ch = chain_error(build_chain(), 'rss')
        json.dump({'requirement': REQ, 'chain': ch,
                   'assessment': assess(REQ, ch),
                   'holdover': {k: {'at_1h': holdover_error_ns(3600, **o),
                                    'at_24h': holdover_error_ns(86400, **o)}
                                for k, o in OSCILLATORS.items()}},
                  sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write('\n')
        return 0

    print('Time-error budget, reference to radio (Chapter 47, the budget section)')
    print('Every figure is a stated input.  No clock, no receiver, no test set.')
    print()
    section_a()
    section_b()
    section_c()
    section_d()
    section_e()
    section_f()
    print('What this does NOT establish')
    print('-' * 74)
    print('- No equipment and no measurement. Sections A to E use invented')
    print('  inputs; section F uses one published datasheet, which is a')
    print('  MANUFACTURER CLAIM about a product and not a measurement either.')
    print('- The holdover model is three terms.  A real oscillator\'s holdover')
    print('  depends on temperature, on how long it was locked before it lost the')
    print('  reference, on ageing, and on the servo\'s own behaviour, and it is')
    print('  specified as a bound over a stated period and condition --- not as a')
    print('  formula.')
    print('- The combination rules here are a CHOICE made visible, not the')
    print('  applicable standard\'s method.  Use the standard that applies to you.')
    print('- Nothing here is a conformance assessment.  A budget that closes on')
    print('  paper is a prediction; the requirement is met when it is MEASURED at')
    print('  the stated reference point, in the deployed chain, under load.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
