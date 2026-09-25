# Lab 38.1 — the SONiC evidence chain

**Nothing in this book has been run on SONiC.** The host these labs were prepared
on has no Docker daemon, so neither the SONiC virtual switch (`docker-sonic-vs`)
nor Containerlab's `sonic-vs` kind was available, and no SONiC image — virtual or
physical — was executed. This lab teaches a method and gives you a checklist to
verify against your own image. It is not a result.

```bash
python3 dbwalk.py            # the chain for a route learned from BGP
python3 dbwalk.py --static   # the chain for a statically configured route
python3 dbwalk.py --json     # the same, as data
python3 test_dbwalk.py       # 23 checks, exit 0
```

## The correction this lab exists to make

The previous version of this lab modelled the chain as:

```
CONFIG_DB  ->  APPL_DB  ->  ASIC_DB  ->  STATE_DB
(you asked)   (BGP took)   (SAI made)   (chip has)
```

and said a route missing from `CONFIG_DB` meant *"you never configured it"*.

Both ends of that are wrong, and an engineer following it would waste an outage.

**A learned route is not expected in `CONFIG_DB`.** `CONFIG_DB` holds *intended
configuration* — the BGP session you configured, a static route you wrote, an
interface address. A prefix a neighbour advertised to you was never part of your
intent, so it will not be there, and concluding "nobody configured it" sends you
after a prerequisite that does not exist.

**`STATE_DB` is not the chip's acknowledgement.** It carries observed operational
state: link status, neighbours, transceiver health, per-feature status. It is
genuinely useful and it is not a per-route hardware receipt. `ASIC_DB` holds the
*request*; the outcome lives in `syncd`'s logs and SAI status, and ultimately in
whether traffic moves.

## The chain, for a learned BGP route

| Stage | Evidence | What it does **not** establish |
|---|---|---|
| bgpd RIB | `vtysh -c 'show bgp ipv4 unicast <prefix>'` | that it was selected, or that zebra has it |
| bgpd best path | the best marker in the same output | anything about the kernel or the ASIC |
| zebra RIB + next hop | `vtysh -c 'show ip route <prefix>'` | **that the ASIC has it** — this is the software RIB |
| `APPL_DB` `ROUTE_TABLE` | `redis-cli -n <APPL_DB> keys "ROUTE_TABLE:<prefix>*"` | that orchagent acted on it |
| `ASIC_DB` route entry | `redis-cli -n <ASIC_DB> keys "ASIC_STATE:SAI_OBJECT_TYPE_ROUTE_ENTRY:*"` | that syncd programmed it — this is the request |
| syncd / SAI status | syncd log and syslog for SAI errors on that object | that traffic follows the route |
| forwarding | send traffic, count it at both ends | that it holds at scale or under load |

For a **static** route, the same chain with `CONFIG_DB` in front of it.

The database numbers are written as placeholders on purpose. Read them from
`database_config.json` on the switch rather than assuming; they are conventional,
not guaranteed.

## Verify before you rely on any of it

Stage names, Redis layout, container composition and tooling vary by SONiC
release and distribution. If you have a switch or a virtual switch:

1. Configure a route and walk the chain, confirming each stage's evidence.
2. Break it deliberately at one named stage — withdraw the prefix upstream, stop
   the routing container, remove the next-hop route — and confirm the evidence
   stops where the model predicts.
3. Record the image name and version alongside whatever you observe. Anything
   else is not reproducible.

## One exercise the previous version proposed, which you should not do

It suggested filling the route table past the ASIC's capacity **on a virtual
switch** and watching hardware programming fail. A virtual switch does not
reproduce a physical ASIC's table capacity, buffering or SAI resource limits.
Whatever that produces is a property of the emulation. If you need a chip's
limits, take them from its documentation and confirm them on the hardware.

## What to take away

- In SONiC you debug by reading state you can actually query — but start where
  the route enters and end at evidence, not at a database that means something
  else.
- The stage where the evidence stops narrows the fault to a team: control plane,
  next-hop resolution, the FPM path, orchestration, SAI, or silicon.
- `show ip route` is never the end of a hardware investigation.
