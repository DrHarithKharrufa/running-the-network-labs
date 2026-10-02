# Design and leadership route: Chapters 76–87

Six paper sessions take the branch service to an investment and operating decision. These are invented requirements, observations and financial inputs. Existing worked answers provide alternative examples; a well-supported different design can earn full credit.

## 1. Turn a request into acceptance — Chapters 76–77

The sponsor asks for “a resilient network with AI monitoring”. Rewrite that into a service boundary, user transaction, protected failure cases, observation coverage, recovery target, data-handling constraints, operating owner and acceptance evidence. Identify which targets are agreed requirements and which remain proposals.

Draw DNS, identity, timing, management, power and provider dependencies. A PRTG alarm, n8n workflow and model endpoint can share a database or identity dependency; three product names do not create three independent paths. The model can be unavailable while the incident procedure remains usable. Submit two designs and a common-failure test. Keep intended architecture, configuration and observed forwarding/service behaviour as separate evidence.

## 2. Allocate identity and qualify scale — Chapters 78–79

An invented IPv6 /40 contains 65,536 /56 site allocations; each /56 contains 256 /64 LANs. Reserve an explicit structure for regions, growth, infrastructure and ownership, and verify overlaps mechanically. Do not treat this capacity as permission to allocate somebody else's prefix.

Select one failure-state load and one route/MAC/ACL scale profile. Obtain the exact model, memory/profile, licence and software release limits rather than quoting the largest number from a product family. Tables may share resources or differ by profile. Include convergence, update rate, packet size, logging and troubleshooting under load. A control-plane parser test cannot establish forwarding or hardware capacity. Submit a traceable resource budget and test matrix with unknown cells visible.

## 3. Survive a partition and retire the old path — Chapters 80–81

The branch loses central connectivity while local monitoring continues. Decide which local operations remain available and which must wait for central authority. Queue age and stale identity mappings matter when the connection returns. Give a queued event a mapping generation and verify that an old sensor ID cannot act on a newly assigned device.

For migration, describe old, new and mixed states, including return paths and policy. Two individually correct complete configurations do not prove every intermediate state is safe. Write dependencies and rollback boundaries, then inject a delayed approval and a partially applied change. Retire old routes, identities, credentials, queued jobs and monitoring records deliberately; deleting a diagram is not decommissioning evidence.

## 4. Price the operating model — Chapters 82–83

An invented workflow saves 50 hours/month of old work but requires 8.333 hours of review, 12 hours maintenance and ten hours of non-overlapping exception/rework effort. Net released capacity is about 19.667 hours/month. At 80 implementation hours, simple effort break-even is about 4.068 months. This is neither measured productivity nor automatically a payroll saving.

Add the actual trial's sensor/collector coverage, workflow execution volume, model tokens, storage, backup, support, integration, training and exit costs. Separate fixed from variable costs and distinguish a subscription's entitlement from hosting it yourself. Score PRTG, n8n, execution and AI options against their respective responsibilities; do not compare a monitoring platform with a workflow engine as if they solve the same problem.

Submit a three-year cash schedule, a declared discount rate and one sensitivity. Explain the distinction between cash timing, depreciation and financing. Require a release-specific licensing and support record from each supplier, including any customer-facing service or redistribution constraints.

## 5. A percentage needs its contract — Chapters 83–84

Four eligible customers are observed for 60 minutes each. Customer A has 15 unavailable minutes after unioning overlapping records; B has ten; C and D have none. Customer-minute availability is `1−25/240 = 89.5833%`. If at least one customer was unavailable for 15 elapsed minutes, the separately defined “all customers available” fraction is 75%. Neither is the SLA answer until the contract selects a definition.

Now mark five additional customer-minutes unknown. Report the range implied by that uncertainty using the same eligible denominator; do not silently remove those minutes. Keep supplier credits and customer liabilities on their own fee bases, exclusions, claim clocks and caps.

For the UK provider scenario in Chapter 84, make an applicability register before choosing a reporting clock. Include entity/service, jurisdiction, trigger, effective date, owner/deputy and submission evidence. Distinguish an enacted obligation from a bill. The workflow may prepare a timeline; legal assessment and authorised reporting remain accountable decisions. Use current primary guidance when applying this paper scenario in practice.

## 6. Ask for a decision people can deliver — Chapters 85–87

Four engineers supply 150 gross hours/week. After 30 hours of stated allowance, capacity is 120; committed demand is 110. A 20-hour incident raises demand to 130, ten above capacity. Assign an explicit trade-off, cover or deferral rather than booking one engineer twice. Test a deputy's competence, access, authority and availability through a bounded absence exercise.

Write a one-page request for a read-only monitoring-to-investigation trial. Name its owner, cost ceiling, eligible sites, accepted data, success/stopping criteria and manual fallback. Place the established monitoring profile and the new model-assisted workflow separately on a local technology radar. Do not allow maturity in one component to approve autonomous containment in another.

Your executive page should reconcile customer impact, capacity, cost, security exposure, change outcomes and staffing evidence. Retain unknowns and material qualitative risks. End with a specific requested decision and the evidence needed at its review date. A reassuring chart is useful only if the team can explain what happened and what should happen next.

## Review

Use the Appendix G rubric and introduce one changed assumption: longer delivery, a common provider duct, higher model costs, missing logs or an absent specialist. Revise the affected recommendation while retaining unchanged facts. Reader testing, actual platform acceptance and an accountable production approval remain outside this paper exercise.
