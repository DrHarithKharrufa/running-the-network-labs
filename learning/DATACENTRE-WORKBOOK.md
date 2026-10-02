# Data-centre workbook: from a rack to an accepted service

Eight paper sessions for Chapters 34–41. All observations below are **constructed teaching inputs**, not captured traffic, lab output or deployment evidence. Work in the fictional Anvil data centre; the final hybrid session connects the separate Aldergate enterprise case to a cloud. Do not merge their address plans merely because both appear here.

Submit a prediction, a calculation or packet path, a distinguishing test, a rollback/recovery condition and a short decision note for each session. Consult the selected answers after attempting it. Actual execution requires the chosen lab's supported environment and your own records. These sheets can be completed without commercial NOS or GPU hardware.

## 1 — Capacity after the less convenient failure (Chapter 34)

A general leaf has 24 × 25 Gb/s server interfaces and eight 25 Gb/s uplinks, one to each spine. The uplinks occupy two four-lane breakout cages. The salesperson shows only the one-spine-failure figure.

Calculate normal capacity, one-spine failure and one-cage failure. **Model guidance:** 600/200 = 3:1; 600/175 = 24:7; 600/100 = 6:1. The cage shares four lanes' fate. Explain why neither a 3:1 label nor eight distinct spines promises survival at the normal service target. Draw which workloads share that cage and propose a requirement for the degraded state. Ask what would falsify a claim that the four lanes are independent. Deliver the same arithmetic in an engineer's port table and a director's two-sentence risk note.

## 2 — Three gates before forwarding (Chapter 35)

Four neighbours show Established. Constructed route detail says four updates were received, three were accepted, two have equivalent eligible attributes and only one next hop is installed.

Do not choose a knob yet. Make three columns: admission, selection and installation. Name evidence for the rejected advertisement, the third accepted route's ineligibility and the final installation limit. **Model guidance:** a filter can explain the first reduction, a policy/next-hop difference the second, and an ECMP installation limit the third. These are hypotheses, not causes established by the numbers. Propose one change at a time with a known inverse and a permitted-prefix negative test. A changed FIB still needs a data-plane test.

## 3 — Small packets make poor witnesses (Chapter 36)

Tenant traffic crosses untagged VXLAN over outer IPv4. The underlay IP MTU is 1,500 bytes. Small pings work; a constructed capture shows an attempted 1,500-byte inner IP packet.

Draw every header. **Model guidance:** the outer IP packet would be 1,550 bytes, exceeding the stated limit; 1,450 is the maximum inner IP packet without additional headers. With inner IPv4 ICMP, the maximum data is 1,422 bytes. Decide whether to raise a qualified end-to-end underlay MTU or lower the tenant MTU, including hosts and overlays. Test the boundary and one byte beyond it, with actual packet-size semantics recorded. Do not interpret a failed ping alone as proof of the exact drop location. For IPv6, repeat the budget rather than recycling the same number.

## 4 — A route can be true in one database (Chapter 37)

Constructed observations: bgpd accepted the prefix; the routing manager selected it; an orchestration log reports a failed next-hop operation; a traffic probe fails. The switch still has a route in its routing-table display.

Draw the route's owners from protocol to forwarding. Identify the last proven state and request evidence on either side of the failed boundary. **Model guidance:** routing-table presence does not prove successful ASIC programming or adjacency resolution. Check the exact prefix/VRF and error context before assuming the log belongs to this flow. Write an escalation containing versions, timestamps, reproduction and rollback, without calling the whole NOS broken. Then allocate responsibility for firmware, SAI, platform and NOS support in the purchase contract.

## 5 — The verifier did not read the change request (Chapter 38)

The policy says “block source 192.0.2.9”. Consider untagged IPv4, IPv4 with options, an IPv4 fragment, VLAN-tagged IPv4, IPv6 and ARP against the shipped source-address dropper.

**Model guidance:** the first three still reach IPv4 source matching after its base-header checks; the last three do not. IPv6 needs a distinct address/policy, not a reinterpretation of the IPv4 literal. Build a test matrix with allowed, blocked, truncated and malformed packets. Include packets that expose a policy omission without violating memory bounds. Distinguish code inspection, a host model, verifier acceptance and actual hook execution in the evidence form. No one of them automatically proves the others. Decide whether this narrow example is adequate for the stated deployment; a safe answer can be to redesign the policy before deployment.

## 6 — Two teams and one packet (Chapter 39)

A two-member 25 Gb/s LACP bond is up. A single-flow backup reaches 7 Gb/s. Constructed observations show low average fabric utilisation, one busy host core and no reported drops on the port inspected.

Draw the sender and receiver path and identify where a capture occurs relative to segmentation/checksum completion. **Model guidance:** one flow cannot simply add member rates, and 7 Gb/s still needs diagnosis below the single-link ceiling. A busy core is a hypothesis; compare application, TCP, queue and receiver evidence at matching times. Propose a bounded multi-flow test and inspect both directions' member distribution. Decide jointly who owns MTU, LACP and application acceptance. Do not present a quiet port or an `[offload: on]` flag as a verdict.

## 7 — A premium fabric must buy useful time (Chapter 40)

Use the constructed 16-rank, 200 Gb/s, 5 μs model from answer 41.4. Derive the 2,000,000-byte crossover and 300 μs total time at it. Then use g = £4, fA = £0.40, fB = £0.10 per GPU-hour and c = 0.20. Compare s = 0.50 with s = 0.20.

**Model guidance:** the £0.30 premium is below £0.44 in the first case and above £0.176 in the second. A communication fraction alone cannot select the fabric. Record what a controlled vendor trial must measure to estimate s. Constructed rising PFC counters add a diagnosis task: list threshold, classification, feedback and downstream-stall hypotheses and one observation that distinguishes each. No threshold from the fluid queue model belongs in switch configuration.

## 8 — A cloud route and a bill tell different stories (Chapter 41)

Aldergate's receiving router has circuit 10.10.0.0/16 at preference 200 and VPN 10.10.1.0/24 at 50. Predict routes for 10.10.1.7 and 10.10.2.7. **Model guidance:** VPN then circuit; longest-prefix match compares the installed prefixes, not their preferences against each other. Write the intended advertisement policy and a failure/restoration acceptance test.

Price a separately constructed 40,000 GB/month transfer at £0.01/GB: £400/month. A resilience reduction adding 0.1 expected downtime hour/month breaks even at £4,000/hour before other differences. Challenge the downtime assumption and the metering boundary. Submit a short funding note that names the cloud provider, service mode, DNS/encryption dependencies, recovery owner and unresolved evidence. The director should be able to see what the lower bill would actually give up.

## Completion review

Use Appendix G's four-dimension rubric: mechanism/units, evidence/limits, service/recovery and communication/ownership, each scored 0–2. Aim for at least six with no zero and correct material errors. Have a reviewer change one input: remove a cage, add an inner VLAN, halve a link rate or change cloud provider. Revise the affected reasoning without silently changing the other facts. Self-review is useful; real learner feedback and platform acceptance remain separate work.
