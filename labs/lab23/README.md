# Lab 23: shared-service routes and the limits of route isolation

The Python model checks route membership. The Containerlab fixture proposes an FRR 10.2.1 implementation on a Linux host with VRF and MPLS support. **The model was run during editing; the container and packet tests were not run.** Expected results below are not measured output.

The baseline demonstrates IPv4 route distribution and ICMP reachability. It does not configure DNS, NTP, encryption or an application firewall. The security extension needs those additional controls before anyone can claim DNS/NTP-only access.

A separate [Linux VRF-lite exercise](linux/README.md) now has 35 local runtime
assertions, including real UDP/TCP DNS and UDP NTP, HTTP denial, indirect
tenant transit, one spoofed source, and fault/restoration. It uses static
cross-context routes on one router, without BGP, RD, RT or MPLS; it does not
validate this two-PE VPN fixture. The local kernel has VRF support but
`CONFIG_MPLS_ROUTING` is not set. Read the Linux record for the required
explicit route reconciliation after the service interface returns.

## Design

| Context | Client | Gateway | Export RT |
|---|---|---|---|
| CUST-A | 10.101.0.10/24 | 10.101.0.1 | 64500:1001 |
| CUST-B | 10.102.0.10/24 | 10.102.0.1 | 64500:1002 |
| CUST-C | 10.103.0.10/24 | 10.103.0.1 | 64500:1003 |
| SERVICES | 10.109.0.10/24 | 10.109.0.1 | 64500:9000 |

PE1 holds the tenants; PE2 holds SERVICES. Their link is 10.254.0.0/31 and loopbacks are 10.255.0.1 and .2. Each context exports only its listed /24. Tenants import their own RT plus 64500:9000; SERVICES imports all three tenant RTs.

The original draft assigned 10.0.0.10 to all tenants while expecting one service IP table to reach each independently. An RD distinguishes VPN routes but is absent from the server's ordinary reply packet. The revised baseline uses distinct prefixes; the overlap exercise below explains the limitation.

## Policy model

```bash
python3 policy_model.py --output model-results.json
```

The 18 assertions cover service imports, tenant route separation, exact-prefix export boundaries and overlapping return addresses. This model does not parse FRR configuration, select BGP paths, establish labels, enforce ports or simulate forwarding.

## Deploy on an isolated Linux lab host

Use Docker and Containerlab on a host with the required kernel facilities. Stop if any prerequisite or setup command fails.

```bash
sudo modprobe vrf
sudo modprobe mpls_router
sudo modprobe mpls_iptunnel
sudo containerlab deploy -t vrf.clab.yml
```

Record host/kernel/Containerlab versions and resolved image digests; release tags are not immutable digests. PE setup creates kernel VRFs and attachments, installs an unreachable default in each context, enables MPLS and reloads FRR after the objects exist. Inspect setup and FRR logs for rejected commands. The VRF unreachable default prevents a missing tenant route from falling through to the default routing context.

## Observe transport and service state

```bash
docker exec clab-lab23-pe1 ip -d link show type vrf
docker exec clab-lab23-pe2 ip -d link show type vrf
docker exec clab-lab23-pe1 vtysh -c 'show ip ospf neighbor'
docker exec clab-lab23-pe1 vtysh -c 'show mpls ldp neighbor'
docker exec clab-lab23-pe1 vtysh -c 'show bgp ipv4 vpn summary'
docker exec clab-lab23-pe1 vtysh -c 'show bgp ipv4 vpn'
docker exec clab-lab23-pe1 vtysh -c 'show ip route vrf CUST-A'
docker exec clab-lab23-pe2 vtysh -c 'show ip route vrf SERVICES'
docker exec clab-lab23-pe1 ip -f mpls route show
```

Wait for observed state, not a fixed sleep. CUST-A should have its connected /24, the service /24 and its kernel unreachable default, without other tenant /24s. SERVICES should contain all three distinct tenant prefixes. Compare VPN RIB, imported RIB, installed FIB and label resolution; a route visible in BGP may still be unusable.

## Allowed and denied packet matrix

