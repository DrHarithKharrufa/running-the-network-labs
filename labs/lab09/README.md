# Lab 9.1 - Observe forwarding, NAT and a directional policy fault

Topology: `pc -- acc (bridge) -- core -- fw -- isp -- server`. There are five
links and three IPv4 forwarding nodes. No MPLS, HA firewall or alternate
physical return path is present. Use an isolated Linux Containerlab host;
record images, digests and tools before claiming a deployment result.

The explicit data routes preserve management defaults. The firewall allows
only the illustrated HTTP flow and its tracked return packets; SNAT is scoped
to that source subnet and server network. These are teaching rules, not a
production firewall template. The HTTP server exposes the disposable /tmp only.

## Predict, capture, compare

Write one row per link per direction: ten rows for a chosen request/reply pair.
Record source/destination MAC, IP, ports and TTL. Obtain actual MACs and the
client's selected initial TTL; do not copy an invented trace. The bridge keeps
the Ethernet addresses and does not decrement IP TTL. Core, firewall and ISP
each decrement the forwarded IPv4 TTL. Outbound SNAT changes the source to
198.51.100.2; a source-port change is possible but not required.

```sh
sudo containerlab deploy -t journey.clab.yml
bash capture-all.sh 12
```

Each tap captures at most 500 filtered packets, 160 bytes each, for 5-60
seconds. Read each `.log` for drops and errors before treating its `.pcap` as
evidence. `tcpdump -nn -e -r <file>` shows headers; limited snap length can
truncate payload. Check checksum-offload effects before diagnosing corruption.

## Break return policy, observe and restore

```sh
bash fault.sh block
docker exec clab-lab09-pc curl --noproxy '*' --interface 10.10.0.42 --connect-timeout 2 --max-time 4 -v http://203.0.113.20/
docker exec clab-lab09-fw iptables -nvxL FORWARD
bash fault.sh restore
docker exec clab-lab09-pc curl --noproxy '*' --interface 10.10.0.42 --connect-timeout 2 --max-time 4 --fail http://203.0.113.20/
```

The blocked probe must time out and the labelled rule's packet counter must
increase. A DNS, routing or server error is not a passing fault test. The
SYN-ACK of a new TCP attempt can already match conntrack ESTABLISHED; this does
not mean the application completed its TCP handshake. To test an already-open
connection, complete `connect()` before inserting the rule, then send its
request and observe the blocked reply. Record these as different cases.

Deleting an ISP route to 10.10.0.0/22 does **not** break this SNAT return path:
the ISP replies to the connected 198.51.100.2 address. The removed old exercise
therefore did not demonstrate asymmetric forwarding. Here the fault is a
specific policy drop; correlate its counter, ingress capture and absent egress.

Always restore the labelled rule, repeat the successful request, retain your
evidence, and destroy `journey.clab.yml`. Independent namespace execution can
verify these Linux mechanisms, but does not validate Docker/image startup or a
commercial firewall's state machine.

This standalone Internet-path exercise temporarily uses 10.10.255.0/30 for
core-to-firewall transit, from space otherwise unallocated in the reference
plan. It is distinct from the campus walk's 10.10.15.252/30 transit and does
not silently assign that reserved space to a permanent site.

The fault helper fails on a rule-inspection error or a conflicting rule with
the same ownership comment, and restores all exact owned duplicates. Six Bash
command-double tests (`python3 test_fault.py -v`) check these paths without
Docker or packet forwarding. A failed command can leave a partial change;
inspect the remaining rules and retain the error before attempting recovery.
