# Five flows, with a real listener

`service_fixture.py` supplies an original bounded TCP/UDP echo fixture for
DC-11 and related transport filtering trials. It uses only Python's standard
library. Execute on **owned hosts in the isolated task topology**. It neither
adds addresses/routes nor prepares a firewall automatically.

Before policy, prove the intended source, destination, route/return path and
real receiver. Example receiver at the task's actual service address:

```text
python service_fixture.py serve --bind 198.51.100.100 --port 8443 --transport tcp --count 30 --seconds 120
python service_fixture.py probe --source 203.0.113.2 --target 198.51.100.100 --port 8443 --transport tcp --count 5 --source-port-base 40100 --label WB-BEFORE
```

Run the receiver in a separate lab terminal. Its READY record proves only that
the listener bound locally. Require five successful client echoes plus an
independent receiver/wire observation before applying policy. Prepare the task's
8444 control listener separately. SEC-09 needs the named alternative **TCP4444**
receiver for IOS XE and **TCP443** comparison listener for the FortiOS service
case: binding low port443 needs the qualified privilege/capability on its owned
host. The helper supports that port when the operating system grants the bind.
Do not substitute8443 silently; a refused bind is a fixture failure.

An echo on port 443 establishes TCP state and port filtering, **not HTTPS**.
For SEC-09's HTTPS criterion use `https_fixture.py` instead. It implements a
fixed GET /wb response over certificate-verified TLS; it does not serve files.
Provision an isolated lab certificate for `wb-server.lab` and distribute only
its trusted public CA/certificate to the client. Keep its private key on the
server and out of this book's archive. Certificate issuance is an operator
preparation step, not a reason to disable verification. The target address and
certificate name are separate, so no external DNS is needed for this helper:

```text
python https_fixture.py serve --bind 198.51.100.100 --port 443 --cert server.pem --key server-key.pem --count 30 --seconds 120
python https_fixture.py probe --source 203.0.113.2 --target 198.51.100.100 --port 443 --ca lab-ca.pem --server-name wb-server.lab --count 5 --source-port-base 40500
```

For the reverse-new negative test, also prepare a verified HTTPS listener on
the client, with its own certificate/identity, and prove it reachable before
policy. Use fresh source-port batches for all phases. A certificate error is a
fixture failure, not evidence of firewall denial. Both helpers use absolute
transaction and overall deadlines, including partial reads. The HTTPS helper
uses standard-library TLS behavior described in the
[Python SSL documentation](https://docs.python.org/3/library/ssl.html).

After policy, offer five **new connections** from each prescribed source and five
control connections. Use different declared source-port batches (40200,40300,
40400) for successive trials, and record existing connection tracking and effective
rule order. A TCP service trial counts echo transactions, not exactly five wire
packets; SYN/ACK/data/FIN/retransmission and ARP/ND are separate observations.
For UDP use --transport udp on both server and probe, preserving protocol match.

The client records failures as failures, never as empty healthy results. A bind
failure means the fixture is invalid. Do not treat it as firewall denial. The
receiver stops on its count or separate finite clock bound. After removing only
the owned policy, repeat a fresh-port batch and check recovery. These example
commands are lab instructions; supplied fixtures have no claim of vendor-device
execution. Local loopback QA, if recorded, qualifies the software service only.
