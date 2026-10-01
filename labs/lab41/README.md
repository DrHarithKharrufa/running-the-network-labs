# Lab 41 — three pieces of AI-fabric arithmetic that can come out wrong

Three calculators. None of them touches a GPU, a NIC, a switch or a fabric, and
none of them validates a configuration. What they do is take the chapter's three
load-bearing claims and put them somewhere they can be checked — and, more to
the point, somewhere they can **fail**.

| | What it computes | What it can show you were wrong about |
|---|---|---|
| 41.1 `allreduce.py` | Ring all-reduce cost, latency and bandwidth terms kept apart | That "a 25%-slow link is a 4× problem" is true only above a message size you have to name |
| 41.2 `ecn_pfc.py` | One egress queue with a real feedback delay | That an ECN threshold copied from another fabric is safe on yours |
| 41.3 `fabric_breakeven.py` | When a dearer fabric is the cheaper fabric | That a communication-to-compute ratio decides the purchase |

```bash
python3 allreduce.py          # and --json
python3 ecn_pfc.py
python3 fabric_breakeven.py
python3 test_allreduce.py         # 51 checks
python3 test_ecn_pfc.py           # 43 checks
python3 test_fabric_breakeven.py  # 56 checks
```

All three exit 0 when their checks pass. Python 3 only; nothing else is needed,
and nothing else is used.

## Why all three were rewritten

The previous versions of the first two labs had the same defect, and it is worth
naming because it is the commonest way a lab lies to you: **their conclusions
were built into their formulas**, so no input could have disagreed with them.

`allreduce.py` computed the step time as `data / min(link_bandwidths)` and then
announced that a link at a quarter of line rate made the collective "4× slower".
Dividing a constant by the minimum *is* that answer. There was nothing to
discover. It also had no per-step cost term at all, so it declared every message
size bandwidth-bound — including the sizes where the fabric spends nearly all its
time on per-step overhead and the link rate barely matters.

`ecn_pfc.py` marked the queue and cut the sender's rate in the **same time
step**. A control loop with zero feedback delay cannot overshoot, so PFC never
fired for any ECN threshold below 99.4% of the PAUSE line, and every
configuration came back "ECN carries it, PFC quiet". That is not a tuning
lesson; it is the model's arithmetic. It also contradicted the chapter it
illustrated, which says the parameters interact and the safe region is narrow.
In that model the safe region was everything.

The third lab is new, and replaces a rule of thumb in the chapter that was not
the break-even condition.

## 41.1 — the straggler rules, but only above a message size

Ring all-reduce over N ranks is `2(N-1)` steps, each shipping `S/N` bytes over
every link at once:

```
T  =  2(N-1)·α  +  (2(N-1)/N)·S/B
```

`α` is the per-step cost — link latency, library overhead, the synchronisation
at each step — paid `2(N-1)` times whatever the message size. `B` is the
**slowest** usable link rate in bytes/s in this equation. The code accepts
Gb/s and converts to bytes/s explicitly.

The two terms compete, and which one wins changes the answer to the question the
chapter cares about. Degrading one link from 400 to 100 Gb/s — a 4× bandwidth
cut — costs:

```
   gradient |   healthy |  degraded | slowdown | regime
   256 KiB  |  0.079 ms |  0.107 ms |   1.35x  | latency-bound
     4 MiB  |  0.217 ms |  0.657 ms |   3.03x  | bandwidth-bound
    64 MiB  |  2.419 ms |  9.465 ms |   3.91x  | bandwidth-bound
      4 GiB | 150.394 ms| 601.365 ms|   4.00x  | bandwidth-bound
```

The same slow link costs 4.00× at one size and 1.35× at another. **Quote a
slowdown without the message size and you have quoted nothing.** Set `α` to zero
and every row becomes 4.00× — which is the old script, now visible as the special
case it always was. `test_allreduce.py` asserts exactly that, so the tautology
cannot come back unnoticed.

The script also prints the crossover: with these parameters the two terms are
equal at a 1.9 MiB gradient, and `S = α·B·N` with B in bytes/s (or `α·b·N/8` with b in bits/s) says where it moves when your
fabric changes.

### The scale-up number that is not a network number

The same script prints two budgets for one GPU server, because the chapter's
sizing section warns that conflating them is the commonest mistake — and the
chapter itself used to make it:

```
  one GPU onto the back-end fabric :   50.0 GB/s  (400 Gb/s NIC, one direction)
  one GPU over the scale-up fabric :  450.0 GB/s  (900 GB/s bidirectional, halved)
```

With one 400 Gb/s NIC per rank and a pure inter-node ring, the one-direction
physical budget is 50 GB/s before overhead. A claim of 350 GB/s needs a different
boundary: scale-up, multiple NICs, aggregate traffic or normalised bandwidth.
NCCL bus bandwidth is an algorithm-dependent normalisation, not automatically
the measured throughput of an individual port. Check the topology and metric.

