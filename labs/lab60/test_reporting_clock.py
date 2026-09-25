#!/usr/bin/env python3
"""Tests for lab 60.3.  Run: python3 test_reporting_clock.py"""
import datetime
import io
import sys

import reporting_clock as r

PASS = [0]
H = datetime.timedelta


def ok(cond, what):
    if not cond:
        raise AssertionError(what)
    PASS[0] += 1


def raises(fn, what):
    try:
        fn()
    except r.ClockError:
        PASS[0] += 1
        return
    raise AssertionError('expected ClockError: %s' % what)


REG = r.Regime('test', 'aware', (('initial', H(hours=24)),
                                 ('full', H(hours=72))), 'nowhere')
TL = r.timeline(aware='2026-09-01T11:05:00', first_alert='2026-08-30T22:04:00')

# ---- a regime is parameters, not a hard-coded rule -------------------------
raises(lambda: r.Regime('empty', 'aware', (), 'nowhere'),
       'a regime with no steps is not a regime')
steps = REG.deadlines(TL)
ok(len(steps) == 2, 'both steps are returned')
ok(steps[0][1] == r._dt('2026-09-02T11:05:00'), '24 hours from the trigger')
ok(steps[1][1] == r._dt('2026-09-04T11:05:00'), '72 hours from the trigger')
ok(steps[0][0] == 'initial', 'each step keeps its label')
open_ended = r.Regime('shape', 'aware', (('early warning', None),), 'nowhere')
ok(open_ended.deadlines(TL)[0][1] is None,
   'a step with no published limit yields no invented date')

# ---- the clock does not start where the old text said it did ---------------
other = r.Regime('alt', 'first_alert', (('initial', H(hours=24)),), 'nowhere')
ok(other.deadlines(TL)[0][1] != REG.deadlines(TL)[0][1],
   'the same limit against a different trigger is a different deadline')
ok(other.deadlines(TL)[0][1] < REG.deadlines(TL)[0][1],
   'and reading the trigger as the first alert makes it earlier here')

# ---- refusal, not a default ------------------------------------------------
raises(lambda: REG.deadlines(r.timeline(aware=None)),
       'a missing trigger must refuse rather than fall back to another event')
raises(lambda: REG.deadlines({}),
       'an empty timeline has no trigger either')
raises(lambda: r.timeline(aware='1899-01-01T00:00:00'),
       'an implausible timestamp is rejected at entry')
ok(r.timeline(aware=None)['aware'] is None,
   'an unknown event is recorded as None, so the absence stays visible')

# ---- back-dating ------------------------------------------------------------
raises(lambda: r.check_not_backdated(TL, 'aware', r._dt('2026-08-20T00:00:00')),
       'a trigger recorded after the report was sent is not a trigger')
ok(r.check_not_backdated(TL, 'aware', r._dt('2026-09-02T00:00:00')) is True,
   'a trigger before the report is fine')
ok(r.check_not_backdated(TL, 'aware', None) is True,
   'nothing sent yet, nothing to compare')
ok(r.check_not_backdated(TL, 'absent', r._dt('2026-09-02T00:00:00')) is True,
   'an unknown trigger is handled by deadlines(), not here')

# ---- status: met, missed, silent, running ----------------------------------
d = r._dt('2026-09-02T11:05:00')
now = r._dt('2026-09-05T00:00:00')
ok(r.status(d, r._dt('2026-09-02T09:00:00'), now) == 'met', 'reported in time')
ok(r.status(d, d, now) == 'met', 'reporting exactly on the limit is met')
ok(r.status(d, r._dt('2026-09-03T11:05:00'), now).startswith('MISSED'),
   'reported late is MISSED, loudly')
ok(r.status(d, None, now).startswith('MISSED'),
   'nothing sent past the limit is MISSED, not "pending"')
ok(r.status(d, None, r._dt('2026-09-02T00:00:00')).startswith('running'),
   'before the limit it is running')
