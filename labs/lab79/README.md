# Lab 79.1 — A traceable design, implemented in isolated Linux namespaces

This is a small **IPv4 lab service**, not an enterprise WAN proposal. The four namespaces represent London host HL, router RL, router RM and Manchester host HM. Two veth transit links join RL and RM. Each router has one LAN. The only external control is the local root process; no physical/host interface is attached and no Internet route is installed in the routers.

```text
HL --- lan RL wan-a ========== wan-a RM lan --- HM
              wan-b ========== wan-b
            primary metric 100; backup metric 200
```

## Requirements and acceptance matrix (revision 1)

| ID | Requirement and boundary | Acceptance/evidence |
|---|---|---|
| R1 | Bidirectional IPv4 ICMP between HL and HM in this isolated lab | T1: three probes each way, no loss, normal RL/RM route lookup uses wan-a |
| R2 | Either single RL transit administrative shutdown leaves connectivity via the other link | T2/T3: correct RL/RM route lookup, three loss-free probes each way; command start through completion under 5 s in each test |
| R3 | Explicit restoration procedure restores primary preference and connectivity | T4: bring interfaces up **and reapply both routes**; check route selection and final probes |
| R4 | No external network attachment and no leftover lab namespaces | T0: review the interface/route construction and record inventory; router default routes absent; T5: owned names absent after cleanup |
| C1 | Local Linux root privileges and iproute2/iputils; no commercial image | Record exact software versions and retain commands/output |
| C2 | Teaching implementation fits a notional 24 engineer-hour budget | Hypothetical estimate only; not a measured result or procurement quote |

The 5 s threshold is a **local test completion allowance**, including two three-probe sequences and subprocess overhead. It is not a failover packet-loss interval, a measured convergence distribution or a production SLA. Only one run per fault in the recorded acceptance pass is claimed. IPv6, encryption, TCP applications, silent forwarding failure, router/host failure, throughput, physical diversity and simultaneous independent faults are outside R1–R4. Both transits down is deliberately tested as unreachable. A real requirement in any excluded area changes the design and test plan.

## Alternatives and decision

All effort figures are invented estimates for this teaching exercise, not market data.

| Option | Mandatory feasibility | Central/range estimate | Decision |
|---|---|---|---|
| A: one transit, static routes | Fails R2 | 6 h / 4–9 h | Reject before scoring |
| B: two transits, static routes and explicit recovery | Meets the bounded tested fault model | 10 h / 8–16 h | Select for revision 1 |
| C: two transits with a routing daemon and tested timers | Candidate for R1–R4; not implemented/tested here | 18 h / 12–22 h | Defer; extra operational work without a current silent-fault requirement |
| D: B plus an unused controller | Same assumed required behaviour as B; extra dependency | 22 h / 20–26 h | Dominated under these assumptions and risks exceeding budget |

Feasibility is not rescued by a cheap score. B and C's estimate ranges overlap, so do not claim certain cost savings. If C's existing skills/tooling reduce its effort to 8 h, reconsider it. If requirements add remote forwarding-loss detection or router failure, B no longer qualifies without redesign; C also needs explicit evidence for the new fault rather than a protocol label. No arbitrary weighted sum or assumed independence conceals these limits.

## HLD and operating model

This lab uses one router per site and two parallel transit links. LAN subnets are routed, not bridged. The preferred route has metric 100; backup has metric 200. Linux `ignore_routes_with_linkdown=1` allows the forwarding lookup to avoid routes on down links. This does not detect a silent remote forwarding failure. Interfaces and routes are controlled only inside the namespaces. IPv4 forwarding is enabled on RL/RM; reverse-path filtering is explicitly disabled within those router namespaces for deterministic lab routing. That is a lab choice, not a production anti-spoofing policy. No firewall, authentication or confidentiality service is modelled.

The supervising process builds the topology, runs all acceptance checks, records commands and output, and removes only the namespaces it created. Production would require separate management, access control, logging, persistence, monitoring and recovery; they are not supplied by this topology.

