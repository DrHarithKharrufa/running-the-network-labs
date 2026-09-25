"""Tests for lab 64.2.  Run: python3 test_four_questions.py

The lab was repaired rather than withdrawn. These tests cover the two claims
the original made and could not support --- that "it never worked" establishes
a configuration fault and that "one user" establishes an edge fault --- plus
the three things the repair added: weights instead of verdicts, an explicit
list of what the answers did not rule out, and refusal rather than guesswork
on an answer the questionnaire does not recognise.
"""
import contextlib
import io
import math
import unittest

import four_questions as lab
from four_questions import (CAUSES, CHANGE_AFFINITY, PRIORS, SCOPES, TESTS,
                            UNKNOWN, AnswerError, apply_change_evidence,
                            break_point, change_evidence, demo_original,
                            entropy_bits, not_ruled_out, posterior_after,
                            prove_the_claims, rank, rank_tests,
                            rate_at_which_correlation_dies, report,
                            sensitivity, test_value, weigh)


class ModelShapeTests(unittest.TestCase):
    """The tables have to be complete and consistent before anything else."""

    def test_priors_are_a_distribution(self):
        self.assertAlmostEqual(sum(PRIORS.values()), 1.0)
        self.assertEqual(set(PRIORS), set(CAUSES))
        for cause, p in PRIORS.items():
            self.assertGreater(p, 0.0, msg=cause)

    def test_every_table_covers_every_cause(self):
        tables = dict(SCOPES)
        tables['never worked'] = lab.NEVER_WORKED_GIVEN
        tables['change affinity'] = CHANGE_AFFINITY
        for name, table in tables.items():
            with self.subTest(table=name):
                self.assertEqual(set(table), set(CAUSES))
                for cause, p in table.items():
                    self.assertGreaterEqual(p, 0.0, msg=cause)
                    self.assertLessEqual(p, 1.0, msg=cause)

    def test_every_test_covers_every_cause(self):
        for name, spec in TESTS.items():
            with self.subTest(test=name):
                self.assertEqual(set(spec['p']), set(CAUSES))
                self.assertTrue(spec['outcome'].strip())

    def test_every_cause_is_explained(self):
        for cause, text in CAUSES.items():
            self.assertGreater(len(text), 20, msg=cause)


class WeighingTests(unittest.TestCase):

    def test_no_answers_changes_nothing(self):
        posterior, asked = weigh()
        self.assertEqual(asked, [])
        for cause in PRIORS:
            self.assertAlmostEqual(posterior[cause], PRIORS[cause], places=12)

    def test_a_posterior_is_a_distribution(self):
        for ever in (True, False, UNKNOWN):
            for scope in list(SCOPES) + [UNKNOWN]:
                with self.subTest(ever=ever, scope=scope):
                    posterior, _ = weigh(ever_worked=ever, scope=scope)
                    self.assertAlmostEqual(sum(posterior.values()), 1.0)
                    self.assertEqual(set(posterior), set(CAUSES))

    def test_never_worked_does_not_establish_a_configuration_fault(self):
        """TE-0622, first half, as an inequality."""
        posterior, _ = weigh(ever_worked=False, scope='one user')
        self.assertLess(posterior['config_error'], 0.5)
        self.assertGreater(posterior['new_media'], 0.05)
        self.assertGreater(posterior['provider'], 0.0)

    def test_never_worked_favours_new_media_over_its_prior(self):
        before = PRIORS['new_media']
        after, _ = weigh(ever_worked=False)
        self.assertGreater(after['new_media'], before)

    def test_one_user_does_not_establish_an_edge_fault(self):
        """TE-0622, second half."""
        posterior, _ = weigh(scope='one user')
        core = (posterior['filter_selective'] + posterior['path_partial']
                + posterior['hardware_silent'])
        self.assertGreater(core, 0.05)
        edge = posterior['edge_host'] + posterior['edge_access']
        self.assertLess(edge, 0.95)

    def test_everywhere_does_not_establish_a_shared_service(self):
        posterior, _ = weigh(scope='everywhere')
        self.assertLess(posterior['shared_service'], 0.8)
        self.assertGreater(posterior['config_error'], 0.05)

    def test_nothing_is_ever_ruled_out_to_zero_by_the_questions(self):
        for ever in (True, False):
            for scope in SCOPES:
                posterior, _ = weigh(ever_worked=ever, scope=scope)
                zeroed = [c for c, p in posterior.items() if p == 0.0]
                # "everywhere" genuinely excludes a single host or port, and
                # the model is allowed to say so; nothing else may be zero.
                allowed = {'edge_host', 'edge_access'} if scope == 'everywhere' \
                    else set()
                self.assertTrue(set(zeroed) <= allowed,
                                msg=f'{scope}/{ever} zeroed {zeroed}')

    def test_asked_records_only_the_questions_answered(self):
        _, asked = weigh(ever_worked=True)
        self.assertEqual(asked, ['did it ever work'])
        _, asked = weigh(scope='one site')
        self.assertEqual(asked, ['is it one or many'])
        _, asked = weigh(ever_worked=False, scope='one site')
        self.assertEqual(len(asked), 2)


