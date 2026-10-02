# Lab 53 — Hardening the device and the control plane

Three labs. The first is a questionnaire and says so; the second and third run
on real Linux kernels and measure what the chapter's advice actually does.

| Lab | What it is | What it needs |
|-----|------------|---------------|
| 53.1 `harden_check.py` | a hardening questionnaire, and a demonstration of how the shipped version failed open | python3 only |
| 53.2 `urpf_modes.py` | strict vs loose uRPF vs a prefix filter, measured on namespaces | root, iproute2, nftables |
| 53.3 `iacl_exceptions.py` | what a blanket infrastructure ACL breaks, measured | root, iproute2, nftables |

---

## Lab 53.1 — the questionnaire, and the fail-open it replaces

```bash
python3 harden_check.py
python3 harden_check.py --demo-fail-open
python3 test_harden_check.py
```

**This is not a compliance scanner.** There is no collector, no parser and no
session to a device. It reads a dictionary somebody typed and sorts it into
three verdicts — `FINDING`, `UNSTATED`, `CLAIMED` — and there is deliberately no
`PASS`. That restraint is the lesson. It is easy to write a tool like this and
describe it as checking "a device's live configuration" — the output looks
identical, and nobody notices until an audit rests on it. A checker that never
touched a device cannot tell you a device is compliant; it can only tell you
what someone wrote down.

There is a worse failure available than the wrong label, and `--demo-fail-open`
shows it. Consider two checks written as blocklists:

```python
if dev.get("urpf_edge") == "loose":            # -> MEDIUM
if dev.get("bgp_authentication") == "md5":     # -> LOW
```

Each recognised exactly one value, and that value was the *middling* one. Set
`urpf_edge` to `"disabled"` and `bgp_authentication` to `"none"` — make the
device strictly worse — and both checks went silent. The described device
produced **seven** findings; the same device with uRPF off and BGP
unauthenticated produced **five**. The report got shorter because the device got
worse.

That is worth stopping on, because it is not the ordinary bug. The script did
not crash and did not refuse to run; it produced a *shorter, calmer* report from
a correct input. A blocklist's silence means "I did not recognise that string",
and it is read as "nothing wrong here".

The rebuilt version is an allowlist throughout: every control names the answers
it recognises, and anything else — an unknown string, a typo, `None`, a missing
key — comes out as `UNSTATED`. There is no code path that returns nothing.

It also fixes three things the chapter overstated:

- **Baselines are selected by role and versioned.** A PE, an access edge, a
  route reflector and an out-of-band management host do not have the same
  correct answers; strict uRPF belongs on one of them and is an outage on
  another. A control outside a role's baseline is reported `NOT APPLICABLE`,
  which is not a pass.
- **A platform default is not an absent control.** `copp: none` on IOS-XR, where
  LPTS polices punted traffic without an explicit policy, is a different
  statement from the same answer on a platform with no default. The record
  carries the platform and the note says which case it is.
- **A description is not evidence.** Every record carries `record_source`
  (`asserted`, `config` or `observed`) and a date, and every verdict prints what
  would actually settle it. Run it a month from now and watch the staleness note
  appear on its own: a device is hardened *as of* the last check, and this one
  ages in front of you.

---

## Lab 53.2 — source validation, measured

```bash
sudo python3 urpf_modes.py
sudo python3 test_urpf_modes.py
```

Three namespaces, a real forwarding router, real UDP datagrams, and the kernel's
own `rp_filter` — mode 1 is RFC 3704 strict, mode 2 is RFC 3704 loose. The
customer is allocated `10.20.0.0/24`, the router's best route to it points out
link A, and the customer also sends traffic in on link B.

Four traffic classes against four postures. This is the measured result:

```
posture                     legit symmetric   legit ASYMMETRIC   SPOOFED but routed   unrouted
no validation               delivered         delivered          delivered            delivered
uRPF strict                 delivered         dropped            dropped              dropped
uRPF loose                  delivered         delivered          delivered            dropped
per-customer prefix filter  delivered         delivered          dropped              dropped
```

Two rows deserve attention.

