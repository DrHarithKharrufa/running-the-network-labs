#!/usr/bin/env bash
set -euo pipefail
for n in r1 r2 r3 rp; do docker exec "clab-lab24-$n" bash /lab/start-node.sh "$n"; done
