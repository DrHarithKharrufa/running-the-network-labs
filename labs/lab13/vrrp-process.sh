#!/usr/bin/env bash
set -euo pipefail
action=${1:-}
peer=${2:-}
case "$peer" in r1|r2) ;; *) echo 'Peer must be r1 or r2' >&2; exit 2 ;; esac
node="clab-lab13-vrrp-$peer"
case "$action" in
  start)
    timeout 10s docker exec "$node" install -m 0644 /etc/keepalived/keepalived.conf /run/lab13.conf
    timeout 10s docker exec "$node" keepalived --config-test -f /run/lab13.conf
    timeout 10s docker exec -d "$node" sh -c 'exec keepalived -n -l -G -R -P -f /run/lab13.conf -p /run/lab13.pid -r /run/lab13-vrrp.pid >> /tmp/lab13-keepalived.log 2>&1'
    sleep 1
    timeout 10s docker exec "$node" sh -c 'test -f /run/lab13.pid && kill -0 "$(cat /run/lab13.pid)"'
    ;;
  stop)
    timeout 10s docker exec "$node" sh -c 'test -f /run/lab13.pid && kill -TERM "$(cat /run/lab13.pid)"'
    ;;
  logs) timeout 10s docker exec "$node" cat /tmp/lab13-keepalived.log ;;
  *) echo 'Usage: vrrp-process.sh start|stop|logs r1|r2' >&2; exit 2 ;;
esac
