# From a subscriber complaint to an interconnection decision

Four paper sessions for Chapters 31–34. All observations below are **constructed teaching inputs**, not measured network results. Keep your predictions separate from supplied inputs and from anything you later execute. The arithmetic uses decimal units. The billing CSV is the book's existing synthetic fixture.

Prerequisites: packet/return-path reasoning, rate and delay units, prefix lengths, ordinary BGP import/export policy and Chapters 24–30's service boundaries. If a step is unfamiliar, return to Chapters 7, 8 and 22. Use `EVIDENCE-FORM.md` for actual practice and `SELECTED-ANSWERS.md` after making your own attempt.

## Session 1 — The busy instant

**Read:** Chapter 31. **Submit:** a service-allocation calculation and an acceptance matrix.

A fictional 100-Mb/s bottleneck carries 8 Mb/s of admitted priority traffic. Business and default queues are both continuously backlogged at residual weights 60:40. A failure leaves 50 Mb/s usable capacity; the priority workload stays at 8 Mb/s and within its envelope. Business service needs at least 30 Mb/s during that failure. Assume an ideal work-conserving scheduler, matching byte accounting and no other ceiling.

1. Calculate both residual shares before and after failure. Decide whether the unchanged policy meets the business requirement.
2. The team suggests increasing the priority marking of all business traffic. Explain what must be agreed about admission and overload before that change can be assessed.
3. Design observations that would distinguish a wrong classifier, policer loss and ordinary queue competition. Include mixed packet sizes and an unauthorised EF source.

**Model reasoning:** the normal residual is 92 Mb/s, divided 55.2/36.8. After failure it is 42, divided 25.2/16.8, so the 30-Mb/s business objective is not met by this model. If default must retain at least 15 Mb/s as well, 8 + 30 + 15 = 53 Mb/s exceeds the survivor's 50: no weight setting alone can meet all three. Reconsider demand, service objectives or surviving capacity. With a 42-Mb/s residual, giving business 30 requires at least a 30:12 allocation, leaving only 12 for default under these assumptions.

**Transfer question:** what changes when business is idle, when a child ceiling applies, or when the priority envelope changes as a percentage of the failed port? Do not claim byte-accurate device shares without platform evidence.

## Session 2 — Authorised, addressed, still broken

**Read:** Chapter 32. **Submit:** the first contradictory boundary and a recovery/negative-test plan.

Constructed observations for an isolated subscriber fixture:

| Stage | Supplied observation |
| --- | --- |
| Identity | Customer A's trusted attachment and session agree with its provisioning record. |
| Authorisation | The accepted product names a delegated `2001:db8:3200:1200::/56`. |
| CPE | PD lease is present; a LAN host uses `2001:db8:3200:1201::10/64` and reaches its CPE. |
| Outward path | The host's controlled request leaves the provider towards the isolated server. |
| Return path | The server reply reaches the provider; its forwarding lookup has no usable route to A's /56. |
| Control customer | Customer B's equivalent transaction succeeds. |

1. Locate the first demonstrated return-path failure. Explain why restarting DNS or increasing the access rate does not address the supplied contradiction.
2. Identify the component that should install the subscriber route; compare its inputs and effective state before changing anything. State what cannot be concluded about the underlying cause from the table alone.
3. After a controlled repair, repeat the transaction, check B and attempt an authorised negative test using A's prefix from B's attachment.

**Model reasoning:** the missing usable subscriber route explains the observed return-path break; it does not identify whether allocation signalling, route programming, an expired binding or another fault caused it. A RADIUS field is not a forwarding route. A link-local WAN next hop can be sufficient with the right interface context. Recovery needs actual return delivery and source isolation, not a fresh Access-Accept alone. These documentation addresses are for an isolated exercise.

**Capacity extension:** 120,000 subscribers at 64 per public address need 1,875 raw addresses. Explain the difference between adding 10% reserve (2,063 total) and keeping 10% of the total unused (2,084). Say which failure the accessible reserve can cover; neither formula proves resilient CGN state.

## Session 3 — The cheapest row loses packets

**Read:** Chapter 33 and `labs/lab33/README.md`. **Submit:** one page separating invoice arithmetic, capacity and service evidence.

Use the retained synthetic June fixture. From the lab directory, run:

```text
python -B percentile.py traffic.csv --ix-split 0.8 --capacity-a 20000 --capacity-b 20000 --output constrained.json
```

This is optional local Python model execution, not a network experiment. Retain the input hash, command and output if executed. Before opening the answer, predict why moving most IX traffic to A can fail even if A's percentile stays below its port speed.

**Model checkpoints:** no-exchange A/B percentiles are 19,697.0/10,968.8 Mb/s and the offered-rate charge is £1,839.95 under the default invented contract. A exceeds 20,000 Mb/s in 332 five-minute intervals and peaks at 52,847 Mb/s; B peaks at 17,931. The current traffic already overloads A in 24 intervals. Neither scenario is accepted for lossless delivery on those ports. The calculator does not predict the dropped traffic or delivered-traffic invoice.

Next use Answer 33.2's commit scenario. Identify A's remaining excess charge, B's commit floor and the unchanged IX fee. Explain why removing 15% of each transit sample is different from taking 15% off the total bill. Add a cache's own costs before recommending it.

**Decision question:** which observations would make you retain the IX even if a feasible no-IX scenario saved money? Consider client performance, routing control, failure dependence and contract exit. Use dated quotations for a real decision; do not turn the exercise's invented GBP inputs into market evidence.

## Session 4 — Valid is one answer, not every answer

**Read:** Chapter 34. **Submit:** a route-state table, policy decision and recovery test.

Constructed VRPs:

- V1: `203.0.113.0/24`, maximum /24, AS64501.
- V2: `203.0.113.128/25`, maximum /25, AS64502.

Predict validation for the /24 from AS64501, the /25 from AS64501 and the /25 from AS64502. Then broaden only V1's maximum to /25 and recalculate. Finally remove both records. Treat each data set as complete for this paper exercise.

**Model reasoning:** initially the three states are Valid, Invalid and Valid. After broadening V1, all three are Valid. With no covering records, all are Not-found. One matching covering record is sufficient; a more-specific conflicting record is not an override. The state alone says nothing about this session's permitted announcement set. For a customer authorised to send only the aggregate, an exact /24 allowlist still rejects either /25.

Plan a controlled cache update that makes an installed candidate unacceptable. Observe data arrival, automatic route revalidation, policy withdrawal, forwarding change and the application result. Keep an unaffected route and an independent management path. A successful manual refresh must be recorded separately; it cannot demonstrate automatic recovery. Do not publish teaching ROAs or announce these documentation prefixes publicly.

**Leadership handover:** give the service owner the affected customers, observed boundaries, recovery evidence, exception owner/expiry and unresolved tests. The incident team needs a next action, not an undifferentiated “RPKI problem”.

## Completion and a new input

Score mechanism/units, evidence/limits, service/recovery and communication/ownership from 0–2 each. Aim for at least 6/8, no zero and no unresolved material error. Rework a failed part; producing the model number without its assumptions is insufficient.

Repeat one session with a changed input: a 60-Mb/s survivor, a different intended prefix set or a different commit. Predict the direction of change first. A colleague or reader test should check whether the explanation transfers; this workbook itself does not establish reader acceptance or production competence.
