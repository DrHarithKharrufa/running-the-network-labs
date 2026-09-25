#!/usr/bin/env python3
"""Lab 54.1 --- first match wins, and what a rule-order model can honestly tell you.

WHAT THIS IS, STATED FIRST
--------------------------
A deliberately small model of one firewall behaviour: rules are evaluated in
order and the first match wins. It reasons about SYMBOLIC LABELS compared for
equality, plus the single wildcard `any`. That is the whole of its semantics.

WHAT IT THEREFORE DOES NOT MODEL, and will refuse rather than guess:

  ADDRESSES. "10.10.30.10" here is a STRING, not an address. This model does not
  know that 10.10.30.10 is inside 10.10.30.0/24, and it never will. Give it a
  prefix, a range, an address group or an object name that expands elsewhere and
  it cannot reason about containment --- so it REFUSES the input rather than
  comparing the text and reporting a confident wrong answer.

  PORTS AND PROTOCOLS. "443" is a label, not a port number, and there is no
  protocol field at all. A rule for TCP/443 and one for UDP/443 are the same rule
  to this model.

  NAT. A published server is reached on one address and reached BY the firewall
  on another, and which one the policy matches is the trap §54.5 is about. This
  model has one address space and cannot express that at all.

  STATE. Return traffic, established flows, session timeouts: none of it. This
  models the rule table, not the state table.

  ANYTHING ELSE A REAL FIREWALL DOES. Schedules, users and identity, application
  identification, security profiles, interface and zone pairs beyond the two it
  carries, rule enable/disable.

WHY THIS LAB WAS REBUILT
------------------------
The shipped version reported exactly one shadowed rule and was right about it.
Three things were wrong with what it did NOT report.

  IT DETECTED ONLY SHADOWING BY A SINGLE EARLIER RULE, and said nothing about
  whether that was enough. Two or more earlier rules that between them cover
  everything a later rule would match leave it just as dead. Building the
  detector for that case produced the more interesting result: IN THIS MODEL THE
  UNION CASE CANNOT HAPPEN under the stated equality/wildcard semantics.
  `union_reduces_to_single()` checks a finite subset by exhaustion; the general
  argument uses a fresh label simultaneously in every wildcard field. The reason is worth more than the
  detector would have been. Covering a wildcard field requires an earlier rule
  that is itself wildcard in that field --- there is always a label no rule names
  --- and such a rule, if it matches the others, covers the later rule on its
  own. So a check for union shadows here would be code that can never fire, which
  is the "can this model fail?" defect rather than the fail-open one. A REAL
  rule base does not have this property, and that is the point: once rules carry
  prefixes, 10.0.0.0/8 genuinely IS the union of narrower prefixes, several rules
  really can combine to kill a later one, and you need an analyser with address
  semantics. This model tells you when it is out of its depth instead.

  IT IGNORED THE ACTION. A rule shadowed by an earlier rule with the SAME action
  is harmless duplication. A rule shadowed by one with the OPPOSITE action is a
  control that is not there --- somebody wrote a deny and got an allow. The
  shipped script printed both identically, so the dangerous case and the tidy-up
  case looked the same.

  IT COMPARED ADDRESS-LIKE STRINGS AS TEXT. Nothing stopped a reader putting
  10.10.30.0/24 in one rule and 10.10.30.10 in another, and the script would
  cheerfully report no relationship between them. That is the fail-open shape of
  FR-0050 applied to a policy analyser: a correct-looking input, a confident
  answer, and the answer is wrong.

    python3 ruleorder.py
    python3 ruleorder.py --json
    python3 ruleorder.py --demo-limits
    python3 test_ruleorder.py

No firewall was contacted. This reads a list of dictionaries.
"""
import argparse
import itertools
import json
import re
import sys

FIELDS = ('src', 'dst', 'port')
ANY = 'any'
ALLOW, DENY = 'allow', 'deny'
ACTIONS = (ALLOW, DENY)

