# Lab 43 — three numbers the physical layer will hold you to

Three calculators. None touches a fibre, a light source, a power meter or an
OTDR. What they do is take the three claims Chapter 43 rests on and put them
where a plausible design can be shown to **fail on paper**, which is the only
place a fibre decision is cheap to change.

| | What it computes | What it can show you were wrong about |
|---|---|---|
| 43.1 `loss_budget.py` | A span's loss on three different bases | That "typical" figures are what you design to |
| 43.2 `otdr_events.py` | The arithmetic behind a trace | That one trace identifies an event, or locates a dig site |
| 43.3 `route_procurement.py` | Cost per gigabit-year against demand | That building always gives the lowest long-run cost per bit |

```bash
python3 loss_budget.py            # and --json
python3 otdr_events.py
python3 route_procurement.py      # and --years

python3 test_loss_budget.py         # 38 checks
python3 test_otdr_events.py         # 55 checks
python3 test_route_procurement.py   # 41 checks
```

Python 3 only.

## 43.1 — typical, acceptance, design: three numbers, one of them yours

The previous version of this lab multiplied a span's length, splices and
connectors by the chapter's *typical* figures and printed a total. Typical
figures are the wrong ones for design and the wrong ones for acceptance:

- **Design** needs the worst case the span is *allowed* to be, because the link
  must work with every element at its specification limit, at end of life,
  after the repairs it has not had yet.
- **Acceptance** needs the contractual limit — what you test against and what
  lets you reject the build. "Typical" is not a threshold anyone owes you.
- **Diagnosis** needs what *this* span measured at commissioning, which is
  neither of the above.

The chapter's own worked span is the case in point:

```
                                 span |  typical | acceptance |   design |   budget | verdict
          the chapter's 60 km example |   12.60  |     18.60  |   20.52  |    16.0  | PASSES ON TYPICAL, FAILS ON DESIGN by 4.5 dB
```

On typical figures it fits a 16 dB budget with 3.4 dB spare. On the figures you
would actually design to it loses 20.52 dB and does not fit — a gap of **7.92
dB**, more than the entire connector allowance, and none of it exotic:

```
    fibre, 60 km at 0.25 dB/km                    15.00 dB
    4 fusion splices at 0.15 dB                    0.60 dB
    4 connector pairs at 0.75 dB                   3.00 dB
    3 repairs x 2 splices at 0.15 dB               0.90 dB
    3 repairs x 30 m of slack cable                0.02 dB
    ageing and drift allowance                     1.00 dB
```

Two things there that the old lab had no place for. **A repair adds two splices,
not one** — the cable is cut, so there are two joints — and a buried cable will
be repaired several times in twenty years. And the joints are at their
*specification* values, not a good crew's best day.

Note which fix works: taking out two patch panels is a real 1.5 dB saving and
still leaves the span 3 dB short. What fits it is optics with a larger budget,
which is a procurement decision made *before* the glass goes in the ground. The
last two shipped spans fit as designed — a design basis is not a way of failing
everything, it is a way of finding out on paper.

Every per-element figure is an **illustrative default**. Take `maximum` from the
datasheets of the cable and components you are buying and `typical` from your own
commissioning records; those are the only numbers that bind anybody.

## 43.2 — why one trace is not an identification, or a dig site

The chapter used to say you could tell splice from connector from bend from break
"at a glance" from one trace, and that this locates a fault "to within metres".
Four pieces of arithmetic say otherwise.

**A one-direction measurement can be negative across a real, lossy splice.**

```
     A->B |      B->A |      true |     error | what one trace would have told you
   -0.09  |     0.49  |     0.20  |     0.29  | a GAINER: one direction shows a step UP
```

A splice cannot amplify. The OTDR infers loss from backscattered light, so it
reports the event's loss *plus* half the difference in the two fibres'
backscatter coefficients — and that second term reverses sign when you measure
from the other end. Average both directions and it cancels exactly. Accept a
one-way figure and you have recorded a real splice as free, or, standing at the
other end, as twice its actual loss.

**Two events closer than the dead zone are one event.** A 100 ns pulse cannot
separate events 5 m apart. The pulse width is a setting you chose, so "there is
one event here" is a statement about your instrument as much as about the fibre.

**The trace measures fibre; the crew digs route.** At 43.210 km optical, past
three closures each holding 25 m of slack, with the fibre stranded 0.7% longer
than its cable, the route position is 42.835 km — **375 m** from where the
optical distance says. That is not "within metres" of anything.

**The distance comes from an index you typed in.** Assume 1.4682 where the fibre
is 1.4750 and every distance is 0.46% out — 200 m at 43 km.

And **bend or splice needs two wavelengths**: a splice reading 0.30/0.31 dB and a
macrobend reading 0.09/0.32 dB are the same event at 1550 nm. One is fine; the
other will get worse. The second wavelength is what separates them and it costs
one more sweep.

## 43.3 — build, IRU or buy, decided by demand

"Building gives the lowest long-run cost per bit" is true above a demand nobody
stated. The two kinds of option have different *shapes*: a route costs the same
whether you light one wavelength or fill it, so its cost per bit falls without
limit; bought capacity scales with demand, so its cost per bit is flat. They
cross.

```
      demand |      build and own |      IRU, 20 years |   dark fibre lease |  leased 400G waves
     100 Gb/s |              4800  |              2700  |              4260  |              2400*
     800 Gb/s |               600  |               338* |               532  |               600
    4800 Gb/s |               100  |                56* |                89  |               600

  build vs leased waves:       800 Gb/s  (17% of a 4800 Gb/s route)
  IRU vs leased waves:         450 Gb/s  (9% of a 4800 Gb/s route)
```

The leased line is a **sawtooth**, not a line — 401 Gb/s costs what 800 does —
so the crossovers are computed at full waves, the comparison that survives
however your demand falls.

Two results worth sitting with. At these figures **building never wins on cost**,
at any demand or any term; if you build, be clear it is not for the arithmetic
but for what the arithmetic cannot hold — no counterparty, no renewal negotiated
from a position of having nowhere else to go, no clause letting somebody move
your cable. And **an IRU is a right of use, not a purchase**: it has an O&M
charge, an end date, and terms about relocation and the grantor's insolvency,
all of which this model makes you state.

One thing no column can show: **leased capacity is not automatically diverse**.
Two circuits sold as diverse can share a duct. Ask for the physical route and
check it against your own rather than against the supplier's diagram.

## What none of this establishes

- **No fibre, no light, no instrument.** Nothing was measured, spliced, tested or
  installed. These are calculations on figures you supply.
- **No standard is quoted as a limit.** The per-element defaults are illustrative
  and are not any recommendation's or manufacturer's numbers; a recommendation's
  limit, a cable maker's specification and a good crew's result are three
  different figures, and using one where another belongs is this lab's subject.
- **No prices.** No quotation, price list or market rate was available.
- **No trace is read.** `otdr_events.py` processes no trace file and models no
  backscatter physics beyond the single coefficient difference that produces a
  gainer. It tells you what a number from a trace does and does not mean.
