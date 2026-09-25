# Lab 24 — multicast state, delivery and recovery

Seven nodes: source—r1—r2—r3—rx1, rx2 attached to r2, and **rp attached as a
side branch to r2**. The RP is 10.255.0.4; it is not a transit node on either
source-to-receiver path. Inspect `multicast.clab.yml` for every address/link.
All router configurations use OSPF, IPv4 PIM, a static RP for 239/8, SSM for
232/8 and explicit `urib-only` lookup. LAN membership uses IGMPv3. This is an
isolated teaching topology, not a production allocation/security template.

## Reproduction and evidence boundary

The native Linux adapter executed the interface commands and these FRR
configurations using FRR 10.5.1-1ubuntu4.1. It used private process/mount
namespaces. Docker image building, Containerlab deployment and the container
startup scripts have **not** been executed. `VALIDATION.md` gives exact scope.
To evaluate that separate adapter on a suitable Docker/Containerlab host:

```bash
docker build -f ../lab18/Dockerfile.frr -t netbook-frr:10.5.1 ../lab18
sudo containerlab deploy -t multicast.clab.yml
bash start.sh
docker exec clab-lab24-r3 vtysh -c 'show ip route'
docker exec clab-lab24-r3 vtysh -c 'show ip pim neighbor'
docker exec clab-lab24-r1 ping -c 3 10.255.0.4
docker exec clab-lab24-r3 ping -c 3 10.1.0.10
```

The host kernel must support IPv4 multicast routing; check the daemon logs and
`show ip mroute`, not just container state. `start.sh` explicitly starts zebra,
mgmtd, staticd, ospfd and pimd, then loads the configuration. Do not rerun it
over live processes. The query interval is 10 **seconds**; maximum response
time is 10 **deciseconds**, or one second. Set the reduced maximum-response
value before reducing the query interval: the original order was rejected.

## ASM baseline

Start receivers before sending. Keep each receiver in a separate terminal so
its JSON sequence records remain available. Stop it with Ctrl-C when finished.

```bash
docker exec -i clab-lab24-rx1 python3 -u /lab/traffic.py recv 239.1.1.1 10.3.0.10 asm
docker exec -i clab-lab24-rx2 python3 -u /lab/traffic.py recv 239.1.1.1 10.4.0.10 asm
```

In another terminal, capture at the RP before starting a new source/group:

```bash
docker exec -i clab-lab24-rp tcpdump -n -vv -i eth1 pim
```

Send a warm-up burst, inspect membership/tree state, then a measured burst:

```bash
docker exec clab-lab24-source python3 /lab/traffic.py send 239.1.1.1 10.1.0.10 asm-warm 100
docker exec clab-lab24-r3 vtysh -c 'show ip igmp groups' -c 'show ip mroute' -c 'show ip pim upstream'
docker exec clab-lab24-source python3 /lab/traffic.py send 239.1.1.1 10.1.0.10 asm-baseline 100
```

The sender uses UDP port 5000, a 20 ms nominal interval, TTL 8 by default and
an explicit source/interface address. Count unique sequences per tag at each
receiver. Inspect Register messages and tree flags; an `(S,G)` entry alone
does not prove the last-hop router switched away from the shared tree. The
local run captured Registers but did not establish that SPT switchover.

## Isolate RP dependency, source filtering and TTL

```bash
docker exec clab-lab24-rp ip link set eth1 down
docker exec clab-lab24-r3 ping -c 3 10.1.0.10
```

Leave the original streams as observations, then start **new** rx1 membership
for ASM `239.1.1.2` and SSM `232.1.1.1`; add rx2 to the SSM channel as well:

```bash
docker exec -i clab-lab24-rx1 python3 -u /lab/traffic.py recv 239.1.1.2 10.3.0.10 asm
docker exec -i clab-lab24-rx1 python3 -u /lab/traffic.py recv 232.1.1.1 10.3.0.10 10.1.0.10
docker exec -i clab-lab24-rx2 python3 -u /lab/traffic.py recv 232.1.1.1 10.4.0.10 10.1.0.10
```

Each command occupies a terminal. Allow membership/join state to form and
send separate tagged bursts to both groups. The local test received no new
ASM packets and 100/100 measured SSM packets at each receiver. Then send SSM
from `10.1.0.11`, the source host's second configured address: neither receiver
requested it. Send again from `.10` with the optional final TTL argument `1`:
neither receiver should receive across the routers. Restore TTL 8 and verify
delivery. These are distinct faults; an SSM source filter is not identity
authentication or a comprehensive spoofing defence.

## Wrong RPF direction and restoration

With SSM working, record the effective lookup, introduce one host route on r3,
and compare rx1 with the unaffected rx2:

```bash
docker exec clab-lab24-r3 vtysh -c 'show ip pim nexthop-lookup 10.1.0.10 232.1.1.1'
docker exec clab-lab24-r3 vtysh -c 'configure terminal' -c 'ip route 10.1.0.10/32 10.3.0.10' -c end
docker exec clab-lab24-r3 vtysh -c 'show ip pim nexthop-lookup 10.1.0.10 232.1.1.1' -c 'show ip pim upstream' -c 'show ip mroute'
docker exec clab-lab24-source python3 /lab/traffic.py send 232.1.1.1 10.1.0.10 rpf-fault 100
docker exec clab-lab24-r3 vtysh -c 'configure terminal' -c 'no ip route 10.1.0.10/32 10.3.0.10' -c end
docker exec clab-lab24-rp ip link set eth1 up
```

The fault selects r3 eth2 (receiver side) instead of eth1 (source side).
After restoring, verify OSPF/RP reachability, send new warm-up/measured bursts
to both SSM receivers and the previously failed ASM group, and retain their
sequence counts. FRR `show ip rpf ADDRESS` inspects MRIB independently of the
configured lookup mode; it is not equivalent to `nexthop-lookup` here.

## Separate snooping exercise and questions

See `snooping/README.md`. It has no PIM routers or Containerlab validation.

1. Explain why a multicast MAC alias can cause unwanted frame delivery but
   need not cause application delivery. Can aliased groups coexist?
2. Which evidence distinguishes RPF failure, TTL exhaustion, source filtering,
   aged snooping membership and an application socket problem?
3. Why does losing r2 fail to isolate RP dependence? Which existing/new
   source/group/receiver cases belong in a redundant-RP acceptance test?
4. Which state and receiver observations support an SPT-switch claim? What
   additional experiments would test querier election or MLDv2?

Cleanup the disposable Containerlab only after saving evidence:
`sudo containerlab destroy -t multicast.clab.yml`.
