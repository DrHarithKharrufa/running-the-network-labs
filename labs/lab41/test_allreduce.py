#!/usr/bin/env python3
"""Checks for allreduce.py --- the cost model, not a cluster.

The previous version of that script could not be wrong: it divided a constant by
the minimum link rate, so "one link at a quarter of line rate makes it 4x
slower" was the formula restated, not a finding. These checks exist to make sure
the replacement can be wrong, and is not.

In particular they assert the thing that broke the old headline: the straggler
penalty must DEPEND ON THE MESSAGE SIZE, approaching the bandwidth ratio for
large gradients and approaching 1 for small ones. A model that returns the
bandwidth ratio at every size has lost the latency term again.

This executes no GPU, NIC, switch or fabric and predicts no real cluster.

    python3 test_allreduce.py
"""
import contextlib
import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import allreduce as ar  # noqa: E402

FAILS = []
COUNT = 0


def check(name, cond, detail=''):
    global COUNT
    COUNT += 1
    detail = str(detail) if detail not in ('', None) else ''
    suffix = ('  [' + detail + ']') if detail else ''
    if cond:
        print('ok    ' + name + suffix)
    else:
        FAILS.append(name + suffix)
        print('FAIL  ' + name + suffix)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


GIB = 1024 ** 3

# ---- the two terms, separately --------------------------------------------
r = ar.ring_allreduce(8, 4 * GIB, 400, alpha_us=5.0)
check('14 steps for an 8-rank ring', r['steps'] == 14, r['steps'])
check('latency term is 2(n-1)*alpha', abs(r['latency_s'] - 14 * 5e-6) < 1e-12,
      r['latency_s'])
check('transfer term is 2(n-1)/n * S / B',
      abs(r['transfer_s'] - (14 / 8 * 4 * GIB * 8) / 400e9) < 1e-12,
      r['transfer_s'])
check('total is the sum of the two',
      abs(r['total_s'] - (r['latency_s'] + r['transfer_s'])) < 1e-15)
check('a 4 GiB gradient is bandwidth-bound', r['regime'] == 'bandwidth-bound')

small = ar.ring_allreduce(8, 64 * 1024, 400, alpha_us=5.0)
check('a 64 KiB gradient is latency-bound', small['regime'] == 'latency-bound',
      small['regime'])
check('...and its latency share is the majority', small['latency_share'] > 0.5,
      small['latency_share'])

# ---- with alpha = 0 the model reduces to the OLD one ----------------------
# This is the check that pins down exactly what the previous script assumed.
old = ar.ring_allreduce(8, 4 * GIB, 400, alpha_us=0.0)
check('alpha=0 reproduces the old script exactly',
      abs(old['total_s'] - 0.15032385) < 1e-6, old['total_s'])
check('alpha=0 calls everything bandwidth-bound',
      old['regime'] == 'bandwidth-bound' and old['latency_s'] == 0)

# ---- busbw and algbw follow NCCL's definitions -----------------------------
check('busbw = algbw * 2(n-1)/n',
      abs(r['busbw_GBps'] - r['algbw_GBps'] * 14 / 8) < 1e-9)
check('busbw approaches the link rate for a large gradient',
      abs(r['busbw_GBps'] - 50.0) < 0.1, r['busbw_GBps'])
check('a 400 Gb/s link cannot give a busbw in the hundreds of GB/s',
      r['busbw_GBps'] < 60, r['busbw_GBps'])

# ---- the ring runs at the minimum, not the mean ---------------------------
mixed = ar.ring_allreduce(8, 4 * GIB, [400] * 7 + [100])
check('the ring is paced by the slowest link', mixed['slowest_gbps'] == 100)
check('...and not by the mean', abs(mixed['mean_gbps'] - 362.5) < 1e-9,
      mixed['mean_gbps'])
uniform_at_min = ar.ring_allreduce(8, 4 * GIB, 100)
check('one slow link costs the same as every link being slow',
      abs(mixed['total_s'] - uniform_at_min['total_s']) < 1e-12)

# ---- THE CHECK THE OLD SCRIPT WOULD HAVE FAILED ---------------------------
# The penalty must vary with message size. If it does not, the latency term has
# gone missing and the headline is a tautology again.
pens = {s: ar.straggler_penalty(8, s, 400, 100)['ratio']
        for s in (64 * 1024, 1024 * 1024, 64 * 1024 * 1024, 4 * GIB)}
check('the straggler penalty depends on the gradient size',
      len(set(round(v, 3) for v in pens.values())) == len(pens),
      {k: round(v, 3) for k, v in pens.items()})
check('...it rises with the gradient size',
      all(a < b for a, b in zip(list(pens.values()), list(pens.values())[1:])),
      list(pens.values()))
check('...tends to the bandwidth ratio for a huge gradient',
      abs(pens[4 * GIB] - 4.0) < 0.01, pens[4 * GIB])
