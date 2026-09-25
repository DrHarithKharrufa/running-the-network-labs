# Shared reference inventories — 25 September 2026

These files are teaching artefacts, not production designs or a tested deployment
bundle. The current changes have static and offline checks only. No new SR Linux,
FRR container, Containerlab or GNS3 execution is claimed. Record the actual image
digest, orchestrator, host, licence route and observations before claiming a run.

| Inventory | Nodes / links | Supplied state |
|---|---:|---|
| Aldergate | 12 / 14 | Wiring only; no configured firewall, HA, routing or hosts |
| Kestrel | 14 / 14 | IPv4 candidate configurations; runtime acceptance pending |
| Anvil | 10 / 12 | Wiring only; no underlay, EVPN, VXLAN, SONiC or GPU workload |

The `ixr-d2` and `ixr-d3` node types follow Containerlab's documented names.
Anvil uses D3 ports 29/30 for leaf uplinks, within its 32 QSFP28 ports. Aldergate
uses D2 ports 49/50, within its eight QSFP28 uplink ports after 48 SFP28 ports.
These are port-inventory checks, not proof of virtual port speed or image support.

## Kestrel candidate contract

Seven SR Linux 24.10.1 nodes and one FRR 10.2.1 subscriber stand-in participate
in level-2 IS-IS and an eight-node iBGP full mesh (28 sessions). Four further
FRR nodes represent two transits, a peer and a customer. Internal loopbacks are
10.255.0.{11,12,13,14,21,22,23,24}/32. The four-node core is a ring, not a mesh.
The historical `lon-pe-01` attachment to Birmingham and `bhm-bng-01` attachment
to Leeds are logical lab labels, not a physical cable or site design.

External import policies use exact prefixes and exact single-origin AS paths:

| Neighbour | Allowed prefixes | Local preference / provenance |
|---|---|---|
| Transit A, 64496 | default; 198.18.0.0/17; 198.19.0.0/17 | 100 / 64500:3000 |
| Transit B, 64497 | default; 198.18.128.0/17; 198.19.128.0/17 | 100 / 64500:3000 |
| Peer, 64498 | 198.51.100.128/25 | 150 / 64500:2000 |
| Customer, 64501 | 203.0.113.0/24 | 200 / 64500:1000 |

These intentionally narrow origin paths exclude prepending and downstream ASes.
They do not implement Internet-scale import policy, RPKI or relationship validation.
Import removes only the three local provenance tags before adding the assigned
tag; it preserves other communities, including well-known restrictions.
The sole customer prefix, with its customer tag, can leave to a peer/transit.
External eligible routes can leave towards the customer. No subscriber prefix,
infrastructure prefix or route learned from another upstream is authorised for
peer/transit export. The customer intentionally offers 10.0.0.0/8: reject it.

The core carries IPv4 BGP routes. This is not a BGP-free MPLS core. The FRR
subscriber stand-in originates 100.64.0.0/24 internally. There is no CGNAT,
PPPoE/IPoE subscriber lifecycle, RADIUS, public Internet or subscriber isolation.
Discard routes originate synthetic remote prefixes; they are not reachable
Internet servers. A host cannot ping a Null0 prefix to prove Internet service.

## Generate and inspect

From `configs`, use `python3 generate.py --out ../../../../candidate-kestrel` with
a fresh output directory. The renderer refuses to overwrite existing outputs.
Review a diff before replacing candidates. Configuration text is neither an
accepted transaction nor evidence of forwarding. Start with disposable instances;
inspect every startup log, running configuration, address and daemon state.

The offline audit parses actual generated policy text and checks the allowed and
forbidden advertisements, including forged provenance, unwanted prefixes,
more-specifics and wrong paths. It also checks inventory endpoints and the iBGP
graph. It is not a Nokia or FRR parser and does not emulate BGP selection.

## Runtime acceptance worksheet (all items initially UNVERIFIED)

1. Record host/runtime/node-kind versions, image digests and rights; check topology
   management networks against host and VPN routes. Complete `host-manifest.template.json`.
2. Validate candidate syntax on all images and save parser/startup logs. Check all
   point-to-point pairs and IS-IS adjacencies: eight internal links, sixteen
   directed adjacency records, including the BNG stand-in.
3. Check all eight /32 loopbacks bidirectionally; establish 28 iBGP sessions
   (56 directed neighbour records). Confirm every selected next hop resolves.
4. Check expected prefixes at the receiving peer and selected RIB/FIB. Verify
   customer's 10.0.0.0/8 rejection. Inject an eligible peer prefix carrying
   64500:1000: confirm the forged tag is removed and no peer/transit leak occurs.
5. Capture outbound updates to each upstream. Only the authorised customer /24
   is eligible; test default, subscriber, infrastructure and wrong-AS rejection.
   Withdraw a route and confirm removal rather than just a session remaining up.
6. Establish host-customer to subscriber-host ICMP and a bounded TCP service
   baseline with return-path evidence. It demonstrates this unrestricted lab
   path, not production subscriber isolation. Capture the data interfaces.
7. Remove each core link separately. Check connectivity, observed route changes,
   packet loss and recovery; a surviving graph alone is insufficient. A single
   edge attachment failure is expected to isolate that edge. Restore every fault.
8. Save state, restart a disposable node and compare persistence. Test deletion
   and full rebuild from the owned topology; retain failed runs. Destroy only the
   named lab and inspect residual interfaces, routes, mounts and processes.

## Sources

Checked 25 September 2026:
- https://containerlab.dev/manual/kinds/srl/
- https://documentation.nokia.com/srlinux/24-10/books/product-overview/hardware-overview.html
- https://documentation.nokia.com/srlinux/24-10/books/routing-protocols/rout-policies.html
- https://documentation.nokia.com/srlinux/24-10/books/routing-protocols/is-is.html
- https://documentation.nokia.com/srlinux/24-10/books/routing-protocols/bgp.html
- https://docs.frrouting.org/en/stable-10.2/bgp.html
