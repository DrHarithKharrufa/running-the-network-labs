# Lab 39 — programmable data planes

Two parts, and the gap between them is the lesson.

| | What it does | What it establishes |
|---|---|---|
| 39.1 `dropcost.py` | Arithmetic on constants **you** supply, comparing a worst-case linear walk against one assumed constant-time lookup | How a linear term and a constant term diverge — nothing else |
| 39.2 `xdp_lab.py` | Compiles a real XDP program, loads it through libbpf, watches the kernel verifier accept one and reject another, attaches it and drops real packets | What the kernel actually did, on this host, on this run |

Neither measures throughput. Neither reports a packets-per-second figure. That
is deliberate, and the reason is below.

## Lab 39.1 — the model, labelled as one

```bash
python3 dropcost.py
python3 dropcost.py --rule-ns 8 --stack-ns 450 --lookup-ns 35   # your figures
python3 test_dropcost.py      # 28 checks, exit 0
```

**Why this version exists.** The previous script shipped invented nanosecond
constants, multiplied them out to a *"30015x speedup"* and *"25 million
drops/sec"*, and offered those as the reason DDoS scrubbing lives in XDP. Model
arithmetic is not a measurement. The constants are now declared placeholders, the
output prints the **early-match** case beside the worst case, and it prints no
rate at all — `test_dropcost.py` asserts that no rate string appears.

**What the model leaves out**, all of which moves the answer:

- **Early matches.** A chain whose first rule matches costs one rule, not N. The
  linear column is a worst case by construction, and real traffic is not the
  worst case.
- **Set-based matching.** ipset and nftables sets do not walk linearly. A modern
  nftables ruleset with a set lookup sits much closer to the constant column.
  Comparing XDP against a worst-case linear iptables chain is a straw man.
- **Map type and cache behaviour**, parsing and driver cost, and what both sides
  do under attack load rather than at idle.

## Lab 39.2 — XDP, actually compiled, verified and dropping

Needs root, `clang`, `gcc`, `libbpf-dev` and `iproute2`.

```bash
sudo python3 xdp_lab.py
```

Files: `xdp_drop.c` (bounds-checked dropper), `xdp_unsafe.c` (the same thing
without its bounds check), `loader.c` (a minimal libbpf loader).

- **A — compile.** Both programs compile. **clang does not catch the unsafe
  one**, which is the first thing worth noticing.
- **B — the verifier.** The kernel *rejects* the unbounded program at load time
  and names the offending access:
  `invalid access to packet, off=26 size=4 ... R1 offset is outside of the packet`.
  The bounds-checked version is accepted.
- **C — dropping, counted.** With the peer's address in the blocklist map the
  ping fails and the drop counter rises; with an empty map the ping succeeds and
  nothing is dropped. The counts come out of a BPF map, not from inference.
- **D — modes.** The lab attempts native (driver) and hardware-offload attach and
  records what this interface supports. Mode availability is a property of the
  driver, not of XDP.

### What the verifier proves, and what it does not

It checks, for the kernel you load on, that memory accesses are in bounds, that
control flow terminates, and that the program uses only permitted helpers in a
way appropriate to its hook. It does **not** check that your policy is right. A
program that passes can still drop the wrong traffic. It is also
kernel-dependent: a program one kernel accepts, another may refuse.

### Why no rate is reported

`xdp_lab.py` runs in **generic (SKB) mode on a veth pair**. Generic mode runs
after the kernel has allocated an `skb` — later, and slower, than native driver
mode, which is what people mean when they say XDP is fast. A veth is not a NIC.
Any rate measured here would describe the harness. If a rate matters to your
design, measure it on your hardware, with your program and your traffic, and
publish the conditions with the number.

### The scope of `xdp_drop.c`, stated in the file

Untagged IPv4 source addresses are matched after bounds checks on the Ethernet
and fixed IPv4 base headers. VLAN-tagged frames, IPv6 and ARP pass without a
blocklist lookup. Options and fragments still undergo source matching; their
source address remains in the base header. The earlier comments saying they
bypass the lookup were wrong. The executable C body is unchanged.

This is not a full IPv4 validator: version, total length, checksum and complete
option bytes are not checked. A transport-port filter would need IHL-aware
parsing and an explicit fragment policy. Verifier acceptance does not establish
that the policy matches the operator's requirements. No fresh kernel/XDP run
is claimed by this documentation correction.

## What to take away

- A cost model shows a shape. It does not produce a rate, and a rate presented
  without its conditions is not evidence.
- The verifier is a memory-safety and termination proof. Correctness of policy is
  still yours.
- Which XDP mode you got decides the performance. Check it; do not assume.
