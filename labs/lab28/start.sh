#!/usr/bin/env bash
set -euo pipefail
for n in r1 r2 r3 r4; do docker exec "clab-lab28-$n" bash /lab/start-node.sh "$n"; done
