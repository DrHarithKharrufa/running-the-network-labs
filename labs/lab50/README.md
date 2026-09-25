# Lab 50 — the threat model, scored so it can come out badly

Three calculators. No network, device, scanner, audit, log or incident record:
this is bookkeeping and exact combinatorics over stated inputs.

| | What it computes | What it can show you were wrong about |
|---|---|---|
| 50.1 `threat_model.py` | The one-hour method, with derived scoring | That a control field with words in it is a control |
| 50.2 `control_coverage.py` | What a control set actually covers | That image signing covers the supply chain |
| 50.3 `scoring_resolution.py` | How much of a ranking is real | That likelihood × impact produces a ranking |

```bash
python3 threat_model.py        # and --json
python3 control_coverage.py    # and --json
python3 scoring_resolution.py  # and --json

python3 test_threat_model.py       # 118 checks
python3 test_control_coverage.py   #  81 checks
python3 test_scoring_resolution.py # 186 checks
```

385 checks in total.

## Why the old lab was withdrawn

`threatmodel.py`, which this replaces, contained a defect a security tool must
never have. It credited a control to an entry point whose control field said, in
plain English, that there was no control:

```python
("IoT cameras on flat segment", "opportunist", "none (flat)", 2, 2),
...
has_control = control is not None
if has_control:          # a real control roughly halves residual risk
    r = r / 2.0
```

`"none (flat)"` is a string, so `control is not None` was `True`, and the flat
camera VLAN was scored **2.0 instead of 4.0**. It got worse. The gap list — which
that script's own closing line called *"the output that matters"* — was built as:

```python
gaps = [row for row in rows if row[3] is None]
```

so the same entry point was **left out of the gap list entirely**. An operator
running it over their own network would have been told their flat camera segment
was half-mitigated and not a gap. Neither was true, and the input said so in
words. The README shipped alongside it documented the flat halving as a feature.

In the rebuilt model that row scores **4.00** and appears at the top of the gaps.

## 50.1 — absence is a value, and a control is not a flat halving

Three changes, and the third is the one that matters.

**Absence is a value.** A control is `Control(...)` or the singleton `ABSENT`.
There is no way to spell "no control" that also reads as one: a `Control` whose
name starts with *none*, *no*, *n/a*, *nil*, *nothing*, *absent*, *not*,
*unprotected*, *flat*, *TBD*, *todo*, *unknown* or *assume* is **rejected at
construction**. `"we assume nobody knows"` — which the chapter explicitly says is
not a control — will not construct. A bare string is refused outright.

**A control states what it does and to whom.** The old model gave `"VPN only"` on
a contractor account with estate-wide access exactly the same 50 % credit as
`"MFA + filtering"`. Here each control names the classes it raises cost against
and by how much, and **earns nothing against a class it does not address**:

```
  Console ports in an unlocked comms room
    has 'BGP session authentication and prefix filters', which covers
    criminal, opportunist, state --- and this entry point faces the insider.
```

A coverage claim must be strictly between 0 and 1. `1.0` is rejected: no control
removes a risk, and a model that lets you say so is the model the chapter warns
about. Controls compose on what is *left*, so two claiming half each leave a
quarter and nothing ever reaches zero.

**And the ranking is reported with its ties showing.** Count them two ways:

```
    on likelihood x impact alone   6 of 8 rows tied, 5 distinct values
    on residual after controls     0 of 8 rows tied, 8 distinct values
```

The score the chapter teaches puts **six of eight rows in a tie**. What separates
them is not a finer scale — it is having said what each control does and to whom.

The closing section prices one more control against the register, and on this
data **two candidates tie exactly**, so it says so instead of picking one:

```
  NO SINGLE BEST. 2 candidates tie exactly at 14.00:
    MFA on all administrative access, closing 4
    BGP session authentication and prefix filters, closing 3
```

They tie on the arithmetic and are not interchangeable — different gaps,
different classes, different cost. The model handing the decision back is the
correct behaviour.

## 50.2 — "stopped by" is the wrong verb

The chapter's class table ends every row with what *stops* that class. Three
things are wrong with that, and they compound.

**Nothing stops a class.** A control does one of three quite different things —
**reduce frequency**, **limit reach**, **shorten dwell** — and they are not
interchangeable. The class table lists all three in one breath under "stopped",
so a set can be the wrong shape and nothing in the method notices:

```
  Shape of this set: 62% reduce frequency, 25% limit reach, 12% shorten dwell.
```

