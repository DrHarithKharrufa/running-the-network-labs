#!/usr/bin/env python3
"""Lab 41.1 --- what a ring all-reduce actually costs, and when the straggler rules.

WHY THIS VERSION EXISTS
-----------------------
The previous script computed the step time as

    data_bits / min(link_bandwidths)

and then announced that a link at a quarter of line rate made the collective
"4x slower".  It could not have announced anything else.  Dividing a constant by
the minimum is a definition, not a result: the answer was already in the formula
before any fabric was described.  It also had no latency term, so it reported
every gradient size as bandwidth-bound --- including sizes where the fabric
spends almost all its time on per-step overhead and the link rate barely
matters.

This version keeps both terms of the standard cost model and lets them compete.
The straggler still dominates, but only where it really does, and the script
says which regime each answer came from.

THE MODEL
---------
Ring all-reduce over N ranks is 2(N-1) sequential steps: N-1 reduce-scatter
steps and N-1 all-gather steps.  Each step ships one chunk of S/N bytes over
every link at once.  So

    T  =  2(N-1) * alpha  +  (2(N-1)/N) * S / B

  alpha : per-step cost --- link latency, the library's own overhead, and the
          synchronisation at each step.  Paid 2(N-1) times whatever S is.
  S     : gradient bytes.
  B     : usable bytes/s of the slowest link on the ring. Every step waits for
          every link, so the ring runs at its minimum, not its mean.

This is the classic alpha-beta cost model applied to the ring algorithm.  It is
arithmetic about an idealised ring.  It is NOT a measurement, NOT NCCL, and NOT
a prediction of any real cluster: no congestion, no ECMP collisions, no PFC, no
tree or hierarchical algorithm, no NVLink/network hybrid, no compute overlap.

    python3 allreduce.py
    python3 allreduce.py --json
    python3 test_allreduce.py

Nothing here touches a GPU, a NIC, a switch or a fabric.
"""
import argparse
import json
import sys

GIB = 1024 ** 3


class ModelError(ValueError):
    """The inputs do not describe a ring that can be costed."""


# --------------------------------------------------------------------------
# the cost model
# --------------------------------------------------------------------------
def ring_allreduce(n, grad_bytes, link_gbps, alpha_us=5.0):
    """Cost one ring all-reduce.

    n           number of ranks in the ring (>= 2)
    grad_bytes  gradient size per rank, bytes
    link_gbps   either one bandwidth for every link, or a list of per-link
                bandwidths in Gb/s.  The ring runs at the MINIMUM.
    alpha_us    per-step overhead in microseconds, paid 2(n-1) times

    Returns a dict with the two terms kept separate, because which one
    dominates is the whole point.
    """
    if not isinstance(n, int) or n < 2:
        raise ModelError('a ring needs at least 2 ranks, got %r' % (n,))
    if grad_bytes <= 0:
        raise ModelError('gradient size must be positive, got %r' % (grad_bytes,))
    links = [link_gbps] * n if isinstance(link_gbps, (int, float)) else list(link_gbps)
    if len(links) != n:
        raise ModelError('a ring of %d ranks has %d links, got %d'
                         % (n, n, len(links)))
    if any(b <= 0 for b in links):
        raise ModelError('every link bandwidth must be positive, got %r' % (links,))
    if alpha_us < 0:
        raise ModelError('alpha must not be negative, got %r' % (alpha_us,))

    steps = 2 * (n - 1)
    slowest = min(links)
    latency_s = steps * alpha_us * 1e-6
    # bytes crossing each link in total = (2(n-1)/n) * S
    bytes_per_link = steps / n * grad_bytes
    transfer_s = bytes_per_link * 8 / (slowest * 1e9)
    total_s = latency_s + transfer_s

    return {
        'ranks': n,
        'grad_bytes': grad_bytes,
        'steps': steps,
        'slowest_gbps': slowest,
        'mean_gbps': sum(links) / len(links),
        'alpha_us': alpha_us,
        'latency_s': latency_s,
        'transfer_s': transfer_s,
        'total_s': total_s,
        'latency_share': latency_s / total_s,
        # NCCL's two bandwidth conventions, so the numbers here can be compared
        # with what a real nccl-tests run would print.
        'algbw_GBps': grad_bytes / total_s / 1e9,
        'busbw_GBps': grad_bytes / total_s / 1e9 * steps / n,
        'regime': 'latency-bound' if latency_s > transfer_s else 'bandwidth-bound',
    }


