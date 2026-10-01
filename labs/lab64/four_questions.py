#!/usr/bin/env python3
"""Lab 64.2 --- the four questions, and what their answers are worth.

THIS LAB WAS REPAIRED, NOT WITHDRAWN. The four questions are still the
cheapest thing you can do, and asking them first is still right. What it got
wrong was what it did with the answers: it turned each one into a verdict.

  * IT TREATED "IT NEVER WORKED" AS PROOF OF A CONFIGURATION FAULT. A circuit
    can be delivered dead, a new fibre can be patched to the wrong port, an
    optic can arrive broken. None of those is a configuration error, and all
    of them are commonest precisely on first use.
  * IT TREATED "ONE USER" AS PROOF OF AN EDGE FAULT. An ACL matching one
    address, one broken member of a bundle, an MTU mismatch on one of several
    paths: each is in the core and each can present as a single complaint.
  * IT TREATED CORRELATION WITH A CHANGE AS NAMING THE CAUSE. How much a
    correlation is worth depends on how often you change things, and this lab
    computes that number. Past a certain change rate it is worth almost
    nothing.

So the questionnaire still runs, on the same command line. It now returns
RANKED HYPOTHESES with the weight of each, the thing each answer did NOT rule
out, and the test that would separate the leaders --- because a diagnosis you
cannot distinguish from its rival is not a diagnosis.

    python3 four_questions.py
    python3 four_questions.py --demo-original
    python3 test_four_questions.py

To put YOUR incident through it, pass the answers; you do not have to edit this
file. An unanswered question is answered 'unknown', which updates nothing:

    python3 four_questions.py --case "pump room" --ever-worked yes \
            --scope "one site" --changes-per-day 40
    python3 four_questions.py --help

Offline calculation only. Every prior and likelihood used here is written down
below, is illustrative rather than surveyed, and is swept in sensitivity() so
you can see which conclusions survive changing it. No network was probed.
"""
import math
import sys

UNKNOWN = 'unknown'


class AnswerError(ValueError):
    """Raised when an answer is not one this questionnaire can use."""


# ---------------------------------------------------------------------------
# The candidate causes. Exactly one of them is what actually broke, which is
# what lets these be weighed against each other at all.
# ---------------------------------------------------------------------------

CAUSES = {
    'edge_host':        'the host itself --- its stack, its supplicant, its software',
    'edge_access':      'the patch lead, the wall port, the access switch port',
    'new_media':        'newly installed media --- wrong port, wrong pair, dirty or broken optic',
    'provider':         'the provider circuit or the upstream carrier',
    'config_error':     'a configuration or design error on the path',
    'filter_selective': 'a filter or policy that matches only some traffic',
    'path_partial':     'one broken member of a bundle, or an MTU mismatch on one path',
    'hardware_silent':  'forwarding hardware that drops while the control plane looks right',
    'capacity':         'congestion --- the path works but not at this rate',
    'shared_service':   'a shared service (name resolution, address assignment, authentication)',
}

# Base rates for a reachability complaint arriving at a service desk.
# STATED HERE, NOT SURVEYED. sensitivity() sweeps them.
PRIORS = {
    'edge_host':        0.14,
    'edge_access':      0.12,
    'new_media':        0.05,
    'provider':         0.07,
    'config_error':     0.22,
    'filter_selective': 0.11,
    'path_partial':     0.08,
    'hardware_silent':  0.05,
    'capacity':         0.07,
    'shared_service':   0.09,
}

# P(the symptom is "it has never once worked" | this cause).
# Note new_media and provider: both are HIGHEST on first use, which is the
# whole reason "it never worked" cannot be read as "somebody mistyped".
NEVER_WORKED_GIVEN = {
    'edge_host':        0.30,
    'edge_access':      0.35,
    'new_media':        0.85,
    'provider':         0.55,
    'config_error':     0.60,
    'filter_selective': 0.45,
    'path_partial':     0.20,
    'hardware_silent':  0.10,
    'capacity':         0.05,
    'shared_service':   0.15,
}

# P(exactly one user complains | this cause). filter_selective, path_partial
# and hardware_silent are deliberately NOT zero: that is the second half of
# the finding this lab was repaired for.
ONE_USER_GIVEN = {
    'edge_host':        0.92,
    'edge_access':      0.70,
    'new_media':        0.60,
    'provider':         0.05,
    'config_error':     0.20,
    'filter_selective': 0.30,
    'path_partial':     0.15,
    'hardware_silent':  0.12,
    'capacity':         0.08,
    'shared_service':   0.06,
}

