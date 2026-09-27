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

1. An incident record (Chapter 66)
2. An architecture decision record (Chapter 79)
3. A capacity recommendation (Chapter 67)

---

## 1. An incident record

**The task.** Chapter 66's exercises ask you to run the timeline exercise and
supply a defensible clock bound. More generally: write the record for an
incident you have run.

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
> **Timeline.** Clock bound. Device logs are NTP-synchronised to
> `ntp1.internal`; the last offset check before the incident read 3 ms, and the
> daemon's own worst dispersion over the incident window was 18 ms, so **device
> times below are good to ±20 ms** and events 50 ms apart can be ordered. The
> 3 ms reading on its own would not have established that: an offset estimate
> says where the clock was, an uncertainty bound says how far it could have
> been, and only the second lets you order two events. The ticket system is
> browser-timestamped against an unsynchronised client, so its times carry no
> bound I can defend; they are marked ±60 s as a working assumption and are
> **not** used to order anything.
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
"root cause" heading at all — many good teams do not, and Chapter 66 explains
why.

**Failure signatures to check your own work for.** Times without sources; a
clock offset offered where an uncertainty bound is needed; a *single* cause
presented as sufficient when the detection and process factors are unexamined —
the heading is not the problem, the singularity is; any action whose
verification is "we will be careful"; the passive voice hiding who did what;
and a record that reads as though the outcome was obvious from the start, which
no real investigation is.

---

## 2. An architecture decision record

**The task.** Chapter 79's exercises ask you to write an ADR for a migration
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
is described only as bad, which means the trade was never made; there is no
cost, no risk and no condition that would make this decision wrong.

### Complete

> **ADR-014 — Overlay for the Anvil fabric**
> **Status:** accepted, 2026-03-02. Supersedes nothing. Revisit trigger below.
>
> **Context.** Anvil carries 2 spines and 4 leaves today, projected to 2 and 10
> within 18 months. Two requirements drive this decision:
> - R-07: a tenant's layer-2 domain may span any leaf pair (product requirement,
>   confirmed with the platform team 2026-02-18).
> - R-09: onboarding a tenant onto a leaf pair must not require configuration on
>   any device outside that pair (operational requirement, 2026-02-18).
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
> | VXLAN with a controller | Meets both requirements; adds a controller to the failure domain and a licence we would have to keep current | Licence ~£28k/yr, plus the controller's own availability design |
> | EVPN-VXLAN, asymmetric IRB | Meets both; requires every VNI on every leaf, which we expect to exceed leaf table capacity at the 10-leaf projection | £0 licence; a table-capacity wall we would hit inside the projection window |
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
  An option described only as bad was never really considered.
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

One thing this rubric deliberately does **not** say: that an option without a
written cost was never really considered. You cannot infer what somebody
thought from what they wrote down. What you can say is that the record does not
let a successor check the trade, which is the defect to fix.

---

## 3. A capacity recommendation

**The task.** Chapter 67's exercise 3, exactly as printed: *a load of 45 grows
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
> So the last honest moment to start the procurement is about **23 months from
> now**, not 29. "Complete delivery time" is the whole chain — approval, order,
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
> **What I am recommending.** Diarise the procurement start at 20 months, three
> months before the computed 23, and review the growth figure at 12 months.
>
> **The assumption most likely to be wrong.** 20% compound is a fitted
> parameter, not a mechanism. This growth is driven by branch onboarding; if the
> onboarding schedule is known, use it and discard the percentage. A straight
> line through two points is not a forecast.

### The same question with real-world conditions added

This is **a different exercise**, stated separately because the figures change
and it is not what Chapter 67 asked. Everything below is an added assumption,
labelled as one.

> **Added:** the 45 is busy-hour p95, not a daily mean. The path is two equal
> members; the in-service limit of 70 is the pair's, so one member's is 35. The
> service must survive a single member failure.
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
> **What the measure is worth.** If the daily mean were used instead, and the
> mean runs about 1.6 times below busy-hour p95, the same model starting from
> 28.1 crosses at 60.0 months rather than 29.1:
>
> ```text
> 12 × ln(1.6) / ln(1.2) = 30.9 months of difference
> ```
>
> Two and a half years of false comfort, from the choice of statistic alone.

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
Chapter 67 teaches that the measure follows the service objective and the
sampling model, so busy-hour p95 is a good default for a shared link and the
wrong default for, say, a table-occupancy limit. State the measure and why.

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
