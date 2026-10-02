# From a CSV to an operational decision

Edition **RTN-2026-10-03**. Allow eight sessions of 45–90 minutes, then the n8n and Power Automate sessions. These are learning estimates, not measured reader completion times. Start here even if you have never written Python. The existing `learning/` workbooks cover the wider network and leadership route; this course supplies the missing code-to-workflow progression.

The story: Aldergate's branch dashboard says “uplink down”. A colleague suggests automating a port bounce. Your first job is to establish what the observation means. By the end you can collect evidence, distinguish missing data from a down interface, create a review case and explain why a case is not a repair. The devices in this course are simulated. The HTTP requests, Python processes, SQLite transactions and n8n execution are real. For actual routing and packet forwarding, continue to the FRR workbook and `harness/`.

## Set up once

Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/). On Windows, open PowerShell; on Linux/macOS, open a terminal. Change into this directory using `cd` and a quoted absolute path if it contains spaces. On Windows test `py -3 --version`; elsewhere test `python3 --version`. Below, `python` means that verified interpreter. Substitute `py -3` or `python3` consistently if necessary.

Create a task environment:

```text
python -m venv .venv
```

On Windows run programs with `.venv\Scripts\python.exe`; on Linux/macOS use `.venv/bin/python`. Activation is optional. This course uses the standard library: no `pip install` is needed for sessions 1–8. The n8n, Power Automate, optional model and existing vendor labs have separate prerequisites. Keep the original files, then copy a lesson to `my_01.py` before changing it. Do not call a file `json.py`, `csv.py` or `ipaddress.py`: it would shadow the library you are trying to import.

## 1. Read the inventory; understand the objects

Run `python 01_inventory.py`. Expected:

```text
r1: ask branch-team
r2: ask branch-team
r3: ask core-team
3 devices inventoried
```

Open the 15-line program beside `inventory.csv`. `import csv` loads a library; `Path(__file__)` locates this program, so the CSV is found even if your terminal starts elsewhere. `with ... as source` owns the open file and closes it when the indented block ends. `DictReader` turns each data row into a dictionary: keys are the header names and values are strings. `list(...)` materialises those rows. `devices[0]` selects the first dictionary; `devices[0]['owner']` selects one value. Python counts list positions from zero. Quotes delimit strings; they are not part of the value.

The `for` loop repeats its indented body for each dictionary. `name = ...` binds a value to a name; it does not compare values. An f-string evaluates expressions inside braces. `len(devices)` counts rows, not CSV lines including the header. Indentation is syntax: use four spaces, consistently.

**Do it:** in your copy, print `r1 -> 192.0.2.11` and the corresponding lines for r2/r3. Then print only devices owned by `branch-team`, using `if device['owner'] == 'branch-team':` inside the loop. Predict how many lines appear before running it. **Transfer:** change r3's owner in a copied CSV; your program should adapt without a hard-coded count. **Solution:** see `SOLUTIONS.md`, P1. If you see `KeyError`, compare the field spelling to the CSV header. If you see `FileNotFoundError`, inspect the path, not the network.

## 2. Turn strings into addresses; reject invalid inventory

Run `python 02_addresses.py`: `Validated 3 unique targets; no connections made`. A string that looks like an address is not yet an address. `ipaddress.ip_address()` validates and creates an address object. `ip_network(..., strict=True)` rejects host bits in a supposed network definition. `address in network` asks a subnet-membership question; it is not a textual prefix comparison.

`def validate_inventory(rows):` defines a function. Its argument is the data supplied by the caller; `return rows` supplies a result back to that caller. A set stores unique values, making duplicate checks direct. `raise ValueError(...)` stops the operation with a useful reason. The `if __name__ == '__main__':` guard runs the command-line example when launched directly, but not when another program imports its functions.

**Do it:** fill `exercises/P2_inventory.py` so an empty owner is rejected. Then try a duplicate address and `192.0.2.11` in `198.51.100.0/24`. Both must fail; no connection has yet occurred. A script should not “fix” an address by guessing which digit you meant. **Transfer:** use an IPv6 address and network. Explain why dotted-string sorting would be a poor substitute for address objects. **Solution:** P2 in `SOLUTIONS.md` and the complete `02_addresses.py`.

## 3. Parse a snapshot; preserve unknowns

Run `python 03_report.py`. The JSON output has eth1 up with error ratio `0.0`, and eth2 down with ratio `0.04`. These are constructed cumulative counters, not measured interval error rates. The four errors in 100 packets give 4%; do not label the fraction 0.04 as 0.04%.

`json.loads()` decodes text to Python values. It does not establish that required interfaces exist. Read `validate_snapshot()` in `common.py`: it checks the object, generation, field names, states, counters and complete expected interface set. `isinstance(x, dict)` tests a container type; `type(counter) is int` deliberately excludes booleans, which Python otherwise treats as integers. Returning an empty interface list would conceal a parser failure.

