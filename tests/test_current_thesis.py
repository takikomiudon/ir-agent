"""Raw current version coherence blocks stale candidates without recalculation."""
from copy import deepcopy
from datetime import datetime
import json
import unittest
from unittest.mock import patch

from ir_agent.information_review import add_assessment, current_decision_view, current_evaluation_view
import test_decision_lifecycle as fixtures

SAVED = '2026-10-09T17:00:00+09:00'
CHANGED = '2026-10-09T17:10:00+09:00'
CHECKED = '2026-10-09T17:11:00+09:00'


class CurrentThesisTests(unittest.TestCase):
    def setUp(self):
        self.env = fixtures.DecisionLifecycleTests('runTest')
        self.env.setUp(); self.addCleanup(self.env.doCleanups)
        self.env.receive(); self.store = self.env.store
        quote = self.env.fresh_quote('1600', SAVED)
        result = self.env.harness.evaluate_reply(self.env.evaluation(quote), now=datetime.fromisoformat(SAVED))
        self.review = self.store.decision_review(result['decision_review_id'])
        self.evaluation = json.loads(self.store.connection.execute('SELECT data FROM evaluations WHERE reply_id=? AND version=1', ('demo-reply-cost',)).fetchone()['data'])
        self.assertEqual(self.review['result']['proposed_action'], 'exit_review')

    def advance(self, *, saved=CHANGED):
        old = self.store.thesis('demo-services')
        changed = {**deepcopy(old), 'version': old['version'] + 1}
        self.assertEqual({key: value for key, value in changed.items() if key != 'version'},
                         {key: value for key, value in old.items() if key != 'version'})
        self.store.put_thesis(changed, now=datetime.fromisoformat(saved))
        return changed

    def test_matching_version_is_a_limited_mechanical_check(self):
        view = current_decision_view(self.store, self.review, now=CHECKED)
        check = view['current_thesis_check']
        self.assertEqual((check['reviewed_version'], check['current_version'], check['status']), (2, 2, 'matched'))
        self.assertIn('not financial validation', check['scope'])
        self.assertEqual(view['result'], self.review['result'])

    def test_only_version_advance_holds_current_review_and_evaluation_without_writes(self):
        changed = self.advance()
        original = deepcopy(self.review); dump = list(self.store.connection.iterdump())
        total = self.store.connection.total_changes
        view = current_decision_view(self.store, self.review, now=CHECKED)
        self.assertEqual(view['current_quote_check']['status'], 'fresh')
        self.assertEqual(view['current_thesis_check']['status'], 'mismatch')
        self.assertEqual(view['current_thesis_check']['current_version'], 3)
        self.assertEqual(view['current_validity'], 'requires_thesis_review')
        self.assertEqual(view['result']['proposed_action'], 'unresolved')
        self.assertEqual(view['historical_result'], original['result'])
        evaluation = current_evaluation_view(self.store, self.evaluation, now=CHECKED)
        self.assertEqual(evaluation['action'], 'unresolved')
        self.assertEqual(evaluation['decision_status'], 'requires_thesis_review')
        self.assertEqual(evaluation['current_thesis_check'], view['current_thesis_check'])
        self.assertEqual(self.store.thesis('demo-services'), changed)
        self.assertEqual(self.review, original)
        self.assertEqual(self.store.decision_review(original['id']), original)
        self.assertEqual(list(self.store.connection.iterdump()), dump)
        self.assertEqual(self.store.connection.total_changes, total)

    def test_information_then_version_then_price_priority_preserves_all_requirements(self):
        self.advance()
        reply = self.store.reply('demo-reply-cost')
        add_assessment(self.store, {'reply_id': reply['id'], 'expected_version': 0,
            'information_status': 'potential_nonpublic', 'basis_quote': reply['raw_text'][:10],
            'rationale': 'Fictional independent review hold.', 'recorded_at': CHECKED}, now=CHECKED)
        view = current_decision_view(self.store, self.review, now='2026-10-09T20:00:00+09:00')
        self.assertEqual(view['current_validity'], 'requires_information_review')
        self.assertEqual(view['current_review_requirements'], ['requires_information_review', 'requires_thesis_review', 'requires_price_review'])
        self.assertEqual(view['historical_result'], self.review['result'])
        self.assertEqual(view['result']['proposed_action'], 'unresolved')

    def test_unknown_review_identity_or_current_thesis_is_held(self):
        for field, bad in (('company_id', None), ('thesis_version', None), ('thesis_version', True), ('company_id', [])):
            review = deepcopy(self.review); review[field] = bad
            with self.subTest(field=field, bad=bad):
                view = current_decision_view(self.store, review, now=CHECKED)
                self.assertEqual(view['current_thesis_check']['status'], 'unknown')
                self.assertEqual(view['current_validity'], 'requires_thesis_review')
                self.assertEqual(view['result']['proposed_action'], 'unresolved')
        with patch.object(self.store, 'thesis', return_value=None):
            self.assertEqual(current_decision_view(self.store, self.review, now=CHECKED)['current_thesis_check']['status'], 'unknown')

    def test_raw_latest_comparison_is_not_historical_reconstruction(self):
        self.advance(saved='2026-10-09T19:00:00+09:00')
        view = current_decision_view(self.store, self.review, now=CHECKED)
        self.assertEqual(view['current_thesis_check']['current_version'], 3)
        self.assertEqual(view['current_thesis_check']['status'], 'mismatch')
        self.assertIn('historical PIT', view['current_thesis_check']['scope'])
        self.assertEqual(view['current_quote_check']['status'], 'fresh')

    def test_old_applied_evaluation_without_resolved_review_cannot_keep_action(self):
        value = deepcopy(self.evaluation)
        value.pop('decision_review_id'); value.pop('decision_review')
        original = deepcopy(value)
        view = current_evaluation_view(self.store, value, now=CHECKED)
        self.assertEqual(view['current_thesis_check']['status'], 'unknown')
        self.assertEqual(view['current_validity'], 'requires_thesis_review')
        self.assertEqual(view['action'], 'unresolved')
        self.assertEqual(value, original)

    def test_matching_version_never_releases_other_holds_or_promotes_unresolved(self):
        stale = current_decision_view(self.store, self.review, now='2026-10-09T20:00:00+09:00')
        self.assertEqual(stale['current_thesis_check']['status'], 'matched')
        self.assertEqual(stale['current_validity'], 'requires_price_review')
        unresolved = deepcopy(self.review)
        unresolved['result'].update(status='unresolved', proposed_action='unresolved', reason_codes=['missing_market_quote'])
        unresolved['result'].pop('quote')
        self.advance()
        view = current_decision_view(self.store, unresolved, now=CHECKED)
        self.assertEqual(view['result'], unresolved['result'])
        self.assertEqual(view['result']['proposed_action'], 'unresolved')


if __name__ == '__main__': unittest.main()
