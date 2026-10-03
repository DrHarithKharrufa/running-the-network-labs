# Workbook baselines and platform boundaries

Edition RTN-2026-10-04.

The current workbook contains 120 tasks across ten parts, with six vendor
outcomes per task. Its 714 READ panels establish returned documentation syntax;
six NO_PANEL results preserve unresolved source qualification. READ is not a
device execution claim. Each task's context and acceptance experiment define
its preparation. Additional core/EVPN preparation contracts are in
`../workbook-fixtures/README.md`; bounded stimuli and offline automation are in
`../workbook-automation/`. Do not concatenate different nodes or task fragments
into one router session.

## Historical IGP/BGP execution baselines

The table below belongs to the retained RTN-2026-10-01 historical sample,
identified as H-IGP/H-BGP in the current workbook. It does not certify current
tasks with the same original numbers. Complete FRR starting configurations and
addressing are in `harness/topologies/`. Preserve the historical records and
their exact image/version before attempting a new qualification.

| Task family | FRR baseline / node |
| --- | --- |
| IGP-01 router IDs | `igp-ospf-areas.yml`, r1 and r2 explicitly |
| IGP-02 dual stack | `ospf-p2p.yml` plus the addressing commands in `workbook_checks.py`; the original topology has a different IPv4 /30, so the extension explicitly adds the /31 |
| IGP-03/04 static | `igp-static-bfd.yml`, r1; reverse route on r2 and transit on r3 |
| IGP-05/06 OSPF | `ospf-p2p.yml`, r1 with r2 peer |
| IGP-07 cost / 08 summary | `igp-ospf-areas.yml`, r2 for cost/range; r1 for received routes |
| IGP-09 authentication | `igp-ospf-areas.yml`, r1/r2 eth1; deliberate wrong key on r2 |
| IGP-11/12 IS-IS | `igp-isis-flat.yml` / `igp-isis.yml`; nodes named per panel |
| IGP-13 BFD client | static triangle, then `workbook_checks.py` binds both primary routes |
| IGP-14 passive | `igp-ospf-areas.yml`, r1 loopback |
| BGP-01/02 | `bgp-ebgp-ibgp.yml` / `bgp-next-hop-self.yml`; explicit external prefix policies retained |

FRR target is 10.2.1, image digest recorded in each fresh result. The harness enables IPv4 forwarding inside each router namespace. It attaches only its own virtual links. The new run evidence and initial failures are separate from the seven historical records in `evidence/`.

## Vendor translations

Use an isolated two-router lab. For the OSPF translations, assign r1 `10.0.12.0/31`, r2 `10.0.12.1/31`, loopbacks `10.255.0.1/32` and `.2/32`, and router IDs matching those loopbacks. Attach the transit interface to area 0 on both routers and advertise the loopback. Check address-family support, interface MTU, network type, timers and authentication. The FRR `ospf-p2p.yml` uses a /30 instead; do not mix that address plan into this translation baseline.

| Platform / source scope | r1 interface / configuration context | Verify, then adapt the peer |
| --- | --- | --- |
| Cisco IOS XE; OSPF references linked in workbook | `GigabitEthernet0/0/0`, `Loopback0`; configure IPs, `no shutdown`, OSPF process 1 and router ID before panel commands | `show ip interface brief`, `show ip ospf neighbor`, `show ip route 10.255.0.2`; licensing/hardware/release acceptance pending |
| Arista EOS 4.36.2F documentation | `Ethernet1`, `Loopback0`; routed port (`no switchport` where applicable), IPs, `ip routing`, OSPF process 1 | `show ip ospf neighbor`, `show ip route 10.255.0.2`; verify actual platform's defaults |
| Junos OSPF guide | `ge-0/0/0.0`, `lo0.0`, family inet addresses; router ID under routing-options | `show ospf neighbor`, `show route 10.255.0.2/32`; commit candidate and verify rollback procedure |
| Nokia SR Linux 24.10 | `ethernet-1/2.0`, default network-instance; complete candidate files adjacent | `show network-instance default protocols ospf neighbor`; inspect `info from state` under the actual instance and route table; on-box acceptance pending |
| VyOS rolling documentation | `eth1`, `lo`; address configuration, `set protocols ospf parameters router-id`, then interface area | `show ip ospf neighbor`, `show ip route`; commit/save semantics need the selected release |

For BGP, r1/r2 are AS64500, r3 AS64510. r1 external `10.0.13.0/31` peers with r3 `.1`; r1/r2 loopbacks have independent OSPF reachability. r2 originates `198.51.100.0/24`, r3 `203.0.113.1/32`. Implement the same explicit import/export intent on the chosen vendor before testing. The EOS/VyOS session panels are documented fragments, not complete alternative topologies or executed commercial NOS tests. Huawei is outside this workbook sample; the main book retains its identified panels.

Use the printed evidence register's direct documentation links. Preserve the exact release, full configuration, rejected commands, observations and recovery, rather than giving the READ panel a RUN label merely because FRR accepted a translation.


The SR Linux candidates include lo0.0 and advertise each unique /32 through OSPF.
Both transit and loopback subinterfaces must belong to the default network instance.
These are adapted documented examples, not SR Linux execution records:
[24.10 OSPF](https://documentation.nokia.com/srlinux/24-10/books/routing-protocols/ospf.html)
and [24.10 loopback membership](https://documentation.nokia.com/srlinux/24-10/books/routing-protocols/segment-routing-bgp-lu.html).
Inspect candidate differences and validation errors before committing in an isolated
lab. Verify neighbours, remote /32 routes and sourced probes on your release.
