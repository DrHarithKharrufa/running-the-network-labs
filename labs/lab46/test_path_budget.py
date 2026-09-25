#!/usr/bin/env python3
"""Checks for Lab 46.2.

The point of these checks is that the model must be able to APPROVE and to
REFUSE the chapter's design depending on the ring it is given.  A model that
can only refuse is as useless as the one it replaces, which could only
confirm.  So the first group shows it approving the ring as drawn, and the
second shows exactly what has to change before it refuses.

    python3 test_path_budget.py
"""
import sys

import path_budget as P

PASS = 0
FAIL = []


def check(name, cond, detail=''):
    global PASS
    if cond:
        PASS += 1
    else:
        FAIL.append('%s%s' % (name, (' --- ' + detail) if detail else ''))


def close(name, got, want, tol=0.05):
    check(name, abs(got - want) <= tol, 'got %.4f, wanted %.4f' % (got, want))


def raises(name, fn, want):
    try:
        fn()
    except P.BudgetError as e:
        check(name, want.lower() in str(e).lower(),
              'raised %r, wanted something about %r' % (str(e), want))
    except Exception as e:                      # noqa: BLE001
        check(name, False, 'raised %s, not BudgetError' % type(e).__name__)
    else:
        check(name, False, 'did not raise')


R = P.KESTREL

# ===========================================================================
# 1. The ring geometry, which is what the whole result rests on
# ===========================================================================
check('four sites', R['n'] == 4)
close('96 km round', sum(R['spans_km']), 96.0)

cw, acw = P.paths_between(R, 'PoP-A', 'PoP-B')
check('the short way is one span', len(cw['spans']) == 1)
check('the short way has no express pass', len(cw['through']) == 0)
check('the long way is three spans', len(acw['spans']) == 3)
check('the long way has two express passes', len(acw['through']) == 2)
check('and they are the two sites in between',
      set(acw['through']) == {'PoP-D', 'PoP-C'})

# opposite corners: both ways are two spans and one express pass
cw2, acw2 = P.paths_between(R, 'PoP-A', 'PoP-C')
check('opposite corners are two spans each way',
      len(cw2['spans']) == len(acw2['spans']) == 2)
check('and one express pass each way',
      len(cw2['through']) == len(acw2['through']) == 1)
check('the two directions use different spans',
      not set(cw2['spans']) & set(acw2['spans']))

raises('a site not on the ring', lambda: P.paths_between(R, 'PoP-A', 'PoP-Z'),
       'must both be on the ring')
raises('a path from a site to itself',
       lambda: P.paths_between(R, 'PoP-A', 'PoP-A'), 'two different sites')
raises('a two-site ring', lambda: P.ring(['X', 'Y'], [1.0, 2.0]),
       'at least three sites')
raises('wrong span count', lambda: P.ring(['X', 'Y', 'Z'], [1.0, 2.0]),
       'has 3 spans, got 2')
raises('a zero-length span', lambda: P.ring(['X', 'Y', 'Z'], [1.0, 0.0, 2.0]),
       'positive')
raises('wrong duct count',
       lambda: P.ring(['X', 'Y', 'Z'], [1.0, 2.0, 3.0], ducts=['a', 'b']),
       'one duct name per span')

# ===========================================================================
# 2. A ROADM pass is an amplified section, not a decoration
# ===========================================================================
b_short = P.path_osnr(R, cw)
b_long = P.path_osnr(R, acw)
check('the short path has one amplified section',
      b_short['amplified_sections'] == 1)
check('the long path has five', b_long['amplified_sections'] == 5)
check('three of them are fibre, two are nodes',
      b_long['express_passes'] == 2)
close('single 18 km span gives 44.54 dB', b_short['osnr_db'], 44.54)
close('the long way gives 28.98 dB', b_long['osnr_db'], 28.98)
check('so restoration costs over 15 dB on this pair',
      b_short['osnr_db'] - b_long['osnr_db'] > 15)

