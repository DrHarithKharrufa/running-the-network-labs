# Lab 55.1 — Candidate micro-segmentation policy, and the two ways a generator misleads you

```bash
python3 microseg_policy.py
python3 microseg_policy.py --demo-window
python3 test_microseg_policy.py
```

Micro-segmentation fails on policy **authorship**, not enforcement (§55.4). So
you label workloads, discover flows, and generate. This lab does that — and
produces **candidates for a human to approve**, never policy. It will not call
its output policy, because the gap between "these rules were generated" and
"this policy was approved" is where both of the failures below live.

## The two failures, which point in opposite directions

A generator sits between what you **intended** and what you **observed**, and it
can go wrong in each direction.

**Observed but not intended.** Something is talking that policy does not
sanction. The shipped version of this lab caught this and was right to — it
surfaced a web server reaching a database directly. What it could not say is
whether that is a forgotten dependency or an attacker moving laterally, and
neither can this one. It is a *question*, never an answer, and above all not a
reason to write a rule. **Observed traffic is evidence to review; it is not
permission.** A generator that adds a rule because it saw the traffic will
faithfully legitimise an intrusion.

**Intended but not observed.** Something is authorised and simply did not happen
while you were watching. The shipped lab generated the *intersection* of intent
and observation, so an authorised relationship that was quiet during the window
produced **no rule at all and was never mentioned**. This is the more dangerous
of the two, because it is silent and it is on the path to production: the
quarterly billing run, the disaster-recovery replication, the annual audit
extract, the month-end backup. Each is authorised, each is invisible in a
fortnight's capture, and each breaks the first time it runs after enforcement is
switched on — which is exactly when somebody needs it.

So the rebuilt lab reports **four** sets, not one:

| set | meaning |
|---|---|
| `CANDIDATE` | intent that *was* observed — the safe core |
| `UNOBSERVED` | authorised, never seen: **keep** unless a human retires it |
| `UNSANCTIONED` | seen, not authorised: adjudicate, never auto-permit |
| `UNLABELLED` | endpoints no rule can be written about at all |

## The window decides what appears to exist

`--demo-window` runs the same estate and the same intent through four
observation windows:

```
  days     candidates   unobserved   saw the month-end job?
  1        3            1            NO
  7        3            1            NO
  30       4            0            yes
  60       4            0            yes
```

Note which way the trap runs. The **shorter** window produces the **smaller**
policy — three rules instead of four — and a smaller policy looks tidier,
tighter, more like good least-privilege work. It is an outage waiting for the
end of the month. A generator that reports only what it saw is reporting a
property of your capture, not a property of your network.

And rarity is not the only way a flow goes unseen: a sampling gap, a sensor
outage, or a path that never crosses the collection point all produce the same
silence.

## What this model does not do

It knows nothing about your enforcement platform — whether these rules can be
expressed there, in what order they are evaluated, what the default is, or
whether a bypass exists. It has labels but no addresses, and a port number but
no protocol. Test enforcement separately, on the real platform.

It also refuses inputs it cannot reason about: an empty label map, empty intent,
an intent entry with no stated business reason (because nobody can review or
retire a rule whose purpose was never written down), a malformed flow, or a
window that is not two ISO dates.

## What to take away

- Generate **candidates**, approve **policy**. Approval is a human act with an
  owner and a date.
- Every authorised relationship must end up in exactly one visible bucket. The
  one thing a generator must never do is drop an authorised relationship in
  silence.
- Observation is evidence, not authority — in both directions.
- An endpoint nobody labelled is usually an endpoint nobody owns, which is its
  own finding.
