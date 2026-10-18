"""Offline same-now replay and twelve direct issuer-display checks; no DB/network."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def load(path):
    return json.loads(path.read_bytes())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


request = load(HERE / 'normalization-input.json')
saved = load(HERE / 'normalized-bundle.json')
generation = load(HERE / 'generation.log')
ref = load(HERE / 'source-reference.json')
assert not (HERE / 'reproduction.json').exists()
assert digest(ROOT / 'src/ir_agent/disclosed_facts.py') == generation['normalizer_code_sha256']
before = deepcopy(request)
original, derived = saved['sources']
assert original == request['source']
assert original == load(ROOT / ref['source_bundle']['path'])['sources'][2]
assert saved['companies'] == saved['theses'] == []
assert normalize_disclosed_facts(request, now=derived['retrieved_at']) == saved
assert request == before
reproduction = reproduce_disclosed_fact_source(derived, {original['id']: original})
assert reproduction['status'] == 'reproduced'
assert reproduction['original_content_sha256_status'] == 'matched'
assert reproduction['original_snapshot_sha256_status'] == 'matched_supplied_snapshot'
assert derived['metadata']['normalization_version'] == 1
facts = json.loads(derived['content'])['facts']
expected = ['4693842000', '111568000', '-12167000', '-126493000', '-0.75', '199000000',
            '6166000000', '107000000', '107000000', '91000000', '0.66', '0']
assert len(facts) == 12 and [f['value'] for f in facts] == expected
content = original['content']; raw_bytes = content.encode('utf-8')
assert sha256(raw_bytes).hexdigest() == ref['original_content_sha256']
assert sha256(json.dumps(original, ensure_ascii=False, sort_keys=True).encode()).hexdigest() == ref['original_native_snapshot_sha256']
checks = []
for i, (declared, fact) in enumerate(zip(request['facts'], facts)):
    assert all(fact[k] == v for k, v in declared.items())
    assert 'raw_value_format' not in fact
    assert fact['normalization']['raw_numeric_token_verified'] is True
    assert fact['financial_inputs_verified'] is False and fact['meaning_review_required'] is True
    scope = fact['scope']; loc = fact['location']
    assert scope['model_or_policy_adopted'] is False
    assert scope['October_current_guidance_or_share_basis_verified'] is False
    multiplier = Decimal('1000') if i < 4 else Decimal('1000000') if i in (5, 6, 7, 8, 9) else Decimal('1')
    assert Decimal(fact['raw_value'].replace(',', '').replace('△', '-').replace('▲', '-')) * multiplier == Decimal(fact['value'])
    assert content[loc['source_character_start']:loc['source_character_end']] == fact['basis_quote']
    assert raw_bytes[loc['source_UTF8_byte_start']:loc['source_UTF8_byte_end']].decode() == fact['basis_quote']
    assert content[loc['raw_token_source_character_start']:loc['raw_token_source_character_end']] == fact['raw_value']
    assert raw_bytes[loc['raw_token_UTF8_byte_start']:loc['raw_token_UTF8_byte_end']].decode() == fact['raw_value']
    assert loc['source_UTF8_byte_start'] == len(content[:loc['source_character_start']].encode())
    assert loc['raw_token_UTF8_byte_start'] == len(content[:loc['raw_token_source_character_start']].encode())
    assert fact['basis_quote'] in content.split('\f')[loc['pdf_page'] - 1]
    assert digest(ROOT / loc['image_file']) == loc['image_sha256']
    context_checks = []
    for key, context in scope['source_context_references'].items():
        assert 'basis_quote' not in context and digest(ROOT / context['path']) == context['file_sha256']
        document = load(ROOT / context['path'])
        context_quotes = document if isinstance(document, list) else document['quotes']
        quote = next(q for q in context_quotes if q['id'] == context['quote_id'])
        assert key == quote['id'] and context['source_id'] == original['id']
        assert context['source_snapshot_sha256'] == ref['original_native_snapshot_sha256']
        assert content[context['character_start']:context['character_end']] == quote['quote']
        assert raw_bytes[context['UTF8_byte_start']:context['UTF8_byte_end']].decode() == quote['quote']
        assert quote.get('pdf_physical_page', quote.get('physical_pdf_page')) == context['pdf_page']
        context_checks.append(key)
    checks.append({'id': fact['id'], 'kind': fact['kind'], 'raw_value': fact['raw_value'],
                   'value': fact['value'], 'unit': fact['unit'],
                   'unit_multiplier': str(multiplier), 'same_declaration_fields': True,
                   'explicit_unit_conversion_exact': True,
                   'Unicode_UTF8_quote_and_token_offsets_exact': True,
                   'context_reference_offsets_and_file_pins_exact': context_checks})

for fact in facts[:4]:
    assert fact['raw_unit_label'] == '千円' and fact['location']['pdf_page'] == 13
    assert fact['location']['column'] == '当第３四半期連結累計期間'
for i in range(11):
    assert facts[i]['period']['start_date'] == '2025-11-01'
    assert facts[i]['period']['end_date'] == ('2026-07-31' if i < 6 else '2026-10-31')
    assert facts[i]['scope']['accounting_basis'] == 'Japanese_GAAP'
    assert facts[i]['scope']['consolidation_scope'] == '連結'
for fact in facts:
    assert fact['scope']['special_item_netting_or_addbacks_applied'] is False
    assert fact['scope']['normal_profit_future_cash_tax_or_CF_adopted'] is False
    assert fact['scope']['current_share_or_forecast_EPS_denominator_verified'] is False
for fact in facts[6:11]:
    assert fact['kind'] == 'issuer_guidance'
    assert fact['period']['previous_forecast_announcement_date'] == '2025-12-19'
    assert fact['scope']['previous_Dec19_original_body_read'] is False
# Same display107 occurs in different OP and ordinary columns, with distinct spans.
assert facts[7]['raw_value'] == facts[8]['raw_value'] == '107'
assert facts[7]['location']['column'] == '営業利益'
assert facts[8]['location']['column'] == '経常利益'
assert facts[7]['location']['raw_token_source_character_start'] != facts[8]['location']['raw_token_source_character_start']
metric = facts[5]
assert metric['concept'] == 'issuer_defined_adjusted_ebitda'
assert metric['scope']['issuer_definition_literal'] == '調整後EBITDA＝営業利益＋減価償却費＋のれん償却費'
assert metric['scope']['company_nonGAAP_supplement'] is True
assert metric['scope']['standardized_EBITDA_or_cross_company_comparability'] is False
assert metric['scope']['EBITDA_independently_recomputed'] is False
assert metric['scope']['not_CFO_FCFF_or_normal_profit'] is True
assert metric['kind'] == 'reported_fact' and metric['raw_value'] == '199'
dps = facts[11]
assert dps['concept'] == 'reported_interim_dividend_per_share' and dps['kind'] == 'reported_fact'
assert dps['raw_value'] == '0.00' and dps['value'] == '0'
assert dps['location']['row'] == '2026年10月期' and dps['location']['column'] == '第２四半期末'
assert dps['period']['start_date'] is dps['period']['end_date'] is None
assert dps['period']['dividend_record_date'] is None
assert dps['scope']['accounting_basis'] is dps['scope']['consolidation_scope'] is None
assert dps['scope']['cash_payment_confirmation'] is False
assert dps['scope']['final_or_annual_forecast_undetermined_dash_not_zero_filled'] is True
assert not any('annual_dividend' in f['concept'] or 'final_dividend' in f['concept'] for f in facts)
assert all(f['raw_value'] not in ['207,825', '207,719'] for f in facts)
rows = load(ROOT / ref['signed_PL_rows_file']['path'])['rows']
assert len(rows) == 33
for row in rows:
    assert content[row['global_native_unicode_start']:row['global_native_unicode_end_exclusive']] == row['quote']
    assert raw_bytes[row['global_native_utf8_start']:row['global_native_utf8_end_exclusive']].decode() == row['quote']
assert original['published_at'] is derived['published_at'] is None
assert original['metadata']['publication_date'] == '2026-09-14'
assert original['retrieved_at'] == ref['original_retrieved_at']
assert derived['retrieved_at'] == generation['generation_now']
assert all(digest(ROOT / path) == wanted for path, wanted in ref['old_input_pins'].items())
report = {'status': 'reproduced_twelve_direct_display_tokens_file_only',
          'completed_at': datetime.now(timezone.utc).isoformat(), 'reproduction': reproduction,
          'same_now_whole_bundle_and_ID_exact': True, 'original_whole_object_unchanged': True,
          'request_unchanged': True, 'normalization_version': 1, 'fact_count': 12,
          'per_fact_checks': checks, 'current_PL_thousand_precision_not_cover_million': True,
          'positive_OP_issuer_EBITDA_negative_ordinary_parent_and_EPS_separate': True,
          'issuer_EBITDA_dedicated_nonGAAP_concept_no_rebuild_or_CF_adoption': True,
          'FY_OP107_and_ordinary107_are_distinct_column_tokens': True,
          'interim_DPS0_display_not_payment_final_or_annual_forecast': True,
          'DPS_dates_record_accounting_consolidation_null': True,
          'context_reference_bindings_verified': sum(len(f['scope']['source_context_references']) for f in facts),
          'accepted_signed_PL_row_source_spans_verified': len(rows),
          'special_items_tax_NCI_context_only_not_netted_reallocated_or_normalized': True,
          'original_publication_day_null_clock_and_retrieval_preserved': True,
          'old_file_pins_unchanged': len(ref['old_input_pins']),
          'derived_retrieved_at': derived['retrieved_at'],
          'actual_DB_firstsave_queried_or_inferred': False,
          'explicit_same_now_normalizer_replay_calls': 3, 'existing_reproducer_calls': 3,
          'successful_full_validation_runs': 1, 'preceding_context_walker_failures': 2,
          'retry_reason': 'Legacy and note quote container/page-key schemas differ; data/normalizer values unchanged',
          'reproducer_internal_reconstruction_separate_from_primary_generation': True,
          'DB_connections': 0, 'GETs': 0, 'financial_inputs_adopted': 0}
with (HERE / 'reproduction.json').open('x', encoding='utf-8') as output:
    output.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
