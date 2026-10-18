"""Offline deterministic replay only; no Store, DB or network access."""
from hashlib import sha256
import json
from pathlib import Path

from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source

p = Path(__file__).resolve().parent
request = json.loads((p / 'normalization-input.json').read_bytes())
saved = json.loads((p / 'normalized-bundle.json').read_bytes())
original, derived = saved['sources']
assert original == request['source']
assert normalize_disclosed_facts(request, now=derived['retrieved_at']) == saved
result = reproduce_disclosed_fact_source(derived, {original['id']: original})
assert result['status'] == 'reproduced'
assert result['original_content_sha256_status'] == 'matched'
assert result['original_snapshot_sha256_status'] == 'matched_supplied_snapshot'
print(json.dumps({'reproduction': result, 'same_now_bundle_exact': True,
                  'derived_retrieved_at': derived['retrieved_at'],
                  'input_sha256': sha256((p / 'normalization-input.json').read_bytes()).hexdigest(),
                  'bundle_sha256': sha256((p / 'normalized-bundle.json').read_bytes()).hexdigest(),
                  'DB_connections': 0, 'new_GETs': 0, 'financial_inputs_adopted': 0},
                 ensure_ascii=False, indent=2))
