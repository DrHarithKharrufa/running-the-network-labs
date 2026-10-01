# Lab 12 — predict, fail and restore a spanning tree

## 12.1: classic Linux kernel STP

This triangle runs **classic kernel STP**, not RSTP. All three switches have
two interswitch links and a host on eth3. sw1 is priority 4096; sw2 8192;
sw3 32768. Explicit bridge MACs make IDs reproducible. Data-plane addresses
are h1 10.0.12.10/24, h2 .20/24 and h3 .30/24. eth0 is management only.

Build the common image as described in ../common/README.md, then run from
this directory on a disposable Linux Containerlab host:

```sh
sudo containerlab deploy -t stp.clab.yml
bash stp.sh verify
bash stp.sh failure-test
bash stp.sh guard-test
sudo containerlab destroy -t stp.clab.yml --cleanup
```

Keep host control access independent of the lab data plane. The topology
enables STP before attaching and raising data ports. There is no `off` action:
do not start a broadcast loop as a prerequisite for understanding one.
Initial forwarding and classic-STP recovery may take around 30 seconds with
these timers. The host wrapper bounds each Docker call and its polling loop;
an unexpected state stops the test and restores the changed link. Retain the
output and inspect the tree rather than suppressing errors.

Expected stable state: root ID 1000.020000001201 everywhere; sw2 root port 1;
sw3 root port 2; sw3 eth1 blocking. Kernel state numbers are 0 disabled,
1 listening, 2 learning, 3 forwarding, 4 blocking. These are states, not
RSTP role labels. `stp_state` must be 1; the wrapper refuses another mode.

`failure-test` disables sw1 eth2, observes an interruption, waits for sw3's
path through sw2, restores the link and verifies the original blocked port.
Record the probe cadence and timeouts; the printed polling interval is not
an exact outage duration or an SLA measurement. Test restoration separately.

`guard-test` enables the Linux bridge BPDU guard flag on sw1 eth3 and sends
exactly one valid configuration BPDU from h1. The guarded bridge port becomes
disabled; h1 loses remote service while h2-to-h3 remains available. With the
one-frame source stopped, cycling the guarded port restores it through classic
STP. Guard remains enabled. This Linux flag is not proof of any vendor's
error-disable, log or automatic-recovery semantics.

For protocol evidence, use a finite capture on a data port, for example
`timeout 10 tcpdump -n -e -c 20 -i eth1 'ether dst 01:80:c2:00:00:00'`
inside a switch. Record an expected timeout (124) separately from capture
failure. Use packet timestamps alongside root IDs, port states and probes.

## 12.2: RSTP comparison on a supported target

Use a licensed RSTP-capable switch/VM and record its model, exact image,
mode and interface mapping. Recreate the same triangle, host attachments,
priorities and acceptance matrix. Verify that captures actually contain
RSTP and that interswitch links operate with the intended point-to-point
behaviour. Compare link-down, root restart and restoration; examine legacy
interoperation separately. Select edge and guard settings for host ports.
Do not copy Linux `stp_state 1` and call the result RSTP.

The optional open-source mstpd route also needs a supported kernel/userspace
integration. Its 0.2.0 tag was built locally for investigation, but the
available Linux 6.18 namespace path cannot select its userspace STP mode
through the supplied iproute2 6.19 interface. The attempted RSTP run failed
before a protocol assertion. It is not included as a working lab path.
MSTI forwarding is a further integration question, not proved by an RSTP run.

## Recorded scope

On 16 September 2026 the equivalent data-plane commands ran in isolated WSL
Linux 6.18.33.2 namespaces with iproute2 6.19.0: 15 assertions passed for
root selection, blocked/forwarding state, reachability, link failure/restore
and BPDU guard/recovery. Evidence: publication-revision/runtime-evidence/
20260916T204158Z/results.json and its state snapshots. Initial and recovered
forwarding were observed after roughly 30 seconds of polling. This does not
establish Containerlab deployment, image-build success, RSTP or a commercial
NOS result. Those are separate entries in the validation ledger.
