#!/usr/bin/env python3
"""Lab 55.1 --- turning labels and observed flows into CANDIDATE micro-segmentation
policy, and the two mistakes that turn candidates into an outage.

WHAT THIS PRODUCES, STATED FIRST
--------------------------------
CANDIDATE rules for a human to approve. Not policy. Nothing here is safe to push
to an enforcement point, and the module will not call its output policy, because
the gap between "these rules were generated" and "this policy was approved" is
where both of the following failures live.

THE TWO FAILURES, WHICH POINT IN OPPOSITE DIRECTIONS
----------------------------------------------------
A generator sits between what you INTENDED and what you OBSERVED, and it can go
wrong in each direction. The shipped version of this lab handled one of them and
was silent about the other.

  OBSERVED BUT NOT INTENDED --- something is talking that policy does not
  sanction. The shipped lab caught this and was right to: it surfaced a web
  server reaching a database directly. What it could not say is whether that
  flow is a forgotten legitimate dependency or an attacker moving laterally, and
  neither can this one. It is a QUESTION, never an answer, and above all it is
  not a reason to write a rule. Observed traffic is evidence to review. It is
  not permission, and a generator that adds a rule because it saw the traffic
  will faithfully legitimise an intrusion.

  INTENDED BUT NOT OBSERVED --- something is authorised and simply did not
  happen while you were watching. The shipped lab generated the INTERSECTION of
  intent and observation, so an authorised relationship that was quiet during
  the observation window produced NO RULE AT ALL and was never mentioned. This
  is the more dangerous of the two, because it is silent and it is on the path
  to production: the quarterly billing run, the disaster-recovery replication,
  the annual audit extract, the backup job that only fires at month end. Each is
  authorised, each is invisible in a two-week capture, and each breaks the first
  time it runs after enforcement is switched on --- at the worst possible
  moment, since those jobs matter precisely because they are rare.

So this module reports FOUR sets, not one, and the two it adds are the ones that
were missing:

    candidate rules     intent that WAS observed --- the safe core
    unobserved intent   authorised, never seen: KEEP unless a human retires it
    unsanctioned flows  seen, not authorised: adjudicate, do not auto-permit
    unlabelled          endpoints no rule can be written about at all

WHAT THIS MODEL DOES NOT DO
---------------------------
It does not know your enforcement platform, and says nothing about whether the
rules can be expressed there, in what order they are evaluated, what the default
is, or whether an enforcement bypass exists. It has no addresses, only labels. It
has no protocol field, only a port number. It cannot see a flow that your
collection missed for any reason other than rarity --- a sampling gap, a sensor
outage, a path that does not cross the collection point. Treat its output as an
input to a review, and test enforcement separately on the real platform.

    python3 microseg_policy.py
    python3 microseg_policy.py --json
    python3 microseg_policy.py --demo-window
    python3 test_microseg_policy.py

No workload, fabric, hypervisor or controller was contacted. This reads lists.
"""
import argparse
import datetime as _dt
import json
import sys

# Verdicts. There is deliberately no "approved" and no "policy".
CANDIDATE = 'CANDIDATE'        # intent, corroborated by observation
UNOBSERVED = 'UNOBSERVED'      # intent, never seen in the window
UNSANCTIONED = 'UNSANCTIONED'  # seen, never intended
UNLABELLED = 'UNLABELLED'      # no label, so no rule can be written


class PolicyError(ValueError):
    """The inputs cannot be turned into candidate rules as given."""


# --------------------------------------------------------------------------
# Inputs. All three are things a human wrote or a collector produced --- and
# the module keeps them apart, because they have different authority.
# --------------------------------------------------------------------------

LABEL = {
    'web-01': 'web', 'web-02': 'web',
    'app-01': 'app', 'app-02': 'app',
    'db-01': 'db',
    'jump-01': 'admin',
    'backup-01': 'backup',
    # 'legacy-07' is deliberately absent: see UNLABELLED below.
}

# What the business says is allowed. This is the authority.
INTENT = {
    ('web', 'app', 8080): 'web tier to application tier',
    ('app', 'db', 5432): 'application tier to database',
    ('admin', 'db', 22): 'administrative access from the jump host',
    # Authorised, and it runs once a month. A fortnight of observation will not
    # see it, and the shipped lab would have dropped it without a word.
    ('backup', 'db', 5432): 'month-end backup extract from the database',
}

