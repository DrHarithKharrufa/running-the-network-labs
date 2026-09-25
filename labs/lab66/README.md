# Chapter 66: incident evidence exercises

These standard-library Python 3.10+ exercises run offline. They use synthetic
data and make no network connections or changes to devices. From this directory:

```text
python -B timeline.py
python -B renewal_gate.py
python -B -m unittest -v test_incident_models.py
```

`timeline.py` retains event, observation and report time separately. For a source
clock reading t, offset o = source clock minus UTC, and investigator-supplied
uncertainty u, the UTC event interval is [t-o-u, t-o+u]. Unknown event time, offset
or uncertainty produces UNKNOWN. Overlap does not establish simultaneous events
or causal order; touching endpoints cannot establish strict order. Receipt times
are metadata and never substitute for the event. The model does not estimate
clock errors, prove timestamps genuine, handle leap-second strings, reconcile
contradictory sources, or infer causation. A zero bound must be justified outside
the model. Retain the original logs and the grounds for each bound.

Expected example: router event [02:39:59, 02:40:03] UTC; probe event [02:40:02,
02:40:04] UTC. Result OVERLAP. An event with only receipt/report time is UNKNOWN.
Artificially setting both bounds to zero changes the first verdict to BEFORE.

`renewal_gate.py` models a TLS certificate deployment acceptance decision.
Approved per-target SHA256 certificate fingerprints are compared with the
certificate each synthetic probe says it received. The model requires a fresh
sample, expected certificate, valid dates with the selected remaining-validity
reserve, and an explicit successful TLS validation result. Issuance alone is not
an input that can make the model pass. The TLS verdict is assumed to include
the intended hostname, trust chain and applicable validation policy. The script
does not perform any of those validations. A sample cannot establish continued
health after it was taken or coverage of undiscovered targets.

Default synthetic policy: 60-second maximum sample age, seven-day minimum
remaining validity; both boundaries inclusive. Missing, stale, future-dated or
incomplete evidence is UNKNOWN; a known current failure takes priority over
UNKNOWN. Empty scope, duplicate/unexpected target, malformed data or non-positive
limits raise ValueError rather than silently passing. The caller must resolve
conflicting samples; this model deliberately accepts one per target. Real
collectors also need clock uncertainty, connection timeout handling, complete
endpoint/SNI/path coverage, approved trust policy and protected evidence storage.

Examples: certificate issued but one target still serving the old certificate:
FAIL; one target not sampled: UNKNOWN; both targets checked: PASS; validation
failure: FAIL; a stale sample: UNKNOWN. PASS means the supplied model criteria
were met for this target set and time. It is not a production security approval,
proof of remediation effectiveness over time, or vendor/hardware validation.

Tests include boundary, negative-input, missing-evidence, reversal and permutation
cases. The chapter verifier has a separate before-copy control. There was no
pre-existing Lab66, so no historical implementation or device run is implied.
