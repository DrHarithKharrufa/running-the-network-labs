#!/usr/bin/env python3
"""Lab 44.2 --- the OSNR budget, and why more power stops helping.

WHY THIS EXISTS
---------------
Chapter 44 said OSNR governs reach on a coherent link and then pointed at a lab
that computed no OSNR at all.  It computed a POWER budget --- transmit power
minus losses against receiver sensitivity --- and declared the link good.  On a
coherent link those are different questions and the power one is not the
governing one.

It also said the link fails "no matter how much power you pump", with the
implication that extra power is merely useless.  It is worse than useless.  Past
an optimum, extra launch power makes the link worse, because the fibre's
nonlinearity turns power into a noise of its own that grows faster than the
signal does.  There is a best launch power and a reach beyond which no power
setting works, and both fall out of arithmetic.

WHAT IS MODELLED
----------------
  * Per-span OSNR from launch power, span loss and amplifier noise figure, in
    the usual reference bandwidth, with the constant stated rather than hidden.
  * Accumulation down a chain: noise powers add, so the reciprocals of OSNR add.
  * A nonlinear penalty in the shape the Gaussian-noise models give --- nonlinear
    noise rising as the cube of launch power, so the effective SNR has a maximum.
  * A required OSNR made of the transceiver's back-to-back requirement plus an
    implementation penalty plus the margin you choose to hold.

WHAT IS NOT MODELLED
--------------------
This is a teaching model with ONE nonlinear coefficient, not a Gaussian-noise
model, not a simulation, and not a planning tool.  It has no Raman tilt, no
spectral hole burning, no polarisation-dependent loss, no filtering penalty from
cascaded ROADMs, no residual dispersion, no transient behaviour and no channel
interaction beyond that single coefficient.  Every figure below is an input.
No transponder, amplifier, fibre or spectrum analyser was involved; nothing here
was measured, and no number it prints belongs in a design without a real
planning tool behind it.

    python3 osnr_budget.py
    python3 osnr_budget.py --json
    python3 test_osnr_budget.py
"""
import argparse
import json
import math
import sys

# 10*log10(h * nu * B_ref) for 1550 nm in a 0.1 nm reference bandwidth, in dBm.
# Quoted as a constant so it can be checked rather than believed: with
# h = 6.626e-34 J.s, nu = 193.4 THz and B_ref = 12.5 GHz, h*nu*B_ref is about
# 1.6e-9 W, which is -58 dBm.
NOISE_REF_DBM = -58.0


class OpticalError(ValueError):
    """The system described cannot be costed in OSNR."""


def db_to_lin(db):
    return 10.0 ** (db / 10.0)


def lin_to_db(x):
    if x <= 0:
        raise OpticalError('cannot express %r as dB' % (x,))
    return 10.0 * math.log10(x)


# --------------------------------------------------------------------------
# ASE: one span, then the chain
# --------------------------------------------------------------------------
def span_osnr_db(launch_dbm, span_loss_db, amp_nf_db, noise_ref_dbm=NOISE_REF_DBM):
    """OSNR contributed by one amplified span, in the reference bandwidth.

        OSNR = P_launch - L_span - NF - 10log10(h.nu.B_ref)

    The amplifier is assumed to recover exactly the span's loss, which is the
    usual design and is why the span loss appears once rather than twice.
    """
    if span_loss_db < 0:
        raise OpticalError('a span loss is not negative, got %r' % (span_loss_db,))
    if amp_nf_db < 0:
        raise OpticalError('a noise figure is not negative, got %r' % (amp_nf_db,))
    return launch_dbm - span_loss_db - amp_nf_db - noise_ref_dbm


def chain_osnr_db(launch_dbm, spans, noise_ref_dbm=NOISE_REF_DBM):
    """Accumulate OSNR over a chain. spans: [(loss_db, nf_db), ...]

    Noise powers add, so it is the RECIPROCALS of the linear OSNRs that add.
    Identical spans therefore cost 10log10(N) --- four spans reduce linear OSNR to one quarter, a loss of about 6 dB.
    """
    if not spans:
        raise OpticalError('a chain has at least one span')
    inv = 0.0
    per = []
    for loss, nf in spans:
        o = span_osnr_db(launch_dbm, loss, nf, noise_ref_dbm)
        per.append(o)
        inv += 1.0 / db_to_lin(o)
    return {'per_span_db': per, 'total_db': lin_to_db(1.0 / inv),
            'spans': len(spans)}


