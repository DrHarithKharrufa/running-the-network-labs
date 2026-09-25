"""Offline teaching model: no HTTP server, model call, credentials or device action.

Identity/role arguments represent a trusted adapter's established context, not
claims accepted from an event. This file does NOT authenticate that context.
SQLite models a local journal/outbox; it cannot atomically commit a remote effect.
Only draft_case is modelled. Security containment is a separate paper exercise.
"""
import hashlib
import json
import math
import sqlite3
from dataclasses import dataclass


class Refused(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def finite_time(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise Refused('time must be finite and nonnegative')
    return value


def identifier(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 80:
        raise Refused('invalid identifier')
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in value):
        raise Refused('identifier contains forbidden characters')
    return value


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refused('duplicate JSON key')
        result[key] = value
    return result


@dataclass(frozen=True)
class Binding:
    source: str
    sensor: str
    tenant: str
    asset: str
    generation: int


@dataclass(frozen=True)
class Grant:
    grant_id: str
    action_digest: str
    reviewer: str
    tenant: str
    expires: float


EVENT_KEYS = {'event_id', 'sensor_id', 'observed_at', 'state', 'generation', 'message'}
PLAN_KEYS = {'action', 'source', 'event_id', 'sensor_id', 'tenant', 'asset',
             'generation', 'evidence_revision', 'parameters', 'expires'}


class Journal:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS events (
            source TEXT, event_id TEXT, body TEXT, fingerprint TEXT,
            PRIMARY KEY(source,event_id));
          CREATE TABLE IF NOT EXISTS current (
            source TEXT, sensor TEXT, observed REAL, event_id TEXT,
            PRIMARY KEY(source,sensor));
          CREATE TABLE IF NOT EXISTS outbox (
            action_digest TEXT PRIMARY KEY, grant_id TEXT UNIQUE, plan TEXT,
            status TEXT, receipt TEXT);
        ''')

    def close(self):
        self.db.close()

    def admit(self, raw, authenticated_source, binding, now):
        finite_time(now)
        if authenticated_source != binding.source:
            raise Refused('authenticated source mismatch')
        if not isinstance(raw, str) or len(raw.encode('utf8')) > 4096:
            raise Refused('event size/type')
        try:
            event = json.loads(raw, object_pairs_hook=no_duplicate_keys)
        except (ValueError, TypeError) as exc:
            raise Refused('invalid event JSON') from exc
        if not isinstance(event, dict) or set(event) != EVENT_KEYS:
            raise Refused('event schema')
        for key in ('event_id', 'sensor_id'):
            identifier(event[key])
        finite_time(event['observed_at'])
        if type(event['generation']) is not int or event['generation'] < 1:
            raise Refused('generation must be a positive integer')
        if event['sensor_id'] != binding.sensor or event['generation'] != binding.generation:
            raise Refused('sensor mapping changed or unknown')
        if event['state'] not in ('Down', 'Up', 'Unknown'):
            raise Refused('unknown state')
        message = event['message']
        if not isinstance(message, str) or len(message) > 512 or any(ord(c) < 32 for c in message):
            raise Refused('message limit/control characters')
        if not now - 300 <= event['observed_at'] <= now + 5:
            raise Refused('event outside age/skew allowance')
        encoded, fingerprint = canonical(event), digest(event)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            old = self.db.execute('SELECT fingerprint FROM events WHERE source=? AND event_id=?',
                                  (binding.source, event['event_id'])).fetchone()
            if old:
                if old[0] != fingerprint:
                    raise Refused('conflicting replay')
                return 'duplicate'
            latest = self.db.execute('SELECT observed,event_id FROM current WHERE source=? AND sensor=?',
                                     (binding.source, binding.sensor)).fetchone()
            if latest and event['observed_at'] <= latest[0]:
                raise Refused('older or ambiguous equal-time event; reconcile')
            self.db.execute('INSERT INTO events VALUES (?,?,?,?)',
                            (binding.source, event['event_id'], encoded, fingerprint))
            self.db.execute('INSERT OR REPLACE INTO current VALUES (?,?,?,?)',
                            (binding.source, binding.sensor, event['observed_at'], event['event_id']))
        return 'admitted'

    def _current_event(self, source, event_id, binding):
        if source != binding.source:
            raise Refused('source changed')
        row = self.db.execute('SELECT body FROM events WHERE source=? AND event_id=?',
                              (source, event_id)).fetchone()
        if not row:
            raise Refused('unknown event')
        event = json.loads(row[0])
        if event['sensor_id'] != binding.sensor or event['generation'] != binding.generation:
            raise Refused('mapping generation changed')
        current = self.db.execute('SELECT event_id FROM current WHERE source=? AND sensor=?',
                                  (source, binding.sensor)).fetchone()
        if not current or current[0] != event_id:
            raise Refused('superseded event')
        return event

    def plan(self, event_id, binding, evidence_revision, now):
        finite_time(now)
        identifier(evidence_revision)
        event = self._current_event(binding.source, event_id, binding)
        if event['state'] != 'Down' or now - event['observed_at'] > 300:
            raise Refused('current fresh Down evidence required')
        return dict(action='draft_case', source=binding.source, event_id=event_id,
                    sensor_id=binding.sensor, tenant=binding.tenant, asset=binding.asset,
                    generation=binding.generation, evidence_revision=evidence_revision,
                    parameters={'template': 'branch-investigation-v1'}, expires=now + 120)

    def validate_plan(self, plan, binding, current_evidence_revision, now):
        finite_time(now)
        if not isinstance(plan, dict) or set(plan) != PLAN_KEYS:
            raise Refused('plan schema')
        if plan['action'] != 'draft_case' or plan['parameters'] != {'template': 'branch-investigation-v1'}:
            raise Refused('action or parameters not allowed')
        if (plan['tenant'], plan['asset'], plan['generation'], plan['sensor_id']) != (
                binding.tenant, binding.asset, binding.generation, binding.sensor):
            raise Refused('plan scope changed')
        if plan['evidence_revision'] != current_evidence_revision:
            raise Refused('evidence changed')
        finite_time(plan['expires'])
        if now >= plan['expires'] or plan['expires'] > now + 120:
            raise Refused('expired or excessive plan lifetime')
        event = self._current_event(plan['source'], plan['event_id'], binding)
        if event['state'] != 'Down' or now - event['observed_at'] > 300:
            raise Refused('current fresh Down evidence required')

    def approve(self, plan, binding, evidence_revision, now, reviewer, role, tenant, grant_id):
        # In production these are independently authenticated role/scope claims.
        self.validate_plan(plan, binding, evidence_revision, now)
        if role != 'case-reviewer' or tenant != binding.tenant:
            raise Refused('reviewer authority')
        identifier(reviewer); identifier(grant_id)
        return Grant(grant_id, digest(plan), reviewer, tenant, plan['expires'])

    def enqueue(self, plan, grant, binding, evidence_revision, now):
        self.validate_plan(plan, binding, evidence_revision, now)
        if not isinstance(grant, Grant) or grant.tenant != binding.tenant or now >= grant.expires:
            raise Refused('invalid/expired grant')
        if grant.action_digest != digest(plan) or grant.expires != plan['expires']:
            raise Refused('approval does not bind this exact plan')
        try:
            with self.db:
                self.db.execute('INSERT INTO outbox VALUES (?,?,?,?,?)',
                                (digest(plan), grant.grant_id, canonical(plan), 'pending', None))
        except sqlite3.IntegrityError as exc:
            raise Refused('action or grant already used') from exc
        return digest(plan)

    def claim(self, action_digest, binding, evidence_revision, now):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row = self.db.execute('SELECT plan,status FROM outbox WHERE action_digest=?',
                                  (action_digest,)).fetchone()
            if not row or row[1] != 'pending':
                raise Refused('not pending: reconcile an uncertain result before retry')
            plan = json.loads(row[0])
            self.validate_plan(plan, binding, evidence_revision, now)
            self.db.execute('UPDATE outbox SET status=? WHERE action_digest=?',
                            ('in_progress', action_digest))
        return plan  # no external effect is executed by this teaching model

    def record_result(self, action_digest, receipt):
        identifier(receipt)  # a synthetic receipt, not verification of a real API
        with self.db:
            cur = self.db.execute('UPDATE outbox SET status=?,receipt=? WHERE action_digest=? AND status=?',
                                  ('recorded', receipt, action_digest, 'in_progress'))
            if cur.rowcount != 1:
                raise Refused('result requires one claimed action')

    def status(self, action_digest):
        row = self.db.execute('SELECT status FROM outbox WHERE action_digest=?', (action_digest,)).fetchone()
        return row[0] if row else None
