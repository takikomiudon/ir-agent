from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from ir_agent.job_attempts import JobAttempts, SCHEMA as ATTEMPT_SCHEMA
from ir_agent.job_requests import JobRequestReceipts, SCHEMA, claim_payload, renew_payload
from ir_agent.models import json_text


JOB_SCHEMA = '''
CREATE TABLE jobs (
    id TEXT PRIMARY KEY, company_id TEXT, packet TEXT, lease_owner TEXT,
    lease_until TEXT, attempts INTEGER, status TEXT, result TEXT, completed_at TEXT
);
'''
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def at(seconds):
    return (NOW + timedelta(seconds=seconds)).isoformat()


@contextmanager
def transaction(connection):
    connection.execute('BEGIN IMMEDIATE')
    try:
        yield
    except BaseException:
        connection.execute('ROLLBACK')
        raise
    else:
        connection.execute('COMMIT')


class JobRequestTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript(JOB_SCHEMA + ATTEMPT_SCHEMA + SCHEMA)
        self.packet = {'thesis': {'version': 1}, 'content': 'do not duplicate the private fixture'}
        self.db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)',
                        ('job', 'issuer', json_text(self.packet), 'worker', at(100), 1,
                         'leased', 'do not duplicate the result', None))
        self.receipts = JobRequestReceipts(self.db)
        self.journal = JobAttempts(self.db)
        self.payload = claim_payload('worker', 100, None)

    def tearDown(self):
        self.db.close()

    def claim_receipt(self, request_id='claim', *, now=0, synthetic=None):
        payload = claim_payload('worker', 100, synthetic)
        with transaction(self.db):
            self.db.execute('UPDATE jobs SET lease_until=?', (at(now + 100),))
            self.journal.start('job', 1, synthetic=synthetic, now=at(now))
            return self.receipts.record('caller', request_id, payload, 'job', now=at(now))

    def count(self, table):
        return self.db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]

    def test_payloads_include_only_semantic_fields_and_three_states(self):
        self.assertEqual(self.payload, {'contract_version': 1, 'operation': 'claim', 'worker': 'worker',
                                        'lease_seconds': 100, 'measurement_synthetic': None})
        self.assertEqual(renew_payload('job', 'worker', 3, 20),
                         {'contract_version': 1, 'operation': 'renew', 'job_id': 'job',
                          'worker': 'worker', 'expected_attempt': 3, 'lease_seconds': 20})
        self.assertNotEqual(claim_payload('worker', 100, None), claim_payload('worker', 100, False))
        self.assertNotEqual(claim_payload('worker', 100, False), claim_payload('worker', 100, True))
        with self.assertRaises(TypeError):
            claim_payload('worker', 100)
        for value in (True, 0, '100'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                claim_payload('worker', value, None)
        for value in (0, 'false', []):
            with self.subTest(value=value), self.assertRaises(ValueError):
                claim_payload('worker', 100, value)
        with self.assertRaises(ValueError):
            renew_payload('job', 'worker', True, 100)

    def test_record_requires_outer_transaction_and_returns_minimal_metadata(self):
        self.journal.start('job', 1, synthetic=None, now=at(0))
        with self.assertRaises(ValueError):
            self.receipts.record('caller', 'claim', self.payload, 'job', now=at(0))
        with transaction(self.db):
            receipt = self.receipts.record('caller', 'claim', self.payload, 'job', now=NOW)
            self.assertTrue(self.db.in_transaction)
        original = receipt['original_response']
        self.assertEqual(set(original), {'job_id', 'company_id', 'worker', 'generation',
                                         'lease_until', 'packet_sha256', 'attempt_id', 'measurement_event_id'})
        self.assertEqual(original['job_id'], 'job')
        self.assertEqual(original['generation'], 1)
        self.assertEqual(original['packet_sha256'], sha256(json_text(self.packet).encode()).hexdigest())
        self.assertEqual(original['measurement_event_id'], self.journal.history('job', 1)['events'][0]['id'])
        self.assertEqual(receipt['request_sha256'], sha256(json_text(self.payload).encode()).hexdigest())
        self.assertNotIn(self.packet['content'], json_text(receipt))
        self.assertNotIn('do not duplicate the result', json_text(receipt))

    def test_lookup_preserves_original_after_time_changes_and_terminal_status(self):
        first = self.claim_receipt()
        self.db.execute("UPDATE jobs SET status='completed',completed_at=?", (at(10),))
        with transaction(self.db):
            retry = self.receipts.record('caller', 'claim', self.payload, 'job', now=at(200))
        self.assertEqual(retry, first)
        self.assertEqual(self.receipts.lookup('caller', 'claim', self.payload), first)
        self.assertEqual(self.count('job_request_receipts'), 1)
        self.assertEqual(self.count('job_attempt_events'), 1)

    def test_same_namespace_and_id_reject_changes_including_operation(self):
        self.claim_receipt()
        for changed in (claim_payload('other', 100, None), claim_payload('worker', 101, None),
                        claim_payload('worker', 100, False), renew_payload('job', 'worker', 1, 100)):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.receipts.lookup('caller', 'claim', changed)
        self.assertIsNone(self.receipts.lookup('other-caller', 'claim', self.payload))
        self.assertIsNone(self.receipts.lookup('caller', 'new-poll', self.payload))
        self.assertEqual(self.count('job_request_receipts'), 1)

    def test_namespace_and_request_identifiers_are_exact_nonempty_strings(self):
        for namespace, request_id in (('', 'id'), ('caller', ''), (' caller', 'id'), ('caller', 'id '),
                                      (None, 'id'), ('caller', 1)):
            with self.subTest(namespace=namespace, request_id=request_id), self.assertRaises(ValueError):
                self.receipts.lookup(namespace, request_id, self.payload)

    def test_unknown_payload_fields_and_invalid_versions_are_not_dropped(self):
        for changes in ({'now': at(0)}, {'prompt': 'private'}, {'contract_version': True},
                        {'contract_version': 2}, {'operation': 'complete'}):
            value = dict(self.payload, **changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.receipts.lookup('caller', 'request', value)
        value = dict(self.payload)
        value.pop('measurement_synthetic')
        with self.assertRaises(ValueError):
            self.receipts.lookup('caller', 'request', value)

    def test_null_nojob_response_is_immutable_when_work_later_exists(self):
        with transaction(self.db):
            nojob = self.receipts.record('caller', 'empty-poll', self.payload, None, now=at(0))
        self.assertIsNone(nojob['original_response'])
        self.assertEqual(self.receipts.envelope(nojob, now=at(10), replayed=True),
                         {'request_ref': {'caller_namespace': 'caller', 'request_id': 'empty-poll',
                                          'operation': 'claim', 'contract_version': 1},
                          'replayed': True, 'original_response': None, 'current_lease': None})
        with transaction(self.db):
            self.assertEqual(self.receipts.record('caller', 'empty-poll', self.payload, None, now=at(20)), nojob)
            with self.assertRaises(ValueError):
                self.receipts.record('caller', 'empty-poll', self.payload, 'job', now=at(20))
        self.assertIsNone(self.receipts.lookup('caller', 'fresh-poll', self.payload))
        self.assertEqual(self.db.execute('SELECT attempts FROM jobs').fetchone()[0], 1)

    def test_active_expired_completed_and_reclaimed_views_never_mutate(self):
        receipt = self.claim_receipt()
        changed = self.db.total_changes
        active = self.receipts.envelope(receipt, now=at(10))
        self.assertEqual(active['current_lease']['status'], 'active')
        self.assertIs(active['current_lease']['valid_now'], True)
        expired = self.receipts.envelope(receipt, now=at(100), replayed=True)
        self.assertEqual(expired['current_lease']['status'], 'expired')
        self.assertIs(expired['current_lease']['valid_now'], False)
        self.assertEqual(self.db.total_changes, changed)
        self.assertEqual(self.db.execute('SELECT status FROM jobs').fetchone()[0], 'leased')
        self.db.execute("UPDATE jobs SET status='completed'")
        self.assertEqual(self.receipts.envelope(receipt, now=at(10))['current_lease']['status'], 'completed')
        self.db.execute("UPDATE jobs SET attempts=2,status='leased',lease_until=?", (at(300),))
        reclaimed = self.receipts.envelope(receipt, now=at(20), replayed=True)
        self.assertEqual(reclaimed['current_lease']['status'], 'reclaimed')
        self.assertIs(reclaimed['current_lease']['valid_now'], False)
        self.assertEqual(reclaimed['original_response'], receipt['original_response'])
        self.assertEqual(self.count('job_attempt_events'), 1)

    def test_owner_packet_and_missing_job_do_not_prove_current_lease(self):
        receipt = self.claim_receipt()
        self.db.execute("UPDATE jobs SET lease_owner='other'")
        self.assertEqual(self.receipts.envelope(receipt, now=at(10))['current_lease']['status'], 'reclaimed')
        self.db.execute('UPDATE jobs SET lease_owner=?,packet=?', ('worker', json_text({'changed': True})))
        view = self.receipts.envelope(receipt, now=at(10))['current_lease']
        self.assertEqual(view['status'], 'unknown')
        self.assertIsNone(view['valid_now'])
        self.assertIn('frozen_job_identity_or_packet_changed', view['reason_codes'])
        self.db.execute('DELETE FROM job_attempt_events')
        self.db.execute('DELETE FROM job_attempts')
        self.db.execute('DELETE FROM jobs')
        self.assertEqual(self.receipts.envelope(receipt, now=at(10))['current_lease']['reason_codes'], ['job_not_available'])

    def test_renew_replay_keeps_first_deadline_after_another_renew(self):
        self.claim_receipt()
        with transaction(self.db):
            self.db.execute('UPDATE jobs SET lease_until=?', (at(200),))
            self.journal.renew('job', 1, expected_sequence=1, lease_until=at(200), now=at(10))
            first_payload = renew_payload('job', 'worker', 1, 190)
            first = self.receipts.record('caller', 'renew-1', first_payload, 'job', now=at(10))
        with transaction(self.db):
            self.db.execute('UPDATE jobs SET lease_until=?', (at(300),))
            self.journal.renew('job', 1, expected_sequence=2, lease_until=at(300), now=at(20))
            self.receipts.record('caller', 'renew-2', renew_payload('job', 'worker', 1, 280), 'job', now=at(20))
        changes = self.db.total_changes
        replay = self.receipts.envelope(self.receipts.lookup('caller', 'renew-1', first_payload), now=at(30), replayed=True)
        self.assertEqual(replay['original_response']['lease_until'], at(200))
        self.assertEqual(replay['current_lease']['lease_until'], at(300))
        self.assertEqual(self.db.total_changes, changes)
        self.assertEqual(self.count('job_attempt_events'), 3)
        self.assertEqual(first['original_response'], replay['original_response'])

    def test_legacy_renew_has_no_invented_measurement_references(self):
        payload = renew_payload('job', 'worker', 1, 100)
        with transaction(self.db):
            receipt = self.receipts.record('caller', 'renew', payload, 'job', now=at(0))
        self.assertIsNone(receipt['original_response']['attempt_id'])
        self.assertIsNone(receipt['original_response']['measurement_event_id'])
        self.assertEqual(self.count('job_attempts'), 0)
        with transaction(self.db), self.assertRaises(ValueError):
            self.receipts.record('caller', 'null-renew', payload, None, now=at(0))

    def test_record_checks_worker_generation_operation_event_and_provenance(self):
        self.journal.start('job', 1, synthetic=None, now=at(0))
        cases = [(claim_payload('other', 100, None), 'job'),
                 (renew_payload('job', 'worker', 2, 100), 'job'),
                 (renew_payload('different-job', 'worker', 1, 100), 'job'),
                 (renew_payload('job', 'worker', 1, 100), 'job'),
                 (claim_payload('worker', 100, False), 'job')]
        for payload, job_id in cases:
            with self.subTest(payload=payload), transaction(self.db), self.assertRaises(ValueError):
                self.receipts.record('caller', 'bad-request', payload, job_id, now=at(0))
        self.assertEqual(self.count('job_request_receipts'), 0)

    def test_new_clock_rollback_rejects_but_replay_keeps_receipt_and_returns_unknown(self):
        receipt = self.claim_receipt(now=10)
        with transaction(self.db), self.assertRaises(ValueError):
            self.receipts.record('caller', 'too-early', self.payload, None, now=at(5))
        replay = self.receipts.envelope(receipt, now=at(5), replayed=True)
        self.assertEqual(replay['original_response'], receipt['original_response'])
        self.assertEqual(replay['current_lease']['status'], 'unknown')
        self.assertIsNone(replay['current_lease']['valid_now'])
        self.assertTrue(replay['current_lease']['reason_codes'])
        with transaction(self.db):
            self.assertEqual(self.receipts.record('caller', 'claim', self.payload, 'job', now=at(-10)), receipt)
        self.assertEqual(self.count('job_request_receipts'), 1)

    def test_clock_rollback_after_journal_is_not_a_new_early_proof(self):
        self.journal.start('job', 1, synthetic=None, now=at(10))
        with transaction(self.db), self.assertRaises(ValueError):
            self.receipts.record('caller', 'bad-time', self.payload, 'job', now=at(5))
        self.assertEqual(self.count('job_request_receipts'), 0)
        self.db.execute('UPDATE jobs SET lease_until=?', (at(200),))
        self.journal.renew('job', 1, expected_sequence=1, lease_until=at(200), now=at(5))
        with transaction(self.db), self.assertRaises(ValueError):
            self.receipts.record('caller', 'abnormal', renew_payload('job', 'worker', 1, 180), 'job', now=at(20))

    def test_new_receipt_binds_requested_length_to_the_operation_clock_and_saved_deadline(self):
        self.journal.start('job', 1, synthetic=None, now=at(0))
        with transaction(self.db), self.assertRaisesRegex(ValueError, 'requested lease length'):
            self.receipts.record('caller', 'wrong-claim-length', claim_payload('worker', 99, None), 'job', now=at(0))
        self.db.execute('UPDATE jobs SET lease_until=?', (at(200),))
        self.journal.renew('job', 1, expected_sequence=1, lease_until=at(200), now=at(10))
        with transaction(self.db), self.assertRaisesRegex(ValueError, 'requested lease length'):
            self.receipts.record('caller', 'wrong-renew-length', renew_payload('job', 'worker', 1, 191), 'job', now=at(10))
        self.assertEqual(self.count('job_request_receipts'), 0)

    def test_known_expiry_event_never_becomes_an_active_grant(self):
        receipt = self.claim_receipt()
        self.journal.expire('job', 1, expected_sequence=1, now=at(110))
        view = self.receipts.envelope(receipt, now=at(120))['current_lease']
        self.assertEqual(view['status'], 'expired')
        self.assertIs(view['valid_now'], False)
        backward = self.receipts.envelope(receipt, now=at(50))['current_lease']
        self.assertEqual(backward['status'], 'unknown')
        self.assertIsNone(backward['valid_now'])

    def test_receipt_record_and_job_changes_roll_back_together(self):
        self.db.execute("UPDATE jobs SET status='pending',attempts=0,lease_owner=NULL,lease_until=NULL")
        with self.assertRaisesRegex(RuntimeError, 'abort outer'):
            with transaction(self.db):
                self.db.execute("UPDATE jobs SET status='leased',attempts=1,lease_owner='worker',lease_until=?", (at(100),))
                self.journal.start('job', 1, synthetic=None, now=at(0))
                self.receipts.record('caller', 'claim', self.payload, 'job', now=at(0))
                self.assertTrue(self.db.in_transaction)
                raise RuntimeError('abort outer')
        self.assertEqual(self.count('job_request_receipts'), 0)
        self.assertEqual(self.count('job_attempts'), 0)
        self.assertEqual(self.db.execute('SELECT status FROM jobs').fetchone()[0], 'pending')

    def test_receipt_insert_failure_can_roll_back_job_and_measurement(self):
        self.db.executescript("""CREATE TRIGGER receipt_failure BEFORE INSERT ON job_request_receipts
            BEGIN SELECT RAISE(ABORT,'receipt unavailable'); END;""")
        self.db.execute("UPDATE jobs SET status='pending',attempts=0,lease_owner=NULL,lease_until=NULL")
        with self.assertRaises(sqlite3.IntegrityError):
            with transaction(self.db):
                self.db.execute("UPDATE jobs SET status='leased',attempts=1,lease_owner='worker',lease_until=?", (at(100),))
                self.journal.start('job', 1, synthetic=None, now=at(0))
                self.receipts.record('caller', 'claim', self.payload, 'job', now=at(0))
        self.assertEqual(self.count('job_request_receipts'), 0)
        self.assertEqual(self.count('job_attempt_events'), 0)
        self.assertEqual(self.db.execute('SELECT attempts FROM jobs').fetchone()[0], 0)

    def test_inner_receipt_error_does_not_commit_or_poison_outer_transaction(self):
        self.db.executescript("""CREATE TRIGGER receipt_failure BEFORE INSERT ON job_request_receipts
            BEGIN SELECT RAISE(ABORT,'receipt unavailable'); END;""")
        self.db.execute('BEGIN IMMEDIATE')
        self.db.execute("UPDATE jobs SET company_id='outer-change'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.receipts.record('caller', 'empty', self.payload, None, now=at(0))
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.db.execute('SELECT company_id FROM jobs').fetchone()[0], 'outer-change')
        self.db.execute('ROLLBACK')
        self.assertEqual(self.db.execute('SELECT company_id FROM jobs').fetchone()[0], 'issuer')

    def test_forged_envelope_and_corrupt_request_hash_are_rejected(self):
        receipt = self.claim_receipt()
        forged = deepcopy(receipt)
        forged['original_response']['lease_until'] = at(500)
        with self.assertRaises(ValueError):
            self.receipts.envelope(forged, now=at(10))
        changed = deepcopy(receipt)
        changed['request_sha256'] = '0' * 64
        self.db.execute('UPDATE job_request_receipts SET data=?', (json_text(changed),))
        with self.assertRaises(ValueError):
            self.receipts.lookup('caller', 'claim', self.payload)

    def test_measurement_reference_identity_drift_cannot_confirm_current_lease(self):
        receipt = self.claim_receipt()
        row = self.db.execute('SELECT data FROM job_attempt_events').fetchone()
        event = json.loads(row[0])
        event['attempt_id'] = 'different-attempt'
        self.db.execute('UPDATE job_attempt_events SET data=?', (json_text(event),))
        view = self.receipts.envelope(receipt, now=at(10))['current_lease']
        self.assertEqual(view['status'], 'unknown')
        self.assertIsNone(view['valid_now'])
        self.assertEqual(view['reason_codes'], ['saved_lease_metadata_invalid'])

    def test_no_ttl_or_automatic_mutation_on_late_replay(self):
        receipt = self.claim_receipt()
        changes = self.db.total_changes
        late = self.receipts.envelope(receipt, now=at(1000000), replayed=True)
        self.assertEqual(late['original_response'], receipt['original_response'])
        self.assertEqual(late['current_lease']['status'], 'expired')
        self.assertEqual(self.db.total_changes, changes)
        self.assertEqual(self.count('job_request_receipts'), 1)

    def test_two_connections_same_id_apply_one_mutation_and_one_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'jobs.sqlite3'
            initial = sqlite3.connect(path, isolation_level=None)
            initial.executescript(JOB_SCHEMA + ATTEMPT_SCHEMA + SCHEMA)
            initial.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)',
                            ('job', 'issuer', json_text(self.packet), None, None, 0, 'pending', None, None))
            initial.close()
            ready = threading.Event(); second_entered = threading.Event(); release = threading.Event()
            results = []; errors = []

            def run(first):
                db = sqlite3.connect(path, isolation_level=None, timeout=5)
                try:
                    receipts = JobRequestReceipts(db)
                    if not first:
                        second_entered.set()
                    with transaction(db):
                        receipt = receipts.lookup('caller', 'one-intent', self.payload)
                        replayed = receipt is not None
                        if receipt is None:
                            db.execute("UPDATE jobs SET status='leased',attempts=attempts+1,lease_owner='worker',lease_until=?", (at(100),))
                            JobAttempts(db).start('job', 1, synthetic=None, now=at(0))
                            receipt = receipts.record('caller', 'one-intent', self.payload, 'job', now=at(0))
                        if first:
                            ready.set()
                            if not release.wait(5):
                                raise RuntimeError('test did not release first transaction')
                        results.append(receipts.envelope(receipt, now=at(1), replayed=replayed))
                except BaseException as error:
                    errors.append(error)
                finally:
                    db.close()

            first = threading.Thread(target=run, args=(True,))
            second = threading.Thread(target=run, args=(False,))
            first.start()
            try:
                self.assertTrue(ready.wait(5))
                second.start()
                self.assertTrue(second_entered.wait(5))
            finally:
                release.set()
                first.join(5)
                if second.ident is not None:
                    second.join(5)
            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(len(results), 2)
            self.assertEqual(sorted(result['replayed'] for result in results), [False, True])
            self.assertEqual(results[0]['original_response'], results[1]['original_response'])
            checked = sqlite3.connect(path)
            try:
                self.assertEqual(checked.execute('SELECT attempts FROM jobs').fetchone()[0], 1)
                self.assertEqual(checked.execute('SELECT COUNT(*) FROM job_request_receipts').fetchone()[0], 1)
                self.assertEqual(checked.execute('SELECT COUNT(*) FROM job_attempt_events').fetchone()[0], 1)
            finally:
                checked.close()


if __name__ == '__main__':
    unittest.main()
