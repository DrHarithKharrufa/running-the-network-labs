#!/bin/sh
set -eu
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv4.conf.all.rp_filter=0
sysctl -w net.ipv4.conf.default.rp_filter=0
sysctl -w net.mpls.platform_labels=1048575
sysctl -w net.mpls.conf.eth1.input=1
ip address replace 10.255.0.1/32 dev lo
ip address replace 10.254.0.0/31 dev eth1
ip link set eth1 up
ip link show CUST-A >/dev/null 2>&1 || ip link add CUST-A type vrf table 1001
ip link set CUST-A up
ip link set eth2 master CUST-A
ip link set eth2 up
ip address replace 10.101.0.1/24 dev eth2
ip route replace table 1001 unreachable default metric 4278198272
sysctl -w net.ipv4.conf.eth2.rp_filter=0
ip link show CUST-B >/dev/null 2>&1 || ip link add CUST-B type vrf table 1002
ip link set CUST-B up
ip link set eth3 master CUST-B
ip link set eth3 up
ip address replace 10.102.0.1/24 dev eth3
ip route replace table 1002 unreachable default metric 4278198272
sysctl -w net.ipv4.conf.eth3.rp_filter=0
ip link show CUST-C >/dev/null 2>&1 || ip link add CUST-C type vrf table 1003
ip link set CUST-C up
ip link set eth4 master CUST-C
ip link set eth4 up
ip address replace 10.103.0.1/24 dev eth4
ip route replace table 1003 unreachable default metric 4278198272
sysctl -w net.ipv4.conf.eth4.rp_filter=0
# Reload after kernel VRFs and their attachments exist.
vtysh -b
