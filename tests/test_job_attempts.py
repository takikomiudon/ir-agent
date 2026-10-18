import json
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from ir_agent.job_attempts import JobAttempts, SCHEMA
from ir_agent.models import json_text


class JobAttemptTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
            CREATE TABLE jobs (
                id TEXT PRIMARY KEY, company_id TEXT, packet TEXT, lease_owner TEXT,
                lease_until TEXT, attempts INTEGER, status TEXT, result TEXT, completed_at TEXT
            );
        ''' + SCHEMA)
        self.clock = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.packet = {'company': {'id': 'issuer'}, 'thesis': {'version': 1}, 'sources': []}
        self.db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)',
                        ('job', 'issuer', json_text(self.packet), 'worker', self.at(100), 1,
                         'leased', None, None))
        self.journal = JobAttempts(self.db)

    def tearDown(self):
        self.db.close()

    def at(self, seconds):
        return (self.clock + timedelta(seconds=seconds)).isoformat()

    def start(self, **updates):
        values = {'synthetic': None, 'now': self.at(0)}
        values.update(updates)
        return self.journal.start('job', 1, **values)

    def set_deadline(self, seconds):
        self.db.execute('UPDATE jobs SET lease_until=? WHERE id=?', (self.at(seconds), 'job'))

    def finish_job(self, seconds):
        result = {'summary': 'saved result', 'evidence': []}
        self.db.execute('UPDATE jobs SET status=?,result=?,completed_at=? WHERE id=?',
                        ('completed', json_text(result), self.at(seconds), 'job'))
        return result

    def event_count(self):
        return self.db.execute('SELECT COUNT(*) FROM job_attempt_events').fetchone()[0]

    def test_start_freezes_saved_identity_and_scope_without_usage(self):
        result = self.start(worker_session_id='session')
        header, event = result['attempt'], result['event']
        self.assertTrue(result['added'])
        self.assertEqual(header['company_id'], 'issuer')
        self.assertEqual(header['worker_id'], 'worker')
        self.assertEqual(header['worker_session_id'], 'session')
        self.assertEqual(header['generation'], 1)
        self.assertEqual(header['job_kind'], 'research')
        self.assertIsNone(header['stage'])
        self.assertIsNone(header['synthetic'])
        self.assertIsNone(header['previous_measured_attempt'])
        self.assertEqual(header['packet_sha256'], sha256(json_text(self.packet).encode()).hexdigest())
        self.assertEqual(header['measurement_scope'], 'lease_ownership')
        self.assertEqual(event['kind'], 'lease_started')
        self.assertEqual(event['sequence'], 1)
        self.assertEqual(event['payload'], {'lease_until': self.at(100)})
        self.assertTrue(event['normal_interval'])
        self.assertEqual(event['clock_issues'], [])
        for name in ('active_seconds', 'tokens', 'cost'):
            self.assertNotIn(name, header)
            self.assertNotIn(name, event)

    def test_synthetic_must_be_explicit_and_does_not_come_from_packet(self):
        packet = {'kind': 'intake', 'stage': 'source_classification', 'synthetic': True}
        self.db.execute('UPDATE jobs SET packet=?', (json_text(packet),))
        with self.assertRaises(TypeError):
            self.journal.start('job', 1, now=self.at(0))
        for wrong in (0, 1, 'false', [], {}):
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                self.start(synthetic=wrong)
        measured = self.start(synthetic=None)['attempt']
        self.assertIsNone(measured['synthetic'])
        self.assertEqual(measured['job_kind'], 'intake')
        self.assertEqual(measured['stage'], 'source_classification')
        self.assertIsNone(measured['worker_session_id'])
        with self.assertRaises(ValueError):
            self.start(synthetic=False)

    def test_explicit_observed_and_synthetic_are_preserved(self):
        for value in (False, True):
            with self.subTest(value=value):
                self.db.execute('DELETE FROM job_attempt_events')
                self.db.execute('DELETE FROM job_attempts')
                self.assertIs(self.start(synthetic=value)['attempt']['synthetic'], value)

    def test_unknown_packet_kind_and_stage_are_not_full_research(self):
        self.db.execute('UPDATE jobs SET packet=?', (json_text({'sources': []}),))
        header = self.start()['attempt']
        self.assertIsNone(header['job_kind'])
        self.assertIsNone(header['stage'])

    def test_start_retry_returns_original_time_and_adds_no_event(self):
        first = self.start()
        self.finish_job(10)
        retry = self.start(now=self.at(50))
        self.assertFalse(retry['added'])
        self.assertEqual(first['attempt'], retry['attempt'])
        self.assertEqual(first['event'], retry['event'])
        self.assertEqual(self.event_count(), 1)
        with self.assertRaises(ValueError):
            self.start(worker_session_id='different')

    def test_only_current_unexpired_successful_claim_can_start(self):
        with self.assertRaises(ValueError):
            self.journal.start('job', 2, synthetic=None, now=self.at(0))
        with self.assertRaises(ValueError):
            self.start(now=self.at(100))
        self.db.execute("UPDATE jobs SET status='pending'")
        with self.assertRaises(ValueError):
            self.start()
        self.assertEqual(self.event_count(), 0)

    def test_legacy_operations_remain_unmeasured_even_with_zero_sequence(self):
        original = self.db.execute('SELECT * FROM jobs').fetchone()
        results = [self.journal.history('job', 1),
                   self.journal.renew('job', 1, expected_sequence=0, lease_until=self.at(100), now=self.at(5)),
                   self.journal.complete('job', 1, expected_sequence=0, now=self.at(5)),
                   self.journal.expire('job', 1, expected_sequence=0, now=self.at(105))]
        for result in results:
            self.assertEqual(result['status'], 'unmeasured')
            self.assertEqual(result['reason_codes'], ['attempt_start_not_measured'])
        self.assertEqual(tuple(original), tuple(self.db.execute('SELECT * FROM jobs').fetchone()))
        self.assertEqual(self.event_count(), 0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM job_attempts').fetchone()[0], 0)

    def test_renew_reads_previous_deadline_and_checks_saved_new_deadline(self):
        self.start()
        self.set_deadline(200)
        with self.assertRaises(ValueError):
            self.journal.renew('job', 1, expected_sequence=1, lease_until=self.at(201), now=self.at(10))
        updated = self.journal.renew('job', 1, expected_sequence=1, lease_until=self.at(200), now=self.at(10))
        self.assertEqual(updated['event']['payload'],
                         {'previous_lease_until': self.at(100), 'lease_until': self.at(200)})
        self.assertEqual(updated['event']['sequence'], 2)
        self.assertEqual(updated['attempt']['started_at'], self.at(0))
        self.assertEqual(self.event_count(), 2)

    def test_renew_can_record_a_shorter_still_live_deadline(self):
        self.start()
        self.set_deadline(50)
        result = self.journal.renew('job', 1, expected_sequence=1, lease_until=self.at(50), now=self.at(10))
        self.assertEqual(result['event']['payload']['previous_lease_until'], self.at(100))
        self.assertEqual(result['event']['payload']['lease_until'], self.at(50))

    def test_stale_same_request_retry_is_legal_after_later_events(self):
        self.start()
        self.set_deadline(200)
        first = self.journal.renew('job', 1, expected_sequence=1, lease_until=self.at(200), now=self.at(10))
        self.set_deadline(300)
        self.journal.renew('job', 1, expected_sequence=2, lease_until=self.at(300), now=self.at(20))
        retry = self.journal.renew('job', 1, expected_sequence=1, lease_until=self.at(200), now=self.at(500))
        self.assertFalse(retry['added'])
        self.assertEqual(retry['event'], first['event'])
        self.assertEqual(self.event_count(), 3)
        with self.assertRaises(ValueError):
            self.journal.renew('job', 1, expected_sequence=1, lease_until=self.at(300), now=self.at(25))
        with self.assertRaises(ValueError):
            self.journal.complete('job', 1, expected_sequence=1, now=self.at(25))
        with self.assertRaises(ValueError):
            self.journal.renew('job', 1, expected_sequence=4, lease_until=self.at(300), now=self.at(25))

    def test_same_worker_new_generation_cannot_close_or_renew_old_attempt(self):
        self.start()
        self.db.execute('UPDATE jobs SET attempts=2,lease_until=?', (self.at(300),))
        with self.assertRaises(ValueError):
            self.journal.renew('job', 1, expected_sequence=1, lease_until=self.at(300), now=self.at(110))
        self.finish_job(120)
        with self.assertRaises(ValueError):
            self.journal.complete('job', 1, expected_sequence=1, now=self.at(120))
        self.assertEqual(self.event_count(), 1)

    def test_complete_derives_result_hash_once_and_is_terminal(self):
        self.start()
        saved = self.finish_job(20)
        first = self.journal.complete('job', 1, expected_sequence=1, now=self.at(21))
        event = first['event']
        self.assertEqual(event['kind'], 'completed')
        self.assertEqual(event['effective_at'], self.at(20))
        self.assertEqual(event['observed_at'], self.at(21))
        self.assertEqual(event['payload']['result_sha256'], sha256(json_text(saved).encode()).hexdigest())
        retry = self.journal.complete('job', 1, expected_sequence=1, now=self.at(30))
        self.assertFalse(retry['added'])
        self.assertEqual(retry['event'], event)
        with self.assertRaises(ValueError):
            self.journal.complete('job', 1, expected_sequence=2, now=self.at(30))
        with self.assertRaises(ValueError):
            self.journal.expire('job', 1, expected_sequence=2, now=self.at(110))
        self.assertEqual(self.event_count(), 2)

    def test_complete_requires_saved_result_and_nonexpired_completion(self):
        self.start()
        with self.assertRaises(ValueError):
            self.journal.complete('job', 1, expected_sequence=1, now=self.at(20))
        self.db.execute("UPDATE jobs SET status='completed',completed_at=?", (self.at(20),))
        with self.assertRaises(ValueError):
            self.journal.complete('job', 1, expected_sequence=1, now=self.at(20))
        self.finish_job(100)
        with self.assertRaises(ValueError):
            self.journal.complete('job', 1, expected_sequence=1, now=self.at(100))
        self.assertEqual(self.event_count(), 1)

    def test_expiry_separates_deadline_from_later_observation_and_retry(self):
        self.start()
        with self.assertRaises(ValueError):
            self.journal.expire('job', 1, expected_sequence=1, now=self.at(99))
        first = self.journal.expire('job', 1, expected_sequence=1, now=self.at(120))
        event = first['event']
        self.assertEqual(event['effective_at'], self.at(100))
        self.assertEqual(event['observed_at'], self.at(120))
        self.assertEqual(event['first_saved_at'], self.at(120))
        self.assertTrue(event['normal_interval'])
        self.db.execute("UPDATE jobs SET status='pending',lease_owner=NULL,lease_until=NULL")
        retry = self.journal.expire('job', 1, expected_sequence=1, now=self.at(130))
        self.assertEqual(retry['event'], event)
        self.assertFalse(retry['added'])
        self.assertEqual(self.event_count(), 2)

    def test_reacquisition_references_only_measured_previous_generation(self):
        first = self.start()['attempt']
        self.journal.expire('job', 1, expected_sequence=1, now=self.at(100))
        self.db.execute('UPDATE jobs SET attempts=4,lease_owner=?,lease_until=?', ('worker-2', self.at(300)))
        result = self.journal.start('job', 4, synthetic=False, now=self.at(110))
        self.assertEqual(result['attempt']['previous_measured_attempt'], {'id': first['id'], 'generation': 1})
        self.assertEqual(result['attempt']['worker_id'], 'worker-2')
        self.assertEqual(self.journal.history('job', 2)['status'], 'unmeasured')
        self.assertEqual(self.journal.history('job', 3)['status'], 'unmeasured')

    def test_changed_worker_company_or_packet_does_not_append(self):
        self.start()
        for field, changed, original in [('lease_owner', 'other-worker', 'worker'),
                                         ('company_id', 'other-issuer', 'issuer'),
                                         ('packet', json_text({'changed': True}), json_text(self.packet))]:
            with self.subTest(field=field):
                self.db.execute('UPDATE jobs SET ' + field + '=?', (changed,))
                with self.assertRaises(ValueError):
                    self.journal.expire('job', 1, expected_sequence=1, now=self.at(110))
                self.db.execute('UPDATE jobs SET ' + field + '=?', (original,))
        self.assertEqual(self.event_count(), 1)

    def test_unrecorded_renewal_drift_does_not_look_like_a_normal_completion(self):
        self.start()
        self.set_deadline(200)
        self.finish_job(50)
        with self.assertRaises(ValueError):
            self.journal.complete('job', 1, expected_sequence=1, now=self.at(50))
        self.assertEqual(self.event_count(), 1)

    def test_clock_rollback_preserves_original_times_and_taints_later_interval(self):
        self.start(now=self.at(10))
        self.set_deadline(200)
        renewal = self.journal.renew('job', 1, expected_sequence=1, lease_until=self.at(200), now=self.at(5))
        self.assertEqual(renewal['event']['observed_at'], self.at(5))
        self.assertEqual(renewal['event']['first_saved_at'], self.at(5))
        self.assertFalse(renewal['event']['normal_interval'])
        self.assertIn('wall_clock_before_attempt_start', renewal['event']['clock_issues'])
        self.finish_job(50)
        completed = self.journal.complete('job', 1, expected_sequence=2, now=self.at(50))
        self.assertFalse(completed['event']['normal_interval'])
        self.assertEqual(completed['event']['clock_issues'], renewal['event']['clock_issues'])

    def test_completion_before_start_is_saved_as_abnormal_not_clamped(self):
        self.start(now=self.at(10))
        self.finish_job(5)
        result = self.journal.complete('job', 1, expected_sequence=1, now=self.at(6))
        self.assertEqual(result['event']['effective_at'], self.at(5))
        self.assertFalse(result['event']['normal_interval'])
        self.assertIn('terminal_time_before_attempt_start', result['event']['clock_issues'])

    def test_future_effective_completion_is_abnormal_not_a_clean_interval(self):
        self.start()
        self.finish_job(50)
        result = self.journal.complete('job', 1, expected_sequence=1, now=self.at(40))
        self.assertEqual(result['event']['effective_at'], self.at(50))
        self.assertFalse(result['event']['normal_interval'])
        self.assertIn('effective_time_after_observation', result['event']['clock_issues'])

    def test_aware_datetime_is_supported_and_naive_clock_is_rejected(self):
        result = self.start(now=self.clock)
        self.assertEqual(result['event']['observed_at'], self.at(0))
        with self.assertRaises(ValueError):
            self.start(now=datetime(2026, 1, 1))

    def test_helpers_do_not_commit_outer_start_or_completion(self):
        self.db.execute('BEGIN IMMEDIATE')
        self.start()
        self.assertTrue(self.db.in_transaction)
        self.db.execute('ROLLBACK')
        self.assertEqual(self.journal.history('job', 1)['status'], 'unmeasured')
        self.start()
        self.db.execute('BEGIN IMMEDIATE')
        self.finish_job(20)
        self.journal.complete('job', 1, expected_sequence=1, now=self.at(20))
        self.assertTrue(self.db.in_transaction)
        self.db.execute('ROLLBACK')
        self.assertEqual(self.event_count(), 1)
        self.assertEqual(self.db.execute('SELECT status FROM jobs').fetchone()[0], 'leased')

    def test_event_insert_failure_rolls_back_header_and_keeps_outer_transaction(self):
        self.db.executescript("""CREATE TRIGGER reject_measurement BEFORE INSERT ON job_attempt_events
            BEGIN SELECT RAISE(ABORT, 'measurement unavailable'); END;""")
        self.db.execute('BEGIN IMMEDIATE')
        self.db.execute("UPDATE jobs SET lease_owner='outer-worker'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.start()
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM job_attempts').fetchone()[0], 0)
        self.assertEqual(self.db.execute('SELECT lease_owner FROM jobs').fetchone()[0], 'outer-worker')
        self.db.execute('ROLLBACK')
        self.assertEqual(self.db.execute('SELECT lease_owner FROM jobs').fetchone()[0], 'worker')

    def test_bad_sequence_unknown_job_and_boolean_generation_are_rejected(self):
        self.start()
        for sequence in (-1, True, '1'):
            with self.subTest(sequence=sequence), self.assertRaises(ValueError):
                self.journal.expire('job', 1, expected_sequence=sequence, now=self.at(110))
        with self.assertRaises(ValueError):
            self.journal.start('missing', 1, synthetic=None, now=self.at(0))
        with self.assertRaises(ValueError):
            self.journal.history('job', True)
        with self.assertRaises(ValueError):
            self.journal.complete('job', 1, expected_sequence=0, now=self.at(20))
        self.assertEqual(self.event_count(), 1)


if __name__ == '__main__':
    unittest.main()
