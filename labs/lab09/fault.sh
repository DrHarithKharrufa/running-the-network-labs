#!/usr/bin/env bash
set -euo pipefail
R=clab-lab09-fw
rule=(-i eth2 -o eth1 -s 203.0.113.20 -d 10.10.0.0/22 -p tcp --sport 80 -m conntrack --ctstate ESTABLISHED -m comment --comment LAB09-RETURN-FAULT -j DROP)
action=${1:-}
case "$action" in block|restore) ;; *) echo 'usage: bash fault.sh {block|restore}' >&2; exit 2 ;; esac
# An inspection error is not evidence that the rule is absent.
rules=$(docker exec "$R" iptables -S FORWARD)
if [[ "$action" == block ]]; then
  if grep -Eq -- '--comment "?LAB09-RETURN-FAULT"?( |$)' <<<"$rules"; then
    docker exec "$R" iptables -C FORWARD "${rule[@]}"
  else
    docker exec "$R" iptables -I FORWARD 1 "${rule[@]}"
  fi
else
  while grep -Eq -- '--comment "?LAB09-RETURN-FAULT"?( |$)' <<<"$rules"; do
    docker exec "$R" iptables -D FORWARD "${rule[@]}"
    rules=$(docker exec "$R" iptables -S FORWARD)
  done
fi
docker exec "$R" iptables -nvxL FORWARD
