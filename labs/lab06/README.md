# Lab 6.1 - Observe SLAAC, DHCPv6 and the router source

This isolated topology has a shared SLAAC LAN (router, client and dormant
rogue node), a distinct managed-address LAN, and a distinct /127 router link.
The rogue is on the victim's Ethernet segment; routers do not relay its RA
from the separate point-to-point link. All prefixes here are within London's
2001:db8:a1de::/56 reservation. The earlier :110/:120 examples were inconsistent
with the revised site plan.

## Build and deploy

```sh
docker build -t netbook-services:20260916 ../common
sudo containerlab deploy -t ip-plan.clab.yml
docker exec clab-lab06-rtr cat /netbook-package-versions.txt
docker image inspect netbook-services:20260916
docker exec clab-lab06-rtr cat /tmp/lab06-dnsmasq.log
```

Record the base image digest, built image ID, package list, kernel and engine
versions. A date-like local tag does not pin upstream package contents. Keep
the built image/manifest for reproducibility. Require successful daemon startup
and the expected listeners before proceeding. No server is installed at deploy
time; package installation happens at image build time and fails on error.

## Separate each source of state

Wait for DAD and RA, then inspect addresses and routes on both clients. Capture
ICMPv6 and UDP 546/547 with a finite duration. On the SLAAC client, expect an
autoconfigured :10::/64 address and an RA default through the router's link-local
address. Read the prefix's A/L flags, router lifetime and RDNSS option. A Linux
kernel RA route does not prove the userspace resolver installed RDNSS.

On the managed client, invoke an explicit DHCPv6 client:

```sh
docker exec clab-lab06-client-dhcp busybox udhcpc6 -f -n -q -t 4 -T 2 -i eth1 -O 23 -s /lab/dhcp6-hook.sh
docker exec clab-lab06-client-dhcp ip -6 address show dev eth1
docker exec clab-lab06-client-dhcp ip -6 route show
docker exec clab-lab06-rtr cat /tmp/lab06.leases
docker exec clab-lab06-client-slaac dig -6 @2001:db8:a1de:10::1 router.lab.example AAAA
```

The hook installs the leased IA_NA address as /128 with the lifetime reported
by the client, so it does not remain valid forever; the on-link route and default
router are supplied by RA. The one-shot `-q` command exits after acquisition:
it is **not** a lease-renewal or expiry test and the minimal hook is not a full
production network manager. Do not leave this lab running past the lease and
call the retained address valid. Record DNS option data separately from an
actual resolver query. Querying the explicit server does not prove resolver
integration. Confirm the /127 peer using a source-bound ping to
2001:db8:a1de:ff::1 from the router's eth3 address.

## Unwanted RA: observe, do not assume selection

Record the legitimate router's link-local address and baseline default routes.
Start the bounded observation on the victim before enabling the isolated rogue:

```sh
docker exec clab-lab06-client-slaac timeout 12 tcpdump -ni eth1 -vv -c 40 icmp6
# In a second terminal, for this isolated lab only:
docker exec clab-lab06-rogue sh -c 'dnsmasq --keep-in-foreground --conf-file=/lab/rogue.conf --pid-file=/tmp/lab06-rogue.pid >/tmp/lab06-rogue.log 2>&1 &'
docker exec clab-lab06-client-slaac ip -6 route show default
```

The unwanted RA advertises a second prefix and high router preference. Record
whether the client accepts it and which router it actually selects; preference,
reachability and client policy matter. A new default-route entry is not proof
that packets used it. The rogue has no upstream, so a selected path can fail.

Stop only this rogue process using the PID file, retain the trace, and redeploy
the disposable topology to clear learned RA addresses/routes deterministically.
Do not claim that stopping advertisements immediately withdraws existing state:
router and prefix lifetimes are distinct. On real access equipment, implement
release-specific RA Guard on untrusted ports and prove both legitimate RA
delivery and unwanted RA rejection, including extension-header cases. This
Linux topology does not claim to implement or validate a vendor RA Guard.

Use `sudo containerlab destroy -t ip-plan.clab.yml` for final cleanup. For the
address-allocation exercise use `aldergate-plan.json` and `test_address_plan.py`;
those arithmetic checks are separate from this packet experiment.

References: dnsmasq's maintained manual, RFC 4861, RFC 4862, RFC 8106 and RFC
9915. Container/image execution and resolver integration must each be recorded;
neither is implied by a static topology review.

## Explicit graph for the Chapter 6 allocation exercise

`sparse-graph.json` is a separate Kestrel-style teaching scenario with twelve
routers and sixteen undirected links. Allocate consecutive /31s from the link
pool, twelve distinct /32s from the loopback pool, and one management subnet per
PoP for twenty hosts plus one reserved gateway. Four worked /27s leave room for
growth inside the management pool. The ring keeps the graph connected after
each single edge removal; it does not prove route convergence, shared-risk
independence or sufficient surviving capacity. The seventeen address-plan tests
check these bounded graph/allocation properties as well as the Aldergate plan.
