#!/usr/bin/env python3
"""Lab 61.3 --- what an operating model actually moves, counted rather than
argued.

Chapter 61 offered three NOC models and two structural options, and described
them in adjectives. This lab describes them in a responsibility matrix and two
counts, because two of the chapter's claims turn out to be wrong once counted:

  * FOLLOW-THE-SUN DOES NOT MEAN NOBODY WORKS NIGHTS. It ends scheduled night
    shifts for whichever tier actually moved. If the deep-knowledge tier stayed
    in one place --- which the same chapter recommends --- then every incident
    needing that tier still wakes somebody, and follow-the-sun removed none of
    those wake-ups.
  * FOLLOW-THE-SUN DOES NOT ADD HANDOVERS. A single-site 24/7 NOC on eight-hour
    shifts already has three a day. The count is identical. What changes is the
    KIND of boundary, and that is the thing to argue about --- not the number,
    which the chapter got the wrong way round.

    python3 coverage_models.py
    python3 coverage_models.py --json
    python3 test_coverage_models.py

Offline calculation in closed form. The duty list and the incident profile are
worked examples; substitute your own and the arithmetic still holds.
"""
import json
import sys

# The things somebody must be holding at 3 a.m. A model is a statement about
# who holds each of these, not about how the org chart is drawn.
DUTIES = (
    'notice it',
    'triage and gather facts',
    'decide whether to act now',
    'make a change on the production network',
    'commit the operator to a customer or a regulator',
    'diagnose something nobody has seen before',
    'own the permanent fix',
)

WHO = ('first line', 'owning engineer', 'duty manager', 'nobody, until morning')


class ModelError(ValueError):
    """Raised when a model is described too loosely to be assessed."""


class Model(object):
    """An operating model reduced to what decides the night."""

    def __init__(self, name, first_line_hours, first_line_sites,
                 deep_tier_sites, deep_tier_in_house, holders,
                 authority_in_house=True):
        if first_line_hours not in (8, 12, 24):
            raise ModelError('first_line_hours must be 8, 12 or 24 --- the '
                             'hours a day the first line is staffed')
        if first_line_sites < 1 or deep_tier_sites < 1:
            raise ModelError('a model has at least one site per tier')
        missing = [d for d in DUTIES if d not in holders]
        if missing:
            raise ModelError('the model does not say who holds: %s. A duty '
                             'nobody was assigned is held by whoever is '
                             'nearest at 3 a.m., which is not a model'
                             % ', '.join(missing))
        bad = {d: w for d, w in holders.items() if w not in WHO}
        if bad:
            raise ModelError('unknown holders: %s' % bad)
        self.name = name
        self.first_line_hours = first_line_hours
        self.first_line_sites = first_line_sites
        self.deep_tier_sites = deep_tier_sites
        self.deep_tier_in_house = deep_tier_in_house
        self.holders = dict(holders)
        self.authority_in_house = authority_in_house

    # -- coverage -------------------------------------------------------
    def scheduled_night_shifts(self):
        """Night shifts the model requires somebody to work, per site per day.

        A site staffed 24 hours works nights. A site staffed 8 or 12 hours in
        its own daytime does not. This is the ONLY thing follow-the-sun changes
        about coverage, and it changes it completely.
        """
        first = 1 if self.first_line_hours == 24 else 0
        return dict(first_line_sites_working_nights=first * self.first_line_sites,
                    deep_tier_scheduled_nights=0,
                    note=('The deep tier is never scheduled for nights in any '
                          'of these models. It is woken, which is a different '
                          'thing and is counted separately.'))

    def handovers_per_day(self):
        """Shift handovers a day, across the whole operation.

        Counted honestly: a 24-hour site on eight-hour shifts hands over three
        times a day whether those shifts are in one building or three
        continents.
        """
        if self.first_line_sites > 1:
            total = self.first_line_sites       # one handover per site per day
        elif self.first_line_hours == 24:
            total = 24 // 8                     # three eight-hour shifts
        else:
            total = 1                           # into and out of on-call
        return dict(total=total,
                    interval_hours=24.0 / total,
                    crosses_organisation=not self.deep_tier_in_house,
                    crosses_timezone=self.first_line_sites > 1)


