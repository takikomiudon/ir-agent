"""One fictional memory-only stale-current-view case; no external operations.

Uses the existing test_reply_uses_frozen_policy_actual_position_and_saved_price
fixture's held position, 1600 JPY quote and unchanged policy. Only the trusted
processing time is moved to 20:00; financial values/thresholds are not fitted.
"""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import sys

REPO = Path('/workspace/ir-agent')
sys.path[:0] = [str(REPO / 'src'), str(REPO / 'tests')]
from ir_agent.decision import evaluate_decision
from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.information_review import current_decision_view, current_evaluation_view
from ir_agent.models import timestamp
from test_decision_lifecycle import DecisionLifecycleTests


def main():
    env = DecisionLifecycleTests(); env.setUp()
    try:
        env.receive()
        quote = env.fresh_quote('1600')
        saved_now = datetime.fromisoformat('2026-10-09T20:00:00+09:00')
        evaluation = env.harness.evaluate_reply(env.evaluation(quote), now=saved_now)
        automatic_review = evaluation['decision_review']
        request = {'reply_id': 'demo-reply-cost', 'expected_thesis_version': 2,
                   'recorded_at': '2026-10-09T17:30:00+09:00', 'decision_quote': deepcopy(quote)}
        added_review = env.harness.review_decision(request, now=saved_now)
        current_view = current_decision_view(env.store, added_review)
        evaluation_view = current_evaluation_view(env.store, evaluation)
        question = env.store.question(env.question['id'])
        policy = question['decision_contract']['policy_snapshot']
        thesis = env.store.thesis('demo-services')
        inputs = {'synthetic': True, 'as_of': saved_now.isoformat(), 'thesis': thesis,
                  'policy': policy, 'quote': deepcopy(quote),
                  'sources': DecisionLifecycle(env.store).sources_for(thesis, quote),
                  'context': deepcopy(added_review['context'])}
        at_saved_now = evaluate_decision(inputs)
        historical_inputs = {**inputs, 'as_of': request['recorded_at']}
        historical = evaluate_decision(historical_inputs)
        actual_first_saved = env.store.connection.execute(
            'SELECT first_saved_at FROM decision_reviews WHERE id=?', (added_review['id'],)).fetchone()[0]
        report = {
            'all_inputs_fictional': True, 'database': ':memory:',
            'fixture': 'test_reply_uses_frozen_policy_actual_position_and_saved_price',
            'trusted_save_now': saved_now.isoformat(), 'quote_observed_at': quote['observed_at'],
            'max_quote_age_seconds': policy['parameters']['max_quote_age_seconds'],
            'quote_age_at_save_seconds': int((saved_now - timestamp(quote['observed_at'])).total_seconds()),
            'review_applied': {'recorded_at': automatic_review['recorded_at'],
                               'default_evaluation_action': evaluation['action'],
                               'result': automatic_review['result']['proposed_action']},
            'add_review': {'recorded_at': added_review['recorded_at'],
                           'first_saved_at': actual_first_saved, 'result': added_review['result']['proposed_action']},
            'default_current_view': {'result': current_view['result']['proposed_action'],
                                     'current_validity': current_view['current_validity'],
                                     'has_historical_result': 'historical_result' in current_view},
            'current_evaluation_view_action': evaluation_view['action'],
            'pure_historical': {'as_of': historical_inputs['as_of'],
                                'result': historical['proposed_action'], 'reasons': historical['reason_codes']},
            'pure_at_save_now': {'as_of': inputs['as_of'], 'result': at_saved_now['proposed_action'],
                                 'reasons': at_saved_now['reason_codes']},
            'scope': 'Historical calculation and its honest save time are valid; default current-facing action lacks a trusted-current quote freshness gate.'
        }
        assert evaluation['action'] == added_review['result']['proposed_action'] == 'exit_review'
        assert current_view['result']['proposed_action'] == evaluation_view['action'] == 'exit_review'
        assert historical['proposed_action'] == 'exit_review'
        assert at_saved_now['proposed_action'] == 'unresolved'
        assert at_saved_now['reason_codes'] == ['market_quote_stale']
        assert timestamp(actual_first_saved) == saved_now
        Path('/tmp/ir_stale_current_decision_repro.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    finally:
        env.doCleanups()


if __name__ == '__main__':
    main()
