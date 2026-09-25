#!/usr/bin/env python3
"""Checks for Lab 46.3.

A contract checker that accepts everything is the chapter's original claim in
code, and one that refuses everything is no more useful.  So these checks show
each clause refusing on its own, each clause passing on its own, and the two
questions the contract cannot answer staying unanswered.

    python3 test_ols_contract.py
"""
import sys

import ols_contract as C

PASS = 0
FAIL = []


def check(name, cond, detail=''):
    global PASS
    if cond:
        PASS += 1
    else:
        FAIL.append('%s%s' % (name, (' --- ' + detail) if detail else ''))


def close(name, got, want, tol=0.02):
    check(name, abs(got - want) <= tol, 'got %.4f, wanted %.4f' % (got, want))


def raises(name, fn, want):
    try:
        fn()
    except C.ContractError as e:
        check(name, want.lower() in str(e).lower(),
              'raised %r, wanted something about %r' % (str(e), want))
    except Exception as e:                      # noqa: BLE001
        check(name, False, 'raised %s, not ContractError' % type(e).__name__)
    else:
        check(name, False, 'did not raise')


OLS = C.OLS


def src(**kw):
    base = dict(name='test source', centre_thz=193.100, baud_gbd=118,
                width_ghz=137.5, launch_dbm=-3.0, required_osnr_db=20.0,
                mode_id='118Gbd-16QAM-oFEC-15%', telemetry='api')
    base.update(kw)
    return C.wavelength_source(**base)


def clause(result, name):
    return [c for c in result['clauses'] if c[0] == name][0]


# ===========================================================================
# 1. The baseline is ACCEPTED --- the checker is not rigged to refuse
# ===========================================================================
r = C.check_contract(OLS, src())
check('the baseline source is accepted', r['accepted'], '%r' % r['failed'])
check('no clause failed', r['failed'] == [])
check('and none was left unevaluated', r['unevaluated'] == [])
check('every clause reports a detail string',
      all(isinstance(c[2], str) and c[2] for c in r['clauses']))
check('there are seven clauses', len(r['clauses']) == 7,
      'got %d' % len(r['clauses']))

# ===========================================================================
# 2. Each clause can refuse ON ITS OWN
# ===========================================================================
only = lambda res, name: res['failed'] == [name]            # noqa: E731

r = C.check_contract(OLS, src(centre_thz=186.500))
check('band refuses alone', only(r, 'band'), '%r' % r['failed'])

r = C.check_contract(OLS, src(centre_thz=193.104))
check('off-grid centre refuses alone', only(r, 'centre on grid'),
      '%r' % r['failed'])
check('and says what the index came to',
      'n = 0.640' in clause(r, 'centre on grid')[2])

r = C.check_contract(OLS, src(launch_dbm=+3.0))
check('a hot source refuses alone', only(r, 'power spectral density'),
      '%r' % r['failed'])
r = C.check_contract(OLS, src(launch_dbm=-15.0))
check('a cold source refuses alone too', only(r, 'power spectral density'))

r = C.check_contract(OLS, src(), channels_in_service=64)
check('a full line system refuses alone', only(r, 'channel count'),
      '%r' % r['failed'])
r = C.check_contract(OLS, src(), channels_in_service=63)
check('and the last channel still fits', r['accepted'])

r = C.check_contract(OLS, src(telemetry='none', where='router faceplate'))
check('an unreported channel refuses alone',
      only(r, 'visibility to the line system'), '%r' % r['failed'])
r = C.check_contract(OLS, src(telemetry='manual'))
check('a manually registered channel passes that clause', r['accepted'])

tight = C.line_system('tight', 191.3, 196.1, -26.0, -20.0, 64,
                      per_channel_osnr_db=20.5)
r = C.check_contract(tight, src())
check('a path short of OSNR refuses alone', only(r, 'OSNR on the path'),
      '%r' % r['failed'])
r = C.check_contract(tight, src(required_osnr_db=17.5))
check('an easier mode on the same path is accepted', r['accepted'])

# ===========================================================================
# 3. A clause the envelope does not publish is UNEVALUATED, not passed
# ===========================================================================
silent = C.line_system('silent', 191.3, 196.1, -26.0, -20.0, 64)
r = C.check_contract(silent, src())
check('an unpublished OSNR is not counted as a pass',
      r['unevaluated'] == ['OSNR on the path'])
check('the source is still accepted on the clauses that exist', r['accepted'])
check('and the verdict says a clause was unevaluated',
      'unevaluated' in C.verdict(r))
check('a published OSNR is evaluated',
      C.check_contract(OLS, src())['unevaluated'] == [])

# ===========================================================================
# 4. Power spectral density is not launch power
# ===========================================================================
narrow = src(width_ghz=50.0, launch_dbm=-3.0, baud_gbd=40)
wide = src(width_ghz=200.0, launch_dbm=-3.0, baud_gbd=118)
close('a 137.5 GHz channel at -3 dBm is -24.38 dBm/GHz',
      src()['psd_dbm_per_ghz'], -24.38)
