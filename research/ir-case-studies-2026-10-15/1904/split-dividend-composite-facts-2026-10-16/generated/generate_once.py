"""One offline primary generation; refuse overwriting or automatic retry."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import traceback

from ir_agent.disclosed_facts import normalize_disclosed_facts

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
CODE = ROOT / 'src/ir_agent/disclosed_facts.py'
EXPECTED_CODE = 'd434b41cfa19568d0cef1a2e6710365f447012d75a4b07ca950cc62b6bd9db51'


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def differences(old, new, prefix=''):
    if isinstance(old, dict) and isinstance(new, dict):
        result = []
        for key in sorted(old.keys() | new.keys()):
            path = prefix + '/' + key
            if key not in new:
                result.append({'path': path, 'operation': 'remove', 'old': old[key]})
            elif key not in old:
                result.append({'path': path, 'operation': 'add', 'new': new[key]})
            else:
                result += differences(old[key], new[key], path)
        return result
    if isinstance(old, list) and isinstance(new, list) and len(old) == len(new):
        return [item for i, (a, b) in enumerate(zip(old, new))
                for item in differences(a, b, prefix + '/' + str(i))]
    return [] if old == new else [{'path': prefix, 'operation': 'replace', 'old': old, 'new': new}]


if __name__ == '__main__':
    assert sha(CODE) == EXPECTED_CODE
    assert not any((HERE / name).exists() for name in
                   ('generation-request.json', 'normalized-bundle.json', 'generation.log', 'generation-error.json'))
    previous = json.loads((HERE.parent / 'normalization-input.json').read_bytes())
    acceptance = ROOT / 'research/ir-yen-sen-normalization-integration-2026-10-16/parent-acceptance.json'
    input_acceptance = HERE.parent / 'parent-input-acceptance.json'
    assert json.loads(acceptance.read_bytes())['status'] == 'accepted_explicit_yen_sen_normalization'
    assert json.loads(input_acceptance.read_bytes())['input_sha256'] == sha(HERE.parent / 'normalization-input.json')
    pins = {str(p.relative_to(ROOT)): sha(p) for p in HERE.parent.iterdir() if p.is_file()}
    pins.update(json.loads((HERE.parent / 'input-validation.json').read_bytes())['immutable_existing_files_pins'])
    pins[str(acceptance.relative_to(ROOT))] = sha(acceptance)
    request = deepcopy(previous)
    for fact in request['facts']:
        assert fact['scope'].pop('normalization_performed') is False
    request['review'] = {
        'author': 'Codex offline extraction reviewer; issuer 大成温調株式会社 authored the forecasts and annual comparative reference',
        'recorded_at': datetime.now(timezone.utc).isoformat(),
        'rationale': 'Generate three source-bound yen/sen displays after accepted parser implementation and accepted input semantics. Preserve interim pre-split, final post-split and issuer annual pre-split comparative reference as distinct declarations. Exact display composition only; no annual addition, split adjustment, payment/execution certification, current forecast recognition, DDM/valuation/thesis or financial-model adoption.',
    }
    diff = differences(previous, request)
    expected = {f'/facts/{i}/scope/normalization_performed' for i in range(3)} | {
        '/review/author', '/review/recorded_at', '/review/rationale'}
    assert {item['path'] for item in diff} == expected
    assert request['source'] == previous['source']
    assert all(sha(ROOT / path) == expected_sha for path, expected_sha in pins.items())
    save('generation-request.json', request)
    now = datetime.now(timezone.utc).isoformat()
    try:
        bundle = normalize_disclosed_facts(request, now=now)  # Sole primary generation call.
        assert bundle['sources'][0] == previous['source']
        assert request['source'] == previous['source']
        save('normalized-bundle.json', bundle)
        assert all(sha(ROOT / path) == expected_sha for path, expected_sha in pins.items())
        receipt = {
            'status': 'generated_file_only_pending_parent_review',
            'command': '.venv/bin/python ' + str(Path(__file__).relative_to(ROOT)),
            'primary_normalizer_calls': 1, 'generation_now': now,
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'normalizer_code_sha256': EXPECTED_CODE,
            'preparation_to_generation_request_diff': diff,
            'permitted_difference_groups_only': ['preparation_process_state_removal', 'truthful_generation_review_update'],
            'immutable_existing_file_pins': pins, 'all_existing_pins_unchanged': True,
            'request_sha256': sha(HERE / 'generation-request.json'),
            'bundle_sha256': sha(HERE / 'normalized-bundle.json'),
            'original_source_id': bundle['sources'][0]['id'],
            'derived_source_id': bundle['sources'][1]['id'],
            'sources': len(bundle['sources']), 'DB_connections': 0, 'GETs': 0,
            'financial_adoptions': 0,
        }
        save('generation.log', receipt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
    except Exception:
        save('generation-error.json', {'recorded_at': datetime.now(timezone.utc).isoformat(),
                                      'traceback': traceback.format_exc(), 'automatic_retry': False})
        raise
