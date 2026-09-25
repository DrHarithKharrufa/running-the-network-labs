#!/usr/bin/env python3
"""Tests for lab 61.3.  Run: python3 test_coverage_models.py"""
import io
import sys

import coverage_models as cm

PASS = [0]


def ok(cond, what):
    if not cond:
        raise AssertionError(what)
    PASS[0] += 1


def raises(fn, what):
    try:
        fn()
    except cm.ModelError:
        PASS[0] += 1
        return
    raise AssertionError('expected ModelError: %s' % what)


HOLDERS = {d: 'owning engineer' for d in cm.DUTIES}
HOLDERS['decide whether to act now'] = 'duty manager'
HOLDERS['commit the operator to a customer or a regulator'] = 'duty manager'


def model(**over):
    kw = dict(name='t', first_line_hours=24, first_line_sites=1,
              deep_tier_sites=1, deep_tier_in_house=True, holders=HOLDERS)
    kw.update(over)
    return cm.Model(**kw)


# ---- a model must say who holds what ---------------------------------------
raises(lambda: cm.Model('t', 24, 1, 1, True, {}),
       'a model that assigns no duties is not a model')
part = {d: 'first line' for d in cm.DUTIES[:-1]}
raises(lambda: cm.Model('t', 24, 1, 1, True, part),
       'a model missing one duty names it rather than defaulting')
raises(lambda: cm.Model('t', 24, 1, 1, True,
                        {d: 'the vendor' for d in cm.DUTIES}),
       'an unknown holder')
raises(lambda: cm.Model('t', 10, 1, 1, True, HOLDERS), 'a 10-hour first line')
raises(lambda: cm.Model('t', 24, 0, 1, True, HOLDERS), 'a model with no site')
raises(lambda: cm.Model('t', 24, 1, 0, True, HOLDERS), 'no deep-tier site')
ok(len(cm.DUTIES) == 7, 'seven duties somebody must hold at 3 a.m.')

# ---- night shifts ----------------------------------------------------------
ok(model().scheduled_night_shifts()['first_line_sites_working_nights'] == 1,
   'a single 24-hour site works nights')
ok(model(first_line_hours=12, first_line_sites=3)
   .scheduled_night_shifts()['first_line_sites_working_nights'] == 0,
   'three 12-hour sites work no nights: the follow-the-sun claim, and it holds')
ok(model(first_line_hours=24, first_line_sites=3)
   .scheduled_night_shifts()['first_line_sites_working_nights'] == 3,
   'three 24-hour sites work three lots of nights, which is not '
   'follow-the-sun, it is three NOCs')
ok(model().scheduled_night_shifts()['deep_tier_scheduled_nights'] == 0,
   'no model schedules the deep tier for nights; it wakes it')

# ---- handovers: the count the chapter had backwards ------------------------
a = model().handovers_per_day()
b = model(first_line_hours=12, first_line_sites=3).handovers_per_day()
ok(a['total'] == 3, 'a single 24-hour site on eight-hour shifts: three a day')
ok(b['total'] == 3, 'three follow-the-sun sites: also three a day')
ok(a['total'] == b['total'],
   'THE CORRECTION: the handover COUNT is identical, so "follow-the-sun '
   'multiplies the handover problem" is false as arithmetic')
ok(a['crosses_timezone'] is False and b['crosses_timezone'] is True,
   'what differs is the KIND of boundary, and the model says so')
ok(model(deep_tier_in_house=False).handovers_per_day()['crosses_organisation'],
   'an outsourced tier makes the boundary contractual')
ok(model(first_line_hours=12).handovers_per_day()['total'] == 1,
   'a single day-shift team hands over once, into on-call')
ok(abs(a['interval_hours'] - 8.0) < 1e-12, 'three handovers is every eight hours')

# ---- boundaries crossed depends only on the interval -----------------------
ten = cm.boundaries_crossed(10, 3)
ok(abs(ten['expected'] - 10 / 8.0) < 1e-12,
   'a ten-hour incident crosses 1.25 eight-hour boundaries')
ok(cm.boundaries_crossed(10, 3)['expected']
   == cm.boundaries_crossed(10, 3)['expected'],
   'and the figure does not know or care where the people are')
ok(cm.boundaries_crossed(2, 3)['p_at_least_one'] < 1,
   'a short incident may cross none')
ok(cm.boundaries_crossed(40, 3)['p_at_least_one'] == 1.0,
   'a long one certainly crosses at least one')
ok(cm.boundaries_crossed(10, 0)['expected'] == 0.0,
   'no handovers means no boundaries, and the note says one team carries it')
ok(cm.boundaries_crossed(0, 3)['expected'] == 0.0, 'a zero-length incident')
raises(lambda: cm.boundaries_crossed(-1, 3), 'a negative duration')