close('the same power over 50 GHz is -19.99', narrow['psd_dbm_per_ghz'], -19.99)
close('and over 200 GHz is -26.01', wide['psd_dbm_per_ghz'], -26.01)
check('so the same launch power passes at one width and fails at another',
      C.check_contract(OLS, src())['accepted'] and
      not C.check_contract(OLS, narrow)['accepted'] and
      not C.check_contract(OLS, wide)['accepted'])
check('which is why the envelope is written in PSD and not in dBm',
      'dBm/GHz' in clause(C.check_contract(OLS, src()),
                          'power spectral density')[2])

# ===========================================================================
# 5. Flexgrid: two granularities, and the rounding is spectrum you lose
# ===========================================================================
check('the centre index uses 6.25 GHz', C.CENTRE_GRANULARITY_GHZ == 6.25)
check('the slot width uses 12.5 GHz', C.SLOT_GRANULARITY_GHZ == 12.5)
check('they are different numbers',
      C.CENTRE_GRANULARITY_GHZ != C.SLOT_GRANULARITY_GHZ)
check('62.5 GHz is five slots exactly', C.slots_needed(62.5) == 5)
check('63 GHz is six', C.slots_needed(63.0) == 6)
check('137.5 GHz is eleven', C.slots_needed(137.5) == 11)
check('a channel on a 6.25 GHz index but not a 12.5 one is still on grid',
      C.check_contract(OLS, src(centre_thz=193.10625))['accepted'],
      'that half-step is most of the point of a flexible grid')
close('the anchor is 193.1 THz', C.n_index(193.1), 0.0)
close('one index step is 6.25 GHz', C.n_index(193.10625), 1.0)
check('the waste is reported', 'unusable' in clause(
    C.check_contract(OLS, src()), 'slot width')[2])

# ===========================================================================
# 6. The line system is not a party to modem interoperability
# ===========================================================================
a = src(name='a', mode_id='118Gbd-16QAM-oFEC-15%')
b = src(name='b', centre_thz=193.150, mode_id='118Gbd-16QAM-oFEC-15%')
c = src(name='c', centre_thz=193.200, mode_id='118Gbd-8QAM-cFEC-25%',
        required_osnr_db=17.5)
check('all three are accepted by the line system',
      all(C.check_contract(OLS, x)['accepted'] for x in (a, b, c)))
check('the two with the same mode interoperate',
      C.modems_interoperate(a, b)['interoperate'])
check('the two with different modes do not',
      not C.modems_interoperate(a, c)['interoperate'])
check('and the reason names both modes',
      '8QAM' in C.modems_interoperate(a, c)['why'] and
      '16QAM' in C.modems_interoperate(a, c)['why'])
check('acceptance and interoperability are independent',
      C.check_contract(OLS, c)['accepted'] and
      not C.modems_interoperate(a, c)['interoperate'])
check('a mode differing only in FEC does not interoperate',
      not C.modems_interoperate(
          src(mode_id='118Gbd-16QAM-oFEC-15%'),
          src(mode_id='118Gbd-16QAM-cFEC-15%'))['interoperate'],
      'FEC is part of the mode, not a detail below it')

# ===========================================================================
# 7. Malformed envelopes and declarations are refused
# ===========================================================================
raises('an inverted band',
       lambda: C.line_system('x', 196.1, 191.3, -26.0, -20.0, 64), 'inverted')
raises('an inverted power window',
       lambda: C.line_system('x', 191.3, 196.1, -20.0, -26.0, 64), 'inverted')
raises('a line system carrying no channels',
       lambda: C.line_system('x', 191.3, 196.1, -26.0, -20.0, 0),
       'at least one channel')
raises('zero baud', lambda: src(baud_gbd=0), 'positive')
raises('zero width', lambda: src(width_ghz=0), 'positive')
raises('a channel narrower than its baud rate',
       lambda: src(baud_gbd=118, width_ghz=60.0), 'not physical')
raises('an unknown telemetry value', lambda: src(telemetry='maybe'),
       'none, manual or api')

# ===========================================================================
# 8. The report is consistent with the model
# ===========================================================================
check('the report declares seven sources', len(C.SOURCES) == 7)
results = [C.check_contract(OLS, s, channels_in_service=12) for s in C.SOURCES]
check('three are accepted', sum(1 for r in results if r['accepted']) == 3,
      '%d accepted' % sum(1 for r in results if r['accepted']))
failed = [f for r in results for f in r['failed']]
check('and the four refusals are on four different clauses',
      len(set(failed)) == 4 and len(failed) == 4, '%r' % failed)
check('one refusal is the band', 'band' in failed)
check('one is the grid', 'centre on grid' in failed)
check('one is the power', 'power spectral density' in failed)
check('one is visibility', 'visibility to the line system' in failed)
check('the two accepted third-party sources run different modes',
      len({s['mode_id'] for s in C.SOURCES
           if s['name'].startswith('a third party')}) == 2)

# ===========================================================================
if __name__ == '__main__':
    total = PASS + len(FAIL)
    for f in FAIL:
        print('FAIL: %s' % f)
    print('%d/%d checks passed' % (PASS, total))
    sys.exit(1 if FAIL else 0)
