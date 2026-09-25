#!/usr/bin/env python3
"""Tests for anycast_catchment.py.

The chapter used to assert that an anycast estate divides an attack equally and
that damage stays regional. Both are now claims about a model, so both are
tested as claims: the model must produce the skew, must cascade, and must refuse
inputs that would let it quietly discard part of the attack.

    python3 test_anycast_catchment.py
"""
import io
import sys

import anycast_catchment as ac

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
    except ac.AnycastError as exc:
        if fragment and fragment not in str(exc):
            FAILED.append('%s (message lacked %r)' % (label, fragment))
        return
    except Exception as exc:                                    # noqa: BLE001
        FAILED.append('%s (raised %s)' % (label, type(exc).__name__))
        return
    FAILED.append('%s (did not raise)' % label)


THREE = {'a': dict(capacity_bps=400e9, share=0.62),
         'b': dict(capacity_bps=400e9, share=0.27),
         'c': dict(capacity_bps=400e9, share=0.11)}


# -- 1. Shares must account for all the traffic ----------------------------

raises(lambda: ac.load({'a': dict(capacity_bps=1, share=0.5)}, 10),
       'shares that do not sum to one are refused', 'silently discarding')
raises(lambda: ac.load({'a': dict(capacity_bps=1, share=0.5),
                        'b': dict(capacity_bps=1, share=0.6)}, 10),
       'shares that sum above one are refused')
raises(lambda: ac.load({}, 10), 'an empty estate is refused')
raises(lambda: ac.load({'a': dict(capacity_bps=0, share=1.0)}, 10),
       'a zero-capacity site is refused', 'not a site')
raises(lambda: ac.load({'a': dict(share=1.0)}, 10), 'a missing capacity is refused')
raises(lambda: ac.load({'a': dict(capacity_bps=1, share=True)}, 10),
       'a bool is not a share')
raises(lambda: ac.load(THREE, -1), 'a negative attack is refused')
raises(lambda: ac.cascade(THREE, 1, redistribute='nearest'),
       'an unmodelled redistribution policy is refused', 'must be measured')

lo = ac.load(THREE, 1000e9)
ok(abs(lo['a'] - 620e9) < 1, 'the skewed catchment gives site a 62 per cent')
ok(abs(sum(lo.values()) - 1000e9) < 1, 'and the loads sum to the attack')


# -- 2. Equal thirds is a special case, not the behaviour ------------------

eq = ac.load(ac.EQUAL, 900e9)
ok(len({round(v) for v in eq.values()}) == 1, 'equal shares do give equal loads')
sk = ac.load(ac.SKEWED, 900e9)
ok(len({round(v) for v in sk.values()}) == 3,
   'and the skewed case gives three different loads --- the point of the finding')
ok(max(sk.values()) / min(sk.values()) > 5,
   'the busiest site takes more than five times the quietest')


# -- 3. The cascade, which is the critical part -----------------------------

c = ac.cascade(ac.SKEWED, 900e9)
ok(c['survived'] is False,
   'A 900 Gb/s ATTACK DESTROYS A 1200 Gb/s ESTATE once withdrawal is modelled')
ok(c['attack_bps'] < c['total_capacity_bps'],
   'and it does so while smaller than the total capacity')
ok(len(c['rounds']) >= 4, 'the collapse takes several rounds')
ok(c['rounds'][0]['overwhelmed'] == ['site-A'], 'site A goes first')
ok(c['rounds'][0]['utilisation']['site-C'] < 0.3,
   'while site C is under 30 per cent in round one --- comfortable')
ok('site-C' in c['withdrawn'],
   'AND SITE C STILL DIES, killed by the withdrawals rather than by its own load')
ok(c['withdrawn'] == ['site-A', 'site-B', 'site-C'], 'in that order')

survivable = ac.cascade(ac.SKEWED, 500e9)
ok(survivable['survived'] is True, 'a smaller attack is survived')
ok(not survivable['withdrawn'], 'with nothing withdrawn')
ok(len(survivable['rounds']) == 1, 'and it settles in one round')

# The equal case survives what the skewed case does not: the difference is
# entirely catchment policy, not capacity.
ok(ac.cascade(ac.EQUAL, 900e9)['survived'] is True,
   'the same attack against the same total capacity is survived when equal')
ok(ac.cascade(ac.SKEWED, 900e9)['survived'] is False,
   'and not when skewed --- same hardware, different BGP')


# -- 4. Thresholds --------------------------------------------------------

t_eq = ac.survival_threshold(ac.EQUAL)
t_sk = ac.survival_threshold(ac.SKEWED)
t_tg = ac.survival_threshold(ac.TARGETED)
ok(abs(t_eq - 1200e9) < 2e6, 'the equal estate survives its full 1200 Gb/s')
ok(t_sk < t_eq, 'the skewed estate survives less')
ok(abs(t_sk - 645e9) < 5e9, 'about 645 Gb/s, which is 54 per cent of capacity')
ok(t_sk / t_eq < 0.6, 'barely half of what the equal drawing promises')
ok(t_tg < t_eq, 'and a targeted catchment less still')
for sites in (ac.EQUAL, ac.SKEWED, ac.TARGETED):
    t = ac.survival_threshold(sites)
    ok(ac.cascade(sites, t * 0.999)['survived'], 'just under the threshold survives')
    ok(not ac.cascade(sites, t * 1.01)['survived'], 'just over it does not')

# The zero-share fallback must be declared, never silent.
c = ac.cascade(ac.TARGETED, 900e9)
notes = [r.get('assumption') for r in c['rounds'] if r.get('assumption')]
ok(notes, 'the equal-split fallback is recorded as an assumption')
ok('must be measured' in notes[0], 'and says it must be measured, not assumed')


# -- 5. The report --------------------------------------------------------

buf = io.StringIO()
ac.report(buf)
out = buf.getvalue()
ok('withdraws' in out, 'the report shows the withdrawals')
ok('collapsed entirely' in out, 'and states the outcome plainly')
ok('is true only until the first site leaves' in out,
   'and names the claim it refutes')
ok('one case a designer does not control' in out,
   'and says why the equal case is not a design property')
_s = sys.stdout
sys.stdout = io.StringIO()
try:
    rc, rj = ac.main([]), ac.main(['--json'])
finally:
    sys.stdout = _s
ok(rc == 0 and rj == 0, 'both modes run')

print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
