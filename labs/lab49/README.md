# Lab 49 — the arithmetic chapter 49 promised and did not do

Four calculators. No radio, satellite, dish, fibre, site survey or measurement of
any kind: this is geometry, probability and the speed of light over stated
inputs.

| | What it computes | What it can show you were wrong about |
|---|---|---|
| 49.1 `latency_by_path.py` | Propagation by medium and orbit | That altitude sets latency, and that wireless never wins on it |
| 49.2 `availability.py` | Nines, and capacity against availability | That a link has two rates, and that five nines is "about five minutes" |
| 49.3 `shared_risk.py` | What two paths actually share | That a different medium is the strongest diversity there is |
| 49.4 `band_choice.py` | The link budget across bands | That a higher frequency means a weaker link, and that frequency is bandwidth |

```bash
python3 latency_by_path.py    # and --json
python3 availability.py       # and --json
python3 shared_risk.py        # and --json
python3 band_choice.py        # and --json

python3 test_latency_by_path.py   # 52 checks
python3 test_availability.py      # 53 checks
python3 test_shared_risk.py       # 62 checks
python3 test_band_choice.py       # 94 checks
```

261 checks in total.

## 49.1 — the satellite table contradicts itself

A request and its reply cross the gap **four** times: up to the satellite, down
to the gateway, up again, down again. Run the chapter's own altitudes through
that:

```
orbit altitude           claimed RTT      propagation alone  verdict
GEO   35,786-35,786 km   600-700 ms       477.5-477.5 ms     consistent
MEO   8,000-20,000 km    100-150 ms       106.7-266.9 ms     IMPOSSIBLE
LEO   550-1,200 km       25-70 ms         7.3-16.0 ms        consistent
```

At its own upper altitude the MEO row needs **266.9 ms** of pure propagation —
78% above its own upper figure, before geometry, gateways or queues. The
altitudes that would give 100–150 ms are about 7,495 to 11,242 km.

### "Altitude sets latency" describes GEO well and LEO badly

Straight up is the best case and almost never the real one:

```
  altitude       overhead         40 deg         25 deg         10 deg
     550 km         7.3 ms        10.8 ms        15.0 ms        24.2 ms
  35,786 km       477.5 ms       504.1 ms       521.3 ms       541.5 ms
```

At 550 km and 25° the propagation is 15.0 ms. Against a quoted service latency:

```
      quoted    propagation everything else        share
       25 ms        15.0 ms        10.0 ms          40%
       70 ms        15.0 ms        55.0 ms          79%
```

So **40 to 79 per cent of a quoted LEO figure is not the speed of light** — it is
the access scheduler, the gateway, the terrestrial leg beyond it, handover and
queuing. Compare GEO, where 477.5 ms of a quoted 650 is propagation and only 27
per cent is anything else. That is a latency altitude really does set.

### And the thing radio beats fibre at

```
medium                       per km
air (radio)                3.337 us
fibre                      4.897 us
```

**46.8 per cent slower in fibre**, before the route is counted — and a radio hop
is straight while a fibre route follows roads. Over 100 km at an ordinary 1.3
route factor the radio saves 0.606 ms on a round trip, about half of it. That is
why latency-sensitive traffic pays for microwave on routes where fibre is already
in the ground. What wireless does not win is capacity, and the chapter was right
about that — both are true at once.

## 49.2 — availability is a curve, and it is statistical

```
availability    unavailable       the same
99.9%            525.600 min     31536.0 s
99.99%            52.560 min      3153.6 s
99.999%            5.256 min       315.4 s
```

Five nines of a 365-day year is **5.256** minutes, not "about five". Four nines
is 52.56, which people call "about an hour". The arithmetic is trivial; not doing
it is the habit that lets a contract be written against a number nobody checked.

And the figure is a long-run **expectation**. It does not promise that any
particular year contains 5.256 minutes of outage — one storm can spend the budget
in an afternoon and the link still meets its design availability over its life.

### A link has as many rates as it has states, not two

```
state       capacity    margin   availability   unavailable   nines
1024QAM      2000 Mb/s    2.0 dB     99.788616%   1111.03 min    2.67
256QAM       1400 Mb/s    7.0 dB     99.927003%    383.67 min    3.14
64QAM        1000 Mb/s   12.0 dB     99.966143%    177.95 min    3.47
QPSK          350 Mb/s   26.0 dB     99.993441%     34.48 min    4.18
```

Six states, six capacities, six availabilities. Which one is "the guaranteed
rate" is a decision about the service, not a property of the link, and it is only
makeable once the curve exists.

```
target           best state    capacity   unavailable
99%              1024QAM        2000 Mb/s   1111.03 min
99.99%           QPSK            350 Mb/s     34.48 min
99.999%          NONE                -- no state meets it
```

Tightening from 99% to 99.99% costs 82 per cent of the headline. And the last row
is the answer a design must be able to give: on this path **no state** meets five
nines, and the fix is a bigger antenna, a lower frequency, a shorter hop or a
different medium — not a lower modulation, because the curve has run out.

**The fade model in this script is a placeholder fitted to nothing.** The
arithmetic above it is reusable; the fade model is not, and a real design replaces
it with a dated propagation method and the path's own rain statistics.

## 49.3 — what a different medium does and does not remove