def residual_night_wakeups(model, incidents_per_week, fraction_needing_deep,
                           working_hours_per_site=9.0):
    """Calls the deep tier still takes outside working hours, and at night.

    An incident reaches the deep tier when it needs the deep tier AND no site
    holding that tier is at work. With S sites each working H hours a day,
    evenly spread, the clock is covered for min(1, S*H/24) of the day; the
    remainder is somebody's evening or somebody's night.

    Two numbers, because they are different harms. An evening call interrupts a
    life; a night call costs sleep that the shift-work guidance says cannot be
    made up on demand. Follow-the-sun moves the FIRST LINE around the clock; it
    moves neither of these unless the deep tier moved too.
    """
    if incidents_per_week < 0:
        raise ModelError('an incident rate cannot be negative')
    if not 0 <= fraction_needing_deep <= 1:
        raise ModelError('fraction_needing_deep is a proportion')
    if not 0 < working_hours_per_site <= 24:
        raise ModelError('working_hours_per_site must be between 0 and 24')
    covered = min(1.0, model.deep_tier_sites * working_hours_per_site / 24.0)
    out_of_hours = 1.0 - covered
    # The night window, 23:00-07:00, is a third of the clock. A site at work
    # during part of it shrinks the uncovered night in the same proportion.
    night = min(8.0 / 24.0, out_of_hours)
    need = incidents_per_week * fraction_needing_deep
    return dict(incidents_per_week=incidents_per_week,
                needing_deep_tier=need,
                deep_tier_sites=model.deep_tier_sites,
                working_hours_per_site=working_hours_per_site,
                clock_covered=covered,
                out_of_hours_fraction=out_of_hours,
                night_fraction=night,
                out_of_hours_calls_per_week=need * out_of_hours,
                wakeups_per_week=need * night,
                note=('Follow-the-sun removes scheduled night SHIFTS. It '
                      'removes a night WAKE-UP only for a tier that moved.'))


def boundaries_crossed(duration_hours, handovers_per_day):
    """Expected shift boundaries an incident of this length crosses.

    Uniform arrival, evenly spaced handovers. The result depends only on how
    often handovers happen, not on where the people are --- which is the point.
    """
    if duration_hours < 0:
        raise ModelError('an incident cannot last a negative time')
    if handovers_per_day <= 0:
        return dict(handovers_per_day=handovers_per_day, expected=0.0,
                    p_at_least_one=0.0,
                    note='no handovers: one team carries it throughout')
    gap = 24.0 / handovers_per_day
    return dict(handovers_per_day=handovers_per_day,
                interval_hours=gap,
                expected=duration_hours / gap,
                p_at_least_one=min(1.0, duration_hours / gap),
                note=('Identical for a single-site rota and a three-continent '
                      'one with the same handover interval.'))


def responsibility_matrix(model):
    """Who holds each duty, and whether they can act on it.

    The column that matters is the last one. A duty held by somebody without
    the authority to act on it is not held.
    """
    rows = []
    for duty in DUTIES:
        who = model.holders[duty]
        if who == 'nobody, until morning':
            authority = 'n/a'
            gap = True
        elif duty == 'commit the operator to a customer or a regulator':
            authority = 'yes' if (who == 'duty manager'
                                  and model.authority_in_house) else 'NO'
            gap = authority == 'NO'
        elif duty == 'make a change on the production network':
            authority = 'yes' if who != 'first line' or model.deep_tier_in_house \
                else 'contractual'
            gap = False
        elif duty == 'diagnose something nobody has seen before':
            authority = 'yes' if who == 'owning engineer' else 'NO'
            gap = authority == 'NO'
        else:
            authority = 'yes'
            gap = False
        rows.append(dict(duty=duty, holder=who, can_act=authority, gap=gap))
    return rows