The chapter's own assume-breach section asks for the opposite emphasis. A set
weighted towards frequency is a set built for the world where prevention works.

**Coverage is per mechanism, not per threat.** "Supply chain" is at least six
distinct mechanisms, and image signing addresses **two**:

```
  covered    image-tampered-in-transit
  covered    image-unsigned-on-disk
  UNCOVERED  vendor-compromised-signs-malice
  UNCOVERED  signing-key-stolen
  UNCOVERED  hardware-implant-at-odm
  UNCOVERED  dependency-in-vendor-build
```

**In every uncovered case the signature verifies.** Signing answers *"is this the
image the vendor signed?"*; the supply-chain question is *"should I trust what
the vendor signed?"* An inventory that marks the plane green because signing is
in place has answered the first and reported the second.

**And a timebox is not assurance.** Take one mechanism off the inventory and
re-run: the state class goes from 4 open to 3. The risk did not change; the
report did. An hour spent well returns the mechanisms you thought of in that
hour. The timebox is good advice about **repetition** — a real defence against a
changing estate — and it is not evidence of completeness. What bounds that is a
list someone else wrote, checked against yours.

## 50.3 — how much of a risk ranking is real

Exact combinatorics. No sampling and no random number anywhere in the file: the
expectations are computed in closed form and by dynamic programming, and the test
file checks all of them against an independently written enumeration.

**A 3×3 scale has nine cells and six values.** A third of the distinctions you
made when scoring are thrown away by the multiplication itself, before any two
rows are compared. And the values are not evenly spaced:

```
    values  1, 2, 3, 4, 6, 9
    gaps      1,  1,  1,  2,  3
```

So "one rank worse" is 1 at the bottom and 3 at the top. A difference between two
risk scores is **not a magnitude** and cannot be summed, averaged or set against a
budget — which is most of what a register is used for once it leaves the team.

**The ordering has anomalies you would not sign if they were written down.**

```
    L1 x I3 = 3 ranks BELOW L2 x I2 = 4
    L1 x I3 = 3 ranks BELOW L3 x I2 = 6
```

Put the scale back in: impact 3 is *control of infrastructure others depend on*,
impact 2 is *a site or customer-facing service lost*, and the register funds the
second before the first. Multiplying two ordinals puts that policy in place
without anyone deciding it.

**A register of any size is mostly ties.**

```
spread                              items  distinct   largest     tied
uniform over cells                     20      5.70      6.37      96%
skewed towards high impact             20      5.53      6.69      96%
```

96 per cent of a 20-item register's rows are tied with something, and the
probability that the worst item is *uniquely* worst — that the top of your gap
list is one row rather than a tie you broke silently — is **24 per cent** evenly
spread and **10 per cent** skewed. Both spreads are run precisely so the
conclusion can be seen not to depend on the assumption.

**Widening the scale is a trade, not a fix.**

```
    scale    distinct   seen@20 tied@20  anomalies
    2x2             3       3.0    100%          0
    3x3             6       5.7     96%          3
    4x4             9       7.8     89%         14
    5x5            14      10.5     77%         44
```

Read the last column. A finer scale separates more rows **and misorders more
pairs**, and the anomalies grow faster than the resolution does.

**The tie-break is the policy.** Two defensible rules — product first, then
impact, or product first, then likelihood — disagree on **six of nine** positions.
One funds the rare catastrophe, the other the constant nuisance. If your register
does not state which it uses, it is still using one: whatever your sort left in
place, which is usually the order the rows were typed in. That a coarse scale
forces the policy into the open is the only good news in this lab.

## What none of this establishes

- **No network, device, scanner, audit or incident record.** Every entry point,
  class, plane, score, coverage claim, mechanism and failure assumption is a
  stated input, and the absolute numbers mean nothing outside these scripts.
- **None of the likelihood figures is a base rate.** Yours come from your own
  incident history and from published advisories for networks like yours, and
  writing them down is most of the work.
- **A coverage claim is a claim.** "Covered" here means a control is *named*
  against a mechanism — not that it is deployed everywhere, configured
  correctly, monitored, or tested. An untested control is a claim with nothing
  behind it.
- **Coverage is not risk**, and 50.3's combinatorics say nothing about whether a
  3×3 scale is the right choice. A coarse scale people fill in beats a fine one
  they do not. What it says is that the *ranking* read off a coarse scale is
  mostly not there.
- **50.2's mechanism list is deliberately incomplete**, which is the subject of
  its own Section D. Its gaps are the honest demonstration of its limit.
