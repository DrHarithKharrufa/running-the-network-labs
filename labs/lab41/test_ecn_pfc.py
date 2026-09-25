#!/usr/bin/env python3
"""Checks for ecn_pfc.py --- the queue model, not a lossless fabric.

The previous model cut the sender's rate in the same step it marked the packet.
With no feedback delay a control loop cannot overshoot, so PFC never fired for
any ECN threshold below 99.4% of the PAUSE line, and the script reported that as
the tuning lesson. It was reporting its own arithmetic.

The first duty of these checks is therefore to prove the replacement CAN FAIL:
that some configurations fire PFC, that some drop, and that the boundary moves
when the fabric changes. A model that passes everything is worth nothing.

They also pin the headroom arithmetic, because that is a claim the chapter now
makes in print: what the queue accumulates while a PAUSE is in flight is
(offered - service) * pfc_delay, and the switch drops when the buffer above xoff
is smaller than that.

No switch, NIC, RoCE traffic or hardware is touched. This is NOT DCQCN and
validates no configuration.

    python3 test_ecn_pfc.py
"""
import contextlib
import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import ecn_pfc as ep  # noqa: E402

FAILS = []
COUNT = 0


def check(name, cond, detail=''):
    global COUNT
    COUNT += 1
    detail = str(detail) if detail not in ('', None) else ''
    suffix = ('  [' + detail + ']') if detail else ''
    if cond:
        print('ok    ' + name + suffix)
    else:
        FAILS.append(name + suffix)
        print('FAIL  ' + name + suffix)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


D = ep.DEFAULTS

# ---- THE MODEL MUST BE ABLE TO FAIL ---------------------------------------
early = ep.simulate(20)
late = ep.simulate(180)
check('an early ECN ramp keeps PFC quiet', early['pause_asserts'] == 0,
      early['pause_asserts'])
check('a late ECN ramp fires PFC', late['pause_asserts'] > 0,
      late['pause_asserts'])
check('the two differ --- the model is not answering by construction',
      early['pause_asserts'] != late['pause_asserts'])
check('a late ramp leaves a deeper queue than an early one',
      late['max_queue'] > early['max_queue'],
      (early['max_queue'], late['max_queue']))

tight = ep.simulate(180, capacity=230.0)
check('a buffer too small for the PAUSE reaction time DROPS',
      tight['dropped'] > 0 and not tight['lossless'], tight['dropped'])
check('...and the verdict says so, not "PFC quiet"',
      'DROPPED' in tight['verdict'], tight['verdict'])

# ---- the feedback delay is what makes the problem exist -------------------
instant = ep.simulate(180, delay=0)
check('removing the feedback delay alone makes the same config far better',
      instant['pause_asserts'] < late['pause_asserts'] / 4,
      (instant['pause_asserts'], late['pause_asserts']))
check('...and leaves a shallower queue',
      instant['max_queue'] < late['max_queue'],
      (instant['max_queue'], late['max_queue']))
# Instant feedback is not a free pass, and the reason matters: a RED ramp marks
# with probability ~0 just above kmin, so the first notification is late even
# when its journey is instantaneous. The old model used a hard step instead of
# a ramp AND no delay, which is why nothing could ever go wrong in it.
check('even instant feedback can overshoot, because the ramp starts at p=0',
      instant['pause_asserts'] > 0
      or ep.simulate(195, delay=0)['pause_asserts'] > 0,
      instant['pause_asserts'])

edges = {d: ep.highest_safe_kmin(delay=d) for d in (0, 8, 24, 48)}
check('the safe threshold falls as the feedback delay grows',
      all(a > b for a, b in zip(list(edges.values()), list(edges.values())[1:])),
      edges)
check('at zero delay almost the whole range below xoff is safe',
      edges[0] > 0.8 * D['xoff'], edges[0])
check('at a realistic delay much less of it is',
      edges[24] < 0.6 * D['xoff'], edges[24])
check('the safe region is an interval, not a point',
      ep.simulate(edges[24] - 5)['pause_asserts'] == 0
      and ep.simulate(min(D['xoff'] - 1, edges[24] + 20))['pause_asserts'] > 0,
      edges[24])

# ---- headroom arithmetic, as printed in the chapter -----------------------
r = ep.simulate(180)
predicted = (D['offered'] - D['service']) * D['pfc_delay']
check('the predicted net headroom is (offered - service) * pfc_delay',
      abs(r['headroom_needed_net'] - predicted) < 1e-9,
      (r['headroom_needed_net'], predicted))
