# Lab 32.1 — Authorise and change a bounded subscriber service

This is an isolated Linux/RADIUS teaching fixture with **static attachment and
address bindings**. It is not a complete BNG. It sends real Access, Accounting,
CoA and Disconnect packets and changes per-attachment filters and queue objects.
Read VALIDATION.md before interpreting results as evidence of deployment support.

There is no DHCP relay/option 82, PPPoE, DHCPv6-PD, IPv6 forwarding or CGN here.
`Delegated-IPv6-Prefix` is recorded metadata, not a prefix actually delegated to
a CPE. The circuit IDs are configured labels, not learned line identities.
`Filter-Id` meanings below are this fixture's local contract, not universal
vendor rate attributes. Do not extrapolate the serial exec controller to BNG scale.

## Topology and policy

| Attachment | CPE | BNG interface/address | Initial authorised product |
|---|---|---|---|
| circuit-id-0001 | 100.64.1.2/30 | eth1, 100.64.1.1/30 | lab-5m |
| circuit-id-0002 | 100.64.2.2/30 | eth2, 100.64.2.1/30 | lab-1m |
| AAA | 10.255.32.2/30 | eth3, 10.255.32.1/30 | Authentication/accounting and CoA peer |
| Simulated services | 203.0.113.20 and .80 | eth4, 203.0.113.1/24 | HTTP :80 and portal :8080 |

Before authorisation, the router drops forwarded traffic. An accepted supported
profile enables only the authorised source address on its configured attachment
towards the simulated service subnet, with stateful return filtering. Subscriber
attachments cannot forward to each other. This is a forwarding policy: it does
not harden management access to the disposable router itself.

`lab-5m` and `lab-1m` install separate 5 and 1 Mbit/s downstream HTB ceilings and
upstream ingress policers, with 16,000-byte bursts. Their rates are configured
Linux accounting rates, not exact application-payload promises. `garden` uses
1 Mbit/s objects and permits only TCP to 203.0.113.80:8080 plus its return traffic.
Existing connections receive no bypass rule. Changing a profile temporarily
closes that attachment while rebuilding its queues; loss during a change is
possible even though its session ID remains the same.

## Build and start (Linux Docker/Containerlab adapter)

These commands are the **unexecuted Containerlab adapter**. The recorded local
runtime used the same topology commands and helpers in Linux namespaces.
Use a disposable Linux lab host with Docker, Containerlab, traffic-control and
netfilter support. The Dockerfile installs packages only inside its image;
record the image digest and `/netbook-package-versions.txt` for reproducibility.
Its Ubuntu tag and package repositories can change. Do not repair host packages
or run `subscriber.py` in a production router namespace.

Run in this lab directory. Generate configuration inside the container so paths
point to the container mounts. The generator refuses to overwrite an existing
configuration. The `generated` directory is a pre-deploy bind prerequisite.

```bash
mkdir -p generated
docker build -t netbook-subscriber:1 .
sudo containerlab deploy -t bng.clab.yml
docker exec clab-lab32-bng python3 /lab/make-config.py /run/netbook32/config
docker exec clab-lab32-bng python3 /lab/subscriber.py --directory /run/netbook32/config init
docker exec -d clab-lab32-radius sh -c 'exec freeradius -X -d /run/netbook32/config/aaa > /run/netbook32/aaa.log 2>&1'
docker exec -d clab-lab32-bng sh -c 'exec freeradius -X -d /run/netbook32/config/dynamic > /run/netbook32/dynamic.log 2>&1'
docker exec clab-lab32-radius tail -n 10 /run/netbook32/aaa.log
docker exec clab-lab32-bng tail -n 10 /run/netbook32/dynamic.log
```

Both logs must reach `Ready to process requests`. Configuration errors are not
successful startup. Only the BNG and RADIUS node mount the private generated
directory. Each permitted RADIUS peer has a specific source address; auth and
dynamic authorisation use separate generated secrets. The fixture uses UDP/PAP
and a deliberately simple dummy password (`line`). It is not a production AAA
transport, credential store or replay-protection design. Keep it isolated.

Start services:

