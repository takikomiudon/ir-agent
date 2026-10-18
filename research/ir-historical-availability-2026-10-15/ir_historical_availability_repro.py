"""Memory-only reproduction of a historical thesis/daily availability gap.

All financial inputs are fictional fixtures. No external requests, real
databases, company contacts, or orders are used. The supplied trusted clocks
represent sequential processing stages, not the execution host's real clock.

Run: /workspace/ir-agent/.venv/bin/python /tmp/ir_historical_availability_repro.py
"""
from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

REPO = Path('/workspace/ir-agent')
sys.path.insert(0, str(REPO / 'src'))
sys.path.insert(0, str(REPO / 'tests'))
os.chdir(REPO)

from ir_agent.decision import evaluate_decision
from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.models import timestamp
from test_decision_lifecycle import DecisionLifecycleTests, CREATED, SAVED, EVALUATED


def main():
    env = DecisionLifecycleTests()
    with patch('ir_agent.store.now_iso', return_value='2026-10-09T00:58:00+00:00'):
        env.setUp()
    try:
        with patch('ir_agent.store.now_iso', return_value='2026-10-09T00:59:00+00:00'):
            env.harness.set_company_status('demo-services', 'active', 'Fictional position known before the design', held=False)
        policy = deepcopy(env.value['policy']); policy['id'] = 'explicit-user-policy'
        for declaration in policy['parameter_sources'].values():
            declaration['kind'] = 'user'
        env.harness.register_decision_policy(policy, now=CREATED)
        env.question['decision_contract'].update(policy_id=policy['id'], synthetic=False)
        env.question['decision_contract'].pop('synthetic_position')
        question = env.harness.add_question(env.question, now=SAVED)
        frozen_guard = False
        try:
            env.harness.mark_sent(env.question['id'], '2026-10-09T10:00:30+09:00', now=SAVED)
        except ValueError as error:
            frozen_guard = 'saved decision contract' in str(error)
        env.harness.mark_sent(env.question['id'], '2026-10-09T10:05:00+09:00',
                             now=datetime.fromisoformat('2026-10-09T10:06:00+09:00'))
        boundary = timestamp('2026-10-09T17:30:00+09:00')
        before = env.store.thesis('demo-services', as_of=boundary)
        first_daily_id = env.harness.daily(boundary.isoformat())['selected'][0]['job_id']
        # The late ingestion/evaluation phase is 18:00. The existing API saves
        # no independent source/reply first_saved_at, so their event timestamps
        # can legitimately be older while actual ingestion happens only now.
        with patch('ir_agent.store.now_iso', return_value=EVALUATED.isoformat()), \
             patch('ir_agent.harness.now_iso', return_value=EVALUATED.isoformat()):
            env.harness.add_reply(json.loads((REPO / 'examples/reply.json').read_text()))
            quote = env.fresh_quote('1000', '2026-10-09T17:15:00+09:00', 'late-ingested-at-18')
            request = env.evaluation(quote)
            request['recorded_at'] = '2026-10-09T17:20:00+09:00'
            evaluation = env.harness.evaluate_reply(request, now=EVALUATED)
        after = env.store.thesis('demo-services', as_of=boundary)
        last_daily_id = env.harness.daily(boundary.isoformat())['selected'][0]['job_id']
        review = evaluation['decision_review']
        first_saved = env.store.connection.execute('SELECT first_saved_at FROM decision_reviews WHERE id=?',
                                                  (review['id'],)).fetchone()[0]
        current = evaluate_decision({'as_of': EVALUATED.isoformat(), 'thesis': env.store.thesis('demo-services'),
                                    'policy': policy, 'quote': quote,
                                    'sources': DecisionLifecycle(env.store).sources_for(after, quote),
                                    'context': {'held': False, 'thesis_status': 'intact',
                                                'information_status': 'public_clarification',
                                                'evidence_ids': after['evidence_ids']}})
        report = {
            'all_inputs_are_fictional': True,
            'database': ':memory:',
            'contract_mode_under_test': 'synthetic:false; explicit user policy and observed position',
            'processing_time': EVALUATED.isoformat(),
            'historical_as_of': boundary.isoformat(),
            'before_late_processing': {'thesis_version': before['version'], 'daily_job_id': first_daily_id},
            'after_late_processing': {'thesis_version': after['version'], 'daily_job_id': last_daily_id,
                                      'packet_thesis_version': env.store.job(last_daily_id)['packet']['thesis']['version']},
            'review': {'evaluation_time': review['recorded_at'], 'actual_first_saved_at': first_saved,
                       'candidate_action': evaluation['action'], 'candidate_at_actual_processing_time': current['proposed_action']},
            'derived_reply_source_retrieved_at': env.store.source('reply:demo-reply-cost')['retrieved_at'],
            'existing_frozen_contract_blocks_earlier_send': frozen_guard,
            'finding': 'The same 17:30 thesis/daily lookup changes from version 1 to version 2 after processing at 18:00.',
            'not_a_finding': 'The review honestly stores first_saved_at=18:00. This does not show a decision was stored at 17:20; the current candidate is not itself the defect.'
        }
        assert before['version'] == 1 and after['version'] == 2
        assert env.store.job(last_daily_id)['packet']['thesis']['version'] == 2
        assert first_daily_id != last_daily_id and frozen_guard
        assert timestamp(first_saved) == EVALUATED
        assert current['proposed_action'] == 'buy_review'
        output = Path('/tmp/ir_historical_availability_repro.json')
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        env.doCleanups()


if __name__ == '__main__':
    main()
