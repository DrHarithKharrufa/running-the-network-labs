# Lab 71: parsing and uncertain outcomes

These exercises run locally. No device or network connection is made by default.
The parser fixture is synthetic IOS-style output, not a capture or NOS test.

## Installation

Use Python 3.11 or later in an isolated environment. The recorded Windows run
uses Python 3.12; versions are retained in the review evidence.

```sh
python -m venv .venv
# Windows PowerShell: .venv/Scripts/python.exe
# Linux/macOS: .venv/bin/python
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -v
```

Substitute the Windows interpreter path on Windows. The three primary parser
dependencies are pinned. `requirements-tested.txt` records all distributions
from the tested environment; it is a snapshot, not a promise of compatibility
with every OS/Python combination. Keep environments outside publication archives.
The failure simulation itself uses only the Python standard library.

## Lab 71.1: local parser and optional single-device read

```sh
python collect.py
```

The parser should produce two interface records. GigabitEthernet0/1 is
administratively down. Parsing success (exit 0) is not a service-health verdict.
The tests reject raw strings, empty results, missing/wrong fields, invalid IPv4
addresses, duplicate interfaces and missing expected interfaces. This teaching
schema accepts only the documented fixture's status vocabulary; broaden it only
after reviewing new output and meaning. One fixture does not cover a NOS release.

An optional live read requires an explicit target, user, trusted known-hosts file
and expected interface. Verify the fingerprint independently before adding it.
Use only an authorised lab target compatible with the `cisco_ios` driver:

```sh
python collect.py --host 192.0.2.2 --user reader --known-hosts verified_keys --expect GigabitEthernet0/0
```

The address is a documentation placeholder. This optional SSH path has not been
executed against a device in this review. The program prompts for a password;
do not put it on the command line. It sends one show command, has separate
connection/authentication/banner/read timeouts, and closes the connection.
Those limits are not a single whole-program deadline. Parser errors and failed
collections are errors, not empty successful inventories. Live failures return
1 and report the exception class without raw session contents. Invalid arguments
return 2. Exit 0 means the data passed the bounded record contract, not that all
interfaces or services are healthy. Raw captured evidence needs separate access
controls, redaction, timestamps and a documented retention policy.

## Lab 71.2: timed simulation and reconciliation

```sh
python robust_run.py
python robust_run.py --policy independent --max-incidents 6
python robust_run.py --policy independent --max-incidents 6 --restore-partial
```

Each demo deliberately returns **exit 1**, because incidents remain. It is not a
test-run failure. The default stops dependent work after leaf-02 applies the
change but loses its reply. The independent run shows all seven targets:

| Target | Fault | Final observation without restoration |
|---|---|---|
| leaf-01 | None | Desired two-field state |
| leaf-02 | Apply, then timeout | Desired state after `UNKNOWN` history |
| leaf-03 | Partial write, then timeout | New description, old MTU |
| leaf-04 | Apply, then read also times out | `UNKNOWN`; no observation |
| leaf-05 | Reject before mutation | Baseline observed |
| leaf-06 | Timeout before mutation | Baseline observed |
| leaf-07 | None | Desired two-field state |

The report's `simulator_truth` exposes hidden state for learners: leaf-04 really
changed, despite no successful read. The controller result must remain unknown.
`VERIFIED_SCOPE` means only the two in-memory fields matched; service was not
tested. Acknowledgement, observation and recovery are retained in each history.
No uncertain write is retried. The incident budget counts faults even when later
read-back finds the desired state. The restore option explicitly restores the
known baseline only for a partial state that can be read, then checks it again.

`asyncio.wait_for` enforces a real local deadline on a cooperative coroutine.
It cancels the delayed local call; a real remote operation could continue after
local cancellation. This simulator is not a transport, device or rollback model.
Unexpected programming errors propagate rather than being reported as success.

Run `python robust_run.py --demo-original` to inspect the byte-identical historical
script. Its claims about implemented timeouts and untouched failed devices are
wrong; it is retained for comparison, not as the recommended pattern.

## Evidence and later integration

Nineteen tests cover local failure decisions and parsing, including Netmiko's
actual missing-template fallback and parsing exception. One test replaces
Netmiko's connection with a fake to inspect arguments; this is not an SSH test.
No NAPALM, Nornir, Scrapli, Containerlab or vendor runtime is asserted here.
For later integration, pin platform/driver/parser versions, preserve authorised
baseline state, inject denied access and lost replies on an isolated target,
observe actual configuration and service, test stop/recovery/persistence and
retain a timestamped evidence manifest. Hardware limits need hardware evidence.

Primary documentation: Netmiko 4.8.0 BaseConnection and utilities source,
NAPALM support matrix/platform caveats, Nornir failed-task documentation,
RFC 7951 and the OpenConfig gNMI specification.
