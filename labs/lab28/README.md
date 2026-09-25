# Lab 28 — SRv6 instructions, service context and packet size

Four Linux/FRR routers form r1–r2–r3–r4–r1. Each chain link costs 10 in
both directions; the direct r1–r4 link costs 50. IS-IS carries IPv6 locator
reachability. Static Linux routes supply SRv6 behaviours and service mapping.
There is **no BGP service advertisement, RD/RT import policy or controller**.
Read VALIDATION.md for the exact executed subset. Use a disposable lab.

Blue/table 100 and red/table 200 attach to r1/r4. Both use overlapping
customer addresses: left host 10.28.1.10/24, right host 10.28.2.10/24, local
gateway .1. Namespaces and VRFs distinguish them; customer prefixes stay out
of the IGP. Capturing the attachment is essential when addresses overlap.

## Allocation and startup

| Owner | Locator | SID function field | Behaviour |
|---|---|---|---|
| r1 | 2001:db8:4500:1::/64 | 400 / 401 | End.DT4 blue / red |
| r2 | 2001:db8:4500:2::/64 | 100 | End |
| r3 | 2001:db8:4500:3::/64 | 200 | End.X to r4 |
| r4 | 2001:db8:4500:4::/64 | 400 / 401 | End.DT4 blue / red |

SIDs use a 64-bit locator, 16-bit function and 48 zero argument bits: for
example r4 blue is `2001:db8:4500:4:400::`. Router loopbacks end in `::1`.
Core link /127s use fourth hextets ff12, ff23, ff34 and ff14. The topology
has the exact endpoint map. The former four purported /48 locators collapsed
to one prefix; the distinct /64s above correct that error.

The Linux host needs IPv6 segment-routing lightweight tunnels, the required
End/End.X/End.DT4 behaviours and VRFs. A container shares its host kernel;
installing FRR does not add missing kernel behaviour. The topology sets
forwarding, intended interface SR processing, a tunnel source and VRF strict
mode. Each customer table has an unreachable default to prevent unintended
fall-through. From this directory:

```sh
docker build -t netbook-frr:10.5.1 -f ../lab18/Dockerfile.frr ../lab18
sudo modprobe vrf
# Verify the host kernel supports the required SRv6 behaviours.
sudo containerlab deploy -t srv6.clab.yml
bash start.sh
```

Startup explicitly launches zebra, mgmtd, staticd and isisd, and loads each
baseline. Check eight directed Up adjacency rows, installed IPv6 routes and
both loopback directions. Startup alone is not convergence:

```sh
docker exec clab-lab28-r1 vtysh -c 'show isis neighbor detail'
docker exec clab-lab28-r1 ip -6 route show
docker exec clab-lab28-r1 ping -6 -I 2001:db8:4500:1::1 -c 3 2001:db8:4500:4::1
docker exec clab-lab28-r4 ping -6 -I 2001:db8:4500:4::1 -c 3 2001:db8:4500:1::1
```

Customer traffic should fail before service mapping. Resolve absent underlay
routes before proceeding; a startup timeout is not evidence of an SRv6 fault.

## Install and trace

In a fresh, converged topology:

```sh
for n in r1 r2 r3 r4; do
  docker exec "clab-lab28-$n" python3 /lab/configure-srv6.py "$n"
done
docker exec clab-lab28-blue-1 ping -c 3 10.28.2.10
docker exec clab-lab28-red-1 ping -c 3 10.28.2.10
docker exec clab-lab28-blue-2 ping -c 3 10.28.1.10
docker exec clab-lab28-red-2 ping -c 3 10.28.1.10
```

The helper prints commands and stops on an error. Its `add` operations refuse
to overwrite existing entries. Inspect partial installation or recreate the
disposable topology before retrying. It installs outer IPv6 reachability in
each customer table as well as inner IPv4 encapsulation routes.

The forward list is r2 End, r3 End.X, r4's customer-specific End.DT4. The
reverse list contains r1's customer-specific End.DT4. End.X explicitly selects
r4 at 2001:db8:4500:ff34::1. Save these views on each router:

```sh
ip -6 -s -d route show table all
ip -4 -s -d route show table all
ip -6 rule show
```

Capture r1 eth1, r2 eth2 and r3 eth2 while probing blue. Read outer source,
destination, hop limit and payload length; SRH type, length, Last Entry and
Segments Left; stored SID order; and inner IPv4 length/addresses. Full
three-SID encapsulation adds 96 bytes. Segments Left progresses 2→1→0 at
these links, with SRH still present before decapsulation. The wire list stores
the final SID at index 0; the route command lists processing order.

## Fault, discriminate and restore

Remove only r4's blue SID, test blue failure and continuing red delivery,
then restore the exact context:

```sh
docker exec clab-lab28-r4 ip -6 route del 2001:db8:4500:4:400::/128
# Observe both services before restoring:
docker exec clab-lab28-r4 ip -6 route add 2001:db8:4500:4:400::/128 encap seg6local action End.DT4 vrftable 100 count dev blue
```

Separately remove r2's End route. The original list loses service. Replace
r1's list with r3 End.X plus r4's service SID: r2 can carry ordinary IPv6
transit without executing the missing End instruction. Restore r2 with:

