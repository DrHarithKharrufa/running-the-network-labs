# Eight branching investigations

Finished reader-facing copy. All incidents, measurements and people are fictional teaching scenarios. Read the opening, choose an action, then follow its named paragraph. These are evidence exercises, not certifications. Where a platform command is needed, use the chapter's qualified command panel for the actual release and context.

## B01 — The cable is innocent until measured

**Chapter 3.** A Reading uplink remains up, but its receiving interface gains CRC errors during a reproducible transfer. The application slows down. The sending interface shows no corresponding transmit error. A colleague proposes changing the MTU: “It fixed something last Thursday.” You have a maintenance window, a known-good compatible patch lead and optics, and permission to interrupt this one link. Other links are out of scope.

Choose your first action:

- **A:** Record counters, direction, optical diagnostics and timestamps; reproduce briefly. Go to **B01-A**.
- **B:** Raise the MTU immediately. Go to **B01-B**.
- **C:** Replace the lead and both optics together. Go to **B01-C**.

**B01-A.** The receiving CRC counter rises with the test. Optical diagnostics alone neither prove nor exclude a physical fault. You have narrowed the symptom to a receive path; you have not convicted a component. Choose a controlled one-component substitution (**B01-D**) or declare the receiving optic defective (**B01-E**).

**B01-B.** The supplied evidence does not connect an MTU mismatch to corrupted received frames. You have changed another variable and may have changed service behaviour. Restore the approved setting, record the attempt and go to **B01-A**. Last Thursday declines to testify.

**B01-C.** The transfer improves. Useful recovery, weak isolation: the lead, either optic, disturbed connections or an intermittent condition could explain it. Retain the removed components for controlled testing. Go to **B01-D** if isolation remains necessary and authorised; otherwise close with the cause unresolved.

**B01-D.** Substitute one compatible component at a time, recording the same directional counters and test conditions. In this scenario, replacing the patch lead stops the errors; returning that lead reproduces them. Record the bounded finding: that lead or its connector condition explains this reproduced failure. Confirm service recovery and monitor. Do not generalise the result to every CRC incident.

**B01-E.** A counter is evidence of a symptom, not a component serial number. Revise the hypothesis and go to **B01-D**.

**Close the ticket:** Identify the evidence that supported the substitution, the controlled result, the service verification and the remaining uncertainty.

## B02 — The backup that answered on the primary

**Chapter 17.** Aldergate's backup WAN dashboard is green. Its probe targets an address reachable over either circuit. A packet capture shows the probe leaving through the primary. The current probe therefore says little about the backup. You may change the monitoring test, but may not interrupt production today.

- **A:** Design a test whose forwarding context forces the backup, with explicit return-path checks. Go to **B02-A**.
- **B:** Increase the probe rate. Go to **B02-B**.
- **C:** Announce that failover has passed. Go to **B02-C**.

**B02-A.** Pinning a source address alone may not force the intended egress. Depending on the platform, use the appropriate route, policy or isolated test context, and make primary-path escape fail visibly. Check what happens if the backup becomes unavailable: a fallback through the primary must not produce a misleading pass. Choose capture and forwarding-table verification (**B02-D**) or trust the new label (**B02-E**).

**B02-B.** More samples of the wrong path improve confidence in the wrong claim. Return to **B02-A**.

**B02-C.** The evidence proves a reachable destination over the primary. Correct the dashboard claim, then go to **B02-A**. The backup has an excellent attendance record at a meeting it has never joined.

**B02-D.** A capture confirms the intended outbound path. Check the return path and the test's dependency on shared equipment. Label the result precisely: backup-path reachability under these conditions. A later authorised failover trial must still check application recovery, convergence and failure behaviour.

**B02-E.** “Backup” is a label, not a forwarding decision. Go to **B02-D**.

**Close the ticket:** State what this non-disruptive test establishes and which claims still require a controlled failure trial.

## B03 — The route with an invalid passport

**Chapter 33.** A newly announced customer prefix is classified RPKI Invalid, and Kestrel's configured policy rejects it. The customer says the announcement was planned. Existing unrelated routes work. You can inspect the announcement, validator evidence and intended authorisation; you cannot rewrite the customer's records yourself.

- **A:** Compare the actual origin ASN and prefix length with the applicable validated authorisations. Go to **B03-A**.
- **B:** Disable invalid-route rejection for the whole network. Go to **B03-B**.
- **C:** Assume Invalid means the router is broken. Go to **B03-C**.

