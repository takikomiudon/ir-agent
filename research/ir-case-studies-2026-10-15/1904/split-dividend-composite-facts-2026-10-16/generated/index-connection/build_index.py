"""Append three accepted 1904 displays only after parent job104 completion.

Preparation of this script does not authorize execution. Require the parent's
post-completion DB SHA and qualitative-acceptance SHA explicitly. SQLite is
opened read-only/query_only, closed, and never passed to Store/Harness.
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
OLD = BASE / 'disclosed-fact-index-v29.json'
NEW = BASE / 'disclosed-fact-index-v30.json'
OLD_SHA = '105c79dc46d1543b56d35f32c447dadd1da407a481ba4ecf1f540d2aa0e5f234'
BUNDLE_SHA = '681c31d6a3274ba0f0b851f0f44e56caefe5b97a16a1462e981640f7ac5ffff8'
SOURCE_ID = 'disclosed-facts:b14c45dfc511d39e0057a06c1f014a00335b13b2858679660fa76319ec18e0c2'
ORIGINAL_ID = 'case-public:d5515999569e0a44d30c01701d683bb136b302cc8166a9374e625fe753b23d83'
ACTUAL = ROOT / 'research/ir-1926-1904-intake-2026-10-16/parent-acceptance.json'
ACTUAL_COMPLETION = ACTUAL.parent / 'actual-completion.json'
QUALITATIVE = HERE.parents[1] / 'qualitative-review/parent-acceptance.json'


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
    parser.add_argument('--expected-qualitative-acceptance-sha256', required=True)
    args = parser.parse_args()
    assert all(re.fullmatch(r'[0-9a-f]{64}', value) for value in vars(args).values())
    assert not any(path.exists() for path in (NEW, HERE / 'validation.json', HERE / 'README.md'))
    assert digest(OLD) == OLD_SHA
    assert digest(DB) == args.expected_db_sha256
    assert digest(QUALITATIVE) == args.expected_qualitative_acceptance_sha256
    accepted = load(QUALITATIVE)
    assert accepted['status'] == 'accepted_completed_composite_qualitative_review'
    assert accepted['actual_main_sha256'] == args.expected_db_sha256
    assert load(ACTUAL)['status'] == 'accepted_four_sources_two_completed_intakes'
    assert load(HERE.parent / 'parent-acceptance.json')['status'] == 'accepted_three_composite_displays_for_source_connection'
    bundle_path = HERE.parent / 'normalized-bundle.json'
    assert digest(bundle_path) == BUNDLE_SHA
    original, derived = load(bundle_path)['sources']
    assert (original['id'], derived['id']) == (ORIGINAL_ID, SOURCE_ID)
    assert derived['metadata']['normalization_version'] == 2
    facts = json.loads(derived['content'])['facts']
    assert len(facts) == 3 and [f['value'] for f in facts] == ['99.00', '24.75', '198.00']
    assert [f['scope']['share_basis'] for f in facts] == ['pre_split', 'post_split', 'issuer_pre_split_comparative_reference']
    assert [f['period']['dividend_record_date_as_explicitly_noted'] for f in facts] == ['2026-09-30', '2027-03-31', None]
    assert all(f['kind'] == 'issuer_guidance' and f['raw_value_format'] == 'jpy_yen_sen'
               and f['source_id'] == f['original_source_id'] == ORIGINAL_ID
               and f['period']['start_date'] is f['period']['end_date'] is None
               and f['scope']['accounting_basis'] is f['scope']['consolidation_scope'] is None
               and not f['scope']['investor_DDM_dividend_column_adopted']
               and not f['scope']['current_annual_DPS_adopted']
               and not f['scope']['simple_annual_addition_permitted']
               and f['scope']['current_annual_column_dash_not_numeric']
               and not f['financial_inputs_verified'] and not f['scope']['financial_input_adoption']
               for f in facts)
    old = load(OLD)
    assert len(old['companies']) == 33 and sum(len(e['facts']) for e in old['companies']) == old['fact_count'] == 150
    pins = dict(load(HERE.parent / 'generation.log')['immutable_existing_file_pins'])
    frozen_files = [p for p in HERE.parent.iterdir() if p.is_file()]
    frozen_files += [p for p in HERE.parents[1].iterdir() if p.is_file()]
    frozen_files += [OLD, ACTUAL, ACTUAL_COMPLETION, QUALITATIVE]
    pins.update({str(p.relative_to(ROOT)): digest(p) for p in frozen_files})
    value = deepcopy(old)
    # The raw normalized fact.source_id binds its original quote; it must not
    # override this enclosing derived source. Existing overrides stay untouched.
    value['companies'].append({
        'artifact': str(bundle_path.relative_to(ROOT)), 'artifact_sha256': BUNDLE_SHA,
        'company_id': 'jp:1904', 'contact_catalog_member': True,
        'derived_retrieved_at': derived['retrieved_at'],
        'derived_source_imported_into_actual_database': True,
        'facts': [{key: deepcopy(f[key]) for key in ('id', 'concept', 'kind', 'period', 'scope', 'unit', 'value')}
                  for f in facts],
        'original_retrieved_at': original['retrieved_at'],
        'original_source_id': ORIGINAL_ID, 'source_id': SOURCE_ID})
    assert value['companies'][:33] == old['companies']
    flattened = [(e, f) for e in value['companies'] for f in e['facts']]
    assert len({f['id'] for _, f in flattened}) == len(flattened) == 153
    sources = {resolved(e, f) for e, f in flattened}
    pairs = {(e['company_id'], f.get('original_source_id', e['original_source_id'])) for e, f in flattened}
    assert (len({e['company_id'] for e in value['companies']}), len(value['companies']), len(sources), len(pairs)) == (21, 34, 36, 27)
    with closing(sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('PRAGMA query_only=ON')
        assert connection.execute('PRAGMA query_only').fetchone()[0] == 1
        connection.execute('BEGIN')
        counts = {table: connection.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                  for table in ('sources', 'source_classifications', 'jobs', 'qualitative_case_versions')}
        assert counts == {'sources': 175, 'source_classifications': 174, 'jobs': 104, 'qualitative_case_versions': 40}
        assert connection.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'").fetchone()[0] == 104
        assert connection.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0] == 0
        heads = [json.loads(row[0]) for row in connection.execute('''SELECT a.data FROM qualitative_case_versions a JOIN
            (SELECT case_id,MAX(version) version FROM qualitative_case_versions GROUP BY case_id) b
            ON a.case_id=b.case_id AND a.version=b.version''')]
        assert len(heads) == 19 and sum(len(row['reviewed_sources']) for row in heads) == 114
        head1904 = next(row for row in heads if row['case_id'] == '1904-earnings-and-event-basis-monitor')
        assert head1904['reviewed_sources'][SOURCE_ID]['source_snapshot_sha256'] == sha256(json_text(derived).encode()).hexdigest()
        for source in (original, derived):
            row = connection.execute('SELECT company_id,data FROM sources WHERE id=?', (source['id'],)).fetchone()
            assert row and row[0] == 'jp:1904' and json.loads(row[1]) == source
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
        assert (len(actual), actual_facts, len(outside_sources), len(flattened) - actual_facts) == (34, 146, 2, 7)
        outside = [(e['company_id'], f['id'], resolved(e, f)) for e, f in flattened if resolved(e, f) in outside_sources]
        old_outside = [(e['company_id'], f['id'], resolved(e, f)) for e in old['companies'] for f in e['facts']
                       if resolved(e, f) in outside_sources]
        assert outside == old_outside and {item[0] for item in outside} == {'jp:8331', 'jp:9702'}
        availability = connection.execute("SELECT snapshot_sha256,first_saved_at,basis FROM record_availability WHERE entity_type='source' AND entity_id=?",
                                          (SOURCE_ID,)).fetchone()
        assert availability and availability[0] == sha256(json_text(derived).encode()).hexdigest()
        assert availability[1] is not None and availability[2] == 'trusted_insert'
        connection.rollback()
    assert digest(DB) == args.expected_db_sha256
    assert all(digest(ROOT / path) == expected for path, expected in pins.items())
    now = datetime.now(timezone.utc).isoformat()
    value.update(recorded_at=now, previous_index=str(OLD.relative_to(ROOT)), previous_index_sha256=OLD_SHA,
                 fact_count=153, company_source_entry_count=34, unique_company_count=21,
                 unique_derived_source_count=36, unique_original_company_source_pair_count=27)
    value['actual_research_source_connections'].update(
        actual_database_main_sha256=args.expected_db_sha256, database_snapshot_recorded_at=now, database_source_count=175,
        connected_derived_source_count=34, connected_fact_count=146, unconnected_derived_source_count=2, unconnected_fact_count=7)
    receipts = [str(path.relative_to(ROOT)) for path in (ACTUAL, ACTUAL_COMPLETION, QUALITATIVE)]
    value['actual_research_source_connections']['connection_receipts'] += receipts
    value['layout_note'] = ('34 parent entries resolve to 36 derived sources and 153 facts across 21 companies/27 company-original pairs. '
        '34 sources/146 facts are stored and classified; outside8331/9702 two sources/7 facts remain file-only. No financial adoption.')
    # Clarify the old six-fact entry's own limitation in this new version only.
    value['limitations'] = [note.replace('No new split-DPS fact or DDM series is indexed.',
        'Those six Q1/annual company amounts do not contain split-DPS facts or a DDM series.') for note in value['limitations']]
    value['limitations'].append('The distinct September10 notice entry adds only three direct composite yen/sen displays: interim pre-split, '
        'final post-split, and issuer annual pre-split comparative reference. Annual current dash is not zero; no addition, split adjustment, '
        'payment/execution confirmation, current annual DPS or DDM adoption. Fiscal boundaries, accounting and consolidation remain null. '
        'The original acquisition notice and August Q1 source are not merged into this entry.')
    value['revision_basis'] = {'kind': 'append_1904_three_split_dividend_composite_displays', 'added_fact_count': 3,
        'added_parent_entry_count': 1, 'prior_33_parent_entries_and_150_facts_all_fields_exact': True,
        'existing_per_fact_source_artifact_overrides_preserved': True, 'financial_model_adoption': False}
    validation = {'status': 'frozen_append_only_v30_pending_parent_review', 'recorded_at': now,
        'previous_index_sha256': OLD_SHA, 'old_33_parents_150_facts_all_fields_exact': True,
        'added_parent_entries': 1, 'added_facts': 3, 'unique_companies': 21, 'parent_entries': 34,
        'fact_count': 153, 'unique_derived_sources': 36, 'company_original_pairs': 27,
        'actual_derived_sources': 34, 'actual_facts': 146, 'outside_derived_sources': 2, 'outside_facts': 7,
        'outside_entries_unchanged': outside, 'new_original_and_derived_all_object_match_actual': True,
        'all34_stored_sources_have_current_snapshot_bound_classification': True,
        'new_facts_use_parent_derived_source_not_raw_original_override': True,
        'all_prior_per_fact_source_and_artifact_overrides_preserved': True,
        'original_source_id': ORIGINAL_ID, 'derived_source_id': SOURCE_ID,
        'original_retrieved_at': original['retrieved_at'], 'derived_retrieved_at': derived['retrieved_at'],
        'new_derived_firstsave': availability[1], 'scope_period_preserved': True,
        'fiscal_boundary_nulls_preserved': True, 'annual_reference_record_date_null_preserved': True,
        'annual_current_dash_not_zero_or_summed': True, 'DDM_and_financial_adoption_false': True,
        'actual_database_main_sha256_before': args.expected_db_sha256, 'actual_database_main_sha256_after': digest(DB),
        'actual_counts': counts, 'current_case_heads': 19, 'reviewed_sources': 114, 'all104_jobs_completed': True,
        'read_only_connection': 'sqlite mode=ro; PRAGMA query_only=ON; contextlib.closing; no Store',
        'source_and_qualitative_receipt_refs': receipts, 'qualitative_acceptance_sha256': digest(QUALITATIVE),
        'old_input_file_pins': pins, 'old_inputs_unchanged': True, 'financial_inputs_adopted': False,
        'DB_writes': 0, 'GETs': 0, 'production_code_or_shared_doc_edits': 0}
    save(NEW, value)
    validation['new_index_sha256'] = digest(NEW)
    save(HERE / 'validation.json', validation)
    (HERE / 'README.md').write_text('# Disclosed fact index v30\n\n'
        '1904分割通知の3表示を独立1parentとして追加。旧v29全33parent/150factの全fieldを保持した。'
        '中間pre/期末post/会社年間参考・年度null・annualdash非数値/DDM非採用を維持。Q1や取得通知と混合しない。\n\n'
        '21社153fact/34parent/36派生/27会社原典pair。実接続34派生146fact、旧8331/9702の外部2派生7factは不変。'
        '元sourceを指すraw fact.source_idを派生overrideへ転記せず、旧個別overrideは保持した。\n\n'
        '指定SHAとjob104完了受入を照合後、mode=ro/query_only/contextlib.closingで実DB175source/174分類/'
        '104全job完了・pending/leased0・19heads40versions114reads、原2source全objectと34分類snapshotを確認。'
        'DB書込み・GET・金融採用0。\n\n'
        + '\n'.join('- [' + str(path.relative_to(ROOT)) + '](' + str(path) + ')' for path in (ACTUAL, ACTUAL_COMPLETION, QUALITATIVE))
        + '\n\n実DBのfirstsaveと派生処理retrievedはvalidationに分けて記録。root最終レビュー待ち。\n', encoding='utf-8')
    assert digest(DB) == args.expected_db_sha256
    assert all(digest(ROOT / path) == expected for path, expected in pins.items())
    print(json.dumps({'new_index_sha256': digest(NEW), 'validation_sha256': digest(HERE / 'validation.json'),
                      'fact_count': 153, 'actual_facts': 146, 'DB_writes': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
