"""Append accepted 1904 six facts to v28; actual SQLite is read-only and closed."""
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from ir_agent.models import json_text

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = ROOT / 'research/ir-case-studies-2026-10-15'
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED_DB = '7ab7d8f54da46b0c95c3893be4454ec42b2f6aca903c2b440f94bfaf2ed1fa44'


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf8') as output:
        json.dump(value, output, ensure_ascii=False, sort_keys=True, indent=2)
        output.write('\n')


def resolved(entry, fact):
    # Existing per-fact overrides retain precedence over the parent.
    return fact.get('source_id', entry['source_id'])


def main():
    old_path = BASE / 'disclosed-fact-index-v28.json'
    new_path = BASE / 'disclosed-fact-index-v29.json'
    assert not new_path.exists() and not (HERE / 'validation.json').exists()
    bundle_path = HERE.parent / 'normalized-bundle.json'
    actual_ref = HERE.parent / 'actual-connection/actual-completion.json'
    qual_ref = HERE.parent / 'qualitative-review/parent-acceptance.json'
    frozen_files = [p for p in HERE.parent.rglob('*') if p.is_file()
                    and HERE not in p.parents and '__pycache__' not in p.parts]
    frozen_files += [old_path, ROOT / 'research/ir-new-company-intake-2026-10-16/index-connection/build_index.py']
    pins = {str(path.relative_to(ROOT)): digest(path) for path in frozen_files}
    old = json.loads(old_path.read_bytes())
    assert len(old['companies']) == 32 and sum(len(e['facts']) for e in old['companies']) == 144
    assert old['fact_count'] == 144 and old['unique_derived_source_count'] == 34
    assert digest(bundle_path) == '07e79894f6727dba572e63852bf7093e3fe805547742c832e48168e14efd0ea0'
    original, derived = json.loads(bundle_path.read_bytes())['sources']
    assert derived['id'] == 'disclosed-facts:e7ca122ed5aaa0bfc91f7ff96d815b499b472fae77f3c9132d507def18454826'
    assert original['id'] == 'case-public:cd0710232d105dbfbd9a4fff16df1b2d631daf2d95337c50e771fa7d486d2e29'
    facts = json.loads(derived['content'])['facts']
    assert len(facts) == 6 and [f['kind'] for f in facts] == ['reported_fact'] * 3 + ['issuer_guidance'] * 3
    assert all(f['original_source_id'] == f['source_id'] == original['id'] for f in facts)
    assert all(f['financial_inputs_verified'] is False and not f['scope']['financial_meaning_adopted'] for f in facts)
    assert all(f['period']['version_reference_announcement_date'] == '2026-05-13'
               and f['period']['observed_in_source_disclosure_date'] == '2026-08-06'
               and f['scope']['October_current_guidance_or_share_or_consolidation_basis_verified'] is False
               for f in facts if f['kind'] == 'issuer_guidance')
    accepted = json.loads(qual_ref.read_bytes())
    assert accepted['status'] == 'accepted_completed_six_disclosed_fact_qualitative_review'
    assert accepted['actual_main_sha256'] == digest(DB) == EXPECTED_DB
    value = deepcopy(old)
    value['companies'].append({
        'artifact': str(bundle_path.relative_to(ROOT)), 'artifact_sha256': digest(bundle_path),
        'company_id': 'jp:1904', 'contact_catalog_member': True,
        'derived_retrieved_at': derived['retrieved_at'],
        'derived_source_imported_into_actual_database': True,
        'facts': [{key: deepcopy(f[key]) for key in ('id', 'concept', 'kind', 'period', 'scope', 'unit', 'value')}
                  for f in facts],
        'original_retrieved_at': original['retrieved_at'],
        'original_source_id': original['id'], 'source_id': derived['id']})
    assert value['companies'][:32] == old['companies']
    flattened = [(entry, fact) for entry in value['companies'] for fact in entry['facts']]
    assert len({f['id'] for _, f in flattened}) == len(flattened) == 150
    sources = {resolved(e, f) for e, f in flattened}
    pairs = {(e['company_id'], f.get('original_source_id', e['original_source_id'])) for e, f in flattened}
    companies = {e['company_id'] for e in value['companies']}
    assert (len(companies), len(value['companies']), len(sources), len(pairs)) == (21, 33, 35, 26)
    # No Store(actual) and no schema initialization; the connection always closes.
    with closing(sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('PRAGMA query_only=ON')
        assert connection.execute('PRAGMA query_only').fetchone()[0] == 1
        connection.execute('BEGIN')
        counts = {name: connection.execute('SELECT COUNT(*) FROM ' + name).fetchone()[0]
                  for name in ('sources', 'source_classifications', 'jobs', 'job_attempts', 'job_attempt_events',
                               'job_request_receipts', 'qualitative_case_versions')}
        assert counts == {'sources': 171, 'source_classifications': 170, 'jobs': 101, 'job_attempts': 98,
                          'job_attempt_events': 196, 'job_request_receipts': 98, 'qualitative_case_versions': 39}
        assert connection.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'").fetchone()[0] == 101
        assert connection.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0] == 0
        heads = connection.execute('''SELECT a.data FROM qualitative_case_versions a JOIN
            (SELECT case_id,MAX(version) version FROM qualitative_case_versions GROUP BY case_id) b
            ON a.case_id=b.case_id AND a.version=b.version''').fetchall()
        assert len(heads) == 19 and sum(len(json.loads(r[0])['reviewed_sources']) for r in heads) == 113
        for source in (original, derived):
            row = connection.execute('SELECT company_id,data FROM sources WHERE id=?', (source['id'],)).fetchone()
            assert row and row[0] == 'jp:1904' and json.loads(row[1]) == source
        actual, unconnected = set(), set()
        for source_id in sources:
            row = connection.execute('SELECT data FROM sources WHERE id=?', (source_id,)).fetchone()
            if row is None:
                unconnected.add(source_id)
                continue
            actual.add(source_id)
            classification = connection.execute('SELECT data FROM source_classifications WHERE source_id=? ORDER BY version DESC LIMIT 1',
                                                (source_id,)).fetchone()
            assert classification is not None
            assert json.loads(classification[0])['source_snapshot_sha256'] == sha256(
                json_text(json.loads(row[0])).encode()).hexdigest()
        actual_facts = sum(resolved(e, f) in actual for e, f in flattened)
        assert (len(actual), actual_facts, len(unconnected), len(flattened) - actual_facts) == (33, 143, 2, 7)
        outside = [(e['company_id'], f['id'], resolved(e, f)) for e, f in flattened if resolved(e, f) in unconnected]
        old_outside = [(e['company_id'], f['id'], resolved(e, f)) for e in old['companies'] for f in e['facts']
                       if resolved(e, f) in unconnected]
        assert outside == old_outside and {x[0] for x in outside} == {'jp:8331', 'jp:9702'}
        availability = connection.execute('SELECT snapshot_sha256,first_saved_at,basis FROM record_availability WHERE entity_type=\'source\' AND entity_id=?',
                                          (derived['id'],)).fetchone()
        assert availability and availability[0] == sha256(json_text(derived).encode()).hexdigest()
        assert availability[1] is not None and availability[2] == 'trusted_insert'
        connection.rollback()
    assert digest(DB) == EXPECTED_DB
    assert all(digest(ROOT / path) == wanted for path, wanted in pins.items())
    clock = datetime.now(timezone.utc).isoformat()
    value.update(recorded_at=clock, previous_index=str(old_path.relative_to(ROOT)), previous_index_sha256=digest(old_path),
                 fact_count=150, company_source_entry_count=33, unique_company_count=21,
                 unique_derived_source_count=35, unique_original_company_source_pair_count=26)
    value['actual_research_source_connections'].update(
        actual_database_main_sha256=EXPECTED_DB, database_snapshot_recorded_at=clock, database_source_count=171,
        connected_derived_source_count=33, connected_fact_count=143,
        unconnected_derived_source_count=2, unconnected_fact_count=7)
    value['actual_research_source_connections']['connection_receipts'] += [str(actual_ref.relative_to(ROOT)), str(qual_ref.relative_to(ROOT))]
    value['layout_note'] = ('33 parent entries resolve to 35 unique derived sources, 150 facts across '
        '21 companies/26 company-original pairs. 33 sources/143 facts are stored and classified in '
        'the actual research ledger; two out-of-scope sources/7 facts remain file-only. No financial input adoption.')
    value['limitations'].append('1904 six p1 company amounts retain Q1 actuals versus annual issuer guidance, Japanese GAAP/consolidation and '
        'million-JPY truncation. May13 guidance was observed unchanged on Aug6; October-current guidance or later share/split/acquisition '
        'basis is not certified. The p7 thousand-JPY table is not mixed into these six facts. No new split-DPS fact or DDM series is indexed.')
    value['revision_basis'] = {'kind': 'append_1904_six_disclosed_facts', 'added_fact_count': 6,
        'added_parent_entry_count': 1, 'prior_32_parent_entries_and_144_facts_all_fields_exact': True,
        'existing_per_fact_source_artifact_overrides_preserved': True, 'financial_model_adoption': False}
    save(new_path, value)
    validation = {'recorded_at': clock, 'status': 'frozen_append_only_v29_pending_parent_review',
        'previous_index_sha256': digest(old_path), 'new_index_sha256': digest(new_path),
        'old_32_parent_entries_and_144_facts_all_fields_exact': True, 'added_parent_entries': 1, 'added_facts': 6,
        'unique_companies': 21, 'fact_count': 150, 'parent_entries': 33, 'unique_derived_sources': 35,
        'original_company_source_pairs': 26, 'actual_derived_sources': 33, 'actual_facts': 143,
        'outside_derived_sources': 2, 'outside_facts': 7, 'outside_entries_unchanged': outside,
        'new_facts_use_parent_derived_source_ID_not_raw_quote_source_ID_override': True,
        'all_existing_per_fact_artifact_source_overrides_preserved': True,
        'new_original_and_derived_all_object_match_actual': True, 'all33_stored_sources_have_current_snapshot_bound_classification': True,
        'new_derived_firstsave': availability[1], 'derived_retrieved_at': derived['retrieved_at'],
        'actual_database_main_sha256_before': EXPECTED_DB, 'actual_database_main_sha256_after': digest(DB),
        'actual_counts': counts, 'current_case_heads': 19, 'reviewed_sources': 113, 'all101_jobs_completed': True,
        'read_only_connection': 'sqlite mode=ro; PRAGMA query_only=ON; contextlib.closing; no Store',
        'source_and_qualitative_receipt_refs': [str(actual_ref.relative_to(ROOT)), str(qual_ref.relative_to(ROOT))],
        'old_input_file_pins': pins, 'old_inputs_unchanged': True,
        'new_DPS_facts_generated_or_indexed': 0, 'financial_inputs_adopted': False,
        'DB_writes': 0, 'GETs': 0, 'production_code_or_shared_doc_edits': 0}
    save(HERE / 'validation.json', validation)
    print(json.dumps({'new_index_sha256': digest(new_path), 'validation_sha256': digest(HERE / 'validation.json'),
                      'fact_count': 150, 'actual_facts': 143, 'DB_writes': 0}))


if __name__ == '__main__':
    main()
