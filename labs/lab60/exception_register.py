#!/usr/bin/env python3
"""Lab 60.2 --- an exceptions register that can refuse.

Chapter 60 used to say "an exception is defensible; a silent gap is
negligence".  Half of that is right.  Writing a gap down does not make it
lawful, and a register that approves whatever is put into it is a silent gap
with a form around it. Record failures honestly and escalate them; hiding a
failure is not a safer alternative to documenting it.

This lab implements the register the chapter now describes, and its point is
what it REFUSES:

  * a requirement that cannot be waived at all, however well documented;
  * an owner named without the authority to accept the risk;
  * a compensating control asserted but never verified;
  * an exception whose expiry has passed, which is an undocumented gap again;
  * an exception over something under active exploitation, which is an
    incident, not a risk decision.

Run --demo-fail-open to see the same records through a register that only
checks whether every box is filled in.  It approves every one of them.

    python3 exception_register.py
    python3 exception_register.py --demo-fail-open
    python3 exception_register.py --json
    python3 test_exception_register.py

Offline calculation over worked example records.  It is a model of a control,
not legal advice, and the non-waivable list below is an illustration: your own
list comes from your regulator, your contracts and your lawyers.
"""
import datetime
import json
import sys

TODAY = datetime.date(2026, 9, 23)

REQUIRED_FIELDS = ('id', 'asset', 'requirement', 'requirement_class',
                   'exposure', 'risk_owner', 'compensating_controls',
                   'expires', 'review_triggers', 'remediation_plan')

# Illustrative only.  A requirement lands here when a regulator, a statute or a
# contract leaves no discretion --- at which point an "exception" is not a risk
# decision an organisation is entitled to take.
NON_WAIVABLE = {
    'incident-reporting-deadline':
        'a statutory reporting deadline is not an internal control and cannot '
        'be excepted by the party it binds',
    'contracted-encryption-in-transit':
        'the customer contract states it without qualification; only the '
        'counterparty can vary it, and that is a contract change, not an '
        'exception',
    'lawful-intercept-capability':
        'a licence condition on the operator; the regulator, not the operator, '
        'decides whether it is met',
}

VERDICTS = ('incomplete', 'refused-non-waivable', 'refused-no-authority',
            'escalate-active-exploitation', 'expired', 'accepted-unevidenced',
            'accepted-time-boxed')


class RegisterError(ValueError):
    """Raised when a record cannot be assessed at all, as opposed to refused."""


def _as_date(value, field):
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError:
        raise RegisterError('%s must be an ISO date (YYYY-MM-DD), got %r'
                            % (field, value))


