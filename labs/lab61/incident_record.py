#!/usr/bin/env python3
"""Lab 61.1 --- the same mistake at both ends of an incident: forcing a field
before the answer exists.

Chapter 61 asked for two things that sound like good discipline and are the
same defect wearing different clothes.

  * AT THE START: "define severity by concrete, observable customer impact, so
    it classifies itself from the facts". At 02:40 the facts are not in. A
    classifier keyed to a measured subscriber count meets an incident whose
    scope is unknown and returns the LOWEST severity, because zero confirmed
    subscribers is what an unmeasured outage looks like in the field.
  * AT THE END: "capture the cause at ticket time, because you cannot backfill
    it". Make the cause mandatory at closure and you do not get the cause. You
    get whatever the closing engineer could pick from the list at 04:00, and a
    year later that guess is the dataset the improvement programme runs on.

Both are fail-open: the process produces a confident value rather than
refusing, and nothing downstream can tell the difference between a value and a
guess.

    python3 incident_record.py
    python3 incident_record.py --demo-fail-open
    python3 incident_record.py --json
    python3 test_incident_record.py

Offline calculation over a fixed, hand-written set of worked incidents. There
is no random element and no seed. The `true_cause` field is a MODELLING DEVICE
so the lab can score the two processes; no real ticket system has it, which is
the whole problem.
"""
import json
import sys

SEVERITIES = ('SEV1', 'SEV2', 'SEV3', 'SEV4')
_ORDER = {s: i for i, s in enumerate(SEVERITIES)}     # SEV1 is most severe

TRIGGERS = ('measured impact', 'safety', 'security', 'imminent impact',
            'critical dependency lost', 'unknown scope, large upper bound')

CAUSES = ('hardware fault', 'software defect', 'configuration change',
          'third-party or upstream', 'power or environmental', 'capacity',
          'fibre or physical', 'not established')


class RecordError(ValueError):
    """Raised when a record cannot be assessed, as distinct from being unknown."""


def _worse(a, b):
    return a if _ORDER[a] <= _ORDER[b] else b


# --------------------------------------------------------------------------
# Part A: severity at the start, when the facts are not in
# --------------------------------------------------------------------------

def impact_only(obs):
    """The classifier the chapter used to recommend. Kept so it can be run.

    Severity from measured customer impact alone. Note what it does with an
    unmeasured outage: `subscribers_confirmed` is 0 or None, no threshold is
    met, and it returns the bottom of the scale with no hint that it is
    guessing.
    """
    n = obs.get('subscribers_confirmed') or 0
    if obs.get('service_down_confirmed'):
        return 'SEV1'
    if n >= 5000:
        return 'SEV1'
    if n >= 500:
        return 'SEV2'
    if n >= 50:
        return 'SEV3'
    return 'SEV4'


