"""Synthetic IR lifecycle plus policy review; uses only a temporary local DB."""
from __future__ import annotations

from copy import deepcopy
import json
from datetime import datetime
from pathlib import Path

from ir_agent.decision import evaluate_decision, evaluate_ir_plan
from ir_agent.harness import Harness
from ir_agent.models import load_json
from ir_agent.store import Store

ROOT = Path(__file__).resolve().parents[1]


def run_demo() -> dict:
    examples = ROOT / 'examples'
    store = Store(':memory:')
    try:
        harness = Harness(store)
        harness.ingest(load_json(examples / 'demo.json'), now=datetime.fromisoformat('2026-10-08T15:06:00+09:00'))
        selected = harness.daily('2026-10-08', now=datetime.fromisoformat('2026-10-09T08:58:00+09:00'))['selected']
        job = harness.claim('synthetic-demo', measurement_synthetic=True, now=datetime.fromisoformat("2026-10-09T08:59:00+09:00"))
        assert job and job['id'] == selected[0]['job_id']
        harness.complete(job['id'], 'synthetic-demo', load_json(examples / 'research-result.json'), expected_attempt=job['attempts'], now=datetime.fromisoformat('2026-10-09T09:00:00+09:00'))
        request = load_json(examples / 'ir-plan.json')
        request['thesis'] = store.thesis('demo-services')
        request['question']['thesis_version'] = request['thesis']['version']
        request['question']['evidence_ids'] = request['thesis']['evidence_ids']
        request['context']['held'] = store.company('demo-services')['held']
        price_source = deepcopy(next(x for x in request['sources'] if x['id'] == request['quote']['source_id']))
        request['sources'] = store.sources('demo-services') + [price_source]
        before_sending = evaluate_ir_plan(request)
        harness.add_question(request['question'], now=datetime.fromisoformat('2026-10-09T10:01:00+09:00'))
        # This is a synthetic sent-state record in an in-memory DB, not a send.
        harness.mark_sent(request['question']['id'], '2026-10-09T11:00:00+09:00')
        harness.add_reply(load_json(examples / 'reply.json'), now=datetime.fromisoformat('2026-10-09T16:00:00+09:00'))
        applied = harness.evaluate_reply(load_json(examples / 'reply-evaluation.json'), now=datetime.fromisoformat('2026-10-09T17:00:00+09:00'))
        request['thesis'] = store.thesis('demo-services')
        request['as_of'] = '2026-10-09T17:30:00+09:00'
        request['quote'].update(observed_at='2026-10-09T17:25:00+09:00', retrieved_at='2026-10-09T17:26:00+09:00')
        price_source['retrieved_at'] = request['quote']['retrieved_at']
        price_source['metadata']['observed_at'] = request['quote']['observed_at']
        request['sources'] = store.sources('demo-services') + [price_source]
        request['context'].update(thesis_status='intact', information_status='public_clarification',
                                  evidence_ids=request['thesis']['evidence_ids'])
        after_reply = evaluate_decision(request)
        return {'synthetic': True, 'external_send_count': 0, 'order_count': 0,
                'before_sending': before_sending,
                'reply_application': {'thesis_version': applied['thesis_version'],
                                      'precommitted_action': applied['precommitted_action'], 'applied': applied['applied']},
                'after_reply': after_reply,
                'note': 'The precommitted proposal and price/position-aware review are distinct; all inputs are fictional.'}
    finally:
        store.close()


if __name__ == '__main__':
    print(json.dumps(run_demo(), ensure_ascii=False, indent=2))