The chapter closed on: a wireless backup *"cannot be cut by the digger that cuts
the fibre… so it provides diversity that a second fibre struggles to match."* The
first clause is true and the conclusion does not follow.

```
  two fibre routes                         6 shared
      building entry, change or human error, management system,
      provider control plane, regional weather, site power
  fibre + microwave on the same roof       6 shared
      building entry, change or human error, management system,
      provider control plane, regional weather, site power
  fibre + microwave done properly          1 shared
      regional weather
```

The roof-mounted microwave removes the digger and keeps **six** shared
dependencies — the same six as the two fibre routes. On that description the
medium bought nothing. The well-sited one shares **one**, and it is the weather,
which no medium removes.

```
pair                                     both out  if indep. understated
two fibre routes                         27.5597%   13.6962%        2.0x
fibre + microwave on the same roof       27.2262%   12.8735%        2.1x
fibre + microwave done properly          15.4956%   12.8735%        1.2x
```

The middle column is what "we have two paths" assumes. The left is what the
shared dependencies give. A pair with nothing shared comes out exactly equal to
the independent product, so the model is not adding pessimism — it is counting.

**And the improvement is real.** Every pair beats the single path, including the
lazy one. Redundancy with shared dependencies is still redundancy: it protects
the classes it does not share, and those are most of them by count. What it is
not is protection against the classes it *does* share — and a plan that says "we
have a diverse backup" without naming which classes has not said what it protects
against. Both statements are true at once; the chapter made only the flattering
one.

## 49.4 — the frequency explanation is backwards

The chapter explained E-band with one sentence: *"the very high frequency
provides the huge bandwidth for the capacity, and that same high frequency is
severely attenuated by rain and has short range."* Half of that is right.

**Frequency is not bandwidth.** Capacity comes from the width of the channel you
are allowed to occupy. A 2 GHz channel carries the same bits at 8 GHz as at
80 GHz. Multi-gigabit links live in the millimetre bands because that is where
regulators allocate channels that wide — an allocation fact, not a physical one.

**And a higher frequency makes a dish-to-dish link stronger.** Free-space path
loss rises as the square of frequency, which is where "higher frequency, shorter
range" comes from — but that figure is for isotropic radiators, and no microwave
link has one. A dish of fixed size gains as the square of frequency too, at
*both* ends:

```
band         free-space    gain each       budget    beamwidth
    7.5 GHz      116.0 dB       24.9 dB      -66.3 dB      9.33 deg
   15.0 GHz      122.0 dB       30.9 dB      -60.2 dB      4.66 deg
   38.0 GHz      130.1 dB       38.9 dB      -52.2 dB      1.84 deg
   80.0 GHz      136.5 dB       45.4 dB      -45.7 dB      0.87 deg
```

Path loss rises 20.6 dB from 7.5 to 80 GHz. The two dishes gain 20.6 dB **each**
— 41.1 dB between them. Net: the budget **improves by 20.6 dB**. Doubling the
frequency with the same hardware is 6 dB better, not worse.

The mirror of it: matching an 80 GHz budget down at 15 GHz needs 2.31 times the
diameter — exactly √(80/15) — and 5.3 times the area. Which is the real reason
small high-band dishes fit on street furniture.

### What actually shortens the hop

Rain attenuation is **per kilometre**, so it grows with the path while the
antenna advantage does not:

```
80 GHz rain (dB/km)    80 GHz's budget drops below 15 GHz's at
               5.0      4.16 km
              20.0      0.79 km
              30.0      0.52 km
```

**This script refuses to model that input.** The specific attenuation figures in
it are an illustrative ramp, not ITU-R P.838, and the sweep exists to show how
far one unmodelled number moves the answer. Get real ones from a dated method
with your own rain statistics.

And the beam narrows in exact proportion to frequency: the same 0.3 m dish has a
9.33° beam at 7.5 GHz and a 0.87° beam at 80 GHz. A mast that moves half of that
in a gale has spent 3 dB the link budget never recorded — a structural, survey
and maintenance cost that arrives with the frequency, not with the weather.

Sections A and C of this script are the Friis equation and aperture geometry:
no fitted model, no vendor figure. The test file re-derives the budget a second
time from aperture areas and checks the module's gain-based version against it.

## What none of this establishes

- **No equipment, no survey, no records, no measurement.** Indices, route
  factors, elevation angles, modulation states, fade figures, dependencies and
  failure rates are all stated inputs.
- **Propagation is a lower bound** and usually not the largest term in a service
  latency. Scheduling, framing, handover, processing and queuing are absent.
- **49.2's fade model and 49.4's rain ramp are placeholders.** Rain is also not
  the only fade mechanism — multipath, ducting, diffraction and obstruction are
  absent, and so is atmospheric gas absorption, which is not even a smooth trend
  (the oxygen line near 60 GHz is a large local peak).
- **49.4 compares received power, not capacity.** The high band is also the one
  with the wide channel, so a band that loses on budget may still be the only one
  that carries the bits.
- **49.3 computes outage probabilities, not unavailabilities.** Duration is
  absent, and its failure classes are treated as independent of each other when
  a storm plainly causes several at once.
- **A dependency list is a claim about records**, and records are often wrong.
  The only real test of a diverse path is failing the primary and watching.
