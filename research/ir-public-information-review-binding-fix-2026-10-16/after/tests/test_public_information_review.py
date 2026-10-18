"""Optional public-review evidence binding, never semantic absence or trading."""
from copy import deepcopy
from datetime import datetime, timedelta
from hashlib import sha256
import json
import unittest
from unittest.mock import patch

from ir_agent.availability import RecordAvailability
from ir_agent.decision import evaluate_ir_plan
from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.harness import Harness
from ir_agent.information_review import add_assessment
from ir_agent.models import json_text, validate_question, validate_source
from ir_agent.store import Store
from test_decision import plan

CREATED = datetime.fromisoformat('2026-10-09T10:00:00+09:00')
BEFORE = CREATED - timedelta(minutes=1)
REVIEWED = CREATED - timedelta(seconds=30)
SAVED = CREATED + timedelta(minutes=1)
SENT = CREATED + timedelta(minutes=5)


def source(identity='public-qa', company='demo-services', **changes):
    value = {'id': identity, 'company_id': company, 'title': 'Synthetic public QA only',
             'url': 'https://example.invalid/qa', 'source_type': 'public_disclosure',
             'published_at': None, 'retrieved_at': (BEFORE - timedelta(minutes=1)).isoformat(),
             'content': 'Synthetic Q: Which table? A: Consolidated table. Other definitions not stated here.',
             'requires_research': True, 'metadata': {'synthetic': True}}
    value.update(changes)
    return value


def binding(qa, scope='Saved Q&A, question1/table scope only'):
    return {'reviewed_at': REVIEWED.isoformat(), 'reviewer': 'Synthetic reviewer',
            'rationale': 'The remaining definition is not resolved by this cited scope; assertion only.',
            'sources': [{'source_id': qa['id'], 'source_snapshot_sha256': sha256(json_text(qa).encode()).hexdigest(),
                         'scope': scope, 'basis_quote': qa['content']}]}


def pure():
    value = plan(); qa = source(company=value['thesis']['company_id'])
    value['sources'].append(qa)
    value['question']['public_information_review'] = binding(qa)
    return value


