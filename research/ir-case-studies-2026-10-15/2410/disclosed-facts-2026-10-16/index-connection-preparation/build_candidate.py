"""File-only v37 candidate. Default emits deterministic replay; --write creates once.
No DB/Store/network/normalizer invocation or shared-index write.
"""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'src'))
from ir_agent.models import json_text
from ir_agent.adapters.common import canonical_json
BASE=ROOT/'research/ir-case-studies-2026-10-15'
OLD=BASE/'disclosed-fact-index-v36.json'
P=HERE.parent
FIELDS=('id','concept','kind','period','scope','unit','value')
def load(p):return json.loads(p.read_bytes())
def digest(p):return sha256(p.read_bytes()).hexdigest()
def native(x):return sha256(json_text(x).encode()).hexdigest()
def save(p,x):
 with p.open('x',encoding='utf-8') as out:out.write(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def run():
 pins=load(HERE/'input-pins.json')
 assert all(digest(ROOT/p)==h for p,h in pins['files'].items())
 assert digest(OLD)=='f614e11911c28adfe4a126fbe60d85141886faefb40b73059d9ca919552bda35'
 old=load(OLD);assert len(old['companies'])==40 and old['fact_count']==214
 bundle_path=P/'normalized-bundle.json';bundle=load(bundle_path);original,derived=bundle['sources']
 acceptance=load(P/'parent-acceptance.json');replay=load(P/'reproduction.json')
 assert digest(bundle_path)==acceptance['bundle_SHA']=='6fc7d3f12a060e9f0578275af1acd38e72fe2a1f790e171ec1666bdb8d9a63e8'
 assert derived['id']==acceptance['derived_source_id']
 assert original==load(P/'normalization-input.json')['source']==load(BASE/'2410/initial-public-review-2026-10-16/source-bundle.json')['sources'][0]
 assert replay['original_wholeobject_exact'] and replay['report']['status']=='reproduced'
 parent_path=ROOT/'research/ir-2410-initial-with-listing-intake-2026-10-16/parent-acceptance.json'
 parent=load(parent_path);assert parent['status']=='accepted_actual_two_sources_one_intake_job'
 receipt=next(s for s in parent['sources'] if s['id']==original['id'])
 assert receipt['first_saved_at']=='2026-10-16T06:50:38.803336+00:00' and receipt['basis']=='trusted_insert'
 assert native(original)==load(P/'source-reference.json')['original_source_native_SHA']==replay['native_original_SHA']
 assert sha256(canonical_json(original).encode()).hexdigest()==derived['metadata']['original_source_snapshot_sha256']
 assert sha256(original['content'].encode()).hexdigest()==derived['metadata']['original_source_content_sha256']
 facts=json.loads(derived['content'])['facts'];assert len(facts)==12
 assert [f['value'] for f in facts]==acceptance['exact_tokens_and_Decimal_values']
 assert all(f['source_id']==f['original_source_id']==original['id'] and f['financial_inputs_verified'] is False for f in facts)
 assert all(f['concept']=='net_income' and f['scope']['consolidation_scope']=='nonconsolidated' for f in (facts[3],facts[8]))
 assert facts[-1]['value']=='160.00' and facts[-1]['scope']['composition_is_context_not_additional_numeric_fact']
 selection=load(BASE/'2410/initial-public-review-2026-10-16/selection.json')
 assert selection['company_snapshot']['id']=='jp:2410' and selection['roster']['row']['security_code']=='2410'
 value=deepcopy(old)
 entry={'artifact':str(bundle_path.relative_to(ROOT)),'artifact_sha256':digest(bundle_path),'company_id':'jp:2410','contact_catalog_member':True,
 'derived_retrieved_at':derived['retrieved_at'],'derived_source_imported_into_actual_database':False,
 'facts':[{k:deepcopy(f[k]) for k in FIELDS} for f in facts],
 'original_retrieved_at':original['retrieved_at'],'original_source_id':original['id'],'source_id':derived['id']}
 value['companies'].append(entry)
 assert value['companies'][:40]==old['companies']
 flat=[(e,f) for e in value['companies'] for f in e['facts']]
 counts={'facts':len(flat),'parents':len(value['companies']),'companies':len({e['company_id'] for e in value['companies']}),
 'derived_sources':len({f.get('source_id',e['source_id']) for e,f in flat}),
 'company_original_pairs':len({(e['company_id'],f.get('original_source_id',e['original_source_id'])) for e,f in flat})}
 assert counts=={'facts':226,'parents':41,'companies':28,'derived_sources':43,'company_original_pairs':34}
 assert len({f['id'] for _,f in flat})==226 and all('source_id' not in f for f in entry['facts'])
 value.update(recorded_at=pins['recorded_at'],previous_index=str(OLD.relative_to(ROOT)),previous_index_sha256=digest(OLD),fact_count=226,
 company_source_entry_count=41,unique_company_count=28,unique_derived_source_count=43,unique_original_company_source_pair_count=34)
 value['layout_note']='PREPARATION ONLY:41 parent entries,226 facts,28 companies,43 resolved derived sources,34 company-original pairs. New2410 derivative/facts12 pending root actual intake and connection. Existing actual_research_source_connections is the historical v36 snapshot, not this preparation-time DB state.'
 value['limitations'].append('2410 net_income remains standalone, not parent-attributable. July31 issuer FY guidance is a dated forecast for a now-ended FY, not actual results or current guidance. AnnualDPS160 includes ordinary140+special20; its complete original scope/nulls are preserved, without permanent-dividend or payment inference. Candidate only; no model adoption.')
 value['revision_basis']={'kind':'file_only_v37_candidate_append_2410_accepted12_pending_actual_derived_save','added_fact_count':12,'added_parent_entry_count':1,'prior40_parent_objects_214facts_whole_exact':True,'existing_source_artifact_overrides_preserved':True,'financial_model_adoption':False}
 value['candidate_connection_state']={'status':'prepared_not_published_no_current_DB_check','requires_root_actual_derived_intake_acceptance_before_shared_connection':True,
 'new_original_source_id':original['id'],'new_original_actual_save_receipt':str(parent_path.relative_to(ROOT)),'new_original_actual_first_saved_at_as_receipt':receipt['first_saved_at'],
 'new_original_actual_save_verified_by_this_worker_DB':False,'new_derived_source_id':derived['id'],'new_derived_actual_first_saved_at':None,'new_derived_actual_connection':False,
 'new_file_only_fact_count':12,'new_file_only_derived_count':1,'historical_v36_actual_connection_snapshot_kept_exact':True,'historical_v36_connected_facts':207,'historical_v36_connected_derived':40,
 'candidate_unconnected_facts_including_unchanged_old7':19,'candidate_unconnected_derived_including_unchanged_old2':3,
 'conditional_after_future_accepted_derived_intake':{'connected_facts':219,'connected_derived':41,'unchanged_outside_facts':7,'unchanged_outside_derived':2,'not_observed_or_claimed_actual':True},
 'inherited_connection_preparation_and_previous_snapshots':'historical provenance from v36; not a new2410 actual-connection claim'}
 assert value['actual_research_source_connections']==old['actual_research_source_connections']
 validation={'status':'file_only_v37_candidate_pending_root_actual_derived_save','counts':counts,'old_v36_SHA':digest(OLD),
 'old40_parent_objects_214facts_whole_exact':True,'old_parent_objects_SHA_before':native(old['companies']),'old_parent_objects_SHA_after':native(value['companies'][:40]),
 'old_per_fact_source_and_artifact_overrides_unchanged':True,'new12_index_projection_whole_exact':all(entry['facts'][i]=={k:f[k] for k in FIELDS} for i,f in enumerate(facts)),
 'rawfact_primary_sourceid_not_copied_as_index_override':True,'newfacts_resolve_to_enclosing_derived_id':True,
 'source_native_bindings':{'original_source_id':original['id'],'original_models_json_text_SHA':native(original),'original_normalizer_compact_snapshot_SHA':derived['metadata']['original_source_snapshot_sha256'],
 'derived_source_id':derived['id'],'derived_models_json_text_SHA':native(derived),'serialization_methods_not_conflated':True},
 'original_actual_firstsave_from_root_receipt':receipt['first_saved_at'],'derived_actual_firstsave':None,'newentry_derived_imported_into_actual_database':False,
 'historical_actual_connections_object_unchanged':True,'standalone_net_income_unchanged':True,'DPS_special_dividend_scope_all_fields_unchanged':True,'historical_guidance_not_relabelled':True,
 'shared_v36_unchanged':True,'shared_v37_not_written':True,'DB_Store_GET_normalizer_production_code_shared_docs_calls_or_edits':0,'financial_adoption':False,'input_pins':pins['files']}
 assert all(digest(ROOT/p)==h for p,h in pins['files'].items())
 return value,validation
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
 candidate,validation=run()
 if args.write:
  save(HERE/'proposed-index-v37.json',candidate);save(HERE/'validation.json',validation)
  print(json.dumps({'counts':validation['counts'],'candidate_SHA':digest(HERE/'proposed-index-v37.json')},ensure_ascii=False))
 else:print(json.dumps({'candidate':candidate,'validation':validation},ensure_ascii=False,sort_keys=True,indent=2))
