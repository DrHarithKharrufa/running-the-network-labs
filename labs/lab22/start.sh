#!/usr/bin/env bash
set -euo pipefail
for node in lon-pr-01 lon-pe-01 transit-a ix-peer cust-a; do
  docker exec "clab-lab22-$node" bash /lab/start-node.sh "$node"
done
