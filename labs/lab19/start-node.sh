#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in abr1|abr2|core|r-a1|r-b1) node="$1" ;; *) exit 1 ;; esac
mkdir -p /run/frr
for daemon in zebra mgmtd staticd ospfd; do
  if [[ -e "/run/frr/$daemon.pid" ]]; then echo "FRR already started" >&2; exit 1; fi
done
for daemon in zebra mgmtd staticd ospfd; do
  /usr/lib/frr/"$daemon" -d -u root -g root -P 0 --log "file:/run/frr/$daemon.log"
done
vtysh -f "/lab/configs/$node.conf"
