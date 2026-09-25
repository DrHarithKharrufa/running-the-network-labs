#!/usr/bin/env python3
"""Lab 64.1 --- what bisection actually buys, and what it needs to buy it.

THIS LAB WAS REPAIRED, NOT WITHDRAWN. As it first shipped it compared three
strategies and drew a conclusion the comparison could not support:

  * IT GAVE THE STRATEGIES DIFFERENT ORACLES. Bisection was asked "is the fault
    in this half?" --- an ordering question about a whole region --- while the
    linear scan and the guesser were asked "is the fault at exactly this
    position?". Most of the gap it reported comes from that difference, not
    from one strategy being tidier than another.
  * IT SAID GUESSING "DOES NOT CONVERGE AT ALL". Random probing with
    replacement has a finite expected cost of N trials and succeeds almost
    surely; it is inefficient, not non-convergent. Guessing WITHOUT replacement
    --- that is, remembering your misses --- costs (N+1)/2, exactly the same as
    a linear scan.
  * AND IT SAID NOTHING ABOUT WHAT BISECTION REQUIRES. Halving works on a
    single fault, in an ordered space, with a test you can run at an arbitrary
    midpoint, answered by a reliable oracle. Networks break all four.

Its purpose and entry point are unchanged, because the advice --- be systematic
--- is right. What changed is the argument, and the argument now includes the
case where bisection quietly returns the wrong answer.

    python3 bisect_vs_guess.py
    python3 bisect_vs_guess.py --demo-original
    python3 test_bisect.py

Offline calculation in closed form, with one seeded simulation used only to
cross-check a closed form. No network was probed.
"""
import math
import random
import sys

SEED = 64


class SearchError(ValueError):
    """Raised when a search question cannot be answered as posed."""


def _n(n):
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise SearchError('the search space must be a positive whole number '
                          'of positions')
    return n


# ---------------------------------------------------------------------------
# The two oracles, named, because the comparison is meaningless without them
# ---------------------------------------------------------------------------

ORACLES = {
    'position': ('"is the fault at exactly this position?" --- one probe tells '
                 'you about one hop, which is what a single device check does'),
    'region': ('"is the fault at or before this position?" --- one probe tells '
               'you about a whole region, which is what an end-to-end test from '
               'a midpoint does'),
}


def linear_scan(n):
    """Position oracle, checked in order. Average over all fault positions."""
    n = _n(n)
    return dict(strategy='linear scan', oracle='position',
                expected_probes=(n + 1) / 2.0, worst_case=n,
                note='Every probe eliminates exactly one position.')


def random_without_replacement(n):
    """Position oracle, remembering misses. Identical to a linear scan."""
    n = _n(n)
    return dict(strategy='random probing, misses remembered', oracle='position',
                expected_probes=(n + 1) / 2.0, worst_case=n,
                note=('The same cost as scanning in order: what matters is that '
                      'a miss removes a position, not which position you chose.'))


def random_with_replacement(n):
    """Position oracle, forgetting misses. Geometric, mean N. Finite."""
    n = _n(n)
    return dict(strategy='random probing, misses forgotten', oracle='position',
                expected_probes=float(n), worst_case=None,
                p_still_searching_after=lambda k: (1 - 1.0 / n) ** k,
                note=('Expected N probes and success with probability one '
                      'eventually. Inefficient, NOT non-convergent --- the '
                      'original lab said otherwise.'))


def bisection(n):
    """Region oracle. Exactly the number of halvings, averaged over positions."""
    n = _n(n)
    total = 0
    for target in range(n):
        lo, hi, probes = 0, n - 1, 0
        while lo < hi:
            mid = (lo + hi) // 2
            probes += 1
            if target <= mid:
                hi = mid
            else:
                lo = mid + 1
        total += probes
    return dict(strategy='bisection', oracle='region',
                expected_probes=total / float(n),
                worst_case=int(math.ceil(math.log2(n))) if n > 1 else 0,
                note=('Each probe removes half the remaining region, which is '
                      'possible only because the oracle answers about a region.'))


