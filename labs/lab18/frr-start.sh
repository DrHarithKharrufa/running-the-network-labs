#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in site|core) node="$1" ;; *) echo "usage: frr-start.sh {site|core}"; exit 1 ;; esac
mkdir -p /run/frr
for daemon in zebra mgmtd staticd bfdd; do
  if [[ -e "/run/frr/$daemon.pid" ]]; then echo "FRR already started" >&2; exit 1; fi
done
for daemon in zebra mgmtd staticd bfdd; do
  /usr/lib/frr/"$daemon" -d -u root -g root -P 0 --log "file:/run/frr/$daemon.log"
done
vtysh -f "/lab/bfd-$node.conf"
vtysh -c 'show bfd peers json'
