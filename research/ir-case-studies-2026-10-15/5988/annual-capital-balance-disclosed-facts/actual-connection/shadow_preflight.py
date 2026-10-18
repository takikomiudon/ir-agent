"""One bounded shadow run. This script has no actual-write mode and no retry path."""
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
ROOT = HERE.parents[4]
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED = 'b554610546a874eb3d57c0e3689a77a68aa67912551e2bbdea87715a7bb513cf'
COMPANY = 'jp:5988'
WORKER = 'codex-5988-annual-capital-balance-intake'
SOURCE = 'disclosed-facts:cba31cbae3e2b2d78353862ceb382b11f3d92efc2195eb944dc0871209e49bd5'
DELTAS = {'sources': 1, 'record_availability': 1, 'source_classifications': 1,
          'jobs': 1, 'job_attempts': 1, 'job_request_receipts': 1, 'job_attempt_events': 2}


def check(value, message):
    if not value:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x', encoding='utf8') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write('\n'); output.flush(); os.fsync(output.fileno())


def readonly():
    connection = sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)
    connection.execute('PRAGMA query_only=ON')
    return connection


def snapshot(connection):
    return {name: Counter(tuple(row) for row in connection.execute('SELECT * FROM "' + name + '"'))
            for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")}


def schema(connection):
    return [tuple(row) for row in connection.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name')]


def state(connection):
    cases = connection.execute('''SELECT a.data FROM qualitative_case_versions a JOIN
        (SELECT case_id,MAX(version) version FROM qualitative_case_versions GROUP BY case_id) b
        ON a.case_id=b.case_id AND a.version=b.version''').fetchall()
    return {'current_cases': len(cases), 'reviewed_sources': sum(len(json.loads(r[0])['reviewed_sources']) for r in cases)}


def main():
    # Reserve exactly one execution. Existing journals are never resumed automatically.
    check(not any((HERE / name).exists() for name in ('shadow-stage.jsonl', 'shadow-completion.json', 'shadow-error.json')),
          'Existing run receipt: stop and inspect; do not resend successful/uncertain mutations')
    stage = 'guards'
    store = None
    with (HERE / 'shadow-stage.jsonl').open('x', encoding='utf8') as journal:
        def event(phase, value):
            journal.write(json.dumps({'recorded_at': now().isoformat(), 'stage': stage, 'phase': phase,
                                      'result': value}, ensure_ascii=False) + '\n')
            journal.flush(); os.fsync(journal.fileno())

        def invoke(name, operation):
            nonlocal stage
            stage = name; event('begin', {})
            result = operation(); event('succeeded', result)
            return result

        try:
            check(digest(DB) == EXPECTED, 'Actual main SHA changed')
            pins = json.loads((HERE / 'input-pins.json').read_bytes())
            check(all(digest(ROOT / path) == wanted for path, wanted in pins['input_files'].items()), 'Frozen input changed')
            for name, key in [('derived-only-bundle.json', 'derived_only_bundle_sha256'), ('classification-request.json', 'classification_request_sha256')]:
                check(digest(HERE / name) == pins[key], 'Prepared request changed')
            full = json.loads((HERE.parent / 'normalized-bundle.json').read_bytes())
            original, derived = full['sources']
            bundle = json.loads((HERE / 'derived-only-bundle.json').read_bytes())
            request = json.loads((HERE / 'classification-request.json').read_bytes())
            check(bundle == {'schema_version': 1, 'companies': [], 'sources': [derived], 'theses': []} and
                  derived['id'] == SOURCE and derived['company_id'] == COMPANY, 'Source-only binding changed')
            facts = json.loads(derived['content'])['facts']
            check(len(facts) == 8 and all(f['period']['end_date'] is None and f['period']['as_of_date'] is None
                  for f in facts[-2:]) and [f['period']['boundary_role'] for f in facts[-2:]] ==
                  ['opening_balance', 'closing_balance'], 'Schedule null dates/boundaries changed')
            with closing(readonly()) as origin:
                origin.execute('BEGIN')
                before, old_schema, old_state = snapshot(origin), schema(origin), state(origin)
                expected = {'sources': 152, 'source_classifications': 151, 'jobs': 86, 'job_attempts': 83,
                            'job_attempt_events': 166, 'job_request_receipts': 83, 'qualitative_case_versions': 31}
                check(all(sum(before[n].values()) == count for n, count in expected.items()) and
                      old_state == {'current_cases': 16, 'reviewed_sources': 98}, 'Baseline counts changed')
                check(origin.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0] == 0 and
                      origin.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'").fetchone()[0] == 86,
                      'Baseline jobs must all be completed')
                check(origin.execute('SELECT COUNT(*) FROM sources WHERE id=?', (SOURCE,)).fetchone()[0] == 0, 'Source already saved')
                check(json.loads(origin.execute('SELECT data FROM sources WHERE id=?', (original['id'],)).fetchone()[0]) == original,
                      'Existing original snapshot differs')
                fd, filename = tempfile.mkstemp(prefix='ir-5988-balance-shadow-', suffix='.sqlite3'); os.close(fd)
                with closing(sqlite3.connect(filename)) as copy:
                    origin.backup(copy)
                    check(snapshot(copy) == before and schema(copy) == old_schema, 'Backup mismatch')
                origin.rollback()
            event('succeeded', {'database_sha256': EXPECTED, 'shadow_file': filename, 'shadow_backup_sha256': digest(filename)})
            store = Store(filename)  # Only the disposable copy is ever passed to Store.
            check(snapshot(store.connection) == before and schema(store.connection) == old_schema, 'Store init changed old data')
            harness = Harness(store)
            check(invoke('ingest', lambda: harness.ingest(bundle, now=now())) ==
                  {'companies': 0, 'sources_added': 1, 'theses_added': 0}, 'Unexpected ingest result')
            clock = now()
            queued = invoke('queue', lambda: Intake(store).queue(clock.isoformat(), company_id=COMPANY, new_only=True, now=clock))
            check(len(queued['selected']) == queued['jobs_created'] == 1 and queued['selected'][0]['company_id'] == COMPANY and
                  queued['selected'][0]['source_count'] == 1 and not queued['skipped'] and queued['deferred_count'] == 0,
                  'Unexpected intake selection')
            job_id = queued['selected'][0]['job_id']
            packet = store.job(job_id)['packet']
            check(packet['kind'] == 'intake' and packet['stage'] == 'source_classification' and packet['sources'] == [derived] and
                  packet['company'] == store.company(COMPANY) and store.source(SOURCE) == derived, 'Wrong frozen packet')
            envelope = invoke('claim', lambda: harness.claim(WORKER, now=now(), measurement_synthetic=False,
                caller_namespace=WORKER, request_id='5988-balance-shadow-20261016-1'))
            claimed, lease = envelope['original_response'], envelope['current_lease']
            check(not envelope['replayed'] and claimed['job_id'] == lease['job_id'] == job_id and claimed['company_id'] == COMPANY and
                  claimed['worker'] == lease['worker'] == WORKER and claimed['generation'] == lease['generation'] == 1 and
                  lease['valid_now'] is True and claimed['packet_sha256'] == lease['packet_sha256'] ==
                  sha256(json_text(packet).encode()).hexdigest(), 'Wrong claim envelope/lease')
            done = invoke('complete', lambda: harness.complete(job_id, WORKER, request, expected_attempt=1, now=now()))
            check(done['id'] == job_id and done['company_id'] == COMPANY and done['status'] == 'completed', 'Wrong completion')
            after = snapshot(store.connection); comparisons = {}
            check(set(before) == set(after) and schema(store.connection) == old_schema, 'Schema changed')
            for table in before:
                delta = sum(after[table].values()) - sum(before[table].values())
                check(not (before[table] - after[table]) and delta == DELTAS.get(table, 0), 'Unexpected mutation: ' + table)
                comparisons[table] = {'before_count': sum(before[table].values()), 'after_count': sum(after[table].values()),
                    'delta': delta, 'old_rows_preserved': True, 'entire_table_equal': before[table] == after[table]}
            check(state(store.connection) == old_state and store.source(original['id']) == original and store.source(SOURCE) == derived,
                  'Existing state or source changed')
            classification = json.loads(store.connection.execute('SELECT data FROM source_classifications WHERE source_id=?', (SOURCE,)).fetchone()[0])
            item = request['classifications'][0]
            check(all(classification[k] == item[k] for k in ('source_id', 'kind', 'financial_content', 'basis_quote', 'rationale')) and
                  classification['job_id'] == job_id and classification['version'] == 1 and classification['inputs_verified'] is False,
                  'Classification changed')
            receipt = dict(store.connection.execute('SELECT * FROM record_availability WHERE entity_id=?', (SOURCE,)).fetchone())
            check(receipt['snapshot_sha256'] == sha256(json_text(derived).encode()).hexdigest() and receipt['basis'] == 'trusted_insert' and
                  receipt['first_saved_at'] == receipt['presence_observed_at'], 'Receipt changed')
            store.close(); store = None
            check(digest(DB) == EXPECTED, 'Actual main SHA changed during shadow')
            with closing(readonly()) as origin:
                check(snapshot(origin) == before and schema(origin) == old_schema, 'Actual logical data changed')
            stage = 'verified'
            result = {'recorded_at': now().isoformat(), 'status': 'shadow_saved_classified_actual_not_executed',
                'actual_before_sha256': EXPECTED, 'actual_after_sha256': digest(DB), 'source_id': SOURCE, 'fact_count': 8,
                'job_id': job_id, 'shadow_file': filename, 'old_row_comparison': comparisons, 'case_state_unchanged': old_state,
                'claim_envelope': envelope, 'classification_in_shadow': classification, 'availability_in_shadow': receipt,
                'original_and_derived_snapshots_unchanged': True, 'schedule_null_dates_unchanged': True,
                'pipeline_is_not_single_transaction': True, 'actual_database_writes': 0, 'new_GETs': 0,
                'financial_inputs_adopted': 0, 'native_cases_changed': 0}
            save('shadow-completion.json', result); event('succeeded', {'all_old_rows_preserved': True})
            print(json.dumps({'status': result['status'], 'job_id': job_id, 'actual_sha256': EXPECTED}))
        except BaseException as error:
            if store is not None:
                store.close()
            failure = {'recorded_at': now().isoformat(), 'stage': stage, 'error_type': type(error).__name__,
                       'error': str(error), 'instruction': 'Stop; inspect stage receipts. Never blindly resend a successful/uncertain mutation.'}
            save('shadow-error.json', failure); event('failed', failure)
            raise


if __name__ == '__main__':
    main()