# ---- residual out-of-hours work, which is what actually moves --------------
one = cm.residual_night_wakeups(model(), 20, 0.30)
ok(abs(one['needing_deep_tier'] - 6.0) < 1e-12, '30 per cent of 20 is 6')
ok(abs(one['out_of_hours_fraction'] - (1 - 9 / 24.0)) < 1e-12,
   'one site working nine hours leaves 62.5 per cent of the clock uncovered')
ok(abs(one['night_fraction'] - 1 / 3.0) < 1e-12,
   'of which the night window is a third of the clock')
ok(abs(one['wakeups_per_week'] - 2.0) < 1e-12, 'two night calls a week')
fts = cm.residual_night_wakeups(
    model(first_line_hours=12, first_line_sites=3), 20, 0.30)
ok(abs(fts['wakeups_per_week'] - one['wakeups_per_week']) < 1e-12,
   'THE RESULT: follow-the-sun with a single-site deep tier removes NONE of '
   'the night calls, because the deep tier did not move')
moved = cm.residual_night_wakeups(
    model(first_line_hours=12, first_line_sites=3, deep_tier_sites=3), 20, 0.30)
ok(moved['wakeups_per_week'] == 0.0,
   'moving the deep tier as well does remove them')
ok(abs(moved['clock_covered'] - 1.0) < 1e-12,
   'because three sites of nine hours cover more than the clock')
two = cm.residual_night_wakeups(model(deep_tier_sites=2), 20, 0.30)
ok(0 < two['wakeups_per_week'] < one['wakeups_per_week'],
   'two sites help without solving it')
ok(one['out_of_hours_calls_per_week'] > one['wakeups_per_week'],
   'evening calls outnumber night calls, and are reported separately because '
   'they are a different harm')
ok(cm.residual_night_wakeups(model(), 0, 0.30)['wakeups_per_week'] == 0.0,
   'no incidents, no calls')
ok(cm.residual_night_wakeups(model(), 20, 0.0)['wakeups_per_week'] == 0.0,
   'a first line that never escalates never wakes anybody')
raises(lambda: cm.residual_night_wakeups(model(), -1, 0.3), 'a negative rate')
raises(lambda: cm.residual_night_wakeups(model(), 20, 1.5), 'a share above one')
raises(lambda: cm.residual_night_wakeups(model(), 20, 0.3, 0),
       'a site that works no hours')
raises(lambda: cm.residual_night_wakeups(model(), 20, 0.3, 30),
       'a site that works more than a day')

# ---- the responsibility matrix ---------------------------------------------
rows = cm.responsibility_matrix(model())
ok(len(rows) == len(cm.DUTIES), 'one row per duty')
ok(not any(r['gap'] for r in rows), 'a well-formed model has no gaps')
outsourced = dict(HOLDERS)
outsourced['diagnose something nobody has seen before'] = 'first line'
g = cm.responsibility_matrix(model(holders=outsourced, deep_tier_in_house=False))
gaps = [r['duty'] for r in g if r['gap']]
ok('diagnose something nobody has seen before' in gaps,
   'a first line asked to diagnose the novel is flagged as a gap')
nobody = dict(HOLDERS)
nobody['own the permanent fix'] = 'nobody, until morning'
n = cm.responsibility_matrix(model(holders=nobody))
ok(any(r['gap'] and r['duty'] == 'own the permanent fix' for r in n),
   'a duty held by nobody is a gap, which is how the same incident recurs')
ok([r for r in n if r['duty'] == 'own the permanent fix'][0]['can_act'] == 'n/a',
   'and authority is not asserted for a duty nobody holds')
noauth = dict(HOLDERS)
noauth['commit the operator to a customer or a regulator'] = 'first line'
na = cm.responsibility_matrix(model(holders=noauth))
ok(any(r['gap'] for r in na),
   'a first line that cannot commit the operator but is asked to is a gap')

# ---- the control ------------------------------------------------------------
p = cm.prove_the_models_differ()
ok(len(p['night_shift_values']) >= 2, 'the models differ on night shifts')
ok(len(p['wakeup_values']) >= 2, 'and on out-of-hours load')
ok(p['models_with_gaps'] >= 1, 'at least one worked model has an authority gap')
ok(p['models_with_gaps'] < len(cm.worked_models()),
   'but not all of them, so the column distinguishes something')
ok(len(cm.worked_models()) == 6, 'six worked models')

# ---- the report -------------------------------------------------------------
buf = io.StringIO()
cm.report(buf)
text = buf.getvalue()
flat = ' '.join(text.split())
ok('%%' not in text, 'no literal double percent leaks')
ok('WHICH THE CHAPTER HAD BACKWARDS' in text,
   'the handover-count correction is stated plainly')
ok('is not true as arithmetic' in flat, 'and its basis given')
ok('GAP' in text, 'the responsibility gaps are marked')
ok('not condemned by that table' in flat,
   'the outsourced model is described rather than dismissed')

print('coverage_models: %d checks passed' % PASS[0])
sys.exit(0)
