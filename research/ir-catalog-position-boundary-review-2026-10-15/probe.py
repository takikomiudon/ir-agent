"""Two synthetic databases; no real DB, GET, source edits, or new financial values.

The catalog probe's observation resets affect only its disposable DB. They
isolate the existing status-only and legacy-startup paths after initial import.
"""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
from unittest.mock import patch
import csv,json,sys,tempfile,hashlib
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'src'),str(R/'tests')]
from ir_agent.store import Store
from ir_agent.harness import Harness
from ir_agent.contacts import build_contact_bundle
from ir_agent.models import validate_company,json_text
from ir_agent.decision import evaluate_decision
from ir_agent.decision_lifecycle import DecisionLifecycle
from test_contacts import row,IMPORTED
from test_decision import plan

COMPANY='jp:130A'
OBSERVED='2026-10-15T01:30:00+00:00'
AS_OF='2026-10-15T10:31:00+09:00'
clock=lambda t:datetime.fromisoformat(t)


def decision_probe(store,harness):
    value=plan();original_financials=deepcopy(value['thesis']['valuation']);original_policy=deepcopy(value['policy']);price=value['quote']['price_jpy']
    value['as_of']=AS_OF;value['thesis']['company_id']=COMPANY
    for source in value['sources']:source['company_id']=COMPANY
    value['quote'].update(company_id=COMPANY,observed_at=IMPORTED,retrieved_at=IMPORTED)
    value['sources'][1].update(retrieved_at=IMPORTED)
    value['sources'][1]['metadata']['observed_at']=IMPORTED
    harness.ingest({'schema_version':1,'sources':value['sources'],'theses':[value['thesis']]},
                   now=clock('2026-10-15T01:30:30+00:00'))
    harness.register_decision_policy(value['policy'],now=clock('2026-10-15T01:30:30+00:00'))
    lifecycle=DecisionLifecycle(store);position=lifecycle.position_for(COMPANY,AS_OF,{})
    assert position['kind']=='observed' and position['held']is False
    value['context']['held']=position['held']
    reviewed=evaluate_decision(value)
    missing=deepcopy(value);missing['context']['held']=None;unknown=evaluate_decision(missing)
    assert reviewed['proposed_action']=='buy_review'
    assert unknown['proposed_action']=='unresolved' and unknown['reason_codes']==['position_not_verified']
    question=deepcopy(value['question']);question.update(company_id=COMPANY,created_at=AS_OF)
    question['decision_contract']={'policy_id':value['policy']['id'],'policy_version':1,'quote':value['quote'],'synthetic':True}
    frozen=harness.add_question(question,now=clock(AS_OF))
    assert frozen['decision_contract']['held']is False
    assert frozen['decision_contract']['position_snapshot']['kind']=='observed'
    assert frozen['decision_contract']['synthetic_position']is None
    assert value['thesis']['valuation']==original_financials and value['policy']==original_policy and value['quote']['price_jpy']==price
    return {'position_snapshot':position,'frozen_contract_position':frozen['decision_contract']['position_snapshot'],
      'synthetic_position_assumption_present':False,'observed_false_decision':{'status':reviewed['status'],'proposed_action':reviewed['proposed_action'],'reason_codes':reviewed['reason_codes']},
      'same_inputs_except_unknown_held':{'status':unknown['status'],'proposed_action':unknown['proposed_action'],'reason_codes':unknown['reason_codes']},
      'financial_values_and_policy_unchanged_from_existing_fixture':True,'only_test_identity_and_time_rebased':True}


