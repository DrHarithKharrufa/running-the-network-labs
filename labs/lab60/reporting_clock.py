#!/usr/bin/env python3
"""Lab 60.3 --- which event starts the regulatory clock, and what it costs to
guess.

Chapter 60 used to say the reporting clock "starts at detection" and runs 24,
72 and 30 days.  Neither half survives contact with an actual regime.  The
trigger is a defined event that differs between regimes --- awareness of a
significant incident, classification of a major incident, awareness of a
qualifying personal-data breach --- and the limits attached to each trigger
differ with it.  Picking the wrong event does not shift a deadline by an hour;
on the incidents that matter it shifts it by days.

So this lab does not hard-code any regime.  It takes a regime as PARAMETERS
you fill in from your own obligation, and then it:

  * refuses to compute a deadline when the trigger event has no recorded
    timestamp, because a deadline you cannot evidence is not a deadline you
    can demonstrate you met;
  * shows the same incident against several parameter sets, so the reader sees
    that "24 and 72" is a property of one regime and not a fact about the
    world;
  * shows how far the deadline moves when the trigger is read as each of the
    other events in the same timeline;
  * refuses to accept a trigger timestamp recorded after the report was sent,
    which is what back-dating looks like in data.

    python3 reporting_clock.py
    python3 reporting_clock.py --json
    python3 test_reporting_clock.py

Offline calculation.  The worked parameter sets are illustrations, two of them
drawn from sources cited in the chapter and one deliberately left generic;
The alternative event calculations do not establish that each is a legally
valid trigger. Use the applicability, awareness and deadline requirements of
the governing instrument, including compound deadlines and phased updates.
"""
import datetime
import json
import sys

UTC = datetime.timezone.utc


class ClockError(ValueError):
    """Raised when no honest deadline can be derived from what was recorded."""


class Regime(object):
    """A reporting obligation reduced to the four things that decide a date."""

    def __init__(self, name, trigger, steps, jurisdiction, note=''):
        if not steps:
            raise ClockError('a regime with no reporting steps is not a regime')
        self.name = name
        self.trigger = trigger
        self.steps = tuple(steps)          # ((label, timedelta or None), ...)
        self.jurisdiction = jurisdiction
        self.note = note

    def deadlines(self, timeline):
        when = timeline.get(self.trigger)
        if when is None:
            raise ClockError(
                'regime %r starts its clock at %r, and this timeline has no '
                'recorded time for that event. The absence is the finding: '
                'record the moment, or you cannot show you met the limit even '
                'if you did.' % (self.name, self.trigger))
        out = []
        for label, delta in self.steps:
            out.append((label, None if delta is None else when + delta))
        return out


def _dt(text):
    if isinstance(text, datetime.datetime):
        return text if text.tzinfo else text.replace(tzinfo=UTC)
    return datetime.datetime.fromisoformat(text).replace(tzinfo=UTC)


def timeline(**events):
    """An incident timeline.  Unknown events are passed as None, not omitted,
    so that 'we never recorded it' is visible rather than silent."""
    out = {}
    for k, v in events.items():
        out[k] = None if v is None else _dt(v)
    ordered = [(k, v) for k, v in out.items() if v is not None]
    for k, v in ordered:
        if v.year < 2000 or v.year > 2100:
            raise ClockError('%s has an implausible timestamp: %s' % (k, v))
    return out


def status(deadline, reported_at, now):
    """Met, missed, or still running --- and never 'probably fine'."""
    if deadline is None:
        return 'no fixed limit in this parameter set'
    if reported_at is not None:
        return 'met' if reported_at <= deadline else 'MISSED by %s' % _span(
            deadline, reported_at)
    if now > deadline:
        return 'MISSED (nothing sent, %s past the limit)' % _span(deadline, now)
    return 'running, %s remaining' % _span(now, deadline)


def _span(a, b):
    total = abs((b - a).total_seconds())
    hours = total / 3600.0
    if hours < 48:
        return '%.1f h' % hours
    return '%.1f days' % (hours / 24.0)


def check_not_backdated(timeline_, trigger, reported_at):
    """A trigger recorded after the report went out is not a trigger."""
    when = timeline_.get(trigger)
    if when is None or reported_at is None:
        return True
    if when > reported_at:
        raise ClockError(
            'the recorded trigger (%s) is later than the report that was sent '
            'about it (%s). Either the clock record is wrong or it was written '
            'afterwards; both are findings, and neither produces a defensible '
            'date.' % (when.isoformat(), reported_at.isoformat()))
    return True


# The events a reasonable person could argue were "when we became aware".
# first_malicious_activity is not among them --- nobody claims the clock runs
# from an act you had no knowledge of --- and neither is containment.
ARGUABLE_TRIGGERS = ('first_alert', 'first_human_triage',
                     'aware_significant_incident', 'classified_significant',
                     'aware_personal_data_breach')


