# Lab 64.1 / 64.2 / 64.3 — what a method buys, what a questionnaire is worth, and where a correct control plane still drops your packet

Three labs for Chapter 63. All are offline calculation and enumeration, with
one seeded simulation used only to cross-check a closed form. No device was
queried, no NOS was executed and no vendor's behaviour is claimed. The
pipeline in 64.3 is a teaching model of forwarding, not anyone's silicon; the
priors and likelihoods in 64.2 are stated in the file, illustrative rather
than surveyed, and swept so you can see which conclusions depend on them.

Two of the three carry a `--demo-original` mode. It is not a legacy switch: it
prints the **same question answered badly** — the confident, plausible version
of the analysis that most people would produce — so you can run the two side by
side and see where the reasoning parts company from the arithmetic. Read the
wrong one. It is the more instructive output.

## 64.1 — `bisect_vs_guess.py`

```bash
python3 bisect_vs_guess.py
python3 bisect_vs_guess.py --demo-original
python3 test_bisect.py                       # 49 tests
```

**What it got wrong.** It compared three strategies and gave them different
tests. Bisection was asked *"is the fault in this half?"* — a question about a
whole region — while the scan and the guesser were asked *"is the fault at
exactly this position?"*. Most of the gap it reported came from that
difference. It also reported guessing as non-convergent, which is false:
probing at random **with** replacement costs N trials in expectation and
succeeds almost surely, and probing **without** replacement — remembering your
misses — costs exactly (N+1)/2, the same as scanning in order.

**What it now shows.** At 1,024 positions: linear scan 512.5, remembered-miss
guessing 512.5, forgotten-miss guessing 1,024.0, a scan *given bisection's own
oracle* 512.5, and bisection 10.0. The fourth row is the point — the oracle
alone buys nothing. Bisection needs the region oracle **and** the halving.

It then computes what halving requires, and what happens when it does not get
it:

- **A reliable oracle.** At a 10 % per-probe error rate over ten halvings, a
  naive bisection lands on the right position about **35 %** of the time — and
  returns an answer that looks identical either way. Best-of-three probes
  improves it, at three times the probes.
- **A single fault.** With breaks at positions 100 and 700, bisection converges
  correctly on 100 and says nothing whatever about 700. Fix it, stop, and the
  symptom survives.
- **An ordered space and a testable midpoint.** Equal-cost paths, asymmetric
  return routing and a provider core you cannot log into each remove one.

And the probe that passed proves less than you think: with one broken member
of eight, a single test comes back healthy **87.5 %** of the time; **eighteen**
probes are needed for 90 % confidence, since seventeen still leave a 10.3 %
chance of having missed it.

The same question in the time domain closes the chapter's intermittent-fault
section. A fault that has stopped recurring is unobserved, not fixed: against a
link flapping twice a day, assume stationary Poisson events, perfect observation,
no such events after a successful repair, and a prior repair probability of 0.5.
Three quiet days then leave a posterior probability of about 1 in 404 that it is
still broken; 95% posterior confidence arrives after about 1.472 days. The chance
of that silence if it is still broken is a different quantity, exp(−6). Changing
the prior, workload or observation model changes these confidence values. For
something that happens twice a year the same confidence would need roughly **537
days** of silence, which is why rare faults are closed on evidence of the cause
rather than on evidence of the silence. The residual doubt is carried in
logarithms, because computed the obvious way it rounds to certainty after about
ninety days and the lab would print the opposite of what it had just said — a
defect its own tests caught.

## 64.2 — `four_questions.py`

```bash
python3 four_questions.py                    # the four demonstration cases
python3 four_questions.py --demo-original    # the withdrawn verdict version
python3 test_four_questions.py               # 51 tests

# your own incident, without editing anything:
python3 four_questions.py --case "pump room" --ever-worked yes \
        --scope "one site" --changes-per-day 40
python3 four_questions.py --help
```

The four printed cases are the `_case(...)` calls inside `report()`, near the end
of an 800-line file, which is why `--case` exists: a reader putting their own
incident through this should not have to read the program first. Any question you
leave out is answered `unknown`, and an unknown answer updates nothing.

