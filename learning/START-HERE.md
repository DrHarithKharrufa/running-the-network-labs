# Running the Network: learning companion

Edition: RTN-2026-09-26, practical route and print proof. Start with Appendix G in the matching book. This directory supplies a learning route and worked guidance for all 500 chapter exercises; the existing `labs/` directory supplies the technical lab files and their environment-specific READMEs.

1. Complete the number and terminal entry checks in Appendix G and Chapter 3.
2. Choose the first milestone below that you cannot yet demonstrate.
3. Read the relevant mechanism, predict a result, then attempt the exercise before consulting an answer.
4. Keep the actual evidence, including failed attempts and recovery. Label paper calculations and synthetic data accordingly.
5. Use the rubric with a peer, or explain a changed input aloud during self-study. Correct material mistakes before advancing.

| Milestone | Core reading | Practical submission | Worked guidance |
| --- | --- | --- | --- |
| L1: explain | Chapters 1-9 | Packet path, /26 calculation, rate/delay bound | Answers for Chapters 1-9 |
| L2: change and recover | Chapters 10-18 and 61-66 | Lab 3.2 baseline, return-route fault, restoration and handover | Answers for Chapters 3 and 10-18; the evidence form |
| L3: deliver a service | Chapters 19-23, chosen service chapters, security 50-53 | Client transaction, platform/configuration record, fault diagnosis and acceptance | Answers for Chapters 19–60; provider, edge, data-centre, transport and security/operations workbooks; capstone steps 2-3; the chosen lab README |
| L4: defend a design | Chapters 67 and 79-84, Appendix C | Alternative designs, shared-failure and survivor-capacity analysis | Chapters 67 and 79–84 answers; design/leadership workbook; capstone step 4 |
| L5: govern a decision | Chapters 85-91; 74-78 for automation | Funding memo, staffing, changed assumption and follow-up | Chapters 74–78 and 85–91 answers; modern-operations and design/leadership workbooks; capstone step 5 |

Reading can run alongside practice. Campus (11-16), provider (24-34), data centre (35-42) and transport (43-49) are specialisation routes, not competing levels of seniority. Select them from the service you need to understand. The milestones do not confer production authority or a professional title.

For the first ten chapters, work through `FOUNDATIONS-WORKBOOK.md`: specify one service, predict a packet and reply, interpret constructed DNS/route evidence, then hand over an unresolved incident. Then use CAMPUS-WORKBOOK.md for a six-session commissioning review through Chapters 11–16. Continue with ROUTING-WORKBOOK.md for seven sessions through Chapters 17–23, ending with a shared-service acceptance plan. PROVIDER-WORKBOOK.md adds seven sessions through Chapters 24–30, from multicast to provider transport and service acceptance. EDGE-WORKBOOK.md adds four sessions linking QoS, subscriber service, billing and routing security in Chapters 31–34. DATACENTRE-WORKBOOK.md adds eight sessions through Chapters 35–42. Continue through TRANSPORT-WORKBOOK.md (43–49), SECURITY-OPERATIONS-WORKBOOK.md (50–67), MODERN-OPERATIONS-WORKBOOK.md (68–78, with monitoring in 62), and DESIGN-LEADERSHIP-WORKBOOK.md (79–91). The paper sessions use constructed inputs and can precede available lab execution.

## Files

- `TRANSPORT-WORKBOOK.md`: seven paper sessions from route records to degraded transport-service acceptance.
- `SECURITY-OPERATIONS-WORKBOOK.md`: six sessions joining trust, policy, detection, staffing, diagnosis and capacity.
- `MODERN-OPERATIONS-WORKBOOK.md`: six sessions designing a PRTG/n8n investigation workflow, optional AI assistance and a bounded security agent, with alternatives and deployment criteria.
- `operations_policy.py` and `test_operations_policy.py`: an offline event journal, action/approval boundary and outbox model. It opens no network connection and executes no product integration or containment action. Run `python -B learning/test_operations_policy.py` from the companion root.
- `DESIGN-LEADERSHIP-WORKBOOK.md`: six sessions from requirements and failure domains to an accountable investment and operating decision.

- `DATACENTRE-WORKBOOK.md`: eight paper sessions from cage budgets to hybrid service acceptance; all supplied observations are constructed.

