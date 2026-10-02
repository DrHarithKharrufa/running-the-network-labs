# Lab 21 — BGP transport, routes and forwarding

This IPv4 exercise has five internal routers, three external peers and explicit
policy. It is a reduced Kestrel control/forwarding exercise, not a complete ISP
network. Actual FRR/Linux evidence is recorded in VALIDATION.md; Containerlab
and the image build remain a separate, unexecuted adapter on the review host.

Use an isolated disposable environment. The selected package is Ubuntu 26.04
frr=10.5.1-1ubuntu4.1. These configurations have no transport authentication;
they teach routing mechanics, not a production control-plane security profile.
The short 3/9-second timers are also lab settings. Chapter 32 covers protection.
All example ASNs are documentation ASNs; service space is documentation or
benchmarking space. Do not connect this lab to an external routing domain.

## Inventory

| Router | Role | AS | Loopback |
|---|---|---|---|
| lon-p-01 | core / RR1 | 64500 | 10.255.0.11/32 |
| man-p-01 | core / RR2 | 64500 | 10.255.0.12/32 |
| lon-pr-01 | transit A border / client | 64500 | 10.255.0.21/32 |
| man-pr-01 | transit B border / client | 64500 | 10.255.0.22/32 |
| lon-pe-01 | customer border / client | 64500 | 10.255.0.23/32 |
| transit-a | external peer | 64496 | 10.96.0.1/32 |
| transit-b | external peer | 64497 | 10.97.0.1/32 |
| cust-a | external peer | 64501 | 10.101.0.1/32 |

| Endpoint A | Endpoint B | IPv4 A/B, each /31 |
|---|---|---|
| lon-p-01 eth1 | man-p-01 eth1 | 10.254.0.0 / .1 |
| lon-pr-01 eth1 | lon-p-01 eth2 | 10.254.1.0 / .1 |
| man-pr-01 eth1 | man-p-01 eth2 | 10.254.1.2 / .3 |
| lon-pe-01 eth1 | lon-p-01 eth3 | 10.254.1.4 / .5 |
| lon-pr-01 eth2 | transit-a eth1 | 192.0.2.0 / .1 |
| man-pr-01 eth2 | transit-b eth1 | 192.0.2.2 / .3 |
| lon-pe-01 eth2 | cust-a eth1 | 192.0.2.4 / .5 |

Only the four internal links and five internal loopbacks participate in L2
IS-IS. This underlay is a tree: two route-reflector sessions do not create
physical path redundancy. In particular, losing a client's only access link
isolates it from both reflectors. External link prefixes are intentionally
absent from the IGP and there is no default route concealing that absence.

| Origin | Advertised prefix | Actual responding address |
|---|---|---|
| transit-a | 198.18.0.0/24 | 198.18.0.1/32 on lo |
| transit-b | 198.19.0.0/24 | 198.19.0.1/32 on lo |
| cust-a | 203.0.113.0/24 | 203.0.113.1/32 on lo |

Each origin has an exact discard route for its advertised /24 and a connected
responding /32. Addresses elsewhere in the /24 are discarded, not hosts. The
configured `network` statement requires the exact RIB prefix. Customer routes
go to both transit peers; transit routes go to the customer. Exact-prefix
import/export lists prevent this topology from providing transit between the
two providers. There is no unrestricted permit-any starting state.

## Start and establish the underlay

From this directory, on a suitable Docker/Containerlab host:

```bash
docker build -f ../lab18/Dockerfile.frr -t netbook-frr:10.5.1 ../lab18
sudo containerlab deploy -t bgp.clab.yml
bash start.sh
v() { local n="$1"; shift; docker exec "clab-lab21-$n" vtysh "$@"; }
ipn() { local n="$1"; shift; docker exec "clab-lab21-$n" ip "$@"; }
v lon-pr-01 -c 'show isis neighbor'
docker exec clab-lab21-lon-pr-01 ping -c 5 -I 10.255.0.21 10.255.0.22
```

The start script loads `configs/` (underlay only). Confirm all four physical
IGP adjacencies, eight directed Up records, and source-specific reachability
among the five internal loopbacks. Save versions and effective configuration.
Wait for required routes; a fixed delay is not proof of convergence.

## 21.1 Full mesh and next-hop fault

Build the BGP configuration yourself from the address/policy contract, or load
the complete reference answer:

```bash
bash apply-phase.sh mesh
```

`mesh/` contains complete BGP and policy files for both sides of every session.
The phase loader replaces each BGP process configuration; it disrupts BGP
sessions and is suitable only for this disposable exercise. It leaves IS-IS
running. Do not present this reset as a hitless production migration method.

Expect ten internal sessions and three external sessions: 13 unique sessions,
or 26 Established records counted at both ends. On all five internal routers,
check all three service prefixes, their next hops and selected/installed state:

