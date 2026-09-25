# Lab 57.1–57.3 — what the numbers support, and what they do not

```bash
python3 ddos_triage.py              # which resource is under pressure
python3 ddos_triage.py --prove      # every hypothesis is reachable
python3 detection_budget.py         # where the seconds go, and what sampling costs
python3 anycast_catchment.py        # catchment skew and the withdrawal cascade
python3 test_ddos_triage.py         # 87 checks
python3 test_detection_budget.py    # 44 checks
python3 test_anycast_catchment.py   # 43 checks
```

All three are **offline calculation**. Nothing here measures a network, and the
chapter is careful to say so: no DDoS traffic was generated, no mitigation was
executed, and no vendor platform was contacted.

## 57.1 — the classifier that was confident about four numbers

The version that shipped took bits per second, packets per second, CPU and a
pipe size, walked three hard-coded thresholds, and returned **one** class with
**one** place to mitigate. Four things were wrong with it:

| the defect | why it matters |
|---|---|
| confident from sparse input | four numbers, no baseline, no units — and an operator acts on the answer at three in the morning |
| its own arithmetic was wrong | its README said 80 % utilisation meant the flood was "bigger than your pipe". **80 % of a pipe is smaller than the pipe** |
| thresholds that do not generalise | 5 and 10 Mpps are a rounding error on one platform and fatal on another |
| mutually exclusive classes | real attacks exhaust more than one resource at once, which is exactly when picking one class sends you to the wrong mitigation |

The rebuilt model reports **hypotheses**, each tied to a named resource and a
**stated baseline**, and it refuses a rate that arrives without one — because
"40 Mpps" is not a fact about an attack until you say what the platform is rated
for. It permits several resources to be under pressure at once and says so. It
never names an attacker, a class or a mitigation, because the same measurements
are produced by faults and by legitimate load: a serving tier at 100 % CPU is
equally consistent with an application flood, a bad deploy and a slow dependency.

The amplification helper is now honest about its own nature. A ratio is
arithmetic over two byte counts. `amplified_bps()` returns a **ceiling** and
flags itself `is_a_measurement: False`, because reaching that ceiling needs
reachable reflectors, path capacity in both directions and no rate limiting
anywhere — it is the size of the prize, not the size of the flood.

## 57.2 — why a 35-second attack is over before you see it

The chapter's detection table used to say sampling "adds a little delay". That
gets the mechanism backwards, and the correction is arithmetic:

```
  pipeline                                        total  against a 35 s burst
  ordinary flow telemetry, human in the loop       360s  TOO LATE by 325 s
  tuned flow telemetry, pre-authorised action       40s  TOO LATE by 5 s
  in-path inspection, automatic                      5s  IN TIME, 30 s to spare
```

A 60-second active-flow export timeout is an ordinary default, and **it alone is
longer than the attack**: the flood is finished before its first flow record
leaves the router. That is not a tuning problem.

Sampling costs something different — statistical confidence, in proportion to
how small the thing is:

```
  what you are looking for                   expected    P(>=5)
  a volumetric flood (1:4096, 10s)            2.2e+07    1.0000
  a 500 req/s application flood (1:4096, 10s)    1.22    0.0083
  the same, 1:1000 over 5 minutes                 150    1.0000
```

The same sampling rate that sees a volumetric flood instantly is **effectively
blind** to a low-rate application flood in a short window. Widening the window
recovers it, at the cost of the latency in the first table. That is the real
trade, and the budget function refuses to run with a stage omitted, because a
budget with a hidden zero in it is how "we detect in five seconds" gets into a
design document.

## 57.3 — anycast does not divide an attack equally

The chapter's figure drew a botnet split one third, one third, one third, and
concluded that no single site sees the whole flood and that damage stays
regional. A catchment is whatever BGP policy makes it — AS path length, local
preference at every network in between, and the attacker's own distribution.
Nothing about it is equal, and nothing about it is geography.

Three sites of 400 Gb/s each, 1,200 Gb/s in total:

```
  catchment                          survives up to      which is
  equal thirds, as the old figure drew it   1200 Gb/s   100% of the estate
  measured skew 62 / 27 / 11                 645 Gb/s    54% of the estate
  a botnet inside one catchment              800 Gb/s    67% of the estate
```

Then the part the old text had exactly backwards. A **900 Gb/s** attack — three
hundred gigabits *smaller* than the estate — destroys it completely:

```
  round 1: site-A 140%, site-B 61%, site-C 25%   -> withdraws: site-A
  round 2: site-B 160%, site-C 65%               -> withdraws: site-B
  round 3: site-C 225%                           -> withdraws: site-C
```

Site C was at **25 %** in round one — comfortable, nothing to report on a
dashboard — and it died anyway, killed by the withdrawal of the sites that were
failing rather than by the attack it was itself receiving. "Damage stays
regional" is true only until the first site leaves.

The model states its assumptions rather than hiding them: a withdrawn site's
share moves to the survivors in proportion to their existing shares, and when
every surviving share is zero the equal split it falls back on is **recorded as
an assumption** in the result.

## What to take away

- A rate without a baseline is a guess with a number on it. Refuse it.
- More than one resource can be exhausted at once, and that is precisely when a
  single-class answer sends you to the wrong mitigation.
- Sampling decides what is *visible*; timers decide what is *timely*. Confusing
  them produces a monitoring design that cannot see the attacks it was bought for.
- Anycast capacity is not the sum of the sites. It is the sum of the sites that
  are still announcing, and the first withdrawal changes that number.