check('the observed overshoot never exceeds the prediction',
      r['overshoot'] <= predicted + 1e-9, (r['overshoot'], predicted))
check('...and is within a packet or two of it',
      r['overshoot'] > predicted - 3, (r['overshoot'], predicted))

no_ecn = ep.simulate(10 ** 6)
check('with ECN off the overshoot reaches the prediction exactly',
      abs(no_ecn['overshoot'] - predicted) < 1e-9,
      (no_ecn['overshoot'], predicted))

# the drop boundary should sit where the arithmetic says it does
generous = ep.simulate(180, capacity=D['xoff'] + predicted + 5)
meagre = ep.simulate(180, capacity=D['xoff'] + predicted - 10)
check('headroom above the prediction stays lossless', generous['lossless'],
      generous['dropped'])
check('headroom below it does not', not meagre['lossless'], meagre['dropped'])

# ---- PFC counting is assertions, not steps --------------------------------
check('pause_asserts counts transitions, not steps above xoff',
      late['pause_asserts'] < late['paused_steps'],
      (late['pause_asserts'], late['paused_steps']))
check('hysteresis means a single assertion covers many steps',
      late['paused_steps'] / max(late['pause_asserts'], 1) > 2,
      late['paused_steps'] / max(late['pause_asserts'], 1))

# ---- monotonicity: later marking is never better --------------------------
sweep = [ep.simulate(k)['pause_asserts'] for k in (20, 60, 100, 140, 180)]
check('firing never decreases as the ramp is pushed later',
      all(a <= b for a, b in zip(sweep, sweep[1:])), sweep)

# ---- determinism -----------------------------------------------------------
check('the model is deterministic',
      ep.simulate(120) == ep.simulate(120))

# ---- the RED ramp is a ramp, not a step -----------------------------------
wide = ep.simulate(60, kspan=120.0)
narrow = ep.simulate(60, kspan=1.0)
check('the ramp width changes the outcome --- kmax is a real parameter',
      wide['max_queue'] != narrow['max_queue'],
      (wide['max_queue'], narrow['max_queue']))

# ---- rejection -------------------------------------------------------------
cases = [
    (dict(kmin=-1), 'negative'),
    (dict(kmin=60, kmax=10), 'kmax'),
    (dict(kmin=60, xon=250.0), 'xon'),
    (dict(kmin=60, xoff=300.0), 'capacity'),
    (dict(kmin=60, service=0), 'positive'),
    (dict(kmin=60, offered=-1), 'positive'),
    (dict(kmin=60, delay=-1), 'delays'),
    (dict(kmin=60, cut=0), 'decrease factor'),
    (dict(kmin=60, cut=1.5), 'decrease factor'),
]
for kw, word in cases:
    k = kw.pop('kmin')
    try:
        ep.simulate(k, **kw)
        check('rejects %r' % (kw or {'kmin': k},), False, 'no exception')
    except ep.ModelError as e:
        check('rejects %r' % (kw or {'kmin': k},), word in str(e), str(e)[:60])

# ---- highest_safe_kmin is honest when nothing works -----------------------
hopeless = ep.highest_safe_kmin(delay=400, xoff=40.0, xon=20.0, capacity=400.0)
check('when no threshold keeps PFC quiet it returns None rather than a number',
      hopeless is None, hopeless)

# ---- the report says what it is and is not --------------------------------
_r, out = quiet(ep.report, ep.analyse())
low = ' '.join(out.lower().split())
check('the report disclaims DCQCN', 'not dcqcn' in low)
check('the report disclaims being a device', 'not a device' in low)
check('the report names the constants as arbitrary', 'arbitrary' in low)
check('the report shows at least one configuration firing PFC',
      'pfc fired' in low)
check('the report shows at least one configuration dropping',
      'no' in [c.strip() for c in low.split('|')] or 'lossless' in low)
check('the report says the safe threshold belongs to the fabric',
      'property of the fabric' in low)
check('the report shows the headroom arithmetic',
      'x 16 = 48 packets' in low or '48 packets' in low)
rc, _o = quiet(ep.main, [])
check('the script exits 0', rc == 0, rc)
rc2, _o = quiet(ep.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
