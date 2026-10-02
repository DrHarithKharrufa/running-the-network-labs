# Aldergate branch: from a packet to a funding decision

This standalone fictional teaching scenario accompanies Appendix G. It does not amend the cumulative network in Appendix C. All demand, prices, growth rates and supplier allowances here are invented. The practical service test is proposed, not reported as executed.

Work each task before reading its model guidance. Keep the same case evidence as you move through the five milestones. The numbers are in `branch-case.json`; `case_math.py` reproduces the arithmetic.

## 1. Address the clients and explain the service

**Inputs:** 120 staff endpoints, one gateway address, client LAN `10.10.64.0/25`, management LAN `10.10.65.0/27`, and a 20% endpoint-growth scenario. The order-processing service is remote. Its particular address, DNS resolver, security policy and route are requirements to discover, not supplied facts.

**Submit:** network/broadcast boundaries, host capacity, explicit reservations, future demand and a diagram showing the questions needed to trace both directions of a client transaction.

**Model guidance:** the client network has 128 total and 126 conventional host addresses. Its network is `.0`, broadcast `.127`, and host range `.1-.126`. The present demand is 121 addresses, leaving five. Growth gives 144 endpoints plus a gateway, requiring 145; this exceeds a /25. A reserved `10.10.64.0/24` gives 254 conventional host addresses and does not overlap the stated management /27. Check reservations beyond the scenario before reusing it elsewhere.

Explain how a client resolves a service name, chooses a route and resolves its local next-hop neighbour; then follow the return path. DNS, routing and neighbour resolution answer different questions. A broader site allocation does not update the client's mask or the DHCP server. Identify changes to both, and to routes, ACLs, monitoring and rollback.

**Reviewer variation:** management instead occupies `10.10.64.128/27`. Now the /24 expansion overlaps it. Reject that combined plan; propose a reserved alternative or a coordinated renumbering. Do not mark overlapping ranges valid simply because the total number of hosts fits.

## 2. Practise the change on a small topology

Use the existing Lab 3.2 routed path in a supported isolated environment. If the required environment is unavailable, submit a plan and leave the execution milestone incomplete. The Chapter 2 recorded Linux evidence does not prove that you deployed the Containerlab wrapper.

**Submit:** a correct baseline with explicit probe source, the predicted effect of removing only r3's return route, the observed fault and the restored service. Use `EVIDENCE-FORM.md` and the lab README. Keep exact route state rather than only a ping screenshot.

**Model guidance:** r1 needs its route to the r2-r3 subnet, r2 needs forwarding and the relevant route, and r3 needs a return route to the actual source. In this deliberately isolated topology, removing the only return route should stop the request/reply exchange, while preserving the direct r2-r3 link. Verify the absence of fallback/default routes before predicting that outcome. A working forward path does not establish a working round trip. Restore the removed route and recheck both state and probe counts.

**Handover exercise:** write service impact, timed observations, a labelled hypothesis, the next discriminating test and the accepting owner. Ask a peer to continue using only the record. Add the details they needed to ask for.

## 3. Define and test the branch service

**Proposed requirement:** a correct order-processing transaction completes within 60 seconds after each specified single-circuit failure, over ten agreed trials per circuit. This is a bounded acceptance requirement, not an annual availability claim.

Before execution, identify the client, server, transaction, success response, load profile, failure mechanism, observation points and timing resolution. Establish that the observer can detect both success and failure. Set abort conditions for unexpected impact or loss of recovery access. Retain the working baseline and test failback as well as failover.

**Model guidance:** a useful record joins the fault timestamp to route/FIB state, the survivor's actual load and the client transaction result. A BGP session or an accepted configuration command is insufficient. Investigate DNS, firewall state, application retries and shared dependencies when network restoration and transaction restoration disagree. Preserve each trial, including a slow or failed one. Do not replace it with a better-looking repeat.

**Reviewer variation:** both circuits use a common last-mile duct. A single circuit test does not establish duct diversity. Record the shared-failure exposure and the evidence or design change needed to meet a duct-cut requirement. The original narrower circuit-failure requirement and this new requirement are distinct.

## 4. Put a date on the capacity decision

**Inputs:** two circuits, each assumed to carry 100 Mbit/s of usable load; aligned total demand 70 Mbit/s; normal equal split 35/35; sole-survivor demand 70 after successful rerouting; a chosen survivor **in-service planning limit** of 80. Added capacity must be operational before demand reaches that limit. It is not an order trigger already adjusted for lead time. The historical JSON key `survivor_planning_trigger_mbps` is retained for compatibility and means this in-service limit. Evaluate 10%, 25% and 40% constant annual compound growth.

