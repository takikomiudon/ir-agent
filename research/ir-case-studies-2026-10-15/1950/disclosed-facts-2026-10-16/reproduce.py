"""Finite same-now source-bound replay; no Store, DB or network."""
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
request = json.loads((HERE / 'normalization-input.json').read_bytes())
saved = json.loads((HERE / 'normalized-bundle.json').read_bytes())
generation = json.loads((HERE / 'generation.log').read_bytes())
assert sha256((ROOT / 'src/ir_agent/disclosed_facts.py').read_bytes()).hexdigest() == generation['normalizer_code_sha256']
before = deepcopy(request)
original, derived = saved['sources']
assert original == request['source']
assert saved['companies'] == saved['theses'] == []
assert normalize_disclosed_facts(request, now=derived['retrieved_at']) == saved
assert request == before
result = reproduce_disclosed_fact_source(derived, {original['id']: original})
assert result['status'] == 'reproduced'
assert result['original_content_sha256_status'] == 'matched'
assert result['original_snapshot_sha256_status'] == 'matched_supplied_snapshot'
assert derived['metadata']['normalization_version'] == 1
facts = json.loads(derived['content'])['facts']
assert len(facts) == 9
expected = ['34971000000', '1081000000', '1443000000', '242310000000', '23890000000',
            '18470000000', '24.73', '316.42', '127.00']
assert [fact['value'] for fact in facts] == expected
checks = []
for i, (declared, fact) in enumerate(zip(request['facts'], facts)):
    assert all(fact[key] == value for key, value in declared.items())
    assert 'raw_value_format' not in fact  # Ordinary decimal tokens, no composite opt-in.
    assert fact['normalization']['raw_numeric_token_verified'] is True
    assert fact['financial_inputs_verified'] is False and fact['meaning_review_required'] is True
    assert fact['scope']['financial_meaning_adopted'] is False
    assert fact['scope']['model_or_policy_adopted'] is False
    multiplier = Decimal('1000000') if i < 6 else Decimal('1')
    assert Decimal(fact['raw_value'].replace(',', '')) * multiplier == Decimal(fact['value'])
    loc = fact['location']; content = original['content']
    assert content[loc['source_character_start']:loc['source_character_end']] == fact['basis_quote']
    assert content[loc['raw_token_source_character_start']:loc['raw_token_source_character_end']] == fact['raw_value']
    assert content.encode()[loc['raw_token_UTF8_byte_start']:loc['raw_token_UTF8_byte_end']].decode() == fact['raw_value']
    assert fact['basis_quote'] in content.split('\f')[0]
    assert sha256((ROOT / loc['image_file']).read_bytes()).hexdigest() == loc['image_sha256']
    checks.append({'id': fact['id'], 'kind': fact['kind'], 'raw_value': fact['raw_value'],
                   'value': fact['value'], 'unit': fact['unit'], 'same_declaration_fields': True,
                   'explicit_unit_conversion_exact': True, 'quote_and_token_offsets_exact': True,
                   'value_path': 'facts.' + str(i) + '.value'})
assert facts[-1]['period']['start_date'] is facts[-1]['period']['end_date'] is None
assert facts[-1]['period']['dividend_record_date'] is None
assert facts[-1]['scope']['accounting_basis'] is facts[-1]['scope']['consolidation_scope'] is None
assert facts[-1]['location']['column'] == '年間配当金・合計'
assert all(fact['scope']['previous_forecast_announcement_date'] is None for fact in facts if fact['kind'] == 'issuer_guidance')
assert original['published_at'] is derived['published_at'] is None
assert original['metadata']['publication_date'] == '2026-07-31'
assert original['retrieved_at'] == '2026-10-16T03:08:13.157646+00:00'
assert derived['retrieved_at'] == generation['generation_now']
ref = json.loads((HERE / 'source-reference.json').read_bytes())
assert all(sha256((ROOT / path).read_bytes()).hexdigest() == wanted for path, wanted in ref['old_input_pins'].items())
print(json.dumps({'status': 'reproduced_nine_direct_display_tokens_file_only',
                  'reproduction': result, 'same_now_whole_bundle_and_ID_exact': True,
                  'original_whole_object_unchanged': True, 'request_unchanged': True,
                  'version1_ordinary_decimal_tokens_only': True, 'per_fact_checks': checks,
                  'DPS_FY_and_record_dates_accounting_and_consolidation_null': True,
                  'DPS_annual_total_column_not_final_column': True,
                  'previous_forecast_date_not_invented': True,
                  'original_publication_day_and_null_clock_preserved': True,
                  'old_file_pins_unchanged': True, 'derived_retrieved_at': derived['retrieved_at'],
                  'actual_original_or_derived_firstsave_queried_or_changed': False,
                  'explicit_same_now_normalizer_replay_calls': 1, 'existing_reproducer_calls': 1,
                  'reproducer_internal_reconstruction_separate_from_primary_generation': True,
                  'DB_connections': 0, 'GETs': 0, 'financial_inputs_adopted': 0}, ensure_ascii=False, indent=2))
