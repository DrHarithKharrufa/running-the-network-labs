# Recorded validation, 16 September 2026

These are actual Linux network-namespace runs on Ubuntu 26.04 under WSL2.
They are not Containerlab/image, commercial NOS or hardware acceptance tests.
The shared image Dockerfile has not been built here. Its Ubuntu 24.04 package
versions can differ from the separately extracted Ubuntu 26.04 tools used here.

| Lab | Measured scope | Passing assertions | Still required |
|---|---|---:|---|
| 03 | Direct link and routed return-path baseline, fault and recovery | 6 | Containerlab/FRR image and verify.sh Docker adapter execution |
| 05 | 1500-byte boundary, 1501-byte DF rejection, 9000-byte restored path and reset | 5 | Containerlab image; vendor counters and forwarding hardware |
| 07 | One-direction 80 ms, symmetric 160 ms RTT changes and restoration | 7 | Docker adapter; throughput, stochastic loss, window scaling and PMTU-blackhole cases |
| 09 | HTTP, five captures, observed SNAT and TTL decrement, existing/new flow blocking and recovery | 13 | Containerlab deployment and Docker capture/fault wrappers; commercial firewall semantics |
| 06 | SLAAC, DAD, finite DHCPv6 lease, RA defaults, /127, received RDNSS and rogue RA arrival | 14 | Container image; resolver integration, renewal/expiry and vendor RA Guard |
| 08 | Fresh DHCP failure/recovery through relay, captured giaddr, finite lease, independent DNS/NTP/log faults and recovery | 16 | Container image/start script; renewal/expiry, option 82, vendor relay and authenticated time |

Full records, commands, failures, captures and daemon logs are in
`../../runtime-evidence/` relative to this lab directory. From the checkpoint
root, selected results and hashes are indexed in
`project/work/publication/resumed/runtime-summary.json`.

The 61 assertions include readiness and evidence checks; this is not a coverage
percentage or 61 independent end-user scenarios. The Lab 03/05/07 components
passed before a later Lab 09 capture-account error in that run. The corrected
Lab 09 run passed separately. Earlier failed runs remain in the evidence.

Namespace execution uses the topology's addressing/link commands and the same
daemon configuration files, with paths adjusted for the absence of container
bind mounts. Lab 07's iperf3 startup is omitted in the RTT-only run. Container
startup, orchestration and Docker wrapper execution are separate pending work.

Primary references consulted for this pass:
- [dnsmasq maintained manual](https://thekelleys.org.uk/dnsmasq/docs/dnsmasq-man.html)
- [chronyd 4.8](https://chrony-project.org/doc/4.8/chronyd.html)
- [chrony.conf 4.8](https://chrony-project.org/doc/4.8/chrony.conf.html)
- [Linux IP sysctls](https://docs.kernel.org/networking/ip-sysctl.html)
- [DHCPv6, RFC 9915](https://datatracker.ietf.org/doc/rfc9915/)
