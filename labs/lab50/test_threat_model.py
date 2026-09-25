#!/usr/bin/env python3
"""Checks for threat_model.py.

The first block is the regression that this lab was rebuilt for. The shipped
version credited a control to an entry point whose control field was the string
"none (flat)", and then excluded that entry point from the gap list. Those
checks come first and are written so that reintroducing either half of the
defect fails a test by name.
"""
import json
import subprocess
import sys

import threat_model as T

CHECKS = 0
FAILED = []


def check(label, cond):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except T.ModelError:
        return True
    except Exception:
        return False
    return False


# ===========================================================================
# THE REGRESSION. An absence must never read as a presence.
# ===========================================================================
check('a control named "none (flat)" is refused at construction',
      raises(T.Control, 'none (flat)', {'opportunist': 0.5}))
for bad in ('none', 'No segmentation', 'N/A', 'nil', 'nothing yet',
            'absent', 'not implemented', 'unprotected', 'flat VLAN',
            'TBD', 'todo: firewall', 'unknown', 'assume nobody knows'):
    check('a control named %r is refused' % bad,
          raises(T.Control, bad, {'opportunist': 0.5}))
check('"we assume nobody knows" is refused, as the chapter says it must be',
      raises(T.Control, 'assume nobody knows', {'opportunist': 0.9}))
check('a legitimate control name starting with a normal word is allowed',
      isinstance(T.Control('Nobody-but-admins ACL', {'opportunist': 0.5}), T.Control))

check('ABSENT is not None, which is exactly the trap', T.ABSENT is not None)
check('ABSENT is falsy, so `if control:` is safe', not T.ABSENT)
check('ABSENT credits nothing to any class',
      all(T.ABSENT.credit(c) == 0.0 for c in T.CLASSES))
check('ABSENT covers nothing', T.ABSENT.covers == ())

e = T.EntryPoint('flat camera VLAN', 'opportunist', 'data', 2, 2)
check('an entry point with no controls defaults to ABSENT', e.controls == [T.ABSENT])
check('and its residual equals its inherent risk', close(e.residual, 4.0))
check('and it is a gap', e.is_gap)
check('an empty controls list also becomes ABSENT',
      T.EntryPoint('x', 'opportunist', 'data', 2, 2, []).controls == [T.ABSENT])
check('an explicit [ABSENT] is a gap',
      T.EntryPoint('x', 'opportunist', 'data', 2, 2, [T.ABSENT]).is_gap)

check('a bare string as a control is refused, which is the old bug shape',
      raises(T.EntryPoint, 'x', 'opportunist', 'data', 2, 2, ['none (flat)']))
check('a bare string that names a real control is refused too',
      raises(T.EntryPoint, 'x', 'opportunist', 'data', 2, 2, ['MFA']))
check('None in the controls list is refused',
      raises(T.EntryPoint, 'x', 'opportunist', 'data', 2, 2, [None]))
check('a number in the controls list is refused',
      raises(T.EntryPoint, 'x', 'opportunist', 'data', 2, 2, [1]))

rep = T.build_report()
cam = next(x for x in rep['entries'] if 'camera' in x['name'])
check('the camera segment scores its full inherent risk', close(cam['residual'], 4.0))
check('the camera segment is NOT half-credited', not close(cam['residual'], 2.0))
check('the camera segment is marked a gap', cam['is_gap'])
check('the camera segment appears in the gap list',
      any('camera' in g['name'] for g in rep['gaps']))
check('the gap list has four entries, not two', len(rep['gaps']) == 4)

# ===========================================================================
# a control does not earn credit against a class it does not address
# ===========================================================================
bgp = T.Control('BGP session authentication', {'criminal': 0.6})
ins = T.EntryPoint('console port', 'insider', 'management', 1, 3, [bgp])
check('a control aimed at another class earns nothing', close(ins.residual, 3.0))
check('and the entry point is still a gap', ins.is_gap)
check('and the control is reported as inert', ins.inert_controls == [bgp])
check('and it is not counted as effective', ins.effective_controls == [])
crim = T.EntryPoint('peering session', 'criminal', 'control', 1, 3, [bgp])
check('the same control does work against the class it names',
      close(crim.residual, 3.0 * 0.4))
check('and that entry point is not a gap', not crim.is_gap)
check('ABSENT is never reported as inert',
      T.EntryPoint('y', 'insider', 'data', 1, 1).inert_controls == [])

# ===========================================================================
# the model can come out badly, which is the point
# ===========================================================================
allgap = [T.EntryPoint('a', 'opportunist', 'management', 3, 3),
          T.EntryPoint('b', 'criminal', 'control', 3, 3),
          T.EntryPoint('c', 'insider', 'data', 3, 3),
          T.EntryPoint('d', 'state', 'supply chain', 3, 3)]
check('a register with no controls at all is entirely gaps',
      len(T.gaps(allgap)) == 4)
check('and every residual equals its inherent risk',
      all(close(e.residual, e.inherent) for e in allgap))
