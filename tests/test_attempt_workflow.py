"""Lease journaling must commit with the research/classification it measures."""
from datetime import timedelta
import sqlite3
import unittest
from unittest.mock import patch

import test_job_fencing as fencing


class AttemptWorkflowTests(unittest.TestCase):
    environment = fencing.JobFencingTests.environment
    result = fencing.JobFencingTests.result

    def history(self, store, job):
        from ir_agent.job_attempts import JobAttempts
        return JobAttempts(store.connection).history(job['id'], job['attempts'])

    def renew(self, harness, job):
        with patch('ir_agent.harness.datetime') as clock:
            clock.now.return_value = fencing.NOW + timedelta(seconds=1)
            return harness.renew(job['id'], 'worker', 90, expected_attempt=job['attempts'])

    def test_both_completion_paths_record_start_renew_end_and_retry_adds_nothing(self):
        for kind in ('research', 'intake'):
            with self.subTest(kind=kind):
                store, harness = self.environment(kind)
                job = harness.claim('worker', now=fencing.NOW, measurement_synthetic=True)
                first = self.history(store, job)
                self.assertTrue(first['attempt']['synthetic'])
                self.assertEqual(first['attempt']['measurement_scope'], 'lease_ownership')
                self.renew(harness, job)
                value = self.result(job)
                completed = harness.complete(job['id'], 'worker', value, expected_attempt=job['attempts'],
                                             now=fencing.NOW + timedelta(seconds=3))
                history = self.history(store, job)
                self.assertEqual([e['kind'] for e in history['events']],
                                 ['lease_started', 'lease_renewed', 'completed'])
                self.assertEqual(history['events'][-1]['effective_at'], completed['completed_at'])
                harness.complete(job['id'], 'worker', value, expected_attempt=job['attempts'],
                                 now=fencing.NOW + timedelta(seconds=4))
                self.assertEqual(self.history(store, job), history)

    def test_expiry_keeps_effective_deadline_separate_from_observation_and_new_claim(self):
        store, harness = self.environment('intake')
        old = harness.claim('worker', 1, now=fencing.NOW, measurement_synthetic=True)
        new = harness.claim('worker', 60, now=fencing.NOW + timedelta(seconds=2), measurement_synthetic=True)
        history = self.history(store, old)
        terminal = history['events'][-1]
        self.assertEqual(terminal['kind'], 'lease_expired')
        self.assertEqual(terminal['effective_at'], old['lease_until'])
        self.assertEqual(terminal['observed_at'], (fencing.NOW + timedelta(seconds=2)).isoformat())
        next_history = self.history(store, new)
        self.assertEqual(next_history['attempt']['previous_measured_attempt']['id'], history['attempt']['id'])
        self.assertEqual(len(next_history['events']), 1)
        with self.assertRaisesRegex(ValueError, 'Stale lease attempt'):
            harness.complete(old['id'], 'worker', self.result(old), expected_attempt=old['attempts'],
                             now=fencing.NOW + timedelta(seconds=3))
        self.assertEqual(self.history(store, new), next_history)

    def test_unspecified_measurement_provenance_remains_unknown(self):
        for provenance in (None, True, False):
            store, harness = self.environment('intake')
            job = harness.claim('worker', now=fencing.NOW, measurement_synthetic=provenance)
            self.assertIs(self.history(store, job)['attempt']['synthetic'], provenance)
        store, harness = self.environment('intake')
        for invalid in (0, 1, 'false', {}, []):
            with self.assertRaises(ValueError):
                harness.claim('worker', now=fencing.NOW, measurement_synthetic=invalid)
        self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM job_attempts').fetchone()[0], 0)

    def test_start_failure_rolls_back_claim_header_and_events(self):
        store, harness = self.environment('intake')
        store.connection.executescript("""
            CREATE TRIGGER reject_attempt_start BEFORE INSERT ON job_attempt_events
            WHEN NEW.kind='lease_started' BEGIN SELECT RAISE(ABORT,'injected start failure'); END;
        """)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'injected start failure'):
            harness.claim('worker', now=fencing.NOW)
        self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM job_attempts').fetchone()[0], 0)
        job = dict(store.connection.execute('SELECT * FROM jobs').fetchone())
        self.assertEqual(job['status'], 'pending'); self.assertEqual(job['attempts'], 0)

    def test_terminal_journal_failure_rolls_back_both_results(self):
        for kind in ('research', 'intake'):
            with self.subTest(kind=kind):
                store, harness = self.environment(kind)
                job = harness.claim('worker', now=fencing.NOW)
                before = self.history(store, job)
                store.connection.executescript("""
                    CREATE TRIGGER reject_attempt_end BEFORE INSERT ON job_attempt_events
                    WHEN NEW.kind='completed' BEGIN SELECT RAISE(ABORT,'injected journal failure'); END;
                """)
                with self.assertRaisesRegex(sqlite3.IntegrityError, 'injected journal failure'):
                    harness.complete(job['id'], 'worker', self.result(job), expected_attempt=job['attempts'],
                                     now=fencing.NOW + timedelta(seconds=3))
                self.assertEqual(store.job(job['id']), job)
                self.assertEqual(self.history(store, job), before)
                self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM source_classifications').fetchone()[0], 0)
                if kind == 'research': self.assertEqual(store.thesis('c1')['version'], 1)

    def test_renewal_journal_failure_rolls_back_new_deadline(self):
        store, harness = self.environment('intake')
        job = harness.claim('worker', now=fencing.NOW)
        before = self.history(store, job)
        store.connection.executescript("""
            CREATE TRIGGER reject_attempt_renew BEFORE INSERT ON job_attempt_events
            WHEN NEW.kind='lease_renewed' BEGIN SELECT RAISE(ABORT,'injected renew failure'); END;
        """)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'injected renew failure'):
            self.renew(harness, job)
        self.assertEqual(store.job(job['id']), job)
        self.assertEqual(self.history(store, job), before)

    def test_expiry_journal_failure_preserves_old_generation_and_does_not_claim_again(self):
        store, harness = self.environment('intake')
        job = harness.claim('worker', 1, now=fencing.NOW)
        before = self.history(store, job)
        store.connection.executescript("""
            CREATE TRIGGER reject_attempt_expiry BEFORE INSERT ON job_attempt_events
            WHEN NEW.kind='lease_expired' BEGIN SELECT RAISE(ABORT,'injected expiry failure'); END;
        """)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'injected expiry failure'):
            harness.claim('replacement', now=fencing.NOW + timedelta(seconds=2))
        self.assertEqual(store.job(job['id']), job)
        self.assertEqual(self.history(store, job), before)
        self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM job_attempts').fetchone()[0], 1)

    def test_legacy_lease_completes_without_inventing_a_start(self):
        store, harness = self.environment('intake')
        pending = store.connection.execute('SELECT id FROM jobs').fetchone()['id']
        store.connection.execute("UPDATE jobs SET status='leased',lease_owner='worker',attempts=1,lease_until=? WHERE id=?",
                                 ((fencing.NOW + timedelta(seconds=60)).isoformat(), pending))
        job = store.job(pending)
        self.renew(harness, job)
        harness.complete(job['id'], 'worker', self.result(job), expected_attempt=1,
                         now=fencing.NOW + timedelta(seconds=3))
        self.assertEqual(self.history(store, job)['status'], 'unmeasured')
        self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM job_attempts').fetchone()[0], 0)

    def test_empty_poll_creates_no_measured_attempt(self):
        store, harness = self.environment('intake')
        harness.claim('worker', now=fencing.NOW)
        self.assertIsNone(harness.claim('other-worker', now=fencing.NOW + timedelta(seconds=1)))
        self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM job_attempts').fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()
