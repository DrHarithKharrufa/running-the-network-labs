#!/bin/sh
# Minimal, explicit teaching client hook. It does not edit host resolv.conf.
set -eu
case "$1" in
  bound|renew)
    test -n "${ipv6:-}" || { echo 'No DHCPv6 IA_NA address in hook environment' >&2; exit 1; }
    case "${lease:-}" in ""|*[!0-9]*) echo "Invalid lease lifetime" >&2; exit 1 ;; esac
    ip -6 address replace "$ipv6/128" dev "$interface" valid_lft "$lease" preferred_lft "$lease"
    printf 'event=%s interface=%s address=%s lease=%s dns=%s\n' "$1" "$interface" "$ipv6" "${lease:-unknown}" "${dns:-not-supplied}"
    ;;
  deconfig) : ;;
esac
