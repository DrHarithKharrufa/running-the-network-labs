# Lab 8.1 - Service startup, failure and recovery

Build the shared image before deployment. There are separate DNS and DHCP
processes, a relay, an isolated chrony teaching source and a small UDP collector.
Stopping DNS therefore no longer silently stops DHCP too. Package installation
failures are not ignored, and every service has explicit configuration/startup.

```sh
docker build -t netbook-services:20260916 ../common
sudo containerlab deploy -t services.clab.yml
docker exec clab-lab08-svc cat /netbook-package-versions.txt
docker exec clab-lab08-client busybox udhcpc -f -n -q -t 4 -T 2 -i eth1 -s /lab/dhcp4-hook.sh
docker exec clab-lab08-client python3 /lab/probe.py dns
docker exec clab-lab08-client dig @10.10.14.10 srv-dc.ald.example A
docker exec clab-lab08-client python3 /lab/probe.py ntp
docker exec clab-lab08-client python3 /lab/probe.py log SEQUENCE-0001
docker exec clab-lab08-svc cat /tmp/lab08-events.jsonl
```

Record the image ID/digest, tool versions, hook output and all server logs. The
DHCP hook installs the address for the reported lifetime and a specific route
to the service network, preserving Containerlab's management default. It records
router/DNS options without editing the host resolver. This one-shot acquisition
does not test renewal or install production client policy.

Capture the relayed exchange on svc eth1 with a 15-second, 100-packet limit and
filter `udp port 67 or udp port 68`. Identify giaddr 10.10.0.1 in the actual
packet; compare the selected pool and the server's route back to the client LAN.
A configured relay command alone is insufficient evidence.

## One fault at a time

Use `docker exec clab-lab08-svc bash /lab/service.sh stop NAME`, test, then
`start NAME` and repeat a successful transaction before the next fault.

| Service | Required failure observation | Recovery observation |
|---|---|---|
| dns | Explicit-server DNS probe times out/fails; existing IP connectivity remains | Expected A answer returns |
| dhcp | A fresh acquisition cannot obtain a lease; previously leased client retains usable state until its deadline | New acquisition succeeds |
| ntp | Bounded UDP/123 probe has no valid response | Reply has expected origin token and stratum 10 |
| log | Numbered UDP message is absent from stopped collector | Later numbered message is present after restart |

Use a separately provisioned fresh client or redeploy for the new-acquisition
case; do not erase an existing lease and call that expiry. For renewal/expiry,
run a full client continuously, observe ACK lifetime/T1/T2, and wait for the
actual state transitions. The supplied short run does not establish them.

Chrony runs with `-x`: it cannot adjust the shared host clock. `local stratum 10`
deliberately serves the local unsynchronised teaching clock. A response here
proves protocol service only, not UTC accuracy, NTS authentication, client clock
discipline or holdover performance. `chronyc tracking` is a management query,
not a substitute for an NTP client transaction.

The collector stores JSON lines, but there is no acknowledgement, durable queue,
TLS or disk-failure recovery. A successful UDP `sendto()` is not delivery proof.
Check sequence numbers at the collector; gaps can also arise from routing,
filtering or loss. A stopped collector is a controlled cause in this experiment.
Do not describe this helper as a production logging system.

Finally restore each process, repeat all baseline probes, save evidence and run
`sudo containerlab destroy -t services.clab.yml`. Commercial AAA timeout/reject
behaviour and production DNS/time/log resilience need their own platform tests.

Primary documentation: dnsmasq manual (relay, interface and DHCP options),
chronyd/chrony.conf manuals (-x, allow, local), RFC 2131, RFC 5905 and RFC 5424.

## Acceptance boundaries

The DNS probe requires the single fixed A answer `10.10.14.10` for
`srv-dc.ald.example`; a non-empty wrong answer does not pass. It invokes the
image's `dig` command with a bounded timeout. It is deliberately not a general
DNS parser, DNSSEC validation test or test of the client's default resolver.
The NTP probe requires version 3 or 4, server mode, a matching origin token,
the expected peer, a non-alarm leap field and the configured stratum 10. These
checks do not authenticate the server or establish clock accuracy.

Run `python3 -m unittest -v test_probe.py` for eleven offline acceptance tests
using synthetic responses and a mocked dig process. They send no packets.
The current lab uses a ten-minute lease and pool .100-.150 to bound the
experiment; the separate vendor example uses .100-.200. The obsolete combined
`dnsmasq.conf` is no longer supplied: `dns.conf`, `dhcp.conf` and `relay.conf`
are the active files, and their independent processes enable separate faults.
