# Campus commissioning: from a frame to a design decision

Campus revision, 25 September 2026. Read Chapters 11–16 and attempt their numbered exercises first. This workbook joins their mechanisms into a fictional Aldergate commissioning day. **Every observation below is constructed teaching data, not a captured log or an executed acceptance test.** Each stage starts after the preceding service has been restored; do not assume one fault explains all six cards.

Use six sessions of roughly 25–40 minutes. Keep a diagram, predictions, competing explanations and a decision record. Paper work is sufficient. An actual deployment uses the relevant lab README, an appropriate isolated environment and its own evidence. Do not introduce these faults into a production network.

## 1. The missing VLAN — Chapter 11

Use the two-switch topology with untagged port-5 clients 10.10.0.11/22 and 10.10.0.13/22, and the port-24 trunk. Assume captures can see the relevant tags and are running at the correct observation points.

| Constructed observation | What it establishes |
| --- | --- |
| Each client reaches an eligible neighbour on its own switch. | Some local communication works. |
| The same-VLAN cross-trunk ARP request leaves A with tag 110. | A classified and emitted this request onto the trunk. |
| B's trunk ingress capture sees that request; B's VLAN-110 endpoint capture does not. | The investigation can focus between those observation points. |
| VLAN 120 crosses the same trunk successfully. | The link carries at least that control service. |

**Task:** name three candidate causes and select a discriminating observation before changing anything. Draw the expected request and reply, including tag state.

**Model reasoning:** check B's allowed/operational VLAN membership, the instance's forwarding/filter state and port-5 egress membership. A control VLAN does not prove VLAN 110 is admitted. These cards do not uniquely identify the fault. Request the missing state; do not invent a successful repair. After a justified repair, repeat the exact baseline and an isolation check.

## 2. The longer but cheaper path — Chapter 12

Use A/B/C priorities 4096/8192/32768 with matching extensions. Set AB and BC costs to 20,000 and AC to 60,000.

**Task:** draw the expected RSTP roles, predict loss of BC, and predict restoration.

**Model reasoning:** A remains root. C prefers CB at total cost 40,000; CA is its alternate. Loss of BC makes the 60,000 direct path relevant. Restoring BC should restore the cheaper route. Cost is not a latency measurement. Submit predicted states and the time-stamped service probes needed to measure the transitions; no recovery duration is supplied.

## 3. The spare capacity that cannot help — Chapter 13

Assume a conventional two-member 10 Gb/s LAG and the simplified offered flows 8, 6 and 2 Gb/s, ignoring overhead. The stated hash assigns 8 and 6 to member 1 and 2 to member 2.

**Task:** explain why a 16 Gb/s total can overload this bundle, then assess loss of one member.

**Model reasoning:** demand is 14/2 across members, not 8/8. Member 1 cannot sustain 14 on a 10 Gb/s line. A different supported distribution might help normally; after a member loss, 16 still exceeds 10. Ask for member counters, queue/drop evidence and actual flow/hash information. These offered rates are inputs, not measured delivered throughput.

## 4. The theatre at ten o'clock — Chapter 14

Use 300 laptops and 300 phones, the chapter's active fractions and rates, with one quarter of active laptops on 6 GHz. Treat this as a separate room-planning exercise, not extra demand to add automatically to Chapter 16's campus aggregate.

**Task:** calculate per-band demand and radio lower bounds, then identify an observation that could invalidate the model.

**Model reasoning:** 5 GHz needs 390 Mb/s and seven radios at 60 Mb/s budget each; 6 GHz needs 120 Mb/s and two radios at 90 Mb/s. Seven APs is the paired-radio physical lower bound. Failed-AP capacity alone raises the counts to eight and three radios, hence eight APs. A measured lower useful capacity, poor association balance, unavailable channels or failed coverage can reject this result. A spreadsheet cannot perform the occupied-room survey.

## 5. The successful login with excessive access — Chapter 15

Constructed records agree on endpoint/session identity and time: the RADIUS server returns the intended staff role; the switch installs VLAN 110; the controlled probe to 10.10.14.10 succeeds. The written policy prohibits staff access to that management service. No effective-filter output or packet-path trace has yet been supplied.

**Task:** write the next evidence request and two candidate explanations. Separately size eighteen 36 W PSE allocations against a 740 W budget with 10% reserve and the assumed 370 W surviving budget.

**Model reasoning:** inspect installed filters and the actual path, including another interface or a policy bypass. Correct authentication does not prove enforcement. Normal allocations total 648 W and fit the 666 W usable budget. Nine allocations fit the 333 W failed-state budget; priorities and service coverage must decide which nine. Passing admission and retaining electrical power are different acceptance conditions.

## 6. The review meeting — Chapter 16

For this card only, double London's assumed AP demand to 1.2 Gb/s per AP. Retain the other Chapter 16 inputs and its 25% growth factor.

**Task:** submit a one-page decision for the design authority and a short handover for operations.

**Model reasoning:** each access switch requires 7.10 Gb/s after growth, below a surviving 10 Gb/s leg by nominal line rate. The twenty-switch bound is 142 Gb/s, above the surviving 100 Gb/s server attachment if that bound is directed there. Request the real traffic matrix, assess added surviving capacity or changed load placement, and retain the separate single-server-edge failure point. Give an owner and deadline to each unresolved item; “resilient” is not a test result.

## Review your submission

Use Appendix G's four dimensions: mechanism/units, evidence/limits, service/recovery reasoning and communication/ownership, each scored 0–2. Aim for at least 6/8, no zero and no unresolved material error. Explain one changed input aloud. Another well-supported design can pass.

Keep predictions separate from constructed cards and actual observations. To progress to a lab, follow Labs 11–16 within their stated scope: Linux bridges do not qualify vendor ASICs; classic STP does not qualify RSTP; a protocol-only 802.1X exercise does not prove enforcement; arithmetic does not qualify RF or MC-LAG. Retain failed attempts and restoration in EVIDENCE-FORM.md.
