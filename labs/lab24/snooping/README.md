# Separate Linux bridge experiment

`topology.json` records the exact namespace/interface setup executed by the
review harness. It is a setup manifest, **not** a Containerlab deployment file
or a standalone runner. Create isolated namespaces/veth links using the named
endpoints, then execute each node's `exec` list in order inside that namespace.
Requires root/CAP_NET_ADMIN, a Linux bridge with snooping support, iproute2,
Python3 and tcpdump. Do not run the bridge commands in the host namespace.

The switch node is s24: eth1 to source10.24.0.10, eth2 to member10.24.0.11,
eth3 to nonmember10.24.0.12; br0 querier10.24.0.254. All addresses are /24.
Run `traffic.py recv 239.2.1.1 10.24.0.11 asm` in the member. Capture UDP5000
on the nonmember without joining; capture IGMP on the member-facing bridge
port. Send tagged50-packet bursts with `traffic.py send 239.2.1.1 10.24.0.10 TAG 50`.
Use `python3 -u` for the receiver and preserve stdout.

Inside s24, observe `bridge -j mdb show dev br0`, and use this fault sequence:

```bash
ip link set br0 type bridge mcast_querier 0
# Wait until the dynamic239.2.1.1 membership has actually disappeared; send.
bridge link set dev eth2 mcast_flood off
# Send again: compare receiver delivery and nonmember wire capture.
ip link set br0 type bridge mcast_querier 1
# Observe queries/reports/MDB and send across the transition and after settling.
```

The iproute2 bridge interval values200,100 and500 in the manifest are
centiseconds (2s,1s and5s). Enable the querier after all setup commands, as
recorded. Do not infer selective forwarding or complete recovery from an MDB
row alone: check both receiver sequences and nonmember captures. The passing
run's first recovery burst still lost24/50 packets. See `../VALIDATION.md`
for failed attempts and limits. Restore `mcast_flood on` if reusing the isolated
lab, or delete only the namespaces/links this experiment created.
