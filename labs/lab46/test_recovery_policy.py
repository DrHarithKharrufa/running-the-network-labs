#!/usr/bin/env python3
"""Checks for Lab 46.1.

The first duty of these checks is to show that the model CAN produce the
answer the chapter used to assert and CAN refuse it, depending on the inputs
--- because the script this replaces could only ever produce one answer.  So
the first group deliberately drives the model into the old conclusion, and the
second group drives it out again.

    python3 test_recovery_policy.py
"""
import sys

import recovery_policy as R

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
    except R.PolicyError as e:
        check(name, want.lower() in str(e).lower(),
              'raised %r, wanted something about %r' % (str(e), want))
    except Exception as e:                      # noqa: BLE001
        check(name, False, 'raised %s, not PolicyError' % type(e).__name__)
    else:
        check(name, False, 'did not raise')


# ===========================================================================
# 1. The model is capable of BOTH answers
# ===========================================================================
def opt(mech, **kw):
    return R.layer('optical', detect_ms=kw.pop('detect_ms', 10),
                   mechanism_name=mech, **kw)


def pkt(mech='packet-igp', **kw):
    return R.layer('packet', detect_ms=kw.pop('detect_ms', 150),
                   mechanism_name=mech, **kw)


# --- the hold-off CAN be right: when the layer it waits for is genuinely
#     faster and cannot fail to find a path
sim = R.simulate(opt('optical-protection'), pkt(holdoff_ms=250))
check('protection + hold-off: optical wins', sim['restored_by'] == 'optical')
check('protection + hold-off: 60 ms outage', sim['outage_ms'] == 60,
      'got %r' % sim['outage_ms'])
check('protection + hold-off: packet never acted',
      sim['packet_up_at_ms'] is None)
check('protection + hold-off: beats packet alone',
      sim['outage_ms'] < R.simulate(opt('none'), pkt())['outage_ms'])

# --- the hold-off is wrong when it waits for restoration
sim = R.simulate(opt('optical-restoration'), pkt(holdoff_ms=35000))
check('restoration + hold-off: optical wins', sim['restored_by'] == 'optical')
check('restoration + hold-off: 30 s outage', sim['outage_ms'] == 30010,
      'got %r' % sim['outage_ms'])
alone = R.simulate(opt('none'), pkt())
check('restoration + hold-off is worse than packet alone',
      sim['outage_ms'] > alone['outage_ms'])
check('and worse by a factor of more than a hundred',
      sim['outage_ms'] / float(alone['outage_ms']) > 100,
      'factor %.1f' % (sim['outage_ms'] / float(alone['outage_ms'])))

# ===========================================================================
# 2. The old conclusion is refused: one cut does not churn
# ===========================================================================
both = R.simulate(opt('optical-restoration'), pkt())
check('uncoordinated: restored by packet', both['restored_by'] == 'packet')
check('uncoordinated: 211 ms', both['outage_ms'] == 211, 'got %r' % both['outage_ms'])
check('uncoordinated: zero churn', R.churn_cycles(both) == 0)
check('uncoordinated: exactly one down cycle', both['down_cycles'] == 1)
check('uncoordinated: the second path is noted, not counted as an outage',
      both['second_path_at_ms'] == 30010, 'got %r' % both['second_path_at_ms'])
check('uncoordinated: no transition says flap or churn',
      not any('flap' in t['why'].lower() or 'churn' in t['why'].lower()
              for t in both['transitions']))
check('uncoordinated: beats the hold-off policy',
      both['outage_ms'] < R.simulate(opt('optical-restoration'),
                                     pkt(holdoff_ms=35000))['outage_ms'])

# every combination of the two layers acting, and none of them churns
combos = 0
for om in ('none', 'optical-protection', 'optical-restoration'):
    for pm in ('none', 'packet-frr', 'packet-igp'):
        for ho in (0, 250, 35000):
            s = R.simulate(opt(om), pkt(pm, holdoff_ms=ho) if pm != 'none'
                           else R.layer('packet', detect_ms=150,
                                        mechanism_name='none'))
            combos += 1
            if R.churn_cycles(s) != 0:
                FAIL.append('combo %s/%s/%d churned with no cause' % (om, pm, ho))
check('every layer combination churns zero times without a stated cause',
      combos == 27, 'ran %d combinations' % combos)

# ===========================================================================
# 3. Churn exists only when a cause is named
# ===========================================================================
base = R.simulate(opt('optical-protection'), pkt())
check('no disturbances: zero churn', R.churn_cycles(base) == 0)