# --------------------------------------------------------------------------
# the nonlinear penalty, and therefore an optimum
# --------------------------------------------------------------------------
def effective_snr_db(launch_dbm, spans, nl_coefficient_db=-24.0,
                     noise_ref_dbm=NOISE_REF_DBM):
    """Effective SNR with both noises present.

    ASE noise falls as launch power rises; nonlinear noise rises as its CUBE, so

        1/SNR = 1/OSNR_ase + 1/SNR_nl,   SNR_nl(dB) = -2*P - eta - 10log10(N)

    where eta is a single lumped coefficient standing in for everything the
    Gaussian-noise models compute properly. The shape is right and the value is
    not a measurement: change eta and every absolute number here changes with
    it. What does NOT change is that the curve has a maximum, which is the
    point.
    """
    ase = chain_osnr_db(launch_dbm, spans, noise_ref_dbm)
    n = len(spans)
    snr_nl_db = -2.0 * launch_dbm - nl_coefficient_db - 10.0 * math.log10(n)
    total = 1.0 / (1.0 / db_to_lin(ase['total_db']) + 1.0 / db_to_lin(snr_nl_db))
    return {'launch_dbm': launch_dbm, 'osnr_ase_db': ase['total_db'],
            'snr_nl_db': snr_nl_db, 'effective_snr_db': lin_to_db(total),
            'nonlinear_penalty_db': ase['total_db'] - lin_to_db(total)}


def optimum_launch(spans, nl_coefficient_db=-24.0, lo=-15.0, hi=15.0,
                   step=0.01, noise_ref_dbm=NOISE_REF_DBM):
    """The launch power that maximises effective SNR, by search.

    The classical result is that the optimum sits where the nonlinear noise is
    half the ASE noise, so the penalty at the optimum is about 1.76 dB whatever
    the numbers --- a useful thing to check an answer against.
    """
    best = None
    p = lo
    while p <= hi + 1e-9:
        r = effective_snr_db(p, spans, nl_coefficient_db, noise_ref_dbm)
        if best is None or r['effective_snr_db'] > best['effective_snr_db']:
            best = r
        p += step
    return best


# --------------------------------------------------------------------------
# what the receiver needs
# --------------------------------------------------------------------------
def required_osnr_db(back_to_back_db, implementation_penalty_db=1.0,
                     ageing_penalty_db=1.0, design_margin_db=2.0):
    """What the link must deliver, which is more than a datasheet's headline.

    The back-to-back figure is measured with a short patch lead in a laboratory.
    A measured back-to-back threshold already includes receiver implementation
    loss. The legacy implementation_penalty_db argument must therefore mean
    only an additional penalty not already included; set it to zero otherwise.
    Add path/ageing allowances and reserve once, under stated conditions.
    """
    for v in (back_to_back_db, implementation_penalty_db, ageing_penalty_db,
              design_margin_db):
        if v < 0:
            raise OpticalError('penalties and margins are not negative')
    return {'back_to_back_db': back_to_back_db,
            'implementation_penalty_db': implementation_penalty_db,
            'ageing_penalty_db': ageing_penalty_db,
            'design_margin_db': design_margin_db,
            'required_db': (back_to_back_db + implementation_penalty_db
                            + ageing_penalty_db + design_margin_db)}


def assess(spans, required, launch_dbm=None, nl_coefficient_db=-24.0):
    """Does this chain deliver what the receiver needs, at the best launch power?"""
    best = optimum_launch(spans, nl_coefficient_db)
    at = (effective_snr_db(launch_dbm, spans, nl_coefficient_db)
          if launch_dbm is not None else best)
    return {'spans': len(spans),
            'total_loss_db': sum(l for l, _ in spans),
            'optimum_launch_dbm': best['launch_dbm'],
            'best_snr_db': best['effective_snr_db'],
            'at_launch_dbm': at['launch_dbm'],
            'snr_at_launch_db': at['effective_snr_db'],
            'osnr_ase_at_launch_db': at['osnr_ase_db'],
            'nonlinear_penalty_db': at['nonlinear_penalty_db'],
            'required_db': required['required_db'],
            'margin_db': at['effective_snr_db'] - required['required_db'],
            'works': at['effective_snr_db'] >= required['required_db'],
            'could_ever_work': best['effective_snr_db'] >= required['required_db']}


