#!/usr/bin/env python3
"""Tests for ruleorder.py.

Three things are being pinned. That the model REFUSES what it cannot represent
rather than guessing. That its shadow report distinguishes a contradicted rule
from a merely redundant one, because those need different responses. And that
the claim it makes about itself --- that union shadowing cannot occur in this
model --- is verified by exhaustion rather than asserted.

    python3 test_ruleorder.py
"""
import io
import itertools
import sys

import ruleorder as ro

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
    except ro.RuleError as exc:
        if fragment and fragment not in str(exc):
            FAILED.append('%s (message lacked %r: %s)' % (label, fragment, exc))
        return
    except Exception as exc:                                    # noqa: BLE001
        FAILED.append('%s (raised %s, not RuleError)' % (label, type(exc).__name__))
        return
    FAILED.append('%s (did not raise)' % label)


def R(n, s, d, p, a):
    return dict(n=n, src=s, dst=d, port=p, action=a)


# -- 1. What the model refuses -------------------------------------------
# Every one of these is a shape a reader could plausibly type, and every one
# would produce a confident wrong answer if compared as text.

for bad, frag in (
        ('10.10.0.0/16', 'CIDR'),
        ('192.168.1.0/24', 'CIDR'),
        ('1024-65535', 'range'),
        ('10.0.0.1-10.0.0.9', 'range'),
        ('hr,finance', 'list or group'),
        ('a;b', 'list or group'),
        ('', 'empty'),
        ('   ', 'empty')):
    raises(lambda b=bad: ro.validate([R(1, b, 'any', 'any', 'allow')]),
           'a src of %r is refused' % bad, frag)
    raises(lambda b=bad: ro.validate([R(1, 'any', b, 'any', 'allow')]),
           'a dst of %r is refused' % bad, frag)
    raises(lambda b=bad: ro.validate([R(1, 'any', 'any', b, 'allow')]),
           'a port of %r is refused' % bad, frag)

# Ordinary object names containing a hyphen MUST be accepted: a validator that
# refuses "dmz-web" fails closed, which is safer than failing open and is still
# a bug.
for good in ('dmz-web', 'dmz-db', 'ot-historian', 'guest-wifi', 'x-1y'):
    ok(ro.validate([R(1, good, good, 'any', 'allow')]) is True,
       'the object name %r is accepted' % good)

raises(lambda: ro.validate([R(1, 'any', 'any', 'any', 'inspect')]),
       'an unknown action is refused', 'knows only')
raises(lambda: ro.validate([R(1, 'any', 'any', 'any', 'ALLOW')]),
       'a differently-cased action is refused')
raises(lambda: ro.validate([dict(n=1, src='a', dst='b', action='allow')]),
       'a missing field is refused', 'missing')
raises(lambda: ro.validate([R(1, 'a', 'b', 'c', 'allow'), R(1, 'd', 'e', 'f', 'deny')]),
       'a duplicate rule number is refused', 'reuses')
raises(lambda: ro.validate([]), 'an empty rule base is refused')
raises(lambda: ro.validate('rules'), 'a non-list rule base is refused')
raises(lambda: ro.validate([R(1, 1, 'b', 'c', 'allow')]),
       'a non-string field is refused', 'text labels')

# A flow is one packet, not a set.
for f in ro.FIELDS:
    flow = {x: 'concrete' for x in ro.FIELDS}
    flow[f] = ro.ANY
    raises(lambda fl=flow: ro.validate_flow(fl),
           'a flow with %s=any is refused' % f, 'one concrete packet')
raises(lambda: ro.validate_flow({'src': 'a'}), 'an incomplete flow is refused')
ok(ro.validate_flow({'src': 'a', 'dst': 'b', 'port': 'c'}) is True,
   'a concrete flow is accepted')

# The demonstration the module prints must actually refuse everything it shows.
demo = ro.demo_limits()
ok(len(demo) == 5, 'the limits demonstration covers five shapes')
ok(all(d['refused'] for d in demo),
   'every shape in the limits demonstration is refused')


# -- 2. First match wins -------------------------------------------------

RB = [R(1, 'internal', 'any', 'any', 'allow'),
      R(2, 'internal', 'web', 'ssh', 'deny'),
      R(3, 'any', 'any', 'any', 'deny')]
ok(ro.first_match(RB, dict(src='internal', dst='web', port='ssh'))['n'] == 1,
   'the earlier broad allow wins over the later specific deny')
ok(ro.first_match(RB, dict(src='guest', dst='web', port='ssh'))['n'] == 3,
   'an unmatched source falls to the cleanup rule')
ok(ro.first_match([R(1, 'a', 'b', 'c', 'allow')],
                  dict(src='x', dst='y', port='z')) is None,
   'no rule matching returns None rather than inventing a default')