**B03-A.** In this scenario the origin ASN matches, but the advertised prefix is more specific than the authorisation permits. Choose coordination of the intended announcement and authorisation (**B03-D**) or a global validator reset (**B03-E**).

**B03-B.** That change would affect unrelated routes and would not explain the mismatch. It exceeds the stated authority. Return to **B03-A**. An exception, if genuinely needed, requires a separately authorised, scoped and expiring decision with documented exposure; the exercise supplies no such approval.

**B03-C.** A policy rejection can be the router doing exactly what it was configured to do. Go to **B03-A**.

**B03-D.** Confirm who owns the intended origin and prefix policy. Arrange the appropriate correction, then observe the validator's refreshed state and the router's resulting decision. Do not equate changing a published record with immediate convergence everywhere. Verify route acceptance and service separately.

**B03-E.** Resetting a cache cannot turn a genuinely unauthorised more-specific announcement into an authorised one. Investigate freshness if evidence warrants it, but here return to **B03-D**.

**Close the ticket:** Distinguish publication, validation, routing policy and application recovery. Four green boxes are more useful than one optimistic sentence.

## B04 — The tunnel that swallowed large packets

**Chapter 36.** An Anvil pilot carries small packets successfully. A synthetic capture shows a large test packet becoming an outer IPv4 packet of 1,550 bytes, with DF set. A downstream link's IP MTU is 1,500 bytes. The relevant ICMP response is filtered. These sizes are supplied observations for this exercise, not universal VXLAN overhead rules. You may test two pilot endpoints; production changes require the normal change process.

- **A:** Correlate endpoint and underlay captures, MTU limits and ICMP handling. Go to **B04-A**.
- **B:** Disable DF everywhere. Go to **B04-B**.
- **C:** Clamp TCP MSS and declare every application repaired. Go to **B04-C**.

**B04-A.** The evidence explains why this packet cannot traverse that link as sent and why the sender may not learn the constraint. Choose a reviewed end-to-end MTU/encapsulation design and appropriate ICMP handling (**B04-D**) or only increase the first switch's MTU (**B04-E**).

**B04-B.** A broad fragmentation change introduces new behaviour without validating the path. Return to **B04-A**. The network has enough mysteries without adding a bag of packet fragments.

**B04-C.** MSS adjustment can address particular TCP flows under suitable conditions. It does not establish recovery for UDP, every tunnel or every direction. Narrow the claim and return to **B04-A**.

**B04-D.** Assess every relevant path, including failure paths and endpoint constraints. Select a supported design: adequate underlay MTU where feasible, or correctly constrained inner traffic, with the intended discovery/error behaviour. Retest small and large traffic in both directions and with representative protocols. Record the pilot's limits.

**B04-E.** A chain's carrying capacity is not determined by its most enthusiastic link. Return to **B04-D**.

**Close the ticket:** Explain the demonstrated failure without assuming all overlays use this packet size or that ping alone proves application health.

## B05 — The legitimate packet at the wrong entrance

**Chapter 52.** A permitted customer source arrives on interface A. Strict reverse-path checking looks up its source in the relevant forwarding context and selects interface B; the drop counter rises. The network intentionally has an asymmetric path. Independent policy evidence confirms that this customer is allowed to send this source on A. That evidence matters: reverse-path reachability alone does not establish ownership.

- **A:** Confirm the lookup context, policy and intended paths before choosing a supported validation mode. Go to **B05-A**.
- **B:** Remove all source filtering. Go to **B05-B**.
- **C:** Treat the counter as proof of spoofing. Go to **B05-C**.

**B05-A.** In the supplied scenario, a legitimate asymmetric path conflicts with strict checking. Choose a scoped design using the platform's supported alternatives plus source authorisation controls (**B05-D**) or assume loose mode alone authorises the source (**B05-E**).

**B05-B.** That abandons independent protections and changes unrelated traffic. Go to **B05-A**.

**B05-C.** The counter establishes the check's failure, not the sender's intent. Go to **B05-A**. A security control should not become a personality test for packets.

**B05-D.** Evaluate feasible-path checking where supported, or another carefully scoped design appropriate to the topology. Preserve customer prefix controls and verify legitimate traffic, disallowed sources and failure-path behaviour. Record the precise implementation and exceptions. The right answer depends on platform semantics; the exercise does not mandate one universal mode.

**B05-E.** A route to a source can exist even when that ingress is not authorised to carry it. Return to **B05-D**.

**Close the ticket:** Separate topology compatibility from source permission. Verify both.

## B06 — The change window has a clock

