#!/usr/bin/env bash
# Run only after deploying this book's first.clab.yml on the isolated host.
# Counts are iputils/BusyBox-style C-locale summaries, not arbitrary text.
set -euo pipefail
changed=0
restore() { docker exec clab-first-r2 ip link set dev eth1 up; }
cleanup() {
  rc=$?
  trap - EXIT
  if [ "$changed" -eq 1 ]; then
    if ! restore; then
      printf 'FAIL: could not restore r2 eth1; inspect through console\n' >&2
      rc=1
    fi
  fi
  exit "$rc"
}
trap cleanup EXIT
probe() {
  expected_received=$1
  expected_status=$2
  status=0
  output=$(docker exec -e LC_ALL=C clab-first-r1 ping -I 10.0.0.1 -c 5 -W 1 10.0.0.2 2>&1) || status=$?
  printf '%s\n' "$output"
  if [ "$status" -ne "$expected_status" ]; then
    printf 'FAIL: ping exit %s, expected %s\n' "$status" "$expected_status" >&2
    return 1
  fi
  counts=$(printf '%s\n' "$output" | sed -nE 's/^([0-9]+) packets transmitted, ([0-9]+) (packets )?received,.*$/\1 \2/p')
  if [ "$counts" != "5 $expected_received" ]; then
    printf 'FAIL: expected 5 transmitted and %s received; summary missing or different\n' "$expected_received" >&2
    return 1
  fi
}
docker exec clab-first-r1 ip -br address show dev eth1
docker exec clab-first-r2 ip -br address show dev eth1
probe 5 0
changed=1
docker exec clab-first-r2 ip link set dev eth1 down
probe 0 1
restore
changed=0
probe 5 0
printf 'PASS: 5/5 replies, link-down 0/5 replies, restored 5/5 replies\n'
