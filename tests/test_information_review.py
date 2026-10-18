"""Information corrections retain originals and hold dependent decisions."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import unittest

from ir_agent.information_review import add_assessment, assessments, current_decision_view, current_evaluation_view
import test_decision_lifecycle as fixtures


class InformationReviewTests(unittest.TestCase):
    def setUp(self):
        self.env = fixtures.DecisionLifecycleTests('runTest')
        self.env.setUp(); self.addCleanup(self.env.doCleanups)
        self.env.receive()
        self.store = self.env.store; self.harness = self.env.harness
        self.request = {'reply_id': 'demo-reply-cost', 'expected_version': 0,
                        'information_status': 'potential_nonpublic',
                        'basis_quote': self.store.reply('demo-reply-cost')['raw_text'][:10],
                        'rationale': 'Classification withdrawn pending review of the public basis.',
                        'recorded_at': '2026-10-09T18:05:00+09:00'}
        self.now = '2026-10-09T09:05:00+00:00'

    def apply(self):
        self.quote = self.env.fresh_quote('1600', '2026-10-09T17:15:00+09:00')
        self.evaluation = self.env.evaluation(self.quote)
        self.evaluation['recorded_at'] = '2026-10-09T17:15:00+09:00'
        return self.harness.evaluate_reply(self.evaluation, now=fixtures.EVALUATED)

    def test_correction_is_append_only_idempotent_and_preserves_models_and_reviews(self):
        applied = self.apply()
        original_review = self.store.decision_review(applied['decision_review_id'])
        original_thesis = self.store.thesis('demo-services')
        original_reply = self.store.reply('demo-reply-cost')
        record = add_assessment(self.store, self.request, now=self.now)
        self.assertEqual(add_assessment(self.store, self.request, now=self.now), record)
        self.assertEqual(len(assessments(self.store, 'demo-reply-cost')), 1)
        viewed = current_decision_view(self.store, original_review, now=self.now)
        self.assertEqual(viewed['current_validity'], 'requires_information_review')
        self.assertEqual(viewed['result']['proposed_action'], 'unresolved')
        self.assertEqual(viewed['historical_result']['proposed_action'], 'exit_review')
        self.assertEqual(self.store.decision_review(applied['decision_review_id']), original_review)
        self.assertEqual(self.store.thesis('demo-services'), original_thesis)
        self.assertEqual(self.store.reply('demo-reply-cost'), original_reply)
        self.assertEqual(current_evaluation_view(self.store, applied, now=self.now)['action'], 'unresolved')
        retried = self.harness.evaluate_reply(self.evaluation, now=datetime(2026, 10, 9, 9, 10, tzinfo=timezone.utc))
        self.assertEqual(retried['decision_status'], 'requires_information_review')
        self.assertEqual(len(self.harness.inbox()['replies_for_review']), 1)

    def test_correction_is_not_visible_before_it_was_actually_saved(self):
        self.apply()
        delayed = deepcopy(self.request); delayed['recorded_at'] = '2026-10-09T18:01:00+09:00'
        add_assessment(self.store, delayed, now=self.now)
        self.assertEqual(assessments(self.store, 'demo-reply-cost', as_of='2026-10-09T18:04:00+09:00'), [])
        self.assertEqual(len(assessments(self.store, 'demo-reply-cost', as_of='2026-10-09T18:05:00+09:00')), 1)

    def test_future_price_review_consults_correction_without_reapplying_reply(self):
        self.apply(); add_assessment(self.store, self.request, now=self.now)
        quote = self.env.fresh_quote('1000', '2026-10-09T18:09:00+09:00', 'later')
        review = self.harness.review_decision({'reply_id': 'demo-reply-cost', 'expected_thesis_version': 2,
                    'recorded_at': '2026-10-09T18:10:00+09:00', 'decision_quote': quote},
                    now=datetime(2026, 10, 9, 9, 10, tzinfo=timezone.utc))
        self.assertEqual(review['result']['proposed_action'], 'unresolved')
        self.assertIn('reply_information_corrected', review['result']['reason_codes'])
        self.assertEqual(self.harness.status()['theses'], 2)
        self.assertEqual(self.harness.status()['evaluations'], 1)

    def test_initial_apply_cannot_override_current_unclear_classification(self):
        request = deepcopy(self.request); request.update(information_status='unclear', recorded_at='2026-10-09T16:59:00+09:00')
        add_assessment(self.store, request, now='2026-10-09T07:59:00+00:00')
        evaluation = self.env.evaluation(self.env.fresh_quote())
        evaluation['information_status'] = 'public_clarification'
        result = self.harness.evaluate_reply(evaluation, now=fixtures.EVALUATED)
        self.assertFalse(result['applied']); self.assertEqual(result['status'], 'held_for_review')
        self.assertEqual(result['information_status'], 'unclear')
        self.assertEqual(self.store.thesis('demo-services')['version'], 1)

    def test_review_versions_quotes_dates_and_schema_are_checked_without_partial_writes(self):
        variants = [dict(self.request, expected_version=1), dict(self.request, basis_quote='Never in the saved reply'),
                    dict(self.request, recorded_at='2026-10-10T18:05:00+09:00'),
                    dict(self.request, recorded_at='2026-10-08T18:05:00+09:00'),
                    dict(self.request, information_status='public'), dict(self.request, override_model=True)]
        for request in variants:
            with self.subTest(request=request), self.assertRaises(ValueError):
                add_assessment(self.store, request, now=self.now)
            self.assertEqual(assessments(self.store, 'demo-reply-cost'), [])
        first = add_assessment(self.store, self.request, now=self.now)
        changed = dict(self.request, rationale='Different rationale')
        with self.assertRaisesRegex(ValueError, 'version changed'):
            add_assessment(self.store, changed, now=self.now)
        second = dict(self.request, expected_version=1, information_status='public_clarification',
                      recorded_at='2026-10-09T18:10:00+09:00', rationale='Public basis subsequently confirmed.')
        add_assessment(self.store, second, now='2026-10-09T09:10:00+00:00')
        self.assertEqual(add_assessment(self.store, self.request, now=self.now), first)
        self.assertEqual(len(assessments(self.store, 'demo-reply-cost')), 2)

    def test_reaffirming_classification_does_not_reactivate_an_old_price_review(self):
        applied = self.apply()
        add_assessment(self.store, self.request, now=self.now)
        second = dict(self.request, expected_version=1, information_status='public_clarification',
                      recorded_at='2026-10-09T18:10:00+09:00', rationale='Public basis subsequently confirmed.')
        add_assessment(self.store, second, now='2026-10-09T09:10:00+00:00')
        review = current_decision_view(self.store, self.store.decision_review(applied['decision_review_id']),
                                       now='2026-10-09T18:10:00+09:00')
        self.assertEqual(review['current_validity'], 'requires_information_review')
        self.assertEqual(review['result']['proposed_action'], 'unresolved')

    def test_saving_a_historical_review_after_reaffirmation_does_not_claim_current_validity(self):
        self.apply()
        add_assessment(self.store, self.request, now=self.now)
        second = dict(self.request, expected_version=1, information_status='public_clarification',
                      recorded_at='2026-10-09T18:10:00+09:00', rationale='Public basis subsequently confirmed.')
        add_assessment(self.store, second, now='2026-10-09T09:10:00+00:00')
        quote = self.env.fresh_quote('1000', '2026-10-09T17:25:00+09:00', 'historical')
        saved = self.harness.review_decision({'reply_id': 'demo-reply-cost', 'expected_thesis_version': 2,
                    'recorded_at': '2026-10-09T17:30:00+09:00', 'decision_quote': quote},
                    now=datetime(2026, 10, 9, 9, 15, tzinfo=timezone.utc))
        self.assertEqual(self.store.decision_review(saved['id'])['result']['proposed_action'], 'hold_review')
        self.assertEqual(saved['historical_result']['proposed_action'], 'hold_review')
        self.assertEqual(saved['current_validity'], 'requires_information_review')
        self.assertEqual(saved['result']['proposed_action'], 'unresolved')
        self.assertNotIn('information_review_versions', saved['context'])
        self.assertEqual(current_decision_view(self.store, saved, now='2026-10-09T18:15:00+09:00')['result']['proposed_action'], 'unresolved')
        quote = self.env.fresh_quote('1000', '2026-10-09T18:14:00+09:00', 'after-reaffirmation')
        fresh = self.harness.review_decision({'reply_id': 'demo-reply-cost', 'expected_thesis_version': 2,
                    'recorded_at': '2026-10-09T18:15:00+09:00', 'decision_quote': quote},
                    now=datetime(2026, 10, 9, 9, 15, tzinfo=timezone.utc))
        self.assertEqual(fresh['context']['information_review_versions']['demo-reply-cost'], 2)
        self.assertEqual(current_decision_view(self.store, fresh, now='2026-10-09T18:15:00+09:00')['result']['proposed_action'], 'hold_review')


if __name__ == '__main__': unittest.main()
