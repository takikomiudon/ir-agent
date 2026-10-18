"""Synthetic baseline commitments; no external sends, quotes or actual DBs."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import unittest

from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.harness import Harness
from ir_agent.models import json_text
from ir_agent.research_decisions import ResearchDecisions
from ir_agent.store import Store
from ir_agent.availability import RecordAvailability
from test_decision import plan

NOW = datetime.fromisoformat('2026-10-09T10:00:00+09:00')
BEFORE = NOW - timedelta(minutes=1)
CREATED = NOW + timedelta(minutes=1)
SAVED = NOW + timedelta(minutes=2)
SENT = NOW + timedelta(minutes=5)


class QuestionBaselineBindingTests(unittest.TestCase):
    def setUp(self):
        self.value = plan()
        self.store = Store(':memory:')
        self.addCleanup(self.store.close)
        self.harness = Harness(self.store)
        self.company = self.value['thesis']['company_id']
        self.harness.ingest({'schema_version': 1, 'companies': [
            {'id': self.company, 'name': 'Synthetic baseline company', 'status': 'active'}],
            'sources': self.value['sources'], 'theses': [self.value['thesis']]}, now=BEFORE)
        self.harness.register_decision_policy(self.value['policy'], now=BEFORE)
        self.store.declare_position(self.company, False, now=BEFORE)

    def baseline(self, *, identity='before-question', status='intact', now=NOW, quote=None):
        return self.harness.review_research_decision({
            'id': identity, 'company_id': self.company,
            'expected_thesis_version': self.store.thesis(self.company)['version'],
            'policy_id': self.value['policy']['id'], 'policy_version': 1, 'synthetic': True,
            'decision_quote': deepcopy(self.value['quote'] if quote is None else quote),
            'assessment': {'thesis_status': status,
                'evidence_ids': self.store.thesis(self.company)['evidence_ids'][:1],
                'reviewer': 'synthetic reviewer', 'rationale': 'Synthetic baseline assessment.'}}, now=now)

    def question(self, *, baseline='before-question', created=CREATED):
        question = deepcopy(self.value['question'])
        question['thesis_version'] = self.store.thesis(self.company)['version']
        question['created_at'] = created.isoformat()
        question['decision_contract'] = {
            'policy_id': self.value['policy']['id'], 'policy_version': 1,
            'quote': deepcopy(self.value['quote']), 'synthetic': True}
        if baseline is not None:
            question['decision_contract']['research_baseline_id'] = baseline
        return question

    def save(self, question=None):
        return self.harness.add_question(question or self.question(), now=SAVED)

    def snapshot(self):
        return tuple(self.store.connection.iterdump())

    def mutate_record(self, change):
        row = self.store.connection.execute(
            'SELECT data FROM research_decision_reviews WHERE id=?', ('before-question',)).fetchone()
        record = json.loads(row['data'])
        change(record)
        self.store.connection.execute('UPDATE research_decision_reviews SET data=? WHERE id=?',
                                      (json_text(record), 'before-question'))

    def test_binding_freezes_record_not_current_view_and_retries_exactly(self):
        baseline = self.baseline()
        saved = self.save()
        binding = saved['decision_contract']['research_baseline_binding']
        self.assertEqual(binding['record_sha256'], sha256(json_text(baseline['record']).encode()).hexdigest())
        self.assertEqual(binding['first_saved_at'], baseline['first_saved_at'])
        self.assertEqual(binding['recorded_at'], baseline['record']['recorded_at'])
        self.assertEqual(binding['basis'], baseline['record']['basis'])
        self.assertNotIn('current_view', binding)
        self.assertTrue(binding['basis']['public_only'])
        self.assertEqual(saved['decision_contract']['preflight']['question_value'], 'decision_distinguishing')
        self.assertEqual(self.save(), saved)
        self.assertEqual(self.store.connection.execute('SELECT COUNT(*) FROM research_decision_reviews').fetchone()[0], 1)

    def test_legacy_contract_resend_and_no_baseline_behavior_unchanged(self):
        question = self.question(baseline=None)
        saved = self.save(question)
        self.assertNotIn('research_baseline_id', saved['decision_contract'])
        self.assertNotIn('research_baseline_binding', saved['decision_contract'])
        self.assertEqual(self.save(question), saved)
        self.assertEqual(saved['decision_contract']['preflight']['question_value'], 'decision_distinguishing')

    def test_baseline_addition_removal_and_replacement_are_not_retries(self):
        self.baseline()
        self.save()
        before = self.snapshot()
        for identity in (None, 'replacement'):
            with self.subTest(identity=identity), self.assertRaisesRegex(ValueError, 'immutable'):
                self.save(self.question(baseline=identity))
            self.assertEqual(self.snapshot(), before)
        self.harness.close_question(self.value['question']['id'], 'cancelled')
        question = self.question(baseline=None)
        question['id'] = 'old-without-baseline'
        self.save(question)
        before = self.snapshot()
        question['decision_contract']['research_baseline_id'] = 'before-question'
        with self.assertRaisesRegex(ValueError, 'immutable'):
            self.save(question)
        self.assertEqual(self.snapshot(), before)

    def test_caller_cannot_supply_binding_snapshots_or_unknown_baseline(self):
        for key in ('research_baseline_binding', 'research_baseline_sha256', 'current_view'):
            with self.subTest(key=key):
                question = self.question()
                question['decision_contract'][key] = {}
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    self.save(question)
                self.assertEqual(self.snapshot(), before)
        with self.assertRaisesRegex(ValueError, 'Unknown research baseline'):
            self.save()

    def test_baseline_actual_first_save_and_recording_cannot_postdate_question(self):
        self.baseline()
        question = self.question(created=NOW - timedelta(seconds=1))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'before question creation'):
            self.save(question)
        self.assertEqual(self.snapshot(), before)
        self.store.connection.execute('UPDATE research_decision_reviews SET first_saved_at=?',
                                      ((CREATED + timedelta(seconds=1)).isoformat(),))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'before question creation'):
            self.save()
        self.assertEqual(self.snapshot(), before)
        self.store.connection.execute('UPDATE research_decision_reviews SET first_saved_at=?',
                                      (NOW.isoformat(),))
        self.mutate_record(lambda record: record.update(recorded_at=(CREATED + timedelta(seconds=1)).isoformat()))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'before question creation'):
            self.save()
        self.assertEqual(self.snapshot(), before)

    def test_baseline_quote_mismatch_is_rejected_even_when_price_is_equivalent(self):
        self.baseline()
        question = self.question()
        question['decision_contract']['quote']['price_jpy'] = '1000.0'
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'same quote snapshot'):
            self.save(question)
        self.assertEqual(self.snapshot(), before)

    def test_thesis_policy_and_synthetic_mismatches_do_not_write_questions(self):
        self.baseline()
        original = self.store.connection.execute('SELECT data FROM research_decision_reviews').fetchone()[0]
        for key, value in (('company_id', 'other'), ('thesis_version', 2),
                           ('thesis_sha256', '0' * 64), ('policy_id', 'other-policy'), ('policy_version', 2),
                           ('policy_sha256', '0' * 64), ('synthetic', False)):
            with self.subTest(key=key):
                self.store.connection.execute('UPDATE research_decision_reviews SET data=?', (original,))
                self.mutate_record(lambda record: record.update({key: value}))
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    self.save()
                self.assertEqual(self.snapshot(), before)

    def test_subset_evidence_new_same_held_observation_and_branch_status_are_allowed(self):
        extra = deepcopy(self.value['sources'][0])
        extra.update(id='second-public-premise', content='Synthetic second public premise')
        self.store.put_source(extra, now=BEFORE)
        # Append a real fixture version before the baseline; never rewrite v1.
        thesis = self.store.thesis(self.company)
        thesis.update(version=2, recorded_at=BEFORE.isoformat())
        thesis['evidence_ids'].append(extra['id'])
        self.store.put_thesis(thesis, now=BEFORE)
        baseline = self.baseline(status='invalidated')
        position = self.store.declare_position(self.company, False, now=CREATED)
        question = self.question()
        question['evidence_ids'] = [extra['id']]
        saved = self.save(question)
        self.assertNotEqual(baseline['record']['position_snapshot']['observation_id'], position['observation_id'])
        self.assertNotEqual(baseline['record']['assessment']['evidence_ids'], question['evidence_ids'])
        self.assertEqual(saved['decision_contract']['preflight']['question_value'], 'decision_distinguishing')

    def test_changed_effective_held_or_unknown_question_position_cannot_bypass_binding(self):
        self.baseline()
        self.store.declare_position(self.company, True, now=CREATED)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'effective position differs'):
            self.save()
        self.assertEqual(self.snapshot(), before)
        self.store.connection.execute('DELETE FROM position_declarations')
        saved = self.save()
        self.assertEqual(saved['decision_contract']['preflight']['question_value'], 'needs_review')
        self.assertIn('research_baseline_position_unknown',
                      saved['decision_contract']['preflight']['research_baseline_reason_codes'])

    def test_unresolved_baseline_stays_a_hold_when_branches_become_distinguishing(self):
        baseline = self.baseline(status='uncertain')
        saved = self.save()
        preflight = saved['decision_contract']['preflight']
        self.assertEqual(preflight['question_value'], 'needs_review')
        self.assertIn('research_baseline_unresolved', preflight['research_baseline_reason_codes'])
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'needs review'):
            self.harness.mark_sent(saved['id'], SENT.isoformat(), now=SENT)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(ResearchDecisions(self.store).show_review('before-question', now=SENT)['record'], baseline['record'])

    def test_verify_rejects_changed_baseline_record_or_actual_first_save(self):
        self.baseline()
        saved = self.save()
        original = self.store.connection.execute('SELECT data FROM research_decision_reviews').fetchone()[0]
        self.mutate_record(lambda record: record['assessment'].update(rationale='changed after commitment'))
        with self.assertRaisesRegex(ValueError, 'binding differs'):
            DecisionLifecycle(self.store).verify_saved_contract(saved)
        self.store.connection.execute('UPDATE research_decision_reviews SET data=?', (original,))
        self.store.connection.execute('UPDATE research_decision_reviews SET first_saved_at=?', (BEFORE.isoformat(),))
        with self.assertRaisesRegex(ValueError, 'binding differs'):
            DecisionLifecycle(self.store).verify_saved_contract(saved)

    def test_current_source_snapshot_changes_cannot_be_hidden(self):
        self.baseline()
        source = self.store.source(self.value['sources'][0]['id'])
        source['content'] = 'Changed saved original'
        self.store.connection.execute('UPDATE sources SET data=? WHERE id=?', (json_text(source), source['id']))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'source closure or snapshot SHA'):
            self.save()
        self.assertEqual(self.snapshot(), before)

    def test_source_receipts_after_question_creation_keep_draft_unresolved(self):
        self.baseline()
        self.store.connection.execute(
            'UPDATE record_availability SET first_saved_at=?,presence_observed_at=? WHERE entity_type=?',
            (SAVED.isoformat(), SAVED.isoformat(), 'source'))
        saved = self.save()
        self.assertIn('research_baseline_source_availability_unresolved',
                      saved['decision_contract']['preflight']['research_baseline_reason_codes'])
        with self.assertRaisesRegex(ValueError, 'needs review'):
            self.harness.mark_sent(saved['id'], SENT.isoformat(), now=SENT)

    def test_historical_send_uses_sent_at_price_and_position_not_current_view(self):
        self.baseline()
        saved = self.save()
        later = NOW + timedelta(hours=2)
        self.store.declare_position(self.company, True, now=later)
        view = ResearchDecisions(self.store).show_review('before-question', now=later)['current_view']
        self.assertIn('requires_price_review', view['current_review_requirements'])
        self.assertIn('requires_position_review', view['current_review_requirements'])
        sent = self.harness.mark_sent(saved['id'], SENT.isoformat(), now=later)
        self.assertEqual(sent['status'], 'awaiting_reply')

    def quote_only_ir(self):
        question = {'id': 'earlier-question', 'company_id': self.company, 'created_at': BEFORE.isoformat()}
        reply = {'id': 'earlier-reply', 'question_id': question['id'], 'received_at': BEFORE.isoformat(),
                 'raw_text': 'Synthetic public clarification', 'information_status': 'public_clarification'}
        with self.store.transaction():
            self.store.connection.execute('INSERT INTO questions VALUES (?,?,?,?,?,?,?,?)',
                (question['id'], self.company, 'prior', 'answered', json_text(question), BEFORE.isoformat(), None, None))
            self.store.connection.execute('INSERT INTO replies VALUES (?,?,?)', (reply['id'], question['id'], json_text(reply)))
            ledger = RecordAvailability(self.store.connection)
            for kind, record in (('question', question), ('reply', reply)):
                ledger.record_first_save(kind, record['id'], record, now=BEFORE.isoformat())
        source = {'id': 'quote-only-IR-parent', 'company_id': self.company, 'title': 'Synthetic IR parent',
                  'url': 'https://example.invalid/prior', 'source_type': 'ir_reply', 'published_at': None,
                  'retrieved_at': BEFORE.isoformat(), 'content': reply['raw_text'],
                  'metadata': {'reply_id': reply['id'], 'information_status': 'public_clarification'}}
        self.store.put_source(source, now=BEFORE)
        quote_source = deepcopy(self.value['sources'][1])
        quote_source['id'] = 'quote-with-IR-parent'
        quote_source['metadata']['original_source_id'] = source['id']
        self.store.put_source(quote_source, now=BEFORE)
        self.value['quote']['source_id'] = quote_source['id']
        return reply['id']

    def test_prior_ir_is_not_public_only_and_quote_only_current_correction_blocks_send(self):
        reply_id = self.quote_only_ir()
        baseline = self.baseline()
        self.assertEqual(baseline['record']['result']['status'], 'reviewed')
        saved = self.save()
        self.assertFalse(saved['decision_contract']['research_baseline_binding']['basis']['public_only'])
        self.assertTrue(saved['decision_contract']['research_baseline_binding']['basis']['has_IR_reply_origin'])
        later = NOW + timedelta(hours=2)
        review = {'reply_id': reply_id, 'version': 1, 'recorded_at': later.isoformat(),
                  'information_status': 'potential_nonpublic'}
        self.store.connection.execute('INSERT INTO reply_information_reviews VALUES (?,?,?,?)',
                                      (reply_id, 1, json_text(review), later.isoformat()))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'needs review'):
            self.harness.mark_sent(saved['id'], SENT.isoformat(), now=later)
        self.assertEqual(self.snapshot(), before)

    def test_baseline_current_source_holds_are_checked_during_freeze(self):
        reply_id = self.quote_only_ir()
        self.baseline()
        review = {'reply_id': reply_id, 'version': 1, 'recorded_at': SAVED.isoformat(),
                  'information_status': 'unclear'}
        self.store.connection.execute('INSERT INTO reply_information_reviews VALUES (?,?,?,?)',
                                      (reply_id, 1, json_text(review), SAVED.isoformat()))
        saved = self.save()
        self.assertIn('research_baseline_information_held_for_review',
                      saved['decision_contract']['preflight']['research_baseline_reason_codes'])

    def test_new_public_classification_is_not_consumed_by_old_baseline(self):
        reply_id = self.quote_only_ir()
        self.baseline()
        review = {'reply_id': reply_id, 'version': 1, 'recorded_at': SAVED.isoformat(),
                  'information_status': 'public_clarification'}
        self.store.connection.execute('INSERT INTO reply_information_reviews VALUES (?,?,?,?)',
                                      (reply_id, 1, json_text(review), SAVED.isoformat()))
        saved = self.save()
        self.assertIn('research_baseline_information_review_changed',
                      saved['decision_contract']['preflight']['research_baseline_reason_codes'])

    def test_prior_ir_cannot_be_relabelled_public_only_or_contain_own_reply(self):
        self.quote_only_ir()
        self.baseline()
        original = self.store.connection.execute('SELECT data FROM research_decision_reviews').fetchone()[0]
        self.mutate_record(lambda record: record['basis'].update(public_only=True))
        with self.assertRaisesRegex(ValueError, 'origin distinction'):
            self.save()
        self.store.connection.execute('UPDATE research_decision_reviews SET data=?', (original,))
        question = self.question()
        question['id'] = 'earlier-question'
        with self.assertRaisesRegex(ValueError, 'own reply'):
            DecisionLifecycle(self.store).freeze(question, self.store.thesis(self.company), SAVED.isoformat())


if __name__ == '__main__':
    unittest.main()
