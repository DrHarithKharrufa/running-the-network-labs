# Chapter 60 — security governance

Three models that refuse rather than reassure.

- `exception_register.py` assesses an exceptions register against seven
  verdicts. `--demo-fail-open` shows a completeness-only check approving six
  of seven records it should refuse.
- `metric_honesty.py` shows mean time to detect *falling* from 124.9 hours to
  65.7 as detection degrades, because it is computed over detected incidents.
- `reporting_clock.py` moves a 72-hour regulatory deadline by 66 hours across
  four defensible readings of when you "became aware", and refuses to produce
  a date when the triggering decision was never recorded.

## Files

- `exception_register.py`
- `metric_honesty.py`
- `reporting_clock.py`
- `test_exception_register.py`
- `test_metric_honesty.py`
- `test_reporting_clock.py`

Run the tests with `python3 -m unittest discover -v` from this directory,
where this lab ships them.
