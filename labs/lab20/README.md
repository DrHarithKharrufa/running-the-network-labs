# Lab 20 — IS-IS reachability and maintenance scope

This is a five-router teaching subset of Kestrel. It exercises IPv4 standard
topology and IPv6 multi-topology 2 with FRR 10.5.1. It has no MPLS, SRv6,
customer services, traffic-capacity model or commercial NOS. See VALIDATION.md
for the exact Linux execution evidence and the unexecuted Containerlab adapter.

Use an isolated disposable lab. All authentication strings are public lab
values. HMAC-MD5 here is a legacy compatibility mechanism, not the production
algorithm recommendation. Hello and LSP/SNP authentication are both configured;
production key selection, rollover and replay/restart policy require a separate
target-specific design. One-second Hellos and calculation timers are lab choices.

## Topology and addressing

| Router | IPv4 loopback | IPv6 loopback | NET |
|---|---|---|---|
| lon-p-01 | 10.255.0.11/32 | 2001:db8:20::11/128 | 49.0001.0102.5500.0011.00 |
| man-p-01 | 10.255.0.12/32 | 2001:db8:20::12/128 | 49.0001.0102.5500.0012.00 |
| bhm-p-01 | 10.255.0.13/32 | 2001:db8:20::13/128 | 49.0001.0102.5500.0013.00 |
| lds-p-01 | 10.255.0.14/32 | 2001:db8:20::14/128 | 49.0001.0102.5500.0014.00 |
| lds-p-02 | 10.255.0.15/32 | 2001:db8:20::15/128 | 49.0001.0102.5500.0015.00 |

| Endpoint A | Endpoint B | IPv4 A/B, each /31 | IPv6 prefix, A ::0 and B ::1, each /127 | Cost each direction |
|---|---|---|---|---|
| lon-p-01 eth1 | man-p-01 eth1 | 10.254.0.0 / .1 | 2001:db8:20:1:: | 60 |
| lon-p-01 eth2 | bhm-p-01 eth1 | 10.254.0.2 / .3 | 2001:db8:20:2:: | 40 |
| man-p-01 eth2 | lds-p-01 eth1 | 10.254.0.4 / .5 | 2001:db8:20:3:: | 60 |
| bhm-p-01 eth2 | lds-p-01 eth2 | 10.254.0.6 / .7 | 2001:db8:20:4:: | 40 |
| lds-p-01 eth3 | lds-p-02 eth1 | 10.254.0.8 / .9 | 2001:db8:20:5:: | 40 |

The IPv6 allocation is local to this exercise. The JSON-compatible YAML
contains the complete interface addressing and forwarding settings. All five
physical links are point-to-point L2 adjacencies: expect ten directed Up rows
when summing neighbour records, excluding passive loopbacks. London-to-Leeds
cost is 40+40+10=90 via Birmingham versus 60+60+10=130 via Manchester, including
the advertised loopback prefix cost of 10. Reverse-direction routes must also
work; a one-way next-hop observation is insufficient.

## Start and establish evidence

The prepared image uses Ubuntu 26.04 and package frr=10.5.1-1ubuntu4.1. Build
from lab18, then deploy from this directory:

```bash
docker build -f ../lab18/Dockerfile.frr -t netbook-frr:10.5.1 ../lab18
sudo containerlab deploy -t isis.clab.yml
bash start.sh
```

Containerlab/Docker deployment was not available on the review host. Commands
above are a prepared adapter, not a recorded execution. Record the image
digest, package version, kernel and Containerlab version when you execute it.
Do not silently substitute a newer FRR release and call the result identical.

These Bash helpers refer only to containers created by this topology:

```bash
v() { local n="$1"; shift; docker exec "clab-lab20-$n" vtysh "$@"; }
ipn() { local n="$1"; shift; docker exec "clab-lab20-$n" ip "$@"; }
```

For every router, save `show version`, `show running-config`,
`show isis neighbor`, `show isis interface detail`,
`show isis database detail`, `show ip route` and `show ipv6 route` using
`v ROUTER -c 'COMMAND'`. Confirm correct NET, level, topology membership,
metric, source prefix and authentication, then wait for the required routes.
Do not treat a fixed ten-second delay or Up adjacency as proof of convergence.

```bash
ipn lon-p-01 route get 10.255.0.14
ipn lon-p-01 -6 route get 2001:db8:20::14
docker exec clab-lab20-lon-p-01 ping -c 5 -I 10.255.0.11 10.255.0.14
docker exec clab-lab20-lon-p-01 ping -6 -c 5 -I 2001:db8:20::11 2001:db8:20::14
docker exec clab-lab20-lds-p-01 ping -c 5 -I 10.255.0.14 10.255.0.11
docker exec clab-lab20-lds-p-01 ping -6 -c 5 -I 2001:db8:20::14 2001:db8:20::11
```

London uses eth2 for both destinations. Test each other router's loopback in
both families too. Ping replies exercise a return path but are not throughput,
MTU, TCP continuity or control-plane capacity tests. Resolve baseline failures
before introducing faults.

## Experiment A: overload, finite cost and interface failure

In separate terminals, run timestamped probes while applying changes:

```bash
docker exec clab-lab20-lon-p-01 ping -n -D -O -i 0.1 -I 10.255.0.11 10.255.0.14
docker exec clab-lab20-lon-p-01 ping -6 -n -D -O -i 0.1 -I 2001:db8:20::11 2001:db8:20::14
```

Save output and command timestamps; stop each probe with Ctrl-C to retain its
summary. First change only the standard topology overload indication:

```bash
v bhm-p-01 -c 'configure terminal' -c 'router isis CORE' -c 'set-overload-bit' -c end
v lon-p-01 -c 'show isis database detail'
ipn lon-p-01 route get 10.255.0.14
ipn lon-p-01 -6 route get 2001:db8:20::14
```