## LLD: interfaces and addresses

| Node | Interface | Address | Peer |
|---|---|---|---|
| HL | eth0 | 10.79.10.10/24 | RL lan |
| RL | lan | 10.79.10.1/24 | HL eth0 |
| RL | wan-a | 10.79.0.1/30 | RM wan-a |
| RM | wan-a | 10.79.0.2/30 | RL wan-a |
| RL | wan-b | 10.79.0.5/30 | RM wan-b |
| RM | wan-b | 10.79.0.6/30 | RL wan-b |
| RM | lan | 10.79.20.1/24 | HM eth0 |
| HM | eth0 | 10.79.20.10/24 | RM lan |

HL default: 10.79.10.1; HM default: 10.79.20.1. RL route to 10.79.20.0/24: via 10.79.0.2 on wan-a metric 100, via 10.79.0.6 on wan-b metric 200. RM route to 10.79.10.0/24: via 10.79.0.1 on wan-a metric 100, via 10.79.0.5 on wan-b metric 200. Routers have no default. All addresses are RFC 1918 private space, used solely inside this isolated lab. Check for conflicts before adapting any example to a connected environment.

Exact commands, sysctl settings and route-reconciliation logic are in `design_case.py`; generated evidence includes interface and route inventories. Names use a fresh `rtn79-<random>-<role>` prefix to avoid touching existing namespaces. No persistent daemon is installed. Tested environment: WSL2 Linux 6.18.33.2-microsoft-standard-WSL2, Python 3.14.4, iproute2 6.19.0, iputils ping as recorded in the execution JSON. This is Linux kernel forwarding, **not Containerlab, vendor NOS, physical router or carrier testing**.

## Run, inspect and recover

Read the script first. With no flag it does nothing and prints NOT_RUN:

```sh
python3 design_case.py
sudo python3 -B design_case.py --run > acceptance.json
```

T0 builds only the four namespaces and internal veth links, records addresses/routes and rejects missing commands or errors. T1 checks both normal route choices and bidirectional probes. T2 disables RL wan-a, checks backup routing/probes, then restores the interface **and both route sets**. T3 repeats for wan-b; wan-a remains preferred. The boundary test disables both transits and expects ping failure. T4 restores both, reapplies routes and confirms reachability. T5 removes owned namespaces and verifies their absence. JSON `status: PASSED` requires all 31 assertions and cleanup.

The first exploratory run failed the return-to-primary check: Linux had removed a static route when its device was administratively disabled. The final procedure now explicitly reconciles routes on restoration. Interface-up alone is not a sufficient rollback. The failed run and successful correction are retained with the book's review evidence.

Stop on any failed command, wrong route, unexpected address or probe result; investigate the retained report rather than extending the test to a real interface. `finally` cleanup handles ordinary errors but cannot guarantee cleanup after SIGKILL or host failure. If interrupted, use the recorded exact namespace names, inspect `ip netns list`, and remove **only that run's names**. Never use a blanket namespace deletion command. No production device configuration is applied or restored.

## ADR-079-01 (teaching example, revision 1)

- **Status:** selected for isolated Linux lab; no production approval.
- **Context:** R1–R4 require a buildable, observable example of single transit administrative failure; no silent-failure or router-redundancy requirement.
- **Decision:** option B with explicit link-down route behaviour and route reapplication during recovery.
- **Alternatives:** A violates R2. C remains a plausible extension requiring its own implementation and evidence. D adds unneeded cost/dependency under the stated assumptions.
- **Consequences:** simple inspection and reproduction; one router per site remains a single failure point, and static routes do not detect remote blackholes. Recovery is a procedure, not automatic reconciliation.
- **Evidence:** 31 acceptance assertions and namespace cleanup in the recorded Linux pass. The two fault-test completion durations are about 0.43 s, which do not measure outage duration.
- **Revisit:** new faults/services, unsupported kernel behaviour, skill/effort changes, changed endpoints or any acceptance failure. The service owner approves changed requirements; the implementer stops if assumptions differ.
