#!/usr/bin/env python3
"""Checks for otdr_events.py --- the arithmetic behind a trace, not a trace.

The chapter used to say a single trace identifies an event by its visual
signature and locates a fault "to within metres". The central checks here are
that a one-direction measurement can be NEGATIVE across a genuinely lossy
splice, and that optical distance is not route distance --- because those are
the two claims that send crews to the wrong place.

No OTDR, no fibre, no measurement.

    python3 test_otdr_events.py
"""
import contextlib, io, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import otdr_events as oe  # noqa: E402

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


# ---- 1. bidirectional averaging, and the gainer ---------------------------
g = oe.true_event_loss(-0.09, 0.49)
check('a one-way measurement can be NEGATIVE across a lossy splice',
      g['is_gainer'] and g['true_loss_db'] > 0,
      (g['a_to_b_db'], g['true_loss_db']))
check('the true loss is the mean of the two directions',
      abs(g['true_loss_db'] - 0.20) < 1e-12, g['true_loss_db'])
check('the backscatter term is half the difference',
      abs(g['backscatter_term_db'] - (-0.29)) < 1e-12)
check('the one-way error is reported, not hidden',
      abs(g['one_way_error_db'] - 0.29) < 1e-12)
check('a symmetric event needs no correction',
      oe.true_event_loss(0.05, 0.05)['backscatter_term_db'] == 0)
check('...and is not a gainer', not oe.true_event_loss(0.05, 0.05)['is_gainer'])
check('averaging is order-independent',
      oe.true_event_loss(0.28, 0.12)['true_loss_db']
      == oe.true_event_loss(0.12, 0.28)['true_loss_db'])
check('the sign of the backscatter term reverses with direction',
      oe.true_event_loss(0.28, 0.12)['backscatter_term_db']
      == -oe.true_event_loss(0.12, 0.28)['backscatter_term_db'])
# the arithmetic identity the whole method rests on
for a, b in ((0.0, 0.0), (1.0, -0.4), (-0.3, 0.9), (2.5, 2.5)):
    r = oe.true_event_loss(a, b)
    check('loss + d reconstructs the A->B reading at (%g, %g)' % (a, b),
          abs(r['true_loss_db'] + r['backscatter_term_db'] - a) < 1e-12)

# ---- 2. dead zones ---------------------------------------------------------
dz100 = oe.dead_zone_m(100)
check('a 100 ns pulse has a dead zone of about ten metres',
      9.5 < dz100 < 11.0, dz100)
check('a longer pulse resolves less', oe.dead_zone_m(1000) > dz100)
check('a shorter pulse resolves more', oe.dead_zone_m(10) < dz100)
check('the dead zone scales linearly with pulse width',
      abs(oe.dead_zone_m(200) - 2 * dz100) < 1e-9)
check('a higher index shortens it',
      oe.dead_zone_m(100, index=1.6) < oe.dead_zone_m(100, index=1.4))
check('events closer than the dead zone merge',
      not oe.resolvable(5.0, 100)['resolvable'])
check('...and further apart do not',
      oe.resolvable(25.0, 100)['resolvable'])
check('the same separation resolves at a shorter pulse',
      oe.resolvable(5.0, 10)['resolvable'])
check('the overlap note does not claim separately measured losses',
      'not established' in oe.resolvable(5.0, 100)['note'])

# ---- 3. optical distance is not route distance ----------------------------
d = oe.dig_position(43.210, closures_passed=3)
check('the route position is SHORTER than the optical distance',
      d['route_km'] < d['optical_km'])
check('the error is hundreds of metres, not "within metres"',
      d['error_if_ignored_m'] > 100, d['error_if_ignored_m'])
check('more closures push the route position back further',
      oe.dig_position(43.210, closures_passed=8)['route_km'] < d['route_km'])
check('slack is counted per closure',
      abs(oe.dig_position(10, closures_passed=4, slack_per_closure_m=25.0)['slack_m']
          - 100.0) < 1e-9)
check('a launch lead is removed as well',
      oe.dig_position(10, launch_lead_m=150)['route_km']
      < oe.dig_position(10, launch_lead_m=0)['route_km'])
