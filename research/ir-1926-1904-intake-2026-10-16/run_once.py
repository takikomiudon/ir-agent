"""One guarded intake per stage; never resume uncertain mutations automatically."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.store import Store

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED = '7ab7d8f54da46b0c95c3893be4454ec42b2f6aca903c2b440f94bfaf2ed1fa44'
DELTAS = {'sources': 4, 'record_availability': 4, 'source_classifications': 4,
          'jobs': 2, 'job_attempts': 2, 'job_attempt_events': 4, 'job_request_receipts': 2}
SPEC = importlib.util.spec_from_file_location('read_checks', ROOT /
    'research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/actual-connection/shadow_preflight.py')
CHECKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKS)  # Pure helpers only; its main is never invoked.


def clock():
    return datetime.now(timezone.utc)


def save(path, value):
    with path.open('x', encoding='utf8') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write('\n'); output.flush(); os.fsync(output.fileno())


def main(stage):
    journal_path = HERE / (stage + '-stage.jsonl')
    assert not journal_path.exists(), 'Existing journal: inspect; never resend uncertain/successful operations'
    assert sha256(DB.read_bytes()).hexdigest() == EXPECTED, 'Actual database changed'
    pins = json.loads((HERE / 'input-pins.json').read_bytes())
    assert all(sha256((ROOT / p).read_bytes()).hexdigest() == wanted for p, wanted in pins.items())
    bundle = json.loads((HERE / 'source-bundle.json').read_bytes())
    requests = json.loads((HERE / 'classification-requests.json').read_bytes())
    assert set(requests) == {'jp:1926', 'jp:1904'} and len(bundle['sources']) == 4
    assert bundle['companies'] == bundle['theses'] == []
    if stage == 'actual':
        shadow = json.loads((HERE / 'shadow-completion.json').read_bytes())
        assert shadow['status'] == 'completed_and_verified' and shadow['actual_main_after_sha256'] == EXPECTED
        assert shadow['prepared_files_sha256'] == {name: sha256((HERE / name).read_bytes()).hexdigest()
            for name in ('source-bundle.json', 'classification-requests.json', 'input-pins.json')}
    with closing(CHECKS.readonly()) as origin:
        before, schema, case_state = CHECKS.snapshot(origin), CHECKS.schema(origin), CHECKS.state(origin)
        assert origin.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'").fetchone()[0] == 101
        assert origin.execute("SELECT COUNT(*) FROM jobs WHERE status!='completed'").fetchone()[0] == 0
        assert sum(before['sources'].values()) == 171 and case_state == {'current_cases': 19, 'reviewed_sources': 113}
        for source in bundle['sources']:
            assert not origin.execute('SELECT 1 FROM sources WHERE id=?', (source['id'],)).fetchone()
        if stage == 'shadow':
            descriptor, name = tempfile.mkstemp(prefix='ir-1926-1904-shadow-', suffix='.sqlite3')
            os.close(descriptor); backup = Path(name)
        else:
            backup = ROOT / 'data/backups/ir-research-before-1926-1904-composite-2026-10-16.sqlite3'
            assert not backup.exists(), 'Existing backup: inspect prior run'
        with closing(sqlite3.connect(backup)) as copy:
            origin.backup(copy)
            assert CHECKS.snapshot(copy) == before and CHECKS.schema(copy) == schema
    target = backup if stage == 'shadow' else DB
    store = None
    with journal_path.open('x', encoding='utf8') as journal:
        def event(name, phase, value):
            journal.write(json.dumps({'recorded_at': clock().isoformat(), 'operation': name,
                'phase': phase, 'value': value}, ensure_ascii=False) + '\n')
            journal.flush(); os.fsync(journal.fileno())

        def invoke(name, operation):
            event(name, 'begin', {})
            result = operation(); event(name, 'succeeded', result)
            return result

        try:
            store = Store(str(target))
            assert CHECKS.snapshot(store.connection) == before and CHECKS.schema(store.connection) == schema
            harness = Harness(store)
            added = invoke('ingest', lambda: harness.ingest(bundle, now=clock()))
            assert added == {'companies': 0, 'sources_added': 4, 'theses_added': 0}
            completed = []
            for company, request in requests.items():
                current = clock()
                queue = invoke(company + ':queue', lambda: Intake(store).queue(current.isoformat(),
                    company_id=company, new_only=True, now=current))
                assert queue['jobs_created'] == 1 and len(queue['selected']) == 1 and not queue['skipped']
                job_id = queue['selected'][0]['job_id']
                packet = store.job(job_id)['packet']
                expected_sources = [s for s in bundle['sources'] if s['company_id'] == company]
                assert {s['id'] for s in packet['sources']} == {s['id'] for s in expected_sources}
                assert all(store.source(s['id']) == s for s in expected_sources)
                worker = 'codex-' + company.split(':')[1] + '-public-composite-' + stage
                claim = invoke(company + ':claim', lambda: harness.claim(worker, now=clock(),
                    measurement_synthetic=False, caller_namespace=worker, request_id='20261016-public-composite-1'))
                lease = claim['current_lease']
                assert not claim['replayed'] and lease['job_id'] == job_id and lease['generation'] == 1 and lease['valid_now']
                done = invoke(company + ':complete', lambda: harness.complete(job_id, worker,
                    request, expected_attempt=1, now=clock()))
                assert done['status'] == 'completed'
                completed.append(job_id)
            after = CHECKS.snapshot(store.connection)
            assert CHECKS.schema(store.connection) == schema and CHECKS.state(store.connection) == case_state
            comparisons = {}
            for table in before:
                delta = sum(after[table].values()) - sum(before[table].values())
                assert not (before[table] - after[table]) and delta == DELTAS.get(table, 0), table
                comparisons[table] = {'before': sum(before[table].values()), 'after': sum(after[table].values()),
                    'delta': delta, 'old_rows_preserved': True, 'entire_table_equal': before[table] == after[table]}
            assert store.connection.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'").fetchone()[0] == 103
            store.close(); store = None
            if stage == 'shadow':
                with closing(CHECKS.readonly()) as origin:
                    assert CHECKS.snapshot(origin) == before and CHECKS.schema(origin) == schema
                assert sha256(DB.read_bytes()).hexdigest() == EXPECTED
            else:
                with closing(CHECKS.readonly()) as origin:
                    assert CHECKS.snapshot(origin) == after
            result = {'recorded_at': clock().isoformat(), 'stage': stage, 'status': 'completed_and_verified',
                'actual_main_before_sha256': EXPECTED, 'actual_main_after_sha256': sha256(DB.read_bytes()).hexdigest(),
                'backup_file': str(backup), 'job_ids': completed, 'old_row_comparison': comparisons,
                'case_state': case_state, 'prepared_files_sha256': {name: sha256((HERE / name).read_bytes()).hexdigest()
                    for name in ('source-bundle.json', 'classification-requests.json', 'input-pins.json')},
                'financial_inputs_adopted': False, 'GETs': 0, 'external_sends': 0,
                'pipeline_is_not_single_transaction': True, 'actual_database_mutations': stage == 'actual'}
            save(HERE / (stage + '-completion.json'), result)
            event('verification', 'succeeded', {'old_rows_preserved': True})
            print(json.dumps({k: result[k] for k in ('stage', 'status', 'actual_main_after_sha256', 'case_state')}))
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
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('shadow', 'actual'))
    main(parser.parse_args().stage)