```sh
docker exec clab-lab28-r2 ip -6 route add 2001:db8:4500:2:100::/128 encap seg6local action End count dev eth2
```

In the recorded kernel, ingress `seg6_enabled=0` alone did **not** disable
the installed seg6local End route. Do not rely on this knob as a SID access
boundary. Restore intended settings and apply real ingress filtering/policy.

For a mapping fault, change r1 blue's final SID to r4 red (`...:4:401::`).
Capture both right-hand customer attachments. A packet entering red despite
blue ingress demonstrates incorrect context selection. Ping may still fail
because the reply follows red's reverse mapping to the other left-hand host;
that failure is not proof of isolation. Restore blue's final SID and verify
both the receiving attachment and successful delivery.

This healthy command is run **inside r1**:

```sh
ip route replace 10.28.2.0/24 vrf blue encap seg6 mode encap segs 2001:db8:4500:2:100::,2001:db8:4500:3:200::,2001:db8:4500:4:400:: dev eth1
```

## Encapsulation and MTU

For the same three SIDs, change `mode encap` to `mode encap.red` and capture:
two stored SIDs plus outer IPv6/SRH base add 80 bytes. A reduced list
containing only r4's blue SID can omit SRH and add 40 bytes. Verify bytes
and behaviour rather than inferring them from the mode name. Restore full
three-SID mode before the following boundary test.

First confirm `ping -M do -s 1472` from blue-1 passes with core MTU 2000.
Set **r1 eth1 and r2 eth1 together** to MTU 1500, wait for routing and verify
the intended first-segment path. Echo data 1376 gives 1404-byte inner IPv4;
1377 gives 1405. Probe both and a small packet. Restore both ends to 2000,
confirm the path and repeat the full-size probe. Retain ICMP messages and
captures because cached PMTU can affect later probes.

## A separate NEXT-CSID phase

Use block `2001:db8:4500:0::/64`, 16-bit node/function values and four slots.
The three instructions are 0102 at r2, 0103 at r3, then 0400 (blue End.DT4)
at r4. The remaining slot is zero. This is an explicit 64/16 construction,
not an assumption that the preceding /64 router locators are compressible.

Run each group **inside the named router**, after the previous full-SID phase:

```sh
# r1: transport to each compressed instruction prefix
for s in 102 103 400; do
  ip -6 route add "2001:db8:4500:0:$s::/80" via 2001:db8:4500:ff12::1 dev eth1
done
# r2: its own instruction shifts the destination; later ones use ordinary routing
ip -6 route add 2001:db8:4500:0:102::/80 encap seg6local action End flavors next-csid lblen 64 nflen 16 count dev eth2
for s in 103 400; do
  ip -6 route add "2001:db8:4500:0:$s::/80" via 2001:db8:4500:ff23::1 dev eth2
done
# r3
ip -6 route add 2001:db8:4500:0:103::/80 encap seg6local action End flavors next-csid lblen 64 nflen 16 count dev eth2
ip -6 route add 2001:db8:4500:0:400::/80 via 2001:db8:4500:ff34::1 dev eth2
# r4: the shifted terminal destination selects the blue service
ip -6 route add 2001:db8:4500:0:400::/128 encap seg6local action End.DT4 vrftable 100 count dev blue
# r1: impose one container using reduced encapsulation
ip route replace 10.28.2.0/24 vrf blue encap seg6 mode encap.red segs 2001:db8:4500:0:102:103:400:0 dev eth1
```

Capture r1 eth1, r2 eth2 and r3 eth2. Expected destinations are respectively
`2001:db8:4500:0:102:103:400:0`, `2001:db8:4500:0:103:400::` and
`2001:db8:4500:0:400::`. Check for a 40-byte outer IPv6 header without SRH,
then verify the inner packet reaches blue-2. The return direction continues
to use its separately configured ordinary service SID. Restore r1's full
three-SID route with the healthy command above and retest.

VALIDATION.md records the actual executed scope. This small software path
does not establish hardware rate, all slot capacities or interoperability
with every compressed format.

Destroy only this topology: `sudo containerlab destroy -t srv6.clab.yml`.

## Primary references

- [SRH](https://www.rfc-editor.org/rfc/rfc8754.html),
  [behaviours](https://www.rfc-editor.org/rfc/rfc8986.html),
  [compression](https://www.rfc-editor.org/rfc/rfc9800.html),
  [SID addressing](https://www.rfc-editor.org/rfc/rfc9602.html).
- [BGP services](https://www.rfc-editor.org/rfc/rfc9252.html),
  [argument signalling](https://www.rfc-editor.org/rfc/rfc9819.html).
- [Linux SR controls](https://docs.kernel.org/networking/seg6-sysctl.html),
  [iproute2 syntax](https://github.com/iproute2/iproute2/blob/main/man/man8/ip-route.8.in),
  [upstream End.DT4 test design](https://github.com/torvalds/linux/blob/master/tools/testing/selftests/net/srv6_end_dt4_l3vpn_test.sh).
- [Service Programming draft](https://datatracker.ietf.org/doc/draft-ietf-spring-srv6-service-programming/),
  revision 00, 6 July 2026, **work in progress**, for proxy discussion.