def worked_models():
    base = {
        'notice it': 'first line',
        'triage and gather facts': 'first line',
        'decide whether to act now': 'duty manager',
        'make a change on the production network': 'owning engineer',
        'commit the operator to a customer or a regulator': 'duty manager',
        'diagnose something nobody has seen before': 'owning engineer',
        'own the permanent fix': 'owning engineer',
    }
    outsourced = dict(base)
    outsourced['decide whether to act now'] = 'first line'
    outsourced['diagnose something nobody has seen before'] = 'first line'
    embedded = dict(base)
    embedded['notice it'] = 'owning engineer'
    embedded['triage and gather facts'] = 'owning engineer'
    embedded['decide whether to act now'] = 'owning engineer'
    gap = dict(base)
    gap['own the permanent fix'] = 'nobody, until morning'
    return [
        Model('centralised 24/7, one site', 24, 1, 1, True, base),
        Model('embedded, you-run-it', 12, 1, 1, True, embedded),
        Model('hybrid, outsourced first line', 24, 1, 1, False, outsourced,
              authority_in_house=True),
        Model('follow-the-sun, three sites', 12, 3, 1, True, base),
        Model('follow-the-sun, deep tier also moved', 12, 3, 3, True, base),
        Model('centralised, no fix owner named', 24, 1, 1, True, gap),
    ]


