"""Synthetic policy -> frozen question -> reply -> price review persistence.

All source content, prices and thresholds are fictional. The sent-state record
exists only in an in-memory DB. No network calls, IR sends or orders occur.
"""
from copy import deepcopy
import json
from datetime import datetime
from pathlib import Path

from ir_agent.harness import Harness
from ir_agent.models import load_json
from ir_agent.store import Store

ROOT = Path(__file__).resolve().parents[1]


def run_demo():
    examples = ROOT / 'examples'
    store = Store(':memory:')
    try:
        harness = Harness(store)
        harness.ingest(load_json(examples / 'demo.json'), now=datetime.fromisoformat('2026-10-08T15:06:00+09:00'))
        harness.daily('2026-10-08', now=datetime.fromisoformat('2026-10-09T08:58:00+09:00'))
        job = harness.claim('policy-demo', measurement_synthetic=True, now=datetime.fromisoformat("2026-10-09T08:59:00+09:00"))
        harness.complete(job['id'], 'policy-demo', load_json(examples / 'research-result.json'), expected_attempt=job['attempts'], now=datetime.fromisoformat('2026-10-09T09:00:00+09:00'))
        value = load_json(examples / 'ir-plan.json')
        harness.register_decision_policy(value['policy'], now=datetime.fromisoformat('2026-10-09T09:01:00+09:00'))
        price = deepcopy(value['sources'][1])
        harness.ingest({'schema_version': 1, 'sources': [price]}, now=datetime.fromisoformat(price['retrieved_at']))
        question = value['question']
        question.update(thesis_version=2, evidence_ids=store.thesis('demo-services')['evidence_ids'],
                        decision_contract={'policy_id': value['policy']['id'], 'policy_version': 1,
                                           'quote': value['quote'], 'synthetic': True,
                                           'synthetic_position': {'held': True, 'observed_at': '2026-10-09T09:59:00+09:00'}})
        draft = harness.add_question(question, now=datetime.fromisoformat("2026-10-09T10:01:00+09:00"))
        harness.mark_sent(question['id'], '2026-10-09T10:05:00+09:00')
        harness.add_reply(load_json(examples / 'reply.json'), now=datetime.fromisoformat('2026-10-09T16:00:00+09:00'))
        price.update(id='synthetic-price-after-reply', retrieved_at='2026-10-09T16:59:00+09:00')
        price['metadata'].update(price_jpy='1600', observed_at='2026-10-09T16:58:00+09:00')
        harness.ingest({'schema_version': 1, 'sources': [price]}, now=datetime.fromisoformat(price['retrieved_at']))
        quote = deepcopy(value['quote'])
        quote.update(source_id=price['id'], price_jpy='1600', observed_at=price['metadata']['observed_at'], retrieved_at=price['retrieved_at'])
        evaluation = load_json(examples / 'reply-evaluation.json')
        evaluation['decision_quote'] = quote
        applied = harness.evaluate_reply(evaluation, now=datetime.fromisoformat("2026-10-09T17:00:00+09:00"))
        return {'synthetic': True, 'network_requests': 0, 'external_sends': 0, 'orders': 0,
                'policy_id': value['policy']['id'], 'frozen_policy_version': draft['decision_contract']['policy_version'],
                'preflight': draft['decision_contract']['preflight']['question_value'],
                'precommitted_proposal': applied['precommitted_action'], 'price_checked_action': applied['action'],
                'price_checked_reasons': applied['decision_review']['result']['reason_codes'],
                'stored_review': store.decision_review(applied['decision_review_id']), 'records': harness.status()}
    finally:
        store.close()


if __name__ == '__main__':
    print(json.dumps(run_demo(), ensure_ascii=False, indent=2))
