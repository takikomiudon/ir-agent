"""One fictional memory-only current-view/version mismatch reproduction.

Reuses unchanged existing fixture policy, quote and financial inputs. Appends
v3 through Store.put_thesis, changing only its version, within quote freshness.
"""
from argparse import Namespace
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import sys
from unittest.mock import patch

REPO = Path('/workspace/ir-agent')
sys.path[:0] = [str(REPO / 'src'), str(REPO / 'tests')]
from ir_agent.cli import run
from ir_agent.information_review import current_decision_view, current_evaluation_view
from test_decision_lifecycle import DecisionLifecycleTests


def main():
    env = DecisionLifecycleTests(); env.setUp()
    try:
        env.receive()
        quote = env.fresh_quote('1600')
        evaluated = env.harness.evaluate_reply(env.evaluation(quote),
            now=datetime.fromisoformat('2026-10-09T17:00:00+09:00'))
        raw_evaluation = json.loads(env.store.connection.execute(
            'SELECT data FROM evaluations WHERE reply_id=? AND version=1', ('demo-reply-cost',)).fetchone()[0])
        request = {'reply_id': 'demo-reply-cost', 'expected_thesis_version': 2,
                   'recorded_at': '2026-10-09T17:05:00+09:00', 'decision_quote': deepcopy(quote)}
        reviewed = env.harness.review_decision(request,
            now=datetime.fromisoformat('2026-10-09T17:05:00+09:00'))
        historical_review = env.store.decision_review(reviewed['id'])
        clock = datetime.fromisoformat('2026-10-09T17:11:00+09:00')
        before = current_decision_view(env.store, historical_review, now=clock)
        old_thesis = env.store.thesis('demo-services')
        next_thesis = {**deepcopy(old_thesis), 'version': 3}
        assert {k: v for k, v in next_thesis.items() if k != 'version'} == {
            k: v for k, v in old_thesis.items() if k != 'version'}
        env.store.put_thesis(next_thesis, now=datetime.fromisoformat('2026-10-09T17:10:00+09:00'))

        dump_before = list(env.store.connection.iterdump())
        changes_before = env.store.connection.total_changes
        after = current_decision_view(env.store, historical_review, now=clock)
        current_eval = current_evaluation_view(env.store, raw_evaluation, now=clock)
        retry = env.harness.review_decision(request, now=clock)
        with patch('ir_agent.information_review.now_iso', return_value=clock.isoformat()):
            cli = run(Namespace(command='decision-review', operation='show', review_id=reviewed['id']), env.store)
        new_request = {**request, 'recorded_at': clock.isoformat()}
        try:
            env.harness.review_decision(new_request, now=clock)
        except ValueError as error:
            guard_error = str(error)
        else:
            raise AssertionError('New v2 review should fail after thesis advances')
        assert 'Thesis changed' in guard_error
        assert before['result']['proposed_action'] == after['result']['proposed_action'] == 'exit_review'
        assert after['current_quote_check']['status'] == 'fresh'
        assert after['current_review_requirements'] == []
        assert current_eval['action'] == retry['result']['proposed_action'] == cli['result']['proposed_action'] == 'exit_review'
        assert env.store.thesis('demo-services')['version'] == 3
        assert env.store.decision_review(reviewed['id']) == historical_review
        assert list(env.store.connection.iterdump()) == dump_before
        assert env.store.connection.total_changes == changes_before
        report = {
            'all_inputs_fictional': True, 'database': ':memory:',
            'only_thesis_version_changed': True, 'policy_and_financial_inputs_unchanged': True,
            'quote_observed_at': quote['observed_at'], 'checked_at': clock.isoformat(),
            'max_quote_age_seconds': historical_review['result']['policy_snapshot']['parameters']['max_quote_age_seconds'],
            'current_quote_status': after['current_quote_check']['status'],
            'quote_age_microseconds': after['current_quote_check']['age_microseconds'],
            'before': {'store_thesis_version': 2, 'current_action': before['result']['proposed_action']},
            'after': {'store_thesis_version': 3, 'review_thesis_version': after['thesis_version'],
                      'current_action': after['result']['proposed_action'],
                      'current_validity': after['current_validity'],
                      'current_review_requirements': after['current_review_requirements'],
                      'historical_result_label_present': 'historical_result' in after,
                      'current_evaluation_action': current_eval['action'],
                      'same_request_retry_action': retry['result']['proposed_action'],
                      'cli_show_action': cli['result']['proposed_action']},
            'new_review_with_old_version_rejected': guard_error,
            'historical_review_unchanged': True, 'read_and_retry_db_unchanged': True,
            'scope': 'Version coherence of current-facing candidates, not financial recalculation or quote freshness.'
        }
        Path('/tmp/ir_current_thesis_version_repro.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    finally:
        env.doCleanups()


if __name__ == '__main__':
    main()