check('with no slack, no lead and no helix the two agree',
      abs(oe.dig_position(10, closures_passed=0, helix_percent=0.0)['route_km']
          - 10.0) < 1e-12)
check('the helix allowance alone still shifts it',
      oe.dig_position(10, closures_passed=0, helix_percent=0.7)['route_km'] < 10.0)
check('a larger helix allowance shifts it further',
      oe.dig_position(10, helix_percent=1.5)['route_km']
      < oe.dig_position(10, helix_percent=0.5)['route_km'])

# ---- 4. the index you typed in --------------------------------------------
i = oe.index_error(43.2, 1.4682, 1.4750)
check('a sub-one-per-cent index error is hundreds of metres at 43 km',
      abs(i['error_m']) > 100, i['error_m'])
check('...and is under half a per cent', abs(i['error_percent']) < 0.5,
      i['error_percent'])
check('the right index gives no error',
      oe.index_error(43.2, 1.4682, 1.4682)['error_m'] == 0)
check('a lower actual index reads short',
      oe.index_error(43.2, 1.4682, 1.4600)['error_m'] < 0)
check('the error scales with distance',
      abs(oe.index_error(86.4, 1.4682, 1.4750)['error_m']
          - 2 * i['error_m']) < 1e-6)

# ---- 5. two wavelengths, not one -------------------------------------------
splice = oe.classify_by_wavelength(0.30, 0.31)
bend = oe.classify_by_wavelength(0.09, 0.32)
check('a splice and a bend can read ALIKE at 1550 nm',
      abs(splice['loss_1550_db'] - bend['loss_1550_db']) < 0.05,
      (splice['loss_1550_db'], bend['loss_1550_db']))
check('...and are told apart by the second wavelength',
      'splice' in splice['kind'] and 'macrobend' in bend['kind'])
check('...which one trace cannot supply',
      'and nothing more' in splice['single_trace_would_say'])
check('reflectance identifies a connector',
      'connector' in oe.classify_by_wavelength(0.31, 0.34,
                                               reflective=True)['kind'])
check('a loss worse at the SHORTER wavelength is called out as odd',
      'not a bend' in oe.classify_by_wavelength(0.40, 0.12)['kind'])
check('the delta is reported', abs(bend['delta_db'] - 0.23) < 1e-9)

# ---- rejection -------------------------------------------------------------
for fn, args, word in (
        (oe.true_event_loss, ('0.1', 0.2), 'number in dB'),
        (oe.dead_zone_m, (0,), 'positive'),
        (oe.dead_zone_m, (-5,), 'positive'),
        (oe.dead_zone_m, (100, 0.9), 'greater than 1'),
        (oe.dig_position, (-1,), 'not negative'),
        (oe.index_error, (10, 1.0, 1.46), 'greater than 1'),
        (oe.index_error, (10, 1.46, 0.5), 'greater than 1')):
    try:
        fn(*args)
        check('rejects %s%r' % (fn.__name__, args), False, 'no exception')
    except oe.TraceError as e:
        check('rejects %s%r' % (fn.__name__, args), word in str(e), str(e)[:60])
try:
    oe.dig_position(10, closures_passed=-1)
    check('rejects a negative closure count', False, 'no exception')
except oe.TraceError as e:
    check('rejects a negative closure count', 'not negative' in str(e))

# ---- the report states its limits ------------------------------------------
_r, out = quiet(oe.report, oe.analyse())
low = ' '.join(out.lower().split())
check('the report disclaims having an OTDR',
      'no otdr, no fibre, no measurement' in low)
check('the report says a splice cannot amplify', 'cannot amplify' in low)
check('the report rejects "within metres"', 'within metres' in low)
check('the report says the pulse width is a choice you made',
      'a choice you made' in low)
check('the report names the second wavelength as the discriminator',
      'the second' in low and 'wavelength' in low)
rc, _o = quiet(oe.main, [])
check('the script exits 0', rc == 0, rc)
rc2, _o = quiet(oe.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
