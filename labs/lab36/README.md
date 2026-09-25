# Lab 36 — the Anvil underlay

Two parts, separated by what each can actually establish. Read the difference
before you read the results: one reads a file, the other runs routers.

| | What it does | What it proves |
|---|---|---|
| 36.1 `ecmp_check.py` | Parses a Containerlab topology and counts, per leaf pair, the spines both are wired to | How many paths the **cabling** permits |
| 36.2 `underlay_lab.py` | Builds six Linux network namespaces, runs FRR on each, forms real eBGP sessions and reads back BGP and kernel state | How BGP and Linux forwarding **actually behaved**, on this host, on this run |

Neither runs Containerlab, a commercial NOS or an ASIC. Neither measures
throughput.

## Lab 36.1 — read the topology

```bash
python3 ecmp_check.py                      # defaults to ../topologies/anvil.clab.yml
python3 ecmp_check.py --multipath 2        # compare against a different maximum-paths
python3 ecmp_check.py other.clab.yml --json
```

Against the shipped topology it reports two spines, four leaves, twelve links
read, and two candidate paths for each of the six leaf pairs. Exit status is 0
when every leaf pair has one candidate path per spine and `--multipath` does not
cap them, and 1 otherwise.

**Why this version exists.** The previous script built its own full mesh in a
list comprehension and then counted that mesh. It reported a perfect fabric
regardless of what the topology file said, which is to say it proved a property
of its own source code. This one parses the file. Copy the topology, delete one
leaf-spine link, and run it again:

```
    anv-leaf-01 <-> anv-leaf-03: 1 candidate path(s) via anv-spine-01   <-- fewer than the spine count
Cabling gaps found in the file:
  - anv-leaf-03 is not wired to anv-spine-02
```

`test_ecmp_check.py` holds 38 checks, including that exact case, malformed
endpoints, unknown nodes and reused interfaces. It explicitly forces the
fallback path as well as using the available parser. The fallback accepts
the shipped inline node mappings and double-quoted endpoint lists; it rejects
unsupported syntax instead of silently omitting it. Install PyYAML for other
YAML layouts. Neither parser validates the full Containerlab schema or a real
port map. An unwired leaf must not report a complete fabric.

```bash
python3 test_ecmp_check.py     # 22/22, exit 0
```

**A candidate path count is not a forwarding outcome.** Between the cabling and
a packet sit session establishment, import and export policy, next-hop
resolution, the multipath configuration, AS-path comparison, FIB capacity and
the hash that picks a member for each flow. Lab 36.2 tests several of those.

## Lab 36.2 — run the underlay

Needs root, `iproute2` and FRR (`zebra`, `bgpd`, `vtysh`).

```bash
sudo python3 underlay_lab.py
```

It builds two spines and four leaves as namespaces, wires a complete
leaf-spine mesh of veth pairs, starts one FRR instance per node and asserts:

- **A — shared spine AS, unique leaf ASNs, no `allowas-in`, no
  `multipath-relax`.** Sessions Established; leaf-02 receives leaf-01's loopback
  with AS-path `4200000000 4200000101`; two ECMP next-hops installed; loopback
  ping succeeds; all 12 directed leaf pairs has two next-hops; the word
  `allowas-in` appears nowhere in the running configuration.
- **B — unique ASN per spine, no `multipath-relax`.** Two received paths with
  *different* AS-paths, and only **one** next-hop installed.
- **C — the same, with `multipath-relax`.** Two next-hops again.
- **D — two leaves sharing an ASN.** Without `allowas-in`, leaf-02 receives
  **zero** paths for leaf-01's loopback. With `allowas-in 1`, it receives them,
  and the accepted AS-path does contain its own ASN. This is where the knob
  belongs.
- **E — no route policy.** Sessions reach Established and carry **no** prefixes;
  the summary marks the neighbour `(Policy)`. The harness explicitly enables `bgp ebgp-requires-policy` for
  RFC 8212 behaviour; the platform defaults profile must not be assumed.
- **F — spine failure and recovery.** One spine's links are taken down: the
  route survives on one next-hop and forwarding continues. Brought back up, both
  next-hops return.

19 checks, exit 0 when they all pass. Results are written to
`lab36-results.json` in the working directory, with the kernel and FRR versions
recorded.

### Scope of the fresh run

The revised harness passed **19/19 checks on 24 September 2026 UTC**, using
FRR 10.5.1 and Linux 6.18.33.2-microsoft-standard-WSL2. It reads the actual
Linux FIB and checks all 12 directed leaf pairs. Root processes ran in uniquely
owned network namespaces with a private mount namespace per router; an adapter
loaded the retained FRR binaries, saved configs and logs, and cleaned up only
namespaces it created. This is not a run of the Containerlab file.

An earlier FRR 8.4.4 run on a different host is historical evidence for the
earlier harness. The current run does not replace or extend that evidence.
Both fixtures use numbered IPv4 /31 links. Neither qualifies BGP unnumbered,
IPv6 link-local transport, RFC 8950, an ASIC, or per-flow ECMP hashing.

## The shipped Containerlab inventory

`../topologies/anvil.clab.yml` is an inventory: two spines, four leaves and four
hosts, all SR Linux for the fabric nodes, with **no** startup configuration.
Deploying it gives you six devices, not a fabric. Image, port and schema
qualification are outstanding, and no run of it is recorded anywhere in this
book.

## What to take away

- Equal-cost paths between two leaves are bounded by the spines they are *both*
  wired to. Read that from the topology, not from an assumption.
- `maximum-paths` must be at least that count. `multipath-relax` is needed only
  when the candidate AS-paths differ — with a shared spine AS they do not.
- A shared spine AS does not need `allowas-in`; shared *leaf* ASNs do, bounded.
- An eBGP session with no policy is a session that carries nothing, and it looks
  healthy while doing it.
- Debug the underlay as loopback-to-loopback reachability, on its own, before
  you look at the overlay (§37).

## Instrumentation checks and retained evidence

`../test_frr_harness_audit.py` contains 16 offline tests of invalid/empty CLI,
malformed JSON, wrong peers, FIB filtering, FDB row association and owned cleanup.
Mocks check the test instrumentation; they are not device or forwarding tests.
The qualification record stores the executed source hash and environment adapter.
Use the edition's evidence catalogue to locate that record; future reruns must
record their own environment, source hash, commands, failures and cleanup.
