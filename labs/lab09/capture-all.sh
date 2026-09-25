#!/usr/bin/env bash
# Finite, filtered captures; failed collectors cannot be reported as success.
set -euo pipefail
DUR="${1:-12}"
[[ "$DUR" =~ ^[0-9]+$ ]] && (( DUR >= 5 && DUR <= 60 )) || { echo 'duration must be 5..60 seconds' >&2; exit 2; }
OUT="${2:-pcap-$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir "$OUT"
declare -a pids=() names=()
cleanup() { local p; for p in "${pids[@]}"; do kill "$p" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM
while read -r name container interface; do
  names+=("$name")
  docker exec "$container" timeout -s INT "$DUR" tcpdump -U -i "$interface" -nn -s 160 -c 500 -w - \
    '(host 203.0.113.20 and tcp port 80) or icmp' >"$OUT/$name.pcap" 2>"$OUT/$name.log" &
  pids+=("$!")
done <<'TAPS'
pc-acc clab-lab09-pc eth1
acc-core clab-lab09-core eth1
core-fw clab-lab09-fw eth1
fw-isp clab-lab09-fw eth2
isp-server clab-lab09-server eth1
TAPS
for name in "${names[@]}"; do
  ready=0
  for attempt in {1..30}; do
    if grep -q 'listening on' "$OUT/$name.log"; then ready=1; break; fi
    sleep 0.1
  done
  (( ready == 1 )) || { echo "capture did not start: $name" >&2; cat "$OUT/$name.log" >&2; exit 1; }
done
docker exec clab-lab09-pc curl --noproxy '*' --interface 10.10.0.42 --connect-timeout 2 --max-time 4 --fail -sS -o /dev/null \
  -w 'http %{http_code} in %{time_total}s\n' http://203.0.113.20/
failed=0
for index in "${!pids[@]}"; do
  status=0; wait "${pids[$index]}" || status=$?
  name="${names[$index]}"
  if [[ "$status" != 0 && "$status" != 124 ]]; then echo "capture failed: $name ($status)" >&2; failed=1; fi
  if [[ $(wc -c <"$OUT/$name.pcap") -le 24 ]]; then echo "empty capture: $name" >&2; failed=1; fi
done
pids=()
(( failed == 0 )) || exit 1
echo "Captures and diagnostics: $OUT"
