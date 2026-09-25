# Lab 15 — authentication evidence and the enforcement boundary

This lab has two separately recorded parts. Part A exchanges **wired EAP-TLS
using TLS 1.2**. It does not implement a controlled Ethernet port, MAB,
dynamic VLAN assignment, ACL installation or endpoint-health assessment.
Part B is an acceptance worksheet for an enforcement-capable switch/AP;
its platform configuration and execution remain target-specific.

## Part A: bounded Linux protocol exercise

The authenticator is hostapd's `wired` driver. Its EAPOL/RADIUS exchange can
succeed while ordinary IP passes before authentication. That is an intended
observation of this stand-in, not a secure admission design. **Do not use it
to control a production access port.** No wireless association is exercised.

Topology (only the test interfaces; Containerlab management is separate):

| Node | Interface | Address | Peer |
|---|---|---|---|
| client | eth1 | 198.51.100.2/30 | auth eth1 |
| auth | eth1 | 198.51.100.1/30 | client |
| auth | eth2 | 192.0.2.1/30 | radius eth1 |
| radius | eth1 | 192.0.2.2/30 | auth |

No bridge, default route or VLAN interface is configured on these links.
`make-config.py` creates a fresh seven-day CA (private CA key retained only
in generator memory), two-day server/client certificates, an expired client
certificate and one random shared RADIUS secret. It refuses an existing
destination. The lab server name is `radius.example.test`; no external DNS
lookup is required for the certificate name check. File permissions are 0600,
and the directory is 0700. Generated private keys are disposable lab material.
Never add this CA to an operating-system or production trust store.

The supplicant validates the CA and **exact expected server name**. The server
requires a client certificate, checks its CN against the presented identity
and authorises only `alice`. `bob` has a valid certificate but is rejected by
policy. This deliberately simple identity mapping is a lab rule, not a design
for anonymous outer identities or a production identity database. Rejection
uses the certificate-policy virtual server before EAP success; rejection
processing emits EAP-Failure as well as RADIUS Access-Reject and removes key
attributes. A contradictory EAP-Success inside Access-Reject is not acceptable.

TLS 1.2 is explicitly fixed for this interoperability exercise. Revocation,
TLS 1.3, enrolment, renewal, resumption policy and CA rollover are **not tested**.
Do not use this minimal configuration as a production PKI or RADIUS service.
The exact RADIUS source is restricted to 192.0.2.1, and
`require_message_authenticator = yes` is enabled. All keys are mounted into
isolated root containers for this experiment; production key distribution
must separate roles and protect private material.

### Containerlab adapter (execution pending)

Build the local image from `labs/common` as described in its README; it must
include FreeRADIUS, hostapd, wpa_supplicant and Python cryptography. From this
lab directory, generate files at the same `/lab/generated` path each container
will see, then deploy:

```sh
docker run --rm -v "$PWD:/lab" netbook-services:20260916 \
  python3 /lab/make-config.py /lab/generated
sudo containerlab deploy -t dot1x.clab.yml
```

Use a new empty lab working directory for a fresh generation; never overwrite
an existing PKI accidentally. For a Windows host, run these commands from the
Linux environment that owns the Docker daemon. On a filesystem that does not
preserve POSIX permissions, copy configurations into a private native Linux
directory before starting FreeRADIUS. The adapter below makes a private copy
inside each container and rewrites only the common generated-directory path.

Run three terminals. Start the server and authenticator first:

```sh
bash run.sh radius
bash run.sh auth
bash run.sh valid
```

Each command stays in the foreground; Ctrl-C stops that process. Save its log
if required before closing the terminal. Capture EAPOL on auth eth1 and UDP
1812 on auth eth2 using `tcpdump -ni eth1 ether proto 0x888e` and
`tcpdump -ni eth2 udp port 1812` inside the auth container. A debug log can
contain lab identity and derived key material; keep it with the disposable lab.

Stop the client and authenticator between cases; restart `bash run.sh auth`
then run the requested client profile. This prevents a prior successful
session from being mistaken for a fresh attempt.

| Profile/action | Required evidence |
|---|---|
| Before daemons start | Client can ping 198.51.100.1: no admission enforcement |
| `bash run.sh valid` | EAP-Success, RADIUS Access-Accept, VLAN attribute 110 |
| `bash run.sh wrong-name` | Supplicant server-name validation failure; no success |
| `bash run.sh expired` | Server rejects expired certificate; EAP-Failure |
| `bash run.sh policy-reject` | Valid bob certificate, Access-Reject and EAP-Failure |
| Stop RADIUS; fresh valid attempt | Retransmissions, no accept; record observation interval |
| Restore RADIUS; fresh valid attempt | Successful authentication again |

For policy rejection after the TLS handshake, wpa_supplicant can log
`Received EAP-Failure` without an immediate `CTRL-EVENT-EAP-FAILURE`. Check
the authenticator's Access-Reject and failed authentication state and absence
of EAP-Success; do not infer the result from a single client event string.

After each rejection, ping 198.51.100.1 again. It still works in this stand-in.
Likewise `ip -d link` shows no VLAN 110 being installed. Returning an attribute
and printing an internal “authorised” state do not create data-plane enforcement.
Destroy only this topology with `sudo containerlab destroy -t dot1x.clab.yml`.

### Recorded local execution

The publication review uses disposable Linux namespaces, not Containerlab.
FreeRADIUS 3.2.8 and hostapd/wpa_supplicant 2.11 were extracted from Ubuntu
packages without installing host services. Native private temporary files
avoid Windows-mount permission and concurrent-log-read behaviour. Exact
commands, versions, results and failed attempts are in the review evidence.
The common image's Ubuntu 24.04 package versions may differ: capture its
version manifest and repeat the cases before claiming adapter equivalence.

## Part B: enforcement acceptance on a supported target

Record target model, release, licence, host mode, RADIUS policy revision and
physical/virtual topology. Provide routed test destinations and an authorised
change/rollback plan. The table is a policy specification; choose supported
vendor commands and populate every address/interface before execution.

| Condition | Required result and evidence |
|---|---|
| Fresh unauthenticated staff endpoint | Only documented pre-authentication traffic passes |
| Valid staff identity | VLAN 110 installed; approved staff service passes; management probe denied |
| Invalid/expired credential or explicit reject | No staff role; inspect actual deny/quarantine policy |
| Known camera MAC without supplicant | MAB role on VLAN 410; only documented camera/support flows |
| Unknown MAC | Deny or restricted onboarding as specified; never staff access |
| Test endpoint impersonates camera MAC | Same constrained role at most; camera service permitted, corporate and lateral probes denied |
| All RADIUS servers unreachable | Documented new-session and existing-session outcomes; no confusion with rejection |
| RADIUS restored | Sessions reassessed; temporary access removed as specified |
| Unsupported VLAN/filter or resource exhaustion | Documented fail-safe outcome, actionable alarm |
| Phone plus downstream host | Independent enforcement consistent with selected host mode |

Test IPv4 and IPv6, same-segment and routed paths, both directions where policy
differs, and positive controls for each “blocked” test. A dead destination is
not proof of a working ACL. Save the RADIUS reply, switch session/effective
policy output and packet/application observations together. Restore normal
MACs, policy and service and retest. This worksheet has **not** been executed
on a commercial switch or hardware enforcement platform in the local review.

Primary implementation references: hostapd 2.11 source `src/drivers/driver_wired.c`
from https://w1.fi/releases/hostapd-2.11.tar.gz; the installed FreeRADIUS 3.2.8
`mods-available/eap` and `sites-available/default`; RFC 3580 and RFC 5216/9190.
