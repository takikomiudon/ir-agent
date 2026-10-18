"""Caller-scoped claim/renew receipts, committed with the job mutation.

Call lookup before cleanup or mutation and record afterwards in the same caller
transaction. No transaction is committed here. A receipt is historical metadata,
not a new lease grant. There is no TTL, deletion API, restore-loss detection,
authentication, model execution, or complete-request API in this module.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta
from hashlib import sha256
import json

from .models import integer, json_text, text, timestamp


SCHEMA = """
CREATE TABLE IF NOT EXISTS job_request_receipts (
    caller_namespace TEXT NOT NULL, request_id TEXT NOT NULL,
    data TEXT NOT NULL, first_saved_at TEXT NOT NULL,
    PRIMARY KEY(caller_namespace,request_id)
);
"""


def _label(value, field):
    text(value, field)
    if value != value.strip():
        raise ValueError(field + ' must not have surrounding whitespace')
    return value


def _clock(value):
    rendered = value.isoformat() if isinstance(value, datetime) else value
    timestamp(rendered, 'trusted now')
    return rendered


def _digest(value):
    return sha256(json_text(value).encode()).hexdigest()


def claim_payload(worker, lease_seconds, measurement_synthetic):
    """Normalize only semantic input; None is explicitly unknown provenance."""
    _label(worker, 'worker')
    integer(lease_seconds, 'lease_seconds', minimum=1)
    if measurement_synthetic is not None and type(measurement_synthetic) is not bool:
        raise ValueError('measurement_synthetic must be true, false or null')
    return {'contract_version': 1, 'operation': 'claim', 'worker': worker,
            'lease_seconds': lease_seconds, 'measurement_synthetic': measurement_synthetic}


def renew_payload(job_id, worker, expected_attempt, lease_seconds):
    _label(job_id, 'job_id'); _label(worker, 'worker')
    integer(expected_attempt, 'expected_attempt', minimum=1)
    integer(lease_seconds, 'lease_seconds', minimum=1)
    return {'contract_version': 1, 'operation': 'renew', 'job_id': job_id,
            'worker': worker, 'expected_attempt': expected_attempt, 'lease_seconds': lease_seconds}


def _payload(value):
    if not isinstance(value, dict) or value.get('contract_version') != 1 or type(value.get('contract_version')) is not int:
        raise ValueError('A supported, explicit request contract version is required')
    if value.get('operation') == 'claim':
        normalized = claim_payload(value.get('worker'), value.get('lease_seconds'), value.get('measurement_synthetic'))
    elif value.get('operation') == 'renew':
        normalized = renew_payload(value.get('job_id'), value.get('worker'), value.get('expected_attempt'), value.get('lease_seconds'))
    else:
        raise ValueError('Only claim and renew request receipts are supported')
    if set(value) != set(normalized) or value != normalized:
        raise ValueError('Request payload must contain exactly its normalized semantic fields')
    return deepcopy(normalized)


class JobRequestReceipts:
    def __init__(self, connection):
        self.connection = connection
        self._savepoint = 0

    def _tables(self):
        return {row[0] for row in self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    @contextmanager
    def _atomic_record(self):
        if not self.connection.in_transaction:
            raise ValueError('Record a request receipt inside the job mutation transaction')
        self._savepoint += 1
        point = 'job_request_' + str(id(self)) + '_' + str(self._savepoint)
        self.connection.execute('SAVEPOINT ' + point)
        try:
            yield
        except BaseException:
            self.connection.execute('ROLLBACK TO SAVEPOINT ' + point)
            self.connection.execute('RELEASE SAVEPOINT ' + point)
            raise
        else:
            self.connection.execute('RELEASE SAVEPOINT ' + point)

    def _stored(self, namespace, request_id):
        row = self.connection.execute(
            'SELECT data,first_saved_at FROM job_request_receipts WHERE caller_namespace=? AND request_id=?',
            (namespace, request_id)).fetchone()
        if row is None:
            return None
        value = json.loads(row[0])
        required = {'caller_namespace', 'request_id', 'contract_version', 'operation',
                    'request_payload', 'request_sha256', 'original_response', 'first_saved_at'}
        if not isinstance(value, dict) or set(value) != required:
            raise ValueError('Stored receipt has an invalid shape')
        payload = _payload(value['request_payload'])
        if (value['caller_namespace'] != namespace or value['request_id'] != request_id
                or value['first_saved_at'] != row[1] or type(value['contract_version']) is not int
                or value['contract_version'] != payload['contract_version']
                or value['operation'] != payload['operation'] or value['request_sha256'] != _digest(payload)):
            raise ValueError('Stored receipt identity or request hash differs from its payload')
        timestamp(value['first_saved_at'], 'saved receipt time')
        original = value['original_response']
        if original is None:
            if value['operation'] != 'claim':
                raise ValueError('A renew receipt cannot contain a null original response')
        else:
            fields = {'job_id', 'company_id', 'worker', 'generation', 'lease_until',
                      'packet_sha256', 'attempt_id', 'measurement_event_id'}
            if not isinstance(original, dict) or set(original) != fields:
                raise ValueError('Stored original response must be minimal immutable metadata')
            for field in ('job_id', 'company_id', 'worker'):
                _label(original[field], 'response.' + field)
            integer(original['generation'], 'response.generation', minimum=1)
            timestamp(original['lease_until'], 'response.lease_until')
            digest = original['packet_sha256']
            if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                raise ValueError('Stored original packet hash is invalid')
            for field in ('attempt_id', 'measurement_event_id'):
                if original[field] is not None:
                    _label(original[field], 'response.' + field)
            if original['measurement_event_id'] is not None and original['attempt_id'] is None:
                raise ValueError('A measurement event reference requires a measured attempt')
        return value

    def lookup(self, namespace, request_id, payload):
        _label(namespace, 'caller_namespace'); _label(request_id, 'request_id')
        normalized = _payload(payload)
        value = self._stored(namespace, request_id)
        if value is not None and (value['request_sha256'] != _digest(normalized)
                                  or value['request_payload'] != normalized):
            raise ValueError('Request ID was already used for a different semantic payload')
        return value

    def _job(self, job_id):
        row = self.connection.execute(
            'SELECT id,company_id,packet,lease_owner,lease_until,attempts,status FROM jobs WHERE id=?',
            (job_id,)).fetchone()
        if row is None:
            return None
        value = dict(zip(('id', 'company_id', 'packet', 'worker', 'lease_until', 'generation', 'status'), row))
        value['packet'] = json.loads(value['packet'])
        if not isinstance(value['packet'], dict):
            raise ValueError('Saved job packet must be an object')
        return value

    def _measurement(self, job_id, generation):
        if 'job_attempts' not in self._tables():
            return None, []
        row = self.connection.execute(
            'SELECT attempt_id,data,first_saved_at FROM job_attempts WHERE job_id=? AND generation=?',
            (job_id, generation)).fetchone()
        if row is None:
            return None, []
        header = json.loads(row[1])
        if (header['id'] != row[0] or header['job_id'] != job_id or header['generation'] != generation
                or header['first_saved_at'] != row[2]):
            raise ValueError('Measured header differs from its stored identity')
        events = []
        for row in self.connection.execute(
                'SELECT event_id,attempt_id,sequence,kind,data,first_saved_at FROM job_attempt_events '
                'WHERE attempt_id=? ORDER BY sequence', (header['id'],)):
            event = json.loads(row[4])
            if ((event['id'], event['attempt_id'], event['sequence'], event['kind'], event['first_saved_at'])
                    != (row[0], row[1], row[2], row[3], row[5]) or event['sequence'] != len(events) + 1):
                raise ValueError('Measured event differs from its stored identity or sequence')
            events.append(event)
        return header, events

    def _clock_issues(self, now):
        """Known later saves block creating a falsely early receipt.

        No deleted history or silent backup rollback can be detected from this
        local high-water check. Clock ordering is not authentication or proof of
        the exact commit instant of an outer transaction.
        """
        current = timestamp(now)
        issues = []
        tables = self._tables()
        for table in ('job_request_receipts', 'job_attempts', 'job_attempt_events'):
            if table not in tables:
                continue
            if any(timestamp(row[0]) > current for row in self.connection.execute('SELECT first_saved_at FROM ' + table)):
                issues.append('clock_before_known_saved_' + table)
        return issues

    def record(self, namespace, request_id, payload, job_id, *, now):
        """Record success (including no-job) in an existing mutation transaction.

        The caller must look up the receipt before performing any job mutation.
        This helper cannot undo side effects a caller already committed before
        consulting it, nor reconstruct an old response from current job data.
        """
        now = _clock(now)
        normalized = _payload(payload)
        with self._atomic_record():
            existing = self.lookup(namespace, request_id, normalized)
            if existing is not None:
                original_id = (existing['original_response'] or {}).get('job_id')
                if job_id != original_id:
                    raise ValueError('An immutable receipt cannot be assigned another result job')
                return existing
            issues = self._clock_issues(now)
            if issues:
                raise ValueError('Receipt clock precedes known saved history; do not create an early proof')
            original = None
            if job_id is None:
                if normalized['operation'] != 'claim':
                    raise ValueError('Only a successful no-job claim can have a null response')
            else:
                _label(job_id, 'job_id')
                job = self._job(job_id)
                if job is None:
                    raise ValueError('Receipt job is not saved')
                if job['status'] != 'leased' or job['worker'] != normalized['worker']:
                    raise ValueError('Receipt needs the saved successful lease and its worker')
                integer(job['generation'], 'saved lease generation', minimum=1)
                if timestamp(job['lease_until']) <= timestamp(now):
                    raise ValueError('A new success receipt cannot grant an already expired lease')
                try:
                    requested_deadline = timestamp(now) + timedelta(seconds=normalized['lease_seconds'])
                except OverflowError as error:
                    raise ValueError('Requested lease deadline is outside the supported clock range') from error
                if timestamp(job['lease_until']) != requested_deadline:
                    raise ValueError('Saved lease deadline differs from this operation clock and requested lease length')
                if normalized['operation'] == 'renew' and (job_id != normalized['job_id']
                        or job['generation'] != normalized['expected_attempt']):
                    raise ValueError('Renew receipt job or generation differs from its request')
                header, events = self._measurement(job_id, job['generation'])
                event_id = None
                if header is not None:
                    if (header['company_id'] != job['company_id'] or header['worker_id'] != job['worker']
                            or header['packet_sha256'] != _digest(job['packet']) or not events):
                        raise ValueError('Receipt measurement differs from its saved job')
                    expected_kind = 'lease_started' if normalized['operation'] == 'claim' else 'lease_renewed'
                    event = events[-1]
                    if event['kind'] != expected_kind or event['payload']['lease_until'] != job['lease_until']:
                        raise ValueError('Receipt needs the corresponding successful measurement event')
                    if not event['normal_interval'] or event['clock_issues']:
                        raise ValueError('Cannot create a new success receipt from an abnormal clock interval')
                    if normalized['operation'] == 'claim' and header['synthetic'] is not normalized['measurement_synthetic']:
                        raise ValueError('Claim provenance differs from its saved measurement')
                    event_id = event['id']
                original = {'job_id': job['id'], 'company_id': job['company_id'], 'worker': job['worker'],
                            'generation': job['generation'], 'lease_until': job['lease_until'],
                            'packet_sha256': _digest(job['packet']),
                            'attempt_id': header['id'] if header else None, 'measurement_event_id': event_id}
            receipt = {'caller_namespace': namespace, 'request_id': request_id, 'contract_version': 1,
                       'operation': normalized['operation'], 'request_payload': normalized,
                       'request_sha256': _digest(normalized), 'original_response': original,
                       'first_saved_at': now}
            self.connection.execute('INSERT INTO job_request_receipts VALUES (?,?,?,?)',
                                    (namespace, request_id, json_text(receipt), now))
            return receipt

    def envelope(self, receipt, *, now, replayed=False):
        """Read-only replay: original metadata plus present lease checks.

        No cleanup, claim, renewal, expiry event, or usage is written here.
        Namespace is only an ID scope; this module is not an authentication layer.
        """
        now = _clock(now)
        if type(replayed) is not bool or not isinstance(receipt, dict):
            raise ValueError('A saved receipt and explicit replay flag are required')
        stored = self._stored(_label(receipt.get('caller_namespace'), 'caller_namespace'),
                              _label(receipt.get('request_id'), 'request_id'))
        if stored is None or stored != receipt:
            raise ValueError('Envelope must reference the unchanged saved receipt')
        original = stored['original_response']
        current = None
        if original is not None:
            current = {'status': 'unknown', 'valid_now': None, 'observed_at': now,
                       'job_id': original['job_id'], 'generation': None, 'worker': None,
                       'job_status': None, 'lease_until': None, 'packet_sha256': None, 'reason_codes': []}
            try:
                job = self._job(original['job_id'])
                clock_issues = self._clock_issues(now)
                if job is None:
                    current['reason_codes'] = ['job_not_available']
                else:
                    current.update(generation=job['generation'], worker=job['worker'], job_status=job['status'],
                                   lease_until=job['lease_until'], packet_sha256=_digest(job['packet']))
                    header, events = self._measurement(original['job_id'], original['generation'])
                    if events and (not events[-1]['normal_interval'] or events[-1]['clock_issues']):
                        clock_issues.append('measured_clock_interval_abnormal')
                    if clock_issues:
                        current['reason_codes'] = clock_issues
                    elif job['generation'] != original['generation']:
                        current.update(status='reclaimed', valid_now=False, reason_codes=['lease_generation_changed'])
                    elif job['company_id'] != original['company_id'] or current['packet_sha256'] != original['packet_sha256']:
                        current['reason_codes'] = ['frozen_job_identity_or_packet_changed']
                    elif job['status'] == 'completed' or (events and events[-1]['kind'] == 'completed'):
                        current.update(status='completed', valid_now=False, reason_codes=['job_completed'])
                    elif events and events[-1]['kind'] == 'lease_expired':
                        current.update(status='expired', valid_now=False, reason_codes=['lease_expiry_recorded'])
                    elif job['status'] != 'leased':
                        current.update(status='inactive', valid_now=False, reason_codes=['job_not_leased'])
                    elif job['worker'] != original['worker']:
                        current.update(status='reclaimed', valid_now=False, reason_codes=['lease_owner_changed'])
                    elif timestamp(job['lease_until']) <= timestamp(now):
                        current.update(status='expired', valid_now=False, reason_codes=['lease_deadline_reached'])
                    else:
                        current.update(status='active', valid_now=True)
            except (ValueError, KeyError, TypeError):
                current.update(status='unknown', valid_now=None, reason_codes=['saved_lease_metadata_invalid'])
        return {'request_ref': {'caller_namespace': stored['caller_namespace'], 'request_id': stored['request_id'],
                                'operation': stored['operation'], 'contract_version': stored['contract_version']},
                'replayed': replayed, 'original_response': deepcopy(original), 'current_lease': current}
