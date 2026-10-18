"""Finite append-only v32 build, actual SQLite read-only; no new extraction."""
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source
from ir_agent.models import json_text

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = ROOT / 'research/ir-case-studies-2026-10-15'
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED_DB = '446078451a45181c76ae6e8dad01ce5483079e69d5f419b879500630d68f8591'
OLD = BASE / 'disclosed-fact-index-v31.json'
NEW = BASE / 'disclosed-fact-index-v32.json'
OLD_SHA = 'a8e962de6cc25e2f10b0108816f08eff3f7007a03a71d5e1978d65cdc2211424'
BUNDLE_SHA = 'c09b24ecf30c52420b4ec893219c2fbc7ae51fdd7e63d3ada4e9a2949c3d3f56'
NORMALIZER_SHA = 'd434b41cfa19568d0cef1a2e6710365f447012d75a4b07ca950cc62b6bd9db51'
ORIGINAL_ID = 'case-public:33917957734a3f4b705072164e8e3526e23fec79c9f1b2265a7131a17e6253b1'
DERIVED_ID = 'disclosed-facts:e691939950fbeb9823ff565d34da55861f18a761249cb755efd3855193bfa91e'
INTAKE = ROOT / 'research/ir-1963-initial-with-facts-intake-2026-10-16'


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
    assert not any(path.exists() for path in (NEW, HERE / 'validation.json', HERE / 'README.md', HERE / 'manifest.json'))
    assert digest(DB) == EXPECTED_DB and digest(OLD) == OLD_SHA
    assert digest(ROOT / 'src/ir_agent/disclosed_facts.py') == NORMALIZER_SHA
    bundle_path = HERE.parent / 'normalized-bundle.json'
    assert digest(bundle_path) == BUNDLE_SHA
    original, derived = load(bundle_path)['sources']
    assert (original['id'], derived['id']) == (ORIGINAL_ID, DERIVED_ID)
    assert load(HERE.parent / 'parent-acceptance.json')['derived_source_id'] == DERIVED_ID
    actual_accepted = load(INTAKE / 'parent-acceptance.json')
    assert actual_accepted['status'] == 'accepted_actual_six_source_intake_completed'
    assert actual_accepted['DB_main_sha256'] == EXPECTED_DB
    facts = json.loads(derived['content'])['facts']
    assert len(facts) == 9 and [fact['value'] for fact in facts] == [
        '159299000000', '12355000000', '11617000000', '670000000000', '40000000000',
        '46000000000', '48.03', '190.25', '52.00']
    assert all(fact['source_id'] == fact['original_source_id'] == ORIGINAL_ID
               and not fact['financial_inputs_verified'] and not fact['scope']['model_or_policy_adopted']
               and not fact['scope']['October_current_guidance_or_share_basis_verified'] for fact in facts)
    dps = facts[-1]
    assert dps['period']['start_date'] is dps['period']['end_date'] is dps['period']['dividend_record_date'] is None
    assert dps['scope']['accounting_basis'] is dps['scope']['consolidation_scope'] is None
    assert not dps['scope']['investor_DDM_dividend_column_adopted']
    request = load(HERE.parent / 'normalization-input.json')
    assert request['source'] == original
    assert normalize_disclosed_facts(request, now=derived['retrieved_at']) == load(bundle_path)
    replay = reproduce_disclosed_fact_source(derived, {ORIGINAL_ID: original})
    assert replay['status'] == 'reproduced' and replay['original_content_sha256_status'] == 'matched'
    assert replay['original_snapshot_sha256_status'] == 'matched_supplied_snapshot'
    old = load(OLD)
    assert len(old['companies']) == 35 and sum(len(entry['facts']) for entry in old['companies']) == old['fact_count'] == 162
    receipts = [INTAKE / name for name in ('parent-acceptance.json', 'actual-completion.json', 'source-firstsave.json')]
    frozen_files = [path for path in HERE.parent.rglob('*') if path.is_file()
                    and HERE not in path.parents and '__pycache__' not in path.parts]
    frozen_files += [OLD, INTAKE / 'source-bundle.json', INTAKE / 'classification-requests.json', INTAKE / 'input-pins.json', *receipts,
                     ROOT / 'src/ir_agent/disclosed_facts.py', ROOT / 'src/ir_agent/models.py',
                     ROOT / 'src/ir_agent/adapters/common.py']
    notes = HERE.parents[1] / 'statement-note-followup-2026-10-16'
    frozen_files += [notes / name for name in ('parent-acceptance.json', 'handoff.json', 'source-quotes.json')]
    pins = {str(path.relative_to(ROOT)): digest(path) for path in frozen_files}
    pins.update(load(INTAKE / 'input-pins.json'))
    value = deepcopy(old)
    value['companies'].append({'artifact': str(bundle_path.relative_to(ROOT)), 'artifact_sha256': BUNDLE_SHA,
        'company_id': 'jp:1963', 'contact_catalog_member': True, 'derived_retrieved_at': derived['retrieved_at'],
        'derived_source_imported_into_actual_database': True,
        # fact.source_id in the producer output cites the primary quote source.
        # Omit it here so the new entry resolves to its enclosing derived source.
        'facts': [{key: deepcopy(fact[key]) for key in ('id', 'concept', 'kind', 'period', 'scope', 'unit', 'value')}
                  for fact in facts], 'original_retrieved_at': original['retrieved_at'],
        'original_source_id': ORIGINAL_ID, 'source_id': DERIVED_ID})
    assert value['companies'][:35] == old['companies']
    flattened = [(entry, fact) for entry in value['companies'] for fact in entry['facts']]
    assert len({fact['id'] for _, fact in flattened}) == len(flattened) == 171
    sources = {resolved(entry, fact) for entry, fact in flattened}
    pairs = {(entry['company_id'], fact.get('original_source_id', entry['original_source_id'])) for entry, fact in flattened}
    assert (len({entry['company_id'] for entry in value['companies']}), len(value['companies']), len(sources), len(pairs)) == (23, 36, 38, 29)
    intake_sources = load(INTAKE / 'source-bundle.json')['sources']
    desired_classes = {item['source_id']: item for item in load(INTAKE / 'classification-requests.json')['jp:1963']['classifications']}
    saved_availability = {row['source_id']: row for row in load(INTAKE / 'source-firstsave.json')['sources']}
    assert len(intake_sources) == 6
    with closing(sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('PRAGMA query_only=ON')
        assert connection.execute('PRAGMA query_only').fetchone()[0] == 1
        connection.execute('BEGIN')
        counts = {table: connection.execute('SELECT count(*) FROM ' + table).fetchone()[0] for table in (
            'sources', 'record_availability', 'source_classifications', 'jobs', 'job_attempts', 'job_attempt_events',
            'job_request_receipts', 'qualitative_case_versions')}
        assert counts == {'sources': 186, 'record_availability': 186, 'source_classifications': 185,
            'jobs': 106, 'job_attempts': 103, 'job_attempt_events': 206, 'job_request_receipts': 103, 'qualitative_case_versions': 41}
        assert connection.execute("SELECT count(*) FROM jobs WHERE status='completed'").fetchone()[0] == 106
        assert connection.execute("SELECT count(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0] == 0
        heads = [json.loads(row[0]) for row in connection.execute('''SELECT a.data FROM qualitative_case_versions a JOIN
            (SELECT case_id,max(version) version FROM qualitative_case_versions GROUP BY case_id)b
            ON a.case_id=b.case_id AND a.version=b.version''')]
        assert len(heads) == 20 and sum(len(row['reviewed_sources']) for row in heads) == 119
        assert all(row['company_id'] != 'jp:1963' for row in heads)
        for source in intake_sources:
            row = connection.execute('SELECT company_id,data FROM sources WHERE id=?', (source['id'],)).fetchone()
            assert row and row[0] == 'jp:1963' and json.loads(row[1]) == source
            native_sha = sha256(json_text(source).encode()).hexdigest()
            availability = connection.execute("SELECT snapshot_sha256,first_saved_at,presence_observed_at,basis FROM record_availability WHERE entity_type='source' AND entity_id=?",
                                               (source['id'],)).fetchone()
            receipt = saved_availability[source['id']]
            assert tuple(availability) == (receipt['source_snapshot_sha256'], receipt['first_saved_at'], receipt['presence_observed_at'], receipt['basis'])
            assert availability[0] == native_sha and availability[3] == 'trusted_insert'
            current = json.loads(connection.execute('SELECT data FROM source_classifications WHERE source_id=? ORDER BY version DESC LIMIT 1',
                                                    (source['id'],)).fetchone()[0])
            assert current['source_snapshot_sha256'] == native_sha
            assert all(current[key] == desired_classes[source['id']][key] for key in ('kind', 'financial_content', 'basis_quote', 'rationale'))
        assert connection.execute('SELECT count(*) FROM sources WHERE company_id=?', ('jp:1963',)).fetchone()[0] == 6
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
        actual_facts = sum(resolved(entry, fact) in actual for entry, fact in flattened)
        assert (len(actual), actual_facts, len(outside_sources), len(flattened) - actual_facts) == (36, 164, 2, 7)
        outside = [(entry['company_id'], fact['id'], resolved(entry, fact)) for entry, fact in flattened if resolved(entry, fact) in outside_sources]
        assert outside == [(entry['company_id'], fact['id'], resolved(entry, fact)) for entry in old['companies'] for fact in entry['facts']
                           if resolved(entry, fact) in outside_sources]
        assert {row[0] for row in outside} == {'jp:8331', 'jp:9702'}
        connection.rollback()
    assert digest(DB) == EXPECTED_DB and all(digest(ROOT / path) == wanted for path, wanted in pins.items())
    now = datetime.now(timezone.utc).isoformat()
    value.update(recorded_at=now, previous_index=str(OLD.relative_to(ROOT)), previous_index_sha256=OLD_SHA,
        fact_count=171, company_source_entry_count=36, unique_company_count=23,
        unique_derived_source_count=38, unique_original_company_source_pair_count=29)
    value['actual_research_source_connections'].update(actual_database_main_sha256=EXPECTED_DB,
        database_snapshot_recorded_at=now, database_source_count=186, connected_derived_source_count=36,
        connected_fact_count=164, unconnected_derived_source_count=2, unconnected_fact_count=7)
    value['actual_research_source_connections']['connection_receipts'] += [str(path.relative_to(ROOT)) for path in receipts]
    value['layout_note'] = ('36 parents resolve to 38 derived sources and 171 facts across 23 companies/29 company-original pairs. '
        '36 sources/164 facts are stored and classified; outside8331/9702 two sources/7 facts remain file-only. No financial adoption.')
    value['limitations'].append('1963 nine direct issuer tokens retain Q1 actual amounts/basic EPS and dated Aug7 full-year company forecasts/EPS/annual total DPS. '
        'Basic48.03 differs from diluted47.96; forecast190.25 is not current EPS. DPS fiscal boundaries/record date/accounting/consolidation remain null. '
        'New consolidation, quarter-specific accounting, FX nonoperating/tax/NCI and historical share scope remain reviewer-declared. '
        'Later p9–12 reading is a dated file-only supplement to the same original, not another source/fact or adopted financial input; '
        'unread-at-extraction notes are historical scope, not current assertions of absent public explanations.')
    value['revision_basis'] = {'kind': 'append_1963_preferred_nine_disclosed_facts', 'added_fact_count': 9,
        'added_parent_entry_count': 1, 'prior_35_parent_entries_and_162_facts_all_fields_exact': True,
        'existing_per_fact_source_artifact_overrides_preserved': True, 'financial_model_adoption': False}
    save(NEW, value)
    validation = {'status': 'frozen_append_only_v32_pending_parent_review', 'recorded_at': now,
        'previous_index_sha256': OLD_SHA, 'new_index_sha256': digest(NEW),
        'old_35_parent_objects_162facts_all_fields_exact': True, 'added_parent_entries': 1, 'added_facts': 9,
        'unique_companies': 23, 'parent_entries': 36, 'fact_count': 171, 'unique_derived_sources': 38,
        'company_original_pairs': 29, 'actual_derived_sources': 36, 'actual_facts': 164,
        'outside_derived_sources': 2, 'outside_facts': 7, 'outside_entries_unchanged': outside,
        'new_entry_projected_fields_exact': True, 'no_raw_original_source_ID_index_override': True,
        'old_per_fact_artifact_and_source_overrides_unchanged': True,
        'original_source_id': ORIGINAL_ID, 'derived_source_id': DERIVED_ID,
        'same_now_whole_bundle_ID_replay_exact': True, 'reproduction': replay,
        'new_primary_normalization_or_new_numeric_facts': 0,
        'DPS_nulls_basic_vs_diluted_FYEPS_dated_issuer_scope_preserved': True,
        'p9_to_p12_additional_context_kept_file_only_not_indexed_as_source_or_facts': True,
        'six_whole_actual_sources_and_current_classifications_exact': True,
        'six_actual_availability_receipts_match_saved_firstsave': saved_availability,
        'original_retrieved_at': original['retrieved_at'], 'derived_retrieved_at': derived['retrieved_at'],
        'new_derived_actual_firstsave': saved_availability[DERIVED_ID]['first_saved_at'],
        'current_case_heads': 20, 'case_versions': 41, 'reviewed_sources': 119,
        '1963_native_case_not_registered_in_this_snapshot': True, 'actual_counts': counts,
        'all106_jobs_completed_pending_leased0': True, 'actual_DB_SHA_before': EXPECTED_DB, 'actual_DB_SHA_after': digest(DB),
        'read_only_connection': 'sqlite mode=ro/query_only/contextlib.closing; no Store',
        'receipt_refs': [str(path.relative_to(ROOT)) for path in receipts],
        'normalizer_SHA_unchanged': NORMALIZER_SHA, 'old_input_pins': pins, 'old_pins_unchanged': True,
        'DB_writes': 0, 'GETs': 0, 'financial_inputs_adopted': False, 'production_code_or_shared_doc_edits': 0}
    save(HERE / 'validation.json', validation)
    (HERE / 'README.md').write_text('# Disclosed fact index v32\n\n'
        '1963の受入済みe691…派生9表示だけを1parent追加した。旧v31全35parent/162fact全objectを保持。'
        '23社171fact/36parent/38派生/29会社原典pair、実36派生164fact。外部8331/9702の2派生7factは不変。'
        'raw fact.source_idは原文bindingなのでindexoverrideへ転記せず、旧個別overrideを保持した。\n\n'
        'Q1金額/基本EPS48.03（潜在調整後47.96とは別）、当時FY会社予想/FYEPS190.25/DPS52.00を区別。'
        'DPS年度両端/基準日/会計/連結null、issuer-as-of/原scopeを全保持。p9–12追加読解は同原典のfile-only補足のままで、'
        '新source/factや現在予想/正常利益/金融採用へ移していない。\n\n'
        'RO/query_only/closingで186source/185分類/106全job完了、103attempt206event103receipt、'
        '20case41版119既読、pending/leased0を確認。原6source全object・分類snapshot・firstsave receiptを照合した。'
        'この照合時点で1963native caseは未登録。新派生処理時刻とactual firstsaveをvalidationで分けた。\n\n'
        'd434…normalizer不変。同now全文bundle/ID replayと既存reproducer一致を確認、新primary生成0。'
        'GET/実DB書込み/production/shared/旧v31編集/金融入力採用0、rootレビュー待ち。\n\n'
        + '\n'.join('- [' + str(path.relative_to(ROOT)) + '](' + str(path) + ')' for path in receipts) + '\n', encoding='utf-8')
    assert digest(DB) == EXPECTED_DB and all(digest(ROOT / path) == wanted for path, wanted in pins.items())
    save(HERE / 'manifest.json', {'status': validation['status'], 'recorded_at': now,
        'files': {path.name: {'sha256': digest(path), 'bytes': path.stat().st_size} for path in sorted(HERE.iterdir()) if path.is_file()},
        'new_index_path': str(NEW.relative_to(ROOT)), 'new_index_sha256': digest(NEW), 'old_input_pins': pins,
        'DB_main_SHA_unchanged': EXPECTED_DB, 'financial_adoption': False, 'DB_writes': 0, 'GETs': 0})
    print(json.dumps({'new_index_sha256': digest(NEW), 'validation_sha256': digest(HERE / 'validation.json'),
        'manifest_sha256': digest(HERE / 'manifest.json'), 'facts': 171, 'actual_facts': 164, 'DB_writes': 0}))


if __name__ == '__main__':
    main()
