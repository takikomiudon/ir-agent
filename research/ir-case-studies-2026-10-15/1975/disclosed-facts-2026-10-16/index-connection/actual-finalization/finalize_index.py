"""One finite append-only v33 finalization; SQLite strictly read-only, no Store."""
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
BASE = ROOT / 'research/ir-case-studies-2026-10-15'
OLD = BASE / 'disclosed-fact-index-v32.json'
NEW = BASE / 'disclosed-fact-index-v33.json'
DB = ROOT / 'data/ir-research-2026-10-15.sqlite3'
EXPECTED_DB = '11b6ad2c3cd5f6903fc3ce3654bf2ab5b850cd137061ac05fd6627d426b73778'
INTAKE = ROOT / 'research/ir-1975-initial-with-facts-intake-2026-10-16'
FIRSTSAVE = '2026-10-16T04:37:22.269407+00:00'


def load(path):
    return json.loads(path.read_bytes())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def native_sha(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as output:
        output.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def resolved(entry, fact):
    return fact.get('source_id', entry['source_id'])


def main():
    assert not NEW.exists() and not (HERE / 'validation.json').exists()
    pins = load(HERE / 'input-pins.json')
    assert all(digest(ROOT / path) == wanted for path, wanted in pins.items())
    assert digest(DB) == EXPECTED_DB
    old, proposed = load(OLD), load(HERE.parent / 'proposed-index-v33.json')
    assert len(old['companies']) == 36 and old['fact_count'] == 171
    assert proposed['companies'][:36] == old['companies']
    assert sum(len(e['facts']) for e in old['companies']) == 171
    value = deepcopy(proposed)
    entry = value['companies'][-1]
    assert len(value['companies']) == 37 and entry['company_id'] == 'jp:1975'
    original, derived = load(HERE.parents[1] / 'normalized-bundle.json')['sources']
    facts = json.loads(derived['content'])['facts']
    assert entry['source_id'] == derived['id'] and entry['original_source_id'] == original['id']
    assert entry['facts'] == [{k: deepcopy(f[k]) for k in ('id','concept','kind','period','scope','unit','value')} for f in facts]
    assert len(facts) == 9 and all(f['source_id'] == f['original_source_id'] == original['id'] for f in facts)
    assert [f['value'] for f in facts] == ['19483000000','2205000000','1546000000','112500000000','12200000000','9250000000','59.78','357.49','144.00']
    dps = facts[-1]
    assert dps['period']['start_date'] is dps['period']['end_date'] is dps['period']['dividend_record_date'] is None
    assert dps['scope']['accounting_basis'] is dps['scope']['consolidation_scope'] is None
    assert not dps['scope']['investor_DDM_dividend_column_adopted']
    accepted = load(INTAKE / 'parent-acceptance.json')
    assert accepted['status'] == 'accepted_actual_four_source_intake_completed' and accepted['DB_SHA'] == EXPECTED_DB
    receipts = {r['source_id']: r for r in load(INTAKE / 'source-firstsave.json')['receipts']}
    intake_sources = load(INTAKE / 'source-bundle.json')['sources']
    desired_classes = {r['source_id']: r for r in load(INTAKE / 'classification-requests.json')['jp:1975']['classifications']}
    assert len(intake_sources) == len(receipts) == len(desired_classes) == 4
    assert original in intake_sources and derived in intake_sources
    flat = [(e,f) for e in value['companies'] for f in e['facts']]
    sources = {resolved(e,f) for e,f in flat}
    assert (len(flat),len(value['companies']),len(sources),len({e['company_id'] for e in value['companies']}),
        len({(e['company_id'],f.get('original_source_id',e['original_source_id'])) for e,f in flat})) == (180,37,39,24,30)
    assert len({f['id'] for _,f in flat}) == 180
    checks = []
    with closing(sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('PRAGMA query_only=ON')
        assert connection.execute('PRAGMA query_only').fetchone()[0] == 1
        connection.execute('BEGIN')
        counts = {t:connection.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in (
            'sources','record_availability','source_classifications','jobs','job_attempts','job_attempt_events','job_request_receipts','qualitative_case_versions')}
        assert counts == {'sources':190,'record_availability':190,'source_classifications':189,'jobs':107,
            'job_attempts':104,'job_attempt_events':208,'job_request_receipts':104,'qualitative_case_versions':42}
        assert connection.execute("SELECT count(*) FROM jobs WHERE status='completed'").fetchone()[0] == 107
        assert connection.execute("SELECT count(*) FROM jobs WHERE status IN ('pending','leased')").fetchone()[0] == 0
        heads = [json.loads(r[0]) for r in connection.execute('''SELECT a.data FROM qualitative_case_versions a JOIN
            (SELECT case_id,max(version) version FROM qualitative_case_versions GROUP BY case_id)b
            ON a.case_id=b.case_id AND a.version=b.version''')]
        assert len(heads) == 21 and sum(len(r['reviewed_sources']) for r in heads) == 125
        assert not any(r['company_id']=='jp:1975' for r in heads)
        for source in intake_sources:
            sid=source['id']; native=native_sha(source)
            row=connection.execute('SELECT company_id,data FROM sources WHERE id=?',(sid,)).fetchone()
            assert row and row[0]=='jp:1975' and json.loads(row[1])==source
            availability=connection.execute("SELECT snapshot_sha256,first_saved_at,presence_observed_at,basis FROM record_availability WHERE entity_type='source' AND entity_id=?",(sid,)).fetchone()
            receipt=receipts[sid]
            assert tuple(availability)==(native,FIRSTSAVE,FIRSTSAVE,'trusted_insert')
            assert (receipt['native_snapshot_SHA'],receipt['first_saved_at'],receipt['presence_observed_at'],receipt['basis'])==tuple(availability)
            assert receipt['original_retrieved_at']==source['retrieved_at']
            classification=json.loads(connection.execute('SELECT data FROM source_classifications WHERE source_id=? ORDER BY version DESC LIMIT 1',(sid,)).fetchone()[0])
            assert classification['source_snapshot_sha256']==native
            assert all(classification[k]==desired_classes[sid][k] for k in ('kind','financial_content','basis_quote','rationale'))
            checks.append({'source_id':sid,'native_snapshot_sha256':native,'whole_actual_source_exact':True,
                'current_classification_snapshot_and_requested_fields_exact':True,'availability_and_saved_receipt_exact':True,
                'first_saved_at':FIRSTSAVE,'original_retrieved_at':source['retrieved_at']})
        assert connection.execute('SELECT count(*) FROM sources WHERE company_id=?',('jp:1975',)).fetchone()[0]==4
        actual,outside=set(),set()
        for sid in sources:
            row=connection.execute('SELECT data FROM sources WHERE id=?',(sid,)).fetchone()
            if row is None:
                outside.add(sid)
                continue
            actual.add(sid)
            classification=connection.execute('SELECT data FROM source_classifications WHERE source_id=? ORDER BY version DESC LIMIT 1',(sid,)).fetchone()
            assert classification and json.loads(classification[0])['source_snapshot_sha256']==native_sha(json.loads(row[0]))
        actual_facts=sum(resolved(e,f) in actual for e,f in flat)
        assert (len(actual),actual_facts,len(outside),len(flat)-actual_facts)==(37,173,2,7)
        outside_rows=[(e['company_id'],f['id'],resolved(e,f)) for e,f in flat if resolved(e,f) in outside]
        assert outside_rows==[(e['company_id'],f['id'],resolved(e,f)) for e in old['companies'] for f in e['facts'] if resolved(e,f) in outside]
        assert {r[0] for r in outside_rows}=={'jp:8331','jp:9702'}
        connection.rollback()
    assert digest(DB)==EXPECTED_DB and all(digest(ROOT/path)==wanted for path,wanted in pins.items())
    now=datetime.now(timezone.utc).isoformat()
    entry['derived_source_imported_into_actual_database']=True
    assert value['companies'][:36]==old['companies']
    assert all(resolved(entry,f)==derived['id'] and 'source_id' not in f for f in entry['facts'])
    del value['candidate_connection_state']
    value['recorded_at']=now
    value['actual_research_source_connections'].update(actual_database_main_sha256=EXPECTED_DB,
        database_snapshot_recorded_at=now,database_source_count=190,connected_derived_source_count=37,
        connected_fact_count=173,unconnected_derived_source_count=2,unconnected_fact_count=7)
    receipt_paths=[INTAKE/n for n in ('parent-acceptance.json','actual-completion.json','source-firstsave.json')]
    value['actual_research_source_connections']['connection_receipts'] += [str(p.relative_to(ROOT)) for p in receipt_paths]
    value['layout_note']='37 parents resolve to 39 derived sources and 180 facts across 24 companies/30 company-original pairs. 37 sources/173 facts are stored and classified; outside8331/9702 two sources/7 facts remain file-only. No financial adoption.'
    value['revision_basis']={'kind':'append_1975_nine_accepted_disclosed_facts_after_actual_intake',
        'added_fact_count':9,'added_parent_entry_count':1,'prior_36_parent_entries_171_facts_all_fields_exact':True,
        'existing_per_fact_source_artifact_overrides_preserved':True,'financial_model_adoption':False}
    save(NEW,value)
    save(HERE/'validation.json',{'status':'frozen_final_v33_pending_root_review','recorded_at':now,
        'old_index_sha256':digest(OLD),'new_index_sha256':digest(NEW),
        'old36_parent_objects_171facts_all_fields_exact':True,'new_parent_entries':1,'new_facts':9,
        'companies':24,'parents':37,'facts':180,'derived_sources':39,'company_original_pairs':30,
        'actual_derived_sources':37,'actual_facts':173,'outside_sources':2,'outside_facts':7,
        'outside_8331_9702_entries_unchanged':outside_rows,'new_projected_facts_exact':True,
        'raw_primary_source_id_not_copied_to_index_override':True,'old_overrides_all_fields_exact':True,
        'all_four_actual_source_checks':checks,'actual_counts':counts,
        'all107_jobs_completed_pending_leased0':True,'current_case_heads':21,'current_case_versions':42,
        'current_reviewed_sources':125,'1975_case_not_yet_registered_in_this_snapshot':True,
        'actual_database_SHA_before':EXPECTED_DB,'actual_database_SHA_after':digest(DB),
        'RO_connection':'sqlite URI mode=ro + query_only + contextlib.closing; no Store',
        'original_source_retrieved_at':original['retrieved_at'],'derived_retrieved_at':derived['retrieved_at'],
        'derived_actual_first_saved_at':FIRSTSAVE,'DPS_nulls_scope_and_no_DDM_unchanged':True,
        'frozen_proposal_and_all_dependency_pins_unchanged':True,
        'receipt_refs':[str(p.relative_to(ROOT)) for p in receipt_paths],
        'new_normalizer_or_replay_calls':0,'DB_writes':0,'GETs':0,'financial_adoption':False})
    save(HERE/'execution.log',{'status':'final_v33_build_succeeded_read_only_DB',
        'command':'.venv/bin/python '+str(Path(__file__).relative_to(ROOT)),
        'recorded_at':now,'new_index_sha256':digest(NEW),'actual_DB_SHA_unchanged':digest(DB)})
    save(HERE/'manifest.json',{'status':'frozen_final_v33_pending_root_review','recorded_at':now,
        'files':{p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(HERE.iterdir()) if p.is_file()},
        'new_index':str(NEW.relative_to(ROOT)),'new_index_sha256':digest(NEW),
        'frozen_input_pins':pins,'self_excluded':True,'DB_SHA_unchanged':EXPECTED_DB,
        'DB_writes':0,'GETs':0,'financial_adoption':False})
    print(json.dumps({'index_v33_sha256':digest(NEW),'validation_sha256':digest(HERE/'validation.json'),
        'manifest_sha256':digest(HERE/'manifest.json'),'actual_derived_sources':37,'actual_facts':173,'DB_writes':0}))


if __name__=='__main__':
    main()