one = R.simulate(opt('optical-protection'), pkt(),
                 disturbances=[(1000, 'reversion was not hitless', 40)])
check('one disturbance: one churn cycle', R.churn_cycles(one) == 1)
check('one disturbance: two down cycles', one['down_cycles'] == 2)
check('one disturbance: total down is the sum of both',
      one['total_down_ms'] == 60 + 40, 'got %r' % one['total_down_ms'])
check('one disturbance: the cause is carried into the transition',
      any('hitless' in t['why'] for t in one['transitions']))

two = R.simulate(opt('optical-protection'), pkt(),
                 disturbances=[(1000, 'a', 40), (2000, 'b', 50)])
check('two disturbances: two churn cycles', R.churn_cycles(two) == 2)
check('two disturbances: total down accumulates',
      two['total_down_ms'] == 60 + 40 + 50, 'got %r' % two['total_down_ms'])

perm = R.simulate(opt('optical-protection'), pkt(),
                  disturbances=[(1000, 'a permanent second fault')])
check('a disturbance with no recovery leaves the service down',
      perm['total_down_ms'] is None)

raises('a disturbance before the recovery is refused',
       lambda: R.simulate(opt('optical-protection'), pkt(),
                          disturbances=[(10, 'too early', 5)]),
       'not after the recovery')

# ===========================================================================
# 4. Restoration can fail; protection cannot fail to find a path
# ===========================================================================
f = R.simulate(opt('optical-restoration', succeeds=False), pkt(holdoff_ms=35000))
check('failed restoration: packet ends up restoring', f['restored_by'] == 'packet')
check('failed restoration: outage is the hold-off plus convergence',
      f['outage_ms'] == 35211, 'got %r' % f['outage_ms'])
check('failed restoration: optical never came up', f['optical_up_at_ms'] is None)
check('failed restoration: the timeline says so',
      any(e['kind'] == 'failed' for e in f['events']))

g = R.simulate(opt('optical-restoration', succeeds=False), pkt())
check('failed restoration without hold-off: 211 ms', g['outage_ms'] == 211)
check('the hold-off cost 35 seconds for nothing',
      f['outage_ms'] - g['outage_ms'] == 35000)

n = R.simulate(opt('optical-restoration', succeeds=False),
               pkt(holdoff_ms=35000, succeeds=False))
check('neither layer recovers: unrecovered', n['unrecovered'])
check('neither layer recovers: no outage figure', n['outage_ms'] is None)
check('neither layer recovers: total down is open', n['total_down_ms'] is None)

failed_protection = R.simulate(opt('optical-protection', succeeds=False), pkt())
check('unavailable optical protection falls back to packet recovery',
      failed_protection['restored_by'] == 'packet' and failed_protection['outage_ms'] == 211)
failed_frr = R.simulate(opt('none'), R.layer('packet', detect_ms=1,
                       mechanism_name='packet-frr', succeeds=False))
check('unavailable packet FRR with no other recovery leaves service down',
      failed_frr['unrecovered'] and failed_frr['total_down_ms'] is None)
both_failed = R.simulate(opt('optical-protection', succeeds=False),
                        R.layer('packet', detect_ms=1, mechanism_name='packet-frr', succeeds=False))
check('a shared-risk failure can defeat both pre-established backups', both_failed['unrecovered'])

# ===========================================================================
# 5. The client-fault-propagation mechanism
# ===========================================================================
sq = R.simulate(opt('optical-restoration'), pkt(detect_ms=3000),
                propagation='squelch')
hd = R.simulate(opt('optical-restoration'), pkt(detect_ms=3000),
                propagation='hold')
check('squelch lets the packet layer act on the optical detection',
      sq['outage_ms'] == 211, 'got %r' % sq['outage_ms'])
check('hold makes it wait for its own liveness check',
      hd['outage_ms'] == 3200, 'got %r' % hd['outage_ms'])
check('hold is the slower of the two', hd['outage_ms'] > sq['outage_ms'])
check('hold imposes seconds of delay nobody configured as a hold-off',
      hd['outage_ms'] - sq['outage_ms'] > 2500)
check('squelch is recorded in the result', sq['propagation'] == 'squelch')
check('a squelched port pre-empts the router timer, it does not add to it',
      sq['outage_ms'] < 3000 + R.MECHANISMS['packet-igp']['recover_ms'])
