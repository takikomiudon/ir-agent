"""Immutable measurements of successful job leases, not active analysis time.

The caller installs SCHEMA and calls start immediately after a successful claim,
renew after its job update, complete after its result update, and expire before
resetting an expired lease. Related writes belong in the caller's transaction.
``now`` is a trusted, offset-aware clock supplied by the runtime, not job data.
Synthetic status must be explicitly supplied: None means unknown, not observed.
No usage, cost, request receipts, capacity projection, or integration hooks live
here. Missing legacy starts remain unmeasured.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json

from .models import integer, json_text, text, timestamp


SCHEMA = """
CREATE TABLE IF NOT EXISTS job_attempts (
    attempt_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    generation INTEGER NOT NULL CHECK(generation>=1),
    data TEXT NOT NULL, first_saved_at TEXT NOT NULL,
    UNIQUE(job_id,generation)
);
CREATE TABLE IF NOT EXISTS job_attempt_events (
    event_id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL REFERENCES job_attempts(attempt_id),
    sequence INTEGER NOT NULL CHECK(sequence>=1),
    kind TEXT NOT NULL CHECK(kind IN ('lease_started','lease_renewed','completed','lease_expired')),
    data TEXT NOT NULL, first_saved_at TEXT NOT NULL,
    UNIQUE(attempt_id,sequence)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_job_attempt_terminal
    ON job_attempt_events(attempt_id) WHERE kind IN ('completed','lease_expired');
"""

_TERMINAL = frozenset({'completed', 'lease_expired'})


def _digest(value):
    return sha256(json_text(value).encode()).hexdigest()


def _identity(job_id, expected_attempt):
    text(job_id, 'job_id')
    integer(expected_attempt, 'expected_attempt', minimum=1)
    return {'job_id': job_id, 'expected_attempt': expected_attempt}


def _unmeasured(job_id, generation):
    return {'status': 'unmeasured', 'job_id': job_id, 'generation': generation,
            'reason_codes': ['attempt_start_not_measured']}


def _clock_text(value):
    rendered = value.isoformat() if isinstance(value, datetime) else value
    timestamp(rendered, 'trusted now')
    return rendered


class JobAttempts:
    def __init__(self, connection):
        self.connection = connection
        self._savepoint_sequence = 0

    @contextmanager
    def _atomic(self):
        nested = self.connection.in_transaction
        self._savepoint_sequence += 1
        point = 'job_attempt_' + str(id(self)) + '_' + str(self._savepoint_sequence)
        self.connection.execute('SAVEPOINT ' + point if nested else 'BEGIN IMMEDIATE')
        try:
            yield
        except BaseException:
            if nested:
                self.connection.execute('ROLLBACK TO SAVEPOINT ' + point)
                self.connection.execute('RELEASE SAVEPOINT ' + point)
            else:
                self.connection.execute('ROLLBACK')
            raise
        else:
            self.connection.execute('RELEASE SAVEPOINT ' + point if nested else 'COMMIT')

    def _job(self, job_id):
        row = self.connection.execute(
            'SELECT id,company_id,packet,lease_owner,lease_until,attempts,status,result,completed_at '
            'FROM jobs WHERE id=?', (job_id,)).fetchone()
        if row is None:
            raise ValueError('Unknown job')
        keys = ('id', 'company_id', 'packet', 'lease_owner', 'lease_until', 'attempts',
                'status', 'result', 'completed_at')
        value = dict(zip(keys, row))
        value['packet'] = json.loads(value['packet'])
        if not isinstance(value['packet'], dict):
            raise ValueError('Saved job packet must be an object')
        return value

    def _header(self, job_id, generation):
        row = self.connection.execute(
            'SELECT data FROM job_attempts WHERE job_id=? AND generation=?',
            (job_id, generation)).fetchone()
        return json.loads(row[0]) if row is not None else None

    def _events(self, attempt_id):
        return [json.loads(row[0]) for row in self.connection.execute(
            'SELECT data FROM job_attempt_events WHERE attempt_id=? ORDER BY sequence',
            (attempt_id,))]

    def history(self, job_id: str, expected_attempt: int) -> dict:
        _identity(job_id, expected_attempt)
        self._job(job_id)
        header = self._header(job_id, expected_attempt)
        if header is None:
            return _unmeasured(job_id, expected_attempt)
        return {'status': 'recorded', 'attempt': header, 'events': self._events(header['id'])}

    @staticmethod
    def _response(header, event, *, added):
        return {'status': 'recorded', 'added': added,
                'attempt': deepcopy(header), 'event': deepcopy(event)}

    @staticmethod
    def _validate_job(job, header, *, status):
        if job['attempts'] != header['generation']:
            raise ValueError('Job lease generation differs from the measured attempt')
        if job['status'] != status or job['lease_owner'] != header['worker_id']:
            raise ValueError('Saved job state or worker differs from the measured attempt')
        if job['company_id'] != header['company_id'] or _digest(job['packet']) != header['packet_sha256']:
            raise ValueError('Saved job company or packet differs from the frozen attempt')

    @staticmethod
    def _latest_deadline(events):
        return next(event['payload']['lease_until'] for event in reversed(events)
                    if event['kind'] in ('lease_started', 'lease_renewed'))

    @staticmethod
    def _event(header, events, request, *, now, effective_at, payload):
        current = timestamp(now, 'trusted now')
        effective = timestamp(effective_at, 'effective_at')
        issues = list(events[-1]['clock_issues']) if events else []
        if current < timestamp(header['started_at']):
            issues.append('wall_clock_before_attempt_start')
        if events and current < timestamp(events[-1]['observed_at']):
            issues.append('wall_clock_before_previous_observation')
        if events and current < timestamp(events[-1]['first_saved_at']):
            issues.append('wall_clock_before_previous_save')
        if effective > current:
            issues.append('effective_time_after_observation')
        if request['kind'] in _TERMINAL and effective < timestamp(header['started_at']):
            issues.append('terminal_time_before_attempt_start')
        issues = list(dict.fromkeys(issues))
        sequence = len(events) + 1
        event_id = 'attempt-event-' + _digest({'attempt_id': header['id'], 'sequence': sequence})
        return {'id': event_id, 'attempt_id': header['id'], 'sequence': sequence,
                'kind': request['kind'], 'observed_at': now, 'first_saved_at': now,
                'effective_at': effective_at, 'normal_interval': not issues,
                'clock_issues': issues, 'request': deepcopy(request), 'payload': deepcopy(payload)}

    def _put_event(self, event):
        self.connection.execute('INSERT INTO job_attempt_events VALUES (?,?,?,?,?,?)',
                                (event['id'], event['attempt_id'], event['sequence'], event['kind'],
                                 json_text(event), event['first_saved_at']))

    def start(self, job_id: str, expected_attempt: int, *, synthetic: bool | None,
              now: str | datetime, worker_session_id: str | None = None) -> dict:
        """Record a fresh successful claim; never use as a legacy backfill.

        Identity, worker, packet and generation come from the saved job. The
        trusted hook must call this in the same transaction as that new claim;
        a job row alone cannot prove when a pre-existing lease was first taken.
        None is an explicit unknown synthetic classification. Retries return the
        original start, even if trusted now or the job's current lease advanced.
        """
        identity = _identity(job_id, expected_attempt)
        now = _clock_text(now)
        if synthetic is not None and type(synthetic) is not bool:
            raise ValueError('synthetic must explicitly be true, false or null (unknown)')
        if worker_session_id is not None:
            text(worker_session_id, 'worker_session_id')
        request = {'kind': 'lease_started', **identity, 'synthetic': synthetic,
                   'worker_session_id': worker_session_id}
        with self._atomic():
            job = self._job(job_id)
            existing = self._header(job_id, expected_attempt)
            if existing is not None:
                events = self._events(existing['id'])
                if not events or events[0]['kind'] != 'lease_started' or existing['request'] != request:
                    raise ValueError('A measured start is immutable; retry the same request')
                return self._response(existing, events[0], added=False)
            if job['attempts'] != expected_attempt or job['status'] != 'leased':
                raise ValueError('Record only the current successful claim generation')
            text(job['lease_owner'], 'saved lease owner')
            if timestamp(job['lease_until'], 'saved lease deadline') <= timestamp(now):
                raise ValueError('A new measured claim must have an unexpired lease')
            packet = job['packet']
            job_kind = packet.get('kind')
            if job_kind is None and 'thesis' in packet:
                job_kind = 'research'
            stage = packet.get('stage')
            for field, value in (('packet kind', job_kind), ('packet stage', stage)):
                if value is not None:
                    text(value, field)
            previous = self.connection.execute(
                'SELECT attempt_id,generation FROM job_attempts WHERE job_id=? AND generation<? '
                'ORDER BY generation DESC LIMIT 1', (job_id, expected_attempt)).fetchone()
            header = {'id': 'attempt-' + _digest(identity), 'job_id': job['id'],
                      'company_id': job['company_id'], 'generation': job['attempts'],
                      'worker_id': job['lease_owner'], 'worker_session_id': worker_session_id,
                      'job_kind': job_kind, 'stage': stage, 'packet_sha256': _digest(packet),
                      'synthetic': synthetic, 'started_at': now, 'first_saved_at': now,
                      'previous_measured_attempt': {'id': previous[0], 'generation': previous[1]} if previous else None,
                      'measurement_scope': 'lease_ownership', 'request': request}
            event = self._event(header, [], request, now=now, effective_at=now,
                                payload={'lease_until': job['lease_until']})
            self.connection.execute('INSERT INTO job_attempts VALUES (?,?,?,?,?)',
                                    (header['id'], job_id, expected_attempt, json_text(header), now))
            self._put_event(event)
            return self._response(header, event, added=True)

    def _append(self, job_id, *, expected_attempt, expected_sequence, kind, now, lease_until=None):
        identity = _identity(job_id, expected_attempt)
        integer(expected_sequence, 'expected_sequence', minimum=0)
        now = _clock_text(now)
        current = timestamp(now, 'trusted now')
        request = {'kind': kind, **identity, 'expected_sequence': expected_sequence}
        if kind == 'lease_renewed':
            timestamp(lease_until, 'lease_until')
            request['lease_until'] = lease_until
        with self._atomic():
            job = self._job(job_id)
            header = self._header(job_id, expected_attempt)
            if header is None:
                return _unmeasured(job_id, expected_attempt)
            events = self._events(header['id'])
            if expected_sequence < len(events):
                existing = events[expected_sequence]
                if existing['request'] != request:
                    raise ValueError('An event sequence is immutable; retry the same request')
                return self._response(header, existing, added=False)
            if expected_sequence != len(events):
                raise ValueError('Event sequence changed; read the latest attempt before appending')
            if not events or events[-1]['kind'] in _TERMINAL:
                raise ValueError('A measured attempt has already ended')
            previous_deadline = self._latest_deadline(events)
            expected_status = 'completed' if kind == 'completed' else 'leased'
            self._validate_job(job, header, status=expected_status)
            if kind == 'lease_renewed':
                if timestamp(job['lease_until']) != timestamp(lease_until):
                    raise ValueError('Renewal deadline differs from the updated saved job')
                if timestamp(previous_deadline) <= current or timestamp(job['lease_until']) <= current:
                    raise ValueError('Only an unexpired measured lease can be renewed')
                payload = {'previous_lease_until': previous_deadline, 'lease_until': job['lease_until']}
                effective_at = now
            else:
                if timestamp(job['lease_until']) != timestamp(previous_deadline):
                    raise ValueError('Saved lease differs from its measured renewal history')
                payload = {'lease_until': previous_deadline}
                if kind == 'completed':
                    completed = timestamp(job['completed_at'], 'saved completion time')
                    if completed >= timestamp(previous_deadline):
                        raise ValueError('A measured completion must precede its lease deadline')
                    if job['result'] is None:
                        raise ValueError('A completed measurement needs its saved job result')
                    payload.update(completed_at=job['completed_at'], result_sha256=_digest(json.loads(job['result'])))
                    effective_at = job['completed_at']
                else:
                    if current < timestamp(previous_deadline):
                        raise ValueError('Cannot observe a lease expiry before its saved deadline')
                    effective_at = previous_deadline
            event = self._event(header, events, request, now=now,
                                effective_at=effective_at, payload=payload)
            self._put_event(event)
            return self._response(header, event, added=True)

    def renew(self, job_id: str, expected_attempt: int, *, expected_sequence: int,
              lease_until: str, now: str | datetime) -> dict:
        """Call after the saved job's renewal, within that transaction."""
        return self._append(job_id, expected_attempt=expected_attempt, expected_sequence=expected_sequence,
                            kind='lease_renewed', lease_until=lease_until, now=now)

    def complete(self, job_id: str, expected_attempt: int, *, expected_sequence: int, now: str | datetime) -> dict:
        """Call after the saved job result; result and event must commit together."""
        return self._append(job_id, expected_attempt=expected_attempt, expected_sequence=expected_sequence,
                            kind='completed', now=now)

    def expire(self, job_id: str, expected_attempt: int, *, expected_sequence: int, now: str | datetime) -> dict:
        """Call before resetting the expired saved lease; do not infer worker stop."""
        return self._append(job_id, expected_attempt=expected_attempt, expected_sequence=expected_sequence,
                            kind='lease_expired', now=now)
