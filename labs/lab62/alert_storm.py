#!/usr/bin/env python3
"""Lab 62.2 --- a rule evaluator, rather than a list of pre-labelled events.

THIS LAB WAS REPAIRED, NOT WITHDRAWN. As it first shipped it held a list of ten
strings, nine tagged "cause" and one tagged "symptom", and counted them:
cause-based alerting pages nine times, symptom-based pages once. No rule was
evaluated, no metric was read, and the answer was written into the fixture. The
conclusion it reached is a fair one and is kept; the demonstration was circular
and is now an evaluator.

It evaluates real rules against a real timeline of samples, and it shows three
things the original got wrong or left out:

  * THE CHAPTER'S OWN ALERT GOES SILENT WHEN THE PROBE DIES. A rule of the form
    `probe_loss_ratio > 0.02` is false when the metric is absent, so the worst
    failure --- the measurement stopping --- produces no page at all. A
    comparison operator is not a health check.
  * A PAGE IS SOMETIMES REQUIRED BEFORE ANY CUSTOMER SYMPTOM. Lost redundancy,
    a generator running out of fuel, an active compromise and the loss of
    monitoring itself all need somebody now, and a rule that pages only on
    user-visible degradation suppresses every one of them.
  * THE ALERT STORM IS SOLVED BY GROUPING AND INHIBITION, not only by refusing
    to write cause rules. Causes are worth evaluating --- they are how you
    diagnose --- and the question is what reaches a phone.

    python3 alert_storm.py
    python3 alert_storm.py --demo-original
    python3 alert_storm.py --json
    python3 test_alert_storm.py

Offline calculation over hand-written timelines. No alerting system was run and
no product's semantics are claimed; this is a model of rule evaluation, and
where it differs from your stack, your stack wins.
"""
import json
import sys

SEVERITIES = ('page', 'ticket', 'record')
KINDS = ('symptom', 'risk', 'cause')


class AlertError(ValueError):
    """Raised when a rule or timeline cannot be evaluated as given."""


class Rule(object):
    """A rule that is EVALUATED, not a label attached to an event.

    `expr` receives the sample dict for one instant and returns True, False, or
    None for 'cannot be evaluated' --- which is the case the first edition had
    no way to express and is the one that matters most.
    """

    def __init__(self, name, expr, for_seconds=0, severity='page',
                 kind='symptom', inhibited_by=(), group='default'):
        if severity not in SEVERITIES:
            raise AlertError('severity must be one of %s' % (SEVERITIES,))
        if kind not in KINDS:
            raise AlertError('kind must be one of %s' % (KINDS,))
        if for_seconds < 0:
            raise AlertError('a for-duration cannot be negative')
        if not callable(expr):
            raise AlertError('a rule needs an expression to evaluate')
        self.name = name
        self.expr = expr
        self.for_seconds = for_seconds
        self.severity = severity
        self.kind = kind
        self.inhibited_by = tuple(inhibited_by)
        self.group = group

    def __repr__(self):
        return 'Rule(%s)' % self.name


