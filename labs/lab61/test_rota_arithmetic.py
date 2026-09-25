#!/usr/bin/env python3
"""Tests for lab 61.2.  Run: python3 test_rota_arithmetic.py"""
import io
import math
import sys

import rota_arithmetic as r

PASS = [0]


def ok(cond, what):
    if not cond:
        raise AssertionError(what)
    PASS[0] += 1


def raises(fn, what):
    try:
        fn()
    except r.RotaError:
        PASS[0] += 1
        return
    raise AssertionError('expected RotaError: %s' % what)


# ---- the quoted guidance is carried, not paraphrased ------------------------
ok(r.HSE_SOURCE.startswith('https://www.hse.gov.uk/'),
   'the source URL is recorded in the lab itself')
ok('either rotate shifts every 2-3 days or every 3-4 weeks' in HSE_ROT
   if (HSE_ROT := r.HSE['rotation_speed']) else False,
   'the rotation guideline is quoted verbatim, including BOTH bands')
ok('otherwise adopt forward rotating shifts' in r.HSE['rotation_speed'],
   'including the forward-rotating alternative')
ok('8h if they are night shifts' in r.HSE['shift_length'],
   'the night-shift length guideline is quoted')
ok(len(r.UNTESTABLE_HERE) >= 8,
   'the guidelines this lab CANNOT check are enumerated rather than ignored')
ok(r.UK_STATUTORY_LEAVE_WEEKS == 5.6, 'UK statutory leave is 5.6 weeks')

# ---- coverage arithmetic ----------------------------------------------------
c = r.coverage_posts()
ok(abs(c['naive_posts'] - 168 / 37.5) < 1e-12, '168/37.5 = 4.48 posts')
ok(abs(c['naive_posts'] - 4.48) < 1e-9, 'which is 4.48 exactly')
ok(c['posts_required'] > c['naive_posts'],
   'cover for absence always increases the requirement')
ok(4.9 < c['posts_required'] < 5.6,
   'about 5.3 posts, got %.3f' % c['posts_required'])
ok(abs(c['weeks_absent_per_person'] - 6.6) < 1e-9,
   '5.6 weeks leave plus a week of training')
perfect = r.coverage_posts(leave_weeks=0, training_weeks=0, sickness_rate=0)
ok(abs(perfect['posts_required'] - perfect['naive_posts']) < 1e-12,
   'with nobody ever absent the two figures coincide, so the model is not '
   'adding a fudge factor')
two = r.coverage_posts(on_duty=2)
ok(abs(two['posts_required'] - 2 * c['posts_required']) < 1e-9,
   'two seats cost exactly twice one seat')
raises(lambda: r.coverage_posts(on_duty=0), 'nobody on duty')
raises(lambda: r.coverage_posts(contracted_hours=0), 'zero contracted hours')
raises(lambda: r.coverage_posts(contracted_hours=200), 'over 168 contracted')
raises(lambda: r.coverage_posts(leave_weeks=-1), 'negative leave')
raises(lambda: r.coverage_posts(sickness_rate=1.0), 'sickness of the whole year')
raises(lambda: r.coverage_posts(leave_weeks=40, training_weeks=13),
       'absence consuming the year')

# ---- the pattern checker ----------------------------------------------------
good = r.check_pattern(8, 8, 2, 4, 3, True, 1, nights_off_when_switching=2,
                       earliest_start_hour=7, handover_minutes=30)
ok(all(x['verdict'] == 'consistent' for x in good),
   'a pattern built to satisfy every testable guideline does')
ok(len({x['guideline'] for x in good}) == len(r.HSE) - 1,
   'one guideline (on-call control) is not a pattern property, so the pattern '
   'checker does not claim to test it')
bad = r.check_pattern(12, 12, 4, 4, 7, False, 0, nights_off_when_switching=1,
                      earliest_start_hour=7, handover_minutes=None)
conflicts = [x['guideline'] for x in bad if x['verdict'] == 'conflicts']
ok('shift_length' in conflicts, '12 h nights conflict with the 8 h guideline')
ok('rotation_speed' in conflicts,
   'a 7-day backward rotation is in neither band and is not forward')
