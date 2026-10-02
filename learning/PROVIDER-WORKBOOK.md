# Provider services: seven paper sessions

Use Chapters 23–29 after the routing workbook. These sessions follow one invented provider review from receiver interest to an accepted customer service. **Every observation below is constructed for teaching. None is a new lab result, device capture or measurement.** The packet identifiers and numerical inputs are local to this workbook; they do not amend the shared Kestrel lab topology.

Spend roughly 25–40 minutes on each session. First submit your prediction and the next observation you would collect; then read the model reasoning. Keep unperformed tests under that name. For actual execution, select a supported lab adapter and its validation record, agree a bounded test, and use EVIDENCE-FORM.md. Linux, Containerlab and vendor/hardware results remain separate evidence.

## 1. The joined receiver with no picture — Chapter 23

**Constructed observations.** Source S=10.1.0.10 sends to G=232.1.1.1. At the last-hop router, the effective RPF interface for S is A. Receiver interest exists on B; a snooping entry includes the receiver's switch port. A capture shows stream packets arriving at the router on C. No matching packets leave B. The address and interfaces are teaching identifiers, not a deployable configuration.

**Your submission.** Draw interest travelling towards the source and data travelling towards the receiver. Explain the first disagreement, then propose one observation that can distinguish an unintended source path from a wrong multicast RPF selection. Define the restoration test.

**Model reasoning.** Receiver membership and downstream switching state do not correct a packet arriving on the wrong upstream interface for this SSM state. Check the source path, route/policy and effective PIM lookup; compare the selected RPF interface with the incoming capture. Do not infer a missing querier from silence alone when this constructed case supplies membership and a different contradiction. Correct only the intended fault, then verify the source sequence at the router and receiver, loss, and restoration of the original intended route. Changing the incoming interface without confirming why can conceal a topology/policy error.

**Change the input.** The RPF check now agrees, but the outgoing list is empty. Which receiver/membership transition must you inspect next? Explain why this is a new fault boundary.

## 2. The provider map earns its keep — Chapter 24

**Inputs.** Use the chapter's 50,000 subscriptions, 900 business circuits and artificial graph exposure model. Two candidate failure pairs both expose 50,900 units: the borders, or the represented PE plus BNG. The shared graph implements neither subscriber authentication nor CGN.

**Your submission.** Give the NOC a next diagnostic step for each failure pair and give the sponsor a paragraph explaining why equal totals do not rank the investments. Repair the business/broadband IPv6 plan and state the residual capacity.

**Model reasoning.** Border loss removes the represented general-transit paths; PE/BNG loss removes the relevant access/service attachment paths. The exposure sum does not measure unique people, service restoration or stateful dependencies. Build a separate dependency inventory before ranking recovery investment. The business /38 offers 1,024 /48s, with 124 left after 900; broadband 2001:db8:4400::/40 offers 65,536 /56s, with 15,536 left after 50,000. Both sit disjointly inside 2001:db8:4000::/36. The old 4100 broadband block would overlap the expanded business pool.

**Change the input.** A second “independent” circuit uses the first circuit's building entrance and duct. Update the failure model before adding the bandwidths.

## 3. Follow the service label — Chapter 25

**Constructed observations.** The predicted stack is [1002,24002] on PE1–P1, [2003,24002] on P1–P2 and [24002] on P2–PE2 after PHP, top first. A capture agrees on the first link but shows unlabelled IP leaving P1. A small ping to PE2's loopback succeeds. These are invented observations, not a revision to the book's historical MPLS execution.

**Your submission.** Identify the earliest contradiction and name the lookup/action and context to inspect. Separately calculate the inner-IP and IPv4 Echo-data budgets for a 1,514-byte frame limit excluding FCS with four labels and two tags.

**Model reasoning.** P1's observed output differs from the expected top-label swap while retaining the service label. Inspect its incoming-label context/action for 1002, actual installed forwarding and the capture's exact interface/direction; confirm that capture decoding has not hidden the stack. The loopback ping cannot validate the customer service action. The size budgets are 1,476 inner-IP bytes and 1,448 Echo-data bytes under base IPv4/ICMP assumptions. Neither observation alone proves a specific NOS defect.

**Change the input.** The same numeric frame limit includes FCS. The answers become 1,472 and 1,444. Explain why a four-byte accounting change can create an apparently intermittent large-packet fault.

## 4. The resilience slide loses a path — Chapter 26

**Inputs.** Two 10 Gb/s paths carry 8 Gb/s sensitive and 6 Gb/s flexible demand. Delays are 4 ms through Manchester and 9 ms through Birmingham. A fictional service owner requires the sensitive traffic's path delay to remain at most 6 ms under either specified single-path failure.

**Your submission.** Calculate the survivor deficit and decide whether the current design meets the stated failure promise. Write the next design decision without asserting that a priority queue reduces propagation delay.

