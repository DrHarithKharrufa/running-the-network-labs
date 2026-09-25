# Lab 48 — the three numbers a mobile transport design actually needs

Three calculators. No radio, radio unit, distributed unit, switch or measurement
of any kind: nothing here was measured, and apart from the eCPRI delay classes
and frame loss ratios, every figure is a stated input and none is any vendor's.

| | What it computes | What it can show you were wrong about |
|---|---|---|
| 48.1 `fronthaul_budget.py` | Delay class → reach, hop by hop | That a 100 µs class leaves "a few kilometres" |
| 48.2 `fronthaul_rate.py` | Fronthaul capacity from the radio configuration | That "huge bandwidth" is a specification |
| 48.3 `segment_contract.py` | A path against a stated contract, clause by clause | That the segment's *name* tells you its requirements |

```bash
python3 fronthaul_budget.py     # and --json
python3 fronthaul_rate.py       # and --json
python3 segment_contract.py     # and --json

python3 test_fronthaul_budget.py  # 52 checks
python3 test_fronthaul_rate.py    # 49 checks
python3 test_segment_contract.py  # 65 checks
```

## 48.1 — the boundary the chapter moved

The chapter said the 100 µs figure is the **total** budget, "most of which the
radio processing itself consumes, leaving the transport perhaps a few tens of
microseconds, i.e. a few kilometres of reach."

The eCPRI transport requirements define one-way maximum frame delay classes —
High25, High100, High200, High500 — and those are the allowance for the
**transport network**: the document says the requirement covers fibre
propagation and switching delay, and warns that a *larger* transport budget than
the class leaves a *smaller* budget for the radio equipment. The radio's
processing has its own separate allocation. Subtracting it from the class is
subtracting it twice.

```
reading                                             reach
chapter: 100 us less 70 us of radio                6.1 km
spec: High100 is the transport allowance          20.4 km
```

A factor of 3.3, pointing the wrong way: a team told the distributed unit must
sit within 6 km will build hub sites it did not need.

### Where the reach really goes

```
  hops      at 1 Gb/s     at 10 Gb/s     at 25 Gb/s  at 100 Gb/s
     0        20.4 km        20.4 km        20.4 km      20.4 km
     2        14.7 km        19.1 km        19.4 km      19.6 km
     8        -2.5 km        15.2 km        16.4 km      17.0 km
```

A 1500-byte frame takes 12.00 µs to clock out at 1 Gb/s and 0.48 µs at 25 Gb/s,
and a store-and-forward hop cannot begin sending until it has received the whole
frame. Eight 1 Gb/s hops spend 112 µs of a 100 µs class before a metre of fibre —
hence the negative reach, which the model reports rather than hiding.

**So the constraint on fronthaul reach is usually not the kilometres.** It is the
hop count and the line rate, both of which are yours to choose, and neither of
which appears in a sentence about distance.

### And what the specification does not give you

Frame loss ratio: 10⁻⁷ for High and Medium classes of service, 10⁻⁶ for Low.
Packet delay variation: **not specified** — the relevant sections are marked for
further study. So "near-zero jitter" and the old lab's 1 µs limit came from
nowhere. A delay variation figure comes from the radio vendor or from your own
engineering, with a measurement method attached.

## 48.2 — where the bandwidth comes from

"Huge" is not a number. The rate is arithmetic on five terms:

```
subcarriers x symbols per second x 2 (I and Q) x bits per sample x streams
```

```
100 MHz, 30 kHz subcarrier spacing, 4 streams, 16-bit samples:
    resource blocks                    273
    subcarriers (12 per block)         3276
    symbols per second                 28000
    resource elements per second       91.7 M
    payload                            11.74 Gb/s
    with 10% overhead                  12.92 Gb/s
```

```
configuration                                    rate    vs base
the configuration above                      12.92 Gb/s      1.00x
twice the streams                            25.83 Gb/s      2.00x
sixteen streams                              51.66 Gb/s      4.00x
sixty-four streams                          206.64 Gb/s     16.00x
9-bit compressed samples                      7.26 Gb/s      0.56x
```

**Streams are the term that runs away.** The same 100 MHz cell needs 12.9 Gb/s at
four and 206.6 Gb/s at sixty-four — one link against a bundle — and that is
decided by the radio architecture, not by anything a transport engineer controls.
Which is exactly why it has to be asked for. Compression is the one negotiable
lever: 16 bits to 9 is a 44% saving, at a cost in signal quality the radio team
owns.

Note that streams are **not** antenna elements. How many a given radio puts on
the wire is a property of its architecture and the split, and it is the first
question to ask.

## 48.3 — a contract instead of a table of adjectives

The old script checked a path against three hard-coded segments and then printed
a fixed paragraph. The contradiction was on the screen:

```
  [FAIL] midhaul:
           - sync 'frequency' weaker than required 'phase'
...
The shared backhaul-grade path carries backhaul and (barely) midhaul,
```

It printed FAIL for midhaul and then said the path carried midhaul. Underneath
that, three worse things: the jitter limits were invented; synchronisation was a
**rank** (`frequency=1, phase=2, phase-tight=3`) when frequency and phase are
different quantities; and the segment *name* was treated as a specification.

A contract states the split, the plane, both interface endpoints, the delay class
or figure, the frame loss ratio, packet delay variation, absolute *or* relative
time error, capacity, MTU and the failure state. Anything it does not state comes
back **unstated**, not passed:

```
  open fronthaul, user       FAILS: one-way delay, frame loss ratio, capacity
  DU to CU, user             meets what was stated (3 clauses unstated)
  CU to core, user           meets what was stated (3 clauses unstated)
```

Midhaul **passes** — the old lab's midhaul failure was its invented sync rank.

### Fronthaul can share

```
  open fronthaul, user       meets what was stated (2 clauses unstated)
  DU to CU, user             FAILS: MTU
  CU to core, user           FAILS: MTU
```

An engineered shared path that gives fronthaul its own class **meets a fronthaul
contract while carrying other traffic**, which the "dedicated versus ordinary
IP/MPLS" framing could not express. And the model found the real tension, which
is not latency: the path uses a 1500-byte MTU because small frames keep
serialisation down (48.1), while midhaul and backhaul need 9000 for tunnelled
traffic. Nobody asks that when the segments are three rows of adjectives.

### The state that matters most

```
contract                   working    after a failure
open fronthaul, user       meets      meets
DU to CU, user             meets      FAILS: one-way delay
CU to core, user           meets      meets
```

Met in the working state, missed on the protection path — 2400 µs against a
1000 µs requirement. A working-state check never sees it, and it is the state the
network is in on the day it matters. A path that supplies no failure figures
raises an error rather than passing.

## What none of this establishes

- **No equipment and no measurement.** Switch delays, frame sizes, line rates,
  sample widths, compression ratios, overheads and every contract figure are
  stated inputs.
- **The resource-block counts are plausible values**, not a reproduction of the
  specification's channel table.
- **Cut-through switching** changes the serialisation term materially and is not
  modelled. **Queuing** is not modelled at all — it is why fronthaul gets
  scheduling treatment, and it belongs in a measurement under load.
- **The contract clause list is not complete**: security, management-plane
  reachability, MTU across every encapsulation, and assurance over time are all
  missing.
- **Meeting a class or a contract on paper is not meeting it.** The radio
  equipment at the ends has its own budget, and the service works when the whole
  thing is measured end to end, under peak load, on both paths.
