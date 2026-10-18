"""Current-facing actions expire without rewriting their historical calculation."""
from datetime import datetime, timedelta
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_decision_lifecycle as fixtures
from ir_agent.cli import run


LATE = datetime.fromisoformat('2026-10-09T20:00:00+09:00')


class StaleDecisionWorkflowTests(unittest.TestCase):
    def environment(self):
        env = fixtures.DecisionLifecycleTests('runTest')
        env.setUp(); self.addCleanup(env.doCleanups)
        env.receive()
        return env

    def raw_records(self, store):
        return {table: [tuple(row) for row in store.connection.execute('SELECT * FROM '+table)]
                for table in ('theses', 'evaluations', 'decision_reviews')}

    def test_first_reply_application_keeps_history_but_current_action_requires_price_review(self):
        env = self.environment()
        quote = env.fresh_quote('1600')
        request = env.evaluation(quote)
        result = env.harness.evaluate_reply(request, now=LATE)
        self.assertTrue(result['applied'])
        self.assertEqual(result['action'], 'unresolved')
        self.assertEqual(result['decision_status'], 'requires_price_review')
        original = env.store.decision_review(result['decision_review_id'])
        self.assertEqual(original['result']['proposed_action'], 'exit_review')
        self.assertEqual(result['decision_review']['historical_result'], original['result'])
        self.assertIn('market_quote_stale', result['decision_review']['result']['reason_codes'])
        items = env.harness.inbox(now=LATE)['replies_for_review']
        self.assertEqual(items[0]['status'], 'requires_price_review')
        self.assertEqual(env.store.thesis('demo-services')['version'], 2)

    def test_later_retry_expires_action_and_leaves_all_saved_records_unchanged(self):
        env = self.environment()
        quote = env.fresh_quote('1600')
        request = env.evaluation(quote)
        first = env.harness.evaluate_reply(request, now=fixtures.EVALUATED)
        self.assertEqual(first['action'], 'exit_review')
        before = self.raw_records(env.store)
        retry = env.harness.evaluate_reply(request, now=LATE)
        self.assertEqual(retry['action'], 'unresolved')
        self.assertEqual(retry['decision_status'], 'requires_price_review')
        self.assertEqual(self.raw_records(env.store), before)
        later = env.harness.evaluate_reply(request, now=LATE+timedelta(minutes=1))
        self.assertEqual(later['action'], 'unresolved')
        self.assertEqual(self.raw_records(env.store), before)

    def test_price_review_retry_and_cli_shows_apply_the_current_gate(self):
        env = self.environment()
        quote = env.fresh_quote('1600')
        applied = env.harness.evaluate_reply(env.evaluation(quote), now=fixtures.EVALUATED)
        request = {'reply_id': 'demo-reply-cost', 'expected_thesis_version': 2,
                   'recorded_at': '2026-10-09T17:30:00+09:00', 'decision_quote': quote}
        review = env.harness.review_decision(request, now=LATE)
        self.assertEqual(review['current_validity'], 'requires_price_review')
        self.assertEqual(review['result']['proposed_action'], 'unresolved')
        self.assertEqual(review['historical_result']['proposed_action'], 'exit_review')
        before = self.raw_records(env.store)
        retry = env.harness.review_decision(request, now=LATE+timedelta(minutes=1))
        self.assertEqual(retry['id'], review['id'])
        self.assertEqual(retry['result']['proposed_action'], 'unresolved')
        with patch('ir_agent.information_review.now_iso', return_value=LATE.isoformat()), \
             patch('ir_agent.cli.now_iso', return_value=LATE.isoformat()):
            shown = run(SimpleNamespace(command='decision-review', operation='show', review_id=review['id']), env.store)
            replies = run(SimpleNamespace(command='reply', operation='show', reply_id='demo-reply-cost'), env.store)
        self.assertEqual(shown['result']['proposed_action'], 'unresolved')
        self.assertEqual(replies['evaluations'][0]['action'], 'unresolved')
        self.assertEqual(self.raw_records(env.store), before)

    def test_fresh_price_creates_a_new_review_without_reapplying_the_reply(self):
        env = self.environment()
        first_quote = env.fresh_quote('1600')
        initial = env.harness.evaluate_reply(env.evaluation(first_quote), now=LATE)
        self.assertEqual(initial['action'], 'unresolved')
        quote = env.fresh_quote('1600', '2026-10-09T19:59:00+09:00', 'current-price')
        now = LATE+timedelta(minutes=2)
        request = {'reply_id': 'demo-reply-cost', 'expected_thesis_version': 2,
                   'recorded_at': now.isoformat(), 'decision_quote': quote}
        current = env.harness.review_decision(request, now=now)
        self.assertEqual(current['result']['proposed_action'], 'exit_review')
        self.assertNotEqual(current['id'], initial['decision_review_id'])
        self.assertEqual(env.harness.status()['evaluations'], 1)
        self.assertEqual(env.harness.status()['theses'], 2)


if __name__ == '__main__':
    unittest.main()
