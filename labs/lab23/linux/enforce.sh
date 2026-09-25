#!/usr/bin/env bash
set -euo pipefail
# Run only in the disposable PE namespace. Never on the host firewall.
for i in 1 2 3; do
  iptables -t raw -A PREROUTING -i "eth$i" ! -s "10.$((100+i)).0.0/24" -j DROP
done
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
for i in 1 2 3; do
  iptables -A FORWARD -s "10.$((100+i)).0.0/24" -d 10.109.0.10 -p udp -m multiport --dports 53,123 -j ACCEPT
  iptables -A FORWARD -s "10.$((100+i)).0.0/24" -d 10.109.0.10 -p tcp --dport 53 -j ACCEPT
done
iptables -A FORWARD -j DROP
