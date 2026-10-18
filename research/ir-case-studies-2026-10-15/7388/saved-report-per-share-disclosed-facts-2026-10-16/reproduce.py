#!/usr/bin/env python3
"""Read-only reproduction using the pinned existing disclosure normalizer."""
import hashlib
import json
from pathlib import Path
import sys

artifact = Path(__file__).resolve().parent
repo = next(parent for parent in artifact.parents if (parent / 'src/ir_agent').is_dir() and (parent / 'pyproject.toml').is_file())
manifest = json.loads((artifact / 'manifest.json').read_text(encoding='utf-8'))
def digest(data):
    return hashlib.sha256(data).hexdigest()
for path, expected in manifest['input_pins'].items():
    assert digest((repo / path).read_bytes()) == expected, path
for name, expected in manifest['files'].items():
    assert digest((artifact / name).read_bytes()) == expected, name
sys.path.insert(0, str(repo / 'src'))
from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source
from ir_agent.models import json_text
request = json.loads((artifact / 'normalization-input.json').read_text(encoding='utf-8'))
saved = json.loads((artifact / 'normalized-bundle.json').read_text(encoding='utf-8'))
result = normalize_disclosed_facts(request, now=manifest['normalization_now'])
assert result == saved
expected_bytes = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
assert expected_bytes == (artifact / 'normalized-bundle.json').read_bytes()
assert result['sources'][0] == request['source']
assert digest(json_text(result['sources'][0]).encode('utf-8')) == manifest['original_source_native_sha256']
derived = result['sources'][1]
assert digest(json_text(derived).encode('utf-8')) == manifest['derived_source_native_sha256']
facts = json.loads(derived['content'])['facts']
assert len(facts) == 2
assert [(f['concept'], f['value']) for f in facts] == [('reported_annual_earnings_per_share', '88.79'), ('reported_book_value_per_share', '508.60')]
for fact in facts:
    assert fact['kind'] == 'reported_fact' and fact['unit'] == 'JPY-per-share'
    assert fact['period']['start_date'] is None and fact['period']['end_date'] is None
    for field in ('accounting_basis', 'consolidation_scope', 'basic_or_diluted', 'ordinary_share_attribution', 'ordinary_profit_or_equity_attribution', 'share_class_of_denominator', 'EPS_annual_average_share_denominator', 'BPS_period_end_share_denominator', 'common_equity_OCI_NCI_preferred_treasury_mapping'):
        assert fact['scope'][field] is None, field
    assert fact['financial_inputs_verified'] is False
    assert fact['scope']['Graham_input_fit_certified'] is False
    quote = fact['basis_quote']
    loc = fact['location']
    assert request['source']['content'][loc['source_character_start']:loc['source_character_end']] == quote
    assert request['source']['content'][loc['raw_token_source_character_start']:loc['raw_token_source_character_end']] == fact['raw_value']
checks = reproduce_disclosed_fact_source(derived, {request['source']['id']: request['source']})
assert checks['status'] == 'reproduced' and checks['reason_codes'] == []
for path, expected in manifest['input_pins'].items():
    assert digest((repo / path).read_bytes()) == expected, path
print(json.dumps({'status': 'reproduced', 'fact_count': len(facts), 'derived_source_id': derived['id'], 'original_whole_preserved': True, 'period_day_endpoints_null': True, 'unknown_bases_preserved': True, 'financial_inputs_verified': False, 'DB_connections': 0, 'GET': 0, 'valuation_or_reference_calculated': False}, ensure_ascii=False, indent=2))
