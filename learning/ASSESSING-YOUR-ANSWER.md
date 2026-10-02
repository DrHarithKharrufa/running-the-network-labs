# Assessing your own answer

Many exercises in this book ask you to *explain*, *design* or *produce a
record*. Those questions build judgement only if you can tell a good attempt
from a poor one, and a model answer alone does not teach that — it is too easy
to read one and feel you would have written it.

So each standard below gives you three things: a complete example, a **plausible
but inadequate** answer of the kind that passes a casual read, and a rubric that
separates what must be present from what is a legitimate difference of
approach. Write your own answer first. Then compare it with the inadequate one
before you look at the complete one, and be honest about which it resembles.

Three artefacts are covered, because they recur across the book and because
each is something you will be asked for at work:

1. An incident record (Chapter 65)
2. An architecture decision record (Chapter 76)
3. A capacity recommendation (Chapter 66)

---

## 1. An incident record

**The task.** Chapter 65's exercises ask you to run the timeline exercise and
supply a defensible clock bound --- or to say plainly that you cannot, and show
that the record's conclusions survive without one. Both are complete answers;
inventing a bound is not. More generally: write the record for an incident you
have run.

### Plausible but inadequate

> **Incident: network outage, 14 March**
>
> At around 09:15 users reported they could not reach the CRM. Investigation
> found a routing problem on the core. The team worked on it and service was
> restored at about 10:30. Root cause was a bad config change. Action: be more
> careful with changes and improve testing.

This reads like a record. It is the version most incident reports actually are,
and it fails on five counts: nothing in it can be checked, "around" and "about"
destroy the timeline, "a routing problem" and "a bad config change" name a
category rather than a mechanism, the action has no owner and no date, and
"be more careful" is not an action — it is a wish addressed to human attention,
which is the thing that already failed.

### Complete

> **INC-2026-0314-01 — CRM unreachable from two branch sites**
>
> **Impact.** 09:14–10:27 UTC (73 min). CRM (svc-crm-prod) unreachable from
> Leeds and Sheffield branches; approximately 240 users. Other sites and all
> other services unaffected. No data loss. Two customer-facing orders delayed,
> both completed same day.
>
> **Timeline.** Clock bound: **I do not have one, and the record does not need
> one.** Device logs are NTP-synchronised to `ntp1.internal` by `chronyd`. What I
> have from the window is a *last offset* reading of 3 ms taken before the
> incident and a worst root dispersion of 18 ms during it, and those two
> quantities do not combine into a bound. Chrony documents the bound as
> `clock_error <= |system_time_offset| + root_dispersion + (0.5 * root_delay)`,
> assuming the reference is correct: the first term is the remaining correction
> *at the moment of the timestamp*, which a last-offset reading from earlier is
> not, and the third term is a root delay I never recorded. Even read
> generously, 3 ms and 18 ms already exceed 20 ms before any root delay is
> added, so a ±20 ms claim would have been arithmetically wrong as well as
> unsupported.
>
> So: **no subsecond ordering is claimed below.** The ordering this record
> shows an apparent 81-second gap between the change at 09:12:41 and the
  > first probe failure at 09:14:02. Without a contemporaneous bound for both
  > clocks, those cross-system timestamps do not establish event order. Treat
  > them as a useful hypothesis to test. The configuration history and a
  > controlled replay must supply the causal evidence; synchronisation alone
  > is not a quantified error bound. The ticket system is browser-timestamped
