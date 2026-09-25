#!/usr/bin/env python3
"""Checks for reach_capacity.py --- reach inferred, not decorated.

The previous version labelled typed-in OSNR figures with distances and told a
reader in trouble to "add amplification". The central checks are that the OSNR
now FOLLOWS from the described path, that a ROADM node counts as an amplified
section, and that more gain at the same points buys exactly nothing.

No transponder, amplifier, ROADM or planning tool.

    python3 test_reach_capacity.py
"""
import contextlib, io, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import reach_capacity as rc  # noqa: E402

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


# ---- a mode is four numbers, and line rate is not client rate -------------
m = rc.mode('x', 118, 4, 20.0, 20.0)
check('line rate is baud x bits x two polarisations',
      abs(m['line_gbps'] - 118 * 4 * 2) < 1e-9, m['line_gbps'])
check('client rate is the line rate less the FEC overhead',
      abs(m['client_gbps'] - 944 / 1.2) < 1e-6, m['client_gbps'])
check('the two differ by a useful amount',
      m['line_gbps'] - m['client_gbps'] > 100)
check('zero overhead makes them equal',
      rc.mode('y', 118, 4, 0.0, 20.0)['client_gbps'] == 944)
check('every shipped mode carries its own baud, bits, overhead and requirement',
      all({'baud_gbd', 'bits_per_symbol_per_pol', 'fec_overhead_percent',
           'required_osnr_db'} <= set(x) for x in rc.MODES))
check('two modes share a modulation name and differ in requirement',
      len({x['required_osnr_db'] for x in rc.MODES if x['name'].startswith('QPSK')}) > 1)

# ---- THE OSNR FOLLOWS FROM THE PATH ---------------------------------------
short = rc.path_osnr_db(launch_dbm=-3.0, fibre_spans=2, span_km=20)
long_ = rc.path_osnr_db(launch_dbm=-3.0, fibre_spans=25, span_km=80)
check('a longer path has less OSNR', long_['osnr_db'] < short['osnr_db'],
      (short['osnr_db'], long_['osnr_db']))
check('distance is an input that does something',
      rc.path_osnr_db(launch_dbm=-3.0, fibre_spans=2, span_km=40)['osnr_db']
      < short['osnr_db'])
check('N identical sections cost 10log10(N)',
      abs((rc.path_osnr_db(launch_dbm=0.0, fibre_spans=1, span_km=80)['osnr_db']
           - rc.path_osnr_db(launch_dbm=0.0, fibre_spans=4, span_km=80)['osnr_db'])
          - 10 * math.log10(4)) < 1e-9)
check('more launch power raises OSNR one for one',
      abs(rc.path_osnr_db(launch_dbm=0.0, fibre_spans=4, span_km=80)['osnr_db']
          - rc.path_osnr_db(launch_dbm=-3.0, fibre_spans=4, span_km=80)['osnr_db']
          - 3.0) < 1e-9)
check('a quieter amplifier raises it one for one',
      abs(rc.path_osnr_db(launch_dbm=0.0, fibre_spans=4, span_km=80, amp_nf_db=4.5)['osnr_db']
          - rc.path_osnr_db(launch_dbm=0.0, fibre_spans=4, span_km=80, amp_nf_db=5.5)['osnr_db']
          - 1.0) < 1e-9)

# ---- A ROADM NODE IS AN AMPLIFIED SECTION ---------------------------------
none_ = rc.path_osnr_db(launch_dbm=-3.0, fibre_spans=2, span_km=20, roadm_passes=0)
some = rc.path_osnr_db(launch_dbm=-3.0, fibre_spans=2, span_km=20, roadm_passes=8)
check('ROADM passes cost OSNR', some['osnr_db'] < none_['osnr_db'],
      (none_['osnr_db'], some['osnr_db']))
check('...a lot of it', none_['osnr_db'] - some['osnr_db'] > 5)
check('each pass is counted as a section, not only as a penalty',
      some['sections'] == 2 + 8, some['sections'])
check('the filtering penalty is separate from the noise',
      abs(some['filter_penalty_db'] - 8 * 0.4) < 1e-9)
