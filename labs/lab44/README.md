# Lab 44 — two budgets, and a gauge that is not a countdown

Three calculators. No transponder, amplifier, fibre, power meter or spectrum
analyser: nothing here was measured, and no number any of them prints belongs in
a design without a real planning tool behind it.

| | What it computes | What it can show you were wrong about |
|---|---|---|
| 44.1 `link_budget.py` | The power budget at both extremes | That a positive margin means the link works |
| 44.2 `osnr_budget.py` | The OSNR chain, with nonlinearity | That more launch power is never harmful |
| 44.3 `fec_and_errors.py` | Coding gain and error statistics | That coding gain is decibels you can spend on loss |

```bash
python3 link_budget.py         # and --json
python3 osnr_budget.py
python3 fec_and_errors.py

python3 test_link_budget.py      # 44 checks
python3 test_osnr_budget.py      # 43 checks
python3 test_fec_and_errors.py   # 47 checks
```

## Why the lab was rebuilt

The previous version computed a received power, compared it with the receiver's
sensitivity, subtracted a ten-year reserve, and printed a verdict — from that one
subtraction alone. It printed the overload check on the line above and ignored it.
Given a +10 dBm transmitter into 5 dB of loss it reported, in the same run:

```
overload check: Rx +5.0 < overload -8.0?  NO -- receiver clipped!
verdict: OK -- still positive in year 10
```

A receiver driven thirteen decibels past its maximum input, declared good.

It also computed no OSNR at all, although the chapter said OSNR governs reach on
a coherent link and pointed at this lab as the place the reader would track it
down the chain.

## 44.1 — the power budget, at both extremes

"Aim for the middle of the window" is not a design method. Two cases have to
hold and neither is a midpoint: the **maximum** received power — a new
transmitter at the top of its tolerance into a short, low-loss path — must clear
overload, and the **minimum** — end of life, maximum losses, after the repairs to
come — must clear sensitivity.

```
                                      case |   Rx max |   Rx min |  margin | verdict
                  the chapter's 60 km span |   -10.6  |   -20.5  |   1.50  | power conditions met
     the same span, transmitter at +10 dBm |    -1.6  |   -11.5  |  10.50  | FAILS: too strong at best case
a short patch, nobody fitted an attenuator |     1.0  |    -3.0  |  19.00  | FAILS: too strong at best case
 ...the same patch with a 10 dB attenuator |    -9.0  |   -13.0  |   9.00  | power conditions met
                   a long span at the edge |   -23.0  |   -33.0  | -11.00  | FAILS: too weak at worst case
   a path that varies more than the window |     0.0  |   -20.0  |   2.00  | FAILS: ...; path varies more than the window
```

The second row is the old bug: 10.5 dB of margin over sensitivity and 6.4 dB
past overload. The last row fails a condition a midpoint cannot even express —
the path varies by 20 dB and the receiver accepts 14, so **no transmitter power
satisfies both ends**.

It also refuses to print the sentence the chapter used to: none of this says the
link *works*. It says the light lands inside the window the receiver accepts.

**The double-counting trap.** If your maximum path loss already used
specification limits and already included the repairs to come — which is what
Lab 43.1 computes — then adding an ageing and repair reserve here counts the same
decibels twice. Twice-counted margin is not caution; it buys equipment nobody
needed and can make a workable span look impossible. The script gives both
conventions and tells you to hold to one.

## 44.2 — the OSNR chain, and why more power stops helping

Per-span OSNR is `launch − span loss − noise figure − (−58)` in the usual
reference bandwidth. Noise powers add, so the *reciprocals* of OSNR add: four
identical spans cost 10·log10(4) = 6.02 dB, not a quarter of the OSNR.

Then the part the chapter left out. ASE noise falls as launch power rises;
nonlinear noise rises as its **cube**. So the effective SNR has a maximum:

```
    launch |  OSNR(ASE) |    SNR(NL) |    effective | penalty
   -6.0 dBm |    15.47   |    26.97   |      15.17   |   0.30 dB
   -3.0 dBm |    18.47   |    20.97   |      16.53   |   1.94 dB
    0.0 dBm |    21.47   |    14.97   |      14.09   |   7.38 dB
    3.0 dBm |    24.47   |     8.97   |       8.85   |  15.62 dB
   12.0 dBm |    33.47   |    -9.03   |      -9.03   |  42.50 dB
```

The ASE column improves for ever. The effective column peaks at −3.17 dBm and
falls away. So "the link fails no matter how much power you pump" **understates
it**: past the optimum more power makes the link worse, and a system running hot
gets better when you turn it down. The penalty at the peak is 1.76 dB — the
classical figure, and a useful check on any answer of this kind.

The reach follows. This system crosses **5 spans**; counting ASE alone at the
same launch power says 8, and ASE-only reasoning would not stop there, because in
that arithmetic raising the power always helps — so it recommends the one
adjustment that makes the real link worse.

This is a **teaching model with one lumped nonlinear coefficient**: not a
Gaussian-noise model, not a planning tool, and not a measurement. It has no
filtering penalty from cascaded ROADMs, no polarisation-dependent loss, no
residual dispersion, no Raman tilt and no spectral hole burning — all of which
spend OSNR too.

## 44.3 — coding gain, and the gauge that is not a countdown

**Coding gain is an OSNR quantity.** It lowers what the *receiver* needs and
lowers no fibre attenuation, no splice and no connector:

```
                                   | power margin | OSNR margin
          before FEC is considered |     1.50 dB |     0.80 dB
       after applying the net gain |     1.50 dB |    10.83 dB
```

Apply it to the power side by mistake and the same link shows 10 dB of margin it
does not have. It is also not free: the overhead raises the symbol rate, a wider
signal collects more noise, and the requirement rises by 10·log10(1+overhead) —
which is why the honest figure is **net** coding gain and why a headline gain
quoted without its overhead is not a number you can use.

**And the countdown is in the margin, not the error rate.** Take a link running
2.76 dB above its FEC threshold. Losing that margin slowly gives seven readings
you could have acted on. Losing 3 dB at a stroke — a connector disturbed on a
patch, a bend, a protection switch — gives two:

```
      0.0 dB |    6.00   |     2.39e-03 |    2.76  | correcting
      3.0 dB |    3.00   |     2.29e-02 |   -0.24  | PAST THRESHOLD
```

No ramp, no weeks, no intermediate value anybody could have trended. The
"countdown" is a property of *slow* degradation, not of the error rate, and one
decibel is worth between a third and one and a half orders of magnitude of BER —
which is why an error rate looks flat and then looks like a cliff. **Trend the
margin in dB.**

**Post-FEC errors are not nothing.** A post-FEC error is corrupted data that
reached the customer. What is true is that a clean counter over a short window
proves little: at 400 Gb/s a five-minute poll has watched 4% of the traffic
needed to establish a 1e-15 rate. That is an argument for long windows and an
alarm on any non-zero count, not for ignoring the counter.

## What none of this establishes

- **No optical equipment of any kind** and no measurement. Every figure is an
  input.
- **The BER curve is textbook**, for one modulation format with no
  implementation penalty, used for its *shape*. A real transponder's curve is
  its own and comes from its vendor.
- **The nonlinear model is one coefficient.** Change it and every absolute
  number changes with it. What does not change is that the curve has a maximum.
- **No vendor's thresholds, gains, overheads or noise figures** were available;
  all are illustrative inputs.
