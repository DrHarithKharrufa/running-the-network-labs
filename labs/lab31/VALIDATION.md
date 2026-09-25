# Lab 31 validation record

Actual Linux network namespaces: WSL Ubuntu 26.04, Linux 6.18.33.2-microsoft-standard-WSL2, iproute2 6.19.0.
The current `configure-qos.py`, `traffic.py` and topology commands were executed. Helpers were copied byte-for-byte into a private Linux temporary directory for execution. Source hashes, exact runner copies, commands, queue/filter counters and sender/receiver observations are retained in each evidence directory.

Main run `20260917T091741Z` has 22 passing assertions, then a failed generator-rate check in the final idle case. The source requested 0.05 Mbit/s but achieved about 0.0353 Mbit/s, with a 2.385-second maximum observed delay. This host scheduling interruption invalidates that idle sample; the overall run is **not a clean pass**.
Follow-up `20260917T092312Z` tests the remaining idle/burst observations and cleanup in a fresh namespace fixture. It has 7 passing assertions. It does not repeat or replace the main run's earlier mechanism observations, and is not proof of uninterrupted recovery of the original traffic flow.

## Observations

Payload rates use the sender observation duration and include packets drained afterwards. They are not instantaneous wire rates. Delay includes user-space scheduling and socket queues; these short local trials do not establish hardware latency bounds.

| Case | Flow | Actual offered Mbit/s | Received/sent | Delivered payload Mbit/s over sender duration | p95 one-way ms |
|---|---|---:|---:|---:|---:|
| 01-idle-fifo | ef | 0.0507 | 38/38 | 0.0507 | 3.276 |
| 02-busy-fifo | be | 14.9708 | 5846/11244 | 7.7836 | 460.812 |
| 02-busy-fifo | ef | 0.0506 | 19/38 | 0.0253 | 439.197 |
| 03-busy-fq | be | 14.9651 | 5792/11229 | 7.7191 | 224.382 |
| 03-busy-fq | ef | 0.0506 | 38/38 | 0.0506 | 79.425 |
| 04-fourclass | control | 0.9006 | 371/680 | 0.4914 | 421.576 |
| 04-fourclass | ef | 3.6011 | 1478/2719 | 1.9575 | 468.723 |
| 04-fourclass | business | 9.0008 | 3004/6796 | 3.9786 | 168.276 |
| 04-fourclass | be | 9.0008 | 2048/6796 | 2.7124 | 187.123 |
| 05-best-effort-borrowing | be | 11.9893 | 6722/8997 | 8.9576 | 121.869 |
| 06-unbounded-priority | ef | 19.9983 | 6016/15000 | 8.0207 | 457.524 |
| 06-unbounded-priority | be | 0.9999 | 227/750 | 0.3026 | 5626.010 |
| 07-policed-priority | ef | 19.9992 | 1474/15001 | 1.9651 | 2.025 |
| 07-policed-priority | be | 0.9999 | 750/750 | 0.9999 | 0.621 |
| 08-shaper | ef | 7.9997 | 1655/6000 | 2.2066 | 834.235 |
| 09-policer | ef | 7.9993 | 1474/6000 | 1.9652 | 5.241 |
| 10-restored-idle | ef | 0.0507 | 38/38 | 0.0507 | 1.706 |
| 11-short-bursts | be | 0.9999 | 800/800 | 0.9999 | 220.327 |

The unbounded PRIO case received 227 of 750 best-effort packets, with p95 delay about 5.626 seconds. This is severe suppression, not a claim that zero packets ever pass. The policed case received all 750, and its explicit ingress policer counted 13,527 excess EF drops. A 200-packet shaper queue produced substantial delay; the policer discarded excess without that rate-enforcement queue. The shaper's count divided by the sender interval exceeds 2 Mbit/s because burst allowance and post-send drain are included; it does not demonstrate a rate-ceiling violation.

Four-class contention delivered approximately 0.491, 1.958, 3.979 and 2.712 Mbit/s of UDP payload to control, EF, business and default. The generator was close to the allowed 10% tolerance in this case; do not treat the measured allocation as an exact hardware fairness guarantee. Default alone borrowed to about 8.958 Mbit/s. EF packets marked ECT(0) arrived with TOS186, confirming that the DSCP mask did not erase those bits; ECN was disabled in the qdisc, and no congestion feedback was tested.

## Retained earlier failures and execution boundaries

- `20260917T090835Z`: traffic helper exceeded its initial process timeout after the routing check; no QoS measurement accepted.
- `20260917T091335Z`: idle delivery passed, then the sustained-load generator fell outside the 10% offered-rate tolerance. The overall run failed.
- The earlier review-owned QEMU guest was idle but consuming CPU and was shut down before the main run. Host scheduling jitter still occurred; no host package repair, service installation or global network policy change was made.
- `qos-arithmetic-check.json` records 75 separate arithmetic/bit-mask model checks. These are not packet tests.
- Static YAML, shell and Python checks do not execute Docker or Containerlab. Neither the common image build nor Containerlab orchestration was run here.
- Commercial schedulers, MPLS classification, IPv6 QoS, TCP congestion control, ECN feedback, WRED, production scale and failure-state capacity remain unexecuted. The chapter's exact two-priority-level four-class design requires complete platform adapters and hardware acceptance.
- The local namespace helpers clean only their owned `nbk-*` fixture. No production interface is used.
