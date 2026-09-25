#!/bin/sh
set -eu
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv4.conf.all.rp_filter=0
sysctl -w net.ipv4.conf.default.rp_filter=0
sysctl -w net.mpls.platform_labels=1048575
sysctl -w net.mpls.conf.eth1.input=1
ip address replace 10.255.0.2/32 dev lo
ip address replace 10.254.0.1/31 dev eth1
ip link set eth1 up
ip link show SERVICES >/dev/null 2>&1 || ip link add SERVICES type vrf table 9000
ip link set SERVICES up
ip link set eth2 master SERVICES
ip link set eth2 up
ip address replace 10.109.0.1/24 dev eth2
ip route replace table 9000 unreachable default metric 4278198272
sysctl -w net.ipv4.conf.eth2.rp_filter=0
# Reload after kernel VRFs and their attachments exist.
vtysh -b