class InvalidInputTests(unittest.TestCase):
    """TE-0645: invalid and unknown input must be handled, not absorbed."""

    def test_an_unrecognised_scope_is_refused(self):
        for bad in ('one building', 'ONE USER', 'one vlan', 'one prefix', ''):
            with self.subTest(scope=bad), self.assertRaises(AnswerError):
                weigh(scope=bad)

    def test_a_non_boolean_history_is_refused(self):
        for bad in ('yes', 1, 0, None, 0.5):
            with self.subTest(ever=bad), self.assertRaises(AnswerError):
                weigh(ever_worked=bad)

    def test_unknown_is_accepted_for_both(self):
        posterior, asked = weigh(ever_worked=UNKNOWN, scope=UNKNOWN)
        self.assertEqual(asked, [])
        self.assertAlmostEqual(sum(posterior.values()), 1.0)

    def test_incomplete_priors_are_refused(self):
        short = {c: v for c, v in PRIORS.items() if c != 'capacity'}
        with self.assertRaises(AnswerError):
            weigh(priors=short)

    def test_all_zero_priors_are_refused(self):
        with self.assertRaises(AnswerError):
            weigh(priors={c: 0.0 for c in PRIORS})

    def test_a_test_outcome_must_be_a_boolean(self):
        posterior, _ = weigh(scope='one user')
        name = next(iter(TESTS))
        for bad in ('pass', 1, None, UNKNOWN):
            with self.subTest(observed=bad), self.assertRaises(AnswerError):
                posterior_after(posterior, name, bad)

    def test_an_unknown_test_is_refused(self):
        posterior, _ = weigh(scope='one user')
        with self.assertRaises(AnswerError):
            posterior_after(posterior, 'ping it and hope', True)

    def test_impossible_change_parameters_are_refused(self):
        with self.assertRaises(AnswerError):
            change_evidence(changes_per_day=-1)
        with self.assertRaises(AnswerError):
            change_evidence(changes_per_day=10, window_minutes=0)
        for bad in (0.0, 1.0, -0.2, 1.5):
            with self.subTest(prior=bad), self.assertRaises(AnswerError):
                change_evidence(changes_per_day=10, prior_change_caused=bad)

    def test_a_worthless_target_ratio_is_refused(self):
        for bad in (1.0, 0.5, 0.0, -2.0):
            with self.subTest(lr=bad), self.assertRaises(AnswerError):
                rate_at_which_correlation_dies(target_lr=bad)


class ChangeCorrelationTests(unittest.TestCase):
    """TE-0622, third part: correlation is not causation, and here is by how much."""

    def test_a_quiet_estate_makes_the_correlation_strong(self):
        ev = change_evidence(changes_per_day=2)
        self.assertGreater(ev['likelihood_ratio'], 10.0)
        self.assertGreater(ev['posterior_change_caused'], 0.95)

    def test_a_busy_estate_makes_it_worthless(self):
        ev = change_evidence(changes_per_day=200)
        self.assertLess(ev['likelihood_ratio'], 1.1)
        self.assertLess(ev['bits'], 0.1)
        self.assertLess(abs(ev['posterior_change_caused']
                            - ev['prior_change_caused']), 0.01)

    def test_the_evidence_weakens_monotonically_with_the_change_rate(self):
        rates = [1, 5, 20, 50, 100, 400]
        ratios = [change_evidence(changes_per_day=r)['likelihood_ratio']
                  for r in rates]
        self.assertEqual(ratios, sorted(ratios, reverse=True))

    def test_the_coincidence_formula_is_the_poisson_one(self):
        ev = change_evidence(changes_per_day=40, window_minutes=15)
        self.assertAlmostEqual(ev['coincidence'],
                               1.0 - math.exp(-40 * 30 / 1440.0))

    def test_a_wider_window_is_weaker_evidence(self):
        narrow = change_evidence(changes_per_day=40, window_minutes=2)
        wide = change_evidence(changes_per_day=40, window_minutes=120)
        self.assertGreater(narrow['likelihood_ratio'],
                           wide['likelihood_ratio'])

    def test_the_rate_where_the_evidence_dies_is_where_it_says(self):
        rate = rate_at_which_correlation_dies(target_lr=2.0)
        at = change_evidence(changes_per_day=rate)
        self.assertAlmostEqual(at['likelihood_ratio'], 2.0, places=6)

    def test_folding_it_in_moves_things_by_no_more_than_it_earned(self):
        posterior, _ = weigh(ever_worked=True, scope='everywhere')
        weak = apply_change_evidence(posterior,
                                     change_evidence(changes_per_day=100000))
        strong = apply_change_evidence(posterior,
                                       change_evidence(changes_per_day=1))
        moved_weak = sum(abs(weak[c] - posterior[c]) for c in posterior)
        moved_strong = sum(abs(strong[c] - posterior[c]) for c in posterior)
        self.assertLess(moved_weak, moved_strong)
        self.assertAlmostEqual(sum(weak.values()), 1.0)
        self.assertAlmostEqual(sum(strong.values()), 1.0)

    def test_a_strong_correlation_favours_what_changes_introduce(self):
        posterior, _ = weigh(ever_worked=True, scope='everywhere')
        after = apply_change_evidence(posterior,
                                      change_evidence(changes_per_day=1))
        self.assertGreater(after['config_error'], posterior['config_error'])
        self.assertLess(after['hardware_silent'], posterior['hardware_silent'])


