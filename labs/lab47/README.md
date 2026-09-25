# Lab 47.1 — the time-error budget, and the two things it used to leave out

One calculator. No clock, no grandmaster, no boundary clock, no GNSS receiver
and no test set: nothing here was measured, and no figure below is any vendor's
specified performance or any standard's allocation.

```bash
python3 time_error_budget.py      # and --json
python3 test_time_error_budget.py # 72 checks
```

## Why it was rewritten

The previous script summed a list of per-device figures, added a flat 1000 ns
"GNSS holdover penalty", compared the total with 1500 ns, and finished with a
fixed paragraph:

> Add one more boundary clock, or a worse holdover oscillator, and it would fail
> **ONLY during holdover**

Its own numbers say otherwise. The chain totalled 330 ns normally and 1330 ns in
holdover; one more 50 ns boundary clock gives **1380 ns**, which is 120 ns
*inside* the limit:

```
chain                                   total      limit   verdict
old model, 4 boundary clocks           1330 ns     1500 ns    passes
old model, 5 boundary clocks           1380 ns     1500 ns    passes
old model, 6 boundary clocks           1430 ns     1500 ns    passes
old model, 8 boundary clocks           1530 ns     1500 ns     fails
```

It takes **four** more boundary clocks, not one. The sentence was printed
unconditionally and the program never evaluated it.

Two things were missing underneath that slip, and they matter more than it does.

## 1. The budget is not the whole limit

"Within 1.5 microseconds" is meaningless until you say 1.5 microseconds of what,
measured where. Absolute time error at the air interface and relative alignment
between two radios are different requirements. And the radio and your own
measurement have shares of the limit before the network gets any:

```
requirement                        phase alignment to the radio
reference point                    air interface
stated limit                       1500 ns
endpoint allocation                 350 ns
measurement uncertainty              50 ns
LEFT FOR THE NETWORK               1100 ns
```

A budget that skips this step gives itself **36% more room than it is entitled
to** — which is exactly the size of error that makes a chain pass on paper and
fail on site.

## 2. Not all time error adds the same way

**Constant** time error is systematic — each device's own offset, and any
uncompensated path asymmetry. It is the same sign every time, so it accumulates
hop by hop, and because it is constant it *can* be measured and calibrated out.
**Dynamic** time error is the varying part, from packet delay variation and
servo behaviour. It does not simply add across independent elements and it
cannot be calibrated away.

```
combination                  constant    dynamic      total   verdict
dynamic combined by sum         150 ns      100 ns      250 ns     meets
dynamic combined by rss         150 ns       44 ns      194 ns     meets
```

Neither combination rule is "the answer" — the applicable standard says how to
combine, and a budget has to declare which rule it used. What is not defensible
is summing constant and dynamic error together as one quantity, which is what
the old lab did.

The consequence shows up when the chain gets longer: constant error grows
**linearly** with hops while dynamic error grows as the **square root**. So a
long chain is a constant-error problem, and the fix is calibration and fewer
hops — not a better oscillator.

## Asymmetry: the error that halves itself and never averages out

PTP estimates the offset from four timestamps. Writing the one-way delays as
`d_ms` and `d_sm` and the true offset as `o`:

```
t2 - t1 = d_ms + o                    t4 - t3 = d_sm - o

mean path delay  = ((t2-t1) + (t4-t3)) / 2 = (d_ms + d_sm) / 2
estimated offset = ((t2-t1) - (t4-t3)) / 2 = o + (d_ms - d_sm) / 2
```

The estimate is wrong by **exactly half the asymmetry**, every time. It is not
noise, so no amount of filtering or averaging removes it:

```
uncompensated asymmetry per link                   bias     total
0 ns difference between the two directions          0 ns     194 ns  meets
100 ns difference between the two directions       50 ns     394 ns  meets
200 ns difference between the two directions      100 ns     594 ns  meets
500 ns difference between the two directions      250 ns    1194 ns  FAILS
```

Four links at 500 ns each put 1000 ns of constant bias into the chain and the
budget fails on that alone. Asymmetry comes from ordinary things: fibre pairs of
unequal length in the same cable, an amplifier or regenerator in one direction
only, different transmit and receive paths through a device, a protection switch
that moved one direction and not the other. It is constant, so it *can* be
compensated — and it is invisible until somebody measures it.

## Holdover is a curve, so the answer is a duration

"The grandmaster holds over" is not a state with an error. It is an error that
**grows** from the moment the reference is lost: a frequency offset of *f* parts
per billion accumulates *f* nanoseconds of phase every second, and the offset
itself drifts with ageing and temperature, which integrates to a quadratic term.

With 906 ns of the budget left for holdover:

```
oscillator                        at 1 h      at 8 h     at 24 h  time to limit
disciplined TCXO                 19500 ns    240000 ns  1296000 ns       3.0 min
ordinary OCXO                     1875 ns     19200 ns    86400 ns      29.6 min
temperature-controlled OCXO        188 ns      1920 ns     8640 ns         4.3 h
rubidium                            19 ns       192 ns      864 ns        24.8 h
```

A factor of nearly 500 between the cheapest and the dearest clock in the table.
**Holding this budget for a day takes a rubidium**, and no amount of care about
the chain changes that — it is a property of the oscillator alone. "A holdover
penalty of 1000 ns" describes none of these, because the question was never how
much error holdover adds. It is how long you have.

Those figures are *residual* — what is left at the moment the reference is lost,
after the servo has spent hours learning this oscillator's offset. They are not
free-run specifications, which are far larger and are the wrong number to use
here.

### And what holdover is not

Holdover begins when the clock **rejects** a reference and coasts, which means it
has correctly noticed something is wrong. A clock that keeps *following* a
reference that has gone bad — a spoofed signal, a receiver reporting lock on a
bad solution — never enters holdover at all, and none of this arithmetic applies
to it. That failure is neither slow nor bounded.

## What this does not establish

- **No equipment and no measurement.** Every figure is an input, and none is any
  vendor's specified performance or any standard's allocation.
- **The holdover model is three terms.** A real oscillator's holdover depends on
  temperature, on how long it was locked beforehand, on ageing and on the servo's
  behaviour, and is specified as a bound over a stated period and condition — not
  as a formula.
- **The combination rules are a choice made visible**, not the applicable
  standard's method.
- **Nothing here is a conformance assessment.** A budget that closes on paper is
  a prediction. The requirement is met when it is *measured* at the stated
  reference point, in the deployed chain, under load.
