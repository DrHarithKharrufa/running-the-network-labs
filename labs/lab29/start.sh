#!/usr/bin/env bash
set -euo pipefail
for n in pe1 p1 pe2 ce1 ce2 ce3; do docker exec "clab-lab29-$n" bash /lab/start-node.sh "$n"; done
