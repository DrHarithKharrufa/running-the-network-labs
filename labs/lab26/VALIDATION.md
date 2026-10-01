# Lab 26 validation boundary

Run `20260917T012854Z` records **31 passed assertions** with FRR
10.5.1-1ubuntu4.1 and Linux 7.0.0-31-generic in an isolated QEMU guest.
The host WSL kernel lacks MPLS routing; guest execution does not change that.
No external network interface was attached to the guest. Packages were
extracted into private directories, without installing or repairing host services.

The namespace adapter executes the topology's addressing/kernel commands and
the FRR baseline/LDP configuration files. It independently installs the four
manual service forwarding entries. The Containerlab orchestration, image build,
start scripts and Docker service-install wrapper are not implied to have run.
The separate run `20260917T013621Z` executes the delivered `service-labels.py`
inside each PE's private namespace: ten assertions verify its two installations,
customer delivery and PHP capture. That tests the Python helper, while leaving
the Docker shell orchestration explicitly unexecuted.

Observed coverage:
- Five core link adjacencies, ten directed operational LDP rows, learned PE
  transport labels and bidirectional customer delivery without customer IGP routes.
- Captured transport/service stack and PHP; removed service label and disabled
  MPLS input each cause independent failure and recover after restoration.
- A 1,500-byte core MPLS payload budget passes 1,492-byte customer IPv4 packets
  with two labels, rejects 1,493 bytes and passes smaller probes. Both link-end
  MTUs are changed together and the preferred path is explicitly checked.
- Explicit null above the service label fails with egress loopback MPLS input
  disabled, works when enabled, and repeats the failure/recovery in a negative
  control. A single-label explicit-null PE-loopback probe continues working.
- Blocking UDP/646 Hellos on the configured preferred core link leaves IS-IS
  selected but loses service. P-router IP reachability remains; the far-PE
  ordinary IP probe also fails in this retained forwarding state. Enabling
  IS-IS LDP synchronisation selects the healthy alternate and restores service.
  Removing the exact drop rules restores LDP, the preferred path and service.

This sustained readiness gap is not a timed returning-link convergence test.
No loss bound, MPLS LSP-ping implementation, QoS scheduling/TTL-model suite,
IPv6 transport, VPN RD/RT isolation, commercial NOS or hardware is verified.
Earlier failures remain in the evidence, including a one-sided MTU change
that rerouted traffic and an LDP-interface removal that did not represent
the configured-interface discovery failure used in the final case.

Evidence is in `runtime-evidence/20260917T012854Z` relative to the
publication-revision directory: results, exact commands, control snapshots,
kernel tables, raw captures and decoded captures. The review harness remains
separate from the learner-facing Containerlab adapter.
