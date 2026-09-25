# Lab 85.1 — invented economics worksheet

Run `python economics.py` and `python -m unittest discover -v` in this directory.
Python 3 standard library only; no network or financial service is contacted.

All GBP inputs are invented; there are no market quotes, outage observations or audited accounts.
Costs use positive values, receipts negative. Index 0 is the decision date, indices 1–7 year ends.
Outputs retain unrounded Decimal arithmetic until display. Cost PV is not benefits-minus-costs NPV.

Ownership pays 140,000 at zero; 15,000 support, 3,679.20 facility power, 3,000 rack and 8,000 purchased
operations annually. Year 7 adds 10,000 disposal minus 5,000 sale. Service pays 10,000 at zero and
52,000 annually including equal capacity/quality/scope and exit (assumed, not verified).
Prices are fixed nominal in the base case; VAT, tax, financing and working capital are excluded.

Two separate sensitivities: owned support escalates 3% from year 2; or a growth module costs 100,000
at end year 3 plus 15,000 support in years 4–7. The latter holds all other costs fixed and does not
prove the base service offer accommodates that growth. The accounting bridge is a separate 70,000
router example; its 10,000 depreciation must not be added to ownership cash costs.

23 tests check dated discounting against a manually solvable example, input boundaries, receipts,
category totals, sensitivity dates and ranking reversal, checkpoint break-even, denominators,
event-frequency arithmetic and the profit-to-cash bridge. This is bounded local arithmetic.