check('and the total is the worst the scale allows',
      close(sum(e.residual for e in allgap), 36.0))
weak = T.Control('a control that barely helps', {'opportunist': 0.01})
check('a weak control leaves almost all the risk',
      close(T.EntryPoint('a', 'opportunist', 'management', 3, 3, [weak]).residual,
            9.0 * 0.99))
check('a weak control still removes the gap status, which is a real limit '
      'of a binary gap test',
      not T.EntryPoint('a', 'opportunist', 'management', 3, 3, [weak]).is_gap)

# ===========================================================================
# coverage claims are bounded
# ===========================================================================
check('a claim of 1.0 is refused: no control removes a risk',
      raises(T.Control, 'perfect firewall', {'opportunist': 1.0}))
check('a claim above 1.0 is refused',
      raises(T.Control, 'magic', {'opportunist': 1.4}))
check('a claim of 0.0 is refused as a claim',
      raises(T.Control, 'useless', {'opportunist': 0.0}))
check('a negative claim is refused',
      raises(T.Control, 'harmful', {'opportunist': -0.2}))
check('an empty claim set is refused',
      raises(T.Control, 'a control that does nothing', {}))
check('a claim against an unknown class is refused',
      raises(T.Control, 'x', {'hacktivist': 0.5}))
check('an unnamed control is refused', raises(T.Control, '', {'opportunist': 0.5}))
check('a whitespace-only name is refused',
      raises(T.Control, '   ', {'opportunist': 0.5}))
check('0.999 is allowed, so the bound is on 1 and not on being strong',
      isinstance(T.Control('very good', {'opportunist': 0.999}), T.Control))

# ===========================================================================
# scales are defined, and values off them are refused
# ===========================================================================
check('three likelihood bands are defined', len(T.LIKELIHOOD_SCALE) == 3)
check('three impact bands are defined', len(T.IMPACT_SCALE) == 3)
check('every likelihood band has a description',
      all(len(v) > 20 for v in T.LIKELIHOOD_SCALE.values()))
check('every impact band has a description',
      all(len(v) > 20 for v in T.IMPACT_SCALE.values()))
check('likelihood 0 is refused', raises(T.EntryPoint, 'x', 'opportunist', 'data', 0, 2))
check('likelihood 4 is refused', raises(T.EntryPoint, 'x', 'opportunist', 'data', 4, 2))
check('impact 0 is refused', raises(T.EntryPoint, 'x', 'opportunist', 'data', 2, 0))
check('impact 5 is refused', raises(T.EntryPoint, 'x', 'opportunist', 'data', 2, 5))
check('a fractional likelihood is refused',
      raises(T.EntryPoint, 'x', 'opportunist', 'data', 2.5, 2))
check('an unknown attacker class is refused',
      raises(T.EntryPoint, 'x', 'hacktivist', 'data', 2, 2))
check('an unknown plane is refused',
      raises(T.EntryPoint, 'x', 'opportunist', 'wireless', 2, 2))
check('all four planes are accepted',
      all(T.EntryPoint('x', 'opportunist', p, 1, 1).plane == p for p in T.PLANES))
check('all four classes are accepted',
      all(T.EntryPoint('x', c, 'data', 1, 1).attacker_class == c for c in T.CLASSES))

# ===========================================================================
# composition
# ===========================================================================
half = T.Control('control one', {'opportunist': 0.5})
half2 = T.Control('control two', {'opportunist': 0.5})
two = T.EntryPoint('x', 'opportunist', 'data', 3, 3, [half, half2])
check('two controls claiming half each leave a quarter, not nothing',
      close(two.residual, 9.0 * 0.25))
check('and never reach zero', two.residual > 0)
strong = T.Control('nine tenths', {'opportunist': 0.9})
many = T.EntryPoint('x', 'opportunist', 'data', 3, 3, [strong] * 5)
check('five strong controls still leave something', many.residual > 0)
check('more coverage always leaves less residual',
      T.EntryPoint('x', 'opportunist', 'data', 3, 3, [strong]).residual
      < T.EntryPoint('x', 'opportunist', 'data', 3, 3, [half]).residual)
check('adding an inert control changes nothing',
      close(T.EntryPoint('x', 'opportunist', 'data', 3, 3, [half, bgp]).residual,
            T.EntryPoint('x', 'opportunist', 'data', 3, 3, [half]).residual))
check('residual never exceeds inherent',
      all(e.residual <= e.inherent + 1e-12
          for e in [T.EntryPoint('x', c, 'data', l, i, [half])
                    for c in T.CLASSES for l in (1, 2, 3) for i in (1, 2, 3)]))
check('inherent is the plain product',
      T.EntryPoint('x', 'opportunist', 'data', 2, 3).inherent == 6)

# ===========================================================================
# ranking, gaps and planes
# ===========================================================================
entries, ctls = T.aldergate()
r = T.ranked(entries)
check('ranking returns every entry', len(r) == len(entries))
check('ranking is descending by residual',
      all(r[i]['residual'] >= r[i + 1]['residual'] for i in range(len(r) - 1)))