- `EDGE-WORKBOOK.md`: four paper sessions linking subscriber service to QoS, cost, capacity and routing-security evidence; supplied observations are constructed.

- `PROVIDER-WORKBOOK.md`: seven paper sessions separating membership, transport, service policy and packet acceptance; supplied observations are constructed.

- `ROUTING-WORKBOOK.md`: seven sessions following a packet, recovering a path, comparing routing information, applying policy and accepting shared services; all supplied observations are constructed.

- `CAMPUS-WORKBOOK.md`: six sessions connecting VLANs, tree selection, flow distribution, wireless, admission and an architecture decision; all supplied observations are constructed.
- `FOUNDATIONS-WORKBOOK.md`: five guided sessions linking Chapters 1-10, with clearly labelled constructed evidence and model reasoning.
- `CAPSTONE-WORKBOOK.md`: tasks, inputs, model reasoning and review prompts for the standalone fictional Aldergate branch.
- `SELECTED-ANSWERS.md`: guidance for all 500 numbered end-of-chapter exercises across Chapters 1–91; the historical filename is retained for link compatibility. Empirical exercises have evidence criteria, not invented results.
- `EVIDENCE-FORM.md`: an empty record for actual practice and peer review.
- `branch-case.json`: machine-readable teaching inputs, separate from the cumulative reference designs in Appendix C.
- `case_math.py`: offline arithmetic only; no network access, subprocesses or device changes.
- `test_case_math.py`: numerical and invalid-input checks for that calculator.

## Run the offline example

Use Python 3.11 or newer for this edition’s declared test route. From the extracted companion root:

```text
python -B learning/case_math.py
```

On systems where the interpreter is named `python3`, use that name instead. To run the calculation checks:

```text
cd learning
python -B -m unittest -v test_case_math.py
```

You should see five spare client addresses, 145 future required host addresses, and a central-growth trigger crossing at approximately 7.18 months. Option A's latest decision is about 0.82 months in the past under that scenario; option B's is about 3.18 months ahead. Inspect all three growth scenarios before selecting a modelled delivery option. These are invented inputs and offline outputs, not observations of a real service.

To change a scenario, copy `branch-case.json` to a new filename and supply it using `--input`. Keep the original inputs with your answer. The calculator deliberately models two circuits and one survivor; it is not a general routing, queue, reliability or procurement simulator. It rejects overlapping client expansion/management networks and some invalid inputs. It does not decide whether a real address pool is free or whether a policy has been implemented.

## Move to an actual lab

Read `labs/lab03/README.md` and Appendix A before installing or deploying anything. The printed first-topology commands expect an appropriate Linux host, Docker/Containerlab and the stated image prerequisites. The offline calculator above needs none of these. Vendor images are not supplied by this learning guide. Preserve the distinction between historical Linux results, an orchestration deployment and a test on a particular vendor release.

## Assessment and errata

Score mechanism/units, evidence/limits, service/recovery reasoning and communication/ownership from 0 to 2 each. For the teaching milestones, aim for at least 6/8, no zero, and no unresolved material technical or recovery error. A different well-supported design can earn full credit.

For a suspected error, record the edition, chapter/section or file, the claim, the expected result, a minimal reproduction and any primary reference. Exclude passwords, customer data and unrelated logs. The author-facing revision package includes an errata template. The public repository and issue tracker are linked in the companion README. Match EDITION.json to the book; the proof requires publication of its matching public release.


## From paper reasoning to a working tool

Open [practical-route/README.md](practical-route/README.md) for eight graded sessions.
Each provides a goal, commands, expected observation, deliberate failure, recovery
and transfer exercise, starting with no assumed Python knowledge. Then use
[N8N-LAB.md](practical-route/N8N-LAB.md) to import and run the workflow, or
[POWER-AUTOMATE-LAB.md](practical-route/POWER-AUTOMATE-LAB.md) to construct the
tenant flow and capture its acceptance record. Use [TASK-INDEX.md](TASK-INDEX.md)
when looking up a job instead of reading sequentially.


The connected [OPERATIONS-JOURNEY.md](OPERATIONS-JOURNEY.md) joins commissioning, daily checks, recovery, monitoring, a controlled change and a capacity decision. Keep the FRR network and simulated HTTP service evidence separate.
