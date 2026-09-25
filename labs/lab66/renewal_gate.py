"""Offline evidence gate for a synthetic TLS certificate deployment.

This does not make TLS connections, parse certificates or establish trust. The
fingerprints, validity times and validation verdicts are explicit synthetic input.
PASS applies only to the supplied target set, sample freshness and reserve.
"""
from dataclasses import dataclass, replace
from datetime import timedelta
import json
import re
from timeline import utc, seconds


def fingerprint(value):
    if not isinstance(value, str) or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise ValueError('Use a normalised lowercase SHA256 certificate fingerprint')
    return value


def name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Non-empty target and source identifiers are required')
    return value


@dataclass(frozen=True)
class Observation:
    target: str
    source: str
    sampled_at: str
    served_fingerprint: str
    not_before: str
    not_after: str
    tls_validated: bool | None

    def __post_init__(self):
        name(self.target)
        name(self.source)
        utc(self.sampled_at)
        fingerprint(self.served_fingerprint)
        if utc(self.not_before) >= utc(self.not_after):
            raise ValueError('Certificate validity interval must have positive length')
        if self.tls_validated is not None and type(self.tls_validated) is not bool:
            raise ValueError('TLS verdict must be True, False or None')


def assess(expected, observations, *, now, max_age_s, min_remaining_s):
    """FAIL dominates UNKNOWN; absent, stale or future-dated evidence cannot pass.

The caller selects one observation per expected target at a known evaluation
time. Duplicate and unexpected target input is rejected, never silently merged.
"""
    if not expected:
        raise ValueError('An empty target set cannot pass')
    for target, cert in expected.items():
        name(target)
        fingerprint(cert)
    instant = utc(now)
    age_limit = seconds(max_age_s, positive=True)
    reserve = timedelta(seconds=seconds(min_remaining_s, positive=True))
    by_target = {}
    for row in observations:
        if row.target not in expected or row.target in by_target:
            raise ValueError('Unexpected or duplicate target')
        by_target[row.target] = row
    decisions = {}
    for target in sorted(expected):
        row = by_target.get(target)
        if row is None:
            decisions[target] = {'verdict': 'UNKNOWN', 'reasons': ['missing observation']}
            continue
        age = (instant - utc(row.sampled_at)).total_seconds()
        if age < 0 or age > age_limit:
            decisions[target] = {'verdict': 'UNKNOWN', 'reasons': ['future or stale observation']}
            continue
        failures = []
        if row.served_fingerprint != expected[target]:
            failures.append('served certificate differs from approved certificate')
        # Check validity at both the sampled handshake time and evaluation time.
        if utc(row.not_before) > utc(row.sampled_at) or utc(row.not_before) > instant:
            failures.append('certificate not yet valid')
        if utc(row.not_after) <= instant or utc(row.not_after) - instant < reserve:
            failures.append('insufficient remaining validity')
        if row.tls_validated is False:
            failures.append('TLS validation failed')
        if failures:
            verdict, reasons = 'FAIL', failures
        elif row.tls_validated is None:
            verdict, reasons = 'UNKNOWN', ['TLS validation result missing']
        else:
            verdict, reasons = 'PASS', ['all model criteria satisfied']
        decisions[target] = {'verdict': verdict, 'reasons': reasons, 'source': row.source}
    states = {value['verdict'] for value in decisions.values()}
    overall = 'FAIL' if 'FAIL' in states else 'UNKNOWN' if 'UNKNOWN' in states else 'PASS'
    return {'verdict': overall, 'targets': decisions}


def fixture():
    expected = {'lon-edge-1': 'a' * 64, 'lon-edge-2': 'a' * 64}
    rows = [Observation(target, 'synthetic-probe:' + target, '2026-09-24T02:59:30Z',
                        'a' * 64, '2026-09-01T00:00:00Z', '2026-12-01T00:00:00Z', True)
            for target in expected]
    policy = dict(now='2026-09-24T03:00:00Z', max_age_s=60, min_remaining_s=7*86400)
    return expected, rows, policy


def examples():
    expected, rows, policy = fixture()
    cases = {'issued_but_second_target_still_old': [rows[0], replace(rows[1], served_fingerprint='b'*64)],
             'second_target_not_sampled': rows[:1], 'both_targets_checked': rows,
             'validation_failed': [rows[0], replace(rows[1], tls_validated=False)],
             'stale_observation': [rows[0], replace(rows[1], sampled_at='2026-09-24T02:58:00Z')]}
    return {'scope': 'Synthetic offline inputs; no TLS or device execution', 'policy': policy,
            'cases': {key: assess(expected, data, **policy) for key, data in cases.items()}}


if __name__ == '__main__':
    print(json.dumps(examples(), indent=2))
