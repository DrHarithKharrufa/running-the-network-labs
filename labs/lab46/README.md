# Lab 46 — the three questions a converged design has to answer

Three calculators. No router, no transponder, no pluggable, no line system, no
ROADM and no control plane: nothing here was measured, and every duration,
loss, noise figure and required OSNR below is an input somebody typed.

| | What it computes | What it can show you were wrong about |
|---|---|---|
| 46.1 `recovery_policy.py` | Detection, recovery, reversion at both layers | That two layers reacting to one cut must cause a flap |
| 46.2 `path_budget.py` | OSNR on the working **and** protection paths | That a short metro ring means OSNR is plentiful |
| 46.3 `ols_contract.py` | An open line system's compatibility clauses | That "accepts any compliant wavelength" says anything |

```bash
python3 recovery_policy.py     # and --json
python3 path_budget.py         # and --json
python3 ols_contract.py        # and --json

python3 test_recovery_policy.py   # 66 checks
python3 test_path_budget.py       # 71 checks
python3 test_ols_contract.py      # 56 checks
```

## Why 46.1 was rewritten

The previous script did not simulate anything. Its entire result was one branch:

```python
if ip_holdoff_ms < optical_restore_ms:
    events.append((..., "links flap as optical restores under IP -- CHURN"))
    churn = True
```

The flap was appended because the timers compared that way, not because
anything flapped. The conclusion *was* the code, so a reader could not have
discovered it was false.

### Protection and restoration are not one mechanism

It also gave the optical layer 50 ms to "restore the wavelength (ROADM
reroute)" and the packet layer 200 ms, and concluded that IP should wait. Those
are the timings of two different things:

```
mechanism              kind         recovers   can fail to find a path
optical-protection     protection   50 ms      no
optical-restoration    restoration  30.0 s     yes
packet-frr             protection   50 ms      no
packet-igp             restoration  200 ms     yes
```

**Protection** is pre-computed: the second path is already lit and already
carrying the signal, so the switch is tens of milliseconds and cannot fail to
find a path. **Restoration** is computed at the time: choose a path, assign
spectrum on every link, re-level the amplifiers for the new channel loading,
re-lock the modem. That is seconds to minutes, and it can fail — there may be
no contiguous spectrum on the alternate route (Lab 45.2), or the route may be
long enough that the mode stops closing (Lab 46.2).

Each layer has one of each. So "optical is fast" and "packet is fast" are both
true and both useless until you say which mechanism.

### One cut, five policies

```
policy                                                  outage  restored  down again?
packet only, no optical recovery                        211 ms  packet    no
the chapter's advice: optical restores, IP holds off    30.0 s  optical   no
both act, uncoordinated                                 211 ms  packet    no
optical 1+1 protection, short IP hold-off                60 ms  optical   no
same cut, transport HOLDS the client up, no BFD          3.2 s  packet    no
```

Row 3 is the case the old lab called CHURN. It is 211 ms and clean. **Nothing
flaps in any of the five**, because churn is the service going down *after* it
came back, counted off the transition list, and one cut with a successful
recovery does not produce one however many layers act.

Row 2 is the chapter's advice, and it is 142 times slower than doing nothing at
all. The hold-off did not coordinate anything; it chose the longer outage. And
when the restoration it was waiting for fails, the bill is worse:

```
case                                                    outage  restored by
IP holds off 35 s, optical restoration fails            35.4 s  packet
IP does not hold off, optical restoration fails         211 ms  packet
IP holds off, and has no alternate path either           never  --
```

35 seconds spent waiting for something that was never going to succeed, while
the packet layer had a path throughout and had been told not to use it.

### The hold-off nobody configured

Row 5 is the mechanism the old lab had no notion of. A router does not see a
fibre cut; it sees what the transport equipment does to its client port. If
transport **squelches**, the router gets a hardware link-down event and that
pre-empts its timers altogether. If transport **holds the client laser on** —
which is what equipment does when it means to recover the line itself — the
port says nothing and the router waits for its own liveness check. Fault
propagation from the transport layer is worth more than fast timers on the
router, and a transport setting made for the optical layer's convenience takes
it away.

