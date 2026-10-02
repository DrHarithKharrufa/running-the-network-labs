# Configuration Workbook task navigator

Edition **RTN-2026-10-03**. Generated from the authoritative task ledgers.

Start with Part 1 and proceed in order, or select a task whose prerequisites you can demonstrate.
Session estimates cover one panel on a prepared lab. They exclude provisioning and comparison; they are not measured completion times.
READ establishes documentary syntax evidence, not device execution. Check the exact image and panel scope. No licensed images are bundled.

## Tasks at a glance

| Task | Part | Current book chapters | Session estimate (minutes) | Goal |
|---|---:|---|---|---|
| [DEV-01](#dev-01) | 1 | 9, 51 | 30-60 | Get to a prompt, and know which mode you are in |
| [DEV-02](#dev-02) | 1 | 9, 51 | 30-60 | Hostname, banner and a device identity |
| [DEV-03](#dev-03) | 1 | 9, 64 | 30-60 | Save, diff and recover: rehearse the whole sequence |
| [DEV-04](#dev-04) | 1 | 9, 51 | 30-60 | Build a management path that survives the data-plane mistake |
| [DEV-05](#dev-05) | 1 | 9, 51, 52 | 30-60 | Create an account, then prove what it cannot do |
| [DEV-06](#dev-06) | 1 | 9, 51, 52 | 30-60 | SSH: check the key, not just the padlock |
| [DEV-07](#dev-07) | 1 | 51, 52 | 30-60 | AAA fallback: a refusal is not a timeout |
| [DEV-08](#dev-08) | 1 | 51, 52, 61 | 30-60 | Synchronise time before comparing evidence |
| [DEV-09](#dev-09) | 1 | 61, 62 | 30-60 | Send a log, then find it at the other end |
| [DEV-10](#dev-10) | 1 | 9, 64 | 30-60 | Stage an image without deleting your way home |
| [L2-01](#l2-01) | 2 | 5, 9, 16 | 45-75 | A green LED is not an IP path |
| [L2-02](#l2-02) | 2 | 3, 4, 16 | 45-75 | The port label, the packet budget and the link agreement |
| [L2-03](#l2-03) | 2 | 4, 10 | 45-75 | Give two hosts a shared Ethernet room |
| [L2-04](#l2-04) | 2 | 10 | 45-75 | A trunk is a contract between two ports |
| [L2-05](#l2-05) | 2 | 10 | 45-75 | The tag that is missing is still a decision |
| [L2-06](#l2-06) | 2 | 11 | 45-75 | Elect the root before the network elects one for you |
| [L2-07](#l2-07) | 2 | 11, 52 | 45-75 | An edge port should not accept a new boss |
| [L2-08](#l2-08) | 2 | 11 | 45-75 | An MST region is a shared map, not just a shared name |
| [L2-09](#l2-09) | 2 | 12 | 45-75 | Two cables, one contract |
| [L2-10](#l2-10) | 2 | 12, 34 | 45-75 | Two chassis still need one agreed story |
| [L2-11](#l2-11) | 2 | 10, 30, 52 | 45-75 | Rate-limit the noise without silencing the service |
| [L2-12](#l2-12) | 2 | 12, 17, 64 | 45-75 | The gateway address survives; the service must too |
| [IGP-01](#igp-01) | 3 | 16, 18 | 45-90 | Give the router an identity that does not move with a cable |
| [IGP-02](#igp-02) | 3 | 5, 16, 17 | 45-90 | Use both addresses of the link, not a classroom subnet convention |
| [IGP-03](#igp-03) | 3 | 16, 17 | 45-90 | A route needs a next hop and a way home |
| [IGP-04](#igp-04) | 3 | 16, 17, 64 | 45-90 | A backup route floats only when the first candidate stops winning |
| [IGP-05](#igp-05) | 3 | 16, 18 | 45-90 | Full is an adjacency state, not a service report |
| [IGP-06](#igp-06) | 3 | 18 | 45-90 | Two routers do not need a designated-router election |
| [IGP-07](#igp-07) | 3 | 16, 18 | 45-90 | Cost is a direction, not a cable label |
| [IGP-08](#igp-08) | 3 | 18 | 45-90 | An area boundary changes what the router knows |
| [IGP-09](#igp-09) | 3 | 18, 50, 52 | 45-90 | A neighbour must know the key, not merely the subnet |
| [IGP-10](#igp-10) | 3 | 5, 18, 52 | 45-90 | IPv6 routing still has a 32-bit router ID |
| [IGP-11](#igp-11) | 3 | 16, 19, 24 | 45-90 | The IGP that does not need IP to say Hello |
| [IGP-12](#igp-12) | 3 | 19, 24 | 45-90 | Two levels, one deliberate boundary |
| [IGP-13](#igp-13) | 3 | 16, 17, 19, 64 | 45-90 | Detect a dead path while the cable still looks alive |
| [IGP-14](#igp-14) | 3 | 16, 18, 52 | 45-90 | Advertise the room without inviting neighbours inside |
| [BGP-01](#bgp-01) | 4 | 20, 21, 52 | 60-90 | Established is permission to start asking questions |
| [BGP-02](#bgp-02) | 4 | 20, 21, 52 | 60-90 | The route arrived; its next hop did not |
| [BGP-03](#bgp-03) | 4 | 20, 21, 24, 52 | 60-90 | An allowlist should be boringly exact |
| [BGP-04](#bgp-04) | 4 | 20, 21, 24, 52 | 60-90 | Originate a promise you can actually keep |
| [BGP-05](#bgp-05) | 4 | 20, 21, 24, 52 | 60-90 | Attach meaning, then prove it survived the trip |
| [BGP-06](#bgp-06) | 4 | 20, 21, 24, 64 | 60-90 | Choose your exit before the Internet chooses for you |
| [BGP-07](#bgp-07) | 4 | 20, 21, 24, 52 | 60-90 | Influence the far end without pretending to control it |
| [BGP-08](#bgp-08) | 4 | 20, 21, 24, 32 | 60-90 | Reflect the route, preserve the forwarding question |
| [BGP-09](#bgp-09) | 4 | 20, 21, 24, 64 | 60-90 | A prefix fuse is different from a prefix filter |
| [BGP-10](#bgp-10) | 4 | 20, 21, 24, 52 | 60-90 | Authenticate the session, not the business relationship |
| [BGP-11](#bgp-11) | 4 | 20, 21, 32, 34, 64 | 60-90 | Two good paths do not make every packet alternate |
| [BGP-12](#bgp-12) | 4 | 20, 21, 24, 64, 67 | 60-90 | Graceful is a measured outcome, not a command name |
| [BGP-13](#bgp-13) | 4 | 20, 21, 24, 52, 64 | 60-90 | Valid means authorised origin, not a safe route |
| [BGP-14](#bgp-14) | 4 | 20, 21, 24, 52, 64 | 60-90 | A learned route is not automatically yours to resell |
| [VPN-01](#vpn-01) | 5 | 22, 23, 27, 32 | 60-120 | Same address, different room |
| [VPN-02](#vpn-02) | 5 | 22, 23, 27, 32 | 60-120 | Open a service door, not the whole building |
| [VPN-03](#vpn-03) | 5 | 23, 24, 25, 52 | 60-120 | A label is a local promise |
| [VPN-04](#vpn-04) | 5 | 24, 25, 26, 52 | 60-120 | Reserve the path; prove the passenger |
| [VPN-05](#vpn-05) | 5 | 24, 25, 26, 52 | 60-120 | The index travels; the label changes |
| [VPN-06](#vpn-06) | 5 | 25, 26, 27, 52 | 60-120 | An IPv6 address with a job description |
| [VPN-07](#vpn-07) | 5 | 22, 23, 24, 27, 52 | 60-120 | Two labels, two responsibilities |
| [VPN-08](#vpn-08) | 5 | 22, 23, 27, 52 | 60-120 | The name badge and the guest list |
| [VPN-09](#vpn-09) | 5 | 24, 27, 28, 52 | 60-120 | A wire that crosses a core |
| [VPN-10](#vpn-10) | 5 | 28, 29, 52 | 60-120 | Three sites, one LAN, no shortcut |
| [VPN-11](#vpn-11) | 5 | 29, 30, 31, 52 | 60-120 | The MAC address gets a control plane |
| [VPN-12](#vpn-12) | 5 | 29, 32, 33, 52 | 60-120 | Stretch a service, contain the consequences |
| [DC-01](#dc-01) | 6 | 30, 31, 34, 52 | 60-120 | Build the floor before decorating it |
| [DC-02](#dc-02) | 6 | 20, 30, 34, 52 | 60-120 | Unnumbered does not mean unaddressed |
| [DC-03](#dc-03) | 6 | 30, 31, 34, 52 | 60-120 | A VTEP is an endpoint, not a promise |
| [DC-04](#dc-04) | 6 | 29, 30, 31, 52 | 60-120 | Follow one MAC from host to remote FDB |
| [DC-05](#dc-05) | 6 | 30, 31, 34, 52 | 60-120 | An IP prefix takes the routed entrance |
| [DC-06](#dc-06) | 6 | 30, 31, 34, 52 | 60-120 | The gateway is wherever the host is |
| [DC-07](#dc-07) | 6 | 23, 30, 31, 34, 52 | 60-120 | Two chassis, one fabric attachment |
| [DC-08](#dc-08) | 6 | 20, 21, 30, 32, 34, 64 | 60-120 | A fabric with more than one way home |
| [DC-09](#dc-09) | 6 | 9, 23, 30, 34, 52 | 60-120 | The packet grew a jacket |
| [DC-10](#dc-10) | 6 | 9, 30, 36, 52, 81 | 60-120 | SONiC: find the owner before editing the tenant |
| [DC-11](#dc-11) | 6 | 30, 34, 37, 52, 61 | 60-120 | The tenant door has a precise guest list |
| [DC-12](#dc-12) | 6 | 30, 32, 34, 36, 52, 64 | 60-120 | Pause is local; congestion is a conversation |
| [QOS-01](#qos-01) | 7 | 32, 34, 52, 64 | 60-120 | A marking finds its queue |
| [QOS-02](#qos-02) | 7 | 32, 34, 37, 52, 64 | 60-120 | Trust is a boundary, not a compliment |
| [QOS-03](#qos-03) | 7 | 32, 34, 52, 64 | 60-120 | Sharing the queue without starving the neighbour |
| [QOS-04](#qos-04) | 7 | 32, 34, 52, 64 | 60-120 | Make the burst wait its turn |
| [QOS-05](#qos-05) | 7 | 32, 34, 37, 52, 64 | 60-120 | The bucket has a budget |
| [QOS-06](#qos-06) | 7 | 32, 34, 52, 64 | 60-120 | Warn early; measure the conversation |
| [QOS-07](#qos-07) | 7 | 32, 34, 52, 64 | 60-120 | A per-hop promise travels through a path |
| [QOS-08](#qos-08) | 7 | 32, 34, 52, 64, 80 | 60-120 | Publish the evidence, not the knob position |
| [SEC-01](#sec-01) | 8 | 37, 52, 61 | 45-90 | A source-only gate needs the right location |
| [SEC-02](#sec-02) | 8 | 37, 52, 61 | 45-90 | A service gate names both endpoints and the port |
| [SEC-03](#sec-03) | 8 | 9, 37, 51, 52, 61 | 45-90 | Protect the prompt without losing the rescue rope |
| [SEC-04](#sec-04) | 8 | 51, 52, 57, 61 | 45-90 | Give the control plane a measured budget |
| [SEC-05](#sec-05) | 8 | 5, 16, 51, 57 | 45-90 | A valid source can arrive through the wrong door |
| [SEC-06](#sec-06) | 8 | 4, 10, 51, 52, 57 | 45-90 | Trust the server path, then inspect the claimed binding |
| [SEC-07](#sec-07) | 8 | 4, 10, 51, 57 | 45-90 | One port, one expected speaker |
| [SEC-08](#sec-08) | 8 | 7, 51, 52, 57, 61 | 45-90 | Authenticate the speaker, then test the service |
| [SEC-09](#sec-09) | 8 | 7, 51, 52, 57 | 45-90 | A zone boundary has a direction and a memory |
| [SEC-10](#sec-10) | 8 | 5, 7, 51, 53 | 45-90 | Follow the tuple through translation |
| [SEC-11](#sec-11) | 8 | 7, 51, 54, 55, 57 | 45-90 | Build the encrypted path and keep the clear path closed |
| [SEC-12](#sec-12) | 8 | 7, 51, 54, 55, 62 | 45-90 | Make the wire testify |
| [SEC-13](#sec-13) | 8 | 20, 21, 32, 33, 51, 57 | 45-90 | A route is also a request for authority |
| [SEC-14](#sec-14) | 8 | 21, 32, 33, 51, 57 | 45-90 | Mitigation needs an owner and an expiry |
| [OPS-01](#ops-01) | 9 | 42, 52, 64, 65 | 45-90 | A poll should reveal counters, not credentials |
| [OPS-02](#ops-02) | 9 | 42, 52, 64, 65 | 45-90 | Turn down the noise without losing the warning |
| [OPS-03](#ops-03) | 9 | 42, 64, 65 | 45-90 | A flow record is a measurement with assumptions |
| [OPS-04](#ops-04) | 9 | 42, 64, 65 | 45-90 | One sample is not the whole conversation |
| [OPS-05](#ops-05) | 9 | 42, 64, 65, 69 | 45-90 | Subscribe to a fact, not a guess |
| [OPS-06](#ops-06) | 9 | 68, 69, 70 | 45-90 | The hello tells you what the server can do |
| [OPS-07](#ops-07) | 9 | 68, 69, 70 | 45-90 | HTTPS is a transport, not a common data model |
| [OPS-08](#ops-08) | 9 | 42, 64, 66 | 45-90 | A locked clock still needs a witness |
| [OPS-09](#ops-09) | 9 | 42, 64, 66 | 45-90 | Frequency is not a timestamp |
| [OPS-10](#ops-10) | 9 | 42, 52, 64, 65 | 45-90 | A copy has a point of view |
| [OPS-11](#ops-11) | 9 | 42, 52, 64, 65 | 45-90 | The device capture is one witness |
| [OPS-12](#ops-12) | 9 | 42, 52, 64, 65 | 45-90 | Give the counter a denominator |
| [AUT-01](#aut-01) | 10 | 52, 68–72 | 60-120 | Inventory before ingenuity |
| [AUT-02](#aut-02) | 10 | 52, 68–72 | 60-120 | The template that refuses to guess |
| [AUT-03](#aut-03) | 10 | 52, 68–72 | 60-120 | The second run earns the word idempotent |
| [AUT-04](#aut-04) | 10 | 52, 68–72 | 60-120 | One API, several observation boundaries |
| [AUT-05](#aut-05) | 10 | 52, 68–72 | 60-120 | A transaction with a way home |
| [AUT-06](#aut-06) | 10 | 52, 68–72 | 60-120 | A diff is a proposal, not permission |
| [AUT-07](#aut-07) | 10 | 52, 68–72 | 60-120 | Prove the preconditions before the change |
| [AUT-08](#aut-08) | 10 | 52, 68–72 | 60-120 | Make CI a skeptical colleague |
| [AUT-09](#aut-09) | 10 | 52, 68–72 | 60-120 | Restoration is a test, not a promise |
| [AUT-10](#aut-10) | 10 | 52, 68–72 | 60-120 | Golden configuration, with fingerprints |
| [AUT-11](#aut-11) | 10 | 52, 68–72 | 60-120 | An event may ask; it may not push |
| [AUT-12](#aut-12) | 10 | 52, 68–72 | 60-120 | The guardrail says no, usefully |

## DEV-01

Get to a prompt, and know which mode you are in

**Read:** current book chapters 9, 51.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a platform console and a recovery path; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 30-60 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Name the mode from the prompt; try a harmless configuration command in operational mode and retain the refusal before applying it in the correct mode.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; chapter updated 2023-08-21 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification |
| srl | READ | SR Linux 24.3 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## DEV-02

Hostname, banner and a device identity

**Read:** current book chapters 9, 51.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a platform console and a recovery path; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 30-60 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A fresh session displays the expected warning; the operational hostname agrees with the inventory. FRR covers CLI identity only.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9500 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification; Junos OS; guide revision 2026-06-26; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## DEV-03

Save, diff and recover: rehearse the whole sequence

**Read:** current book chapters 9, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a platform console and a recovery path; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 30-60 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** The before/change/recovered observations identify the same field. A fresh session sees the restored value and the saved configuration contains it. On timed-commit platforms, demonstrate the timeout before separately rehearsing confirmation. FRR uses an interface description because its CLI hostname is not saved.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## DEV-04

Build a management path that survives the data-plane mistake

**Read:** current book chapters 9, 51.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a platform console and a recovery path; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 30-60 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** The management peer reaches the node through the recorded interface and routing instance. Identify the actual peer route and service binding. Fault a production path that is carrying a separate probe and prove that probe fails while management survives. A same-subnet management ping alone does not demonstrate out-of-band independence. Restore the fault and capture both results.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-26; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## DEV-05

Create an account, then prove what it cannot do

**Read:** current book chapters 9, 51, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a platform console and a recovery path; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 30-60 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A fresh session authenticates with a private lab password. Its effective role or privilege matches the inventory; a denied operation is recorded for restricted accounts. Keep the original console administrator until this passes.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-26; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fortios | READ | FortiOS 7.6.6; CLI Reference |

## DEV-06

SSH: check the key, not just the padlock

**Read:** current book chapters 9, 51, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a platform console and a recovery path; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 30-60 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A fresh SSH client authenticates with the intended account and trusted host fingerprint. For panels that install a user public key, require a public-key-only login; the IOS XE panel covers host keys, ciphers and VTY transport only. Record the negotiated algorithms and effective role. Inventory and probe management listeners, including all VTY ranges. Report observed Telnet exposure or refusal; enabling SSH alone does not prove Telnet is disabled. Restore any changed policy after a second session succeeds.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-26; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fortios | READ | FortiOS 7.6.6; CLI Reference |

## DEV-07

AAA fallback: a refusal is not a timeout

**Read:** current book chapters 51, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a platform console and a recovery path; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 30-60 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Record accepted, explicitly rejected and timed-out AAA attempts from fresh sessions, including effective roles and server/client logs. Test the intended local recovery account under the documented failure condition and use it to restore the original policy. A working read-only account is not proof that the operator can repair AAA.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-26; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fortios | READ | FortiOS 7.6.6; CLI Reference |

## DEV-08

Synchronise time before comparing evidence

**Read:** current book chapters 51, 52, 61.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a platform console and a recovery path; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 30-60 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Record the selected source and reported offset over five minutes; use 20 ms as a declared lab offset tolerance, not proof of UTC accuracy. During a 15-minute controlled source outage record reachability and synchronisation/holdover transitions with elapsed times; do not demand an immediate unsynchronised alarm. Isolate alternate sources, trial a wrong key where configured, restore the correct key and demonstrate reacquisition.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9500 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fortios | READ | FortiOS 7.6.6; CLI Reference |

## DEV-09

Send a log, then find it at the other end

**Read:** current book chapters 61, 62.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a platform console and a recovery path; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 30-60 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Identify an actual local test event before choosing the remote filter. Find its repeated timestamp, node identity and message at the collector and record source address, transport, severity and a five-minute search window. Repeat during a two-minute collector outage and after recovery; report observed loss or buffering rather than assuming delivery guarantees.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9500 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-06; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## DEV-10

Stage an image without deleting your way home

**Read:** current book chapters 9, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a platform console and a recovery path; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 30-60 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Retain the pre-upgrade image/configuration identities, trusted download evidence, expected and measured interruption, post-upgrade tests, and a successful backout result. Documentation READ is not proof that this upgrade has been executed.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-09-08; no release qualification; Junos OS; base command predates 7.4; maintained command reference; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fortios | READ | FortiOS 7.6.6; CLI Reference |

## L2-01

A green LED is not an IP path

**Read:** current book chapters 5, 9, 16.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated switching topology and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-75 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** The peer uses 198.51.100.2/30 and the node 198.51.100.1/30. Capture configuration, admin/carrier state, neighbour resolution and a bidirectional probe. On physical equipment remove the cable, observe carrier and probe failure, restore it and prove recovery. In a virtual lab disconnect the virtual link or administratively disable it and label the resulting trial as virtual; it does not test PHY or transceiver behaviour. Retain console access throughout.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification; Junos OS; guide revision 2026-06-26; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fortios | READ | FortiOS 7.6.6; CLI Reference |

## L2-02

The port label, the packet budget and the link agreement

**Read:** current book chapters 3, 4, 16.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated switching topology and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-75 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Record description, configured and operational speed/duplex, negotiation policy, media and IP MTU. First classify a directly attached client DF probe as a local send-limit test; local EMSGSIZE is not evidence of a DUT drop. To test DUT egress, prepare a three-node routed path A--DUT--B: ingress and A support at least 1600-byte IP packets; this task sets the DUT egress to 1500; B returns traffic through the DUT. Enable lab forwarding and any required transit firewall policy before the test. Send IPv4 DF packets toward B with 1472 and 1473 ICMP payload bytes, then capture at ingress and egress. With 20-byte IPv4 and 8-byte ICMP headers, these are 1500 and 1501 bytes. Distinguish local rejection, DUT ICMP fragmentation-needed and silent loss. Restore the baseline.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fortios | READ | FortiOS 7.6.6; CLI Reference |

## L2-03

Give two hosts a shared Ethernet room

**Read:** current book chapters 4, 10.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated switching topology and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-75 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Host A and B use untagged frames and addresses 198.51.100.10/24 and .11/24. Their MAC addresses are learned on the intended ports/domain and bidirectional traffic succeeds without a gateway. Inject a tagged test frame and record its treatment on this exact platform; do not infer tag rejection from the word access. Move one host into a separate prepared bridge domain, prove isolation and restore it.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-09-23; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |

## L2-04

A trunk is a contract between two ports

**Read:** current book chapters 10.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated switching topology and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-75 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Prepare matching access hosts/domains on switches A and B. Capture a VLAN-10 and VLAN-20 frame on the inter-switch link and prove same-VLAN reachability in both directions. Inject VLAN 30, verify it is excluded and prove host probes for the other two still pass. Record untagged-data treatment separately for L2-05. Break one admitted VLAN on one end, diagnose the asymmetric failure and restore it.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-09-23; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |

## L2-05

The tag that is missing is still a decision

**Read:** current book chapters 10.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated switching topology and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-75 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** On the isolated L2-04 link, send an untagged frame and identify the receiving bridge domain/MAC-learning context. Capture the return frame to establish the actual egress tag policy. Tagged VLAN 20 continues to work. Deliberately mismatch the untagged classification at one end, observe the wrong-domain or failed result and restore the agreed policy. Also record how tagged VLAN 10 and priority-tagged VLAN 0 are handled; do not infer that from the native VLAN name.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-09-23; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |

## L2-06

Elect the root before the network elects one for you

**Read:** current book chapters 11.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated switching topology and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-75 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Start with a line of three bridges and management outside the test links. Set the intended root priority to 4096, the planned secondary to 8192 and the third to 32768. Verify every node agrees on root ID and instance scope before closing the triangle. Capture one alternate/discarding path, continuous probe sequence numbers and the measured transition after removing one active link. Restore the link and baseline. Record the actual protocol mode and BPDU version; do not report legacy STP as RSTP.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2025-12-11; no release qualification |
| sros | READ | SR OS 25.3.R1 |
| aoscx | READ | AOS-CX 10.13; 6300/6400 guide, March 2024, version 2 |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |

## L2-07

An edge port should not accept a new boss

**Read:** current book chapters 11, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated switching topology and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-75 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** On the host-facing port, a normal host works; an isolated lab bridge sending BPDUs triggers the documented guard action. On a different downstream bridge-facing port, ordinary BPDUs work, but a superior-root proposal cannot replace the intended root and the protected path stops forwarding as documented. Record alarms, port state and recovery. Remove the offending bridge before resetting a disabled port; prove normal host traffic and the intended root afterwards.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2025-12-11; no release qualification |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |
| aoscx | READ | AOS-CX 10.13.1000; April 2024, edition 1; AOS-CX 10.13; 6300/6400 guide, March 2024, version 2 |
| vyos | NO_PANEL | The returned VyOS 1.4 bridge guide establishes STP and bridge membership, but does not establish the edge, BPDU-guard and root-guard recipe required here. Ordinary bridge participation is not equivalent to these protections. |

## L2-08

An MST region is a shared map, not just a shared name

**Read:** current book chapters 11.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated switching topology and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-75 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Use region WB-REGION, revision 1, VLAN 10 in MSTI 1 and VLAN 20 in MSTI 2; other VLANs remain in instance 0 unless deliberately mapped. All nodes inside the intended region report the same complete map/digest. Change one peer revision, observe a boundary and continued controlled forwarding, then restore it and prove region agreement. Inspect CIST and each MSTI root/role separately.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2025-12-11; no release qualification |
| sros | READ | SR OS 25.3.R1 |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |
| aoscx | READ | AOS-CX 10.13; 6300/6400 guide, March 2024, version 2 |

## L2-09

Two cables, one contract

**Read:** current book chapters 12.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated switching topology and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-75 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** On each end, both members report the same partner system and compatible partner key; A actor identity/key match B partner identity/key and vice versa. Both members are synchronized, collecting and distributing. Use several independent traffic flows and inspect per-member counters; a single flow need not exceed one member rate. Unplug one labelled member, record packet loss and recovery time, and show continued forwarding on the survivor. Reconnect and prove two-member recovery. A separate passive/passive trial must not be labelled a successful negotiated bundle; restore active operation before finishing.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-26; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |

## L2-10

Two chassis still need one agreed story

**Read:** current book chapters 12, 34.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated switching topology and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-75 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Before connecting the client, both peers agree on domain, client aggregate identifier, VLAN/service policy and LACP system identity/key as applicable; control adjacency and peer data path are healthy. The client sees one eligible partner system across its members. Test one client member failure, one chassis outage and peer-data-link-only failure separately, recording forwarding, suspension and orphan-port behaviour. Restore health between faults. Inspect the documented split-brain policy before attempting combined peer-link/control loss; do that combined trial only inside a disposable isolated topology. Restore both peer paths and prove the original client membership and traffic.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x); Nexus 9000 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-23; no release qualification |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |
| aoscx | READ | AOS-CX 10.13; VSX guide, 6400/8xxx/9300/10000 |
| sros | READ | SR OS 25.3.R1 |

## L2-11

Rate-limit the noise without silencing the service

**Read:** current book chapters 10, 30, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated switching topology and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-75 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Record the effective hardware threshold, units, monitored traffic classes, aggregation scope and any burst/window behaviour. Send a marked low-rate broadcast baseline, a bounded above-threshold trial for 10 seconds and then the baseline again; compare offered and received counts, relevant drop counters and timestamps. Keep a low-rate known-unicast positive control through the same protected ingress running, plus an independent unicast pair as a general lab-health control. Stop the generator and prove normal forwarding returns with protection still enabled. Never equate identical numeric values across percent, kbps and packets per second. Do not require exact threshold arithmetic when hardware quantization or accounting overhead differs; report measured behaviour.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| nxos | READ | NX-OS 10.5(x); Nexus 9000 |
| junos | READ | Junos OS; guide revision not stated; no release qualification |
| srl | READ | SR Linux 24.10 |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |

## L2-12

The gateway address survives; the service must too

**Read:** current book chapters 12, 17, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated switching topology and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-75 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A and B have physical addresses .2/.3 on 203.0.113.0/24 and share virtual gateway .1, group 10. A uses priority 150 and B 100; neither owns .1 as its physical address. Capture the elected active/master role, advertisements, virtual MAC and host neighbour entry. Run a timestamped probe through .1 to a routed test destination with working return routes via both routers. Stop A, measure loss/takeover, restore A and observe the declared preemption behaviour. Then fail A upstream while keeping its client-facing interface up: without tracking, a healthy gateway election can still blackhole service. Restore it and explain the distinction; this task does not claim upstream tracking was configured.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-29; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fortios | READ | FortiOS 7.6.6; CLI Reference |

## IGP-01

Give the router an identity that does not move with a cable

**Read:** current book chapters 16, 18.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Node A uses loopback/router ID 203.0.113.1 and node B .2; maintain a unique allocation ledger. Show the configured loopback/router ID and prove the local /32 is installed. Inspect the effective OSPF router ID only where a process is actually instantiated; defer that operational check to IGP-05 when area/interfaces are present. Removing an unrelated physical link does not remove the local loopback or change the configured ID. Remote reachability is not required until IGP-05 advertises the address: a configured ID alone does not install a remote route. If an OSPF process already exists, record whether changing its ID requires a controlled restart; do not clear a live adjacency as an undocumented shortcut.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; IOS XE 17.x; maintained OSPF configuration chapter |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification; Junos OS; guide revision not stated; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## IGP-02

Use both addresses of the link, not a classroom subnet convention

**Read:** current book chapters 5, 16, 17.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A uses 198.51.100.0/31 and 2001:db8:100::/127; B uses .1 and ::1. Both addresses are host endpoints on these two-node links. Prove reciprocal direct pings with the intended source/interface, connected routes, IPv4 ARP and IPv6 neighbour/link-local state. Compare with the earlier /30 pair, explicitly removing its captured old addresses before this replacement. Disconnect the physical link, observe interface and connected-route changes, then reconnect and prove recovery. A peer timeout must be diagnosed with neighbour/capture evidence rather than declaring the .0 address invalid.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## IGP-03

A route needs a next hop and a way home

**Read:** current book chapters 16, 17.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** On A, 203.0.113.2/32 selects the specific route via B at 198.51.100.1; an otherwise unmatched test destination selects the default via the same peer. B has a return /32 route to A’s loopback via 198.51.100.0. Source a probe from 203.0.113.1 to B’s loopback and capture both directions. Show configured routes, selected RIB entries, programmed forwarding entries and resolved ARP. Remove only the specific route: the default may still forward the probe, so a working ping does not prove the specific route remains. Restore it. Remove the return route briefly and explain why A’s forward route alone cannot guarantee a reply, then restore and verify. Before calling return-route removal a loss-of-return-path fault, inspect B’s longest-prefix match to A’s probe source and prove no alternate/default/dynamic route remains; otherwise label the observation a candidate-removal trial.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision not stated; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## IGP-04

A backup route floats only when the first candidate stops winning

**Read:** current book chapters 16, 17, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A reaches B loopback203.0.113.2/32 through primary next-hop198.51.100.1 at preference/distance10 and backup198.51.100.3 at200. Both peer links and reciprocal return paths already work. Show the selected primary and retained backup candidate; record forwarding next hop. Shut A’s primary interface so its connected next-hop resolution is lost, measure traffic loss and backup selection, then restore primary and prove re-selection. Separately keep A’s primary carrier up while temporarily removing B’s destination loopback address (using the captured inverse configuration): the static route may remain selected and blackhole traffic. No end-to-end health tracking is configured here; distinguish that result from link-based route withdrawal.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-02-17; no release qualification |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |
| fortios | READ | FortiOS 7.6.6; CLI Reference |

## IGP-05

Full is an adjacency state, not a service report

**Read:** current book chapters 16, 18.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A/B have unique effective router IDs, their transit interfaces in area0, matching authentication/network type/Hello-dead settings and compatible MTU. The two-node transit adjacency reaches Full; record DR/BDR roles if the inspected network type is broadcast. Each peer learns the other loopback as an OSPF route, installs the expected forwarding next hop and passes a loopback-source probe with a return path. Temporarily change only B’s transit area to1; capture the mismatch and adjacency/route loss, then restore0 and prove recovery. A remaining static/default route may preserve ping during the fault, so isolate the IGP trial and do not infer adjacency health from ping alone.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## IGP-06

Two routers do not need a designated-router election

**Read:** current book chapters 18.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Capture the IGP-05 network type, Hello/DBD packets, DR/BDR state and area LSAs first. Apply point-to-point at both ends; adjacency recovers Full, no DR/BDR is elected on that interface, and the router-LSA describes the point-to-point relationship. Compare transit-network-LSA behaviour with the preceding broadcast trial; retain per-link proof rather than expecting unrelated Type2 LSAs to disappear from a whole area. Route installation and loopback-source traffic still pass. Restore the captured broadcast settings if continuing a comparison, or explicitly record point-to-point as the new baseline for IGP-07.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | Cisco IOS OSPF maintained command reference; base syntax history in source; no target-release qualification |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## IGP-07

Cost is a direction, not a cable label

**Read:** current book chapters 16, 18.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Both links form Full point-to-point area0 adjacencies. On A, primary cost10 and alternate20 select the primary next hop for B’s loopback; retain the router-LSA metric and installed route cost. Repeat the prediction on B using its own outbound costs; do not infer symmetrical forwarding from one screen. Change A primary to30: the alternate20 wins without a physical cable failure. Set both A costs20 and inspect whether the target installs/uses multiple equal-cost next hops under its effective maximum-paths policy; do not require one flow to alternate packets. Restore primary10/alternate20 and prove expected forwarding. Measure loss/change timing, not an invented universal convergence time.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained OSPF configuration chapter |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## IGP-08

An area boundary changes what the router knows

**Read:** current book chapters 18.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A-B remains area0; B-C and C loopback203.0.113.3/32 belong to area10. B reports ABR status and C learns A’s loopback as inter-area information. Capture a normal-area baseline first. Configure ordinary stub at both B and C for area10; Full adjacency recovers and C receives a default from B while Type5 external LSAs are excluded from area10. Existing specific inter-area summaries remain permitted; do not confuse ordinary stub with no-summary variants. If no external LSA existed in the normal baseline, mark exclusion not exercised until a separately scoped lab ASBR originates a test external prefix. Deliberately mismatch only C’s stub setting, observe the area-capability/adjacency failure, then restore and prove routes and return traffic.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained OSPF configuration chapter |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## IGP-09

A neighbour must know the key, not merely the subnet

**Read:** current book chapters 18, 50, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** On the isolated A-B area0 link, configure matching algorithm, key ID and private lab secret at both ends; Full adjacency and loopback routing recover. Capture authentication type/key ID and failed-authentication counters without exposing the secret. Change only B’s secret to a different lab value; authenticated Hellos are rejected and the existing adjacency expires according to its inspected dead timer rather than an assumed immediate event. Restore the shared key and prove adjacency, routes and forwarding. Record effective key lifetimes/clock behaviour where keychains are used. A packet capture still shows routing information: message authentication does not encrypt it. The MD5 adapters are legacy compatibility exercises, not the production security recommendation.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained OSPF configuration chapter |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## IGP-10

IPv6 routing still has a 32-bit router ID

**Read:** current book chapters 5, 18, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A/B transit IPv6 addresses from IGP-02 and link-local neighbours work before OSPFv3 starts. Allocate A2001:db8:ffff::1/128 and B::2/128 on loopbacks; router IDs remain203.0.113.1/.2. Both transit interfaces use area0 and compatible instance/network-type/timer settings. OSPFv3 reaches Full, the remote /128 is installed and a loopback-source IPv6 probe passes with a return route. Record link-local adjacency/forwarding next hop together with its interface zone; a bare fe80 address is ambiguous across links. Change only B’s area, observe neighbour/route loss, then restore and prove recovery. Existing IPv4 OSPF authentication does not establish protection for this separate OSPFv3 control exchange.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## IGP-11

The IGP that does not need IP to say Hello

**Read:** current book chapters 16, 19, 24.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A/B use area49.0001 with unique six-byte system IDs and selector00. Record the operational NET/system ID and enabled level/address family on each node. The transit adjacency reaches Up at Level2; the peer loopback appears in the IS-IS database, selected route and programmed forwarding table, and a loopback-source probe passes with a return path. Capture Ethernet LLC/IS-IS control packets separately from IPv4 user traffic: a neighbour Up does not prove IPv4 addressing or forwarding works. Remove only A’s transit IPv4 address while leaving IS-IS layer2 participation/carrier intact; record whether adjacency remains Up while numbered IPv4 forwarding loses its prerequisite. Restore the exact address and prove recovery. Address-removal outcome depends on unnumbered support and alternative resolution: record observed forwarding rather than assuming universal failure. Exclude alternate paths and unnumbered fallback from the numbered baseline or explicitly classify them as a different trial.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxr | READ | IOS XR 24.1.x–24.4.x; ASR 9000, chapter updated 2024-12-16 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-16; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## IGP-12

Two levels, one deliberate boundary

**Read:** current book chapters 19, 24.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A-B forms Level1 in area49.0001; B-C forms Level2 with C in area49.0002. B maintains distinct Level1 and Level2 databases. Record B attached-bit behavior and A selected default next hop toward B, then prove A-to-C loopback traffic and its return path. Do not require every Level2-specific route in A Level1 database: default reachability is not automatic detailed downward leaking. Shut only B-C; after convergence record the attached-bit/default change and failed remote reachability while A-B remains Up. Restore B-C and prove recovery. Capture any static/default substitutes and remove them before awarding protocol-derived acceptance.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxr | READ | IOS XR 24.1.x–24.4.x; ASR 9000, chapter updated 2024-12-16 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-16; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## IGP-13

Detect a dead path while the cable still looks alive

**Read:** current book chapters 16, 17, 19, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Both endpoints show OSPF Full and a BFD session Up with the intended client binding. Record negotiated transmit/receive intervals, multiplier, mode and resulting detection time in each direction. Nominal300 ms and multiplier3 are a starting request, not a measured900 ms service guarantee. With carrier retained, a lab bridge blocks BFD control UDP3784 in both directions while allowing OSPF/IP and management; record last received BFD packet, session Down, OSPF reaction, RIB/FIB change and end-to-end loss/recovery timestamps. Compare with the same fault after BFD is unbound: OSPF may remain Full because its Hellos still pass. Restore the bridge rule and bindings. Pulling a cable may be an extra comparison, but does not satisfy this carrier-up experiment. Use the remote learned loopback as the traffic target, not directly connected peer addresses that remain reachable during BFD failure. On this two-node baseline, service recovery is expected after filter removal and protocol recovery; without a prepared alternate path do not promise failover. Observe possible repeated OSPF restart/re-adjacency while BFD remains blocked and record the actual behavior.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## IGP-14

Advertise the room without inviting neighbours inside

**Read:** current book chapters 16, 18, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** an isolated routing topology and reachability probes; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Baseline OSPF is Full on the primary transit and the peer installs A loopback. Capture shows Hellos on transit and none originated from passive loopback; inspect the loopback prefix in the peer database/route/FIB and prove sourced return traffic. Temporarily make A transit passive using this panel: verify Hello cessation, adjacency expiry/removal and peer-route loss while link carrier and connected addressing remain. Restore the exact captured active transit setting and prove recovery, leaving loopback passive. In a separate candidate diff, remove loopback OSPF membership and compare lost advertisement with passive membership; restore it. Remove static substitutes so forwarding cannot hide route withdrawal.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## BGP-01

Established is permission to start asking questions

**Read:** current book chapters 20, 21, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A AS 64500 and B AS64510 use the primary /31 and unique router IDs. Both report Established with the intended remote AS, IPv4-unicast capability and expected source/peer addresses. Record received, accepted, advertised and installed routes separately; an empty table or policy rejection is a legitimate session-only result, not a failed session. No customer route origination or permit-all policy is introduced here. Change only B remote-as to an incorrect lab AS, capture Open/notification failure and session loss, then restore and prove Established. Retain logs without exposing secrets. No traffic-through-the-peer claim is awarded until BGP-03/04 supplies explicit prefix policy and route eligibility.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## BGP-02

The route arrived; its next hop did not

**Read:** current book chapters 20, 21, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A and C AS 64500 establish iBGP between loopbacks203.0.113.1/.3, using a prepared IGP or exact static underlay for those loopbacks only. A external B AS64510 advertises exactly192.0.2.100/32 under a documented prefix filter; C receives that route through A with original next hop198.51.100.1 and initially cannot resolve that next hop. Capture C BGP valid/selected status, RIB and FIB before change. Apply next-hop-self on A toward C; capture changed advertised next hop, its recursive resolution to A and C selected/programmed route. A must still resolve B and B must have an explicit return path to C source. Source a probe from C loopback to the real B test loopback; restore the captured next-hop treatment and compare. An Established loopback-sourced session alone does not satisfy the forwarding test.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## BGP-03

An allowlist should be boringly exact

**Read:** current book chapters 20, 21, 24, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A permits only192.0.2.200/32 inbound from B and only192.0.2.100/32 outbound to B; B reciprocal policy reverses them. Prepared actual loopbacks/originations and return routes make both test prefixes real. The test speaker also sends192.0.2.0/24,192.0.2.201/32 and0.0.0.0/0; record those updates received at the wire/peer while the allowlist prevents their acceptance. Verify intended prefix selected/installed and unintended prefixes absent from accepted routes/FIB. For export, inspect what the peer actually receives, not just a local policy counter. Remove only the intended allow entry in a controlled lab, refresh/re-advertise, observe withdrawal/rejection and restore. Do not confuse an unavailable pre-policy table with proof no unwanted update arrived.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; IOS XE 17.x; maintained external-service-provider BGP chapter |
| eos | READ | EOS 4.36.2F |
| frr | READ | FRR 10.2 |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |

## BGP-04

Originate a promise you can actually keep

**Read:** current book chapters 20, 21, 24, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A has an active static192.0.2.100/32 to a real isolated service host through a separate prepared service link. Exact export allowlist and B reciprocal import allowlist from BGP-03 are attached before origination. B receives and accepts only that intended prefix and installs its correct next hop; with reciprocal return route, a service probe passes. Remove only A backing static while leaving eBGP Up. Record local origin/export withdrawal and B route removal after convergence; restore the exact static and prove route/service recovery. If the platform still originates without the backing route, diagnose effective origination/import-check options rather than accepting a routing black hole. No aggregate or broad redistribute-connected is used.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained Basic BGP chapter |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## BGP-05

Attach meaning, then prove it survived the trip

**Read:** current book chapters 20, 21, 24, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A tags its exported192.0.2.100/32 with standard community64500:100, whose equivalent32-bit decimal encoding is4227072100. Record any pre-existing communities before change; replacement versus additive behavior is deliberate and documented. B receives the same intended community on the actual route while prefix allowlists remain unchanged. The tag alone must not change path preference: record unchanged selected next hop unless an explicit matching downstream policy exists. In a second prepared B policy, match this tag and apply a documented preference action; compare before/after attribute and path selection, then remove that policy and prove recovery. If community transmission is disabled or stripped, distinguish local tagging from wire/peer reception. The downstream selection phase requires a prepared second eligible path with resolvable next hop and equal earlier attributes; without it record only preference-attribute transformation and mark path-choice effect not exercised.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; IOS XE 17.x; maintained Basic BGP chapter |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## BGP-06

Choose your exit before the Internet chooses for you

**Read:** current book chapters 20, 21, 24, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A AS 64500 learns the identical192.0.2.200/32 from B AS64510 and D AS64511 over separate links. Both are accepted, eligible and next-hop-resolvable. Baseline has equal local preference and documented competing attributes; no platform weight or earlier criterion masks the experiment. Set B path local preference200 and D100; record B chosen in BGP/RIB/FIB and a probe identifies B site. Change only B to50; D wins and site-identifying probe changes. Restore200. With iBGP C optionally prepared, confirm local preference propagation inside64500. Inspect outbound eBGP updates to avoid teaching it as an attribute sent to ordinary external peers. A missing/filtered/invalid alternative cannot demonstrate preference.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained external-service-provider BGP chapter; IOS XE 17.x; maintained Basic BGP chapter |
| eos | READ | EOS 4.36.2F |
| frr | READ | FRR 10.2 |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |

## BGP-07

Influence the far end without pretending to control it

**Read:** current book chapters 20, 21, 24, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Prepend trial: A exports one exact test prefix to two isolated external sites. Extra two copies of its own AS are applied to only one export; captures/downstream route detail confirm actual AS_PATH, then downstream selected path/forwarding and site probe are recorded. If higher-priority local policy keeps the same choice, explain it rather than claiming prepend failed to modify the attribute. Restore baseline. MED trial uses both exits toward the same adjacent AS64510 with equal earlier attributes and no extra prepend. Set one MED50 and the other100; inspect whether lower MED is compared/preferred under the actual downstream settings. Change one adjacent AS to64511 as a separately restored scope test, record effective always-compare/deterministic-MED settings and actual result; do not assume MED is compared across different ASs by default.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained external-service-provider BGP chapter |
| eos | READ | EOS 4.36.2F |
| frr | READ | FRR 10.2 |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |

## BGP-08

Reflect the route, preserve the forwarding question

**Read:** current book chapters 20, 21, 24, 32.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A,B,C AS 64500 have underlay routes to all peering loopbacks. B originates exact192.0.2.100/32 under explicit filter; A-B/A-C iBGP are Up and B-C direct session is absent. Baseline both A peers non-clients: A learns B route but C does not receive it via ordinary iBGP re-advertisement. Make B/C clients of A; C receives permitted route with B ORIGINATOR_ID and A cluster ID in CLUSTER_LIST, preserves expected next hop and resolves it through underlay. Verify selected route/FIB and sourced service/return traffic. Restore both peer client settings to the non-client baseline, trigger documented reevaluation if needed, observe C withdrawal, then recover. Removing just one client may still permit reflection and is not the intended negative test.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained Catalyst9000 BGP guide; individual feature minimum releases stated in source |
| eos | READ | EOS 4.36.2F |
| frr | READ | FRR 10.2 |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |

## BGP-09

A prefix fuse is different from a prefix filter

**Read:** current book chapters 20, 21, 24, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Isolated sender originates three distinct exact /32s192.0.2.200/.201/.202. Receiver policy is temporarily an explicit allowlist of these three, not the earlier one-prefix allowlist, so accepted-prefix limits can actually be exercised. Configure limit2. Send one, then two, then three prefixes, recording pre-policy received count, accepted count, limit state/logs and session status at every boundary; teardown may occur at a documented boundary that differs across platforms. Once triggered, stop extra announcements first, restore one intended prefix and original exact filter, then use the platform’s documented recovery/reset or captured timer behavior to re-establish. Verify intended route/FIB and service recovery. A session that stays Up under a warning-only setting is classified as warning behavior, not successful teardown proof.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained Catalyst9000 BGP guide; individual feature minimum releases stated in source |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision not stated; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## BGP-10

Authenticate the session, not the business relationship

**Read:** current book chapters 20, 21, 24, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Both endpoints install the same lab-only key on the intended peer and establish a new authenticated TCP/BGP session. Capture peer identity, Established state, intended filtered route and TCP MD5 option where the capture point exposes it. Change only B key, then perform a controlled fresh-connection/reset trial: record failed establishment/authentication or packet rejection, not just whether an old connection persists. Restore matching key, establish fresh session and prove route/FIB/service recovery. Capture no plaintext secret in published transcripts. Authentication does not replace prefix/AS policy, hide route contents or encrypt forwarded customer traffic. These MD5 panels are legacy interoperability exercises, not a claim of modern TCP-AO support.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained Catalyst9000 BGP guide; individual feature minimum releases stated in source |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision not stated; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## BGP-11

Two good paths do not make every packet alternate

**Read:** current book chapters 20, 21, 32, 34, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A receives identical192.0.2.200/32 from B and D in same adjacent AS64510, with equal required selection attributes and both recursive next hops reachable. Record two BGP candidates before change but baseline FIB path count1. Enable multipath; record selected/multipath status and actual FIB members2, or classify target restriction if hardware/image cannot install them. Generate bounded multiple flows with different source/destination ports and observe per-next-hop counters/site labels; a single flow may remain on one member and unequal small-sample counts do not disprove hashing. Disable one isolated next hop, capture surviving-member forwarding and service loss interval, restore and inspect membership/distribution again. Do not infer ECMP installation from two rows in the BGP table.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained Catalyst9000 BGP guide; individual feature minimum releases stated in source |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## BGP-12

Graceful is a measured outcome, not a command name

**Read:** current book chapters 20, 21, 24, 64, 67.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Planned drain first: on one isolated exit, send standard GRACEFUL_SHUTDOWN community65535:0 using BGP-05 tagging grammar and a prepared receiving policy that lowers matching route local preference to0. Verify tag reception, selected alternate route/FIB and traffic movement before administratively removing that exit; restore original tag/policy/session. This does not require GR. Separate GR trial: A helper and B capable restarter negotiate intended AF capability, restart time and forwarding-state indication. A continuously probes a route through B while the prepared B control-plane-only restart retains forwarding. Record stale marking, actual continued/lost traffic, re-established session, End-of-RIB and stale cleanup. In a second bounded restart where B does not recover, observe stale route expiry and traffic consequences, then restore B. Do not set a forwarding-preserved flag unless forwarding really remains intact.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; BGP graceful-restart per-neighbor guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision not stated; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.5.x (circinus) documented variant; not1.4 qualification |
| frr | READ | FRR 10.2 |

## BGP-13

Valid means authorised origin, not a safe route

**Read:** current book chapters 20, 21, 24, 52, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Test cache203.0.113.60 TCP3323 serves a recorded lab VRP dataset:192.0.2.200/32 maxLength32 origin64510;192.0.2.201/32 maxLength32 origin64511; no covering VRP for192.0.2.202/32. Sender AS64510 announces all three. Verify cache synchronized, actual VRPs and route states Valid(.200), Invalid(.201), NotFound(.202). Temporary explicit three-prefix allowlist permits classification independent of earlier one-prefix filter. Enforce Invalid rejection/unusability: .201 must not be eligible/programmed in forwarding, while permitted Valid and chosen NotFound policy are separately recorded. Stop only RTR cache transport, observe retained data until expiry and post-expiry policy behavior; restore synchronization and reevaluate routes. A broken cache connection does not instantly mean every route is Invalid, and NotFound is not proof of a malicious route.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained origin-AS-validation chapter; IOS XE 17.x; maintained Basic BGP chapter |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification; Junos OS; guide revision not stated; no release qualification |
| sros | READ | SR OS 25.3.R1 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |
| eos | NO_PANEL | The official EOS 4.36.2F material establishes RPKI display/state references, but the cache configuration and enforcement syntax was not returned by the accessible sources. The relevant support articles required sign-in. No configuration panel is qualified; the retained attempt ledger identifies the manual, articles and PDF that were checked. |

## BGP-14

A learned route is not automatically yours to resell

**Read:** current book chapters 20, 21, 24, 52, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated BGP speakers and explicit route-policy test inputs; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A AS 64500 originates own192.0.2.100/32; customerB AS64501 supplies.200/32, peerC AS64502 supplies.201/32, transitD AS64503 supplies.202/32. All are actually received/accepted at A under separate exact imports before export-policy tests. C/D must receive only A own and customer routes; they must not receive each other’s routes through A. Customer receives the four named permitted lab routes under its separate exact export policy. Record A selected/FIB and far-end received routes for every matrix cell, not just local export counters. With prepared real endpoints and return paths, customer can reach peer/transit service while ordinary peer-to-transit reachability lacks the withheld route, with no peer covering/default/static alternative. Temporarily add one explicit peer-origin permit to the transit export list only in this isolated lab, observe leak at D, then remove it, reevaluate and prove withdrawal/recovery. Origin validation may remain Valid during a leak: business relationship policy is a different boundary.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained external-service-provider BGP chapter; IOS XE 17.x; maintained Basic BGP chapter |
| eos | READ | EOS 4.36.2F |
| frr | READ | FRR 10.2 |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |

## VPN-01

Same address, different room

**Read:** current book chapters 22, 23, 27, 32.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task VPN topology, separated customer contexts and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** WB-BLUE and WB-RED each have a separate routed lab interface192.0.2.1/24 and a separate isolated host192.0.2.2. Record interface-to-instance membership, distinct routing/neighbor tables and context-scoped probes. Blue host returns BLUE site marker and red host returns RED marker despite identical destination address. A default/global-context probe must not be accepted as evidence for either tenant. Shut only blue attachment: blue service fails while red continues; restore and prove independent recovery. Before any leaking, no blue-to-red route or bridge exists. VRF isolation does not encrypt traffic and two routing tables do not imply an MPLS/EVPN VPN has been built.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-09-23; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | Linux kernel 6.6 documentation; VRF/l3mdev and iproute2 command examples; FRR 10.2 |

## VPN-02

Open a service door, not the whole building

**Read:** current book chapters 22, 23, 27, 32.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task VPN topology, separated customer contexts and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** The exact two opposite service /32 routes are installed in the intended VRFs and actual host-to-host service traffic works. Negative .101 controls and opposite covering prefixes remain excluded; removing only the return leak gives a captured one-way failure, restoring it recovers, and removing both leaks restores isolation. Use new TCP tuples/stateless probes after each fault; any SRX stateful flow cache must not mask the changed RIB/FIB. Negative controls require absence of a usable route and corresponding packet captures, not only application silence. Final isolation refers to this unique-prefix VPN-02 baseline; do not claim the old overlapping addresses were restored.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 16.12.x/17.x; Cisco lab article revised2026-06-08; IOS XE 17.x; maintained Basic BGP chapter |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; instance-import introduced before7.4; maintained reference; Junos OS; Juniper virtual-router example2022; no target-release qualification; Junos OS; guide revision not stated; no release qualification; Junos OS; guide revision 2026-02-17; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## VPN-03

A label is a local promise

**Read:** current book chapters 23, 24, 25, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task VPN topology, separated customer contexts and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** IGP loopback reachability and actual label-forwarding evidence agree for the remote /32. Session-up alone is insufficient. LDP-only B-C fault is distinguished from IP underlay failure and ordinary IP fallback; recovery restores label actions.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxr | READ | IOS XR 24.1.x–24.4.x; ASR 9000 MPLS guide |
| junos | READ | Junos OS; guide revision 2026-08-23; no release qualification |
| eos | READ | EOS 4.36.2F |
| sros | READ | SR OS 25.3.R1 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## VPN-04

Reserve the path; prove the passenger

**Read:** current book chapters 24, 25, 26, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task VPN topology, separated customer contexts and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A-C strict LSP follows incoming B and C interface addresses, reserves10 Mb/s and forwards a probe actually steered through it. Over-capacity signaling is recorded without confusing retained old LSP with a new successful reservation; restore/recover and compare actual labels.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxr | READ | IOS XR 24.1.x–24.4.x; ASR 9000 MPLS guide; IOS XR ASR 9000 maintained MPLS OAM command reference; exact target image separately qualified |
| iosxe | READ | IOS XE 17 MPLS Traffic Engineering guide; IOS XE 17.x maintained MPLS LSP Ping guide; IOS XE 17 SR guide; SRv6 feature minimum17.12.1a |
| junos | READ | Junos OS; guide revision 2026-08-23; no release qualification |
| sros | READ | SR OS 25.3.R1; SR OS 23.3.R1 classic CLI command reference; target release separately qualified |
| eos | READ | EOS 4.36.2F |
| frr | NO_PANEL | The returned FRR 10.2 protocol, pathd and ldpd references establish SR-TE policy and segment-list syntax, not RSVP PATH/RESV signalling or RSVP bandwidth reservations. Use the FRR SR variant in VPN-05, or a qualified RSVP implementation for this task; they test different mechanisms. |

## VPN-05

The index travels; the label changes

**Read:** current book chapters 24, 25, 26, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task VPN topology, separated customer contexts and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** All three SRGBs and Prefix-SID indexes are recorded and actual next-hop label mapping is correct. Test flow demonstrably uses SR transport; withdrawing C SID leaves IP reachability but removes this C Prefix-SID103 transport dependency, restored afterward.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxr | READ | IOS XR 24.1.x–24.4.x; ASR9000 segment routing guide |
| iosxe | READ | IOS XE 17 access/edge router segment routing guide |
| junos | READ | Junos OS; guide revision 2026-08-23; no release qualification |
| sros | READ | SR OS 25.3.R1 |
| eos | READ | EOS 4.36.2F |
| frr | READ | FRR 10.2 |

## VPN-06

An IPv6 address with a job description

**Read:** current book chapters 25, 26, 27, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task VPN topology, separated customer contexts and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Outer IPv6 locator reachability, local endpoint function and actual processed packet are individually evidenced. Per-panel format/flavor is recorded; withdrawal/control packet distinguishes plain IPv6 forwarding from SRv6 processing and restores cleanly.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxr | READ | IOS XR 24.1.x–24.4.x ASR9000 SR guide |
| iosxe | READ | IOS XE 17; SRv6 introduced17.12.1a, supported access/edge models |
| junos | READ | Junos OS20.3R1 or later; MX MPC7E/8E/9E documented example |
| sros | READ | SR OS 25.3.R1 |
| frr | READ | FRR 10.2 |
| linux | READ | iproute2 v6.6.0 upstream tagged manual; Linux kernel 6.6 SRv6 sysctl documentation |

## VPN-07

Two labels, two responsibilities

**Read:** current book chapters 22, 23, 24, 27, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task VPN topology, separated customer contexts and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Remote customer route is advertised with RD/RT/service label, resolved through actual MPLS PE transport and imported in BLUE; real customer request/reply and label captures agree. P has no customer routes; RED remains isolated; import RT-only fault/recovery is distinguished from underlay/session failure.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxr | READ | IOS XR 24.1.x–24.4.x; ASR 9000 L3VPN guide |
| iosxe | READ | IOS XE 17; Multiprotocol BGP MPLS VPN guide |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification |
| sros | READ | SR OS 25.3.R1 |
| eos | READ | EOS 4.36.2F |
| frr | READ | FRR 10.2 |

## VPN-08

The name badge and the guest list

**Read:** current book chapters 22, 23, 27, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task VPN topology, separated customer contexts and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Each phase has before/after VPN RIB, tenant RIB/FIB and service evidence. RD-only change alters NLRI identity with RT membership retained; import-only RT mismatch excludes the remote route from BLUE while VPN control-plane receipt can persist. Restore baseline between phases and afterward; same-prefix dual-origin result explains route selection rather than a false guarantee of two reachable identical addresses.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxr | READ | IOS XR 24.1.x–24.4.x; ASR 9000 L3VPN guide |
| iosxe | READ | IOS XE 17; Multiprotocol BGP MPLS VPN guide |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification |
| sros | READ | SR OS 25.3.R1; SR OS 24.3.R2 MD-CLI advanced configuration guide |
| eos | READ | EOS 4.36.2F |
| frr | READ | FRR 10.2 |

## VPN-09

A wire that crosses a core

**Read:** current book chapters 24, 27, 28, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task VPN topology, separated customer contexts and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Both attachment circuits and matched PW bindings are correct, customer ARP and unicast cross the core, and PW-ID-only mismatch fails service without breaking provider IP transport. Restore baseline. FRR panel qualifies signaling only until its actual PW forwarding backend is demonstrated.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxr | READ | IOS XR 24.1.x–24.4.x ASR9000 L2VPN guide |
| iosxe | READ | IOS XE 17 AToM maintained configuration chapter |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification |
| sros | READ | SR OS 25.3.R2 classic CLI example |
| eos | READ | EOS 4.36.2F |
| frr | READ | FRR 10.2 |

## VPN-10

Three sites, one LAN, no shortcut

**Read:** current book chapters 28, 29, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task VPN topology, separated customer contexts and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Known unicast, bounded flooding and remote MAC learning are proven on qualified dataplanes. Removing one direct mesh PW fails that pair rather than transiting a different PE; restore. Record FRR backend gate and EOS source-access gap explicitly.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxr | READ | IOS XR 24.1.x–24.4.x ASR9000 L2VPN guide |
| iosxe | READ | IOS XE 17 maintained VPLS chapter |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification |
| sros | READ | SR OS 25.3.R2 classic CLI example; SR OS 25.3.R1 |
| frr | READ | FRR 10.2 |
| eos | NO_PANEL | The returned EOS material establishes point-to-point pseudowires and confirms VPLS feature prose, but the required LDP-VPLS service/mesh syntax was not returned. The relevant support article required sign-in. This is a syntax-access gap, not a claim that VPLS is unsupported; an EVPN recipe does not qualify this LDP-VPLS task. |

## VPN-11

The MAC address gets a control plane

**Read:** current book chapters 29, 30, 31, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task VPN topology, separated customer contexts and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A local learned MAC produces EVPN RT2 and a remote forwarding entry. RT3 builds flooding state. Captured customer traffic uses the correct VNI. A UDP-only fault separates persistent BGP state from broken VXLAN forwarding; restore afterward. Record whether the expected route is MAC-only or MAC+IP.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 VXLAN EVPN chapter, updated2025-04-23 |
| junos | READ | Junos OS; guide revision 2026-09-02; no release qualification |
| eos | READ | EOS 4.36.2F |
| srl | READ | SR Linux 24.10 |
| sros | READ | SR OS 25.3.R1 |
| frr | READ | FRR 10.2 |

## VPN-12

Stretch a service, contain the consequences

**Read:** current book chapters 29, 32, 33, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task VPN topology, separated customer contexts and test endpoints; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** BLUE customer traffic and EVPN state cross the WAN with correct VNI, RT and MTU. RED remains local: no remote RED MAC or flood membership is installed in RED, no RED frame enters BLUE, and no VNI 200 frame crosses the WAN. Observe WAN route withdrawal, unresolved tunnel state and service failure, then restore. Explain the resulting failure domain. This basic transparent VTEP-to-VTEP DCI exercise does not qualify vendor Multi-Site or tunnel stitching.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 VXLAN EVPN chapter, updated2025-04-23 |
| junos | READ | Junos OS; guide revision 2026-09-02; no release qualification |
| eos | READ | EOS 4.36.2F |
| srl | READ | SR Linux 24.10 |
| sros | READ | SR OS 25.3.R1 |
| frr | READ | FRR 10.2 |

## DC-01

Build the floor before decorating it

**Read:** current book chapters 30, 31, 34, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task fabric topology and a tenant traffic test; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** L1–S1–L2 sessions and three loopback /32s are correct; sourced leaf-to-leaf traffic crosses the spine. Loopback-export withdrawal fails the destination service without requiring link/session failure; restore. No overlay/VXLAN or customer prefix is used to hide an underlay defect.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 BGP chapter |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| frr | READ | FRR 10.2 |
| nvue | READ | Cumulus Linux 5.9 NVUE documented configuration |

## DC-02

Unnumbered does not mean unaddressed

**Read:** current book chapters 20, 30, 34, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task fabric topology and a tenant traffic test; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** No numbered transit IPv4/global IPv6 address is needed; interface-scoped peering, extended-next-hop capability, remote /32 FIB adjacency and sourced IPv4 traffic all agree. Peer-binding fault and AS rejection are observed and restored. Device qualification includes discovery and forwarding, not syntax alone.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nvue | READ | Cumulus Linux 5.9 NVUE documented configuration |
| frr | READ | FRR 10.2 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| srl | READ | SR Linux 24.10 |
| junos | READ | Junos OS21.1R1+ feature; maintained auto-discovery reference; target image not qualified |
| eos | READ | EOS 4.36.2F |

## DC-03

A VTEP is an endpoint, not a promise

**Read:** current book chapters 30, 31, 34, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task fabric topology and a tenant traffic test; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Configured source/VNI/VRF, actual remote tunnel state and captured UDP 4789 customer traffic agree. Specific endpoint-route withdrawal fails resolution/delivery; restore. Record whether control peering shares the failed endpoint, and distinguish that from the UDP-only fault.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 VXLAN EVPN chapter, updated2025-04-23 |
| junos | READ | Junos OS; guide revision 2026-09-02; no release qualification |
| eos | READ | EOS 4.36.2F |
| srl | READ | SR Linux 24.10 |
| sros | READ | SR OS 25.3.R1 |
| frr | READ | FRR 10.2 |

## DC-04

Follow one MAC from host to remote FDB

**Read:** current book chapters 29, 30, 31, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task fabric topology and a tenant traffic test; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Fresh MAC and route attributes agree at each stage, and known unicast follows the resolved remote entry. Host detachment tests measured ageing/withdrawal without clearing unrelated state. Restored host regenerates its route and service; MAC-only versus MAC+IP is recorded.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 VXLAN EVPN chapter, updated2025-04-23 |
| junos | READ | Junos OS; guide revision 2026-09-02; no release qualification |
| eos | READ | EOS 4.36.2F |
| srl | READ | SR Linux 24.10 |
| sros | READ | SR OS 25.3.R1 |
| frr | READ | FRR 10.2 |

## DC-05

An IP prefix takes the routed entrance

**Read:** current book chapters 30, 31, 34, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task fabric topology and a tenant traffic test; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** The exact service /32 appears as RT5, is imported in the remote tenant RIB/FIB and carries real request/reply. Vendor-specific gateway/router-MAC/VNI resolution is recorded. Backing-route-only withdrawal removes service reachability, then restoration recovers; no discard-route forwarding claim.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 external VRF/EVPN chapter; NX-OS 10.5(x) Nexus9000 BGP chapter; NX-OS 10.5(x) Nexus9000 VXLAN EVPN chapter, updated2025-04-23 |
| junos | READ | Junos OS; guide revision 2026-09-02; no release qualification |
| eos | READ | EOS 4.36.2F |
| srl | READ | SR Linux 24.10 |
| sros | READ | SR OS 25.3.R1 |
| frr | READ | FRR 10.2 |

## DC-06

The gateway is wherever the host is

**Read:** current book chapters 30, 31, 34, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task fabric topology and a tenant traffic test; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Both leaf attachments resolve the same gateway identity and reach a real routed service. Host movement converges without changing its gateway; isolated identity mismatch is detected and restored.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 VXLAN EVPN chapter, updated2025-04-23 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-09-02; no release qualification |
| srl | READ | SR Linux 24.10 |
| frr | READ | FRR 10.2 |
| nvue | READ | Cumulus Linux 5.9 NVUE VRR reference |

## DC-07

Two chassis, one fabric attachment

**Read:** current book chapters 23, 30, 31, 34, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task fabric topology and a tenant traffic test; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Both leaf peers form the documented coordination relationship, client LACP membership and fabric service forward in the baseline. Single-client-member, peer-data-path and independent-liveness faults are tested separately. The recorded split-brain policy prevents duplicate unsafe forwarding, and controlled restoration recovers the original service.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x); Nexus 9000 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-23; no release qualification |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |
| aoscx | READ | AOS-CX 10.13; VSX guide, 6400/8xxx/9300/10000 |
| sros | READ | SR OS 25.3.R1 |

## DC-08

A fabric with more than one way home

**Read:** current book chapters 20, 21, 30, 32, 34, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task fabric topology and a tenant traffic test; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A receives identical192.0.2.200/32 from B and D in same adjacent AS64510, with equal required selection attributes and both recursive next hops reachable. Record two BGP candidates before change but baseline FIB path count1. Enable multipath; record selected/multipath status and actual FIB members2, or classify target restriction if hardware/image cannot install them. Generate bounded multiple flows with different source/destination ports and observe per-next-hop counters/site labels; a single flow may remain on one member and unequal small-sample counts do not disprove hashing. Disable one isolated next hop, capture surviving-member forwarding and service loss interval, restore and inspect membership/distribution again. Do not infer ECMP installation from two rows in the BGP table.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.x; maintained Catalyst9000 BGP guide; individual feature minimum releases stated in source |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## DC-09

The packet grew a jacket

**Read:** current book chapters 9, 23, 30, 34, 52.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task fabric topology and a tenant traffic test; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Small routed baseline works. Captured inner/outer lengths match the declared encapsulation, 1500-byte inner IPv4 packets cross the prepared fabric without unexpected fragmentation, and a controlled transport-MTU reduction produces a measured failure or fragmentation outcome. Restore the saved MTU and prove recovery.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fortios | READ | FortiOS 7.6.6; CLI Reference |

## DC-10

SONiC: find the owner before editing the tenant

**Read:** current book chapters 9, 30, 36, 52, 81.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task fabric topology and a tenant traffic test; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** SONiC ConfigDB intent, persisted baseline and live interface state are captured separately; the isolated delta is restored. Each comparison identifies its own persistent owner. No reboot or ASIC programming claim is inferred from successful syntax alone.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x); Nexus 9000 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-18; no release qualification |
| frr | READ | FRR 10.2 |
| sonic | READ | SONiC sonic-utilities release branch202405; target vendor image unqualified |
| nvue | READ | Cumulus Linux 5.9 NVUE documented configuration |

## DC-11

The tenant door has a precise guest list

**Read:** current book chapters 30, 34, 37, 52, 61.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task fabric topology and a tenant traffic test; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Admitted and denied fresh flows differ exactly at the intended tenant ingress. Counters/captures explain the result, unrelated service stays usable and controlled removal restores baseline.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-23; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| linux | READ | nft official manual revision2026-07-02; installed executable version must be recorded |

## DC-12

Pause is local; congestion is a conversation

**Read:** current book chapters 30, 32, 34, 36, 52, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the task fabric topology and a tenant traffic test; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Actual ECT-to-CE and endpoint response are distinguished from drops; priority pause is measured separately, unrelated service and drain/recovery are checked, all saved QoS state is restored.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 QoS guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision not stated; no release qualification; Junos OS; guide revision 2026-06-16; no release qualification |
| srl | READ | SR Linux 25.10 documented PFC variant; exact ASIC support required; SR Linux 25.10 queue-management profile variant |
| nvue | READ | Cumulus Linux 5.9 NVUE QoS guide |
| sonic | READ | SONiC sonic-utilities release branch202405; target vendor image unqualified; SONiC sonic-buildimage release branch202405 WRED schema |

## QOS-01

A marking finds its queue

**Read:** current book chapters 32, 34, 52, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** traffic source and sink, counters and the required dataplane features; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** DSCP46 and DSCP0 hit declared classes, ECT bits do not alter the DSCP match, packet captures and counters agree, and saved classifier/mapping restoration recovers baseline.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 QoS guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-16; no release qualification |
| srl | READ | SR Linux 25.10; documented model and hardware constraints apply |
| nvue | READ | Cumulus Linux 5.9 NVUE QoS guide |
| linux | READ | iproute2 v6.6.0 upstream tagged manual; kernel/hardware capability separately qualified |

## QOS-02

Trust is a boundary, not a compliment

**Read:** current book chapters 32, 34, 37, 52, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** traffic source and sink, counters and the required dataplane features; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Ingress and egress captures show DSCP46 becoming0 with ECN unchanged, counters/internal class explain the selected traffic, trusted control and saved restoration work.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 QoS guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-16; no release qualification |
| srl | READ | SR Linux 25.10; documented model and hardware constraints apply |
| nvue | READ | Cumulus Linux 5.9 NVUE QoS guide |
| linux | READ | iproute2 v6.6.0 upstream tagged manual; kernel/hardware capability separately qualified |

## QOS-03

Sharing the queue without starving the neighbour

**Read:** current book chapters 32, 34, 52, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** traffic source and sink, counters and the required dataplane features; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Both test classes make progress under bounded contention, effective mappings and measured service explain the policy, unused-capacity behavior and full restoration are recorded.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 QoS guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-16; no release qualification |
| srl | READ | SR Linux 25.10; documented model and hardware constraints apply |
| nvue | READ | Cumulus Linux 5.9 NVUE QoS guide |
| linux | READ | iproute2 v6.6.0 upstream tagged manual; kernel/hardware capability separately qualified |

## QOS-04

Make the burst wait its turn

**Read:** current book chapters 32, 34, 52, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** traffic source and sink, counters and the required dataplane features; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Effective rate units/cap, receiver service, backlog/delay and drain are measured under bounded excess; saved restoration recovers baseline.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 QoS guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-16; no release qualification |
| srl | READ | SR Linux 25.10; documented model and hardware constraints apply |
| nvue | READ | Cumulus Linux 5.9 NVUE QoS guide |
| linux | READ | iproute2 v6.6.0 upstream tagged manual; kernel/hardware capability separately qualified |

## QOS-05

The bucket has a budget

**Read:** current book chapters 32, 34, 37, 52, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** traffic source and sink, counters and the required dataplane features; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Low-rate traffic passes; excess disposition/counters agree with receiver captures and declared burst, unrelated traffic and saved restoration work.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 QoS guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-23; no release qualification |
| srl | READ | SR Linux 25.10; documented model and hardware constraints apply |
| nvue | READ | Cumulus Linux 5.9 NVUE QoS guide; Cumulus Linux 5.9 ACL configuration; cl-acltool owner variant |
| linux | READ | iproute2 v6.6.0 upstream tagged manual; kernel/hardware capability separately qualified |

## QOS-06

Warn early; measure the conversation

**Read:** current book chapters 32, 34, 52, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** traffic source and sink, counters and the required dataplane features; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Measured queue attachment/thresholds explain CE and drops, endpoint feedback is recorded, repeated bounded trials drain and saved restoration recovers service.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 QoS guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-16; no release qualification |
| srl | READ | SR Linux 25.10; documented model and hardware constraints apply |
| nvue | READ | Cumulus Linux 5.9 NVUE QoS guide |
| linux | READ | iproute2 v6.6.0 upstream tagged manual; kernel/hardware capability separately qualified |

## QOS-07

A per-hop promise travels through a path

**Read:** current book chapters 32, 34, 52, 64.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** traffic source and sink, counters and the required dataplane features; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Every hop has captured marking, class/queue and scheduler evidence. Under bounded contention both classes progress; changing one hop mapping alters only the declared treatment, restoration recovers it. End-to-end performance is measured, never inferred from DSCP alone.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 QoS guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-16; no release qualification |
| srl | READ | SR Linux 25.10; documented model and hardware constraints apply |
| nvue | READ | Cumulus Linux 5.9 NVUE QoS guide |
| linux | READ | iproute2 v6.6.0 upstream tagged manual; kernel/hardware capability separately qualified |

## QOS-08

Publish the evidence, not the knob position

**Read:** current book chapters 32, 34, 52, 64, 80.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** traffic source and sink, counters and the required dataplane features; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A complete bounded trial table separates rate/queue/marking/drop/feedback observations, includes baseline and recovery, and explains units, uncertainty and unavailable evidence.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 QoS guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-16; no release qualification |
| srl | READ | SR Linux 25.10; documented model and hardware constraints apply |
| nvue | READ | Cumulus Linux 5.9 NVUE QoS guide |
| linux | READ | iproute2 v6.6.0 upstream tagged manual; kernel/hardware capability separately qualified |

## SEC-01

A source-only gate needs the right location

**Read:** current book chapters 37, 52, 61.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Admitted and denied fresh source flows differ only at the protected destination segment, unrelated reachability survives and task-only restoration recovers baseline.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-23; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| linux | READ | nft official manual revision2026-07-02; installed executable version must be recorded |

## SEC-02

A service gate names both endpoints and the port

**Read:** current book chapters 37, 52, 61.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Admitted and denied fresh flows differ exactly at the intended tenant ingress. Counters/captures explain the result, unrelated service stays usable and controlled removal restores baseline.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-23; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| linux | READ | nft official manual revision2026-07-02; installed executable version must be recorded |

## SEC-03

Protect the prompt without losing the rescue rope

**Read:** current book chapters 9, 37, 51, 52, 61.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Authorised new SSH succeeds, denied new SSH fails, rescue/control paths remain available and saved policy recovery works; IPv6/VRF coverage is explicitly recorded.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-23; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| linux | READ | nft official manual revision2026-07-02; installed executable version must be recorded |

## SEC-04

Give the control plane a measured budget

**Read:** current book chapters 51, 52, 57, 61.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Scoped policy units, burst and attachment are recorded; finite low-rate evidence and recovery checks are captured without an uncontrolled CPU-load test.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 CoPP chapter |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-23; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| linux | READ | nft official manual revision2026-07-02; installed executable version must be recorded |

## SEC-05

A valid source can arrive through the wrong door

**Read:** current book chapters 5, 16, 51, 57.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Strict/loose/restore matrix is explained using the reverse lookup and egress captures, with no-default and platform exceptions explicit.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| nxos | READ | NX-OS 10.5(x) Nexus9000 security guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-23; no release qualification |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| linux | READ | Linux kernel v6.6 tagged sysctl documentation |

## SEC-06

Trust the server path, then inspect the claimed binding

**Read:** current book chapters 4, 10, 51, 52, 57.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Lease/port/VLAN binding and rogue-offer/ARP positive-negative evidence are recorded; partial vendor capabilities and static-client gates are disclosed.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| nxos | READ | NX-OS 10.5(x) Nexus9000 security guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision not stated; no release qualification |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |
| aoscx | READ | AOS-CX 10.13.1000; April 2024, edition 1; AOS-CX10.13.1000 Hardening Guide; official PDF page44 |

## SEC-07

One port, one expected speaker

**Read:** current book chapters 4, 10, 51, 57.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** First/excess/restored-host matrix, security counters and port state match declared vendor violation action.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| nxos | READ | NX-OS 10.5(x) Nexus9000 security guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision not stated; no release qualification |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |
| aoscx | READ | AOS-CX10.13 Security Guide; 6200/6300/6400 |

## SEC-08

Authenticate the speaker, then test the service

**Read:** current book chapters 7, 51, 52, 57, 61.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Fresh valid/reject/server-unreachable matrix has packet, server and access-port evidence with exact fallback behavior and recovery.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| nxos | READ | NX-OS 10.5(x) Nexus9000 security guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision not stated; no release qualification |
| fsw | READ | FortiSwitchOS 7.6.2; CLI Reference |
| aoscx | READ | AOS-CX10.13 Security Guide; 6200/6300/6400 |

## SEC-09

A zone boundary has a direction and a memory

**Read:** current book chapters 7, 51, 52, 57.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Fresh HTTPS/other-port/reverse-new matrix, session state and exact policy-order evidence agree, followed by restored baseline.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17 maintained zone-based firewall chapter; IOS XE 17.15.x / Catalyst 9300 |
| junos | READ | Junos OS; guide revision 2026-07-10; no release qualification |
| fortios | READ | FortiOS7.6.6 CLI Reference |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| linux | READ | nft official manual revision2026-07-02; installed executable version must be recorded |
| routeros | READ | RouterOS7 documentation, frozen maintained page; image version separately recorded; RouterOS7 common firewall matcher reference; image version separately recorded |

## SEC-10

Follow the tuple through translation

**Read:** current book chapters 5, 7, 51, 53.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Inside/outside five-tuples, translation and session state, and fresh-flow recovery evidence account for both clients and an unmatched source.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17 maintained NAT address-conservation chapter |
| junos | READ | Junos OS; guide revision not stated; no release qualification |
| fortios | READ | FortiOS7.6.6 CLI Reference |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| linux | READ | nft official manual revision2026-07-02; installed executable version must be recorded |
| routeros | READ | RouterOS7 NAT documented variant; image version separately recorded |

## SEC-11

Build the encrypted path and keep the clear path closed

**Read:** current book chapters 7, 51, 54, 55, 57.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** The real inner service works through negotiated Child SAs. A credential fault prevents fresh negotiation without cleartext fallback; restoring it recovers the service.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17 IKEv2 profile/keyring chapter; IOS XE 17 maintained VTI chapter |
| junos | READ | Junos OS; guide revision 2026-09-08; no release qualification |
| fortios | READ | FortiOS 7.6.6; CLI Reference |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| linux | READ | strongSwan5.9 swanctl.conf reference; strongSwan 5.9 documentation branch; strongswan.conf file syntax |
| routeros | READ | RouterOS7 IPsec documented variant; image version separately recorded; RouterOS7 IKEv2 interoperability example, published2024; target image separately qualified |

## SEC-12

Make the wire testify

**Read:** current book chapters 7, 51, 54, 55, 62.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Evidence worksheet joins inner service, WAN protocol/SPI, SA counter deltas, route-fault diagnosis and zero clear protected traffic during bounded tunnel failure.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17 IKEv2 profile/keyring chapter; IOS XE 17 maintained VTI chapter |
| junos | READ | Junos OS; guide revision 2026-09-08; no release qualification |
| fortios | READ | FortiOS 7.6.6; CLI Reference |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| linux | READ | strongSwan5.9 SA listing reference; child filter since5.9.6; iproute2v6.6.0 tagged XFRM manual |
| routeros | READ | RouterOS7 IPsec documented variant; image version separately recorded |

## SEC-13

A route is also a request for authority

**Read:** current book chapters 20, 21, 32, 33, 51, 57.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Same-peer authorised/unwanted update evidence, accepted RIB/FIB, peer export and controlled withdraw/restore matrix agree.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; IOS XE 17.x; maintained external-service-provider BGP chapter |
| eos | READ | EOS 4.36.2F |
| frr | READ | FRR 10.2 |
| junos | READ | Junos OS; guide revision 2026-07-08; no release qualification |
| srl | READ | SR Linux 24.10 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |

## SEC-14

Mitigation needs an owner and an expiry

**Read:** current book chapters 21, 32, 33, 51, 57.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** isolated security test clients and recoverable management access; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Authorised scope, installed discard/filter, bounded positive/control probes, expiry and fresh service recovery are recorded. FRR 10.2 is explicitly a receiver-observation variant; installation and validation are unsupported/unqualified, not passed.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | Cisco IOS RTBH design note, 2005; mechanism reference paired with IOS XE 17.15 syntax; IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-06-23; no release qualification |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |
| sros | READ | SR OS 24.3.R2 MD-CLI advanced configuration guide |

## OPS-01

A poll should reveal counters, not credentials

**Read:** current book chapters 42, 52, 64, 65.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the named observation services and controlled test traffic; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Protected reads, privacy-level and credential negatives, effective permissions, source scope and removal evidence are recorded; unsupported equivalences are explicit.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-06; no release qualification |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fortios | READ | FortiOS 7.6.6; CLI Reference |
| linux | READ | Net-SNMP maintained snmpd.conf manual; exact installed build/version required |

## OPS-02

Turn down the noise without losing the warning

**Read:** current book chapters 42, 52, 64, 65.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the named observation services and controlled test traffic; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Two observed severity classes, source/collector evidence, threshold transition and recovery agree; absent safe event fixtures remain explicit.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9500 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-06; no release qualification |
| srl | READ | SR Linux 24.3 |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| frr | READ | FRR 10.2 |

## OPS-03

A flow record is a measurement with assumptions

**Read:** current book chapters 42, 64, 65.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the named observation services and controlled test traffic; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Exporter/domain/template, five-tuple, direction, counter units and controlled collector interruption/recovery are documented.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x Catalyst9500 Flexible NetFlow; exact model/ASIC restrictions apply |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision not stated; no release qualification |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fortios | READ | FortiOS 7.6.6; CLI Reference |
| routeros | READ | RouterOS7 Traffic Flow reference; target image and offload path separately qualified |

## OPS-04

One sample is not the whole conversation

**Read:** current book chapters 42, 64, 65.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the named observation services and controlled test traffic; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Decoded agent/interface/ratio/direction and counter samples are correlated with a bounded wire capture; collector interruption and recovery are shown.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-06; no release qualification |
| nvue | READ | Cumulus Linux 5.9 host sFlow manual configuration; NVUE ownership separately checked |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| fortios | READ | FortiOS 7.6.6; CLI Reference |
| sonic | READ | SONiC sonic-utilities release branch202405; target vendor image unqualified |

## OPS-05

Subscribe to a fact, not a guess

**Read:** current book chapters 42, 64, 65, 69.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the named observation services and controlled test traffic; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Capabilities/schema, verified transport, bounded stream, independent observation, authentication negatives and reconnection semantics are recorded.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 Programmability Guide |
| eos | READ | Arista official Open Management configuration; target EOS 4.36.2F separately qualified |
| junos | READ | Junos OS telemetry guide; maintained revision and exact sensor support separately qualified |
| srl | READ | SR Linux 24.10 |
| sros | READ | SR OS 25.3.R1 MD-CLI system model |
| nvue | READ | Cumulus Linux 5.9 NetQ gNMI streaming variant; OpenConfig gNMIc maintained file-configuration reference; installed client version recorded |

## OPS-06

The hello tells you what the server can do

**Read:** current book chapters 68, 69, 70.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the named observation services and controlled test traffic; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Host key, hello/capabilities, framed RPC/reply IDs, namespace/filter semantics and clean close are recorded.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x NETCONF programmability guide |
| nxos | READ | NX-OS 10.5(x) Nexus9000 Programmability Guide |
| junos | READ | Junos OS maintained NETCONF guide; installed release/capabilities required |
| sros | READ | SR OS 25.3.R1 MD-CLI system model |
| iosxr | READ | IOS XR 24.1.x–24.4.x ASR 9000 System Management guide |
| linux | READ | CESNET Netopeer2 upstream master command source captured2026-10-02; hash pinned, installed client version separately recorded |

## OPS-07

HTTPS is a transport, not a common data model

**Read:** current book chapters 68, 69, 70.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the named observation services and controlled test traffic; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Verified HTTPS, real HTTP status/media/schema, narrow data comparison and negative auth/path results are recorded; non-RESTCONF variants are labelled.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x RESTCONF programmability guide |
| nxos | READ | NX-OS 10.5(x) Nexus9000 Programmability Guide |
| eos | READ | Arista official Open Management RESTCONF configuration; target EOS 4.36.2F separately qualified |
| junos | READ | Junos OS maintained REST API guide; target release/HTTPS configuration separately qualified |
| fortios | READ | FortiOS7.6.6 API administration guide |
| vyos | NO_PANEL | The returned VyOS 1.4 API guide establishes POST /retrieve rather than a RESTCONF GET endpoint. It is a different API and cannot be labelled RFC 8040 RESTCONF. This GET-only panel remains unqualified; a POST-based read requires a separately scoped experiment. |

## OPS-08

A locked clock still needs a witness

**Read:** current book chapters 42, 64, 66.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the named observation services and controlled test traffic; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Profile/role/reference, parent/state/messages, bounded reference-loss/recovery and the limits of the timing claim are explicit.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| nxos | READ | NX-OS 10.5(x) Nexus9000 system management guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS maintained timing guide; exact hardware/profile support required |
| sros | READ | SR OS 25.3.R1 Basic System Configuration Guide |
| nvue | READ | Cumulus Linux 5.9 PTP guide; NVUE owner/Spectrum hardware variant |
| linux | READ | LinuxPTP maintained ptp4l manual; installed version required; LinuxPTP maintained pmc manual; installed version required |

## OPS-09

Frequency is not a timestamp

**Read:** current book chapters 42, 64, 66.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the named observation services and controlled test traffic; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Physical capability, quality option/SSM, selection state, data-path control, backup and restore policy are documented.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17 maintained SyncE/ESMC/SSM chapter; timing-capable router required |
| iosxr | READ | IOS XR 24.1.x–24.4.x ASR9000 frequency-synchronisation chapter |
| nxos | READ | NX-OS 10.5(x) Nexus9000 system management guide |
| junos | READ | Junos OS maintained timing guide; exact hardware/profile support required |
| srl | READ | SR Linux 24.10 Network Synchronization Guide |
| sros | READ | SR OS 23.10.R2 classic CLI SyncE example; not25.3 MD-CLI qualification |

## OPS-10

A copy has a point of view

**Read:** current book chapters 42, 52, 64, 65.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the named observation services and controlled test traffic; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Ingress direction, selected traffic, copy/original identity, capture health and scoped removal/recovery are demonstrated.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| nxos | READ | NX-OS 10.5(x) Nexus9000 system management guide |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-06; no release qualification |
| vyos | READ | VyOS 1.4.x (sagitta) documentation |
| linux | READ | iproute2 v6.6.0 upstream tagged manual; kernel/hardware capability separately qualified |

## OPS-11

The device capture is one witness

**Read:** current book chapters 42, 52, 64, 65.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the named observation services and controlled test traffic; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Capture point/filter/bounds, local-control versus transit visibility, synthetic packet correlation and exact cleanup are recorded.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| nxos | READ | NX-OS 10.5(x) Nexus9000 Troubleshooting Guide |
| eos | READ | EOS 4.36.2F; tcpdump maintained manual; exact installed binary/libpcap version recorded |
| junos | READ | Junos OS; guide revision 2026-07-06; no release qualification |
| fortios | READ | FortiOS 7.6.6; CLI Reference |
| linux | READ | tcpdump maintained manual; exact installed binary/libpcap version recorded |

## OPS-12

Give the counter a denominator

**Read:** current book chapters 42, 52, 64, 65.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** the named observation services and controlled test traffic; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 45-90 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Two valid snapshots, traffic/counter correlation, unit/rate calculation and reset/wrap rejection are recorded without erasing unrelated diagnostic history.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300 |
| nxos | READ | NX-OS 10.5(x); Nexus 9000 |
| eos | READ | EOS 4.36.2F |
| junos | READ | Junos OS; guide revision 2026-07-06; no release qualification |
| srl | READ | SR Linux 24.10 |
| linux | READ | iproute2v6.6.0 tagged ip-link manual |

## AUT-01

Inventory before ingenuity

**Read:** current book chapters 52, 68–72.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a controller host, its pinned dependencies and an isolated target or supported fixture; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** One inventory entry resolves to the intended device; identity, trusted transport, denied credential and unchanged configuration evidence agree.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; Ansible collection 11.5.1; runtime separately pinned/qualified |
| nxos | READ | NX-OS 10.5(x); Nexus 9000; Ansible collection 11.2.0; runtime separately pinned/qualified |
| eos | READ | EOS 4.36.2F; Ansible collection 12.2.0; runtime separately pinned/qualified |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification; Junos Ansible guide revision 2026-08-24; juniper.device migration; device image separately qualified |
| srl | READ | SR Linux 24.10; Nokia srlinux collection main revision; fetched source SHA-256 pins syntax; version_added 0.1.0 is not installed version |
| vyos | READ | VyOS 1.4.x (sagitta) documentation; Ansible collection 6.0.0; runtime separately pinned/qualified |

## AUT-02

The template that refuses to guess

**Read:** current book chapters 52, 68–72.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a controller host, its pinned dependencies and an isolated target or supported fixture; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Six native variants render deterministically; missing, multiline and out-of-scope inputs are refused.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; Ansible collection 11.5.1; runtime separately pinned/qualified; Maintained upstream API; retrieval/hash pins reference; installed runtime must be recorded |
| nxos | READ | NX-OS 10.5(x); Nexus 9000; Ansible collection 11.2.0; runtime separately pinned/qualified; Maintained upstream API; retrieval/hash pins reference; installed runtime must be recorded |
| eos | READ | EOS 4.36.2F; Ansible collection 12.2.0; runtime separately pinned/qualified; Maintained upstream API; retrieval/hash pins reference; installed runtime must be recorded |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification; Junos Ansible guide revision 2026-08-24; juniper.device migration; device image separately qualified; Maintained upstream API; retrieval/hash pins reference; installed runtime must be recorded |
| srl | READ | SR Linux 24.10; Nokia srlinux collection main revision; fetched source SHA-256 pins syntax; version_added 0.1.0 is not installed version; Maintained upstream API; retrieval/hash pins reference; installed runtime must be recorded |
| vyos | READ | VyOS 1.4.x (sagitta) documentation; Ansible collection 6.0.0; runtime separately pinned/qualified; Maintained upstream API; retrieval/hash pins reference; installed runtime must be recorded |

## AUT-03

The second run earns the word idempotent

**Read:** current book chapters 52, 68–72.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a controller host, its pinned dependencies and an isolated target or supported fixture; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** First change, unchanged second run, detected drift and exact baseline restoration all have independent evidence.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; Ansible collection 11.5.1; runtime separately pinned/qualified |
| nxos | READ | NX-OS 10.5(x); Nexus 9000; Ansible collection 11.2.0; runtime separately pinned/qualified |
| eos | READ | EOS 4.36.2F; Ansible collection 12.2.0; runtime separately pinned/qualified |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification; Junos Ansible guide revision 2026-08-24; juniper.device migration; device image separately qualified |
| srl | READ | SR Linux 24.10; Nokia srlinux collection main revision; fetched source SHA-256 pins syntax; version_added 0.1.0 is not installed version |
| vyos | READ | VyOS 1.4.x (sagitta) documentation; Ansible collection 6.0.0; runtime separately pinned/qualified |

## AUT-04

One API, several observation boundaries

**Read:** current book chapters 52, 68–72.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a controller host, its pinned dependencies and an isolated target or supported fixture; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Two getters correlate with native evidence, while unsupported/absent/unauthenticated cases fail explicitly.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; NAPALM 3 documentation; supported-driver matrix, not current binary qualification |
| nxos | READ | NX-OS 10.5(x); Nexus 9000; NAPALM 3 documentation; supported-driver matrix, not current binary qualification |
| eos | READ | EOS 4.36.2F; NAPALM 3 documentation; supported-driver matrix, not current binary qualification |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification; NAPALM 3 documentation; supported-driver matrix, not current binary qualification |
| iosxr | READ | IOS XR 24.1.x–24.4.x ASR 9000 Programmability guide; NAPALM 3 documentation; supported-driver matrix, not current binary qualification |
| srl | READ | Nokia srlinux collection main revision; fetched source SHA-256 pins syntax; version_added 0.1.0 is not installed version; napalm-srlinux community driver maintained documentation; retrieval/hash pins reference, not installed binary; NAPALM 3 documentation; supported-driver matrix, not current binary qualification |

## AUT-05

A transaction with a way home

**Read:** current book chapters 52, 68–72.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a controller host, its pinned dependencies and an isolated target or supported fixture; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Payload/namespace checks and negative fixtures pass; a device write qualifies only after candidate validation, confirmed commit and independent restoration.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x NETCONF programmability guide; Cisco IOS XE 17.15.1 vendor YANG model; ncclient maintained API documentation; installed package version must be recorded |
| nxos | READ | NX-OS 10.5(x) Nexus9000 Programmability Guide; ncclient maintained API documentation; installed package version must be recorded |
| junos | READ | Junos OS maintained NETCONF guide; installed release/capabilities required; Junos OS; guide revision 2026-06-17; no release qualification; ncclient maintained API documentation; installed package version must be recorded |
| iosxr | READ | IOS XR 24.1.x–24.4.x ASR 9000 Programmability guide; Cisco IOS XR 24.1.1 vendor YANG model; ncclient maintained API documentation; installed package version must be recorded |
| sros | READ | SR OS 25.3.R1 System Management Guide; Nokia SR OS 25.3 vendor YANG system submodule; fetched hash pins maintained revision; ncclient maintained API documentation; installed package version must be recorded |
| eos | NO_PANEL | The returned Arista sources establish OpenConfig/gNMI and RESTCONF syntax, but do not establish a native NETCONF edit-config schema and transaction recipe for this task. Those APIs do not replace NETCONF. This is an unqualified recipe, not a claim that every EOS image lacks the feature. |

## AUT-06

A diff is a proposal, not permission

**Read:** current book chapters 52, 68–72.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a controller host, its pinned dependencies and an isolated target or supported fixture; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** The exact candidate hash, scoped native diff and independent ownership check agree; unexpected context is refused.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; Ansible collection 11.5.1; runtime separately pinned/qualified |
| nxos | READ | NX-OS 10.5(x); Nexus 9000; Ansible collection 11.2.0; runtime separately pinned/qualified |
| eos | READ | EOS 4.36.2F; Ansible collection 12.2.0; runtime separately pinned/qualified |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification; Junos Ansible guide revision 2026-08-24; juniper.device migration; device image separately qualified |
| srl | READ | SR Linux 24.10; Nokia srlinux collection main revision; fetched source SHA-256 pins syntax; version_added 0.1.0 is not installed version |
| vyos | READ | VyOS 1.4.x (sagitta) documentation; Ansible collection 6.0.0; runtime separately pinned/qualified |

## AUT-07

Prove the preconditions before the change

**Read:** current book chapters 52, 68–72.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a controller host, its pinned dependencies and an isolated target or supported fixture; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Positive and negative fixtures pass offline; actual pre-change service checks must pass before any write.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; Ansible collection 11.5.1; runtime separately pinned/qualified |
| nxos | READ | NX-OS 10.5(x); Nexus 9000; Ansible collection 11.2.0; runtime separately pinned/qualified |
| eos | READ | EOS 4.36.2F; Ansible collection 12.2.0; runtime separately pinned/qualified |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification; Junos Ansible guide revision 2026-08-24; juniper.device migration; device image separately qualified |
| srl | READ | SR Linux 24.10; Nokia srlinux collection main revision; fetched source SHA-256 pins syntax; version_added 0.1.0 is not installed version |
| vyos | READ | VyOS 1.4.x (sagitta) documentation; Ansible collection 6.0.0; runtime separately pinned/qualified |

## AUT-08

Make CI a skeptical colleague

**Read:** current book chapters 52, 68–72.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a controller host, its pinned dependencies and an isolated target or supported fixture; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** CI runs strict rendering and negative guard fixtures, archives hashes/results and never receives device credentials.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; Ansible collection 11.5.1; runtime separately pinned/qualified |
| nxos | READ | NX-OS 10.5(x); Nexus 9000; Ansible collection 11.2.0; runtime separately pinned/qualified |
| eos | READ | EOS 4.36.2F; Ansible collection 12.2.0; runtime separately pinned/qualified |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification; Junos Ansible guide revision 2026-08-24; juniper.device migration; device image separately qualified |
| srl | READ | SR Linux 24.10; Nokia srlinux collection main revision; fetched source SHA-256 pins syntax; version_added 0.1.0 is not installed version |
| vyos | READ | VyOS 1.4.x (sagitta) documentation; Ansible collection 6.0.0; runtime separately pinned/qualified |

## AUT-09

Restoration is a test, not a promise

**Read:** current book chapters 52, 68–72.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a controller host, its pinned dependencies and an isolated target or supported fixture; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** A controlled description change is restored, including absence semantics, while unrelated state is preserved.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; Ansible collection 11.5.1; runtime separately pinned/qualified |
| nxos | READ | NX-OS 10.5(x); Nexus 9000; Ansible collection 11.2.0; runtime separately pinned/qualified |
| eos | READ | EOS 4.36.2F; Ansible collection 12.2.0; runtime separately pinned/qualified |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification; Junos Ansible guide revision 2026-08-24; juniper.device migration; device image separately qualified |
| srl | READ | SR Linux 24.10; Nokia srlinux collection main revision; fetched source SHA-256 pins syntax; version_added 0.1.0 is not installed version |
| vyos | READ | VyOS 1.4.x (sagitta) documentation; Ansible collection 6.0.0; runtime separately pinned/qualified |

## AUT-10

Golden configuration, with fingerprints

**Read:** current book chapters 52, 68–72.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a controller host, its pinned dependencies and an isolated target or supported fixture; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Expected compliance and deliberate drift/missing-interface cases are distinguished; normalization retains operational meaning.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; Ansible collection 11.5.1; runtime separately pinned/qualified |
| nxos | READ | NX-OS 10.5(x); Nexus 9000; Ansible collection 11.2.0; runtime separately pinned/qualified |
| eos | READ | EOS 4.36.2F; Ansible collection 12.2.0; runtime separately pinned/qualified |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification; Junos Ansible guide revision 2026-08-24; juniper.device migration; device image separately qualified |
| srl | READ | SR Linux 24.10; Nokia srlinux collection main revision; fetched source SHA-256 pins syntax; version_added 0.1.0 is not installed version |
| vyos | READ | VyOS 1.4.x (sagitta) documentation; Ansible collection 6.0.0; runtime separately pinned/qualified |

## AUT-11

An event may ask; it may not push

**Read:** current book chapters 52, 68–72.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a controller host, its pinned dependencies and an isolated target or supported fixture; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** Duplicate, stale, unknown-target and rapid repeated events are rejected; one fresh owned event produces a read-only plan.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; Ansible collection 11.5.1; runtime separately pinned/qualified |
| nxos | READ | NX-OS 10.5(x); Nexus 9000; Ansible collection 11.2.0; runtime separately pinned/qualified |
| eos | READ | EOS 4.36.2F; Ansible collection 12.2.0; runtime separately pinned/qualified |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification; Junos Ansible guide revision 2026-08-24; juniper.device migration; device image separately qualified |
| srl | READ | SR Linux 24.10; Nokia srlinux collection main revision; fetched source SHA-256 pins syntax; version_added 0.1.0 is not installed version |
| vyos | READ | VyOS 1.4.x (sagitta) documentation; Ansible collection 6.0.0; runtime separately pinned/qualified |

## AUT-12

The guardrail says no, usefully

**Read:** current book chapters 52, 68–72.

**Prepare:** Read the referenced book chapters and the chosen panel scope. Identify the baseline, exact target release and acceptance observations before changing state.

**Resources:** a controller host, its pinned dependencies and an isolated target or supported fixture; verify target feature support before execution. No licensed image is bundled.

**Estimate:** 60-120 minutes. Editorial planning estimate for one selected vendor panel on a prepared lab; excludes provisioning and cross-vendor comparison. Not measured reader completion time.

**Expected result:** The positive owned-description proposal passes, every dangerous fixture fails and the refusal names the failed rule.

**Recovery and cleanup:** Restore only this task's changed state to the captured baseline using the platform's supported recovery method. Repeat the baseline acceptance probes and record any remaining differences; do not assume a factory reset is required.

| Platform | Evidence | Documented version/revision |
|---|---|---|
| iosxe | READ | IOS XE 17.15.x / Catalyst 9300; Ansible collection 11.5.1; runtime separately pinned/qualified |
| nxos | READ | NX-OS 10.5(x); Nexus 9000; Ansible collection 11.2.0; runtime separately pinned/qualified |
| eos | READ | EOS 4.36.2F; Ansible collection 12.2.0; runtime separately pinned/qualified |
| junos | READ | Junos OS; guide revision 2026-06-17; no release qualification; Junos Ansible guide revision 2026-08-24; juniper.device migration; device image separately qualified |
| srl | READ | SR Linux 24.10; Nokia srlinux collection main revision; fetched source SHA-256 pins syntax; version_added 0.1.0 is not installed version |
| vyos | READ | VyOS 1.4.x (sagitta) documentation; Ansible collection 6.0.0; runtime separately pinned/qualified |
