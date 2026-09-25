#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in lon-p-01|man-p-01|lon-pr-01|man-pr-01|lon-pe-01|transit-a|transit-b|cust-a) node="$1" ;; *) exit 1 ;; esac
mkdir -p /run/frr
for daemon in zebra mgmtd staticd isisd bgpd; do
  [[ ! -e "/run/frr/$daemon.pid" ]] || { echo "Already started" >&2; exit 1; }
done
for daemon in zebra mgmtd staticd isisd bgpd; do
  /usr/lib/frr/"$daemon" -d -u root -g root -P 0 --log "file:/run/frr/$daemon.log"
  ready=0
  for attempt in {1..100}; do
    if [[ -S "/run/frr/$daemon.vty" ]]; then ready=1; break; fi
    sleep 0.1
  done
  [[ "$ready" == 1 ]] || { echo "$daemon VTY unavailable" >&2; exit 1; }
done
vtysh -f "/lab/configs/$node.conf"