# P(a whole site complains | this cause).
ONE_SITE_GIVEN = {
    'edge_host':        0.01,
    'edge_access':      0.04,
    'new_media':        0.20,
    'provider':         0.80,
    'config_error':     0.35,
    'filter_selective': 0.25,
    'path_partial':     0.30,
    'hardware_silent':  0.30,
    'capacity':         0.35,
    'shared_service':   0.20,
}

# P(everyone, everywhere complains | this cause).
EVERYWHERE_GIVEN = {
    'edge_host':        0.00,
    'edge_access':      0.00,
    'new_media':        0.02,
    'provider':         0.05,
    'config_error':     0.25,
    'filter_selective': 0.25,
    'path_partial':     0.20,
    'hardware_silent':  0.15,
    'capacity':         0.30,
    'shared_service':   0.65,
}

SCOPES = {
    'one user':   ONE_USER_GIVEN,
    'one site':   ONE_SITE_GIVEN,
    'everywhere': EVERYWHERE_GIVEN,
}

# How readily each cause is introduced BY a change, given the fault was
# change-triggered at all. Used only to the extent the correlation is worth
# anything, which change_evidence() computes rather than assumes.
CHANGE_AFFINITY = {
    'edge_host':        0.25,
    'edge_access':      0.20,
    'new_media':        0.55,
    'provider':         0.30,
    'config_error':     0.90,
    'filter_selective': 0.80,
    'path_partial':     0.45,
    'hardware_silent':  0.15,
    'capacity':         0.50,
    'shared_service':   0.60,
}


# ---------------------------------------------------------------------------
# Weighing the answers
# ---------------------------------------------------------------------------

def _normalise(weights):
    total = sum(weights.values())
    if total <= 0:
        raise AnswerError('these answers leave no cause with any weight at '
                          'all, which means the model is wrong, not the fault')
    return {k: v / total for k, v in weights.items()}


def entropy_bits(posterior):
    """How much is still unknown, in bits. Ten equal causes would be 3.32."""
    return -sum(p * math.log2(p) for p in posterior.values() if p > 0)


def rank(posterior, top=None):
    order = sorted(posterior.items(), key=lambda kv: (-kv[1], kv[0]))
    return order if top is None else order[:top]


def weigh(ever_worked=UNKNOWN, scope=UNKNOWN, priors=None):
    """Ranked hypotheses from the two questions that bear on WHERE it broke.

    Every answer may be UNKNOWN, in which case it simply does not update
    anything --- an unanswered question must cost you nothing, not silently
    become an answer.
    """
    priors = dict(priors or PRIORS)
    missing = set(CAUSES) - set(priors)
    if missing:
        raise AnswerError(f'no prior given for: {sorted(missing)}')

    weights = dict(priors)
    asked = []

    if ever_worked is not UNKNOWN and ever_worked != UNKNOWN:
        if not isinstance(ever_worked, bool):
            raise AnswerError("'did it ever work?' takes True, False or "
                              f"UNKNOWN, not {ever_worked!r}")
        asked.append('did it ever work')
        for cause in weights:
            p = NEVER_WORKED_GIVEN[cause]
            weights[cause] *= (1.0 - p) if ever_worked else p

    if scope != UNKNOWN:
        if scope not in SCOPES:
            raise AnswerError(
                f'scope {scope!r} is not one this questionnaire can weigh; '
                f'use one of {sorted(SCOPES)} or UNKNOWN. Guessing a scope is '
                'worse than admitting you have not established one.')
        asked.append('is it one or many')
        table = SCOPES[scope]
        for cause in weights:
            weights[cause] *= table[cause]

    return _normalise(weights), asked


def change_evidence(changes_per_day, window_minutes=15.0,
                    prior_change_caused=0.70):
    """What "it started right after a change" is actually worth.

    If changes arrive at a steady rate and this fault's start time is
    independent of them, the chance that SOME unrelated change lands inside
    the window anyway is 1 - exp(-rate * window). That coincidence rate is the
    denominator of the likelihood ratio. window_minutes is the HALF-width
    of a symmetric +/- window; the total is 2*window_minutes. This is not
    a preceding-only window. The numerator is assumed to be 1 (every truly
    causal change lies within this window); generally use P(E|causal)/P(E|other).
    """
    if not math.isfinite(changes_per_day) or changes_per_day < 0:
        raise AnswerError('a change rate cannot be negative')
    if not math.isfinite(window_minutes) or window_minutes <= 0:
        raise AnswerError('the correlation window must be a positive number '
                          'of minutes')
    if not 0.0 < prior_change_caused < 1.0:
        raise AnswerError('the prior that a fault is change-caused must lie '
                          'strictly between 0 and 1')

    span_days = (2.0 * window_minutes) / 1440.0
    coincidence = 1.0 - math.exp(-changes_per_day * span_days)
    coincidence = min(max(coincidence, 1e-12), 1.0)
    lr = 1.0 / coincidence
    p = prior_change_caused
    posterior = p / (p + (1.0 - p) * coincidence)
    return dict(changes_per_day=changes_per_day,
                window_minutes=window_minutes,
                coincidence=coincidence,
                likelihood_ratio=lr,
                prior_change_caused=p,
                posterior_change_caused=posterior,
                bits=math.log2(lr))