```bash
docker exec clab-lab23-cust-a ping -c 3 -W 1 10.109.0.10
docker exec clab-lab23-cust-b ping -c 3 -W 1 10.109.0.10
docker exec clab-lab23-cust-c ping -c 3 -W 1 10.109.0.10
docker exec clab-lab23-services ping -c 3 -W 1 10.101.0.10
docker exec clab-lab23-services ping -c 3 -W 1 10.102.0.10
docker exec clab-lab23-services ping -c 3 -W 1 10.103.0.10
docker exec clab-lab23-cust-a ping -c 3 -W 1 10.102.0.10
docker exec clab-lab23-cust-a ping -c 3 -W 1 10.103.0.10
docker exec clab-lab23-cust-b ping -c 3 -W 1 10.101.0.10
docker exec clab-lab23-cust-b ping -c 3 -W 1 10.103.0.10
docker exec clab-lab23-cust-c ping -c 3 -W 1 10.101.0.10
docker exec clab-lab23-cust-c ping -c 3 -W 1 10.102.0.10
```

Expect the first six to succeed and the final six to fail. For negative tests, prove the destination is alive from SERVICES, inspect the source VRF lookup and capture the failure point. Record actual exit codes and packet counts. These tests do not establish every protocol, spoofed-source case or indirect path.

## Challenge and restore the service export filter

Inject a discard default in SERVICES and make static routes eligible for its BGP instance. The existing exact-prefix export guard should deny the default at VPN export.

```bash
docker exec clab-lab23-pe2 vtysh \
  -c 'configure terminal' \
  -c 'ip route 0.0.0.0/0 Null0 vrf SERVICES' \
  -c 'router bgp 64500 vrf SERVICES' \
  -c 'address-family ipv4 unicast' \
  -c 'redistribute static'
docker exec clab-lab23-pe2 vtysh -c 'show bgp vrf SERVICES ipv4 unicast'
docker exec clab-lab23-pe1 vtysh -c 'show bgp ipv4 vpn'
```

Now deliberately permit the exact default in the export prefix list:

```bash
docker exec clab-lab23-pe2 vtysh \
  -c 'configure terminal' \
  -c 'ip prefix-list SERVICES-EXPORT seq 20 permit 0.0.0.0/0'
```

Observe policy re-evaluation and the changed tenant route on the chosen image. The route leads to a **discard**, not the Internet. Compare before/fault/after RIB and FIB state; a successful CLI command alone does not prove re-advertisement. Restore the guard and remove the injection:

```bash
docker exec clab-lab23-pe2 vtysh \
  -c 'configure terminal' \
  -c 'no ip prefix-list SERVICES-EXPORT seq 20' \
  -c 'no ip route 0.0.0.0/0 Null0 vrf SERVICES' \
  -c 'router bgp 64500 vrf SERVICES' \
  -c 'address-family ipv4 unicast' \
  -c 'no redistribute static'
```

Verify the BGP default withdraws while the intentional kernel unreachable default remains. Redeploy the bound baseline if restoration is incomplete.

## Extensions and questions

1. Configure actual DNS/NTP services and enforce permitted ports, source validation and prevention of unintended tenant transit. Test allowed queries, other ports and a service host acting as a relay. RT membership alone is insufficient.
2. Import three RDs for the same 10.0.0.0/24 into one service context on paper. Explain its possible forwarding choices for 10.0.0.10 and why ECMP does not identify the intended tenant. Compare separate service contexts, translation, a suitable proxy and renumbering.
3. Repeat the complete packet matrix after a transport-link failure and recovery. Measure loss and restoration rather than inferring service health from adjacency state.

| Stage | Status during editing | Lab evidence required |
|---|---|---|
| Policy model | 18 assertions passed | model-results.json |
| Container deployment | Not run | versions, digests, setup/configuration logs |
| Transport/VPN state | Not run | adjacencies, RIB/FIB and labels |
| 12 packet cases | Not run | exit codes, packet counts and captures |
| Default fault/restoration | Not run | before/fault/after route state |
| DNS/NTP-only security | Exercise; not configured | application results and enforcement counters |
| Separate Linux VRF-lite construction | 35 assertions passed | linux/README.md; not VPN/MPLS evidence |

Reference: [FRR 10.2 VRF route leaking](https://docs.frrouting.org/en/stable-10.2/bgp.html#vrf-route-leaking). Documentation establishes command intent; execution establishes behaviour on a particular image and kernel.
