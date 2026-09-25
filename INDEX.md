# Chapter to lab index

Every lab in this repository and the chapter it belongs to. `L1`-`L5` is the
book's own ladder: Foundation, Operations, Engineering, Architecture, Leadership.

Labs not tied to one chapter: [`common`](labs/common), [`gns3`](labs/gns3),
[`reference-designs`](labs/reference-designs), [`standards`](labs/standards),
[`topologies`](labs/topologies).


## Orientation

| Ch | Level | Chapter | Lab | What it runs |
|---|---|---|---|---|
| 1 | L1 Foundation | Why this book exists, and how to read it | — | — |
| 2 | L1 Foundation | The shape of the industry and the shape of a career | — | — |
| 3 | L1 Foundation | Building the lab: Containerlab and GNS3 | [`lab03`](labs/lab03) | Containerlab, shell, Python |

## Foundations

| Ch | Level | Chapter | Lab | What it runs |
|---|---|---|---|---|
| 4 | L1 Foundation | Signals, cables and optics | [`lab04`](labs/lab04) | Containerlab, Python |
| 5 | L1 Foundation | Ethernet and the local network | [`lab05`](labs/lab05) | Containerlab |
| 6 | L1 Foundation | IP addressing, subnetting and IPv6 done properly | [`lab06`](labs/lab06) | Containerlab, shell, Python |
| 7 | L1 Foundation | The transport layer: TCP, UDP and QUIC | [`lab07`](labs/lab07) | Containerlab, shell, Python |
| 8 | L1 Foundation | The services that make a network usable | [`lab08`](labs/lab08) | Containerlab, shell, Python |
| 9 | L1 Foundation | Following a packet from application to application | [`lab09`](labs/lab09) | Containerlab, shell, Python |
| 10 | L1 Foundation | Living on the command line: network operating systems | [`lab10`](labs/lab10) | Containerlab |

## Campus

| Ch | Level | Chapter | Lab | What it runs |
|---|---|---|---|---|
| 11 | L2 Operations | VLANs, trunks and the access layer | [`lab11`](labs/lab11) | Containerlab, shell, Python |
| 12 | L2 Operations | Spanning tree and the loop problem | [`lab12`](labs/lab12) | Containerlab, shell, Python |
| 13 | L2 Operations | Link aggregation, MLAG and redundant gateways | [`lab13`](labs/lab13) | Containerlab, shell, Python |
| 14 | L2 Operations | Wireless: Wi-Fi 6E, Wi-Fi 7 and RF planning | [`lab14`](labs/lab14) | Python |
| 15 | L2 Operations | Controlling who gets on: 802.1X, NAC, PoE and IoT | [`lab15`](labs/lab15) | Containerlab, shell, Python |
| 16 | L3 Engineering | Campus architectures and overlays | [`lab16`](labs/lab16) | — |

## Routing

| Ch | Level | Chapter | Lab | What it runs |
|---|---|---|---|---|
| 17 | L2 Operations | How a router actually forwards | [`lab17`](labs/lab17) | Containerlab, Python |
| 18 | L2 Operations | Static routing and the routing table under pressure | [`lab18`](labs/lab18) | Containerlab, shell, Python |
| 19 | L2 Operations | OSPF | [`lab19`](labs/lab19) | Containerlab, device configs, shell, Python |
| 20 | L3 Engineering | IS-IS | [`lab20`](labs/lab20) | Containerlab, device configs, shell |
| 21 | L3 Engineering | BGP I: the protocol | [`lab21`](labs/lab21) | Containerlab, device configs, shell |
| 22 | L3 Engineering | BGP II: policy, scale and control | [`lab22`](labs/lab22) | Containerlab, device configs, shell, Python |
| 23 | L3 Engineering | VRFs, redistribution and route leaking | [`lab23`](labs/lab23) | Containerlab, device configs, Python |
| 24 | L3 Engineering | Multicast | [`lab24`](labs/lab24) | Containerlab, device configs, shell, Python |

## Provider

