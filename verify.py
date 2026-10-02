#!/usr/bin/env python3
"""Verify this delivery's SHA-256 manifests, without third-party dependencies.

python verify.py --root .
python verify.py --archive running-the-network-labs.zip

Every contained manifest is checked; archives also receive a complete CRC test.
Generated Python caches and a git clone's .git directory are ignored in an
unpacked tree. Run it before your own test runs add result folders. No files
are changed.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import zipfile


def entries(data):
    result = {}
    for line in data.decode('utf-8').splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        if not match:
            raise ValueError('Malformed manifest line')
        digest, name = match.groups()
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name:
            raise ValueError('Unsafe manifest path: ' + name)
        if name in result:
            raise ValueError('Duplicate manifest path: ' + name)
        result[name] = digest
    return result


def ignored(name):
    p = PurePosixPath(name)
    return ('__pycache__' in p.parts or '.git' in p.parts
            or p.suffix == '.pyc')


def validate(manifest, names, read):
    parent = str(PurePosixPath(manifest).parent)
    prefix = '' if parent == '.' else parent + '/'
    expected = entries(read(manifest))
    actual = {n[len(prefix):] for n in names
              if n.startswith(prefix) and n != manifest and not ignored(n)}
    errors = []
    for name in sorted(set(expected) - actual):
        errors.append('Missing: ' + prefix + name)
    for name in sorted(actual - set(expected)):
        errors.append('Unlisted: ' + prefix + name)
    for name in sorted(set(expected) & actual):
        if hashlib.sha256(read(prefix + name)).hexdigest() != expected[name]:
            errors.append('Hash mismatch: ' + prefix + name)
    return {'manifest': manifest, 'files': len(expected), 'errors': errors,
            'status': 'PASS' if not errors else 'FAIL'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--root', type=Path, default=None)
    group.add_argument('--archive', type=Path)
    args = parser.parse_args()
    if args.archive:
        with zipfile.ZipFile(args.archive) as archive:
            names = [x.filename for x in archive.infolist() if not x.is_dir()]
            if len(names) != len(set(names)):
                raise ValueError('Duplicate archive paths')
            for name in names:
                p = PurePosixPath(name)
                if p.is_absolute() or '..' in p.parts or '\\' in name:
                    raise ValueError('Unsafe archive path: ' + name)
            bad = archive.testzip()
            reports = [validate(n, names, archive.read) for n in names
                       if PurePosixPath(n).name == 'SHA256SUMS.txt']
            report = {'archive': str(args.archive), 'crc': 'PASS' if bad is None else bad,
                      'manifests': reports}
    else:
        root = (args.root or Path(__file__).parent).resolve()
        names = [p.relative_to(root).as_posix() for p in root.rglob('*')
                 if p.is_file() and not ignored(p.relative_to(root).as_posix())]
        read = lambda n: (root / n).read_bytes()
        reports = [validate(n, names, read) for n in names
                   if PurePosixPath(n).name == 'SHA256SUMS.txt']
        report = {'root': str(root), 'manifests': reports}
    good = bool(reports) and all(x['status'] == 'PASS' for x in reports)
    good = good and report.get('crc', 'PASS') == 'PASS'
    report['status'] = 'PASS' if good else 'FAIL'
    print(json.dumps(report, indent=2))
    return 0 if good else 1


if __name__ == '__main__':
    raise SystemExit(main())
