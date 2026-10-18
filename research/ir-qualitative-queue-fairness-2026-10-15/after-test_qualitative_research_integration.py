"""Synthetic workflow checks: no live files, network, positions or decisions."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from ir_agent.cli import parser, run
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.job_attempts import JobAttempts
from ir_agent.models import json_text
from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.store import Store
from test_catalyst_schedule import source


def at(minute, second=0):
    return datetime(2026, 10, 15, 10, minute, second, tzinfo=timezone.utc)


class QualitativeIntegrationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.store = Store(':memory:'); self.addCleanup(self.store.close)
        self.harness = Harness(self.store); self.registry = QualitativeResearch(self.store)
        self.harness.ingest({'schema_version': 1, 'companies': [
            {'id': 'jp:TEST', 'name': 'Synthetic qualitative company', 'status': 'watch'}]}, now=at(0))
        self.add_source('A', 0)
        self.ref = self.file('case.json', '{"date":"2027-01-15","issue":"orders"}')
        self.request = {'case_id': 'orders-case', 'company_id': 'jp:TEST', 'issue_id': 'orders',
            'synthetic': True, 'enabled': True, 'recorded_at': at(3).isoformat(),
            'case_ref': self.ref, 'manifest_ref': self.ref, 'management_review': {
                'date': '2027-01-15', 'timezone': 'Asia/Tokyo',
                'basis_ref': self.ref, 'basis_quote': '2027-01-15'}, 'bootstrap_reviews': []}

    def file(self, name, content):
        path = self.root / name; path.write_text(content, encoding='utf-8')
        return {'path': name, 'sha256': sha256(path.read_bytes()).hexdigest()}

    def add_source(self, identity, minute):
        value = source(identity, content='Synthetic order observation ' + identity)
        self.harness.ingest({'schema_version': 1, 'sources': [value]}, now=at(minute))
        Intake(self.store).queue(at(minute).isoformat(), now=at(minute))
        job = self.harness.claim('classifier', now=at(minute, 1), measurement_synthetic=True)
        self.assertEqual(job['packet']['kind'], 'intake')
        self.harness.complete(job['id'], 'classifier', {'classifications': [{
            'source_id': s['id'], 'expected_version': 0, 'kind': 'other', 'financial_content': False,
            'basis_quote': s['content'], 'rationale': 'Synthetic classification only.'}
            for s in job['packet']['sources']]}, now=at(minute, 2))

    def register(self, request=None, version=0, minute=3):
        return self.registry.register_case(request or self.request, version,
                                           research_root=self.root, now=at(minute))

    def queue(self, minute=4):
        return self.registry.queue_cases(['orders-case'], at(minute).isoformat(), now=at(minute))

    def claim(self, minute=5, lease=900):
        return self.harness.claim('reviewer', lease, now=at(minute), measurement_synthetic=True)

    def result(self, job, minute=6):
        packet = job['packet']
        return {'summary': 'Compare evidence, without a numerical forecast.', 'recorded_at': at(minute).isoformat(),
            'source_reviews': [{'source_id': s['id'], 'snapshot_sha256': packet['source_snapshot_sha256'][s['id']],
                'read_state': 'reviewed', 'outcome': 'unresolved', 'basis_quote': s['content'],
                'rationale': 'The observation alone does not establish a future business result.'}
                for s in packet['sources']],
            'case_observation': {'issue_id': 'orders', 'outcome': 'unresolved',
                'rationale': 'Forecast uncertainty remains.', 'evidence_source_ids': packet['pending_source_ids']},
            'management_review_update': {'mode': 'retain'}}

    def complete(self, job, value=None, minute=6, expected_attempt=None):
        return self.harness.complete(job['id'], 'reviewer', value or self.result(job, minute), now=at(minute),
            expected_attempt=expected_attempt or job['attempts'])

    def test_watch_without_thesis_queues_once_completes_and_never_writes_financial_records(self):
        original = deepcopy(self.store.company('jp:TEST'))
        self.register(); self.assertEqual(self.queue()['jobs_created'], 1)
        self.assertEqual(self.queue()['jobs_created'], 0)
        job = self.claim(); self.assertEqual(job['packet']['kind'], 'qualitative_review')
        saved = self.complete(job); self.assertEqual(saved['status'], 'completed')
        self.assertEqual(self.complete(job), saved)
        self.assertEqual(self.queue(7)['jobs_created'], 0)
        self.assertEqual(self.registry.show_case('orders-case')['version'], 2)
        self.assertEqual(self.store.company('jp:TEST'), original)
        for table in ('theses', 'questions', 'replies', 'decision_policies', 'source_reviews'):
            self.assertEqual(self.store.connection.execute('SELECT count(*) FROM ' + table).fetchone()[0], 0)

    def test_arrival_during_lease_is_next_packet_only_and_does_not_repeat_A(self):
        self.register(); self.queue(); old = self.claim()
        self.harness.ingest({'schema_version': 1, 'sources': [source('B', content='New order B')]}, now=at(6))
        Intake(self.store).queue(at(6).isoformat(), now=at(6))
        # Classification also respects the company's existing review lease.
        self.assertIsNone(self.harness.claim('classifier', now=at(6, 1)))
        self.complete(old, self.result(old, 7), minute=7)
        classification = self.harness.claim('classifier', now=at(7, 1))
        self.assertEqual(classification['packet']['kind'], 'intake')
        self.harness.complete(classification['id'], 'classifier', {'classifications': [{
            'source_id': 'B', 'expected_version': 0, 'kind': 'other', 'financial_content': False,
            'basis_quote': 'New order B', 'rationale': 'Synthetic source classification only.'}]}, now=at(7, 2))
        self.assertEqual(self.queue(8)['jobs_created'], 1)
        new = self.claim(9)
        self.assertEqual(new['packet']['pending_source_ids'], ['B'])
        self.assertEqual([s['id'] for s in old['packet']['sources']], ['A'])

    def test_registration_retry_is_immutable_after_progress_and_cannot_restore_old_head(self):
        first = self.register(); self.queue(); self.complete(self.claim())
        again = self.register(minute=7)
        self.assertFalse(again['added']); self.assertEqual(again['version'], first['version'])
        self.assertEqual(again['head_version'], 2)
        changed = deepcopy(self.request); changed['enabled'] = False
        with self.assertRaises(ValueError): self.register(changed, 0, 7)

    def test_new_config_fences_lease_even_when_old_files_are_unchanged(self):
        self.register(); self.queue(); old = self.claim()
        changed = deepcopy(self.request); changed['enabled'] = False
        self.register(changed, 1, 6)
        with self.assertRaises(ValueError): self.complete(old, minute=7)
        self.assertEqual(self.store.job(old['id'])['status'], 'leased')

    def test_changed_file_supersedes_unclaimed_packet(self):
        self.register(); self.queue()
        (self.root / 'case.json').write_text('changed', encoding='utf-8')
        self.assertIsNone(self.claim())
        self.assertEqual(self.store.connection.execute("select count(*) from jobs where status='superseded'").fetchone()[0], 1)

    def test_future_asof_and_case_before_trusted_insert_are_not_available(self):
        self.register()
        with self.assertRaises(ValueError):
            self.registry.queue_cases(['orders-case'], at(5).isoformat(), now=at(4))
        result = self.registry.queue_cases(['orders-case'], at(2).isoformat(), now=at(4))
        self.assertEqual(result['jobs_created'], 0)
        self.assertEqual(result['skipped'][0]['reason'], 'case_saved_after_as_of')

    def test_source_quote_and_complete_coverage_are_required(self):
        self.register(); self.queue(); job = self.claim(); valid = self.result(job)
        mutations = []
        wrong = deepcopy(valid); wrong['source_reviews'][0]['basis_quote'] = 'not present'; mutations.append(wrong)
        wrong = deepcopy(valid); wrong['source_reviews'] = []; mutations.append(wrong)
        wrong = deepcopy(valid); wrong['source_reviews'][0]['read_state'] = 'not_reviewed'; mutations.append(wrong)
        wrong = deepcopy(valid); wrong['valuation'] = {}; mutations.append(wrong)
        for value in mutations:
            with self.subTest(value=value), self.assertRaises(ValueError): self.complete(job, value)
            self.assertEqual(self.registry.show_case('orders-case')['version'], 1)
        self.complete(job, valid)
        wrong = deepcopy(valid); wrong['summary'] = 'changed request'
        with self.assertRaises(ValueError): self.complete(job, wrong, 7)

    def test_expired_generation_cannot_complete_even_with_reused_worker_name(self):
        self.register(); self.queue(); old = self.claim(5, 1)
        new = self.claim(6)
        self.assertEqual(new['attempts'], 2)
        with self.assertRaisesRegex(ValueError, 'Stale lease attempt'):
            self.complete(old, self.result(old, 7), 7, expected_attempt=1)
        self.complete(new, self.result(new, 7), 7, expected_attempt=2)

    def test_journal_failure_rolls_back_case_progress_and_job_completion(self):
        self.register(); self.queue(); job = self.claim()
        with patch.object(JobAttempts, 'complete', side_effect=RuntimeError('injected journal failure')):
            with self.assertRaises(RuntimeError): self.complete(job)
        self.assertEqual(self.registry.show_case('orders-case')['version'], 1)
        self.assertEqual(self.store.job(job['id'])['status'], 'leased')
        self.assertEqual(len(JobAttempts(self.store.connection).history(job['id'], 1)['events']), 1)
        self.complete(job)

    def test_due_review_requires_new_management_and_does_not_repeat_consumed_date(self):
        self.ref = self.file('due.json', '2026-10-15')
        self.request['case_ref'] = self.ref; self.request['manifest_ref'] = self.ref
        self.request['management_review'] = {'date': '2026-10-15', 'timezone': 'Asia/Tokyo',
            'basis_ref': self.ref, 'basis_quote': '2026-10-15'}
        self.register(); self.queue(); job = self.claim()
        with self.assertRaises(ValueError): self.complete(job)
        value = self.result(job); value['management_review_update'] = {'mode': 'unset', 'reason': 'Next date is not yet configured.'}
        self.complete(job, value)
        self.assertEqual(self.queue(7)['jobs_created'], 0)
        self.assertIsNone(self.registry.show_case('orders-case')['record']['management_review'])

    def test_set_management_requires_future_local_date_bound_to_file(self):
        self.register(); self.queue(); job = self.claim(); value = self.result(job)
        ref = self.file('next.json', '2027-01-15')
        value['management_review_update'] = {'mode': 'set', 'management_review': {'date': '2027-01-15',
            'timezone': 'Asia/Tokyo', 'basis_ref': ref, 'basis_quote': '2027-01-15'}}
        self.complete(job, value)
        self.assertEqual(self.queue(7)['jobs_created'], 0)

    def test_bootstrap_requires_source_receipt_and_review_binding(self):
        saved = self.store.source('A'); digest = sha256(json_text(saved).encode()).hexdigest()
        ref = self.file('previous.json', json_text({'source_id': 'A', 'source_snapshot_sha256': digest}))
        self.request['bootstrap_reviews'] = [{'source_id': 'A', 'source_snapshot_sha256': digest,
            'reviewed_at': at(2).isoformat(), 'review_ref': ref}]
        self.register(); self.assertEqual(self.queue()['jobs_created'], 0)
        self.assertFalse(self.registry.show_case('orders-case')['record']['bootstrap_meaning_verified'])

    def test_bootstrap_cannot_backdate_before_classification(self):
        saved = self.store.source('A'); digest = sha256(json_text(saved).encode()).hexdigest()
        ref = self.file('previous.json', 'A ' + digest)
        self.request['bootstrap_reviews'] = [{'source_id': 'A', 'source_snapshot_sha256': digest,
            'reviewed_at': at(0, 1).isoformat(), 'review_ref': ref}]
        with self.assertRaises(ValueError): self.register()
        self.assertIsNone(self.registry._row('orders-case'))

    def test_unknown_kind_does_not_fall_through_to_financial_thesis_processing(self):
        self.register(); self.queue(); row = self.store.connection.execute("select id,packet from jobs where status='pending'").fetchone()
        packet = json.loads(row['packet']); packet['kind'] = 'unknown'
        self.store.connection.execute('update jobs set packet=? where id=?', (json_text(packet), row['id']))
        self.assertIsNone(self.claim())
        with self.assertRaisesRegex(ValueError, 'Unknown research job kind'):
            self.harness.complete(row['id'], 'reviewer', {}, now=at(6))

    def test_CLI_registration_queue_and_show_use_the_same_versioned_store(self):
        request_file = self.root / 'register.json'; request_file.write_text(json_text(self.request))
        with patch('ir_agent.cli.now_iso', return_value=at(3).isoformat()):
            registered = run(parser().parse_args(['qualitative', 'register', str(request_file),
                '--expected-version', '0', '--research-root', str(self.root)]), self.store)
        with patch('ir_agent.cli.now_iso', return_value=at(4).isoformat()):
            queued = run(parser().parse_args(['qualitative', 'queue', '--case-id', 'orders-case']), self.store)
        self.assertEqual(registered['version'], 1); self.assertEqual(queued['jobs_created'], 1)
        shown = run(parser().parse_args(['qualitative', 'show', 'orders-case', '--version', '1']), self.store)
        self.assertEqual(shown['record'], registered['record'])

    def test_CLI_fails_closed_for_future_cutoff_and_stale_CAS(self):
        self.register()
        with patch('ir_agent.cli.now_iso', return_value=at(4).isoformat()):
            with self.assertRaises(ValueError):
                run(parser().parse_args(['qualitative', 'queue', '--case-id', 'orders-case',
                    '--as-of', at(5).isoformat()]), self.store)
        self.assertEqual(self.store.connection.execute("select count(*) from jobs where status='pending'").fetchone()[0], 0)

    def test_queue_limit_counts_new_jobs_and_does_not_starve_later_cases(self):
        self.register()
        second = deepcopy(self.request)
        second.update(case_id='z-second-case', issue_id='second-issue')
        self.registry.register_case(second, research_root=self.root, now=at(3))
        ids = ['orders-case', 'z-second-case']
        first = self.registry.queue_cases(ids, at(4).isoformat(), limit=1, now=at(4))
        self.assertEqual(first['jobs_created'], 1)
        self.assertEqual(first['deferred_count'], 1)
        second = self.registry.queue_cases(ids, at(5).isoformat(), limit=1, now=at(5))
        self.assertEqual(second['jobs_created'], 1)
        self.assertEqual(second['selected'][0]['case_id'], 'z-second-case')
        self.assertEqual(second['deferred_count'], 0)
        self.assertEqual(second['skipped'][0]['reason'], 'same_trigger_already_queued')
        third = self.registry.queue_cases(ids, at(6).isoformat(), limit=1, now=at(6))
        self.assertEqual(third['jobs_created'], 0)
        self.assertEqual(third['deferred_count'], 0)
        self.assertEqual(len(third['skipped']), 2)


if __name__ == '__main__':
    unittest.main()