def max_spans(span, required, nl_coefficient_db=-24.0, limit=60):
    """How many identical spans this system can cross, at the best launch power."""
    n = 0
    for k in range(1, limit + 1):
        a = assess([span] * k, required, nl_coefficient_db=nl_coefficient_db)
        if not a['could_ever_work']:
            return n
        n = k
    return n


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------
SPAN = (22.0, 5.5)          # 22 dB of loss, a 5.5 dB noise figure
REQ = required_osnr_db(14.0)    # a 16QAM-class back-to-back figure, illustrative


def analyse():
    chain = [SPAN] * 8
    sweep = [effective_snr_db(p, chain) for p in
             (-6, -3, 0, 1, 2, 3, 4, 6, 9, 12)]
    counts = [(n, assess([SPAN] * n, REQ)) for n in (1, 4, 8, 12, 16, 20, 24)]
    return {'span': SPAN, 'required': REQ, 'sweep': sweep, 'counts': counts,
            'optimum': optimum_launch(chain),
            'max_spans': max_spans(SPAN, REQ),
            # the fair comparison: ASE-only reasoning at the SAME launch power
            'ase_only_at_optimum': max(
                [n for n in range(1, 201)
                 if chain_osnr_db(optimum_launch([SPAN] * 8)['launch_dbm'],
                                  [SPAN] * n)['total_db'] >= REQ['required_db']]
                or [0])}


def report(a):
    s, req = a['span'], a['required']
    print('OSNR chain arithmetic. A TEACHING MODEL with one lumped nonlinear')
    print('coefficient --- not a Gaussian-noise model, not a planning tool, and')
    print('not a measurement. No transponder, amplifier or fibre was involved.\n')
    print('  each span: %.1f dB loss, %.1f dB amplifier noise figure' % s)
    print('  required OSNR: %.1f back-to-back + %.1f implementation + %.1f ageing'
          % (req['back_to_back_db'], req['implementation_penalty_db'],
             req['ageing_penalty_db']))
    print('                 + %.1f design margin = %.1f dB\n'
          % (req['design_margin_db'], req['required_db']))

    print('A. More power is not more reach: eight spans, launch power swept')
    print('%10s | %10s | %10s | %12s | %s'
          % ('launch', 'OSNR(ASE)', 'SNR(NL)', 'effective', 'penalty'))
    print('-' * 68)
    for r in a['sweep']:
        print('%7.1f dBm | %8.2f   | %8.2f   | %10.2f   | %6.2f dB'
              % (r['launch_dbm'], r['osnr_ase_db'], r['snr_nl_db'],
                 r['effective_snr_db'], r['nonlinear_penalty_db']))
    o = a['optimum']
    print('\nThe ASE column improves for ever as power rises. The effective')
    print('column does not: it peaks at %.2f dBm and falls away, because the'
          % o['launch_dbm'])
    print('fibre turns power into a noise of its own that grows as the cube.')
    print('At the peak the penalty is %.2f dB, which is the classical figure'
          % o['nonlinear_penalty_db'])
    print('and a useful check on any answer of this kind.')
    print('\nSo "no matter how much power you pump" understates it. Past the')
    print('optimum, more power makes the link WORSE, and a system running hot')
    print('gets better when you turn it down.')

    print('\nB. Reach, at the best launch power for each length')
    print('%7s | %10s | %11s | %10s | %8s | %s'
          % ('spans', 'total loss', 'best launch', 'best SNR', 'margin', 'verdict'))
    print('-' * 76)
    for n, c in a['counts']:
        print('%7d | %7.0f dB | %8.1f dBm | %8.2f  | %7.2f | %s'
              % (n, c['total_loss_db'], c['optimum_launch_dbm'],
                 c['best_snr_db'], c['margin_db'],
                 'works' if c['could_ever_work'] else 'cannot be made to work'))
    print('\nThis system crosses %d spans. Count ASE alone at the same launch'
          % a['max_spans'])
    print('power and the answer is %d --- and ASE-only reasoning would not stop'
          % a['ase_only_at_optimum'])
    print('there, because in that arithmetic raising the power always helps, so')
    print('it recommends the one adjustment that makes the real link worse.')
    print('\nNote what is NOT in this answer: no filtering penalty from cascaded')
    print('ROADMs, no polarisation-dependent loss, no residual dispersion, no')
    print('Raman tilt, no spectral hole burning. Every one of those spends OSNR')
    print('too, which is why a real design uses the vendor\'s planning tool and')
    print('this arithmetic is for understanding the shape, not for committing.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        a = analyse()
    except OpticalError as e:
        print('optical error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(a, indent=2))
    else:
        report(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
