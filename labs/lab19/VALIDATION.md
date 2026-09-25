# Recorded local validation

FRR10.5.1-1ubuntu4.1; WSL Ubuntu26.04, Linux6.18.33.2.
Private network/mount namespaces; final fault run also uses private UTS
namespaces. Package binaries were extracted into the workspace, not installed
as host services. Host routes/accounts/FRR configuration were not changed.

- 20260916T225507Z: 24 passed assertions, six fault/parameter cases and recovery.
- 20260916T225246Z: 25 passed assertions, area policy, two link failures and
  normal-area restoration, using the explicit process resets in README.

Evidence is under publication-revision/runtime-evidence/<run>/results.json
with commands, observed output, captures and daemon logs. Earlier failed runs
are retained. They exposed startup/observation timing, retained live-conversion
state and the need to distinguish Full from service recovery. Their failed
end-to-end status is not relabelled as a passing run.

Semantic non-MaxAge record totals: normal12 (2 router,8 summary,1 ASBR,1 external),
fresh stub11 (2 router,9 summaries including default), default-only3
(2 router,1 default summary). A retained non-MaxAge record is not necessarily
an installed route; inspect routing state too.

Static checks parse topology/binds, Python and shell syntax. Docker image
build, Containerlab orchestration, commercial NOS, OSPFv3, broadcast DR
behaviour, NSSA translation, key rotation/replay, restart persistence, scale
and hardware convergence have not been executed. The local runner measures
bounded control/forwarding behaviour, not a production readiness guarantee.