def assess(record, today=TODAY):
    """Return (verdict, reasons) for one exception record.

    The order of the tests is deliberate and is itself the argument.  A
    completeness check runs first because an incomplete record cannot be
    assessed; the non-waivable test runs before anything about compensation,
    because no amount of compensating control makes a non-waivable requirement
    waivable; authority runs before expiry, because an exception nobody could
    grant was never live enough to expire.
    """
    if not isinstance(record, dict):
        raise RegisterError('an exception record must be a mapping of fields')
    reasons = []

    missing = [f for f in REQUIRED_FIELDS
               if f not in record or record[f] in (None, '', [], {})]
    if missing:
        return 'incomplete', [
            'missing: %s' % ', '.join(missing),
            'An incomplete record is not an exception. It is the gap it was '
            'meant to document, with a form around it.']

    req = record['requirement']
    if req in NON_WAIVABLE:
        return 'refused-non-waivable', [
            'requirement %r is non-waivable: %s' % (req, NON_WAIVABLE[req]),
            'Record the unmet obligation and corrective action honestly; an internal '
            'exception cannot waive it. Do not conceal the failure.',
            'Route: escalate to the accountable executive and to legal, and '
            'treat the shortfall as a compliance failure to be closed, not a '
            'risk to be accepted.']

    owner = record['risk_owner']
    if not isinstance(owner, dict) or 'name' not in owner or 'role' not in owner:
        raise RegisterError('risk_owner must carry at least a name and a role')
    if not owner.get('may_accept_risk_of_this_class'):
        return 'refused-no-authority', [
            '%s (%s) is named as risk owner but is not authorised to accept a '
            '%s risk' % (owner['name'], owner['role'],
                         record['requirement_class']),
            'Accountability requires authority. A name without the power to '
            'decide is a name to blame later, not an owner.']

    if record.get('active_exploitation'):
        return 'escalate-active-exploitation', [
            'evidence indicates active exploitation in this estate (fixture assumption)',
            'A risk being exploited now is an incident, not a risk decision. '
            'The exception is suspended and the incident process owns it '
            'until the exploitation is stopped.']

    expires = _as_date(record['expires'], 'expires')
    granted = _as_date(record.get('granted', record['expires']), 'granted')
    if expires < granted:
        raise RegisterError('the expiry precedes the grant date; the record is '
                            'internally inconsistent and cannot be assessed')
    if expires < today:
        return 'expired', [
            'expired on %s, %d days ago' % (expires.isoformat(),
                                            (today - expires).days),
            'An expired exception is not a lapsed formality. On the day it '
            'expired the approval lapsed; the historical documentation remains. '
            'Escalate the unresolved gap and its current operating authority.']

    controls = record['compensating_controls']
    if not isinstance(controls, (list, tuple)) or not controls:
        raise RegisterError('compensating_controls must be a non-empty list, '
                            'or the field should be absent so the record is '
                            'assessed as incomplete')
    evidenced, unevidenced = [], []
    for c in controls:
        if not isinstance(c, dict) or 'control' not in c:
            raise RegisterError('each compensating control needs a control name')
        if c.get('evidence') and c.get('verified_on'):
            verified = _as_date(c['verified_on'], 'verified_on')
            if verified > today:
                raise RegisterError('a control cannot have been verified in the '
                                    'future: check the clock on whatever wrote '
                                    'this record')
            evidenced.append(c)
        else:
            unevidenced.append(c)
    if not evidenced:
        return 'accepted-unevidenced', [
            'all %d compensating controls are asserted, none demonstrated: %s'
            % (len(controls), ', '.join(c['control'] for c in unevidenced)),
            'Legacy status accepted-unevidenced supplies no verified mitigation '
            'credit. Require an authorised interim decision and a control test; '
            'documentary evidence fields alone do not verify implementation.']

    plan = record['remediation_plan']
    if not isinstance(plan, dict) or not plan.get('action') or not plan.get('by'):
        raise RegisterError('remediation_plan needs at least an action and a '
                            'date or event it is to be done by')
    reasons.append('%d of %d compensating controls verified (most recent %s)'
                   % (len(evidenced), len(controls),
                      max(_as_date(c['verified_on'], 'verified_on')
                          for c in evidenced).isoformat()))
    reasons.append('expires %s, %d days remaining'
                   % (expires.isoformat(), (expires - today).days))
    reasons.append('remediation: %s by %s' % (plan['action'], plan['by']))
    if record.get('renewals', 0) >= 2:
        reasons.append('RENEWED %d TIMES: a repeatedly renewed exception is a '
                       'decision being taken again each time, and usually means '
                       'the remediation plan is not real.' % record['renewals'])
    return 'accepted-time-boxed', reasons


def complete_form_only(record):
    """The fail-open register, for comparison.

    This is the one most organisations actually run: it checks that the form is
    filled in.  It is written here so the chapter can show what it approves.
    """
    if not isinstance(record, dict):
        return 'rejected'
    for f in REQUIRED_FIELDS:
        if f not in record or record[f] in (None, '', [], {}):
            return 'rejected'
    return 'approved'