class PublicInformationPureTests(unittest.TestCase):
    def test_extra_review_source_is_not_financial_evidence_or_absence_certification(self):
        value = pure(); saved = deepcopy(value); baseline = deepcopy(value)
        baseline['question'].pop('public_information_review'); baseline['sources'].pop()
        old = evaluate_ir_plan(baseline); result = evaluate_ir_plan(value)
        self.assertEqual(result['outcomes'], old['outcomes'])
        self.assertEqual(result['question_value'], old['question_value'])
        self.assertNotIn('public_information_review_check', old)
        baseline['question']['public_information_review_check'] = {'answer_absence_verified': True}
        self.assertEqual(evaluate_ir_plan(baseline), old)
        check = result['public_information_review_check']
        self.assertEqual(check['source_closure_ids'], ['public-qa'])
        self.assertFalse(check['answer_absence_verified']); self.assertTrue(check['meaning_review_required'])
        self.assertNotIn('public-qa', value['thesis']['evidence_ids']); self.assertEqual(value, saved)
        value['question']['public_answer_status'] = 'found'
        self.assertEqual(evaluate_ir_plan(value)['question_value'], 'needs_review')

    def test_record_shape_scope_hash_types_duplicates_and_typos_are_strict(self):
        for mode in ('null', 'empty', 'extra', 'missing', 'source_empty', 'duplicate', 'scope_empty',
                     'scope_object', 'hash_upper', 'hash_short', 'source_extra', 'quote_empty', 'reviewer_empty'):
            value = pure(); r = value['question']['public_information_review']; s = r['sources'][0]
            if mode == 'null': value['question']['public_information_review'] = None
            elif mode == 'empty': value['question']['public_information_review'] = {}
            elif mode == 'extra': r['reviewd_at'] = r['reviewed_at']
            elif mode == 'missing': del r['rationale']
            elif mode == 'source_empty': r['sources'] = []
            elif mode == 'duplicate': r['sources'].append(deepcopy(s))
            elif mode == 'scope_empty': s['scope'] = ' '
            elif mode == 'scope_object': s['scope'] = {'page': 1}
            elif mode == 'hash_upper': s['source_snapshot_sha256'] = 'A' * 64
            elif mode == 'hash_short': s['source_snapshot_sha256'] = '0' * 63
            elif mode == 'source_extra': s['source_hash'] = s['source_snapshot_sha256']
            elif mode == 'quote_empty': s['basis_quote'] = ''
            else: r['reviewer'] = ''
            with self.subTest(mode=mode), self.assertRaises(ValueError): validate_question(value['question'])

    def test_hash_quote_company_market_missing_root_and_review_time_refuse(self):
        for mode in ('hash', 'quote', 'company', 'market', 'missing', 'naive', 'later_review'):
            value = pure(); qa = value['sources'][-1]; r = value['question']['public_information_review']
            if mode == 'hash': r['sources'][0]['source_snapshot_sha256'] = '0' * 64
            elif mode == 'quote': r['sources'][0]['basis_quote'] = 'Not in saved source'
            elif mode == 'company': qa['company_id'] = 'another-company'; value['question']['public_information_review'] = binding(qa)
            elif mode == 'market': qa['source_type'] = 'market_data'; value['question']['public_information_review'] = binding(qa)
            elif mode == 'missing': value['sources'].pop()
            elif mode == 'naive': r['reviewed_at'] = '2026-10-09T09:59:30'
            else: r['reviewed_at'] = (CREATED + timedelta(seconds=1)).isoformat()
            with self.subTest(mode=mode), self.assertRaises(ValueError): evaluate_ir_plan(value)

    def test_unavailable_source_is_notready_even_if_caller_spoofs_a_success_check(self):
        value = pure(); qa = value['sources'][-1]
        qa['retrieved_at'] = CREATED.isoformat(); value['question']['public_information_review'] = binding(qa)
        value['question']['public_information_review_check'] = {'reason_codes': [], 'answer_absence_verified': True}
        result = evaluate_ir_plan(value)
        self.assertEqual(result['question_value'], 'needs_review')
        self.assertIn('source_origin_not_available', result['public_information_review_check']['reason_codes'])
        self.assertFalse(result['public_information_review_check']['answer_absence_verified'])

    def test_dag_uses_all_parents_shared_origin_cycle_missing_and_private_hold(self):
        value = pure(); root = value['sources'][-1]; a = source('parent-a'); b = source('parent-b'); shared = source('shared')
        root['metadata']['original_source_ids'] = [a['id'], b['id']]
        a['metadata']['original_source_id'] = shared['id']; b['metadata']['original_source_id'] = shared['id']
        value['sources'].extend([a, b, shared]); value['question']['public_information_review'] = binding(root)
        self.assertEqual(len(evaluate_ir_plan(value)['public_information_review_check']['source_closure_ids']), 4)
        for mode in ('private', 'missing', 'company', 'market', 'cycle'):
            changed = deepcopy(value); parent = changed['sources'][-1]
            if mode == 'private': parent['metadata']['information_status'] = 'unclear'
            elif mode == 'missing': changed['sources'].pop()
            elif mode == 'company': parent['company_id'] = 'another-company'
            elif mode == 'market': parent['source_type'] = 'market_data'
            else: parent['metadata']['original_source_id'] = root['id']
            with self.subTest(mode=mode):
                if mode in ('company', 'market', 'cycle'):
                    with self.assertRaises(ValueError): evaluate_ir_plan(changed)
                else: self.assertEqual(evaluate_ir_plan(changed)['question_value'], 'needs_review')

    def test_pure_long_valid_chain_needs_no_new_depth_limit(self):
        value = pure(); root = value['sources'][-1]
        previous = root
        for index in range(1100):
            parent = source('chain-' + str(index))
            previous['metadata']['original_source_id'] = parent['id']
            value['sources'].append(parent); previous = parent
        value['question']['public_information_review'] = binding(root)
        self.assertEqual(len(evaluate_ir_plan(value)['public_information_review_check']['source_closure_ids']), 1101)


class PublicInformationPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.value = plan(); self.store = Store(':memory:'); self.addCleanup(self.store.close)
        self.harness = Harness(self.store); self.company = self.value['thesis']['company_id']; self.qa = source(company=self.company)
        self.harness.ingest({'schema_version': 1, 'companies': [{'id': self.company, 'name': 'Synthetic company', 'status': 'active'}],
                            'sources': [*self.value['sources'], self.qa], 'theses': [self.value['thesis']]}, now=BEFORE)
        self.harness.register_decision_policy(self.value['policy'], now=BEFORE)
        self.store.declare_position(self.company, False, now=BEFORE)

    def question(self, *, contracted=True):
        q = deepcopy(self.value['question']); q['public_information_review'] = binding(self.qa)
        if contracted:
            q['decision_contract'] = {'policy_id': self.value['policy']['id'], 'policy_version': 1,
                                      'quote': deepcopy(self.value['quote']), 'synthetic': True}
        return q

    def save(self, q=None): return self.harness.add_question(q or self.question(), now=SAVED)
    def snapshot(self): return tuple(self.store.connection.iterdump())
    def check(self, q): return q.get('public_information_review_check', q.get('decision_contract', {}).get('preflight', {}).get('public_information_review_check'))

    def ir_source(self, *, other_company=False):
        company = 'other-company' if other_company else self.company
        with self.store.transaction():
            if other_company: self.store.connection.execute("INSERT INTO companies(id,data) VALUES (?,?)", (company, json_text({'id': company, 'name': 'Other synthetic', 'status': 'watch'})))
            question = {'id': 'prior-question', 'company_id': company, 'created_at': (BEFORE - timedelta(minutes=10)).isoformat()}
            reply = {'id': 'prior-reply', 'question_id': question['id'], 'received_at': (BEFORE - timedelta(minutes=2)).isoformat(),
                     'raw_text': self.qa['content'], 'information_status': 'public_clarification'}
            self.store.connection.execute('INSERT INTO questions(id,company_id,topic,status,data,sent_at) VALUES (?,?,?,?,?,?)',
                (question['id'], company, 'prior', 'answered', json_text(question), question['created_at']))
            self.store.connection.execute('INSERT INTO replies VALUES (?,?,?)', (reply['id'], question['id'], json_text(reply)))
            RecordAvailability(self.store.connection).record_first_save('reply', reply['id'], reply, now=BEFORE)
        ir = source('review-only-ir', company=self.company, source_type='ir_reply',
                    metadata={'synthetic': True, 'reply_id': reply['id'], 'information_status': 'public_clarification'})
        self.store.put_source(validate_source(ir), now=BEFORE); self.qa = ir
        return reply

    def correct(self, status, at, version=0):
        return add_assessment(self.store, {'reply_id': 'prior-reply', 'expected_version': version,
            'information_status': status, 'basis_quote': self.qa['content'], 'rationale': 'Synthetic correction',
            'recorded_at': at.isoformat()}, now=at.isoformat())

    def test_binding_freezes_scope_and_keeps_review_roots_outside_financial_sources(self):
        q = self.question(); original = deepcopy(q); saved = self.save(q)
        self.assertEqual(saved['decision_contract']['preflight']['question_value'], 'decision_distinguishing')
        self.assertEqual(self.check(saved)['reason_codes'], [])
        self.assertNotIn(self.qa['id'], [s['id'] for s in DecisionLifecycle(self.store).sources_for(self.store.thesis(self.company), {})])
        self.assertEqual(self.save(q), saved); self.assertEqual(q, original)
        q['public_information_review']['sources'][0]['scope'] = 'Same source, new physical page only'
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'immutable'): self.save(q)
        self.assertEqual(self.snapshot(), before)

    def test_uncontracted_new_field_has_notready_reasons_and_original_request_retry(self):
        self.store.connection.execute('DELETE FROM record_availability WHERE entity_type=? AND entity_id=?', ('source', self.qa['id']))
        q = self.question(contracted=False); saved = self.save(q); before = self.snapshot()
        self.assertIn('public_information_review_source_availability_unresolved', self.check(saved)['reason_codes'])
        self.assertEqual(self.save(q), saved); self.assertEqual(self.snapshot(), before)
        # Like the old API, its response adds row state; it is not a new add request.
        with self.assertRaises(ValueError): self.save(saved)
        with self.assertRaisesRegex(ValueError, 'needs review'): self.harness.mark_sent(q['id'], SENT.isoformat(), now=SENT)
        self.assertEqual(self.snapshot(), before)

    def test_server_check_spoof_refused_for_new_and_changed_retry(self):
        q = self.question(contracted=False); q['public_information_review_check'] = {'reason_codes': []}; before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'server-computed'): self.save(q)
        self.assertEqual(self.snapshot(), before)
        q.pop('public_information_review_check'); saved = self.save(q)
        q['public_information_review_check'] = {**self.check(saved), 'answer_absence_verified': True}
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'immutable'): self.save(q)
        self.assertEqual(self.snapshot(), before)

    def test_first_save_after_review_cannot_be_backdated_and_blocks_new_send_record(self):
        self.store.connection.execute('UPDATE record_availability SET first_saved_at=?,presence_observed_at=? WHERE entity_type=? AND entity_id=?',
            (CREATED.isoformat(), CREATED.isoformat(), 'source', self.qa['id']))
        saved = self.save(); check = self.check(saved)
        self.assertIn('public_information_review_source_availability_unresolved', check['reason_codes'])
        self.assertIn('first_saved_after_knowledge_at', check['availability_at_review'][self.qa['id']]['reason_codes'])
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'needs review'): self.harness.mark_sent(saved['id'], SENT.isoformat(), now=SENT)
        self.assertEqual(self.snapshot(), before)

    def test_legacy_known_by_is_used_without_minting_an_earlier_first_save(self):
        self.store.connection.execute('DELETE FROM record_availability WHERE entity_type=? AND entity_id=?', ('source', self.qa['id']))
        with self.store.transaction(): RecordAvailability(self.store.connection).observe_existing('source', self.qa['id'], self.qa, now=BEFORE)
        saved = self.save(); self.assertEqual(self.check(saved)['reason_codes'], [])
        receipt = RecordAvailability(self.store.connection).get('source', self.qa['id'])
        self.assertIsNone(receipt['first_saved_at']); self.assertEqual(receipt['basis'], 'legacy_presence')

    def test_late_legacy_presence_remains_unknown_for_the_claimed_review_time(self):
        self.store.connection.execute('DELETE FROM record_availability WHERE entity_type=? AND entity_id=?', ('source', self.qa['id']))
        with self.store.transaction(): RecordAvailability(self.store.connection).observe_existing('source', self.qa['id'], self.qa, now=CREATED)
        saved = self.save(); self.assertIn('public_information_review_source_availability_unresolved', self.check(saved)['reason_codes'])
        self.assertIn('legacy_history_unknown', self.check(saved)['availability_at_review'][self.qa['id']]['reason_codes'])

    def test_runtime_correction_on_review_only_ir_blocks_historical_send_without_rewriting(self):
        self.ir_source(); q = self.question(); saved = self.save(q)
        self.correct('unclear', SENT + timedelta(minutes=1)); before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'needs review'):
            self.harness.mark_sent(q['id'], SENT.isoformat(), now=SENT + timedelta(minutes=2))
        self.assertEqual(self.snapshot(), before); self.assertEqual(self.save(q), saved)
        check = DecisionLifecycle(self.store).review_public_information(q, as_of=SENT.isoformat(), now=(SENT + timedelta(minutes=2)).isoformat())
        self.assertEqual(check['information_reviews']['at_boundary'], {})
        self.assertEqual(check['information_reviews']['at_runtime']['prior-reply']['information_status'], 'unclear')

    def test_correction_at_question_boundary_not_hidden_by_later_reaffirmation(self):
        self.ir_source(); self.correct('unclear', CREATED - timedelta(seconds=10))
        self.correct('public_clarification', CREATED + timedelta(seconds=10), version=1)
        saved = self.save(); check = self.check(saved)
        self.assertEqual(check['information_reviews']['at_review'], {})
        self.assertEqual(check['information_reviews']['at_boundary']['prior-reply']['information_status'], 'unclear')
        self.assertEqual(check['information_reviews']['at_runtime']['prior-reply']['information_status'], 'public_clarification')
        self.assertIn('public_information_review_information_held_for_review', check['reason_codes'])

    def test_other_company_reply_subject_is_not_accepted_through_same_company_source(self):
        self.ir_source(other_company=True); before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'reply belongs to another company'): self.save()
        self.assertEqual(self.snapshot(), before)

    def test_same_company_reply_with_different_content_is_not_a_correction_subject(self):
        self.ir_source()
        other = deepcopy(self.qa)
        other.update(id='different-content-source', content='A different synthetic explanation, not this reply.')
        self.store.put_source(validate_source(other), now=BEFORE); self.qa = other
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'differs from its saved reply'): self.save()
        self.assertEqual(self.snapshot(), before)

    def test_saved_reply_and_question_row_identities_must_match_the_references(self):
        self.ir_source()
        for table, identity in (('replies', 'prior-reply'), ('questions', 'prior-question')):
            original = self.store.connection.execute('SELECT data FROM ' + table + ' WHERE id=?', (identity,)).fetchone()[0]
            damaged = json.loads(original); damaged['id'] = 'different-stored-id'
            self.store.connection.execute('UPDATE ' + table + ' SET data=? WHERE id=?', (json_text(damaged), identity))
            before = self.snapshot()
            with self.subTest(table=table), self.assertRaisesRegex(ValueError, 'identity mismatch'): self.save()
            self.assertEqual(self.snapshot(), before)
            self.store.connection.execute('UPDATE ' + table + ' SET data=? WHERE id=?', (original, identity))

    def test_persistent_long_valid_chain_uses_one_flat_receipt_check_per_source(self):
        root = source('long-root'); nodes = [root]; previous = root
        for index in range(1100):
            parent = source('long-parent-' + str(index))
            previous['metadata']['original_source_id'] = parent['id']
            nodes.append(parent); previous = parent
        for node in nodes: self.store.put_source(validate_source(node), now=BEFORE)
        self.qa = root
        original_at = RecordAvailability.at
        with patch.object(self.store, 'source_availability', side_effect=AssertionError('recursive reader used')):
            with patch.object(RecordAvailability, 'at', autospec=True, side_effect=original_at) as checks:
                saved = self.save(self.question(contracted=False))
            self.assertEqual(checks.call_count, len(nodes))
            check = self.check(saved)
            self.assertEqual(len(check['availability_at_review']), len(nodes))
            self.assertTrue(all(value['available'] is True for value in check['availability_at_review'].values()))
            self.assertEqual(check['reason_codes'], [])
            sent = self.harness.mark_sent(saved['id'], SENT.isoformat(), now=SENT)
            self.assertEqual(sent['status'], 'awaiting_reply')

    def test_flat_receipts_still_check_ancestors_not_just_direct_review_sources(self):
        parent = self.qa; root = source('derived-review-root')
        root['metadata']['original_source_id'] = parent['id']
        self.store.put_source(validate_source(root), now=BEFORE); self.qa = root
        self.store.connection.execute('UPDATE record_availability SET first_saved_at=?,presence_observed_at=? WHERE entity_type=? AND entity_id=?',
            (CREATED.isoformat(), CREATED.isoformat(), 'source', parent['id']))
        saved = self.save(self.question(contracted=False)); check = self.check(saved)
        self.assertTrue(check['availability_at_review'][root['id']]['available'])
        self.assertFalse(check['availability_at_review'][parent['id']]['available'])
        self.assertIn('first_saved_after_knowledge_at', check['availability_at_review'][parent['id']]['reason_codes'])
        self.assertIn('public_information_review_source_availability_unresolved', check['reason_codes'])

    def test_missing_ancestor_remains_a_hold_after_flat_receipt_checks(self):
        root = source('missing-ancestor-root'); root['metadata']['original_source_id'] = 'not-saved'
        self.store.put_source(validate_source(root), now=BEFORE); self.qa = root
        saved = self.save(self.question(contracted=False)); check = self.check(saved)
        self.assertIn('missing_origin_source_snapshot', check['reason_codes'])
        self.assertEqual(set(check['availability_at_review']), {root['id']})
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'needs review'):
            self.harness.mark_sent(saved['id'], SENT.isoformat(), now=SENT)
        self.assertEqual(self.snapshot(), before)

    def test_insert_and_question_receipt_roll_back_atomically(self):
        before = self.snapshot()
        with patch('ir_agent.availability.RecordAvailability.record_first_save', side_effect=ValueError('injected receipt failure')):
            with self.assertRaisesRegex(ValueError, 'injected receipt'): self.save()
        self.assertEqual(self.snapshot(), before)

    def test_invalid_binding_and_unknown_root_leave_no_partial_question(self):
        for mode in ('hash', 'quote', 'unknown'):
            q = self.question(); item = q['public_information_review']['sources'][0]
            if mode == 'hash': item['source_snapshot_sha256'] = '0' * 64
            elif mode == 'quote': item['basis_quote'] = 'Absent quote'
            else: item['source_id'] = 'unknown'
            before = self.snapshot()
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.save(q)
            self.assertEqual(self.snapshot(), before)

    def test_unintroduced_legacy_question_keeps_old_fields_and_send_behavior(self):
        q = self.question(contracted=False); q.pop('public_information_review'); saved = self.save(q)
        self.assertNotIn('public_information_review', saved); self.assertNotIn('public_information_review_check', saved)
        self.assertEqual(self.save(q), saved)
        sent = self.harness.mark_sent(q['id'], SENT.isoformat(), now=SENT)
        self.assertEqual(sent['status'], 'awaiting_reply'); self.assertNotIn('public_information_review_check', sent)

    def test_unintroduced_same_named_extra_json_retains_legacy_no_feature_meaning(self):
        q = self.question(contracted=False); q.pop('public_information_review')
        q['public_information_review_check'] = {'legacy_extra_json': True, 'reason_codes': ['not_a_server_check']}
        saved = self.save(q)
        self.assertEqual(saved['public_information_review_check'], q['public_information_review_check'])
        self.assertEqual(self.save(q), saved)
        sent = self.harness.mark_sent(q['id'], SENT.isoformat(), now=SENT)
        self.assertEqual(sent['status'], 'awaiting_reply')
        self.assertNotIn('public_information_review', sent)


if __name__ == '__main__': unittest.main()