def rate_at_which_correlation_dies(target_lr=2.0, window_minutes=15.0):
    """The change rate above which the correlation is worth less than target_lr.

    Solving 1/(1 - exp(-rate*span)) = target_lr.
    """
    if not math.isfinite(window_minutes) or window_minutes <= 0:
        raise AnswerError("window half-width must be finite and positive")
    if not math.isfinite(target_lr) or target_lr <= 1.0:
        raise AnswerError('a likelihood ratio at or below 1 is not evidence, '
                          'so there is no rate to solve for')
    span_days = (2.0 * window_minutes) / 1440.0
    return -math.log(1.0 - 1.0 / target_lr) / span_days


def apply_change_evidence(posterior, evidence):
    """Fold "it correlates with a change" in, at the strength it has earned.

    The estate's own change rate decides how far this moves anything. As the
    likelihood ratio approaches 1 the update vanishes, which is the correct
    behaviour and not a safeguard bolted on afterwards.
    """
    q = evidence['posterior_change_caused']
    triggered = _normalise({c: posterior[c] * CHANGE_AFFINITY[c]
                            for c in posterior})
    spontaneous = _normalise({c: posterior[c] * (1.0 - CHANGE_AFFINITY[c])
                              for c in posterior})
    return {c: q * triggered[c] + (1.0 - q) * spontaneous[c] for c in posterior}


def not_ruled_out(posterior, floor=0.01):
    """Causes the answers have left alive. The list the original never printed."""
    return [(c, p) for c, p in rank(posterior) if p >= floor]


# ---------------------------------------------------------------------------
# Tests, and what each one is worth against THIS set of hypotheses
# ---------------------------------------------------------------------------

TESTS = {
    'another host on the same wall port': dict(
        outcome='the other host works',
        p={'edge_host': 0.95, 'edge_access': 0.05, 'new_media': 0.05,
           'provider': 0.05, 'config_error': 0.25, 'filter_selective': 0.35,
           'path_partial': 0.50, 'hardware_silent': 0.45, 'capacity': 0.20,
           'shared_service': 0.15}),
    'this host on a port known to work': dict(
        outcome='the host works there',
        p={'edge_host': 0.05, 'edge_access': 0.95, 'new_media': 0.90,
           'provider': 0.05, 'config_error': 0.35, 'filter_selective': 0.20,
           'path_partial': 0.45, 'hardware_silent': 0.40, 'capacity': 0.25,
           'shared_service': 0.10}),
    'pin the flow to each bundle member in turn': dict(
        outcome='one member fails while the others pass',
        p={'edge_host': 0.02, 'edge_access': 0.02, 'new_media': 0.02,
           'provider': 0.05, 'config_error': 0.08, 'filter_selective': 0.10,
           'path_partial': 0.88, 'hardware_silent': 0.45, 'capacity': 0.15,
           'shared_service': 0.02}),
    'full-size packets with fragmentation forbidden': dict(
        outcome='large packets fail where small ones pass',
        p={'edge_host': 0.05, 'edge_access': 0.05, 'new_media': 0.10,
           'provider': 0.15, 'config_error': 0.20, 'filter_selective': 0.05,
           'path_partial': 0.55, 'hardware_silent': 0.15, 'capacity': 0.10,
           'shared_service': 0.02}),
    'test the address rather than the name': dict(
        outcome='the address works and the name does not',
        p={'edge_host': 0.15, 'edge_access': 0.02, 'new_media': 0.02,
           'provider': 0.02, 'config_error': 0.05, 'filter_selective': 0.08,
           'path_partial': 0.05, 'hardware_silent': 0.03, 'capacity': 0.05,
           'shared_service': 0.85}),
    'read the provider circuit alarms and error counters': dict(
        outcome='the circuit shows errors or is down',
        p={'edge_host': 0.01, 'edge_access': 0.02, 'new_media': 0.05,
           'provider': 0.80, 'config_error': 0.03, 'filter_selective': 0.01,
           'path_partial': 0.10, 'hardware_silent': 0.12, 'capacity': 0.08,
           'shared_service': 0.01}),
    'compare the programmed entry with the route (Lab 64.3)': dict(
        outcome='what is programmed disagrees with what is routed',
        p={'edge_host': 0.01, 'edge_access': 0.01, 'new_media': 0.01,
           'provider': 0.02, 'config_error': 0.05, 'filter_selective': 0.03,
           'path_partial': 0.25, 'hardware_silent': 0.80, 'capacity': 0.03,
           'shared_service': 0.01}),
    'ping the default gateway from the host': dict(
        outcome='the gateway replies',
        p={'edge_host': 0.55, 'edge_access': 0.10, 'new_media': 0.10,
           'provider': 0.95, 'config_error': 0.70, 'filter_selective': 0.85,
           'path_partial': 0.92, 'hardware_silent': 0.88, 'capacity': 0.90,
           'shared_service': 0.97}),
}


