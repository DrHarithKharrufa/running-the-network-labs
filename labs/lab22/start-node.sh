#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in lon-pr-01|lon-pe-01|transit-a|ix-peer|cust-a) node="$1" ;; *) exit 1 ;; esac
mkdir -p /run/frr
for daemon in zebra mgmtd staticd isisd bgpd; do
  [[ ! -e "/run/frr/$daemon.pid" ]] || { echo "Already started" >&2; exit 1; }
done
case "$node" in lon-*)
  cp /lab/vrps.json /run/frr/vrps.json
  python3 -u /lab/rtr-fixture.py /run/frr/vrps.json > /run/frr/rtr.log 2>&1 &
  echo "$!" > /run/frr/rtr.pid
  ;;
esac
for daemon in zebra mgmtd staticd isisd bgpd; do
  extra=()
  if [[ "$daemon" == bgpd && "$node" == lon-* ]]; then extra=(-M rpki); fi
  /usr/lib/frr/"$daemon" -d -u root -g root -P 0 --log "file:/run/frr/$daemon.log" "${extra[@]}"
  ready=0
  for attempt in {1..100}; do
    if [[ -S "/run/frr/$daemon.vty" ]]; then ready=1; break; fi
    sleep 0.1
  done
  [[ "$ready" == 1 ]] || { echo "$daemon VTY unavailable" >&2; exit 1; }
done
vtysh -f "/lab/configs/$node.conf"