**Do it:** in a copy of `snapshot.json`, delete eth2, duplicate eth1, set errors to `-1`, and change `oper_state` to `maybe`. Each must be rejected. Set packets to zero: the result is JSON `null` (`None` in Python), because the ratio is undefined. A zero denominator is not proof of zero errors. **Transfer:** add an expected third interface to the contract and the fixture together. **Solution:** P3 and `03_report.py`. Keep a valid *down* observation separate from an invalid observation.

## 4. Make your first bounded HTTP read

Start the local teaching API in a second terminal, from this directory. Generate a local credential without putting it in a script. PowerShell:

```powershell
$env:RTN_LAB_TOKEN = (& python -c "import secrets; print(secrets.token_urlsafe(32))")
python lab_service.py --db my-course.sqlite
```

Linux/macOS:

```sh
export RTN_LAB_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
python3 lab_service.py --db my-course.sqlite
```

The server listens only on `127.0.0.1:8765`. Do not expose this teaching server publicly. In your first terminal run `python 04_collect.py`: it returns r1's snapshot with both interfaces. Stop the server with Ctrl+C and run the collector again. A connection failure is an error, not a report that every port is healthy. Restart with the **same** database to retain the state; use a new filename for a clean exercise. Keep the same token in all terminals that perform writes. Enter it locally with PowerShell `$env:RTN_LAB_TOKEN = Read-Host 'Local lab token'` or a shell `read -r -s RTN_LAB_TOKEN; export RTN_LAB_TOKEN`; do not include it in evidence submitted to a reviewer.

Read `request()` in `common.py`: `Request` describes the operation, the opener performs it with redirects rejected, and the context manager closes the response. The fixed destination prevents an event from choosing a target URL. A three-second socket timeout and a 65,536-byte read limit bound this small read; they are not a universal whole-program deadline. The Content-Type and decoded object are checked before the device schema. HTTP errors raise exceptions instead of entering the healthy path.

**Do it:** change the copied collector's path to `/api/devices/missing`. Expect HTTP 404. Explain which fact is known (that resource was not found) and which is unknown (any real device's condition). **Transfer:** collect r2 and retain its asset ID. Do not send these documentation IPs to a real network.

## 5. Calculate a diff before a write

Run `python 05_plan.py`. It reports before/after descriptions, the asset, `expected_generation: 0` on a fresh database, and `change_required: true`. Read again with lesson 4: generation remains zero. The plan is a dictionary; creating it changes no remote state.

**Do it:** fill `exercises/P5_plan.py` to return `change_required: false` when the desired description already matches. Reject an empty or excessively long description. **Transfer:** change the desired description without changing the observed snapshot. Explain why a plan needs the snapshot's generation: it becomes stale if someone changes the resource meanwhile. **Solution:** P5 and `05_plan.py`.

## 6. Collect a small fleet without hiding partial failure

Run `python 06_fleet.py`. r1/r2 are `COLLECTED`; `missing` is `UNKNOWN`; the process exits **1 intentionally**. On PowerShell inspect `$LASTEXITCODE`; in a POSIX shell inspect `$?` immediately after the command. Exit 0 would wrongly imply the whole requested set succeeded.

`ThreadPoolExecutor(max_workers=2)` permits at most two concurrent tasks here. `submit` returns a future; `as_completed` yields finished futures. Calling `future.result()` either returns the value or raises that task's exception. `try/except` records the target's failure while independent reads continue. The final sort makes the report stable despite completion order. A thread finishing is not the same as a healthy device.

**Do it:** add r3; predict three collected and one unknown. Change the worker count to 1 and compare elapsed time without treating this tiny loopback experiment as a network-performance benchmark. **Transfer:** explain why the same “continue with others” policy may be inappropriate for changes to two members of one redundancy pair. Do not add automatic write retries to this collector.

## 7. Apply, verify, fail an acceptance check, recover

Make the server's local token available in the client terminal. Run:

```text
python 07_change.py
python 07_change.py --apply
python 07_change.py --apply
python 07_change.py --description "Rejected test description" --apply --fail-service
```

On a fresh database the statuses are `DRY_RUN`, `VERIFIED`, `NO_CHANGE`, `ROLLED_BACK`. The last flag deliberately fails the local acceptance decision; it does not damage a physical network. Re-read r1: its description is `Aldergate verified uplink`. Generation has increased because the rejected change and restoration were both writes. A restored description with an unhealthy service returns `RECOVERY_SERVICE_FAILED`; missing or malformed recovery evidence returns `RECOVERY_UNKNOWN`. Neither exits successfully.

