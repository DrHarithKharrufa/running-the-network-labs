# Lab 63.1 / 63.2 / 63.3 — what a selector can see, what a capture path can hold, what a transport promises

Three labs for Chapter 62. All are arithmetic and seeded simulation: no
exporter, collector, ASIC, capture card, broker or pipeline is executed, and no
vendor's behaviour is claimed. Ring sizes, splitter losses, sustained write
rates and broker settings are **inputs** to look up or measure on your own
equipment; the defaults here are ordinary values chosen to make the arithmetic
concrete.

## 63.1 — `sampling_floor.py` (repaired twice)

```bash
python3 sampling_floor.py
python3 sampling_floor.py --demo-original
python3 sampling_floor.py --output result.json
python3 test_sampling.py              # 34 tests
```

**Its history is the lesson.** As first shipped it computed `packets // N` per
flow and printed *"INVISIBLE (below the floor)"* whenever that came to zero.
That is a counter reset at the start of every flow, and it manufactures a hard
floor by construction: a 50-packet flow at 1-in-4000 could never be seen, so the
chapter's claim about small flows was true of the model and of nothing else. An
earlier technical edit replaced it with the correct independent-selection
arithmetic — for p = 1/N and k packets, `P = 1 - (1 - 1/N)^k`, so at k = N the
answer is 63.2 % and there is no threshold — and that is kept here unchanged in
substance.

**What this pass added is the other half.** Real exporters do not all select
independently. A *systematic* sampler takes every Nth packet of the interleaved
stream, and for a periodic flow on a steady link that is not a probability at
all: 3 phases in 2,000 see the flow and see **every** burst, while 99.9 % of
phases never see it, however long you wait. The outcome depends on the residues
the flow occupies modulo N, not on the absolute scale — which the lab checks by
repeating the sweep at a realistic packet spacing rather than asserting it.

This is why RFC 3176 specifies a **randomised** skip, and says *"variation of
+-10% of the mean value is sufficient"*. The lab measures that claim: at ±10 %
jitter the same flow is observed in about 22 % of runs, back to roughly the
independent-selection answer, and ±50 % is no better — exactly as the
specification says.

It also computes what sampling actually saves. At 1-in-2000 the packet records
fall by the full factor of 2,000; with counter samples and template re-sends the
total export falls by about **1,357**.

## 63.2 — `capture_budget.py` (new)

```bash
python3 capture_budget.py
python3 test_capture_budget.py        # 28 tests
```

The whole chain, budgeted as one thing, with the first component to discard
named:

- **Mirror destination.** Both directions of one fully utilised 10 Gb/s link
  offer 20 Gb/s to a 10 Gb/s output — it fits only while the link stays under
  50 % utilised, which is to say until the incident it was built for.
- **Optical tap.** A 50/50 splitter costs about 3 dB each way before excess
  loss. Both paths are reported, because a 10 % tap can leave the production
  link comfortable and the **monitor** below its receiver sensitivity —
  installed, budgeted and delivering nothing.
- **Receive ring.** 4,096 descriptors taking both directions of 10 Gb/s at
  minimum frame size drain in **138 µs**. Any scheduling delay longer than that
  discards packets, behind a tap or not, visible only in the driver's counters.
- **Snapshot length.** The largest lever and a destructive one: on 800-byte
  average traffic, snapping to 128 bytes writes about a fifth of the bytes and
  removes the payload a protocol dispute would have needed.

Every bottleneck branch is proved reachable, and so is the clean case — a budget
that can only ever blame one component is not a budget.

## 63.3 — `log_delivery.py` (new)

```bash
python3 log_delivery.py
python3 test_log_delivery.py          # 30 tests
```

Seven hops from UDP syslog to a replicated log, each with what it guarantees
and, in its own sentence, **what it does not**. The two columns that get
conflated are *acknowledged* and *durable*, and the gap between them is where a
pipeline loses events while reporting success.

Then the arithmetic nobody computes:

- At 8,000 events/s a fifteen-minute sink outage is **7.2 million events** —
  2.88 GB at 400 bytes each. A 50,000-event queue holds 6.25 seconds.
- A backlog drains at the sink's **surplus**, not its total: 7.2 million events
  clearing at 2,000 events/s of spare capacity takes **an hour**, five times
  what dividing by the sink rate suggests. A sink no faster than the source
  never drains at all.
- `acks=1` loses an acknowledged write when the leader dies. `acks=all` with
  `min.insync.replicas=2` survives one broker — and stops surviving the moment
  unclean leader election is permitted.
- Four counts to compare during a deliberate outage — generated, received,
  persisted, searchable — because each gap has a different owner.

## Make it yours

- In `sampling_floor.py`, put in your own flow's burst size and spacing and your
  own sampling rate, and find out whether your platform's selector jitters.
- In `capture_budget.py`, replace the ring size, splitter loss and sustained
  write rate with figures measured on your own equipment.
- In `log_delivery.py`, put in your own event rate and the outage you intend to
  survive, then compare the answer with your relay's configured queue.

## What to take away

- Sampling gives a probability, unless your selector gives an outcome instead.
- Budget the capture chain end to end; naming the weakest link is the point.
- Acknowledged is not durable, and durable is not searchable.