def scan_with_region_oracle(n):
    """A linear scan given bisection's oracle, to isolate what the oracle buys.

    Walk outward testing "is the fault at or before here?" and stop at the first
    yes. Same oracle as bisection, same guarantee, no halving --- so whatever
    separates this from bisection is the STRATEGY, and whatever separates it
    from the position-oracle rows is the ORACLE.
    """
    n = _n(n)
    return dict(strategy='scan, region oracle', oracle='region',
                expected_probes=(n + 1) / 2.0, worst_case=n,
                note=('The oracle alone does not help if you do not halve: this '
                      'costs the same as a position-oracle scan. Bisection needs '
                      'both the oracle and the halving.'))


def comparison(n):
    return [linear_scan(n), random_without_replacement(n),
            random_with_replacement(n), scan_with_region_oracle(n),
            bisection(n)]


def simulate_random_with_replacement(n, trials=20000, seed=SEED):
    """Seeded cross-check that the geometric mean really is N."""
    n = _n(n)
    rng = random.Random(seed)
    total = 0
    for _ in range(trials):
        target = rng.randrange(n)
        probes = 1
        while rng.randrange(n) != target:
            probes += 1
        total += probes
    return total / float(trials)


# ---------------------------------------------------------------------------
# What bisection requires, and what happens when it does not hold
# ---------------------------------------------------------------------------

PRECONDITIONS = (
    ('a single fault',
     'Two faults on one path make the region oracle report the FIRST one. '
     'Bisection is still sound about that one and silent about the rest, which '
     'is why the method has a verify step.'),
    ('an ordered space',
     'Halving needs "before" and "after" to mean something. Equal-cost paths, '
     'asymmetric return routing and overlays give a set of candidates with no '
     'order, and there is nothing to halve.'),
    ('a testable midpoint',
     'You must be able to run the test AT the midpoint. Where you have no '
     'access --- a provider core, a customer LAN --- the midpoint you can reach '
     'is not the one that splits the space.'),
    ('a reliable oracle',
     'Each answer is acted on irreversibly. An intermittent fault, a rate-'
     'limited ICMP responder or a policy that drops probes but not traffic '
     'makes the answer wrong sometimes, and the search commits anyway.'),
)


def unreliable_bisection(n, error_rate, repeats=1):
    """Probability a naive bisection lands on the right position.

    Every answer is acted on and never revisited, so one wrong answer sends the
    search into the wrong half and it never comes back. With d halvings and a
    per-answer error rate q, the chance of being right is (1-q)^d --- and the
    search reports an answer with exactly the same confidence either way.
    """
    n = _n(n)
    if not 0 <= error_rate < 0.5:
        raise SearchError('a probe that is wrong half the time or more carries '
                          'no information; state an error rate below 0.5')
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 1 \
            or repeats % 2 == 0:
        raise SearchError('repeats must be an odd positive number, so that a '
                          'majority exists')
    depth = int(math.ceil(math.log2(n))) if n > 1 else 0
    q = majority_error(error_rate, repeats)
    return dict(positions=n, depth=depth, per_probe_error=error_rate,
                repeats=repeats, effective_error=q,
                p_correct=(1 - q) ** depth,
                probes=depth * repeats,
                note=('The search returns a position whether or not it is the '
                      'right one, and nothing in its output distinguishes the '
                      'two. Confidence has to come from repeating the probes or '
                      'from verifying the fix, not from the search.'))


def majority_error(q, k):
    """Chance a best-of-k vote is wrong when each probe is wrong with prob q."""
    if not 0 <= q < 0.5:
        raise SearchError('per-probe error must be below 0.5')
    if k % 2 == 0 or k < 1:
        raise SearchError('k must be odd and positive')
    need = k // 2 + 1
    return sum(math.comb(k, i) * q ** i * (1 - q) ** (k - i)
               for i in range(need, k + 1))