def prove_the_models_differ():
    """Positive control: if every model produced the same numbers, the lab
    would be printing a table that proves nothing."""
    models = worked_models()
    nights = {m.name: m.scheduled_night_shifts()[
        'first_line_sites_working_nights'] for m in models}
    wakes = {m.name: round(residual_night_wakeups(m, 20, 0.30)[
        'out_of_hours_calls_per_week'], 4) for m in models}
    if len(set(nights.values())) < 2:
        raise ModelError('every model schedules the same night shifts')
    if len(set(wakes.values())) < 2:
        raise ModelError('every model produces the same wake-up count')
    gaps = {m.name: sum(1 for r in responsibility_matrix(m) if r['gap'])
            for m in models}
    if not any(gaps.values()):
        raise ModelError('no worked model has an authority gap, so the gap '
                         'column has never been shown to work')
    if all(gaps.values()):
        raise ModelError('every worked model has a gap, so the column cannot '
                         'distinguish anything')
    return dict(night_shift_values=sorted(set(nights.values())),
                wakeup_values=sorted(set(wakes.values())),
                models_with_gaps=sum(1 for v in gaps.values() if v))


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
    proof = prove_the_models_differ()
    models = worked_models()
    out.write('Lab 61.3 --- what an operating model moves, counted\n')
    out.write('=' * 74 + '\n')
    out.write('control: the models produce %d distinct night-shift counts and '
              '%d distinct wake-up rates\n\n'
              % (len(proof['night_shift_values']), len(proof['wakeup_values'])))

    out.write('20 INCIDENTS A WEEK, 30 PER CENT OF THEM NEEDING THE DEEP TIER\n\n')
    out.write('  %-38s %7s %7s %9s %8s\n'
              % ('model', 'night', 'hand-', 'deep-tier', 'of which'))
    out.write('  %-38s %7s %7s %9s %8s\n'
              % ('', 'shifts', 'overs', 'calls/wk', 'at night'))
    for m in models[:5]:
        n = m.scheduled_night_shifts()['first_line_sites_working_nights']
        h = m.handovers_per_day()['total']
        r = residual_night_wakeups(m, 20, 0.30)
        out.write('  %-38s %7d %7d %9.1f %8.1f\n'
                  % (m.name, n, h, r['out_of_hours_calls_per_week'],
                     r['wakeups_per_week']))

    fts = residual_night_wakeups(models[3], 20, 0.30)['wakeups_per_week']
    cen = residual_night_wakeups(models[0], 20, 0.30)['wakeups_per_week']
    out.write('\n  %s\n\n' % _wrap(
        'Read the last two columns together. Follow-the-sun with three sites '
        'takes scheduled night shifts to zero --- that part of the pitch is '
        'true and it is worth a great deal. It takes deep-tier wake-ups from '
        '%.1f a week to %.1f a week: it does not move them at all, because the '
        'engineers who understand the network did not move. The same chapter '
        'that recommends follow-the-sun also recommends keeping the '
        'deep-knowledge escalation in-house, and those two recommendations '
        'cancel on exactly this line.' % (cen, fts), 2))
    moved = residual_night_wakeups(models[4], 20, 0.30)['wakeups_per_week']
    out.write('  %s\n\n' % _wrap(
        'Move the deep tier as well and the wake-ups fall to %.1f a week --- '
        'but that is a different decision with a different price, because now '
        'three sites each need enough of the rare knowledge to diagnose '
        'something nobody has seen before, which is the thing that was scarce '
        'in the first place.' % moved, 2))

    out.write('AND THE HANDOVER COUNT, WHICH THE CHAPTER HAD BACKWARDS\n\n')
    a = models[0].handovers_per_day()
    b = models[3].handovers_per_day()
    out.write('  %-38s %d a day, %s\n'
              % ('centralised 24/7 on eight-hour shifts', a['total'],
                 'one site, one employer'))
    out.write('  %-38s %d a day, %s\n'
              % ('follow-the-sun, three sites', b['total'],
                 'three sites, three time zones'))
    ten = boundaries_crossed(10, a['total'])
    out.write('\n  %s\n\n' % _wrap(
        'The counts are the same, and so is the exposure: an incident lasting '
        '10 hours crosses %.2f boundaries on either model, because both hand '
        'over every %.0f hours. So "follow-the-sun multiplies the handover '
        'problem" is not true as arithmetic. What it multiplies is the '
        'DIFFICULTY of each boundary --- the incoming shift has no overlap '
        'with the outgoing one\'s working day, may work for a different '
        'company, and cannot lean over and ask. Argue about that, and stop '
        'counting.' % (ten['expected'], ten['interval_hours']), 2))

    out.write('WHO HOLDS WHAT, WHICH IS THE PART A MODEL IS ACTUALLY FOR\n\n')
    for m in (models[2], models[5]):
        out.write('  %s\n' % m.name)
        for r in responsibility_matrix(m):
            flag = '   <-- GAP' if r['gap'] else ''
            out.write('    %-48s %-22s %-4s%s\n'
                      % (r['duty'], r['holder'], r['can_act'], flag))
        out.write('\n')
    out.write('  %s\n' % _wrap(
        'The outsourced model is not condemned by that table --- plenty of '
        'operators run one well. It is DESCRIBED by it: the two duties marked '
        'as gaps are the ones the contract has to buy back explicitly, and an '
        'operator who has not noticed they are gaps has not bought them. The '
        'second table is the commoner failure: every duty assigned, every duty '
        'actionable, and the permanent fix owned by nobody until morning --- '
        'which is how the same incident recurs for a year.', 2))
    out.write('\n  %s\n' % _wrap(
        'Fill this matrix in for your own operation before choosing between '
        'the models in this chapter. The model is a consequence of where the '
        'duties can honestly sit, not a thing you pick first.', 2))


def main(argv):
    if '--json' in argv:
        models = worked_models()
        print(json.dumps(dict(
            control=prove_the_models_differ(),
            models=[dict(name=m.name,
                         nights=m.scheduled_night_shifts(),
                         handovers=m.handovers_per_day(),
                         wakeups=residual_night_wakeups(m, 20, 0.30),
                         matrix=responsibility_matrix(m)) for m in models],
            boundaries={h: boundaries_crossed(10, h) for h in (1, 2, 3, 6)}),
            indent=1))
        return 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