# A branch this unlikely carries no measurable entropy, and trying to
# renormalise it divides by rounding error.
NEGLIGIBLE = 1e-12


def test_value(posterior, p_outcome):
    """Expected bits this binary test removes from the current uncertainty."""
    missing = set(posterior) - set(p_outcome)
    if missing:
        raise AnswerError('a test must say what it would show for every cause '
                          f'in play; missing: {sorted(missing)}')
    for cause, p in p_outcome.items():
        if not 0.0 <= p <= 1.0:
            raise AnswerError(f'the chance of an outcome given {cause} is '
                              f'{p!r}, which is not a probability')
    p_yes = min(max(sum(posterior[c] * p_outcome[c] for c in posterior),
                    0.0), 1.0)
    p_no = 1.0 - p_yes
    before = entropy_bits(posterior)
    after = 0.0
    if p_yes > NEGLIGIBLE:
        yes = _normalise({c: posterior[c] * p_outcome[c] for c in posterior})
        after += p_yes * entropy_bits(yes)
    if p_no > NEGLIGIBLE:
        no = _normalise({c: posterior[c] * (1.0 - p_outcome[c])
                         for c in posterior})
        after += p_no * entropy_bits(no)
    return dict(bits=max(before - after, 0.0), p_outcome=p_yes,
                before=before, after=after)


def rank_tests(posterior):
    scored = [(name, test_value(posterior, spec['p']), spec['outcome'])
              for name, spec in TESTS.items()]
    scored.sort(key=lambda row: (-row[1]['bits'], row[0]))
    return scored


def posterior_after(posterior, test_name, observed):
    """Where the hypotheses stand once a test has actually been run."""
    if test_name not in TESTS:
        raise AnswerError(f'no such test: {test_name!r}')
    if not isinstance(observed, bool):
        raise AnswerError('a test outcome is True or False; an untried test '
                          'is not an outcome')
    p = TESTS[test_name]['p']
    weights = {c: posterior[c] * (p[c] if observed else 1.0 - p[c])
               for c in posterior}
    if sum(weights.values()) <= NEGLIGIBLE:
        raise AnswerError(
            f'no cause in play could have produced that result for '
            f'{test_name!r}, so either the test was run differently from the '
            'way it is described here or the fault is not in this list at all')
    return _normalise(weights)


# ---------------------------------------------------------------------------
# Controls. Each one fails loudly if the claim it guards stops being true.
# ---------------------------------------------------------------------------

