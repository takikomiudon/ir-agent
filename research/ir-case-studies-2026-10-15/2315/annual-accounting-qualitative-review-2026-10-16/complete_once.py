"""Root-only copy rehearsal then one actual completion of the claimed review."""
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
from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.store import Store

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED = 'a58c753a50289659b45f3f57b86ccbf8061c39f33f266bebca7e0622da8fced4'
SPEC = importlib.util.spec_from_file_location('readonly_checks', ROOT / 'research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/actual-connection/shadow_preflight.py')
CHECKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKS)


def clock():
    return datetime.now(timezone.utc)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(name, value):
    with (HERE / name).open('x', encoding='utf8') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        output.flush()
        os.fsync(output.fileno())


def main(stage):
    assert not (HERE / (stage + '-stage.jsonl')).exists()
    assert not (HERE / (stage + '-completion.json')).exists()
    assert digest(DB) == EXPECTED
    acceptance = load(HERE / 'parent-input-acceptance.json')
    assert acceptance['status'].startswith('accepted_')
    request = load(HERE / 'worker-result.json')
    assert digest(HERE / 'worker-result.json') == acceptance['worker_result_SHA']
    for name, expected in acceptance['review_dependency_pins'].items():
        assert digest(ROOT / name) == expected
    code_file = ROOT / 'research/ir-2315-annual-accounting-intake-2026-10-16/prepared-code-pins.json'
    assert digest(code_file) == '9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60'
    for name, expected in load(code_file).items():
        assert digest(ROOT / name) == expected
    claim = load(HERE / 'queue-claim-completion.json')
    packet = load(HERE / 'job-packet.json')
    job_id, worker = claim['job_id'], claim['worker']
    inputs = {name: digest(HERE / name) for name in ('worker-result.json', 'job-packet.json', 'parent-input-acceptance.json')}
    if stage == 'actual':
        prior = load(HERE / 'copyguard-completion.json')
        assert prior['status'] == 'completed_and_verified' and prior['input_files_SHA'] == inputs
        assert prior['runner_SHA'] == digest(Path(__file__))
        assert load(HERE / 'parent-copyguard-acceptance.json')['status'].startswith('accepted_')
    with tempfile.TemporaryDirectory(prefix='ir-2315-annual-complete-', dir='/tmp') as directory:
        copied_path = Path(directory) / 'leased.sqlite3'
        with closing(CHECKS.readonly()) as original:
            before, schema = CHECKS.snapshot(original), CHECKS.schema(original)
            assert CHECKS.state(original) == {'current_cases': 24, 'reviewed_sources': 141}
            assert original.execute('SELECT COUNT(*) FROM qualitative_case_versions').fetchone()[0] == 45
            assert original.execute("SELECT COUNT(*) FROM jobs WHERE status='leased'").fetchone()[0] == 1
            with closing(sqlite3.connect(copied_path)) as copied:
                original.backup(copied)
                assert CHECKS.snapshot(copied) == before and CHECKS.schema(copied) == schema
        target = DB if stage == 'actual' else copied_path
        store = None
        with (HERE / (stage + '-stage.jsonl')).open('x', encoding='utf8') as journal:
            def event(operation, phase, value):
                journal.write(json.dumps({'recorded_at': clock().isoformat(), 'operation': operation,
                                          'phase': phase, 'value': value}, ensure_ascii=False) + '\n')
                journal.flush()
                os.fsync(journal.fileno())
            try:
                store = Store(str(target))
                assert CHECKS.snapshot(store.connection) == before and CHECKS.schema(store.connection) == schema
                old_job = store.job(job_id)
                assert old_job['status'] == 'leased' and old_job['attempts'] == 1 and old_job['lease_owner'] == worker
                assert old_job['packet'] == packet and datetime.fromisoformat(old_job['lease_until']) > clock()
                event('complete', 'begin', {'job_id': job_id, 'worker': worker, 'expected_attempt': 1})
                completed = Harness(store).complete(job_id, worker, request, expected_attempt=1, now=clock())
                event('complete', 'succeeded', {'job_id': completed['id'], 'status': completed['status']})
                save(stage + '-job.json', completed)
                assert completed['status'] == 'completed' and completed['result']['request'] == request
                case = QualitativeResearch(store).show_case(packet['case_id'])
                save(stage + '-case.json', case)
                assert case['version'] == 2 and case['config_revision'] == 1
                assert len(case['record']['reviewed_sources']) == 8
                for identity, old_review in packet['case_snapshot']['reviewed_sources'].items():
                    assert case['record']['reviewed_sources'][identity] == old_review
                assert case['record']['management_review'] == packet['case_snapshot']['management_review']
                after = CHECKS.snapshot(store.connection)
                assert CHECKS.schema(store.connection) == schema
                for table in before:
                    if table in ('jobs', 'job_attempts'):
                        field = 'id' if table == 'jobs' else 'job_id'
                        columns = [row[1] for row in store.connection.execute('PRAGMA table_info(' + table + ')')]
                        index = columns.index(field)
                        assert {row: n for row, n in before[table].items() if row[index] != job_id} == {
                            row: n for row, n in after[table].items() if row[index] != job_id}
                        assert sum(after[table].values()) == sum(before[table].values())
                    else:
                        assert not (before[table] - after[table]), table
                        assert sum(after[table].values()) - sum(before[table].values()) == (
                            1 if table in ('qualitative_case_versions', 'job_attempt_events') else 0), table
                assert CHECKS.state(store.connection) == {'current_cases': 24, 'reviewed_sources': 142}
                assert store.connection.execute("SELECT COUNT(*) FROM jobs WHERE status!='completed'").fetchone()[0] == 0
                boundary = clock()
                queued = QualitativeResearch(store).queue_cases([packet['case_id']], boundary.isoformat(), now=boundary)
                event('after_review_queue', 'succeeded', queued)
                assert queued['jobs_created'] == 0 and CHECKS.snapshot(store.connection) == after
                store.close()
                store = None
                with closing(CHECKS.readonly()) as original:
                    assert CHECKS.snapshot(original) == (after if stage == 'actual' else before)
                assert stage == 'actual' or digest(DB) == EXPECTED
                result = {'status': 'completed_and_verified', 'recorded_at': clock().isoformat(), 'stage': stage,
                          'job_id': job_id, 'DB_before_SHA': EXPECTED, 'DB_after_SHA': digest(DB),
                          'input_files_SHA': inputs, 'runner_SHA': digest(Path(__file__)),
                          'case_heads': 24, 'case_versions': 46, 'reviewed_sources': 142,
                          'only_claimed_job_and_attempt_updated': True, 'old_other_rows_preserved': True,
                          'after_review_queue_jobs': 0, 'financial_inputs_adopted': False}
                save(stage + '-completion.json', result)
                print(json.dumps(result))
            except BaseException as error:
                if store is not None:
                    store.close()
                event('failure', 'failed', {'type': type(error).__name__, 'message': str(error),
                                            'instruction': 'Inspect journal/current job; do not replay a successful or uncertain completion.'})
                raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('copyguard', 'actual'))
    main(parser.parse_args().stage)
