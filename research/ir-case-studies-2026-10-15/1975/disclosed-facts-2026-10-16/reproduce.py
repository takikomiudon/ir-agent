"""Finite source-bound replay and explicit unit/offset checks; no DB or network."""
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


request = json.loads((HERE / 'normalization-input.json').read_bytes())
saved = json.loads((HERE / 'normalized-bundle.json').read_bytes())
generation = json.loads((HERE / 'generation.log').read_bytes())
ref = json.loads((HERE / 'source-reference.json').read_bytes())
assert digest(ROOT / 'src/ir_agent/disclosed_facts.py') == generation['normalizer_code_sha256']
before = deepcopy(request)
original, derived = saved['sources']
assert original == request['source']
assert original == json.loads((ROOT / ref['source_bundle']['path']).read_bytes())['sources'][1]
assert saved['companies'] == saved['theses'] == []
assert normalize_disclosed_facts(request, now=derived['retrieved_at']) == saved
assert request == before
result = reproduce_disclosed_fact_source(derived, {original['id']: original})
assert result['status'] == 'reproduced'
assert result['original_content_sha256_status'] == 'matched'
assert result['original_snapshot_sha256_status'] == 'matched_supplied_snapshot'
assert derived['metadata']['normalization_version'] == 1
facts = json.loads(derived['content'])['facts']
expected = ['19483000000', '2205000000', '1546000000', '112500000000', '12200000000',
            '9250000000', '59.78', '357.49', '144.00']
assert len(facts) == 9 and [f['value'] for f in facts] == expected
content = original['content']; content_bytes = content.encode('utf-8')
assert sha256(content_bytes).hexdigest() == ref['original_content_sha256']
assert sha256(json.dumps(original, ensure_ascii=False, sort_keys=True).encode()).hexdigest() == ref['original_native_snapshot_sha256']
checks = []
for i, (declared, fact) in enumerate(zip(request['facts'], facts)):
    assert all(fact[key] == value for key, value in declared.items())
    assert 'raw_value_format' not in fact
    assert fact['normalization']['raw_numeric_token_verified'] is True
    assert fact['financial_inputs_verified'] is False and fact['meaning_review_required'] is True
    assert fact['scope']['model_or_policy_adopted'] is False
    assert fact['scope']['October_current_guidance_or_share_basis_verified'] is False
    multiplier = Decimal('1000000') if i < 6 else Decimal('1')
    assert Decimal(fact['raw_value'].replace(',', '')) * multiplier == Decimal(fact['value'])
    loc = fact['location']
    assert content[loc['source_character_start']:loc['source_character_end']] == fact['basis_quote']
    assert content_bytes[loc['source_UTF8_byte_start']:loc['source_UTF8_byte_end']].decode() == fact['basis_quote']
    assert content[loc['raw_token_source_character_start']:loc['raw_token_source_character_end']] == fact['raw_value']
    assert content_bytes[loc['raw_token_UTF8_byte_start']:loc['raw_token_UTF8_byte_end']].decode() == fact['raw_value']
    assert loc['source_UTF8_byte_start'] == len(content[:loc['source_character_start']].encode())
    assert loc['raw_token_UTF8_byte_start'] == len(content[:loc['raw_token_source_character_start']].encode())
    assert fact['basis_quote'] in content.split('\f')[0]
    assert digest(ROOT / loc['image_file']) == loc['image_sha256']
    context_checks = []
    for key, context in fact['scope']['source_context_references'].items():
        assert 'basis_quote' not in context and digest(ROOT / context['path']) == context['file_sha256']
        document = json.loads((ROOT / context['path']).read_bytes())
        quotes = document
        quote = next(q for q in quotes if q['id'] == context['quote_id'])
        assert context['quote_id'] == key and context['source_id'] == original['id']
        assert context['source_snapshot_sha256'] == ref['original_native_snapshot_sha256']
        extracted = content[context['character_start']:context['character_end']]
        assert content_bytes[context['UTF8_byte_start']:context['UTF8_byte_end']].decode() == extracted
        assert extracted == quote['quote'] and quote['pdf_physical_page'] == context['pdf_page']
        context_checks.append(key)
    checks.append({'id': fact['id'], 'kind': fact['kind'], 'raw_value': fact['raw_value'],
                   'value': fact['value'], 'unit': fact['unit'], 'same_declaration_fields': True,
                   'explicit_unit_conversion_exact': True, 'Unicode_UTF8_quote_and_token_offsets_exact': True,
                   'context_reference_offsets_and_file_pins_exact': context_checks,
                   'value_path': 'facts.' + str(i) + '.value'})
dps = facts[-1]
assert dps['period']['start_date'] is dps['period']['end_date'] is None
assert dps['period']['dividend_record_date'] is None
assert dps['scope']['accounting_basis'] is dps['scope']['consolidation_scope'] is None
assert dps['location']['column'] == '年間配当金・合計'
assert dps['location']['row'] == '2027年３月期（予想）'
assert dps['location']['raw_token_source_character_start'] == 3330
assert dps['scope']['previous_forecast_announcement_date'] is None
assert dps['scope']['annual_total_not_computed'] is True
assert dps['scope']['investor_DDM_dividend_column_adopted'] is False
for fact in facts:
    if fact['kind'] == 'issuer_guidance' and fact is not dps:
        assert fact['scope']['previous_forecast_announcement_date'] == '2026-05-14'
        assert fact['period']['start_date'] == '2026-04-01' and fact['period']['end_date'] == '2027-03-31'
    if fact['kind'] == 'reported_fact':
        assert fact['period']['start_date'] == '2026-04-01' and fact['period']['end_date'] == '2026-06-30'
assert original['published_at'] is derived['published_at'] is None
assert original['metadata']['publication_date'] == '2026-08-04'
assert original['retrieved_at'] == '2026-10-16T04:18:59.234370+00:00'
assert derived['retrieved_at'] == generation['generation_now']
assert all(digest(ROOT / path) == wanted for path, wanted in ref['old_input_pins'].items())
print(json.dumps({'status': 'reproduced_nine_direct_display_tokens_file_only', 'reproduction': result,
                  'same_now_whole_bundle_and_ID_exact': True, 'original_whole_object_unchanged': True,
                  'request_unchanged': True, 'version1_ordinary_decimal_tokens_only': True,
                  'per_fact_checks': checks, 'DPS_FY_and_record_dates_accounting_and_consolidation_null': True,
                  'current_DPS_total_distinct_from_prior_total_interim_final': True,
                  'May14_earnings_reference_not_inherited_by_dividend': True,
                  'source_contexts_reference_only_not_repeated_text': True,
                  'original_publication_day_and_null_clock_preserved': True,
                  'old_file_pins_unchanged': len(ref['old_input_pins']),
                  'derived_retrieved_at': derived['retrieved_at'],
                  'actual_original_or_derived_firstsave_queried_or_changed': False,
                  'explicit_same_now_normalizer_replay_calls': 1, 'existing_reproducer_calls': 1,
                  'reproducer_internal_reconstruction_separate_from_primary_generation': True,
                  'DB_connections': 0, 'GETs': 0, 'financial_inputs_adopted': 0}, ensure_ascii=False, indent=2))
