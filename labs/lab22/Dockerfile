FROM netbook-frr:10.5.1
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends frr-rpki-rtrlib=10.5.1-1ubuntu4.1 \
 && dpkg-query -W > /netbook-package-versions.txt \
 && rm -rf /var/lib/apt/lists/*
CMD ["sleep", "infinity"]
