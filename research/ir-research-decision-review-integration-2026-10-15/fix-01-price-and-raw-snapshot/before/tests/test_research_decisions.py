"""Synthetic in-memory fault tests for reply-independent saved price reviews."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr

from ir_agent.availability import RecordAvailability
from ir_agent.cli import main
from ir_agent.harness import Harness
from ir_agent.models import json_text
from ir_agent.research_decisions import ResearchDecisions
from ir_agent.store import Store
from test_decision import request as synthetic_decision

NOW = datetime.fromisoformat('2026-10-09T10:00:00+09:00')
BEFORE = NOW - timedelta(minutes=1)


class ResearchDecisionTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(':memory:')
        self.addCleanup(self.store.close)
        self.harness = Harness(self.store)
        self.value = synthetic_decision()  # All values/policies are synthetic.
        self.company = self.value['thesis']['company_id']
        self.harness.ingest({'schema_version': 1, 'companies': [
            {'id': self.company, 'name': '架空研究会社', 'held': False, 'status': 'active'}],
            'sources': self.value['sources'], 'theses': [self.value['thesis']]}, now=BEFORE)
        self.harness.register_decision_policy(self.value['policy'], now=BEFORE)
        self.store.declare_position(self.company, False, now=BEFORE)
        self.reviews = ResearchDecisions(self.store)

    def request(self, **updates):
        request = {'id': 'synthetic-research-baseline', 'company_id': self.company,
            'expected_thesis_version': 1, 'policy_id': self.value['policy']['id'], 'policy_version': 1,
            'decision_quote': deepcopy(self.value['quote']), 'synthetic': True,
            'assessment': {'thesis_status': 'intact', 'evidence_ids': self.value['thesis']['evidence_ids'],
                           'reviewer': 'synthetic agent fixture', 'rationale': 'Synthetic evidence supports the chosen thesis status; no real company forecast.'}}
        request.update(updates)
        return request

    def add(self, value=None, *, now=NOW):
        return self.harness.review_research_decision(value or self.request(), now=now)

    def count(self):
        return self.store.connection.execute('SELECT COUNT(*) FROM research_decision_reviews').fetchone()[0]

    def next_thesis(self, evidence=None, *, recorded=NOW, save=NOW):
        thesis = deepcopy(self.store.thesis(self.company))
        thesis.update(version=thesis['version'] + 1, recorded_at=recorded.isoformat())
        if evidence is not None:
            thesis['evidence_ids'] = evidence
        self.store.put_thesis(thesis, now=save)
        return thesis

    def extra_source(self, identity, *, kind='public_disclosure', parents=None, metadata=None, content='Synthetic additional document'):
        source = {'id': identity, 'company_id': self.company, 'title': 'Synthetic extra original',
                  'url': 'https://example.invalid/synthetic', 'source_type': kind,
                  'published_at': None, 'retrieved_at': BEFORE.isoformat(), 'content': content,
                  'metadata': {'synthetic': True, **(metadata or {})}}
        if parents is not None:
            source['metadata']['original_source_ids'] = parents
        self.store.put_source(source, now=BEFORE)
        return source

    def ir_origin(self, *, information='public_clarification', source_information='public_clarification', with_binding=True):
        reply_id = 'synthetic-prior-reply'
        if with_binding:
            question = {'id': 'synthetic-prior-question', 'company_id': self.company,
                        'created_at': BEFORE.isoformat(), 'question': 'Synthetic public definition?'}
            reply = {'id': reply_id, 'question_id': question['id'], 'received_at': BEFORE.isoformat(),
                     'raw_text': 'Synthetic public clarification', 'information_status': information}
            with self.store.transaction():
                self.store.connection.execute('INSERT INTO questions VALUES (?,?,?,?,?,?,?,?)',
                    (question['id'], self.company, 'synthetic', 'answered', json_text(question), None, None, None))
                self.store.connection.execute('INSERT INTO replies VALUES (?,?,?)', (reply_id, question['id'], json_text(reply)))
                ledger = RecordAvailability(self.store.connection)
                ledger.record_first_save('question', question['id'], question, now=BEFORE.isoformat())
                ledger.record_first_save('reply', reply_id, reply, now=BEFORE.isoformat())
        source = self.extra_source('synthetic-IR-origin', kind='ir_reply',
            metadata={'reply_id': reply_id, 'information_status': source_information}, content='Synthetic public clarification')
        return source

    def quote_parent(self, parent):
        source = deepcopy(self.value['sources'][1])
        source['id'] = 'synthetic-quote-with-parent'
        source['metadata']['original_source_ids'] = [parent]
        self.store.put_source(source, now=BEFORE)
        quote = deepcopy(self.value['quote']); quote['source_id'] = source['id']
        return quote

    def classification(self, status, version, when):
        value = {'reply_id': 'synthetic-prior-reply', 'version': version,
                 'recorded_at': when.isoformat(), 'information_status': status}
        self.store.connection.execute('INSERT INTO reply_information_reviews VALUES (?,?,?,?)',
            (value['reply_id'], version, json_text(value), when.isoformat()))

    def test_public_baseline_saves_bound_inputs_without_questions_or_other_writes(self):
        tables = ['companies', 'sources', 'theses', 'decision_policies', 'questions', 'replies',
                  'evaluations', 'decision_reviews', 'record_availability']
        before = {t: self.store.connection.execute('SELECT * FROM ' + t).fetchall() for t in tables}
        output = self.add(); record = output['record']
        self.assertTrue(output['added'])
        self.assertEqual(record['basis']['kind'], 'saved_research')
        self.assertTrue(record['basis']['public_only'])
        self.assertFalse(record['basis']['has_IR_reply_origin'])
        self.assertEqual(record['result']['proposed_action'], 'buy_review')
        self.assertEqual(record['recorded_at'], NOW.astimezone(timezone.utc).isoformat())
        self.assertEqual(output['first_saved_at'], NOW.astimezone(timezone.utc).isoformat())
        self.assertEqual(record['policy_snapshot'], self.value['policy'])
        self.assertEqual(record['position_snapshot']['kind'], 'user_declaration')
        self.assertEqual(set(record['source_ids']), {s['id'] for s in self.value['sources']})
        self.assertEqual(output['current_view']['result'], record['result'])
        self.assertTrue(record['assessment_is_reviewer_assertion_not_engine_fact'])
        self.assertFalse(record['financial_inputs_verified'])
        for table in tables:
            self.assertEqual(self.store.connection.execute('SELECT * FROM ' + table).fetchall(), before[table], table)

    def test_exact_retry_precedes_latest_CAS_and_keeps_first_save_with_current_hold(self):
        value = self.request(); first = self.add(value)
        self.next_thesis(recorded=NOW + timedelta(seconds=1), save=NOW + timedelta(seconds=1))
        retried = self.add(value, now=NOW + timedelta(seconds=2))
        self.assertFalse(retried['added'])
        self.assertEqual(retried['record'], first['record'])
        self.assertEqual(retried['first_saved_at'], first['first_saved_at'])
        self.assertIn('requires_thesis_review', retried['current_view']['current_review_requirements'])
        self.assertEqual(retried['current_view']['result']['proposed_action'], 'unresolved')
        self.assertEqual(self.count(), 1)

    def test_changed_request_same_id_rejected_and_new_id_checks_latest_version(self):
        self.add()
        for changes in ({'assessment': {**self.request()['assessment'], 'rationale': 'changed'}}, {'policy_version': 2}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.add(self.request(**changes))
        self.next_thesis(recorded=NOW + timedelta(seconds=1), save=NOW + timedelta(seconds=1))
        with self.assertRaises(ValueError):
            self.add(self.request(id='new-id'), now=NOW + timedelta(seconds=2))
        self.assertEqual(self.count(), 1)

    def test_caller_clocks_held_action_and_snapshots_are_rejected(self):
        for key in ('as_of', 'recorded_at', 'held', 'action', 'first_saved_at', 'thesis', 'sources', 'policy', 'reply_id'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.add(self.request(**{key: 'not accepted'}))
        self.assertEqual(self.count(), 0)

    def test_empty_valid_quote_or_unset_policy_is_unresolved_without_defaults(self):
        empty = self.add(self.request(decision_quote={}))
        self.assertEqual(empty['record']['result']['proposed_action'], 'unresolved')
        self.assertIn('missing_market_quote', empty['record']['result']['reason_codes'])
        policy = deepcopy(self.value['policy']); policy['version'] = 2; policy['parameters']['minimum_upside_pct'] = None
        self.harness.register_decision_policy(policy, now=BEFORE)
        output = self.add(self.request(id='missing-policy-value', policy_version=2))
        self.assertEqual(output['record']['result']['reason_codes'], ['policy_not_configured'])
        self.assertIsNone(output['record']['policy_snapshot']['parameters']['minimum_upside_pct'])

    def test_invalid_quote_binding_rejected_even_when_position_or_policy_missing(self):
        self.store.connection.execute('DELETE FROM position_declarations')
        policy = deepcopy(self.value['policy']); policy['version'] = 2; policy['parameters']['minimum_upside_pct'] = None
        self.harness.register_decision_policy(policy, now=BEFORE)
        for changes in ({'price_jpy': '999'}, {'company_id': 'another-company'}, {'price_path': ['content', 'missing']},
                        {'observed_at': '2026-10-09T09:54:00+09:00'}, {'retrieved_at': '2026-10-09T09:57:00+09:00'}):
            quote = {**self.value['quote'], **changes}
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.add(self.request(policy_version=2, decision_quote=quote))
        self.assertEqual(self.count(), 0)

    def test_partial_quote_missingness_does_not_mask_a_supplied_wrong_price(self):
        quote = deepcopy(self.value['quote']); quote.pop('observed_at')
        output = self.add(self.request(decision_quote=quote))
        self.assertEqual(output['record']['result']['proposed_action'], 'unresolved')
        quote['price_jpy'] = '999'
        with self.assertRaisesRegex(ValueError, 'price'):
            self.add(self.request(id='bad-partial-price', decision_quote=quote))
        self.assertEqual(self.count(), 1)

    def test_imported_flat_is_unknown_and_does_not_invent_position(self):
        self.store.connection.execute('DELETE FROM position_declarations')
        output = self.add()
        self.assertIsNone(output['record']['position_snapshot'])
        self.assertEqual(output['record']['result']['proposed_action'], 'unresolved')
        self.assertIn('position_history_unknown', output['record']['result']['reason_codes'])

    def test_new_undeclared_observation_does_not_fall_back_to_prior_declaration(self):
        self.store.connection.execute('INSERT INTO position_observations(company_id,observed_at,held) VALUES (?,?,?)',
            (self.company, NOW.astimezone(timezone.utc).isoformat(), 0))
        self.assertIsNone(self.add()['record']['position_snapshot'])

    def test_fixed_policy_version_is_not_replaced_by_newer_registry_policy(self):
        policy = deepcopy(self.value['policy']); policy['version'] = 2; policy['parameters']['minimum_upside_pct'] = '999'
        self.harness.register_decision_policy(policy, now=BEFORE)
        output = self.add()
        self.assertEqual(output['record']['policy_version'], 1)
        self.assertEqual(output['record']['result']['policy_version'], 1)
        self.assertEqual(output['record']['result']['proposed_action'], 'buy_review')

    def test_unrelated_legacy_old_version_does_not_blanket_hold_valid_latest(self):
        thesis = self.next_thesis(recorded=BEFORE, save=BEFORE)
        self.store.connection.execute("DELETE FROM record_availability WHERE entity_type='thesis' AND version=1")
        output = self.add(self.request(expected_thesis_version=thesis['version']))
        self.assertEqual(output['record']['availability']['thesis_selection']['availability_status'], 'partial')
        self.assertEqual(output['record']['result']['proposed_action'], 'buy_review')
        self.assertEqual(output['current_view']['result']['proposed_action'], 'buy_review')

    def test_unknown_latest_never_falls_back_to_usable_old_thesis(self):
        thesis = deepcopy(self.value['thesis']); thesis['version'] = 2
        self.store.connection.execute('INSERT INTO theses VALUES (?,?,?)', (self.company, 2, json_text(thesis)))
        output = self.add(self.request(expected_thesis_version=2))
        self.assertEqual(output['record']['thesis_version'], 2)
        self.assertEqual(output['record']['availability']['thesis_selection']['record']['version'], 1)
        self.assertEqual(output['record']['result']['proposed_action'], 'unresolved')
        self.assertIn('latest_thesis_availability_unresolved', output['record']['result']['reason_codes'])

    def test_future_latest_is_saved_as_unresolved_not_computed_with_older_snapshot(self):
        thesis = deepcopy(self.value['thesis']); thesis.update(version=2, recorded_at=(NOW + timedelta(hours=1)).isoformat())
        self.store.connection.execute('INSERT INTO theses VALUES (?,?,?)', (self.company, 2, json_text(thesis)))
        output = self.add(self.request(expected_thesis_version=2))
        self.assertEqual(output['record']['thesis_version'], 2)
        self.assertEqual(output['record']['result']['proposed_action'], 'unresolved')

    def test_missing_second_origin_and_unknown_receipt_cannot_be_public_only(self):
        source = self.extra_source('with-missing-origin', parents=['missing-parent'])
        self.next_thesis([source['id']], recorded=BEFORE, save=BEFORE)
        output = self.add(self.request(expected_thesis_version=2,
            assessment={**self.request()['assessment'], 'evidence_ids': [source['id']]}))
        self.assertFalse(output['record']['basis']['public_only'])
        self.assertEqual(output['record']['missing_source_ids'], ['missing-parent'])
        self.assertEqual(output['record']['result']['proposed_action'], 'unresolved')
        self.store.connection.execute("DELETE FROM record_availability WHERE entity_type='source'")
        other = self.add(self.request(id='unknown-receipts', expected_thesis_version=2,
            assessment={**self.request()['assessment'], 'evidence_ids': [source['id']]}))
        self.assertFalse(other['record']['basis']['source_availability_check'])

    def test_cycle_or_cross_company_quote_origin_is_error_before_result(self):
        a = self.extra_source('cycle-a', parents=['cycle-b'])
        self.extra_source('cycle-b', parents=[a['id']])
        with self.assertRaisesRegex(ValueError, 'Cyclic'):
            self.add(self.request(decision_quote=self.quote_parent(a['id'])))
        self.harness.ingest({'schema_version': 1, 'companies': [{'id': 'other', 'name': '架空別社'}]}, now=BEFORE)
        other = deepcopy(a); other.update(id='other-parent', company_id='other', metadata={})
        self.store.put_source(other, now=BEFORE)
        quote = deepcopy(self.value['sources'][1]); quote['id'] = 'quote-other-parent'; quote['metadata']['original_source_id'] = other['id']
        self.store.put_source(quote, now=BEFORE)
        with self.assertRaisesRegex(ValueError, 'company'):
            self.add(self.request(decision_quote={**self.value['quote'], 'source_id': quote['id']}))
        self.assertEqual(self.count(), 0)

    def test_synthetic_second_quote_parent_cannot_enter_real_review(self):
        parent = self.extra_source('synthetic-hidden-parent')
        policy = deepcopy(self.value['policy']); policy['version'] = 2
        for value in policy['parameter_sources'].values():
            value['kind'] = 'external_policy'  # Still a deliberately synthetic test of contamination rejection.
        self.harness.register_decision_policy(policy, now=BEFORE)
        with self.assertRaisesRegex(ValueError, 'Synthetic'):
            self.add(self.request(policy_version=2, synthetic=False, decision_quote=self.quote_parent(parent['id'])))
        self.assertEqual(self.count(), 0)

    def test_shared_valid_parent_is_not_misclassified_as_cycle(self):
        parent = self.extra_source('shared-original')
        left = self.extra_source('left', parents=[parent['id']]); right = self.extra_source('right', parents=[parent['id']])
        self.next_thesis([left['id'], right['id']], recorded=BEFORE, save=BEFORE)
        output = self.add(self.request(expected_thesis_version=2,
            assessment={**self.request()['assessment'], 'evidence_ids': [left['id'], right['id']]}))
        self.assertTrue(output['record']['basis']['public_only'])
        self.assertEqual(output['record']['result']['proposed_action'], 'buy_review')

    def test_public_IR_ancestor_can_be_reviewed_but_never_called_public_only(self):
        source = self.ir_origin()
        output = self.add(self.request(decision_quote=self.quote_parent(source['id'])))
        self.assertTrue(output['record']['basis']['has_IR_reply_origin'])
        self.assertFalse(output['record']['basis']['public_only'])
        self.assertEqual(output['record']['result']['proposed_action'], 'buy_review')
        self.assertIn('synthetic-prior-reply', output['record']['reply_bindings'])

    def test_received_unclear_reply_can_have_a_valid_public_applied_source(self):
        source = self.ir_origin(information='unclear', source_information='public_clarification')
        output = self.add(self.request(decision_quote=self.quote_parent(source['id'])))
        self.assertEqual(output['record']['result']['proposed_action'], 'buy_review')
        self.assertFalse(output['record']['basis']['public_only'])
        binding = output['record']['reply_bindings']['synthetic-prior-reply']
        self.assertEqual(binding['raw_reply_initial_information_status'], 'unclear')
        self.assertEqual(binding['classification_basis'], 'immutable_IR_source_metadata')

    def test_missing_IR_identity_or_underlying_binding_does_not_become_public_only(self):
        source = self.extra_source('unbound-IR', kind='ir_reply', metadata={'information_status': 'public_clarification'})
        output = self.add(self.request(decision_quote=self.quote_parent(source['id'])))
        self.assertFalse(output['record']['basis']['public_only'])
        self.assertIn('origin_reply_identity_missing', output['record']['result']['reason_codes'])
        source = self.ir_origin(with_binding=False)
        quote = deepcopy(self.value['sources'][1]); quote['id'] = 'unknown-reply-quote'; quote['metadata']['original_source_id'] = source['id']
        self.store.put_source(quote, now=BEFORE)
        output = self.add(self.request(id='unknown-reply', decision_quote={**self.value['quote'], 'source_id': quote['id']}))
        self.assertIn('origin_reply_unresolved', output['record']['result']['reason_codes'])
        self.assertFalse(output['record']['basis']['public_only'])

    def test_underlying_reply_content_mismatch_is_atomic_error(self):
        source = self.ir_origin()
        self.store.connection.execute("UPDATE replies SET data=? WHERE id='synthetic-prior-reply'", (json_text({
            'id': 'synthetic-prior-reply', 'question_id': 'synthetic-prior-question',
            'received_at': BEFORE.isoformat(), 'raw_text': 'different', 'information_status': 'public_clarification'}),))
        with self.assertRaisesRegex(ValueError, 'content'):
            self.add(self.request(decision_quote=self.quote_parent(source['id'])))
        self.assertEqual(self.count(), 0)

    def test_immutable_source_hold_survives_later_public_reply_assessment(self):
        source = self.ir_origin(source_information='unclear')
        self.classification('public_clarification', 1, BEFORE)
        output = self.add(self.request(decision_quote=self.quote_parent(source['id'])))
        self.assertEqual(output['record']['result']['proposed_action'], 'unresolved')
        self.assertTrue(output['record']['source_information_holds'])
        self.assertFalse(output['record']['basis']['public_only'])

    def test_new_reply_classification_and_restored_public_version_require_fresh_review(self):
        source = self.ir_origin(); req = self.request(decision_quote=self.quote_parent(source['id']))
        initial = self.add(req)
        self.classification('potential_nonpublic', 1, NOW + timedelta(seconds=1))
        held = self.reviews.show_review(req['id'], now=NOW + timedelta(seconds=2))
        self.assertIn('requires_information_review', held['current_view']['current_review_requirements'])
        self.assertEqual(held['current_view']['result']['proposed_action'], 'unresolved')
        self.classification('public_clarification', 2, NOW + timedelta(seconds=3))
        held = self.reviews.show_review(req['id'], now=NOW + timedelta(seconds=4))
        self.assertIn('requires_information_review', held['current_view']['current_review_requirements'])
        self.assertEqual(held['record'], initial['record'])
        fresh = self.add({**req, 'id': 'new-public-version'}, now=NOW + timedelta(seconds=5))
        self.assertEqual(fresh['record']['context']['information_review_versions'], {'synthetic-prior-reply': 2})
        self.assertEqual(fresh['record']['result']['proposed_action'], 'buy_review')

    def test_quote_expiration_boundary_and_current_hold_do_not_rewrite_history(self):
        initial = self.add()
        boundary = datetime.fromisoformat(self.value['quote']['observed_at']) + timedelta(seconds=3600)
        exact = self.reviews.show_review(initial['record']['id'], now=boundary)
        self.assertEqual(exact['current_view']['current_quote_check']['status'], 'fresh')
        later = self.reviews.show_review(initial['record']['id'], now=boundary + timedelta(microseconds=1))
        self.assertIn('requires_price_review', later['current_view']['current_review_requirements'])
        self.assertEqual(later['current_view']['result']['proposed_action'], 'unresolved')
        self.assertEqual(later['record'], initial['record'])

    def test_current_position_change_unknown_and_redeclare_same_held(self):
        initial = self.add()
        self.store.declare_position(self.company, False, now=NOW + timedelta(seconds=1))
        same = self.reviews.show_review(initial['record']['id'], now=NOW + timedelta(seconds=2))
        self.assertNotIn('requires_position_review', same['current_view']['current_review_requirements'])
        self.store.declare_position(self.company, True, now=NOW + timedelta(seconds=3))
        changed = self.reviews.show_review(initial['record']['id'], now=NOW + timedelta(seconds=4))
        self.assertIn('requires_position_review', changed['current_view']['current_review_requirements'])
        self.store.connection.execute('DELETE FROM position_declarations')
        unknown = self.reviews.show_review(initial['record']['id'], now=NOW + timedelta(seconds=5))
        self.assertEqual(unknown['current_view']['current_position_check']['status'], 'unknown')
        self.assertEqual(unknown['record'], initial['record'])

    def test_current_management_due_and_same_version_receipt_mismatch_hold(self):
        initial = self.add()
        due = self.reviews.show_review(initial['record']['id'], now=datetime.fromisoformat('2026-10-30T00:00:00+09:00'))
        self.assertIn('requires_thesis_review', due['current_view']['current_review_requirements'])
        self.store.connection.execute("UPDATE record_availability SET snapshot_sha256=? WHERE entity_type='thesis'", ('0' * 64,))
        corrupt = self.reviews.show_review(initial['record']['id'], now=NOW + timedelta(seconds=1))
        self.assertIn('requires_thesis_review', corrupt['current_view']['current_review_requirements'])
        self.assertEqual(corrupt['current_view']['result']['proposed_action'], 'unresolved')

    def test_current_view_never_promotes_historically_unresolved_assessment(self):
        value = self.request(assessment={**self.request()['assessment'], 'thesis_status': 'uncertain'})
        initial = self.add(value)
        current = self.reviews.show_review(value['id'], now=NOW + timedelta(seconds=1))
        self.assertEqual(current['current_view']['result']['proposed_action'], 'unresolved')
        self.assertEqual(current['record'], initial['record'])

    def test_insert_and_envelope_failure_roll_back_without_partial_row(self):
        with patch.object(self.reviews, '_envelope', side_effect=ValueError('synthetic postinsert fault')):
            with self.assertRaises(ValueError):
                self.reviews.add_review(self.request(), now=NOW)
        self.assertEqual(self.count(), 0)


class ResearchDecisionCliTests(unittest.TestCase):
    def test_add_show_commands_use_runtime_clock_and_preserve_raw_record(self):
        # Temp database only; all issuer/policy/price inputs come from synthetic_decision.
        with tempfile.TemporaryDirectory() as directory:
            db = str(Path(directory) / 'synthetic.sqlite3')
            store = Store(db); h = Harness(store); value = synthetic_decision(); company = value['thesis']['company_id']
            h.ingest({'schema_version': 1, 'companies': [{'id': company, 'name': '架空CLI会社'}],
                'sources': value['sources'], 'theses': [value['thesis']]}, now=BEFORE)
            h.register_decision_policy(value['policy'], now=BEFORE); store.declare_position(company, False, now=BEFORE); store.close()
            request = {'id': 'synthetic-cli-review', 'company_id': company, 'expected_thesis_version': 1,
                'policy_id': value['policy']['id'], 'policy_version': 1, 'decision_quote': value['quote'], 'synthetic': True,
                'assessment': {'thesis_status': 'intact', 'evidence_ids': value['thesis']['evidence_ids'],
                               'reviewer': 'synthetic CLI', 'rationale': 'synthetic test only'}}
            path = Path(directory) / 'request.json'; path.write_text(json.dumps(request))
            results = []
            with patch('ir_agent.research_decisions._clock', return_value=NOW):
                for command in (['add', str(path)], ['show', request['id']]):
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        code = main(['--db', db, 'research-decision-review', *command])
                    self.assertEqual(code, 0, stderr.getvalue()); results.append(json.loads(stdout.getvalue()))
            self.assertEqual(results[0]['record'], results[1]['record'])
            self.assertTrue(results[0]['added']); self.assertFalse(results[1]['added'])


if __name__ == '__main__':
    unittest.main()
