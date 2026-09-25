#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in lon-p-01|man-p-01|bhm-p-01|lds-p-01|lds-p-02) node="$1" ;; *) exit 1 ;; esac
mkdir -p /run/frr
for daemon in zebra mgmtd isisd; do
  if [[ -e "/run/frr/$daemon.pid" ]]; then echo "FRR already started" >&2; exit 1; fi
done
for daemon in zebra mgmtd isisd; do
  /usr/lib/frr/"$daemon" -d -u root -g root -P 0 --log "file:/run/frr/$daemon.log"
done
for daemon in zebra mgmtd isisd; do
  ready=0
  for attempt in {1..100}; do
    if [[ -S "/run/frr/$daemon.vty" ]]; then ready=1; break; fi
    sleep 0.1
  done
  [[ "$ready" == 1 ]] || { echo "$daemon VTY unavailable" >&2; exit 1; }
done
output=$(vtysh -f "/lab/configs/$node.conf" 2>&1) || { echo "$output" >&2; exit 1; }
printf '%s\n' "$output"
if grep -Eiq 'failure|unknown command|ambiguous command|incomplete command|error' <<<"$output"; then
  echo "Inspect configuration load output before proceeding" >&2; exit 1
fi
