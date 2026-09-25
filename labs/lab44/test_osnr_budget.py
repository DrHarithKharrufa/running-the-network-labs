#!/usr/bin/env python3
"""Checks for osnr_budget.py --- the chain, and the optimum that exists.

The chapter said OSNR governs reach and pointed at a lab that computed none, and
said a link fails "no matter how much power you pump" as though extra power were
merely useless. The central checks are that the effective SNR has a MAXIMUM ---
so past it more power is actively harmful --- and that ASE-only reasoning
overstates the reach.

No transponder, amplifier, fibre or spectrum analyser.

    python3 test_osnr_budget.py
"""
import contextlib, io, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import osnr_budget as ob  # noqa: E402

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


SPAN = (22.0, 5.5)

# ---- the per-span formula --------------------------------------------------
o = ob.span_osnr_db(0.0, 22.0, 5.5)
check('one span is launch - loss - NF - the noise reference',
      abs(o - (0.0 - 22.0 - 5.5 + 58.0)) < 1e-9, o)
check('more launch power gives more OSNR, one for one',
      abs(ob.span_osnr_db(3.0, 22.0, 5.5) - o - 3.0) < 1e-9)
check('more span loss costs OSNR, one for one',
      abs(ob.span_osnr_db(0.0, 25.0, 5.5) - o + 3.0) < 1e-9)
check('a noisier amplifier costs OSNR, one for one',
      abs(ob.span_osnr_db(0.0, 22.0, 8.5) - o + 3.0) < 1e-9)

# ---- the chain accumulates as reciprocals ---------------------------------
one = ob.chain_osnr_db(0.0, [SPAN])
four = ob.chain_osnr_db(0.0, [SPAN] * 4)
check('one span in a chain equals the span formula',
      abs(one['total_db'] - o) < 1e-9)
check('four identical spans cost exactly 10log10(4) = 6.02 dB',
      abs((one['total_db'] - four['total_db']) - 10 * math.log10(4)) < 1e-9,
      one['total_db'] - four['total_db'])
check('...which is NOT a quarter of the OSNR', four['total_db'] > one['total_db'] / 4)
check('ten spans cost 10 dB',
      abs((one['total_db'] - ob.chain_osnr_db(0.0, [SPAN] * 10)['total_db'])
          - 10.0) < 1e-9)
check('an unequal chain is dominated by its worst span',
      ob.chain_osnr_db(0.0, [SPAN, (30.0, 5.5)])['total_db']
      < ob.chain_osnr_db(0.0, [SPAN, SPAN])['total_db'])
check('per-span figures are reported, not just the total',
      len(four['per_span_db']) == 4)

# ---- THE POINT: there is an optimum, and past it power hurts --------------
chain = [SPAN] * 8
best = ob.optimum_launch(chain)
low = ob.effective_snr_db(best['launch_dbm'] - 6.0, chain)
high = ob.effective_snr_db(best['launch_dbm'] + 6.0, chain)
check('the effective SNR has a maximum',
      best['effective_snr_db'] > low['effective_snr_db']
      and best['effective_snr_db'] > high['effective_snr_db'],
      (low['effective_snr_db'], best['effective_snr_db'], high['effective_snr_db']))
check('past the optimum, MORE power gives LESS effective SNR',
      high['effective_snr_db'] < best['effective_snr_db'],
      (best['launch_dbm'], high['effective_snr_db']))
check('...while the ASE figure keeps improving, which is the trap',
      high['osnr_ase_db'] > best['osnr_ase_db'])
check('the penalty at the optimum is the classical 1.76 dB',
      abs(best['nonlinear_penalty_db'] - 1.76) < 0.02,
      best['nonlinear_penalty_db'])
check('that figure is independent of the chain length',
      abs(ob.optimum_launch([SPAN] * 3)['nonlinear_penalty_db']
          - ob.optimum_launch([SPAN] * 20)['nonlinear_penalty_db']) < 0.02)
