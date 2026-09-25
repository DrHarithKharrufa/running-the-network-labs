# Lab 22 validation — 17 September 2026

## Executed scope

Run `20260917T000022Z`: 24 assertions passed using actual FRR
10.5.1-1ubuntu4.1 and its RPKI module, RTRlib 0.8.0-7, Linux
6.18.33.2-microsoft-standard-WSL2 and iproute2 6.19.0. Five network
namespaces use private mount/UTS contexts and extracted packages. No host
service installation, account change or dpkg repair was performed.

The tests establish the four-session baseline and customer delivery to four
service addresses; exact prefix authorisation; relationship preference
independent of Valid/NotFound; forged provenance removal; transit-only and
conflicting prepend requests; no-peer and exact-AS suppression; customer
own-AS repeats; NO_EXPORT; origin rejection and explicit re-evaluation;
candidate /25 acceptance/export with /26 rejection; accepted-prefix-limit
failure/recovery; complementary/mismatched BGP Roles; real cache expiry and
restoration. Read individual assertion details, not only this total.

## Failed automatic behaviour remains unresolved

Automatic recovery observations:

```json
{
  "valid_record_restore": {
    "accepted_after_10_seconds": false
  },
  "second_invalid_transition": {
    "accepted_before_refresh": true,
    "path": {
      "aspath": {
        "string": "64501",
        "segments": [
          {
            "type": "as-sequence",
            "list": [
              64501
            ]
          }
        ],
        "length": 1
      },
      "origin": "IGP",
      "metric": 0,
      "locPrf": 200,
      "valid": true,
      "version": 20,
      "rpkiValidationState": "invalid",
      "bestpath": {
        "overall": true,
        "selectionReason": "First path received"
      },
      "largeCommunity": {
        "string": "64500:1:1 64500:2:11",
        "list": [
          "64500:1:1",
          "64500:2:11"
        ]
      },
      "lastUpdate": {
        "epoch": 1789603276,
        "string": "Thu Sep 17 00:01:16 2026"
      },
      "nexthops": [
        {
          "ip": "192.0.2.5",
          "hostname": "cust-a",
          "afi": "ipv4",
          "metric": 0,
          "accessible": true,
          "used": true
        }
      ],
      "peer": {
        "peerId": "192.0.2.5",
        "routerId": "10.101.0.1",
        "hostname": "cust-a",
        "domainname": "localdomain",
        "type": "external"
      }
    }
  },
  "cache_expiry": {
    "accepted_before_refresh": false,
    "seconds_after_stop": 603.540882319
  }
}
```

The first Valid-to-Invalid transition withdrew the route. Restoring the Valid
record did not automatically readmit it during the observation window. After
subsequent session/fault work, another Invalid record left a displayed Invalid
route selected until explicit inbound soft re-evaluation. Soft-reconfiguration
inbound was configured. The passing assertions cover the documented explicit
re-evaluation; they do not certify automatic cache-change policy handling.
Do not rely on this build for that behaviour without resolving and retesting
the discrepancy on the intended deployment. No upstream defect report or
claim about other versions is implied.

The fixture advertises refresh/retry 1 second and expiry 600 seconds; router
settings match. It serves synthetic IPv4 data over namespace loopback only.
Expiry is measured in real elapsed time. No certificates, signatures, ROAs,
repositories, public trust chain or redundant validator failover were tested.

Earlier attempts are retained: 20260916T234255Z and 234830Z failed automatic
Valid restoration; 235327Z reached the limit experiment then exposed an
incomplete neighbour-inspection command; 235752Z failed the second automatic
Invalid transition. The corrected command is `show bgp neighbors ADDRESS`.
Some RPKI-enabled bgpd processes logged SIGSEGV in shutdown/thread cleanup
after the harness requested termination. This is separate from the running
policy checks and remains an implementation/environment limitation; graceful
daemon shutdown has not been validated. Logs and backtraces are retained.

## Unexecuted boundaries

Dockerfile build, Containerlab startup and its writable-fixture adapter;
commercial NOS configurations; IPv6; full Internet-table scale, MRT replay
and Batfish; malformed attributes, redundant caches and public validator
cryptography. The SR Linux contract remains a translation task, not tested
syntax. Extra allowed community variants need their own target cases.

Source files and local execution are distinct from these pending stages.
The lab is not a production RPKI cache, security certification or throughput
benchmark. The exact event commands and route snapshots are in the cited
runtime-evidence directory.
