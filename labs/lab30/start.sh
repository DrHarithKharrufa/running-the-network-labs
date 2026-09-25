#!/usr/bin/env bash
set -euo pipefail
for n in pe1 pe2 pe3; do docker exec "clab-lab30-$n" bash /lab/start-node.sh "$n"; done
