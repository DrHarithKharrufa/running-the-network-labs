#!/usr/bin/env python3
"""Checks for Lab 48.2.

The chapter said fronthaul needs "huge bandwidth". These checks show the five
terms that actually decide it, each one moving the answer by the amount it
should, and the model refusing a configuration it has no figure for rather than
guessing.

    python3 test_fronthaul_rate.py
"""
import sys

import fronthaul_rate as R

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
    except R.RateError as e:
        check(name, want.lower() in str(e).lower(),
              'raised %r, wanted something about %r' % (str(e), want))
    except Exception as e:                      # noqa: BLE001
        check(name, False, 'raised %s, not RateError' % type(e).__name__)
    else:
        check(name, False, 'did not raise')


# ===========================================================================
# 1. The frame structure
# ===========================================================================
check('15 kHz at numerology 0', R.scs_khz(0) == 15.0)
check('30 kHz at 1', R.scs_khz(1) == 30.0)
check('120 kHz at 3', R.scs_khz(3) == 120.0)
check('spacing doubles with each step',
      all(R.scs_khz(u + 1) == 2 * R.scs_khz(u) for u in range(5)))
check('1000 slots a second at numerology 0', R.slots_per_second(0) == 1000.0)
check('and 8000 at numerology 3', R.slots_per_second(3) == 8000.0)
check('14 symbols to a slot', R.SYMBOLS_PER_SLOT == 14)
check('12 subcarriers to a resource block', R.SUBCARRIERS_PER_RB == 12)
close('28000 symbols a second at numerology 1', R.symbols_per_second(1), 28000.0)
raises('a numerology out of range is refused', lambda: R.scs_khz(9), '0..6')

# ===========================================================================
# 2. The base calculation, term by term
# ===========================================================================
r = R.fronthaul_gbps(100.0, 1, streams=4)
check('273 resource blocks', r['resource_blocks'] == 273)
check('3276 subcarriers', r['subcarriers'] == 3276)
close('91.728 M resource elements a second',
      r['resource_elements_per_s'] / 1e6, 91.728, 0.01)
close('11.74 Gb/s of payload', r['payload_gbps'], 11.741, 0.01)
close('12.92 Gb/s with 10% overhead', r['with_overhead_gbps'], 12.915, 0.01)
check('the payload is elements x 2 x bits x streams',
      abs(r['payload_gbps'] * 1e9
          - r['resource_elements_per_s'] * 2 * 16 * 4) < 1)
close('the occupied bandwidth is 98.28 MHz',
      R.occupied_bandwidth_mhz(100.0, 1), 98.28, 0.01)
check('which is less than the channel, as it must be',
      R.occupied_bandwidth_mhz(100.0, 1) < 100.0)

# ===========================================================================
# 3. Each lever moves it by the factor it should
# ===========================================================================
base = R.fronthaul_gbps(100.0, 1, streams=4)['with_overhead_gbps']
check('doubling the streams doubles the rate',
      abs(R.fronthaul_gbps(100.0, 1, streams=8)['with_overhead_gbps'] / base - 2.0)
      < 1e-9)
check('sixteen times the streams is sixteen times the rate',
      abs(R.fronthaul_gbps(100.0, 1, streams=64)['with_overhead_gbps'] / base - 16.0)
      < 1e-9)
check('halving the sample width nearly halves the rate',
      abs(R.fronthaul_gbps(100.0, 1, streams=4, bits_per_sample=8)['with_overhead_gbps']
          / base - 0.5) < 1e-9)
close('9-bit compression saves 44%',
      100 * (1 - R.fronthaul_gbps(100.0, 1, streams=4,
                                  bits_per_sample=9)['with_overhead_gbps'] / base),
      43.75, 0.01)
check('a duty cycle of 0.5 halves it',
      abs(R.fronthaul_gbps(100.0, 1, streams=4,
                           duty_cycle=0.5)['with_overhead_gbps'] / base - 0.5) < 1e-9)
check('zero overhead is the payload',
      abs(R.fronthaul_gbps(100.0, 1, streams=4,
                           overhead_percent=0)['with_overhead_gbps']
          - r['payload_gbps']) < 1e-9)

