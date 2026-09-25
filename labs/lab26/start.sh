#!/usr/bin/env bash
set -euo pipefail
for n in lon-pe-01 lon-p-01 bhm-p-01 lds-pe-01 alt-p-01; do
  docker exec "clab-lab26-$n" bash /lab/start-node.sh "$n"
done
