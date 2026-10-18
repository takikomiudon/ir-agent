"""One-shot v37 connection: live SQLite read-only, only a new index file writes.

No Store, network, normalizer, backup, job/case mutation or automatic rerun.
"""
from collections import Counter
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from ir_agent.models import json_text
BASE = ROOT / 'research/ir-case-studies-2026-10-15'
OLD = BASE / 'disclosed-fact-index-v36.json'
NEW = BASE / 'disclosed-fact-index-v37.json'
PRE = HERE.parent / 'index-connection-preparation'
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED = 'a11f53fb245bad768e591012c8823094b5b37ca9d2e00f29723cea75ba57bece'
I = ROOT / 'research/ir-2410-initial-with-listing-intake-2026-10-16'
F = ROOT / 'research/ir-2410-facts-with-qa-intake-2026-10-16'

def load(p): return json.loads(p.read_bytes())
def digest(p): return sha256(p.read_bytes()).hexdigest()
def native(value): return sha256(json_text(value).encode('utf-8')).hexdigest()
def resolved(entry, fact): return fact.get('source_id', entry['source_id'])
def save(p, value):
    with p.open('x', encoding='utf-8') as out:
        out.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')

def typed(value):
    if isinstance(value, bytes): return ['blob_hex', value.hex()]
    return [type(value).__name__, value]

def logical_snapshot(connection):
    # Stream each SQL row into a typed SHA, retaining multiplicity. No DB copy.
    output = {}
    for name, in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        records = Counter()
        for row in connection.execute('SELECT * FROM "' + name.replace('"', '""') + '"'):
            records[native([typed(value) for value in row])] += 1
        output[name] = {'rows': sum(records.values()), 'typed_row_multiset_sha256': native(sorted(records.items()))}
    return output

