# Linux VRF-lite and shared-service enforcement

This is a separate exercise from the two-PE VPN fixture in the parent
directory. One Linux router has four kernel VRFs. Explicit static routes
cross selected contexts. **No BGP, RD, RT, label, MPLS or commercial router is
executed by this exercise.** It demonstrates forwarding and security
properties, not VPN route distribution.

`topology.json` lists every node, link and initial command. PE interface eth1
belongs to CUST-A/table 1001, eth2 to CUST-B/1002, eth3 to CUST-C/1003 and
eth4 to SERVICES/9000. Leaf nodes t23-a/b/c/s use 10.101/102/103/109.0.10/24
respectively, with .1 gateways. Each VRF has an unreachable default. The
tenants have only their connected prefix and a static 10.109.0.0/24 route
out eth4; SERVICES has return routes out eth1/2/3. Those cross-context
routes are deliberate Linux FIB configuration, not inferred RT membership.

The local runner created `nbk-` network namespaces for these nodes and veth
pairs for the declared links, ran the listed commands there, then deleted
only its own namespaces and processes. Every command/result is preserved in
the book's runtime evidence. To reproduce elsewhere, build the same isolated
objects from the JSON; never run `enforce.sh` in the host network namespace.
It adds firewall rules to an initially empty disposable PE ruleset.

## Sequence and observations

1. Verify four VRFs, l3mdev rules and all four tables. A higher-priority policy
   rule can precede the VRF lookup; inspect the complete `ip rule` list.
2. Probe all three tenants to 10.109.0.10, and service-to-tenant return paths.
   Probe all six directed tenant-to-tenant pairs. The former six pass; the
   latter six fail with destinations known alive from SERVICES.
3. Start a real HTTP listener at 10.109.0.10:8080. It is reachable from a
   tenant before traffic policy. Route membership does not restrict ports.
4. In this isolated exercise, enable IPv4 forwarding on the service host.
   Add a lower-metric default in both tables 1001 and 1002 via 10.109.0.10,
   dev eth4, `onlink`. A-to-B ping succeeds through the service host even
   though neither tenant has imported the other's specific route. Both
   defaults are needed for the demonstrated forward and return paths.
5. Remove those defaults. Direct separation returns. The high-metric
   unreachable defaults remain.
6. Run dnsmasq 2.92 for svc.lab = 10.109.0.10 on UDP/TCP 53, with no upstream
   resolver or host-file use. Run chronyd 4.8 with `-x`, `local stratum 10`,
   `allow` for each tenant /24, `bindaddress 10.109.0.10`, `cmdport 0`, and a
   private PID file. This is an isolated NTP response source, not accurate UTC
   or a host clock-discipline test.
7. Apply `enforce.sh` inside the PE. It drops source addresses inconsistent
   with each tenant attachment, allows established/related replies, allows
   tenant DNS over UDP/TCP and NTP over UDP to the exact service address, and
   drops other forwarded traffic. Router-local INPUT policy is outside scope.
8. Run `python3 probe.py dns`, `dns-tcp` and `ntp` inside each tenant namespace.
   The probes check DNS response identity/status/A data and NTP server mode,
   stratum and echoed originate timestamp. All nine succeed. HTTP fails from
   each tenant while a local service-host HTTP request still succeeds.
9. Reintroduce the two unsafe defaults: A-to-B ping now fails. Remove them.
   Add 10.102.0.99/32 on A and run `probe.py dns 10.102.0.99`; its failure plus
   the physical eth1 source-validation DROP counter proves that this forged
   packet reached the intended control. Remove the address.
10. Delete the SERVICES return route to 10.101.0.0/24 and observe failed DNS
    from A. Restore it and prove a successful reply.
11. Bring PE eth4 down and up. In this kernel, the cross-context service
    routes disappear from the tenant tables and do not return automatically.
    Restore them explicitly, then verify DNS. Interface Up alone is insufficient.

Representative PE commands for the deliberately unsafe default test are:

```sh
ip route add table 1001 default via 10.109.0.10 dev eth4 onlink metric 10
ip route add table 1002 default via 10.109.0.10 dev eth4 onlink metric 10
# Restore both exceptions after observing the test:
ip route del table 1001 default via 10.109.0.10 dev eth4 metric 10
ip route del table 1002 default via 10.109.0.10 dev eth4 metric 10
```

The demonstrated post-link-recovery reconciliation is:

```sh
ip route replace table 1001 10.109.0.0/24 dev eth4
ip route replace table 1002 10.109.0.0/24 dev eth4
ip route replace table 1003 10.109.0.0/24 dev eth4
```

Persisting intended configuration and reconciling it after interface events
is a separate operational requirement. This manual lab does not supply a
production route manager.

## Execution record

Run `20260917T000447Z`: 35 assertions passed on Linux
6.18.33.2-microsoft-standard-WSL2, iproute2 6.19.0, iptables 1.8.11,
dnsmasq 2.92 and chrony 4.8. Evidence includes the spoof DROP counter,
route tables showing the missing cross-context routes after interface Up,
and successful DNS after explicit reconciliation. Earlier run
`20260917T000326Z` failed at the assumption of automatic route recovery and
is retained. Kernel probe `20260916T235935Z` confirms VRF creation but
`CONFIG_MPLS_ROUTING` is not set; the parent MPLS exercise remains unexecuted.

The allowed/denied tests do not prove arbitrary application isolation,
IPv6 behaviour, resistance to a compromised PE, or every attack a permitted
DNS/NTP service might facilitate. A compromised shared application still
requires application and host controls. The source-validation test covers
one forged packet; it is not a load or exhaustive spoofing test.
