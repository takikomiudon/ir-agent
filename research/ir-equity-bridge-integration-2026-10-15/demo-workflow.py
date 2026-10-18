"""One synthetic, in-memory public-clarification workflow; no external sends.

Fictional runtime clocks are explicit. Reuses the synthetic integration fixture,
not real-company values, author examples or live research/database records.
"""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
from ir_agent.decision import _flatten
from ir_agent.harness import Harness
from ir_agent.models import json_text, validate_source
from ir_agent.store import Store
from test_equity_bridge_integration import METHOD, synthetic_bridge_plan


def clock(value):
    return datetime.fromisoformat(value)


def main():
    value = synthetic_bridge_plan('non_operating_assets_jpy')
    company_id = value['thesis']['company_id']
    value['policy']['id'] = 'synthetic-equity-bridge-policy'
    value['thesis'].update(
        statement='Synthetic base equity bridge has non-operating assets 10 JPY and minority interests 10 JPY; all explicit FCFF/rate inputs remain fixed.',
        pillars=['Fictional fixed explicit-FCFF scenarios.', 'Fictional asset amount may receive a public clarification.'],
        invalidation_conditions=['Fictional asset amount is unavailable under the adverse precommitted branch.'])
    source = value['sources'][0]
    source['title'] = 'Synthetic initial public asset-category note'
    source['content'] = 'Fictional public asset-category note. The initial synthetic base bridge assumes non-operating assets 10 JPY and minority interests 10 JPY. No actual issuer information.'
    question = value['question']
    question.update(
        question='架空の公開資料に示された非営業資産の金額について、基本ケース10円と異なる20円が確認される場合の公表済み説明を照合する合成例です。',
        topic='Synthetic non-operating asset public clarification',
        target_parameter='scenarios.base.inputs.non_operating_assets_jpy')
    first, adverse, unclear = question['branches']
    first.update(id='assets_confirmed_20', condition='架空の公開補足で非営業資産20円と確認される。',
        interpretation='事前許可された基本ケースの非営業資産10円だけを20円へ更新し、他の入力を維持する。')
    adverse.update(id='assets_unavailable_0', condition='架空の公開補足で当該非営業資産を利用できないと確認される。',
        interpretation='事前保存した0円の不利な枝を点検する。今回この枝は観測していない。')
    unclear.update(condition='説明が曖昧/無回答/公表根拠を確認できない。',
        interpretation='仮説と評価を変更せず未解決のままにする。')
    question['decision_contract'] = {
        'policy_id': value['policy']['id'], 'policy_version': 1,
        'quote': deepcopy(value['quote']), 'synthetic': True,
        'synthetic_position': {'held': True, 'observed_at': '2026-10-09T09:59:00+09:00'}}
    template = json.loads((ROOT / 'examples/demo.json').read_text())
    company = next(item for item in template['companies'] if item['id'] == company_id)
    company.update(name='Synthetic equity bridge company', held=True,
                   screening_reason='Synthetic software workflow only; no actual investment screen.')
    bundle = {'schema_version': 1, 'companies': [company], 'sources': value['sources'], 'theses': [value['thesis']]}
    store = Store(':memory:')
    try:
        harness = Harness(store)
        assert all(not row['file'] for row in store.connection.execute('PRAGMA database_list'))
        harness.ingest(bundle, now=clock('2026-10-09T10:00:00+09:00'))
        harness.register_decision_policy(value['policy'], now=clock('2026-10-09T10:00:00+09:00'))
        saved_question = harness.add_question(question, now=clock('2026-10-09T10:01:00+09:00'))
        assert saved_question['decision_contract']['preflight']['question_value'] == 'decision_distinguishing'
        old_thesis = store.connection.execute('SELECT data FROM theses WHERE company_id=? AND version=1', (company_id,)).fetchone()['data']
        old_question = store.connection.execute('SELECT data FROM questions WHERE id=?', (question['id'],)).fetchone()['data']
        before = _flatten(json.loads(old_thesis)['valuation'])
        # This marks a fictional send in an in-memory fixture only. There is
        # no transport, recipient, form, external message or real sent-state.
        harness.mark_sent(question['id'], '2026-10-09T10:05:00+09:00',
                          now=clock('2026-10-09T10:06:00+09:00'))
        basis_quote = '基本ケースの会社全体の非営業資産額は20円です。'
        reply = {'id': 'synthetic-reply-nonoperating-assets', 'question_id': question['id'],
            'received_at': '2026-10-09T16:00:00+09:00', 'information_status': 'public_clarification',
            'raw_text': '架空の公開資料の補足です。' + basis_quote +
                '非支配持分額は10円から変更していません。これは合成テスト専用であり、実企業の回答・金額・将来CFの保証ではありません。'}
        harness.add_reply(reply, now=clock('2026-10-09T16:00:00+09:00'))
        fresh_source = deepcopy(value['sources'][1])
        fresh_source.update(id='synthetic-equity-bridge-reply-price',
            title='Synthetic fresh comparison price', retrieved_at='2026-10-09T16:59:00+09:00')
        fresh_source['metadata'].update(price_jpy='1600', observed_at='2026-10-09T16:59:00+09:00', synthetic=True)
        fresh_source = validate_source(fresh_source)
        harness.ingest({'schema_version': 1, 'sources': [fresh_source]},
                       now=clock('2026-10-09T16:59:00+09:00'))
        quote = deepcopy(value['quote'])
        quote.update(source_id=fresh_source['id'], price_jpy='1600',
                     observed_at=fresh_source['retrieved_at'], retrieved_at=fresh_source['retrieved_at'])
        rationale = '架空公開補足の20円という原文を、質問前に固定したassets_confirmed_20枝へ対応させる。基本ケースの非営業資産10→20だけを適用し、非支配持分・FCFF・割引率・成長率・株数は維持する。'
        evaluation = {'reply_id': reply['id'], 'branch_id': first['id'], 'basis_quote': basis_quote,
            'rationale': rationale, 'recorded_at': '2026-10-09T17:00:00+09:00',
            'expected_thesis_version': 1, 'next_review_date': '2026-10-30', 'decision_quote': quote}
        applied = harness.evaluate_reply(evaluation, now=clock('2026-10-09T17:00:00+09:00'))
        assert applied['applied'] is True and applied['action'] == 'exit_review'
        thesis = store.thesis(company_id)
        assert thesis['version'] == 2
        after = _flatten(thesis['valuation'])
        changes = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
        target = 'scenarios.base.inputs.non_operating_assets_jpy'
        assert changes == [target] and before[target] == Decimal('10') and after[target] == Decimal('20')
        assert all(scenario['method'] == METHOD for scenario in thesis['valuation']['scenarios'])
        assert all(value == after[path] for path, value in before.items() if path != target)
        assert store.connection.execute('SELECT data FROM theses WHERE company_id=? AND version=1', (company_id,)).fetchone()['data'] == old_thesis
        assert store.connection.execute('SELECT data FROM questions WHERE id=?', (question['id'],)).fetchone()['data'] == old_question
        assert store.reply(reply['id'])['raw_text'] == reply['raw_text']
        review = store.decision_review(applied['decision_review_id'])
        assert review['thesis_version'] == 2 and review['policy_version'] == 1
        assert review['result']['policy_snapshot'] == saved_question['decision_contract']['policy_snapshot']
        assert review['result']['quote'] == quote
        assert review['result']['proposed_action'] == 'exit_review'
        assert review['result']['reason_codes'] == ['valuation_target_reached']
        assert review['source_sha256'][fresh_source['id']] == sha256(json_text(fresh_source).encode()).hexdigest()
        assert review['result']['quote']['source_id'] == fresh_source['id']
        base_before = next(s for s in json.loads(old_thesis)['valuation']['scenarios'] if s['name'] == 'base')
        base_after = next(s for s in thesis['valuation']['scenarios'] if s['name'] == 'base')
        report = {'synthetic': True, 'executed_at': datetime.now(timezone.utc).isoformat(),
            'database': ':memory:', 'external_send_performed': False, 'orders': 0, 'HTTP_requests': 0,
            'fictional_mark_sent_only': True,
            'workflow': 'Synthetic frozen asset-amount question -> fictional sent-state -> synthetic public clarification -> fresh fictional price -> atomic reply application and saved review.',
            'question_id': question['id'], 'reply_id': reply['id'], 'reply_raw_text': reply['raw_text'],
            'basis_quote': basis_quote, 'rationale': rationale,
            'allowed_parameter_paths': saved_question['parameter_paths'], 'actual_parameter_changes': changes,
            'base_non_operating_assets_before_jpy': base_before['inputs']['non_operating_assets_jpy'],
            'base_non_operating_assets_after_jpy': base_after['inputs']['non_operating_assets_jpy'],
            'base_minority_interests_before_jpy': base_before['inputs']['minority_interests_jpy'],
            'base_minority_interests_after_jpy': base_after['inputs']['minority_interests_jpy'],
            'all_other_canonical_inputs_unchanged': True,
            'applied': applied['applied'], 'action': applied['action'], 'new_thesis_version': thesis['version'],
            'old_thesis_version_unchanged': True, 'old_question_data_unchanged': True, 'raw_reply_unchanged': True,
            'saved_decision_review_id': review['id'], 'saved_review_thesis_version': review['thesis_version'],
            'saved_review_policy_id': review['policy_id'], 'saved_review_policy_version': review['policy_version'],
            'saved_review_quote_source_id': review['result']['quote']['source_id'],
            'saved_review_quote_price_jpy': review['result']['quote']['price_jpy'],
            'saved_review_reasons': review['result']['reason_codes'],
            'frozen_policy_snapshot_matches_saved_review': True,
            'fictional_runtime_clocks': {'ingest_and_policy_saved': '2026-10-09T10:00:00+09:00',
                'question_saved': '2026-10-09T10:01:00+09:00', 'sent_at': '2026-10-09T10:05:00+09:00',
                'reply_received_and_saved': reply['received_at'], 'quote_saved': quote['retrieved_at'],
                'reply_evaluated': evaluation['recorded_at']},
            'actual_company_financial_inputs_adopted': False, 'actual_investment_policy_adopted': False,
            'scope': 'Software integration demonstration only. No accounting-meaning, forecast, IR efficacy or actual-company investment validation.'}
    finally:
        store.close()
    output = Path(__file__).with_name('synthetic-workflow-result.json')
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
