"""Offline interval arithmetic for synthetic incident evidence; no log collector.

Clock offset means source clock minus UTC, in seconds. The uncertainty is a
bound supplied by the investigator, not a measured or statistical confidence.
Event, observation and report timestamps must not be silently interchanged.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
import json
import math


def utc(value):
    if not isinstance(value, str) or 'T' not in value:
        raise ValueError('Use an ISO timestamp with T and an explicit UTC offset')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('Invalid timestamp') from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError('Timezone is required; local time is not assumed')
    return result.astimezone(timezone.utc)


def seconds(value, *, positive=False, signed=False):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('Seconds must be a finite number, not a boolean')
    if not signed and (value < 0 or (positive and value == 0)):
        raise ValueError('Invalid seconds bound')
    return value


@dataclass(frozen=True)
class Event:
    source: str
    event_time: str | None
    observed_at: str
    reported_at: str
    clock_offset_s: float | None
    uncertainty_s: float | None

    def __post_init__(self):
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError('An evidence source identifier is required')
        utc(self.observed_at)
        utc(self.reported_at)
        if self.event_time is not None:
            utc(self.event_time)
        if self.clock_offset_s is not None:
            seconds(self.clock_offset_s, signed=True)
        if self.uncertainty_s is not None:
            seconds(self.uncertainty_s)

    def interval(self):
        if any(x is None for x in (self.event_time, self.clock_offset_s, self.uncertainty_s)):
            return None
        centre = utc(self.event_time) - timedelta(seconds=self.clock_offset_s)
        margin = timedelta(seconds=self.uncertainty_s)
        return centre - margin, centre + margin


def order(a, b):
    """An overlap, including a touching endpoint, cannot establish strict order."""
    left, right = a.interval(), b.interval()
    if left is None or right is None:
        return 'UNKNOWN'
    if left[1] < right[0]:
        return 'BEFORE'
    if right[1] < left[0]:
        return 'AFTER'
    return 'OVERLAP'


def examples():
    common = dict(observed_at='2026-09-24T02:40:20Z', reported_at='2026-09-24T02:41:00Z')
    a = Event('router-log:17', '2026-09-24T02:40:05Z', clock_offset_s=4, uncertainty_s=2, **common)
    b = Event('probe-log:31', '2026-09-24T02:40:03Z', clock_offset_s=0, uncertainty_s=1, **common)
    c = Event('ticket:9', None, clock_offset_s=None, uncertainty_s=None, **common)
    precise_a = Event(a.source, a.event_time, a.observed_at, a.reported_at, 4, 0)
    precise_b = Event(b.source, b.event_time, b.observed_at, b.reported_at, 0, 0)
    records = []
    for event in (a, b, c):
        interval = event.interval()
        records.append({**asdict(event), 'utc_interval': [t.isoformat() for t in interval] if interval else None})
    return {'scope': 'Synthetic offline arithmetic, no measured clock bounds', 'events': records,
            'a_vs_b': order(a, b), 'a_vs_unknown': order(a, c),
            'a_vs_b_if_zero_uncertainty': order(precise_a, precise_b)}


if __name__ == '__main__':
    print(json.dumps(examples(), indent=2))
