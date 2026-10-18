"""Binding-only probe on a backup of actual saved sources; no question creation."""
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import tempfile

from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.models import json_text
from ir_agent.store import Store

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED = '446078451a45181c76ae6e8dad01ce5483079e69d5f419b879500630d68f8591'


def load(path):
    return json.loads(path.read_bytes())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x', encoding='utf8') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    assert not (HERE / 'binding-check.json').exists()
    assert digest(DB) == EXPECTED
    sources = load(HERE.parent / 'public-explanation-followup-2026-10-16/source-quotes.json')
    qa = next(q for q in sources if q['id'] == 'public_qa-physical-2')
    notes = load(HERE.parent / 'statement-note-followup-2026-10-16/source-quotes.json')['quotes']
    note = next(q for q in notes if q['id'] == 'indonesia-period-and-method-change')
    selected = [
        (qa['source_id'], qa['quote'], '公開Q&A物理1–4を既読。8月7日時点の説明。引用はp2。'),
        (note['existing_source_id'], note['quote'], '短信の初回1/2/4/7と追加9–12を既読。引用はp10。全14頁の意味読了ではない。'),
    ]
    now = datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix='ir-1963-public-binding-', dir='/tmp') as directory:
        copied = Path(directory) / 'copy.sqlite3'
        with closing(sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)) as original:
            original.execute('PRAGMA query_only=ON')
            original.execute('BEGIN')
            before = tuple(original.iterdump())
            with closing(sqlite3.connect(copied)) as target:
                original.backup(target)
        store = Store(str(copied))
        try:
            assert tuple(store.connection.iterdump()) == before
            bindings = []
            for identity, quote, scope in selected:
                source = store.source(identity)
                assert quote in source['content']
                bindings.append({'source_id': identity,
                    'source_snapshot_sha256': sha256(json_text(source).encode()).hexdigest(),
                    'scope': scope, 'basis_quote': quote})
            # Deliberately lacks id, branches and valuation: this is not a
            # registerable question and does not assert public_answer_status.
            subject = {'company_id': 'jp:1963', 'created_at': now,
                'public_information_review': {'reviewed_at': now,
                    'reviewer': 'Codex root / real-source binding-only probe',
                    'rationale': '保存済み資料の参照を照合する。質問・投資仮説・未回答判定は生成しない。',
                    'sources': bindings}}
            check = DecisionLifecycle(store).review_public_information(subject, as_of=now, now=now)
            assert check['reason_codes'] == []
            assert len(check['availability_at_review']) == 2
            assert all(value['available'] is True for value in check['availability_at_review'].values())
            assert check['answer_absence_verified'] is False and check['meaning_review_required'] is True
            assert tuple(store.connection.iterdump()) == before
            save('binding-subject.json', subject)
            save('binding-check.json', check)
        finally:
            store.close()
    assert digest(DB) == EXPECTED
    save('validation.json', {'recorded_at': now, 'status': 'passed_real_source_binding_only',
        'actual_DB_SHA_before_and_after': EXPECTED, 'copy_rows_and_schema_unchanged': True,
        'actual_DB_connections': 'mode=ro/query_only/contextlib.closing',
        'Store_initialized_only_on_temporary_backup': True, 'bound_sources': 2,
        'new_questions_jobs_financial_inputs_or_sends': 0,
        'answer_absence_verified': False, 'meaning_or_IR_value_certified': False})
    print('passed_real_source_binding_only; actual DB unchanged; no question or financial decision')


if __name__ == '__main__':
    main()
