"""Generate one compact-scope variant; exact old proof retained, no DB/network."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from ir_agent.disclosed_facts import normalize_disclosed_facts

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
CODE_SHA = 'd434b41cfa19568d0cef1a2e6710365f447012d75a4b07ca950cc62b6bd9db51'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    assert not (HERE / 'normalized-bundle.json').exists() and not (HERE / 'generation.log').exists()
    assert digest(ROOT / 'src/ir_agent/disclosed_facts.py') == CODE_SHA
    prior = load(HERE.parent / 'normalization-input.json')
    assert digest(HERE.parent / 'normalized-bundle.json') == '32078b72a0ee6c030684c84138bb61dfce978ba298601fe935395ffb338f9145'
    request = load(HERE / 'normalization-input.json')
    expected = deepcopy(prior)
    removals = 0
    for fact in expected['facts']:
        for quote_id, ref in fact['scope']['source_context_references'].items():
            text = ref.pop('basis_quote')
            quote = next(q for q in load(ROOT / ref['path']) if q['id'] == quote_id)
            assert digest(ROOT / ref['path']) == ref['file_sha256']
            assert quote['quote'] == text and quote['character_start'] == ref['character_start']
            assert quote['character_end'] == ref['character_end'] and quote['pdf_physical_page'] == ref['pdf_page']
            assert text == request['source']['content'][ref['character_start']:ref['character_end']]
            removals += 1
    assert removals == 27 and expected == request
    pins = dict(load(HERE.parent / 'source-reference.json')['old_input_pins'])
    pins.update({str(path.relative_to(ROOT)): digest(path) for path in HERE.parent.iterdir() if path.is_file()})
    assert all(digest(ROOT / path) == expected_sha for path, expected_sha in pins.items())
    now = datetime.now(timezone.utc).isoformat()
    bundle = normalize_disclosed_facts(request, now=now)  # One additional primary generation.
    assert bundle['sources'][0] == prior['source']
    save('normalized-bundle.json', bundle)
    assert all(digest(ROOT / path) == expected_sha for path, expected_sha in pins.items())
    save('generation.log', {'status': 'generated_context_reference_only_variant_file_only',
        'command': '.venv/bin/python ' + str(Path(__file__).relative_to(ROOT)),
        'additional_primary_generation_calls': 1, 'generation_now': now,
        'completed_at': datetime.now(timezone.utc).isoformat(), 'normalizer_code_sha256': CODE_SHA,
        'only_27_scope_context_quote_fields_removed': True, 'old_generation_and_all_other_fields_unchanged': True,
        'old_file_pins': pins, 'input_sha256': digest(HERE / 'normalization-input.json'),
        'bundle_sha256': digest(HERE / 'normalized-bundle.json'),
        'old_derived_source_id': load(HERE.parent / 'normalized-bundle.json')['sources'][1]['id'],
        'new_derived_source_id': bundle['sources'][1]['id'],
        'DB_connections': 0, 'GETs': 0, 'financial_inputs_adopted': 0})
    print((HERE / 'generation.log').read_bytes().decode())