# What was actually seen. This is evidence, not authority.
OBSERVED = [
    ('web-01', 'app-01', 8080),
    ('web-02', 'app-02', 8080),
    ('app-01', 'db-01', 5432),
    ('app-02', 'db-01', 5432),
    ('jump-01', 'db-01', 22),
    ('web-01', 'db-01', 5432),      # web straight to db: not intended
    ('legacy-07', 'db-01', 5432),   # an endpoint nobody labelled
]

# The window bounds every conclusion drawn from OBSERVED, so it is an input
# rather than a footnote.
WINDOW = {'start': '2026-09-01', 'end': '2026-09-15'}


def _days(window):
    try:
        a = _dt.date.fromisoformat(window['start'])
        b = _dt.date.fromisoformat(window['end'])
    except (KeyError, TypeError, ValueError):
        raise PolicyError('the observation window needs ISO start and end dates; '
                          'without them nothing can be said about what a quiet '
                          'relationship means')
    if b < a:
        raise PolicyError('the observation window ends before it starts')
    return (b - a).days + 1


def validate(label, intent, observed):
    if not isinstance(label, dict) or not label:
        raise PolicyError('a label map is required: policy is written about '
                          'labels, so an unlabelled estate has no policy')
    for k, v in label.items():
        if not isinstance(v, str) or not v.strip():
            raise PolicyError('%r has label %r; a label must be a non-empty '
                              'name' % (k, v))
    if not isinstance(intent, dict) or not intent:
        raise PolicyError('intent is required, and it is the authority here. '
                          'Generating rules from observation alone would mean '
                          'whatever was talking becomes what is permitted.')
    for key, reason in intent.items():
        if not (isinstance(key, tuple) and len(key) == 3):
            raise PolicyError('intent key %r must be (src-label, dst-label, port)' % (key,))
        if not isinstance(key[2], int):
            raise PolicyError('intent %r has a non-integer port' % (key,))
        if not isinstance(reason, str) or not reason.strip():
            raise PolicyError(
                'intent %r has no stated reason. Every authorised relationship '
                'needs one, or nobody can review it later or decide when it '
                'should be retired.' % (key,))
    for f in observed:
        if not (isinstance(f, tuple) and len(f) == 3 and isinstance(f[2], int)):
            raise PolicyError('observed flow %r must be (src, dst, port)' % (f,))
    return True


def analyse(label=None, intent=None, observed=None, window=None):
    label = LABEL if label is None else label
    intent = INTENT if intent is None else intent
    observed = OBSERVED if observed is None else observed
    window = WINDOW if window is None else window
    validate(label, intent, observed)
    days = _days(window)

    candidates, unsanctioned, unlabelled = {}, [], []
    seen_pairs = set()
    for src, dst, port in observed:
        missing = [e for e in (src, dst) if e not in label]
        if missing:
            unlabelled.append({'flow': (src, dst, port), 'unlabelled': missing,
                               'verdict': UNLABELLED,
                               'why': ('no rule can be written about %s until it '
                                       'is labelled --- and an endpoint nobody '
                                       'labelled is also an endpoint nobody owns'
                                       % ' and '.join(missing))})
            continue
        key = (label[src], label[dst], port)
        seen_pairs.add(key)
        if key in intent:
            candidates.setdefault(key, []).append((src, dst))
        else:
            unsanctioned.append({'flow': (src, dst, port), 'labels': key,
                                 'verdict': UNSANCTIONED,
                                 'why': ('observed but not authorised. This is a '
                                         'question for a human: a forgotten '
                                         'dependency, or lateral movement. It is '
                                         'not a reason to write a rule.')})

    unobserved = [{'rule': k, 'reason': intent[k], 'verdict': UNOBSERVED,
                   'why': ('authorised but not seen in %d days of observation. '
                           'KEEP IT unless somebody decides to retire it: a '
                           'relationship that is quiet is not a relationship '
                           'that is dead, and the rare ones are the ones whose '
                           'failure hurts most.' % days)}
                  for k in sorted(intent) if k not in seen_pairs]

    return {
        'window': dict(window), 'window_days': days,
        'candidates': [{'rule': k, 'reason': intent[k], 'verdict': CANDIDATE,
                        'corroborating_pairs': sorted(v)}
                       for k, v in sorted(candidates.items())],
        'unobserved_intent': unobserved,
        'unsanctioned_flows': unsanctioned,
        'unlabelled_endpoints': unlabelled,
        'counts': {'workload_pairs_observed': len(observed),
                   'candidate_rules': len(candidates),
                   'unobserved_intent': len(unobserved),
                   'unsanctioned_flows': len(unsanctioned),
                   'unlabelled': len(unlabelled)},
    }