**Strict uRPF dropped the customer's own address** when it arrived on the link
the best route does not point at. Strict mode consults the best route, not the
set of paths that would be feasible (RFC 8704 §3). That is why §53.5's "strict
at the single-homed edge" carries the qualifier it does — and why deploying it
where the reverse path is not symmetric is an outage, not a tightening.

**Loose uRPF delivered a spoofed source.** `10.99.0.5` is not the customer's
address; the router simply has a route for it, which is all loose mode asks.
The chapter said loose uRPF "still kills obviously spoofed sources" — measured,
it does not kill a spoofed source that has a route, and on the Internet nearly
every address has a route. **Reachability is not authorisation.**

Only the fourth posture gets all four classes right, and it is the only one that
was told which prefixes the customer is entitled to use.

The script will not fake a result. It refuses to run without root, iproute2 and
nftables; it counts arrivals at the router's ingress so a non-delivery can be
told from a packet that never left; and it runs the no-validation case first and
aborts if anything fails to arrive, because a "drop" measured on a broken
topology is a fabricated result.

---

## Lab 53.3 — what the one-line infrastructure ACL breaks

```bash
sudo python3 iacl_exceptions.py
sudo python3 test_iacl_exceptions.py
```

Three namespaces and a forwarding hop with a 1400-byte MTU. Infrastructure space
is `10.53.0.0/24` (loopbacks) and `10.0.4.0/22` (links). The lab applies §53.4's
rule exactly as the chapter writes it — deny anything from outside destined to
infrastructure space — and then applies the same rule with the exceptions a
working network needs.

```
posture                             authorised peer   unauthorised source   PMTUD
blanket deny to infrastructure      blocked           blocked               silent black hole
deny with the required exceptions   allowed           blocked               PMTU learned
```

The one-line rule does block the attacker. It also blocks two things nobody
meant to block:

- **The external BGP session**, because an eBGP session terminates *on* an
  infrastructure address — the link `/30` or `/31`. The rule that makes the core
  unaddressable from outside makes the peering unaddressable too.
- **Path MTU discovery for the router's own traffic.** When the router sources a
  session from its loopback across a narrower path, the ICMP
  fragmentation-needed comes *back* to that loopback: an infrastructure
  destination, from outside. Drop it and there is no error and no log — just
  large packets vanishing. The lab reads the kernel's route cache to prove it:
  after the blanket rule the cache carries no MTU at all, and after the
  exceptions it carries `mtu 1400`.

Both are outages, not security. What makes the rule deployable is the exception
list in front of it — authorised peers to the routing ports, ICMP
fragmentation-needed and time-exceeded — and the deny line stays last. It did
not get weaker; it got the permits it always needed.

Add IPv6: ICMPv6 carries neighbour discovery as well as packet-too-big, and an
ACL that filters ICMPv6 the way this one filters ICMP will break the link
itself.

---

## What to take away

- Ask two questions of any checking script, not one: can it fail, and can it
  fail **open**? A check that goes quiet on an answer it does not recognise is
  worse than no check, because its silence gets quoted.
- A script that reads a dictionary is reading a description. It can sort that
  description and say what evidence would settle each claim. It cannot certify a
  control, and it should not print a word that suggests it has.
- Loose uRPF asks whether a source is *reachable*. A per-customer prefix filter
  can enforce the customer's declared allocation. Feasible-path uRPF uses
  additional routing information to tolerate legitimate asymmetric paths;
  its protection depends on the correctness and admission policy of that
  information. It is not an independent ownership check.
- The infrastructure ACL is right and its one-line form is an outage. The
  exception list is the part worth writing down.
- These labs run on Linux namespaces. `rp_filter` and nftables are not a Cisco
  or Nokia forwarding plane, and the drop semantics, counters and feasible-path
  support differ on a commercial NOS. What transfers is the shape of the result,
  not the syntax — verify each on the platform you actually run.

## Running everything

```bash
python3 test_harden_check.py        # no privilege needed
sudo python3 test_urpf_modes.py     # builds real namespaces
sudo python3 test_iacl_exceptions.py
```

Without root the two execution tests report their privileged half as **skipped**
and say so. They do not simulate it, and a skipped half is not a pass.