def prove_the_claims():
    out = []

    never_one_user, _ = weigh(ever_worked=False, scope='one user')
    config = never_one_user['config_error']
    edge = never_one_user['edge_host'] + never_one_user['edge_access']
    fresh = never_one_user['new_media']
    core = (never_one_user['filter_selective']
            + never_one_user['path_partial']
            + never_one_user['hardware_silent'])
    out.append(('"never worked, one user" does not establish a config fault',
                config < 0.5,
                f'configuration error carries {config:.1%}, against {edge:.1%} '
                f'at the edge and {fresh:.1%} on the new media'))
    out.append(('"never worked" leaves new media and the provider alive',
                fresh + never_one_user['provider'] > 0.05,
                f'new media {fresh:.1%} plus provider '
                f'{never_one_user["provider"]:.1%}'))
    out.append(('"one user" leaves core causes alive',
                core > 0.05,
                f'filter, bundle member and silent hardware together {core:.1%}'))

    everywhere, _ = weigh(ever_worked=True, scope='everywhere')
    out.append(('"everywhere" does not establish a shared service either',
                everywhere['shared_service'] < 0.6,
                f'shared service {everywhere["shared_service"]:.1%}; the rest '
                f'is spread across {len(not_ruled_out(everywhere)) - 1} others'))

    unanswered, asked = weigh()
    out.append(('an unanswered questionnaire changes nothing',
                all(abs(unanswered[c] - PRIORS[c]) < 1e-12 for c in PRIORS)
                and asked == [],
                'the posterior is the prior, exactly'))

    quiet = change_evidence(changes_per_day=40)
    busy = change_evidence(changes_per_day=200)
    out.append(('correlation with a change is weak evidence at 40 changes/day',
                quiet['likelihood_ratio'] < 3.0,
                f'likelihood ratio {quiet["likelihood_ratio"]:.2f}, '
                f'{quiet["bits"]:.2f} bits'))
    out.append(('and almost worthless at 200 changes/day',
                busy['likelihood_ratio'] < 1.1,
                f'likelihood ratio {busy["likelihood_ratio"]:.3f}, '
                f'{busy["bits"]:.3f} bits'))
    out.append(('the correlation gets weaker as the estate gets busier',
                busy['likelihood_ratio'] < quiet['likelihood_ratio'],
                f'{quiet["likelihood_ratio"]:.2f} at 40/day falls to '
                f'{busy["likelihood_ratio"]:.3f} at 200/day'))

    # Would the questionnaire ever say something FALSE? It must be able to.
    truth = 'filter_selective'
    posterior, _ = weigh(ever_worked=True, scope='one user')
    top = rank(posterior, 1)[0][0]
    out.append(('the questionnaire can and does rank the true cause below a '
                'wrong one',
                top != truth and posterior[truth] > 0,
                f'with the true cause {truth}, it ranks {top} first and puts '
                f'{truth} at {posterior[truth]:.1%}'))

    # An unknown answer must be refused, not guessed at.
    refused = False
    try:
        weigh(scope='one building')
    except AnswerError:
        refused = True
    out.append(('an unrecognised scope is refused rather than guessed',
                refused, "weigh(scope='one building') raises AnswerError"))

    # A test that cannot tell the leaders apart must score near zero bits.
    flat = _normalise({c: 1.0 for c in CAUSES})
    useless = test_value(flat, {c: 0.5 for c in CAUSES})
    out.append(('a test whose outcome does not depend on the cause is worth '
                'no bits',
                abs(useless['bits']) < 1e-9,
                f'{useless["bits"]:.1e} bits, which is zero to within '
                f'floating-point noise'))
    return out


def _with_config_prior(share):
    """The stated priors, with configuration error given `share` of the mass."""
    if not 0.0 < share < 1.0:
        raise AnswerError('a prior share must lie strictly between 0 and 1')
    others = {c: PRIORS[c] for c in PRIORS if c != 'config_error'}
    scale = (1.0 - share) / sum(others.values())
    priors = {c: v * scale for c, v in others.items()}
    priors['config_error'] = share
    return priors


def sensitivity(steps=12, lo=0.02, hi=0.90):
    """Do the conclusions survive moving the numbers this lab made up?

    The prior on a configuration error is swept from far below its stated
    value to far above it, and the headline claim --- that "never worked, one
    user" does not establish a configuration fault --- is re-tested at each
    step. The sweep runs past the point where the claim fails on purpose: a
    sensitivity check that only visits the range where you were right is not
    a sensitivity check.
    """
    rows = []
    for i in range(steps):
        share = lo + i * (hi - lo) / (steps - 1)
        posterior, _ = weigh(ever_worked=False, scope='one user',
                             priors=_with_config_prior(share))
        rows.append((share, posterior['config_error'],
                     posterior['config_error'] < 0.5))
    return rows


def break_point(threshold=0.5, tol=1e-9):
    """The prior on configuration error at which the headline claim fails.

    Returns None if the claim holds across the whole range, which would mean
    the sweep above is not probing hard enough.
    """
    def post(share):
        p, _ = weigh(ever_worked=False, scope='one user',
                     priors=_with_config_prior(share))
        return p['config_error']

    lo, hi = 1e-6, 1.0 - 1e-6
    if post(hi) < threshold:
        return None
    while hi - lo > tol:
        mid = (lo + hi) / 2.0
        if post(mid) < threshold:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ---------------------------------------------------------------------------
# What the lab used to say
# ---------------------------------------------------------------------------

