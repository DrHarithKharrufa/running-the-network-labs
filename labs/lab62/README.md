# Lab 62.1 / 62.2 / 62.3 — what a label costs, what a rule does, what a sample can see

Three labs for Chapter 62. All are offline calculation in closed form: no store
is run, no device is sampled, no alerting system is started, and no figure here
is a benchmark of any product.

Two of them — `cardinality_check.py` and `alert_storm.py` — carry a
`--demo-original` mode, and it is worth running every time. It prints the
**naive version of the same analysis**: one that builds in the conclusion it
appears to demonstrate. Both are plausible, both are the kind of thing that
reaches a capacity review, and seeing the two outputs together is the point of
the lab. Treat a calculation that agrees with you as the one most in need of
checking — including these.

## 62.1 — `cardinality_check.py`

What a label actually costs, counted rather than multiplied.

```bash
python3 cardinality_check.py
python3 cardinality_check.py --demo-original
python3 test_cardinality_check.py      # 61 checks
```

The product of label value counts is an **upper bound**, reached only if every
combination is emitted. A subscriber is attached to one interface on one device,
so `subscriber_id` rides on the interface rather than multiplying it: 400,000
series, not 9,600,000,000 — a factor of 24,000, and comfortably inside the very
budget this script itself used to declare it over.

What does grow is **churn**: a subscriber who left in March keeps a series until
their last sample falls out of retention. And the storage bill is driven by
**sample interval**, not by the label count — three retention tiers come to
644 GiB where the same series at one-second resolution for two years come to
54,041 GiB.

The lab also separates three things that all get called high cardinality and
need different answers: *bounded* (a queue number), *entity* (a subscriber —
countable, usually affordable, and a lookup dimension rather than an aggregation
one), and *open* (a source IP — the only case where "unbounded" is literally
true, because you do not choose the values).

## 62.2 — `alert_storm.py`

A rule evaluator, rather than a list of pre-labelled events.

```bash
python3 alert_storm.py
python3 alert_storm.py --demo-original
python3 test_alert_storm.py            # 61 checks
```

Rules are **evaluated** against a timeline of samples, with a for-duration that
delays and resets, and with an expression that can return "cannot evaluate" as
distinct from False. Three results:

- The chapter's own alert, `probe_loss_ratio > 0.02`, **never fires when the
  prober dies**, because a comparison against a missing metric is False. The
  companion rule that fires on absence is what turns the measurement stopping
  into a page.
- One upstream link failure fires nine rules, five of them page-severity;
  grouping and inhibition reduce that to **one page** without deleting a single
  cause rule.
- On a night where probe loss never leaves 0.1 per cent, **four things still need
  paging**: lost redundancy, a generator with 45 minutes of fuel, a confirmed
  intrusion, and the collector ceasing to ingest. A policy of "page only for
  user-affecting problems" delivers nothing on that night.

And one that will surprise you: a **silenced alert is usually still firing**, so
it goes on inhibiting, and silencing one symptom during a change can take its
whole group off the air. The lab models both semantics; find out which one your
stack implements.

## 62.3 — `sampling_limits.py` (new)

What a sample rate can and cannot see.

```bash
python3 sampling_limits.py
python3 test_sampling_limits.py        # 69 checks
```

A 200-microsecond queue excursion once a second is caught by an instantaneous
one-second sample **0.02 per cent of the time**, and sampling a hundred times
faster still catches under 3 per cent — because the per-sample probability is the
duty cycle and never changes. The counter does not rescue you either: a 10 Gb/s
port at line rate for 5 ms of every second reads **0.5 per cent utilisation**, an
understatement of 200×, and shortening the interval does not help because both
are means.

The instruments that do see it are different instruments — a hardware high-water
mark, an on-device histogram, a threshold event — and each gives something up.
The lab also computes 32-bit counter wrap (**3.44 s** at 10 Gb/s, so every normal
poll interval is longer than the wrap), export aliasing (a device refreshing
every 10 s and exporting every 1 s gives you 90 per cent duplicates and nothing
in the stream says so), and what a synthetic probe is a sample *of*.

## Make it yours

- In `cardinality_check.py`, describe your own label relationships with `attach()`
  and put your own measured bytes-per-series and bytes-per-sample into `budget()`.
  Both defaults are order-of-magnitude inputs, not measurements.
- In `alert_storm.py`, write your own rules as expressions over a sample dict and
  run your own incident timeline through them. Check what your stack does with a
  silenced inhibitor.
- In `sampling_limits.py`, put in your own burst durations, link rates and probe
  parameters, and look up what your platform's queue-depth register actually
  means before believing any of it.

## What to take away

- The product is an upper bound. Count the tuples you actually emit, and budget
  from measured series and a measured sample rate.
- A comparison is not a health check. Say what your rule does when the metric is
  absent, or it will resolve the question in the direction of silence.
- Page on a symptom the customer feels **or** on a risk a human must act on
  before it becomes one.
- No instantaneous sample rate observes a microburst reliably. Use the register
  that was built for it, and know what it gives up.
