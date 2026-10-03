# Running the Network — reader companion

Edition **RTN-2026-10-04**, matching the 714-page black-and-white print
proof and the 713-page colour edition. There are 84 chapter lab directories, five shared
lab directories and 35 Containerlab topology files. Reproduce inventories with
`python tools/count.py .`; programs, tests and topologies are different counts.

This edition also carries everything the 120-task *Configuration Workbook* uses:
the offline automation kit in [`workbook-automation/`](workbook-automation/README.md),
the preparation contracts in [`workbook-fixtures/`](workbook-fixtures/README.md), and
the documented-source register in
[`workbook-baselines/documented-sources.json`](workbook-baselines/README.md) — 714 READ
and six NO_PANEL vendor outcomes, each READ entry with its official URL, version and
retrieval date. READ is documentary syntax evidence, not a device run.
[TASK-NAVIGATOR.md](TASK-NAVIGATOR.md) lists every task with its preparation,
resources and evidence; [READER-MAP.json](READER-MAP.json) is the same map for programs.

## Lab numbers are stable identifiers

The book has 87 chapters. Four former chapters now share a chapter with a
neighbour, and every subject and all 500 exercises remain. Lab directories keep
their original numbers, so `labs/lab64` is a stable identifier, not the printed
chapter number: [INDEX.md](INDEX.md) gives the printed chapter in its Ch column and
[learning/CHAPTER-MAP.md](learning/CHAPTER-MAP.md) converts in both directions.
Program banners and docstrings written before the 87-chapter edition still cite
the earlier chapter number; they are left unchanged so that the recorded test and
evidence hashes of those programs stay valid. Use the chapter map for them too.

## Start with a task

- New to the profession: [learning/START-HERE.md](learning/START-HERE.md).
- A connected operating case: [OPERATIONS-JOURNEY.md](learning/OPERATIONS-JOURNEY.md).
- New to Python: [eight-session practical route](learning/practical-route/README.md).
- Find a chapter: [INDEX.md](INDEX.md).
- Troubleshoot, change, monitor or plan: [task index](learning/TASK-INDEX.md).
- Build n8n monitoring: [N8N-LAB.md](learning/practical-route/N8N-LAB.md).
- Build Power Automate: [POWER-AUTOMATE-LAB.md](learning/practical-route/POWER-AUTOMATE-LAB.md).
- Check your exercise attempt: [500 model answers](learning/SELECTED-ANSWERS.md).
- Judge an answer you had to *produce* — an incident record, a design decision, a capacity case: [assessment standards](learning/ASSESSING-YOUR-ANSWER.md), each with a complete example, a plausible bad one and a rubric.

The Python course starts with local CSV/JSON and progresses to an HTTP device
simulator, bounded collection, a dry-run plan, apply/read-back/recovery and a durable
investigation case. It uses Python 3.11+ on Windows, Linux or macOS. Later network
labs have separate Linux, package, privilege, image and equipment requirements.

## Prerequisites and tests

From the extracted companion root:

```text
python check-environment.py --lab-id 71 --mode offline
python check-environment.py --lab-id 79 --mode live
python run-all-tests.py --quick --out my-test-results
```

Use `python3` if that is your interpreter's name. The checker reads
`prerequisites.json`, checks pinned dependencies and separates offline from live
work. It does not infer readiness from a nearby topology file. A missing or manual
prerequisite is not a pass. The runner preserves previous output directories.
`--quick` includes eligible offline tests beside topology files.
`--include-live` explicitly selects declared privileged tests; read their READMEs.

[QUALIFICATION.md](QUALIFICATION.md) lists actual fresh execution. The older
blanket “all 104 programs pass” claim is superseded by dated per-program results.
A model test does not deploy a topology or qualify a commercial NOS.

## Routing and monitoring evidence

Use the complete named topology on a dedicated Linux/Docker lab host; see
[harness/README.md](harness/README.md). Captures are in dated folders —
`evidence/revision-2026-09-26/` and `evidence/revision-2026-10-01/` — and the
Linux namespace and test-suite logs of the 1–2 October review are in
`evidence/review-2026-10-01-codex/`; older records remain unchanged in `evidence/`.
The new output hash covers the exact stored text's UTF-8 encoding. It is an
integrity check, not a digital signature or an image digest.

The n8n route was executed locally against a simulated monitoring/device adapter.
The Power Automate route is a construction and acceptance guide, not a qualified
tenant export. Live PRTG, a Power Automate tenant, an optional real language model
and production effects require their stated acceptance tests. No new commercial
NOS, hardware or scale qualification is claimed. Historical evidence in the author
package retains its original date and scope. Vendor images are not supplied.

## Edition, errata and licence

This repository's [releases](https://github.com/DrHarithKharrufa/running-the-network-labs/releases)
are frozen editions; the tag a book was printed against never changes. `EDITION.json`
names this edition and the SHA-256 of the PDFs it matches, and `SHA256SUMS.txt`
lists every file in this release: check a download with `python verify.py --root .`
from the root, or `sha256sum -c SHA256SUMS.txt` on Linux. [CHANGELOG.md](CHANGELOG.md) records what moved
between editions; corrections made after printing go in [ERRATA.md](ERRATA.md) in
the repository's current state.

Report errors in the [issue tracker](https://github.com/DrHarithKharrufa/running-the-network-labs/issues):
the edition, the chapter or file, the expected and observed result and a minimal
reproduction, without secrets or customer data. Companion code and lab material use
the [MIT licence](LICENSE). The book and the separate configuration workbook remain
copyright works. Vendor names identify platforms and do not imply endorsement.
