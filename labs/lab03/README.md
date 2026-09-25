# Lab 3: first link and routed extension

This lab requires an isolated supported Linux host, Docker, Containerlab and access
to quay.io/frrouting/frr:10.2.1. Record actual versions, image digest and host resources.
The first topology tests local IPv4 reachability; the second tests two-subnet kernel routing.
Neither establishes FRR protocol convergence or hardware performance.

From this directory:

```sh
set -o pipefail # Bash: preserve verifier failure through tee
sudo containerlab deploy -t first.clab.yml
bash verify.sh 2>&1 | tee first-test.log
sudo containerlab destroy -t first.clab.yml
sudo containerlab deploy -t routed.clab.yml
docker exec clab-first-routed-r1 ip route
```

For the routed topology the container names are `clab-first-routed-r1`,
`clab-first-routed-r2` and `clab-first-routed-r3`; inspect all three route tables.
Use `docker exec clab-first-routed-r1 ping -I 10.0.12.1 -c 5 -W 1 10.0.23.2`.
Remove the return route on r3, require failure, restore it via 10.0.23.1 and require recovery.
Destroy using `sudo containerlab destroy -t routed.clab.yml` when finished.

The direct-link and routed positive/fault/recovery cases passed in disposable Linux
network namespaces on 16 September 2026. Containerlab deployment and the FRR image
remain untested. See `../RESUMED-VALIDATION.md` for the exact evidence boundary.

The verifier now requires exactly 5 transmitted/5 received before and after the fault,
and 5 transmitted/0 received with ping status 1 during the fault. An execution error,
missing summary or partial success fails. It attempts restoration after a disable
attempt; a restoration error is a failing result requiring console inspection.

`python3 test_verify.py -v` runs eight tests of the actual Bash script against a temporary
local `docker` command double. They include partial replies, command errors, unexpected
negative success, wrong counts, missing summaries and failed restoration. These are
offline acceptance-logic tests, not Docker, Containerlab or network execution. The C-locale
summary parser recognises the shown iputils and BusyBox formats and fails closed on other
formats; confirm utilities in the exact image before deployment.
