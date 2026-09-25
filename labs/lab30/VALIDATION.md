# Lab 30 validation boundaries

## Source and baseline execution

All 449 incoming Chapter 30 lines and five original lab files were read.
The previous fixture mixed unsupported PW/VPLS assumptions with incomplete
SR Linux VXLAN objects. Original files remain in the review backup.

Run 20260917T084016Z: 30 assertions passed on Linux 6.18.33.2-microsoft-standard-WSL2,
iproute2 6.19.0 and extracted Ubuntu FRR 10.5.1-1ubuntu4.1. Real Linux namespaces,
kernel bridges/VXLAN and private FRR processes execute the baseline topology
commands and pe1/pe2/pe3 configs. This is not Containerlab execution.

Eleven independent binary-PCAP checks inspect 19 captures: silent/unknown
destinations 5+5; known destination 0+5; flood disable 0+0 but known 0+5; restore 5+5.
ARP request crosses overlay with suppression off and stays local with it on,
with a matching host reply. Three 1450-byte inner IP packets give outer IP 1500;
three restored 1500-byte packets give outer IP 1550, VNI 3000, DF set and inner
TTL 64. Captured ICMP type 3/code 4 reports 1450 for the rejected 1451-byte packet.
Host route-get retains a 1450 PMTU with a 599-second expiry at observation.
Explicitly flushing only that disposable host's cache restores large probes.
This is not automatic immediate PMTU recovery or a full PMTUD application suite.

Run 20260917T083254Z failed before assertions: an AF-inapplicable generic
send-community command caused CLI context fallback. Run 20260917T083616Z passed
24 assertions then failed the assumed immediate large-packet recovery; it
exposed the retained host PMTU. Both attempts and captures are retained.

## Multihoming experiment

Run 20260917T084250Z passed two setup assertions and eight of ten service
requirements. Overall acceptance FAILED. ESI/type 4, a two-member CE aggregator,
pe2 DF/pe3 non-DF, a kernel MAC next-hop group and 128 UDP flows split 70/58 were
observed. Attachment and core isolation/restoration recovered reachability.
Eight remote broadcasts produced 8+8 member arrivals and 16 at the bond; eight
locally originated broadcasts appeared on both CE members. First reverse
ping also had one duplicate reply. These observations must not be labelled
complete multihoming support. Follow-up run 20260917T084548Z passed four setup assertions and seven of
eleven acceptance requirements, but FAILED overall. Type 1 routes and matching
DF/non-DF state were confirmed. Independent binary decoding confirms 8+8 remote
broadcast arrivals, 16 bond deliveries, and locally sourced frames transmitted
8/0 but received 0/8 on the two direction-filtered CE members. The 128 distinct
UDP flows again split 70/58 with no duplicated or missing flow IDs. The core
isolation probe, started after a five-second wait, failed in this run;
restoration worked. Do not claim consistent core-failure recovery or a
convergence bound from these observations. Root cause of that varied core
observation is not established; duplicate delivery and return direction are
directly evidenced. A first reverse ping had a duplicate in both runs.

## Not established

No Docker build/deploy or Containerlab validation; no commercial NOS, ASIC,
MPLS PW, VPLS, EVPN-MPLS, IPv6 underlay, ND/DAD, IRB/type 5, multicast membership
proxy, hardware-scale result or timed convergence guarantee. The experimental
MH duplicate/split-horizon failure remains an acceptance failure, even where
other functions worked. The exact send-frame.py helper ran separately in 20260917T084934Z: three
assertions verify five received 100-byte frames with the intended addresses,
EtherType and tag, and rejection of a nonpositive count. This helper check
is separate from EVPN service execution.

The standards/source review uses RFCs 4448/8469/8077/4761/4762/7432/8365/8584/7348/
9135/9136/9251 and FRR stable-10.5 documentation. Source review, Linux execution,
orchestration and commercial execution are different evidence categories.