def trigger_sensitivity(timeline_, limit_hours):
    """How far the same limit moves when read from each event in the timeline.

    Two spreads are reported, because only one of them is an honest argument.
    The full spread includes events nobody would claim as the trigger and so
    overstates the case. The ARGUABLE spread covers only the readings a
    competent team could defend to each other on the night, and it is the one
    the chapter quotes.
    """
    limit = datetime.timedelta(hours=limit_hours)
    known = [(k, v) for k, v in timeline_.items() if v is not None]
    if not known:
        raise ClockError('nothing in this timeline has a timestamp')
    first_deadline = min(v for _, v in known) + limit
    rows = []
    for k, v in sorted(known, key=lambda kv: kv[1]):
        rows.append(dict(event=k, at=v.isoformat(),
                         deadline=(v + limit).isoformat(),
                         arguable=k in ARGUABLE_TRIGGERS,
                         later_than_first_by=_span(first_deadline, v + limit)))
    return rows


def arguable_spread(timeline_, limit_hours):
    """Spread over candidate event timestamps, not legally interchangeable triggers."""
    limit = datetime.timedelta(hours=limit_hours)
    times = [v for k, v in timeline_.items()
             if v is not None and k in ARGUABLE_TRIGGERS]
    if len(times) < 2:
        raise ClockError('fewer than two candidate trigger events were '
                         'recorded, so no spread can be computed --- which is '
                         'itself the finding')
    spread = max(times) - min(times)
    return dict(n_events=len(times),
                earliest=min(times).isoformat(), latest=max(times).isoformat(),
                spread_hours=spread.total_seconds() / 3600.0,
                limit_hours=float(limit_hours),
                spread_as_share_of_limit=(spread.total_seconds() / 3600.0)
                / float(limit_hours),
                note=('Choosing between two readings a competent team could '
                      'both defend moves the deadline by %.1f hours against a '
                      'limit of %.0f.'
                      % (spread.total_seconds() / 3600.0, limit_hours)))


def worked_regimes():
    """Illustrative parameter sets.

    The UK rows are the ones the chapter cites; the third is deliberately
    generic, because the chapter refuses to print hour figures for regimes
    whose article text it could not read from the official source while the
    chapter was written.
    """
    h = datetime.timedelta
    return [
        Regime('UK GDPR personal-data breach (ICO)',
               trigger='aware_personal_data_breach',
               steps=(('notify the supervisory authority', h(hours=72)),),
               jurisdiction='UK',
               note='Only a personal-data breach meeting the risk threshold is '
                    'notifiable; a decision not to notify must itself be '
                    'recorded and justified.'),
        Regime('UK Cyber Security and Resilience Bill, as introduced',
               trigger='aware_significant_incident',
               steps=(('initial notification', h(hours=24)),
                      ('full report', h(hours=72))),
               jurisdiction='UK',
               note='A Bill, not yet law, and the operative detail is to come '
                    'in secondary legislation. Track it; do not build to it.'),
        Regime('EU staged regime, shape only',
               trigger='classified_significant',
               steps=(('early warning', None),
                      ('fuller notification', None),
                      ('final report', None)),
               jurisdiction='EU',
               note='The shape is an early warning, a fuller notification and '
                    'a final report, each keyed to a defined awareness or '
                    'classification event rather than to detection. The hour '
                    'figures are set by the instrument and its national '
                    'transposition: read those, not this table.'),
    ]


def worked_timeline():
    """A slow, quiet compromise --- the kind where the trigger choice matters.

    Every field is something an operator either recorded or did not.  Two are
    None on purpose.
    """
    return timeline(
        first_malicious_activity='2026-06-02T03:11:00',
        first_alert='2026-08-30T22:04:00',
        first_human_triage='2026-08-31T08:40:00',
        aware_personal_data_breach='2026-09-02T16:20:00',
        aware_significant_incident='2026-09-01T11:05:00',
        classified_significant=None,           # nobody wrote the decision down
        contained='2026-09-04T19:30:00',
        resolved=None,
    )


