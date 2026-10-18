"""Source/receipt binding is narrower than semantic labels or proper scoring."""
from copy import deepcopy
from hashlib import sha256
import json
import sqlite3
import unittest

from ir_agent.availability import RecordAvailability, SCHEMA as AVAILABILITY_SCHEMA
from ir_agent.information_review import SCHEMA as INFORMATION_SCHEMA
from ir_agent.models import json_text, validate_source
from ir_agent.observation_assessments import digest
from ir_agent.observation_store import ObservationStore, SCHEMA as OBSERVATION_SCHEMA
from ir_agent.prediction_bindings import report_prediction_bindings
from ir_agent.prediction_store import PredictionStore, SCHEMA as PREDICTION_SCHEMA
from test_observation_store import design, fixture
from test_prediction_store import candidate, DESIGN_SAVED, SAVED

AS_OF = '2026-11-02T16:00:00+09:00'
NOW = '2026-11-04T12:00:00+09:00'


class PredictionBindingsTests(unittest.TestCase):
    def setUp(self):
        self.environment()

    def environment(self, *, synthetic=True, no_reply=False):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.addCleanup(self.db.close)
        self.db.executescript(OBSERVATION_SCHEMA + PREDICTION_SCHEMA + AVAILABILITY_SCHEMA + INFORMATION_SCHEMA +
            'CREATE TABLE sources(id TEXT PRIMARY KEY,data TEXT); CREATE TABLE replies(id TEXT PRIMARY KEY,data TEXT); CREATE TABLE questions(id TEXT PRIMARY KEY,data TEXT);')
        self.record = fixture(); self.record['synthetic'] = synthetic
        if no_reply: self.record['replies'] = []
        self.observations = ObservationStore(self.db)
        initial = self.observations.register(design(synthetic=synthetic), DESIGN_SAVED)
        self.predictions = PredictionStore(self.db)
        self.predictions.register(candidate(initial), SAVED)
        self.saved = self.observations.append(self.record, 1, AS_OF)
        self.premise = self.make_source(self.record['premise_evidence'][0])
        self.state = self.make_source(self.record['verification']['evidence'][0])
        self.question = {'id': self.record['question_id'], 'company_id': self.record['company_id'],
            'created_at': self.record['question_created_at'], 'question': self.record['question'], 'thesis_version': self.record['thesis_version']}
        self.raw_text = 'Synthetic reply: the cost is temporary, repeating public information.'
        self.reply = {'id': fixture()['replies'][0]['id'], 'question_id': self.record['question_id'],
            'received_at': fixture()['replies'][0]['received_at'], 'raw_text': self.raw_text, 'information_status': 'public_clarification'}
        # Receipts use an explicitly injected fictional clock in time order.
        self.save_raw('sources', self.premise, self.premise['retrieved_at'])
        self.save_raw('questions', self.question, self.question['created_at'])
        if not no_reply: self.save_raw('replies', self.reply, self.reply['received_at'])
        self.save_raw('sources', self.state, self.state['retrieved_at'])
        self.binding = {'observation_ref': self.reference(self.saved),
            'source_links': [{'role': role, 'observation_evidence_id': source['id'], 'source_id': source['id'], 'source_snapshot_sha256': digest(source)}
                for role, source in (('premise', self.premise), ('state_evidence', self.state))],
            'reply_links': [] if no_reply else [{'reply_id': self.reply['id'], 'observation_reply_sha256': digest(self.record['replies'][0]),
                'raw_reply_sha256': sha256(self.raw_text.encode()).hexdigest(), 'basis_quote': 'the cost is temporary'}]}

    def make_source(self, evidence):
        return validate_source({'id': evidence['id'], 'company_id': evidence['company_id'], 'title': 'Synthetic source-only fixture',
            'url': evidence['url'], 'source_type': 'public_disclosure', 'published_at': evidence['published_at'],
            'retrieved_at': evidence['retrieved_at'], 'content': evidence['quote'], 'metadata': {}})

    def save_raw(self, table, record, when, *, legacy=False):
        kind = {'sources': 'source', 'replies': 'reply', 'questions': 'question'}[table]
        self.db.execute('BEGIN')
        self.db.execute('INSERT INTO ' + table + ' VALUES (?,?)', (record['id'], json_text(record)))
        ledger = RecordAvailability(self.db)
        method = ledger.observe_existing if legacy else ledger.record_first_save
        method(kind, record['id'], record, now=when)
        self.db.execute('COMMIT')

    @staticmethod
    def reference(saved):
        return {'id': saved['id'], 'version': saved['version'], 'snapshot_sha256': digest(saved['record']), 'design_sha256': saved['design_sha256']}

    def report(self, requests=None, *, as_of=AS_OF, now=NOW):
        return report_prediction_bindings(self.db, [self.binding] if requests is None else requests, as_of=as_of, now=now)

    def composed_state(self, *, second_damage=None):
        first = deepcopy(self.state); first['id'] = 'first-parent'
        second = deepcopy(self.state); second['id'] = 'second-parent'
        if second_damage == 'synthetic': second['metadata']['synthetic'] = True
        if second_damage == 'company': second['company_id'] = 'another-company'
        if second_damage == 'held': second['metadata']['information_status'] = 'potential_nonpublic'
        if second_damage == 'future':
            second.update(published_at='2026-11-03T10:00:00+09:00', retrieved_at='2026-11-03T10:01:00+09:00')
        self.save_raw('sources', first, first['retrieved_at'])
        self.save_raw('sources', second, second['retrieved_at'])
        root = deepcopy(self.state); root['id'] = 'composed-state'
        root['metadata'] = {'original_source_ids': [first['id'], second['id']]}
        saved_at = max(first['retrieved_at'], second['retrieved_at'])
        self.save_raw('sources', root, saved_at)
        self.binding['source_links'][1].update(source_id=root['id'], source_snapshot_sha256=digest(root))
        return root, first, second

    def test_complete_mechanical_bindings_preserve_sources_but_never_approve_labels(self):
        original = deepcopy(self.binding); dump = list(self.db.iterdump()); changes = self.db.total_changes
        result = self.report(); observation = result['observations'][0]
        self.assertEqual(result['status'], 'source_binding_report_only')
        self.assertEqual(observation['binding_status'], 'matched')
        self.assertEqual(result['population'], {'observation_count': 1, 'visible_prediction_count': 1, 'no_prediction_count': 0, 'orphan_prediction_count': 0})
        self.assertEqual(result['sources_by_id'][self.state['id']]['record'], self.state)
        self.assertEqual(result['reply_snapshots'][self.reply['id']]['record'], self.reply)
        for item in (result, observation):
            self.assertEqual(item['state_independence'], 'unknown'); self.assertEqual(item['semantic_signal'], 'unknown')
            self.assertEqual(item['training'], 'unknown'); self.assertEqual(item['calibration'], 'unknown')
            self.assertIsNone(item['score']); self.assertIsNone(item['score_request'])
        self.assertIsNone(observation['selected_state'])
        self.assertEqual(self.report(), result)
        self.assertEqual(self.binding, original); self.assertEqual(list(self.db.iterdump()), dump)
        self.assertEqual(self.db.total_changes, changes); self.assertFalse(self.db.in_transaction)

    def test_empty_unknown_tables_and_missing_bindings_keep_population(self):
        empty = sqlite3.connect(':memory:', isolation_level=None); self.addCleanup(empty.close)
        result = report_prediction_bindings(empty, [], as_of=AS_OF, now=NOW)
        self.assertEqual(result['population']['observation_count'], 0)
        self.assertTrue(all(value == 'unknown' for value in result['table_status'].values()))
        result = self.report([])
        self.assertEqual(result['population']['observation_count'], 1)
        self.assertEqual(result['observations'][0]['binding_status'], 'unknown')
        self.assertEqual(len(result['observations'][0]['missing_bindings']), 3)
        self.db.execute('DELETE FROM ir_predictions'); self.db.execute('DELETE FROM ir_prediction_models')
        result = self.report()
        self.assertEqual(result['population']['no_prediction_count'], 1)
        self.assertEqual(result['table_status']['ir_predictions'], 'known')

    def test_partial_null_and_orphan_mappings_remain_unknown_not_approved(self):
        result = self.report([{'observation_ref': None, 'source_links': None, 'reply_links': None}])
        self.assertEqual(len(result['unresolved_binding_requests']), 1)
        value = deepcopy(self.binding); value['source_links'][0]['source_id'] = None
        value['source_links'][1]['source_snapshot_sha256'] = None
        result = self.report([value])
        self.assertEqual(result['observations'][0]['binding_status'], 'unknown')
        old = deepcopy(self.binding); old['observation_ref']['version'] = 1
        self.assertEqual(self.report([old])['observations'][0]['reference_check']['status'], 'mismatch')

    def test_caller_approval_bad_types_and_duplicate_mapping_fail_without_writes(self):
        before = list(self.db.iterdump())
        variants = [None, {}, [None], [{'observation_ref': []}], [self.binding, self.binding]]
        value = deepcopy(self.binding); value['verified'] = True; variants.append([value])
        value = deepcopy(self.binding); value['source_links'][0]['role'] = []; variants.append([value])
        value = deepcopy(self.binding); value['reply_links'][0]['reply_id'] = {}; variants.append([value])
        value = deepcopy(self.binding); value['observation_ref']['version'] = True; variants.append([value])
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                report_prediction_bindings(self.db, variant, as_of=AS_OF, now=NOW)
        self.assertEqual(list(self.db.iterdump()), before)

    def test_source_sha_quote_url_dates_and_raw_reply_mismatch_are_explicit(self):
        original = deepcopy(self.state)
        for field, bad, reason in (('content', 'Different text', 'source_quote_mismatch'),
            ('url', 'https://example.invalid/other', 'source_url_mismatch'),
            ('published_at', '2026-11-02T14:00:00+09:00', 'source_published_at_mismatch')):
            damaged = {**deepcopy(original), field: bad}
            self.db.execute('UPDATE sources SET data=? WHERE id=?', (json_text(damaged), original['id']))
            bound = self.report()['observations'][0]['resolved_bindings'][1]
            with self.subTest(field=field):
                self.assertEqual(bound['status'], 'mismatch'); self.assertIn(reason, bound['reason_codes'])
        self.db.execute('UPDATE sources SET data=? WHERE id=?', (json_text(original), original['id']))
        value = deepcopy(self.binding); value['reply_links'][0]['raw_reply_sha256'] = '0'*64
        bound = self.report([value])['observations'][0]['resolved_bindings'][-1]
        self.assertIn('raw_reply_sha_mismatch', bound['reason_codes'])
        value = deepcopy(self.binding); value['source_links'][1]['source_snapshot_sha256'] = '0'*64
        self.assertIn('source_snapshot_sha_mismatch', self.report([value])['observations'][0]['resolved_bindings'][1]['reason_codes'])

    def test_second_origins_synthetic_company_held_and_future_cannot_hide(self):
        for damage in ('synthetic', 'company', 'held', 'future'):
            with self.subTest(damage=damage):
                self.environment(synthetic=False)
                self.composed_state(second_damage=damage)
                result = self.report()
                bound = result['observations'][0]['resolved_bindings'][1]
                self.assertIn(bound['status'], ('mismatch', 'held'))
                self.assertIn('second-parent', result['sources_by_id'])
                self.assertIsNone(result['score'])

    def test_shared_parent_dag_is_not_cycle_and_actual_cycle_is_reported(self):
        root, first, second = self.composed_state()
        # Two branches share the same parent snapshot.
        second['metadata'] = {'original_source_id': first['id']}
        self.db.execute('UPDATE sources SET data=? WHERE id=?', (json_text(second), second['id']))
        self.db.execute('UPDATE record_availability SET snapshot_sha256=? WHERE entity_id=?', (digest(second), second['id']))
        self.assertEqual(self.report()['observations'][0]['resolved_bindings'][1]['status'], 'matched')
        first['metadata'] = {'original_source_id': root['id']}
        self.db.execute('UPDATE sources SET data=? WHERE id=?', (json_text(first), first['id']))
        self.db.execute('UPDATE record_availability SET snapshot_sha256=? WHERE entity_id=?', (digest(first), first['id']))
        bound = self.report()['observations'][0]['resolved_bindings'][1]
        self.assertIn('source_provenance_cycle', bound['reason_codes'])

    def test_legacy_known_by_does_not_invent_first_save_before_presence(self):
        self.db.execute("UPDATE record_availability SET basis='legacy_presence',first_saved_at=NULL,presence_observed_at=? WHERE entity_type='source' AND entity_id=?",
            ('2026-11-01T00:00:00+09:00', self.premise['id']))
        source = self.report()['observations'][0]['resolved_bindings'][0]['lineage_checks'][0]
        self.assertEqual(source['usage_availability']['status'], 'unknown')
        self.assertEqual(source['historical_availability']['status'], 'matched')
        availability = source['historical_availability']['availability']
        self.assertFalse(availability['first_save_known']); self.assertIsNone(availability['receipt']['first_saved_at'])

    def test_missing_or_wrong_receipt_is_unknown_or_mismatch(self):
        self.db.execute("DELETE FROM record_availability WHERE entity_type='source' AND entity_id=?", (self.premise['id'],))
        self.assertEqual(self.report()['observations'][0]['resolved_bindings'][0]['status'], 'unknown')
        self.db.execute("UPDATE record_availability SET snapshot_sha256=? WHERE entity_type='reply'", ('0'*64,))
        self.assertEqual(self.report()['observations'][0]['resolved_bindings'][-1]['status'], 'mismatch')

    def test_information_hold_after_asof_is_current_hold_and_history_is_preserved(self):
        review = {'reply_id': self.reply['id'], 'version': 1, 'information_status': 'potential_nonpublic',
            'recorded_at': '2026-11-03T17:00:00+09:00'}
        self.db.execute('INSERT INTO reply_information_reviews VALUES (?,?,?,?)', (self.reply['id'], 1, json_text(review), review['recorded_at']))
        dump = list(self.db.iterdump())
        binding = self.report()['observations'][0]['resolved_bindings'][-1]
        self.assertEqual(binding['historical_publicity']['status'], 'matched')
        self.assertEqual(binding['current_publicity']['status'], 'held')
        self.assertEqual(binding['status'], 'held')
        self.assertEqual(list(self.db.iterdump()), dump)

    def test_ir_origin_uses_current_review_and_its_raw_reply_receipts(self):
        parent = deepcopy(self.state)
        parent.update(id='ir-origin', source_type='ir_reply', content=self.raw_text,
                      metadata={'reply_id': self.reply['id'], 'information_status': 'public_clarification'})
        self.save_raw('sources', parent, parent['retrieved_at'])
        root = deepcopy(self.state); root.update(id='derived-state', metadata={'original_source_id': parent['id']})
        self.save_raw('sources', root, root['retrieved_at'])
        self.binding['source_links'][1].update(source_id=root['id'], source_snapshot_sha256=digest(root))
        review = {'reply_id': self.reply['id'], 'version': 1, 'information_status': 'potential_nonpublic',
                  'recorded_at': '2026-11-03T17:00:00+09:00'}
        self.db.execute('INSERT INTO reply_information_reviews VALUES (?,?,?,?)', (self.reply['id'], 1, json_text(review), review['recorded_at']))
        bound = self.report()['observations'][0]['resolved_bindings'][1]
        origin = next(check for check in bound['lineage_checks'] if check['source_id'] == parent['id'])
        self.assertEqual(origin['historical_publicity']['status'], 'matched')
        self.assertEqual(origin['current_publicity']['status'], 'held')
        self.assertEqual(origin['current_publicity']['reply_availability']['status'], 'matched')
        self.assertEqual(bound['status'], 'held')

    def test_state_known_signal_change_is_held_as_leakage_even_without_prediction(self):
        event = {'id': 'after-state', 'target_kind': 'reply', 'target_id': self.reply['id'],
            'target_snapshot_sha256': digest(self.record['replies'][0]), 'version': 1, 'expected_previous_version': 0,
            'recorded_at': '2026-11-03T16:00:00+09:00', 'reviewer': 'Synthetic-only test worker',
            'rationale': 'Test a visible classification correction after the state label.',
            'basis': {'target_text_reference': self.reply['id'], 'target_text_sha256': sha256(self.raw_text.encode()).hexdigest(),
                'basis_quote': 'the cost is temporary', 'public_evidence_references': [{'source_id': self.state['id'], 'source_sha256': digest(self.state), 'basis_quote': self.state['content']}]},
            'assessment': {'signal': 'persistent_explanation', 'information_status': 'public_clarification'}}
        changed = deepcopy(self.record); changed['assessments'] = [event]
        saved = self.observations.append(changed, 2, event['recorded_at'])
        self.binding['observation_ref'] = self.reference(saved)
        self.db.execute('DELETE FROM ir_predictions')
        result = self.report(as_of=NOW)['observations'][0]
        self.assertEqual(result['current_signal'], 'persistent_explanation')
        self.assertEqual(result['leakage_candidates'][0]['assessment_id'], event['id'])
        self.assertEqual(result['state_independence'], 'unknown'); self.assertIsNone(result['score_request'])

    def test_no_response_and_outer_transaction_keep_missingness_and_ownership(self):
        self.environment(no_reply=True)
        self.db.execute('BEGIN')
        result = self.report()
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(result['observations'][0]['current_signal'], 'no_response_by_deadline')
        self.assertIn('response_log_completeness_unverified', result['observations'][0]['reason_codes'])
        self.assertIsNone(result['score'])
        self.db.execute('ROLLBACK')
        with self.assertRaises(ValueError): self.report(as_of='2026-11-05T12:00:00+09:00')


if __name__ == '__main__': unittest.main()
