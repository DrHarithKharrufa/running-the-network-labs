# Lab 22 — BGP policy and recovery

This isolated IPv4 reference uses FRR 10.5.1. Read `VALIDATION.md` for exact
local execution and limitations. Docker/Containerlab files are supplied but
have not run here. Linux namespace execution is a separate result. The
SR Linux adapter contract in `variants/` awaits commercial verification.
Keep these documentation/benchmark addresses disconnected from live routing.

## Topology

| Node | ASN | Loopback | Service /32s |
|---|---:|---|---|
| lon-pr-01 | 64500 | 10.255.0.21 | 198.18.255.1 |
| lon-pe-01 | 64500 | 10.255.0.23 | — |
| transit-a | 64496 | 10.96.0.1 | 198.18.0.1, 198.19.0.1 |
| ix-peer | 64498 | 10.98.0.1 | 198.51.100.129 |
| cust-a | 64501 | 10.101.0.1 | 203.0.113.1 |

| Link | Left /31 address | Right /31 address |
|---|---|---|
| lon-pr-01 eth1 — lon-pe-01 eth1 | 10.254.1.0 | 10.254.1.1 |
| lon-pr-01 eth2 — transit-a eth1 | 192.0.2.0 | 192.0.2.1 |
| lon-pr-01 eth3 — ix-peer eth1 | 198.51.100.0 | 198.51.100.1 |
| lon-pe-01 eth2 — cust-a eth1 | 192.0.2.4 | 192.0.2.5 |

The internal link runs level-2 IS-IS; iBGP uses loopbacks and next-hop-self at
both ends. Three eBGP sessions give four total sessions, or eight directed
Established rows. There is no physical redundancy. Covering discard routes
support BGP origination; actual /32 interface addresses provide test service.

## Containerlab adapter (unexecuted)

Build the FRR base image from Lab 18, then from this directory:

```sh
docker build -t netbook-frr-rpki:10.5.1 .
sudo containerlab deploy -t kestrel-policy.clab.yml
bash start.sh
```

Check pinned package availability and record the resulting image digest.
Do not substitute a version while retaining the original validation claim.
Run startup once per fresh deployment. Both border routers load the RPKI
module and start a synthetic RTR fixture on namespace loopback. Their writable
records are `/run/frr/vrps.json`; fixture PID/log are `/run/frr/rtr.pid` and
`/run/frr/rtr.log`. Plain FRR without the module is not equivalent.

Use `docker exec -it clab-lab22-NODE vtysh`, replacing NODE with the exact name,
for the commands below. Service probes from cust-a must reach all four remote
addresses, using customer address 203.0.113.1 as source, for example:

```sh
docker exec clab-lab22-cust-a ping -c 3 -I 203.0.113.1 198.18.0.1
```

Repeat for 198.19.0.1, 198.51.100.129 and 198.18.255.1. Route presence alone
does not demonstrate delivery.

## Baseline contract and observations

Customer import permits exactly 203.0.113.0/24 and an AS path containing only
AS 64501, including its repeated prepends. Customer /25, /26, 10/8 and default
announcements are negative fixtures. Transit supplies exactly 198.18.0/24 and
198.19.0/24; peer supplies 198.51.100.128/25; Kestrel originates 198.18.255/24.
These finite feeds are not production Internet filters. Customer receives the
four remote prefixes. Peer and transit receive only Kestrel and eligible
customer origins. LOCAL_PREF is 200/150/100 for customer/peer/transit.

Trusted large communities are 64500:1:0 own, 64500:1:1 customer,
64500:1:2 peer, 64500:1:3 transit and 64500:2:11 London. External provenance
is stripped before trusted tags are assigned. Allowed customer requests:

| Full community value | Meaning |
|---|---|
| 64500:100:1 | One extra AS 64500 copy to transit only |
| 64500:100:2 | Two extra copies to transit only |
| 64500:100:3 | Three extra copies to transit only; highest request wins |
| 64500:200:0 | No peer export |
| 64500:201:64496 | No export to Transit A |
| 64500:201:64498 | No export to ix-peer |

There are no standard aliases. External export removes all large communities.
Standard NO_EXPORT, NO_ADVERTISE and NO_EXPORT_SUBCONFED survive sanitisation;
other standard and all extended values are removed. No blackhole service is
offered; 64500:9:666 is removed. This is not VPN route-target policy.

In this FRR build, deletion lists inspect each community in order: matching
deny preserves that value; matching permit deletes it. The final `permit .*`
removes everything else. Import then jumps past unconditional rejection to
trusted-tag assignment. Preserve the unconditional deny: otherwise failed
authorisation can reach the later unconditional permit.

On lon-pe-01 inspect:

```text
show bgp ipv4 unicast summary
show bgp neighbors 192.0.2.5
show bgp ipv4 unicast neighbors 192.0.2.5 received-routes json
show bgp ipv4 unicast 203.0.113.0/24 json
show rpki prefix-table json
show ip route 203.0.113.0/24
```

On lon-pr-01 inspect the customer path and both active export views:

```text
show bgp ipv4 unicast 203.0.113.0/24 json
show bgp ipv4 unicast neighbors 192.0.2.1 advertised-routes json
show bgp ipv4 unicast neighbors 198.51.100.1 advertised-routes json
```