t = ro.trace([R(1, 'a', 'b', 'c', 'allow')], dict(src='x', dst='y', port='z'))
ok(t['rule'] is None and t['action'] is None, 'an unmatched trace reports no rule')
ok('does not guess' in t['note'] and 'property of the product' in t['note'],
   'and says the real default belongs to the product, not to this model')


# -- 3. Shadow classification -------------------------------------------

contra = [R(1, 'internal', 'any', 'any', 'allow'),
          R(2, 'internal', 'web', 'ssh', 'deny')]
s = ro.find_shadows(contra)
ok(len(s) == 1 and s[0]['rule'] == 2, 'the contradicted rule is found')
ok(s[0]['severity'] == 'CONTRADICTED',
   'a deny shadowed by an allow is CONTRADICTED')

redun = [R(1, 'internal', 'any', 'any', 'deny'),
         R(2, 'internal', 'web', 'ssh', 'deny')]
s = ro.find_shadows(redun)
ok(len(s) == 1 and s[0]['severity'] == 'REDUNDANT',
   'a deny shadowed by a deny is REDUNDANT, not a hole')
ok('dead weight' in s[0]['meaning'], 'and the report says why that differs')

live = [R(1, 'internal', 'web', 'ssh', 'allow'),
        R(2, 'guest', 'web', 'ssh', 'deny')]
ok(ro.find_shadows(live) == [],
   'a rule base with nothing dead reports nothing --- a checker that only ever '
   'finds problems has not been tested against a clean input')

# The shipped rule base must exercise BOTH severities and leave a live rule.
res = ro.analyse()
sev = {x['severity'] for x in res['shadows']}
ok(sev == {'CONTRADICTED', 'REDUNDANT'},
   'the shipped rule base shows both severities, got %s' % sorted(sev))
ok(any(x['rule'] == 2 for x in res['shadows']), 'rule 2 is reported')
ok(any(x['rule'] == 8 for x in res['shadows']), 'rule 8 is reported')
ok(not any(x['rule'] == 7 for x in res['shadows']),
   'rule 7 is REACHABLE and must not be reported: partner to internal on sql '
   'reaches it')
ok(ro.unreachable(ro.RULES, 6) is None,
   'and unreachable() agrees that rule 7 is live')

# Shadowing is about coverage, not adjacency: an unrelated rule in between must
# not hide it.
gap = [R(1, 'internal', 'any', 'any', 'allow'),
       R(2, 'guest', 'printer', 'ipp', 'allow'),
       R(3, 'internal', 'web', 'ssh', 'deny')]
ok([x['rule'] for x in ro.find_shadows(gap)] == [3],
   'a rule two positions later is still detected')


# -- 4. The claim the module makes about itself --------------------------
# union_reduces_to_single() is the module's own proof that a union-shadow
# detector here would be code that can never fire. Re-run it, small, every time.

proof = ro.union_reduces_to_single(max_rules=3, labels=('a', 'b'))
ok(proof['counterexample'] is None,
   'no counter-example to union-reduces-to-single at 3 rules')
ok(proof['checked'] > 1000,
   'and the search actually examined rule bases (%d)' % proof['checked'])

# Pin the reasoning too: covering a wildcard field needs an earlier wildcard.
ok(ro.covers(R(1, 'any', 'any', 'any', 'deny'), R(2, 'a', 'b', 'c', 'allow')),
   'any/any/any covers everything')
ok(not ro.covers(R(1, 'a', 'any', 'any', 'deny'), R(2, 'b', 'any', 'any', 'allow')),
   'a specific src does not cover a different specific src')
ok(not ro.covers(R(1, 'a', 'b', 'c', 'deny'), R(2, 'a', 'any', 'c', 'allow')),
   'a specific rule does not cover a wildcard one')
# The open label space is what makes that true: _values must add a label that
# appears in no rule.
vals = ro._values([R(1, 'a', 'x', 'p', 'allow')], 'src')
ok(len(vals) == 2 and any('not-named' in v for v in vals),
   'the label space includes a value no rule names')


# -- 5. Output ------------------------------------------------------------

buf = io.StringIO()
ro.report(ro.analyse(), buf)
out = buf.getvalue()
ok('CONTRADICTED' in out and 'REDUNDANT' in out, 'the report shows both severities')
ok('does not understand addresses' in out,
   'the report states its own limits where a reader will see them')
for probe in ('first match wins', 'Flow traces'):
    ok(probe in out, 'the report contains %r' % probe)
ok(ro.main([]) == 0, 'the module runs')
ok(ro.main(['--json']) == 0, 'the JSON form runs')
ok(ro.main(['--demo-limits']) == 0, 'the limits demonstration runs')
ok(ro.analyse() == ro.analyse(), 'the analysis is deterministic')

print('%d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: %s' % f)
sys.exit(1 if FAILED else 0)