**Chapter 64.** It is 18:44. Service must be restored and verified by 19:00. For this fictional exercise, the rehearsed restoration takes nine minutes, verification takes three, and the agreed guard allowance is two. Treat those bounds as valid for the supplied scenario. The new configuration has failed an acceptance check. A colleague offers “one quick three-minute experiment.”

- **A:** Calculate the latest safe restoration decision and use the agreed failure criteria. Go to **B06-A**.
- **B:** Try the three-minute experiment first. Go to **B06-B**.
- **C:** Wait until 19:00 to decide whether to restore. Go to **B06-C**.

**B06-A.** Nine plus three plus two is fourteen minutes. The latest planned decision is 18:46. Choose restoration now after the failed acceptance check (**B06-D**) or reserve that budget for improvisation (**B06-E**).

**B06-B.** The experiment would end at 18:47, beyond the latest planned decision. It cannot fit the stated recovery budget even if it takes exactly three minutes. Return to **B06-A**.

**B06-C.** A deadline is not a starting gun. Return to **B06-A**.

**B06-D.** Start the approved recovery, verify the service criteria and record the result. If conditions invalidate the rehearsed bounds, escalate promptly and update the recovery plan; do not pretend arithmetic guarantees reality. The experiment can become a lab task with a proper hypothesis.

**B06-E.** The guard allowance exists for uncertainty in recovery, not as a voucher for another change. Return to **B06-D**. The clock is the only attendee who never agrees to “just one more thing.”

**Close the ticket:** Include the failed criterion, decision time, recovery evidence and follow-up hypothesis. No prize is awarded for using every minute.

## B07 — The twin that passed its own exam

**Chapter 72.** A proposed automation change passes a digital twin's fixtures. The model covers routing policy and reachability, but does not represent HA switchover timing, optical behaviour or the application's timeout. Deployment would touch a redundant service pair. You have authority to recommend a rollout plan, not to waive acceptance criteria.

- **A:** Map each acceptance claim to evidence and identify the unmodelled behaviour. Go to **B07-A**.
- **B:** Treat the simulated pass as complete production validation. Go to **B07-B**.
- **C:** Reject all modelling as useless. Go to **B07-C**.

**B07-A.** The pass supports the modelled claims under its assumptions. Choose a bounded rollout with additional representative tests and recovery gates (**B07-D**) or add “high confidence” to the report (**B07-E**).

**B07-B.** The twin has answered the questions it was built to answer. Return to **B07-A**. An exam cannot assess a subject absent from the syllabus.

**B07-C.** The model still offers useful policy and reachability evidence. Keep that value and go to **B07-A**.

**B07-D.** Identify a suitable lab or pilot for the missing behaviour. Define service-level acceptance, observable stop conditions and supported recovery before production rollout. A canary must be meaningful for the affected failure domain: touching one member of a redundant pair is not automatically low impact. Preserve the evidence's scope in the approval record.

**B07-E.** Confidence needs a claim and supporting evidence. Return to **B07-D**.

**Close the ticket:** Write one sentence stating what the twin proved, and one stating what it could not establish.

## B08 — Two offices, one address

**Chapter 81.** An acquired business unit within Aldergate's Manchester operation uses 10.10.20.0/24 in an isolated routing context. An existing Aldergate context also uses that prefix. The groups need a shared application. This is a fictional migration detail, not an additional site or an amendment to the book's canonical address plan. Identity, DNS and application dependencies are partly documented.

- **A:** Map the conflicting contexts and application identities; plan a staged migration or explicit translation design. Go to **B08-A**.
- **B:** Join the routing contexts and hope the preferred route is useful. Go to **B08-B**.
- **C:** Renumber everything in one night before discovering dependencies. Go to **B08-C**.

**B08-A.** Separate the desired service access from the eventual address plan. Choose a reviewed phased design with ownership, name resolution, observability and recovery gates (**B08-D**) or add an unexplained NAT rule (**B08-E**).

**B08-B.** One route cannot identify two different destinations with the same address in the same context. Return to **B08-A**. The packets have not read the acquisition announcement.

**B08-C.** A clean spreadsheet does not prove a clean migration. Return to **B08-A** and identify dependencies first.

**B08-D.** A staged renumbering may be appropriate; explicitly scoped translation or service mediation may support an interim phase. Check bidirectional flows, DNS, embedded addresses, logging and security policy for the selected design. Some steps may require forward recovery rather than reversal. Define those commitments before proceeding, and test the actual shared application.

**B08-E.** Translation introduces its own identities and dependencies. Make the design explicit and return to **B08-D**.

**Close the ticket:** Document which identities exist on each side, what the application sees and how operators trace a failed transaction.
