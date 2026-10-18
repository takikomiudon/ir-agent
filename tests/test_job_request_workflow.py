"""Lost claim/renew responses must not repeat lease mutations."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import test_job_fencing as fixtures
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.store import Store
from test_workflow import source


class JobRequestWorkflowTests(unittest.TestCase):
    environment = fixtures.JobFencingTests.environment
    result = fixtures.JobFencingTests.result

    def claim(self, harness, identity='poll-1', *, seconds=60, moment=None, **kwargs):
        return harness.claim('worker', seconds, now=moment or fixtures.NOW,
                             measurement_synthetic=True, request_id=identity, caller_namespace='test-runner', **kwargs)

    def snapshot(self, store):
        return '\n'.join(store.connection.iterdump())

    def add_company(self, harness, identity='c2', *, now=None):
        now = now or fixtures.NOW
        harness.ingest({'schema_version': 1, 'companies': [{'id': identity, 'name': 'Fictional queued company'}],
                        'sources': [source(identity, identity+'-public')]}, now=now)
        Intake(harness.store).queue(now.isoformat(), now=now)

    def test_claim_retry_returns_one_grant_without_claiming_another_company(self):
        store, harness = self.environment('intake'); self.add_company(harness)
        first = self.claim(harness)
        before = self.snapshot(store)
        replay = self.claim(harness, moment=fixtures.NOW+timedelta(seconds=2))
        self.assertTrue(replay['replayed']); self.assertFalse(first['replayed'])
        self.assertEqual(replay['original_response'], first['original_response'])
        self.assertTrue(replay['current_lease']['valid_now'])
        self.assertEqual(self.snapshot(store), before)
        self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM jobs WHERE status='leased'").fetchone()[0], 1)
        self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM job_attempt_events').fetchone()[0], 1)
        next_poll = self.claim(harness, 'poll-2', moment=fixtures.NOW+timedelta(seconds=3))
        self.assertNotEqual(next_poll['original_response']['job_id'], first['original_response']['job_id'])

    def test_no_job_result_stays_null_until_a_new_poll_id(self):
        store = Store(':memory:'); self.addCleanup(store.close); harness = Harness(store)
        first = self.claim(harness)
        self.assertIsNone(first['original_response']); self.assertIsNone(first['current_lease'])
        self.add_company(harness, now=fixtures.NOW+timedelta(seconds=1))
        before = self.snapshot(store)
        replay = self.claim(harness, moment=fixtures.NOW+timedelta(seconds=2))
        self.assertIsNone(replay['original_response']); self.assertTrue(replay['replayed'])
        self.assertEqual(self.snapshot(store), before)
        granted = self.claim(harness, 'new-poll', moment=fixtures.NOW+timedelta(seconds=3))
        self.assertIsNotNone(granted['original_response'])

    def test_expired_and_reclaimed_replays_never_cleanup_or_grant_again(self):
        store, harness = self.environment('intake')
        original = self.claim(harness, seconds=1)
        before = self.snapshot(store)
        expired = self.claim(harness, seconds=1, moment=fixtures.NOW+timedelta(seconds=2))
        self.assertFalse(expired['current_lease']['valid_now'])
        self.assertEqual(expired['current_lease']['status'], 'expired')
        self.assertEqual(self.snapshot(store), before)
        new = self.claim(harness, 'reclaim', moment=fixtures.NOW+timedelta(seconds=2))
        self.assertEqual(new['original_response']['generation'], 2)
        before = self.snapshot(store)
        replay = self.claim(harness, seconds=1, moment=fixtures.NOW+timedelta(seconds=3))
        self.assertEqual(replay['original_response'], original['original_response'])
        self.assertEqual(replay['current_lease']['status'], 'reclaimed')
        self.assertFalse(replay['current_lease']['valid_now'])
        self.assertEqual(self.snapshot(store), before)

    def test_completed_replay_preserves_original_response_and_result(self):
        store, harness = self.environment('intake')
        granted = self.claim(harness)
        original = granted['original_response']; job = store.job(original['job_id'])
        harness.complete(job['id'], 'worker', self.result(job), expected_attempt=original['generation'],
                         now=fixtures.NOW+timedelta(seconds=3))
        before = self.snapshot(store)
        replay = self.claim(harness, moment=fixtures.NOW+timedelta(seconds=4))
        self.assertEqual(replay['original_response'], original)
        self.assertEqual(replay['current_lease']['status'], 'completed')
        self.assertFalse(replay['current_lease']['valid_now'])
        self.assertEqual(self.snapshot(store), before)

    def test_renew_retry_keeps_first_deadline_and_does_not_repeat_an_event(self):
        store, harness = self.environment('intake'); job = harness.claim('worker', now=fixtures.NOW)
        options = {'expected_attempt': job['attempts'], 'caller_namespace': 'test-runner'}
        first = harness.renew(job['id'], 'worker', 90, request_id='extend-1',
                              now=fixtures.NOW+timedelta(seconds=1), **options)
        before = self.snapshot(store)
        replay = harness.renew(job['id'], 'worker', 90, request_id='extend-1',
                               now=fixtures.NOW+timedelta(seconds=5), **options)
        self.assertEqual(replay['original_response'], first['original_response'])
        self.assertEqual(self.snapshot(store), before)
        newer = harness.renew(job['id'], 'worker', 90, request_id='extend-2',
                              now=fixtures.NOW+timedelta(seconds=10), **options)
        self.assertNotEqual(newer['original_response']['lease_until'], first['original_response']['lease_until'])
        before = self.snapshot(store)
        old = harness.renew(job['id'], 'worker', 90, request_id='extend-1',
                            now=fixtures.NOW+timedelta(seconds=11), **options)
        self.assertEqual(old['original_response'], first['original_response'])
        self.assertEqual(old['current_lease']['lease_until'], newer['original_response']['lease_until'])
        self.assertEqual(self.snapshot(store), before)
        self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM job_attempt_events WHERE kind='lease_renewed'").fetchone()[0], 2)

    def test_mismatch_and_partial_identity_are_rejected_before_job_changes(self):
        store, harness = self.environment('intake'); self.claim(harness)
        before = self.snapshot(store)
        with self.assertRaises(ValueError): self.claim(harness, seconds=61)
        with self.assertRaises(ValueError):
            harness.claim('different-worker', request_id='poll-1', caller_namespace='test-runner',
                           measurement_synthetic=True, lease_seconds=60, now=fixtures.NOW)
        job_id = store.connection.execute('SELECT id FROM jobs').fetchone()[0]
        with self.assertRaises(ValueError):
            harness.renew(job_id, 'worker', request_id='poll-1', caller_namespace='test-runner', now=fixtures.NOW)
        with self.assertRaises(ValueError): harness.claim('worker', request_id='partial', now=fixtures.NOW)
        with self.assertRaises(ValueError): harness.claim('worker', caller_namespace='partial', now=fixtures.NOW)
        self.assertEqual(self.snapshot(store), before)

    def test_receipt_failure_and_outer_rollback_revert_job_events_and_receipts(self):
        store, harness = self.environment('intake')
        before = self.snapshot(store)
        with self.assertRaisesRegex(ValueError, 'outer rollback'):
            with store.transaction():
                granted = self.claim(harness)
                harness.renew(granted['original_response']['job_id'], 'worker', 90,
                    expected_attempt=granted['original_response']['generation'], request_id='extend',
                    caller_namespace='test-runner', now=fixtures.NOW+timedelta(seconds=1))
                raise ValueError('outer rollback')
        self.assertEqual(self.snapshot(store), before)
        store.connection.execute("CREATE TRIGGER reject_receipt BEFORE INSERT ON job_request_receipts "
                                 "BEGIN SELECT RAISE(ABORT,'receipt failure'); END")
        before = self.snapshot(store)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'receipt failure'): self.claim(harness)
        self.assertEqual(self.snapshot(store), before)
        job = harness.claim('worker', now=fixtures.NOW)
        before = self.snapshot(store)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'receipt failure'):
            harness.renew(job['id'], 'worker', 90, request_id='extend', caller_namespace='test-runner',
                          expected_attempt=job['attempts'], now=fixtures.NOW+timedelta(seconds=1))
        self.assertEqual(self.snapshot(store), before)

    def test_concurrent_same_request_serializes_one_claim_across_connections(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'requests.sqlite3'
            store = Store(path); harness = Harness(store)
            self.add_company(harness, 'first'); self.add_company(harness, 'second'); store.close()

            def perform():
                local = Store(path)
                try: return self.claim(Harness(local))
                finally: local.close()

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: perform(), range(2)))
            self.assertEqual(results[0]['original_response'], results[1]['original_response'])
            self.assertEqual(sum(result['replayed'] is False for result in results), 1)
            store = Store(path); self.addCleanup(store.close)
            self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM job_request_receipts').fetchone()[0], 1)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM jobs WHERE status='leased'").fetchone()[0], 1)
            self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM job_attempt_events').fetchone()[0], 1)

    def test_runtime_clock_is_sampled_after_acquiring_writer_for_claim_and_renew(self):
        for operation in ('claim', 'renew'):
            with self.subTest(operation=operation):
                store, harness = self.environment('intake')
                job = harness.claim('worker', now=fixtures.NOW) if operation == 'renew' else None
                original_write = store._record_write
                acquired = False

                @contextmanager
                def delayed_writer():
                    nonlocal acquired
                    with original_write():
                        acquired = True
                        yield

                grant_time = fixtures.NOW + timedelta(seconds=2)
                with patch.object(store, '_record_write', delayed_writer), \
                        patch('ir_agent.harness.datetime', wraps=datetime) as clock:
                    clock.now.side_effect = lambda *_: grant_time if acquired else fixtures.NOW
                    options = {'request_id': operation+'-after-wait', 'caller_namespace': 'test-runner'}
                    if operation == 'claim':
                        response = harness.claim('worker', 60, measurement_synthetic=True, **options)
                    else:
                        response = harness.renew(job['id'], 'worker', 60,
                                                 expected_attempt=job['attempts'], **options)
                self.assertEqual(response['original_response']['lease_until'],
                                 (grant_time+timedelta(seconds=60)).isoformat())
                self.assertEqual(response['current_lease']['observed_at'], grant_time.isoformat())


if __name__ == '__main__':
    unittest.main()
