# Lab 31.1 — Measure shaping, policing and scheduling separately

This is an IPv4 Linux mechanism lab. It does not implement a commercial BNG,
an MPLS hardware policy or the chapter's two-priority-level design contract.
Read `VALIDATION.md` for the precise executed scope.

## Topology and preparation

`h1 eth1 — eth1 rtr eth2 — eth1 h2` uses `10.0.1.0/24` and
`10.0.2.0/24`. Hosts are `.10`; the router is `.1` in each subnet. The MTU is
1500. The forward bottleneck is deliberately created on router `eth2`; the
reverse direction has no corresponding shaper. No Internet access is needed.

Build the common image from the `labs` directory, then deploy from this folder:

```bash
docker build -t netbook-linux:1 common
cd lab31
sudo containerlab deploy -t qos.clab.yml
docker exec clab-lab31-rtr tc -Version
docker exec clab-lab31-rtr uname -r
docker exec clab-lab31-h1 ping -c 3 10.0.2.10
```

Record the built image ID, kernel and `/netbook-package-versions.txt`. The
Dockerfile records installed versions but its base tag and package repositories
are not immutable; pin the resulting image digest for repeatable deployment.
The namespace evidence did not build or execute this container image.

`qos.sh` invokes `configure-qos.py` inside the disposable router. The helper
replaces the root qdisc on `eth2` and ingress qdisc on `eth1`. Do not run it on
a production router or a shared interface containing unrelated policies.

## What each mode actually configures

All rates below are decimal bit rates. HTB burst and cburst are explicitly
16,000 bytes, and leaf queue limits are 200 packets. Interface MTU remains 1500.

| Mode | Configuration |
|---|---|
| `fifo` | 10 Mbit/s HTB bottleneck, single explicit packet FIFO. This is shaping without class differentiation. |
| `fq` | Same bottleneck; FQ-CoDel with 5 ms target, 100 ms interval and ECN disabled. |
| `fourclass` | HTB parent 10 Mbit/s; CS6 guarantee/ceiling 0.5/0.5, EF 2/2, AF31 4.5/10, default 3/10 Mbit/s. FQ-CoDel leaves, ECN disabled. |
| `priority` | Same 10 Mbit/s parent, PRIO child: EF in first band, all other traffic in last band. Packet FIFO in each band. No EF cap. |
| `priority-policed` | Same PRIO scheduler, plus an explicit ingress EF policer at 2 Mbit/s, 16,000-byte burst, drop excess. |
| `shaper` | Single FIFO behind a 2 Mbit/s HTB shaper. |
| `policer` | Single FIFO behind the 10 Mbit/s parent, plus the same 2 Mbit/s ingress EF policer. |
| `clear` | Remove the lab's egress root and ingress qdiscs. |

The HTB `prio` field does not turn its classes into the separate PRIO scheduler.
Setting HTB `ceil` equal to `rate` prevents borrowing; it does **not** install
a policer. Business/default have the same HTB priority and explicit byte
quanta 9,084/6,056 (60:40); do not infer exact instantaneous shares from these
parameters. Observe guarantees, ceilings, borrowing and packet granularity.

The classifier matches DSCP, ignoring ECN bits with mask `0xfc`. CS6 is
`0xc0`, EF is `0xb8` (or `0xba` with ECT(0)), AF31 is `0x68`. Other values
use default treatment in this fixture. It does not implement a full AF
drop-precedence mapping, MPLS TC mapping or production trust boundary.

## Repeatable observations

`traffic.py` emits UDP packets with a sequence number and monotonic timestamp.
Default payload size is 1000 bytes, including the test header. Rates count
**UDP payload**, excluding UDP/IP/link overhead. The receiver reports unique
counts, duplicates, received TOS values and p50/p95/p99/maximum one-way delay.
Sender and receiver must share the same kernel monotonic clock. Results from
independent machines or time namespaces require another clock methodology.
User-space scheduling and socket queues contribute to the observed delay.

In one terminal, start the receiver and wait for `READY`:

```bash
docker exec clab-lab31-h2 python3 -u /lab/traffic.py receive \
  --seconds 20 --port 31002 --port 31004
```

In another terminal, immediately run the chosen policy and send traffic. Apply
the policy **before starting the receiver** if configuration startup is slow:

```bash
bash qos.sh fifo
docker exec clab-lab31-h1 python3 /lab/traffic.py send --seconds 6 \
  --flow be:31004:0:15 --flow ef:31002:0xb8:0.05
docker exec clab-lab31-rtr tc -s -d qdisc show dev eth2
docker exec clab-lab31-rtr tc -s -d class show dev eth2
docker exec clab-lab31-rtr tc -s -d filter show dev eth1 parent ffff:
```

Save complete sender, receiver and counter output for every case. Check that
the generator achieved the requested rate; an overloaded host is not a valid
network performance result. The receiver must remain active through the sender
interval and queue drain. A fixed receiver timeout is not synchronisation:
restart the pair if startup consumed the observation window.

Use fresh policies and counters between the following cases:

| Case | Mode | Sender flows (`name:port:TOS:payload-Mbit/s`) |
|---|---|---|
| Idle baseline | `fifo` | `ef:31002:0xb8:0.05` |
| Sustained overload | `fifo`, then `fq` | `be:31004:0:15` and `ef:31002:0xb8:0.05` |
| Four-class contention | `fourclass` | `control:31001:0xc0:1`, `ef:31002:0xba:4`, `business:31003:0x68:10`, `be:31004:0:10` |
| Borrowing | `fourclass` | `be:31004:0:12` |
| Priority failure/mitigation | `priority`, then `priority-policed` | `ef:31002:0xb8:20` and `be:31004:0:1` |
| Delay versus immediate discard | `shaper`, then `policer` | `ef:31002:0xb8:8` |
| Recovery | `fifo` | Repeat the idle baseline. |
| Short bursts, low average | `fifo` | `be:31004:0:1`, with `--seconds 6.4 --burst 100`. |

Start the receiver with a `--port` argument for every destination in that case.
For the burst case, 100 payload packets are released together every 0.8 seconds;
this targets 1 Mbit/s average but produces short queueing bursts. Timing is
subject to the sender's scheduler, so measure the actual output.

Compute delivery fraction as unique received packets divided by sent packets.
Compute delivered payload rate over the sender interval separately from the
receiver's first-to-last-packet rate; the latter can include queue drain or
have a very short denominator. A received count after the sender stops does
not prove useful service during the congested interval. Inspect the counter
and timing evidence before describing starvation or a service guarantee.

Use broad, stated tolerances for rate comparisons and repeat when the host
cannot sustain the traffic matrix. Do not require idle measurements to match
exactly. AQM results with this non-responsive UDP source do not establish how
TCP congestion control or ECN feedback will behave.

## Target-specific extension and cleanup

To validate the chapter's design contract on a commercial platform, specify
the release, hardware, parent bottleneck, classification path, all four queue
bindings, priority caps/bursts, weighted scheduler and AQM parameters. Test
IP and MPLS traffic separately where applicable. Include mis-marked input,
mixed packet sizes, failure-state capacity and restoration. Linux success
does not complete that acceptance work.

```bash
bash qos.sh clear
sudo containerlab destroy -t qos.clab.yml --cleanup
```