### And where churn does come from

```
one cut, optical 1+1 protection, repaired at 4 h, 5 min wait-to-restore
  churn with no cause supplied                 0
  churn with two causes supplied               2

    t=4.08 h  reversion is not hitless: the switch back drops traffic for 40 ms
    t=4.10 h  the repaired splice was not tested before traffic returned
```

Both are real; neither is "two layers reacted to one cut". The fixes are a
non-revertive policy or a hitless switch, and proving a repair before traffic
goes back on it. Neither is a hold-off timer.

## 46.2 — the budget the Kestrel design never had

The chapter chose the modulation like this: *"16QAM because the ring is short
and OSNR is plentiful."* It then promised optical restoration, which moves the
service onto the **other** path. On a ring that is the long way round: more
spans, and an express ROADM pass at every site in between.

```
PoP-A to PoP-B, the two ways round:
  clockwise       1 span,  0 express ROADM passes,  18.0 km
  anticlockwise   3 spans, 2 express ROADM passes,  78.0 km
```

Five amplified sections against one.

```
service     working   protect   penalty  mode from working    mode that survives
A-B         44.5 dB   29.0 dB   15.6 dB  16QAM, 118 Gbaud     16QAM, 118 Gbaud
A-C         32.4 dB   32.1 dB    0.3 dB  16QAM, 118 Gbaud     16QAM, 118 Gbaud
A-D         41.7 dB   29.1 dB   12.6 dB  16QAM, 118 Gbaud     16QAM, 118 Gbaud
B-C         43.7 dB   29.0 dB   14.7 dB  16QAM, 118 Gbaud     16QAM, 118 Gbaud
B-D         32.3 dB   32.2 dB    0.1 dB  16QAM, 118 Gbaud     16QAM, 118 Gbaud
C-D         43.0 dB   29.0 dB   14.0 dB  16QAM, 118 Gbaud     16QAM, 118 Gbaud
```

**The design survives, and it is worth being exact about what that means.** It
is true that 16QAM closes both ways round this ring. It was not true *because*
the ring is short: the worst protection path delivers 29.0 dB against a 20.0 dB
requirement, and that 9 dB of headroom comes from there being four sites on the
ring, not 96 km of it. Nobody computed either number. The design asserted a
conclusion that happened to hold, which is not the same as holding.

Note also which services lose most. The **adjacent** pairs — one span working,
the whole rest of the ring on protection — lose 12 to 16 dB. The opposite
corners lose 0.1 dB. A design reviewed on its longest service looks at exactly
the pair with the least to lose.

### What it takes to stop being true

```
 sites    circum.    spans   working   protect  from working       survives
     4       96 km        5   43.2 dB   29.0 dB  16QAM, 118 Gbaud   16QAM, 118 Gbaud
     8       96 km       13   45.9 dB   23.0 dB  16QAM, 118 Gbaud   16QAM, 118 Gbaud
    12       96 km       21   46.7 dB   19.3 dB  16QAM, 118 Gbaud   16QAM, 60 Gbaud
    16       96 km       29   47.2 dB   16.2 dB  16QAM, 118 Gbaud   QPSK, 60 Gbaud
```

At 96 km the ring breaks at **ten sites**; at 400 km it breaks at **four**. And
notice the working column *improving* as sites are added — the spans get
shorter — while the protection column collapses. That is precisely why a
working-path budget hides the problem instead of finding it.

Kilometres move the answer slowly; **sites move it fast**, because each one is
an amplified section on every path that passes through it. Adding an
aggregation site to a working ring is the change most likely to invalidate a
restoration promise, and the least likely to be reviewed as though it might.

### Two more things the promise depends on

```
(i)  diversity.  Spans A-B and D-A are drawn as two sides of the ring,
     but the records say both are in duct-north:
       shared ducts on the A-B service: duct-north
       diverse: NO

(ii) capacity.  Every service that used the cut span now rides the others:
       slots available per span          : 384
       busiest span, normal working      :  36
       busiest span, after a cut on A-B  :  48
```

