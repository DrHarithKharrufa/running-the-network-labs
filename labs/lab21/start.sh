#!/usr/bin/env bash
set -euo pipefail
for node in lon-p-01 man-p-01 lon-pr-01 man-pr-01 lon-pe-01 transit-a transit-b cust-a; do
  docker exec "clab-lab21-$node" bash /lab/start-node.sh "$node"
done
