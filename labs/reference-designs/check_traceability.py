#!/usr/bin/env python3
"""Check that BRANCH-COMPLETE.md is traceable, rather than asserting it is.

    python3 check_traceability.py

"Worked" is a word a design document can claim without earning. This parses the
tables in BRANCH-COMPLETE.md and fails unless every requirement is served by at
least one decision, one acceptance test, one fault test and one recovery
procedure -- and unless every decision, test and procedure names a requirement
it exists for. An orphan in either direction is the gap the next incident starts
in.

It reads the document only. It proves nothing about a network.
"""
import os
import re
import sys

DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'BRANCH-COMPLETE.md')
KINDS = {'D': 'decision', 'AT': 'acceptance test', 'FT': 'fault test', 'RP': 'recovery procedure'}


def parse(text):
    """Every identifier defined in a table's first cell, and what each serves."""
    defined, serves = {}, {}
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if not cells:
            continue
        m = re.fullmatch(r'(R|D|AT|FT|RP)-(\d+[a-z]?)', cells[0])
        if not m:
            continue
        ident = cells[0]
        defined.setdefault(m.group(1), set()).add(ident)
        # requirements referenced anywhere else in the row
        refs = set(re.findall(r'\bR-\d+[a-z]?\b', ' '.join(cells[1:])))
        serves[ident] = refs
    return defined, serves


def main():
    if not os.path.exists(DOC):
        print('BRANCH-COMPLETE.md not found beside this script')
        return 2
    text = open(DOC, encoding='utf-8').read()
    defined, serves = parse(text)

    reqs = sorted(defined.get('R', set()))
    if not reqs:
        print('no requirements found; the document is not in the expected shape')
        return 2

    problems = []

    # A requirement may be exempted from one kind, but only out loud: the
    # document has to say which requirement, which kind, and why.
    exempt = set()
    for m in re.finditer(r'\*\*Declared exemption\.\*\*\s+(R-\d+[a-z]?)[^.]*?no (fault test|acceptance test|decision|recovery procedure)', text, re.S):
        exempt.add((m.group(1), m.group(2)))

    # forwards: every requirement is served by each kind
    for r in reqs:
        for kind, name in KINDS.items():
            if (r, name) in exempt:
                continue
            if not any(r in serves.get(i, set()) for i in defined.get(kind, set())):
                problems.append('%s has no %s' % (r, name))

    # backwards: nothing exists without a requirement
    for kind in KINDS:
        for i in sorted(defined.get(kind, set())):
            if not serves.get(i):
                problems.append('%s names no requirement it serves' % i)
            else:
                for r in serves[i]:
                    if r not in defined.get('R', set()):
                        problems.append('%s serves %s, which is not defined' % (i, r))

    print('%d requirements, %d decisions, %d acceptance tests, %d fault tests, '
          '%d recovery procedures'
          % (len(reqs), len(defined.get('D', ())), len(defined.get('AT', ())),
             len(defined.get('FT', ())), len(defined.get('RP', ()))))

    if problems:
        for p in problems:
            print('    %s' % p)
        print('\n%d gap(s). The design is not traceable end to end.' % len(problems))
        return 2
    print('every requirement has a decision, an acceptance test, a fault test and a '
          'recovery procedure, and nothing exists without a requirement.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
