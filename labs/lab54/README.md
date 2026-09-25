# Lab 54.1 — First match wins, and the limits of reasoning about it offline

```bash
python3 ruleorder.py
python3 ruleorder.py --demo-limits
python3 test_ruleorder.py
```

The single most important fact about a firewall rule base is that rules match
top-down and the **first match wins** (§54.3). This lab finds rules that can
*never* match because earlier rules always get there first, and traces whether a
given flow is permitted — narrate-the-path for policy.

## What it models, and what it refuses

It compares **symbolic labels for equality**, plus the wildcard `any`. That is
the whole of its semantics. It does **not** model:

- **addresses** — `10.10.30.10` here is a *string*. The model does not know it
  sits inside `10.10.30.0/24` and never will;
- **ports and protocols** — `https` is a label; TCP/443 and UDP/443 are the same
  thing to it;
- **NAT** — one address space, so the pre-NAT/post-NAT trap of §54.5 cannot even
  be expressed;
- **state** — return traffic, established flows, timeouts: none of it. This is
  the rule table, not the state table;
- schedules, identity, application awareness, security profiles, disabled rules.

So it **refuses** a prefix, a range, a group or an unknown action rather than
comparing the text and handing you a confident wrong answer. Run
`--demo-limits` to watch it decline all five.

That refusal is the point. A policy analyser that silently treats
`10.10.0.0/16` and `10.10.30.10` as unrelated strings is not a weaker tool than
one that understands addresses — it is a tool that will tell you a rule is
unreachable when it is live, or live when it is dead.

## What changed, and why

The shipped version reported one shadowed rule and was right about it. Three
things were wrong with what it did **not** report.

**It ignored the action.** A rule shadowed by an earlier rule with the *same*
action is harmless duplication. A rule shadowed by one with the *opposite*
action is a control that is not there — somebody wrote a deny and got an allow.
The shipped script printed both identically. The rebuilt one separates
`CONTRADICTED` from `REDUNDANT`, because those need different responses: one is
an incident, the other is tidying.

**It compared address-like strings as text**, with nothing to stop a reader
putting real CIDR in. That is FR-0050's fail-open shape applied to a policy
analyser.

**It only looked for shadowing by a single earlier rule.** Building the general
detector produced the more interesting result, below.

## A result worth keeping: union shadowing cannot happen here

Could two or more earlier rules *between them* kill a later rule that neither
kills alone? In this model, **no** — and `union_reduces_to_single()` proves it
by exhaustive search rather than asserting it. Over every rule base up to four
rules on a two-label alphabet, **7,642,564** cases where a rule was unreachable
were examined and in every one some *single* earlier rule already covered it.
No counter-example exists.

The reason is worth more than the detector would have been. Covering a wildcard
field requires an earlier rule that is itself wildcard in that field — there is
always a label no rule names — and such a rule, if it matches the other fields,
covers the later rule on its own.

**A real rule base does not have this property, and that is the point.** Once
rules carry prefixes, `10.0.0.0/8` genuinely *is* the union of narrower
prefixes, several rules really can combine to kill a later one, and you need an
analyser with address semantics. This model tells you when it is out of its
depth instead of pretending.

## Lab 54.2 — on a real firewall

The model reasons; the device decides. Build the policy from §54.3 on a real
firewall, put a broad accept above a specific deny, and confirm the deny never
matches — then reorder and watch it start working.

On a firewall that keeps **per-rule hit counters** this is directly visible:
a shadowed rule's counter stays at zero no matter how much matching traffic you
send, which is the difference between believing a rule is dead and knowing it.
Check what your platform calls that counter, whether it survives a reload, and
whether it is reset by an edit — §54.9 depends on the answer, because "no hits
in a year" is only evidence if the counter really has been counting for a year.

## What to take away

- First match wins: order specific before broad, default deny, explicit logged
  cleanup rule.
- A shadowed rule is silent. It looks present and does nothing, which is worse
  than absent.
- Distinguish *contradicted* from *redundant*: only one of them is a hole.
- A model that refuses input it cannot represent is more useful than one that
  guesses — and knowing exactly where your model stops is the skill this lab is
  really teaching.
