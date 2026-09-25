# Lab 72.1: observable local loop controls

Python 3.11+; standard library only. Run in this directory:

```sh
python closed_loop.py
python -m unittest discover -v
python closed_loop.py --demo-original
```

The default demonstration verifies the actual in-memory state through a separate
observation method, restores a baseline after a bad-health result, records local
notifications and trips a breaker after two failed attempts. The original flawed
script is retained byte-for-byte only for comparison. Exit 0 for the demo means
the scenario ran, not that all simulated actions succeeded. Inspect its results.

## What is implemented and tested

- A single allowed target and desired operation; schema, fixture producer,
  event-age and resource-version checks.
- Event-ID deduplication and collision rejection within this process. The 1000
  accepted-event teaching limit stops further admission; it is not durable storage.
- Actual monotonic rolling-window expiry. Three **primary attempts** per 60 s
  are reserved before action. Each attempt can also make at most one restoration:
  the bound is six simulated writes, not three. Rate reservations include failed
  and uncertain attempts and are not erased by manual breaker reset.
- A shared in-process lock makes reservations atomic for threads sharing that
  object. The test runs 20 reservations concurrently; only three can succeed.
- A separate observation of value/version/health, actual state restoration and a
  version check that prevents restoration from overwriting a newer change.
- Breaker threshold, cooldown and explicit healthy/manual reset. Time passing
  alone does not restart the loop. Reset retains the rate budget.
- Kill before admission, kill after reservation but before write, and kill after
  mutation. The last case records a need for reconciliation, not an undone write.
- Injected apply-then-lost-reply and failed-observation cases. No automatic retry.
- A local memory notification adapter. Adapter failure halts future work.

Twenty-three tests exercise those behaviours, including expiry after admission
but before mutation. Times in boundary tests come from
an injected clock, so 60 simulated seconds need no 60-second sleep. The normal
window uses `time.monotonic`; event age uses a separate wall-clock source. The
fixture permits at most 30 s of age and 2 s of future skew; these are teaching
values, not universal policy.

## Limits that must stay visible

This is an in-memory, one-process teaching model. The state, deduplication records
and notifications do not survive restart. A producer-name allow-list does not
authenticate a sender. There is no message bus, durable outbox, real queue,
cryptographic producer verification, distributed lease, cross-process rate
budget, crash recovery, network device, forwarding or customer-service probe.
The observation method is independent of the actuator's returned success value,
but both use the same simulated device object; it is not an independent physical
measurement. The `healthy` flag is injected test state, not a real health probe.

Timeouts are injected exceptions here; Chapter 71 separately exercises real
local coroutine deadlines. Remote cancellation, long-running writes and device
rollback are not modelled. The before-write hook represents admitted work waiting
to act. The after-write hook shows why stopping a worker cannot undo an already
completed effect. No pages, emails or external messages are sent.

For production, design authenticated event ingestion, durable operation/outcome
storage, resource fencing, atomic shared budgets, bounded queues, retention and
replay policy, failure recovery and independent service observation. A kill
switch must stop new/queued work through each actuator path, reconcile in-flight
operations and preserve a separate recovery path. Measure those behaviours in
the intended deployment; do not promote this simulation into a controller.

The lesson is the observable contract and its limits. It is not proof that a
feedback loop is stable, safe or reversible merely because these tests pass.
