#!/usr/bin/env python3
"""Tests for ddos_triage.py.

THE PROPERTY THAT MATTERS MOST: the model never converts sparse input into a
confident class. The shipped version took four numbers and named an attack type
and a mitigation; most of what follows exists to make that impossible again.

    python3 test_ddos_triage.py
"""
import io
import sys

import ddos_triage as dt

CHECKS = 0
FAILED = []


def ok(cond, label):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


def raises(fn, label, fragment=None):
    global CHECKS
    CHECKS += 1
    try:
        fn()
    except dt.TriageError as exc:
        if fragment and fragment not in str(exc):
            FAILED.append('%s (message lacked %r: %s)' % (label, fragment, exc))
        return
    except Exception as exc:                                    # noqa: BLE001
        FAILED.append('%s (raised %s)' % (label, type(exc).__name__))
        return
    FAILED.append('%s (did not raise)' % label)


def fired(res, i):
    return any(h['id'] == i for h in res['hypotheses'])


# -- 1. 80 per cent of a pipe is not bigger than the pipe -------------------

r80 = dt.analyse({'ingress_bps': 80e9, 'link_capacity_bps': 100e9})
ok(fired(r80, 'bandwidth-congested'), 'a link at 80% is reported as congested')
ok(not fired(r80, 'bandwidth-exceeded'),
   'AND NOT AS EXCEEDED --- the shipped lab called 80% "bigger than your pipe"')
r100 = dt.analyse({'ingress_bps': 100e9, 'link_capacity_bps': 100e9})
ok(fired(r100, 'bandwidth-exceeded'), 'offered load equal to the link is exceeded')
ok(not fired(r100, 'bandwidth-congested'), 'and is not merely congested')
r120 = dt.analyse({'ingress_bps': 120e9, 'link_capacity_bps': 100e9})
ok(fired(r120, 'bandwidth-exceeded'), 'and more than the link certainly is')
ok('1.20x' in [h['measured'] for h in r120['hypotheses']
               if h['id'] == 'bandwidth-exceeded'][0],
   'the ratio is reported, not just the verdict')
r70 = dt.analyse({'ingress_bps': 70e9, 'link_capacity_bps': 100e9})
ok(not r70['hypotheses'], 'a link at 70% raises nothing at all')
ok(any('offered' in h['caveat'].lower() for h in r120['hypotheses'] if h.get('caveat')),
   'the exceeded hypothesis carries the offered-versus-delivered caveat')


# -- 2. A rate without a baseline is refused --------------------------------

raises(lambda: dt.analyse({'ingress_pps': 40e6}),
       'packets per second without a platform rating is refused', 'baseline')
raises(lambda: dt.analyse({'ingress_bps': 80e9}),
       'bits per second without a link capacity is refused', 'baseline')
raises(lambda: dt.analyse({'concurrent_flows': 1e6}),
       'a flow count without a table size is refused')
raises(lambda: dt.analyse({'app_latency_ms': 900}),
       'a latency without its baseline is refused')
ok(dt.analyse({'ingress_pps': 40e6, 'platform_pps_capacity': 30e6}),
   'with the baseline it is accepted')
raises(lambda: dt.analyse({'ingress_bps': 1, 'link_capacity_bps': 0}),
       'a zero capacity is refused', 'denominator')
raises(lambda: dt.analyse({'ingress_bps': -1, 'link_capacity_bps': 100}),
       'a negative rate is refused', 'unit or sign')
raises(lambda: dt.analyse({'ingress_bps': True, 'link_capacity_bps': 100}),
       'a bool is not a rate')
raises(lambda: dt.analyse({'nonsense': 1}), 'an unrecognised measure is refused',
       'unrecognised')
raises(lambda: dt.analyse([]), 'a non-dict is refused')
raises(lambda: dt.analyse({'drops_at_ingress': 'yes'}),
       'a non-boolean flag is refused')


# -- 3. Several resources at once, which the old model could not express ----

both = dt.analyse({'ingress_bps': 200e9, 'link_capacity_bps': 100e9,
                   'ingress_pps': 40e6, 'platform_pps_capacity': 30e6})
ok(fired(both, 'bandwidth-exceeded') and fired(both, 'packet-rate-pressure'),
   'bandwidth and packet rate can be reported together')