def register_health(records, today=TODAY):
    """What the register says about the programme, rather than about one risk."""
    counts = {v: 0 for v in VERDICTS}
    errors = 0
    for r in records:
        try:
            verdict, _ = assess(r, today)
        except RegisterError:
            errors += 1
            continue
        counts[verdict] += 1
    total = len(records)
    return dict(total=total, errors=errors, counts=counts,
                would_be_approved_by_form_check=sum(
                    1 for r in records if complete_form_only(r) == 'approved'),
                note=('A register is healthy when exceptions leave it. Count '
                      'what the assessment refuses, not what it holds.'))


def prove_every_verdict_reachable(today=TODAY):
    """FR-0052 inside the lab: can each branch ever fire?

    A verdict no record can produce is dead code pretending to be a control.
    Every verdict is produced here by a record built for it, so the assessment
    is known to be live before the chapter claims anything about it.
    """
    base = dict(
        id='PROOF', asset='lab device', requirement='patch-CVE-2026-0001',
        requirement_class='policy',
        exposure='management VLAN, reachable from the operations bastion only',
        risk_owner=dict(name='A. Owner', role='Head of Network',
                        may_accept_risk_of_this_class=True),
        compensating_controls=[dict(control='bastion-only access list',
                                    evidence='config read back 2026-09-01',
                                    verified_on='2026-09-01')],
        granted='2026-06-01', expires='2026-12-01',
        review_triggers=['vendor publishes a fixed release'],
        remediation_plan=dict(action='upgrade to the fixed release',
                              by='2026-11-15', owner='A. Owner'))
    cases = {}
    cases['accepted-time-boxed'] = dict(base)
    cases['incomplete'] = {k: v for k, v in base.items() if k != 'exposure'}
    nw = dict(base); nw['requirement'] = 'incident-reporting-deadline'
    cases['refused-non-waivable'] = nw
    na = dict(base)
    na['risk_owner'] = dict(base['risk_owner'], may_accept_risk_of_this_class=False)
    cases['refused-no-authority'] = na
    ae = dict(base); ae['active_exploitation'] = True
    cases['escalate-active-exploitation'] = ae
    ex = dict(base); ex['expires'] = '2026-07-01'
    cases['expired'] = ex
    ue = dict(base)
    ue['compensating_controls'] = [dict(control='extra monitoring, we believe')]
    cases['accepted-unevidenced'] = ue

    seen = {}
    for want, rec in cases.items():
        got, _ = assess(rec, today)
        seen[want] = got
    unreachable = [v for v in VERDICTS if v not in seen.values()]
    wrong = {w: g for w, g in seen.items() if w != g}
    if unreachable or wrong:
        raise RegisterError('verdict reachability proof failed: unreachable=%s '
                            'misrouted=%s' % (unreachable, wrong))
    return dict(verdicts=len(VERDICTS), all_reachable=True, cases=seen)


