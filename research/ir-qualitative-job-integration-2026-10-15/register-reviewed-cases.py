"""One guarded real case-ledger bootstrap, after tests and copy validation."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.models import json_text
from ir_agent.store import Store
from ir_agent.qualitative_research import QualitativeResearch

HERE = Path(__file__).resolve().parent
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'


def load(path):
    return json.loads(path.read_bytes())


def save(name, value):
    with (HERE / name).open('x') as handle:
        handle.write(json_text(value) + '\n')


def inventory(connection):
    result = {}
    for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        name = row[0]
        if name == 'qualitative_case_versions':
            continue
        quoted = '"' + name.replace('"', '""') + '"'
        rows = sorted(json_text(list(item)) for item in connection.execute('SELECT * FROM ' + quoted))
        result[name] = {'count': len(rows), 'rows_sha256': sha256(json_text(rows).encode()).hexdigest()}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', required=True)
    parser.parse_args()
    acceptance = load(HERE / 'parent-acceptance.json')
    assert acceptance['status'] == 'accepted_with_documented_limits'
    assert all(sha256((ROOT / name).read_bytes()).hexdigest() == digest
               for name, digest in acceptance['source_sha256'].items())
    check = load(HERE / 'copy-bootstrap-validation-v2.json')
    assert check['status'] == 'copy_only_bootstrap_v2_verified' and check['queue']['jobs_created'] == 0
    assert not (HERE / 'actual-bootstrap.json').exists()
    request_file = HERE / 'bootstrap-case-requests-v2.json'
    assert sha256(request_file.read_bytes()).hexdigest() == check['request_sha256']
    requests = load(request_file)
    before_sha = sha256(DB.read_bytes()).hexdigest()
    assert before_sha == check['actual_DB_sha256_after']
    ro = sqlite3.connect(DB.resolve().as_uri() + '?mode=ro', uri=True)
    ro.execute('PRAGMA query_only=ON')
    before = inventory(ro)
    assert before['sources']['count'] == 116 and before['jobs']['count'] == 47
    assert not ro.execute("SELECT name FROM sqlite_master WHERE name='qualitative_case_versions'").fetchone()
    backup = ROOT / ('data/ir-research-before-qualitative-bootstrap-' +
                     datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.sqlite3')
    destination = sqlite3.connect(backup); ro.backup(destination); destination.close(); ro.close()
    save('execution-start.json', {'started_at': datetime.now(timezone.utc).isoformat(),
        'database_main_sha256_before': before_sha, 'backup_path': str(backup.relative_to(ROOT)),
        'backup_sha256': sha256(backup.read_bytes()).hexdigest(), 'old_table_inventory': before})
    store = Store(DB)
    registry = QualitativeResearch(store)
    with store.transaction():
        assert inventory(store.connection) == before
        records = [registry.register_case(item, 0, research_root=ROOT, now=datetime.now(timezone.utc))
                   for item in requests]
        assert len(records) == 12 and sum(len(r['record']['reviewed_sources']) for r in records) == 62
        current = datetime.now(timezone.utc)
        queued = registry.queue_cases([r['case_id'] for r in requests], current.isoformat(),
                                      limit=20, now=current)
        assert queued['jobs_created'] == 0
        assert inventory(store.connection) == before
    result = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'status': 'completed',
        'case_count': len(records), 'reviewed_source_count': 62, 'case_versions': [
            {key: r[key] for key in ('case_id', 'version', 'config_revision', 'first_saved_at')}
            for r in records], 'queue': queued, 'old_table_inventory_before': before,
        'old_table_inventory_after': inventory(store.connection), 'old_tables_unchanged': True,
        'bootstrap_meaning_verified': False, 'sources': 116, 'jobs': 47,
        'financial_theses_questions_replies_policies_orders': 0, 'new_GETs': 0}
    store.close()
    result['database_main_sha256_after'] = sha256(DB.read_bytes()).hexdigest()
    save('actual-bootstrap.json', result)
    print(json_text({key: result[key] for key in
        ('status', 'case_count', 'reviewed_source_count', 'old_tables_unchanged', 'sources', 'jobs')}))


if __name__ == '__main__':
    main()
