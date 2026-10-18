"""Root-only guarded registration; successful or uncertain stages are not replayed."""
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

from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.store import Store

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED = '11b6ad2c3cd5f6903fc3ce3654bf2ab5b850cd137061ac05fd6627d426b73778'
SPEC = importlib.util.spec_from_file_location('checks', ROOT / 'research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/actual-connection/shadow_preflight.py')
CHECKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKS)  # Pure helpers, never its main.


def now():
    return datetime.now(timezone.utc)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(name, value):
    with (HERE / name).open('x', encoding='utf8') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main(stage):
    assert not (HERE / (stage + '-stage.jsonl')).exists()
    assert not (HERE / (stage + '-completion.json')).exists()
    assert digest(DB) == EXPECTED
    assert load(HERE / 'parent-input-acceptance.json')['status'].startswith('accepted_')
    code_file = ROOT / 'research/ir-1975-initial-with-facts-intake-2026-10-16/prepared-code-pins.json'
    assert digest(code_file) == '9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60'
    code = load(code_file)
    assert set(code) == {str(f.relative_to(ROOT)) for f in (ROOT / 'src/ir_agent').rglob('*.py')}
    assert all(digest(ROOT / name) == value for name, value in code.items())
    request = load(HERE / 'register-request.json')
    inputs = {name: digest(HERE / name) for name in ('register-request.json', 'case-context.json', 'review-manifest.json', 'management-basis.json', 'parent-input-acceptance.json')}
    if stage == 'actual':
        previous = load(HERE / 'copyguard-completion.json')
        assert previous['status'] == 'completed_and_verified'
        assert previous['input_files_sha256'] == inputs
        assert previous['runner_sha256'] == digest(Path(__file__))
        assert previous['execution_code_sha256'] == digest(code_file)
    with tempfile.TemporaryDirectory(prefix='ir-1975-native-', dir='/tmp') as directory:
        if stage == 'actual':
            backup = ROOT / 'data/backups/ir-research-before-1975-native-case-2026-10-16.sqlite3'
            assert not backup.exists()
        else:
            backup = Path(directory) / 'copy.sqlite3'
        with closing(CHECKS.readonly()) as origin:
            before, schema = CHECKS.snapshot(origin), CHECKS.schema(origin)
            assert CHECKS.state(origin) == {'current_cases': 21, 'reviewed_sources': 125}
            assert sum(before['qualitative_case_versions'].values()) == 42
            assert origin.execute("SELECT COUNT(*) FROM jobs WHERE status!='completed'").fetchone()[0] == 0
            with closing(sqlite3.connect(backup)) as copied:
                origin.backup(copied)
                assert CHECKS.snapshot(copied) == before and CHECKS.schema(copied) == schema
        store = None
        with (HERE / (stage + '-stage.jsonl')).open('x', encoding='utf8') as journal:
            def event(operation, phase, value):
                journal.write(json.dumps({'recorded_at': now().isoformat(), 'operation': operation, 'phase': phase, 'value': value}, ensure_ascii=False) + '\n')
                journal.flush(); os.fsync(journal.fileno())
            try:
                store = Store(str(DB if stage == 'actual' else backup))
                assert CHECKS.snapshot(store.connection) == before and CHECKS.schema(store.connection) == schema
                service = QualitativeResearch(store)
                event('register', 'begin', {'expected_version': 0, 'backup_file': str(backup)})
                registered = service.register_case(request, expected_version=0, research_root=ROOT, now=now())
                event('register', 'succeeded', registered)
                save(stage + '-case.json', registered)
                assert registered['version'] == registered['config_revision'] == 1
                assert len(registered['record']['reviewed_sources']) == 4
                assert registered['record']['bootstrap_meaning_verified'] is False
                after = CHECKS.snapshot(store.connection)
                assert CHECKS.schema(store.connection) == schema
                for table in before:
                    assert not (before[table] - after[table])
                    assert sum(after[table].values()) - sum(before[table].values()) == (1 if table == 'qualitative_case_versions' else 0), table
                assert CHECKS.state(store.connection) == {'current_cases': 22, 'reviewed_sources': 129}
                queue = service.queue_cases([request['case_id']], now().isoformat(), now=now())
                assert queue['jobs_created'] == 0
                assert CHECKS.snapshot(store.connection) == after
                event('initial_queue', 'succeeded', queue)
                store.close(); store = None
                with closing(CHECKS.readonly()) as origin:
                    assert CHECKS.snapshot(origin) == (after if stage == 'actual' else before)
                assert stage == 'actual' or digest(DB) == EXPECTED
                result = {'recorded_at': now().isoformat(), 'stage': stage, 'status': 'completed_and_verified',
                    'backup_file': str(backup), 'DB_main_before_sha256': EXPECTED, 'DB_main_after_sha256': digest(DB),
                    'input_files_sha256': inputs, 'runner_sha256': digest(Path(__file__)), 'execution_code_sha256': digest(code_file),
                    'old_rows_all_preserved': True, 'only_delta': {'qualitative_case_versions': 1},
                    'case_state': {'current_cases': 22, 'reviewed_sources': 129}, 'initial_queue': queue,
                    'financial_inputs_adopted': False, 'actual_DB_writes': stage == 'actual'}
                save(stage + '-completion.json', result)
                event('verification', 'succeeded', {'old_rows_preserved': True})
                print(json.dumps(result, ensure_ascii=False))
            except BaseException as error:
                if store is not None:
                    store.close()
                event('failure', 'failed', {'type': type(error).__name__, 'message': str(error), 'instruction': 'Inspect journal; never replay successful or uncertain registration.'})
                raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('copyguard', 'actual'))
    main(parser.parse_args().stage)
