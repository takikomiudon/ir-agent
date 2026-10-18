"""One bounded company-source batch import; global platform terms remain file-only."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.models import json_text, parse_json
from ir_agent.store import Store
from ir_agent.harness import Harness
from ir_agent.intake import Intake

HERE = Path(__file__).resolve().parent
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
TABLES = ('companies', 'sources', 'source_classifications', 'jobs', 'job_attempts',
          'job_attempt_events', 'job_request_receipts', 'theses', 'questions',
          'replies', 'decision_policies', 'position_declarations')


def load(path):
    return parse_json(path.read_bytes().decode('utf-8'))


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as handle:
        handle.write(json_text(value) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', required=True)
    parser.parse_args()
    acceptance = ROOT / 'research/ir-disclosed-share-unit-integration-2026-10-15/parent-acceptance.json'
    assert load(acceptance)['status'] == 'accepted_with_documented_limits'
    review = load(HERE.parent / 'author-public-chapters/independent-recheck.json')
    assert [x['id'] for x in review['findings']] == ['1723-SOURCE-CONTRACT-01']
    assert load(HERE / 'preflight.json')['independent_finding_resolved_by_addendum'] is True
    assert not (HERE / 'actual-import.json').exists()
    bundle = load(HERE / 'source-only-bundle.json')
    sources = bundle['sources']
    source_ids = {source['id'] for source in sources}
    preflight = load(HERE / 'preflight.json')
    for key in ('source_review', 'resolution_addendum'):
        pinned = preflight[key]
        assert sha256((ROOT / pinned['path']).read_bytes()).hexdigest() == pinned['sha256']
    assert load(ROOT / preflight['resolution_addendum']['path'])['status'] == 'source_contract_finding_resolved_for_new_company_subset_original_bundle_unchanged'
    assert sha256(DB.read_bytes()).hexdigest() == preflight['database_main_sha256_before_and_after']
    assert len(sources) == 3 and set(bundle) == {'schema_version', 'sources'}
    assert {source['id']: sha256(json_text(source).encode()).hexdigest() for source in sources} == preflight['source_snapshot_sha256']
    readonly = sqlite3.connect(DB.resolve().as_uri() + '?mode=ro', uri=True)
    readonly.execute('PRAGMA query_only=ON')
    before = {table: readonly.execute('SELECT * FROM ' + table).fetchall()
              for table in ('sources', 'companies', 'source_classifications')}
    assert len(before['sources']) == 103
    assert all(readonly.execute('SELECT count(*) FROM sources WHERE id=?', (source['id'],)).fetchone()[0] == 0 for source in sources)
    assert readonly.execute("SELECT count(*) FROM jobs WHERE status<>'completed'").fetchone()[0] == 0
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = ROOT / ('data/ir-research-before-1723-author-' + stamp + '.sqlite3')
    destination = sqlite3.connect(backup)
    readonly.backup(destination)
    destination.close()
    readonly.close()
    save('execution-start.json', {'started_at': datetime.now(timezone.utc).isoformat(),
         'backup_path': str(backup.relative_to(ROOT)),
         'backup_sha256': sha256(backup.read_bytes()).hexdigest(),
         'database_main_sha256_before': preflight['database_main_sha256_before_and_after']})
    store = Store(str(DB))
    harness = Harness(store)
    ingestion = harness.ingest(bundle)
    save('ingest-result.json', ingestion)
    assert ingestion == {'companies': 0, 'sources_added': 3, 'theses_added': 0}
    queue = Intake(store).queue(datetime.now(timezone.utc).isoformat(), company_id='jp:1723', limit=1)
    save('queue-result.json', queue)
    assert len(queue['selected']) == 1
    worker = 'parent-1723-author-classification'
    claim = harness.claim(worker, measurement_synthetic=False,
        caller_namespace='research-session-2026-10-15',
        request_id='nihondengi-author-batch-20261015')
    save('claim-request-receipt.json', claim)
    job_id = claim['original_response']['job_id']
    assert claim['current_lease']['valid_now'] is True
    assert job_id == queue['selected'][0]['job_id']
    job = store.job(job_id)
    save('frozen-packet.json', job['packet'])
    assert job['attempts'] == claim['original_response']['generation'] == 1
    assert {item['id'] for item in job['packet']['sources']} == source_ids
    completed = harness.complete(job_id, worker, load(HERE / 'classification-input.json'), expected_attempt=job['attempts'])
    save('completed-job.json', completed)
    assert completed['status'] == 'completed'
    unchanged = {}
    for table, rows in before.items():
        after = set(tuple(row) for row in store.connection.execute('SELECT * FROM ' + table))
        unchanged[table] = set(rows).issubset(after)
        assert unchanged[table]
    assert all(store.source(source['id']) == source for source in sources)
    counts = {table: store.connection.execute('SELECT count(*) FROM ' + table).fetchone()[0] for table in TABLES}
    receipts = [dict(store.connection.execute("SELECT * FROM record_availability WHERE entity_type='source' AND entity_id=?", (source['id'],)).fetchone()) for source in sources]
    availability = dict(store.connection.execute("SELECT basis,count(*) FROM record_availability WHERE entity_type='source' GROUP BY basis"))
    store.connection.close()
    save('actual-import.json', {'recorded_at': datetime.now(timezone.utc).isoformat(),
         'status': 'completed', 'job_id': job_id, 'generation': 1,
         'actual_counts': counts, 'source_availability_counts': availability,
         'new_source_first_save_receipts': receipts,
         'old_records_unchanged': unchanged,
         'source_snapshot_unchanged': True, 'company_metadata_ingested': 0,
         'database_main_sha256_after': sha256(DB.read_bytes()).hexdigest(),
         'financial_inputs_verified': False, 'model_adopted': False,
         'measurement_scope': 'One classification lease only; not full research throughput.',
         'new_GETs_external_sends_orders': 0})
    print(json_text({'status': 'completed', 'job_id': job_id, 'actual_counts': counts}))


if __name__ == '__main__':
    main()