ok('consecutive' in conflicts, 'four consecutive nights exceed 2-3')
ok('switch_recovery' in conflicts, 'one night off at the switch is not two')
ok('free_weekends' in conflicts, 'no free weekend in the cycle')
ok(len(conflicts) == 6, 'six conflicts including both long day and night shifts, got %d'
   % len(conflicts))
ok(any(x['verdict'] == 'not established' for x in bad),
   'the unstated handover time is reported as unestablished, not passed')

# the two recommended bands are BOTH accepted, which is the correction
fast = r.check_pattern(8, 8, 2, 4, 3, False, 1)
slow = r.check_pattern(8, 8, 2, 4, 25, False, 1)
mid = r.check_pattern(8, 8, 2, 4, 7, False, 1)
def speed(rows):
    return [x for x in rows if x['guideline'] == 'rotation_speed'][0]['verdict']
ok(speed(fast) == 'consistent', 'a 3-day rotation is inside the fast band')
ok(speed(slow) == 'consistent', 'a 25-day rotation is inside the slow band')
ok(speed(mid) == 'conflicts',
   'a 7-day BACKWARD rotation is in neither band --- which is why "not too '
   'frequent" was the wrong summary of this guidance')
ok(speed(r.check_pattern(8, 8, 2, 4, 7, True, 1)) == 'consistent',
   'the same 7-day rotation is acceptable if it rotates forward')

# permanent nights and 12 h nights on non-safety-critical work
ok([x for x in r.check_pattern(8, 8, 2, 4, 3, True, 1, permanent_nights=True)
    if x['guideline'] == 'permanent_nights'][0]['verdict'] == 'conflicts',
   'permanent nights conflict')
ok([x for x in r.check_pattern(12, 12, 2, 4, 3, True, 1, safety_critical=False)
    if x['guideline'] == 'shift_length'][0]['verdict'] == 'conflicts',
   '12 h nights conflict even when the work is not safety critical')
ok(any(x['verdict'] == 'conflicts' for x in
       r.check_pattern(8, 13, 2, 4, 3, True, 1)),
   'a 13 h day shift exceeds the 12 h ceiling regardless')
ok([x for x in r.check_pattern(None, None, None, None, None, False, None)
    if x['guideline'] == 'shift_length'][0]['verdict'] == 'not established',
   'an unstated shift length is unestablished, never consistent')

# ---- on-call share ----------------------------------------------------------
s6 = r.oncall_share(6)
ok(abs(s6['naive_share'] - 1 / 3.0) < 1e-12, 'six people, two tiers: one in three')
ok(s6['effective_share'] > s6['naive_share'],
   'the lived share always exceeds the quoted one')
ok(abs(s6['effective_share'] - 2 / (6 * (52 - 5.6) / 52.0)) < 1e-12,
   'the lived share divides by the people actually present')
ok(s6['one_fewer_effective'] > s6['effective_share'],
   'losing a person makes it worse')
ok(abs(r.oncall_share(6, tiers=1)['naive_share'] - 1 / 6.0) < 1e-12,
   'a single-tier rotation halves the share')
raises(lambda: r.oncall_share(1), 'one person is not a two-tier rotation')
raises(lambda: r.oncall_share(2.5), 'a fractional person')
raises(lambda: r.oncall_share(True), 'a bool is not a headcount')
raises(lambda: r.oncall_share(3, tiers=0), 'a rotation has at least one tier')
ok(r.oncall_share(3)['one_fewer_effective'] is None
   or r.oncall_share(3)['one_fewer_effective'] > 0,
   'a rotation that cannot survive a departure says so rather than dividing by '
   'something impossible')

# ---- night disturbance, in closed form -------------------------------------
ok(r.p_night_disturbed(0) == 0.0, 'no pages, no disturbed nights')
ok(abs(r.p_night_disturbed(1.0) - (1 - math.exp(-1))) < 1e-12,
   'one page a night on average disturbs 63 per cent of nights')
