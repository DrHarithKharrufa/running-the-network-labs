# Validation record — Lab 20

Recorded 17 September 2026 local time (run timestamps below are UTC).

The final run `20260916T225833Z` passed 30 assertions using actual extracted
FRR 10.5.1-1ubuntu4.1 on Ubuntu 26.04 / WSL Linux 6.18.33.2, in five private
network/mount/UTS namespaces. The topology addresses and FRR files were loaded
from this lab. Host accounts, service configuration and trust stores were not
modified. This adapter is not Containerlab or commercial vendor execution.

Observed: dual-stack baseline and all peer loopbacks; ten directed Up
adjacencies; a received LSP reporting valid legacy authentication; standard
overload moving IPv4 but not IPv6 MT2; the topology-specific IPv6 overload
moving IPv6; attached-router reachability; restoration; finite cost200 and
restoration; physical link failure losing two directed adjacency records and
restoration; rejection of narrow with multi-topology configured; an explicit
IPv4-only narrow phase retaining adjacency while losing service; transition
restoring IPv4; and restoration to the wide dual-stack baseline.

The standard-overload command-to-observed-IPv4-route interval was approximately
0.307 seconds in this run. Continuous overload/restoration probes sent 63 IPv4
and 64 IPv6 packets at a requested100ms interval, over about6.5seconds per
stream, and received them all. This is a bounded observation, not a zero-loss
or general convergence guarantee. The streams do not cover the later metric
and interface-failure experiments, which have separate service checks.

Prior attempts remain in the evidence directory. In `20260916T225558Z`, the
JSON detailed-database command with narrow records triggered SIGABRT in isisd:
`json_object_array_add` asserted the object was an array, with `lsp_print_all`
in the backtrace. The final run uses the plain-text detailed database for
narrow/transition states. Do not report the failed attempt as a passing run,
or as evidence that narrow operation itself necessarily aborts the daemon.

Evidence: `outputs/publication-revision/runtime-evidence/20260916T225833Z`
relative to the review project, with results.json, commands, configurations,
daemon logs, route/database snapshots and timestamped probe output. The
failed-run backtraces are under the corresponding earlier run directory.

Prepared but not executed here: the Dockerfile build and Containerlab
deployment/start scripts. Unexecuted protocol scope includes L1/L2 leaking,
broadcast DIS election, duplicate-system-ID injection, authentication key
rollover and modern algorithms, restart recovery, SR forwarding, multivendor
interoperability and production hardware/scale. Static syntax/structure
checks do not change those execution boundaries.