def two_faults(n, first, second):
    """What a region oracle reports when the path has two faults.

    The oracle answers about reachability, so it reports the first break. The
    search is correct about that one and carries no information about the
    second, and the operator who fixes it and stops has restored nothing.
    """
    n = _n(n)
    for name, v in (('first', first), ('second', second)):
        if not 0 <= v < n:
            raise SearchError('%s fault must be a position inside the path' % name)
    if first >= second:
        raise SearchError('give the faults in order; the point is what happens '
                          'to the one further along')
    lo, hi, probes = 0, n - 1, 0
    while lo < hi:
        mid = (lo + hi) // 2
        probes += 1
        if first <= mid:
            hi = mid
        else:
            lo = mid + 1
    return dict(positions=n, faults=(first, second), found=lo, probes=probes,
                found_the_first=lo == first,
                second_still_present=True,
                note=('Bisection converged, correctly, on the first fault and '
                      'said nothing at all about the second. The symptom will '
                      'survive the fix, and the only step that catches it is '
                      'verifying against the original definition.'))


def ping_proves_what(members=8, broken=1):
    """A successful probe does not prove the application path is healthy.

    A single test traverses one path. With equal-cost members chosen by a hash
    of the flow's own fields, a probe and the application take different paths
    whenever their five-tuples differ --- which is always.
    """
    if members < 1 or not 0 <= broken <= members:
        raise SearchError('members must be positive and broken within them')
    p_probe_hits = broken / float(members)
    return dict(members=members, broken=broken,
                p_one_probe_traverses_a_broken_member=p_probe_hits,
                p_probe_looks_healthy=1 - p_probe_hits,
                probes_for_90_percent_confidence=(
                    None if broken == 0 else
                    1 if broken == members else
                    math.ceil(math.log(0.10) / math.log(1 - p_probe_hits))),
                note=('And this counts only path selection. The probe may also '
                      'differ in size, in DSCP, in protocol and in port, each of '
                      'which can select a different queue, policy or MTU '
                      'behaviour. A successful ICMP echo is evidence about ICMP '
                      'echo.'))


def quiet_interval_proves_what(rate_per_day, watched_days, prior_fixed=0.5):
    """The same question in the time domain: how long must silence last?

    An intermittent fault that has not recurred is unobserved, not fixed. If it
    arrives at a steady rate when it is still there, the chance of a quiet
    stretch that long by luck alone is exp(-rate * days) --- which never
    reaches zero, so no finite quiet interval proves absence. What it does do
    is put a number on your confidence, and the number is set by the fault's
    own rate, the stated repair prior, perfect observation and the assumption
    that a repaired fault cannot recur. This is conditional model evidence,
    not a calibrated probability for an arbitrary live incident.
    """
    if rate_per_day <= 0:
        raise SearchError('a fault that never happens has no interval to '
                          'wait out; state the rate you actually observed')
    if watched_days < 0:
        raise SearchError('you cannot watch for a negative time')
    if not 0 < prior_fixed < 1:
        raise SearchError('the prior that the fix worked must lie strictly '
                          'between 0 and 1; certainty either way needs no '
                          'observation')
    p_quiet_if_broken = math.exp(-rate_per_day * watched_days)
    denominator = prior_fixed + (1 - prior_fixed) * p_quiet_if_broken
    posterior = prior_fixed / denominator
    # The quantity that carries the argument is the doubt that is left, and it
    # is exactly the one a double cannot hold: past about ninety days against a
    # twice-daily fault the confidence rounds to 1.0 and the lab would print
    # the opposite of what it is here to say. So the doubt is carried in logs,
    # where it stays finite for as long as anyone could watch.
    log10_residual_doubt = (math.log10(1 - prior_fixed)
                            - rate_per_day * watched_days / math.log(10.0)
                            - math.log10(denominator))
    return dict(rate_per_day=rate_per_day, watched_days=watched_days,
                prior_fixed=prior_fixed,
                p_quiet_if_still_broken=p_quiet_if_broken,
                p_fixed_given_quiet=posterior,
                log10_residual_doubt=log10_residual_doubt,
                saturated=posterior >= 1.0,
                note=('Silence is evidence, weighted by how surprising that '
                      'much silence would be. It is never proof: the doubt '
                      'shrinks without bound and never reaches zero, which is '
                      'why it is reported in logs once a double can no longer '
                      'hold it.'))


