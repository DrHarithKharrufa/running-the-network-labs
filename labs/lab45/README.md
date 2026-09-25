# Lab 45 — what decides the mode, and where the channel can go

Two calculators. No transponder, amplifier, ROADM, WSS, line system or planning
tool: nothing here was measured, and no mode or figure below is any vendor's.

| | What it computes | What it can show you were wrong about |
|---|---|---|
| 45.1 `reach_capacity.py` | Path → OSNR → feasible modes → client rate | That distance decides the modulation, and that "add amplification" helps |
| 45.2 `spectrum_plan.py` | Flexgrid allocation and fragmentation | That a CDC ROADM lets you put any wavelength anywhere |

```bash
python3 reach_capacity.py       # and --json
python3 spectrum_plan.py

python3 test_reach_capacity.py   # 48 checks
python3 test_spectrum_plan.py    # 50 checks
```

## Why 45.1 was rewritten

The previous version took an OSNR as an input, labelled each case with a
distance — "metro DCI (40 km)", "long-haul (2000 km)" — and picked the
highest-order modulation that fitted. Nothing in it related kilometres to OSNR,
so the distances were decoration attached to numbers somebody had typed in.

Its advice when nothing fitted was to "shorten the span **or add
amplification**", which contradicts the preceding chapter in the one line a
reader in trouble would look at. And it reported baud × bits × 2 as capacity,
which is the **line** rate including FEC overhead, not the payload you can sell.

### A mode is four numbers, not one word

```
                  mode |    baud |  b/sym | needs OSNR | line rate |    client
        QPSK, 60 Gbaud |    60 G |     2  |     11.5 dB |     240 G |     200 G
       QPSK, 118 Gbaud |   118 G |     2  |     14.5 dB |     472 G |     393 G
      16QAM, 118 Gbaud |   118 G |     4  |     20.0 dB |     944 G |     787 G
```

Two modes both called QPSK need different OSNR, because the baud differs. Baud,
modulation, FEC and its overhead, and often constellation shaping all go into a
mode, so "choose the modulation" is not a thing you do.

### A ROADM node is an amplified section, not a penalty

The node's insertion loss has to be recovered by an amplifier that adds its own
noise, and the channel is narrowed on the way through. So:

```
                                  path | distance |  ROADMs |     OSNR | best mode that fits
     metro ring, 40 km, 2 ROADM passes |     40 km |       2 |   29.4 dB | 16QAM, 118 Gbaud, 787 G
     metro ring, 40 km, 8 ROADM passes |     40 km |       8 |   21.1 dB | 8QAM,  118 Gbaud, 590 G
   regional, 6 x 80 km, 2 ROADM passes |    480 km |       2 |   22.4 dB | 16QAM, 118 Gbaud, 787 G
 long-haul, 25 x 80 km, 4 ROADM passes |   2000 km |       4 |   15.9 dB | QPSK,   60 Gbaud, 200 G
```

Same forty kilometres, same fibre, same launch power, **8.3 dB apart** — entirely
from the nodes. And the 480 km regional path has *more* OSNR than the 40 km metro
ring and carries more, because it passes through two nodes instead of eight.
**Distance is not the variable. The number of amplified sections is, and a node
is one.** So "metro is short, therefore OSNR is plentiful, therefore 16QAM" is
not a rule.

### The two meanings of "add amplification"

```
                                      change |     OSNR |   delta
                             nothing changed |   15.9 dB |   +0.0
                more gain at the same points |   15.9 dB |   +0.0
            an extra hut, halving every span |   20.6 dB |   +4.7
    a quieter amplifier, 4.5 dB noise figure |   16.9 dB |   +1.0
                        one fewer ROADM pass |   16.4 dB |   +0.5
```

More gain at the same points buys **nothing** — the noise is in the signal
already and gain amplifies that too. An extra hut that **halves** every span buys
4.7 dB, because each amplifier now recovers half the loss. That distinction is
the whole of it: amplification helps when it reduces the loss any one amplifier
must make up, and not otherwise.

## 45.2 — flexgrid as it is actually defined

The flexible grid has **two** granularities and they are different numbers:

- **6.25 GHz** — the nominal central frequency granularity, the `n` index
- **12.5 GHz** — the slot width granularity, the `m` count

A channel is `(n, m)`: centre = 193.1 THz + n × 6.25 GHz, slot width = m × 12.5
GHz. Quoting only the 12.5 leaves out the step that lets a wide channel sit
*between* the positions the old fixed grid allowed — which is most of the point
of having a flexible grid.

Slot widths also round **up**, and the rounding is spectrum you have bought and
cannot use: 62.5 GHz takes five slots exactly; 63 GHz takes six and wastes 12.

### And the constraint CDC does not remove

```
                                                                   |       free |  largest run |   frag
                                                        empty band |  4800.0 GHz |    4800.0 GHz |     0%
 85 services placed, alternating 37.5 and 75 GHz, band nearly full |    37.5 GHz |      37.5 GHz |     0%
 every 37.5 GHz service is decommissioned over the following years |  1650.0 GHz |      75.0 GHz |    95%
                      an 800G channel asks for 100.0 GHz (8 slots) |  1650.0 GHz |      75.0 GHz |    95%
                                                                     -> NO ROOM --- the free spectrum is not contiguous
          after defragmenting --- which means moving live services |  1650.0 GHz |      75.0 GHz |    95%
                                                                     -> placed at slot 252
```

**1650 GHz free and nowhere to put a 100 GHz channel**, because the largest
contiguous run is 75 GHz. The spectrum was there; it was in the wrong shape. And
nothing contrived produced it — channels of different widths arrived and left
over years, which is how the holes appear.

Colourless, directionless and contentionless removes the constraint that a given
add/drop port is wired to a given wavelength and a given direction. It does not
create contiguous spectrum; it does not create free spectrum on the **other
links** of the path, which must all have the same slots free since nothing
converts the wavelength in between; and it does not supply the OSNR. "Any
wavelength to any router in any direction by software" is a statement about
patching.

The defragmentation row is the honest ending: the spectrum can be made to fit,
and doing it means moving services that are carrying traffic. That is a
maintenance window, not a software action.

## What none of this establishes

- **No optical equipment and no measurement.** Every figure is an input.
- **No mode is any vendor's.** A real mode's required OSNR depends on its FEC,
  its shaping and the transponder's own implementation, and comes from its
  vendor's datasheet and the line system's planning tool.
- **No product reaches are claimed.** The reach of a pluggable is not a property
  of its name; it depends on the line system, the span losses, the node count
  and the vendor's implementation.
- **45.2 has no OSNR at all**, no filtering penalty, no path computation across
  several links and no notion of which wavelengths a node can reach. It can tell
  you whether there is anywhere to put a channel, not whether it would work.