**What it got wrong.** The four questions are the cheapest thing you can do and
asking them first is still right. The lab turned each answer into a verdict:
*never worked → configuration fault*, *one user → the edge*, *correlates with a
change → that change*. A circuit can be delivered dead and a new fibre patched
to the wrong port, so "it never worked" is not a configuration finding. An ACL
matching one address, one broken bundle member or an MTU mismatch on one path
all present as a single complaint, so "one user" is not an edge finding.

**What it now shows.** Ten candidate causes, ranked by weight, with the list of
what the answers did **not** rule out and the test that separates the leaders.
On the stated numbers, "never worked, one user" leaves configuration error
third at 18.7 %, behind the host and the access port and barely ahead of the
new media at 18.1 %; the sweep finds the claim only reverses if you believe
beforehand that configuration errors cause more than **55 %** of all faults.

It also prices the correlation everybody quotes. If changes arrive steadily and
the fault's start time is independent of them, an unrelated change lands inside
a symmetric ±15-minute window (30 minutes in total) anyway with probability 1 − e^(−rate × window):

| changes/day | coincidence | likelihood ratio | a 70 % prior becomes |
|---|---|---|---|
| 2 | 4.1 % | 24.50 | 98.3 % |
| 40 | 56.5 % | 1.77 | 80.5 % |
| 200 | 98.4 % | 1.02 | 70.3 % |

Past **33 changes a day** the correlation is worth less than a likelihood ratio
of 2. The estate that automates hardest is the one where "it started right
after the change" stops meaning anything — and the one most likely to say it
with confidence.

Two of the four worked cases end with the questionnaire's top hypothesis being
the **wrong** one, and the lab says so, because that is what a questionnaire
can do: rank, not diagnose.

## 64.3 — `control_vs_data_plane.py` (new)

```bash
python3 control_vs_data_plane.py
python3 control_vs_data_plane.py --demo-original
python3 test_control_vs_data_plane.py        # 46 tests
```

The chapter used to say the data plane *"only ever does what the control plane
told it to"*. That is a universal, so one counterexample settles it. The lab
simulates the stages a packet passes — route, next-hop resolution, forwarding
entry, rewrite, hardware table, egress treatment — of which a control-plane
read reaches the **first two**, and builds a device for each of the other four
on which every control-plane reading is clean and the packet is still dropped:

- the route is in the routing table and not in the forwarding table;
- the next hop is reachable and has no usable rewrite;
- the entry is programmed and the silicon is not carrying it;
- every path is up and one member of the bundle is dead;
- the route is perfect and a filter matches one source;
- the path is correct and the packet is too big for it.

On the stated weights a control-plane read reaches **46 %** of forwarding
failures. Conditional on it reading clean, the fault is at the egress 48 % of
the time and in the hardware 22 %. Even assuming four faults in five are simply
a missing route, coverage only reaches 85 % — so *"often"* is fair and *"almost
always"* is not.

The second half times three check orderings against the same faults, against
the cheapest of all 720 orderings found by trying all 720. Control-plane-first
costs 5.4 minutes against a best of 5.2 when the symptom points at the routing
table — as good as thinking about it. On *"small packets pass and large ones do
not"* it costs 20.0 minutes against 4.3. The advice that survives is "read the
control plane first **when the symptom points there**".

## Make it yours

- In `bisect_vs_guess.py`, put in your own path length and your own estimate of
  how often a probe lies, and see what your confidence in the answer should be.
- In `four_questions.py`, replace the priors with your own service desk's mix,
  then re-run the sweep and find your own break point. Put in your real change
  rate and see what your correlations are worth. For a single incident you do not
  need to edit anything: `--case` takes the answers on the command line.
- In `control_vs_data_plane.py`, replace the check costs with how long those
  commands actually take you, and the symptom weights with your own, then look
  at which ordering the arithmetic recommends.

## What to take away

- Bisection is worth ten tests instead of five hundred — when the space is
  ordered, the midpoint is testable, there is one fault and the oracle is
  honest. Check those four before trusting the tenth answer.
- The four questions are still the first thing to do, and their answers are
  weights, not verdicts. Write down what they left alive.
- Correlation with a change is evidence whose strength you can compute, and in
  a busy estate that strength is close to nothing.
- A clean control plane is a result, not an all-clear: you have read two stages
  out of six.
