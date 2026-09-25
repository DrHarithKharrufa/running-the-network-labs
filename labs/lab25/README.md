# Lab 25 — map Kestrel before trusting the map

Begin with a **static inventory**, then a separately identified deployment
stage. The shared topology is a legacy IPv4 teaching configuration; its full
provider/service integration is not yet validated. Chapter 25's diagram is a
logical planning view, not a port map or a production fleet. Do not infer
readiness from the topology or the checks below passing.

## Read-only inventory and model

Requires Python 3 and PyYAML in a suitable isolated Python environment.
From this directory, run `python3 audit.py --output review.json`.
The script reads `../topologies/kestrel.clab.yml` and every referenced
configuration. It does not import or execute the historical generator and
does not change configurations, interfaces or services. The output contains
source hashes, addresses, declared iBGP neighbours, all 14 links,
open issues, 37 graph cases and hypothetical GBP arithmetic.

The 17 September 2026 review recorded **80 passed structural/model checks and
31 open observations**. Passing means recorded endpoints and connected
prefixes agree, and the stated graph/arithmetic cases hold. It does not
make the configurations operational. Some observations repeat a problem per
node or matching line; 31 is not 31 independent defects.

## Integration revision, 25 September 2026

The historical 80/31 result above remains historical. The shared candidates now
include reciprocal BNG iBGP neighbours, exact external prefix/path guards,
explicit export policy and internal next-hop-self. Incoming local provenance
tags are removed before a class is assigned; well-known communities remain.
Transit examples use the reserved benchmark block; all FRR external peers
require explicit import/export policy. Anvil port numbering and Containerlab
type names were also corrected. Read `../topologies/README.md` and run its
`test_inventory.py` for the separate offline policy/inventory checks.

This fixture deliberately uses standard class communities. Lab22's different
large-community contract belongs to that separate lab; do not combine the
configurations without translating and testing the complete policy.

The core remains an IPv4 BGP core, not BGP-free MPLS. Subscriber, CGN, IPv6,
VPN and transport services are not implemented by the fixture. Cross-site
hostnames are historical logical labels, not physical cable placement.
Startup acceptance, RIB/FIB state, live route-policy behaviour, service traffic,
persistence and failure/recovery remain unverified on the specified images.
Discard-originated synthetic prefixes are not reachable Internet applications.

The scanner does not parse complete NOS grammar or detect every issue. Image
support/licensing, startup, host management/default routes, protocol syntax
and end-to-end services need separate checks. Executed Lab 21/22 variants
provide their own bounded evidence; do not attribute it to this shared topology.

## Deliver three linked inventories

1. Devices: intended function, implemented protocols, site, owner, version,
   capacity and dependent services. Naming is only a clue.
2. Links: both interfaces/addresses, prefix, medium, contractual rate,
   physical route/shared risk and baseline/failure load. The model has no
   observed link rate or price. Do not assume only two links cost money.
3. Services: subscriptions/circuits represented, setup and established-flow
   dependencies, alternate paths, recovery objectives and required evidence.

The graph gives each host an artificial population: host-sub represents
50,000 broadband subscriptions; host-cust represents 900 business circuits.
Any surviving path to either transit satisfies the model's general-transit
requirement. It has no BGP policy, convergence, capacity, stateful functions,
DNS/AAA, shared-risk or application model. The peer is not universal transit.
The worst single internal-node exposure is 50,000 units; paired borders and
paired PE/BNG each expose 50,900 for different reasons. Summed units are not
unique people or measured outages. Compare all tied maxima in the output
instead of claiming one uniquely worst pair.

## Deployed stage and economics

After integration is corrected on an available target, capture live
interfaces, routes, neighbours and service tests. Reconcile intended and
observed inventories; introduce one fault at a time, retain measurements and
restore. Containerlab/commercial execution remains pending in this review.

For the hypothetical contract, transit costs GBP 1,200 before and GBP 1,000
after. Adding GBP 300 peering yields GBP 1,300: an increase of GBP 100.
With GBP 100 peering, the total is GBP 1,100. If a renegotiated 8,000 Mb/s
commit uses GBP 0.10/Mb/s and the new billable rate stays 9,000 Mb/s, transit
costs GBP 900; with GBP 300 peering the total is GBP 1,200. All exclude VAT;
these are arithmetic examples, not quotes. The model takes billable rates as
inputs; Lab 33 addresses their separate calculation from traffic samples.

The corrected business /38 contains 1,024 /48s and separate broadband /40
contains 65,536 /56s, both inside the /36. A business /40 offers only 256
/48s; expanding it to /38 overlaps the originally proposed broadband block.
Preserve reservations and growth assumptions in the inventory.
