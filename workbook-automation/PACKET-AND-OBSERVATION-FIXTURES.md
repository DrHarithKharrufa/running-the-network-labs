# A packet offer is not a packet capture

`packet_fixtures.py` creates PCAP files offline and never transmits. The manifest
labels them synthetic offers. Keep them separate from actual ingress/egress
captures and retain the generated file's hash. Ethernet files omit the hardware
FCS; the NIC adds it on transmission. The experimental EtherType 0x88b5 is a
bounded learning stimulus, not ARP or a service request.

## DC-04: exactly five intentional CE transmissions

Use the actual fresh owned CE source MAC and the real remote CE destination MAC:

```text
python packet_fixtures.py --kind ce-five --src-mac 02:00:00:00:01:01 --dst-mac 02:00:00:00:02:02 --out ce-five.pcap
```

The file contains five uniquely labelled 60-byte Ethernet frames before FCS.
On the isolated CE attachment, use one reviewed replay of that file, not a ping
whose ARP/retry/response traffic changes the count. Independently capture the
ingress offer and destination delivery. Record discovery, control traffic and
capture duplicates separately. Five here means **intentional CE transmissions**,
not every frame observed in the fabric. Check source-MAC learning, exact RT2
identity/attributes, remote FDB and observed aging/withdrawal separately.

## OPS-05: WJH reason 209

```text
python packet_fixtures.py --kind wjh-source-multicast --out wjh-five.pcap
```

This deliberately malformed source MAC is 01:00:5e:00:00:01. Replay exactly the
five frames only on a physically isolated owned ingress; do not connect it to a
shared network. Reason209 means **Source MAC is multicast**, not an ACL denial.
Verify actual platform/path/reason mapping before the offer. Keep the independent
wire witness and compare event category, interface and aggregate count. Observe
two complete publication windows; the vendor example batches 30-second windows.
Use a finite 120-second controller stop bound, qualified against actual cadence.
Do not increase traffic because a ten-second stream was silent.

## VPN-06: a concrete Linux plain-End fixture

The Linux panel configures plain End at 2001:db8:1:1::100 on the owned ingress.
Before injection, prove the target's actual local /128 function and route to
2001:db8:3:3::100, plus trusted ingress/seg6_enabled and an independent capture on
the following link. Resolve actual ingress/next-hop MACs. The defaults are
documentation addresses, not a discovered or complete device baseline:

```text
python packet_fixtures.py --kind classic-end --local-sid 2001:db8:1:1::100 --next-sid 2001:db8:3:3::100 --out end-pair.pcap
```

The file has two IPv6/SRH frames: LastEntry1, wire Segment List[0]=nextSID and
[1]=localSID, outerDA=localSID, HopLimit8. The valid packet has SegmentsLeft1 and
should leave this plain End with DA=nextSID, SL0, HopLimit7. The negative packet
has SL0 at this plain End; require the documented local-function rejection rather
than expecting the same behavior from a flavored endpoint. NextHeader59 means
no transport payload: this trial observes the endpoint transformation, not an
application service. Capture before/after the tested endpoint, offer each packet
once and inspect the appropriate action/drop evidence.

Removing the /128 can reveal a covering route and transit behavior. Record that
route and next hop, preserve the bounded HopLimit and count, and score the missing
local transformation rather than assuming ultimate payload loss. Restore the
exact owned route. Never treat a constructed PCAP as captured device evidence.

## Other SRv6 formats require their actual function manifest

IOS XE f3216 and IOS XR uN use compressed micro-segment behavior; Junos USD,
SR OS USP and FRR's allocated SID differ from the Linux plain-End recipe. Do not
replay the plain-End packet unchanged at those targets. Use the following exact
preparation record for each chosen variant, then generate/review its actual
format using the vendor's returned model/reference. Missing values stop the
packet phase and are recorded NOT_RUN rather than guessed:

| Field | Required evidence |
|---|---|
| Node role and actual SID | Operational locator/function allocation, namespace and model revision |
| Format | Classic full SID or compressed block/function/container lengths |
| Behavior/flavor | End/uN/USP/USD/PSP and exact permitted terminal action |
| Packet fields | Outer source/DA/next-header/HopLimit; SRH list/LE/SL or compressed container and next micro-segment |
| Next segment | Actual underlay route, next hop and egress/capture point |
| Positive | Precisely predicted DA/SL/header/decapsulation transform |
| Negative | One documented invalid condition for this exact behavior |
| Withdrawal | Remaining cover route and predicted alternate local/transit outcome |
| Recovery | Exact original function plus rediscovered allocated SID if dynamic |

The workbook's READ panels establish device syntax; a format-specific generated
packet and hardware outcome require this qualified manifest. This explicit gate
is essential where terminal/header behavior differs.

## OPS-11 and OPS-12

`timed_capture.py` previews a tcpdump argv with count10, snap160 and a separate
ten-second controller stop request, followed by at most three seconds of
termination grace before a forced kill. The result records actual elapsed time
and the stop outcome. Invoke its explicit --execute only inside the
declared lab VM/namespace, with an owned interface and new output filename.
Counts can wait forever without the time bound. A 160-byte snapshot can truncate
payloads, and a CPU/local capture may omit ASIC transit; use a separate wire
witness and label both observation boundaries.

`COUNTER-WORKSHEET.csv` and `counter_worksheet.py` provide five actual offline
rows. Ordinary64-bit delta is600octets/2s=2400bit/s. The bounded32-bit wrap is
296octets/1s=2368bit/s. Reset, changed identity and a rate/interval allowing
multiple wraps are refused. The rate bound is part of the input evidence, not a
permission to assume every negative delta is a wrap. No physical counter clearing
is needed. Actual device octet boundaries, width, reset markers and offload
effects are separately recorded.
