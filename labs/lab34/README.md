# Lab 34 — origin validation and forwarding

There are two separate exercises. `validate.py` is an offline VRP coverage
model. The four-node FRR fixture exercises real RTRv1 reception, attached
import policy and Linux forwarding with **synthetic unsigned data**. Neither
exercise fetches repositories or verifies signed ROAs/certificates. See
`VALIDATION.md` for exactly what executed.

All addresses and ASNs are for an isolated lab. Keep it disconnected from real
BGP peers. The `/25` acceptance rule on the neighbour is deliberately broad
to isolate ROV; it is not a production peer prefix-authorisation policy.

## Offline exercise

From this directory, with Python 3:

```sh
python3 test_validate.py
python3 validate.py configs/vrps.json bgp.json --local-as 64500
```

Supply `bgp.json` from FRR's `show bgp ipv4 unicast json` (commands below).
`configs/vrps.json` contains `[prefix, maximumLength, ASN]` records, not signed
ROAs. The report lists every covering/matching record. A single match yields
Valid despite other nonmatching covering records.

Plain AS_SEQUENCE decimal and asdot text is supported. Empty paths require
the speaker's local AS; missing paths and AS_SET/confederation text are
reported as unsupported and the CLI returns 2. It does not implement every
RFC 6811 origin-segment rule. It does not predict acceptance by the rest of
the router policy. JSON numeric floats are rejected as ASNs, not reinterpreted
as asdot strings. Prefixes must be canonical, with host bits clear.

## Topology and policy

| Node | Role and interfaces |
|---|---|
| border, AS64500 | eth1 `192.0.2.0/31`, eth2 `.2/31`, eth3 `.4/31` |
| customer, AS64501 | eth1 `.1/31`; legitimate `203.0.113.0/24` announcement |
| neighbour, AS64502 | eth1 `.3/31`; legitimate `198.51.100.0/24` plus staged attack |
| client | eth1 `.5/31`; default via `.4` |

Customer and neighbour each have `203.0.113.200/32` on their own loopback and
an HTTP server returning a different marker. These are separate network
namespaces. The client can therefore identify where the border forwards.
Both advertisers have a return route for the client's `/31`.

The border imports the customer's exact `/24` at local preference 200 and
the neighbour's candidate prefixes at 150. Both imports first reject Invalid
routes and end with implicit deny; both exports deny everything. Candidate
`PEER-LAB` sequence 20 deliberately permits the victim's `/24` through `/25`.
Removing that entry demonstrates the value of independent prefix authority.

RTR listens only on the border's loopback, port 3323. The fixture implements
the reset/serial exchanges used here, IPv4 prefix data and end-of-data timers;
it is not a general-purpose RTR server or protocol-conformance suite. One-second
poll/retry and 600-second expiry are lab settings, not production guidance.

## Container adapter — supplied, not executed in this review

Docker and Containerlab were unavailable locally. These commands describe
the separate adapter; successful Linux namespace tests do not validate its
image build or orchestration. Record package/image versions before comparing
results. The Ubuntu tag and package repositories can change over time.

```sh
docker build -t netbook-rov:1 .
sudo containerlab deploy -t rpki.clab.yml
for node in border customer neighbour; do
  docker exec clab-lab34-$node sh /lab/start.sh "$node"
done
docker exec clab-lab34-border cat /netbook-package-versions.txt
```

`start.sh` is container-only. It starts FRR and loads each command script with
`load-config.py`; the scripts contain explicit `configure terminal`/`end`
context, so do not substitute them for a daemon's boot configuration file.
It also starts the cache or HTTP marker server. Do not run it on the host.

The following shell helpers shorten the commands. `conf` passes each quoted
argument as one vtysh command, preserving configuration context:

```sh
v() { node=$1; shift; docker exec "clab-lab34-$node" vtysh "$@"; }
conf() {
  node=$1; shift
  docker exec "clab-lab34-$node" python3 -c '
import subprocess,sys
a=["vtysh","-c","configure terminal"]
for c in sys.argv[1:]: a += ["-c",c]
raise SystemExit(subprocess.call(a+["-c","end"]))' "$@"
}
refresh() {
  v border -c 'clear bgp ipv4 unicast 192.0.2.1 soft in'
  v border -c 'clear bgp ipv4 unicast 192.0.2.3 soft in'
}
probe() {
  docker exec clab-lab34-client curl --noproxy '*' --max-time 3 -sS http://203.0.113.200:8080/
}
```

Inspect command output for errors; a vtysh exit status alone can miss CLI
errors. Save each snapshot, rather than overwriting `bgp.json` at each phase:

```sh
v border -c 'show rpki cache-connection'
v border -c 'show rpki prefix-table json'
v border -c 'show bgp ipv4 unicast neighbors 192.0.2.3 received-routes json'
v border -c 'show bgp ipv4 unicast json' > bgp.json
docker exec clab-lab34-border ip route get 203.0.113.200
probe
```

Pre-policy received-route flags such as `valid`/`best` are not proof of
post-policy acceptance or an RPKI Valid state. Compare the accepted table,
explicit origin-validation state, forwarding next hop and HTTP response.

## Baseline, faults and restoration

1. Wait for both BGP sessions and the RTR connection. Confirm two Valid `/24`
   routes, the customer next hop `.1`, and `LEGITIMATE` from the HTTP probe.
