#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in r1|r2|r3|rp) node="$1" ;; *) exit 1 ;; esac
mkdir -p /run/frr
for d in zebra mgmtd staticd ospfd pimd; do
  [[ ! -e "/run/frr/$d.pid" ]] || { echo 'Already started' >&2; exit 1; }
  /usr/lib/frr/"$d" -d -u root -g root -P 0 --log "file:/run/frr/$d.log"
  ready=0
  for attempt in {1..100}; do
    if [[ -S "/run/frr/$d.vty" ]]; then ready=1; break; fi
    sleep 0.1
  done
  [[ "$ready" == 1 ]] || { echo "$d VTY unavailable" >&2; exit 1; }
done
vtysh -f "/lab/configs/$node.conf"
