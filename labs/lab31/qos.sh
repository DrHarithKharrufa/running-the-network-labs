#!/usr/bin/env bash
# Run from Lab31 after deployment. Only changes the disposable router.
set -euo pipefail
docker exec clab-lab31-rtr python3 /lab/configure-qos.py "${1:?mode required}"