```bash
v lon-pe-01 -c 'show bgp ipv4 unicast summary'
v lon-pe-01 -c 'show bgp ipv4 unicast 198.18.0.0/24'
v lon-pe-01 -c 'show bgp nexthop'
v lon-pe-01 -c 'show ip route 198.18.0.0/24'
v lon-pr-01 -c 'show bgp ipv4 unicast neighbors 192.0.2.1 routes'
v lon-pr-01 -c 'show bgp ipv4 unicast neighbors 192.0.2.1 advertised-routes'
docker exec clab-lab21-cust-a ping -c 5 -I 203.0.113.1 198.18.0.1
docker exec clab-lab21-cust-a ping -c 5 -I 203.0.113.1 198.19.0.1
```

Those pings test requests and return traffic across the service path. Also
confirm transit A is not advertised transit B's prefix and vice versa.

Remove next-hop-self only on London's internal advertisements:

```bash
for peer in 10.255.0.11 10.255.0.12 10.255.0.22 10.255.0.23; do
  v lon-pr-01 -c 'configure terminal' -c 'router bgp 64500' \
    -c 'address-family ipv4 unicast' -c "no neighbor $peer next-hop-self" -c end
done
v lon-pr-01 -c 'clear bgp ipv4 unicast * soft out'
```

Inspect the path for 198.18.0.0/24 on lon-pe-01. It now carries external next
hop 192.0.2.1, which is not resolvable in this internal context. Record the
actual validity/selection flags, absent service route and failed service
probe while all 26 session records remain Established. An Established session
did not guarantee an eligible route. The supplied lab uses no default route
and no external-subnet IGP advertisement, so neither masks the intended fault.

Restore by repeating the loop with `neighbor $peer next-hop-self` (without
`no`), then the same soft-out refresh. Confirm selected path, reachable
10.255.0.21 next hop and both service probes. Do not stop at restored TCP state.

## 21.2 Reflection and explicit client/non-client observations

```bash
bash apply-phase.sh reflectors
```

The two core routers reflect to all three border clients and peer with each
other as non-clients. Their cluster IDs are 10.255.0.11 and10.255.0.12. There
are six client sessions plus one inter-reflector session:seven internal and
three external, or 20 directed Established records. Borders still set their
own reachable next hop; the reflectors do not turn themselves into arbitrary
service next hops. Verify originator/cluster attributes and both service probes.

Disable only one client-to-reflector session:

```bash
v lon-pe-01 -c 'configure terminal' -c 'router bgp 64500' -c 'neighbor 10.255.0.11 shutdown' -c end
```

Expect 18 directed Established records and working services via the remaining
control-plane session. Restore with `no neighbor 10.255.0.11 shutdown`, then
verify 20 and service again. This tests a session failure with a connected
underlay; it does not demonstrate surviving the client's only physical link.

For a controlled reflection-rule test, add two distinct test prefixes. Do not
advertise the underlay next-hop address itself as the test NLRI: that confounds
reflection with next-hop eligibility/recursive resolution.

```bash
ipn lon-pe-01 address add 198.18.100.23/32 dev lo
ipn man-p-01 address add 198.18.100.12/32 dev lo
v lon-pe-01 -c 'configure terminal' -c 'router bgp 64500' -c 'address-family ipv4 unicast' -c 'network 198.18.100.23/32' -c end
v man-p-01 -c 'configure terminal' -c 'router bgp 64500' -c 'address-family ipv4 unicast' -c 'network 198.18.100.12/32' -c end
v lon-p-01 -c 'configure terminal' -c 'router bgp 64500' -c 'address-family ipv4 unicast' -c 'no neighbor 10.255.0.22 route-reflector-client' -c end
v man-pr-01 -c 'configure terminal' -c 'router bgp 64500' -c 'neighbor 10.255.0.12 shutdown' -c end
v lon-p-01 -c 'clear bgp ipv4 unicast * soft out'
```

Manchester's border is temporarily an ordinary non-client of RR1 with its
other RR session disabled. Wait for eligible selected paths on RR1 before
checking advertisements. RR1 should advertise the client-originated .23 test
prefix to that non-client. It should not advertise the RR2-originated .12
test prefix, learned from a non-client, to another non-client. It should
advertise .12 to its remaining clients. Use these complete commands:

```bash
v lon-p-01 -c 'show bgp ipv4 unicast 198.18.100.12/32'
v lon-p-01 -c 'show bgp ipv4 unicast neighbors 10.255.0.22 advertised-routes'
v lon-p-01 -c 'show bgp ipv4 unicast neighbors 10.255.0.21 advertised-routes'
```

The output is a post-export route view, not an unfiltered received archive.
The exact-prefix eBGP filters prevent these internal test prefixes escaping
to the external lab peers. Restore all temporary state:

```bash
ipn lon-pe-01 address del 198.18.100.23/32 dev lo
ipn man-p-01 address del 198.18.100.12/32 dev lo
bash apply-phase.sh reflectors
```

Verify 20 Established records, no test advertisements and both services.

