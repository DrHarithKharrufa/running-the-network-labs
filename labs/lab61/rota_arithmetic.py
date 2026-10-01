#!/usr/bin/env python3
"""Lab 61.2 --- what a 24/7 rota actually costs, and why cutting the page count
is not the same as letting people sleep.

Chapter 61 says fatigue is an operational risk, that on-call should be bounded,
and that the page rate is the metric you manage down. All three are right and
none of them is a number. This lab supplies the numbers, and two of them are
uncomfortable:

  * A SINGLE PERSON ON DUTY ROUND THE CLOCK IS NOT FOUR PEOPLE. 168 hours a week
    against a 37.5-hour contract is 4.48 posts before anybody takes leave, falls
    sick or goes on a course --- and UK statutory leave alone is 5.6 weeks.
  * HALVING THE PAGES BARELY HELPS THE ROTATIONS THAT NEED IT MOST. Nights
    disturbed is not proportional to pages received. On a quiet rotation the two
    move together; on a noisy one, halving the page count leaves almost every
    night still broken, so the metric improves while the people do not.

    python3 rota_arithmetic.py
    python3 rota_arithmetic.py --json
    python3 test_rota_arithmetic.py

Offline calculation. Every probability here is computed in closed form, not
simulated, so there is no seed and no sampling error. It models no real team.

The shift-design guidelines it checks against are quoted from the HSE's
published good-practice guidelines (see HSE_SOURCE below), which summarise
'Managing Shift Work: Health and Safety Guidance' (HSE Books 2006, ISBN
0 7176 6197 0). They are guidance, not the Working Time Regulations, and this
lab is not legal advice: a real rota is checked against the working-time rules
that bind you, your own risk assessment and your workers.
"""
import json
import math
import sys

HSE_SOURCE = ('https://www.hse.gov.uk/humanfactors/topics/'
              'good-practice-guidelines.htm')

# Quoted verbatim from that page, read 23 September 2026. Only the guidelines
# this lab can actually test are listed; the page carries others about the work
# environment, health assessments and vulnerable workers that no arithmetic
# here can check, and the lab says so rather than passing them silently.
HSE = {
    'rotation_speed': 'either rotate shifts every 2-3 days or every 3-4 weeks '
                      '- otherwise adopt forward rotating shifts',
    'permanent_nights': 'offer a choice of permanent or rotating shifts and try '
                        'to avoid permanent night shifts',
    'shift_length': 'limit shifts to 12h including overtime, or to 8h if they '
                    'are night shifts and/or the work is demanding, monotonous, '
                    'dangerous and/or safety critical',
    'consecutive': 'limit consecutive work days to a maximum of 5-7 days and '
                   'restrict long shifts, night shifts and early morning shifts '
                   'to 2-3 consecutive shifts',
    'switch_recovery': 'allow 2 nights full sleep when switching from day to '
                       'night shifts and vice versa',
    'free_weekends': 'build regular free weekends into the shift schedule',
    'early_starts': 'avoid early morning starts and try to fit shift times in '
                    'with the availability of public transport',
    'oncall_control': 'control overtime, shift swapping and on-call duties and '
                      'discourage workers from taking second jobs',
    'handover_time': 'set standards and allow time for communication at shift '
                     'handovers',
}

UNTESTABLE_HERE = ('workload variety', 'facilities and training time',
                   'temperature and lighting', 'supervisor training',
                   'supervision during low alertness', 'vulnerable workers',
                   'health assessments for night workers', 'lone-worker contact',
                   'a well lit, safe and secure workplace')

HOURS_PER_WEEK = 168.0
UK_STATUTORY_LEAVE_WEEKS = 5.6      # gov.uk: 28 days for a 5-day week


class RotaError(ValueError):
    """Raised when a rota cannot be costed honestly from what was given."""


