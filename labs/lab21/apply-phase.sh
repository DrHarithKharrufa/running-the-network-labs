#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in mesh|reflectors) phase="$1" ;; *) echo "Choose mesh or reflectors" >&2; exit 1 ;; esac
for node in lon-p-01 man-p-01 lon-pr-01 man-pr-01 lon-pe-01 transit-a transit-b cust-a; do
  case "$node" in transit-a) asn=64496 ;; transit-b) asn=64497 ;; cust-a) asn=64501 ;; *) asn=64500 ;; esac
  current=$(docker exec "clab-lab21-$node" vtysh -c 'show running-config')
  if grep -q '^router bgp ' <<<"$current"; then
    docker exec "clab-lab21-$node" vtysh -c 'configure terminal' -c "no router bgp $asn" -c end
  fi
  docker exec "clab-lab21-$node" vtysh -f "/lab/$phase/$node.conf"
done