def _ordinal(n):
    if 10 <= n % 100 <= 20:
        return f'{n}th'
    return f'{n}' + {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')


ORIGINAL_SCOPE_LOCUS = {
    'one user':   "that user's host, port, or access switch -- the edge",
    'one vlan':   'that VLAN: its SVI/gateway, its L2 domain, its ACL',
    'one site':   "that site's uplink, gateway, or local services",
    'one prefix': 'routing/policy for that prefix (advertisement, filter)',
    'everywhere': 'a shared core service (DNS, auth, a core link/route)',
}


def demo_original(out=print):
    out('WHAT THIS LAB USED TO PRINT, AND WHY IT WAS TOO CONFIDENT')
    out('')
    out('  It mapped each answer to a single verdict:')
    out('')
    out('    never worked  ->  "NEVER worked -> configuration/design fault')
    out('                       (it was never right)"')
    out('    one user      ->  "that user\'s host, port, or access switch')
    out('                       -- the edge"')
    out('    worked, then  ->  "a CHANGE (...); correlate to change log"')
    out('')
    out('  and it printed a "bounded suspect region" with no alternative')
    out('  beside it and no weight on any of them.')
    out('')
    posterior, _ = weigh(ever_worked=False, scope='one user')
    out('  Its Case B --- brand-new desk, one user, never worked --- read out')
    out('  as a configuration fault and sent you bottom-up from layer 1. On')
    out('  the numbers written down in this file it stands at:')
    out('')
    for cause, p in rank(posterior, 5):
        out(f'      {p:6.1%}  {cause:17s} {CAUSES[cause]}')
    out('')
    place = _ordinal([c for c, _ in rank(posterior)].index('config_error') + 1)
    out(f'  The old verdict, configuration error, comes {place} at '
        f'{posterior["config_error"]:.1%}. It is a reasonable')
    out('  place to look. It is not what the question established, and the')
    out('  answer the old lab printed would have had you verifying layers on')
    out('  a desk whose new fibre is in the wrong port.')
    out('')
    ev = change_evidence(changes_per_day=40)
    out('  On "what changed", it said a correlation "often names the cause')
    out('  outright". At 40 changes a day and a +/-15-minute window, an')
    out(f'  unrelated change lands in that window {ev["coincidence"]:.1%} of '
        f'the time all by')
    out(f'  itself, so the correlation is worth a likelihood ratio of '
        f'{ev["likelihood_ratio"]:.2f}:')
    out(f'  about {ev["bits"]:.2f} bits, moving a '
        f'{ev["prior_change_caused"]:.0%} prior to '
        f'{ev["posterior_change_caused"]:.1%}. Useful. Not a name.')


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _case(out, title, ever_worked, scope, changes_per_day=None,
          window_minutes=15.0, truth=None):
    out(title)
    out('-' * len(title))
    answers = []
    answers.append('did it ever work?  ' +
                   ('not established' if ever_worked is UNKNOWN
                    else ('yes, then stopped' if ever_worked else 'never')))
    answers.append('is it one or many? ' +
                   ('not established' if scope is UNKNOWN else scope))
    for line in answers:
        out(f'  {line}')

    posterior, asked = weigh(ever_worked=ever_worked, scope=scope)
    if changes_per_day is not None:
        ev = change_evidence(changes_per_day=changes_per_day,
                             window_minutes=window_minutes)
        out(f'  what changed?      a change {window_minutes:.0f} minutes '
            f'either side, in an estate making {changes_per_day:.0f} changes a day')
        out(f'  when exactly?      close enough to that change to correlate')
        out('')
        out(f'  That correlation is worth a likelihood ratio of '
            f'{ev["likelihood_ratio"]:.2f}, or {ev["bits"]:.2f} bits:')
        out(f'  an unrelated change lands in the same window '
            f'{ev["coincidence"]:.1%} of the time anyway.')
        out(f'  It moves "this was change-triggered" from '
            f'{ev["prior_change_caused"]:.0%} to '
            f'{ev["posterior_change_caused"]:.1%}, and the')
        out('  hypotheses below are reweighted by exactly that much and no '
            'more.')
        posterior = apply_change_evidence(posterior, ev)
    out('')

    out(f'  RANKED HYPOTHESES (uncertainty remaining: '
        f'{entropy_bits(posterior):.2f} bits of a possible '
        f'{math.log2(len(CAUSES)):.2f})')
    for cause, p in rank(posterior, 5):
        out(f'      {p:6.1%}  {cause:17s} {CAUSES[cause]}')

    alive = not_ruled_out(posterior)
    out('')
    out(f'  WHAT THESE ANSWERS DID NOT RULE OUT: {len(alive)} of '
        f'{len(CAUSES)} causes still carry')
    out('  at least one per cent. Among them:')
    leaders = {c for c, _ in rank(posterior, 2)}
    for cause, p in alive:
        if cause not in leaders:
            out(f'      {p:6.1%}  {cause:17s} {CAUSES[cause]}')

    scored = rank_tests(posterior)
    out('')
    out('  TESTS, BY WHAT THEY WOULD ACTUALLY SETTLE')
    for name, value, outcome in scored[:4]:
        out(f'      {value["bits"]:.2f} bits  {name}')
        out(f'                  ("{outcome}" '
            f'{value["p_outcome"]:.0%} likely before you run it)')
    worst = scored[-1]
    out(f'      and last, at {worst[1]["bits"]:.2f} bits: {worst[0]}')

    best_name, best_value, _ = scored[0]
    after_yes = posterior_after(posterior, best_name, True)
    after_no = posterior_after(posterior, best_name, False)
    out('')
    out(f'  Run the first one and you land on {rank(after_yes, 1)[0][0]} at '
        f'{rank(after_yes, 1)[0][1]:.1%} if it')
    out(f'  passes, or {rank(after_no, 1)[0][0]} at '
        f'{rank(after_no, 1)[0][1]:.1%} if it fails. Either way you have '
        f'{best_value["bits"]:.2f} bits')
    out('  more than the questionnaire gave you, for the price of one test.')

    if truth is not None:
        top = rank(posterior, 1)[0]
        out('')
        out(f'  GROUND TRUTH IN THIS CASE: {truth} --- '
            f'{CAUSES[truth]}.')
        if top[0] == truth:
            out(f'  The questionnaire happened to rank it first, at '
                f'{top[1]:.1%}. It was right, at')
            out('  odds it could not have known in advance.')
        else:
            out(f'  The questionnaire ranked {top[0]} first at {top[1]:.1%} '
                f'and put the true')
            out(f'  cause at {posterior[truth]:.1%}. It was wrong. It was not '
                f'broken --- it was')
            out('  doing what a questionnaire can do, which is rank, not '
                'diagnose.')
            best_for_truth = max(
                TESTS, key=lambda n: abs(TESTS[n]['p'][truth]
                                         - TESTS[n]['p'][top[0]]))
            out(f'  The test that separates them best is: {best_for_truth}.')
    out('')


def report(out=print, original=False):
    if original:
        demo_original(out)
        return

    out('=' * 74)
    out('LAB 64.2 --- THE FOUR QUESTIONS, AND WHAT THEIR ANSWERS ARE WORTH')
    out('=' * 74)
    out('')
    out('Ask them first. They cost a conversation, not a login, and nothing')
    out('else you can do is that cheap. Then read the answers for what they')
    out('are: evidence with a weight, not a verdict with a name.')
    out('')
    out(f'Before any question is asked, {len(CAUSES)} causes are in play and')
    out(f'{entropy_bits(_normalise(dict(PRIORS))):.2f} bits of the answer are '
        f'missing.')
    out('')

    _case(out, 'CASE A --- everything is slow, since a push at 09:10',
          ever_worked=True, scope='everywhere', changes_per_day=40)

    _case(out, 'CASE B --- one user, brand-new desk, it has never worked',
          ever_worked=False, scope='one user', truth='new_media')

    _case(out, 'CASE C --- one user, worked yesterday, nothing changed on the '
               'desk',
          ever_worked=True, scope='one user', truth='filter_selective')

    _case(out, 'CASE D --- a whole site, and nobody will say when it started',
          ever_worked=True, scope='one site')

    out('HOW MUCH "IT CORRELATES WITH A CHANGE" IS WORTH')
    out('-' * 46)
    out('  changes/day   coincidence   likelihood ratio   bits   70% becomes')
    for rate in (2, 10, 40, 100, 200, 500):
        ev = change_evidence(changes_per_day=rate)
        out(f'  {rate:>11}   {ev["coincidence"]:>10.1%}   '
            f'{ev["likelihood_ratio"]:>16.2f}   {ev["bits"]:>4.2f}   '
            f'{ev["posterior_change_caused"]:>10.1%}')
    dead = rate_at_which_correlation_dies(target_lr=2.0)
    out('')
    out(f'  Past {dead:.0f} changes a day, a +/-15-minute correlation is worth')
    out('  less than a likelihood ratio of 2 --- which is to say, less than')
    out('  one bit. The estate that automates hardest is the estate where')
    out('  "it started right after the change" stops meaning anything, and')
    out('  it is the estate most likely to say it with confidence.')
    out('')

    out('DOES ANY OF THIS SURVIVE CHANGING THE NUMBERS THIS LAB MADE UP?')
    out('-' * 62)
    out('  Sweeping the prior on a configuration error, and re-asking whether')
    out('  "never worked, one user" establishes one:')
    out('')
    out('    prior on config error   posterior   does it establish it?')
    for share, post, holds in sensitivity():
        out(f'    {share:>19.1%}   {post:>9.1%}   '
            f'{"no" if holds else "YES --- the claim fails here"}')
    rows = sensitivity()
    held = sum(1 for _, _, h in rows if h)
    bp = break_point()
    out('')
    out(f'  The claim holds at {held} of {len(rows)} settings and fails at the')
    out(f'  remaining {len(rows) - held}. The crossing is at a prior of '
        f'{bp:.1%}: if you')
    out('  believe beforehand that configuration errors cause more than')
    out(f'  {bp:.0%} of all faults, then "never worked, one user" does')
    out('  establish one --- but the questionnaire is no longer telling you')
    out('  that, your prior is. That is the assumption the original made')
    out('  without writing it down, and this is the honest shape of the')
    out('  result: a claim with a stated range, not a claim.')
    out('')

    out('CONTROLS')
    out('-' * 8)
    failed = 0
    for claim, ok, detail in prove_the_claims():
        out(f'  [{"ok" if ok else "FAIL"}] {claim}')
        out(f'         {detail}')
        failed += 0 if ok else 1
    out('')
    out(f'  {failed} failed.')
    out('')
    out('WHAT TO DO WITH THE ANSWERS')
    out('-' * 27)
    out('  Ask the four questions first; they are still the cheapest thing on')
    out('  the list. Write down what they leave alive, not just what they')
    out('  favour. Then pick the test that separates your top two, and if no')
    out('  test separates them, you have not got two hypotheses --- you have')
    out('  got one hypothesis and a spare. The questionnaire ranks. Only a')
    out('  test decides.')
    return failed


def one_case(args, out=print):
    """Your own incident, through the same calculation as the printed cases.

    This exists because the book used to tell a first-time reader to "edit the
    case at the top of the file", and the cases are neither at the top nor
    especially editable: they are four _case(...) calls inside report(), near
    the end of 800 lines. A reader putting their own incident through this
    should not have to read the program first.
    """
    ever = {'yes': True, 'no': False, 'unknown': UNKNOWN}[args.ever_worked]
    out('=' * 74)
    out('LAB 64.2 --- YOUR CASE, THROUGH THE SAME WEIGHTS AS THE PRINTED ONES')
    out('=' * 74)
    out('')
    out('The priors and likelihoods are the ones written down in this file. They')
    out('are illustrative, not surveyed. Replace them with your own service')
    out("desk's mix before you believe a number: the README says where.")
    out('')
    _case(out, 'YOUR CASE --- %s' % args.case,
          ever_worked=ever,
          scope=UNKNOWN if args.scope == 'unknown' else args.scope,
          changes_per_day=args.changes_per_day,
          window_minutes=args.window_minutes)
    out('An answer you did not give was treated as unknown and changed nothing.')
    return False


def main(argv=None):
    import argparse
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(
        prog='four_questions.py',
        description='Weigh the four triage questions. With no options, prints '
                    'the four constructed demonstration cases.')
    ap.add_argument('--demo-original', action='store_true',
                    help='print the withdrawn verdict-style version, for comparison')
    ap.add_argument('--case', metavar='NAME',
                    help='put your own incident through it, under this name')
    ap.add_argument('--ever-worked', choices=['yes', 'no', 'unknown'],
                    default='unknown',
                    help='did it ever work? (default: unknown, which updates nothing)')
    ap.add_argument('--scope', choices=sorted(SCOPES) + ['unknown'],
                    default='unknown',
                    help='is it one or many? (default: unknown)')
    ap.add_argument('--changes-per-day', type=float, metavar='N',
                    help='changes a day across the estate, if a change correlates')
    ap.add_argument('--window-minutes', type=float, default=15.0, metavar='M',
                    help='how close in time the change was (default: 15)')
    args = ap.parse_args(argv)

    if args.case:
        if args.demo_original:
            ap.error('--case and --demo-original ask for different reports')
        if args.changes_per_day is not None and args.changes_per_day <= 0:
            ap.error('--changes-per-day must be greater than zero')
        failed = one_case(args)
    else:
        for name, value in (('--ever-worked', args.ever_worked),
                            ('--scope', args.scope)):
            if value != 'unknown':
                ap.error('%s only means something with --case' % name)
        if args.changes_per_day is not None:
            ap.error('--changes-per-day only means something with --case')
        failed = report(original=args.demo_original)
    return 0 if not failed else 1


if __name__ == '__main__':
    raise SystemExit(main())