```bash
docker exec clab-lab32-internet sh -c 'mkdir -p /tmp/lab32-web; printf "Lab32 service\n" > /tmp/lab32-web/index.html'
docker exec -d clab-lab32-internet python3 -u -m http.server 80 --bind 203.0.113.20 --directory /tmp/lab32-web
docker exec -d clab-lab32-internet python3 -u -m http.server 8080 --bind 203.0.113.80 --directory /tmp/lab32-web
```

## Reject first, then authorise

The first curl must time out. A wrong credential and an authenticated but unknown
profile must return non-zero and leave the attachment denied. Inspect the AAA log
to distinguish an Access-Reject from an Access-Accept that the controller refuses.

```bash
docker exec clab-lab32-cpe1 curl --noproxy '*' --max-time 2 http://203.0.113.20/
docker exec clab-lab32-bng python3 /lab/subscriber.py --directory /run/netbook32/config up circuit-id-0001 --password wrong
docker exec clab-lab32-bng python3 /lab/subscriber.py --directory /run/netbook32/config up circuit-id-0001 --identity bad-profile
docker exec clab-lab32-bng python3 /lab/subscriber.py --directory /run/netbook32/config show
docker exec clab-lab32-bng python3 /lab/subscriber.py --directory /run/netbook32/config up circuit-id-0001
docker exec clab-lab32-cpe1 curl --noproxy '*' --max-time 2 http://203.0.113.20/
docker exec clab-lab32-cpe2 curl --noproxy '*' --max-time 2 http://203.0.113.20/
docker exec clab-lab32-bng python3 /lab/subscriber.py --directory /run/netbook32/config up circuit-id-0002
docker exec clab-lab32-cpe2 curl --noproxy '*' --max-time 2 http://203.0.113.20/
docker exec clab-lab32-bng tc -s class show dev eth1
docker exec clab-lab32-bng tc -s class show dev eth2
docker exec clab-lab32-bng tc -s filter show dev eth1 parent ffff:
docker exec clab-lab32-bng iptables -nvxL NBK32
```

Only the first authorised attachment should pass until the second is authorised.
Record both session IDs. Queue inspection establishes configured rate objects;
measure offered/delivered traffic in both directions separately if testing rates.
Lab31 explains packet accounting and generator limits. Do not infer a measured
5 Mbit/s application rate from a `tc` configuration line.

## Send actual CoA and Disconnect packets

The shell variable below contains only a disposable session ID. The shared secret
is read by `radclient -S` from a private file, not put in the command line.

```bash
sid=$(docker exec clab-lab32-bng python3 -c 'import json; print(json.load(open("/run/netbook32/config/sessions.json"))["circuit-id-0001"]["session_id"])')
docker exec clab-lab32-radius python3 /lab/send-dynamic.py coa circuit-id-0001 wrong-session --profile garden
docker exec clab-lab32-radius python3 /lab/send-dynamic.py coa circuit-id-0001 "$sid" --profile unknown
docker exec clab-lab32-radius python3 /lab/send-dynamic.py coa circuit-id-0001 "$sid" --profile garden
docker exec clab-lab32-bng python3 /lab/subscriber.py --directory /run/netbook32/config show
docker exec clab-lab32-cpe1 curl --noproxy '*' --max-time 2 http://203.0.113.80:8080/
docker exec clab-lab32-cpe1 curl --noproxy '*' --max-time 2 http://203.0.113.20/
docker exec clab-lab32-cpe2 curl --noproxy '*' --max-time 2 http://203.0.113.20/
docker exec clab-lab32-radius python3 /lab/send-dynamic.py coa circuit-id-0001 "$sid" --profile lab-5m
docker exec clab-lab32-cpe1 curl --noproxy '*' --max-time 2 http://203.0.113.20/
docker exec clab-lab32-radius python3 /lab/send-dynamic.py disconnect circuit-id-0001 "$sid"
docker exec clab-lab32-cpe1 curl --noproxy '*' --max-time 2 http://203.0.113.20/
docker exec clab-lab32-cpe2 curl --noproxy '*' --max-time 2 http://203.0.113.20/
```