def coverage_posts(on_duty=1, contracted_hours=37.5,
                   leave_weeks=UK_STATUTORY_LEAVE_WEEKS, training_weeks=1.0,
                   sickness_rate=0.03, other_absence_weeks=0.0):
    """Full-time equivalents needed to keep `on_duty` people on duty, always.

    The naive figure everybody quotes is 168/contracted. The real one divides
    that again by the fraction of the year a person is actually available, and
    that second division is where rotas fail --- it is invisible until the first
    week when two people are on leave and one is on a course.
    """
    if on_duty <= 0:
        raise RotaError('a rota with nobody on duty is not a rota')
    if not 0 < contracted_hours <= HOURS_PER_WEEK:
        raise RotaError('contracted hours must be positive and under 168')
    for name, weeks in (('leave_weeks', leave_weeks),
                        ('training_weeks', training_weeks),
                        ('other_absence_weeks', other_absence_weeks)):
        if weeks < 0:
            raise RotaError('%s cannot be negative' % name)
    if not 0 <= sickness_rate < 1:
        raise RotaError('sickness_rate is a fraction of the year below 1')
    absent = leave_weeks + training_weeks + other_absence_weeks
    if absent >= 52:
        raise RotaError('the absence allowances consume the whole year; '
                        'no headcount covers this')
    available = (52 - absent) / 52.0 * (1 - sickness_rate)
    if available <= 0:
        raise RotaError('nobody is available for any of the year')
    naive = on_duty * HOURS_PER_WEEK / contracted_hours
    return dict(on_duty=on_duty,
                naive_posts=naive,
                availability=available,
                posts_required=naive / available,
                weeks_absent_per_person=absent,
                note=('The naive figure assumes nobody is ever away. The '
                      'difference between the two numbers is the relief cover '
                      'that has to exist somewhere, and if it is not in the '
                      'headcount it is in overtime.'))


