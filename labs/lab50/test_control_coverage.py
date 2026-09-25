#!/usr/bin/env python3
"""Checks for control_coverage.py.

The load-bearing claim is that coverage counted per THREAT and coverage counted
per MECHANISM give different answers, and that the difference is where an
inventory reports green on an open plane. That is checked directly, along with
the property that makes the model honest: removing a mechanism from the
inventory must improve the report without improving anything else.
"""
import json
import subprocess
import sys

import control_coverage as C

CHECKS = 0
FAILED = []


def check(label, cond):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except C.CoverageError:
        return True
    except Exception:
        return False
    return False


CTLS = C.estate_controls()

# ===========================================================================
# an effect is one of three, and conflating them is refused
# ===========================================================================
check('three effects are defined', len(C.EFFECTS) == 3)
check('the three effects are distinct', len(set(C.EFFECTS)) == 3)
check('"stops" is not an effect a control may claim',
      raises(C.Control, 'firewall', 'stops', ('exposed-mgmt-interface',)))
check('"prevents" is not an effect a control may claim',
      raises(C.Control, 'firewall', 'prevents', ('exposed-mgmt-interface',)))
check('"mitigates" is not an effect a control may claim',
      raises(C.Control, 'firewall', 'mitigates', ('exposed-mgmt-interface',)))
for e in C.EFFECTS:
    check('a control may claim %r' % e,
          isinstance(C.Control('x', e, ('exposed-mgmt-interface',)), C.Control))
check('a control addressing nothing is refused',
      raises(C.Control, 'x', 'limit reach', ()))
check('a control addressing nothing (None) is refused',
      raises(C.Control, 'x', 'limit reach', None))

# ===========================================================================
# a mechanism is validated
# ===========================================================================
check('an unknown plane is refused',
      raises(C.Mechanism, 'x', 'wireless', ('state',), 'd'))
check('an unknown class is refused',
      raises(C.Mechanism, 'x', 'data', ('hacktivist',), 'd'))
check('a mechanism naming no class is refused',
      raises(C.Mechanism, 'x', 'data', (), 'd'))
check('every shipped mechanism names at least one class',
      all(m.classes for m in C.ALL_MECHANISMS))
check('every shipped mechanism has a description',
      all(len(m.description) > 20 for m in C.ALL_MECHANISMS))
check('mechanism identifiers are unique',
      len({m.ident for m in C.ALL_MECHANISMS}) == len(C.ALL_MECHANISMS))
check('every plane has at least one mechanism',
      all(any(m.plane == p for m in C.ALL_MECHANISMS) for p in C.PLANES))
check('every class has at least one mechanism',
      all(any(c in m.classes for m in C.ALL_MECHANISMS) for c in C.CLASSES))
check('every control addresses a mechanism that exists',
      all(a in {m.ident for m in C.ALL_MECHANISMS}
          for ctl in CTLS for a in ctl.addresses))

# ===========================================================================
# THE HEADLINE: per-threat and per-mechanism coverage disagree
# ===========================================================================
sc = C.coverage(C.SUPPLY_CHAIN, CTLS)
covered = [r for r in sc if r['covered']]
check('the supply chain is more than one mechanism', len(C.SUPPLY_CHAIN) >= 6)
check('image signing covers some supply-chain mechanisms', len(covered) >= 2)
check('and leaves most of them uncovered', len(covered) < len(sc) / 2 + 1)
check('counting the plane as covered because something applies is wrong',
      len(covered) != len(sc))
for ident in ('vendor-compromised-signs-malice', 'signing-key-stolen',
              'hardware-implant-at-odm', 'dependency-in-vendor-build'):
    row = next(r for r in sc if r['mechanism'] == ident)
    check('%s is NOT covered by signing' % ident, not row['covered'])
    check('%s is described' % ident, len(row['description']) > 20)
for ident in ('image-tampered-in-transit', 'image-unsigned-on-disk'):
    row = next(r for r in sc if r['mechanism'] == ident)
    check('%s IS covered by signing' % ident, row['covered'])
sig = next(c for c in CTLS if 'signature' in c.name)
check('the signing control says what it is a statement about',
      'not about the vendor' in sig.note)
check('signing is a frequency control, not a reach or dwell one',
      sig.effect == 'reduce frequency')
check('the two mechanisms signing covers are the two where the signature '
      'would NOT verify',
      set(sig.addresses) == {'image-tampered-in-transit', 'image-unsigned-on-disk'})

# ===========================================================================
# the shape of a control set
# ===========================================================================
be = C.by_effect(CTLS)
check('by_effect covers all three effects', set(be) == set(C.EFFECTS))
check('every control is counted exactly once',
      sum(len(v) for v in be.values()) == len(CTLS))
check('this set is weighted towards reducing frequency',
      len(be['reduce frequency']) > len(be['limit reach']))
check('and thinnest on shortening dwell',
      len(be['shorten dwell']) == min(len(v) for v in be.values()))
check('a set with only frequency controls is detectable',
      len(C.by_effect([c for c in CTLS if c.effect == 'reduce frequency'])
          ['limit reach']) == 0)

# ===========================================================================
# per class
# ===========================================================================
bc = C.by_class(C.ALL_MECHANISMS, CTLS)
check('by_class covers all four classes', set(bc) == set(C.CLASSES))
check('every class has mechanisms counted',
      all(v['mechanisms'] > 0 for v in bc.values()))
