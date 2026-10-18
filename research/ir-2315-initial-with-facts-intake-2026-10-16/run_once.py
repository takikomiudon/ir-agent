"""Root-only staged execution after review; this preparation never runs it.

Use a fresh shadow and then actual only after inspecting successful receipts.
No automatic retry/resume; the pipeline is not one SQLite transaction.
"""
import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.models import json_text
from ir_agent.store import Store

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED = 'f61e892f68d4518e659899e00d0238b163b660d94f5399b8c37ae63f1b03ffca'
COMPANY = 'jp:2315'
DELTAS = {'sources': 6, 'record_availability': 6, 'source_classifications': 6,
          'jobs': 1, 'job_attempts': 1, 'job_attempt_events': 2, 'job_request_receipts': 1}
BASE_COUNTS = {'companies': 1819, 'sources': 195, 'source_classifications': 194, 'record_availability': 195,
               'jobs': 108, 'job_attempts': 105, 'job_attempt_events': 210,
               'job_request_receipts': 105, 'qualitative_case_versions': 44}
BASE_CASE_STATE = {'current_cases': 23, 'reviewed_sources': 134}
PREPARED = ('source-bundle.json', 'classification-requests.json', 'classification-evidence.json',
            'input-pins.json', 'prepared-code-pins.json', 'source-map.json')


def clock():
    return datetime.now(timezone.utc)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(path, value):
    with path.open('x', encoding='utf-8') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        output.flush(); os.fsync(output.fileno())


def readonly():
    connection = sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)
    connection.execute('PRAGMA query_only=ON')
    assert connection.execute('PRAGMA query_only').fetchone()[0] == 1
    return connection


