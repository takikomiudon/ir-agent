"""Offline same-now replay and ten direct issuer-display checks; no DB/network."""
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
assert original == load(ROOT / ref['source_bundle']['path'])['sources'][1]
assert saved['companies'] == saved['theses'] == []
assert normalize_disclosed_facts(request, now=derived['retrieved_at']) == saved
assert request == before
reproduction = reproduce_disclosed_fact_source(derived, {original['id']: original})
assert reproduction['status'] == 'reproduced'
assert reproduction['original_content_sha256_status'] == 'matched'
assert reproduction['original_snapshot_sha256_status'] == 'matched_supplied_snapshot'
assert derived['metadata']['normalization_version'] == 1
facts = json.loads(derived['content'])['facts']
expected = ['7075025000', '1217085000', '815269000', '38.43', '14021000000',
            '2017000000', '1248000000', '58.85', '43.00', '21.50']
assert len(facts) == 10 and [f['value'] for f in facts] == expected
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
    assert scope['prior_consolidated_interim_comparison_available'] is False
    assert scope['prior_standalone_substitution_or_YoY_calculation'] is False
    multiplier = Decimal('1000') if i < 3 else Decimal('1000000') if i in (4, 5, 6) else Decimal('1')
    assert Decimal(fact['raw_value'].replace(',', '')) * multiplier == Decimal(fact['value'])
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
        quote = next(q for q in load(ROOT / context['path']) if q['id'] == context['quote_id'])
        assert key == quote['id'] and context['source_id'] == original['id']
        assert context['source_snapshot_sha256'] == ref['original_native_snapshot_sha256']
        assert content[context['character_start']:context['character_end']] == quote['quote']
        assert raw_bytes[context['UTF8_byte_start']:context['UTF8_byte_end']].decode() == quote['quote']
        assert quote['pdf_physical_page'] == context['pdf_page']
        context_checks.append(key)
    checks.append({'id': fact['id'], 'kind': fact['kind'], 'raw_value': fact['raw_value'],
                   'value': fact['value'], 'unit': fact['unit'],
                   'unit_multiplier': str(multiplier), 'same_declaration_fields': True,
                   'explicit_unit_conversion_exact': True,
                   'Unicode_UTF8_quote_and_token_offsets_exact': True,
                   'context_reference_offsets_and_file_pins_exact': context_checks})
for fact in facts[:3]:
    assert fact['raw_unit_label'] == '千円' and fact['location']['pdf_page'] == 6
for i in (3, 7):
    assert facts[i]['scope']['split_factor_applied_by_extractor'] is False
    assert facts[i]['scope']['share_denominator_adopted'] is False
for i in range(8):
    assert facts[i]['period']['start_date'] == '2026-02-01'
    assert facts[i]['period']['end_date'] == ('2026-07-31' if i < 4 else '2027-01-31')
    assert facts[i]['scope']['accounting_basis'] == 'Japanese_GAAP'
    assert facts[i]['scope']['consolidation_scope'] == '連結'
for fact in facts[4:8]:
    assert fact['kind'] == 'issuer_guidance'
    assert fact['period']['previous_forecast_announcement_date'] == '2026-03-13'
    assert fact['scope']['March13_original_body_independently_read'] is False
interim, final = facts[8:]
assert interim['concept'] == 'reported_interim_dividend_per_share'
assert final['concept'] == 'issuer_forecast_final_dividend_per_share'
assert interim['kind'] == 'reported_fact' and final['kind'] == 'issuer_guidance'
assert interim['scope']['share_basis'] == 'pre_split_interim_display'
assert final['scope']['share_basis'] == 'post_split_final_forecast_display'
assert interim['location']['column'] == '第2四半期末' and final['location']['column'] == '期末'
for fact in (interim, final):
    assert fact['period']['start_date'] is fact['period']['end_date'] is None
    assert fact['period']['dividend_record_date'] is None
    assert fact['scope']['accounting_basis'] is fact['scope']['consolidation_scope'] is None
    assert fact['scope']['split_factor_applied_by_extractor'] is False
    assert fact['scope']['annual_total_not_generated_or_computed'] is True
    assert fact['scope']['interim_final_not_added'] is True
    assert fact['scope']['cash_payment_confirmation'] is False
assert not any('annual_dividend' in fact['concept'] for fact in facts)
assert original['published_at'] is derived['published_at'] is None
assert original['metadata']['publication_date'] == '2026-09-10'
assert original['retrieved_at'] == ref['original_retrieved_at']
assert derived['retrieved_at'] == generation['generation_now']
assert all(digest(ROOT / path) == wanted for path, wanted in ref['old_input_pins'].items())
report = {'status': 'reproduced_ten_direct_display_tokens_file_only',
          'completed_at': datetime.now(timezone.utc).isoformat(), 'reproduction': reproduction,
          'same_now_whole_bundle_and_ID_exact': True, 'original_whole_object_unchanged': True,
          'request_unchanged': True, 'normalization_version': 1, 'fact_count': 10,
          'per_fact_checks': checks,
          'thousand_PL_not_replaced_by_cover_million_precision': True,
          'already_split_adjusted_EPS_not_adjusted_again': True,
          'two_DPS_concepts_kinds_columns_and_share_bases_separate': True,
          'DPS_dates_record_accounting_consolidation_null': True,
          'annual_DPS_dash_fact_sum_or_adjusted_value_not_generated': True,
          'context_reference_bindings_verified': sum(len(f['scope']['source_context_references']) for f in facts),
          'original_publication_day_null_clock_and_retrieval_preserved': True,
          'old_file_pins_unchanged': len(ref['old_input_pins']),
          'derived_retrieved_at': derived['retrieved_at'],
          'actual_DB_firstsave_queried_or_inferred': False,
          'explicit_same_now_normalizer_replay_calls': 1, 'existing_reproducer_calls': 1,
          'reproducer_internal_reconstruction_separate_from_primary_generation': True,
          'DB_connections': 0, 'GETs': 0, 'financial_inputs_adopted': 0}
with (HERE / 'reproduction.json').open('x', encoding='utf-8') as output:
    output.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
