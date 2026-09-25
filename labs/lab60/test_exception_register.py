#!/usr/bin/env python3
"""Tests for lab 60.2.  Run: python3 test_exception_register.py"""
import datetime
import io
import sys

import exception_register as x

PASS = [0]


def ok(cond, what):
    if not cond:
        raise AssertionError(what)
    PASS[0] += 1


def raises(fn, what):
    try:
        fn()
    except x.RegisterError:
        PASS[0] += 1
        return
    raise AssertionError('expected RegisterError: %s' % what)


def base(**over):
    rec = dict(
        id='T-1', asset='LAB-RTR-01', requirement='patch-CVE-2026-0001',
        requirement_class='policy',
        exposure='management VLAN only',
        risk_owner=dict(name='A. Owner', role='Head of Network',
                        may_accept_risk_of_this_class=True),
        compensating_controls=[dict(control='access list',
                                    evidence='read back from the device',
                                    verified_on='2026-09-01')],
        granted='2026-06-01', expires='2026-12-01',
        review_triggers=['exploit published'],
        remediation_plan=dict(action='upgrade', by='2026-11-15',
                              owner='A. Owner'))
    rec.update(over)
    return rec


def verdict(rec, today=x.TODAY):
    return x.assess(rec, today)[0]


# ---- each verdict is produced by a record built for it ----------------------
ok(verdict(base()) == 'accepted-time-boxed', 'a complete, live, evidenced, '
   'authorised, time-boxed exception is accepted')
ok(verdict(base(exposure='')) == 'incomplete', 'a blank field is not a field')
ok(verdict({k: v for k, v in base().items() if k != 'asset'}) == 'incomplete',
   'an absent field is caught the same way as a blank one')
ok(verdict(base(requirement='incident-reporting-deadline'))
   == 'refused-non-waivable', 'a statutory deadline cannot be excepted')
ok(verdict(base(requirement='contracted-encryption-in-transit'))
   == 'refused-non-waivable', 'nor a contractual term only the counterparty '
   'can vary')
ok(verdict(base(risk_owner=dict(name='B', role='Coordinator',
                                may_accept_risk_of_this_class=False)))
   == 'refused-no-authority', 'a name without authority is not an owner')
ok(verdict(base(active_exploitation=True)) == 'escalate-active-exploitation',
   'a risk being exploited now is an incident, not a risk decision')
ok(verdict(base(expires='2026-07-01')) == 'expired',
   'an expired exception is an undocumented gap again')
ok(verdict(base(compensating_controls=[dict(control='we would notice')]))
   == 'accepted-unevidenced', 'an asserted control is not a demonstrated one')
ok(verdict(base(compensating_controls=[
    dict(control='asserted'),
    dict(control='verified', evidence='probe refused',
         verified_on='2026-09-01')])) == 'accepted-time-boxed',
   'one verified control among several is enough to clear the evidence test')
ok(verdict(base(compensating_controls=[
    dict(control='half done', evidence='someone looked')]))
   == 'accepted-unevidenced', 'evidence without a verification date does not '
   'count, because an undated check cannot be shown to be current')

# ---- the ORDER of the tests is itself the argument --------------------------
ok(verdict(base(requirement='incident-reporting-deadline',
                risk_owner=dict(name='B', role='X',
                                may_accept_risk_of_this_class=False)))
   == 'refused-non-waivable',
   'non-waivable is decided before authority: no signature would help')
ok(verdict(base(requirement='incident-reporting-deadline',
                compensating_controls=[dict(control='manual process',
                                            evidence='rehearsed',
                                            verified_on='2026-01-01')]))
   == 'refused-non-waivable',
   'no amount of compensating control makes a non-waivable requirement waivable')
ok(verdict(base(exposure='', requirement='incident-reporting-deadline'))
   == 'incomplete', 'an unassessable record is not silently refused for the '
   'wrong reason')
ok(verdict(base(active_exploitation=True, expires='2026-01-01'))
   == 'escalate-active-exploitation',
   'active exploitation outranks expiry: the incident owns it either way')
ok(verdict(base(expires='2026-07-01', compensating_controls=[
    dict(control='good one', evidence='tested', verified_on='2026-06-01')]))
   == 'expired', 'expiry is decided before the quality of the controls')

# ---- boundaries -------------------------------------------------------------
ok(verdict(base(expires='2026-09-23')) == 'accepted-time-boxed',
   'an exception expiring today has not yet expired')
