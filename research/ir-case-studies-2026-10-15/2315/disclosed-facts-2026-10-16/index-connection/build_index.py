"""Finite append-only v35; actual SQLite RO only, no Store/normalizer/network."""
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
OLD = BASE / 'disclosed-fact-index-v34.json'
NEW = BASE / 'disclosed-fact-index-v35.json'
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED_DB = 'b85405d687fce2e91e9830b8cc53a81e6652f3c77169c78dd8d3eb2560b2b1d9'
INTAKE = ROOT / 'research/ir-2315-initial-with-facts-intake-2026-10-16'
FIRSTSAVE = '2026-10-16T05:18:48.226120+00:00'
BUNDLE_SHA = '62ac24e13125451f58971fabbb76ba2807ca286bcbaacf3b1a0fb83abc535f55'


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
    assert digest(OLD) == 'bf3c8c0b7c4e38a873e2c16667fd39f0d4b76b7a444b8ba095dac0cc3b7ca485'
    old = load(OLD)
    assert len(old['companies']) == 38 and old['fact_count'] == 190
    assert sum(len(e['facts']) for e in old['companies']) == 190
    bundle_path = HERE.parent / 'normalized-bundle.json'
    assert digest(bundle_path) == BUNDLE_SHA
    original, derived = load(bundle_path)['sources']
    accepted_facts = load(HERE.parent / 'parent-acceptance.json')
    assert accepted_facts['status'] == 'accepted_twelve_direct_disclosed_facts_file_only'
    assert accepted_facts['bundle_SHA'] == BUNDLE_SHA and accepted_facts['derived_source_ID'] == derived['id']
    assert load(HERE.parent / 'normalization-input.json')['source'] == original
    replay = load(HERE.parent / 'reproduction.json')
    assert replay['same_now_whole_bundle_and_ID_exact'] and replay['original_whole_object_unchanged']
    assert replay['reproduction']['status'] == 'reproduced'
    facts = json.loads(derived['content'])['facts']
    assert len(facts) == 12 and [f['value'] for f in facts] == [
        '4693842000','111568000','-12167000','-126493000','-0.75','199000000',
        '6166000000','107000000','107000000','91000000','0.66','0']
    assert all(f['source_id'] == f['original_source_id'] == original['id'] and not f['financial_inputs_verified']
        and not f['scope']['model_or_policy_adopted'] for f in facts)
    assert [f['raw_unit_label'] for f in facts[:4]] == ['千円'] * 4
    assert [f['raw_unit_label'] for f in facts[6:10]] == ['百万円'] * 4
    assert facts[5]['concept'] == 'issuer_defined_adjusted_ebitda' and facts[5]['scope']['company_nonGAAP_supplement']
    assert not facts[5]['scope']['EBITDA_independently_recomputed']
    assert facts[7]['concept'] != facts[8]['concept'] and facts[7]['location']['raw_token_source_character_start'] != facts[8]['location']['raw_token_source_character_start']
    dps = facts[-1]
    assert dps['raw_value'] == '0.00' and dps['kind'] == 'reported_fact'
    assert dps['period']['start_date'] is dps['period']['end_date'] is dps['period']['dividend_record_date'] is None
    assert dps['scope']['accounting_basis'] is dps['scope']['consolidation_scope'] is None
    assert dps['scope']['annual_DPS_not_generated_or_added'] and not dps['scope']['cash_payment_confirmation']
    assert dps['scope']['final_or_annual_forecast_undetermined_dash_not_zero_filled']
    assert not any('annual_dividend' in f['concept'] or 'final_dividend' in f['concept'] for f in facts)
    selection = load(HERE.parents[1] / 'initial-public-review-2026-10-16/selection.json')
    assert selection['selected_code'] == selection['selected_csv_row']['security_code'] == '2315'
    value = deepcopy(old)
    entry = {'artifact': str(bundle_path.relative_to(ROOT)), 'artifact_sha256': BUNDLE_SHA,
        'company_id':'jp:2315','contact_catalog_member':True,'derived_retrieved_at':derived['retrieved_at'],
        'derived_source_imported_into_actual_database':True,
        # Producer source_id is the quoted primary; index defaults to enclosing derived ID.
        'facts':[{k:deepcopy(f[k]) for k in ('id','concept','kind','period','scope','unit','value')} for f in facts],
        'original_retrieved_at':original['retrieved_at'],'original_source_id':original['id'],'source_id':derived['id']}
    value['companies'].append(entry)
    assert value['companies'][:38] == old['companies']
    assert all(resolved(entry,f) == derived['id'] and 'source_id' not in f for f in entry['facts'])
    flat = [(e,f) for e in value['companies'] for f in e['facts']]
    sources = {resolved(e,f) for e,f in flat}
    assert (len(flat),len(value['companies']),len(sources),len({e['company_id'] for e in value['companies']}),
        len({(e['company_id'],f.get('original_source_id',e['original_source_id'])) for e,f in flat})) == (202,39,41,26,32)
    assert len({f['id'] for _,f in flat}) == 202
    actual_acceptance = load(INTAKE / 'parent-acceptance.json')
    assert actual_acceptance['status'] == 'accepted_actual_six_source_intake_completed'
    assert actual_acceptance['DB_SHA'] == EXPECTED_DB
    receipts = {r['source_id']:r for r in load(INTAKE / 'actual-source-firstsave.json')}
    intake_sources = load(INTAKE / 'source-bundle.json')['sources']
    desired = {r['source_id']:r for r in load(INTAKE / 'classification-requests.json')['jp:2315']['classifications']}
    saved_classes = {r['source_id']:r for r in load(INTAKE / 'actual-classifications.json')}
    assert len(intake_sources) == len(receipts) == len(desired) == 6
    assert original in intake_sources and derived in intake_sources
    checks = []
    with closing(sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('PRAGMA query_only=ON')
        assert connection.execute('PRAGMA query_only').fetchone()[0] == 1
        connection.execute('BEGIN')
        counts = {t:connection.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in (
            'sources','record_availability','source_classifications','jobs','job_attempts','job_attempt_events','job_request_receipts','qualitative_case_versions')}
        assert counts == {'sources':201,'record_availability':201,'source_classifications':200,'jobs':109,
            'job_attempts':106,'job_attempt_events':212,'job_request_receipts':106,'qualitative_case_versions':44}
        assert connection.execute("SELECT count(*) FROM jobs WHERE status='completed'").fetchone()[0] == 109
        assert connection.execute("SELECT count(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0] == 0
        heads = [json.loads(r[0]) for r in connection.execute('''SELECT a.data FROM qualitative_case_versions a JOIN
            (SELECT case_id,max(version) version FROM qualitative_case_versions GROUP BY case_id)b
            ON a.case_id=b.case_id AND a.version=b.version''')]
        assert len(heads) == 23 and sum(len(r['reviewed_sources']) for r in heads) == 134
        assert not any(r['company_id']=='jp:2315' for r in heads)
        for source in intake_sources:
            sid = source['id']; native = native_sha(source)
            row = connection.execute('SELECT company_id,data FROM sources WHERE id=?',(sid,)).fetchone()
            assert row and row[0]=='jp:2315' and json.loads(row[1])==source
            availability = connection.execute("SELECT snapshot_sha256,first_saved_at,presence_observed_at,basis FROM record_availability WHERE entity_type='source' AND entity_id=?",(sid,)).fetchone()
            receipt = receipts[sid]
            assert tuple(availability)==(native,FIRSTSAVE,FIRSTSAVE,'trusted_insert')
            assert (receipt['source_snapshot_sha256'],receipt['first_saved_at'],receipt['basis'])==(native,FIRSTSAVE,'trusted_insert')
            classification = json.loads(connection.execute('SELECT data FROM source_classifications WHERE source_id=? ORDER BY version DESC LIMIT 1',(sid,)).fetchone()[0])
            assert classification == saved_classes[sid]
            assert classification['source_snapshot_sha256']==native
            assert all(classification[k]==desired[sid][k] for k in ('kind','financial_content','basis_quote','rationale'))
            checks.append({'source_id':sid,'native_snapshot_sha256':native,'whole_actual_source_exact':True,
                'current_classification_and_receipt_exact':True,'first_saved_at':FIRSTSAVE,'original_retrieved_at':source['retrieved_at']})
        assert connection.execute('SELECT count(*) FROM sources WHERE company_id=?',('jp:2315',)).fetchone()[0]==6
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
        assert (len(actual),actual_facts,len(outside),len(flat)-actual_facts)==(39,195,2,7)
        outside_rows = [(e['company_id'],f['id'],resolved(e,f)) for e,f in flat if resolved(e,f) in outside]
        assert outside_rows==[(e['company_id'],f['id'],resolved(e,f)) for e in old['companies'] for f in e['facts'] if resolved(e,f) in outside]
        assert {r[0] for r in outside_rows}=={'jp:8331','jp:9702'}
        connection.rollback()
    assert digest(DB)==EXPECTED_DB and all(digest(ROOT/path)==pin for path,pin in pins.items())
    now = datetime.now(timezone.utc).isoformat()
    value.update(recorded_at=now,previous_index=str(OLD.relative_to(ROOT)),previous_index_sha256=digest(OLD),
        fact_count=202,company_source_entry_count=39,unique_company_count=26,unique_derived_source_count=41,
        unique_original_company_source_pair_count=32)
    value['actual_research_source_connections'].update(actual_database_main_sha256=EXPECTED_DB,
        database_snapshot_recorded_at=now,database_source_count=201,connected_derived_source_count=39,
        connected_fact_count=195,unconnected_derived_source_count=2,unconnected_fact_count=7)
    receipt_paths = [INTAKE/n for n in ('parent-acceptance.json','actual-completion.json','actual-source-firstsave.json')]
    value['actual_research_source_connections']['connection_receipts'] += [str(p.relative_to(ROOT)) for p in receipt_paths]
    value['layout_note'] = '39 parents resolve to 41 derived sources and 202 facts across 26 companies/32 company-original pairs. 39 sources/195 facts are stored and classified; outside8331/9702 two sources/7 facts remain file-only. No financial adoption.'
    value['limitations'].append('2315 twelve direct displayed facts retain thousand-JPY Q3 P/L loss signs, basic negative EPS and the separate issuer-defined nonGAAP adjustedEBITDA199million. FY5 dated issuer forecasts retain distinct OP107 and ordinary107 columns. Interim DPS0.00 is an explicit reported display only; final/annual undetermined/dash are not zero-filled, annual DPS not generated, dividend dates/GAAP/consolidation stay null, no payment/DDM adoption. Tax/NCI/special item context is not netted or normalized; no Q4 required profits, current EPS denominator, current forecast or financial model adoption. Original notices are verified intake sources, not additional indexed facts.')
    value['revision_basis'] = {'kind':'append_2315_twelve_accepted_disclosed_facts_after_actual_intake',
        'added_fact_count':12,'added_parent_entry_count':1,'prior_38_parent_entries_190_facts_all_fields_exact':True,
        'existing_per_fact_source_artifact_overrides_preserved':True,'financial_model_adoption':False}
    save(NEW,value)
    save(HERE/'validation.json',{'status':'frozen_final_v35_pending_root_review','recorded_at':now,
        'old_index_sha256':digest(OLD),'new_index_sha256':digest(NEW),
        'old38_parent_objects_190facts_all_fields_exact':True,'new_parent_entries':1,'new_facts':12,
        'companies':26,'parents':39,'facts':202,'derived_sources':41,'company_original_pairs':32,
        'actual_derived_sources':39,'actual_facts':195,'outside_sources':2,'outside_facts':7,
        'outside_8331_9702_entries_unchanged':outside_rows,'new_projected_fields_exact':True,
        'raw_primary_source_id_not_copied_to_index_override':True,'old_overrides_all_fields_exact':True,
        'twelve_values_signs_precision_EBITDA_vs_profit_stages_DPSnull_noannual_nofinancialadoption_preserved':True,
        'all_six_actual_source_checks':checks,'actual_counts':counts,'all109_jobs_completed_pending_leased0':True,
        'current_case_heads':23,'current_case_versions':44,'current_reviewed_sources':134,
        '2315_case_not_registered_in_this_snapshot':True,'actual_database_SHA_before':EXPECTED_DB,
        'actual_database_SHA_after':digest(DB),'RO_connection':'sqlite mode=ro/query_only/contextlib.closing; no Store',
        'original_source_retrieved_at':original['retrieved_at'],'derived_retrieved_at':derived['retrieved_at'],
        'derived_actual_first_saved_at':FIRSTSAVE,'receipt_refs':[str(p.relative_to(ROOT)) for p in receipt_paths],
        'frozen_inputs_unchanged':True,'new_normalizer_or_replay_calls':0,'DB_writes':0,'GETs':0,'financial_adoption':False})
    save(HERE/'execution.log',{'status':'v35_final_build_succeeded_read_only_DB','recorded_at':now,
        'command':'.venv/bin/python '+str(Path(__file__).relative_to(ROOT)),
        'new_index_sha256':digest(NEW),'actual_DB_SHA_unchanged':digest(DB)})
    save(HERE/'manifest.json',{'status':'frozen_final_v35_pending_root_review','recorded_at':now,
        'files':{p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(HERE.iterdir()) if p.is_file()},
        'new_index':str(NEW.relative_to(ROOT)),'new_index_sha256':digest(NEW),'frozen_input_pins':pins,
        'self_excluded':True,'DB_SHA_unchanged':EXPECTED_DB,'DB_writes':0,'GETs':0,'financial_adoption':False})
    print(json.dumps({'index_v35_sha256':digest(NEW),'validation_sha256':digest(HERE/'validation.json'),
        'manifest_sha256':digest(HERE/'manifest.json'),'actual_derived_sources':39,'actual_facts':195,'DB_writes':0}))


if __name__=='__main__':
    main()