# Shapes this model cannot reason about. Each is refused with its reason, so an
# unsupported input becomes an error the reader sees rather than a wrong answer
# they quote.
UNSUPPORTED = (
    (re.compile(r'/\d{1,3}$'),
     'a CIDR prefix --- this model compares labels for equality and cannot '
     'decide whether one prefix contains another'),
    # A range means digits on both sides of the hyphen (1024-65535,
    # 10.0.0.1-10.0.0.9). A bare hyphen must NOT match, or ordinary object
    # names like "dmz-web" are refused --- that is a validator failing CLOSED,
    # which is safer than failing open and still wrong.
    (re.compile(r'\d\s*-\s*\d'),
     'a range --- this model has no ordering, so it cannot decide overlap'),
    (re.compile(r'[,;]'),
     'a list or group --- expand it into separate rules, or use a model that '
     'understands objects'),
    (re.compile(r'^\s*$'),
     'an empty value --- say "any" if you mean any'),
)


class RuleError(ValueError):
    """The rule base cannot be analysed as given."""


def validate(rules):
    """Reject what the model cannot represent. Never silently accept it."""
    if not isinstance(rules, (list, tuple)) or not rules:
        raise RuleError('a rule base must be a non-empty list of rules')
    seen = set()
    for i, r in enumerate(rules):
        where = 'rule at position %d' % (i + 1)
        if not isinstance(r, dict):
            raise RuleError('%s is not a dictionary' % where)
        missing = [f for f in ('n', 'action') + FIELDS if f not in r]
        if missing:
            raise RuleError('%s is missing %s' % (where, ', '.join(missing)))
        if r['n'] in seen:
            raise RuleError('%s reuses rule number %r' % (where, r['n']))
        seen.add(r['n'])
        if r['action'] not in ACTIONS:
            raise RuleError('%s has action %r; this model knows only %s'
                            % (where, r['action'], ' and '.join(ACTIONS)))
        for f in FIELDS:
            v = r[f]
            if not isinstance(v, str):
                raise RuleError('%s field %s is %r; fields are text labels'
                                % (where, f, v))
            for rx, why in UNSUPPORTED:
                if rx.search(v):
                    raise RuleError(
                        '%s field %s is %r, which this model cannot represent: '
                        '%s. Refusing to analyse rather than report a confident '
                        'wrong answer.' % (where, f, v, why))
    return True


def validate_flow(flow):
    missing = [f for f in FIELDS if f not in flow]
    if missing:
        raise RuleError('a flow needs %s' % ', '.join(missing))
    for f in FIELDS:
        if flow[f] == ANY:
            raise RuleError(
                'the flow specifies %s=%r. A flow is one concrete packet, not a '
                'set: "any" as a flow value asks "what happens to everything at '
                'once", which has no single answer. Name the actual source, '
                'destination and port you mean.' % (f, ANY))
        for rx, why in UNSUPPORTED:
            if rx.search(flow[f]):
                raise RuleError('flow field %s is %r: %s' % (f, flow[f], why))
    return True


# --------------------------------------------------------------------------
# The model
# --------------------------------------------------------------------------

def matches(rule, flow):
    """Does `rule` match this one concrete flow?"""
    return all(rule[f] in (ANY, flow[f]) for f in FIELDS)


def first_match(rules, flow):
    """The rule a first-match-wins firewall would stop at, or None."""
    for r in rules:
        if matches(r, flow):
            return r
    return None


def covers(a, b):
    """Every flow rule `b` would match, rule `a` also matches."""
    return all(a[f] == ANY or a[f] == b[f] for f in FIELDS)


def _values(rules, field):
    """The concrete labels in play for a field, plus one that is in no rule.

    The sentinel matters: without it, a set of rules naming every label that
    appears would look exhaustive when a real firewall would still see traffic
    none of them covers.
    """
    vals = {r[field] for r in rules if r[field] != ANY}
    vals.add('«%s-not-named-in-any-rule»' % field)
    return sorted(vals)


def unreachable(rules, index):
    """Is rules[index] unreachable? Decided by enumeration, not by `covers`.

    Enumerates every flow the rule would match --- over the labels the rule base
    names, plus one label per field that it does NOT name, because the label
    space is open --- and asks whether an earlier rule always gets there first.
    This is the general test. `covers` is the special case of one rule doing it.
    """
    r = rules[index]
    earlier = rules[:index]
    space = [(_values(rules, f) if r[f] == ANY else [r[f]]) for f in FIELDS]
    shadowing = set()
    for combo in itertools.product(*space):
        flow = dict(zip(FIELDS, combo))
        hit = first_match(earlier, flow)
        if hit is None:
            return None                      # some flow reaches it: it is live
        shadowing.add(hit['n'])
    return sorted(shadowing)