# a wider channel at a higher spacing is NOT proportional, because the
# resource-block count comes from a table rather than from the bandwidth
wide = R.fronthaul_gbps(400.0, 3, streams=4)['with_overhead_gbps']
check('four times the bandwidth is not four times the rate',
      abs(wide / base - 4.0) > 0.1,
      'got %.2fx --- the block count and the symbol rate both change' % (wide / base))
check('but it is bigger', wide > base)

# ===========================================================================
# 4. The model refuses what it has no figure for
# ===========================================================================
raises('an unrecorded bandwidth/numerology pair is refused',
       lambda: R.fronthaul_gbps(60.0, 1, streams=4), 'no resource-block count')
try:
    R.fronthaul_gbps(60.0, 1, streams=4)
    _msg = ''
except R.RateError as _e:
    _msg = str(_e)
check('and the message says where the real number comes from',
      'channel table' in _msg, _msg)
raises('zero streams is refused', lambda: R.fronthaul_gbps(100.0, 1, streams=0),
       'at least one stream')
raises('a zero-bit sample is refused',
       lambda: R.fronthaul_gbps(100.0, 1, streams=4, bits_per_sample=0),
       'at least one bit')
raises('negative overhead is refused',
       lambda: R.fronthaul_gbps(100.0, 1, streams=4, overhead_percent=-1),
       'not negative')
raises('a duty cycle above 1 is refused',
       lambda: R.fronthaul_gbps(100.0, 1, streams=4, duty_cycle=1.5), '(0, 1]')
raises('a zero duty cycle is refused',
       lambda: R.fronthaul_gbps(100.0, 1, streams=4, duty_cycle=0), '(0, 1]')

# ===========================================================================
# 5. Links needed
# ===========================================================================
check('12.92 Gb/s needs two 10G links at 90% usable',
      R.links_needed(12.92, 10.0) == 2)
check('and one 25G link', R.links_needed(12.92, 25.0) == 1)
check('206.6 Gb/s needs three 100G links', R.links_needed(206.64, 100.0) == 3)
check('it rounds up, never down', R.links_needed(9.1, 10.0) == 2)
check('a usable fraction of 1 needs fewer',
      R.links_needed(9.1, 10.0, usable_fraction=1.0) == 1)
raises('a zero link rate is refused', lambda: R.links_needed(10, 0), 'positive')
raises('a usable fraction above 1 is refused',
       lambda: R.links_needed(10, 10, usable_fraction=1.5), '(0, 1]')

# compression changes the link count, which is the operational point
big = R.fronthaul_gbps(100.0, 1, streams=64)['with_overhead_gbps']
small = R.fronthaul_gbps(100.0, 1, streams=64, bits_per_sample=9)['with_overhead_gbps']
check('compression saves links at 25G',
      R.links_needed(small, 25.0) < R.links_needed(big, 25.0),
      '%d against %d' % (R.links_needed(small, 25.0), R.links_needed(big, 25.0)))

# ===========================================================================
# 6. The report is consistent with the model
# ===========================================================================
import io                                                     # noqa: E402
import contextlib                                             # noqa: E402

raises('fractional numerology must not be silently truncated',
       lambda: R.fronthaul_gbps(100, 1.5, 4), 'numerology')
raises('fractional stream count is refused',
       lambda: R.fronthaul_gbps(100, 1, 4.5), 'stream')

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    R.main([])
out = buf.getvalue()
check('the report runs', 'A. The five terms' in out)
check('it shows the arithmetic term by term', 'resource elements per second' in out)
check('it names streams as the runaway term', 'Streams are the term that runs away' in out)
check('it gives the link counts', 'at 100G' in out)
check('it says streams are not antenna elements',
      'Streams are not antenna elements' in out)
check('it says the block counts are not the specification table',
      'not a reproduction' in out)
check('it discloses what it does not establish', 'does NOT establish' in out)
check('no report line is absurdly wide',
      max(len(l) for l in out.splitlines()) <= 80,
      'widest %d' % max(len(l) for l in out.splitlines()))

# ===========================================================================
if __name__ == '__main__':
    total = PASS + len(FAIL)
    for f in FAIL:
        print('FAIL: %s' % f)
    print('%d/%d checks passed' % (PASS, total))
    sys.exit(1 if FAIL else 0)
