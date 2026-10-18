"""Finite append-only v34; actual SQLite RO only, no Store/normalizer/network."""
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = ROOT / 'research/ir-case-studies-2026-10-15'
OLD = BASE / 'disclosed-fact-index-v33.json'
NEW = BASE / 'disclosed-fact-index-v34.json'
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED_DB = '60115ab17fd6fbb39d56faf46b1cb8509796552a2756480fffd2294d2ffa5b6d'
INTAKE = ROOT / 'research/ir-2163-initial-with-facts-intake-2026-10-16'
FIRSTSAVE = '2026-10-16T04:48:38.513557+00:00'
BUNDLE_SHA = 'fbbeda004f81a4f0b213239379b789c2a8c1da4fc7367ad8d56595e0b8af2dcd'


def load(path):
    return json.loads(path.read_bytes())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def native_sha(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as out:
        out.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def resolved(entry, fact):
    return fact.get('source_id', entry['source_id'])


def main():
    assert not NEW.exists() and not (HERE / 'validation.json').exists()
    pins = load(HERE / 'input-pins.json')
    assert all(digest(ROOT / path) == pin for path, pin in pins.items())
    assert digest(DB) == EXPECTED_DB
    assert digest(OLD) == '1b87d6d8efbcd48ae4938daf4c70affddd6c514a43a794c315f6f469d1f12605'
    old = load(OLD)
    assert len(old['companies']) == 37 and old['fact_count'] == 180
    assert sum(len(e['facts']) for e in old['companies']) == 180
    bundle_path = HERE.parent / 'normalized-bundle.json'
    assert digest(bundle_path) == BUNDLE_SHA
    original, derived = load(bundle_path)['sources']
    accepted_facts = load(HERE.parent / 'parent-acceptance.json')
    assert accepted_facts['status'] == 'accepted_ten_direct_disclosed_facts_file_only'
    assert accepted_facts['bundle_SHA'] == BUNDLE_SHA and accepted_facts['derived_source_ID'] == derived['id']
    assert load(HERE.parent / 'normalization-input.json')['source'] == original
    replay = load(HERE.parent / 'reproduction.json')
    assert replay['same_now_whole_bundle_and_ID_exact'] and replay['original_whole_object_unchanged']
    assert replay['reproduction']['status'] == 'reproduced'
    facts = json.loads(derived['content'])['facts']
    assert len(facts) == 10 and [f['value'] for f in facts] == [
        '7075025000','1217085000','815269000','38.43','14021000000','2017000000','1248000000','58.85','43.00','21.50']
    assert all(f['source_id'] == f['original_source_id'] == original['id'] and not f['financial_inputs_verified']
               and not f['scope']['model_or_policy_adopted'] for f in facts)
    assert [f['raw_unit_label'] for f in facts[:3]] == ['千円'] * 3
    assert [f['raw_unit_label'] for f in facts[4:7]] == ['百万円'] * 3
    assert all(not facts[i]['scope']['split_factor_applied_by_extractor'] for i in (3, 7, 8, 9))
    for f in facts[-2:]:
        assert f['period']['start_date'] is f['period']['end_date'] is f['period']['dividend_record_date'] is None
        assert f['scope']['accounting_basis'] is f['scope']['consolidation_scope'] is None
        assert not f['scope']['financial_or_DDM_adoption'] and not f['scope']['cash_payment_confirmation']
        assert f['scope']['annual_total_not_generated_or_computed'] and f['scope']['interim_final_not_added']
    assert facts[-2]['concept'] != facts[-1]['concept']
    assert facts[-2]['scope']['share_basis'] == 'pre_split_interim_display'
    assert facts[-1]['scope']['share_basis'] == 'post_split_final_forecast_display'
    assert not any('annual_dividend' in f['concept'] for f in facts)
    selection = load(HERE.parents[1] / 'initial-public-review-2026-10-16/selection.json')
    assert selection['selected_code'] == selection['selected_csv_row']['security_code'] == '2163'
    value = deepcopy(old)
    entry = {'artifact': str(bundle_path.relative_to(ROOT)), 'artifact_sha256': BUNDLE_SHA,
        'company_id':'jp:2163','contact_catalog_member':True,'derived_retrieved_at':derived['retrieved_at'],
        'derived_source_imported_into_actual_database':True,
        # Producer source_id is the quoted primary; index defaults to enclosing derived ID.
        'facts':[{k:deepcopy(f[k]) for k in ('id','concept','kind','period','scope','unit','value')} for f in facts],
        'original_retrieved_at':original['retrieved_at'],'original_source_id':original['id'],'source_id':derived['id']}
    value['companies'].append(entry)
    assert value['companies'][:37] == old['companies']
    assert all(resolved(entry,f) == derived['id'] and 'source_id' not in f for f in entry['facts'])
    flat = [(e,f) for e in value['companies'] for f in e['facts']]
    sources = {resolved(e,f) for e,f in flat}
    assert (len(flat),len(value['companies']),len(sources),len({e['company_id'] for e in value['companies']}),
        len({(e['company_id'],f.get('original_source_id',e['original_source_id'])) for e,f in flat})) == (190,38,40,25,31)
    assert len({f['id'] for _,f in flat}) == 190
    actual_acceptance = load(INTAKE / 'parent-acceptance.json')
    assert actual_acceptance['status'] == 'accepted_actual_five_source_intake_completed'
    assert actual_acceptance['DB_SHA'] == EXPECTED_DB
    receipts = {r['source_id']:r for r in load(INTAKE / 'source-firstsave.json')['receipts']}
    intake_sources = load(INTAKE / 'source-bundle.json')['sources']
    desired = {r['source_id']:r for r in load(INTAKE / 'classification-requests.json')['jp:2163']['classifications']}
    assert len(intake_sources) == len(receipts) == len(desired) == 5
    assert original in intake_sources and derived in intake_sources
    checks = []
    with closing(sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('PRAGMA query_only=ON')
        assert connection.execute('PRAGMA query_only').fetchone()[0] == 1
        connection.execute('BEGIN')
        counts = {t:connection.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in (
            'sources','record_availability','source_classifications','jobs','job_attempts','job_attempt_events','job_request_receipts','qualitative_case_versions')}
        assert counts == {'sources':195,'record_availability':195,'source_classifications':194,'jobs':108,
            'job_attempts':105,'job_attempt_events':210,'job_request_receipts':105,'qualitative_case_versions':43}
        assert connection.execute("SELECT count(*) FROM jobs WHERE status='completed'").fetchone()[0] == 108
        assert connection.execute("SELECT count(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0] == 0
        heads = [json.loads(r[0]) for r in connection.execute('''SELECT a.data FROM qualitative_case_versions a JOIN
            (SELECT case_id,max(version) version FROM qualitative_case_versions GROUP BY case_id)b
            ON a.case_id=b.case_id AND a.version=b.version''')]
        assert len(heads) == 22 and sum(len(r['reviewed_sources']) for r in heads) == 129
        assert not any(r['company_id']=='jp:2163' for r in heads)
        for source in intake_sources:
            sid = source['id']; native = native_sha(source)
            row = connection.execute('SELECT company_id,data FROM sources WHERE id=?',(sid,)).fetchone()
            assert row and row[0]=='jp:2163' and json.loads(row[1])==source
            availability = connection.execute("SELECT snapshot_sha256,first_saved_at,presence_observed_at,basis FROM record_availability WHERE entity_type='source' AND entity_id=?",(sid,)).fetchone()
            receipt = receipts[sid]
            assert tuple(availability)==(native,FIRSTSAVE,FIRSTSAVE,'trusted_insert')
            assert (receipt['native_snapshot_SHA'],receipt['first_saved_at'],receipt['presence_observed_at'],receipt['basis'])==tuple(availability)
            assert receipt['original_retrieved_at']==source['retrieved_at']
            classification = json.loads(connection.execute('SELECT data FROM source_classifications WHERE source_id=? ORDER BY version DESC LIMIT 1',(sid,)).fetchone()[0])
            assert classification['source_snapshot_sha256']==native
            assert all(classification[k]==desired[sid][k] for k in ('kind','financial_content','basis_quote','rationale'))
            checks.append({'source_id':sid,'native_snapshot_sha256':native,'whole_actual_source_exact':True,
                'current_classification_and_receipt_exact':True,'first_saved_at':FIRSTSAVE,'original_retrieved_at':source['retrieved_at']})
        assert connection.execute('SELECT count(*) FROM sources WHERE company_id=?',('jp:2163',)).fetchone()[0]==5
        actual,outside = set(),set()
        for sid in sources:
            row = connection.execute('SELECT data FROM sources WHERE id=?',(sid,)).fetchone()
            if row is None:
                outside.add(sid)
                continue
            actual.add(sid)
            classification = connection.execute('SELECT data FROM source_classifications WHERE source_id=? ORDER BY version DESC LIMIT 1',(sid,)).fetchone()
            assert classification and json.loads(classification[0])['source_snapshot_sha256']==native_sha(json.loads(row[0]))
        actual_facts = sum(resolved(e,f) in actual for e,f in flat)
        assert (len(actual),actual_facts,len(outside),len(flat)-actual_facts)==(38,183,2,7)
        outside_rows = [(e['company_id'],f['id'],resolved(e,f)) for e,f in flat if resolved(e,f) in outside]
        assert outside_rows==[(e['company_id'],f['id'],resolved(e,f)) for e in old['companies'] for f in e['facts'] if resolved(e,f) in outside]
        assert {r[0] for r in outside_rows}=={'jp:8331','jp:9702'}
        connection.rollback()
    assert digest(DB)==EXPECTED_DB and all(digest(ROOT/path)==pin for path,pin in pins.items())
    now = datetime.now(timezone.utc).isoformat()
    value.update(recorded_at=now,previous_index=str(OLD.relative_to(ROOT)),previous_index_sha256=digest(OLD),
        fact_count=190,company_source_entry_count=38,unique_company_count=25,unique_derived_source_count=40,
        unique_original_company_source_pair_count=31)
    value['actual_research_source_connections'].update(actual_database_main_sha256=EXPECTED_DB,
        database_snapshot_recorded_at=now,database_source_count=195,connected_derived_source_count=38,
        connected_fact_count=183,unconnected_derived_source_count=2,unconnected_fact_count=7)
    receipt_paths = [INTAKE/n for n in ('parent-acceptance.json','actual-completion.json','source-firstsave.json')]
    value['actual_research_source_connections']['connection_receipts'] += [str(p.relative_to(ROOT)) for p in receipt_paths]
    value['layout_note'] = '38 parents resolve to 40 derived sources and 190 facts across 25 companies/31 company-original pairs. 38 sources/183 facts are stored and classified; outside8331/9702 two sources/7 facts remain file-only. No financial adoption.'
    value['limitations'].append('2163 ten displayed facts retain thousand-JPY interim P/L actuals and million-JPY dated full-year company guidance. Issuer-adjusted basic/FY EPS are not adjusted again. Interim43pre and final21.50post DPS use separate concepts/kinds; annual DPS is not present or generated, no sum or DDM adoption. Dividend exact boundaries/record date/GAAP/consolidation stay null. Prior standalone interim is not substituted for missing consolidated comparison. FAQ/supplement original sources are verified as intake records but not added as another fact parent or current forecast.')
    value['revision_basis'] = {'kind':'append_2163_ten_accepted_disclosed_facts_after_actual_intake',
        'added_fact_count':10,'added_parent_entry_count':1,'prior_37_parent_entries_180_facts_all_fields_exact':True,
        'existing_per_fact_source_artifact_overrides_preserved':True,'financial_model_adoption':False}
    save(NEW,value)
    save(HERE/'validation.json',{'status':'frozen_final_v34_pending_root_review','recorded_at':now,
        'old_index_sha256':digest(OLD),'new_index_sha256':digest(NEW),
        'old37_parent_objects_180facts_all_fields_exact':True,'new_parent_entries':1,'new_facts':10,
        'companies':25,'parents':38,'facts':190,'derived_sources':40,'company_original_pairs':31,
        'actual_derived_sources':38,'actual_facts':183,'outside_sources':2,'outside_facts':7,
        'outside_8331_9702_entries_unchanged':outside_rows,'new_projected_fields_exact':True,
        'raw_primary_source_id_not_copied_to_index_override':True,'old_overrides_all_fields_exact':True,
        'ten_values_units_periods_EPS_already_split_DPS_two_bases_nulls_noannual_noDDM_preserved':True,
        'all_five_actual_source_checks':checks,'actual_counts':counts,'all108_jobs_completed_pending_leased0':True,
        'current_case_heads':22,'current_case_versions':43,'current_reviewed_sources':129,
        '2163_case_not_registered_in_this_snapshot':True,'actual_database_SHA_before':EXPECTED_DB,
        'actual_database_SHA_after':digest(DB),'RO_connection':'sqlite mode=ro/query_only/contextlib.closing; no Store',
        'original_source_retrieved_at':original['retrieved_at'],'derived_retrieved_at':derived['retrieved_at'],
        'derived_actual_first_saved_at':FIRSTSAVE,'receipt_refs':[str(p.relative_to(ROOT)) for p in receipt_paths],
        'frozen_inputs_unchanged':True,'new_normalizer_or_replay_calls':0,'DB_writes':0,'GETs':0,'financial_adoption':False})
    save(HERE/'execution.log',{'status':'v34_final_build_succeeded_read_only_DB','recorded_at':now,
        'command':'.venv/bin/python '+str(Path(__file__).relative_to(ROOT)),
        'new_index_sha256':digest(NEW),'actual_DB_SHA_unchanged':digest(DB)})
    save(HERE/'manifest.json',{'status':'frozen_final_v34_pending_root_review','recorded_at':now,
        'files':{p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(HERE.iterdir()) if p.is_file()},
        'new_index':str(NEW.relative_to(ROOT)),'new_index_sha256':digest(NEW),'frozen_input_pins':pins,
        'self_excluded':True,'DB_SHA_unchanged':EXPECTED_DB,'DB_writes':0,'GETs':0,'financial_adoption':False})
    print(json.dumps({'index_v34_sha256':digest(NEW),'validation_sha256':digest(HERE/'validation.json'),
        'manifest_sha256':digest(HERE/'manifest.json'),'actual_derived_sources':38,'actual_facts':183,'DB_writes':0}))


if __name__=='__main__':
    main()