## 41.2 — the safe ECN threshold belongs to the fabric, not the vendor

One egress port, fluid, in dimensionless steps where one step drains one packet.
A 4:1 incast offers more than the port can drain. The switch marks on a RED ramp
(`kmin`, `kmax`, `pmax` — the three numbers a switch actually takes, not one
"threshold"). A mark becomes a rate cut at the sender only after `delay` steps,
and the receiver may only signal so often. PFC is separate and lower down:
assert above `xoff`, release below `xon`, and the upstream device needs
`pfc_delay` steps to react. Above `capacity` the switch drops.

**The delay is not a detail of the model. The delay is the problem.** Between the
switch marking a packet and the sender slowing down sit the rest of the path to
the receiver, the receiver noticing, the notification travelling back, and the
sender acting. The queue grows for all of it.

With the delay in place, the model can fail, and the boundary moves:

```
feedback delay | highest kmin that keeps PFC quiet
          0 st | 168.8  (instant feedback: the old model lived here)
          8 st | 155.4
         24 st | 109.0
         48 st |  37.0
```

Longer paths, slower notification, more hops — the usable region shrinks. A
threshold lifted from someone else's fabric is a guess about *their* delay.

### Headroom is a separate requirement, and it has its own arithmetic

When PAUSE is asserted the upstream device does not stop; it stops `pfc_delay`
steps later and keeps sending for all of them. The queue must have room above
`xoff` for what arrives in that window, net of what drains — here
`(4.0 − 1.0) × 16 = 48` packets. The model reaches exactly that overshoot and
starts dropping as soon as the buffer above `xoff` falls below it:

```
 capacity |  headroom | overshoot |   drops | lossless
      250 |        50 |      47.0 |     0.0 | yes
      240 |        40 |      43.0 |     7.0 | NO
```

PFC asserting is not the failure. Asserting without the buffer to cover its own
reaction time is the failure, and it presents as **loss on a fabric everyone
believes is lossless**.

### What this is not

It is **not DCQCN**. DCQCN is a specific algorithm with a smoothed α, byte and
timer counters, and fast-recovery, additive-increase and hyper-increase stages;
none of that is here. The decrease factor and increase step are **arbitrary
constants** chosen to make the feedback loop visible — not measured parameters,
not any vendor's defaults. No number this script prints should be typed into a
device. It cannot validate a configuration, and no configuration in this book
has been validated on one.

## 41.3 — when the dearer fabric is the cheaper fabric

The chapter used to settle this with a rule of thumb: a communication-to-compute
ratio above roughly 25% justified the premium. That is not the break-even
condition, and the arithmetic says so. Per GPU-hour, with `g` the GPU and its
machine, `f` each fabric, `c` the fraction of wall-clock spent waiting on the
cheaper fabric and `s` the fraction of that waiting the dearer one removes:

```
f_A − f_B  <  (g + f_A) · c · s
 premium        what the saved time is worth
```

The ratio `c` is one of two factors on the right. The other is `s`, and the money
turns on it just as hard:

```
                          scenario |  comm | saved | wall-clk | buy A?
           communication-heavy job |   45% |   40% |    18.0% | yes
    heavy job, fabric barely helps |   45% |    5% |     2.3% | no
    light job, fabric helps hugely |   10% |   90% |     9.0% | yes
```

Rows one and two have the **same** ratio and opposite answers. Rows two and three
have opposite ratios and — read against the rule of thumb — the wrong answers.
`test_fabric_breakeven.py` asserts these, so a ratio-only rule cannot quietly
return.

Every figure in the script is an **illustrative input, not a market price**. No
vendor quotation, price list or benchmark was available when this was written and
none is implied. Put your own quotations in and the condition still holds; the
verdict is yours.

## What none of this establishes

- **No fabric was built, configured or measured.** No switch, no NIC, no RoCE
  traffic, no GPU, no collective, no InfiniBand, no Ethernet.
- **No throughput, latency or packet rate was measured anywhere.** Every number
  above is arithmetic on stated inputs.
- **No vendor claim was verified**, because no vendor documentation, benchmark
  or price was available. Where the chapter now names a vendor mechanism it says
  what the mechanism is for, and tells you to check your own release notes.
- **The ECN and PFC numbers are dimensionless.** They are packets and steps in a
  fluid model, not bytes and microseconds on a device, and they do not convert.
- The Containerlab inventory at `../topologies/anvil.clab.yml` has no startup
  configuration and no lossless configuration of any kind. Deploying it gives you
  devices, not a fabric, and no run of it is recorded anywhere in this book.