check('a lower nonlinear coefficient moves the optimum up',
      ob.optimum_launch(chain, nl_coefficient_db=-30.0)['launch_dbm']
      > best['launch_dbm'])
check('the effective SNR is never above the ASE figure',
      all(ob.effective_snr_db(p, chain)['effective_snr_db']
          <= ob.effective_snr_db(p, chain)['osnr_ase_db'] + 1e-9
          for p in (-10, -5, 0, 5, 10)))

# ---- required OSNR is more than a datasheet headline ----------------------
req = ob.required_osnr_db(14.0)
check('the requirement adds the penalties to the back-to-back figure',
      abs(req['required_db'] - (14.0 + 1.0 + 1.0 + 2.0)) < 1e-9,
      req['required_db'])
check('a bare back-to-back figure understates it',
      req['required_db'] > req['back_to_back_db'])
check('every penalty is itemised',
      {'implementation_penalty_db', 'ageing_penalty_db', 'design_margin_db'}
      <= set(req))

# ---- reach, and what ASE-only reasoning would have promised --------------
n = ob.max_spans(SPAN, req)
check('the system reaches a finite number of spans', 0 < n < 60, n)
check('one more span than that does not work',
      not ob.assess([SPAN] * (n + 1), req)['could_ever_work'])
check('...and that many does', ob.assess([SPAN] * n, req)['could_ever_work'])
ase_only = max(k for k in range(1, 201)
               if ob.chain_osnr_db(best['launch_dbm'],
                                   [SPAN] * k)['total_db'] >= req['required_db'])
check('ASE-only reasoning overstates the reach at the same launch power',
      ase_only > n, (ase_only, n))
check('a quieter amplifier reaches further',
      ob.max_spans((22.0, 4.0), req) > n)
check('a lossier span reaches less far', ob.max_spans((26.0, 5.5), req) < n)
check('a lower required OSNR reaches further',
      ob.max_spans(SPAN, ob.required_osnr_db(10.0)) > n)

a = ob.assess([SPAN] * 4, req)
check('assess reports the margin against the requirement',
      abs(a['margin_db'] - (a['snr_at_launch_db'] - req['required_db'])) < 1e-9)
check('a working chain says so', a['works'] and a['could_ever_work'])
check('assess at a stated launch power uses that power, not the optimum',
      ob.assess([SPAN] * 4, req, launch_dbm=6.0)['at_launch_dbm'] == 6.0)
check('...and a badly chosen launch power can fail a chain that would work',
      not ob.assess([SPAN] * 4, req, launch_dbm=12.0)['works']
      and ob.assess([SPAN] * 4, req)['works'])

# ---- rejection -------------------------------------------------------------
for fn, args, word in (
        (ob.span_osnr_db, (0.0, -1.0, 5.5), 'not negative'),
        (ob.span_osnr_db, (0.0, 22.0, -1.0), 'not negative'),
        (ob.chain_osnr_db, (0.0, []), 'at least one span'),
        (ob.required_osnr_db, (-1.0,), 'not negative'),
        (ob.lin_to_db, (0.0,), 'cannot express')):
    try:
        fn(*args)
        check('rejects %s%r' % (fn.__name__, args), False, 'no exception')
    except ob.OpticalError as e:
        check('rejects %s%r' % (fn.__name__, args), word in str(e), str(e)[:60])

# ---- the report says what it is and is not --------------------------------
_r, out = quiet(ob.report, ob.analyse())
lowt = ' '.join(out.lower().split())
check('the report disclaims being a planning tool', 'not a planning tool' in lowt)
check('the report disclaims being a Gaussian-noise model',
      'not a gaussian-noise model' in lowt)
check('the report states that past the optimum more power makes it WORSE',
      'more power makes the link worse' in lowt)
check('the report lists what it leaves out',
      'spectral hole burning' in lowt and 'polarisation-dependent loss' in lowt)
check('the report contrasts ASE-only reasoning with the answer',
      'count ase alone' in lowt)
rc, _o = quiet(ob.main, [])
check('the script exits 0', rc == 0, rc)
rc2, _o = quiet(ob.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