> against an unsynchronised client; its times are marked ±60 s as a working
> assumption and are **not** used to order anything.
>
> If you do need subsecond ordering, this is what it takes: the three chrony
> terms above, read on each device at the time of the timestamps, plus the
> logging path's own precision and capture delay. That is a measurement to set
> up before an incident, not a number to reconstruct after one.
>
> | Time (UTC) | Source | Event |
> |---|---|---|
> | 09:12:41 | change record CHG-4471 | Prefix-list `BRANCH-IN` updated on core-rtr-02, committed without confirm timer |
> | 09:14:02 | monitoring | Synthetic HTTPS probe to svc-crm-prod from Leeds fails |
> | 09:16 ±60 s | ticket INC-… | First user report, Leeds |
> | 09:31 | chat log | Incident declared, commander assigned |
> | 09:48 | engineer's terminal capture | `show ip route 10.20.8.0/22` on core-rtr-02 returns no route; prefix present on core-rtr-01 |
> | 10:02 | chat log | CHG-4471 identified as the only change in the window |
> | 10:21 | device log | Previous prefix-list restored on core-rtr-02 |
> | 10:27 | monitoring | Synthetic probe recovers from both sites |
>
> **What happened.** CHG-4471 replaced the `BRANCH-IN` prefix list rather than
> appending to it. The replacement omitted `10.20.8.0/22`, so core-rtr-02
> stopped accepting the CRM prefix from the branch aggregation layer. Traffic
> from Leeds and Sheffield hashes to core-rtr-02; the other branches hash to
> core-rtr-01, which was unchanged. That is why it looked like a site problem
> rather than a routing problem for the first half hour.
>
> **Contributing factors.**
> - The change was committed without a confirm timer, so nothing reverted it.
> - The prefix list is maintained by hand in two places and the two had already
>   diverged before this change.
> - Monitoring alerted on the synthetic probe at 09:14 but the alert routed to
>   a queue nobody was watching; the first human signal was a user at 09:16.
> - The pre-change test checked that the session stayed up. A session staying
>   up tells you nothing about which prefixes crossed it.
>
> **What we are not claiming.** We have not established why the alert routed to
> the unwatched queue; that is INC-2026-0314-01-A, owned by K. Obi, due 28
> March. We have not reproduced the divergence between the two prefix lists.
>
> **Actions.**
> | # | Action | Owner | Due | Verified by |
> |---|---|---|---|---|
> | 1 | Confirm timers mandatory for core routing-policy changes; enforce in the change template | S. Whitfield | 04 Apr | A change without one is rejected at review; test with a deliberate omission |
> | 2 | Generate `BRANCH-IN` from the source of truth on both cores; remove the hand-edited copies | R. Devlin | 25 Apr | Both cores' lists byte-identical to the generated file for 30 days |
> | 3 | Pre-change test for routing policy checks received prefixes, not session state | R. Devlin | 11 Apr | Template updated; next three policy changes show the prefix check in evidence |

### Rubric

**Must be present — in a *completed* review.** An initial record written while
the incident is open is a different artefact and a good one: it carries what is
known, marks what is not, and names who owns finding out. Where the evidence is
not yet in, `unknown — owned by X, due Y` is a complete entry, not a gap.

- Impact stated as who and what, with a duration and a number.
- A timeline with sources named, and an explicit statement of how much the
  clocks can be trusted.
- A mechanism, not a category: "the prefix list was replaced and omitted this
  prefix", not "a config error".
- An explanation of why the symptom looked like something else, if it did.
- Contributing factors in the plural, addressing detection and process as well
  as the trigger.
- Actions with an owner, a date and a **way to tell they worked**.
- An explicit statement of what has not been established.

**Legitimate variation.** The order of sections. Whether contributing factors
are separated from the narrative. Whether you rank actions. Whether you keep a
"root cause" heading at all — many good teams do not, and Chapter 65 explains
why.

**Failure signatures to check your own work for.** Times without sources; a
clock offset offered where an uncertainty bound is needed; **a precise bound
whose terms are not defined, or are read from a different moment than the
timestamps they are supposed to bound** --- a figure like ±20 ms is worse than
"not established", because it invites an ordering the evidence does not support;
a *single* cause
presented as sufficient when the detection and process factors are unexamined —
the heading is not the problem, the singularity is; any action whose
verification is "we will be careful"; the passive voice hiding who did what;
and a record that reads as though the outcome was obvious from the start, which
no real investigation is.

---

## 2. An architecture decision record

**The task.** Chapter 76's exercises ask you to write an ADR for a migration
you know, including the evidence still missing.

### Plausible but inadequate

> **ADR: move to EVPN-VXLAN**
>
> We have decided to adopt EVPN-VXLAN for the data centre fabric. It is the
> modern standard, offers better scalability and multi-tenancy, and is
> supported by our vendors. The alternative was to stay with our current
> layer-2 design, which does not scale. We will implement in Q3.

Everything in it may be true. It is still not a decision record, because it
does not let a successor disagree with it: no requirement is stated, so nothing
can be checked against; "better scalability" has no number; the rejected option
is described only as bad, so nobody reading this can check the trade; there is
no cost, no risk and no condition that would make this decision wrong.

### Complete

