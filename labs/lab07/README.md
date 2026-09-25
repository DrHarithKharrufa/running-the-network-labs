# Lab 7.1 - Measure direction, delay and recovery

Deploy `transport.clab.yml` on a disposable Containerlab host. Record host,
tool and resolved image versions. Every script command below is run on that
host; the script changes only the named lab router. The declared starting MTU
is 1,500. Do not use this helper on a topology with pre-existing custom qdiscs.

```sh
sudo containerlab deploy -t transport.clab.yml
bash impair.sh baseline
docker exec clab-lab07-client ping -I 10.0.10.10 -c 10 10.0.20.10
bash impair.sh latency
docker exec clab-lab07-client ping -I 10.0.10.10 -c 10 10.0.20.10
bash impair.sh symmetric
docker exec clab-lab07-client ping -I 10.0.10.10 -c 10 10.0.20.10
bash impair.sh clear
```

The router's eth2 **egress** delays client-to-server packets. That adds about
80 ms to RTT, not 160 ms. The symmetric case also delays eth1 egress and adds
about 160 ms. Compare measured means with baseline, keeping scheduler jitter
and queuing visible. Save `tc -s qdisc` output before clearing each condition.

For throughput use bounded, fresh tests:

```sh
docker exec clab-lab07-client iperf3 -c 10.0.20.10 -t 10 -J
docker exec clab-lab07-client iperf3 -c 10.0.20.10 -R -t 10 -J
```

Use `loss` or `both` and repeat several trials; 0.1% loss is stochastic and a
short run may lose no packets. Record direction, bytes, duration, retransmits,
CPU and transport state. A single throughput result cannot identify a cause.

For a receive-window experiment record the original `tcp_window_scaling` on
the receiving endpoint, disable it there, and start a new connection. Capture
the handshake and actual advertised window. Restore the saved sysctl value,
not an assumed value. A 65,535-byte window at 80 ms bounds one flow near
6.55 Mbit/s; at 160 ms it is about 3.28 Mbit/s before other constraints. Those
are bounds, not predicted measurements; congestion and endpoints may dominate.

`bash impair.sh mtu` reduces eth2 to 1,400 and drops locally generated ICMP
fragmentation-needed messages using one labelled rule. Compare a small probe
with a 1,500-byte DF probe and a bounded transfer. Kernel PMTU state and TCP
black-hole recovery can change the symptom: do not require an indefinite stall.
Capture ICMP/TCP and record retransmissions, packet sizes and eventual recovery.

Always run `bash impair.sh clear`, verify both qdiscs, MTU and the removal of
the labelled rule, then destroy with `sudo containerlab destroy -t transport.clab.yml`.
The helper removes its exact rule; it never flushes the whole OUTPUT chain.
The independent namespace evidence, when supplied, validates Linux mechanisms,
not Containerlab startup or the netshoot image's package set.

## Helper failure checks

Eight offline tests (`python3 test_impair.py -v`) execute Bash against Docker
command doubles. Inspection failures now stop cleanup instead of being treated
as an absent qdisc or rule. The helper removes every exact owned LAB07-MTU rule,
without flushing the OUTPUT chain. A deletion or MTU error remains a failure.
If a command fails, retain its output and inspect remaining state before using
`clear` again; an interrupted sequence can leave a partial change. These tests
validate helper control flow, not a Docker image or Linux forwarding behaviour.