**Model reasoning.** There is a 4 Gb/s capacity deficit; protecting 8 leaves at most 2 flexible before headroom. If Manchester fails, the 9 ms survivor violates the assumed 6 ms limit even if sensitive bandwidth is preserved. Choose a feasible lower-delay alternate or renegotiate the service requirement with its owner; both need evidence and a complete cost/availability comparison. No supplied result establishes real delay or controller behaviour.

**Change the input.** Require 1 Gb/s extra survivor headroom and permit 10 ms path delay. The model's flexible allowance falls to 1 Gb/s; the stated path-delay contradiction disappears. Packet loss, queueing and total application delay still require acceptance.

## 5. Fit the SRv6 packet — Chapter 27

**Inputs.** The service needs a 1,500-byte inner IP packet. Full encapsulation stores five SIDs with no TLVs. The candidate outer-IP path MTU is 1,600. A second proposal claims “compression means only 40 extra bytes” but gives no SID layout or service behaviour.

**Your submission.** Calculate the first packet, quantify its shortfall and ask for the missing evidence in the second proposal. Decode 2001:db8:4500:23:0100:: using a declared 64/16/48 locator/function/argument layout.

**Model reasoning.** Full overhead is 128 bytes; outer size is 1,628, exceeding 1,600 by 28. At that path limit the inner budget would be 1,472, not the required 1,500. Obtain the complete encoding, endpoint behaviours, block transitions, arguments and supported hardware. Forty bytes is possible only under the specifically supported no-SRH construction described in the chapter, not a generic compressed-list promise. The SID's /64 locator ends in :23, function is 0x0100, arguments zero; its actual installed behaviour must come from the endpoint inventory.

**Change the input.** Six transport instructions and one service instruction each need a 16-bit slot after a 32-bit block. Six slots cannot contain seven instructions; revise the encoding and then the MTU budget.

## 6. Accept the VPN in both directions — Chapter 28

**Constructed observations.** The egress PE has learned the remote customer prefix. The ingress VPN table receives its route, but the intended VRF does not import it. Underlay loopback probes succeed. An unrelated tenant uses the same customer address in a separate VRF.

**Your submission.** Explain the current fault boundary, distinguish RD from RT, and write one positive service test and one negative isolation test after correction. Include the reply.

**Model reasoning.** Investigate the route's RTs, complete import policy and intended VRF before changing transport labels. A received VPN route is not yet a selected customer forwarding entry. An RD distinguishes VPN prefixes in BGP; it does not authorise import or disambiguate identical destinations inside one ordinary IP routing table. After the authorised correction, inspect selection and forwarding resolution, then send a customer-sourced transaction through both attachments and verify the reply. Capture at the unrelated tenant to ensure prohibited delivery does not occur. Its reused address is valid only while the required contexts stay isolated.

**Change the input.** Both overlapping /24s now belong to one routed customer VPN. Explain why different RDs alone do not solve the customer's destination ambiguity; propose a service-level addressing/context remedy.

## 7. A green multihoming screen is not the sign-off — Chapter 29

**Constructed observations.** The CE has a two-member LAG. Matching ESI and DF election are visible. A numbered remote broadcast reaches the CE twice; one known-unicast flow succeeds. A large inner-IP test of 1,500 bytes is planned over untagged IPv4 VXLAN with outer-IP MTU 1,500.

**Your submission.** Identify two independent acceptance problems and the necessary capture boundaries. Write a short hold/rollback decision for the service owner, and a separate CTO-facing statement of what remains unqualified.

**Model reasoning.** Duplicate broadcast delivery fails the stipulated single-copy expectation for that test. Check DF forwarding towards the segment and source-ES split horizon using direction-specific captures rather than treating every duplication mechanism as the same. The packet also needs 1,550 outer-IP bytes, so the stated underlay cannot carry it unfragmented as specified; the inner budget is 1,450. Fix and qualify both issues before acceptance. One unicast flow proves neither load sharing nor complete multihoming. The book's real Lab 30 limitations remain in its validation record; this constructed case does not replace them.

**Change the input.** Use base IPv6 VXLAN and preserve an inner VLAN tag. Required outer-IP size becomes 1,574; the 1,500-byte outer path permits 1,426 inner-IP bytes. Recalculate rather than adding a memorised “50-byte VXLAN overhead” to an unspecified boundary.

## Submit a portfolio, then move to a supported lab

Keep seven predictions, their calculations, each first contradictory observation, a restoration/acceptance plan and one decision memo. Score mechanism/units, evidence/limits, service/recovery and ownership/communication from 0 to 2 each. Aim for at least 6/8 with no zero and no unresolved material technical or recovery error. A peer should change an input and ask you to revise the conclusion. Without a peer, explain the change aloud and retain your first and corrected answers.

Chapters 30–33 continue provider operation with QoS, subscriber services, peering and provider security. Real service acceptance still requires execution in the relevant environment, observation of failure and recovery, and the service owner's criteria. This workbook supplies practice in reasoning and test design.