check('and is reported separately',
      abs(some['ase_osnr_db'] - some['filter_penalty_db'] - some['osnr_db']) < 1e-9)
check('a section breakdown is returned', len(some['section_detail']) == 10)

# the headline result: a short path with many nodes beats nothing
metro8 = rc.path_osnr_db(launch_dbm=-3.0, fibre_spans=8, span_km=5, roadm_passes=8)
regional = rc.path_osnr_db(launch_dbm=-3.0, fibre_spans=6, span_km=80, roadm_passes=2)
check('a 480 km path can have MORE OSNR than a 40 km one',
      regional['osnr_db'] > metro8['osnr_db'],
      (regional['total_km'], regional['osnr_db'],
       metro8['total_km'], metro8['osnr_db']))
check('...so distance alone does not decide the modulation',
      rc.feasible(regional['osnr_db'])['best']['client_gbps']
      > rc.feasible(metro8['osnr_db'])['best']['client_gbps'])

# ---- THE ADVICE THAT WAS WRONG --------------------------------------------
o = rc.what_would_help(dict(launch_dbm=-3.0, fibre_spans=25, span_km=80,
                            roadm_passes=4))
by = {x['change']: x for x in o['options']}
check('more gain at the same points changes the OSNR by exactly zero',
      abs(by['more gain at the same points']['delta_db']) < 1e-12,
      by['more gain at the same points']['delta_db'])
check('halving every span DOES help',
      by['one additional hut per original span, halving every span']['delta_db'] > 3,
      by['one additional hut per original span, halving every span']['delta_db'])
check('...and the note says why the two differ',
      'half the loss' in by['one additional hut per original span, halving every span']['note'])
check('a quieter amplifier helps', by['a quieter amplifier, 4.5 dB noise figure']['delta_db'] > 0)
check('one fewer ROADM pass helps', by['one fewer ROADM pass']['delta_db'] > 0)
check('raising launch power helps against ASE alone',
      abs(by['launch power up 3 dB']['delta_db'] - 3.0) < 1e-9)
check('...and its note warns about the nonlinear optimum',
      'nonlinear optimum' in by['launch power up 3 dB']['note'])
check('every option reports which modes it would make feasible',
      all('feasible' in x for x in o['options']))

# ---- feasibility --------------------------------------------------------
f = rc.feasible(25.0)
check('a high OSNR makes every mode feasible', len(f['feasible']) == len(rc.MODES))
check('...and the best is the highest client rate, not the highest order',
      f['best']['client_gbps'] == max(x['client_gbps'] for x in rc.MODES))
check('a low OSNR makes none feasible', rc.feasible(5.0)['best'] is None)
check('the margin is subtracted before the comparison',
      rc.feasible(20.0, margin_db=0.0)['feasible']
      != rc.feasible(20.0, margin_db=5.0)['feasible'])
check('a higher-baud lower-order mode can beat a lower-baud higher-order one',
      rc.mode('a', 118, 3, 20.0, 17.5)['client_gbps']
      > rc.mode('b', 60, 4, 20.0, 17.0)['client_gbps'])

# ---- rejection -------------------------------------------------------------
for fn, kw, word in (
        (rc.path_osnr_db, dict(launch_dbm=0, fibre_spans=0, span_km=80), 'at least one'),
        (rc.path_osnr_db, dict(launch_dbm=0, fibre_spans=1, span_km=0), 'positive'),
        (rc.path_osnr_db, dict(launch_dbm=0, fibre_spans=1, span_km=80, roadm_passes=-1), 'not negative'),
        (rc.path_osnr_db, dict(launch_dbm=0, fibre_spans=1, span_km=80, amp_nf_db=-1), 'sensible')):
    try:
        fn(**kw)
        check('rejects %r' % (kw,), False, 'no exception')
    except rc.ModeError as e:
        check('rejects %r' % (kw,), word in str(e), str(e)[:50])
for args, word in ((('m', 0, 4, 20.0, 20.0), 'baud must be positive'),
                   (('m', 118, 0, 20.0, 20.0), 'bits per symbol'),
                   (('m', 118, 4, -1.0, 20.0), 'not negative')):
    try:
        rc.mode(*args)
        check('rejects mode%r' % (args,), False, 'no exception')
    except rc.ModeError as e:
        check('rejects mode%r' % (args,), word in str(e), str(e)[:50])