def check_pattern(night_shift_hours, day_shift_hours, consecutive_nights,
                  consecutive_work_days, rotation_period_days, forward_rotating,
                  free_weekends_per_period, permanent_nights=False,
                  nights_off_when_switching=None, earliest_start_hour=None,
                  handover_minutes=None, safety_critical=True):
    """Compare a proposed pattern with the HSE guidelines this lab can test.

    Returns one row per guideline with a verdict of 'conflicts', 'consistent'
    or 'not established', and the guideline's own words. 'not established' is a
    real answer and is used whenever the caller did not supply the input the
    guideline needs --- a checker that silently passes what it was not told is
    the failure this book calls fail-open.
    """
    rows = []

    def row(key, verdict, detail):
        rows.append(dict(guideline=key, text=HSE[key], verdict=verdict,
                         detail=detail))

    limit = 8  # HSE guidance: night work itself calls for the shorter limit
    if night_shift_hours is None:
        row('shift_length', 'not established', 'no night shift length given')
    elif night_shift_hours > limit:
        row('shift_length', 'conflicts',
            'night shift is %g h against a %d h guideline for this work'
            % (night_shift_hours, limit))
    else:
        row('shift_length', 'consistent',
            'night shift %g h, within %d h' % (night_shift_hours, limit))
    day_limit = 8 if safety_critical else 12
    if day_shift_hours is None:
        row('shift_length', 'not established', 'no day shift length given')
    elif day_shift_hours > day_limit:
        row('shift_length', 'conflicts',
            'day shift is %g h against a %d h guideline for this work'
            % (day_shift_hours, day_limit))
    else:
        row('shift_length', 'consistent',
            'day shift %g h, within %d h' % (day_shift_hours, day_limit))

    if permanent_nights:
        row('permanent_nights', 'conflicts',
            'the pattern assigns permanent nights')
    else:
        row('permanent_nights', 'consistent', 'nights are rotated')

    if rotation_period_days is None:
        row('rotation_speed', 'not established', 'no rotation period given')
    elif 2 <= rotation_period_days <= 3 or 21 <= rotation_period_days <= 28:
        row('rotation_speed', 'consistent',
            'a %g-day rotation is inside one of the two recommended bands'
            % rotation_period_days)
    elif forward_rotating:
        row('rotation_speed', 'consistent',
            'a %g-day rotation is between the two bands, but rotates forward, '
            'which the guideline offers as the alternative'
            % rotation_period_days)
    else:
        row('rotation_speed', 'conflicts',
            'a %g-day backward rotation is neither 2-3 days, nor 3-4 weeks, '
            'nor forward' % rotation_period_days)

    if consecutive_nights is None:
        row('consecutive', 'not established', 'no consecutive-night count given')
    elif consecutive_nights > 3:
        row('consecutive', 'conflicts',
            '%d consecutive nights against a 2-3 guideline' % consecutive_nights)
    elif consecutive_work_days is not None and consecutive_work_days > 7:
        row('consecutive', 'conflicts',
            '%d consecutive work days against a 5-7 maximum'
            % consecutive_work_days)
    else:
        row('consecutive', 'consistent',
            '%d consecutive nights, %s consecutive work days'
            % (consecutive_nights, consecutive_work_days))

    if nights_off_when_switching is None:
        row('switch_recovery', 'not established',
            'the pattern does not say what happens at a day-to-night switch')
    elif nights_off_when_switching < 2:
        row('switch_recovery', 'conflicts',
            '%g night%s off at the switch against a 2-night guideline'
            % (nights_off_when_switching,
               '' if nights_off_when_switching == 1 else 's'))
    else:
        row('switch_recovery', 'consistent',
            '%g night%s off at the switch'
            % (nights_off_when_switching,
               '' if nights_off_when_switching == 1 else 's'))

    if free_weekends_per_period is None:
        row('free_weekends', 'not established', 'no free-weekend count given')
    elif free_weekends_per_period <= 0:
        row('free_weekends', 'conflicts', 'the cycle contains no free weekend')
    else:
        row('free_weekends', 'consistent',
            '%g free weekends in the cycle' % free_weekends_per_period)

    if earliest_start_hour is None:
        row('early_starts', 'not established', 'no shift start time given')
    elif earliest_start_hour < 7:
        row('early_starts', 'conflicts',
            'earliest start is %02d:00' % earliest_start_hour)
    else:
        row('early_starts', 'consistent',
            'earliest start is %02d:00' % earliest_start_hour)

    if handover_minutes is None:
        row('handover_time', 'not established',
            'the pattern allows no stated time for handover, which usually '
            'means the handover happens in unpaid overlap or not at all')
    elif handover_minutes <= 0:
        row('handover_time', 'conflicts', 'no time is allowed for handover')
    else:
        row('handover_time', 'consistent',
            '%g minutes allowed at each handover' % handover_minutes)

    return rows


def oncall_share(engineers, tiers=2, leave_weeks=UK_STATUTORY_LEAVE_WEEKS):
    """How much of the year an engineer carries a pager.

    Two numbers, because the first one is the one quoted in the meeting and the
    second is the one people live: the naive share assumes everybody is always
    there to take their turn, and the effective share is what is left when the
    rota is covered by whoever is not on leave.
    """
    if isinstance(engineers, bool) or not isinstance(engineers, int):
        raise RotaError('engineers must be a whole number of people')
    if engineers < tiers:
        raise RotaError('a %d-tier rotation needs at least %d people; with %d '
                        'somebody is on two tiers at once, which is not a '
                        'rotation, it is one person'
                        % (tiers, tiers, engineers))
    if tiers < 1:
        raise RotaError('a rotation has at least one tier')
    naive = tiers / float(engineers)
    present = (52 - leave_weeks) / 52.0
    effective_engineers = engineers * present
    if effective_engineers < tiers:
        raise RotaError('once leave is taken out there are not enough people '
                        'to fill %d tiers; the rota only works because '
                        'somebody is cancelling leave' % tiers)
    effective = tiers / effective_engineers
    return dict(engineers=engineers, tiers=tiers,
                naive_share=naive,
                naive_weeks_per_year=naive * 52,
                effective_share=effective,
                effective_weeks_per_year=effective * (52 - leave_weeks),
                one_fewer_effective=(tiers / ((engineers - 1) * present)
                                     if (engineers - 1) * present >= tiers
                                     else None),
                note=('The effective share is the one people experience, '
                      'because the weeks somebody is away still need covering '
                      'and there is nobody else to cover them.'))