check('covered never exceeds mechanisms',
      all(v['covered'] <= v['mechanisms'] for v in bc.values()))
check('the uncovered list length matches the arithmetic',
      all(len(v['uncovered']) == v['mechanisms'] - v['covered'] for v in bc.values()))
check('fractions are between zero and one',
      all(0.0 <= v['fraction'] <= 1.0 for v in bc.values()))
check('the opportunist is the best covered class',
      bc['opportunist']['fraction'] == max(v['fraction'] for v in bc.values()))
check('the state actor is the worst covered class',
      bc['state']['fraction'] == min(v['fraction'] for v in bc.values()))
check('the state class is not fully covered', bc['state']['fraction'] < 1.0)
check('an empty control set covers nothing',
      all(v['covered'] == 0 for v in C.by_class(C.ALL_MECHANISMS, []).values()))
check('an empty control set leaves every mechanism uncovered',
      all(len(v['uncovered']) == v['mechanisms']
          for v in C.by_class(C.ALL_MECHANISMS, []).values()))

# ===========================================================================
# per plane
# ===========================================================================
bp = C.plane_coverage(C.ALL_MECHANISMS, CTLS)
check('plane coverage covers all four planes', set(bp) == set(C.PLANES))
check('plane mechanism counts sum to the inventory',
      sum(v['mechanisms'] for v in bp.values()) == len(C.ALL_MECHANISMS))
check('the supply-chain plane is the worst covered',
      bp['supply chain']['fraction'] == min(v['fraction'] for v in bp.values()))
check('the supply-chain plane is partly covered, not green and not red',
      0.0 < bp['supply chain']['fraction'] < 1.0)

# ===========================================================================
# the timebox: dropping a mechanism improves the report and nothing else
# ===========================================================================
tb = C.unnamed_mechanism_effect(C.ALL_MECHANISMS, CTLS, 'hardware-implant-at-odm')
check('dropping a mechanism is reported', tb['dropped'] == 'hardware-implant-at-odm')
check('the class that faced it now shows fewer mechanisms',
      tb['without_it']['state']['mechanisms'] < tb['with_it']['state']['mechanisms'])
check('and fewer open items, which is the false improvement',
      tb['without_it']['state']['uncovered'] < tb['with_it']['state']['uncovered'])
check('classes that did not face it are unchanged',
      all(tb['with_it'][c] == tb['without_it'][c]
          for c in ('opportunist', 'criminal', 'insider')))
check('dropping a covered mechanism also shrinks the count',
      C.unnamed_mechanism_effect(C.ALL_MECHANISMS, CTLS,
                                 'exposed-mgmt-interface')
      ['without_it']['opportunist']['mechanisms'] < bc['opportunist']['mechanisms'])
check('dropping a mechanism that is not there is refused',
      raises(C.unnamed_mechanism_effect, C.ALL_MECHANISMS, CTLS, 'no-such-thing'))

# ===========================================================================
# coverage is not risk
# ===========================================================================
check('a fully covered class can still have uncovered mechanisms elsewhere',
      bc['opportunist']['fraction'] == 1.0 and bc['state']['fraction'] < 1.0)
check('a caveat says covered means named, not deployed or tested',
      any('COVERED HERE MEANS A CONTROL IS NAMED' in c
          for c in C.build_report()['caveats']))
check('a caveat says coverage is not risk',
      any('Coverage is not risk' in c for c in C.build_report()['caveats']))
check('a caveat admits the mechanism list is incomplete',
      any('deliberately\nincomplete' in c or 'deliberately incomplete' in c
          for c in C.build_report()['caveats']))

# ===========================================================================
# report and CLI
# ===========================================================================
rep = C.build_report()
check('report carries the effects', rep['effects'] == list(C.EFFECTS))
check('report carries every control', len(rep['controls']) == len(CTLS))
check('report carries the supply-chain breakdown',
      len(rep['supply_chain']) == len(C.SUPPLY_CHAIN))
check('report carries the timebox demonstration', 'timebox' in rep)
check('report carries caveats', len(rep['caveats']) >= 5)
check('report JSON-serialises', isinstance(json.dumps(rep), str))
text = C.report_text(rep)
check('the text names the four sections',
      all(s in text for s in ('A.', 'B.', 'C.', 'D.')))
check('the text says the signature verifies in the uncovered cases',
      'the signature verifies' in text)
check('the text distinguishes the two questions signing answers',
      'should I' in text and 'the image the vendor signed' in text)
check('the text says the risk did not change', 'The risk did not change' in text)
check('the text discloses what it does not establish', 'does NOT establish' in text)
check('the text gives the shape of the control set', 'Shape of this set' in text)

out = subprocess.run([sys.executable, 'control_coverage.py', '--json'],
                     capture_output=True, text=True)
check('--json exits zero', out.returncode == 0)
check('--json parses', isinstance(json.loads(out.stdout), dict))
plain = subprocess.run([sys.executable, 'control_coverage.py'],
                       capture_output=True, text=True)
check('plain run exits zero', plain.returncode == 0)
check('plain run is not JSON', not plain.stdout.lstrip().startswith('{'))

print('control_coverage: %d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: ' + f)
sys.exit(1 if FAILED else 0)