def evaluate(rules, timeline):
    """Run the rules over the timeline and return the intervals they fire in.

    A rule becomes PENDING when its expression first returns True and FIRING
    once it has been continuously true for its for-duration. An expression that
    returns None resets the pending clock and is recorded separately, because
    'I could not evaluate this' is not the same as 'this is fine' and a system
    that conflates them is the subject of this lab.
    """
    if not rules:
        raise AlertError('no rules to evaluate')
    if not timeline:
        raise AlertError('an empty timeline evaluates to nothing; that is not '
                         'a quiet network, it is no data')
    times = [t for t, _ in timeline]
    if times != sorted(times):
        raise AlertError('the timeline is not in time order')
    state = {r.name: dict(since=None, firing=False) for r in rules}
    events, unevaluable = [], []
    for t, sample in timeline:
        if not isinstance(sample, dict):
            raise AlertError('each timeline entry is (time, sample dict)')
        for rule in rules:
            val = rule.expr(sample)
            if val not in (True, False, None):
                raise AlertError('%s returned %r; an expression returns True, '
                                 'False or None' % (rule.name, val))
            st = state[rule.name]
            if val is None:
                unevaluable.append(dict(rule=rule.name, at=t))
                st['since'], st['firing'] = None, False
                continue
            if val:
                if st['since'] is None:
                    st['since'] = t
                if not st['firing'] and t - st['since'] >= rule.for_seconds:
                    st['firing'] = True
                    events.append(dict(rule=rule.name, at=t,
                                       severity=rule.severity, kind=rule.kind,
                                       group=rule.group,
                                       pending_since=st['since']))
            else:
                st['since'], st['firing'] = None, False
    return dict(events=events, unevaluable=unevaluable,
                firing_at_end=[n for n, s in state.items() if s['firing']])


def notify(events, rules, group_window=None, inhibition=True, silences=(),
           silenced_still_inhibits=True):
    """What reaches a phone, after grouping, inhibition and silences.

    Grouping collapses everything that fired in the same group into one
    notification. Inhibition drops a rule whose inhibitor is also firing ---
    the causes, when the symptom they cause is already firing. Silences
    suppress by name and are the maintenance-window mechanism.

    `silenced_still_inhibits` is the parameter that will surprise you. A
    silenced alert is usually still FIRING; it is only its notification that is
    suppressed. So it goes on inhibiting everything it inhibits, and silencing
    one symptom can take its whole group off the air. Set this False to model a
    stack that drops silenced alerts from the inhibition set instead. Find out
    which way yours behaves before you silence anything during a change.
    """
    by_name = {r.name: r for r in rules}
    firing = {e['rule'] for e in events}
    if not silenced_still_inhibits:
        firing -= set(silences)
    delivered, suppressed = [], []
    for ev in events:
        rule = by_name.get(ev['rule'])
        if rule is None:
            raise AlertError('event for unknown rule %r' % ev['rule'])
        if ev['rule'] in silences:
            suppressed.append(dict(ev, why='silenced'))
            continue
        if inhibition and any(i in firing for i in rule.inhibited_by):
            suppressed.append(dict(ev, why='inhibited by %s'
                                   % ', '.join(i for i in rule.inhibited_by
                                               if i in firing)))
            continue
        if rule.severity != 'page':
            suppressed.append(dict(ev, why='routed as %s' % rule.severity))
            continue
        delivered.append(ev)
    groups = {}
    for ev in delivered:
        groups.setdefault(ev['group'], []).append(ev)
    return dict(pages=len(groups) if group_window else len(delivered),
                notifications=[dict(group=g, rules=[e['rule'] for e in evs],
                                    at=min(e['at'] for e in evs))
                               for g, evs in sorted(groups.items())],
                delivered_events=len(delivered),
                suppressed=suppressed)


# --------------------------------------------------------------------------
# The metric the chapter's rule used, defined
# --------------------------------------------------------------------------

PROBE_DEFINITION = (
    'probe_loss_ratio{service, vantage} --- the fraction of probe packets sent '
    'from one named vantage point to one named service target that received no '
    'reply, over the trailing 60 seconds, reported once per 15 seconds by the '
    'prober. It is a RATIO in 0..1 over completed probe attempts. It is ABSENT '
    'when the prober did not run, could not resolve the target, or has not '
    'reported within two intervals --- and a rule that compares it must say '
    'what absence means, because the comparison itself says nothing.')


def loss_gt(threshold):
    """The chapter's rule, as a comparison. Note the last branch."""
    def expr(sample):
        if 'probe_loss_ratio' not in sample:
            return False          # <-- exactly what a bare comparison does
        return sample['probe_loss_ratio'] > threshold
    return expr