def find_shadows(rules):
    """Every rule that can never match, with what shadows it and how bad that is."""
    out = []
    for i, r in enumerate(rules):
        by_ns = unreachable(rules, i)
        if not by_ns:
            continue
        by = [e for e in rules[:i] if e['n'] in by_ns]
        how = ('a single earlier rule' if len(by) == 1
               else 'several earlier rules between them')
        out.append(_shadow(r, by, how))
    return out


def union_reduces_to_single(max_rules=4, labels=('a', 'b')):
    """Finite exhaustive check of the stated fresh-label shadowing argument.

    Searches every rule base up to `max_rules` long over a tiny label alphabet
    and checks the claim: whenever a rule is unreachable, SOME SINGLE earlier
    rule already covers it. Returns the count checked and any counter-example.

    This is here because the alternative was shipping a union detector that can
    never fire. A real rule base with prefixes and ranges does NOT satisfy this,
    which is exactly why an analyser that understands addresses is a different
    and harder program than this one.
    """
    vals = list(labels) + [ANY]
    atoms = [dict(src=s, dst=d, port=p, action=a)
             for s in vals for d in vals for p in vals for a in ACTIONS]
    checked = 0
    for n in range(2, max_rules + 1):
        for combo in itertools.product(atoms, repeat=n):
            rules = [dict(c, n=i + 1) for i, c in enumerate(combo)]
            for i in range(1, n):
                by = unreachable(rules, i)
                if by:
                    checked += 1
                    if not any(covers(e, rules[i]) for e in rules[:i]):
                        return {'checked': checked, 'counterexample': rules,
                                'unreachable_index': i}
    return {'checked': checked, 'counterexample': None}


def _shadow(rule, by, how):
    actions = {e['action'] for e in by}
    if actions == {rule['action']}:
        severity = 'REDUNDANT'
        meaning = ('the shadowing rule or rules take the same action, so the '
                   'effect is unchanged --- this is dead weight, not a hole')
    else:
        severity = 'CONTRADICTED'
        meaning = ('the shadowing rule or rules take a DIFFERENT action, so the '
                   'policy does the opposite of what this rule says --- somebody '
                   'wrote this rule and did not get it')
    return {'rule': rule['n'], 'action': rule['action'],
            'shadowed_by': [e['n'] for e in by],
            'by_actions': sorted(actions), 'how': how,
            'severity': severity, 'meaning': meaning}


def trace(rules, flow):
    validate_flow(flow)
    r = first_match(rules, flow)
    if r is None:
        return {'flow': dict(flow), 'rule': None, 'action': None,
                'note': ('NO RULE MATCHED. This model stops here and does not '
                         'guess. A real firewall applies its own default, which '
                         'is usually deny but is a property of the product and '
                         'the policy table --- establish yours rather than '
                         'assuming (§54.4).')}
    return {'flow': dict(flow), 'rule': r['n'], 'action': r['action'],
            'note': 'first match wins; evaluation stopped here'}


# --------------------------------------------------------------------------
# The rule base under analysis
# --------------------------------------------------------------------------

RULES = [
    dict(n=1, src='internal', dst='any', port='any', action='allow'),
    dict(n=2, src='internal', dst='dmz-web', port='ssh', action='deny'),
    dict(n=3, src='guest', dst='internal', port='any', action='deny'),
    dict(n=4, src='any', dst='dmz-web', port='https', action='allow'),
    dict(n=5, src='partner', dst='dmz-web', port='any', action='allow'),
    dict(n=6, src='any', dst='dmz-db', port='any', action='deny'),
    # Rule 7 is REACHABLE, and it is here to show that: partner to internal on
    # sql reaches it, because no earlier rule covers that combination. A rule
    # base where nothing is dead is the normal case, and a checker that only
    # ever reports problems has not been tested against one.
    dict(n=7, src='partner', dst='any', port='sql', action='deny'),
    # Rule 8 is REDUNDANT rather than contradicted: rule 6 already denies it,
    # with the same action. Dead weight, not a hole --- the report must say
    # which, because the two need different responses.
    dict(n=8, src='guest', dst='dmz-db', port='sql', action='deny'),
    dict(n=99, src='any', dst='any', port='any', action='deny'),
]