def p_night_disturbed(pages_per_night):
    """Probability that at least one page arrives tonight.

    Pages are taken as a Poisson process with the given mean. That is an
    assumption, not a measurement. Clustering can change both the number
    of nights affected and the burden within them; no general ordering or
    prediction of human recovery follows from this Poisson calculation.
    """
    if pages_per_night < 0:
        raise RotaError('a page rate cannot be negative')
    return 1 - math.exp(-pages_per_night)


def longest_quiet_run(pages_per_night, nights=7):
    """Expected longest run of consecutive undisturbed nights, computed exactly.

    This is a page-free-run statistic, not a physiological recovery model.
    Two page-free nights do not prove two full nights of sleep or adequate rest.
    """
    if nights < 1:
        raise RotaError('a week has at least one night')
    q = math.exp(-pages_per_night)           # P(undisturbed)
    # dp[(run, best)] = probability, over nights processed so far
    dp = {(0, 0): 1.0}
    for _ in range(nights):
        nxt = {}
        for (run, best), p in dp.items():
            k = (run + 1, max(best, run + 1))
            nxt[k] = nxt.get(k, 0.0) + p * q
            k2 = (0, best)
            nxt[k2] = nxt.get(k2, 0.0) + p * (1 - q)
        dp = nxt
    exp_best = sum(best * p for (_, best), p in dp.items())
    p_two = sum(p for (_, best), p in dp.items() if best >= 2)
    return dict(nights=nights, p_undisturbed_night=q,
                expected_longest_run=exp_best,
                p_at_least_two_consecutive=p_two)


def suppression_effect(pages_per_night, suppressed_fraction, nights=7):
    """What removing a fraction of the pages does to the count, and to sleep.

    This is the arithmetic behind the claim that a falling page count is not
    by itself an improvement. The count is linear in the rate. Nights disturbed
    is not.
    """
    if not 0 <= suppressed_fraction < 1:
        raise RotaError('suppressed_fraction is a proportion below 1')
    after = pages_per_night * (1 - suppressed_fraction)
    b, a = p_night_disturbed(pages_per_night), p_night_disturbed(after)
    return dict(
        rate_before=pages_per_night, rate_after=after,
        pages_per_week_before=pages_per_night * nights,
        pages_per_week_after=after * nights,
        page_count_reduction=suppressed_fraction,
        nights_disturbed_before=b * nights,
        nights_disturbed_after=a * nights,
        nights_disturbed_reduction=(b - a) / b if b else 0.0,
        two_quiet_nights_before=longest_quiet_run(
            pages_per_night, nights)['p_at_least_two_consecutive'],
        two_quiet_nights_after=longest_quiet_run(
            after, nights)['p_at_least_two_consecutive'])