| Ch | Level | Chapter | Lab | What it runs |
|---|---|---|---|---|
| 25 | L3 Engineering | Anatomy of an ISP | [`lab25`](labs/lab25) | Python |
| 26 | L3 Engineering | MPLS foundations | [`lab26`](labs/lab26) | Containerlab, device configs, shell, Python |
| 27 | L4 Architecture | Traffic engineering: RSVP-TE to Segment Routing | [`lab27`](labs/lab27) | Containerlab, device configs, shell |
| 28 | L4 Architecture | SRv6 and the modern core | [`lab28`](labs/lab28) | Containerlab, device configs, shell, Python |
| 29 | L3 Engineering | L3VPN | [`lab29`](labs/lab29) | Containerlab, device configs, shell |
| 30 | L4 Architecture | L2VPN and EVPN | [`lab30`](labs/lab30) | Containerlab, device configs, shell, Python |
| 31 | L3 Engineering | Quality of service | [`lab31`](labs/lab31) | Containerlab, shell, Python |
| 32 | L4 Architecture | The subscriber edge: BNG, CGNAT and IPv6 for customers | [`lab32`](labs/lab32) | Containerlab, Python |
| 33 | L4 Architecture | Peering, transit and the economics of the Internet | [`lab33`](labs/lab33) | Python |
| 34 | L4 Architecture | Internet routing security: RPKI, IRR and MANRS | [`lab34`](labs/lab34) | Containerlab, device configs, shell, Python |

## Data centre

| Ch | Level | Chapter | Lab | What it runs |
|---|---|---|---|---|
| 35 | L3 Engineering | Data centre fabric design | [`lab35`](labs/lab35), [`topologies`](labs/topologies) | Containerlab, device configs, Python, Python |
| 36 | L3 Engineering | BGP in the data centre | [`lab36`](labs/lab36), [`topologies`](labs/topologies) | Containerlab, device configs, Python, Python |
| 37 | L4 Architecture | VXLAN/EVPN fabrics and data centre interconnect | [`lab37`](labs/lab37) | Python |
| 38 | L4 Architecture | Whitebox, SONiC and disaggregation | [`lab38`](labs/lab38) | Python |
| 39 | L4 Architecture | Programmable data planes: P4, eBPF/XDP and DPUs | [`lab39`](labs/lab39) | Python |
| 40 | L3 Engineering | Where the server meets the network | [`lab40`](labs/lab40) | Python |
| 41 | L4 Architecture | Fabrics for AI and HPC | [`lab41`](labs/lab41) | Python |
| 42 | L3 Engineering | Cloud networking and hybrid interconnect | [`lab42`](labs/lab42) | Python |

## Optical

| Ch | Level | Chapter | Lab | What it runs |
|---|---|---|---|---|
| 43 | L3 Engineering | Fibre plant and the outside world | [`lab43`](labs/lab43) | Python |
| 44 | L3 Engineering | Optical transmission and link budgets | [`lab44`](labs/lab44) | Python |
| 45 | L4 Architecture | DWDM, coherent optics and ROADMs | [`lab45`](labs/lab45) | Python |
| 46 | L4 Architecture | Open line systems and packet-optical convergence | [`lab46`](labs/lab46) | Python |
| 47 | L4 Architecture | Timing and synchronisation | [`lab47`](labs/lab47) | Python |
| 48 | L4 Architecture | Mobile transport: 4G, 5G, backhaul, fronthaul and slicing | [`lab48`](labs/lab48) | Python |
| 49 | L3 Engineering | Microwave, satellite and fixed wireless access | [`lab49`](labs/lab49) | Python |

## Security

| Ch | Level | Chapter | Lab | What it runs |
|---|---|---|---|---|
| 50 | L3 Engineering | A working threat model for network operators | [`lab50`](labs/lab50) | Python |
| 51 | L3 Engineering | Cryptography for network engineers | [`lab51`](labs/lab51) | Python |
| 52 | L3 Engineering | Identity, access and the management plane | [`lab52`](labs/lab52) | Python |
| 53 | L3 Engineering | Hardening the device and the control plane | [`lab53`](labs/lab53) | Python |
| 54 | L3 Engineering | Firewalls, zones and segmentation | [`lab54`](labs/lab54) | Python |
| 55 | L4 Architecture | Micro-segmentation, zero trust and SASE | [`lab55`](labs/lab55) | Python |
| 56 | L3 Engineering | VPNs and encrypted transport | [`lab56`](labs/lab56) | Python |
| 57 | L4 Architecture | DDoS: surviving the flood | [`lab57`](labs/lab57) | Python |
| 58 | L3 Engineering | DNS and the Internet edge as an attack surface | [`lab58`](labs/lab58) | Python |
| 59 | L4 Architecture | Detection, response and network forensics | [`lab59`](labs/lab59) | Python |
| 60 | L5 Leadership | Security governance, compliance and assurance | [`lab60`](labs/lab60) | Python |

