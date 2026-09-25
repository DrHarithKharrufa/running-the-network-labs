#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in pe1|p1|pe2|ce1|ce2|ce3) node="$1";; *) exit 1;; esac
mkdir -p /run/frr
daemons=(zebra mgmtd staticd bgpd)
case "$node" in pe1|p1|pe2) daemons+=(isisd ldpd);; esac
for d in "${daemons[@]}"; do
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