def prove_checker_can_flag():
    """FR-0052 inside the lab: every verdict the checker can return must be
    producible, or it is decoration.

    A pattern checker that has never returned 'conflicts' has not been shown to
    work; one that cannot return 'not established' will quietly pass whatever it
    was not told.
    """
    bad = check_pattern(night_shift_hours=12, day_shift_hours=13,
                        consecutive_nights=7, consecutive_work_days=9,
                        rotation_period_days=7, forward_rotating=False,
                        free_weekends_per_period=0, permanent_nights=True,
                        nights_off_when_switching=0, earliest_start_hour=5,
                        handover_minutes=0)
    good = check_pattern(night_shift_hours=8, day_shift_hours=8,
                         consecutive_nights=2, consecutive_work_days=4,
                         rotation_period_days=3, forward_rotating=True,
                         free_weekends_per_period=1,
                         nights_off_when_switching=2, earliest_start_hour=7,
                         handover_minutes=30)
    silent = check_pattern(night_shift_hours=None, day_shift_hours=None,
                           consecutive_nights=None, consecutive_work_days=None,
                           rotation_period_days=None, forward_rotating=False,
                           free_weekends_per_period=None)
    verdicts = {'conflicts': sum(1 for r in bad if r['verdict'] == 'conflicts'),
                'consistent': sum(1 for r in good
                                  if r['verdict'] == 'consistent'),
                'not established': sum(1 for r in silent
                                       if r['verdict'] == 'not established')}
    for name, n in verdicts.items():
        if n == 0:
            raise RotaError('the checker never returns %r, so that branch is '
                            'dead code' % name)
    if any(r['verdict'] != 'consistent' for r in good):
        raise RotaError('a pattern built to satisfy every testable guideline '
                        'did not: %s'
                        % [r['guideline'] for r in good
                           if r['verdict'] != 'consistent'])
    return dict(verdicts=verdicts, guidelines_tested=len(HSE),
                guidelines_not_testable_here=len(UNTESTABLE_HERE))


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