Fitting in slots is still not fitting: the free slots must be **contiguous** and
the same ones on **every link** of the path, which is Lab 45.2.

## 46.3 — what "open" has to consist of

The chapter said an open line system "accepts any compliant wavelength source"
and left *compliant* undefined. That is the whole difficulty in one adjective.
A line system has a band, a grid, an input power window, a channel count it was
engineered for, and things it must be **told** before it can manage amplifiers
that everybody's channels share. Open is not the absence of those constraints.
It is the constraints being **published**, so a third party can engineer against
them instead of asking one vendor's permission. A closed system has the same
constraints and does not tell you them.

```
  the line system vendor's own transponder         accepted
  a third party transponder, same mode             accepted
  a pluggable in a router, nobody told the NMS     REFUSED: visibility to the line system
  a pluggable running hot                          REFUSED: power spectral density
  a wide channel centred off the 6.25 GHz grid     REFUSED: centre on grid
  a third party transponder, different mode        accepted
  an L-band source on a C-band line                REFUSED: band
```

Four refusals on four different clauses, and only one of them is the band —
which is the one an engineer would have guessed. The hot pluggable is inside
its own specification and outside the line system's input window, so it is a
perfectly good transponder that will degrade every other channel through the
amplifier it shares. The unreported pluggable is worse: it is optically fine,
and the line system is equalising for a channel it has not been told exists.

Note that the envelope is written in **power spectral density**, not launch
power. The same −3 dBm is −24.4 dBm/GHz over 137.5 GHz, −20.0 over 50 GHz and
−26.0 over 200 GHz — one of those passes and two do not.

### The clause the line system cannot settle

```
  the line system vendor's own transponder
    <-> a third party transponder, same mode           interoperate
  the line system vendor's own transponder
    <-> a third party transponder, different mode      DO NOT
      different modes: '118Gbd-16QAM-oFEC-15%' against '118Gbd-8QAM-cFEC-25%'
```

Both were accepted by the line system. Acceptance is a statement about the
**line**. Whether the two ends carry traffic to each other is an agreement
between two **modems** about a mode, and the line system is not a party to it.
You can buy the line from one supplier and the transponders from another; you
cannot buy the two *ends* of a wavelength from two different suppliers and
assume they meet.

### And acceptance is still not a service

```
  metro open line system                   accepted
  the same line, on a longer path          REFUSED: OSNR on the path
  a line system that publishes no OSNR     accepted (1 clause unevaluated)
```

Same source, same envelope, a path delivering 8.5 dB less. Compatibility did
not change; the service did. And a clause the envelope does not publish comes
back **unevaluated**, not passed — which is the honest answer and the common
one. That is what integration responsibility means in practice: hold the
envelope, hold the declaration, compute the path, prove the pair, and own the
answer when the three disagree.

## What none of this establishes

- **No equipment and no measurement of any kind.** Every duration, loss, noise
  figure, power and required OSNR is an input chosen to be plausible.
- **No product, vendor or standard is characterised.** The modes are
  illustrative; a real mode's required OSNR comes from its vendor, and a
  pluggable's reach is not a property of its name.
- **Restoration times are not a constant.** The 30 s in 46.1 stands for
  "seconds to minutes"; a loaded line system with many channels to re-level can
  be well outside it.
- **46.2 has one channel and no nonlinearity** (Lab 44.2), no Raman tilt, no
  gain ripple, no polarisation-dependent loss, no dispersion and no ageing. Its
  capacity check counts slots without checking they are contiguous or common to
  every link.
- **46.3's clause list is not complete** — a real envelope also covers transient
  control on channel add and drop, ripple and tilt, reflectance, and the
  management interface in detail — and passing every clause is not a
  qualification. A qualification is the pair proved on the actual path, in both
  directions, under the loading it will really see.
- **Nothing here approves a design or a policy.** Each script shows which
  questions have to be answered before anyone can.
