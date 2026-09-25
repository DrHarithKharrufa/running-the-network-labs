#!/usr/bin/env bash
# Disposable lab07 only. Never flush a shared host's firewall or qdiscs.
set -euo pipefail
R=clab-lab07-rtr
run() { docker exec "$R" "$@"; }
clear_netem() {
  local dev observed
  for dev in eth1 eth2; do
    observed=$(run tc qdisc show dev "$dev") || return $?
    if grep -q '^qdisc netem ' <<<"$observed"; then
      run tc qdisc del dev "$dev" root
    fi
  done
}
restore() {
  clear_netem
  run ip link set eth2 mtu 1500
  local rules
  rules=$(run iptables -S OUTPUT) || return $?
  while grep -Eq -- '--comment "?LAB07-MTU"?( |$)' <<<"$rules"; do
    run iptables -D OUTPUT -p icmp --icmp-type fragmentation-needed -m comment --comment LAB07-MTU -j DROP
    rules=$(run iptables -S OUTPUT) || return $?
  done
}
case "${1:-}" in
  baseline|clear) restore ;;
  latency) restore; run tc qdisc replace dev eth2 root netem delay 80ms ;;
  symmetric) restore; run tc qdisc replace dev eth1 root netem delay 80ms
             run tc qdisc replace dev eth2 root netem delay 80ms ;;
  loss) restore; run tc qdisc replace dev eth2 root netem loss 0.1% ;;
  both) restore; run tc qdisc replace dev eth2 root netem delay 80ms loss 0.1% ;;
  mtu) restore; run ip link set eth2 mtu 1400
       run iptables -A OUTPUT -p icmp --icmp-type fragmentation-needed -m comment --comment LAB07-MTU -j DROP ;;
  *) echo "usage: $0 {baseline|latency|symmetric|loss|both|mtu|clear}" >&2; exit 2 ;;
esac
run tc -s qdisc show dev eth1
run tc -s qdisc show dev eth2
run ip -details link show dev eth2
