# Lab70: local schema checks and a device validation plan

Run `python -m unittest discover -v` here: 4 unit tests with multiple boundary cases.
`validate_against_model.py` is a strict small Python schema, NOT a YANG parser,
NETCONF validation RPC or exact device implementation. Read Chapter 70
for the separate device capability, transaction and service-test plan. No NOS/API
runtime was tested in this revision. Use exact advertised modules/features/deviations,
credentials and verified TLS/SSH identities for any later entitled isolated device work.

The MTU range 68–9216 is chosen only for this exercise. It neither defines a
vendor's supported range nor establishes IPv6 link suitability (RFC 8200 requires
at least 1280 octets). The checker leaves omitted optional fields absent; it does
not process YANG defaults, features, deviations, arbitrary expressions or models.
Accepted intent is not sent anywhere. No external packages are required.

## Device experiment record (unexecuted plan)

For each exact platform and release, retain:

1. Device identity, entitlement, software version, tool versions, UTC timestamps,
   approved source revision and management recovery path.
2. Advertised modules/revisions, features and deviations; requested datastore,
   paths, operations, encodings, privileges and exact capability identifiers.
3. Baseline configuration/operational state and independent service probes.
4. Requests and matched replies, with secrets redacted; lock ownership and
   existing candidate state; validation/error handling; confirmed-commit deadline.
5. Read-back and service checks before confirmation, then persistence and
   restoration results. Configuration rollback cannot undo lost traffic.
6. Invalid types, unsupported paths, denied writes, a concurrent edit and lost
   replies on both sides of commit. Record unknown outcomes explicitly and
   reconcile them before another write.
7. For telemetry: initial sync, updates-only behaviour, timestamps, deletions,
   gaps, backpressure, reconnect and cache resynchronisation.

Use `not tested`, `documented`, `parser accepted`, `runtime observed` or
`service verified` for each result, with evidence references. Do not fill this
record with presumed support based on a vendor name or a capabilities response.

Primary references: RFCs 6241, 7950, 8040, 8072, 8200, 8639, 8640 and 8641,
and the OpenConfig gNMI specification linked in Chapter 70.
