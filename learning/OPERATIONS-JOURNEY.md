# Aldergate: commission, operate, recover, explain

Edition RTN-2026-10-04. This is the connecting route through the existing executable exercises. Allow several sessions; completion time has not been measured with readers. Keep a folder of **your own** observations, not a copy of the author records. Chapters 2–8 teach packet/address reasoning; 16–22 explain routing; 60–66 cover operations; 70–71 develop automation; 82–87 cover decisions.

There are two deliberately separate systems: real FRR containers and packet probes on a Linux lab host, and a small Python HTTP/SQLite **device simulator**. The n8n route uses the latter. They are not secretly integrated and passing one does not qualify the other. A real-device monitoring adapter is a later extension with its own acceptance test.

## 1. Establish a service and its boundaries

Use learning/START-HERE.md and EVIDENCE-FORM.md. Draw r1, r2, their /31 link and loopbacks from harness/topologies/ospf-p2p.yml. Identify the forward and return route. Define a successful lab service as three echo replies from the specified remote loopback with zero loss, plus the expected adjacency and installed route. This tests a packet path, not DNS, an application transaction, throughput or production availability.

Read harness/README.md. Use a dedicated Linux/Docker host with root and PyYAML; Windows may drive a WSL2 Linux environment. The Python course can run locally on Windows without Docker. Do not describe a preconfigured Linux success as evidence that a clean Windows install is effortless.

## 2. Commission and capture a baseline

From the companion root on that Linux host, run:

```text
python3 harness/netlab.py run harness/topologies/ospf-p2p.yml -o my-ospf-baseline.json
```

The combined run provisions, configures, observes and cleans up. Expect every capture to match with no command error. Read the node identity, configuration transcript, OSPF state, installed route and ping output. Retain the full record, image digest and exact topology. If any observation is empty or invalid, stop and diagnose; do not turn an UNKNOWN into a passed absence check.

In the configuration workbook do IGP-01 and IGP-02 first, then IGP-05/06. The node comments matter. A RUN label applies only to its cited FRR record. READ panels require the named vendor baseline and an independent run.

## 3. Observe a normal day before automating it

Complete practical-route sessions 1–4. Start the local teaching service with a new database, then save the output of 04_collect.py as a timestamped baseline. Identify the owner from inventory, known down interface, and missing data separately. Its four errors in 100 packets are a cumulative constructed fraction, not a sampled rate.

Run 06_fleet.py. Preserve its intentional UNKNOWN and exit 1. Write a handover containing the affected target, last good observation, evidence still missing, owner and next bounded check. A daily report that hides one failed collection is incomplete even if most devices replied.

## 4. Fail, diagnose and restore routing

Run the complete fault suite from the companion root:

```text
python3 harness/workbook_checks.py --out my-workbook-evidence
```

It starts from named clean baselines and records ten phases: plain static normal/link-down/recovery, BFD-bound normal/peer-down-with-link-up/recovery, OSPF wrong-key/recovery and two IPv4/IPv6 endpoint checks. Compare the primary and backup route with the actual packet probe. Explain why BFD must have a client binding, and why an Ethernet-up state does not prove the peer can forward.

Before opening the author record, predict the result. Then explain one failed hypothesis and cite your observation. Record the recovery as configuration, control-plane and packet evidence separately. Do not infer a measured subsecond recovery time from an advertised timer.

## 5. Control a change and prove recovery

Complete sessions 5–7. Save 04_collect.py output before the change; this JSON is a simulator state baseline, **not** a vendor configuration backup. Keep the dry-run plan and generation. Exercise an accepted change, no-op, rejected service check and restoration. Inspect the lost-response test and explain why the program does not retry the write.

A rollback is accepted only when the restored description/generation and simulated service check agree. RECOVERY_SERVICE_FAILED or RECOVERY_UNKNOWN requires investigation. For a real router, use Chapters 64 and 70 plus the platform's backup/restore mechanism, independent service test and approved recovery window; those mechanisms are not supplied by this simulator.

## 6. Receive an alarm and leave an owned case

Complete session 8, then practical-route/N8N-LAB.md. Send the same saved event twice; inspect one durable case and a duplicate response. Restart and submit it again. Test a bad credential, unknown sensor and failed collector. Record the separate investigate/dismiss decision. Do not close a network incident merely because the workflow returned 200.

Use POWER-AUTOMATE-LAB.md to construct the equivalent cloud flow when a suitable tenant is available. Its SharePoint/Approvals acceptance is still unexecuted. Optional AI is an unreviewed adviser; the deterministic route works without it.

## 7. Explain the incident and the investment

Write a short incident record: impact as actually measured, timeline, competing hypotheses, observations, recovery, unresolved cause, follow-up owner and verification date. Separate synthetic device state from the real FRR packet trial; do not splice them into one fictional measured outage.

Run `python learning/case_math.py` from the companion root and complete CAPSTONE-WORKBOOK.md steps 4–5. Change the growth assumption and delivery lead time. State the forecast trigger, survivor capacity, cost/cash constraint, uncertainty and decision owner. These are explicitly invented business inputs, not supplier quotations or a tested organisation.

## Final transfer task and rubric

Choose one change: a different /31, an additional inventory target, an old event, a failed return route, or a longer circuit lead time. Predict, execute/calculate, preserve the unexpected result and explain the decision. Ask a peer to change one more input without telling you the answer.

Submit diagram, baseline, fault/recovery record, dry-run/change report, durable case, incident handover and decision memo. Score mechanism/units, evidence/limits, recovery/service reasoning and communication/ownership from 0–2 each. Aim for 6/8 with no zero and no unresolved material error. This is a learning rubric, not a professional licence or proof of readiness for a CTO role.