check('ties on the inherent score are reported',
      any(row['inherent_tied_with'] > 0 for row in r))
check('the residual scoring separates rows the inherent one ties',
      sum(1 for x in r if x['inherent_tied_with'])
      > sum(1 for x in r if x['tied_with']))
check('every row carries both tie counts',
      all('tied_with' in x and 'inherent_tied_with' in x for x in r))
ts = T.tie_summary(entries)
check('the tie summary counts the rows', ts['rows'] == len(entries))
check('the inherent scale has fewer distinct values than there are rows',
      ts['inherent_distinct'] < ts['rows'])
check('and fewer than the residual scale produces',
      ts['inherent_distinct'] < ts['residual_distinct'])
check('the tie counts are consistent with the ranking',
      ts['inherent_rows_tied'] == sum(1 for x in r if x['inherent_tied_with'])
      and ts['residual_rows_tied'] == sum(1 for x in r if x['tied_with']))
g = T.gaps(entries)
check('every gap has no effective control', all(e.is_gap for e in g))
check('no non-gap is in the gap list',
      all(e.is_gap for e in g) and len(g) == len([e for e in entries if e.is_gap]))
check('the gap list is descending by residual',
      all(g[i].residual >= g[i + 1].residual for i in range(len(g) - 1)))
bp = T.by_plane(entries)
check('every plane appears, including empty ones', set(bp) == set(T.PLANES))
check('plane counts sum to the register', sum(v['count'] for v in bp.values()) == len(entries))
check('plane residuals sum to the register total',
      close(sum(v['residual'] for v in bp.values()),
            round(sum(e.residual for e in entries), 3), 1e-6))
check('plane gap counts sum to the gap list',
      sum(v['gaps'] for v in bp.values()) == len(g))
inert_rows = T.inert(entries)
check('the inert-control report finds the mismatched control',
      any('Console' in row['entry'] for row in inert_rows))
check('the inert report names the class faced and the classes covered',
      all('class_faced' in row and 'classes_covered' in row for row in inert_rows))

# ===========================================================================
# what one more control buys
# ===========================================================================
w = T.control_would_close(entries, ctls['mfa'])
check('a candidate control reduces the total', w['reduction'] > 0)
check('and closes only gaps it addresses',
      all(any(e.name == n and e.is_gap for e in entries) for n in w['closes']))
check('a candidate that addresses nothing on the register buys nothing',
      T.control_would_close(
          entries, T.Control('anti-state posture', {'state': 0.5}))['reduction'] == 0.0)
check('the reduction percentage is consistent with the totals',
      close(w['reduction_pct'],
            round(100.0 * w['reduction'] / w['residual_before'], 1), 1e-6))
check('residual after is below residual before',
      w['residual_after'] < w['residual_before'])

# ===========================================================================
# report and CLI
# ===========================================================================
check('report carries both scales',
      set(rep['scales']) == {'likelihood', 'impact'})
check('report carries every entry', len(rep['entries']) == 8)
check('report carries the by-plane summary', set(rep['by_plane']) == set(T.PLANES))
check('report carries caveats', len(rep['caveats']) >= 5)
check('a caveat says the scale is ordinal',
      any('ORDINAL' in c for c in rep['caveats']))
check('a caveat says coverage is a claim not a measurement',
      any('CLAIM about a control' in c for c in rep['caveats']))
check('a caveat says a residual never reaches zero',
      any('never reaches zero' in c for c in rep['caveats']))
check('a caveat admits the segmentation simplification',
      any('limit REACH rather than' in c for c in rep['caveats']))
check('report JSON-serialises', isinstance(json.dumps(rep), str))
text = T.report_text(rep)
check('the text explains the defect it replaced', 'none (flat)' in text)
check('the text names the sections',
      all(s in text for s in ('A.', 'B.', 'C.', 'D.', 'E.', 'F.')))
check('the text discloses what it does not establish',
      'does NOT establish' in text)
check('the text reports the tie rather than picking one',
      'NO SINGLE BEST' in text)
check('the text shows the ties in the ranking', 'rows tied' in text)
check('the text contrasts the two scorings',
      'likelihood x impact alone' in text and 'residual after controls' in text)

out = subprocess.run([sys.executable, 'threat_model.py', '--json'],
                     capture_output=True, text=True)
check('--json exits zero', out.returncode == 0)
check('--json parses', isinstance(json.loads(out.stdout), dict))
plain = subprocess.run([sys.executable, 'threat_model.py'],
                       capture_output=True, text=True)
check('plain run exits zero', plain.returncode == 0)
check('plain run is not JSON', not plain.stdout.lstrip().startswith('{'))
check('plain run names the flat camera segment as a gap',
      'IoT cameras on a flat segment' in plain.stdout.split('C. The gaps')[1])

print('threat_model: %d checks, %d failed' % (CHECKS, len(FAILED)))
for f in FAILED:
    print('  FAILED: ' + f)
sys.exit(1 if FAILED else 0)