def loss_gt_honest(threshold):
    """The same comparison, with absence distinguished from healthy."""
    def expr(sample):
        if 'probe_loss_ratio' not in sample:
            return None           # cannot be evaluated; not the same as False
        return sample['probe_loss_ratio'] > threshold
    return expr


def absent_for(metric):
    """The companion rule the chapter's example omitted."""
    def expr(sample):
        return metric not in sample
    return expr


def probe_timeline():
    """Twenty minutes, at 60-second steps.

    Minutes 0-4 healthy. 5-7 a three-minute loss spike that recovers --- which
    a five-minute for-duration should correctly ignore. 8-11 healthy. From
    minute 12 THE PROBER ITSELF DIES and the metric is absent for the rest.
    """
    out = []
    for minute in range(21):
        t = minute * 60
        if minute < 5 or 8 <= minute < 12:
            out.append((t, dict(probe_loss_ratio=0.001)))
        elif 5 <= minute < 8:
            out.append((t, dict(probe_loss_ratio=0.06)))
        else:
            out.append((t, dict()))        # the prober is gone
    return out


# --------------------------------------------------------------------------
# One fault, evaluated from metrics rather than from labels
# --------------------------------------------------------------------------

def fault_rules():
    def sym(s):
        return s.get('probe_loss_ratio', 0.0) > 0.02
    return [
        Rule('EdgePathLoss', sym, for_seconds=120, severity='page',
             kind='symptom', group='broadband-edge'),
        Rule('LinkDown', lambda s: s.get('link_up') == 0, severity='page',
             kind='cause', inhibited_by=('EdgePathLoss',),
             group='broadband-edge'),
        Rule('BgpPeerADown', lambda s: s.get('bgp_a') == 0, severity='page',
             kind='cause', inhibited_by=('EdgePathLoss',),
             group='broadband-edge'),
        Rule('BgpPeerBDown', lambda s: s.get('bgp_b') == 0, severity='page',
             kind='cause', inhibited_by=('EdgePathLoss',),
             group='broadband-edge'),
        Rule('CoreCpuHigh', lambda s: s.get('cpu', 0) > 80, severity='ticket',
             kind='cause', group='broadband-edge'),
        Rule('IfErrorsRising', lambda s: s.get('if_err_rate', 0) > 10,
             severity='ticket', kind='cause', group='broadband-edge'),
        Rule('QueueDepthHigh', lambda s: s.get('queue_depth', 0) > 1000,
             severity='ticket', kind='cause', group='broadband-edge'),
        Rule('RouteChurn', lambda s: s.get('route_churn', 0) > 500,
             severity='ticket', kind='cause', group='broadband-edge'),
        Rule('BfdTimeout', lambda s: s.get('bfd_fails', 0) >= 3,
             severity='page', kind='cause', inhibited_by=('EdgePathLoss',),
             group='broadband-edge'),
    ]


def fault_timeline():
    """An upstream link fails at t=60 and the service degrades from t=120."""
    healthy = dict(link_up=1, bgp_a=1, bgp_b=1, cpu=20, if_err_rate=0,
                   queue_depth=10, route_churn=0, bfd_fails=0,
                   probe_loss_ratio=0.001)
    broken = dict(link_up=0, bgp_a=0, bgp_b=0, cpu=95, if_err_rate=120,
                  queue_depth=4000, route_churn=9000, bfd_fails=3,
                  probe_loss_ratio=0.18)
    return ([(0, dict(healthy)), (60, dict(broken))]
            + [(t, dict(broken)) for t in (120, 180, 240, 300)])


# --------------------------------------------------------------------------
# TE-0613: pages that must happen before any customer feels anything
# --------------------------------------------------------------------------

