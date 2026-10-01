#!/usr/bin/env python3
"""One authority for the edition this download is, and a check that nothing drifts.

    python3 tools/stamp_edition.py            # check; non-zero if anything disagrees
    python3 tools/stamp_edition.py --write    # rewrite the stamped lines

EDITION.json is the authority. Eleven reader-facing files repeated the edition
identifier in their own words. In a previously published release the book's
first page said RTN-2026-09-27 while the README a reader downloaded introduced
itself, historically and wrongly, as RTN-2026-09-26 "matching the 746-page print
proof" --- an earlier edition and an earlier page count. A reader deciding whether the book is dependable reads
that README first. One authority, and a checker, is the only arrangement that
survives the next revision.

Two kinds of mention are distinguished, because both are legitimate:

  * a STAMP is a file introducing the payload it belongs to. It must name the
    current edition, and --write rewrites it.
  * a HISTORICAL mention names an earlier edition on purpose --- a changelog
    section, a superseded-by note, a dated evidence run. It is allowed only on a
    line that says so, with one of the words below, or in a file listed as a
    history. An undeclared stale identifier anywhere else fails the check.

The dated evidence folders are deliberately not renamed. A run that happened on
26 September is evidence from 26 September whatever edition ships it, and
QUALIFICATION.md says which of its runs were repeated for this edition and which
were not.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDITION_FILE = os.path.join(HERE, 'EDITION.json')
TOKEN = re.compile(r'RTN-20\d\d-\d\d-\d\d')

# Files whose whole job is to carry history. Mentions in these are not stamped
# and not policed, line by line.
HISTORIES = {'CHANGELOG.md'}

# Words that make a stale mention legitimate on the line that carries it.
HISTORICAL_WORDS = re.compile(
    r'supersede|superseded|supersedes|previous|previously|earlier|historical|'
    r'history|was published|replaced|prior |retained|captured|revision folder|'
    r'^#+ Revision |no longer', re.I | re.M)

# path -> (regex with one group to replace, replacement built from the edition)
def stamps(ed):
    pages = ed['book']['print_pages']
    colour = ed['book']['colour_pages']
    e = ed['edition']
    return {
        'README.md': [(
            re.compile(r'^Edition \*\*RTN-20\d\d-\d\d-\d\d\*\*, matching the\s+'
                       r'\d+-page black-and-white print\s+proof\s+and (?:the\s+)?'
                       r'\d+-page colour edition\.', re.M),
            'Edition **%s**, matching the %d-page black-and-white print\n'
            'proof and the %d-page colour edition.' % (e, pages, colour))],
        'INDEX.md': [(re.compile(r'^Edition RTN-20\d\d-\d\d-\d\d\.', re.M),
                      'Edition %s.' % e)],
        'QUALIFICATION.md': [(re.compile(r'^# Qualification of RTN-20\d\d-\d\d-\d\d', re.M),
                              '# Qualification of %s' % e)],
        'prerequisites.json': [(re.compile(r'"edition": "RTN-20\d\d-\d\d-\d\d"'),
                                '"edition": "%s"' % e)],
        'workbook-baselines/README.md': [
            (re.compile(r'^Edition RTN-20\d\d-\d\d-\d\d\.', re.M), 'Edition %s.' % e)],
        'learning/START-HERE.md': [
            (re.compile(r'^Edition: RTN-20\d\d-\d\d-\d\d,', re.M), 'Edition: %s,' % e)],
        'learning/TASK-INDEX.md': [
            (re.compile(r'^Edition RTN-20\d\d-\d\d-\d\d\.', re.M), 'Edition %s.' % e)],
        'learning/OPERATIONS-JOURNEY.md': [
            (re.compile(r'^Edition RTN-20\d\d-\d\d-\d\d\.', re.M), 'Edition %s.' % e)],
        'learning/practical-route/README.md': [
            (re.compile(r'^Edition \*\*RTN-20\d\d-\d\d-\d\d\*\*\.', re.M),
             'Edition **%s**.' % e)],
        'learning/practical-route/N8N-LAB.md': [
            (re.compile(r'^Edition RTN-20\d\d-\d\d-\d\d\.', re.M), 'Edition %s.' % e)],
        'learning/practical-route/POWER-AUTOMATE-LAB.md': [
            (re.compile(r'^Edition RTN-20\d\d-\d\d-\d\d\.', re.M), 'Edition %s.' % e)],
    }


def main():
    write = '--write' in sys.argv[1:]
    ed = json.load(open(EDITION_FILE, encoding='utf-8'))
    current = ed['edition']
    problems, changed = [], []

    for rel, rules in stamps(ed).items():
        path = os.path.join(HERE, rel)
        if not os.path.exists(path):
            problems.append('%s: stamped file is missing' % rel)
            continue
        text = open(path, encoding='utf-8').read()
        new = text
        for pattern, replacement in rules:
            if not pattern.search(new):
                problems.append('%s: no line matches the stamp pattern %s'
                                % (rel, pattern.pattern[:46]))
                continue
            new = pattern.sub(lambda m: replacement, new, count=1)
        if new != text:
            if write:
                open(path, 'w', encoding='utf-8').write(new)
                changed.append(rel)
            else:
                problems.append('%s: the stamped line does not name %s'
                                % (rel, current))

    # Every other mention in the payload must be current or declared historical.
    stale = 0
    for dirpath, dirnames, filenames in os.walk(HERE):
        dirnames[:] = [d for d in dirnames
                       if d not in ('.git', '__pycache__', 'evidence')]
        for name in filenames:
            if not name.endswith(('.md', '.json', '.py', '.yml', '.txt')):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), HERE)
            if rel in HISTORIES or rel == 'SHA256SUMS.txt':
                continue
            try:
                text = open(os.path.join(dirpath, name), encoding='utf-8').read()
            except (OSError, UnicodeDecodeError):
                continue
            lines = text.splitlines()
            for i, line in enumerate(lines):
                for tok in TOKEN.findall(line):
                    if tok == current:
                        continue
                    # The declaring word may be on the line before or after:
                    # prose wraps, and a line-based search that missed a phrase
                    # split across a newline is exactly how residue survived a
                    # previous revision. Read a window.
                    window = '\n'.join(lines[max(0, i - 1):i + 2])
                    if HISTORICAL_WORDS.search(window):
                        continue
                    stale += 1
                    problems.append('%s: stale identifier %s with nothing on or '
                                    'beside the line declaring it historical: %s'
                                    % (rel, tok, line.strip()[:68]))

    print('edition %s; %d files stamped; %d stale identifier(s) outside a '
          'declared historical context' % (current, len(stamps(ed)), stale))
    for c in changed:
        print('    rewritten: %s' % c)
    if problems:
        for p in problems:
            print('    %s' % p)
        print('\n%d problem(s).' % len(problems))
        return 2
    print('every stamped file names this edition, and every other mention of an '
          'earlier one is declared historical on or beside its own line.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
