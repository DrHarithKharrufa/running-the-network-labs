# Lab 40 — the server/network boundary

Two parts. One reads the kernel; one validates a plan. Neither builds a bond,
and the reason is recorded rather than hidden.

```bash
sudo python3 offload_probe.py   # 9 checks, needs root + ethtool
python3 bondcheck.py            # the validator
python3 test_bondcheck.py       # 51 checks, exit 0
```

## Lab 40.1 — what "offload" actually means

The usual account is *"TSO: the NIC chops the buffer into segments; GRO/LRO: the
NIC coalesces arriving segments."* Run this against a **veth pair**, which has no
network card, no driver firmware and no silicon anywhere in its path, and the
kernel reports 60 feature flags — with **both** `tcp-segmentation-offload` and
`generic-segmentation-offload` **on**.

There is no NIC there to do any chopping. What is happening is:

- **GSO is a kernel feature.** The stack carries one large buffer as far down as
  it can and segments late, saving per-packet work whether or not hardware helps.
  The lab toggles it on this software-only device; toggling alone does not
  distinguish hardware and software on other devices.
- **GRO** is likewise commonly done in the Linux receive path.
- **LRO** is driver-dependent receive aggregation, possibly hardware-assisted. On this
  device the kernel reports it `off [fixed]` and refuses an attempt to enable it:

```
Could not change any device features / Actual changes: / rx-lro: off [requested on]
```

That `[fixed]` marker is how `ethtool` tells you a feature is not yours to
change. On the reference run, 30 of the 60 flags were fixed and 30 were not.

**No throughput is measured and no rate is reported.** Reading a flag is not
watching a packet, and a flag reported "on" does not prove a given packet took
that path.

## Lab 40.2 — the bond you have not built yet

`bondcheck.py` validates an **intended** host bond against an **intended** switch
side. It knows all seven Linux bonding modes and what each needs:

| Mode | # | Needs from the switch |
|---|---|---|
| `balance-rr` | 0 | a static LAG |
| `active-backup` | 1 | **nothing** — independent ports |
| `balance-xor` | 2 | a static LAG |
| `broadcast` | 3 | a static LAG |
| `802.3ad` | 4 | an LACP partner, or a coordinated multi-chassis one |
| `balance-tlb` | 5 | **nothing** |
| `balance-alb` | 6 | **nothing** |

### What the previous version got wrong

- It tested `mode == "802.3ad"` and treated **every other string** as a valid
  static mode. A typo, or an invented word, passed silently. Now an unknown mode
  is rejected with the valid list.
- It said every mismatch produces a bond that "half-works" and "pings fine". It
  can also **forward nothing at all**, or fall back to one member and work
  quietly at half capacity. Which one depends on configuration you have to
  inspect, so the checker now lists the possible outcomes and what to look at —
  actor and partner state, collecting/distributing flags, the aggregator each
  side thinks it joined.
- It compared a host MTU against a switch MTU as if they measured the same
  thing. They usually do not: a host IP MTU is payload; a switch maximum frame
  size normally includes the Ethernet header and sometimes the FCS. A 9000-byte
  host MTU against a 9000-byte switch frame is now reported as an error, with the
  arithmetic shown, and the header allowance is a parameter you set to whatever
  your platform actually counts.

It also states what a bond does *not* do: the hashing modes select a member **per
flow**, so two 25 GbE links carry 50 Gb/s of aggregate across many flows while
one backup job still gets 25 — and the host's transmit hash and the switch's hash
are chosen independently, so traffic can be balanced in one direction and pinned
to one member in the other.

## What neither lab establishes

**No bond was built.** The host these labs were prepared on has no bonding
driver — `ip link add type bond` returns `Error: Unknown device type` — and
Lab 40.1 checks for it and reports the result rather than assuming. So **nothing
in this book demonstrates LACP actor and partner state.** Lab 40.2 compares two
intentions; agreement of intent is the cheapest check available and the weakest.

On a host that does have bonding, build it and confirm the real state. That is
the step this book cannot take for you.

Also not established: any throughput figure, what a real NIC does with TSO, GRO
or LRO, and anything at all about a specific adapter or driver.
