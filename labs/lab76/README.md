# Lab 76: authorisation before execution

Use Python 3.12 with `PyYAML==6.0.3` in an isolated environment:

```
python -m pip install -r requirements.txt
python agent/run_scenarios.py
```

The suite runs **64 local tests** of policy and SQLite reservation accounting.
It extends the handover's 40-test correction. No LLM, authenticated identity
service, device change, Batfish model, Containerlab topology, rollback, packet
forwarding or hardware is executed. The historical `scenarios.yaml` is labelled
as a superseded constructed fixture, not the current acceptance suite or a list
of documented incidents.

## Trust and policy contract

The test harness supplies world state, policy, approvals, an explicit database
file and a trusted `principal`. Omitting the principal denies authorisation;
there is no default trusted identity. The planner supplies a proposal and cannot
authoritatively choose those harness inputs. These fixture strings do not
authenticate a person: production must obtain the principal and observations
through independently authenticated, access-controlled services.

Policy revision 5 uses exact predicates in `agent/verifier.py`; YAML supplies
the version and freeze windows, not a generic interpreted policy language.
The proposal has exact named string parameters (maximum 256 characters each),
a bounded request ID, matching known ticket, evidence IDs, derived target,
requester, world revision and policy revision. Untrusted provenance claims are
excluded from approval authority. All required checks must pass; the reported
reason is the first failure, not a claim that other checks passed.

The caller's tool/device scope is checked independently of the proposed target.
The approver must be recognised by the trusted fixture. Approval binds the
requester, canonical operation parameters, ticket, evidence IDs, target, request
ID, state revision and policy revision through a digest. A digest binds content;
it does not authenticate its origin. Approval records have issue/expiry times,
roles and revocation state. Revocation is checked again during reservation after
preflight; a real executor must check at execution too.

Shutdown requires an enabled, flapping customer-facing port and fresh collector
evidence for that exact device/interface. Non-integer, Boolean, nonfinite and
nonpositive flap counts cannot qualify. Soft clear is limited to the known
customer session in permitted regions and exact `in`/`out` direction. It has no
device implementation and does not establish route-refresh capability or low
operational impact.

RTBH permits canonical IPv4 /32 or IPv6 /128 only when the prefix lies within
both device authority and requester delegation, is in the trusted active-attack
fixture, and uses an authorised peer/AFI. The requested route expiry must be in
the next 900 seconds; it is bound into the approval. This is a narrow teaching
policy. No route is announced or withdrawn. Production additionally needs real
prefix authority, provider agreement, export filters, validation policy, expiry
enforcement, withdrawal/recovery and forwarding/service evidence.

## Reservation is not execution

`verify` is preflight only. `authorise_and_record` uses `BEGIN IMMEDIATE` to check
and reserve request ID, single-use approval and hourly allowance in one SQLite
transaction. A successful result says **reserved**, not applied or executed.
Denials consume no reservation. Successful reservations count even if no device
operation follows. Limits are global per tool in the shared file: two shutdowns,
six soft clears and four blackholes in `(now - 3600 seconds, now]`.

An explicit persistent database file is required; omitted, empty or in-memory
databases are rejected. Tests create a temporary file, reopen it to verify
persisted state, and remove it only after the exercise. Twelve actual thread
workers with separate SQLite connections race for six soft-clear reservations:
six reserve and six receive rate denials. This tests local concurrent connections,
not independent hosts, filesystem failure, power loss or high availability.
SQLite storage/locking errors fail closed; no device action is attempted.

The default clock is read anew at each decision. Tests inject a fixed or callable
timezone-aware clock. Snapshot/evidence/approval times are checked; a clock value
earlier than a stored reservation is denied, including after reopening the file.
The suite tests exact hourly-window expiry. Forward time jumps, cross-host clock
uncertainty and distributed leases are not solved. Monitor clock quality and
define conservative operational behaviour separately.

A file transaction cannot atomically commit a remote device change. Real execution
needs bound operation IDs, platform-supported preconditions or fencing where
available, durable state transitions, uncertain-write reconciliation, service
checks and a tested recovery path. The SQLite file and all trusted fixture stores
must be protected from the planner. Approval/rate limits are policy choices, not
proof of low impact; one permitted target may serve many customers.

## What remains an integration exercise

Labs 71 and 72 provide stateful local examples of partial writes, lost replies and
reconciliation. Their tests and this policy suite do not constitute one integrated
executor. Before any real deployment, test the actual gateway/identity/executor
path, apply-then-timeout, response loss, concurrent configuration changes,
revocation before execution, observer loss, rollback failure and restart. Record
software/platform versions, expected states, independent observations and residual
risks. No live-NOS execution for those cases is claimed here.

References:
- SQLite transaction semantics: https://www.sqlite.org/lang_transaction.html
- RFC 2918, BGP route refresh: https://www.rfc-editor.org/rfc/rfc2918.html
- RFC 7999, BLACKHOLE community: https://www.rfc-editor.org/rfc/rfc7999.html
- NIST AI 600-1, US cross-sectoral guidance (not UK law):
  https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
