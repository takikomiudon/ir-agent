"""Source-only intake preserves evidence and never invents a financial model."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import sqlite3
import unittest

from ir_agent.harness import Harness
from ir_agent.intake import Intake, SCHEMA, classifications
from ir_agent.store import Store

ROOT = Path(__file__).resolve().parents[1]
AS_OF = '2026-10-09T10:00:00+09:00'


def at(value):
    return datetime.fromisoformat(value)


def source(identifier, content='決算説明資料。売上高と費用の説明。', **updates):
    value = {'id': identifier, 'company_id': 'no-model', 'title': identifier,
             'url': 'https://example.invalid/' + identifier, 'content': content,
             'source_type': 'public_disclosure', 'published_at': '2026-10-09T09:00:00+09:00',
             'retrieved_at': '2026-10-09T09:50:00+09:00'}
    value.update(updates)
    return value


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(':memory:'); self.addCleanup(self.store.close)
        self.store.connection.executescript(SCHEMA)
        self.harness = Harness(self.store); self.intake = Intake(self.store)
        self.harness.ingest({'schema_version': 1, 'companies': [{'id': 'no-model', 'name': 'No numerical model'}],
                             'sources': [source('doc-a'), source('doc-b', '次回の決算発表予定日について。')]},
                            now=at('2026-10-09T09:55:00+09:00'))
        self.original_company = self.store.company('no-model')
        self.original_sources = self.store.sources('no-model')

    def queue(self, **kwargs):
        return self.intake.queue(AS_OF, now=at(AS_OF), **kwargs)

    def claim(self, worker='classifier', stamp='2026-10-09T10:01:00+09:00', lease_seconds=900):
        return self.harness.claim(worker, lease_seconds, now=at(stamp))

    def result(self, job):
        return {'classifications': [{'source_id': saved['id'], 'expected_version': 0,
                                    'kind': 'other', 'financial_content': None,
                                    'basis_quote': saved['content'][:8], 'rationale': 'Classify the saved text only; numerical inputs need separate verification.'}
                                   for saved in job['packet']['sources']]}

    def complete(self, job, result=None, worker='classifier', stamp='2026-10-09T10:02:00+09:00'):
        return self.harness.complete(job['id'], worker, result or self.result(job),
                                     expected_attempt=job['attempts'], now=at(stamp))

    def classification_count(self):
        return self.store.connection.execute('SELECT COUNT(*) FROM source_classifications').fetchone()[0]

    def test_watch_company_without_thesis_can_classify_and_preserves_all_original_state(self):
        queued = self.queue(); selected = queued['selected'][0]
        self.assertEqual(self.queue()['selected'][0]['job_id'], selected['job_id'])
        self.assertEqual(selected['source_count'], 2)
        job = self.claim()
        self.assertEqual(job['packet']['kind'], 'intake')
        self.assertFalse(job['packet']['inputs_verified'])
        self.assertNotIn('thesis', job['packet'])
        result = self.result(job)
        result['classifications'][0].update(kind='earnings_presentation', financial_content=True)
        completed = self.complete(job, result)
        self.assertEqual(completed['status'], 'completed')
        self.assertEqual(self.complete(job, result), completed)
        self.assertFalse(completed['result']['inputs_verified'])
        self.assertTrue(all(not item['inputs_verified'] for item in completed['result']['classifications']))
        self.assertIsNone(self.store.thesis('no-model'))
        self.assertEqual(self.store.company('no-model'), self.original_company)
        self.assertEqual(self.store.sources('no-model'), self.original_sources)
        self.assertEqual(self.intake.queue('2026-10-09T10:03:00+09:00', now=at('2026-10-09T10:03:00+09:00'))['selected'], [])
        self.assertEqual(classifications(self.store, 'doc-a', as_of='2026-10-09T10:01:59+09:00'), [])
        self.assertEqual(len(classifications(self.store, 'doc-a', as_of='2026-10-09T10:02:00+09:00')), 1)

    def test_classifications_require_complete_verbatim_validated_cas_inputs(self):
        self.queue(); job = self.claim()
        variants = []
        for field, bad in [('kind', 'buy'), ('kind', []), ('financial_content', 1), ('expected_version', 1),
                           ('basis_quote', 'Never present in this source')]:
            value = self.result(job); value['classifications'][0][field] = bad; variants.append(value)
        value = self.result(job); value['classifications'].pop(); variants.append(value)
        value = self.result(job); value['classifications'].append(deepcopy(value['classifications'][0])); variants.append(value)
        value = self.result(job); value['classifications'][0]['inputs_verified'] = True; variants.append(value)
        value = self.result(job); value['thesis_update'] = {'version': 1}; variants.append(value)
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.complete(job, value)
            self.assertEqual(self.classification_count(), 0)
            self.assertEqual(self.store.job(job['id'])['status'], 'leased')
            self.assertIsNone(self.store.thesis('no-model'))

    def test_second_insert_failure_rolls_back_all_classifications_and_job_completion(self):
        self.queue(); job = self.claim()
        self.store.connection.executescript("""
            CREATE TRIGGER fail_second_classification BEFORE INSERT ON source_classifications
            WHEN NEW.source_id='doc-b' BEGIN SELECT RAISE(FAIL,'injected persistence failure'); END;
        """)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'injected persistence failure'):
            self.complete(job)
        self.assertEqual(self.classification_count(), 0)
        self.assertEqual(self.store.job(job['id'])['status'], 'leased')
        self.assertEqual(self.store.sources('no-model'), self.original_sources)

    def test_new_source_during_lease_stays_out_and_overlapping_packet_is_superseded(self):
        self.queue(); first = self.claim()
        # This source arrives during the lease, even though its document says
        # it was retrieved earlier. It becomes visible only after persistence.
        self.harness.ingest({'schema_version': 1, 'sources': [source('doc-c', '新たな公開Q&A。')]},
                            now=at('2026-10-09T10:01:30+09:00'))
        overlapping = self.intake.queue('2026-10-09T10:01:30+09:00', now=at('2026-10-09T10:01:30+09:00'))['selected'][0]['job_id']
        self.assertNotEqual(first['id'], overlapping)
        self.assertEqual([item['id'] for item in self.store.job(first['id'])['packet']['sources']], ['doc-a', 'doc-b'])
        self.assertIsNone(self.claim('second-classifier', stamp='2026-10-09T10:01:40+09:00'))
        self.complete(first)
        self.assertIsNone(self.claim(stamp='2026-10-09T10:03:00+09:00'))
        self.assertEqual(self.store.job(overlapping)['status'], 'superseded')
        fresh_id = self.intake.queue('2026-10-09T10:04:00+09:00', now=at('2026-10-09T10:04:00+09:00'))['selected'][0]['job_id']
        fresh = self.claim(stamp='2026-10-09T10:05:00+09:00')
        self.assertEqual(fresh['id'], fresh_id)
        self.assertEqual([item['id'] for item in fresh['packet']['sources']], ['doc-c'])
        self.assertEqual(self.classification_count(), 2)

    def test_lease_owner_expiry_and_immutable_retry_are_enforced(self):
        self.queue(); job = self.claim(lease_seconds=30)
        with self.assertRaisesRegex(ValueError, 'lease owner'):
            self.complete(job, worker='other')
        with self.assertRaisesRegex(ValueError, 'Lease expired'):
            self.complete(job)
        reclaimed = self.claim('replacement', '2026-10-09T10:03:00+09:00')
        self.assertEqual(reclaimed['id'], job['id'])
        completed = self.complete(reclaimed, worker='replacement', stamp='2026-10-09T10:04:00+09:00')
        changed = self.result(reclaimed); changed['classifications'][0]['rationale'] = 'Changed after completion.'
        with self.assertRaisesRegex(ValueError, 'immutable'):
            self.complete(reclaimed, changed, worker='replacement', stamp='2026-10-09T10:05:00+09:00')
        self.assertEqual(self.store.job(job['id']), completed)

    def test_only_saved_public_material_visible_at_cutoff_enters_intake(self):
        self.harness.ingest({'schema_version': 1, 'companies': [{'id': 'empty', 'name': 'No saved public material'}],
                            'sources': [source('market', source_type='market_data'),
                                        source('published-later', published_at='2026-10-09T10:10:00+09:00', retrieved_at='2026-10-09T10:11:00+09:00'),
                                        source('retrieved-later', retrieved_at='2026-10-09T10:12:00+09:00')]},
                            now=at('2026-10-09T10:12:00+09:00'))
        self.assertEqual(self.queue(company_id='empty')['selected'], [])
        job_id = self.queue(company_id='no-model', limit=1)['selected'][0]['job_id']
        self.assertEqual([item['id'] for item in self.store.job(job_id)['packet']['sources']], ['doc-a', 'doc-b'])
        with self.assertRaises(ValueError): self.queue(company_id='unknown')

    def test_existing_research_and_intake_share_company_lease_without_requiring_same_stage(self):
        bundle = json.loads((ROOT / 'examples/demo.json').read_text())
        # Existing intake fixtures were persisted at 09:55 on this date; the
        # demo is added afterwards, before the shared 10:00 daily cutoff.
        self.harness.ingest(bundle, now=at('2026-10-09T09:56:00+09:00'))
        intake_id = self.queue(company_id='demo-services')['selected'][0]['job_id']
        self.harness.daily(AS_OF, now=at(AS_OF))
        research = self.claim()
        self.assertNotEqual(research['packet'].get('kind'), 'intake')
        self.assertIsNone(self.claim('second-worker'))
        updated = deepcopy(research['packet']['thesis'])
        updated.update(version=2, recorded_at='2026-10-09T10:02:00+09:00', next_review_date='2026-10-30',
                       evidence_ids=[item['id'] for item in research['packet']['sources']])
        result = {'summary': 'Reviewed the existing public disclosure.', 'counterarguments': ['Still needs further evidence.'],
                  'evidence_ids': updated['evidence_ids'], 'proposed_action': 'unresolved', 'thesis_update': updated}
        self.complete(research, result)
        intake = self.claim(stamp='2026-10-09T10:03:00+09:00')
        self.assertEqual(intake['id'], intake_id)
        self.assertEqual(intake['packet']['stage'], 'source_classification')


if __name__ == '__main__': unittest.main()
