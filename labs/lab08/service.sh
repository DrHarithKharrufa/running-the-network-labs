#!/usr/bin/env bash
# Execute inside the named disposable node. Each service has a distinct PID.
set -euo pipefail
action=${1:-}; name=${2:-}
case "$name" in dns|dhcp|relay|ntp|log) ;; *) echo 'unknown service' >&2; exit 2;; esac
pidfile="/tmp/lab08-$name.pid"
case "$action" in
 start)
   if [[ -s "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
     echo 'service already running' >&2; exit 1
   fi
   case "$name" in
     dns|dhcp|relay)
       dnsmasq --test --conf-file="/lab/$name.conf"
       dnsmasq --no-daemon --conf-file="/lab/$name.conf" --dhcp-leasefile="/tmp/lab08-$name.leases" >"/tmp/lab08-$name.log" 2>&1 & ;;
     ntp) chronyd -d -x -u root -f /lab/chrony.conf > /tmp/lab08-ntp.log 2>&1 & ;;
     log) python3 /lab/collector.py /tmp/lab08-events.jsonl > /tmp/lab08-log.log 2>&1 & ;;
   esac
   echo "$!" > "$pidfile"
   sleep 0.3
   kill -0 "$(cat "$pidfile")"
   ;;
 stop)
   test -s "$pidfile"
   kill -TERM "$(cat "$pidfile")"
   rm -f "$pidfile"
   ;;
 *) echo 'usage: service.sh start|stop dns|dhcp|relay|ntp|log' >&2; exit 2 ;;
esac