def risk_rules():
    return [
        Rule('RedundancyLost',
             lambda s: s.get('transits_up') is not None
             and s['transits_up'] <= 1,
             severity='page', kind='risk', group='resilience'),
        Rule('GeneratorFuelLow',
             lambda s: s.get('generator_minutes_remaining') is not None
             and s['generator_minutes_remaining'] < 90,
             severity='page', kind='risk', group='facilities'),
        Rule('ActiveCompromise',
             lambda s: bool(s.get('confirmed_intrusion')),
             severity='page', kind='risk', group='security'),
        Rule('TelemetryLost',
             lambda s: s.get('collector_series_ingested') == 0,
             severity='page', kind='risk', group='monitoring'),
        Rule('CustomerSymptom',
             lambda s: s.get('probe_loss_ratio', 0.0) > 0.02,
             severity='page', kind='symptom', group='broadband-edge'),
    ]


def risk_timeline():
    """A night in which nothing the customer can see goes wrong at all."""
    base = dict(transits_up=2, generator_minutes_remaining=100000,
                confirmed_intrusion=False, collector_series_ingested=450000,
                probe_loss_ratio=0.001)
    return [
        (0, dict(base)),
        (300, dict(base, transits_up=1)),
        (600, dict(base, transits_up=1, generator_minutes_remaining=45)),
        (900, dict(base, transits_up=1, generator_minutes_remaining=45,
                   confirmed_intrusion=True)),
        (1200, dict(base, transits_up=1, generator_minutes_remaining=45,
                    confirmed_intrusion=True, collector_series_ingested=0)),
    ]


def prove_the_evaluator_works():
    """FR-0052 inside the lab: an evaluator that cannot NOT fire proves nothing.

    Four properties, each asserted against a constructed case: a true
    expression fires, a false one does not, a for-duration actually delays, and
    an expression that returns None neither fires nor is counted as healthy.
    """
    always = Rule('always', lambda s: True, severity='page')
    never = Rule('never', lambda s: False, severity='page')
    slow = Rule('slow', lambda s: True, for_seconds=120, severity='page')
    dunno = Rule('dunno', lambda s: None, severity='page')
    tl = [(0, {}), (60, {}), (120, {}), (180, {})]
    r = evaluate([always, never, slow, dunno], tl)
    names = {e['rule'] for e in r['events']}
    if 'always' not in names:
        raise AlertError('a rule that is always true never fired')
    if 'never' in names:
        raise AlertError('a rule that is never true fired')
    if 'dunno' in names:
        raise AlertError('an unevaluable rule fired')
    if not r['unevaluable']:
        raise AlertError('an unevaluable rule was not recorded as such')
    slow_at = [e['at'] for e in r['events'] if e['rule'] == 'slow']
    if slow_at != [120]:
        raise AlertError('the for-duration did not delay the firing (got %r)'
                         % slow_at)
    flap = [(0, dict(x=1)), (60, dict(x=0)), (120, dict(x=1))]
    f = evaluate([Rule('flap', lambda s: s['x'] == 1, for_seconds=120)], flap)
    if f['events']:
        raise AlertError('a condition that went false in between still fired, '
                         'so the for-duration is not resetting')
    return dict(fires=True, stays_quiet=True, for_duration_delays=True,
                unevaluable_is_not_healthy=True, pending_resets=True)


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