def worked_records():
    """Six records an operator would recognise, one per outcome worth showing."""
    return [
        dict(id='EX-2026-014',
             asset='CORE-RTR-03, IOS XE 17.9.4a (one of two, both being tracked)',
             requirement='patch-CVE-2026-0447',
             requirement_class='policy',
             exposure='the vulnerable service is reachable only from the '
                      'management VLAN; no Internet path; no customer VRF path',
             risk_owner=dict(name='S. Adeyemi', role='Head of Network Operations',
                             may_accept_risk_of_this_class=True),
             compensating_controls=[
                 dict(control='infrastructure ACL denies the port from all but '
                              'two bastions',
                      evidence='ACL read back from the device and a probe from '
                               'a non-bastion host refused',
                      verified_on='2026-09-10'),
                 dict(control='alert on any accepted connection to that port',
                      evidence='alert fired in a test injection',
                      verified_on='2026-09-10')],
             granted='2026-08-15', expires='2026-11-30', renewals=0,
             review_triggers=['exploit code published',
                              'vendor withdraws the workaround'],
             remediation_plan=dict(action='upgrade during the November change '
                                          'window, standby node first',
                                   by='2026-11-22', owner='S. Adeyemi')),
        dict(id='EX-2026-021',
             asset='all end-of-life access switches',
             requirement='patch-CVE-2026-0512',
             requirement_class='policy',
             exposure='',                      # nobody wrote it down
             risk_owner=dict(name='unassigned', role='',
                             may_accept_risk_of_this_class=False),
             compensating_controls=[],
             granted='2026-03-01', expires='2027-03-01',
             review_triggers=[], remediation_plan={}),
        dict(id='EX-2026-022',
             asset='regional aggregation, all sites',
             requirement='incident-reporting-deadline',
             requirement_class='regulatory',
             exposure='the reporting tooling cannot assemble the return inside '
                      'the statutory window',
             risk_owner=dict(name='P. Nowak', role='Director of Engineering',
                             may_accept_risk_of_this_class=True),
             compensating_controls=[dict(control='manual return prepared by the '
                                                 'duty manager',
                                         evidence='rehearsed in the March '
                                                  'exercise',
                                         verified_on='2026-03-18')],
             granted='2026-06-01', expires='2026-12-31',
             review_triggers=['tooling replacement delivered'],
             remediation_plan=dict(action='replace the reporting tooling',
                                   by='2027-01-31', owner='P. Nowak')),
        dict(id='EX-2026-030',
             asset='BR-FW-11, branch firewall',
             requirement='mfa-on-administrative-access',
             requirement_class='policy',
             exposure='administrative access from the branch LAN only',
             risk_owner=dict(name='J. Hart', role='Branch IT Coordinator',
                             may_accept_risk_of_this_class=False),
             compensating_controls=[dict(control='long unique password in the '
                                                 'vault',
                                         evidence='vault entry exists',
                                         verified_on='2026-09-01')],
             granted='2026-09-01', expires='2026-12-01',
             review_triggers=['identity platform supports the device'],
             remediation_plan=dict(action='move the device behind the identity '
                                          'proxy', by='2026-11-30',
                                   owner='J. Hart')),
        dict(id='EX-2025-088',
             asset='LEGACY-DSLAM-02',
             requirement='remove-exposed-management-interface',
             requirement_class='policy',
             exposure='management interface answers on a public address',
             risk_owner=dict(name='S. Adeyemi', role='Head of Network Operations',
                             may_accept_risk_of_this_class=True),
             compensating_controls=[dict(control='source-address filter at the '
                                                 'edge',
                                         evidence='filter counters observed '
                                                  'incrementing on denied '
                                                  'traffic',
                                         verified_on='2025-11-04')],
             granted='2025-11-01', expires='2026-05-01', renewals=3,
             review_triggers=['decommission date confirmed'],
             remediation_plan=dict(action='decommission with the copper exit',
                                   by='2026-04-30', owner='S. Adeyemi')),
        dict(id='EX-2026-036',
             asset='DC-SPINE-01 through 04',
             requirement='patch-CVE-2026-0533',
             requirement_class='policy',
             exposure='the vulnerable service listens on the fabric underlay; '
                      'no external path is known',
             risk_owner=dict(name='S. Adeyemi', role='Head of Network Operations',
                             may_accept_risk_of_this_class=True),
             compensating_controls=[
                 dict(control='the underlay is isolated from everything else'),
                 dict(control='we would see it in the flow records')],
             granted='2026-09-05', expires='2026-12-05', renewals=0,
             review_triggers=['exploit code published'],
             remediation_plan=dict(action='upgrade with the fabric maintenance',
                                   by='2026-11-28', owner='S. Adeyemi')),
        dict(id='EX-2026-041',
             asset='EDGE-VPN-01 and EDGE-VPN-02',
             requirement='patch-CVE-2026-0601',
             requirement_class='policy',
             exposure='the vulnerable service is the public VPN listener',
             risk_owner=dict(name='S. Adeyemi', role='Head of Network Operations',
                             may_accept_risk_of_this_class=True),
             compensating_controls=[dict(control='geo-restriction on the '
                                                 'listener',
                                         evidence='policy shown in the '
                                                  'dashboard',
                                         verified_on='2026-09-19')],
             granted='2026-09-18', expires='2026-10-18',
             active_exploitation=True,
             review_triggers=['fixed release available'],
             remediation_plan=dict(action='emergency upgrade',
                                   by='2026-09-25', owner='S. Adeyemi')),
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
    proof = prove_every_verdict_reachable()
    records = worked_records()
    out.write('Lab 60.2 --- an exceptions register that can refuse\n')
    out.write('=' * 74 + '\n')
    out.write('assessed as at %s; %d verdicts, all proved reachable\n\n'
              % (TODAY.isoformat(), proof['verdicts']))

    if demo_fail_open:
        out.write('THE REGISTER MOST ORGANISATIONS RUN: IS THE FORM FILLED IN?\n\n')
        for r in records:
            out.write('  %-12s %s\n' % (r['id'], complete_form_only(r)))
        approved = sum(1 for r in records if complete_form_only(r) == 'approved')
        out.write('\n  %s\n\n' % _wrap(
            '%d of %d approved, including the one that excepts a statutory '
            'reporting deadline, the one signed by somebody with no authority '
            'to sign it, the one that expired %d days ago and the one whose '
            'subject is being exploited today. Every field was filled in. That '
            'is the whole of what this check tests, and it is what "we have an '
            'exceptions register" usually means.'
            % (approved, len(records),
               (TODAY - datetime.date(2026, 5, 1)).days), 2))

    out.write('THE SAME RECORDS, ASSESSED\n\n')
    for r in records:
        try:
            verdict, reasons = assess(r)
        except RegisterError as exc:
            out.write('  %-12s ERROR  %s\n\n' % (r['id'], exc))
            continue
        out.write('  %-12s %s\n' % (r['id'], verdict.upper()))
        for line in reasons:
            out.write('       %s\n' % _wrap(line, 7))
        out.write('\n')

    health = register_health(records)
    out.write('WHAT THE REGISTER SAYS ABOUT THE PROGRAMME\n\n')
    for verdict in VERDICTS:
        if health['counts'][verdict]:
            out.write('  %-30s %d\n' % (verdict, health['counts'][verdict]))
    if health['errors']:
        out.write('  %-30s %d\n' % ('unassessable (raised)', health['errors']))
    out.write('\n  %s\n' % _wrap(
        'A form check approves %d of these %d. The assessment accepts %d, and '
        '%d of those only until somebody tests the control it rests on. The '
        'difference between the two numbers is the difference between a '
        'register that documents decisions and one that manufactures them.'
        % (health['would_be_approved_by_form_check'], health['total'],
           health['counts']['accepted-time-boxed']
           + health['counts']['accepted-unevidenced'],
           health['counts']['accepted-unevidenced']), 2))
    out.write('\n  %s\n' % _wrap(
        'Nothing here is legal advice, and the non-waivable list is an '
        'illustration. The transferable part is the shape: some requirements '
        'are not yours to except, and a register that cannot say so will say '
        'yes.', 2))


def main(argv):
    if '--json' in argv:
        records = worked_records()
        out = []
        for r in records:
            try:
                verdict, reasons = assess(r)
            except RegisterError as exc:
                verdict, reasons = 'unassessable', [str(exc)]
            out.append(dict(id=r['id'], verdict=verdict, reasons=reasons,
                            form_check=complete_form_only(r)))
        print(json.dumps(dict(as_at=TODAY.isoformat(),
                              reachability=prove_every_verdict_reachable(),
                              assessments=out,
                              health=register_health(records)), indent=1))
        return 0
    report(demo_fail_open='--demo-fail-open' in argv)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
