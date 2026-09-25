#!/usr/bin/env bash
set -euo pipefail
for node in abr1 abr2 core r-a1 r-b1; do
  docker exec "clab-lab19-$node" bash /lab/start-node.sh "$node"
done