class TestValueTests(unittest.TestCase):
    """A hypothesis you cannot distinguish from its rival is not a hypothesis."""

    def test_a_test_that_ignores_the_cause_is_worth_nothing(self):
        posterior, _ = weigh(scope='one user')
        for constant in (0.0, 0.3, 0.5, 1.0):
            with self.subTest(p=constant):
                value = test_value(posterior, {c: constant for c in CAUSES})
                self.assertLess(abs(value['bits']), 1e-9)

    def test_a_perfectly_separating_test_removes_everything(self):
        posterior, _ = weigh(scope='one user')
        leader = rank(posterior, 1)[0][0]
        perfect = {c: (1.0 if c == leader else 0.0) for c in CAUSES}
        value = test_value(posterior, perfect)
        self.assertGreater(value['bits'], 0.0)
        after = posterior_after(posterior, 'test the address rather than the '
                                'name', True)
        self.assertAlmostEqual(sum(after.values()), 1.0)

    def test_no_test_is_ever_worth_negative_bits(self):
        for scope in SCOPES:
            posterior, _ = weigh(scope=scope)
            for name, value, _ in rank_tests(posterior):
                self.assertGreater(value['bits'], -1e-9, msg=f'{scope}/{name}')

    def test_tests_are_ranked_best_first(self):
        posterior, _ = weigh(ever_worked=False, scope='one user')
        bits = [value['bits'] for _, value, _ in rank_tests(posterior)]
        self.assertEqual(bits, sorted(bits, reverse=True))

    def test_the_best_test_depends_on_the_symptom(self):
        """Which is why no fixed first move can be right for every fault."""
        first = {}
        for scope in SCOPES:
            posterior, _ = weigh(scope=scope)
            first[scope] = rank_tests(posterior)[0][0]
        self.assertGreater(len(set(first.values())), 1,
                           msg=f'the same test won everywhere: {first}')

    def test_running_a_test_reduces_uncertainty_on_average(self):
        posterior, _ = weigh(ever_worked=False, scope='one user')
        before = entropy_bits(posterior)
        for name, spec in TESTS.items():
            with self.subTest(test=name):
                value = test_value(posterior, spec['p'])
                p_yes = value['p_outcome']
                after = (p_yes * entropy_bits(posterior_after(posterior, name,
                                                              True))
                         + (1 - p_yes)
                         * entropy_bits(posterior_after(posterior, name,
                                                        False)))
                self.assertLessEqual(after, before + 1e-9)

    def test_entropy_is_maximal_when_nothing_is_known(self):
        flat = {c: 1.0 / len(CAUSES) for c in CAUSES}
        self.assertAlmostEqual(entropy_bits(flat), math.log2(len(CAUSES)))
        certain = {c: (1.0 if c == 'edge_host' else 0.0) for c in CAUSES}
        self.assertAlmostEqual(entropy_bits(certain), 0.0)

    def test_the_questions_do_reduce_uncertainty(self):
        """The advice the lab kept: asking first is worth something."""
        before = entropy_bits({c: PRIORS[c] for c in PRIORS})
        after, _ = weigh(ever_worked=False, scope='one user')
        self.assertLess(entropy_bits(after), before)


