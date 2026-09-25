#!/bin/sh
set -eu
case "$1" in
 bound|renew)
   test -n "${ip:-}" && test "${subnet:-}" = 255.255.252.0
   case "${lease:-}" in ""|*[!0-9]*) exit 1 ;; esac
   ip address replace "$ip/22" dev "$interface" valid_lft "$lease" preferred_lft "$lease"
   ip route replace 10.10.14.0/24 via 10.10.0.1 dev "$interface"
   printf 'event=%s ip=%s mask=%s router=%s dns=%s lease=%s\n' "$1" "$ip" "$subnet" "${router:-}" "${dns:-}" "$lease"
   ;;
 deconfig) : ;;
esac