The server atomically compares `expected_generation` before updating. The client reads back the result and separately requests `/api/service`. That second HTTP endpoint reports **simulated** service health. It is an architectural teaching boundary, not an independent production data-plane probe. The FRR workbook supplies real packet probes.

**Do it:** run `python -m unittest -v test_route.HTTPTests.test_lost_write_response_not_retried`. Its fake transport applies a change and then loses the reply. The client reports `UNKNOWN_WRITE`, collects what it can and does not repeat the write. Inspect the test; identify exactly which call is mocked. **Transfer:** have two clients plan from one generation and prove that the second stale write gets HTTP 409. Explain why you must not “fix” that by blindly substituting the newest generation. **Solution:** P7 in `SOLUTIONS.md`.

## 8. Investigate a monitoring event and record a decision

Run `python 08_investigate.py`. Keep the returned case ID. The case contains the event, owner, timestamped evidence, deterministic summary and `AWAITING_REVIEW`. It states an observation; it does not invent a root cause. Read it before deciding:

```text
python 08_investigate.py --case case-YOUR-ID
python 08_investigate.py --case case-YOUR-ID --decision investigate
```

The decision becomes `REVIEWED`, with revision 2 and a local-token-holder audit entry. No email is sent and no port is disabled. `dismiss` is the alternative human decision; neither means service recovery. A later Up event creates a separate observation rather than silently closing the earlier case.

Use `test_route.py` to trace exact duplicates, a reused ID with changed content, an old event, a future timestamp, a missing sensor mapping, malformed collection, simultaneous duplicates and process restart. SQLite reserves the operation and creates the case in one transaction. A failed collector commits neither; the same event may be retried after recovery. A stale event is journalled without a case. Retention and cross-system delivery would need additional design in production.

**Do it:** create a fresh event dictionary in a short script, call `request('/events','POST',event)` twice, then restart the service and send it again. One case ID must survive all three submissions. **Transfer:** change `status` while retaining the event ID; expect 409. Change the event ID and increase sequence for a genuinely new Up observation. **Solution:** P8.

## 9–10. Products and optional AI

Follow `N8N-LAB.md` to import and execute the actual workflow. Follow `POWER-AUTOMATE-LAB.md` for the equivalent tenant-hosted flow; its live cloud acceptance remains a reader/author tenant exercise. `agent_advisor.py` adds an optional local Ollama summary with no device or approval tools. Its schema/failure boundaries are tested; no model-generated diagnosis is claimed as verified fact. Installation, model selection and acceptance are in `N8N-LAB.md`.

## Your submission and the move to a real network

Submit your edited P1/P2/P5 files, one invalid-data example with the expected failure, the dry-run and recovery reports, one deduplicated case, and a one-page runbook: target, permission, preconditions, stop conditions, service check, recovery, owner and escalation. Redact the token. Score correctness, evidence, recovery and explanation 0–2 each; require at least 6/8, no zero and no unresolved material error. These are teaching gates, not certification or production authority.

Then use the configuration workbook's FRR tasks, where the IP forwarding is real. For a commercial device, choose one read-only collector in Lab 71 with independently verified SSH host identity. Record device model/NOS, driver and parser versions, complete expected interface set, healthy/empty/error/truncated fixtures and a read-only result. Only after that review should you design a change adapter with qualified commit/rollback behaviour. Do not replace the simulator URL with a production address and assume its semantics transfer.

For expert retrieval, use `../TASK-INDEX.md`. For the move from engineer to architecture and leadership, continue the existing capstone and design/leadership workbook: budget the service under failure, compare alternatives and defend a decision with uncertainty. The code gives you evidence; it does not make the investment decision for you.

## Troubleshooting and reset

| Symptom | Check |
| --- | --- |
| Interpreter not found | Use the verified `py -3` or `python3` executable. |
| Syntax/indentation error | Inspect the named line and the preceding line; compare spacing and quotes. |
| Import finds the wrong module | Rename files such as `json.py`; run from this course directory. |
| Connection refused | Start `lab_service.py`; verify its loopback port, then `/health`. |
| 401 | Client and server must use the same local token. Restarting with a new token requires updating clients and n8n credentials. |
| 409 | Identify stale generation/revision or an event ID reused with changed content; inspect state before resubmitting. |
| STALE | Use a current timestamp and a sequence larger than the last accepted observation, or a fresh database for a clean test. |
| 502/503 | Read the collector/journal error; do not convert it to “healthy”. Remove the intentional lab fault, then retry the identical event. |
| Address already in use | Stop your previous lab process; do not terminate an unidentified process. |

Stop the server with Ctrl+C. Keep the database if it is your evidence; use a new database filename for reset. SQLite files and tokens belong in your local working directory, not in a public issue. Run `python -B test_route.py` to check the supplied boundaries without modifying your course database.