def classify(obs):
    """Severity as the worst of several independent triggers, with uncertainty
    carried rather than resolved.

    Measured impact is one trigger among six, not the definition. Any unknown
    input makes the classification PROVISIONAL, which is a state the process
    has to be able to represent --- an incident whose scope nobody has measured
    yet is not a small incident, it is an unmeasured one.
    """
    if not isinstance(obs, dict):
        raise RecordError('an observation must be a mapping of fields')
    fired, unknown = [], []
    sev = 'SEV4'

    n = obs.get('subscribers_confirmed')
    if n is None:
        unknown.append('subscribers_confirmed')
    else:
        if not isinstance(n, int) or isinstance(n, bool) or n < 0:
            raise RecordError('subscribers_confirmed must be a count or None')
        m = impact_only(dict(obs, subscribers_confirmed=n))
        if m != 'SEV4':
            fired.append(('measured impact', m, '%d subscribers confirmed' % n))
            sev = _worse(sev, m)

    if obs.get('safety_risk'):
        fired.append(('safety', 'SEV1', obs.get('safety_note', 'stated')))
        sev = _worse(sev, 'SEV1')
    if obs.get('security_incident'):
        fired.append(('security', 'SEV1', obs.get('security_note', 'stated')))
        sev = _worse(sev, 'SEV1')
    if obs.get('imminent_impact'):
        fired.append(('imminent impact', 'SEV2',
                      obs.get('imminent_note',
                              'impact is expected but has not arrived')))
        sev = _worse(sev, 'SEV2')
    if obs.get('redundancy_lost'):
        fired.append(('critical dependency lost', 'SEV2',
                      obs.get('redundancy_note',
                              'running without protection')))
        sev = _worse(sev, 'SEV2')

    ub = obs.get('plausible_upper_bound')
    if n is None and ub is None:
        unknown.append('plausible_upper_bound')
    elif n is None and ub is not None:
        if ub >= 5000:
            fired.append(('unknown scope, large upper bound', 'SEV1',
                          'scope unmeasured; up to %d subscribers could be '
                          'affected' % ub))
            sev = _worse(sev, 'SEV1')
        elif ub >= 500:
            fired.append(('unknown scope, large upper bound', 'SEV2',
                          'scope unmeasured; up to %d subscribers' % ub))
            sev = _worse(sev, 'SEV2')

    provisional = bool(unknown)
    return dict(severity=sev, provisional=provisional,
                triggers=fired, unknown=unknown,
                note=('PROVISIONAL: classified on incomplete facts and must be '
                      'reviewed when %s is known. Escalating on a provisional '
                      'classification is correct; waiting for the measurement '
                      'is not.' % ', '.join(unknown)) if provisional else
                     'Classified on complete facts for the triggers tested.')


def reclassify(record, new_obs, who, when, why):
    """Reclassification is a first-class operation with a history, not an edit.

    A severity that changed is one of the most useful things in the dataset ---
    it says the first assessment was made without the facts, which is normal ---
    and a system that overwrites it destroys that signal to keep one field tidy.
    """
    for field, value in (('who', who), ('when', when), ('why', why)):
        if not value or not str(value).strip():
            raise RecordError('a reclassification needs %s; an unattributed '
                              'severity change is indistinguishable from a '
                              'mistake' % field)
    before = record.get('assessment') or classify(record['observation'])
    after = classify(new_obs)
    hist = list(record.get('history', []))
    hist.append(dict(at=when, by=who, why=why,
                     was=before['severity'], now=after['severity'],
                     was_provisional=before['provisional'],
                     now_provisional=after['provisional']))
    out = dict(record)
    out['observation'] = new_obs
    out['assessment'] = after
    out['history'] = hist
    return out


# --------------------------------------------------------------------------
# Part B: cause at the end, when nobody knows yet
# --------------------------------------------------------------------------

def close_forced(incident):
    """Closure with a mandatory cause and no 'unknown' option.

    When the cause is known the engineer records it. When it is not, they pick
    the value the SYMPTOM suggested --- which is a reasonable thing to do with
    a field that will not let them leave it blank, and is why the result is so
    dangerous. The resulting distribution is not obviously broken. It is
    plausible, well spread, professional-looking and wrong.
    """
    if incident.get('cause_established'):
        return incident['true_cause']
    guess = incident.get('guess_at_closure')
    if not guess:
        raise RecordError('this incident does not say what the closing '
                          'engineer would have picked, so the forced process '
                          'cannot be modelled for it')
    return guess


def close_honest(incident):
    """Closure that can say it does not know, and be revisited."""
    if incident.get('cause_established'):
        return incident['true_cause']
    return 'not established'


def apply_review(incidents, closures):
    """Post-incident analysis revises some of the unestablished causes.

    Only the ones a review actually resolved change. A process that cannot
    accept a revision keeps the closing guess for ever.
    """
    out = list(closures)
    for i, inc in enumerate(incidents):
        if not inc.get('cause_established') and inc.get('review_resolved'):
            out[i] = inc['true_cause']
    return out


