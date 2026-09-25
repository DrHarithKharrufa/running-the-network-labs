# Lab 84.1 — A complete, isolated forwarding migration MOP

## Scope and authority

Run only on a suitable Linux lab host as root, with `iproute2` and iputils `ping`.
The script creates four unique `rtn84-<random>-*` network namespaces. All veth
endpoints are created directly within those namespaces; no host or physical
interface is attached. Routers have no default route. The host workload is three
ICMP probes per positive check. There is no production service, routing daemon,
NOS image, hardware, NAT/firewall or persistent application state in this lab.

The static routes reproduce the forwarding states of a two-router transition.
This is actual Linux forwarding evidence, not an OSPF-to-IS-IS migration test.
No flag prints `NOT_RUN`; `--run` performs the lab, including deliberate failure.

```console
python3 design_case.py
sudo python3 design_case.py --run > linux-execution.json
```

The supervising script is executor and local verifier in this bounded exercise;
there is no claim of independent human review. In a real MOP, name authorised
commander, deputy, executor, independent verifier, service owner and communicator.

## Addressing and forwarding policy

| Node/interface | Address | Peer |
| --- | --- | --- |
| H eth0 | 10.84.10.10/24 | A lan |
| A lan | 10.84.10.1/24 | H eth0 |
| A ad | 10.84.0.1/30 | D da |
| D da | 10.84.0.2/30 | A ad |
| A ab | 10.84.0.5/30 | B ba |
| B ba | 10.84.0.6/30 | A ab |
| B bd | 10.84.0.9/30 | D db |
| D db | 10.84.0.10/30 | B bd |
| D lo | 10.84.255.1/32 | Destination |

H defaults to A. B returns 10.84.10/24 through A at 10.84.0.5. D returns
10.84.10/24 and 10.84.0.4/30 through B at 10.84.0.9. The return path remains
D–B–A–H even when the forward request uses A–D. This deliberate asymmetry is
supported by these stateless Linux routers; it is not a stateful-firewall design.
All veth MTUs remain the kernel's default; the lab does not validate a production
encapsulation MTU. No route import, export, redistribution or route-leaking process
runs. The only migrated route is exactly 10.84.255.1/32; the script specifies all
other routes. There are no catch-all permit firewall changes.

Router sysctls enable IPv4 forwarding and ignore link-down routes, and disable
reverse-path filtering and ICMP redirects for the relevant namespace interfaces.
Those last choices are specific to this isolated asymmetric-path/loop demonstration,
not recommendations for production anti-spoofing. Every command is retained in JSON.

## Ordered commands and decision gates

In the command fragments below, `A` and `B` stand for the exact generated namespace
names printed in the run's JSON. The script supplies these names directly without
shell interpolation. Stop if addresses, next hops or observations differ.

| Phase | A's selected next hop to D | B's selected next hop to D | Gate |
| --- | --- | --- | --- |
| P0 old | B (10.84.0.6) | D (10.84.0.10) | H and B receive all 3 replies |
| X1 unsafe B-first, lab only | B | A (10.84.0.5) | Expected failure and TTL exceeded |
| P0 restore | B | D | H receives all 3 replies |
| P1 safe forward step | D (10.84.0.2) | D | H and B receive all 3 replies |
| P2 candidate | D | A | H and B receive all 3 replies |
| F1 A–D down, lab only | Removed/unusable | A | Expected H failure |
| R1 rollback step 1 | Unusable | D | B receives all 3 replies |
| R2 rollback step 2 | B | D | H and B receive all 3 replies |

Selected old routes:

```console
ip -n A route replace 10.84.255.1/32 via 10.84.0.6 dev ab
ip -n B route replace 10.84.255.1/32 via 10.84.0.10 dev bd
```

Safe forward order, with route lookup and probes **between** steps:

```console
ip -n A route replace 10.84.255.1/32 via 10.84.0.2 dev ad
ip -n B route replace 10.84.255.1/32 via 10.84.0.5 dev ba
```

Rollback reverses the dependency order: restore B's old route first, then A's old
route. Reversing just A first while B still uses A recreates the forwarding loop.
The deliberately unsafe B-first phase sends TTL-4 probes, containing their life
inside the isolated lab. The link-fault phase uses `ip -n A link set dev ad down`.
The word `dev` is explicit because short interface names can otherwise be parsed
as command-keyword abbreviations. Interface-up alone does not reinstall a route
deleted by administrative shutdown; `route replace` explicitly reapplies it.

The script then raises the link, repeats the safe transition, verifies the new
state, returns to P0 using the safe rollback order and removes owned namespaces.
It records command argv, exit status, stdout/stderr, address inventories and every
phase's route tables. Expected negative probes are assertions, not unexpected test
failures. Any failed assertion stops normal progression and triggers cleanup.

## Time budget and stop conditions

The automated fault-through-rollback sequence must finish within a **15-second lab
allowance**, including command and probe overhead. This is not measured packet-loss
duration or a production recovery SLA. A real example maintenance window from
01:00 to 03:00, reserving 15 minutes rollback, 10 minutes verification and five
minutes contingency, has a latest safe rollback start of **02:30**. Those are
invented planning allowances, not values inferred from this small lab.

Stop at wrong next hop, unexpected probe result, missing capability, mismatch with
the phase table or loss of reliable evidence. In a production plan also define
service errors, security violations, state/schema changes and the point beyond
which rollback cannot safely undo new writes. After that point use a separately
approved forward-recovery plan. Do not keep troubleshooting past the latest safe
decision time without explicit reassessment of the service window and authority.

## Recorded evidence and limits

The reviewed environment is WSL2 Linux 6.18.33.2-microsoft-standard-WSL2, Python
3.14.4, iproute2 6.19.0. The corrected exploratory run passed 47 assertions and
removed every owned namespace. The first run failed during link creation because
`ad` was interpreted as a keyword abbreviation; both the failed and corrected
records are retained. The final installed script is executed again for its published
evidence. Read that run's exact versions and command outputs from `linux-execution.json`.

The loop probe produces `Time to live exceeded`; successful checks report three
received probes and `0% packet loss`. Selected next hops must match the table above.
These quoted output fragments correspond to observed local results, not fabricated
vendor console output. The run does not measure routing-protocol convergence,
load, MTU, IPv6, security-policy equivalence, application state or hardware forwarding.

Ordinary exceptions invoke cleanup. After forced process/host failure, inspect
`ip netns list` and delete only the exact run-owned names; never remove unrelated
namespaces. Retain the JSON evidence before disposing of the lab.
