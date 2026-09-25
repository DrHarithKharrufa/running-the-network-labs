#!/usr/bin/env bash
set -euo pipefail
for node in lon-p-01 man-p-01 bhm-p-01 lds-p-01 lds-p-02; do
  docker exec "clab-lab20-$node" bash /lab/start-node.sh "$node"
done
