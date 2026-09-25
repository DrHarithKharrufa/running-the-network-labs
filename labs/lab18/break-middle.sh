#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  break) docker exec clab-lab18-provider tc qdisc replace dev eth1 root netem loss 100%
         docker exec clab-lab18-provider tc qdisc replace dev eth2 root netem loss 100% ;;
  fix) docker exec clab-lab18-provider tc qdisc del dev eth1 root
       docker exec clab-lab18-provider tc qdisc del dev eth2 root ;;
  *) echo "usage: $0 {break|fix}"; exit 1 ;;
esac