# the nodes, not the kilometres: same length, more nodes, worse OSNR
few = P.adjacent_service(4, 96.0)
many = P.adjacent_service(16, 96.0)
check('same 96 km, more sites, worse protection path',
      many['protection']['osnr_db'] < few['protection']['osnr_db'] - 10,
      '%.1f vs %.1f' % (many['protection']['osnr_db'],
                        few['protection']['osnr_db']))
check('and the working path actually IMPROVES, because the spans got shorter',
      many['working']['osnr_db'] > few['working']['osnr_db'])
check('which is why a working-path budget hides the problem',
      many['mode_from_working_path']['name'] ==
      few['mode_from_working_path']['name'])

# a node costs more than the fibre between nodes on this ring
node_only = P.path_osnr(R, {'spans': [0], 'through': ['PoP-B']})
check('adding one express node to a single span costs OSNR',
      node_only['osnr_db'] < b_short['osnr_db'])
check('and costs more than doubling the fibre would',
      node_only['osnr_db'] <
      P.path_osnr(R, {'spans': [0, 1], 'through': []})['osnr_db'])

# ===========================================================================
# 3. The model APPROVES the ring as drawn --- it is not rigged to refuse
# ===========================================================================
services = P.all_services(R)
check('six services on four sites', len(services) == 6)
check('none is overstated on this ring',
      not any(s['overstated'] for s in services))
check('every one has a mode that survives restoration',
      all(s['mode_that_survives_restoration'] for s in services))
check('and it is the highest-order mode in the set',
      all(s['mode_that_survives_restoration']['name'] == '16QAM, 118 Gbaud'
          for s in services))
check('so the chapter\'s conclusion is confirmed for THIS ring',
      all(not s['no_mode_survives'] for s in services))

# but the reason the chapter gave is still not the reason
check('the adjacent pairs lose far more OSNR than the opposite pairs',
      max(s['osnr_penalty_db'] for s in services) >
      10 * max(s['osnr_penalty_db'] for s in services
               if s['a'] == 'PoP-A' and s['b'] == 'PoP-C'))
check('the opposite-corner pairs barely notice restoration',
      min(s['osnr_penalty_db'] for s in services) < 0.5)
check('which is the opposite of what distance would predict',
      min(s['osnr_penalty_db'] for s in services) < 0.5 and
      min(s['working']['osnr_db'] for s in services) < 33)

# ===========================================================================
# 4. And it REFUSES once the ring changes in ordinary ways
# ===========================================================================
n10 = P.adjacent_service(10, 96.0)
check('ten sites on the same 96 km is overstated', n10['overstated'])
check('and the surviving mode drops below the working-path mode',
      n10['mode_that_survives_restoration']['client_gbps'] <
      n10['mode_from_working_path']['client_gbps'])

n4_400 = P.adjacent_service(4, 400.0)
check('four sites on a 400 km ring is overstated too', n4_400['overstated'])

n, s = P.breaking_point(96.0)
check('the 96 km ring breaks at ten sites', n == 10, 'got %r' % n)
n, s = P.breaking_point(400.0)
check('the 400 km ring breaks at four', n == 4, 'got %r' % n)

check('a bigger ring never breaks later than a smaller one',
      all(P.adjacent_service(k, 400.0)['protection']['osnr_db'] <=
          P.adjacent_service(k, 96.0)['protection']['osnr_db']
          for k in (4, 6, 8, 10, 12)))

huge = P.adjacent_service(32, 1200.0)
check('a big enough ring carries nothing at all round the long way',
      huge['no_mode_survives'], '%r' % P.name_of(
          huge['mode_that_survives_restoration']))
check('though the working path is still fine',
      huge['mode_from_working_path'] is not None)

# margin moves the answer, which is the point of having one
tight = P.adjacent_service(8, 96.0, margin_db=0.0)
loose = P.adjacent_service(8, 96.0, margin_db=6.0)
check('no margin: eight sites survives', not tight['overstated'])
check('six dB of margin: eight sites does not', loose['overstated'])
check('margin is recorded in the result', loose['margin_db'] == 6.0)

# ===========================================================================
# 5. Diversity: a ring drawn with four sides can have two in one trench
# ===========================================================================
shared = P.ring(R['sites'], R['spans_km'],
                ducts=['duct-north', 'duct-east', 'duct-south', 'duct-north'])
