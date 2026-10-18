"""Finite offline same-now replay and accepted-contract checks; no DB/network."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path

from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
request = json.loads((HERE / 'generation-request.json').read_bytes())
saved = json.loads((HERE / 'normalized-bundle.json').read_bytes())
generation = json.loads((HERE / 'generation.log').read_bytes())
assert sha256((ROOT / 'src/ir_agent/disclosed_facts.py').read_bytes()).hexdigest() == generation['normalizer_code_sha256']
before = deepcopy(request)
original, derived = saved['sources']
assert original == request['source']
assert saved['companies'] == saved['theses'] == []
assert derived['metadata']['normalization_version'] == 2
assert normalize_disclosed_facts(request, now=derived['retrieved_at']) == saved
assert request == before
reproduced = reproduce_disclosed_fact_source(derived, {original['id']: original})
assert reproduced['status'] == 'reproduced'
assert reproduced['original_content_sha256_status'] == 'matched'
assert reproduced['original_snapshot_sha256_status'] == 'matched_supplied_snapshot'
facts = json.loads(derived['content'])['facts']
assert [f['value'] for f in facts] == ['99.00', '24.75', '198.00']
checks = []
for declared, fact in zip(request['facts'], facts):
    assert all(fact[key] == value for key, value in declared.items())
    norm = fact['normalization']
    assert norm['status'] == 'composite_display_normalized'
    assert norm['raw_display_verified'] is True and norm['raw_numeric_token_verified'] is False
    assert fact['financial_inputs_verified'] is False and fact['meaning_review_required'] is True
    assert fact['scope']['financial_input_adoption'] is False
    assert 'normalization_performed' not in fact['scope']
    components = norm['components']
    for part in components.values():
        start, end = part['raw_value_span']
        assert fact['raw_value'][start:end] == part['raw_token']
    with localcontext() as ctx:
        ctx.prec = 80
        recomposed = (Decimal(components['yen']['raw_token'].replace(',', ''))
                      + Decimal(components['sen']['raw_token']) * Decimal('0.01')) * Decimal(components['sign']['multiplier'])
        assert recomposed == Decimal(fact['value'])
    loc = fact['location']; content = original['content']
    assert content[loc['source_character_start']:loc['source_character_end']] == fact['basis_quote']
    assert content[loc['raw_display_source_character_start']:loc['raw_display_source_character_end']] == fact['raw_value']
    assert content.encode()[loc['raw_display_UTF8_byte_start']:loc['raw_display_UTF8_byte_end']].decode() == fact['raw_value']
    assert fact['period']['start_date'] is fact['period']['end_date'] is None
    assert fact['scope']['accounting_basis'] is fact['scope']['consolidation_scope'] is None
    assert not fact['scope']['simple_annual_addition_permitted']
    assert not fact['scope']['investor_DDM_dividend_column_adopted']
    checks.append({'id': fact['id'], 'exact_declarations_retained': True,
                   'raw_value': fact['raw_value'], 'normalized_value': fact['value'],
                   'component_spans_recomputed_and_matched': True,
                   'Decimal_composition_matched': True, 'period_and_scope_nulls_retained': True})
assert [f['period']['dividend_record_date_as_explicitly_noted'] for f in facts] == ['2026-09-30', '2027-03-31', None]
assert original['published_at'] is derived['published_at'] is None
assert original['retrieved_at'] == '2026-10-16T02:03:26.069103+00:00'
assert original['metadata']['publication_date'] == '2026-09-10'
assert derived['retrieved_at'] == generation['generation_now']
assert all(sha256((ROOT / path).read_bytes()).hexdigest() == expected
           for path, expected in generation['immutable_existing_file_pins'].items())
report = {'status': 'reproduced_three_distinct_displays_file_only',
          'same_now_whole_bundle_and_ID_exact': True, 'original_whole_object_unchanged': True,
          'normalization_version': 2, 'reproduction': reproduced, 'per_fact_checks': checks,
          'request_not_mutated': True, 'existing_pins_unchanged': True,
          'derived_retrieved_at': derived['retrieved_at'],
          'original_publication_day_and_null_publication_clock_preserved': True,
          'known_by_and_firstsave': 'No DB connection or receipt mutation; existing receipt files pinned. Derived source is file-only with no actual firstsave/known-by receipt asserted.',
          'same_now_explicit_normalizer_replays_in_this_command': 1,
          'reproducer_calls_in_this_command': 1,
          'reproducer_may_internally_call_normalizer': True,
          'new_primary_generations_in_this_command': 0,
          'DB_connections': 0, 'GETs': 0, 'financial_inputs_adopted': 0}
print(json.dumps(report, ensure_ascii=False, indent=2))