class ReportingTests(unittest.TestCase):

    def test_what_was_not_ruled_out_is_reported(self):
        posterior, _ = weigh(ever_worked=False, scope='one user')
        alive = not_ruled_out(posterior)
        self.assertGreaterEqual(len(alive), 5)
        self.assertEqual([c for c, _ in alive],
                         [c for c, _ in rank(posterior)][:len(alive)])

    def test_the_floor_is_respected(self):
        posterior, _ = weigh(scope='everywhere')
        for _, p in not_ruled_out(posterior, floor=0.05):
            self.assertGreaterEqual(p, 0.05)

    def test_ranking_is_stable_for_ties(self):
        flat = {c: 0.1 for c in CAUSES}
        self.assertEqual([c for c, _ in rank(flat)], sorted(CAUSES))


class HarnessTests(unittest.TestCase):
    """FR-0054: the controls are an instrument, so check the instrument."""

    def test_all_controls_pass(self):
        results = prove_the_claims()
        self.assertGreaterEqual(len(results), 10)
        failed = [claim for claim, ok, _ in results if not ok]
        self.assertEqual(failed, [], msg=f'failing controls: {failed}')

    def test_every_control_reports_a_detail(self):
        for claim, _, detail in prove_the_claims():
            self.assertTrue(claim.strip())
            self.assertTrue(detail.strip(), msg=claim)

    def test_the_controls_notice_a_sabotaged_table(self):
        """Zero the likelihoods the finding says must stay non-zero."""
        kept = dict(lab.ONE_USER_GIVEN)
        try:
            for cause in ('filter_selective', 'path_partial',
                          'hardware_silent'):
                lab.ONE_USER_GIVEN[cause] = 0.0
            failed = [claim for claim, ok, _ in lab.prove_the_claims()
                      if not ok]
            self.assertTrue(failed, 'the controls passed a sabotaged table')
        finally:
            lab.ONE_USER_GIVEN.clear()
            lab.ONE_USER_GIVEN.update(kept)
        self.assertEqual([c for c, ok, _ in prove_the_claims() if not ok], [])

    def test_the_controls_notice_a_sabotaged_coincidence_model(self):
        kept = lab.change_evidence
        try:
            lab.change_evidence = lambda **kw: dict(
                changes_per_day=kw.get('changes_per_day', 0),
                window_minutes=15.0, coincidence=1e-6,
                likelihood_ratio=1e6, prior_change_caused=0.7,
                posterior_change_caused=0.999999, bits=20.0)
            failed = [claim for claim, ok, _ in lab.prove_the_claims()
                      if not ok]
            self.assertTrue(failed, 'the controls passed a sabotaged model')
        finally:
            lab.change_evidence = kept

    def test_the_sensitivity_sweep_visits_both_sides_of_the_claim(self):
        rows = sensitivity()
        self.assertTrue(any(holds for _, _, holds in rows))
        self.assertTrue(any(not holds for _, _, holds in rows),
                        'the sweep never reaches a setting where the claim '
                        'fails, so it is not testing anything')

    def test_the_break_point_is_where_the_sweep_says(self):
        bp = break_point()
        self.assertIsNotNone(bp)
        below, _ = weigh(ever_worked=False, scope='one user',
                         priors=lab._with_config_prior(bp - 0.01))
        above, _ = weigh(ever_worked=False, scope='one user',
                         priors=lab._with_config_prior(bp + 0.01))
        self.assertLess(below['config_error'], 0.5)
        self.assertGreater(above['config_error'], 0.5)

    def test_the_break_point_is_above_the_stated_prior(self):
        self.assertGreater(break_point(), PRIORS['config_error'])

    def test_report_runs_clean(self):
        lines = []
        self.assertEqual(report(out=lines.append), 0)
        text = ' '.join(lines).lower()
        for needle in ('ranked hypotheses', 'did not rule out',
                       'likelihood ratio', 'controls'):
            self.assertIn(needle, text, msg=needle)

    def test_report_never_prints_a_verdict(self):
        lines = []
        report(out=lines.append)
        text = ' '.join(lines).lower()
        for banned in ('bounded suspect region', 'never worked ->',
                       'configuration/design fault'):
            self.assertNotIn(banned, text, msg=banned)

    def test_demo_original_shows_the_old_output_and_the_numbers(self):
        lines = []
        demo_original(out=lines.append)
        text = ' '.join(lines).lower()
        self.assertIn('configuration/design fault', text)
        self.assertIn('likelihood ratio', text)

    def test_main_accepts_only_its_own_flag(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lab.main([]), 0)
        with self.assertRaises(SystemExit):
            lab.main(['--nonsense'])


if __name__ == '__main__':
    unittest.main(verbosity=0)
