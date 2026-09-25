#!/usr/bin/env bash
set -euo pipefail
for node in sel-a1 sel-a2 sel-b select; do
  docker exec "clab-lab21-selection-$node" bash -c '
    mkdir -p /run/frr
    for daemon in zebra mgmtd staticd bgpd; do
      [[ ! -e "/run/frr/$daemon.pid" ]] || exit 1
      /usr/lib/frr/"$daemon" -d -u root -g root -P 0 --log "file:/run/frr/$daemon.log"
      ready=0
      for attempt in {1..100}; do
        if [[ -S "/run/frr/$daemon.vty" ]]; then ready=1; break; fi
        sleep 0.1
      done
      [[ "$ready" == 1 ]] || exit 1
    done
  '
  docker exec "clab-lab21-selection-$node" vtysh -f "/lab/$node.conf"
done