## Operations

| Ch | Level | Chapter | Lab | What it runs |
|---|---|---|---|---|
| 61 | L2 Operations | The NOC and the operating model | [`lab61`](labs/lab61) | Python |
| 62 | L3 Engineering | Monitoring, telemetry and observability | [`lab62`](labs/lab62) | Python |
| 63 | L3 Engineering | Flow, logs and packet capture | [`lab63`](labs/lab63) | Python |
| 64 | L2 Operations | Troubleshooting as a discipline | [`lab64`](labs/lab64) | Python |
| 65 | L3 Engineering | Change management | [`lab65`](labs/lab65) | Python |
| 66 | L3 Engineering | Incidents, outages and post-incident review | [`lab66`](labs/lab66) | Python |
| 67 | L4 Architecture | Capacity planning and traffic forecasting | [`lab67`](labs/lab67) | Python |

## Automation

| Ch | Level | Chapter | Lab | What it runs |
|---|---|---|---|---|
| 68 | L3 Engineering | Source of truth: documentation as data | [`lab68`](labs/lab68) | Python |
| 69 | L3 Engineering | Configuration management with Ansible and Jinja | [`lab69`](labs/lab69) | Python |
| 70 | L4 Architecture | Models and management APIs | [`lab70`](labs/lab70) | Python |
| 71 | L3 Engineering | Python for network engineers | [`lab71`](labs/lab71) | Python |
| 72 | L4 Architecture | Event-driven automation and closed loops | [`lab72`](labs/lab72) | Python |
| 73 | L4 Architecture | CI/CD, pre-change validation and digital twins | [`lab73`](labs/lab73) | Python |
| 74 | L4 Architecture | Machine learning for network operations: what works | [`lab74`](labs/lab74) | Python |
| 75 | L4 Architecture | LLMs in the NOC: retrieval, generation and evidence | [`lab75`](labs/lab75) | Python |
| 76 | L4 Architecture | Agents, tool use and controlled automation | [`lab76`](labs/lab76) | — |
| 77 | L4 Architecture | Intent-based networking and autonomous networks | [`lab77`](labs/lab77) | Python |
| 78 | L5 Leadership | Governing automation and AI | — | — |

## Design

| Ch | Level | Chapter | Lab | What it runs |
|---|---|---|---|---|
| 79 | L4 Architecture | The design method | [`lab79`](labs/lab79) | Python |
| 80 | L4 Architecture | Availability, resilience and failure domains | [`lab80`](labs/lab80) | Python |
| 81 | L4 Architecture | Addressing, naming and numbering plans | [`lab81`](labs/lab81) | Python |
| 82 | L4 Architecture | Scaling: what breaks at ten times the size | [`lab82`](labs/lab82) | Python |
| 83 | L4 Architecture | Multi-site, multi-region and hybrid | [`lab83`](labs/lab83) | Python |
| 84 | L4 Architecture | Migrations, cutovers and brownfield reality | [`lab84`](labs/lab84) | Python |

## Business

| Ch | Level | Chapter | Lab | What it runs |
|---|---|---|---|---|
| 85 | L5 Leadership | Network economics: CAPEX, OPEX and unit cost | [`lab85`](labs/lab85) | Python |
| 86 | L5 Leadership | Vendor management, RFPs and lifecycle | — | — |
| 87 | L5 Leadership | SLAs, SLOs and what you can promise | [`lab87`](labs/lab87) | Python |
| 88 | L5 Leadership | Regulation, compliance and obligation | — | — |
| 89 | L5 Leadership | Building and leading a network team | — | — |
| 90 | L5 Leadership | Strategy, roadmaps and build-versus-buy | — | — |
| 91 | L5 Leadership | The CTO's dashboard | [`lab91`](labs/lab91) | Python |
