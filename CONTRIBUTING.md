# Corrections and contributions

## Reporting an error

Open an issue. The useful ones say:

- **Where** — chapter number, or lab directory and file.
- **What you ran** — the exact command.
- **What you expected**, and **what happened** — paste the output.
- **Your environment** — the output of `python3 check-environment.py` covers it.

That applies to errors in the book as much as errors in the code. A wrong number
in a chapter matters more than a wrong number in a script, because more people
will act on it.

## Sending a fix

Pull requests are welcome.

1. **A failing test first.** If you can add a test that fails before your change
   and passes after it, the fix reviews itself. Most labs already have a test file
   to extend.
2. **Keep the lab's contract.** Filenames, command lines and entry points are
   printed in a book that people own. If a model is wrong, replace the model and
   leave the interface alone.
3. **Say what your change establishes.** The labs are careful about the difference
   between a calculation, a simulation, a Linux execution and a vendor platform.
   A change that blurs those will be asked about.
4. **Run the suite.** `python3 run-all-tests.py` before you push.

## What will not be merged

- Vendor network operating system images or firmware, of any kind.
- Configurations copied from licensed vendor courseware or documentation.
- Claims of tested behaviour on hardware or on a commercial platform that the
  repository cannot reproduce.
