"""Current price freshness preserves historical calculations and raw records."""
from copy import deepcopy
from datetime import datetime
import json
import unittest
from unittest.mock import patch

from ir_agent.decision import check_quote_timing, evaluate_decision
from ir_agent.information_review import add_assessment, current_decision_view, current_evaluation_view
from test_decision import request
import test_decision_lifecycle as fixtures

BOUNDARY = '2026-10-09T18:00:00+09:00'
STALE = '2026-10-09T18:00:00.000001+09:00'
LATER = '2026-10-09T20:00:00+09:00'


class CurrentQuoteTests(unittest.TestCase):
    def setUp(self):
        self.env = fixtures.DecisionLifecycleTests('runTest')
        self.env.setUp(); self.addCleanup(self.env.doCleanups)
        self.env.receive(); self.store = self.env.store
        self.quote = self.env.fresh_quote('1600', '2026-10-09T17:00:00+09:00')
        result = self.env.harness.evaluate_reply(self.env.evaluation(self.quote), now=datetime.fromisoformat(BOUNDARY))
        row = self.store.connection.execute('SELECT data FROM evaluations WHERE reply_id=? AND version=1', ('demo-reply-cost',)).fetchone()
        self.evaluation = json.loads(row['data'])
        self.review = self.store.decision_review(result['decision_review_id'])
        self.assertEqual(self.review['result']['proposed_action'], 'exit_review')

    def test_shared_gate_matches_pure_decision_at_exact_boundary_and_one_microsecond(self):
        value = request(); value['as_of'] = '2026-10-09T10:55:00+09:00'
        first = evaluate_decision(value)
        self.assertNotIn('market_quote_stale', first['reason_codes'])
        before = deepcopy(value)
        fresh = check_quote_timing(value['quote'], 3600, as_of=value['as_of'])
        self.assertEqual(fresh['age_microseconds'], 3600000000)
        self.assertEqual(fresh['status'], 'fresh')
        value['as_of'] = '2026-10-09T10:55:00.000001+09:00'
        self.assertEqual(evaluate_decision(value)['reason_codes'], ['market_quote_stale'])
        self.assertEqual(check_quote_timing(value['quote'], 3600, as_of=value['as_of'])['age_microseconds'], 3600000001)
        self.assertEqual(before['quote'], value['quote'])

    def test_current_review_boundary_and_stale_hold_leave_history_and_database_unchanged(self):
        original = deepcopy(self.review)
        changes = self.store.connection.total_changes
        fresh = current_decision_view(self.store, self.review, now=datetime.fromisoformat(BOUNDARY))
        self.assertEqual(fresh['result'], original['result'])
        self.assertEqual(fresh['current_quote_check']['status'], 'fresh')
        stale = current_decision_view(self.store, self.review, now=STALE)
        self.assertEqual(stale['current_validity'], 'requires_price_review')
        self.assertEqual(stale['result']['proposed_action'], 'unresolved')
        self.assertEqual(stale['historical_result'], original['result'])
        self.assertIn('market_quote_stale', stale['result']['reason_codes'])
        self.assertEqual(self.review, original)
        self.assertEqual(self.store.decision_review(self.review['id']), original)
        self.assertEqual(self.store.connection.total_changes, changes)

    def test_current_evaluation_applies_price_hold_and_retains_stored_action(self):
        current = current_evaluation_view(self.store, self.evaluation, now=LATER)
        self.assertEqual(current['action'], 'unresolved')
        self.assertEqual(current['decision_status'], 'requires_price_review')
        self.assertEqual(current['current_quote_check']['status'], 'stale')
        self.assertEqual(current['decision_review']['historical_result']['proposed_action'], 'exit_review')
        self.assertEqual(self.evaluation['action'], 'exit_review')
        row = self.store.connection.execute('SELECT data FROM evaluations WHERE reply_id=? AND version=1', ('demo-reply-cost',)).fetchone()
        self.assertEqual(json.loads(row['data']), self.evaluation)

    def test_future_observation_or_retrieval_is_unavailable_at_current_time(self):
        for quote in ({'observed_at': BOUNDARY, 'retrieved_at': BOUNDARY},
                      {'observed_at': '2026-10-09T16:00:00+09:00', 'retrieved_at': BOUNDARY}):
            value = deepcopy(self.review); value['result']['quote'].update(quote)
            with self.subTest(quote=quote):
                current = current_decision_view(self.store, value, now='2026-10-09T17:30:00+09:00')
                self.assertEqual(current['current_quote_check']['status'], 'unavailable')
                self.assertEqual(current['result']['proposed_action'], 'unresolved')

    def test_missing_or_malformed_snapshot_is_unknown_and_does_not_invent_freshness(self):
        damaged = []
        for field in ('quote', 'policy_snapshot'):
            value = deepcopy(self.review); value['result'].pop(field); damaged.append(value)
        value = deepcopy(self.review); value['result']['policy_snapshot']['parameters']['max_quote_age_seconds'] = True
        damaged.append(value)
        value = deepcopy(self.review); value['result']['quote']['observed_at'] = []
        damaged.append(value)
        value = deepcopy(self.review); value['result']['quote'].pop('source_id')
        damaged.append(value)
        for value in damaged:
            with self.subTest(result=value['result']):
                current = current_decision_view(self.store, value, now=BOUNDARY)
                self.assertEqual(current['current_quote_check']['status'], 'unknown')
                self.assertEqual(current['current_validity'], 'requires_price_review')
                self.assertEqual(current['result']['proposed_action'], 'unresolved')

    def test_information_hold_has_priority_and_quote_hold_is_separately_visible(self):
        reply = self.store.reply('demo-reply-cost')
        add_assessment(self.store, {'reply_id': reply['id'], 'expected_version': 0,
            'information_status': 'potential_nonpublic', 'basis_quote': reply['raw_text'][:10],
            'rationale': 'Synthetic public basis withdrawn for review.', 'recorded_at': '2026-10-09T18:05:00+09:00'},
            now='2026-10-09T18:05:00+09:00')
        before = current_decision_view(self.store, self.review, now=BOUNDARY)
        self.assertEqual(before['current_review_requirements'], [])
        current = current_decision_view(self.store, self.review, now=LATER)
        self.assertEqual(current['current_validity'], 'requires_information_review')
        self.assertEqual(current['current_review_requirements'], ['requires_information_review', 'requires_price_review'])
        self.assertEqual(current['current_quote_check']['status'], 'stale')
        self.assertEqual(current['historical_result'], self.review['result'])
        evaluated = current_evaluation_view(self.store, self.evaluation, now=LATER)
        self.assertEqual(evaluated['decision_status'], 'requires_information_review')
        self.assertEqual(evaluated['action'], 'unresolved')
        self.assertEqual(evaluated['current_quote_check']['status'], 'stale')

    def test_default_clock_checks_real_current_time_instead_of_recorded_at(self):
        with patch('ir_agent.information_review.now_iso', return_value=LATER):
            self.assertEqual(current_decision_view(self.store, self.review)['result']['proposed_action'], 'unresolved')
            self.assertEqual(current_evaluation_view(self.store, self.evaluation)['action'], 'unresolved')

    def test_unresolved_historical_result_is_neither_promoted_nor_given_new_price_reasons(self):
        value = deepcopy(self.review)
        value['result'].update(status='unresolved', proposed_action='unresolved', reason_codes=['missing_market_quote'])
        value['result'].pop('quote')
        current = current_decision_view(self.store, value, now=LATER)
        self.assertEqual(current['result'], value['result'])
        self.assertEqual(current['current_quote_check']['status'], 'unknown')
        # A fresh underlying review cannot promote a pre-existing unresolved
        # evaluation action, either.
        evaluated = deepcopy(self.evaluation); evaluated['action'] = 'unresolved'
        self.assertEqual(current_evaluation_view(self.store, evaluated, now=BOUNDARY)['action'], 'unresolved')

    def test_clock_type_and_policy_boundary_validation_do_not_mutate_inputs(self):
        original = deepcopy(self.review)
        for now in (None, [], {}, False, datetime(2026, 10, 9)):
            if now is None: continue  # None selects the runtime clock.
            with self.subTest(now=now), self.assertRaises(ValueError): current_decision_view(self.store, self.review, now=now)
        self.assertEqual(self.review, original)
        with self.assertRaises(ValueError): check_quote_timing(self.quote, 0, as_of=BOUNDARY)


if __name__ == '__main__': unittest.main()
