"""Finite offline replay; context references require manual semantic review."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
request = json.loads((HERE / 'normalization-input.json').read_bytes())
prior = json.loads((HERE.parent / 'normalization-input.json').read_bytes())
old_bundle = json.loads((HERE.parent / 'normalized-bundle.json').read_bytes())
saved = json.loads((HERE / 'normalized-bundle.json').read_bytes())
generation = json.loads((HERE / 'generation.log').read_bytes())
assert sha256((ROOT / 'src/ir_agent/disclosed_facts.py').read_bytes()).hexdigest() == generation['normalizer_code_sha256']
expected = deepcopy(prior)
for fact in expected['facts']:
    for ref in fact['scope']['source_context_references'].values():
        ref.pop('basis_quote')
assert request == expected
before = deepcopy(request)
original, derived = saved['sources']
assert original == prior['source'] == old_bundle['sources'][0]
assert normalize_disclosed_facts(request, now=derived['retrieved_at']) == saved
assert request == before
result = reproduce_disclosed_fact_source(derived, {original['id']: original})
assert result['status'] == 'reproduced'
assert result['original_content_sha256_status'] == 'matched'
assert result['original_snapshot_sha256_status'] == 'matched_supplied_snapshot'
assert derived['metadata']['normalization_version'] == 1
old_content = json.loads(old_bundle['sources'][1]['content'])
new_content = json.loads(derived['content'])
for fact in old_content['facts']:
    for ref in fact['scope']['source_context_references'].values():
        ref.pop('basis_quote')
assert old_content == new_content
assert [f['value'] for f in new_content['facts']] == ['34971000000', '1081000000', '1443000000', '242310000000',
    '23890000000', '18470000000', '24.73', '316.42', '127.00']
checks = []
for i, fact in enumerate(new_content['facts']):
    assert fact['basis_quote'] == prior['facts'][i]['basis_quote']
    assert fact['financial_inputs_verified'] is False and fact['meaning_review_required'] is True
    assert fact['scope']['model_or_policy_adopted'] is False
    for quote_id, ref in fact['scope']['source_context_references'].items():
        assert 'basis_quote' not in ref
        path = ROOT / ref['path']
        assert sha256(path.read_bytes()).hexdigest() == ref['file_sha256']
        quote = next(q for q in json.loads(path.read_bytes()) if q['id'] == quote_id)
        assert quote['quote'] == original['content'][ref['character_start']:ref['character_end']]
        assert quote['pdf_physical_page'] == ref['pdf_page']
    checks.append({'id': fact['id'], 'value': fact['value'], 'unit': fact['unit'],
        'value_path': 'facts.' + str(i) + '.value', 'main_basis_quote_unchanged': True,
        'all_scope_period_definition_location_unchanged_except_context_quote_omission': True,
        'referenced_context_quotes_exact_manual_evidence_check': True})
assert original['published_at'] is derived['published_at'] is None
assert original['retrieved_at'] == '2026-10-16T03:08:13.157646+00:00'
assert derived['retrieved_at'] == generation['generation_now']
assert all(sha256((ROOT / path).read_bytes()).hexdigest() == expected_sha
           for path, expected_sha in generation['old_file_pins'].items())
print(json.dumps({'status': 'reproduced_reference_only_variant_file_only', 'reproduction': result,
    'same_now_bundle_and_ID_exact': True, 'normalized_content_diff_exactly_27_context_quote_removals': True,
    'original_whole_object_and_all_metadata_unchanged': True, 'review_unchanged': request['review'] == prior['review'],
    'value_period_definition_main_quote_location_and_other_scope_unchanged': True,
    'source_reference_authentication_is_manual_not_normalizer_certification': True,
    'version1_not_parser_upgrade': True, 'per_fact_checks': checks, 'old_files_unchanged': True,
    'derived_retrieved_at': derived['retrieved_at'], 'same_now_explicit_normalizer_replays': 1,
    'existing_reproducer_calls': 1, 'reproducer_internal_reconstruction_separate_from_primary_generation': True,
    'new_derived_actual_firstsave': None, 'DB_connections': 0, 'GETs': 0, 'financial_inputs_adopted': 0},
    ensure_ascii=False, indent=2))