def report(out=None, demo_original=False):
    out = sys.stdout if out is None else out
    proof = prove_the_evaluator_works()
    out.write('Lab 62.2 --- rules evaluated, not events pre-labelled\n')
    out.write('=' * 74 + '\n')
    out.write('evaluator proved live: %s\n\n'
              % ', '.join(sorted(k for k, v in proof.items() if v)))

    out.write('THE METRIC THE CHAPTER\'S RULE USED, DEFINED\n\n')
    out.write('  %s\n\n' % _wrap(PROBE_DEFINITION, 2))

    tl = probe_timeline()
    bare = Rule('EdgePathLoss(bare)', loss_gt(0.02), for_seconds=300)
    honest = Rule('EdgePathLoss(honest)', loss_gt_honest(0.02), for_seconds=300)
    gone = Rule('ProbeAbsent', absent_for('probe_loss_ratio'), for_seconds=120)
    r_bare = evaluate([bare], tl)
    r_both = evaluate([honest, gone], tl)
    out.write('TWENTY MINUTES: A SPIKE THAT RECOVERS, THEN THE PROBER DIES\n\n')
    out.write('  %-26s %s\n' % ('rule', 'fired at'))
    fired = {}
    for res in (r_bare, r_both):
        for e in res['events']:
            fired.setdefault(e['rule'], e['at'])
    for name in ('EdgePathLoss(bare)', 'EdgePathLoss(honest)', 'ProbeAbsent'):
        when = fired.get(name)
        out.write('  %-26s %s\n'
                  % (name, 'never' if when is None else 't+%d min' % (when // 60)))
    absent_at = fired.get('ProbeAbsent', 0)
    out.write('\n  %s\n\n' % _wrap(
        'The three-minute spike correctly produced nothing --- that is the '
        'for-duration doing its job. Then at minute 12 the prober stopped '
        'reporting and the bare rule stayed silent for the remaining nine '
        'minutes, because `probe_loss_ratio > 0.02` is FALSE when '
        'probe_loss_ratio does not exist. The service could have been down the '
        'whole time. The companion rule --- fire when the metric is absent for '
        'two minutes --- is what turns the measurement stopping into a page, '
        'and it fired at minute %d.' % (absent_at // 60), 2))
    out.write('  %s\n\n' % _wrap(
        'The honest form of the comparison returns "cannot evaluate" rather '
        'than False, and this lab counted %d such instants. A rule engine that '
        'has no way to say that will always resolve the question in the '
        'direction of silence.' % len(r_both['unevaluable']), 2))

    rules = fault_rules()
    ft = fault_timeline()
    res = evaluate(rules, ft)
    raw = notify(res['events'], rules, group_window=None, inhibition=False)
    tuned = notify(res['events'], rules, group_window=300, inhibition=True)
    out.write('ONE UPSTREAM LINK FAILS: WHAT REACHES A PHONE\n\n')
    out.write('  %-44s %s\n' % ('rules that fired (evaluated from metrics)',
                                len(res['events'])))
    out.write('  %-44s %s\n' % ('paged, no grouping and no inhibition',
                                raw['pages']))
    out.write('  %-44s %s\n' % ('paged, grouped and inhibited', tuned['pages']))
    out.write('\n  suppressed, and why:\n')
    for s in tuned['suppressed']:
        out.write('    %-18s %s\n' % (s['rule'], s['why']))
    out.write('\n  %s\n\n' % _wrap(
        'Every one of those rules was evaluated against a number, which is the '
        'difference between this and the fixture it replaces. Note what the '
        'tuning did NOT do: it did not delete the cause rules. They still '
        'fired, they are still in the record, and they are what you read while '
        'diagnosing. Grouping and inhibition decide what rings a phone; they '
        'are not an argument for collecting less.', 2))

    sil_default = notify(res['events'], rules, group_window=300,
                         inhibition=True, silences={'EdgePathLoss'})
    sil_other = notify(res['events'], rules, group_window=300, inhibition=True,
                       silences={'EdgePathLoss'}, silenced_still_inhibits=False)
    out.write('A MAINTENANCE SILENCE ON ONE ALERT, TWO PLAUSIBLE SEMANTICS\n\n')
    out.write('  %-46s %s\n' % ('silence EdgePathLoss; silenced alerts still '
                                'inhibit', '%d pages' % sil_default['pages']))
    out.write('  %-46s %s\n' % ('silence EdgePathLoss; silenced alerts stop '
                                'inhibiting', '%d pages' % sil_other['pages']))
    out.write('\n  %s\n\n' % _wrap(
        'A silenced alert is normally still FIRING --- only its notification is '
        'suppressed --- so it goes on inhibiting everything it inhibits, and '
        'silencing the one symptom took the entire group off the air: %d pages '
        'rather than %d. That is a maintenance window in which a genuine '
        'unrelated failure on the same group would have reached nobody. Find '
        'out which way your own stack behaves before you silence anything '
        'during a change, and prefer silencing the narrow thing over the thing '
        'other rules point at.' % (sil_default['pages'], sil_other['pages']), 2))

    rr = risk_rules()
    rt = risk_timeline()
    rres = evaluate(rr, rt)
    rn = notify(rres['events'], rr, group_window=300, inhibition=True)
    out.write('A NIGHT WHERE NO CUSTOMER SEES ANYTHING WRONG\n\n')
    for e in sorted(rres['events'], key=lambda e: e['at']):
        out.write('  t+%-5d %-20s %-8s %s\n'
                  % (e['at'] // 60, e['rule'], e['kind'], e['severity']))
    sym = [e for e in rres['events'] if e['kind'] == 'symptom']
    out.write('\n  %s\n\n' % _wrap(
        'Probe loss never left 0.1 per cent, so the customer-symptom rule fired '
        '%d times across the whole night, and a policy of "page only for '
        'user-affecting problems that require immediate action" would have '
        'delivered NOTHING. Four things needed somebody: the second transit '
        'went away and the service is now single-homed; the generator has 45 '
        'minutes of fuel; an intrusion was confirmed; and the collector stopped '
        'ingesting, which means every other rule on this page has quietly '
        'stopped being able to fire. %d pages, none of them a symptom.'
        % (len(sym), rn['pages']), 2))
    out.write('  %s\n\n' % _wrap(
        'So the rule is not "page only on symptoms". It is "page on a symptom '
        'the customer feels, OR on a risk that a human must act on before it '
        'becomes one" --- and the second list is short, specific and worth '
        'writing down: lost redundancy on a path with no second failure to '
        'spare, an imminent power or capacity exhaustion with a clock on it, a '
        'confirmed compromise, and the loss of the monitoring itself.', 2))

    if demo_original:
        out.write('THE FIXTURE THIS LAB SHIPPED WITH, AND WHY IT WAS REPAIRED\n\n')
        out.write('  %s\n\n' % _wrap(
            'The original held ten strings, nine tagged "cause" and one '
            'tagged "symptom", and reported that cause-based alerting pages '
            'nine times and symptom-based pages once. Both numbers are just '
            'the tags counted. No threshold was compared, no timeline was '
            'evaluated, no for-duration existed, absence of data was '
            'impossible to express, and grouping and inhibition --- which are '
            'how the problem is actually solved --- did not appear. The '
            'conclusion was reasonable and the demonstration established '
            'nothing, which is the harder kind of defect to notice because '
            'the output looks like evidence.', 2))


def main(argv):
    if '--json' in argv:
        rules, ft = fault_rules(), fault_timeline()
        res = evaluate(rules, ft)
        rr, rt = risk_rules(), risk_timeline()
        rres = evaluate(rr, rt)
        print(json.dumps(dict(
            controls=prove_the_evaluator_works(),
            probe_definition=PROBE_DEFINITION,
            bare=evaluate([Rule('bare', loss_gt(0.02), for_seconds=300)],
                          probe_timeline()),
            with_companion=evaluate(
                [Rule('honest', loss_gt_honest(0.02), for_seconds=300),
                 Rule('ProbeAbsent', absent_for('probe_loss_ratio'),
                      for_seconds=120)], probe_timeline()),
            fault=dict(fired=len(res['events']),
                       raw=notify(res['events'], rules, None, False),
                       tuned=notify(res['events'], rules, 300, True)),
            risk=dict(fired=rres['events'],
                      tuned=notify(rres['events'], rr, 300, True))),
            indent=1, default=str))
        return 0
    report(demo_original='--demo-original' in argv)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