check('squelch helps most where the router timer is slowest',
      (R.simulate(opt('none'), pkt(detect_ms=3000), propagation='hold')['outage_ms'] -
       R.simulate(opt('none'), pkt(detect_ms=3000), propagation='squelch')['outage_ms'])
      >
      (R.simulate(opt('none'), pkt(detect_ms=150), propagation='hold')['outage_ms'] -
       R.simulate(opt('none'), pkt(detect_ms=150), propagation='squelch')['outage_ms']))
check('a router faster than the transport detection is not slowed by squelch',
      R.simulate(opt('none'), pkt(detect_ms=3), propagation='squelch')['outage_ms']
      == 203)
raises('an unknown propagation is refused',
       lambda: R.simulate(opt('none'), pkt(), propagation='ignore'),
       'unknown propagation')

# ===========================================================================
# 6. The hold-off that expires after the link returns does nothing
# ===========================================================================
late = R.simulate(opt('optical-protection'), pkt(holdoff_ms=250))
check('a hold-off longer than a fast protection switch: packet is a no-op',
      any(e['kind'] == 'noop' for e in late['events']))
check('and the packet layer contributed no recovery time',
      late['packet_up_at_ms'] is None)
early = R.simulate(opt('optical-protection'), pkt(holdoff_ms=0))
check('with no hold-off the packet layer does start',
      early['packet_up_at_ms'] == 211, 'got %r' % early['packet_up_at_ms'])
check('but optical protection still restores first',
      early['restored_by'] == 'optical' and early['outage_ms'] == 60)

# ===========================================================================
# 7. Inputs are validated
# ===========================================================================
raises('unknown mechanism', lambda: R.mechanism('optical-magic'), 'unknown mechanism')
raises('negative detection',
       lambda: R.layer('x', detect_ms=-1, mechanism_name='packet-igp'), 'not negative')
raises('negative hold-off',
       lambda: R.layer('x', detect_ms=1, mechanism_name='packet-igp',
                       holdoff_ms=-5), 'not negative')
raises('negative recovery override',
       lambda: R.layer('x', detect_ms=1, mechanism_name='packet-igp',
                       recover_ms=-1), 'not negative')
raises('repair before the cut',
       lambda: R.simulate(opt('none'), pkt(), repair_ms=-1), 'before the cut')
raises('negative wait-to-restore',
       lambda: R.simulate(opt('none'), pkt(), wait_to_restore_ms=-1),
       'not negative')

over = R.layer('packet', detect_ms=150, mechanism_name='packet-igp',
               recover_ms=900)
check('a recovery time can be overridden', over['recover_ms'] == 900)
check('and the override changes the answer',
      R.simulate(opt('none'), over)['outage_ms'] == 911)

# ===========================================================================
# 8. The mechanism table says what it is
# ===========================================================================
check('restoration is slower than protection at both layers',
      R.MECHANISMS['optical-restoration']['recover_ms'] >
      R.MECHANISMS['optical-protection']['recover_ms'] and
      R.MECHANISMS['packet-igp']['recover_ms'] >
      R.MECHANISMS['packet-frr']['recover_ms'])
check('optical restoration is slower than packet restoration',
      R.MECHANISMS['optical-restoration']['recover_ms'] >
      R.MECHANISMS['packet-igp']['recover_ms'])
check('every active recovery mechanism can lack usable resources',
      all(m['can_fail'] == (m['kind'] != 'none')
          for m in R.MECHANISMS.values()))
check('both layers have one of each kind',
      {R.MECHANISMS['optical-protection']['kind'],
       R.MECHANISMS['optical-restoration']['kind']} ==
      {R.MECHANISMS['packet-frr']['kind'],
       R.MECHANISMS['packet-igp']['kind']} == {'protection', 'restoration'})

# ===========================================================================
# 9. The report is consistent with the model
# ===========================================================================
cases = R.build_cases()
check('the report builds five cases', len(cases) == 5)
results = [R.simulate(o, p, propagation=pr, **ex) for _, o, p, pr, ex in cases]
check('no reported case churns', all(R.churn_cycles(r) == 0 for r in results))
check('the advised policy is the slowest of the five',
      results[1]['outage_ms'] == max(r['outage_ms'] for r in results))
check('the fastest is optical protection with a short hold-off',
      results[3]['outage_ms'] == min(r['outage_ms'] for r in results))
check('the uncoordinated case matches the packet-only case',
      results[2]['outage_ms'] == results[0]['outage_ms'])

# ===========================================================================
if __name__ == '__main__':
    total = PASS + len(FAIL)
    for f in FAIL:
        print('FAIL: %s' % f)
    print('%d/%d checks passed' % (PASS, total))
    sys.exit(1 if FAIL else 0)