def days_to_confidence(rate_per_day, confidence=0.95, prior_fixed=0.5):
    """How long you must watch to reach a stated confidence. Inverts the above."""
    if not 0 < confidence < 1:
        raise SearchError('confidence must lie strictly between 0 and 1')
    if not 0 < prior_fixed < 1:
        raise SearchError('the prior must lie strictly between 0 and 1')
    if confidence <= prior_fixed:
        return 0.0
    if rate_per_day <= 0:
        raise SearchError('state the rate you actually observed')
    target = (prior_fixed * (1 - confidence)) / (confidence * (1 - prior_fixed))
    return -math.log(target) / rate_per_day


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

def prove_the_claims():
    """FR-0052 inside the lab: every claim the report prints is checked first."""
    n = 1024
    rows = {r['strategy']: r for r in comparison(n)}
    if rows['linear scan']['expected_probes'] \
            != rows['random probing, misses remembered']['expected_probes']:
        raise SearchError('scanning and remembering misses should cost the same')
    if rows['scan, region oracle']['expected_probes'] \
            != rows['linear scan']['expected_probes']:
        raise SearchError('the region oracle alone should not help a scan')
    if rows['random probing, misses forgotten']['expected_probes'] != float(n):
        raise SearchError('guessing with replacement should cost N in expectation')
    if abs(rows['bisection']['expected_probes'] - math.log2(n)) > 1e-9:
        raise SearchError('bisection on a power of two should cost log2 N')
    observed = simulate_random_with_replacement(64, 20000)
    if abs(observed - 64) > 64 * 0.05:
        raise SearchError('the simulated guessing cost left five per cent of '
                          'the closed form (%.2f against 64)' % observed)
    naive = unreliable_bisection(1024, 0.10)
    if not 0.30 < naive['p_correct'] < 0.40:
        raise SearchError('a ten per cent probe error should leave about a '
                          'third correct, got %.3f' % naive['p_correct'])
    better = unreliable_bisection(1024, 0.10, repeats=3)
    if not better['p_correct'] > naive['p_correct']:
        raise SearchError('repeating the probes did not help')
    tf = two_faults(1024, 100, 700)
    if not tf['found_the_first'] or tf['found'] == 700:
        raise SearchError('bisection should find the first fault and miss the '
                          'second')
    twice_a_day = quiet_interval_proves_what(2.0, 3.0)
    if not 0.99 < twice_a_day['p_fixed_given_quiet'] < 1.0:
        raise SearchError('three quiet days against a twice-daily fault should '
                          'be strong but not conclusive, got %.4f'
                          % twice_a_day['p_fixed_given_quiet'])
    for days in (3.0, 90.0, 3650.0):
        far = quiet_interval_proves_what(2.0, days)
        if not math.isfinite(far['log10_residual_doubt']):
            raise SearchError('the residual doubt after %g days came out as '
                              'zero, which is the claim this lab exists to '
                              'refute' % days)
    rare = days_to_confidence(2.0 / 365.0)
    common = days_to_confidence(2.0)
    if not rare > 100 * common:
        raise SearchError('a rarer fault must demand a longer watch; got '
                          '%.2f days against %.2f' % (rare, common))
    pp = ping_proves_what(8, 1)
    if abs(pp['p_probe_looks_healthy'] - 0.875) > 1e-12:
        raise SearchError('a single probe over eight members with one broken '
                          'should look healthy seven times in eight')
    return dict(oracle_isolated=True, guessing_converges=True,
                bisection_is_log2=True, simulation_matches=True,
                unreliable_oracle_degrades=True, repeats_help=True,
                second_fault_missed=True, probe_is_not_proof=True,
                silence_is_not_proof=True, watch_scales_with_rarity=True)