def crossover_bytes(n, link_gbps, alpha_us=5.0):
    """The gradient size at which the two terms are equal.

    Below it the collective is latency-bound and the link rate hardly matters;
    above it the link rate is nearly the whole answer.  Setting

        2(n-1)*alpha  =  (2(n-1)/n) * S * 8 / B

    Here B is bits/s (unlike the module equation in bytes/s).
    The step count cancels, leaving S = alpha * B * n / 8.
    """
    if not isinstance(n, int) or n < 2:
        raise ModelError('a ring needs at least 2 ranks, got %r' % (n,))
    if link_gbps <= 0:
        raise ModelError('bandwidth must be positive, got %r' % (link_gbps,))
    return alpha_us * 1e-6 * link_gbps * 1e9 * n / 8


def straggler_penalty(n, grad_bytes, fast_gbps, slow_gbps, alpha_us=5.0):
    """How much one slow link costs, as a ratio, at this gradient size.

    The ratio is NOT simply fast/slow.  The latency term is untouched by the
    slow link, so it dilutes the penalty --- completely, for a small enough
    gradient.  That is the honest form of "the straggler rules the collective".
    """
    if slow_gbps > fast_gbps:
        raise ModelError('the straggler must not be faster than the rest')
    healthy = ring_allreduce(n, grad_bytes, fast_gbps, alpha_us)
    links = [fast_gbps] * (n - 1) + [slow_gbps]
    degraded = ring_allreduce(n, grad_bytes, links, alpha_us)
    return {
        'healthy_s': healthy['total_s'],
        'degraded_s': degraded['total_s'],
        'ratio': degraded['total_s'] / healthy['total_s'],
        'bandwidth_ratio': fast_gbps / slow_gbps,
        'regime': healthy['regime'],
        # what the previous version of this script would have said
        'naive_ratio': fast_gbps / slow_gbps,
    }


# --------------------------------------------------------------------------
# the scale-up / back-end separation
# --------------------------------------------------------------------------
def node_budgets(gpus=8, nic_gbps=400, nvlink_GBps_bidir=900):
    """Two bandwidth budgets for one GPU server, kept apart on purpose.

    Chapter 41 warns that conflating the scale-up network with the back-end
    network is the commonest sizing mistake.  This function exists so the
    chapter can show the size of the gap rather than assert it.

    nvlink_GBps_bidir is the per-GPU figure vendors quote, which is the sum of
    both directions; halve it for one direction.
    """
    if gpus < 1 or nic_gbps <= 0 or nvlink_GBps_bidir <= 0:
        raise ModelError('gpus, nic_gbps and nvlink must all be positive')
    per_gpu_net_GBps = nic_gbps / 8.0          # Gb/s -> GB/s, decimal GB
    return {
        'gpus': gpus,
        'nic_gbps': nic_gbps,
        # back-end: what one GPU's NIC can move off the node, one direction
        'backend_per_gpu_GBps': per_gpu_net_GBps,
        'backend_node_aggregate_GBps': per_gpu_net_GBps * gpus,
        # scale-up: what one GPU can move inside the node, one direction
        'nvlink_per_gpu_bidir_GBps': nvlink_GBps_bidir,
        'nvlink_per_gpu_unidir_GBps': nvlink_GBps_bidir / 2.0,
        'ratio_unidir': (nvlink_GBps_bidir / 2.0) / per_gpu_net_GBps,
    }


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------
def analyse(n=8, alpha_us=5.0, fast=400, slow=100):
    sizes = [256 * 1024, 4 * 1024 * 1024, 64 * 1024 * 1024, GIB, 4 * GIB]
    rows = [ring_allreduce(n, s, fast, alpha_us) for s in sizes]
    penalties = [straggler_penalty(n, s, fast, slow, alpha_us) for s in sizes]
    return {
        'ranks': n,
        'alpha_us': alpha_us,
        'fast_gbps': fast,
        'slow_gbps': slow,
        'crossover_bytes': crossover_bytes(n, fast, alpha_us),
        'rows': rows,
        'penalties': penalties,
        'node': node_budgets(),
    }


