"""Synthetic memory-only legacy-presence boundaries; no live DB or network."""
from copy import deepcopy
from hashlib import sha256
import json
import unittest
from unittest.mock import patch

from ir_agent.availability import RecordAvailability
from ir_agent.catalyst_schedule import _ScheduleReader
from ir_agent.intake import Intake
from ir_agent.models import json_text
from ir_agent.research_monitoring import _source
import test_qualitative_research_integration as fixtures

at = fixtures.at


class QualitativeKnownByTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.QualitativeIntegrationTests(
            'test_watch_without_thesis_queues_once_completes_and_never_writes_financial_records')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.db, self.registry = self.f.store.connection, self.f.registry

    def legacy(self, identity='A', minute=1):
        # Model migration of an already-present synthetic source in memory.
        saved = self.f.store.source(identity)
        with self.f.store.transaction():
            self.db.execute("DELETE FROM record_availability WHERE entity_type='source' AND entity_id=?", (identity,))
            return RecordAvailability(self.db).observe_existing('source', identity, saved, now=at(minute))

    def record(self):
        return {'company_id': 'jp:TEST', 'synthetic': True, 'last_review_at': at(0).isoformat()}

    def monitor(self, identity='A', boundary=4, current=4):
        return _source(_ScheduleReader(self.db, at(current).isoformat()), identity,
                       self.record(), None, at(boundary).isoformat())

    def check(self, identity='A', boundary=4, current=4):
        return self.registry._source_check(self.record(), self.f.store.source(identity),
                                           at(boundary), at(current))

    def bootstrap(self, identity='A', reviewed=2, current=3):
        request = deepcopy(self.f.request)
        saved = self.f.store.source(identity)
        digest = sha256(json_text(saved).encode()).hexdigest()
        request['bootstrap_reviews'] = [{'source_id': identity, 'source_snapshot_sha256': digest,
            'reviewed_at': at(reviewed).isoformat(),
            'review_ref': self.f.file('bootstrap.json', identity + ' ' + digest)}]
        return self.registry.register_case(request, 0, research_root=self.f.root, now=at(current))

    def derived(self):
        self.f.add_source('P', 2)
        value = fixtures.source('D', content='Synthetic derived D',
                                metadata={'synthetic': True, 'original_source_id': 'P'})
        self.f.harness.ingest({'schema_version': 1, 'sources': [value]}, now=at(3))
        Intake(self.f.store).queue(at(3).isoformat(), now=at(3))
        job = self.f.harness.claim('classifier', now=at(3, 1), measurement_synthetic=True)
        self.f.harness.complete(job['id'], 'classifier', {'classifications': [{
            'source_id': 'D', 'expected_version': 0, 'kind': 'other', 'financial_content': False,
            'basis_quote': value['content'], 'rationale': 'Synthetic classification only.'}]}, now=at(3, 2))
        self.legacy('D', 4)

    def test_legacy_bootstrap_queue_claim_complete_use_known_by_without_rewriting_receipts(self):
        receipt_a = self.legacy()
        registered = self.bootstrap()
        self.assertEqual(list(registered['record']['reviewed_sources']), ['A'])
        self.f.add_source('B', 4)
        receipt_b = self.legacy('B', 5)
        self.assertEqual(self.f.queue(6)['jobs_created'], 1)
        job = self.f.claim(7)
        self.assertEqual(job['packet']['pending_source_ids'], ['B'])
        self.assertEqual(self.f.complete(job, minute=8)['status'], 'completed')
        self.assertEqual(set(self.registry.show_case('orders-case')['record']['reviewed_sources']), {'A', 'B'})
        self.assertEqual(self.f.queue(9)['jobs_created'], 0)
        self.assertEqual(RecordAvailability(self.db).get('source', 'A'), receipt_a)
        self.assertEqual(RecordAvailability(self.db).get('source', 'B'), receipt_b)
        self.assertIsNone(receipt_b['first_saved_at'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM theses').fetchone()[0], 0)

    def test_cutoff_at_presence_is_readable_but_before_presence_bootstrap_is_rejected(self):
        self.legacy(minute=2)
        result = self.check(boundary=2, current=3)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['known_by_at'], at(2).isoformat(timespec='microseconds'))
        with self.assertRaisesRegex(ValueError, 'not usable'):
            self.bootstrap(reviewed=1, current=3)
        self.assertEqual(self.db.execute('SELECT count(*) FROM qualitative_case_versions').fetchone()[0], 0)
        self.assertNotEqual(self.check(boundary=3, current=1)['status'], 'matched')

    def test_unknown_first_save_and_nonfresh_arrival_survive_wrapper_and_monitor_is_unchanged(self):
        receipt = self.legacy()
        raw_before = self.f.store.source('A')
        monitor = self.monitor()
        self.assertEqual(monitor['status'], 'unknown')
        self.assertEqual(monitor['reason_codes'], ['source_first_save_unknown'])
        current = self.check()
        self.assertEqual(current['status'], 'matched')
        self.assertFalse(current['first_save_known'])
        self.assertIsNone(current['first_saved_at'])
        self.assertEqual(current['arrival'], 'unknown')
        self.assertEqual(current['review_availability_basis'], 'legacy_presence_known_by')
        self.assertEqual(current['nonblocking_diagnostics'], ['source_first_save_unknown'])
        restored = deepcopy(current)
        for key in ('known_by_at', 'review_availability_basis', 'nonblocking_diagnostics'):
            restored.pop(key)
        restored.update(status=monitor['status'], reason_codes=monitor['reason_codes'])
        self.assertEqual(restored, monitor)
        self.assertEqual(self.monitor(), monitor)
        self.assertEqual(self.f.store.source('A'), raw_before)
        self.assertEqual(RecordAvailability(self.db).get('source', 'A'), receipt)

    def test_trusted_first_save_branch_remains_whole_JSON_identical(self):
        self.assertEqual(self.check(), self.monitor())
        self.assertTrue(self.check()['first_save_known'])
        self.assertNotIn('review_availability_basis', self.check())

    def test_missing_invalid_or_SHA_mismatched_receipts_are_never_promoted(self):
        baseline = self.legacy()
        keys = ('entity_type', 'entity_id', 'version', 'snapshot_sha256',
                'first_saved_at', 'presence_observed_at', 'basis')
        faults = [('missing', None), ('invalid_time', ('presence_observed_at', 'not-a-time')),
                  ('SHA', ('snapshot_sha256', '0' * 64)),
                  ('invalid_legacy_first_save', ('first_saved_at', at(1).isoformat()))]
        for name, mutation in faults:
            with self.subTest(fault=name):
                self.db.execute("DELETE FROM record_availability WHERE entity_type='source' AND entity_id='A'")
                self.db.execute('INSERT INTO record_availability VALUES (?,?,?,?,?,?,?)', tuple(baseline[k] for k in keys))
                if mutation is None:
                    self.db.execute("DELETE FROM record_availability WHERE entity_type='source' AND entity_id='A'")
                else:
                    self.db.execute('PRAGMA ignore_check_constraints=ON')
                    self.db.execute('UPDATE record_availability SET ' + mutation[0] + "=? WHERE entity_type='source' AND entity_id='A'", (mutation[1],))
                    self.db.execute('PRAGMA ignore_check_constraints=OFF')
                self.assertNotEqual(self.check()['status'], 'matched')
                self.assertNotIn('review_availability_basis', self.check())
                with self.assertRaisesRegex(ValueError, 'not usable'):
                    self.bootstrap()

    def test_ancestor_first_saved_after_review_cutoff_is_not_waived(self):
        self.derived()
        self.db.execute("UPDATE record_availability SET first_saved_at=?,presence_observed_at=? WHERE entity_type='source' AND entity_id='P'",
                        (at(6).isoformat(), at(6).isoformat()))
        held = self.check('D', boundary=5, current=8)
        self.assertNotEqual(held['status'], 'matched')
        self.assertIn('first_saved_after_knowledge_at', held['reason_codes'])
        with self.assertRaisesRegex(ValueError, 'not usable'):
            self.bootstrap('D', reviewed=5, current=8)

    def test_ancestor_classification_arriving_after_review_cutoff_is_not_waived(self):
        self.derived()
        row = self.db.execute("SELECT data FROM source_classifications WHERE source_id='P'").fetchone()
        changed = json.loads(row['data']); changed['recorded_at'] = at(6).isoformat()
        self.db.execute("UPDATE source_classifications SET data=?,first_saved_at=? WHERE source_id='P'",
                        (json_text(changed), at(6).isoformat()))
        held = self.check('D', boundary=5, current=8)
        self.assertNotEqual(held['status'], 'matched')
        self.assertIn('classification_not_available', held['reason_codes'])
        with self.assertRaisesRegex(ValueError, 'not usable'):
            self.bootstrap('D', reviewed=5, current=8)

    def test_missing_ancestor_receipt_still_blocks_bootstrap_and_queue(self):
        self.derived()
        self.db.execute("DELETE FROM record_availability WHERE entity_type='source' AND entity_id='P'")
        held = self.check('D', boundary=5, current=8)
        self.assertNotEqual(held['status'], 'matched')
        self.assertIn('availability_receipt_missing', held['reason_codes'])
        with self.assertRaisesRegex(ValueError, 'not usable'):
            self.bootstrap('D', reviewed=5, current=8)
        self.f.register(minute=8)
        self.assertEqual(self.f.queue(9)['jobs_created'], 0)

    def test_domain_and_publicity_faults_in_ancestor_are_not_waived(self):
        self.derived()
        originals = {identity: self.f.store.source(identity) for identity in ('D', 'P')}

        def bind_fault_fixture(identity, value):
            # Deliberately corrupt a synthetic in-memory graph, keeping its
            # receipt/classification SHA bindings coherent to isolate the guard.
            digest = sha256(json_text(value).encode()).hexdigest()
            self.db.execute('UPDATE sources SET data=? WHERE id=?', (json_text(value), identity))
            self.db.execute("UPDATE record_availability SET snapshot_sha256=? WHERE entity_type='source' AND entity_id=?",
                            (digest, identity))
            row = self.db.execute('SELECT data FROM source_classifications WHERE source_id=?', (identity,)).fetchone()
            classification = json.loads(row['data'])
            classification['source_snapshot_sha256'] = digest
            self.db.execute('UPDATE source_classifications SET data=? WHERE source_id=?',
                            (json_text(classification), identity))

        for fault, reason in (
                ('company', 'source_identity_or_company_mismatch'),
                ('synthetic', 'synthetic_source_in_real_observation'),
                ('cycle', 'source_provenance_cycle'),
                ('publicity', 'source_information_held_for_review')):
            with self.subTest(fault=fault):
                changed = deepcopy(originals)
                record = self.record()
                if fault == 'company':
                    changed['P']['company_id'] = 'jp:OTHER'
                elif fault == 'synthetic':
                    record['synthetic'] = False
                    changed['D']['metadata']['synthetic'] = False
                elif fault == 'cycle':
                    changed['P']['metadata']['original_source_id'] = 'D'
                else:
                    changed['P']['metadata']['information_status'] = 'potential_nonpublic'
                for identity, value in changed.items():
                    bind_fault_fixture(identity, value)
                held = self.registry._source_check(record, changed['D'], at(5), at(8))
                self.assertNotEqual(held['status'], 'matched')
                self.assertIn(reason, held['reason_codes'])
                self.assertNotIn('review_availability_basis', held)

    def test_new_unresolved_classification_still_blocks_current_claimable_and_complete(self):
        self.legacy(); self.f.register(); self.f.queue(); job = self.f.claim()
        row = self.db.execute("SELECT data,job_id FROM source_classifications WHERE source_id='A'").fetchone()
        changed = json.loads(row['data']); changed.update(version=2, recorded_at=at(6).isoformat(), kind='unresolved')
        self.db.execute('INSERT INTO source_classifications(source_id,version,data,first_saved_at,job_id) VALUES (?,?,?,?,?)',
                        ('A', 2, json_text(changed), at(6).isoformat(), row['job_id']))
        self.assertFalse(self.registry.claimable(job['packet'], now=at(7)))
        with self.assertRaisesRegex(ValueError, 'source evidence changed'):
            self.f.complete(job, minute=7)
        self.assertEqual(self.f.queue(8)['skipped'][0]['reason'], 'source_evidence_held')
        self.assertEqual(self.registry.show_case('orders-case')['version'], 1)

    def test_current_publicity_hold_is_not_cleared_even_when_historical_use_matches(self):
        self.legacy(); self.f.register(); self.f.queue(); job = self.f.claim()
        original = _ScheduleReader.publicity
        def corrected_publicity(reader, source, company_id, cutoff):
            # Synthetic current correction at the existing reader boundary;
            # immutable source bytes and availability receipts remain untouched.
            if cutoff >= at(6).isoformat():
                return {'status': 'held', 'reason_codes': ['source_information_held_for_review']}
            return original(reader, source, company_id, cutoff)
        with patch.object(_ScheduleReader, 'publicity', corrected_publicity):
            held = self.check(boundary=4, current=7)
            self.assertEqual(held['historical_usability']['status'], 'matched')
            self.assertNotEqual(held['current_use']['status'], 'matched')
            self.assertNotEqual(held['status'], 'matched')
            self.assertFalse(self.registry.claimable(job['packet'], now=at(7)))
            with self.assertRaisesRegex(ValueError, 'source evidence changed'):
                self.f.complete(job, minute=7)


if __name__ == '__main__':
    unittest.main()
