# Lab 42 — the hybrid edge, the addressing, and the trade nobody prices

Three calculators. None touches a cloud account, an API or a router, and none
validates a configuration. What they do is take the three claims Chapter 41
rests on and put them somewhere they can be checked — and, more to the point,
somewhere a plausible design can **fail**.

| | What it computes | What it can show you were wrong about |
|---|---|---|
| 42.1 `hybrid_bgp.py` | Route exchange across the cloud on-ramp | That a high local-preference on the circuit makes the circuit carry the traffic |
| 42.2 `landingzone.py` | An addressing plan against what is expensive to undo | That addressing is the only landing-zone decision you cannot cheaply reverse |
| 42.3 `egress_vs_availability.py` | The transfer bill *and* the expected downtime | That collapsing a tier into one availability zone is a saving |

```bash
python3 hybrid_bgp.py               # and --json
python3 landingzone.py
python3 egress_vs_availability.py   # and --downtime-cost / --zone-failure

python3 test_hybrid_bgp.py               # 40 checks
python3 test_landingzone.py              # 48 checks
python3 test_egress_vs_availability.py   # 41 checks
```

Python 3 only. Nothing else is needed and nothing else is used.

## The version this lab is built against

Picture the obvious version of this tool. It calls `ipaddress.overlaps()` on two
hard-coded dictionaries — one deliberately overlapping, one not — and reports
that they did and did not overlap. And it multiplies invented per-gigabyte
tariffs by invented monthly volumes and announces a saving that the choice of
volumes had already decided.

Neither used anything the reader supplied, so neither could disagree with
anyone. And between them they never went near BGP, which is the one thing the
chapter says is the skill: *the cloud edge is not a new kind of device; it is a
peering router*. A lab for this chapter that does not exchange a route is not a
lab for this chapter.

## 42.1 — the failover that does not fail over

A private circuit with a VPN backup is normally built by giving the circuit a
higher local-preference. That works **only while both paths carry the same
prefix**.

Best-path selection runs per prefix. Forwarding then takes the longest match.
Those are two different steps, and the second one has never heard of
local-preference. So if the VPN session advertises `10.10.1.0/24` while the
circuit advertises `10.10.0.0/16`:

```
--- intended: circuit preferred, VPN standby
    best 10.10.0.0/16     via circuit  lp=200  (beat vpn)
    10.10.1.5    -> circuit  (longest match 10.10.0.0/16, lp=200)

--- the mistake: VPN advertises a more-specific
    best 10.10.0.0/16     via circuit  lp=200  (beat vpn)
    best 10.10.1.0/24     via vpn      lp=50
    10.10.1.5    -> vpn      (longest match 10.10.1.0/24, lp=50)
    10.10.9.5    -> circuit  (longest match 10.10.0.0/16, lp=200)
```

The circuit's preference is 200 against the VPN's 50 in **both**. Some of the
traffic takes the VPN anyway — at VPN bandwidth, with VPN latency — and:

- both BGP sessions are up,
- no counter moves,
- no alarm fires,
- the only symptom is that some traffic is mysteriously slow.

Raising the circuit's preference to 4000 changes nothing, and the checks assert
that too. The fix is a prefix-list on the VPN session permitting the summary and
nothing longer — **policy on what you advertise**, not a preference on what you
receive.

The script also models two other things that bite: advertising a supernet that
swallows the cloud's own range, and exceeding the prefix limit on the session.
That second one matters because the failure is not graceful: the session drops
rather than trimming to the limit, so the consequence is total loss of that
path, not partial reachability — and the model reproduces that rather than only
warning about it.

## 42.2 — the decisions that are expensive to undo

The chapter used to say two landing-zone decisions were painful to reverse and
"security groups, subnets and DNS can all be adjusted later". Subnets cannot.
**You cannot resize a subnet after you create it** — you create a new one and
migrate into it — so a subnet sized for today's workload is a migration you have
scheduled without noticing.

The shipped example plan is a plausible first draft and it fails on four
distinct counts, on purpose: a range that collides with something the hosts
already use, a hub too small to hold the subnets planned for it, subnets sized
for today rather than for the growth the plan itself states, and a three-zone
VPC with two zones' worth of subnets. The script prints the prefix each subnet
*should* have, and the revised plan passes clean.

Change a prefix, a growth figure or a host count and the findings follow —
which is what the previous version could not do.

## 42.3 — the trade, priced on both sides

Collapsing a chatty two-zone tier into one zone does stop the cross-zone
metering. It also removes the thing the second zone was there for. The old
advice, and the old lab, priced only the first half.

```
                              design | zones |   transfer | hrs down |   downtime | total
               spread over two zones |     2 |       2150 |     0.00 |          4 |       2154
             collapsed into one zone |     1 |       1750 |     0.73 |       3650 |       5400
two zones, analytics kept cloud-side |     2 |        845 |     0.00 |          4 |        849  <-- cheapest
```

Collapsing saves 400 a month and adds 3,646 in expected downtime. It is not a
saving; it is a trade, and on these figures it loses. Set the downtime cost low
and the answer flips — so it is a trade, not a rule, and the script exists to
make you state both sides rather than one.

Two results worth sitting with:

- **The design that gives nothing up wins.** Keeping both zones and shipping the
  analytics *result* instead of the raw data saves more than collapsing did,
  with no availability surrendered at all. Look for that saving first; it is
  usually the larger one.
- **A second zone you never fail over to is worse than not having it.** Set
  failover effectiveness to zero and the tier is down whenever *either* zone is
  — you have doubled the number of zones that can take you down and gained
  nothing. A second zone is not availability. Failing over to it is.

Every tariff and every probability is **your input**. No vendor price list or
published availability figure was available when this was written, and none is
assumed.

## What none of this establishes

- **No cloud account, API call, VPC, circuit or BGP session.** Nothing here was
  deployed, configured or measured.
- **No provider behaviour was verified.** Where the chapter now describes what a
  specific cloud does, it says which cloud; where the labs model a behaviour,
  they model the general shape and tell you to check your provider's current
  documentation and quotas.
- **No prices and no availability figures.** Both are inputs, both are
  illustrative, and both move faster than a book.
- **The BGP model is partial on purpose.** Longest match, then
  local-preference, then AS-path length, then a stated tie-break. No MED, no
  origin code, no router-ID, no communities, no add-path, no route reflection,
  no dampening.
