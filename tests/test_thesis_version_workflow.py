"""A fresh price does not make a prior thesis version a current candidate."""
from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_decision_lifecycle as fixtures
from ir_agent.cli import run


SAVED = datetime.fromisoformat('2026-10-09T17:00:00+09:00')
UPDATED = datetime.fromisoformat('2026-10-09T17:10:00+09:00')
CURRENT = datetime.fromisoformat('2026-10-09T17:11:00+09:00')


class ThesisVersionWorkflowTests(unittest.TestCase):
    def test_old_version_is_held_on_return_retry_show_and_inbox_without_rebasing(self):
        env = fixtures.DecisionLifecycleTests('runTest')
        env.setUp(); self.addCleanup(env.doCleanups)
        env.receive()
        quote = env.fresh_quote('1600')
        request = env.evaluation(quote)
        first = env.harness.evaluate_reply(request, now=SAVED)
        self.assertEqual(first['action'], 'exit_review')
        raw_review = env.store.decision_review(first['decision_review_id'])
        newer = deepcopy(env.store.thesis('demo-services')); newer['version'] = 3
        env.harness.ingest({'schema_version': 1, 'theses': [newer]}, now=UPDATED)
        before = '\n'.join(env.store.connection.iterdump())
        retry = env.harness.evaluate_reply(request, now=CURRENT)
        self.assertEqual(retry['action'], 'unresolved')
        self.assertEqual(retry['decision_status'], 'requires_thesis_review')
        self.assertEqual(retry['decision_review']['historical_result'], raw_review['result'])
        self.assertEqual(retry['current_quote_check']['status'], 'fresh')
        self.assertEqual(retry['current_thesis_check']['current_version'], 3)
        self.assertEqual(retry['current_thesis_check']['reviewed_version'], 2)
        inbox = env.harness.inbox(now=CURRENT)
        self.assertEqual(inbox['replies_for_review'][0]['status'], 'requires_thesis_review')
        with patch('ir_agent.information_review.now_iso', return_value=CURRENT.isoformat()), \
             patch('ir_agent.cli.now_iso', return_value=CURRENT.isoformat()):
            view = run(SimpleNamespace(command='decision-review', operation='show', review_id=raw_review['id']), env.store)
            replies = run(SimpleNamespace(command='reply', operation='show', reply_id='demo-reply-cost'), env.store)
        self.assertEqual(view['result']['proposed_action'], 'unresolved')
        self.assertEqual(replies['evaluations'][0]['action'], 'unresolved')
        self.assertEqual('\n'.join(env.store.connection.iterdump()), before)
        self.assertEqual(env.store.decision_review(raw_review['id']), raw_review)
        self.assertEqual(env.harness.status()['evaluations'], 1)
        review_request = {'reply_id': 'demo-reply-cost', 'expected_thesis_version': 3,
                          'recorded_at': CURRENT.isoformat(), 'decision_quote': quote}
        with self.assertRaisesRegex(ValueError, 'Thesis changed'):
            env.harness.review_decision(review_request, now=CURRENT)
        self.assertEqual('\n'.join(env.store.connection.iterdump()), before)


if __name__ == '__main__':
    unittest.main()
