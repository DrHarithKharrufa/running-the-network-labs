#!/usr/bin/env python3
"""Offline VRP coverage model for plain AS_SEQUENCE paths, not RPKI validation.

No certificate, signature, repository, RTR, policy or forwarding verification.
AS_SET/confederation notation is deliberately reported as unsupported.
"""
import argparse
import ipaddress
import json
import re
from pathlib import Path


def asn(value, allow_zero=False):
    if type(value) not in (int, str):
        raise ValueError('ASN must be an integer or text, never a float/Boolean')
    token = str(value).removeprefix('AS')
    if re.fullmatch(r'[0-9]+\.[0-9]+', token):
        high, low = map(int, token.split('.'))
        if high > 65535 or low > 65535:
            raise ValueError('asdot component exceeds 65535')
        number = high * 65536 + low
    elif re.fullmatch(r'[0-9]+', token):
        number = int(token)
    else:
        raise ValueError('Expected decimal ASN or asdot notation')
    if not (0 if allow_zero else 1) <= number <= 4294967295:
        raise ValueError('ASN out of range')
    return number


def load_vrps(path):
    data = json.loads(Path(path).read_text())
    records = data['records']
    if not isinstance(records, list):
        raise ValueError('records must be a list')
    out = []
    for record in records:
        if not isinstance(record, list) or len(record) != 3:
            raise ValueError('Each record must contain prefix, maxLength, ASN')
        prefix, maxlen, origin = record
        network = ipaddress.ip_network(prefix, strict=True)
        if type(maxlen) is not int or not network.prefixlen <= maxlen <= network.max_prefixlen:
            raise ValueError('Invalid maxLength')
        out.append((network, maxlen, asn(origin, allow_zero=True)))
    return out


def validate(prefix, origin, vrps):
    network = ipaddress.ip_network(prefix, strict=True)
    origin = asn(origin)
    covering = [r for r in vrps if network.version == r[0].version and network.subnet_of(r[0])]
    matching = [r for r in covering if network.prefixlen <= r[1] and origin == r[2]]
    return ('valid' if matching else 'invalid' if covering else 'not-found'), matching, covering


def origin_from_text(path, local_as=None):
    if not isinstance(path, str):
        raise ValueError('Missing or non-text AS path')
    if any(c in path for c in '{}()[]'):
        raise ValueError('AS_SET/confederation notation unsupported by this adapter')
    tokens = path.split()
    if not tokens:
        if local_as is None:
            raise ValueError('Empty AS path requires --local-as')
        return asn(local_as)
    sequence = [asn(token) for token in tokens]
    return sequence[-1]


def report(vrp_path, bgp_path, local_as=None):
    vrps = load_vrps(vrp_path)
    table = json.loads(Path(bgp_path).read_text())['routes']
    rows = []
    for prefix, paths in sorted(table.items()):
        for entry in paths:
            row = {'prefix': prefix, 'path': entry.get('path')}
            try:
                origin = origin_from_text(row['path'], local_as)
                state, matching, covering = validate(prefix, origin, vrps)
                row.update(origin=origin, state=state,
                           matching=[[str(n), length, a] for n, length, a in matching],
                           covering=[[str(n), length, a] for n, length, a in covering])
            except ValueError as exc:
                row.update(state='unsupported', reason=str(exc))
            rows.append(row)
    return {'scope': __doc__, 'paths': rows,
            'counts': {state: sum(r['state'] == state for r in rows)
                       for state in ['valid', 'invalid', 'not-found', 'unsupported']}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('vrps')
    parser.add_argument('bgp')
    parser.add_argument('--local-as')
    parser.add_argument('--output')
    args = parser.parse_args()
    try:
        result = report(args.vrps, args.bgp, args.local_as)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    text = json.dumps(result, indent=2) + '\n'
    print(text, end='')
    if args.output:
        Path(args.output).write_text(text)
    return 2 if result['counts']['unsupported'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