> **ADR-014 — Overlay for the Anvil fabric**
> **Status:** accepted, 2026-03-02. Supersedes nothing. Revisit trigger below.
>
> **Context.** Anvil carries 2 spines and 4 leaves today, projected to 2 and 10
> within 18 months. Three requirements drive this decision:
> - R-07: a tenant's layer-2 domain may span any leaf pair (product requirement,
>   confirmed with the platform team 2026-02-18).
> - R-09: onboarding a tenant onto a leaf pair must not require per-tenant
>   configuration on transit spines (operational requirement, 2026-02-18).
> - R-11: a leaf failure must not require reconfiguration elsewhere in the
>   fabric (operational requirement, 2026-02-18).
> The current design carries VLANs across the fabric on trunks. It satisfies
> R-07 today, by hand. It fails **R-09**: adding a tenant to a new leaf pair is
> a change on every device in the path. Whether it also fails R-11 is a separate
> question about failure behaviour, and we have not tested it — see evidence
> still missing.
>
> **Decision.** EVPN with VXLAN encapsulation, BGP-signalled, symmetric IRB.
>
> **Alternatives considered.**
> | Option | Why not chosen | What it would have cost |
> |---|---|---|
> | Keep VLAN trunking | Fails R-09; per-tenant change is fabric-wide | £0 now; an estimated 2 engineer-days per tenant onboarding, rising with leaf count |
> | VXLAN with a controller | Meets R-07 and R-09; adds a controller to the failure domain and a licence we would have to keep current | Licence ~£28k/yr, plus the controller's own availability design |
> | EVPN-VXLAN, asymmetric IRB | Meets R-07 and R-09; requires state for all subnets of each tenant IP-VRF on its participating leaves; the assumed host/subnet profile is projected to exceed the selected table budget, pending exact-release verification | £0 licence; a table-capacity wall we would hit inside the projection window |
>
> **Consequences we accept.**
> - Two networks to operate on one fabric: the underlay and the overlay. Chapter
>   37's separation of debugging applies and the NOC runbooks need it.
> - Troubleshooting requires reading BGP EVPN routes, which two of six engineers
>   can do today. Training is a dependency, not an afterthought.
> - We are committed to a multi-vendor-capable control plane but not to
>   multi-vendor leaves in this phase.
>
> **Evidence still missing.**
> - Leaf MAC and ARP table capacity at the 10-leaf projection is taken from the
>   datasheet, not measured on our traffic profile. **This is the number most
>   likely to be wrong.**
> - Whether the current trunked design satisfies R-11 has not been tested.
>   We are replacing it for an onboarding reason (R-09), not a failure one, and
>   the record should not claim otherwise.
> - Convergence on a leaf failure has been modelled, not tested. Acceptance test
>   AT-09 covers it before the second phase.
>
> **Revisit if:** leaf count projection exceeds 16; or the platform team
> withdraws R-07; or measured table utilisation passes 60% of datasheet
> capacity.

### Rubric

**Must be present.**

- A requirement that the decision can be checked against, with a source and a
  date — not a goal like "scalability".
- The rejected options, each with the reason and **what it would have cost**.
  An option described only as bad leaves a successor unable to check the trade.
- Consequences you accept, including operational and human ones.
- The evidence you do not have, and which missing number would hurt most.
- A condition that would make this decision wrong, stated in advance.

**Legitimate variation.** Format and headings. Whether you number requirements.
Whether costs are money, effort or risk. Whether "status" carries a supersession
chain. Teams differ and all of these are fine.

**Failure signatures.** No number anywhere; a rejected option with no cost; a
rejection whose stated reason does not match the requirement it cites; no
revisit trigger; consequences that are all positive; and the decision stated
before the requirement, which usually means the requirement was written to fit.

Note what that bullet does **not** say, and the earlier bad example does not
say either: that an option without a written cost was never really considered.
You cannot infer what somebody thought from what they wrote down, and a team
that argued for three hours and minuted one line has a documentation defect, not
a thinking defect. What you can say is that the record does not let a successor
check the trade. That is the defect, and it is the one you can actually fix.

---

## 3. A capacity recommendation

**The task.** Chapter 66's exercise 3, exactly as printed: *a load of 45 grows
at 20% annually towards an in-service limit of 70, with six months of complete
delivery time. Derive the crossing and begin dates; explain how the calculation
changes if 70 is already an order trigger.*

Note what it asks for: two dates and a variant. An answer with one date has not
finished the question.

### Plausible but inadequate

> Current load is 45 out of 70, which is 64%. Growing at 20% a year it will
> reach 70 in about 2.4 years. So we have a couple of years before this becomes
> a problem. No action needed now.

The arithmetic is right and the answer is incomplete on the exercise's own
terms. It gives the crossing date and stops: the six-month delivery time is
never subtracted, so the *begin* date — the one you can act on — is missing.
The order-trigger variant is not addressed at all. And "no action needed now"
is a recommendation that does not follow from anything computed, because
nothing has been compared with a date.

### Complete

