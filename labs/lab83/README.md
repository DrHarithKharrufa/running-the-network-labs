# Lab 83.1 — Distance, transactions and recovery budgets

```console
python latency_feasibility.py
python -m unittest discover -v
```

Standard-library Python; 17 local arithmetic and boundary tests. All workloads,
route lengths, extra delays, replication rates and recovery times are hypothetical.
There is no network, database, cloud or DR execution. `measured_RTO` is `NOT_RUN`.

The speed parameter defaults to an approximate 200,000 km/s in fibre. Enter the
actual assumed one-way fibre route length, not automatically the geographical
separation; the model assumes equal lengths in both directions. Add RTT overhead
separately. For 800 km of ideal fibre the propagation RTT is 8 ms. A hypothetical
1,100-km route plus 3 ms of other RTT delay gives 14 ms. No universal 1.5× route
factor or two-millisecond synchronous replication limit is used.

Workload latency = sequential WAN round trips × assumed RTT + local time. At
14 ms RTT and 8 ms local time, one/two/three rounds give 22/36/50 ms against a
40-ms deterministic budget. An intercontinental example (8,000-km route, 20 ms
extra RTT, one round and 10 ms local work) gives 110 ms against a 200-ms budget.
Those are feasibility arithmetic, not p95/p99 results, consensus validation,
throughput capacity or evidence that a particular database can use that round count.

The asynchronous example assumes an initially current replica, constant 8 MiB/s
acknowledged writes and effective durable FIFO apply of 12 MiB/s after recovery.
A 240-second transfer outage leaves 1,920 MiB absent at the replica, spanning four
minutes of writes. If the source survives and writes continue, catch-up takes
1,920/(12-8) = 480 seconds. If the source is destroyed at outage end, that unreplicated
data is not available to catch up: it is the model's loss exposure. A 360-second
outage leaves six minutes of writes absent, exceeding the five-minute loss-window
budget. Real RPO depends on commit records, durable apply and the actual failure;
volume alone does not establish it. With effective apply <= write rate, a positive
backlog never clears in this model. Retained logs also need enough storage.

The sequential recovery budget is detect 60 s, fence 120 s, promote/recover 300 s,
steer 180 s, validate 300 s: 960 s (16 minutes), leaving 840 s (14 minutes) against
30 minutes. Each is an assumed allowance. Fencing must actually succeed before a
second writer starts; failed fencing stops promotion. Approval, access recovery,
DNS/application caching, restore and validation may exceed these allowances. A real
test must record those failures and timestamps instead of reporting the sum as RTO.

## Extend it

Replace assumptions with a documented workload transaction/quorum model and a
measured path distribution. Test the full application at load: adding separately
measured p95 components does not normally produce end-to-end p95. Record required
write behaviour when quorum or the replication-loss budget is unavailable. Test
writer fencing, data integrity, backups, client steering, recovery and controlled
failback with the application owner.

The original incoming script is preserved as `latency_feasibility_original.py.txt`.
`python latency_feasibility.py --demo-original` prints its historically flawed
universal thresholds behind an explicit warning; it is not current design guidance.
