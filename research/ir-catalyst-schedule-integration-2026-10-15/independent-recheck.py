"""Finite independent schedule-only recheck; never writes a workspace DB."""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path('/workspace/ir-agent')
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.availability import RecordAvailability, SCHEMA as AVAILABILITY_SCHEMA
from ir_agent.catalyst_schedule import report_catalyst_schedule
from ir_agent.intake import SCHEMA as CLASSIFICATION_SCHEMA
from ir_agent.models import json_text, now_iso, validate_source

spec = importlib.util.spec_from_file_location('bounded_catalyst_cli', ROOT / 'scripts/report_catalyst_schedule.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)

SAVED = '2026-10-14T09:00:00+00:00'
CLASSIFIED = '2026-10-14T10:00:00+00:00'
AS_OF = '2026-10-14T12:00:00+00:00'
NOW = '2026-11-12T12:00:00+00:00'
LATE = '2026-11-09T10:00:00+00:00'
LATE_CLASSIFIED = '2026-11-09T10:01:00+00:00'
WINDOW = {'date_from': '2026-11-01', 'date_through': '2026-11-30'}
report = {'scope': 'Schedule-only finite independent checks; no occurrence, date resolution, changes or jobs',
          'checks': {}, 'limitations': [
              'Source matching does not verify date/period meaning, prospectiveness, complete event universe or economic effects.',
              'Synthetic DB fixtures are isolated; the one real DB call uses SQLite mode=ro and query_only.',
              'Real DB base/WAL hashes are compared once around that call; SHM is coordination state, not audited logical content.',
              'No new GET, Store initialization, migration, production/test edits or workspace DB writes are performed.']}


def digest(value):
    return sha256(json_text(value).encode()).hexdigest()


def source(identity, *, metadata=None, **updates):
    value = {'id': identity, 'company_id': 'jp:BOUND', 'title': 'Synthetic calendar',
             'url': 'https://example.invalid/' + identity, 'source_type': 'public_disclosure',
             'published_at': None, 'retrieved_at': '2026-10-14T08:00:00+00:00',
             'content': '2026年度 2026年4月～2027年3月 11月06日（予定） 2027年3月期第2四半期決算発表',
             'metadata': {'synthetic': True} if metadata is None else metadata}
    value.update(updates)
    return validate_source(value)


def event(value):
    return {'id': 'bounded-q2', 'company_id': value['company_id'], 'synthetic': True,
            'kind': 'earnings_release', 'label': 'Synthetic Q2 announcement',
            'period': {'raw_label': '2027年3月期第2四半期', 'fiscal_year_label': '2027年3月期',
                       'quarter_label': '第2四半期', 'basis_quote': value['content'],
                       'interpretation': 'Explicit synthetic mapping; meaning unverified.'},
            'claims': [{'id': 'bounded-schedule-1', 'kind': 'schedule', 'source_id': value['id'],
                        'source_snapshot_sha256': digest(value), 'basis_quote': value['content'],
                        'basis_quote_location': None, 'raw_date_label': '11月06日（予定）',
                        'date': '2026-11-06', 'time': None, 'timezone': None,
                        'date_context_quote': '2026年度 2026年4月～2027年3月',
                        'date_context_rationale': 'Synthetic year mapping, not a verified interpretation.',
                        'supersedes_claim_id': None}]}


def classification(db, value, *, version=1, kind='schedule', recorded=CLASSIFIED, saved=CLASSIFIED):
    data = {'source_id': value['id'], 'version': version, 'kind': kind,
            'basis_quote': value['content'], 'source_sha256': sha256(value['content'].encode()).hexdigest(),
            'source_snapshot_sha256': digest(value), 'recorded_at': recorded, 'inputs_verified': False}
    db.execute('INSERT INTO source_classifications VALUES (?,?,?,?,?)',
               (value['id'], version, json_text(data), saved, 'synthetic-job'))


def database(entries):
    db = sqlite3.connect(':memory:', isolation_level=None)
    db.executescript('CREATE TABLE sources(id TEXT PRIMARY KEY,data TEXT);' + AVAILABILITY_SCHEMA + CLASSIFICATION_SCHEMA)
    # Sorting keeps the library's global runtime clock monotone, while letting
    # an earlier root depend on a later-arriving second parent.
    for value, saved, classified in sorted(entries, key=lambda entry: entry[1]):
        db.execute('BEGIN')
        db.execute('INSERT INTO sources VALUES (?,?)', (value['id'], json_text(value)))
        RecordAvailability(db).record_first_save('source', value['id'], value, now=saved)
        db.execute('COMMIT')
        if classified is not None:
            classification(db, value, recorded=classified, saved=classified)
    return db


def inspect(db, requests, *, as_of=AS_OF, now=NOW, window=WINDOW):
    before_requests, before_window = deepcopy(requests), deepcopy(window)
    before_dump, before_changes, before_tx = list(db.iterdump()), db.total_changes, db.in_transaction
    result = report_catalyst_schedule(db, requests, as_of=as_of, now=now, calendar_window=window)
    assert requests == before_requests and window == before_window
    assert list(db.iterdump()) == before_dump and db.total_changes == before_changes
    assert db.in_transaction == before_tx
    assert result['status'] == 'schedule_monitor_only'
    assert result['coverage']['event_count'] == len(requests) == len(result['events'])
    for item in result['events']:
        assert item['due'] is None and item['timing']['scheduled_at'] is None
        assert item['timing']['time'] is None and item['timing']['timezone'] is None
        assert item['timing']['relation_to_as_of'] == 'unknown_timezone'
        assert item['occurrence'] == {'status': 'not_established'}
        assert item['result_documents'] == {'status': 'none_linked'}
        assert item['semantic_review_required'] is True
        assert item['schedule']['date_interpretation'] == 'caller_mapping_unverified'
        assert item['mapping_prospectiveness'] == 'unverified'
    return result


def summary(item):
    return {key: item[key] for key in ('status', 'reason_codes', 'historical_usability', 'current_use')}


root = source('calendar')
db = database([(root, SAVED, CLASSIFIED)])
request = event(root)
base = inspect(db, [request])
assert base['events'][0]['status'] == 'source_bound_candidate'
report['checks']['baseline_candidate'] = summary(base['events'][0])

# UTC and JST midnight both remain floating; even a later date is not occurrence.
for boundary in ('2026-11-05T15:00:00+00:00', '2026-11-06T00:00:00+00:00', '2026-11-07T00:00:00+09:00'):
    assert inspect(db, [request], as_of=boundary)['events'][0]['timing']['status'] == 'floating_date'
report['checks']['midnight_and_past_date_do_not_resolve_due_or_occurrence'] = True

bad_bindings = {}
for name in ('snapshot', 'quote', 'company'):
    changed = deepcopy(request)
    if name == 'snapshot': changed['claims'][0]['source_snapshot_sha256'] = '0' * 64
    if name == 'quote': changed['claims'][0]['basis_quote'] = 'Missing quotation'
    if name == 'company': changed['company_id'] = 'jp:OTHER'
    item = inspect(db, [changed])['events'][0]
    assert item['status'] == 'mismatch'
    bad_bindings[name] = summary(item)
report['checks']['snapshot_quote_company_mismatch'] = bad_bindings

# Caller transaction stays open, including its uncommitted work, then remains rollbackable.
db.execute('CREATE TABLE marker(value TEXT)')
db.execute('BEGIN')
db.execute("INSERT INTO marker VALUES ('pending')")
inspect(db, [request])
assert db.in_transaction and db.execute('SELECT * FROM marker').fetchall() == [('pending',)]
db.execute('ROLLBACK')
assert db.execute('SELECT COUNT(*) FROM marker').fetchone()[0] == 0
db.execute('PRAGMA query_only=ON')
inspect(db, [request])
assert db.execute('PRAGMA query_only').fetchone()[0] == 1
report['checks']['outer_transaction_and_query_only_preserved'] = True

# All-parent checks: the first parent is usable; the second carries the sole fault.
parent_cases = {}
for variant in ('shared_dag', 'future_second', 'late_second', 'nonpublic_second', 'unclassified_second', 'synthetic_second'):
    first = source('first', metadata={})
    second_metadata = {'original_source_id': 'first'} if variant == 'shared_dag' else {}
    if variant == 'nonpublic_second': second_metadata['information_status'] = 'potential_nonpublic'
    if variant == 'synthetic_second': second_metadata['synthetic'] = True
    second = source('second', metadata=second_metadata)
    root2 = source('root', metadata={'original_source_ids': ['first', 'second']})
    stamp, class_stamp = SAVED, CLASSIFIED
    if variant in ('future_second', 'late_second'): stamp, class_stamp = LATE, LATE_CLASSIFIED
    if variant == 'future_second':
        second['retrieved_at'] = '2026-11-09T09:00:00+00:00'
    if variant == 'unclassified_second': class_stamp = None
    case_db = database([(first, SAVED, CLASSIFIED), (root2, SAVED, CLASSIFIED), (second, stamp, class_stamp)])
    try:
        case_request = event(root2)
        case_request['synthetic'] = False
        item = inspect(case_db, [case_request])['events'][0]
        assert len(item['lineage_checks']) == 3
        if variant == 'shared_dag':
            assert item['status'] == 'source_bound_candidate'
        else:
            assert item['status'] != 'source_bound_candidate'
        if variant in ('future_second', 'late_second'):
            assert item['historical_usability']['status'] == 'mismatch'
            assert item['current_use']['status'] == 'matched'
            assert 'first_saved_after_knowledge_at' in item['reason_codes']
        if variant == 'future_second': assert 'effective_time_after_as_of' in item['reason_codes']
        if variant == 'nonpublic_second': assert item['current_use']['status'] == 'held'
        if variant == 'unclassified_second': assert 'classification_not_available' in item['reason_codes']
        if variant == 'synthetic_second': assert 'synthetic_source_in_real_observation' in item['reason_codes']
        parent_cases[variant] = summary(item)
    finally:
        case_db.close()
report['checks']['all_parent_lineage'] = parent_cases

# A later classification hold affects current use, preserving the earlier classification.
hold_db = database([(root, SAVED, CLASSIFIED)])
old = inspect(hold_db, [request], now=AS_OF)
classification(hold_db, root, version=2, kind='unresolved', recorded=LATE_CLASSIFIED, saved=LATE_CLASSIFIED)
held = inspect(hold_db, [request])['events'][0]
assert held['historical_usability']['status'] == 'matched'
assert held['current_use']['status'] == 'held'
assert held['lineage_checks'][0]['historical_classification']['version'] == 1
assert held['lineage_checks'][0]['current_classification']['version'] == 2
assert old['events'] == inspect(hold_db, [request], now=AS_OF)['events']
# source_sections is explicitly the current physical table inventory; its
# row_count legitimately increases after an appended classification.
report['checks']['current_classification_hold_preserves_history'] = summary(held)
hold_db.close()

# Real saved public snapshot is copied into a synthetic memory DB, never re-fetched.
case = ROOT / 'research/ir-case-studies-2026-10-15/1332'
requests_path = case / 'catalyst-schedule-requests.json'
requests_raw = requests_path.read_bytes()
nissui_requests = json.loads(requests_raw)
bundle_path = case / 'statement-calendar-followup/source-bundle.json'
bundle_raw = bundle_path.read_bytes()
bundle = json.loads(bundle_raw)
calendar = next(item for item in bundle['sources'] if item['id'] == nissui_requests[0]['claims'][0]['source_id'])
assert all(item['claims'][0]['source_snapshot_sha256'] == digest(calendar) for item in nissui_requests)
nissui_db = database([(calendar, '2026-10-15T10:00:00+00:00', '2026-10-15T10:01:00+00:00')])
nissui = inspect(nissui_db, nissui_requests, as_of='2026-10-15T11:00:00+00:00')
assert nissui['coverage'] == {'event_count': 3, 'in_window_count': 2, 'outside_window_count': 1,
                              'date_unknown_count': 0, 'source_bound_candidate_count': 3}
assert [item['timing']['scheduled_date'] for item in nissui['events']] == ['2026-11-06', '2026-11-10', '2027-02-05']
report['checks']['nissui_saved_snapshot_three_events'] = {'coverage': nissui['coverage'],
    'dates': [item['timing']['scheduled_date'] for item in nissui['events']],
    'snapshot_sha256': digest(calendar), 'all_due_null_occurrence_not_established': True}
nissui_db.close()

# Disk read-only report/actual CLI: use only a synthetic temporary DB.
with tempfile.TemporaryDirectory(prefix='ir-catalyst-schedule-recheck-') as temporary:
    temp = Path(temporary)
    path = temp / 'synthetic.sqlite3'
    disk = sqlite3.connect(path)
    db.backup(disk)
    disk.close()
    before = path.read_bytes()
    ro_report = cli.read_report(path, [request], as_of=AS_OF, now=NOW, calendar_window=WINDOW)
    assert ro_report['events'] == base['events']
    assert path.read_bytes() == before
    event_path = temp / 'events.json'
    event_path.write_text(json_text([request]))
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = cli.main(['--db', str(path), '--events', str(event_path), '--as-of', AS_OF,
                         '--date-from', WINDOW['date_from'], '--date-through', WINDOW['date_through']])
    assert code == 0 and stderr.getvalue() == '', stderr.getvalue()
    parsed = json.loads(stdout.getvalue())
    assert parsed['events'][0]['status'] == 'source_bound_candidate'
    assert parsed['events'][0]['due'] is None
    assert parsed['events'][0]['occurrence']['status'] == 'not_established'
    assert path.read_bytes() == before
    report['checks']['readonly_disk_and_cli_bytes_unchanged'] = True
db.close()

# Exactly one authorized real DB read via the script's mode=ro/query_only path.
actual_database = ROOT / 'data/ir-research-2026-10-15.sqlite3'
actual_output = json.loads((ROOT / 'data/catalyst-schedule-nissui-2026-10-15.json').read_text())
actual_files = [actual_database]
wal = Path(str(actual_database) + '-wal')
if wal.exists(): actual_files.append(wal)
before_hashes = {str(path): sha256(path.read_bytes()).hexdigest() for path in actual_files}
current = now_iso()
actual = cli.read_report(actual_database, nissui_requests, as_of=actual_output['as_of'], now=current, calendar_window=WINDOW)
after_hashes = {str(path): sha256(path.read_bytes()).hexdigest() for path in actual_files}
assert before_hashes == after_hashes
assert actual['coverage'] == {'event_count': 3, 'in_window_count': 2, 'outside_window_count': 1,
                             'date_unknown_count': 0, 'source_bound_candidate_count': 3}
assert all(item['due'] is None and item['occurrence']['status'] == 'not_established' for item in actual['events'])
report['checks']['actual_db_one_readonly_call'] = {'before_sha256': before_hashes, 'after_sha256': after_hashes,
    'coverage': actual['coverage'], 'as_of': actual['as_of'], 'checked_at': actual['checked_at']}
report['actual_readonly_report'] = actual
assert requests_path.read_bytes() == requests_raw and bundle_path.read_bytes() == bundle_raw
report['checks']['original_case_files_unchanged'] = True
report['status'] = 'passed'
out = Path('/tmp/ir_catalyst_schedule_recheck.json')
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'artifact': str(out),
                  'checks': list(report['checks'])}, ensure_ascii=False))
