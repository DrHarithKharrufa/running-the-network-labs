# Qualification of RTN-2026-10-04

**Which runs belong to this edition, and which are carried forward.** One
test run was made for this edition, on 3 October 2026, and it is described
first. The FRR topology runs below were executed on 26 September and 1 October
2026 and have **not** been repeated for this edition; their dated evidence
folders, `evidence/revision-2026-09-26/` and `evidence/revision-2026-10-01/`,
are where they live and those dates are part of the claim. Nothing below should
be read as a statement that an earlier run was re-executed for this edition.

**This edition's run, 3 October 2026.** **All 109 declared test programs pass in
one run on one host**, including the two privileged Lab53 suites: Linux 6.18 in a
container, as root, Python 3.11.15, iproute2 6.1.0 and nftables 1.0.9, using
`python run-all-tests.py --include-live` in a copy of this edition's payload. The
uRPF suite reported 79 checks and the infrastructure-ACL suite 46, none failed.
Results, with the SHA-256 of every test program, are in
`test-results-2026-10-03/execution-RTN-2026-10-04.json`. It is still 109
programs, not 109 network deployments, and only Lab53 uses real privileged
packet filters. The programs are byte-identical to the previous edition's.

**Earlier runs, retained for comparison.** Earlier the same day the same complete
set passed on the same host for the earlier edition RTN-2026-10-03; that record
is `execution.json` in the same dated folder and is unchanged. On 2 October 2026
the same set passed for the earlier edition RTN-2026-10-02, the first
single-host run of all 109 (`test-results-2026-10-02/`). On 1 October 2026, 107 of 109 passed
with the two Lab53 suites NOT_RUN (Linux, Python 3.11.15;
`test-results-2026-10-01/`). On 26 September 2026, 106 of 108 passed, two
NOT_RUN; that run was on Windows Python 3.12.14 for 102 of them, with four
additional Linux/Python 3.14.4 fixtures, and two changed suites were rerun after
corrections and not counted twice (15 harness tests, 30 practical-route tests).
See `evidence/test-programs-2026-09-26.json`; full logs are in the author
package's QA/completion. These runs are on different operating systems and
Python versions and are not a measurement of the same thing twice.

The count rose from 108 to 109 in the earlier edition RTN-2026-10-01, when
`labs/reference-designs/test_check_addressing.py` was added. Other lab
hardware/service requirements remain per-lab.

## Independent AI review execution, 1–2 October 2026

The two previously NOT_RUN Lab53 suites were executed as root on WSL2 Linux
6.18.33.2, Python 3.14.4, nftables 1.1.6 and iproute2 6.19.0. The uRPF suite
reported **79 checks, 0 failed**; the infrastructure ACL suite reported
**46 checks, 0 failed**, with no privileged skips. The raw logs, environment,
source hashes and empty post-run namespace listing are in
`evidence/review-2026-10-01-codex/lab53/`. This is new Linux namespace evidence,
not commercial forwarding-plane qualification and not a relabelling of earlier
109-program runs. The earlier NOT_RUN entries remain historical records.

**Additional suite coverage.** This review ran 108 declared programs on
Linux/Python 3.14.4 (one NOT_RUN for absent pinned Lab71 packages), and ran that
remaining Lab71 program separately on Windows/Python 3.12.10: 19 tests passed.
Thus every one of the 109 declared programs had a successful run across those
two environments; that review did not claim a single-host 109/109 run (this
edition's run, above, is one). The Windows quick run
also passed 102 programs with seven NOT_RUN. The first Windows run's missing
Jinja2 failure is retained; its prerequisite declaration was corrected.
Only Lab53 uses real privileged packet filters; many other suites use synthetic
inputs, fixtures or command doubles. Anonymous public-tag acquisition and the
three printed entry tasks succeeded. See this review's evidence folder.

Three independent AI reader reviews and simulated reader walkthroughs were
performed. They are not human participant trials or a physical bound proof.

## Fresh routing and workflow execution

- Seven complete FRR 10.2.1 topologies, 26 September 2026: 49 captures with all declared checks passing on the final harness.
- Three further FRR 10.2.1 topologies, 1 October 2026: 19 captures, all declared checks passing. They settle one question the workbook had left open --- whether a router checks the OSPF Hello's network mask --- by varying only the interface type across three runs on the same pair of routers.
- Ten additional workbook fault/address phases: 25 captures passing, including static failover/restoration, bound BFD, OSPF wrong-key rejection/recovery and bidirectional /31 and /127 reachability.
- Seventeen exact schema-2 records are in evidence/revision-2026-09-26. Record, output, harness, topology and image hashes identify different objects. None is an authorship signature.
- Eight Python course programs exercised in ten CLI invocations. The fleet's exit 1 is intentional and verified.
- A real local n8n 2.40.7 webhook/HTTP workflow and Python/SQLite adapter passed 12 integration checks. Inputs/devices are simulated. Evidence is in evidence/modern-operations-2026-09-26.
- The optional AI adviser has schema, evidence-ID and failure/fallback tests. No actual model was run. Power Automate has a construction and acceptance guide, not an executed tenant export.

Earlier failed routing, setup, import and boundary attempts remain in the author QA archive. Initial FRR packet failures led to explicit IPv4 forwarding setup. Incorrect endpoint assumptions in an initial address check were corrected and rerun. A final recovery check now refuses success when the description is restored but the service remains unhealthy or unknown.

## Boundaries that still matter

No fresh commercial NOS, hardware, ASIC, RF/optical, cloud-platform, alarm-storm, high-availability, live PRTG, Power Automate tenant, external notification or containment qualification occurred. Selected historical Cisco IOS parser/control-plane observations and FRR 10.5.1 records remain in the author archive with their original dates and limits. They neither vanish nor become evidence for every present configuration.

READ workbook panels remain documentation examples. Their complete Nokia SR Linux 24.10 baseline and official source URLs are supplied, but no new SR Linux run is claimed. A virtual FRR pass is not vendor or hardware acceptance.

No real novice/engineer/leader reader trial or independent subject review was performed in this correction pass. The route is implemented and locally tested; its teaching effectiveness and reader enjoyment still need observation. Amazon's previewer and a physical bound proof remain publication gates; this tag is the matching public release.

## The Configuration Workbook

The workbook has 120 tasks across ten parts, 714 documentary
READ panels and six explicit NO_PANEL outcomes. The dated official syntax
provenance is in the source QA ledger and reader baseline register. All six
planned outcomes were pursued for each task. None of these new panels is
promoted to RUN by the controller checks.

The new workbook kit passed 196 synthetic offline guard/XML checks and 21
counter checks. Local TCP/UDP services and CA-verified HTTPS were exercised,
including incomplete-message, wrong-server-name and absolute-deadline
negatives. Packet files were generated and decoded without transmitting them
to a device. The author QA reports record the precise scope and hashes.
Three independent AI readers reviewed the continuation and performed simulated
walkthroughs; these are not human teaching trials or specialist acceptance.