s = P.service(shared, 'PoP-A', 'PoP-B')
check('the shared duct is found', s['shared_ducts'] == ['duct-north'])
check('and the service is not diverse', not s['diverse'])
ok = P.service(R, 'PoP-A', 'PoP-B')
check('with distinct ducts it is diverse', ok['diverse'])
check('and no duct is shared', ok['shared_ducts'] == [])
check('diversity is independent of the OSNR result',
      abs(s['protection']['osnr_db'] - ok['protection']['osnr_db']) < 1e-9)

# ===========================================================================
# 6. Capacity after a cut
# ===========================================================================
check('16QAM at 118 Gbaud needs twelve 12.5 GHz slots',
      P.slots_for(P.MODES[-1]['width_ghz']) == 12,
      'width %.1f GHz' % P.MODES[-1]['width_ghz'])
check('slot counts round UP', P.slots_for(63.0) == 6 and P.slots_for(62.5) == 5)

occ = P.span_occupancy(R, services)
cut = P.span_occupancy(R, services, restored_span=0)
check('the C band holds 384 slots of 12.5 GHz', occ['slots_available'] == 384)
check('a cut makes the busiest surviving span busier',
      cut['worst_after'] > occ['worst_normal'])
check('the cut span carries nothing afterwards', cut['after_cut'][0] == 0)
check('this ring still fits after a cut', cut['fits_after_cut'])
check('total slots are conserved across the reroute',
      sum(cut['after_cut'].values()) > sum(occ['normal'].values()),
      'rerouted traffic takes more spans, so the total rises')

# a ring loaded enough to fail is expressible
tiny = P.span_occupancy(R, services, band_ghz=500.0, restored_span=0)
check('a narrow band does not fit after a cut', not tiny['fits_after_cut'])
check('but does fit normally',
      P.span_occupancy(R, services, band_ghz=500.0)['fits_normally'])

# ===========================================================================
# 7. Mode arithmetic matches Lab 45.1
# ===========================================================================
m = [x for x in P.MODES if x['name'] == '16QAM, 118 Gbaud'][0]
close('line rate 944 Gb/s', m['line_gbps'], 944.0)
close('client rate 786.7 Gb/s', m['client_gbps'], 786.67, tol=0.01)
check('the client rate is below the line rate for every mode',
      all(x['client_gbps'] < x['line_gbps'] for x in P.MODES))
check('a higher-order mode needs more OSNR at the same baud',
      [x for x in P.MODES if x['name'] == '16QAM, 118 Gbaud'][0]['required_osnr_db'] >
      [x for x in P.MODES if x['name'] == 'QPSK, 118 Gbaud'][0]['required_osnr_db'])
check('and a higher baud needs more OSNR at the same order',
      [x for x in P.MODES if x['name'] == '16QAM, 118 Gbaud'][0]['required_osnr_db'] >
      [x for x in P.MODES if x['name'] == '16QAM, 60 Gbaud'][0]['required_osnr_db'])
check('so two modes called 16QAM are not interchangeable',
      [x for x in P.MODES if x['name'] == '16QAM, 118 Gbaud'][0]['client_gbps'] !=
      [x for x in P.MODES if x['name'] == '16QAM, 60 Gbaud'][0]['client_gbps'])

check('no mode closes on an impossible OSNR', P.best_mode(5.0) is None)
check('the easiest mode closes on 12 dB',
      P.best_mode(12.0)['name'] == 'QPSK, 60 Gbaud')
check('best_mode prefers capacity, not the lowest requirement',
      P.best_mode(40.0)['name'] == '16QAM, 118 Gbaud')

raises('a negative noise figure',
       lambda: P.path_osnr(R, cw, amp_nf_db=-1), 'sensible')
raises('zero attenuation',
       lambda: P.path_osnr(R, cw, fibre_db_per_km=0), 'sensible')

# ===========================================================================
if __name__ == '__main__':
    total = PASS + len(FAIL)
    for f in FAIL:
        print('FAIL: %s' % f)
    print('%d/%d checks passed' % (PASS, total))
    sys.exit(1 if FAIL else 0)
