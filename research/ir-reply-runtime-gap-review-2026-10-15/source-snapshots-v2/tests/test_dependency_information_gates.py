"""Current dependency corrections gate new questions and financial updates."""
from copy import deepcopy
from contextlib import contextmanager
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.harness import Harness
from ir_agent.information_review import add_assessment
from ir_agent.models import json_text
from ir_agent.store import Store
from test_decision import plan


ROOT = Path(__file__).resolve().parents[1]


def clock(value):
    return datetime.fromisoformat(value)


class DependencyInformationGatesTests(unittest.TestCase):
    def setUp(self):
        self.value = plan()
        self.store = Store(':memory:')
        self.addCleanup(self.store.close)
        self.harness = Harness(self.store)
        bundle = self.load('demo.json')
        bundle['theses'] = [self.value['thesis']]
        bundle['sources'].append(self.value['sources'][1])
        self.harness.ingest(bundle, now=clock('2026-10-09T10:00:00+09:00'))
        self.harness.register_decision_policy(self.value['policy'], now=clock('2026-10-09T10:00:00+09:00'))
        self.first_question = deepcopy(self.value['question'])
        self.first_question['decision_contract'] = {
            'policy_id': self.value['policy']['id'], 'policy_version': 1,
            'quote': self.value['quote'], 'synthetic': True,
            'synthetic_position': {'held': True, 'observed_at': '2026-10-09T09:59:00+09:00'},
        }
        self.harness.add_question(self.first_question, now=clock('2026-10-09T10:01:00+09:00'))
        self.harness.mark_sent(self.first_question['id'], '2026-10-09T10:05:00+09:00',
                               now=clock('2026-10-09T10:05:00+09:00'))
        self.first_reply = self.load('reply.json')
        self.harness.add_reply(self.first_reply, now=clock(self.first_reply['received_at']))
        quote = self.quote('first-price', '2026-10-09T17:00:00+09:00')
        evaluation = self.load('reply-evaluation.json')
        evaluation.update(expected_thesis_version=1, decision_quote=quote)
        self.harness.evaluate_reply(evaluation, now=clock('2026-10-09T17:01:00+09:00'))
        self.original = self.store.thesis('demo-services')
        self.original_source = self.store.source('reply:' + self.first_reply['id'])

    def load(self, name):
        return json.loads((ROOT / 'examples' / name).read_bytes())

    def quote(self, source_id, at):
        source = deepcopy(self.value['sources'][1])
        source.update(id=source_id, retrieved_at=at)
        source['metadata']['observed_at'] = at
        self.harness.ingest({'schema_version': 1, 'sources': [source]}, now=clock(at))
        quote = deepcopy(self.value['quote'])
        quote.update(source_id=source_id, retrieved_at=at, observed_at=at)
        return quote

    def correction(self, *, status='unclear', at='2026-10-09T17:09:00+09:00',
                   saved=None, version=0, reply=None):
        reply = reply or self.first_reply
        return add_assessment(self.store, {
            'reply_id': reply['id'], 'expected_version': version, 'information_status': status,
            'basis_quote': reply['raw_text'][:10], 'rationale': 'Synthetic review of public basis only.',
            'recorded_at': at,
        }, now=saved or at)

    def new_question(self, *, legacy=False):
        self.second_quote = self.quote('second-price', '2026-10-09T17:05:00+09:00')
        thesis = self.store.thesis('demo-services')
        question = deepcopy(self.first_question)
        question.update(id='second-question', topic='second-synthetic-review',
                        thesis_version=thesis['version'], evidence_ids=thesis['evidence_ids'],
                        created_at='2026-10-09T17:06:00+09:00')
        if legacy:
            question.pop('decision_contract')
        else:
            question['decision_contract']['quote'] = self.second_quote
        self.second_question = question
        return question

    def send_and_receive(self, *, legacy=False):
        question = self.new_question(legacy=legacy)
        self.harness.add_question(question, now=clock(question['created_at']))
        self.harness.mark_sent(question['id'], '2026-10-09T17:07:00+09:00',
                               now=clock('2026-10-09T17:07:00+09:00'))
        reply = deepcopy(self.first_reply)
        reply.update(id='second-reply', question_id=question['id'], received_at='2026-10-09T17:08:00+09:00')
        self.harness.add_reply(reply, now=clock(reply['received_at']))
        self.second_reply = reply

    def evaluation(self, *, branch='persistent', recorded='2026-10-09T17:10:00+09:00'):
        evaluation = self.load('reply-evaluation.json')
        evaluation.update(reply_id='second-reply', branch_id=branch,
                          basis_quote='人件費は継続的な費用です。', recorded_at=recorded,
                          expected_thesis_version=self.store.thesis('demo-services')['version'],
                          decision_quote=self.second_quote)
        return evaluation

    def dump(self):
        return '\n'.join(self.store.connection.iterdump())

    def assert_no_application(self, result, original):
        self.assertFalse(result['applied'])
        self.assertEqual(result['action'], 'unresolved')
        self.assertEqual(result['information_status'], 'public_clarification')
        self.assertEqual(result['reason_codes'], ['dependency_information_held_for_review'])
        self.assertEqual(set(result['dependency_information_holds']), {self.first_reply['id']})
        self.assertEqual(self.store.thesis('demo-services'), original)
        self.assertEqual(self.store.source(self.original_source['id']), self.original_source)
        self.assertEqual(self.store.reply(self.first_reply['id']), self.first_reply)
        with self.assertRaisesRegex(ValueError, 'Unknown source'):
            self.store.source('reply:second-reply')

    def test_new_preflight_and_send_hold_current_dependency_correction(self):
        self.correction(at='2026-10-09T17:02:00+09:00')
        question = self.new_question()
        saved = self.harness.add_question(question, now=clock(question['created_at']))
        preflight = saved['decision_contract']['preflight']
        self.assertEqual(preflight['question_value'], 'needs_review')
        self.assertIn('dependent_reply_information', preflight['incomplete_reviews'])
        self.assertEqual(preflight['dependency_information_holds'][self.first_reply['id']]['version'], 1)
        before = self.dump()
        with self.assertRaisesRegex(ValueError, 'needs review'):
            self.harness.mark_sent(question['id'], '2026-10-09T17:07:00+09:00',
                                   now=clock('2026-10-09T17:07:00+09:00'))
        self.assertEqual(self.dump(), before)
        self.assertEqual(self.store.question(question['id'])['status'], 'draft')

    def test_send_rechecks_after_freeze_and_cannot_backdate_around_current_hold(self):
        question = self.new_question()
        saved = self.harness.add_question(question, now=clock(question['created_at']))
        self.assertEqual(saved['decision_contract']['preflight']['question_value'], 'decision_distinguishing')
        self.correction(at='2026-10-09T17:08:00+09:00')
        with self.assertRaisesRegex(ValueError, 'needs review'):
            self.harness.mark_sent(question['id'], '2026-10-09T17:07:00+09:00',
                                   now=clock('2026-10-09T17:10:00+09:00'))
        self.assertEqual(self.store.question(question['id'])['decision_contract'], saved['decision_contract'])

    def test_delayed_correction_uses_both_cutoffs_and_backdated_freeze_still_holds(self):
        question = self.new_question()
        self.correction(at='2026-10-09T17:06:00+09:00', saved='2026-10-09T17:09:00+09:00')
        lifecycle = DecisionLifecycle(self.store)
        self.assertEqual(lifecycle.dependency_information_holds(self.original,
                         as_of='2026-10-09T17:08:00+09:00'), {})
        saved = self.harness.add_question(question, now=clock('2026-10-09T17:10:00+09:00'))
        check = saved['decision_contract']['preflight']['dependency_information_check']
        self.assertEqual(check['as_of_holds'], {})
        self.assertEqual(set(check['current_holds']), {self.first_reply['id']})
        self.assertEqual(saved['decision_contract']['preflight']['question_value'], 'needs_review')

    def test_public_new_reply_does_not_update_model_over_held_dependency(self):
        self.send_and_receive()
        self.correction()
        request = self.evaluation(recorded='2026-10-09T17:08:00+09:00')
        result = self.harness.evaluate_reply(request, now=clock('2026-10-09T17:10:00+09:00'))
        self.assertEqual(result['status'], 'held_for_review')
        self.assert_no_application(result, self.original)

    def test_runtime_cutoff_is_sampled_after_writer_acquisition(self):
        self.send_and_receive()
        self.correction()
        request = self.evaluation(recorded='2026-10-09T17:08:00+09:00')
        transaction = self.store.transaction

        @contextmanager
        def acquired_later():
            # Model a correction committed while this operation waits for the
            # writer. Its runtime must be sampled after that wait, not before.
            with transaction():
                with patch('ir_agent.harness.datetime', wraps=datetime) as acquired_clock:
                    acquired_clock.now.return_value = clock('2026-10-09T17:10:00+09:00')
                    yield

        with patch('ir_agent.harness.datetime', wraps=datetime) as start_clock:
            start_clock.now.return_value = clock('2026-10-09T17:08:00+09:00')
            with patch.object(self.store, 'transaction', acquired_later):
                result = self.harness.evaluate_reply(request)
        self.assert_no_application(result, self.original)

    def test_legacy_reply_has_the_same_dependency_application_guard(self):
        self.send_and_receive(legacy=True)
        self.correction(status='potential_nonpublic')
        result = self.harness.evaluate_reply(self.evaluation(), now=clock('2026-10-09T17:10:00+09:00'))
        self.assertEqual(result['status'], 'held_for_review')
        self.assert_no_application(result, self.original)

    def test_ambiguous_branch_remains_unresolved_without_model_writes(self):
        self.send_and_receive()
        self.correction()
        result = self.harness.evaluate_reply(self.evaluation(branch='unclear'),
                                             now=clock('2026-10-09T17:10:00+09:00'))
        self.assertEqual(result['status'], 'unresolved')
        self.assert_no_application(result, self.original)

    def test_reaffirmation_requires_explicit_reassessment_and_keeps_old_retry(self):
        self.send_and_receive()
        self.correction()
        request = self.evaluation()
        held = self.harness.evaluate_reply(request, now=clock(request['recorded_at']))
        self.correction(version=1, status='public_clarification', at='2026-10-09T17:11:00+09:00')
        before = self.dump()
        self.assertEqual(self.harness.evaluate_reply(request, now=clock('2026-10-09T17:12:00+09:00'))['status'],
                         held['status'])
        self.assertEqual(self.dump(), before)
        retry = dict(request, expected_evaluation_version=1, recorded_at='2026-10-09T17:12:00+09:00')
        result = self.harness.evaluate_reply(retry, now=clock(retry['recorded_at']))
        self.assertTrue(result['applied'])
        self.assertEqual(self.store.thesis('demo-services')['version'], 3)
        self.assertEqual(result['decision_review']['context']['information_review_versions'][self.first_reply['id']], 2)
        self.assertNotIn('dependency_information_holds', result)
        before = self.dump()
        self.assertEqual(self.harness.evaluate_reply(retry, now=clock(retry['recorded_at'])), result)
        self.assertEqual(self.dump(), before)

    def test_second_parent_correction_and_shared_dag_gate_plan_and_application(self):
        sources = []
        for source_id, parents in (
            ('shared-parent', []), ('left-parent', ['shared-parent']),
            ('right-parent', ['shared-parent', self.original_source['id']]),
            ('derived-root', ['left-parent', 'right-parent']),
        ):
            source = deepcopy(self.value['sources'][0])
            source.update(id=source_id, retrieved_at='2026-10-09T17:03:00+09:00',
                          metadata={'original_source_ids': parents})
            sources.append(source)
        derived = deepcopy(self.original)
        derived.update(version=3, recorded_at='2026-10-09T17:03:00+09:00', evidence_ids=['derived-root'])
        self.harness.ingest({'schema_version': 1, 'sources': sources, 'theses': [derived]},
                            now=clock(derived['recorded_at']))
        self.send_and_receive()
        self.correction()
        saved = self.store.question('second-question')
        contract = saved['decision_contract']
        result = DecisionLifecycle(self.store).plan(saved, derived, contract, contract['policy_snapshot'], True,
                    '2026-10-09T17:10:00+09:00', now='2026-10-09T17:10:00+09:00')
        self.assertEqual(result['question_value'], 'needs_review')
        self.assertEqual(set(result['dependency_information_holds']), {self.first_reply['id']})
        result = self.harness.evaluate_reply(self.evaluation(), now=clock('2026-10-09T17:10:00+09:00'))
        self.assert_no_application(result, derived)

    def unrelated_correction_does_not_hold(self, *, other_company):
        company_id = 'demo-services'
        thesis = self.original
        if other_company:
            company_id = 'unrelated-company'
            company = deepcopy(self.store.company('demo-services'))
            company['id'] = company_id
            source = deepcopy(self.value['sources'][0])
            source.update(id='unrelated-source', company_id=company_id)
            thesis = deepcopy(self.value['thesis'])
            thesis.update(company_id=company_id, evidence_ids=[source['id']])
            self.harness.ingest({'schema_version': 1, 'companies': [company], 'sources': [source], 'theses': [thesis]},
                                now=clock('2026-10-09T17:02:00+09:00'))
        question = deepcopy(self.first_question)
        question.pop('decision_contract')
        question.update(id='unrelated-question', topic='unrelated', company_id=company_id,
                        thesis_version=thesis['version'], evidence_ids=thesis['evidence_ids'],
                        created_at='2026-10-09T17:03:00+09:00')
        self.harness.add_question(question, now=clock(question['created_at']))
        self.harness.mark_sent(question['id'], '2026-10-09T17:04:00+09:00',
                               now=clock('2026-10-09T17:04:00+09:00'))
        reply = deepcopy(self.first_reply)
        reply.update(id='unrelated-reply', question_id=question['id'], received_at='2026-10-09T17:04:00+09:00')
        self.harness.add_reply(reply, now=clock(reply['received_at']))
        self.correction(reply=reply, at='2026-10-09T17:04:00+09:00')
        self.send_and_receive()
        result = self.harness.evaluate_reply(self.evaluation(), now=clock('2026-10-09T17:10:00+09:00'))
        self.assertTrue(result['applied'])
        self.assertNotIn('dependency_information_holds', result)

    def test_unrelated_reply_correction_does_not_hold_selected_thesis(self):
        self.unrelated_correction_does_not_hold(other_company=False)

    def test_other_company_correction_does_not_hold_selected_thesis(self):
        self.unrelated_correction_does_not_hold(other_company=True)

    def test_hold_evaluation_failure_rolls_back_and_retry_remains_idempotent(self):
        self.send_and_receive()
        self.correction()
        request = self.evaluation()
        before = self.dump()
        with patch('ir_agent.information_review.current_evaluation_view', side_effect=ValueError('view failed')):
            with self.assertRaisesRegex(ValueError, 'view failed'):
                self.harness.evaluate_reply(request, now=clock(request['recorded_at']))
        self.assertEqual(self.dump(), before)
        result = self.harness.evaluate_reply(request, now=clock(request['recorded_at']))
        self.assert_no_application(result, self.original)
        before = self.dump()
        self.assertEqual(self.harness.evaluate_reply(request, now=clock(request['recorded_at'])), result)
        self.assertEqual(self.dump(), before)
        stored = self.store.connection.execute('SELECT data FROM theses WHERE company_id=? AND version=2',
                                               ('demo-services',)).fetchone()[0]
        self.assertEqual(stored, json_text(self.original))

    def add_source_snapshot(self, classification, *, source_type='ir_reply', omit_status=False,
                            second_parent=False):
        source = deepcopy(self.original_source)
        source.update(id='original-source-snapshot', source_type=source_type,
                      retrieved_at='2026-10-09T17:03:00+09:00')
        if omit_status:
            source['metadata'].pop('information_status', None)
        else:
            source['metadata']['information_status'] = classification
        sources = [source]
        evidence_id = source['id']
        if second_parent:
            plain = deepcopy(self.value['sources'][0])
            plain.update(id='plain-origin', retrieved_at=source['retrieved_at'])
            derived = deepcopy(plain)
            derived.update(id='derived-source-snapshot',
                           metadata={'original_source_ids': [plain['id'], source['id']]})
            sources.extend([plain, derived])
            evidence_id = derived['id']
        thesis = deepcopy(self.original)
        thesis.update(version=3, recorded_at=source['retrieved_at'],
                      evidence_ids=[*thesis['evidence_ids'], evidence_id])
        self.harness.ingest({'schema_version': 1, 'sources': sources, 'theses': [thesis]},
                            now=clock(thesis['recorded_at']))
        self.snapshot_source = self.store.source(source['id'])
        self.snapshot_thesis = thesis

    def assert_source_snapshot_hold(self, result, *, correction_hold=False):
        self.assertFalse(result['applied'])
        self.assertEqual(result['action'], 'unresolved')
        self.assertEqual(result['information_status'], 'public_clarification')
        self.assertIn('dependency_source_information_held_for_review', result['reason_codes'])
        holds = result['dependency_source_information_holds']
        self.assertEqual(set(holds), {self.snapshot_source['id']})
        hold = holds[self.snapshot_source['id']]
        self.assertEqual(hold['source_id'], self.snapshot_source['id'])
        self.assertEqual(hold['source_sha256'], sha256(json_text(self.snapshot_source).encode()).hexdigest())
        self.assertEqual(hold['classification_origin'], 'source_snapshot_metadata')
        self.assertNotIn('version', hold)
        self.assertNotIn('reply_id', hold)
        if not correction_hold:
            self.assertNotIn('dependency_information_holds', result)
        self.assertEqual(self.store.thesis('demo-services'), self.snapshot_thesis)
        self.assertEqual(self.store.source(self.snapshot_source['id']), self.snapshot_source)
        self.assertEqual(self.store.reply(self.first_reply['id']), self.first_reply)
        self.assertEqual(self.store.reply('second-reply'), self.second_reply)
        with self.assertRaisesRegex(ValueError, 'Unknown source'):
            self.store.source('reply:second-reply')

    def test_original_unclear_snapshot_blocks_legacy_financial_update_without_review_rows(self):
        self.add_source_snapshot('unclear')
        self.send_and_receive(legacy=True)
        result = self.harness.evaluate_reply(self.evaluation(), now=clock('2026-10-09T17:10:00+09:00'))
        self.assertEqual(result['status'], 'held_for_review')
        self.assert_source_snapshot_hold(result)
        self.assertEqual(self.store.connection.execute('SELECT COUNT(*) FROM reply_information_reviews').fetchone()[0], 0)
        before = self.dump()
        self.assertEqual(self.harness.evaluate_reply(self.evaluation(),
                         now=clock('2026-10-09T17:10:00+09:00')), result)
        self.assertEqual(self.dump(), before)

    def test_original_potential_nonpublic_snapshot_blocks_legacy_financial_update(self):
        self.add_source_snapshot('potential_nonpublic')
        self.send_and_receive(legacy=True)
        result = self.harness.evaluate_reply(self.evaluation(), now=clock('2026-10-09T17:10:00+09:00'))
        self.assert_source_snapshot_hold(result)

    def test_ir_snapshot_missing_classification_is_not_public(self):
        self.add_source_snapshot(None, omit_status=True)
        self.send_and_receive(legacy=True)
        result = self.harness.evaluate_reply(self.evaluation(), now=clock('2026-10-09T17:10:00+09:00'))
        self.assert_source_snapshot_hold(result)
        self.assertIsNone(result['dependency_source_information_holds'][self.snapshot_source['id']]['information_status'])

    def test_public_disclosure_missing_classification_stays_usable(self):
        self.add_source_snapshot(None, source_type='public_disclosure', omit_status=True)
        self.send_and_receive()
        result = self.harness.evaluate_reply(self.evaluation(), now=clock('2026-10-09T17:10:00+09:00'))
        self.assertTrue(result['applied'])
        self.assertEqual(self.store.thesis('demo-services')['version'], 4)
        self.assertNotIn('dependency_source_information_holds', result)

    def test_second_origin_snapshot_hold_is_explained_in_preflight_and_blocks_legacy_apply(self):
        self.add_source_snapshot('unclear', second_parent=True)
        question = self.new_question()
        saved = self.harness.add_question(question, now=clock(question['created_at']))
        preflight = saved['decision_contract']['preflight']
        self.assertEqual(preflight['question_value'], 'needs_review')
        self.assertEqual(set(preflight['dependency_source_information_holds']), {self.snapshot_source['id']})
        self.assertNotIn('dependency_information_holds', preflight)
        # A separate legacy question exercises the application boundary even
        # though a contracted question correctly cannot pass its preflight.
        legacy = deepcopy(question)
        legacy.update(id='legacy-second-question', topic='legacy-origin-review')
        legacy.pop('decision_contract')
        self.harness.add_question(legacy, now=clock(question['created_at']))
        self.harness.mark_sent(legacy['id'], '2026-10-09T17:07:00+09:00',
                               now=clock('2026-10-09T17:07:00+09:00'))
        reply = deepcopy(self.first_reply)
        reply.update(id='second-reply', question_id=legacy['id'], received_at='2026-10-09T17:08:00+09:00')
        self.second_reply = reply
        self.harness.add_reply(reply, now=clock(reply['received_at']))
        result = self.harness.evaluate_reply(self.evaluation(), now=clock('2026-10-09T17:10:00+09:00'))
        self.assert_source_snapshot_hold(result)

    def test_public_reaffirmation_does_not_rewrite_or_release_unclear_source_snapshot(self):
        self.add_source_snapshot('unclear')
        self.send_and_receive(legacy=True)
        request = self.evaluation()
        self.harness.evaluate_reply(request, now=clock(request['recorded_at']))
        self.correction(status='public_clarification', at='2026-10-09T17:11:00+09:00')
        revised = dict(request, expected_evaluation_version=1, recorded_at='2026-10-09T17:12:00+09:00')
        result = self.harness.evaluate_reply(revised, now=clock(revised['recorded_at']))
        self.assert_source_snapshot_hold(result)
        self.assertEqual(result['version'], 2)

    def test_snapshot_and_correction_holds_keep_distinct_identity_and_version_fields(self):
        self.add_source_snapshot('unclear')
        self.send_and_receive(legacy=True)
        self.correction()
        result = self.harness.evaluate_reply(self.evaluation(), now=clock('2026-10-09T17:10:00+09:00'))
        self.assert_source_snapshot_hold(result, correction_hold=True)
        self.assertEqual(result['dependency_information_holds'][self.first_reply['id']]['version'], 1)
        self.assertEqual(set(result['dependency_source_information_holds']), {self.snapshot_source['id']})
        self.assertEqual(result['reason_codes'], ['dependency_information_held_for_review',
                                                 'dependency_source_information_held_for_review'])

    def test_ambiguous_branch_does_not_apply_or_relabel_unclear_source_dependency(self):
        self.add_source_snapshot('unclear')
        self.send_and_receive(legacy=True)
        result = self.harness.evaluate_reply(self.evaluation(branch='unclear'),
                                             now=clock('2026-10-09T17:10:00+09:00'))
        self.assertEqual(result['status'], 'unresolved')
        self.assert_source_snapshot_hold(result)


if __name__ == '__main__':
    unittest.main()