ok(verdict(base(expires='2026-09-22')) == 'expired',
   'one day later it has')
ok(verdict(base(compensating_controls=[
    dict(control='c', evidence='e', verified_on='2026-09-23')]))
   == 'accepted-time-boxed', 'a control verified today counts')

# ---- things that cannot be assessed at all ---------------------------------
raises(lambda: x.assess('not a record'), 'a string is not an exception record')
raises(lambda: x.assess(base(risk_owner=dict(name='A'))),
       'a risk owner needs a role as well as a name')
raises(lambda: x.assess(base(expires='soon')), 'a non-ISO date')
raises(lambda: x.assess(base(granted='2026-12-02')),
       'an expiry before the grant is internally inconsistent')
raises(lambda: x.assess(base(compensating_controls='an access list')),
       'a string is not a list of controls')
raises(lambda: x.assess(base(compensating_controls=[dict(evidence='e')])),
       'a control with no name')
raises(lambda: x.assess(base(compensating_controls=[
    dict(control='c', evidence='e', verified_on='2027-01-01')])),
       'a control verified in the future means the clock is wrong')
raises(lambda: x.assess(base(remediation_plan=dict(action='upgrade'))),
       'a remediation plan needs a date or event as well as an action')

# ---- the fail-open register, which is the point of the comparison -----------
ok(x.complete_form_only(base(requirement='incident-reporting-deadline'))
   == 'approved', 'the form check approves excepting a statutory deadline')
ok(x.complete_form_only(base(expires='2020-01-01')) == 'approved',
   'and an exception six years expired')
ok(x.complete_form_only(base(active_exploitation=True)) == 'approved',
   'and one whose subject is being exploited today')
ok(x.complete_form_only(base(exposure='')) == 'rejected',
   'it rejects exactly one thing: a blank box')
ok(x.complete_form_only('not a record') == 'rejected', 'and a non-record')

# ---- reachability: no verdict is dead code ---------------------------------
proof = x.prove_every_verdict_reachable()
ok(proof['all_reachable'] is True, 'every verdict is produced by some record')
ok(proof['verdicts'] == len(x.VERDICTS) == 7, 'seven verdicts, all live')
ok(set(proof['cases']) == set(x.VERDICTS), 'the proof covers the whole set')
ok(all(k == v for k, v in proof['cases'].items()),
   'and each constructed record produces the verdict it was built for')

# ---- register health --------------------------------------------------------
records = x.worked_records()
h = x.register_health(records)
ok(h['total'] == len(records) == 7, 'seven worked records')
ok(sum(h['counts'].values()) + h['errors'] == h['total'],
   'every record is accounted for exactly once')
ok(h['counts']['accepted-time-boxed'] == 1, 'one clean acceptance')
ok(h['counts']['refused-non-waivable'] == 1, 'one refusal on the law')
ok(h['would_be_approved_by_form_check'] > h['counts']['accepted-time-boxed']
   + h['counts']['accepted-unevidenced'],
   'the form check approves strictly more than the assessment accepts')
ok(x.register_health([])['total'] == 0, 'an empty register is summarisable')

# ---- renewals are surfaced, not just counted -------------------------------
_, reasons = x.assess(base(renewals=3))
ok(any('RENEWED' in r for r in reasons),
   'a repeatedly renewed exception says so in its own reasons')
_, reasons = x.assess(base(renewals=1))
ok(not any('RENEWED' in r for r in reasons), 'one renewal is not yet a pattern')

# ---- the report -------------------------------------------------------------
buf = io.StringIO()
x.report(buf, demo_fail_open=True)
text = buf.getvalue()
flat = ' '.join(text.split())          # wrapped prose: match on the flattened form
ok('REFUSED-NON-WAIVABLE' in text, 'the refusal is printed')
ok('approved' in text and 'rejected' in text, 'the fail-open comparison runs')
ok('Nothing here is legal advice' in flat, 'the scope of the model is stated')
ok('non-waivable list is an illustration' in flat,
   'and the reader is told to build their own non-waivable list')
ok('%%' not in text, 'no literal double percent leaks')
buf2 = io.StringIO()
x.report(buf2)
ok('IS THE FORM FILLED IN' not in buf2.getvalue(),
   'the fail-open demonstration is opt-in, not the default output')

print('exception_register: %d checks passed' % PASS[0])
sys.exit(0)
