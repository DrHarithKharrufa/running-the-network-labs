#!/bin/sh
# Container-only startup; do not run on a host or production router.
set -eu
node=${1:?Expected border, customer or neighbour}
case "$node" in border|customer|neighbour) ;; *) exit 2 ;; esac
test -d /lab/configs
test ! -e /run/netbook-lab34-started
cp /lab/configs/daemons /etc/frr/daemons
touch /etc/frr/frr.conf
chown frr:frr /etc/frr/frr.conf
/usr/lib/frr/frrinit.sh start
python3 /lab/load-config.py "/lab/configs/$node.conf"
if [ "$node" = border ]; then
  cp /lab/configs/vrps.json /tmp/vrps.json
  python3 -u /lab/rtr-fixture.py /tmp/vrps.json >/tmp/rtr.log 2>&1 &
  echo $! >/run/netbook-rtr.pid
else
  mkdir -p /tmp/www
  if [ "$node" = customer ]; then echo LEGITIMATE >/tmp/www/index.html
  else echo FORGED-PATH >/tmp/www/index.html; fi
  python3 -m http.server 8080 --bind 203.0.113.200 --directory /tmp/www >/tmp/http.log 2>&1 &
fi
touch /run/netbook-lab34-started
