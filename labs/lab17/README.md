# Lab 17 — ECMP, flow entropy and a separate polarisation model

This is **IPv4 Linux kernel forwarding with static routes**. No BGP/FRR,
switch ASIC, throughput, IPv6 or failover-time result is implied. Containerlab
is an adapter for the topology; its execution is separate from the namespace
review evidence. The fixed Linux hash seed requires a kernel exposing
`net.ipv4.fib_multipath_hash_seed`; check support before deployment.

## Topology and forwarding assumptions

`h1 -- leaf1 -- {spine1, spine2, spine3, spine4} -- leaf2 -- h2`

h1 is 10.0.1.10/24, gateway 10.0.1.1; h2 is 10.0.2.10/24, gateway
10.0.2.1. For spine number i=1..4, let a=4(i-1), b=16+4(i-1):

| Link | Leaf address | Spine address | Interface pair |
|---|---|---|---|
| leaf1–spine i | 192.0.2.(a+1)/30 | 192.0.2.(a+2)/30 | leaf eth(i+1), spine eth1 |
| leaf2–spine i | 192.0.2.(b+1)/30 | 192.0.2.(b+2)/30 | leaf eth(i+1), spine eth2 |

The topology contains every expanded address and static route. Each leaf
has four equal-weight next hops towards the opposite host LAN. Each spine
has **one** next hop towards each host LAN. In this traffic direction there
is one four-way ECMP choice, at leaf1, not two consecutive independent choices.
Changing the hash at leaf2 therefore cannot establish forward-path multistage
polarisation. Return traffic has its own leaf2 decision.

The previous FRR sketch also paired addresses from different /31s. For a
/31, .0/.1 form one pair, .2/.3 the next; .1/.2 are not an on-link pair.
This replacement uses explicit, non-overlapping /30s and needs no routing daemon.

## Run and collect evidence

Build `netbook-services:20260916` using `labs/common/README.md`, then:

```sh
sudo containerlab deploy -t forwarding.clab.yml
docker exec clab-lab17-leaf1 ip -j route show 10.0.2.0/24
docker exec clab-lab17-h1 ping -c 2 10.0.2.10
```

Record kernel and iproute2 versions, image digest, routes and these sysctls:

```sh
docker exec clab-lab17-leaf1 sysctl net.ipv4.fib_multipath_hash_policy
docker exec clab-lab17-leaf1 sysctl net.ipv4.fib_multipath_hash_seed
```

The starting policy is 1 (Layer 4), seed 314159265. A nonzero seed aids
reproducibility on the same implementation; Linux does not promise the same
algorithm or mapping across kernel versions. The forwarding namespaces disable
reverse-path filtering explicitly so a separately hashed return path is not
mistaken for an ECMP delivery failure.

Start the echo server in one terminal:

```sh
docker exec -it clab-lab17-h2 python3 -u /lab/flows.py server
```

Start a bounded observation in a second terminal; wait for `READY`:

```sh
docker exec -it clab-lab17-leaf1 python3 -u /lab/flows.py observe \
  --output /tmp/l4-baseline.json
```

Then generate 1024 UDP five-tuples, varying source port 20000..21023, four
echo exchanges each. Addresses, destination port 9000 and protocol stay fixed:

```sh
docker exec clab-lab17-h1 python3 /lab/flows.py client --flows 1024 --samples 4
```

After the client completes, stop the observer with Ctrl-C. It writes JSON
counts by interface/source port and a classic Ethernet pcap of outgoing test
requests. It ignores other traffic and the echoed replies. Inspect and export:

```sh
docker exec clab-lab17-leaf1 cat /tmp/l4-baseline.json
docker cp clab-lab17-leaf1:/tmp/l4-baseline.json ./l4-baseline.json
docker cp clab-lab17-leaf1:/tmp/l4-baseline.pcap ./l4-baseline.pcap
```

Required checks: 4096 valid echoes, 4096 captured requests, exactly one egress
per source port with four packets, and all four members used. For this
1024-flow teaching sample, a deliberately broad diagnostic band is **15–35%**
per member. It is not a fairness guarantee or statistical certification of
all traffic mixes. Preserve the actual counts, including an unexpected result,
and inspect packet loss, capture completeness and implementation differences.

## Remove port entropy, then restore it

Set only leaf1's policy to 0 (Layer 3):

```sh
docker exec clab-lab17-leaf1 sysctl -w net.ipv4.fib_multipath_hash_policy=0
```

Repeat observation/generation, naming the output `/tmp/l3-entropy.json`.
All test five-tuples now have the same Layer 3 hash inputs, so the expected
result for this kernel setup is one used member. **This is loss of hash
entropy, not multistage polarisation.** Restore policy 1, repeat with
`/tmp/l4-restored.json`, and compare each source port's mapping with baseline.
Keep seed and next-hop membership unchanged during that comparison.

Finally observe `/tmp/single-flow.json` and run:

```sh
docker exec clab-lab17-h1 python3 /lab/flows.py client --flows 1 --samples 64
```

One fixed five-tuple should stay on one path in this tested static per-flow
configuration. This is a path-selection experiment, not a saturation test
or a universal claim about per-packet, flowlet or adaptive implementations.
Stop the server and destroy only this topology when finished:
`sudo containerlab destroy -t forwarding.clab.yml`.

## Two-stage correlation model

Run `python3 polarisation.py` locally. It constructs two serial two-way choices
using a declared SHA-256-based toy hash. With identical inputs/function/seed,
the choices correlate: only paths 0→0 and 1→1 occur. With another seed in this
particular model, all four combinations occur. Its counts demonstrate the
mathematical possibility of correlation; SHA-256 here is **not** a model of
a switch's actual hashing circuit or the Linux multipath hash.

On real multistage hardware, establish the actual topology, eligible groups,
hash fields, seed controls, tunnel parsing and correlation before changing
settings. Different seeds are an option only where supported; they are not
an unconditional cure. An actual ASIC polarisation experiment remains pending.

## Recorded review execution

Linux 6.18.33.2 and iproute2 6.19.0, in disposable WSL namespaces, passed
17 assertions in `20260916T214701Z`. The Layer 4 counts were **225, 259, 277,
263 flows** across eth2..eth5. Layer 3 put all **1024** on eth3. Restoration
reproduced the initial mapping; the single-flow case used eth5. Every
generated test echo and outgoing request was accounted for. Those counts
describe that run, not promised results on another kernel/image.

## Questions and answer guidance

1. Why does changing source ports help policy 1 but not policy 0 in this setup?
   Identify the varying fields actually included in each hash.
2. How can one large transfer use more aggregate bandwidth? Supported
   application parallelism across distinct flows or an appropriate multipath
   transport can distribute work; a faster member raises single-path capacity.
   More equal-rate members alone do not guarantee improvement for one hashed flow.
3. For encapsulated traffic, determine whether the platform hashes inner
   headers or varying outer fields. An entropy mechanism must be generated
   and consumed by the actual implementation, not merely named in a design.
4. Why is a route lookup different from capture evidence? Lookup models the
   supplied packet context at one instant; capture observes packets on an
   interface. Neither by itself proves application service on the full path.

Primary reference: https://docs.kernel.org/networking/ip-sysctl.html,
especially multipath hash policy, fields and seed. Exact-route command syntax
and resource/ASIC inspection must be checked for the target platform.