def snapshot(connection):
    return {name: Counter(tuple(row) for row in connection.execute('SELECT * FROM "' + name.replace('"', '""') + '"'))
            for name, in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")}


def schema(connection):
    return [tuple(row) for row in connection.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name')]


def case_state(connection):
    heads = connection.execute('''SELECT a.data FROM qualitative_case_versions a JOIN
        (SELECT case_id,MAX(version) version FROM qualitative_case_versions GROUP BY case_id) b
        ON a.case_id=b.case_id AND a.version=b.version''').fetchall()
    return {'current_cases': len(heads), 'reviewed_sources': sum(len(json.loads(row[0])['reviewed_sources']) for row in heads)}


def main(stage, execution_code_file, execution_code_sha256):
    # Parent selects and hashes a reviewed current-code manifest. The initial
    # prepared-code-pins remains a historical observation if another task edits code.
    code_file = (ROOT / execution_code_file).resolve()
    assert ROOT / 'research' in code_file.parents
    assert digest(code_file) == execution_code_sha256
    code_pins = load(code_file)
    current_code_files = {str(path.relative_to(ROOT)) for path in (ROOT / 'src/ir_agent').rglob('*.py')}
    assert set(code_pins) == current_code_files
    assert all(digest(ROOT / path) == wanted for path, wanted in code_pins.items())
    journal_path = HERE / (stage + '-stage.jsonl')
    assert not any((HERE / name).exists() for name in (stage + '-stage.jsonl', stage + '-completion.json', stage + '-error.json'))
    assert digest(DB) == EXPECTED
    input_pins = load(HERE / 'input-pins.json')
    assert all(digest(ROOT / path) == wanted for path, wanted in input_pins.items())
    bundle = load(HERE / 'source-bundle.json')
    requests = load(HERE / 'classification-requests.json')
    sources = bundle['sources']
    assert len(sources) == len({s['id'] for s in sources}) == 6
    assert all(s['company_id'] == COMPANY for s in sources)
    assert bundle == {'schema_version': 1, 'companies': [], 'sources': sources, 'theses': []}
    assert set(requests) == {COMPANY}
    request = requests[COMPANY]
    assert {item['source_id'] for item in request['classifications']} == {source['id'] for source in sources}
    assert len(request['classifications']) == 6
    source_by_id = {source['id']: source for source in sources}
    assert all(item['expected_version'] == 0 and item['basis_quote'] in source_by_id[item['source_id']]['content']
               for item in request['classifications'])
    prepared_sha = {name: digest(HERE / name) for name in PREPARED}
    runner_sha = digest(Path(__file__))
    if stage == 'actual':
        assert load(HERE / 'parent-input-acceptance.json')['status'].startswith('accepted_')
        shadow = load(HERE / 'shadow-completion.json')
        assert shadow['status'] == 'completed_and_verified' and shadow['actual_main_after_sha256'] == EXPECTED
        assert shadow['prepared_files_sha256'] == prepared_sha and shadow['runner_sha256'] == runner_sha
        assert shadow['execution_code_pins_sha256'] == execution_code_sha256 and shadow['execution_code_pins'] == code_pins
    with closing(readonly()) as origin:
        origin.execute('BEGIN')
        before, old_schema, old_case_state = snapshot(origin), schema(origin), case_state(origin)
        assert all(sum(before[table].values()) == count for table, count in BASE_COUNTS.items())
        assert old_case_state == BASE_CASE_STATE
        assert origin.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'").fetchone()[0] == 108
        assert origin.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0] == 0
        assert origin.execute('SELECT COUNT(*) FROM sources WHERE company_id=?', (COMPANY,)).fetchone()[0] == 0
        assert origin.execute('SELECT 1 FROM companies WHERE id=?', (COMPANY,)).fetchone()
        for source in sources:
            assert not origin.execute('SELECT 1 FROM sources WHERE id=?', (source['id'],)).fetchone()
        if stage == 'shadow':
            fd, name = tempfile.mkstemp(prefix='ir-2315-six-source-shadow-', suffix='.sqlite3')
            os.close(fd); backup = Path(name)
        else:
            backup = ROOT / 'data/backups/ir-research-before-2315-initial-with-facts-2026-10-16.sqlite3'
            assert not backup.exists(), 'Existing backup: stop and inspect the prior run'
            backup.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(backup)) as copied:
            origin.backup(copied)
            assert snapshot(copied) == before and schema(copied) == old_schema
        origin.rollback()
    target = backup if stage == 'shadow' else DB
    store = None
    with journal_path.open('x', encoding='utf-8') as journal:
        def event(name, phase, value):
            journal.write(json.dumps({'recorded_at': clock().isoformat(), 'operation': name,
                                      'phase': phase, 'value': value}, ensure_ascii=False) + '\n')
            journal.flush(); os.fsync(journal.fileno())

        def invoke(name, operation):
            event(name, 'begin', {})
            result = operation(); event(name, 'succeeded', result)
            return result

        try:
            event('baseline_backup', 'succeeded', {'backup_file': str(backup), 'target': str(target),
                'backup_sha256': digest(backup), 'actual_main_sha256': EXPECTED})
            store = Store(str(target))
            assert snapshot(store.connection) == before and schema(store.connection) == old_schema
            harness = Harness(store)
            added = invoke('ingest', lambda: harness.ingest(bundle, now=clock()))
            assert added == {'companies': 0, 'sources_added': 6, 'theses_added': 0}
            boundary = clock()
            queued = invoke('queue', lambda: Intake(store).queue(boundary.isoformat(), company_id=COMPANY, new_only=True, now=boundary))
            assert queued['jobs_created'] == len(queued['selected']) == 1 and not queued['skipped']
            assert queued['deferred_count'] == 0 and queued['selected'][0]['company_id'] == COMPANY
            assert queued['selected'][0]['source_count'] == 6
            job_id = queued['selected'][0]['job_id']
            packet = store.job(job_id)['packet']
            assert packet['kind'] == 'intake' and packet['stage'] == 'source_classification'
            assert packet['company'] == store.company(COMPANY)
            assert {s['id'] for s in packet['sources']} == set(source_by_id)
            assert all(store.source(source['id']) == source for source in sources)
            worker = 'codex-2315-initial-facts-' + stage
            claim = invoke('claim', lambda: harness.claim(worker, now=clock(), measurement_synthetic=False,
                caller_namespace=worker, request_id='2315-initial-six-20261016-1'))
            claimed, lease = claim['original_response'], claim['current_lease']
            assert not claim['replayed'] and claimed['job_id'] == lease['job_id'] == job_id
            assert claimed['company_id'] == COMPANY and claimed['worker'] == lease['worker'] == worker
            assert claimed['generation'] == lease['generation'] == 1 and lease['valid_now'] is True
            assert claimed['packet_sha256'] == lease['packet_sha256'] == sha256(json_text(packet).encode()).hexdigest()
            done = invoke('complete', lambda: harness.complete(job_id, worker, request, expected_attempt=1, now=clock()))
            assert done['id'] == job_id and done['company_id'] == COMPANY and done['status'] == 'completed'
            after = snapshot(store.connection)
            assert set(after) == set(before) and schema(store.connection) == old_schema
            assert case_state(store.connection) == old_case_state
            comparisons = {}
            for table in before:
                delta = sum(after[table].values()) - sum(before[table].values())
                assert not (before[table] - after[table]) and delta == DELTAS.get(table, 0), table
                comparisons[table] = {'before': sum(before[table].values()), 'after': sum(after[table].values()),
                    'delta': delta, 'old_rows_preserved': True, 'entire_table_equal': before[table] == after[table]}
            assert store.connection.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'").fetchone()[0] == 109
            assert store.connection.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0] == 0
            assert all(store.source(source['id']) == source for source in sources)
            store.close(); store = None
            with closing(readonly()) as origin:
                assert snapshot(origin) == (before if stage == 'shadow' else after)
                assert schema(origin) == old_schema and case_state(origin) == old_case_state
            if stage == 'shadow':
                assert digest(DB) == EXPECTED
            result = {'recorded_at': clock().isoformat(), 'stage': stage, 'status': 'completed_and_verified',
                'actual_main_before_sha256': EXPECTED, 'actual_main_after_sha256': digest(DB),
                'backup_file': str(backup), 'job_ids': [job_id], 'old_row_comparison': comparisons,
                'case_state': old_case_state, 'prepared_files_sha256': prepared_sha, 'runner_sha256': runner_sha,
                'execution_code_pins_file': str(code_file), 'execution_code_pins_sha256': execution_code_sha256,
                'execution_code_pins': code_pins, 'financial_inputs_adopted': False, 'GETs': 0,
                'external_sends': 0, 'pipeline_is_not_single_transaction': True,
                'actual_database_mutations': stage == 'actual'}
            save(HERE / (stage + '-completion.json'), result)
            event('verification', 'succeeded', {'old_rows_preserved': True})
            print(json.dumps({key: result[key] for key in ('stage', 'status', 'actual_main_after_sha256', 'case_state')}))
        except BaseException as error:
            if store is not None:
                store.close()
            event('failure', 'failed', {'type': type(error).__name__, 'message': str(error),
                'instruction': 'Inspect journal; never resend completed/uncertain mutations automatically.'})
            raise
    if stage == 'shadow':
        for suffix in ('', '-wal', '-shm'):
            Path(str(backup) + suffix).unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('shadow', 'actual'))
    parser.add_argument('--execution-code-pins', required=True)
    parser.add_argument('--execution-code-pins-sha256', required=True)
    options = parser.parse_args()
    main(options.stage, options.execution_code_pins, options.execution_code_pins_sha256)