ok(r.p_night_disturbed(10) > 0.9999, 'ten a night disturbs essentially all')
raises(lambda: r.p_night_disturbed(-1), 'a negative page rate')

q = r.longest_quiet_run(0.0, 7)
ok(abs(q['expected_longest_run'] - 7) < 1e-12,
   'with no pages the longest quiet run is the whole week')
ok(abs(q['p_at_least_two_consecutive'] - 1.0) < 1e-12, 'and two is certain')
loud = r.longest_quiet_run(20.0, 7)
ok(loud['expected_longest_run'] < 1e-6, 'with constant paging there is no run')
ok(loud['p_at_least_two_consecutive'] < 1e-6, 'and no pair of quiet nights')
one = r.longest_quiet_run(1.0, 1)
ok(abs(one['expected_longest_run'] - math.exp(-1)) < 1e-12,
   'over a single night the expected run is just the probability it is quiet')
ok(one['p_at_least_two_consecutive'] == 0.0,
   'one night cannot contain two consecutive quiet nights')
raises(lambda: r.longest_quiet_run(1.0, 0), 'a week of no nights')
mid7 = r.longest_quiet_run(1.0, 7)
ok(0 < mid7['p_at_least_two_consecutive'] < 1, 'the interesting case is interior')

# ---- the suppression result this lab exists to show -------------------------
e = r.suppression_effect(3.0, 0.5)
ok(abs(e['rate_after'] - 1.5) < 1e-12, 'halving the rate halves the rate')
ok(abs(e['page_count_reduction'] - 0.5) < 1e-12,
   'the page count falls by exactly the suppressed fraction, always')
ok(e['nights_disturbed_reduction'] < 0.25,
   'but a broken rotation gets under a quarter of its nights back, got %.3f'
   % e['nights_disturbed_reduction'])
quiet = r.suppression_effect(0.15, 0.5)
ok(quiet['nights_disturbed_reduction'] > 0.45,
   'while a quiet rotation gets nearly half of them back, got %.3f'
   % quiet['nights_disturbed_reduction'])
ok(quiet['nights_disturbed_reduction'] > e['nights_disturbed_reduction'] * 2,
   'THE RESULT: the same 50 per cent page cut buys the quiet rotation more '
   'than twice what it buys the broken one')
ok(e['two_quiet_nights_after'] > e['two_quiet_nights_before'] * 5,
   'and yet the chance of two consecutive quiet nights improves sharply, '
   'which is the third statistic and the reason none of them is sufficient '
   'alone')
ok(abs(r.suppression_effect(2.0, 0.0)['nights_disturbed_reduction']) < 1e-12,
   'suppressing nothing changes nothing')
raises(lambda: r.suppression_effect(2.0, 1.0), 'suppressing every page')
raises(lambda: r.suppression_effect(2.0, -0.1), 'a negative suppression')

# ---- controls ---------------------------------------------------------------
p = r.prove_checker_can_flag()
ok(p['verdicts']['conflicts'] > 0 and p['verdicts']['consistent'] > 0
   and p['verdicts']['not established'] > 0,
   'every verdict the checker can return is produced by some pattern')
ok(p['guidelines_tested'] == len(r.HSE), 'the guideline count is reported')
ok(p['guidelines_not_testable_here'] == len(r.UNTESTABLE_HERE),
   'and so is the count of guidelines arithmetic cannot reach')

# ---- the report -------------------------------------------------------------
buf = io.StringIO()
r.report(buf)
text = buf.getvalue()
flat = ' '.join(text.split())
ok('%%' not in text, 'no literal double percent leaks')
ok('4.48' in text, 'the naive post count is printed')
ok('nights hit' in text, 'nights disturbed is reported beside the page count')
ok('Raising a threshold removes the page and not the incident' in flat,
   'the limit of the model is stated')
ok('night off at the switch' in flat, 'singular and plural are handled')

print('rota_arithmetic: %d checks passed' % PASS[0])
sys.exit(0)
