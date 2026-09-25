# netlab — the execution harness

Every configuration panel in *Running the Network* that is marked **Executed**
points at a JSON record in `evidence/`. This is the program that produces those
records, and it is here so you can produce them yourself and get the same
answer.

## What it does

```
python3 harness/netlab.py run harness/topologies/ospf-p2p.yml -o evidence/ospf-p2p.json
```

That one command starts a container per node, wires them with veth pairs,
applies the configuration through each node's own CLI, waits for the protocols
to settle, runs the capture commands, writes the record, and tears the lab
down. `up`, `config`, `capture` and `down` are also available separately when
you want to poke at a running lab.

## What a record establishes, and what it does not

A record says: *these commands were accepted, and produced this output, on this
image digest, on this kernel, at this time.* Each capture carries the exact
command, the exact bytes returned, its exit status and a SHA-256 of the output.
Where a capture declares an `expect` pattern, the record says whether it matched.

A record does **not** establish anything about hardware forwarding, about a NOS
that was not run, about behaviour at scale, or about behaviour under load. A
container running a routing daemon is a faithful test of control-plane logic and
an unfaithful test of almost everything else. The book keeps those categories
apart on purpose; please do not collapse them when you quote a result.

## Requirements

A Linux host with Docker running, root (veth pairs and network namespaces need
it), and `pyyaml` if your topology is YAML rather than JSON. `python3
check-environment.py` in the repository root tells you what you are missing.

## Writing a topology

```yaml
name: rtnwb-ospf          # container names are <name>-<node>
converge: 50              # seconds to wait before capturing
nodes:
  r1:
    image: quay.io/frrouting/frr:10.2.1
    daemons: [ospfd]      # flipped to yes in /etc/frr/daemons before start
    pre:                  # plain shell, run in the container before the CLI
      - ip address replace 10.0.0.1/30 dev eth1
    config:               # fed to vtysh, one -c per line
      - configure terminal
      - router ospf
      - ospf router-id 10.255.0.1
links:
  - endpoints: ["r1:eth1", "r2:eth1"]
capture:
  - id: adjacency-is-full
    node: r1
    cmd: show ip ospf neighbor
    expect: "Full/"       # a Python regular expression
  - id: forwarding-works
    node: r1
    cli: shell            # anything other than vtysh runs in the shell
    cmd: ping -c 3 -W 2 -I 10.255.0.1 10.255.0.2
    expect: "0% packet loss"
```

Configuration is applied through the device's CLI, not by writing a config
file, so a line the CLI rejects stops the run. That is deliberate: a book should
not print a command that the parser would not take.

## The worked example

`topologies/ospf-p2p.yml` is the smallest complete unit: two routers, one link,
an IGP adjacency, and a remote loopback proved reachable. Its record is
`evidence/ospf-p2p.json`. Note the fourth capture — the routing table showing a
route is not the same claim as a packet arriving, so the record makes both.
