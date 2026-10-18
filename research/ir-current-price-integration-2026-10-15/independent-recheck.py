"""Post-fix current quote recheck, one fictional memory-only workflow.

The prior /tmp/ir_stale_current_decision_repro.py and JSON are read for hashes
only. No repository sources/tests/docs, real databases or networks are changed.
"""
from argparse import Namespace
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

REPO = Path('/workspace/ir-agent')
sys.path[:0] = [str(REPO / 'src'), str(REPO / 'tests')]
from ir_agent.cli import run
from ir_agent.decision import evaluate_decision
from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.information_review import current_decision_view
from test_decision_lifecycle import DecisionLifecycleTests


def unchanged_originals():
    return {str(path): sha256(path.read_bytes()).hexdigest() for path in (
        Path('/tmp/ir_stale_current_decision_repro.py'),
        Path('/tmp/ir_stale_current_decision_repro.json'))}


def database_snapshot(db):
    return {'dump': list(db.iterdump()), 'total_changes': db.total_changes}


def main():
    originals = unchanged_originals()
    env = DecisionLifecycleTests(); env.setUp()
    try:
        env.receive()
        quote = env.fresh_quote('1600')
        save_now = datetime.fromisoformat('2026-10-09T20:00:00+09:00')
        evaluation_request = env.evaluation(quote)
        evaluated = env.harness.evaluate_reply(evaluation_request, now=save_now)
        raw_evaluation = json.loads(env.store.connection.execute(
            'SELECT data FROM evaluations WHERE reply_id=? AND version=1', ('demo-reply-cost',)).fetchone()[0])
        raw_auto_review = env.store.decision_review(evaluated['decision_review_id'])
        review_request = {'reply_id': 'demo-reply-cost', 'expected_thesis_version': 2,
                          'recorded_at': '2026-10-09T17:30:00+09:00', 'decision_quote': deepcopy(quote)}
        reviewed = env.harness.review_decision(review_request, now=save_now)
        raw_review = env.store.decision_review(reviewed['id'])
        policy = raw_review['result']['policy_snapshot']
        assert policy['parameters']['max_quote_age_seconds'] == 3600
        assert evaluated['action'] == reviewed['result']['proposed_action'] == 'unresolved'
        assert raw_evaluation['action'] == raw_auto_review['result']['proposed_action'] == 'exit_review'
        assert raw_review['result']['proposed_action'] == 'exit_review'
        assert reviewed['historical_result'] == raw_review['result']

        before_retry = database_snapshot(env.store.connection)
        retry_eval = env.harness.evaluate_reply(evaluation_request, now=save_now)
        retry_review = env.harness.review_decision(review_request, now=save_now)
        with patch('ir_agent.information_review.now_iso', return_value=save_now.isoformat()):
            cli_review = run(Namespace(command='decision-review', operation='show', review_id=reviewed['id']), env.store)
        with patch('ir_agent.cli.now_iso', return_value=save_now.isoformat()):
            cli_reply = run(Namespace(command='reply', operation='show', reply_id='demo-reply-cost'), env.store)
        inbox = env.harness.inbox(now=save_now)
        after_retry = database_snapshot(env.store.connection)
        assert before_retry == after_retry
        assert retry_eval['action'] == retry_review['result']['proposed_action'] == 'unresolved'
        assert cli_review['result']['proposed_action'] == cli_reply['evaluations'][0]['action'] == 'unresolved'
        assert inbox['replies_for_review'][0]['status'] == 'requires_price_review'

        # The same old-price boundary is checked for the 17:00 quote, which
        # remains stale at 20:00 even when it is newly ingested at 20:00.
        quote17 = env.fresh_quote('1600', '2026-10-09T17:00:00+09:00', 'stale-at-17')
        request17 = {**review_request, 'decision_quote': quote17}
        review17 = env.harness.review_decision(request17, now=save_now)
        assert review17['result']['proposed_action'] == 'unresolved'
        assert env.store.decision_review(review17['id'])['result']['proposed_action'] == 'exit_review'

        # A genuinely new saved quote and a distinct review can recover a
        # current candidate; the old review is kept untouched.
        fresh_quote = env.fresh_quote('1600', save_now.isoformat(), 'fresh-at-20')
        fresh_request = {**review_request, 'recorded_at': save_now.isoformat(), 'decision_quote': fresh_quote}
        fresh = env.harness.review_decision(fresh_request, now=save_now)
        assert fresh['id'] != reviewed['id']
        assert fresh['result']['proposed_action'] == 'exit_review'
        assert fresh['current_quote_check']['status'] == 'fresh'
        before_fresh_retry = database_snapshot(env.store.connection)
        assert env.harness.review_decision(fresh_request, now=save_now)['result']['proposed_action'] == 'exit_review'
        assert before_fresh_retry == database_snapshot(env.store.connection)

        fresh_raw = env.store.decision_review(fresh['id'])
        exact = current_decision_view(env.store, fresh_raw, now='2026-10-09T21:00:00+09:00')
        plus_one = current_decision_view(env.store, fresh_raw, now='2026-10-09T21:00:00.000001+09:00')
        assert exact['result']['proposed_action'] == 'exit_review'
        assert exact['current_quote_check']['age_microseconds'] == 3600000000
        assert plus_one['result']['proposed_action'] == 'unresolved'
        assert plus_one['current_quote_check']['age_microseconds'] == 3600000001
        assert 'market_quote_stale' in plus_one['result']['reason_codes']
        assert env.store.decision_review(raw_review['id']) == raw_review
        assert env.store.decision_review(raw_auto_review['id']) == raw_auto_review
        assert before_fresh_retry == database_snapshot(env.store.connection)

        pure_now = evaluate_decision({'synthetic': True, 'as_of': save_now.isoformat(),
            'thesis': env.store.thesis('demo-services'), 'policy': policy, 'quote': quote,
            'sources': DecisionLifecycle(env.store).sources_for(env.store.thesis('demo-services'), quote),
            'context': deepcopy(raw_review['context'])})
        assert pure_now['proposed_action'] == 'unresolved' and pure_now['reason_codes'] == ['market_quote_stale']
        assert originals == unchanged_originals()
        report = {
            'all_inputs_fictional': True, 'database': ':memory:', 'max_quote_age_seconds': 3600,
            'trusted_save_now': save_now.isoformat(),
            'stale_16_59': {'initial_evaluation_action': evaluated['action'],
                'initial_review_action': reviewed['result']['proposed_action'],
                'raw_historical_action': raw_review['result']['proposed_action'],
                'current_reason': reviewed['current_quote_check']['reason_codes']},
            'stale_17_00': {'current_action': review17['result']['proposed_action'],
                'quote_status': review17['current_quote_check']['status']},
            'retry_and_read_views': {'evaluation_action': retry_eval['action'],
                'review_action': retry_review['result']['proposed_action'],
                'cli_review_show': cli_review['result']['proposed_action'],
                'cli_reply_show': cli_reply['evaluations'][0]['action'],
                'inbox_status': inbox['replies_for_review'][0]['status'], 'no_db_writes': before_retry == after_retry},
            'new_quote_new_review': {'new_id': fresh['id'] != reviewed['id'],
                'action': fresh['result']['proposed_action'], 'quote_status': fresh['current_quote_check']['status'],
                'retry_no_db_writes': before_fresh_retry == database_snapshot(env.store.connection)},
            'expiry_boundary': {'exact_age_us': exact['current_quote_check']['age_microseconds'],
                'exact_action': exact['result']['proposed_action'],
                'plus_one_us_age': plus_one['current_quote_check']['age_microseconds'],
                'plus_one_us_action': plus_one['result']['proposed_action']},
            'pure_at_save_now': {'action': pure_now['proposed_action'], 'reasons': pure_now['reason_codes']},
            'historical_records_unchanged': True, 'original_reproduction_files_unchanged': True,
            'scope': 'Quote timing gate only; no claim of full current investment revalidation.'
        }
        Path('/tmp/ir_current_quote_recheck.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    finally:
        env.doCleanups()


if __name__ == '__main__':
    main()