def human(b):
    for unit, div in (('GiB', GIB), ('MiB', 1024 ** 2), ('KiB', 1024)):
        if b >= div:
            return '%g %s' % (b / div, unit)
    return '%d B' % b


def report(a):
    print('Ring all-reduce, %d ranks, alpha = %g us per step, %d steps'
          % (a['ranks'], a['alpha_us'], 2 * (a['ranks'] - 1)))
    print('All links %d Gb/s unless stated. Arithmetic only: no GPU, no NIC, '
          'no fabric.\n' % a['fast_gbps'])

    print('%10s | %9s | %9s | %9s | %7s | %s'
          % ('gradient', 'latency', 'transfer', 'total', 'busbw', 'regime'))
    print('-' * 74)
    for r in a['rows']:
        print('%10s | %7.3f ms | %7.3f ms | %7.3f ms | %5.1f GB/s | %s'
              % (human(r['grad_bytes']), r['latency_s'] * 1e3,
                 r['transfer_s'] * 1e3, r['total_s'] * 1e3,
                 r['busbw_GBps'], r['regime']))

    print('\nThe two terms are equal at a gradient of %s. That is the only'
          % human(a['crossover_bytes']))
    print('place "all-reduce is bandwidth-bound" starts being true for this ring.')

    print('\nNow degrade ONE link from %d to %d Gb/s --- a %gx bandwidth cut:\n'
          % (a['fast_gbps'], a['slow_gbps'],
             a['fast_gbps'] / a['slow_gbps']))
    print('%10s | %9s | %9s | %8s | %s'
          % ('gradient', 'healthy', 'degraded', 'slowdown', 'regime'))
    print('-' * 68)
    for p, r in zip(a['penalties'], a['rows']):
        print('%10s | %7.3f ms | %7.3f ms | %6.2fx | %s'
              % (human(r['grad_bytes']), p['healthy_s'] * 1e3,
                 p['degraded_s'] * 1e3, p['ratio'], p['regime']))

    worst = max(p['ratio'] for p in a['penalties'])
    best = min(p['ratio'] for p in a['penalties'])
    print('\nThe SAME slow link costs %.2fx at one gradient size and %.2fx at'
          % (worst, best))
    print('another. A bandwidth cut is a bandwidth problem only once the')
    print('collective is bandwidth-bound; below the crossover the per-step')
    print('overhead is paying for the collective and the slow link barely shows.')
    print('Quote the slowdown WITH the message size, or you have quoted nothing.')

    nd = a['node']
    print('\nScale-up and back-end are different budgets, not one number:')
    print('  one GPU onto the back-end fabric : %6.1f GB/s  (%d Gb/s NIC, one direction)'
          % (nd['backend_per_gpu_GBps'], nd['nic_gbps']))
    print('  one GPU over the scale-up fabric : %6.1f GB/s  (%g GB/s bidirectional, halved)'
          % (nd['nvlink_per_gpu_unidir_GBps'], nd['nvlink_per_gpu_bidir_GBps']))
    print('  the scale-up path is %.0fx the back-end path per GPU.'
          % nd['ratio_unidir'])
    print('  Under this one-NIC-per-rank pure inter-node ring model, a rate')
    print('  beyond the NIC budget needs a different measurement boundary.')
    print('  Check scale-up, multiple NICs, aggregation and bandwidth normalisation.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--ranks', type=int, default=8)
    ap.add_argument('--alpha-us', type=float, default=5.0)
    ap.add_argument('--fast', type=float, default=400)
    ap.add_argument('--slow', type=float, default=100)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        a = analyse(args.ranks, args.alpha_us, args.fast, args.slow)
    except ModelError as e:
        print('model error: %s' % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(a, indent=2))
    else:
        report(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