In this release/configuration IPv4 moves to eth1 via Manchester, while IPv6
multi-topology 2 remains on eth2. Inspect the received LSP's standard overload
flag and topology-specific flags. Then overload IPv6 topology 2 as well:

```bash
v bhm-p-01 -c 'configure terminal' -c 'router isis CORE' -c 'topology ipv6-unicast overload' -c end
```

Both routes should now use eth1 and both services should still deliver. All
ten directed adjacencies remain Up. Separately ping Birmingham's own .13 and
`2001:db8:20::13` loopbacks from London's loopbacks: they remain reachable via
eth2. Overload restricts transit calculation; it does not drain all traffic
or withdraw the overloaded router's attached destinations.

Restore **both** indications:

```bash
v bhm-p-01 -c 'configure terminal' -c 'router isis CORE' -c 'no set-overload-bit' -c 'topology ipv6-unicast' -c end
```

The second command retains IPv6 topology membership while clearing its flag.
Wait for eth2 in both route lookups, check the received flags, ten Up rows and
successful probes. Count transmitted/received sequences and timestamp gaps
within the observation window. No loss at 100 ms sampling cannot establish
zero interruption for arbitrary traffic.

With the baseline restored, compare a finite high metric on Birmingham's
outgoing Leeds circuit. This is not a reserved maximum-metric advertisement:

```bash
v bhm-p-01 -c 'configure terminal' -c 'interface eth2' -c 'isis metric 200' -c end
```

London's forward path should move to Manchester in both families; all
adjacencies remain Up. Inspect reverse routes separately because a directional
cost change can make forward and return paths differ. Restore cost 40 and
verify the baseline before the next test:

```bash
v bhm-p-01 -c 'configure terminal' -c 'interface eth2' -c 'isis metric 40' -c end
ipn bhm-p-01 link set eth2 down
```

Now one physical adjacency is lost (eight directed Up records remain) and
both families should use Manchester. Attached-link and adjacency behaviour
differs from overload. Restore and verify all services:

```bash
ipn bhm-p-01 link set eth2 up
```

Complete a results table with before/fault/restored routes for each family,
adjacency totals, local-destination delivery, probe loss and sampling limits.
Do not generalise these virtual results to a hardware line-card drain.

## Experiment B: a deliberately separate legacy IPv4 phase

First attempt `metric-style narrow` under `router isis CORE` on lds-p-02.
FRR 10.5.1 rejects it while multi-topology is configured. Save the error and
confirm the running configuration stayed wide. The rest of this experiment
explicitly removes IPv6 participation on that router; it does not demonstrate
an uninterrupted dual-stack migration.

```bash
v lds-p-02 -c 'configure terminal' \
  -c 'interface eth1' -c 'no ipv6 router isis CORE' -c 'no isis topology ipv6-unicast' -c exit \
  -c 'interface lo' -c 'no ipv6 router isis CORE' -c exit \
  -c 'router isis CORE' -c 'no topology ipv6-unicast' -c 'metric-style narrow' -c end
```

Wait for advertisements to settle, then compare the neighbour state, detailed
database, effective configuration and IPv4 route to .15. In the recorded run
all ten directed adjacencies stayed Up while London could no longer reach
10.255.0.15. Inspect narrow IS/IP reachability versus extended reachability:
the advertised/accepted information needed for a usable path is the issue.

**Observed diagnostic defect:** on the exact extracted Ubuntu FRR package,
`show isis database detail json` aborted isisd when narrow records were
present (a JSON array assertion). Use plain `show isis database detail` in
this narrow/transition exercise. The failed run and backtrace are retained.
This was triggered by the diagnostic command, not proof that narrow encoding
itself crashes the routing protocol. Check the target release for a fix
before enabling automated collection of that JSON command in a legacy domain.

Enable transition on the extra Leeds router:

```bash
v lds-p-02 -c 'configure terminal' -c 'router isis CORE' -c 'metric-style transition' -c end
v lds-p-02 -c 'show isis database detail'
docker exec clab-lab20-lon-p-01 ping -c 5 -I 10.255.0.11 10.255.0.15
```

Inspect both advertisement forms and the installed path; IPv4 service should
return. This is one measured compatibility case, not a universal multivendor
migration order. A production matrix must list each exact release's transmit,
receive and use behaviour, allowed metrics and intermediate states.

Return to the original wide, dual-stack baseline:

```bash
v lds-p-02 -c 'configure terminal' \
  -c 'router isis CORE' -c 'metric-style wide' -c 'topology ipv6-unicast' -c exit \
  -c 'interface eth1' -c 'ipv6 router isis CORE' -c 'isis topology ipv6-unicast' -c exit \
  -c 'interface lo' -c 'ipv6 router isis CORE' -c end
```

Verify both loopback families for every router, all ten directed Up records,
wide advertisements and the intended primary paths. Finish by destroying only
this disposable topology:

```bash
sudo containerlab destroy -t isis.clab.yml
```

## Submission and further work

Submit version/configuration records, the topology/identity inventory, baseline
and restored delivery, received overload flags and per-family route choices,
continuous-probe records, and the metric compatibility observations. Explain
why attached destinations, explicit tunnels, other VRFs, spare capacity and
actual hardware readiness still matter before a maintenance action.

L1/L2 leaking, broadcast DIS election, duplicate-system-ID injection, modern
authentication rollover, restart, SR-MPLS/SRv6 and hardware scale are separate
experiments. Do not mark them passed from this lab. Primary reading: RFCs 1195,
5120, 5302, 5303, 5304, 5305, 5310, 3277 and the
[FRR 10.5 IS-IS manual](https://docs.frrouting.org/en/stable-10.5/isisd.html).
