#!/usr/bin/env bash
set -euo pipefail
for n in lon-p-01 man-p-01 bhm-p-01 lds-p-01; do docker exec "clab-lab27-$n" bash /lab/start-node.sh "$n"; done