> **Crossing date.** Compound growth from 45 to the limit of 70:
>
> ```text
> t = ln(70 / 45) / ln(1.20) = 2.4234 years = 29.1 months
> ```
>
> **Begin date.** Six months of complete delivery time, subtracted from the
> crossing:
>
> ```text
> 2.4234 - 0.5 = 1.9234 years = 23.1 months
> ```
>
> Under this fixed scenario, the latest start is about **23 months from
> now**, rather than 29. This is a conditional deadline, not evidence that the
> service remains safe until then. "Complete delivery time" is the whole chain — approval, order,
> lead time, delivery, install, test, in service — and if any link in it is
> longer than assumed, that date moves earlier, not later.
>
> **If 70 is already an order trigger.** Then the calculation inverts: the
> trigger is not the date you run out, it is the date you are required to act,
> and there is no lead time to subtract from it because acting *is* the
> deliverable. The crossing becomes 29.1 months and the begin date becomes the
> same 29.1 months — but you now need the *next* threshold, the one at which
> service actually degrades, to know what you have bought. A trigger with no
> stated headroom behind it is a date with no consequence attached.
>
> **What I am recommending.** Ask the service owner to commission an evidence
> review now, with the capacity lead reporting missing measurements and required
> failure scenarios within two weeks. The supplied arithmetic alone does not
> establish an immediate purchase need. Provisionally plan a procurement start
> at 20 months, adding an explicitly proposed three-month contingency before the
> computed 23; confirm that allowance with procurement and review the inputs at
> the evidence gate and whenever demand, topology or delivery changes.
>
> **The assumption most likely to change the decision.** The 20% compound
> growth is a supplied scenario, not a measured forecast with known coverage.
> If branch onboarding drives demand, obtain its schedule and compare an event
> scenario with the smooth curve. Two fitted points alone do not establish
> forecast reliability. A separate 40% growth sensitivity gives a crossing in
> 1.31313 years and a latest start in 0.81313 years, about 9.76 months away,
> under the same six-month delivery allowance.

### The same question with real-world conditions added

This is **a different exercise**, stated separately because the figures change
and it is not what Chapter 66 asked. Everything below is an added assumption,
labelled as one.

> **Added synthetic assumptions:** the 45 is the p95 of one complete aligned
> total-demand series, not the sum of member percentiles or a daily mean. The
> path has two equal members, normally sharing that same demand equally. Each
> member has an independently justified in-service limit of 35; the healthy
> pair's aggregate limit is therefore 70. After either member fails, the entire
> demand can reroute to the survivor. The service requirement is to carry that
> demand within the survivor's limit. Routing, queues and service behaviour
> have not been tested by this paper example.
>
> | Condition | Limit | Load today | Crossing | Begin (−6 months) |
> |---|---|---|---|---|
> | Both members | 70 | 45 (64%) | 29.1 months | 23.1 months |
> | **N−1, one member** | **35** | **45 (129%)** | **already exceeded** | **passed** |
>
> That is the line that decides it. Under N−1 the survivor is asked to carry 45
> against an in-service limit of 35. It is not approaching a threshold; it is
> past one, today. The design either accepts degraded service during a single
> failure — which somebody must decide explicitly and record — or it needs
> capacity now, and the 23-month date is irrelevant.
>
> **A separate statistic sensitivity.** Assume, only for this invented
> comparison, that the mean of the same demand series is exactly `45/1.6`.
> Starting the smooth model from that smaller value gives a crossing at 60.0
> months rather than 29.1:
>
> ```text
> 12 × ln(1.6) / ln(1.2) = 30.9 months of difference
> ```
>
> That 30.9-month difference illustrates how the statistic changes the
> calculation. Neither statistic alone proves a service-performance envelope;
> the relevant peak durations, bursts, loss and latency remain evidence needs.

### Rubric

**Must be present.**

- Both dates the question asks for: the crossing *and* the begin date, with the
  delivery time subtracted.
- The variant the question asks for, answered.
- A recommendation with an action and a date that follows from the arithmetic.
- The assumption most likely to be wrong, named.

**Must be present once conditions are added.** If you introduce a failure
state, a traffic statistic or a threshold below the limit, each one must be
stated as an assumption and each threshold must have its own denominator
written down. Applying a percentage reserve on top of a limit that is *already*
a reserve counts the same headroom twice.

**Legitimate variation.** Whether you model N−1 or N−2. Whether growth is
compounded or driven by a known schedule — the second is better where it
exists, and saying so is part of a good answer. **Which statistic you use:**
Chapter 66 teaches that the measure follows the service objective and the
sampling model. Busy-hour p95 is one possible input; maximum interval load,
tail duration or a state-table occupancy measure may answer a different
question. State the measure and why.

**Failure signatures.** One date where the question asked for two; a lead time
mentioned but never subtracted; a threshold whose denominator is not written
down; two reserves multiplied without noticing; and any answer that treats a
growth percentage as a fact rather than a fitted parameter.

## Using these

Work in this order, and reduce the support as you go:

1. **Copy the standard.** Do the same artefact for a case of your own with the
   complete example open beside you.
2. **Write first, compare second.** Next time, write yours, then diff it
   against the rubric. Count how many mandatory items you missed.
3. **Transfer.** Do a third one for a different artefact type with only the
   rubric — no example — and ask a colleague which of the failure signatures
   they can find in it.

The failure signatures are the most useful part of each rubric. They are what a
reviewer looks for first, and they are all detectable in your own writing before
anyone else sees it.
