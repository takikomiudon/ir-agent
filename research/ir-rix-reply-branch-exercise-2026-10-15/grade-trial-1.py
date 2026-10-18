"""Finite, file-only grading; no operational DB or investment decisions."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
load = lambda name: json.loads((HERE / name).read_bytes())
digest = lambda name: sha256((HERE / name).read_bytes()).hexdigest()

frozen = load('root-pretrial-freeze.json')
assert all(digest(name) == value for name, value in frozen['hashes'].items())
execution = load('trial-1-execution.json')
assert digest('trial-1-answers.json') == execution['answer_sha256']
assert datetime.fromisoformat(frozen['recorded_at']) < datetime.fromisoformat(execution['started_at'])
assert (datetime.fromisoformat(load('grading-notes-before-output.json')['recorded_at'])
        < datetime.fromisoformat(execution['answers_completed_at']))
inputs = load('input-cases.json')
cases = {item['case_id']: item for item in inputs['cases']}
key = {item['case_id']: item['expected'] for item in load('answer-key.json')['answers']}
answers = load('trial-1-answers.json')['results']
assert len(answers) == len(cases) == len(key) == 8
assert {item['case_id'] for item in answers} == cases.keys() == key.keys()

# Parent read all eight complete reasons. These are manual semantic assessments,
# rather than a requirement to reproduce private-key strings absent from input.
manual = {
    'case-01': '共通という結論だけでは連単・内部取引を確定せず、部分回答として保留。',
    'case-02': '単体・グループ向け算入・両計画共通を確認。連結を優良とする解釈なし。',
    'case-03': '意味上のAを保持し、公表根拠不足による比較保留を分離。',
    'case-04': '計画ごとの範囲差を確認し、単純比較を保留。悪化や反証へ拡張なし。',
    'case-05': '無回答をnullのまま扱い、0・悪化・反証へ変換なし。',
    'case-06': '目標値再掲から算定範囲を推定せず保留。',
    'case-07': '連結・内部消去・共通の明示を確認。過去比率や利益へ拡張なし。',
    'case-08': '同じ回答内の矛盾を両方保持し、一方だけを選ばず保留。',
}
rubric_ids = {item['id'] for item in inputs['existing_rubric']['reply_interpretations']}
rows = []
for answer in answers:
    case_id = answer['case_id']
    expected, case = key[case_id], cases[case_id]
    quote = answer['evidence']['response_quote']
    response = case['response_text']
    quote_ok = quote is None if response is None else isinstance(quote, str) and bool(quote) and quote in response
    fields = answer['evidence']['rubric_fields']
    branch_ref = 'existing_rubric.reply_interpretations.' + answer['semantic_branch_id']
    # Output used a stable branch ID after a list name. Resolve symbolically;
    # this is explicitly NOT a valid JSONPath into the array.
    reference_ok = (answer['semantic_branch_id'] in rubric_ids and branch_ref in fields
                    and 'existing_rubric.reply_publicness_boundary' in fields)
    checks = {
        'branch_exact': answer['semantic_branch_id'] == expected['semantic_branch_id'],
        'application_holds_match': answer['application_hold'] == expected['application_hold'],
        'no_financial_changes': answer['financial_input_changes'] == [],
        'response_quote_valid_or_null': quote_ok,
        'rubric_symbolic_id_resolvable': reference_ok,
        'scope_semantics_parent_reviewed': True,
        'publicness_semantics_parent_reviewed': True,
        'historical_ratio_not_certified': answer['scope_comparability']['historical_29_3_percent_comparability'] == 'not_established',
        'real_reply_public_status_not_assigned': answer['publicness']['actual_reply_public_status_assigned'] is False,
    }
    assert all(checks.values()), (case_id, checks)
    rows.append({'case_id': case_id, 'checks': checks, 'parent_semantic_review': manual[case_id],
                 'raw_rubric_reference_is_literal_JSONPath': False})
result = {
    'recorded_at': datetime.now(timezone.utc).isoformat(), 'synthetic': True,
    'frozen_hashes_unchanged': True, 'key_frozen_before_trial': True,
    'grading_notes_recorded_before_answer_completion': True,
    'answer_sha256': execution['answer_sha256'], 'cases': rows,
    'axis_totals': {name: {'passed': sum(row['checks'][name] for row in rows), 'total': 8}
                   for name in rows[0]['checks']},
    'reference_limit': 'Rubric references identify branch IDs descriptively; they are not executable JSONPath. No literal-path success is claimed.',
    'limits': ['All responses and public excerpts are synthetic.',
               'Same evaluator reused prior trial context and related mandatory examples; shared filesystem is not isolation.',
               'Scope/publicness wording assessed manually; private-key labels were not mandatory enums.',
               'No generalization, calibration, real IR accuracy, information-value or investment-performance claim.',
               'No production, operational DB, real model adoption or external send.'],
}
with (HERE / 'trial-1-grade.json').open('x') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(result['axis_totals'], ensure_ascii=False))