The first two requests must receive CoA-NAK and preserve the authorised profile.
`garden` must receive CoA-ACK, permit the portal, deny ordinary service, and retain
the other subscriber's service. Restoration keeps the subscriber's session ID.
Disconnect must receive Disconnect-ACK and remove that session's forwarding.
Repeating the old Disconnect should receive NAK (session context not found).
`radclient` normally expects ACK; its non-zero exit for an intentional NAK is
expected negative-test evidence, not a successful change.

Also test `--event-time 1` (stale timestamp) and `--secret-file` naming a private
dummy file containing an incorrect generated lab secret. Stale requests must NAK;
an invalid authenticator must not produce an accepted change. This fixture's
120-second timestamp window and the server's duplicate handling do not constitute
a full persistent replay defence. Do not claim RFC5176 conformance from these
selected cases. Test any new attribute or session selector explicitly.

## Failure, source validation and accounting

After disconnecting subscriber1, stop the AAA process **only inside its named
container**, leaving the separate BNG dynamic listener running:

```bash
docker exec clab-lab32-radius pkill -TERM -x freeradius
docker exec clab-lab32-bng python3 /lab/subscriber.py --directory /run/netbook32/config up circuit-id-0001
docker exec clab-lab32-cpe1 curl --noproxy '*' --max-time 2 http://203.0.113.20/
docker exec clab-lab32-cpe2 curl --noproxy '*' --max-time 2 http://203.0.113.20/
docker exec -d clab-lab32-radius sh -c 'exec freeradius -X -d /run/netbook32/config/aaa >> /run/netbook32/aaa.log 2>&1'
```

Subscriber1 must remain denied; the already-authorised subscriber2 keeps its
forwarding policy. After the AAA log reports readiness again, authorise
subscriber1 and confirm a **new** session ID and restored service. This is an
explicit local failure policy, not a recommendation to keep all sessions forever.

On CPE1, add `100.64.2.2/32` temporarily to eth1 and try a curl using
`--interface 100.64.2.2`. It must fail and increment the final NBK32 DROP counter;
remove the temporary address afterwards. A timeout alone is insufficient evidence
of source filtering without the matching counter and positive control.

```bash
docker exec clab-lab32-bng python3 /lab/subscriber.py --directory /run/netbook32/config interim circuit-id-0001
docker exec clab-lab32-bng python3 /lab/subscriber.py --directory /run/netbook32/config down circuit-id-0001
docker exec clab-lab32-bng python3 /lab/subscriber.py --directory /run/netbook32/config down circuit-id-0002
docker exec clab-lab32-bng cat /run/netbook32/config/accounting-journal.jsonl
docker exec clab-lab32-radius cat /run/netbook32/config/aaa/accounting-detail
```

Inspect Start, Interim-Update and Stop, session ID, Class and acknowledgement.
The fixture sends lifecycle packets but has no octet counters, scheduled interim
worker, durable retry queue, restart reconciliation or billing guarantees. Failed
accounting acknowledgements are recorded locally; they are not automatically
replayed. `init` discards fixture sessions and closes forwarding, without generating
Stop records for a prior run. Use it only for initial disposable setup/reset.

Save logs and observed results; keep generated secret files private. Then destroy
only this lab: `sudo containerlab destroy -t bng.clab.yml`. The generated directory
persists for inspection. Use a new directory/run before regenerating configuration;
do not overwrite evidence with a fresh deployment.

## Model and extension exercises

For 60,000 sessions, ideal processing lower bounds at 500, 200 and 50 successful
sessions/s are 120, 300 and 1,200 seconds. These are arithmetic models, not times
measured by this serial controller. Add arrival spread, retries and dependencies.

For 50,000 subscribers and 64:1 sharing, the raw address requirement is
`ceil(50000/64) = 782` before reserves. With ports 1024–65535, an equal 64-way
division is 1,008 ports per subscriber per protocol. Declare mapping rules and
historical assignment records before comparing per-flow and per-block storage.

A full IPoE extension must separately implement trusted DHCP relay identity,
authorisation, lease/binding installation, DHCPv6 IA_PD, LAN router advertisements,
delegated routes and source validation. Capture the protocol exchanges; test a
spoofed relay identifier, prefix expiry/renewal and failure/restoration. Native
IPv6 documentation addresses show lab routing only, not public reachability.
This extension and commercial BNG adapters remain unimplemented/unexecuted.