ok('remaining' in r.status(d, None, r._dt('2026-09-02T00:00:00')),
   'and says how much is left')
ok(r.status(None, None, now).startswith('no fixed limit'),
   'a step with no limit is not silently treated as met')

# ---- spans read the way a human would ---------------------------------------
ok(r._span(r._dt('2026-09-01T00:00:00'), r._dt('2026-09-01T12:00:00')) == '12.0 h',
   'short spans in hours')
ok(r._span(r._dt('2026-09-01T00:00:00'), r._dt('2026-09-05T00:00:00')) == '4.0 days',
   'long spans in days')
ok(r._span(r._dt('2026-09-05T00:00:00'), r._dt('2026-09-01T00:00:00')) == '4.0 days',
   'order does not change the magnitude')

# ---- the sensitivity table and the honest spread ---------------------------
tl = r.worked_timeline()
rows = r.trigger_sensitivity(tl, 72)
ok(len(rows) == 6, 'six events carry a timestamp in the worked timeline')
ok([x['at'] for x in rows] == sorted(x['at'] for x in rows),
   'the table is ordered by when things happened')
ok(rows[0]['event'] == 'first_malicious_activity', 'earliest first')
ok(rows[0]['arguable'] is False,
   'an act you had no knowledge of is NOT a defensible trigger, and the table '
   'says so rather than counting it in the headline')
ok(sum(1 for x in rows if x['arguable']) == 4,
   'four defensible readings were recorded')
raises(lambda: r.trigger_sensitivity(r.timeline(a=None), 72),
       'a timeline with nothing recorded gives no table')

sp = r.arguable_spread(tl, 72)
ok(sp['n_events'] == 4, 'the spread is computed over the defensible readings only')
ok(abs(sp['spread_hours'] - (66 + 16 / 60.0)) < 1e-9,
   'the spread is 66 h 16 min exactly, got %.4f' % sp['spread_hours'])
ok(0.9 < sp['spread_as_share_of_limit'] < 0.95,
   'which is about 92 per cent of the 72-hour limit itself')
ok(sp['limit_hours'] == 72.0, 'the limit is carried alongside the spread')
raises(lambda: r.arguable_spread(r.timeline(first_alert='2026-09-01T00:00:00'), 72),
       'one defensible event gives no spread, and that absence is the finding')

# ---- controls prove themselves live ----------------------------------------
proof = r.prove_clock_can_fire()
ok(all(proof.values()), 'every control in this lab is demonstrated to fire')
ok(set(proof) == {'missed_detectable', 'met_detectable', 'silence_detectable',
                  'missing_trigger_refused', 'backdating_refused'},
   'and the set of controls is enumerated, not implied')

# ---- the worked regimes are honest about what they are ---------------------
regimes = r.worked_regimes()
ok(len(regimes) == 3, 'three parameter sets')
eu = [g for g in regimes if g.jurisdiction == 'EU'][0]
ok(all(d is None for _, d in eu.steps),
   'the EU set publishes NO hour figures, because the chapter could not read '
   'the article text from the official source')
ok('read those, not this table' in eu.note,
   'and it sends the reader to the instrument instead')
bill = [g for g in regimes if 'Bill' in g.name][0]
ok('not yet law' in bill.note, 'the Bill is labelled as a Bill')
ico = regimes[0]
ok('risk threshold' in ico.note,
   'and the data-protection duty is labelled as conditional, not universal')
ok(len({g.trigger for g in regimes}) == 3,
   'three regimes, three different trigger events: the point of the lab')

# ---- the report -------------------------------------------------------------
buf = io.StringIO()
r.report(buf)
text = buf.getvalue()
flat = ' '.join(text.split())
ok('REFUSED' in text, 'the refusal is visible in the printed output')
ok('never recorded' in text, 'the unrecorded events are shown as unrecorded')
ok('It will not tell you your deadline' in flat, 'the scope is stated')
ok('%%' not in text, 'no literal double percent leaks')

print('reporting_clock: %d checks passed' % PASS[0])
sys.exit(0)
