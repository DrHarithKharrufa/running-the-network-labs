#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
 radius) node=radius; program='exec freeradius -X -d /run/netbook15 -D /usr/share/freeradius';;
 auth) node=auth; program='exec hostapd -dd /run/netbook15/hostapd.conf';;
 valid|wrong-name|expired|policy-reject)
   node=client; program="exec wpa_supplicant -dd -D wired -i eth1 -c /run/netbook15/$1.conf";;
 *) echo 'Usage: bash run.sh radius|auth|valid|wrong-name|expired|policy-reject' >&2; exit 2;;
esac
docker exec -it "clab-netbook15-$node" sh -c '
  umask 077
  mkdir -p /run/netbook15
  cp /lab/generated/* /run/netbook15/
  chmod 600 /run/netbook15/*
  sed -i "s|/lab/generated|/run/netbook15|g" /run/netbook15/*.conf
  exec sh -c "$1"
' sh "$program"