def demo_window(days_list=(1, 7, 30, 60)):
    """Show how the SAME intent yields different candidate sets by window length.

    The point is not the arithmetic. It is that the length of your observation
    decides which authorised relationships appear to exist --- so a generator
    that reports only what it saw is reporting a property of the capture, not a
    property of the network.
    """
    monthly = ('backup', 'db', 5432)
    rows = []
    for d in days_list:
        seen = [f for f in OBSERVED if f[0] != 'backup-01']
        if d >= 30:
            seen = seen + [('backup-01', 'db-01', 5432)]
        w = {'start': '2026-09-01',
             'end': (_dt.date(2026, 9, 1) + _dt.timedelta(days=d - 1)).isoformat()}
        res = analyse(observed=seen, window=w)
        rows.append({'days': d,
                     'candidates': res['counts']['candidate_rules'],
                     'unobserved': res['counts']['unobserved_intent'],
                     'monthly_job_seen': not any(u['rule'] == monthly
                                                 for u in res['unobserved_intent'])})
    return rows


# --------------------------------------------------------------------------

def report(res, stream=sys.stdout):
    w = stream.write
    w('Micro-segmentation CANDIDATES from labels and observed flows (§55.4)\n')
    w('Observation window %s to %s --- %d days. Everything below about what was\n'
      'NOT seen is bounded by that number.\n\n'
      % (res['window']['start'], res['window']['end'], res['window_days']))

    w('CANDIDATE rules --- intent corroborated by observation:\n')
    for c in res['candidates']:
        sl, dl, port = c['rule']
        w('  %-5s -> %-6s :%-5s  %s\n' % (sl, dl, port, c['reason']))
    w('\nUNOBSERVED INTENT --- authorised, not seen. DO NOT DROP THESE:\n')
    if not res['unobserved_intent']:
        w('  (none --- every authorised relationship was seen in this window)\n')
    for u in res['unobserved_intent']:
        sl, dl, port = u['rule']
        w('  %-5s -> %-6s :%-5s  %s\n' % (sl, dl, port, u['reason']))
        w('      %s\n' % u['why'])
    w('\nUNSANCTIONED FLOWS --- seen, not authorised. Adjudicate:\n')
    for a in res['unsanctioned_flows']:
        s, d, p = a['flow']
        w('  %s -> %s :%s  (%s -> %s)\n' % (s, d, p, a['labels'][0], a['labels'][1]))
        w('      %s\n' % a['why'])
    w('\nUNLABELLED ENDPOINTS --- no rule can be written about these:\n')
    if not res['unlabelled_endpoints']:
        w('  (none)\n')
    for u in res['unlabelled_endpoints']:
        s, d, p = u['flow']
        w('  %s -> %s :%s\n      %s\n' % (s, d, p, u['why']))

    c = res['counts']
    w('\n%d candidate rule(s) from %d observed workload pairs. %d authorised '
      'relationship(s)\nwere never seen, %d flow(s) were seen without '
      'authorisation, and %d endpoint(s)\nhave no label.\n'
      % (c['candidate_rules'], c['workload_pairs_observed'],
         c['unobserved_intent'], c['unsanctioned_flows'], c['unlabelled']))
    w('\nNothing above is policy. It is a list of candidates and a list of '
      'questions.\nApproval is a human act with an owner and a date, and the '
      'enforcement platform\nmust be tested separately --- this module has never '
      'seen it.\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--demo-window', action='store_true',
                    help='show how the window length changes what appears to exist')
    args = ap.parse_args(argv)
    if args.demo_window:
        print('The same estate, the same intent, four observation windows:\n')
        print('  %-8s %-12s %-12s %s' % ('days', 'candidates', 'unobserved',
                                         'saw the month-end job?'))
        for r in demo_window():
            print('  %-8d %-12d %-12d %s'
                  % (r['days'], r['candidates'], r['unobserved'],
                     'yes' if r['monthly_job_seen'] else 'NO'))
        print('\nA fortnight of capture makes the month-end backup look like a '
              'relationship\nthat does not exist. Enforce the fortnight\'s '
              'candidates and it breaks at\nmonth end --- which is exactly when '
              'somebody needs it.')
        return 0
    res = analyse()
    if args.json:
        json.dump({k: (v if k != 'candidates' else
                       [dict(c, rule=list(c['rule'])) for c in v])
                   for k, v in res.items()}, sys.stdout, indent=2, default=list)
        sys.stdout.write('\n')
    else:
        report(res)
    return 0


if __name__ == '__main__':
    sys.exit(main())
