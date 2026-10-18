"""Reproduce a rejected token boundary, not financial extraction; no DB/network."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from ir_agent.disclosed_facts import normalize_disclosed_facts

p = Path(__file__).resolve().parent
probe = json.loads((p / 'unsupported-token-probe.json').read_bytes())
request = probe['request']
content = request['source']['content']
assert '24 円 75 銭' in content
assert '24.75' not in content
assert request['facts'][0]['raw_value'] == '24.75'
try:
    normalize_disclosed_facts(request, now=datetime.now(timezone.utc))
except ValueError as error:
    assert str(error) == 'fact.raw_value token is absent from its quote or is only part of a larger numeric token'
    print(json.dumps({'status': 'expected_token_absence_rejection', 'error': str(error),
                      'probe_file_sha256': sha256((p / 'unsupported-token-probe.json').read_bytes()).hexdigest(),
                      'original_content_sha256': sha256(content.encode()).hexdigest(),
                      'normalizer_calls': 1, 'normalized_facts_created': 0, 'derived_sources_created': 0,
                      'DB_connections': 0, 'new_GETs': 0, 'financial_inputs_adopted': 0},
                     ensure_ascii=False, indent=2))
else:
    raise AssertionError('Unexpected acceptance; stop and review the existing API boundary')