**Submit:** the binding failure state, crossing time, latest decision under each supplier allowance, missing performance evidence and an interim option. Use `12 × ln(80/70) / ln(1+g)` for months.

| Annual growth scenario | Crossing in months | Latest decision for A (8 months) | Latest decision for B (4 months) |
| --- | ---: | ---: | ---: |
| 10% | 16.81 | 8.81 | 12.81 |
| 25% | 7.18 | -0.82 | 3.18 |
| 40% | 4.76 | -3.24 | 0.76 |

Negative values mean the modelled latest decision date is already past. The delivery allowances include the complete assumed path to accepted service; do not subtract those same stages twice. The growth rates are scenarios, not confidence intervals. The chosen trigger is not a universal queueing threshold.

Twenty Mbit/s of initial demand is classed as critical and 50 as deferrable. Discuss whether the service owner can permit deferral during failure. Test classification, enforcement, bursts and application behaviour before crediting relief. Growth in the critical class also matters; the initial 20 is not a permanent guarantee. Increasing bandwidth cannot repair an unreachable route or a common dependency.

**Reviewer variation:** the application launches a new service causing an immediate demand step. The smooth-growth calculation no longer describes the complete scenario. Add the step and reconsider the dates instead of forcing the observation into the old curve.

## 5. Make the funding and staffing choice

Both supplier options propose two larger circuits to the same required service scope, subject to acceptance. Option A costs £70,000 setup plus £45,000 annually with an eight-month complete delivery allowance. B costs £20,000 setup plus £65,000 annually with a four-month allowance. The first-year cash ceiling is £100,000. Use three years and an illustrative 8% annual discount rate.

The simplified calculation charges setup at time zero and a full annual amount at each year end, irrespective of commissioning date. It excludes VAT, tax, inflation, financing and residual value. A real decision requires the actual dated payment schedule, exit terms, service acceptance, supplier evidence and complete cost boundary.

| Calculation, before contingency | A | B |
| --- | ---: | ---: |
| Year-one cash | £115,000 | £85,000 |
| Three-year undiscounted cash | £205,000 | £215,000 |
| Cost present value | £185,969 | £187,511 |
| Year-one headroom against £100,000 | -£15,000 | £15,000 |

**Example decision memo:** provisionally select B because its base case fits the first-year ceiling and its delivery allowance fits the central growth scenario. Seek authority for a bounded feasibility/acceptance-design stage before committing to the full order. The service owner must confirm the transaction objective and acceptable interim degradation; engineering must establish diversity, platform capacity and a feasible staffing plan; procurement and finance must confirm dates, commercial terms and payment assumptions. State the cost of that initial stage and whether it is inside or additional to the quoted setup estimate before seeking approval. No approval or actual quotation is supplied by this exercise.

The roughly £1,542 present-cost difference is small beside plausible uncertainty. B's nominal price advantage in year one does not prove it is the better long-term service. A rephased payment plan or faster delivery could change the choice, but neither may be assumed without evidence.

**Change one input:** if B's recurring price rises 20%, it becomes £78,000 annually and £98,000 in year one. Only £2,000 remains before contingency. If growth is 40%, B's latest decision under the model is about 0.76 months away. If the only qualified engineer is unavailable, both quoted delivery allowances need a resource check. Rewrite the decision, interim control and escalation for the changed constraint.

**Staffing worksheet:** list discovery, design, security review, procurement, implementation, independent observation, acceptance and operational handover. For each, state effort, elapsed dependencies, accountable owner, alternate and protected time. A name in eight rows is not eight people's capacity. If incident response competes for the same engineer, identify the work that moves or the cover required. Do not invent an available specialist to make the schedule fit.

**Follow-up dashboard:** after any authorised implementation, report accepted service trials, remaining common failures, actual expenditure versus the agreed cash schedule, operational cover and the next decision. Report unknowns as unknowns. Counting completed orders alone does not show that the promised service arrived.

## Review the portfolio

Use the four-dimension rubric in the evidence form, with 0-2 for each dimension. Aim for 6/8, no zero, and no unresolved material technical or recovery error. Paper reasoning can complete the analytical portions; practical completion needs actual observations from the chosen environment. Retain a changed-input response and a corrected attempt. The goal is to explain and defend the work, not to copy this model wording.
