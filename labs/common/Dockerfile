FROM ubuntu:24.04
RUN printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d && chmod +x /usr/sbin/policy-rc.d \
 && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
 iproute2 iputils-ping iptables tcpdump dnsmasq-base busybox chrony rsyslog \
 keepalived freeradius hostapd wpasupplicant python3-cryptography iperf3 python3 curl dnsutils procps ca-certificates \
 && dpkg-query -W > /netbook-package-versions.txt \
 && rm -rf /var/lib/apt/lists/*
CMD ["sleep", "infinity"]
