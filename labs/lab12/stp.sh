#!/usr/bin/env bash
set -euo pipefail
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
node() { local name=$1; shift; timeout 15s docker exec "clab-lab12-$name" "$@"; }
attr() { node "$1" cat "/sys/class/net/br0/bridge/$2"; }
port() { node "$1" cat "/sys/class/net/$2/brport/state"; }
check_mode() {
  for n in sw1 sw2 sw3; do
    test "$(attr "$n" stp_state)" = 1 || { echo "Expected classic kernel STP on $n" >&2; exit 1; }
  done
}
reachable() { node h1 ping -n -c 1 -W 1 10.0.12.30 >/dev/null; }
settle() {
  for ((i=0;i<55;i++)); do
    if reachable; then return 0; fi
    sleep 1
  done
  echo 'Reachability did not recover within the bounded poll window' >&2
  return 1
}
show() {
  for n in sw1 sw2 sw3; do
    echo "$n bridge=$(attr "$n" bridge_id) root=$(attr "$n" root_id) root_port=$(attr "$n" root_port)"
    node "$n" bridge -d link show
  done
}
baseline() {
  settle
  local root
  root=$(attr sw1 bridge_id)
  for n in sw1 sw2 sw3; do test "$(attr "$n" root_id)" = "$root"; done
  test "$(port sw3 eth1)" = 4
  test "$(port sw3 eth2)" = 3
  node h1 ping -n -c 2 -W 1 10.0.12.20
  show
}
check_mode
case "${1:-show}" in
  show) show ;;
  verify) baseline ;;
  failure-test)
    baseline
    trap 'node sw1 ip link set eth2 up' EXIT
    node sw1 ip link set eth2 down
    if reachable; then echo 'No interruption sampled; inspect the actual path' >&2; exit 1; fi
    start=$SECONDS
    settle
    echo "Alternate-path reachability observed after $((SECONDS-start)) seconds of polling"
    test "$(port sw3 eth1)" = 3
    test "$(attr sw3 root_port)" = 1
    show
    node sw1 ip link set eth2 up
    for ((i=0;i<55;i++)); do
      if test "$(port sw3 eth1)" = 4 && test "$(port sw3 eth2)" = 3 && reachable; then
        trap - EXIT
        baseline
        exit 0
      fi
      sleep 1
    done
    echo 'Preferred tree restoration timed out' >&2; exit 1 ;;
  guard-test)
    baseline
    # The test leaves guard enabled; the source sends only one frame.
    trap 'node sw1 ip link set eth3 down; node sw1 ip link set eth3 up' EXIT
    node sw1 bridge link set dev eth3 guard on
    timeout 15s docker exec -i clab-lab12-h1 python3 - < "$HERE/send-bpdu.py"
    sleep 1
    test "$(port sw1 eth3)" = 0
    if reachable; then echo 'Guard did not isolate the host' >&2; exit 1; fi
    node h2 ping -n -c 2 -W 1 10.0.12.30
    show
    node sw1 ip link set eth3 down
    node sw1 ip link set eth3 up
    settle
    trap - EXIT
    baseline ;;
  *) echo 'Usage: stp.sh show|verify|failure-test|guard-test' >&2; exit 2 ;;
esac
