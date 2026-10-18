#!/usr/bin/env python3
"""5988 one-source intake receipt. Shadow by default; actual execution belongs to root.

Normal APIs commit each stage separately. Never automatically resume/retry this
script after an uncertain or successful mutator; inspect the immutable journal.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.models import json_text
from ir_agent.store import Store

DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED_DB = '2a36bf74a54c61905bb44926692d2ec89570c66315d0ebbd0bbb4b13f4ad93ce'
FULL_BUNDLE = HERE.parent / 'normalized-bundle.json'
FULL_SHA = '4c7723e2667252489997eaa2abaf99862c6c87b3d1fd02cef4053a890ec9683e'
SOURCE = 'disclosed-facts:1fce07909a0b48066cb45e14c7b72920922a97f859d1efe6b3589f49dd23c94b'
ORIGINAL = 'case-public:5d5a98a7770af91318e9bb24fd4bdac483b20cb5fc96a79f58474dbd77f57365'
COMPANY = 'jp:5988'
WORKER = 'codex-5988-annual-capital-facts-intake'
DELTAS = {'sources': 1, 'record_availability': 1, 'source_classifications': 1,
          'jobs': 1, 'job_attempts': 1, 'job_request_receipts': 1, 'job_attempt_events': 2}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def clock():
    return datetime.now(timezone.utc)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def ro_connection():
    connection = sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)
    connection.execute('PRAGMA query_only=ON')
    require(connection.execute('PRAGMA query_only').fetchone()[0] == 1, 'query_only missing')
    return connection


def rows(connection):
    names = [r[0] for r in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    return {name: Counter(tuple(row) for row in connection.execute(
        'SELECT * FROM "' + name.replace('"', '""') + '"')) for name in names}


def row_hash(value):
    ordered = sorted(((list(row), count) for row, count in value.items()), key=json_text)
    return sha256(json_text(ordered).encode()).hexdigest()


def row_receipts(snapshot):
    return {name: {'count': sum(value.values()), 'all_rows_sha256': row_hash(value)}
            for name, value in snapshot.items()}


def schema(connection):
    return list(connection.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name'))


def summary(connection):
    reviewed = connection.execute('''SELECT a.data FROM qualitative_case_versions a
        JOIN (SELECT case_id,MAX(version) version FROM qualitative_case_versions GROUP BY case_id) b
        ON a.case_id=b.case_id AND a.version=b.version''').fetchall()
    return {'case_count': len(reviewed),
            'latest_case_reviewed_sources': sum(len(json.loads(row[0])['reviewed_sources']) for row in reviewed)}


def check_base(connection, original):
    require(connection.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0] == 0,
            'pending/leased jobs must be zero')
    require(connection.execute('SELECT COUNT(*) FROM sources WHERE id=?', (SOURCE,)).fetchone()[0] == 0,
            'derived source already exists; no resend')
    require(connection.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] == 84, 'expected 84 old jobs')
    require(connection.execute('SELECT COUNT(*) FROM qualitative_case_versions').fetchone()[0] == 30,
            'expected 30 old case versions')
    require(summary(connection) == {'case_count': 16, 'latest_case_reviewed_sources': 97},
            'expected 16 current cases / 97 reviewed sources')
    row = connection.execute('SELECT company_id,data FROM sources WHERE id=?', (ORIGINAL,)).fetchone()
    require(row is not None and row[0] == COMPANY and json.loads(row[1]) == original,
            'original snapshot differs from saved bundle')
    require(connection.execute('SELECT id FROM companies WHERE id=?', (COMPANY,)).fetchone() is not None,
            'existing company missing')


def approval_files(args, bundle_hash):
    # These file contracts attest the parent's review; this script cannot authenticate an actor.
    shadow = json.loads((HERE / 'shadow-completion.json').read_bytes())
    require(shadow.get('status') == 'shadow_saved_classified_verified' and
            shadow.get('actual_after_sha256') == EXPECTED_DB and
            shadow.get('actual_database_writes_by_this_run') is False, 'shadow verification missing')
    pins = {'script_sha256': digest(__file__), 'derived_bundle_sha256': bundle_hash,
            'shadow_completion_sha256': digest(HERE / 'shadow-completion.json'),
            'expected_database_sha256': EXPECTED_DB}
    for label in ('independent_review', 'parent_acceptance'):
        name, wanted = getattr(args, label), getattr(args, label + '_sha256')
        require(name is not None and wanted is not None, label + ' path and SHA required')
        path = Path(name).resolve()
        require(digest(path) == wanted, label + ' SHA mismatch')
        receipt = json.loads(path.read_bytes())
        require(receipt.get('status') == ('pass' if label == 'independent_review' else 'accepted'),
                label + ' status is not affirmative')
        require(all(receipt.get(key) == value for key, value in pins.items()), label + ' pin mismatch')
    accepted = json.loads(Path(args.parent_acceptance).read_bytes())
    require(accepted.get('independent_review_sha256') == args.independent_review_sha256,
            'parent acceptance must pin independent review')
    require(args.actor == 'root', 'actual mode is reserved for parent root')
    return pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('shadow', 'actual'), default='shadow')
    parser.add_argument('--actor')
    for label in ('independent-review', 'parent-acceptance'):
        parser.add_argument('--' + label)
        parser.add_argument('--' + label + '-sha256')
    args = parser.parse_args()
    journal_path = HERE / (args.mode + '-stage.jsonl')
    completion_path = HERE / (args.mode + '-completion.json')
    error_path = HERE / (args.mode + '-error.json')
    store = None
    journal = None
    stage = 'guards'
    try:
        require(not any(p.exists() for p in (journal_path, completion_path, error_path)),
                'this mode already has a run receipt; inspect, never blindly resend')
        require(digest(DB) == EXPECTED_DB, 'actual main database SHA changed')
        require(digest(FULL_BUNDLE) == FULL_SHA, 'frozen full bundle SHA mismatch')
        full = json.loads(FULL_BUNDLE.read_bytes())
        require([s['id'] for s in full['sources']] == [ORIGINAL, SOURCE], 'unexpected full bundle sources')
        original, derived = full['sources']
        require(derived['company_id'] == COMPANY, 'derived company mismatch')
        facts = json.loads(derived['content'])['facts']
        require(len(facts) == 14 and all(f['kind'] == 'reported_fact' and
                f['company_id'] == COMPANY and f['financial_inputs_verified'] is False for f in facts),
                '14 historical reported facts required')
        source_only = {'schema_version': 1, 'companies': [], 'sources': [derived], 'theses': []}
        require(json.loads((HERE / 'derived-only-bundle.json').read_bytes()) == source_only,
                'derived-only bundle is not the unchanged new source')
        bundle_hash = digest(HERE / 'derived-only-bundle.json')
        classification = json.loads((HERE / 'classification-request.json').read_bytes())
        require(len(classification['classifications']) == 1, 'one classification required')
        item = classification['classifications'][0]
        require(item['source_id'] == SOURCE and item['expected_version'] == 0 and
                item['kind'] == 'other' and item['financial_content'] is True and
                item['basis_quote'] in derived['content'], 'classification binding mismatch')
        pins = approval_files(args, bundle_hash) if args.mode == 'actual' else None
        with closing(ro_connection()) as origin:
            origin.execute('BEGIN')
            check_base(origin, original)
            before = rows(origin)
            before_schema = schema(origin)
            before_summary = summary(origin)
            fd, backup_name = tempfile.mkstemp(prefix='ir-5988-capital-' + args.mode + '-', suffix='.sqlite3')
            os.close(fd)
            backup_path = Path(backup_name)
            with sqlite3.connect(backup_path) as backup:
                origin.backup(backup)
                require(rows(backup) == before and schema(backup) == before_schema,
                        'backup rows/schema mismatch')
            origin.rollback()
        require(digest(DB) == EXPECTED_DB, 'actual SHA changed during backup')
        backup_hash = digest(backup_path)
        # Only after all guards + verified backup do we reserve a one-time journal.
        journal = journal_path.open('x', encoding='utf-8')

        def record(name, phase, value):
            json.dump({'recorded_at': clock().isoformat(), 'stage': name, 'phase': phase, 'result': value},
                      journal, ensure_ascii=False)
            journal.write('\n'); journal.flush(); os.fsync(journal.fileno())

        def mutate(name, operation):
            nonlocal stage
            stage = name
            record(name, 'begin', {})
            value = operation()
            record(name, 'succeeded', value)
            return value

        preapply = {'recorded_at': clock().isoformat(), 'mode': args.mode,
                    'actual_before_sha256': EXPECTED_DB, 'backup_file': str(backup_path),
                    'backup_sha256': backup_hash, 'all_tables': row_receipts(before),
                    'summary': before_summary, 'source_id': SOURCE, 'original_source_id': ORIGINAL,
                    'script_sha256': digest(__file__), 'derived_bundle_sha256': bundle_hash,
                    'classification_request_sha256': digest(HERE / 'classification-request.json'),
                    'approval_pins': pins, 'pipeline_is_not_single_transaction': True}
        write_new(HERE / (args.mode + '-preapply.json'), preapply)
        record('start', 'succeeded', preapply)
        target = backup_path if args.mode == 'shadow' else DB
        if args.mode == 'actual':
            require(digest(DB) == EXPECTED_DB, 'actual SHA changed before Store open')
            with closing(ro_connection()) as origin:
                require(rows(origin) == before and schema(origin) == before_schema,
                        'actual logical state changed before Store open')
                check_base(origin, original)
        # No Store(actual) in shadow. Root alone may explicitly select actual mode.
        store = Store(target)
        require(rows(store.connection) == before and schema(store.connection) == before_schema,
                'Store init changed old state')
        harness = Harness(store)
        ingested = mutate('ingest', lambda: harness.ingest(source_only, now=clock()))
        require(ingested == {'companies': 0, 'sources_added': 1, 'theses_added': 0}, 'unexpected ingest result')
        require(store.source(SOURCE) == derived and store.source(ORIGINAL) == original, 'stored source changed')
        def queue():
            current = clock()
            return Intake(store).queue(current.isoformat(), company_id=COMPANY, new_only=True, now=current)
        queued = mutate('queue', queue)
        require(queued['jobs_created'] == 1 and len(queued['selected']) == 1 and
                queued['deferred_count'] == 0 and not queued['skipped'], 'unexpected queue selection')
        selected = queued['selected'][0]
        require(selected['company_id'] == COMPANY and selected['source_count'] == 1 and
                selected['status'] == 'pending', 'wrong queue company/source/stage')
        job_id = selected['job_id']

        def check_job(status):
            job = store.job(job_id)
            packet = job['packet']
            require(job['company_id'] == COMPANY and job['status'] == status and
                    packet['kind'] == 'intake' and packet['stage'] == 'source_classification' and
                    packet['company'] == store.company(COMPANY) and packet['sources'] == [derived],
                    'job/packet identity mismatch')
            require(packet['source_sha256'] == {SOURCE: sha256(derived['content'].encode()).hexdigest()} and
                    packet['source_snapshot_sha256'] == {SOURCE: sha256(json_text(derived).encode()).hexdigest()},
                    'packet source SHA mismatch')
            return job

        check_job('pending')
        envelope = mutate('claim', lambda: harness.claim(WORKER, now=clock(), measurement_synthetic=False,
            caller_namespace=WORKER, request_id='5988-capital-' + args.mode + '-20261016-1'))
        claimed = envelope['original_response']
        lease = envelope['current_lease']
        job = check_job('leased')
        require(envelope['replayed'] is False and claimed['job_id'] == job_id and
                claimed['company_id'] == COMPANY and claimed['worker'] == WORKER and
                claimed['generation'] == job['attempts'] == 1 and lease['valid_now'] is True and
                lease['job_id'] == job_id and lease['worker'] == WORKER and lease['generation'] == 1 and
                lease['packet_sha256'] == claimed['packet_sha256'] == sha256(json_text(job['packet']).encode()).hexdigest(),
                'claim envelope/lease mismatch')
        completed = mutate('complete', lambda: harness.complete(job_id, WORKER, classification,
                                                               expected_attempt=1, now=clock()))
        require(completed['id'] == job_id and completed['status'] == 'completed', 'complete mismatch')
        check_job('completed')
        saved_classification = json.loads(store.connection.execute(
            'SELECT data FROM source_classifications WHERE source_id=?', (SOURCE,)).fetchone()[0])
        require(all(saved_classification[key] == item[key] for key in
                    ('source_id', 'kind', 'financial_content', 'basis_quote', 'rationale')) and
                saved_classification['version'] == 1 and saved_classification['job_id'] == job_id and
                saved_classification['inputs_verified'] is False, 'classification result mismatch')
        after = rows(store.connection)
        require(set(before) == set(after) and schema(store.connection) == before_schema, 'schema changed')
        comparisons = {}
        for table in before:
            delta = sum(after[table].values()) - sum(before[table].values())
            preserved = not (before[table] - after[table])
            require(preserved and delta == DELTAS.get(table, 0), 'unexpected table mutation: ' + table)
            comparisons[table] = {'before_count': sum(before[table].values()),
                'after_count': sum(after[table].values()), 'old_rows_preserved': preserved,
                'entire_table_equal': before[table] == after[table], 'delta': delta}
        require(summary(store.connection) == before_summary, 'case/reviewed count changed')
        receipt = dict(store.connection.execute('SELECT * FROM record_availability WHERE entity_id=?', (SOURCE,)).fetchone())
        require(receipt['basis'] == 'trusted_insert' and receipt['first_saved_at'] == receipt['presence_observed_at'] and
                receipt['snapshot_sha256'] == sha256(json_text(derived).encode()).hexdigest(), 'availability mismatch')
        store.close(); store = None
        actual_after = digest(DB)
        if args.mode == 'shadow':
            require(actual_after == EXPECTED_DB, 'actual main SHA changed during shadow')
            with closing(ro_connection()) as origin:
                require(rows(origin) == before and schema(origin) == before_schema, 'actual logical rows changed')
        stage = 'verified'
        result = {'recorded_at': clock().isoformat(), 'status': args.mode + '_saved_classified_verified',
            'mode': args.mode, 'source_id': SOURCE, 'fact_count': 14, 'job_id': job_id,
            'actual_before_sha256': EXPECTED_DB, 'actual_after_sha256': actual_after,
            'actual_database_writes_by_this_run': args.mode == 'actual',
            'before_tables': row_receipts(before), 'after_tables': row_receipts(after),
            'old_row_comparison': comparisons, 'summary': before_summary,
            'availability_receipt_in_target': receipt, 'classification_in_target': saved_classification,
            'claim_envelope': envelope, 'backup_file': str(backup_path), 'backup_before_sha256': backup_hash,
            'target_after_sha256': digest(target), 'financial_inputs_adopted': 0, 'new_GETs': 0,
            'original_snapshot_unchanged': True, 'original_timestamps_preserved': True,
            'pipeline_is_not_single_transaction': True,
            'note': 'Shadow first-save/lease timestamps apply only to the disposable copy; not actual DB persistence.'
                    if args.mode == 'shadow' else 'Actual execution is reserved for root after independent acceptance.'}
        record('verified', 'succeeded', {'all_old_rows_preserved': True, 'actual_after_sha256': actual_after})
        write_new(completion_path, result)
        print(json.dumps({'status': result['status'], 'receipt': str(completion_path), 'actual_sha256': actual_after}))
    except BaseException as error:
        if store is not None:
            store.close()
        failure = {'recorded_at': clock().isoformat(), 'mode': args.mode, 'stage': stage,
                   'error_type': type(error).__name__, 'error': str(error),
                   'instruction': 'Stop. Inspect journal/DB; do not unconditionally replay successful/uncertain mutators.'}
        if journal is not None:
            record(stage, 'failed', failure)
        if not error_path.exists():
            write_new(error_path, failure)
        raise
    finally:
        if journal is not None:
            journal.close()


if __name__ == '__main__':
    main()