On receiving peer/transit inspect the same prefix. Baseline AS_PATH is
`64500 64501` and large communities are absent. Pre-policy customer storage
exists because soft-reconfiguration inbound is enabled; it consumes memory.
Advertised-route views describe active policy, not an unattached candidate.

## Lab 22.1 — community vectors

On cust-a, enter `configure terminal`, then `route-map ANNOUNCE permit 10`.
After each change use `end` and `clear bgp ipv4 unicast 192.0.2.4 soft out`.
Wait for the expected state before continuing. Commands without `additive`
replace the configured set.

1. `set large-community 64500:1:3 64500:2:99 64500:9:666 64500:100:2`.
   Kestrel must retain exactly 64500:1:1, 64500:2:11 and 64500:100:2. Transit
   sees `64500 64500 64500 64501`; peer sees `64500 64501`. Neither external
   receiver sees large communities. Recheck service.
2. `set large-community 64500:100:1 64500:100:3`: transit sees four copies of
   64500 total; peer still sees one.
3. `set large-community 64500:200:0`: peer loses the customer route, transit
   retains it. Then `set large-community 64500:201:64496`: transit loses it,
   peer regains it. Suppression precedes prepending.
4. `no set large-community`, then `set as-path prepend 64501 64501`:
   authorised own-AS repetition remains accepted. Transit sees one 64500 and
   three 64501 copies. Restore with `no set as-path prepend`.
5. `set community no-export`: internal customer path remains but external
   advertisements disappear. Restore with `no set community`, then refresh
   outbound, verify both external paths and all four service probes.

Allowed but separately unexecuted variants, including NO_ADVERTISE and the
64498-specific suppression value, need their own target tests before release.

## Lab 22.2 — candidate diff, limits and roles

The synthetic customer validation record covers /24 through /25 with origin
64501. The /25 is therefore Valid but not authorised by the baseline prefix
filter. The /26 is Invalid. Transit 198.19.0/24 is NotFound and remains at
transit preference 100. No `rpki strict` startup gate is configured.

Save baseline accepted/export JSON. On both Kestrel routers in the isolated
lab only, replace the exact customer filter:

```text
configure terminal
no ip prefix-list CUST seq 10
ip prefix-list CUST seq 10 permit 203.0.113.0/24 le 25
end
```

On lon-pe-01 run `clear bgp ipv4 unicast 192.0.2.5 soft in`. The accepted and
lon-pr-01 export sets now include 203.0.113.128/25; /26 still fails validation.
Transit's unchanged import filter rejects /25, concealing Kestrel's broadened
export from its accepted table. Inspect Kestrel's post-export view directly.

With two customer prefixes accepted, on lon-pe-01 configure:

```text
configure terminal
router bgp 64500
 address-family ipv4 unicast
  neighbor 192.0.2.5 maximum-prefix 1 75
end
clear bgp ipv4 unicast 192.0.2.5 soft in
show bgp neighbors 192.0.2.5
```

Record failure and reason. Restore exact `203.0.113.0/24` on both borders,
restore `maximum-prefix 16 75`, and clear the customer session. Verify eight
Established rows, no /25 export and all service probes. The limit counts
accepted prefixes; this is not a received-route flood/resource test.

For Role mismatch, on cust-a under `router bgp 64501` set
`neighbor 192.0.2.4 local-role provider strict-mode`, then clear that peer.
Provider/provider must not establish. Capture Kestrel's neighbour reason.
Restore cust-a to `customer strict-mode`, clear and verify service recovery.

## Synthetic RTR changes and recovery

The fixture serves IPv4 records only. It validates no certificates, signatures,
ROAs or repositories, and implements only reset/serial exchanges needed here.
It is not a production cache or RTR conformance suite.

Atomically edit each border's writable `vrps.json`, increment `serial`, and
change the first record's ASN from 64501 to 64499. The customer /24 becomes
Invalid and should be withdrawn while BGP sessions remain Established. In the
observed second transition it remained selected despite displaying Invalid;
explicit inbound re-evaluation applied the rejection. This build has not
passed automatic cache-change policy handling. Restore ASN
64501 with another serial. First verify `show rpki prefix-table json`, then
check route re-evaluation and service separately. In this local build,
recovery required `clear bgp ipv4 unicast 192.0.2.5 soft in` on lon-pe-01.
Do not call this automatic recovery.

While the record is Invalid, stop both fixture PIDs and observe initially
retained data. Both fixture and router expiry are 600 seconds: use real elapsed
time. Inspect empty cache and route state separately, then explicitly
re-evaluate customer import if needed. The remaining contract permits
authorised NotFound routes. Restart each fixture with original ASN and a new
serial, confirm four records and route state, and repeat service probes.
`VALIDATION.md` records the actual expiry result and limitations. Container
mutation/startup paths are supplied but have not been executed here.

Further target tests include startup before cache readiness, redundant caches,
public validator chain handling, IPv6, malformed attributes, other actions,
missing import/export, received-route floods and realistic update churn.
No Batfish run or 50,000-prefix replay is claimed. An MRT replay needs a source
and date, attribute-preserving conversion, negative fixtures and sizing.

Retain configs, versions, expected/actual diffs and restoration evidence.
Restore baseline files before another deployment. Teardown:

```sh
sudo containerlab destroy -t kestrel-policy.clab.yml
```
