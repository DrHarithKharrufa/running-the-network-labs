# Running the Network — labs and companion code

The working code for *Running the Network*, an engineer's guide to enterprise and
service provider networks. Every lab the book refers to lives here: **84
laboratory exercises, 252 Python programs, 35 Containerlab topologies and 114
device configuration files**, plus five shared directories (`common`, `gns3`,
`reference-designs`, `standards`, `topologies`) that the exercises draw on.

Those figures come from `tools/count.py`, not from counting by hand. An earlier
version of this page said "89 lab directories" because it counted the five
shared directories as labs.

The book teaches the reasoning. These labs are where you test whether the
reasoning holds. They are not decoration, and several of them exist specifically
to show a plausible answer being wrong.

## Start here, in ten minutes

You need a Linux shell. macOS and Windows can drive a Linux lab host, but their
local commands are not Linux commands — the book is explicit about that, and so
are these labs.

```bash
git clone https://github.com/DrHarithKharrufa/running-the-network-labs.git
cd running-the-network-labs
python3 check-environment.py
```

`check-environment.py` tells you which labs you can run right now and which need
something installed. It changes nothing on your machine.

Then open [`INDEX.md`](INDEX.md), find your chapter, and run its lab.

## What kind of lab is which

| Kind | Count | What you need |
|---|---|---|
| **Python only** — arithmetic, models, policy simulations | most of the 89 | Python 3.10 or newer. Nothing else |
| **Containerlab topologies** — real routing daemons on real veth links | 29 | Docker and Containerlab on Linux |
| **Device configuration sets** | 106 files | Reading material, or your own equipment |
| **Shell** — namespaces, nftables, tc, capture | 43 scripts | Linux, usually root |

Start with the Python labs. They need nothing, they run in seconds, and several of
them carry the book's sharper results.

## Run the tests

Every lab that ships a model ships tests for it.

```bash
python3 -m unittest discover -s labs/lab64 -v      # one lab
python3 run-all-tests.py                            # all of them
```

All 104 test programs pass on Python 3.11 and 3.12 on Linux. If one fails on your
machine, that is worth an issue — see below.

Be precise about what that means: these tests exercise each lab's **model and
its checker**, including feeding the checker deliberately wrong input to prove
it refuses to print a pass. They do not, by themselves, deploy the Containerlab
topologies. Deploying a topology is a separate act with its own record — see
below.

## Executed evidence

```bash
python3 harness/netlab.py run harness/topologies/ospf-p2p.yml -o evidence/ospf-p2p.json
```

`harness/netlab.py` starts a container per node, wires them with veth pairs,
configures each device through its own CLI, waits for the protocols to settle,
and records exactly what the devices said: the command, the bytes returned, the
exit status, a SHA-256 of the output, and the image digest and kernel it ran on.
Where a capture declares an expectation, the record says whether it matched.

Records live in [`evidence/`](evidence/). A record establishes that these
commands were accepted and produced this output on this image at this time. It
establishes nothing about hardware forwarding, about a NOS that was not run, or
about scale. [`harness/README.md`](harness/README.md) has the detail.

## What these labs do and do not establish

Taking this seriously is the point of the book, so it applies here too.

**They do** compute, enumerate and simulate. They run real routing daemons under
Containerlab, real Linux namespaces, real nftables rulesets and real
cryptography. Where a lab quotes a figure, the code that produced it is in the
same directory.

**They do not** qualify any vendor platform. No commercial network operating
system is executed here and none is included. No hardware is involved anywhere.
A lab that models a vendor's behaviour models it — the configuration files are
reading material and starting points, not release-qualified templates. Test
everything in your own lab before it touches a live network.

Several labs are deliberately instructive about their own limits: `lab64`
computes what a successful probe and a quiet interval actually prove, `lab53`
holds a fail-open check beside a sound one, and `lab62` was repaired after it was
found assuming its own conclusion. Each of those keeps a `--demo-original` mode
that runs the flawed version and explains the defect.

## Errata and corrections

If you find an error — in a lab or in the book — please
[open an issue](https://github.com/DrHarithKharrufa/running-the-network-labs/issues).
Include the chapter or lab, what you ran, what you expected and what happened.

Confirmed book errata are collected in [`ERRATA.md`](ERRATA.md).

Corrections are welcome as pull requests. A fix that comes with a failing test
first is the easiest kind to accept.

## Licence

The code, configurations and lab material in this repository are released under
the **MIT Licence** — see [`LICENSE`](LICENSE). Use them at work, adapt them,
teach from them.

The text of *Running the Network* is copyright and is not covered by that
licence. Vendor names, command syntax and product names belong to their
respective owners and appear for identification and instruction only.

## The book

*Running the Network* — 91 chapters, from a first look at a packet to the
decisions a CTO signs off. Paperback and digital.
