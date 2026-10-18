"""One file-only primary normalization of nine direct issuer tokens; no DB/network."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from ir_agent.disclosed_facts import normalize_disclosed_facts

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EXPECTED_CODE = 'd434b41cfa19568d0cef1a2e6710365f447012d75a4b07ca950cc62b6bd9db51'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    assert not (HERE / 'normalized-bundle.json').exists() and not (HERE / 'generation.log').exists()
    assert digest(ROOT / 'src/ir_agent/disclosed_facts.py') == EXPECTED_CODE
    parent = HERE.parent / 'initial-public-review-2026-10-16/parent-acceptance.json'
    accepted = json.loads(parent.read_bytes())
    assert accepted['status'].startswith('accepted_')
    request = json.loads((HERE / 'normalization-input.json').read_bytes())
    ref = json.loads((HERE / 'source-reference.json').read_bytes())
    assert all(digest(ROOT / path) == expected for path, expected in ref['old_input_pins'].items())
    source_before = json.dumps(request['source'], ensure_ascii=False, sort_keys=True)
    now = datetime.now(timezone.utc).isoformat()
    bundle = normalize_disclosed_facts(request, now=now)
    assert bundle['sources'][0] == request['source']
    assert json.dumps(request['source'], ensure_ascii=False, sort_keys=True) == source_before
    save('normalized-bundle.json', bundle)
    assert all(digest(ROOT / path) == expected for path, expected in ref['old_input_pins'].items())
    save('generation.log', {'status': 'primary_generation_succeeded_file_only',
                           'command': '.venv/bin/python ' + str(Path(__file__).relative_to(ROOT)),
                           'primary_normalizer_calls': 1, 'generation_now': now,
                           'completed_at': datetime.now(timezone.utc).isoformat(),
                           'normalizer_code_sha256': EXPECTED_CODE,
                           'request_sha256': digest(HERE / 'normalization-input.json'),
                           'bundle_sha256': digest(HERE / 'normalized-bundle.json'),
                           'original_parent_acceptance_sha256': digest(parent),
                           'original_source_id': bundle['sources'][0]['id'],
                           'derived_source_id': bundle['sources'][1]['id'],
                           'DB_connections': 0, 'GETs': 0, 'financial_inputs_adopted': 0})
    print((HERE / 'generation.log').read_bytes().decode())
