#!/usr/bin/env python3
"""Checks for Lab 49.3.

The chapter's closing claim was that a different medium gives "diversity that a
second fibre struggles to match". The first duty of these checks is to show the
model reaching that conclusion when the description earns it, and refusing it
when the description does not --- because the claim is true of a well-sited
backup and false of a lazy one, and the chapter made it of both.

    python3 test_shared_risk.py
"""
import contextlib
import io
import sys

import shared_risk as S

PASS = 0
FAIL = []


def check(name, cond, detail=''):
    global PASS
    if cond:
        PASS += 1
    else:
        FAIL.append('%s%s' % (name, (' --- ' + detail) if detail else ''))


def raises(name, fn, want):
    try:
        fn()
    except S.RiskError as e:
        check(name, want.lower() in str(e).lower(),
              'raised %r, wanted something about %r' % (str(e), want))
    except Exception as e:                      # noqa: BLE001
        check(name, False, 'raised %s, not RiskError' % type(e).__name__)
    else:
        check(name, False, 'did not raise')


# ===========================================================================
# 1. The claim FAILS on a lazy backup
# ===========================================================================
ff = S.pair_outage_probability(S.FIBRE_A, S.FIBRE_B)
lazy = S.pair_outage_probability(S.FIBRE_A, S.MICROWAVE_LAZY)
check('two fibre routes share six classes', ff['shared_count'] == 6,
      ff['shared_count'])
check('the roof-mounted microwave shares six too', lazy['shared_count'] == 6,
      lazy['shared_count'])
check('so on this description the medium bought no fewer shared classes',
      lazy['shared_count'] == ff['shared_count'])
check('the digger IS removed', 'duct or digger' not in lazy['shared_classes'])
check('but the building entry is not',
      'building entry' in lazy['shared_classes'])
check('nor the power board', 'site power' in lazy['shared_classes'])
check('nor the management system',
      'management system' in lazy['shared_classes'])
check('nor the team', 'change or human error' in lazy['shared_classes'])
check('so "diversity a second fibre struggles to match" is false here',
      lazy['shared_count'] >= ff['shared_count'])

# ===========================================================================
# 2. And SUCCEEDS on a well-sited one
# ===========================================================================
good = S.pair_outage_probability(S.FIBRE_A, S.MICROWAVE_GOOD)
leo = S.pair_outage_probability(S.FIBRE_A, S.LEO)
check('the well-sited microwave shares one class', good['shared_count'] == 1)
check('and it is the weather', good['shared_classes'] == ['regional weather'])
check('the LEO service also shares one', leo['shared_count'] == 1)
check('so the claim IS true when the description earns it',
      good['shared_count'] < ff['shared_count'])
check('and the model says which claim applies by counting, not by medium',
      lazy['shared_count'] > good['shared_count']
      and S.MICROWAVE_LAZY['medium'] == S.MICROWAVE_GOOD['medium'])
check('weather is shared whatever the medium',
      all('regional weather' in r['shared_classes']
          for r in (ff, lazy, good, leo)))

# ===========================================================================
# 3. Shared causes are not independent, and the difference is the point
# ===========================================================================
for name, r in (('two fibre', ff), ('lazy', lazy), ('good', good), ('leo', leo)):
    check('%s: the pair is worse than the independent assumption' % name,
          r['pair_outage_probability'] > r['naive_if_independent'])
    check('%s: the understatement factor is reported' % name,
          r['understatement_factor'] > 1.0)
check('the lazy pair is understated more than the good one',
      lazy['understatement_factor'] > good['understatement_factor'])
check('a shared cause contributes directly, not as a product',
      lazy['p_shared_kills_both'] > 0.2)
check('and the two contributions sum to the pair figure',
      abs(lazy['p_shared_kills_both'] + lazy['p_both_independently']
          - lazy['pair_outage_probability']) < 1e-12)

# a pair with NOTHING shared should be exactly the independent product
iso_a = S.path('a', 'fibre', {'duct or digger': 'd1', 'site power': 'p1'})
iso_b = S.path('b', 'radio', {'regional weather': 'w2',
                              'medium-specific fade': 'f2'})