FLOWS = [
    dict(src='internal', dst='dmz-web', port='ssh',
         label='internal SSH to the DMZ web box (meant to be DENIED)'),
    dict(src='partner', dst='dmz-web', port='https',
         label='partner HTTPS to the DMZ web box'),
    dict(src='guest', dst='internal', port='smb',
         label='guest to internal file sharing'),
    dict(src='contractor', dst='dmz-db', port='sql',
         label='an identity no rule names, to the database'),
]


def analyse(rules=None, flows=None):
    rules = RULES if rules is None else rules
    validate(rules)
    flows = FLOWS if flows is None else flows
    return {'shadows': find_shadows(rules),
            'traces': [dict(trace(rules, f), label=f.get('label', '')) for f in flows],
            'rule_count': len(rules)}


# --------------------------------------------------------------------------

def demo_limits():
    """Show the model refusing the four things it cannot represent."""
    cases = [
        ('a CIDR prefix', [dict(n=1, src='10.10.0.0/16', dst='any', port='any',
                                action='allow')]),
        ('a port range', [dict(n=1, src='any', dst='any', port='1024-65535',
                               action='allow')]),
        ('an address group', [dict(n=1, src='hr,finance', dst='any', port='any',
                                   action='allow')]),
        ('an action it does not know', [dict(n=1, src='any', dst='any',
                                             port='any', action='inspect')]),
    ]
    out = []
    for label, rules in cases:
        try:
            validate(rules)
            out.append({'input': label, 'refused': False,
                        'why': 'ACCEPTED --- which would be a bug'})
        except RuleError as exc:
            out.append({'input': label, 'refused': True, 'why': str(exc)})
    try:
        trace(RULES, dict(src=ANY, dst='dmz-web', port='https'))
        out.append({'input': 'a flow of "any"', 'refused': False,
                    'why': 'ACCEPTED --- which would be a bug'})
    except RuleError as exc:
        out.append({'input': 'a flow of "any"', 'refused': True, 'why': str(exc)})
    return out


def report(res, stream=sys.stdout):
    w = stream.write
    w('Firewall rule-base analysis --- first match wins (§54.3)\n')
    w('%d rules. Symbolic labels only: this model does not understand '
      'addresses,\nports, protocols, NAT or state, and refuses input it cannot '
      'represent.\n\n' % res['rule_count'])
    if not res['shadows']:
        w('No rule in this base is unreachable.\n')
    for s in res['shadows']:
        w('  [%-12s] rule %s (%s) can never match\n'
          % (s['severity'], s['rule'], s['action']))
        w('      shadowed by %s: %s\n'
          % (s['how'], ', '.join('rule %s' % n for n in s['shadowed_by'])))
        w('      %s\n' % s['meaning'])
    w('\nFlow traces:\n')
    for t in res['traces']:
        verdict = ('rule %s %s' % (t['rule'], t['action'].upper())
                   if t['rule'] is not None else 'NO RULE MATCHED')
        w('  %-52s -> %s\n' % (t['label'], verdict))
        if t['rule'] is None:
            w('      %s\n' % t['note'])
    contradicted = [s for s in res['shadows'] if s['severity'] == 'CONTRADICTED']
    w('\n%d unreachable rule(s), of which %d contradicted: an earlier rule takes '
      'the\nopposite action, so the policy does the opposite of what the rule '
      'says.\n' % (len(res['shadows']), len(contradicted)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--demo-limits', action='store_true',
                    help='show the model refusing what it cannot represent')
    args = ap.parse_args(argv)
    if args.demo_limits:
        print('What this model refuses, and why refusing beats guessing:\n')
        for c in demo_limits():
            print('  %-28s %s' % (c['input'], 'REFUSED' if c['refused'] else 'ACCEPTED'))
            print('      %s\n' % c['why'])
        return 0
    res = analyse()
    if args.json:
        json.dump(res, sys.stdout, indent=2)
        sys.stdout.write('\n')
    else:
        report(res)
    return 0


if __name__ == '__main__':
    sys.exit(main())
