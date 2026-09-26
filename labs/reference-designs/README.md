# Reference designs

Supporting data for the three worked reference designs in Appendix C:
addressing, capacity and failure assumptions reconciled against each other.

These are design exercises. They are not accepted production deployments and
they carry no per-port low-level design.

## Files

- `designs.json`
- `test_designs.py`
- `BRANCH-COMPLETE.md` — one Aldergate branch carried all the way through:
  requirement, decision, acceptance test, fault test, recovery procedure, owner
  and cost, sharing one identifier set. This is the completeness standard
  Chapter 79 asks you to reach.
- `check_traceability.py` — parses that document and fails if any requirement
  lacks a decision, acceptance test, fault test or recovery procedure, or if any
  of those exists without naming a requirement. “Traceable” is checked, not claimed.

Run the tests with `python3 -m unittest discover -v` from this directory,
where this lab ships them.
