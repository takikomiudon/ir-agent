"""A worker name cannot authorize a callback from an expired lease generation."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import sqlite3
import unittest
from unittest.mock import patch

from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.store import Store
from test_workflow import source, thesis

NOW = datetime(2026, 10, 10, 3, tzinfo=timezone.utc)


class JobFencingTests(unittest.TestCase):
    def environment(self, kind):
        store = Store(':memory:'); self.addCleanup(store.close)
        harness = Harness(store)
        bundle = {'schema_version': 1,
                  'companies': [{'id': 'c1', 'name': 'Fictional fencing fixture', 'status': 'active'}],
                  'sources': [source('c1', 'c1-baseline'), source('c1', 'c1-new')]}
        if kind == 'research': bundle['theses'] = [thesis()]
        harness.ingest(bundle, now=NOW)
        if kind == 'intake': Intake(store).queue(NOW.isoformat(), now=NOW)
        else: harness.daily(NOW.isoformat(), now=NOW)
        return store, harness

    def result(self, job):
        if job['packet'].get('kind') == 'intake':
            return {'classifications': [{'source_id': saved['id'], 'expected_version': 0, 'kind': 'other',
                        'financial_content': None, 'basis_quote': saved['content'][:8],
                        'rationale': 'Only classify the frozen public text.'} for saved in job['packet']['sources']]}
        updated = deepcopy(job['packet']['thesis'])
        updated.update(version=updated['version'] + 1, recorded_at=(NOW + timedelta(seconds=3)).isoformat(),
                       evidence_ids=[saved['id'] for saved in job['packet']['sources']], next_review_date='2026-10-20')
        return {'summary': 'Completed the frozen research without a new financial assumption.',
                'evidence_ids': updated['evidence_ids'], 'counterarguments': ['The supplied premise remains unproven.'],
                'proposed_action': 'unresolved', 'thesis_update': updated}

    def reclaim(self, harness, old_worker='reused-worker', new_worker='reused-worker'):
        old = harness.claim(old_worker, 1, now=NOW)
        new = harness.claim(new_worker, 60, now=NOW + timedelta(seconds=2))
        self.assertEqual(old['id'], new['id']); self.assertEqual(old['attempts'], 1); self.assertEqual(new['attempts'], 2)
        return old, new

    def renew(self, harness, job, *, worker='reused-worker', moment=None, **kwargs):
        with patch('ir_agent.harness.datetime') as clock:
            clock.now.return_value = moment or NOW + timedelta(seconds=3)
            return harness.renew(job['id'], worker, 90, **kwargs)

    def assert_unapplied(self, store, kind):
        self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM source_classifications').fetchone()[0], 0)
        current = store.thesis('c1')
        if kind == 'research': self.assertEqual(current['version'], 1)
        else: self.assertIsNone(current)

    def test_reused_worker_old_completion_and_completed_retry_cannot_cross_attempts(self):
        for kind in ('research', 'intake'):
            with self.subTest(kind=kind):
                store, harness = self.environment(kind); old, new = self.reclaim(harness)
                value = self.result(old)
                for keywords in ({}, {'expected_attempt': old['attempts']}):
                    with self.assertRaisesRegex(ValueError, 'Stale lease attempt'):
                        harness.complete(old['id'], 'reused-worker', value, now=NOW + timedelta(seconds=3), **keywords)
                    self.assertEqual(store.job(new['id']), new)
                    self.assert_unapplied(store, kind)
                completed = harness.complete(new['id'], 'reused-worker', value, expected_attempt=2,
                                             now=NOW + timedelta(seconds=3))
                for keywords in ({}, {'expected_attempt': 1}):
                    with self.assertRaisesRegex(ValueError, 'Stale lease attempt'):
                        harness.complete(old['id'], 'reused-worker', value, now=NOW + timedelta(seconds=4), **keywords)
                    self.assertEqual(store.job(new['id']), completed)
                self.assertEqual(harness.complete(new['id'], 'reused-worker', value, expected_attempt=2,
                                                 now=NOW + timedelta(seconds=4)), completed)

    def test_reused_worker_old_renewal_is_fenced_and_current_renewal_does_not_increment_attempt(self):
        for kind in ('research', 'intake'):
            with self.subTest(kind=kind):
                store, harness = self.environment(kind); old, new = self.reclaim(harness)
                for keywords in ({}, {'expected_attempt': 1}):
                    with self.assertRaisesRegex(ValueError, 'Stale lease attempt'):
                        self.renew(harness, old, **keywords)
                    self.assertEqual(store.job(new['id']), new)
                renewed = self.renew(harness, new, expected_attempt=2)
                self.assertEqual(renewed['attempts'], 2)
                self.assertEqual(renewed['lease_until'], (NOW + timedelta(seconds=93)).isoformat())

    def test_invalid_explicit_attempts_never_fall_back_to_current_generation(self):
        for kind in ('research', 'intake'):
            store, harness = self.environment(kind); job = harness.claim('reused-worker', now=NOW)
            for invalid in (None, 0, -1, True, False, '1', 1.0, {}, []):
                with self.subTest(kind=kind, expected_attempt=invalid):
                    with self.assertRaises(ValueError):
                        harness.complete(job['id'], 'reused-worker', self.result(job), expected_attempt=invalid,
                                         now=NOW + timedelta(seconds=3))
                    with self.assertRaises(ValueError): self.renew(harness, job, expected_attempt=invalid)
                    self.assertEqual(store.job(job['id']), job)
                    self.assert_unapplied(store, kind)

    def test_omitted_python_token_works_only_for_first_attempt(self):
        for kind in ('research', 'intake'):
            with self.subTest(kind=kind):
                _, harness = self.environment(kind); job = harness.claim('reused-worker', now=NOW)
                self.assertEqual(self.renew(harness, job)['attempts'], 1)
                completed = harness.complete(job['id'], 'reused-worker', self.result(job), now=NOW + timedelta(seconds=3))
                self.assertEqual(completed['status'], 'completed')

    def test_matching_attempt_still_requires_owner_and_unexpired_lease(self):
        for kind in ('research', 'intake'):
            with self.subTest(kind=kind):
                store, harness = self.environment(kind); _, new = self.reclaim(harness, new_worker='replacement')
                value = self.result(new)
                with self.assertRaisesRegex(ValueError, 'lease owner'):
                    harness.complete(new['id'], 'reused-worker', value, expected_attempt=2,
                                     now=NOW + timedelta(seconds=3))
                with self.assertRaisesRegex(ValueError, 'lease owner'):
                    self.renew(harness, new, expected_attempt=2)
                expired = NOW + timedelta(seconds=62)
                with self.assertRaisesRegex(ValueError, 'Lease expired'):
                    harness.complete(new['id'], 'replacement', value, expected_attempt=2, now=expired)
                with self.assertRaisesRegex(ValueError, 'unexpired lease owner'):
                    self.renew(harness, new, worker='replacement', expected_attempt=2, moment=expired)
                self.assertEqual(store.job(new['id']), new)
                self.assert_unapplied(store, kind)

    def test_direct_intake_stale_job_snapshot_cannot_bypass_current_attempt_check(self):
        store, harness = self.environment('intake'); old, new = self.reclaim(harness)
        with self.assertRaisesRegex(ValueError, 'Stale lease attempt'):
            with store.transaction():
                Intake(store).complete(old, 'reused-worker', self.result(old), NOW + timedelta(seconds=3), expected_attempt=1)
        self.assertEqual(store.job(new['id']), new)
        self.assert_unapplied(store, 'intake')

    def test_valid_current_attempt_errors_roll_back_result_thesis_classifications_and_renewal(self):
        for kind in ('research', 'intake'):
            with self.subTest(kind=kind):
                store, harness = self.environment(kind); _, new = self.reclaim(harness)
                store.connection.executescript("""
                    CREATE TRIGGER reject_completion BEFORE UPDATE OF status ON jobs
                    WHEN NEW.status='completed' BEGIN SELECT RAISE(ABORT,'injected completion failure'); END;
                    CREATE TRIGGER reject_renewal BEFORE UPDATE OF lease_until ON jobs
                    BEGIN SELECT RAISE(ABORT,'injected renewal failure'); END;
                """)
                with self.assertRaisesRegex(sqlite3.IntegrityError, 'injected completion failure'):
                    harness.complete(new['id'], 'reused-worker', self.result(new), expected_attempt=2,
                                     now=NOW + timedelta(seconds=3))
                self.assertEqual(store.job(new['id']), new)
                self.assert_unapplied(store, kind)
                with self.assertRaisesRegex(sqlite3.IntegrityError, 'injected renewal failure'):
                    self.renew(harness, new, expected_attempt=2)
                self.assertEqual(store.job(new['id']), new)


if __name__ == '__main__': unittest.main()
