"""Post-fix recheck of one fictional current-view thesis-version mismatch.

Only memory databases are used. The earlier reproduction script/JSON remain
unchanged, and no repository source, tests, docs or actual DBs are modified.
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
from ir_agent.information_review import current_decision_view, current_evaluation_view
from test_decision_lifecycle import DecisionLifecycleTests


def original_hashes():
    return {str(path): sha256(path.read_bytes()).hexdigest() for path in (
        Path('/tmp/ir_current_thesis_version_repro.py'),
        Path('/tmp/ir_current_thesis_version_repro.json'))}


def main():
    originals = original_hashes()
    env = DecisionLifecycleTests(); env.setUp()
    try:
        env.receive(); quote = env.fresh_quote('1600')
        evaluation_request = env.evaluation(quote)
        env.harness.evaluate_reply(evaluation_request, now=datetime.fromisoformat('2026-10-09T17:00:00+09:00'))
        raw_evaluation = json.loads(env.store.connection.execute(
            'SELECT data FROM evaluations WHERE reply_id=? AND version=1', ('demo-reply-cost',)).fetchone()[0])
        request = {'reply_id': 'demo-reply-cost', 'expected_thesis_version': 2,
                   'recorded_at': '2026-10-09T17:05:00+09:00', 'decision_quote': deepcopy(quote)}
        reviewed = env.harness.review_decision(request, now=datetime.fromisoformat('2026-10-09T17:05:00+09:00'))
        raw_review = env.store.decision_review(reviewed['id'])
        now = datetime.fromisoformat('2026-10-09T17:11:00+09:00')
        before = current_decision_view(env.store, raw_review, now=now)
        old_thesis = env.store.thesis('demo-services')
        next_thesis = {**deepcopy(old_thesis), 'version': 3}
        assert {key: value for key, value in old_thesis.items() if key != 'version'} == {
            key: value for key, value in next_thesis.items() if key != 'version'}
        env.store.put_thesis(next_thesis, now=datetime.fromisoformat('2026-10-09T17:10:00+09:00'))
        dump_before = list(env.store.connection.iterdump())
        changes_before = env.store.connection.total_changes

        after = current_decision_view(env.store, raw_review, now=now)
        current_eval = current_evaluation_view(env.store, raw_evaluation, now=now)
        retry_review = env.harness.review_decision(request, now=now)
        retry_eval = env.harness.evaluate_reply(evaluation_request, now=now)
        with patch('ir_agent.information_review.now_iso', return_value=now.isoformat()):
            cli_review = run(Namespace(command='decision-review', operation='show', review_id=reviewed['id']), env.store)
        with patch('ir_agent.cli.now_iso', return_value=now.isoformat()):
            cli_reply = run(Namespace(command='reply', operation='show', reply_id='demo-reply-cost'), env.store)
        inbox = env.harness.inbox(now=now)
        try:
            env.harness.review_decision({**request, 'recorded_at': now.isoformat()}, now=now)
        except ValueError as error:
            guard_error = str(error)
        else:
            raise AssertionError('The new-request old-thesis guard must remain intact')

        assert 'Thesis changed' in guard_error
        assert before['result']['proposed_action'] == 'exit_review'
        assert before['current_thesis_check']['status'] == 'matched'
        for view in (after, retry_review, cli_review):
            assert view['result']['proposed_action'] == 'unresolved'
            assert view['current_validity'] == 'requires_thesis_review'
            assert view['current_review_requirements'] == ['requires_thesis_review']
            assert view['current_quote_check']['status'] == 'fresh'
            assert view['current_thesis_check']['reviewed_version'] == 2
            assert view['current_thesis_check']['current_version'] == 3
            assert view['historical_result'] == raw_review['result']
        for view in (current_eval, retry_eval, cli_reply['evaluations'][0]):
            assert view['action'] == 'unresolved'
            assert view['decision_status'] == 'requires_thesis_review'
            assert view['current_thesis_check']['current_version'] == 3
        assert inbox['replies_for_review'][0]['status'] == 'requires_thesis_review'
        assert raw_review['result']['proposed_action'] == raw_evaluation['action'] == 'exit_review'
        assert env.store.decision_review(raw_review['id']) == raw_review
        assert json.loads(env.store.connection.execute('SELECT data FROM evaluations WHERE reply_id=? AND version=1',
            ('demo-reply-cost',)).fetchone()[0]) == raw_evaluation
        assert list(env.store.connection.iterdump()) == dump_before
        assert env.store.connection.total_changes == changes_before
        assert original_hashes() == originals
        report = {
            'all_inputs_fictional': True, 'database': ':memory:', 'only_thesis_version_changed': True,
            'max_quote_age_seconds': raw_review['result']['policy_snapshot']['parameters']['max_quote_age_seconds'],
            'current_quote_check': after['current_quote_check'], 'current_thesis_check': after['current_thesis_check'],
            'before_action': before['result']['proposed_action'],
            'after': {'current_review': after['result']['proposed_action'], 'current_evaluation': current_eval['action'],
                      'review_retry': retry_review['result']['proposed_action'], 'evaluation_retry': retry_eval['action'],
                      'cli_review_show': cli_review['result']['proposed_action'],
                      'cli_reply_show': cli_reply['evaluations'][0]['action'],
                      'requirements': after['current_review_requirements'],
                      'inbox': inbox['replies_for_review'][0]['status']},
            'historical_exit_and_raw_records_unchanged': True, 'read_retry_db_dump_and_total_changes_unchanged': True,
            'new_review_old_version_guard': guard_error, 'original_reproduction_files_unchanged': True,
            'scope': 'Current-candidate version coherence only; no recomputation of old IR branches against v3.'
        }
        Path('/tmp/ir_thesis_version_recheck.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    finally:
        env.doCleanups()


if __name__ == '__main__':
    main()