def report(out=None):
    out = sys.stdout if out is None else out
    proof = prove_checker_can_flag()
    out.write('Lab 61.2 --- what a 24/7 rota costs, and what cutting pages buys\n')
    out.write('=' * 74 + '\n')
    out.write('checker proved live: %s\n\n'
              % ', '.join('%s=%d' % kv for kv in sorted(proof['verdicts'].items())))

    out.write('HOW MANY PEOPLE KEEP ONE SEAT OCCUPIED, ALWAYS\n\n')
    out.write('  %-38s %8s %8s\n' % ('', 'naive', 'with cover'))
    for label, kw in (('one on duty, 37.5 h contract', {}),
                      ('two on duty, 37.5 h contract', dict(on_duty=2)),
                      ('one on duty, 40 h contract', dict(contracted_hours=40)),
                      ('one on duty, no training, no sickness',
                       dict(training_weeks=0, sickness_rate=0.0))):
        c = coverage_posts(**kw)
        out.write('  %-38s %8.2f %8.2f\n'
                  % (label, c['naive_posts'], c['posts_required']))
    c = coverage_posts()
    out.write('\n  %s\n\n' % _wrap(
        'A single seat covered round the clock is %.2f posts before anybody is '
        'ever away, and %.2f once %.1f weeks of leave, a week of training and '
        'a 3 per cent sickness allowance are taken out. A team of five is not '
        'sufficient on these average assumptions. The shortfall is about 0.29 '
        'FTE, not a whole person. A feasible rota still needs peak absence, '
        'rest, competence and handover cover; this average is not a schedule.'
        % (c['naive_posts'], c['posts_required'],
           UK_STATUTORY_LEAVE_WEEKS), 2))

    out.write('A COMMON PATTERN AGAINST THE PUBLISHED GUIDANCE\n\n')
    rows = check_pattern(night_shift_hours=12, day_shift_hours=12,
                         consecutive_nights=4, consecutive_work_days=4,
                         rotation_period_days=7, forward_rotating=False,
                         free_weekends_per_period=0,
                         nights_off_when_switching=1, earliest_start_hour=7,
                         handover_minutes=None)
    for r in rows:
        out.write('  %-18s %-16s %s\n'
                  % (r['guideline'], r['verdict'], _wrap(r['detail'], 37)))
    out.write('\n  %s\n\n' % _wrap(
        'That is four-on-four-off with twelve-hour nights and a weekly '
        'backward rotation --- a pattern in wide use. %d of the %d testable '
        'guidelines conflict with it and %d could not be established from what '
        'the pattern states. A further %d guidelines on the same page are '
        'about the workplace, training, health assessments and vulnerable '
        'workers, and no arithmetic here can check them at all.'
        % (sum(1 for r in rows if r['verdict'] == 'conflicts'), len(rows),
           sum(1 for r in rows if r['verdict'] == 'not established'),
           len(UNTESTABLE_HERE)), 2))

    out.write('WHAT A PAGER COSTS ITS CARRIER\n\n')
    out.write('  %-12s %10s %10s %12s\n'
              % ('engineers', 'quoted', 'lived', 'if one left'))
    for n in (4, 5, 6, 8, 12):
        s = oncall_share(n)
        out.write('  %-12d %9.0f%% %9.0f%% %11s\n'
                  % (n, 100 * s['naive_share'], 100 * s['effective_share'],
                     ('%.0f%%' % (100 * s['one_fewer_effective'])
                      if s['one_fewer_effective'] else 'impossible')))
    out.write('\n  %s\n\n' % _wrap(
        'Primary and secondary tiers over a weekly rotation. The quoted share '
        'assumes nobody takes leave. A six-person rotation is sold as "one '
        'week in three" and lived as one week in 2.7, and a single resignation '
        'takes it to two weeks in five.', 2))

    out.write('CUTTING THE PAGE COUNT IN HALF, ON TWO ROTATIONS\n\n')
    out.write('  %-22s %9s %9s %11s %11s\n'
              % ('rotation', 'pages/wk', 'after', 'nights hit', 'after'))
    for label, lam in (('quiet (0.15/night)', 0.15),
                       ('busy (1.0/night)', 1.0),
                       ('broken (3.0/night)', 3.0)):
        e = suppression_effect(lam, 0.5)
        out.write('  %-22s %9.1f %9.1f %11.1f %11.1f\n'
                  % (label, e['pages_per_week_before'],
                     e['pages_per_week_after'],
                     e['nights_disturbed_before'], e['nights_disturbed_after']))
    q = suppression_effect(0.15, 0.5)
    b = suppression_effect(3.0, 0.5)
    out.write('\n  %s\n' % _wrap(
        'Every row lost exactly half its pages, and each rotation got '
        'something different for it. The quiet one got %.0f per cent of its '
        'disturbed nights back, because on a quiet rotation a page and a '
        'broken night are nearly the same event. The broken one got %.0f per '
        'cent, because by then almost every night already contains a page and '
        'removing some of them changes nothing about the night.'
        % (100 * q['nights_disturbed_reduction'],
           100 * b['nights_disturbed_reduction']), 2))
    out.write('\n  %s\n' % _wrap(
        'But look at the third statistic before concluding it was wasted. On '
        'the broken rotation the chance of getting two undisturbed nights '
        'together across the week goes from %.1f per cent to %.1f per cent --- '
        'from effectively never to about one week in four. Recovery is not the '
        'average of the nights; it is whether two of them ever came together, '
        'which is the shape the published guidance on switching shifts asks '
        'for. So the same intervention looks like a triumph, a failure or a '
        'real gain depending on which of three legitimate numbers you print.'
        % (100 * b['two_quiet_nights_before'],
           100 * b['two_quiet_nights_after']), 2))
    out.write('\n  %s\n' % _wrap(
        'That is the argument against managing the page count alone, and it is '
        'not that the count is useless --- it is that it is one of at least '
        'three, and it is the only one of the three that a suppressed page '
        'improves for free. Raising a threshold removes the page and not the '
        'incident. This lab cannot tell those two apart, and neither can the '
        'dashboard.', 2))


def main(argv):
    if '--json' in argv:
        print(json.dumps(dict(
            source=HSE_SOURCE,
            controls=prove_checker_can_flag(),
            coverage={k: coverage_posts(**v) for k, v in
                      (('one_seat', {}), ('two_seats', dict(on_duty=2)))},
            pattern=check_pattern(12, 12, 4, 4, 7, False, 0,
                                  nights_off_when_switching=1,
                                  earliest_start_hour=7),
            oncall={n: oncall_share(n) for n in (4, 5, 6, 8, 12)},
            suppression={k: suppression_effect(v, 0.5) for k, v in
                         (('quiet', 0.15), ('busy', 1.0), ('broken', 3.0))},
            not_testable_here=list(UNTESTABLE_HERE)), indent=1))
        return 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