def tally(labels):
    counts = {}
    for lab in labels:
        counts[lab] = counts.get(lab, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def top_cause(labels, ignore_unknown=True):
    """What the quarterly slide says the top cause is.

    With ignore_unknown the 'not established' bar is dropped, which is what
    every dashboard does, and is how an honest dataset gets turned back into a
    dishonest headline.
    """
    counts = tally(labels)
    if ignore_unknown:
        counts.pop('not established', None)
    if not counts:
        return None, 0, 0
    total = sum(counts.values())
    name = max(counts, key=lambda k: (counts[k], k))
    return name, counts[name], counts[name] / float(total)


def worked_incidents():
    """Twenty-four Sev-1 and Sev-2 incidents over a year.

    `true_cause` is what an omniscient observer would record and no ticket
    system has. `cause_established` says whether it was actually known when the
    ticket was closed; `review_resolved` whether a later review worked it out.
    """
    def inc(i, cause, established, reviewed=False, guess=None):
        return dict(id='INC-%03d' % i, true_cause=cause,
                    cause_established=established, review_resolved=reviewed,
                    guess_at_closure=(cause if established else guess))
    # guess_at_closure is what the symptom pointed at when the ticket was
    # closed. The two values people reach for when they do not know are a
    # recent change and somebody else's network, which is why those two are
    # over-represented below.
    return [
        inc(1, 'hardware fault', True),
        inc(2, 'configuration change', True),
        inc(3, 'third-party or upstream', False, True, 'third-party or upstream'),
        inc(4, 'software defect', False, True, 'configuration change'),
        inc(5, 'configuration change', True),
        inc(6, 'fibre or physical', True),
        inc(7, 'software defect', False, False, 'hardware fault'),
        inc(8, 'capacity', False, True, 'third-party or upstream'),
        inc(9, 'third-party or upstream', False, False, 'configuration change'),
        inc(10, 'hardware fault', True),
        inc(11, 'software defect', False, True, 'configuration change'),
        inc(12, 'configuration change', True),
        inc(13, 'power or environmental', False, True, 'hardware fault'),
        inc(14, 'software defect', False, False, 'third-party or upstream'),
        inc(15, 'third-party or upstream', False, True, 'configuration change'),
        inc(16, 'capacity', False, False, 'configuration change'),
        inc(17, 'fibre or physical', True),
        inc(18, 'software defect', False, True, 'configuration change'),
        inc(19, 'third-party or upstream', False, False, 'third-party or upstream'),
        inc(20, 'configuration change', True),
        inc(21, 'software defect', False, True, 'hardware fault'),
        inc(22, 'capacity', False, False, 'configuration change'),
        inc(23, 'hardware fault', True),
        inc(24, 'third-party or upstream', False, True, 'capacity'),
    ]


def cause_comparison(incidents=None):
    """Three processes over the same incidents, scored against the truth."""
    incidents = incidents or worked_incidents()
    truth = [i['true_cause'] for i in incidents]
    forced = [close_forced(i) for i in incidents]
    honest = [close_honest(i) for i in incidents]
    revised = apply_review(incidents, honest)
    established = sum(1 for i in incidents if i['cause_established'])
    reviewed = sum(1 for i in incidents
                   if not i['cause_established'] and i.get('review_resolved'))
    return dict(
        n=len(incidents),
        known_at_closure=established,
        resolved_by_review=reviewed,
        still_unknown=len(incidents) - established - reviewed,
        truth=tally(truth), forced=tally(forced), honest=tally(honest),
        revised=tally(revised),
        forced_top=top_cause(forced), honest_top=top_cause(honest),
        revised_top=top_cause(revised), true_top=top_cause(truth),
        forced_correct=sum(1 for a, b in zip(forced, truth) if a == b),
        revised_correct=sum(1 for a, b in zip(revised, truth) if a == b))


# --------------------------------------------------------------------------
# Controls
# --------------------------------------------------------------------------

def prove_every_trigger_can_fire():
    """FR-0052 inside the lab: a trigger that no observation can fire is not a
    safeguard, it is a line in a policy document."""
    cases = {
        'measured impact': dict(subscribers_confirmed=6000),
        'safety': dict(subscribers_confirmed=0, safety_risk=True),
        'security': dict(subscribers_confirmed=0, security_incident=True),
        'imminent impact': dict(subscribers_confirmed=0, imminent_impact=True),
        'critical dependency lost': dict(subscribers_confirmed=0,
                                         redundancy_lost=True),
        'unknown scope, large upper bound': dict(plausible_upper_bound=20000),
    }
    seen = set()
    for want, obs in cases.items():
        got = [t[0] for t in classify(obs)['triggers']]
        if want not in got:
            raise RecordError('trigger %r never fired for an observation built '
                              'to fire it (got %r)' % (want, got))
        seen.update(got)
    missing = [t for t in TRIGGERS if t not in seen]
    if missing:
        raise RecordError('unreachable triggers: %s' % missing)
    # And the provisional state must be reachable AND avoidable.
    if not classify(dict(plausible_upper_bound=20000))['provisional']:
        raise RecordError('an unmeasured incident was not marked provisional')
    if classify(dict(subscribers_confirmed=10))['provisional']:
        raise RecordError('a fully measured incident was marked provisional, '
                          'so the flag means nothing')
    return dict(triggers=len(TRIGGERS), all_reachable=True,
                provisional_reachable=True, provisional_avoidable=True)


def prove_the_gap_is_real():
    """Positive control for the claim this lab prints about severity.

    The demonstration is that the impact-only classifier and the corrected one
    DISAGREE on the worked observations. If a change ever made them agree, the
    prose would still assert a gap. So the gap is measured before it is
    narrated.
    """
    rows = worked_observations()
    disagreements = [r for r in rows
                     if impact_only(r['observation'])
                     != classify(r['observation'])['severity']]
    if not disagreements:
        raise RecordError('the two classifiers agreed on every worked case, so '
                          'there is no gap to demonstrate')
    worse = [r for r in disagreements
             if _ORDER[classify(r['observation'])['severity']]
             < _ORDER[impact_only(r['observation'])]]
    if not worse:
        raise RecordError('no worked case where the impact-only classifier '
                          'UNDER-rates the incident, which is the direction '
                          'that matters')
    return dict(cases=len(rows), disagreements=len(disagreements),
                under_rated_by_impact_only=len(worse))


def worked_observations():
    """Six calls a duty engineer could take in one night."""
    return [
        dict(id='A', at='02:40',
             what='core fibre cut reported by a third party; scope not yet '
                  'measured',
             observation=dict(subscribers_confirmed=None,
                              plausible_upper_bound=18000)),
        dict(id='B', at='03:05',
             what='one of two upstream transits has dropped; traffic is '
                  'carried by the survivor',
             observation=dict(subscribers_confirmed=0, redundancy_lost=True,
                              redundancy_note='single transit remaining')),
        dict(id='C', at='03:20',
             what='authentication logs show credential stuffing against the '
                  'management plane; nothing is down',
             observation=dict(subscribers_confirmed=0, security_incident=True,
                              security_note='active against the management '
                                            'plane')),
        dict(id='D', at='03:35',
             what='a chiller has failed in a small exchange; temperature is '
                  'rising and will trip equipment within the hour',
             observation=dict(subscribers_confirmed=0, imminent_impact=True,
                              imminent_note='thermal trip expected within the '
                                            'hour')),
        dict(id='E', at='04:10',
             what='confirmed outage, 6,200 subscribers off service',
             observation=dict(subscribers_confirmed=6200)),
        dict(id='F', at='05:00',
             what='a single business customer reports slowness; nothing else '
                  'is showing',
             observation=dict(subscribers_confirmed=1)),
    ]


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


def report(out=None, demo_fail_open=False):
    out = sys.stdout if out is None else out
    triggers = prove_every_trigger_can_fire()
    gap = prove_the_gap_is_real()
    rows = worked_observations()

    out.write('Lab 61.1 --- a field forced before the answer exists\n')
    out.write('=' * 74 + '\n')
    out.write('%d triggers, all proved reachable; provisional state reachable '
              'and avoidable\n\n' % triggers['triggers'])

    out.write('ONE NIGHT, SIX CALLS\n\n')
    out.write('  %-3s %-6s %-12s %-12s %s\n'
              % ('', 'time', 'impact-only', 'all triggers', 'what fired'))
    for r in rows:
        a = impact_only(r['observation'])
        c = classify(r['observation'])
        mark = '  <--' if _ORDER[c['severity']] < _ORDER[a] else ''
        fired = ', '.join(t[0] for t in c['triggers']) or 'nothing'
        out.write('  %-3s %-6s %-12s %-12s %s%s\n'
                  % (r['id'], r['at'], a,
                     c['severity'] + ('*' if c['provisional'] else ''),
                     fired, mark))
    out.write('\n  * provisional: classified on incomplete facts\n')
    out.write('\n  %s\n\n' % _wrap(
        'The impact-only classifier under-rates %d of these %d. Call A is the '
        'one that matters: a core fibre cut at 02:40 with the scope not yet '
        'measured has zero confirmed subscribers, so a definition anchored in '
        '"concrete, observable customer impact" returns the bottom of the '
        'scale --- and the engineer who does not want to wake a director now '
        'has the rulebook agreeing with them. An unmeasured outage is not a '
        'small outage.'
        % (gap['under_rated_by_impact_only'], gap['cases']), 2))

    a = rows[0]
    first = classify(a['observation'])
    out.write('  %s\n' % _wrap(
        'What the corrected classifier does with A instead: %s Severity %s, '
        'provisional, on the trigger "%s".'
        % (first['note'], first['severity'], first['triggers'][0][0]), 2))
    later = reclassify(dict(a, assessment=first),
                       dict(a['observation'], subscribers_confirmed=310,
                            plausible_upper_bound=None),
                       who='duty manager', when='04:55',
                       why='field team confirmed only one distribution node '
                           'was fed by the cut span')
    h = later['history'][-1]
    out.write('\n  %s\n' % _wrap(
        'At 04:55 the scope arrives --- 310 subscribers, not 18,000 --- and '
        'the record is RECLASSIFIED rather than edited: %s -> %s, by %s, '
        'because %s. The provisional flag clears.'
        % (h['was'], h['now'], h['by'], h['why']), 2))
    out.write('\n  %s\n\n' % _wrap(
        'That direction is the answer to the obvious objection, which is that '
        'treating unknown scope as severe will make everything a Sev 1. It '
        'will, provisionally, for as long as the scope is unknown --- and then '
        'it comes back down with a line saying who established what and when. '
        'A provisional Sev 1 that became a Sev 3 at 04:55 is a process working '
        'correctly. A Sev 3 that was a Sev 1 all along and nobody noticed is '
        'the outage you explain to a regulator. The history line is among the '
        'most useful rows in the dataset and is invisible in any system that '
        'overwrites the field.', 2))

    c = cause_comparison()
    out.write('WHAT THE CAUSE FIELD SAYS, AND WHAT WAS TRUE\n\n')
    out.write('  %d incidents. The cause was actually known at closure for %d '
              'of them.\n' % (c['n'], c['known_at_closure']))
    out.write('  A later review worked out %d more. %d were never established.'
              '\n\n' % (c['resolved_by_review'], c['still_unknown']))
    out.write('  %-26s %-22s %-22s\n'
              % ('cause', 'forced at closure', 'recorded honestly'))
    for cause in CAUSES:
        f, hn = c['forced'].get(cause, 0), c['revised'].get(cause, 0)
        t = c['truth'].get(cause, 0)
        if not (f or hn or t):
            continue
        out.write('  %-26s %-22s %-22s   (true %d)\n'
                  % (cause, f or '-', hn or '-', t))
    ft, fc, fs = c['forced_top']
    rt, rc, rs = c['revised_top']
    tt, tc, ts = c['true_top']
    missing = [k for k in c['truth']
               if c['truth'][k] and not c['forced'].get(k)]
    out.write('\n  %s\n' % _wrap(
        'The forced process names "%s" as the top cause with %.0f per cent of '
        'the attributed incidents. The true top cause is "%s" at %.0f per '
        'cent. The honest process, after review, names "%s" --- and gets %d of '
        'the %d labels right against the forced process\'s %d.'
        % (ft, 100 * fs, tt, 100 * ts, rt, c['revised_correct'], c['n'],
           c['forced_correct']), 2))
    if missing:
        out.write('\n  %s\n' % _wrap(
            'Worse than the wrong headline: %s caused %d of these %d incidents '
            'and %s in the forced table AT ALL. A cause nobody '
            'guessed cannot be counted, so the forced dataset is not merely '
            'mis-weighted --- it is blind to whatever does not look like '
            'anything, which is the category new failure modes arrive in.'
            % (' and '.join('"%s"' % m for m in missing),
               sum(c['truth'][m] for m in missing), c['n'],
               'does not appear' if len(missing) == 1 else 'do not appear'), 2))
    out.write('\n  %s\n\n' % _wrap(
        'Nobody lied. Every one of those labels was chosen from an approved '
        'vocabulary by somebody doing their job at four in the morning, under '
        'a rule that would not let them leave the field blank. The dataset '
        'that resulted is not noisy --- noise would average out. It is biased '
        'towards whichever value is easiest to justify, and a year of it '
        'points the improvement programme at the wrong thing with a '
        'well-formatted chart.', 2))

    if demo_fail_open:
        out.write('WHAT THE DASHBOARD DOES TO THE HONEST DATASET\n\n')
        n, cnt, share = top_cause(c['revised'] and
                                  apply_review(worked_incidents(),
                                               [close_honest(i) for i in
                                                worked_incidents()]),
                                  ignore_unknown=True)
        unk = c['revised'].get('not established', 0)
        out.write('  %s\n\n' % _wrap(
            'Drop the "not established" bar --- which every chart does, '
            'because it is not a cause --- and %d incidents leave the '
            'denominator silently. "%s" is then reported as %.0f per cent of '
            'causes, of the %d that remain. The honest chart keeps the bar, '
            'and its height is the most actionable number on the slide: it is '
            'the amount of the operation nobody understands.'
            % (unk, n, 100 * share, c['n'] - unk), 2))

    out.write('WHAT THIS LAB WILL NOT DO\n\n')
    out.write('  %s\n' % _wrap(
        'It will not give you severity thresholds. The subscriber counts in '
        'here are placeholders; yours come from your own service definitions '
        'and obligations. What transfers is the shape: severity is the worst '
        'of several independent triggers rather than one measurement, an '
        'unmeasured incident is marked provisional rather than rated low, and '
        'both severity and cause can be revised with a history rather than '
        'edited.', 2))


def main(argv):
    if '--json' in argv:
        print(json.dumps(dict(
            controls=dict(triggers=prove_every_trigger_can_fire(),
                          gap=prove_the_gap_is_real()),
            calls=[dict(id=r['id'], what=r['what'],
                        impact_only=impact_only(r['observation']),
                        classified=classify(r['observation']))
                   for r in worked_observations()],
            causes=cause_comparison()), indent=1, default=str))
        return 0
    report(demo_fail_open='--demo-fail-open' in argv)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
