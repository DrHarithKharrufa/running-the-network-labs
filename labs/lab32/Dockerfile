FROM ubuntu:26.04
RUN printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d && chmod +x /usr/sbin/policy-rc.d \
 && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
 freeradius freeradius-utils iproute2 iputils-ping iptables python3 curl procps \
 && dpkg-query -W > /netbook-package-versions.txt \
 && rm -rf /var/lib/apt/lists/*
CMD ["sleep", "infinity"]