try:
    rc.feasible(20.0, margin_db=-1)
    check('rejects a negative margin', False, 'no exception')
except rc.ModeError as e:
    check('rejects a negative margin', 'not negative' in str(e))

# ---- the report makes the corrections --------------------------------------
_r, out = quiet(rc.report, rc.analyse())
low = ' '.join(out.lower().split())
check('the report distinguishes line rate from client rate',
      'line rate' in low and 'client rate is what you can sell' in low)
check('the report says the ROADM count can decide more than the kilometres',
      'decides more than the kilometres do' in low)
check('the report shows a longer path with more OSNR',
      'distance is not the' in low)
check('the report separates the two meanings of "add amplification"',
      'they are opposite' in low)
check('the report disclaims equipment',
      'no transponder, amplifier, roadm or planning tool' in low)
check("the report says no mode is a vendor's", "is any vendor's" in low)
rc_, _o = quiet(rc.main, [])
check('the script exits 0', rc_ == 0, rc_)
rc2, _o = quiet(rc.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)


# ---------------------------------------------------------------------------
# The published mode table, and the two findings in it
# ---------------------------------------------------------------------------
v = rc.vendor_mode_table()
check('the published table has seven rows', len(v['rows']) == 7, len(v['rows']))
check('every row carries rate, modulation, baud, FEC and required OSNR',
      all({'rate_gbps', 'modulation', 'baud_gbd', 'fec', 'rx_osnr_db'} <= set(r)
          for r in v['rows']))
check('two FEC types appear', {r['fec'] for r in v['rows']} == {'cFEC', 'oFEC'})

cfec = [r for r in v['rows'] if r['fec'] == 'cFEC' and r['rate_gbps'] == 400][0]
ofec = [r for r in v['rows'] if r['fec'] == 'oFEC' and r['rate_gbps'] == 400][0]
check('the FEC alone moves required OSNR by 2 dB', v['fec_delta_db'] == 2.0,
      v['fec_delta_db'])
check('at the same rate', cfec['rate_gbps'] == ofec['rate_gbps'])
check('the same modulation', cfec['modulation'] == ofec['modulation'])
check('and a baud rate within one per cent',
      abs(cfec['baud_gbd'] - ofec['baud_gbd']) / cfec['baud_gbd'] < 0.01)
check('so a mode named only by its modulation is not named',
      cfec['rx_osnr_db'] != ofec['rx_osnr_db'])

check('every oFEC mode quotes the same figure', v['ofec_spread_db'] == 0.0)
check('across four different rates', v['ofec_rates'] == [100, 200, 300, 400],
      v['ofec_rates'])
check('including both QPSK and 16QAM',
      {r['modulation'] for r in v['rows'] if r['fec'] == 'oFEC'}
      >= {'QPSK', '16QAM'})
check('the illustrative set does vary, as physics would',
      len({m['required_osnr_db'] for m in rc.MODES}) > 1)
check('so the published figure reads as a floor, not a per-mode requirement',
      v['ofec_spread_db'] == 0.0 and len(v['ofec_rates']) > 1)
check('CD tolerance varies by more than forty times across the modes',
      v['cd_max'] / v['cd_min'] > 40, '%.0f' % (v['cd_max'] / v['cd_min']))
check('the cFEC mode has the least CD tolerance',
      min(v['rows'], key=lambda r: r['cd_ps_nm'])['fec'] == 'cFEC')

_r, vout = quiet(rc.report_vendor_modes)
vlow = vout.lower()
check('the report prints the published table', 'open-zrp-ofec1' in vlow)
check('it states the FEC finding', 'the only difference is the fec' in vlow)
check('it states the floor reading', 'specification floor' in vlow)
check('it warns against designing on the difference',
      'do not design on the difference' in vlow)
check('it calls the figures manufacturer claims',
      'manufacturer claim about one' in vlow)
check('it does not present them as properties of ZR or ZR+',
      'not a general property of zr or zr+' in vlow)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
