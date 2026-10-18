"""Prepare v31 from the accepted 1950 reference-only representation.

Run only after the parent supplies post-native-registration DB SHA and acceptance
path/status/SHA. This script never writes SQLite, invokes Store or fetches data.
"""
import argparse
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3

from ir_agent.models import json_text

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
BASE = ROOT / 'research/ir-case-studies-2026-10-15'
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
OLD = BASE / 'disclosed-fact-index-v30.json'
NEW = BASE / 'disclosed-fact-index-v31.json'
OLD_SHA = '04b40b3be42315b740390d0d949c26f4dd1435f3d62a1ba90299054456b5605f'
BUNDLE_SHA = 'e29d7e9ae289c849442c64918f9c73672c1d8a9ceaae510d12cbbeb7d377769f'
DERIVED_ID = 'disclosed-facts:46cbe924b4dd80930b76e0b5ecacb92b35bef6762088d189d5187c0a9089f91c'
ORIGINAL_ID = 'case-public:023e20b23a02e4a4d9e99db8f8aa9d146da5326ce5a8808fe62aa782479e58e1'
OLD_ALTERNATIVE_ID = 'disclosed-facts:85fe54702c90b08266037cf1ec9f92f0541279c0bb546b533e220591a4c6ccea'
INTAKE = ROOT / 'research/ir-1950-initial-with-facts-intake-2026-10-16'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(path, value):
    with path.open('x', encoding='utf-8') as output:
        output.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def resolved(entry, fact):
    return fact.get('source_id', entry['source_id'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-db-sha256', required=True)
    parser.add_argument('--native-acceptance-file', required=True)
    parser.add_argument('--native-acceptance-status', required=True)
    parser.add_argument('--native-acceptance-sha256', required=True)
    parser.add_argument('--contact-catalog-member', action='store_true', default=None,
                        help='Only supply when the parent has confirmed catalog membership; otherwise omit this optional index field.')
    args = parser.parse_args()
    assert all(re.fullmatch('[0-9a-f]{64}', value) for value in
               (args.expected_db_sha256, args.native_acceptance_sha256))
    native_path = (ROOT / args.native_acceptance_file).resolve()
    assert ROOT / 'research' in native_path.parents
    assert digest(native_path) == args.native_acceptance_sha256
    native_accepted = load(native_path)
    assert args.native_acceptance_status.startswith('accepted_')
    assert native_accepted['status'] == args.native_acceptance_status
    if 'actual_main_sha256' in native_accepted:
        assert native_accepted['actual_main_sha256'] == args.expected_db_sha256
    assert digest(DB) == args.expected_db_sha256
    assert not any(path.exists() for path in (NEW, HERE / 'validation.json', HERE / 'README.md'))
    assert digest(OLD) == OLD_SHA
    assert load(INTAKE / 'parent-acceptance.json')['status'] == 'accepted_five_sources_one_completed_initial_intake'
    assert load(HERE.parent / 'parent-acceptance.json')['status'] == 'accepted_preferred_nine_fact_reference_representation_for_initial_connection'
    bundle_path = HERE.parent / 'normalized-bundle.json'
    assert digest(bundle_path) == BUNDLE_SHA
    original, derived = load(bundle_path)['sources']
    assert (original['id'], derived['id']) == (ORIGINAL_ID, DERIVED_ID)
    facts = json.loads(derived['content'])['facts']
    assert len(facts) == 9 and derived['metadata']['normalization_version'] == 1
    assert [f['value'] for f in facts] == ['34971000000', '1081000000', '1443000000', '242310000000',
        '23890000000', '18470000000', '24.73', '316.42', '127.00']
    assert all(f['source_id'] == f['original_source_id'] == ORIGINAL_ID
               and not f['financial_inputs_verified'] and not f['scope']['financial_meaning_adopted']
               and not f['scope']['model_or_policy_adopted'] for f in facts)
    dps = facts[-1]
    assert dps['period']['start_date'] is dps['period']['end_date'] is dps['period']['dividend_record_date'] is None
    assert dps['scope']['accounting_basis'] is dps['scope']['consolidation_scope'] is None
    assert dps['location']['column'] == '年間配当金・合計'
    assert not dps['scope']['investor_DDM_dividend_column_adopted']
    assert all(f['scope']['previous_forecast_announcement_date'] is None for f in facts if f['kind'] == 'issuer_guidance')
    for fact in facts:
        for quote_id, ref in fact['scope']['source_context_references'].items():
            assert 'basis_quote' not in ref
            assert digest(ROOT / ref['path']) == ref['file_sha256']
            quote = next(q for q in load(ROOT / ref['path']) if q['id'] == quote_id)
            assert quote['quote'] == original['content'][ref['character_start']:ref['character_end']]
            assert quote['pdf_physical_page'] == ref['pdf_page']
    old = load(OLD)
    assert len(old['companies']) == 34 and sum(len(e['facts']) for e in old['companies']) == old['fact_count'] == 153
    intake_sources = load(INTAKE / 'source-bundle.json')['sources']
    assert len(intake_sources) == 5 and {s['id'] for s in intake_sources} >= {ORIGINAL_ID, DERIVED_ID}
    assert OLD_ALTERNATIVE_ID not in {s['id'] for s in intake_sources}
    receipts = [INTAKE / name for name in ('parent-acceptance.json', 'actual-completion.json', 'source-firstsave.json')]
    receipts.append(native_path)
    pins = dict(load(HERE.parent / 'generation.log')['old_file_pins'])
    frozen_files = [path for path in HERE.parent.iterdir() if path.is_file()] + [OLD, INTAKE / 'source-bundle.json', *receipts]
    pins.update({str(path.relative_to(ROOT)): digest(path) for path in frozen_files})
    value = deepcopy(old)
    entry = {'artifact': str(bundle_path.relative_to(ROOT)), 'artifact_sha256': BUNDLE_SHA,
        'company_id': 'jp:1950', 'derived_retrieved_at': derived['retrieved_at'],
        'derived_source_imported_into_actual_database': True,
        # Raw fact.source_id is the original quote binding, not an index override.
        'facts': [{key: deepcopy(fact[key]) for key in ('id', 'concept', 'kind', 'period', 'scope', 'unit', 'value')}
                  for fact in facts],
        'original_retrieved_at': original['retrieved_at'], 'original_source_id': ORIGINAL_ID, 'source_id': DERIVED_ID}
    if args.contact_catalog_member is True:
        entry['contact_catalog_member'] = True
    value['companies'].append(entry)
    assert value['companies'][:34] == old['companies']
    flattened = [(e, f) for e in value['companies'] for f in e['facts']]
    assert len({f['id'] for _, f in flattened}) == len(flattened) == 162
    sources = {resolved(e, f) for e, f in flattened}
    pairs = {(e['company_id'], f.get('original_source_id', e['original_source_id'])) for e, f in flattened}
    assert (len({e['company_id'] for e in value['companies']}), len(value['companies']), len(sources), len(pairs)) == (22, 35, 37, 28)
    assert OLD_ALTERNATIVE_ID not in sources
    with closing(sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('PRAGMA query_only=ON')
        assert connection.execute('PRAGMA query_only').fetchone()[0] == 1
        connection.execute('BEGIN')
        counts = {table: connection.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                  for table in ('sources', 'source_classifications', 'jobs', 'qualitative_case_versions')}
        assert counts == {'sources': 180, 'source_classifications': 179, 'jobs': 105, 'qualitative_case_versions': 41}
        assert connection.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'").fetchone()[0] == 105
        assert connection.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0] == 0
        head_rows = connection.execute('''SELECT a.version,a.data FROM qualitative_case_versions a JOIN
            (SELECT case_id,MAX(version) version FROM qualitative_case_versions GROUP BY case_id) b
            ON a.case_id=b.case_id AND a.version=b.version''').fetchall()
        heads = [json.loads(row[1]) for row in head_rows]
        assert len(heads) == 20 and sum(len(row['reviewed_sources']) for row in heads) == 119
        head1950 = next(row for row in heads if row['company_id'] == 'jp:1950')
        assert [version for version, data in head_rows if json.loads(data)['company_id'] == 'jp:1950'] == [1]
        assert set(head1950['reviewed_sources']) == {source['id'] for source in intake_sources}
        for source in intake_sources:
            row = connection.execute('SELECT company_id,data FROM sources WHERE id=?', (source['id'],)).fetchone()
            assert row and row[0] == 'jp:1950' and json.loads(row[1]) == source
            assert head1950['reviewed_sources'][source['id']]['source_snapshot_sha256'] == sha256(json_text(source).encode()).hexdigest()
        assert connection.execute('SELECT 1 FROM sources WHERE id=?', (OLD_ALTERNATIVE_ID,)).fetchone() is None
        actual, outside_sources = set(), set()
        for source_id in sources:
            row = connection.execute('SELECT data FROM sources WHERE id=?', (source_id,)).fetchone()
            if row is None:
                outside_sources.add(source_id)
                continue
            actual.add(source_id)
            classification = connection.execute('SELECT data FROM source_classifications WHERE source_id=? ORDER BY version DESC LIMIT 1',
                                                (source_id,)).fetchone()
            assert classification and json.loads(classification[0])['source_snapshot_sha256'] == sha256(json_text(json.loads(row[0])).encode()).hexdigest()
        actual_facts = sum(resolved(e, f) in actual for e, f in flattened)
        assert (len(actual), actual_facts, len(outside_sources), len(flattened) - actual_facts) == (35, 155, 2, 7)
        outside = [(e['company_id'], f['id'], resolved(e, f)) for e, f in flattened if resolved(e, f) in outside_sources]
        assert outside == [(e['company_id'], f['id'], resolved(e, f)) for e in old['companies'] for f in e['facts']
                           if resolved(e, f) in outside_sources]
        assert {item[0] for item in outside} == {'jp:8331', 'jp:9702'}
        availability = connection.execute("SELECT snapshot_sha256,first_saved_at,basis FROM record_availability WHERE entity_type='source' AND entity_id=?",
                                          (DERIVED_ID,)).fetchone()
        assert availability and availability[0] == sha256(json_text(derived).encode()).hexdigest()
        assert availability[1] is not None and availability[2] == 'trusted_insert'
        connection.rollback()
    assert digest(DB) == args.expected_db_sha256
    assert all(digest(ROOT / path) == expected for path, expected in pins.items())
    now = datetime.now(timezone.utc).isoformat()
    value.update(recorded_at=now, previous_index=str(OLD.relative_to(ROOT)), previous_index_sha256=OLD_SHA,
        fact_count=162, company_source_entry_count=35, unique_company_count=22,
        unique_derived_source_count=37, unique_original_company_source_pair_count=28)
    value['actual_research_source_connections'].update(actual_database_main_sha256=args.expected_db_sha256,
        database_snapshot_recorded_at=now, database_source_count=180, connected_derived_source_count=35,
        connected_fact_count=155, unconnected_derived_source_count=2, unconnected_fact_count=7)
    value['actual_research_source_connections']['connection_receipts'] += [str(path.relative_to(ROOT)) for path in receipts]
    value['layout_note'] = ('35 parents resolve to 37 derived sources and 162 facts across 22 companies/28 company-original pairs. '
        '35 sources/155 facts are stored and classified; outside8331/9702 two sources/7 facts remain file-only. No financial adoption.')
    value['limitations'].append('1950 nine direct p1 tokens preserve Q1 actuals and July31 issuer full-year forecasts, EPS and annual total DPS. '
        'Million-JPY truncation and original decimal per-share displays are preserved. Dividend fiscal dates/record date/accounting/consolidation '
        'remain null; forecast unchanged has no invented prior release date. Historical shares are not current EPS denominators. '
        'Seasonality and operating/ordinary/special/tax/NCI distinctions remain referenced context, not normalized profit or DDM adoption. '
        'Only the accepted context-reference-only representation is indexed; the old full-context alternative is not an additional disclosure.')
    value['revision_basis'] = {'kind': 'append_1950_preferred_nine_disclosed_facts', 'added_fact_count': 9,
        'added_parent_entry_count': 1, 'prior_34_parent_entries_and_153_facts_all_fields_exact': True,
        'old_full_context_alternative_not_indexed': True,
        'existing_per_fact_source_artifact_overrides_preserved': True, 'financial_model_adoption': False}
    validation = {'status': 'frozen_append_only_v31_pending_parent_review', 'recorded_at': now,
        'previous_index_sha256': OLD_SHA, 'old_34_parents_153_facts_all_fields_exact': True,
        'added_parent_entries': 1, 'added_facts': 9, 'unique_companies': 22, 'parent_entries': 35,
        'fact_count': 162, 'unique_derived_sources': 37, 'company_original_pairs': 28,
        'actual_derived_sources': 35, 'actual_facts': 155, 'outside_derived_sources': 2, 'outside_facts': 7,
        'outside_entries_unchanged': outside, 'new_five_intake_sources_all_object_match_actual': True,
        'all35_stored_sources_have_current_snapshot_bound_classification': True,
        'new_facts_use_enclosing_derived_source_not_raw_original_override': True,
        'all_previous_per_fact_source_artifact_overrides_preserved': True,
        'preferred_derived_source_id': DERIVED_ID, 'old_full_context_alternative_not_indexed_or_imported': True,
        'new_derived_firstsave': availability[1], 'original_retrieved_at': original['retrieved_at'],
        'derived_retrieved_at': derived['retrieved_at'], 'DPS_nulls_and_all_scope_references_unchanged': True,
        'context_reference_checks_are_local_evidence_checks_not_normalizer_meaning_authentication': True,
        'actual_database_main_sha256_before': args.expected_db_sha256, 'actual_database_main_sha256_after': digest(DB),
        'actual_counts': counts, 'current_case_heads': 20, 'reviewed_sources': 119, 'all105_jobs_completed': True,
        'new_native_bootstrap_five_IDs_and_SHAs_match_actual': True,
        'read_only_connection': 'sqlite mode=ro; PRAGMA query_only=ON; contextlib.closing; no Store',
        'source_and_native_receipt_refs': [str(path.relative_to(ROOT)) for path in receipts],
        'native_acceptance_sha256': digest(native_path), 'old_input_file_pins': pins, 'old_inputs_unchanged': True,
        'contact_catalog_member_field_confirmed_by_parent': args.contact_catalog_member,
        'financial_inputs_adopted': False, 'DB_writes': 0, 'GETs': 0, 'production_code_or_shared_doc_edits': 0}
    save(NEW, value)
    validation['new_index_sha256'] = digest(NEW)
    save(HERE / 'validation.json', validation)
    (HERE / 'README.md').write_text('# Disclosed fact index v31\n\n'
        '1950推奨参照版の9表示値だけを1parent追加。旧v30全34parent/153factの全fieldを保持し、'
        '旧full-context代替版を登録・索引化していない。22社162fact/35parent/37派生/28会社原典pair、'
        '実35派生155fact・旧8331/9702外部2派生7factは不変。\n\n'
        'Q1/当時FY予想/EPS/DPSと単位・利益・季節性文脈refを維持。DPS年度両端/recorddate/会計/連結null、'
        '原source-IDを派生overrideへ転記せず旧個別override保持。参照照合を金融意味の自動認証とはしない。\n\n'
        '指定native受入のSHAと実DB SHAを確認し、mode=ro/query_only/closingで180source/179分類/105全job完了、'
        'pending/leased0、20heads41versions119reads、新bootstrap5source全object/既読SHA、35派生分類を確認した。'
        '実DB firstsaveと派生処理時刻はvalidationで区別。DB書込み/GET/金融採用0、root最終レビュー待ち。\n\n'
        + '\n'.join('- [' + str(path.relative_to(ROOT)) + '](' + str(path) + ')' for path in receipts) + '\n', encoding='utf-8')
    assert digest(DB) == args.expected_db_sha256
    assert all(digest(ROOT / path) == expected for path, expected in pins.items())
    print(json.dumps({'new_index_sha256': digest(NEW), 'validation_sha256': digest(HERE / 'validation.json'),
                      'fact_count': 162, 'actual_facts': 155, 'DB_writes': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