def run():
    raw={'id':COMPANY,'name':'Synthetic company'}
    normalizer_equal=validate_company(raw)==validate_company({**raw,'held':False})
    assert normalizer_equal
    cases=[]
    with tempfile.TemporaryDirectory(prefix='ir_catalog_position_',dir='/tmp') as tmp:
        path=Path(tmp)/'catalog.sqlite3';csvpath=Path(tmp)/'contacts.csv';item=row()
        assert 'held'not in item
        with csvpath.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(item));writer.writeheader();writer.writerow(item)
        catalog=build_contact_bundle(csvpath,imported_at=IMPORTED)
        company=catalog['bundle']['companies'][0];assert 'held'not in company
        with patch('ir_agent.store.now_iso',return_value=OBSERVED):
            store=Store(path);harness=Harness(store)
            imported=harness.import_contacts(str(csvpath),IMPORTED)
            assert imported['status']=='imported' and store.company(COMPANY)['held']is False
            first=decision_probe(store,harness)
        entry={'case':'catalog_held_omitted','input_had_no_holding_declaration':True,'raw_catalog_company_has_held':False,
          'validated_company_held':store.company(COMPANY)['held'],'company_status_on_initial_catalog_import':'watch',**first}
        # Isolate the effect of a status-only call if fresh-default observation
        # is suppressed by a future fix. No genuine history exists in this toy.
        store.connection.execute('DELETE FROM position_observations')
        assert store.position_at(COMPANY,'2026-10-15T01:31:30+00:00')is None
        with patch('ir_agent.store.now_iso',return_value='2026-10-15T01:32:00+00:00'):
            harness.set_company_status(COMPANY,'active','Synthetic status-only update; no holding declaration supplied.')
        status_position=store.position_at(COMPANY,'2026-10-15T01:32:00+00:00')
        assert status_position['held']is False and status_position['kind']=='observed'
        entry['status_only_empty_history_stage']={'probe_only_disposable_observations_reset':True,'held_argument_supplied':False,'new_position':status_position}
        # Simulate a legacy catalog company without position history, in the
        # same temporary database, to exercise Store's actual opening path.
        store.connection.execute('DELETE FROM position_observations');store.close()
        with patch('ir_agent.store.now_iso',return_value='2026-10-15T01:33:00+00:00'):store=Store(path)
        try:
            boot_position=store.position_at(COMPANY,'2026-10-15T01:33:00+00:00')
            assert boot_position['held']is False and boot_position['kind']=='observed'
            entry['legacy_empty_history_reopen_stage']={'probe_only_disposable_observations_reset':True,'catalog_contact_retained':bool(store.company(COMPANY)['ir_contact']),
               'new_position':boot_position,'columns':[x['name'] for x in store.connection.execute('PRAGMA table_info(position_observations)')]}
        finally:store.close()
        cases.append(entry)
    with patch('ir_agent.store.now_iso',return_value=OBSERVED):
        store=Store(':memory:');harness=Harness(store)
        try:
            declared={**raw,'held':False}
            harness.ingest({'schema_version':1,'companies':[declared]},now=clock(OBSERVED))
            cases.append({'case':'explicit_user_held_false','input_had_explicit_holding_declaration':True,'input_company':declared,
                         'declaration_is_not_broker_audited_proof':True,**decision_probe(store,harness)})
        finally:store.close()
    assert cases[0]['position_snapshot']==cases[1]['position_snapshot']
    return {'schema_version':1,'status':'catalog_default_and_user_declared_false_indistinguishable_in_position_gate',
      'validate_company_omitted_equals_explicit_false':normalizer_equal,'cases':cases,'same_position_observation_fields':True,
      'execution':{'synthetic_databases':2,'temporary_catalog_files':1,'actual_DB_accesses':0,'new_GETs':0,'production_or_old_file_changes':0,'full_suite_runs':0},
      'limits':['Catalog import alone creates watch company and no financial thesis/job/order. Financial effect is conditional on later complete synthetic model/policy inputs.','Caller-declared false is a legitimate input observation in this probe, not independent confirmation of real brokerage holdings.','Status/startup reset stages only delete disposable synthetic observations to isolate legacy-empty-history behavior; no real or original history is altered.']}

if __name__=='__main__':
    data=run();output=Path(sys.argv[1])if len(sys.argv)>1 else Path('/tmp/ir_catalog_position_probe.json')
    output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':data['status'],'cases':[{'case':c['case'],'held':c['position_snapshot']['held'],'kind':c['position_snapshot']['kind'],
       'action':c['observed_false_decision']['proposed_action'],'unknown_control':c['same_inputs_except_unknown_held']['reason_codes']} for c in data['cases']]},ensure_ascii=False))