2. Introduce the neighbour's wrong-origin `/25`:

   ```sh
   conf neighbour 'ip route 203.0.113.128/25 Null0' \
     'route-map EXPORT permit 20' 'match ip address prefix-list ATTACK' 'exit' \
     'router bgp 64502' 'address-family ipv4 unicast' 'network 203.0.113.128/25'
   v neighbour -c 'clear bgp ipv4 unicast 192.0.2.2 soft out'
   refresh
   ```

   Prove the route was received with path `64502`, rejected from the accepted
   table, and did not divert HTTP. Absence alone does not prove a filter worked.
3. Forge the authorised origin:

   ```sh
   conf neighbour 'route-map EXPORT permit 20' 'set as-path prepend 64501'
   v neighbour -c 'clear bgp ipv4 unicast 192.0.2.2 soft out'
   refresh
   ```

   The received path is now `64502 64501`. Strict `/24` maximum length still
   rejects the `/25`. This shows why forging the origin is not sufficient here.
4. Broaden the cache record. The next command changes only the disposable
   container's `/tmp/vrps.json`, incrementing its serial atomically:

   ```sh
   docker exec clab-lab34-border python3 -c '
import json,pathlib
p=pathlib.Path("/tmp/vrps.json");d=json.loads(p.read_text())
d["serial"]+=1;d["records"][0][1]=32
t=p.with_suffix(".next");t.write_text(json.dumps(d));t.replace(p)'
   ```

   Wait until `show rpki prefix-table json` shows maximum 32, then `refresh`.
   Expect the forged `/25` to be Valid, border next hop `.3`, and `FORGED-PATH`.
   Repeat with an additional `['203.0.113.128/25',25,64502]` record (JSON double
   quotes in the file) and the original strict record also present. One broad
   matching VRP remains sufficient for Valid. Increment the serial after every
   data change and verify exact cache contents before policy re-evaluation.
5. Restore the original two records from `configs/vrps.json`, preserving a
   newly incremented serial in `/tmp/vrps.json`. Observe cache contents, run
   `refresh` and recover `LEGITIMATE`. Then change the Invalid gate:

   ```sh
   conf border 'no route-map PEER-IN deny 5' 'route-map PEER-IN permit 5' \
     'match rpki invalid' 'match ip address prefix-list PEER-LAB' 'set local-preference 10'
   refresh
   ```

   Confirm the accepted `/25` is Invalid with preference 10, while the `/24`
   has 200. HTTP still returns `FORGED-PATH`: these are different prefixes.
6. Restore rejection and re-evaluate:

   ```sh
   conf border 'no route-map PEER-IN permit 5' 'route-map PEER-IN deny 5' 'match rpki invalid'
   refresh
   ```

   Remove only the victim's VRP, increment the serial, verify the cache and
   refresh. Both victim routes become Not-found; the broad candidate admits
   the `/25`, diverting HTTP. Remove the candidate entry:

   ```sh
   conf border 'no ip prefix-list PEER-LAB seq 20'
   refresh
   ```

   Now the legitimate Not-found `/24` remains usable and the unauthorised
   `/25` is rejected. Restore original VRPs with a new serial and refresh;
   keep the restrictive prefix contract and confirm Valid legitimate service.
7. Stop the disposable cache process using its recorded PID, observe session
   disconnection and retained data, then restart:

   ```sh
   docker exec clab-lab34-border sh -c 'kill "$(cat /run/netbook-rtr.pid)"'
   # Observe the cache connection, data and service before restarting.
   docker exec -d clab-lab34-border sh -c \
     'python3 -u /lab/rtr-fixture.py /tmp/vrps.json >>/tmp/rtr.log 2>&1 & echo $! >/run/netbook-rtr.pid; wait'
   ```

   Confirm actual RTR reconnection, data and service; process existence alone
   is insufficient. The retained local run observes only a three-second outage.
   Extend the exercise past expiry, and separately test empty startup and
   multiple caches, before making those acceptance claims on a target.

The Linux evidence uses explicit soft-in after changes. Automatic revalidation
is not certified; the earlier Lab 22 FRR tests found transitions that needed
explicit re-evaluation. Soft-in is a lab diagnostic step, not a substitute for
fixing unreliable production update handling.

Clean up the isolated topology after recording restoration:

```sh
sudo containerlab destroy -t rpki.clab.yml
```

## Primary references and vendor boundary

- RFC 6811: https://www.rfc-editor.org/rfc/rfc6811.html
- Current ROA profile: https://www.rfc-editor.org/rfc/rfc9582.html
- RTRv1: https://www.rfc-editor.org/rfc/rfc8210.html
- Minimal maximum-length guidance: https://www.rfc-editor.org/rfc/rfc9319.html
- FRR 10.5 BGP/RPKI: https://docs.frrouting.org/en/stable-10.5/bgp.html
- Cisco IOS XR origin validation and policy attachment: https://www.cisco.com/c/en/us/td/docs/iosxr/cisco8000/bgp/bgp-config-cisco8000/r-wrapper-bgp-session-security-mechanisms/c-bgp-rpki-based-origin-validation-for-ibgp-updates-.html
- Nokia SR OS 24.7 BGP/origin validation: https://documentation.nokia.com/sr/24-7/7750-sr/books/unicast-routing-protocols/bgp-unicast-routing-protocols.html
- SR Linux 26.7 routing policies (not evidence of native RTR support): https://documentation.nokia.com/srlinux/26-7/books/routing-protocols/route-policies.html
- Huawei RPKI overview (not a complete release-specific adapter): https://info.support.huawei.com/info-finder/encyclopedia/en/RPKI.html

Checked 17 September 2026. None of these links converts the local FRR result
into a commercial NOS test. Record exact model/release, cache selection,
transport, policy chaining/attachment and all three states for each adapter.
