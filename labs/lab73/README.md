# Lab 73: evidence-aware pre-change validation

## What actually runs

Python 3.12 standard-library policy checks and adapter contract tests. Run:

```
python -m unittest discover -v
python pipeline.py
python pipeline.py --current fixtures/good.cfg --candidate fixtures/good.cfg
python pipeline.py --demo-original
python batfish_probe.py
```

The test suite has 24 tests. The two pipeline commands exit **1**, intentionally:
both local policy checks pass for the synthetic fixture, but Batfish, NOS
integration, service canary and deployment remain **NOT_RUN**. There is no
promotion. The original demonstration is retained byte-for-byte in
`original_pipeline.py`; its printed Batfish/canary/deployment successes were not
external actions. `--demo-original` labels that limitation before running it.

## Policy scope and inputs

`policy.py` evaluates only the documented `iosxe-vty-and-owned-interfaces-v1`
teaching profile: explicit VTY 0–15 transport, descriptions on the two owned
interfaces, and Loopback0's /32 allocation inside 10.255.0.0/16. This is a bounded
parser for normalised, indented IOS XE running-configuration stanzas, **not** a
complete Cisco parser, command patch interpreter or SSH usability test. The
Catalyst 9300 IOS XE 17.15 documentation is the syntax reference; no device ran.

Supply complete relevant current and post-change state, not just a diff. Caller
provenance and snapshot completeness remain separate requirements. Omitted
VTYs, absent owned interfaces, defaults, banners, ranges, deletion/default forms
and unsupported transport syntax produce UNSUPPORTED (unless a definite
violation already makes the result FAIL). Comments and descriptions cannot
enable Telnet; mixed `ssh telnet` and `all` forms fail. A final explicit command
replaces earlier explicit transport state within a stanza. `none` passes only
the no-Telnet rule; it does not assert that remote login works. Unknown commands
outside these fields are not evaluated and cannot receive a general NOS verdict.

Interface descriptions apply to the owned set, not every physical/logical port.
An ACL string is never used as a reachability oracle: order, direction, attachment,
routes and surrounding policy require a real model or device test. SHA256 values
bind the report to the exact two input texts, not to an approval or deployment.

## Optional Batfish collector — no service run is claimed

`batfish_probe.py` is an optional API adapter. Its session methods and header
constructor were inspected in the official Pybatfish 2026.9.17.3748 wheel. The
adapter is syntax-checked and tested with four local doubles; client imports,
server compatibility, parsing, model traces and forwarding remain **unexecuted**.
The wheel was downloaded for inspection only. The public notebook documentation
has an older displayed version, so establish a compatible client/server pair and
record both versions before using the adapter as integration evidence.

In a disposable environment, install the inspected client with:

```
python -m pip install pybatfish==2026.9.17.3748
```

Prepare a local Batfish service and an existing snapshot using the official
snapshot-format and service documentation. Retain hashes of all configurations,
topology, supplemental and external-routing inputs. This adapter does **not**
upload snapshots, create networks, overwrite snapshots or contact devices.
It queries only `127.0.0.1`, using the client's default service port. Restrict that
service to the local host; analysis data may contain confidential configuration.
Example after replacing every topology-specific value:

```
python batfish_probe.py --run --network lab --snapshot candidate --start "@enter(r1[Ethernet1])" --src 192.0.2.1 --dst 198.51.100.1 --src-port 50000 --dst-port 443 --expected-nodes r1,r2
```

Without `--run`, the adapter reports NOT_RUN and exits 1 without importing the
optional client. With it, it collects file parse status, initialisation issues,
node inventory, server/client versions and one explicit directional TCP trace.
It preserves warnings and empty traces, compares expected/observed node sets,
and always reports REVIEW_REQUIRED (exit 1), never deployment PASS. Errors exit 2.
The 30-second client timeout bounds individual HTTP requests, not the duration
or cancellation of the whole server analysis. Use an external job deadline for
operational runs and reconcile server work after cancellation.

A model reviewer must interpret every unsupported feature, missing/unexpected
node and trace disposition; check source/interface resolution and input
completeness; compare current/candidate and both traffic directions; cover the
required traffic space and failure scenarios. A one-flow trace cannot establish
all-packet policy or actual TCP/service success. A deployment gate additionally
requires an approved immutable artifact, target set, fresh baseline, applicable
NOS/hardware tests, service canary and recovery plan. None is supplied by a
successful API request.

Primary references:
- https://batfish.readthedocs.io/en/latest/notebooks/interacting.html
- https://batfish.readthedocs.io/en/latest/notebooks/forwarding.html
- https://batfish.readthedocs.io/en/latest/formats.html
- https://containerlab.dev/manual/kinds/

## Exercise

Make the current fixture permit Telnet while the candidate disables it. Explain
why the current state fails policy but might still be the source of an authorised
remediation. Require a documented exception for that baseline; do not silently
turn a failure into success. Then introduce a mixed transport form, a comment
containing the same words, a missing VTY range and an unowned undescribed port.
Explain each result and why every case still lacks service/deployment evidence.
