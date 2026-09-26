# Qualification of RTN-2026-09-26

Fresh execution on 26 September 2026: **106 of 108 declared test programs pass; two are NOT_RUN**. The Windows Python 3.12.14 batch ran 102; four additional Linux/Python 3.14.4 fixtures passed. Two changed suites were rerun after corrections, not counted again: 15 harness tests and 30 practical-route tests. See evidence/test-programs-2026-09-26.json; full logs are in the author package's QA/completion.

The two NOT_RUN programs are labs/lab53/test_iacl_exceptions.py and labs/lab53/test_urpf_modes.py. Their privileged Linux packet-filter environment was not available in this run. Do not convert this into “all tests pass”. Other lab hardware/service requirements remain per-lab; these 108 programs are not 108 network deployments.

## Fresh routing and workflow execution

- Seven complete FRR 10.2.1 topologies: 49 captures with all declared checks passing on the final harness.
- Ten additional workbook fault/address phases: 25 captures passing, including static failover/restoration, bound BFD, OSPF wrong-key rejection/recovery and bidirectional /31 and /127 reachability.
- Seventeen exact schema-2 records are in evidence/revision-2026-09-26. Record, output, harness, topology and image hashes identify different objects. None is an authorship signature.
- Eight Python course programs exercised in ten CLI invocations. The fleet's exit 1 is intentional and verified.
- A real local n8n 2.40.7 webhook/HTTP workflow and Python/SQLite adapter passed 12 integration checks. Inputs/devices are simulated. Evidence is in evidence/modern-operations-2026-09-26.
- The optional AI adviser has schema, evidence-ID and failure/fallback tests. No actual model was run. Power Automate has a construction and acceptance guide, not an executed tenant export.

Earlier failed routing, setup, import and boundary attempts remain in the author QA archive. Initial FRR packet failures led to explicit IPv4 forwarding setup. Incorrect endpoint assumptions in an initial address check were corrected and rerun. A final recovery check now refuses success when the description is restored but the service remains unhealthy or unknown.

## Boundaries that still matter

No fresh commercial NOS, hardware, ASIC, RF/optical, cloud-platform, alarm-storm, high-availability, live PRTG, Power Automate tenant, external notification or containment qualification occurred. Selected historical Cisco IOS parser/control-plane observations and FRR 10.5.1 records remain in the author archive with their original dates and limits. They neither vanish nor become evidence for every present configuration.

READ workbook panels remain documentation examples. Their complete Nokia SR Linux 24.10 baseline and official source URLs are supplied, but no new SR Linux run is claimed. A virtual FRR pass is not vendor or hardware acceptance.

No real novice/engineer/leader reader trial or independent subject review was performed in this correction pass. The route is implemented and locally tested; its teaching effectiveness and reader enjoyment still need observation. The matching public release, Amazon Previewer and physical proof remain publication gates.