def prove_clock_can_fire():
    """FR-0052 inside the lab: prove a missed deadline is actually detectable,
    and that a missing trigger raises rather than defaulting to something.

    A compliance check that cannot produce 'MISSED' is decoration.
    """
    tl = timeline(aware_significant_incident='2026-09-01T11:05:00')
    reg = Regime('proof', 'aware_significant_incident',
                 (('initial', datetime.timedelta(hours=24)),), 'n/a')
    (_, deadline), = reg.deadlines(tl)
    late = status(deadline, _dt('2026-09-03T11:05:00'), _dt('2026-09-05T00:00:00'))
    ontime = status(deadline, _dt('2026-09-02T09:00:00'), _dt('2026-09-05T00:00:00'))
    silent = status(deadline, None, _dt('2026-09-05T00:00:00'))
    if not late.startswith('MISSED') or ontime != 'met' \
            or not silent.startswith('MISSED'):
        raise ClockError('the clock cannot distinguish met from missed: %r %r %r'
                         % (ontime, late, silent))
    empty = timeline(aware_significant_incident=None)
    try:
        reg.deadlines(empty)
    except ClockError:
        pass
    else:
        raise ClockError('a missing trigger produced a deadline; the check is '
                         'fabricating dates')
    try:
        check_not_backdated(tl, 'aware_significant_incident',
                            _dt('2026-08-20T00:00:00'))
    except ClockError:
        pass
    else:
        raise ClockError('a back-dated trigger was accepted')
    return dict(missed_detectable=True, met_detectable=True,
                silence_detectable=True, missing_trigger_refused=True,
                backdating_refused=True)


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
    proof = prove_clock_can_fire()
    tl = worked_timeline()
    now = _dt('2026-09-06T09:00:00')

    out.write('Lab 60.3 --- which event starts the clock\n')
    out.write('=' * 74 + '\n')
    out.write('controls proved live: %s\n\n'
              % ', '.join(sorted(k for k, v in proof.items() if v)))

    out.write('ONE INCIDENT, AS RECORDED\n\n')
    for k, v in tl.items():
        out.write('  %-28s %s\n'
                  % (k, v.isoformat() if v else '-- never recorded --'))
    out.write('\n  %s\n\n' % _wrap(
        'The compromise began on 2 June and the first alert fired on 30 '
        'August. If the clock started at "detection" the two would be the '
        'same event, and they are 89 days apart.', 2))

    out.write('THE SAME INCIDENT AGAINST THREE PARAMETER SETS\n\n')
    for reg in worked_regimes():
        out.write('  %s  [%s]\n' % (reg.name, reg.jurisdiction))
        out.write('    trigger: %s\n' % reg.trigger)
        try:
            for label, deadline in reg.deadlines(tl):
                if deadline is None:
                    out.write('    %-26s set by the instrument; not printed here\n'
                              % label)
                else:
                    out.write('    %-26s %s   (%s)\n'
                              % (label, deadline.isoformat(),
                                 status(deadline, None, now)))
        except ClockError as exc:
            out.write('    REFUSED  %s\n' % _wrap(str(exc), 13))
        out.write('    %s\n\n' % _wrap(reg.note, 4))

    out.write('HOW FAR THE DEADLINE MOVES WITH THE TRIGGER (a 72-hour limit)\n\n')
    out.write('  %-28s %-18s %-11s %s\n'
              % ('if the trigger is read as', 'deadline becomes', 'candidate?',
                 'later than the first'))
    for row in trigger_sensitivity(tl, 72):
        out.write('  %-28s %-18s %-11s %s\n'
                  % (row['event'], row['deadline'][:16].replace('T', ' '),
                     'yes' if row['arguable'] else 'no',
                     row['later_than_first_by']))
    sp = arguable_spread(tl, 72)
    out.write('\n  %s\n' % _wrap(
        'Ignore the readings nobody would defend. Among the %d events a '
        'competent team could genuinely argue for as "when we became aware", '
        'the deadline still moves by %.1f hours --- %.0f per cent of the '
        '72-hour limit itself. The limit is the small number. The choice of '
        'event is the large one, which is why the regime names it and why your '
        'incident record has to name it too, at the time, with a person '
        'attached to the decision.'
        % (sp['n_events'], sp['spread_hours'],
           100 * sp['spread_as_share_of_limit']), 2))

    out.write('\nWHAT THIS LAB WILL NOT DO\n\n')
    out.write('  %s\n' % _wrap(
        'It will not tell you your deadline. It refused one of the three '
        'parameter sets above outright, because the decision that would have '
        'started that clock was never written down --- which is the commonest '
        'real failure and is invisible until somebody asks for the evidence.', 2))


def main(argv):
    if '--json' in argv:
        tl = worked_timeline()
        now = _dt('2026-09-06T09:00:00')
        regs = []
        for reg in worked_regimes():
            try:
                steps = [dict(step=l, deadline=(d.isoformat() if d else None),
                              status=status(d, None, now))
                         for l, d in reg.deadlines(tl)]
                refused = None
            except ClockError as exc:
                steps, refused = [], str(exc)
            regs.append(dict(name=reg.name, jurisdiction=reg.jurisdiction,
                             trigger=reg.trigger, steps=steps, refused=refused,
                             note=reg.note))
        print(json.dumps(dict(
            controls=prove_clock_can_fire(),
            timeline={k: (v.isoformat() if v else None) for k, v in tl.items()},
            regimes=regs,
            sensitivity_72h=trigger_sensitivity(tl, 72),
            arguable_spread_72h=arguable_spread(tl, 72)), indent=1))
        return 0
    report()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
