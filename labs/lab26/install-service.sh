#!/usr/bin/env bash
set -euo pipefail
docker exec clab-lab26-lon-pe-01 python3 /lab/service-labels.py left
docker exec clab-lab26-lds-pe-01 python3 /lab/service-labels.py right
