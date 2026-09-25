# Lab29 validation record

Completed bounded execution: **20260917T025506Z**, 31 assertions passed. Independent
PCAP decoding checks six captures containing 18 selected echo requests:
two labels before PHP, one after PHP with the same service label, and the
same unlabelled packet on both hub attachments with a one-hop TTL decrease.
The deny rule has a positive packet counter. Evidence includes complete
commands/results, BGP/VRF/kernel/LFIB snapshots and captures.

Environment: FRR 10.5.1 Ubuntu package 10.5.1-1ubuntu4.1, iproute2 6.19.0,
isolated QEMU 10.2.1/Linux 7.0.0-31-generic. Three provider routers, three
actual CE BGP routers, three site hosts and one private external test host
use isolated network namespaces. The QEMU guest has no external network
device. Native results were exported with SHA256 checks; archives were
extracted with Python's data filter. Run IDs use the guest clock and are
not a cross-host timing reference or a convergence benchmark.

## Executed behaviour

- IPv4 IS-IS/LDP transport and PE-to-PE VPNv4 exchange; automatic per-VRF
  service labels; distinct kernel VRFs/attachments and configured CE policies.
- Same-AS CE rejection before PE AS override, followed by all six ordered
  site-to-site directions working after the supplied override files load.
- Core IPv4 table without customer routes, with actual labelled customer
  forwarding and before/after PHP captures.
- Missing site1 RT import removes service while PE-loopback transport works;
  restoring import restores delivery.
- Hub ingress/return contexts, advertised summary, separate same-PE spoke
  VRFs, selected external-default RT and observed hub traversal.
- Hub deny stops the selected spoke flow. A deliberate direct-spoke RT import
  creates a more-specific bypass. Correcting the complete import list retains
  the hub summary, removes the direct spoke route, and produces both failed
  probes and an increasing hub deny counter. Removing that rule restores
  delivery: the negative test is not merely loss from a missing route.
- Site2's authorised default reaches the synthetic external endpoint while
  site3 cannot. A deliberate site3 external-RT import grants delivery; restoring
  its healthy list removes external access while preserving private reachability
  and site2's authorised external service.

The external endpoint is 198.51.100.2 on a private link with explicit return
routing. It is not public Internet access and does not execute NAT or a
stateful commercial firewall.

## Failed attempts and corrections

Runs 20260917T024221Z and 20260917T024625Z each pass 19 assertions before
failing the hub attachment capture check. The filter `mpls or icmp` excludes
ordinary ICMP because the MPLS primitive changes subsequent BPF offsets.
Core labelled captures showed the round trip, but empty attachment captures
could not validate it. The corrected `icmp or mpls` filter records both.
See the upstream libpcap pcap-filter documentation; this is a measurement
setup correction, not a demonstrated forwarding bypass.

Run 20260917T024927Z passes 25 assertions, then fails restoration after the
hub deny is removed. In this FRR CLI, `rt vpn import` sets the supplied list;
the attempted one-RT addition had replaced the healthy list. Removing that
RT left no remote route. Its earlier failed ping therefore did not prove
restored inspection. The final run applies complete lists and checks both
route state and the deny counter. All failed evidence remains preserved.

## Not executed

Docker build/Containerlab/startup wrappers; commercial NOS/ASIC adapters;
IPv6 VPNs; OSPF domain/sham-link/DN-bit cases; multihomed CE/SoO or backdoor
loop scenarios; inter-AS A/B/C; RT constraint/RR scaling; label exhaustion;
maximum-prefix overflow/restart; QoS and SLA/load/failure timing; NAT,
stateful inspection and real upstream Internet service. Configuration files
were loaded by the isolated FRR adapter, not by Containerlab.

Source YAML/endpoint/bind checks and shell syntax checks are separate from
the runtime above. The generated shell files were normalised to LF after
a CRLF syntax failure. No orchestration execution is implied by bash -n.
