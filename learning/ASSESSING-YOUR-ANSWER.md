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
> **Timeline.** Clock bound: device logs are NTP-synchronised to
> `ntp1.internal`, last offset check 3 ms; the ticket system is
> browser-timestamped and may be up to 60 s adrift, so ticket times below are
> marked ±60 s.
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

**Must be present. An answer without these is not an incident record.**

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

**Failure signatures to check your own work for.** Times without sources;
"root cause" singular; any action whose verification is "we will be careful";
the passive voice hiding who did what; and a record that reads as though the
outcome was obvious from the start, which no real investigation is.

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
> - R-11: a leaf failure must not require reconfiguration elsewhere in the
>   fabric (operational requirement).
> The current design carries VLANs across the fabric on trunks, which satisfies
> R-07 today by hand and fails R-11: adding a tenant to a new leaf pair is a
> change on every device in the path.
>
> **Decision.** EVPN with VXLAN encapsulation, BGP-signalled, symmetric IRB.
>
> **Alternatives considered.**
> | Option | Why not chosen | What it would have cost |
> |---|---|---|
> | Keep VLAN trunking | Fails R-11; per-tenant change is fabric-wide | £0 now; an estimated 2 engineer-days per tenant onboarding, rising with leaf count |
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

**Failure signatures.** No number anywhere; a rejected option with no cost; no
revisit trigger; consequences that are all positive; and the decision stated
before the requirement, which usually means the requirement was written to fit.

---

## 3. A capacity recommendation

**The task.** Chapter 67's exercises give you a load of 45 growing at 20%
annually towards an in-service limit of 70, with a lead time. Recommend.

### Plausible but inadequate

> Current load is 45 out of 70, which is 64%. Growing at 20% a year it will
> reach 70 in about 2.4 years. The lead time is 4 months, so we should order in
> about 2 years. No action needed now.

The arithmetic is right and the recommendation is wrong. It plans to the
average, not the busy hour; it plans to the limit rather than the knee; and it
ignores the failure state entirely — the question a capacity plan exists to
answer is not "when do we run out" but "when do we run out *while something is
broken*".

### Complete

> **Recommendation: order now. The decision date has already passed under N-1.**
>
> **What the numbers are.** Load 45, in-service limit 70, growth 20% per annum,
> delivery lead time 4 months. Load here is busy-hour p95, not a daily mean;
> the two differ by a factor of roughly 1.6 on this link and using the mean
> would put the exhaustion date about 14 months later and be wrong.
>
> **Three dates, not one.**
> | Condition | Threshold | Reached | Order by |
> |---|---|---|---|
> | Normal, at the limit | 70 | 2.43 yr | 2.10 yr |
> | Normal, at the 80% knee | 56 | 1.20 yr | 0.87 yr |
> | **N-1, at the 80% knee** | 28 (half the knee) | **already exceeded** | **passed** |
>
> **The one that decides it.** Under N-1 the surviving member carries the whole
> 45 against a 70 limit — 64% on its own, above the knee at which this platform's
> latency begins to rise, and it is there *today*, not in two years. The design
> either accepts degraded service during a single failure, which is a decision
> somebody must make explicitly, or it needs capacity now.
>
> **What I am recommending.** Order the additional member now, for delivery in
> 4 months. In the meantime, record the accepted risk: a single member failure
> during busy hour degrades this path, and we have chosen to carry that risk for
> one quarter rather than expedite at a premium.
>
> **What would change this.** If the 20% figure is a straight-line fit through
> two points rather than a mechanism, it is not a forecast. The growth here is
> driven by branch onboarding; if the onboarding schedule is known, use it and
> discard the percentage. If the platform's knee is not at 80%, that number
> moves everything.

### Rubric

**Must be present.**

- The measure named: busy-hour p95, not "utilisation", and a statement of what
  difference the choice of measure makes.
- The failure state costed, not just the normal state.
- Lead time subtracted from the threshold date to give a **decision** date,
  distinct from the exhaustion date.
- A recommendation with an action and a date.
- The assumption most likely to be wrong, named.

**Legitimate variation.** The knee percentage. Whether you model N-1 or N-2.
Whether growth is compounded or driven by a known schedule — the second is
better where it exists, and saying so is part of a good answer.

**Failure signatures.** A single date; "utilisation" without a percentile; no
N-1; a recommendation with no owner or date; and any answer that treats a
growth percentage as a fact rather than a fitted parameter.

---

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