check('...and is far below it for a small one',
      pens[64 * 1024] < 1.5, pens[64 * 1024])
check('a 4x bandwidth cut is NOT a 4x slowdown at every size',
      pens[64 * 1024] < 3.0)

# the penalty can never exceed the bandwidth ratio, at any size
for s in (1024, 4096, 1 << 20, 1 << 30, 1 << 33):
    p = ar.straggler_penalty(8, s, 400, 100)
    check('penalty stays within the bandwidth ratio at %d B' % s,
          1.0 <= p['ratio'] <= p['bandwidth_ratio'] + 1e-9,
          (p['ratio'], p['bandwidth_ratio']))

# with alpha = 0 it collapses back to the bandwidth ratio at every size --
# which is precisely the old script's behaviour, now visible as a special case
flat = [ar.straggler_penalty(8, s, 400, 100, alpha_us=0.0)['ratio']
        for s in (1024, 1 << 20, 1 << 30)]
check('with no per-step cost the penalty is 4x at every size --- the old bug',
      all(abs(v - 4.0) < 1e-9 for v in flat), flat)

# ---- crossover -------------------------------------------------------------
x = ar.crossover_bytes(8, 400, 5.0)
at = ar.ring_allreduce(8, int(x), 400, 5.0)
check('at the crossover the two terms are equal',
      abs(at['latency_s'] - at['transfer_s']) / at['latency_s'] < 1e-6,
      (at['latency_s'], at['transfer_s']))
check('the crossover scales with alpha',
      abs(ar.crossover_bytes(8, 400, 10.0) - 2 * x) < 1e-6)
check('the crossover scales with bandwidth',
      abs(ar.crossover_bytes(8, 800, 5.0) - 2 * x) < 1e-6)
check('the crossover scales with rank count',
      abs(ar.crossover_bytes(16, 400, 5.0) - 2 * x) < 1e-6)

# ---- the scale-up / back-end separation ------------------------------------
nd = ar.node_budgets(gpus=8, nic_gbps=400, nvlink_GBps_bidir=900)
check('400 Gb/s is 50 GB/s in one direction',
      abs(nd['backend_per_gpu_GBps'] - 50.0) < 1e-9)
check('a bidirectional figure is halved for one direction',
      abs(nd['nvlink_per_gpu_unidir_GBps'] - 450.0) < 1e-9)
check('the scale-up path is 9x the back-end path per GPU',
      abs(nd['ratio_unidir'] - 9.0) < 1e-9, nd['ratio_unidir'])
check('a whole 8-GPU node aggregates 400 GB/s onto the fabric',
      abs(nd['backend_node_aggregate_GBps'] - 400.0) < 1e-9)
# the specific claim the chapter used to make
check('350 GB/s per GPU is impossible on a 400 Gb/s NIC',
      350.0 > nd['backend_per_gpu_GBps'] * 6)
check('...and is within reach of the scale-up path',
      350.0 < nd['nvlink_per_gpu_unidir_GBps'])

# ---- rejection -------------------------------------------------------------
for args, word in (
        ((1, 1024, 400), 'at least 2'),
        ((8, 0, 400), 'positive'),
        ((8, -1, 400), 'positive'),
        ((8, 1024, 0), 'positive'),
        ((8, 1024, [400] * 7), '8 links'),
        ((8, 1024, [400] * 7 + [0]), 'positive'),
        ((8.5, 1024, 400), 'at least 2')):
    try:
        ar.ring_allreduce(*args)
        check('rejects %r' % (args,), False, 'no exception')
    except ar.ModelError as e:
        check('rejects %r' % (args,), word in str(e), str(e)[:60])

try:
    ar.ring_allreduce(8, 1024, 400, alpha_us=-1)
    check('rejects a negative alpha', False, 'no exception')
except ar.ModelError as e:
    check('rejects a negative alpha', 'negative' in str(e))

try:
    ar.straggler_penalty(8, 1024, 100, 400)
    check('rejects a straggler faster than the rest', False, 'no exception')
except ar.ModelError as e:
    check('rejects a straggler faster than the rest', 'faster' in str(e))

# ---- the report says what it is and is not --------------------------------
_r, out = quiet(ar.report, ar.analyse())
low = ' '.join(out.lower().split())
check('the report refuses a single slowdown number',
      'quote the slowdown with the message size' in low)
check('the report names the regime of every row',
      out.count('latency-bound') >= 1 and out.count('bandwidth-bound') >= 1)
check('the report separates scale-up from back-end',
      'scale-up' in low and 'back-end' in low)
check('the report scopes the budget to its one-NIC inter-node ring',
      'one-nic-per-rank pure inter-node ring' in low and 'measurement boundary' in low)
rc, _o = quiet(ar.main, [])
check('the script exits 0', rc == 0, rc)
rc2, _o = quiet(ar.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