ok(both['simultaneous'], 'and the report says more than one resource is loaded')
ok(len(both['resources_under_pressure']) == 2, 'both resources are named')
one = dt.analyse({'ingress_bps': 10e9, 'link_capacity_bps': 100e9})
ok(not one['simultaneous'], 'a single pressure is not flagged as simultaneous')


# -- 4. Nothing is named an attack --------------------------------------------

for name, obs in dt.CASES.items():
    res = dt.analyse(obs)
    blob = str(res).lower()
    for banned in ('volumetric', 'protocol attack', 'l7', 'will not help',
                   'rtbh if', 'scrubbing --'):
        ok(banned not in blob, 'case %r never emits %r' % (name[:24], banned))
    ok('verdict_withheld' in res, 'every result carries the withheld-verdict note')
app = dt.analyse({'server_cpu_pct': 100, 'ingress_bps': 1e9,
                  'link_capacity_bps': 100e9})
ok(fired(app, 'application-work'), 'a pegged serving tier is reported')
says = [h for h in app['hypotheses'] if h['id'] == 'application-work'][0]
ok('bad deploy' in says['says'] or 'benign' in says['caveat'],
   'and the benign explanations are named beside it')
ok('exclude the benign causes' in says['caveat'],
   'the caveat tells the reader to exclude them before calling it an attack')


# -- 5. Missing evidence is reported, not assumed away ----------------------

empty = dt.analyse({})
ok(not empty['hypotheses'], 'nothing is concluded from nothing')
ok(len(empty['evidence_needed']) == 4, 'all four topics are reported as needed')
ok(all('not evidence that it is fine' in n['says'] for n in empty['evidence_needed']),
   'and silence is explicitly not reassurance')
part = dt.analyse({'ingress_bps': 10e9, 'link_capacity_bps': 100e9})
ok(any(n['resource'] == 'application' for n in part['evidence_needed']),
   'a partially observed estate still reports what is missing')


# -- 6. The amplification ratio is arithmetic, not traffic -------------------

ok(dt.amplification_ratio(60, 3000) == 50.0, 'a 60-byte query, 3000-byte reply is 50x')
raises(lambda: dt.amplification_ratio(0, 3000),
       'a zero-length query is refused', 'divided by it')
raises(lambda: dt.amplification_ratio(60, 0), 'a zero-length reply is refused')
raises(lambda: dt.amplification_ratio(-1, 10), 'a negative length is refused')
raises(lambda: dt.amplification_ratio(True, 10), 'a bool is not a length')
a = dt.amplified_bps(50, 1e9)
ok(a['ceiling_bps'] == 50e9, 'the ceiling is the ratio times the attacker rate')
ok(a['is_a_measurement'] is False, 'AND IT IS LABELLED AS NOT A MEASUREMENT')
ok('size of the prize' in a['why'], 'the caveat explains what it is not')
raises(lambda: dt.amplified_bps(0, 1e9), 'a zero ratio is refused')


# -- 7. Every hypothesis can fire ------------------------------------------

p = dt.prove_every_hypothesis_reachable()
ok(not p['unreachable'], 'no hypothesis is dead code: %s' % p['unreachable'])
ok(len(p['reached']) == 6, 'all six hypotheses were reached (%d)' % len(p['reached']))
ok(p['enumerated'] >= 48, 'the grid is not trivially small')
for i, w in p['witnesses'].items():
    ok(fired(dt.analyse(w), i), 'the recorded witness for %s really fires it' % i)

buf = io.StringIO()
dt.report(buf)
out = buf.getvalue()
ok('does not name an' in out and 'attacker' in out,
   'the report says what it withholds')
ok('80 per cent of a pipe is smaller' in out or 'NOT bigger than the pipe' in out,
   'the report makes the 80-per-cent point visible')
_s = sys.stdout
sys.stdout = io.StringIO()
try:
    rc, rj, rp = dt.main([]), dt.main(['--json']), dt.main(['--prove'])
finally:
    sys.stdout = _s
ok(rc == 0 and rj == 0 and rp == 0, 'all three modes run')
ok(dt.analyse(dt.CASES['the link is full and the offered load is far larger'])
   == dt.analyse(dt.CASES['the link is full and the offered load is far larger']),
   'the analysis is deterministic')

print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
