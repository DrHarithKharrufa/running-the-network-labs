# Security and operations route: Chapters 50–67

Six connected paper sessions for the fictional Aldergate branch. All evidence below is constructed. This route complements the numbered answers and the modern-operations workbook; it does not certify a security programme or a staffing arrangement.

## 1. Name the trust decision — Chapters 50–52

An administrator downloads a firmware file and its checksum from the same compromised location. A second engineer says the checksum matches, so the firmware is trusted. Explain why the pair can be altered consistently. Specify an independently trusted signing identity or authenticated reference, the exact version/bytes and the remaining supply-chain limitations.

Next, an administrator leaves. Remove their authorised access paths, revoke credentials where supported and handle active sessions separately. Removing a shared CA trust path affects more than one person; leaving another valid credential path can leave access possible. A KRL created on a laptop does not prove every server enforces it. Submit a credential-lifecycle and distribution test, including an offline server that misses the update. Use an ordinal risk register to prioritise discussion, not to calculate expected pounds by multiplying rank labels.

## 2. The permitted session and the blocked packet — Chapters 53–56

A branch can open small HTTPS responses but stalls on large ones after a tunnel change. A blanket infrastructure ACL blocks incoming ICMP fragmentation-needed messages. A TCP connection to port 179 succeeds from the approved peer address.

Submit three separate conclusions: the TCP socket was reachable; BGP protocol establishment is unproved; and the transfer failure is consistent with, but does not prove, a PMTU problem. Check the tunnel's exact encapsulation and path limit, endpoint capture and relevant ICMP treatment. Calculate one maximum inner packet using the chosen transform and verify it in a real lab before assigning a production MTU. A Child SA observed at one time and no IKE SA observed later are not necessarily impossible evidence. Record snapshot times and SA lifecycle. Changing a rule or clamping TCP MSS is a mitigation whose complete service effects still need checking.

## 3. Find evidence without inventing visibility — Chapters 57–60

Assume independent 1:2048 packet sampling. A ten-packet exchange has probability `1−(2047/2048)^10 ≈ 0.0048721` of at least one selection, before path and export losses. A missing flow record cannot rule it out. Compare a deterministic selector before applying that formula to another exporter.

The case system reports ten true incidents among 100 alerts. That gives 10% observed precision for those adjudicated alerts; it supplies no recall without independently known missed incidents. Define a benign fixture, an attack fixture and a held-out evaluation set. Explain why raising a threshold can shrink the queue while missing more incidents.

An exception expires during the investigation. Preserve the record and escalate the current authority and unresolved gap; expiry does not erase documentation. If a non-waivable duty is unmet, record and remedy it rather than approving or concealing it. Distinguish exploitation known elsewhere from evidence of exploitation in this estate. For any reporting clock, identify the applicable entity, legal trigger and actual awareness evidence; an AI-generated timestamp is not a legal assessment.

## 4. Cover the service and observe the observer — Chapters 61–63

Five staff each contract for 37.5 hours/week. Use 5.6 weeks leave, one week training and a 3% sickness allowance on the remaining time. The average availability fraction is `(52−6.6)/52×0.97 ≈ 0.84688`; one continuously occupied position requires `168/(37.5×availability) ≈ 5.29 FTE`. A five-person team has an average shortfall of about 0.29 FTE, before testing a feasible rota, handover, simultaneous absence, skills and rest. This is not “one whole person” and not a lawful schedule.

For monitoring, create the PRTG service/sensor/probe map in MODERN-OPERATIONS-WORKBOOK.md. A fixed-phase sample can repeatedly miss a periodic microburst. A counter mean over a long interval can hide a peak; a shorter interval may reduce dilution. State which quantity the instrument actually reports.

A 4,096-descriptor empty ring receiving two million packets/s fills in 2.048 ms if none are reclaimed. A 3 ms ring-service pause exceeds that allowance. A 3 ms disk pause alone does not prove ring loss when downstream buffers continue absorbing traffic. Submit counter and buffer evidence for the whole path. For a log queue, distinguish transport receipt, accepted storage, replication and searchable records; none should be silently substituted for another.

## 5. A quiet incident is not automatically a repaired incident — Chapters 64–66

Construct two candidate explanations for an intermittent failure and choose a test whose possible results change the next action. State location, identity, protocol, size, load, time and observation quality. Keep the change log as evidence, not as a list of automatic causes.

Under a stationary rate of two recurrences/day with perfect observation, three quiet days have probability `exp(−6) ≈ 0.00247875` if the fault remains. With an explicit 0.5 prior repair probability and guaranteed silence when repaired, posterior repair probability is about 99.7527%. Changing the prior changes the answer. None of these assumptions is supplied by a quiet dashboard alone.

Prepare a change with an absolute decision deadline, recovery duration and reserve. At the deadline, unresolved acceptance is unresolved even if the first test looked promising. For an incident review, put clock uncertainty on each event. Two overlapping time intervals do not establish causal order. Submit a timeline, competing hypotheses, actual or proposed evidence and an owned follow-up; use “not observed” rather than “did not happen” when appropriate.

## 6. Capacity is a service promise — Chapter 67

Two 100 Gbit/s links normally share 120 Gbit/s. With one failed, the surviving link cannot carry the same offered load at its stated line rate. Ordinary averages cannot remove that constraint. Specify the protected class, degradation policy and usable failure-state capacity, then test packet rate, bursts and shared downstream bottlenecks.

For a separate growth calculation, current protected load is 50 units, planning trigger 70 and monthly compound growth 3%. The crossing is `ln(70/50)/ln(1.03) ≈ 11.38315 months`. An eight-month complete delivery allowance leaves about 3.38315 months to decide under that scenario. Recompute with 5% growth and explain the changed commitment. A billed percentile and an aggregate of per-interface percentiles do not automatically supply the required simultaneous failure-state load.

## Submission

Hand over a single incident/change portfolio containing the service map, trust decisions, measurements or clearly labelled plans, recovery evidence, staffing assumptions and capacity decision. Use the Appendix G rubric. No synthetic observation in this workbook may be claimed as an actual customer incident or equipment test.
