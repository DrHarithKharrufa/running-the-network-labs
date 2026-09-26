# Running the Network — reader companion

Edition **RTN-2026-09-26**, matching the 746-page black-and-white print proof
and 744-page colour edition. There are 84 chapter lab directories, five shared
lab directories and 35 Containerlab topology files. Reproduce inventories with
`python tools/count.py .`; programs, tests and topologies are different counts.

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
python check-environment.py --chapter 71 --mode offline
python check-environment.py --chapter 79 --mode live
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
[harness/README.md](harness/README.md). Fresh captures are under
`evidence/revision-2026-09-26/`; older records remain unchanged in `evidence/`.
The new output hash covers the exact stored text's UTF-8 encoding. It is an
integrity check, not a digital signature or an image digest.

The n8n route was executed locally against a simulated monitoring/device adapter.
The Power Automate route is a construction and acceptance guide, not a qualified
tenant export. Live PRTG, a Power Automate tenant, an optional real language model
and production effects require their stated acceptance tests. No new commercial
NOS, hardware or scale qualification is claimed. Historical evidence in the author
package retains its original date and scope. Vendor images are not supplied.

## Edition, errata and licence

The public [repository](https://github.com/DrHarithKharrufa/running-the-network-labs)
and [issue tracker](https://github.com/DrHarithKharrufa/running-the-network-labs/issues)
are established. For this proof use the accompanying ZIP and `EDITION.json`.
Its matching public release must be checked before approving the printed download
promise; this local delivery does not publish that release.

Report edition, chapter/file, expected/observed results and a minimal reproduction
without secrets or customer data. [ERRATA.md](ERRATA.md) retains earlier corrections.
Companion code and lab material use the [MIT licence](LICENSE). The book and
separate configuration workbook remain copyright works. Vendor names identify
platforms and do not imply endorsement.
