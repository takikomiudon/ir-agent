"""Independent post-integration recheck; fictional memory-only records."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import sqlite3
import sys
from unittest.mock import patch

REPO = Path('/workspace/ir-agent')
sys.path[:0] = [str(REPO / 'src'), str(REPO / 'tests')]
from ir_agent.availability import RecordAvailability, SCHEMA as AVAILABILITY_SCHEMA
from ir_agent.decision import evaluate_decision
from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.models import json_text, timestamp, validate_source
from ir_agent.store import Store, SCHEMA as STORE_SCHEMA
from test_decision_lifecycle import DecisionLifecycleTests, CREATED, SAVED, EVALUATED


def late_reply():
    env = DecisionLifecycleTests()
    with patch('ir_agent.store.now_iso', return_value='2026-10-09T00:58:00+00:00'):
        env.setUp()
    try:
        with patch('ir_agent.store.now_iso', return_value='2026-10-09T00:59:00+00:00'):
            env.harness.set_company_status('demo-services', 'active', 'Fictional pre-design position', held=False)
        policy = deepcopy(env.value['policy']); policy['id'] = 'explicit-user-policy'
        for declaration in policy['parameter_sources'].values():
            declaration['kind'] = 'user'
        env.harness.register_decision_policy(policy, now=CREATED)
        env.question['decision_contract'].update(policy_id=policy['id'], synthetic=False)
        env.question['decision_contract'].pop('synthetic_position')
        env.harness.add_question(env.question, now=SAVED)
        env.harness.mark_sent(env.question['id'], '2026-10-09T10:05:00+09:00',
                             now=datetime.fromisoformat('2026-10-09T10:06:00+09:00'))
        boundary = timestamp('2026-10-09T17:30:00+09:00')
        before = env.store.thesis('demo-services', as_of=boundary, now=EVALUATED)
        first_id = env.harness.daily(boundary.isoformat(), now=EVALUATED)['selected'][0]['job_id']
        first_packet = deepcopy(env.store.job(first_id)['packet'])
        env.harness.add_reply(json.loads((REPO / 'examples/reply.json').read_text()), now=EVALUATED)
        source = deepcopy(env.value['sources'][1]); source['id'] = 'late-ingested-at-18'
        source['retrieved_at'] = '2026-10-09T17:15:00+09:00'
        source['metadata'].update(price_jpy='1000', observed_at=source['retrieved_at'])
        env.harness.ingest({'schema_version': 1, 'sources': [source]}, now=EVALUATED)
        quote = deepcopy(env.value['quote'])
        quote.update(source_id=source['id'], price_jpy='1000', retrieved_at=source['retrieved_at'],
                     observed_at=source['retrieved_at'])
        request = env.evaluation(quote); request['recorded_at'] = '2026-10-09T17:20:00+09:00'
        evaluation = env.harness.evaluate_reply(request, now=EVALUATED)
        after = env.store.thesis('demo-services', as_of=boundary, now=EVALUATED)
        last_id = env.harness.daily(boundary.isoformat(), now=EVALUATED)['selected'][0]['job_id']
        retrospective = env.store.thesis_view('demo-services', as_of=boundary,
            knowledge_at=EVALUATED, mode='retrospective', now=EVALUATED)
        latest = env.store.thesis('demo-services')
        current = evaluate_decision({'as_of': EVALUATED.isoformat(), 'thesis': latest, 'policy': policy,
            'quote': quote, 'sources': DecisionLifecycle(env.store).sources_for(latest, quote),
            'context': {'held': False, 'thesis_status': 'intact', 'information_status': 'public_clarification',
                        'evidence_ids': latest['evidence_ids']}})
        assert before['version'] == after['version'] == 1
        assert first_id == last_id and env.store.job(last_id)['packet'] == first_packet
        assert retrospective['record']['version'] == latest['version'] == 2
        assert current['proposed_action'] == 'buy_review'
        return {'before_version': before['version'], 'after_version': after['version'],
                'same_job_id': first_id == last_id, 'packet_unchanged': env.store.job(last_id)['packet'] == first_packet,
                'packet_version': first_packet['thesis']['version'], 'current_version': latest['version'],
                'retrospective_version': retrospective['record']['version'],
                'retrospective_label': retrospective['temporal_mode'],
                'current_candidate': current['proposed_action'], 'saved_review_candidate': evaluation['action']}
    finally:
        env.doCleanups()


def parent_dag():
    store = Store(':memory:')
    try:
        store.put_company({'id': 'dag', 'name': 'Fictional DAG', 'held': False, 'status': 'active'})
        def source(identity, parents=()):
            return validate_source({'id': identity, 'company_id': 'dag', 'title': identity,
                'url': 'https://example.test/' + identity, 'content': 'Fictional source',
                'source_type': 'public_disclosure', 'retrieved_at': '2026-10-09T16:00:00+09:00',
                'published_at': None, 'metadata': {'original_source_ids': list(parents)}})
        for item in (source('shared'), source('a', ['shared']), source('cycle-a', ['cycle-b']),
                     source('cycle-b', ['cycle-a']), source('missing', ['absent'])):
            store.put_source(item, now='2026-10-09T16:00:00+09:00')
        root = source('root', ['a', 'late-b'])
        store.put_source(root, now='2026-10-09T17:00:00+09:00')
        store.put_source(source('late-b', ['shared']), now='2026-10-09T18:00:00+09:00')
        strict = store.source_availability(root, as_of='2026-10-09T17:30:00+09:00', now=EVALUATED)
        retro = store.source_availability(root, as_of='2026-10-09T17:30:00+09:00',
                                          knowledge_at=EVALUATED, now=EVALUATED)
        cycle = store.source_availability(store.source('cycle-a'), as_of=EVALUATED, now=EVALUATED)
        missing = store.source_availability(store.source('missing'), as_of=EVALUATED, now=EVALUATED)
        assert strict['available'] is False and retro['available'] is True
        assert sum(item['source_id'] == 'shared' for item in retro['checks']) == 1
        assert cycle['available'] is False and missing['available'] is None
        return {'strict': strict['available'], 'strict_reasons': strict['reason_codes'],
                'retrospective': retro['available'], 'shared_parent_count': 1,
                'cycle': cycle['available'], 'cycle_reasons': cycle['reason_codes'],
                'missing': missing['available'], 'missing_reasons': missing['reason_codes']}
    finally:
        store.close()


def legacy_open():
    original_connect = sqlite3.connect
    results = []
    for case in ('future_declared', 'invalid_declared', 'receipt_clock_ahead'):
        db = original_connect(':memory:', isolation_level=None)
        db.row_factory = sqlite3.Row
        db.executescript(STORE_SCHEMA + AVAILABILITY_SCHEMA)
        company = {'id': 'legacy', 'name': 'Fictional legacy', 'status': 'active', 'held': False}
        db.execute('INSERT INTO companies VALUES (?,?)', ('legacy', json_text(company)))
        source = {'id': 'legacy-source', 'company_id': 'legacy', 'retrieved_at': '2026-10-09T16:00:00+09:00',
                  'published_at': None, 'content': 'Fictional legacy', 'metadata': {}}
        if case == 'future_declared': source['retrieved_at'] = '2026-10-09T19:00:00+09:00'
        if case == 'invalid_declared': source['retrieved_at'] = 'bad'
        db.execute('INSERT INTO sources VALUES (?,?,?,?)', ('legacy-source', 'legacy', 'legacy-hash', json_text(source)))
        if case == 'receipt_clock_ahead':
            db.execute('BEGIN')
            RecordAvailability(db).record_first_save('source', source['id'], source, now='2026-10-09T19:00:00+09:00')
            db.execute('COMMIT')
        with patch('ir_agent.store.sqlite3.connect', return_value=db), \
             patch('ir_agent.store.now_iso', return_value=EVALUATED.isoformat()):
            reopened = Store(':memory:')
        try:
            assert reopened.source(source['id']) == source
            ledger_view = RecordAvailability(db).at('source', source['id'], source,
                as_of=EVALUATED, knowledge_at=EVALUATED, now=EVALUATED)
            try:
                store_view = reopened.source_availability(source, as_of=EVALUATED, now=EVALUATED)
            except ValueError as error:
                store_view = {'error': str(error)}
            results.append({'case': case, 'current_open_ok': True, 'raw_unchanged': True,
                            'library_status': ledger_view['status'], 'library_reasons': ledger_view['reason_codes'],
                            'store_view': store_view.get('available', store_view)})
        finally:
            reopened.close()
    return results


if __name__ == '__main__':
    result = {'all_inputs_fictional': True, 'database': ':memory:', 'late_reply': late_reply(),
              'source_dag': parent_dag(), 'legacy_open': legacy_open()}
    Path('/tmp/ir_historical_availability_recheck.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
