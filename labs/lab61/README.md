# Chapter 60 — the NOC and the operating model

Arithmetic for a chapter with no protocol in it.

- `incident_record.py` treats severity as the worst of six triggers, supports
  provisional classification and reclassification with history, and shows what
  a mandatory cause field does to your data.
- `rota_arithmetic.py` computes 24/7 headcount and checks a proposed pattern
  against the HSE shift-work guidelines.
- `coverage_models.py` counts handovers and residual out-of-hours call-outs.

## Files

- `coverage_models.py`
- `incident_record.py`
- `rota_arithmetic.py`
- `test_coverage_models.py`
- `test_incident_record.py`
- `test_rota_arithmetic.py`

Run the tests with `python3 -m unittest discover -v` from this directory,
where this lab ships them.