def schema_digest(connection):
    return native([list(row) for row in connection.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name')])

def main():
    assert not NEW.exists() and not (HERE / 'validation.json').exists()
    pins = load(HERE / 'input-pins.json')
    assert all(digest(ROOT / f) == value for f, value in pins.items())
    code = {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT / 'src/ir_agent').rglob('*.py'))}
    assert len(code) == 44 and code == load(ROOT / 'research/ir-public-information-review-binding-integration-2026-10-16/fixed-code-under-test-pins.json')
    assert digest(DB) == EXPECTED
    old, candidate = load(OLD), load(PRE / 'proposed-index-v37.json')
    assert digest(OLD) == 'f614e11911c28adfe4a126fbe60d85141886faefb40b73059d9ca919552bda35'
    assert candidate['companies'][:40] == old['companies'] and len(old['companies']) == 40
    assert load(PRE / 'parent-acceptance.json')['candidate_SHA'] == digest(PRE / 'proposed-index-v37.json')
    original, derived = load(HERE.parent / 'normalized-bundle.json')['sources']
    assert original in load(I / 'source-bundle.json')['sources'] and derived in load(F / 'source-bundle.json')['sources']
    parents = {original['id']: load(I / 'parent-acceptance.json'), derived['id']: load(F / 'parent-acceptance.json')}
    assert parents[derived['id']]['status'] == 'accepted_actual_derived_and_QA_two_sources_one_job'
    firsts = {x['id']: x['first_saved_at'] for parent in parents.values() for x in parent['sources']}
    assert parents[derived['id']]['DB_SHA'] == EXPECTED
    assert firsts[original['id']] == '2026-10-16T06:50:38.803336+00:00'
    assert firsts[derived['id']] == '2026-10-16T07:15:18.475308+00:00'
    facts = json.loads(derived['content'])['facts']
    expected_fields = ('id', 'concept', 'kind', 'period', 'scope', 'unit', 'value')
    entry = candidate['companies'][-1]
    assert entry['company_id'] == 'jp:2410' and not entry['derived_source_imported_into_actual_database']
    assert entry['source_id'] == derived['id'] and entry['original_source_id'] == original['id']
    assert entry['facts'] == [{k: deepcopy(f[k]) for k in expected_fields} for f in facts]
    assert len(facts) == 12 and all(f['source_id'] == original['id'] and 'source_id' not in entry['facts'][n] for n, f in enumerate(facts))
    desired = {}
    for folder in (I, F):
        for request in load(folder / 'classification-requests.json')['jp:2410']['classifications']:
            desired[request['source_id']] = request
    source_checks, indexed_checks = [], []
    expected_counts = {'sources': 210, 'record_availability': 210, 'source_classifications': 209,
                       'jobs': 117, 'job_attempts': 114, 'job_attempt_events': 228,
                       'job_request_receipts': 114, 'qualitative_case_versions': 47}
    with closing(sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('PRAGMA query_only=ON')
        assert connection.execute('PRAGMA query_only').fetchone()[0] == 1
        connection.execute('BEGIN')
        before, before_schema = logical_snapshot(connection), schema_digest(connection)
        assert len(before) == 27
        counts = {name: before[name]['rows'] for name in expected_counts}
        assert counts == expected_counts
        assert connection.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'").fetchone()[0] == 117
        assert connection.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0] == 0
        heads = [json.loads(row[0]) for row in connection.execute('''SELECT a.data FROM qualitative_case_versions a JOIN
            (SELECT case_id,MAX(version) version FROM qualitative_case_versions GROUP BY case_id) b
            ON a.case_id=b.case_id AND a.version=b.version''')]
        assert len(heads) == 25 and sum(len(row['reviewed_sources']) for row in heads) == 144
        assert not any(row['company_id'] == 'jp:2410' for row in heads)
        for source in (original, derived):
            sid = source['id']; snapshot = native(source)
            row = connection.execute('SELECT company_id,data FROM sources WHERE id=?', (sid,)).fetchone()
            assert row and row[0] == 'jp:2410' and json.loads(row[1]) == source
            availability = list(connection.execute("SELECT snapshot_sha256,first_saved_at,presence_observed_at,basis FROM record_availability WHERE entity_type='source' AND entity_id=?", (sid,)).fetchone())
            parent = parents[sid]; firstsave = firsts[sid]
            assert snapshot == native(source)
            if sid == original['id']:
                assert snapshot == load(HERE.parent / 'source-reference.json')['original_source_native_SHA']
            else:
                assert snapshot.startswith('a3cb0f1')
            assert availability == [snapshot, firstsave, firstsave, 'trusted_insert']
            classification = json.loads(connection.execute('SELECT data FROM source_classifications WHERE source_id=? ORDER BY version DESC LIMIT 1', (sid,)).fetchone()[0])
            assert classification['source_id'] == sid and classification['source_snapshot_sha256'] == snapshot
            assert classification['version'] == desired[sid]['expected_version'] + 1
            assert all(classification[k] == desired[sid][k] for k in ('kind','financial_content','basis_quote','rationale'))
            assert classification['basis_quote'] in source['content'] and classification['inputs_verified'] is False
            source_checks.append({'source_id': sid, 'native_snapshot_sha256': snapshot,
                'actual_data_column_UTF8_sha256': sha256(row[1].encode()).hexdigest(),
                'whole_actual_source_object_exact': True, 'classification': classification,
                'classification_native_sha256': native(classification), 'availability_columns': availability,
                'first_saved_at': firstsave, 'original_retrieved_at': source['retrieved_at'],
                'published_at': source['published_at'], 'root_receipt_firstsave_exact_and_accepted_bundle_object_exact': True})
        assert connection.execute('SELECT COUNT(*) FROM sources WHERE company_id=?', ('jp:2410',)).fetchone()[0] == 5
        flat = [(e, f) for e in candidate['companies'] for f in e['facts']]
        source_ids = {resolved(e, f) for e, f in flat}
        actual, outside = set(), set()
        for sid in sorted(source_ids):
            row = connection.execute('SELECT company_id,data FROM sources WHERE id=?', (sid,)).fetchone()
            if row is None:
                outside.add(sid); indexed_checks.append({'source_id': sid, 'actual_saved': False}); continue
            actual.add(sid); saved = json.loads(row[1]); actual_class = json.loads(connection.execute('SELECT data FROM source_classifications WHERE source_id=? ORDER BY version DESC LIMIT 1', (sid,)).fetchone()[0])
            assert actual_class['source_snapshot_sha256'] == native(saved)
            assert all(e['company_id'] == row[0] == saved['company_id'] for e,f in flat if resolved(e,f) == sid)
            indexed_checks.append({'source_id': sid, 'actual_saved': True, 'company_id': row[0], 'source_native_sha256': native(saved), 'current_classification_snapshot_matches': True})
        actual_facts = sum(resolved(e, f) in actual for e, f in flat)
        assert (len(actual), actual_facts, len(outside), len(flat) - actual_facts) == (41, 219, 2, 7)
        outside_rows = [(e['company_id'], f['id'], resolved(e,f)) for e,f in flat if resolved(e,f) in outside]
        assert outside_rows == [(e['company_id'], f['id'], resolved(e,f)) for e in old['companies'] for f in e['facts'] if resolved(e,f) in outside]
        assert {row[0] for row in outside_rows} == {'jp:8331', 'jp:9702'}
        actual_derived = json.loads(connection.execute('SELECT data FROM sources WHERE id=?', (derived['id'],)).fetchone()[0])
        assert json.loads(actual_derived['content'])['facts'] == facts
        after, after_schema = logical_snapshot(connection), schema_digest(connection)
        assert before == after and before_schema == after_schema
        journal_mode = connection.execute('PRAGMA journal_mode').fetchone()[0]
        connection.rollback()
    assert digest(DB) == EXPECTED and all(digest(ROOT / f) == h for f, h in pins.items())
    now = datetime.now(timezone.utc).isoformat()
    value = deepcopy(candidate)
    value['companies'][-1]['derived_source_imported_into_actual_database'] = True
    assert value['companies'][:40] == old['companies']
    changed_newentry = deepcopy(value['companies'][-1]); changed_newentry['derived_source_imported_into_actual_database'] = False
    assert changed_newentry == candidate['companies'][-1]
    value.pop('candidate_connection_state')
    value['earlier_previous_actual_research_source_connections_snapshot'] = deepcopy(old['previous_actual_research_source_connections_snapshot'])
    value['previous_actual_research_source_connections_snapshot'] = deepcopy(old['actual_research_source_connections'])
    value['previous_actual_research_source_connections_snapshot_note'] = 'Historical v36 connection observation retained verbatim; not the current v37 state.'
    value['connection_preparation'] = {'candidate_path': str((PRE / 'proposed-index-v37.json').relative_to(ROOT)),
        'candidate_sha256': digest(PRE / 'proposed-index-v37.json'), 'candidate_is_historical_and_unchanged': True,
        'parent_acceptance': str((PRE / 'parent-acceptance.json').relative_to(ROOT)), 'actual_derived_intake_now_separately_accepted': True}
    value['recorded_at'] = now
    value['actual_research_source_connections'].update(actual_database_main_sha256=EXPECTED,
        database_snapshot_recorded_at=now, database_source_count=210, connected_derived_source_count=41,
        connected_fact_count=219, unconnected_derived_source_count=2, unconnected_fact_count=7,
        current_source_classification_count=209, current_completed_job_count=117,
        current_job_attempt_count=114, current_job_attempt_event_count=228, current_job_request_receipt_count=114,
        current_qualitative_case_heads=25, current_qualitative_case_versions=47, current_reviewed_sources=144,
        observation_scope='Live mode=ro/query_only/closing; before2410nativecase registration, all jobs completed, no DB writes')
    receipt_paths = [I / 'parent-acceptance.json', F / 'parent-acceptance.json', F / 'actual-completion.json']
    for path in receipt_paths:
        rel = str(path.relative_to(ROOT))
        if rel not in value['actual_research_source_connections']['connection_receipts']:
            value['actual_research_source_connections']['connection_receipts'].append(rel)
    value['layout_note'] = '41 parents/43 resolvedderived sources/226facts/28companies/34company-original pairs. Live41derived/219facts are stored and classified; outside8331/9702 two derived/7facts stayfile-only. Historicalv36state preserved separately. No financial adoption.'
    value['limitations'][-1] = '2410 accepted12 displays retain nonconsolidated net_income (not parent attributable), dated July31 issuer FY guidance for a now-ended FY (not actual or current guidance), and annualDPS160 including ordinary140+special20 with complete scopes/nulls. No permanent-dividend/payment/currentforecast/model adoption. Newderived now stored/classified; original and derived firstsave timestamps remain distinct from HTTP/extraction.'
    value['revision_basis'] = {'kind': 'connect_2410_twelve_accepted_disclosed_facts_after_live_source_receipt_classification_check',
        'added_fact_count': 12, 'added_parent_entry_count': 1, 'prior40_parent_entries_214facts_all_fields_exact': True,
        'existing_per_fact_source_artifact_overrides_preserved': True, 'newentry_only_imported_flag_changed_from_candidate': True,
        'financial_model_adoption': False}
    save(NEW, value)
    save(HERE / 'code-pins.json', code)
    save(HERE / 'actual-source-proof.json', {'recorded_at': now, 'DB_main_SHA': EXPECTED,
        'new_two_sources': source_checks, 'indexed_source_classification_checks': indexed_checks,
        'old_27table_row_fingerprints_before': before, 'old_27table_row_fingerprints_after': after,
        'schema_digest_before': before_schema, 'schema_digest_after': after_schema,
        'row_fingerprint_method': 'Per SQL row typed-cell JSON SHA, Counter multiplicities, sorted multiset SHA. No raw DB copy.',
        'journal_mode_observed': journal_mode, 'actual_counts': counts,
        'all_old_logical_rows_and_schema_unchanged': True, 'DB_Store_writes': 0})
    save(HERE / 'validation.json', {'recorded_at': now, 'status': 'frozen_live_RO_v37_connection_pending_root_review',
        'new_index_sha256': digest(NEW), 'old_v36_sha256': digest(OLD), 'candidate_sha256': digest(PRE / 'proposed-index-v37.json'),
        'old40parents214facts_whole_exact': True, 'candidate_all12_fact_scope_values_exact': True,
        'candidate_newentry_only_importedflag_changed': True, 'oldsource_artifact_overrides_unchanged': True,
        'rawfact_primary_sourceid_not_used_as_index_override': True,
        'new12facts_actual_derived_content_exact': True, 'two_source_full_objects_classifications_availability_receipts_exact': True,
        'firstsave_original': firsts[original['id']], 'firstsave_derived': firsts[derived['id']],
        'counts': {'companies': 28, 'parents': 41, 'facts': 226, 'derived_sources': 43, 'company_original_pairs': 34,
                   'actual_derived_sources': 41, 'actual_facts': 219, 'outside_derived': 2, 'outside_facts': 7},
        'outside_rows_unchanged': outside_rows, 'all27_logical_tables_and_schema_unchanged': True,
        'old_v36_actual_connection_snapshot_preserved_separately': True, 'actual_DB_main_before_SHA': EXPECTED,
        'actual_DB_main_after_SHA': digest(DB), 'code44_exactly_latest1558_accepted': True,
        'current_case_heads_versions_reads': [25, 47, 144], '2410_native_case_not_registered_at_snapshot': True,
        'all117_jobs_completed_pendingleased0': True, 'normalizer_reproducer_calls': 0,
        'DBwrites_Store_GET_financial_adoption': 0, 'input_pins_unchanged': True})
    print(json.dumps({'index_v37_SHA': digest(NEW), 'validation_SHA': digest(HERE / 'validation.json'),
        'actualsource_proof_SHA': digest(HERE / 'actual-source-proof.json'), 'DB_main_SHA_unchanged': digest(DB)}, ensure_ascii=False))

if __name__ == '__main__': main()