def demo_original():
    """What this lab computed as originally shipped, and why it was wrong."""
    n = 1024
    return dict(
        printed=dict(linear=(n + 1) / 2.0, bisection=math.log2(n),
                     random='reported as non-convergent'),
        defects=(
            'The three rows were not comparable: bisection answered a question '
            'about a region and the other two about a position. Given the same '
            'position oracle, a linear scan and a remembered-miss guesser both '
            'cost (N+1)/2 = %.1f, and a forgotten-miss guesser costs N = %d in '
            'expectation --- finite, and almost surely successful. "Does not '
            'converge at all" was the modelling choice of never remembering a '
            'miss, presented as a property of guessing.'
            % ((n + 1) / 2.0, n)))


def _odds(log10_probability):
    """Render a probability as 1-in-N, in logs, so nothing rounds to certainty."""
    magnitude = -log10_probability
    if magnitude < 15:
        return format(int(round(10 ** magnitude)), ',')
    return '10^%d' % int(round(magnitude))


def _wrap(text, indent, width=78):
    words, lines, cur = text.split(), [], ''
    for word in words:
        if cur and len(cur) + len(word) + 1 > width - indent:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + ' ' + word).strip()
    lines.append(cur)
    return ('\n' + ' ' * indent).join(lines)


def report(out=None, original=False):
    out = sys.stdout if out is None else out
    proof = prove_the_claims()
    out.write('Lab 64.1 --- what bisection buys, and what it needs to buy it\n')
    out.write('=' * 74 + '\n')
    out.write('claims checked before printing: %d\n\n' % len(proof))

    if original:
        d = demo_original()
        out.write('WHAT THIS LAB PRINTED AS ORIGINALLY SHIPPED\n\n')
        out.write('  path of 1024 hops: linear %.1f, bisection %.1f, random %s\n\n'
                  % (d['printed']['linear'], d['printed']['bisection'],
                     d['printed']['random']))
        out.write('  %s\n\n' % _wrap(d['defects'], 2))

    out.write('THE ORACLE IS HALF THE ANSWER, SO NAME IT\n\n')
    for name, text in ORACLES.items():
        out.write('  %-10s %s\n' % (name, _wrap(text, 13)))
    out.write('\n  %-38s %-10s %12s\n' % ('strategy', 'oracle', 'probes (1024)'))
    for row in comparison(1024):
        out.write('  %-38s %-10s %12.1f\n'
                  % (row['strategy'], row['oracle'], row['expected_probes']))
    out.write('\n  %s\n\n' % _wrap(
        'Read it as two comparisons rather than one. Among the position-oracle '
        'rows, remembering your misses is worth a factor of two and nothing '
        'more --- 512.5 probes against 1024 --- which is the real cost of '
        'guessing, not an infinity. Between the two region-oracle rows, the '
        'oracle alone buys nothing: a scan costs the same 512.5. Bisection is '
        'cheap because it has BOTH a region oracle and the halving, and on a '
        'network the region oracle is the part you may not have.', 2))
    sim = simulate_random_with_replacement(64, 20000)
    out.write('  %s\n\n' % _wrap(
        'Cross-checked by simulation: 20,000 seeded trials of guessing with '
        'replacement over 64 positions averaged %.2f probes against a closed '
        'form of 64.' % sim, 2))

    out.write('WHAT BISECTION REQUIRES\n\n')
    for name, why in PRECONDITIONS:
        out.write('  %s\n    %s\n\n' % (name, _wrap(why, 4)))

    out.write('AN UNRELIABLE ORACLE, WHICH IS THE ORDINARY CASE\n\n')
    out.write('  %-28s %10s %10s %10s\n'
              % ('per-probe error', 'repeats', 'probes', 'correct'))
    for q, k in ((0.00, 1), (0.05, 1), (0.10, 1), (0.20, 1),
                 (0.10, 3), (0.10, 5), (0.20, 5)):
        u = unreliable_bisection(1024, q, k)
        out.write('  %-28s %10d %10d %9.1f%%\n'
                  % ('%.0f%%' % (100 * q), k, u['probes'],
                     100 * u['p_correct']))
    naive = unreliable_bisection(1024, 0.10)
    three = unreliable_bisection(1024, 0.10, 3)
    out.write('\n  %s\n\n' % _wrap(
        'A probe that is wrong one time in ten leaves a ten-deep bisection '
        'correct %.1f per cent of the time --- and it returns an answer with '
        'the same confident air either way. Best of three takes it to %.1f per '
        'cent for %d probes instead of %d. This is the arithmetic behind not '
        'trusting a single failed ping: the fix is more probes or a different '
        'test, and the step that catches it regardless is verifying against the '
        'original symptom.'
        % (100 * naive['p_correct'], 100 * three['p_correct'],
           three['probes'], naive['probes']), 2))

    tf = two_faults(1024, 100, 700)
    out.write('TWO FAULTS ON ONE PATH\n\n')
    out.write('  faults at %d and %d; bisection returned %d in %d probes\n\n'
              % (tf['faults'][0], tf['faults'][1], tf['found'], tf['probes']))
    out.write('  %s\n\n' % _wrap(tf['note'], 2))

    pp = ping_proves_what(8, 1)
    out.write('AND A SUCCESSFUL PROBE IS EVIDENCE ABOUT THE PROBE\n\n')
    out.write('  %-46s %s\n' % ('equal-cost members', pp['members']))
    out.write('  %-46s %s\n' % ('broken members', pp['broken']))
    out.write('  %-46s %.1f%%\n' % ('chance one probe looks healthy anyway',
                                    100 * pp['p_probe_looks_healthy']))
    out.write('  %-46s %s\n' % ('independent probes for <=10% miss chance',
                                pp['probes_for_90_percent_confidence']))
    out.write('\n  %s\n\n' % _wrap(pp['note'], 2))

    out.write('AND SO IS A SUCCESSFUL SILENCE\n\n')
    out.write('  A fault that has not recurred is unobserved, not fixed. For a\n')
    out.write('  link that flaps about twice a day, starting from an even bet\n')
    out.write('  that the fix worked:\n\n')
    out.write('  %-22s %24s %16s\n'
              % ('quiet for', 'chance of that silence', 'odds it is'))
    out.write('  %-22s %24s %16s\n'
              % ('', 'if it is still broken', 'still broken'))
    for days in (0.5, 1.0, 3.0, 7.0):
        r = quiet_interval_proves_what(2.0, days)
        out.write('  %-22s %24s %16s\n'
                  % ('%.1f days' % days,
                     '1 in %s' % format(
                         int(round(1.0 / r['p_quiet_if_still_broken'])), ','),
                     '1 in %s' % _odds(r['log10_residual_doubt'])))
    out.write('\n  %-30s %14s %14s\n'
              % ('fault arrives', 'days to 95%', 'days to 99%'))
    for rate, label in ((2.0, 'twice a day'), (1 / 7.0, 'about weekly'),
                        (1 / 30.0, 'about monthly'),
                        (2 / 365.0, 'twice a year')):
        out.write('  %-30s %14.1f %14.1f\n'
                  % (label, days_to_confidence(rate),
                     days_to_confidence(rate, 0.99)))
    out.write('\n  %s\n' % _wrap(
        'The middle column never reaches zero, so no finite quiet interval '
        'proves absence --- and the watch you owe is set by the fault\'s own '
        'rate, not by your patience. A twice-daily flap is settled in a day '
        'and a half. Something that happens twice a year needs about 537 days '
        'of silence for the same confidence, which is longer than anyone will '
        'wait, so that fault is closed on evidence of the cause rather than on '
        'evidence of the silence. Say which one you have. The right-hand '
        'column is carried in logarithms for a reason: computed the obvious '
        'way it rounds to certainty after about ninety days, and the lab would '
        'print the opposite of what it just said.', 2))


def main(argv):
    report(original='--demo-original' in argv)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
