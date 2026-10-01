# Lab 5.1 - Locate and repair a path MTU constraint

Run on an isolated Linux Containerlab host. Record engine versions and image
digests, not just tags. This is Linux forwarding; it does not validate a vendor
ASIC's giant/drop counters. The YAML explicitly enables all data interfaces and
uses specific data routes so the container management default is retained.

```sh
sudo containerlab deploy -t mtu.clab.yml
docker exec clab-lab05-h1 ping -I 10.0.10.10 -c 3 -W 1 10.0.30.10
docker exec clab-lab05-h1 ping -I 10.0.10.10 -M do -s 1472 -c 3 -W 1 10.0.30.10
docker exec clab-lab05-h1 ping -I 10.0.10.10 -M do -s 1473 -c 3 -W 1 10.0.30.10
```

For ordinary IPv4 without options, add 20 IP and 8 ICMP bytes to the payload.
The expected boundary is 1,500 IP bytes. Require successful small and boundary
probes before interpreting a larger failure. Record ICMP type/code and advertised
next-hop MTU, or a local cached-PMTU error; timeout alone does not identify MTU.
Packet size alone establishes a path constraint, not which hop imposed it.

Capture ICMP at h1 and inspect r2's egress MTU and `nstat` IP fragmentation
counters. Linux need not increment the generic link-drop counter for a packet
rejected by IPv4 forwarding. An ICMP source address is evidence to correlate
with the route and interface inventory, not a universal physical-hop identifier.

On this supplied topology r2 eth2 is the 1,500-byte egress. Record that original
value, then change it to 9,000 only in this disposable lab:

```sh
docker exec clab-lab05-r2 ip link set eth2 mtu 9000
docker exec clab-lab05-h1 ping -I 10.0.10.10 -M probe -s 8972 -c 3 -W 1 10.0.30.10
docker exec clab-lab05-r2 ip link set eth2 mtu 1500
sudo containerlab destroy -t mtu.clab.yml
```

`-M probe` bypasses the sender's cached PMTU check and needs the appropriate
privilege. It still sets DF; it does not bypass the path's real MTU. If that
iputils mode is unavailable, wait for verified cache expiry or redeploy the
disposable topology, and document the method. A successful forward probe and
reply cover this flow and packet size, not every ECMP member or encapsulation.
Restore the original MTU even when a probe fails. Retain command output and
packet captures; expected observations are not test evidence.

Require all requested echo replies, not only ping exit status zero. A partial
reply count is loss and must be recorded. A command/tool error is not evidence
of the intended MTU failure. After repairing the constraint, also originate an
equivalent source-bound probe at h2 and inspect both directions. The floating
netshoot `latest` tag is an unpinned prerequisite: retain and reuse the resolved
image digest for any claimed reproduction.