iso = S.pair_outage_probability(iso_a, iso_b)
check('with nothing shared the pair is the independent product',
      abs(iso['pair_outage_probability'] - iso['naive_if_independent']) < 1e-12)
check('and the understatement factor is exactly one',
      abs(iso['understatement_factor'] - 1.0) < 1e-12)
check('so the model is not simply adding pessimism', iso['shared_count'] == 0)

# ===========================================================================
# 4. The improvement that is real
# ===========================================================================
for name, r in (('two fibre', ff), ('lazy', lazy), ('good', good), ('leo', leo)):
    check('%s: the pair still beats the single path' % name,
          r['pair_outage_probability'] < r['a_alone'])
    check('%s: the improvement is reported' % name, r['improvement_over_a'] > 1.0)
check('the well-sited backup improves more than the lazy one',
      good['improvement_over_a'] > lazy['improvement_over_a'])
check('but the lazy one still improves on no backup at all',
      lazy['improvement_over_a'] > 1.0)

# ===========================================================================
# 5. Descriptions are validated
# ===========================================================================
raises('an unknown failure class is refused',
       lambda: S.path('x', 'fibre', {'sunspots': 'sol-1'}),
       'unknown failure class')
raises('a path with no dependencies is refused',
       lambda: S.path('x', 'fibre', {}), 'it is an assumption')
check('sharing needs the same IDENTITY, not just the same class',
      S.shared(S.path('p', 'fibre', {'site power': 'board-A'}),
               S.path('q', 'radio', {'site power': 'board-B'})) == {})
check('and the same identity does count as shared',
      S.shared(S.path('p', 'fibre', {'site power': 'board-A'}),
               S.path('q', 'radio', {'site power': 'board-A'}))
      == {'site power': 'board-A'})

# ===========================================================================
# 6. Separating one dependency at a time
# ===========================================================================
base = S.pair_outage_probability(S.FIBRE_A, S.MICROWAVE_LAZY)
improved = []
for cls, new in (('site power', 'board-B'), ('management system', 'nms-2'),
                 ('change or human error', 'team-2')):
    d = dict(S.MICROWAVE_LAZY['depends_on'])
    d[cls] = new
    r = S.pair_outage_probability(S.FIBRE_A, S.path('t', 'radio', d))
    improved.append((cls, r['pair_outage_probability']))
    check('separating %s helps' % cls,
          r['pair_outage_probability'] < base['pair_outage_probability'])
    check('and removes exactly one shared class',
          r['shared_count'] == base['shared_count'] - 1)
check('the classes differ in how much they are worth',
      len({round(v, 6) for _, v in improved}) > 1)

# ===========================================================================
# 7. The report
# ===========================================================================
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    S.main([])
out = buf.getvalue()
check('the report runs', 'A. The claim, and what the records say' in out)
check('it quotes the chapter\'s claim', 'cannot be cut by the digger' in out)
check('it concedes the claim is true', 'True, and here is everything it leaves'
      in out)
check('it shows the lazy backup sharing as much as two fibres',
      'the two fibre routes share 6' in out)
check('it says these are outage probabilities, not unavailabilities',
      'not' in out and 'unavailabilities' in out)
check('it distinguishes annual joint events from availability',
      'not service availability' in out and 'months apart' in out)
check('it says both statements are true at once',
      'Both' in out and 'true at once' in out)
check('it names the most valuable separation', 'most valuable separation' in out)
check('it says the records may be wrong', 'records are often wrong' in out)
check('it says the only real test is failing the primary',
      'failing the primary' in out)
check('it discloses what it does not establish', 'does NOT establish' in out)
check('no line is absurdly wide',
      max(len(x) for x in out.splitlines()) <= 80,
      'widest %d' % max(len(x) for x in out.splitlines()))

if __name__ == '__main__':
    total = PASS + len(FAIL)
    for f in FAIL:
        print('FAIL: %s' % f)
    print('%d/%d checks passed' % (PASS, total))
    sys.exit(1 if FAIL else 0)
