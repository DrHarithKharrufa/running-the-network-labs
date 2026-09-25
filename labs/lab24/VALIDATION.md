# Lab 24 validation — 17 September 2026

Executed on WSL Ubuntu 26.04, Linux 6.18.33.2-microsoft-standard-WSL2,
iproute2 6.19.0 and extracted FRR 10.5.1-1ubuntu4.1. The machine's installed
package/services state was not repaired or replaced. Kernel multicast routing
was available. The adapter created isolated network/mount namespaces and
removed only its own lab resources after copying observations.

## Routed multicast: 20260917T001822Z — 13 assertions

Four FRR routers (including a detached RP), source and two receiver namespaces;
the supplied configuration files and Python source-filter socket helper ran.
Unicast reachability and PIM snapshots precede actual service tests.
Both receivers obtained 100/100 measured ASM packets, with real PIM Register
traffic captured at the RP. After losing only the RP attachment, source
unicast remained reachable, a new ASM group delivered zero, and a new SSM
channel delivered 100/100 at each receiver. The unrequested source and TTL1
each delivered zero; the correct source/TTL restored delivery. A source /32
static route changed r3's effective RPF lookup to eth2, stopped rx1 while rx2
continued, and removal restored both. RP attachment recovery restored new ASM.

Assertions generally accept at least95/100 positive measured packets after
warm-up; negative tests require zero. Baseline observed counts above were100.
The first assertion records reachability plus PIM snapshots, not a strict
neighbour-count assertion. `(S,G)` state was observed, but the saved last-hop
ASM flags do not prove SPT switchover. No such claim is made. The preliminary
001730Z attempt failed configuration before protocol assertions because the
reduced query interval preceded the reduced maximum-response time.

## Switched snooping: 20260917T002613Z — 7 assertions

Separate Linux bridge with one source, one member and one nonmember observer;
no PIM. Explicit IGMPv3, query interval2s, maximum response1s, membership5s;
accelerated Linux teaching settings, not production timer advice. The querier
was enabled after timer/address/port setup. Known-group delivery was50/50 at
the member and absent from the nonmember capture. Stopping queries aged the
dynamic MDB entry. With unknown flooding enabled, the next50 packets reached
the receiver and the nonmember wire. Disabling unknown flooding on the member
port then delivered zero. Restoring the querier restored membership and later
50/50 forwarding even while that port's unknown flooding stayed disabled.
Actual IGMPv3 reports and general queries are in the retained capture.

MDB appearance was **not** an instantaneous forwarding-readiness indicator:
the first50-packet restoration burst delivered26, followed by50/50 after a
two-second settling period. This does not establish a convergence bound.
Prior002209Z failed a premature50/50 restoration assertion (24 received).
Prior002422Z captured the nominal known baseline on the nonmember as well.
That run enabled the querier before configuring all timer/address state;
the successful run changed the ordering. The precise kernel gating cause was
not isolated, so startup order is documented without a claimed root-cause proof.

## Not executed or established

Docker build, Containerlab adapter/startup, commercial NOS/ASIC, IPv6/MLDv2,
competing-querier election, Anycast RP, MSDP, BSR/Auto-RP operation, multicast
VPN, hardware capacity, load/failover guarantees and microsecond timing.
Source code review, Python/bash/YAML checks and arithmetic are separate from
the protocol evidence. Full captures, commands, states and failed attempts
remain in `outputs/publication-revision/runtime-evidence` in the review bundle.