Finally demonstrate default eBGP policy rejection while transport stays up:

```bash
v lon-pr-01 -c 'configure terminal' -c 'router bgp 64500' -c 'address-family ipv4 unicast' -c 'no neighbor 192.0.2.1 route-map IMPORT in' -c end
v lon-pr-01 -c 'clear bgp ipv4 unicast 192.0.2.1 soft in'
v lon-pr-01 -c 'show bgp ipv4 unicast summary'
```

The configuration explicitly requires eBGP policy. Transit A's route should
be absent even though its session remains Established. Restore the IMPORT
attachment and repeat soft-in; verify the route and service return. The
negotiated refresh supports re-advertisement, but does not imply a retained
pre-policy route archive. The next chapter develops richer policy controls.

## 21.3 Independent selection experiment

The `selection/` directory has a separate four-router topology, so the
selection experiment does not disturb the core's IGP or reflection state.
Run it from that directory:

```bash
sudo containerlab deploy -t selection.clab.yml
bash start.sh
```

`select` is AS 64500. Each directly connected peer advertises 198.18.10.0/24;
their next hops are equally reachable and their initial MEDs are zero.
The receiver explicitly limits eBGP forwarding to one path for this
experiment. Without that setting, a best advertisement and a kernel flow's
chosen member can differ because multipath forwarding is active.

| Peer | Peer address | Receiver address | AS | Router ID |
|---|---|---|---|---|
| sel-a1 | 192.0.2.17/31 | 192.0.2.16/31 | 64496 | 10.96.0.3 |
| sel-a2 | 192.0.2.19/31 | 192.0.2.18/31 | 64496 | 10.96.0.1 |
| sel-b | 192.0.2.21/31 | 192.0.2.20/31 | 64497 | 10.96.0.2 |

All receiver neighbours start administratively shut. Define a helper:

```bash
s() { local n="$1"; shift; docker exec "clab-lab21-selection-$n" vtysh "$@"; }
```

1. With all MEDs zero, enable a1, wait for its path, then enable a2. Save
   `show bgp ipv4 unicast 198.18.10.0/24 json` and
   `show ip route 198.18.10.0/24`. Shut both, wait until neither path remains,
   and enable them in the reverse order. Keep b shut. The received candidates
   are otherwise equal; compare the already-selected-path decision.
2. Enable `bgp bestpath compare-routerid` on select and repeat both orders.
   a2 has the lower router ID. This changes one decision, not MED grouping.
3. Keep router-ID comparison enabled. Under route-map ONLY permit 10 on the
   peers, set MEDs a1=0, a2=100 and b=50 with `set metric VALUE`. Close all
   receiver neighbours before each case, then enable them one at a time in
   each of the six permutations. Wait for each added candidate, and save all
   attributes and the final route after the complete set is present.
4. Repeat step 3 with `bgp deterministic-med` on select, then separately with
   that disabled and `bgp always-compare-med` enabled. Record effective
   configuration and actual outcomes. Do not assume a setting was effective
   just because its command was accepted; see the observed limitation below.
5. Restore: disable both MED controls and router-ID comparison, set all peer
   MEDs to zero, close all neighbours and enable a1 then a2. Check the original
   selected-path behaviour. Do not leave temporary selection policy enabled.

For example, enable a1 with:

```bash
s select -c 'configure terminal' -c 'router bgp 64500' -c 'no neighbor 192.0.2.17 shutdown' -c end
```

Use `neighbor ADDRESS shutdown` to close it. The six orders are a1/a2/b,
a1/b/a2, a2/a1/b, a2/b/a1, b/a1/a2 and b/a2/a1. In the grouped decision model,
a1 wins its AS's MED comparison, then b wins against a1 by router ID because
the two remaining paths are from different ASes. Always-compare MED instead
compares the independent ASes' values and favours a1's zero. These different
intentions must not be described as equivalent knobs. Actual release-specific
observations and any disagreement with that model belong in the results.

JSON detail can mark a per-AS best path as well as the overall winner. Read
`bestpath.overall`, not merely the existence of a `bestpath` object. Save the
kernel next hop separately. VALIDATION.md records the reviewed package's
results and any remaining behavioural discrepancy.

## Finish and submit

Destroy only the topology named in each directory after restoring and saving
the evidence: `sudo containerlab destroy -t bgp.clab.yml` for the core, and
`sudo containerlab destroy -t selection.clab.yml` for selection.

Submit baseline/fault/recovery evidence, unique-session counts, exact-prefix
policy outcomes, received versus selected versus installed routes, the
reflection-rule observations and all selection cases. Explain why none of
these tests establishes IPv6, VPN-family, IXP route-server, ORR, add-path,
confederation, authentication, scale or commercial-NOS interoperability.

Read RFCs 4271,7606,4456,2918,8212,7911,9107 and the
[FRR 10.5 BGP manual](https://docs.frrouting.org/en/stable-10.5/bgp.html).
