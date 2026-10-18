"""Persistent policy/IR contracts, atomic application and repeatable reviews."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ir_agent.harness import Harness, evaluation_view
from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.store import Store
from test_decision import plan

ROOT = Path(__file__).resolve().parents[1]
CREATED = datetime(2026, 10, 9, 1, tzinfo=timezone.utc)
SAVED = datetime(2026, 10, 9, 1, 1, tzinfo=timezone.utc)
EVALUATED = datetime(2026, 10, 9, 9, tzinfo=timezone.utc)


class DecisionLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.value = plan()
        self.store = Store(':memory:'); self.addCleanup(self.store.close)
        self.harness = Harness(self.store)
        bundle = json.loads((ROOT / 'examples/demo.json').read_text())
        bundle['theses'] = [self.value['thesis']]
        bundle['sources'].append(self.value['sources'][1])
        self.harness.ingest(bundle, now=CREATED)
        self.harness.register_decision_policy(self.value['policy'], now=CREATED)
        self.question = deepcopy(self.value['question'])
        self.question['decision_contract'] = {'policy_id': self.value['policy']['id'], 'policy_version': 1,
                                              'quote': deepcopy(self.value['quote']), 'synthetic': True,
                                              'synthetic_position': {'held': True, 'observed_at': '2026-10-09T09:59:00+09:00'}}

    def save(self):
        return self.harness.add_question(self.question, now=SAVED)

    def receive(self):
        self.save()
        self.harness.mark_sent(self.question['id'], '2026-10-09T10:05:00+09:00', now=SAVED.replace(minute=6))
        reply = json.loads((ROOT / 'examples/reply.json').read_text())
        self.harness.add_reply(reply, now=datetime.fromisoformat(reply['received_at']))

    def fresh_quote(self, price='1000', stamp='2026-10-09T17:00:00+09:00', suffix='fresh'):
        source = deepcopy(self.value['sources'][1]); source['id'] = 'price-' + suffix
        source['retrieved_at'] = stamp
        source['metadata'].update(price_jpy=price, observed_at=stamp)
        # Later replayed quotes can describe an earlier market observation;
        # their new DB presence is not backdated before an already saved result.
        latest = self.store.connection.execute('SELECT MAX(presence_observed_at) FROM record_availability').fetchone()[0]
        saved = max(datetime.fromisoformat(stamp), datetime.fromisoformat(latest))
        self.harness.ingest({'schema_version': 1, 'sources': [source]}, now=saved)
        quote = deepcopy(self.value['quote'])
        quote.update(source_id=source['id'], price_jpy=price, retrieved_at=stamp, observed_at=stamp)
        return quote

    def evaluation(self, quote=None):
        value = json.loads((ROOT / 'examples/reply-evaluation.json').read_text())
        value['expected_thesis_version'] = 1
        if quote is not None: value['decision_quote'] = quote
        return value

    def test_policy_is_immutable_idempotent_and_versioned(self):
        self.assertFalse(self.harness.register_decision_policy(self.value['policy'], now=SAVED)['added'])
        bad = deepcopy(self.value['policy']); bad['parameters']['minimum_upside_pct'] = '99'
        with self.assertRaisesRegex(ValueError, 'immutable'): self.harness.register_decision_policy(bad, now=SAVED)
        bad['version'] = 3
        with self.assertRaisesRegex(ValueError, 'consecutive'): self.harness.register_decision_policy(bad, now=SAVED)
        bad['version'] = 2; bad['recorded_at'] = '2026-09-01T00:00:00+09:00'
        with self.assertRaisesRegex(ValueError, 'backdated'): self.harness.register_decision_policy(bad, now=SAVED)

    def test_question_freezes_registered_policy_and_retries_do_not_overwrite(self):
        saved = self.save()
        self.assertEqual(self.save(), saved)
        self.assertEqual(saved['decision_contract']['preflight']['question_value'], 'decision_distinguishing')
        changed = deepcopy(self.question); changed['decision_contract']['quote']['price_jpy'] = '1'
        with self.assertRaisesRegex(ValueError, 'immutable'): self.harness.add_question(changed, now=SAVED)
        newer = deepcopy(self.value['policy']); newer['version'] = 2
        newer['parameters']['minimum_upside_pct'] = '99'
        self.harness.register_decision_policy(newer, now=SAVED)
        self.assertEqual(self.store.question(saved['id'])['decision_contract']['policy_snapshot']['version'], 1)

    def test_real_contract_cannot_claim_an_unregistered_ex_ante_policy(self):
        policy = deepcopy(self.value['policy']); policy['id'] = 'adopted-real-policy'
        for source in policy['parameter_sources'].values(): source['kind'] = 'user'
        self.harness.register_decision_policy(policy, now=SAVED)
        self.question['decision_contract'].update(policy_id=policy['id'], synthetic=False)
        self.question['decision_contract'].pop('synthetic_position')
        with self.assertRaisesRegex(ValueError, 'Register the policy before'):
            self.harness.add_question(self.question, now=SAVED)

    def test_sending_rechecks_quote_freshness_and_position(self):
        self.save()
        with self.assertRaisesRegex(ValueError, 'needs review'):
            self.harness.mark_sent(self.question['id'], '2026-10-09T11:00:00+09:00', now=EVALUATED)
        self.assertEqual(self.store.question(self.question['id'])['status'], 'draft')
        with patch('ir_agent.store.now_iso', return_value='2026-10-09T01:03:00+00:00'):
            self.harness.set_company_status('demo-services', 'active', 'synthetic position update', held=False)
        with self.assertRaisesRegex(ValueError, 'Position changed'):
            self.harness.mark_sent(self.question['id'], '2026-10-09T10:05:00+09:00', now=EVALUATED)

    def test_favorable_reply_without_fresh_quote_does_not_claim_buy(self):
        self.receive()
        applied = self.harness.evaluate_reply(self.evaluation(), now=EVALUATED)
        self.assertTrue(applied['applied'])
        self.assertEqual(applied['precommitted_action'], 'buy_review')
        self.assertEqual(applied['action'], 'unresolved')
        self.assertEqual(applied['decision_review']['result']['reason_codes'], ['missing_market_quote'])
        self.assertEqual(self.harness.status()['decision_reviews'], 1)
        self.assertEqual(self.harness.evaluate_reply(self.evaluation(), now=EVALUATED), applied)

    def test_reply_uses_frozen_policy_actual_position_and_saved_price(self):
        self.receive(); quote = self.fresh_quote('1600')
        newer = deepcopy(self.value['policy']); newer['version'] = 2
        newer['parameters']['minimum_upside_pct'] = '99'
        self.harness.register_decision_policy(newer, now=EVALUATED)
        applied = self.harness.evaluate_reply(self.evaluation(quote), now=EVALUATED)
        self.assertEqual(applied['action'], 'exit_review')
        review = self.store.decision_review(applied['decision_review_id'])
        self.assertEqual(review['policy_version'], 1)
        self.assertEqual(review['result']['reason_codes'], ['valuation_target_reached'])
        self.assertEqual(review['thesis_version'], 2)
        self.assertIn(quote['source_id'], review['source_sha256'])
        self.assertTrue(review['context']['held'])

    def test_missing_quote_source_rolls_back_all_reply_application_writes(self):
        self.receive(); before = self.harness.status()
        with self.assertRaisesRegex(ValueError, 'Unknown source'):
            self.harness.evaluate_reply(self.evaluation({'source_id': 'not-ingested'}), now=EVALUATED)
        self.assertEqual(self.harness.status(), before)
        self.assertEqual(self.store.thesis('demo-services')['version'], 1)

    def test_changed_branch_inputs_are_not_applied_even_if_draft_was_saved(self):
        self.question['branches'][0]['valuation']['scenarios'][1]['inputs']['pe'] = '25'
        saved = self.save()
        self.assertEqual(saved['decision_contract']['preflight']['question_value'], 'needs_review')
        with self.assertRaisesRegex(ValueError, 'needs review'):
            self.harness.mark_sent(self.question['id'], '2026-10-09T10:05:00+09:00', now=EVALUATED)

    def test_fresh_price_review_does_not_reapply_reply_and_is_idempotent(self):
        self.receive()
        self.harness.evaluate_reply(self.evaluation(), now=EVALUATED)
        quote = self.fresh_quote('1000', '2026-10-09T17:25:00+09:00', 'later')
        request = {'reply_id': 'demo-reply-cost', 'expected_thesis_version': 2,
                   'recorded_at': '2026-10-09T17:30:00+09:00', 'decision_quote': quote}
        review = self.harness.review_decision(request, now=EVALUATED)
        self.assertEqual(review['result']['proposed_action'], 'hold_review')
        count = self.harness.status()
        self.assertEqual(self.harness.review_decision(request, now=EVALUATED), review)
        self.assertEqual(self.harness.status(), count)
        self.assertEqual(count['evaluations'], 1)
        self.assertEqual(count['theses'], 2)

    def test_later_position_change_does_not_rewrite_historical_review_or_retry(self):
        self.receive(); self.harness.evaluate_reply(self.evaluation(), now=EVALUATED)
        quote = self.fresh_quote('1000', '2026-10-09T17:25:00+09:00', 'historical')
        request = {'reply_id': 'demo-reply-cost', 'expected_thesis_version': 2,
                   'recorded_at': '2026-10-09T17:30:00+09:00', 'decision_quote': quote}
        original = self.harness.review_decision(request, now=EVALUATED)
        self.assertEqual(original['result']['proposed_action'], 'hold_review')
        self.harness.set_company_status('demo-services', 'active', 'position observed later', held=False)
        self.assertEqual(self.harness.review_decision(request, now=EVALUATED), original)
        # A first review of a different past instant also uses its own position
        # history, rather than projecting the newly observed state backwards.
        request['recorded_at'] = '2026-10-09T17:31:00+09:00'
        historical = self.harness.review_decision(request, now=EVALUATED)
        self.assertTrue(historical['context']['held'])
        self.assertEqual(historical['context']['position_snapshot']['kind'], 'synthetic_assumption')
        self.assertEqual(historical['result']['proposed_action'], 'hold_review')

    def test_review_uses_last_position_observed_before_its_as_of(self):
        self.receive(); self.harness.evaluate_reply(self.evaluation(), now=EVALUATED)
        with patch('ir_agent.store.now_iso', return_value='2026-10-09T08:20:00+00:00'):
            self.harness.set_company_status('demo-services', 'active', 'new observed position', held=False)
        quote = self.fresh_quote('1000', '2026-10-09T17:25:00+09:00', 'observed')
        request = {'reply_id': 'demo-reply-cost', 'expected_thesis_version': 2,
                   'recorded_at': '2026-10-09T17:30:00+09:00', 'decision_quote': quote}
        review = self.harness.review_decision(request, now=EVALUATED)
        self.assertFalse(review['context']['held'])
        self.assertEqual(review['context']['position_snapshot']['kind'], 'observed')
        self.assertEqual(review['result']['proposed_action'], 'buy_review')

    def test_unavailable_historical_position_is_unresolved_without_synthetic_assumption(self):
        self.receive(); self.harness.evaluate_reply(self.evaluation(), now=EVALUATED)
        question = self.store.question(self.question['id'])
        # A pre-existing contract may have no explicit position assumption.
        # Its immutable policy still exists, but today's company state cannot
        # establish the position at its historical decision time.
        question['decision_contract'].pop('synthetic_position')
        evaluation = json.loads(self.store.connection.execute('SELECT data FROM evaluations').fetchone()['data'])
        quote = self.fresh_quote('1000', '2026-10-09T17:25:00+09:00', 'unknown-position')
        with self.store.transaction():
            review = DecisionLifecycle(self.store).review_applied(question, self.store.reply('demo-reply-cost'),
                evaluation, self.store.thesis('demo-services'), quote,
                '2026-10-09T17:30:00+09:00', EVALUATED.isoformat())
        self.assertIsNone(review['context']['held'])
        self.assertEqual(review['result']['proposed_action'], 'unresolved')
        self.assertEqual(review['result']['reason_codes'], ['position_history_unknown'])

    def test_real_contract_rejects_synthetic_position_assumptions(self):
        self.question['decision_contract']['synthetic'] = False
        with self.assertRaisesRegex(ValueError, 'synthetic position assumption'):
            self.save()

    def test_company_state_and_position_observation_roll_back_together(self):
        before = self.store.connection.execute('SELECT COUNT(*) FROM position_observations').fetchone()[0]
        with patch.object(self.store, 'observe_position', side_effect=ValueError('observation failed')):
            with self.assertRaisesRegex(ValueError, 'observation failed'):
                self.harness.set_company_status('demo-services', 'active', 'failed observation', held=False)
        self.assertTrue(self.store.company('demo-services')['held'])
        self.assertEqual(self.store.connection.execute('SELECT COUNT(*) FROM position_observations').fetchone()[0], before)

    def test_legacy_database_observes_position_now_without_backdating(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'legacy.sqlite3'
            legacy = Store(path)
            Harness(legacy).ingest(json.loads((ROOT / 'examples/demo.json').read_text()), now=CREATED)
            legacy.connection.execute('DROP TABLE position_observations')
            legacy.close()
            with patch('ir_agent.store.now_iso', return_value='2026-10-10T00:00:00+00:00'):
                migrated = Store(path)
            try:
                self.assertIsNone(migrated.position_at('demo-services', '2026-10-09T23:59:59+00:00'))
                observed = migrated.position_at('demo-services', '2026-10-10T00:00:00+00:00')
                self.assertTrue(observed['held'])
                self.assertEqual(observed['observed_at'], '2026-10-10T00:00:00+00:00')
                self.assertEqual(observed['kind'], 'observed')
            finally:
                migrated.close()

    def test_stale_expected_version_and_future_review_are_rejected(self):
        self.receive(); self.harness.evaluate_reply(self.evaluation(), now=EVALUATED)
        request = {'reply_id': 'demo-reply-cost', 'expected_thesis_version': 1,
                   'recorded_at': '2026-10-09T17:30:00+09:00'}
        with self.assertRaisesRegex(ValueError, 'Thesis changed'): self.harness.review_decision(request, now=EVALUATED)
        request.update(expected_thesis_version=2, recorded_at='2026-10-10T17:30:00+09:00')
        with self.assertRaisesRegex(ValueError, 'future'): self.harness.review_decision(request, now=EVALUATED)

    def test_historical_branch_only_record_is_viewed_without_mutating_original(self):
        original = {'action': 'buy_review', 'applied': True, 'status': 'applied', 'request': {'reply_id': 'legacy'}}
        viewed = evaluation_view(original)
        self.assertEqual(viewed['action'], 'unresolved')
        self.assertEqual(viewed['precommitted_action'], 'buy_review')
        self.assertEqual(viewed['decision_status'], 'legacy_branch_only')
        self.assertEqual(original['action'], 'buy_review')


if __name__ == '__main__': unittest.main()
