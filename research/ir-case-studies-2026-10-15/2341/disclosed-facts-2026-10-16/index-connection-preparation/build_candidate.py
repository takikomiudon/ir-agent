"""Build only a local v36 candidate; never writes the shared index or any DB.

Default stdout returns deterministic candidate+validation for the pinned inputs.
--write creates the two new preparation files exclusively once.
"""
from copy import deepcopy
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/"src"))
from ir_agent.models import json_text
from ir_agent.adapters.common import canonical_json
BASE=ROOT/"research/ir-case-studies-2026-10-15"
OLD=BASE/"disclosed-fact-index-v35.json"
P=HERE.parent

def load(p):return json.loads(p.read_bytes())
def digest(p):return sha256(p.read_bytes()).hexdigest()
def native(v):return sha256(json_text(v).encode("utf-8")).hexdigest()
def resolved(entry,fact):return fact.get("source_id",entry["source_id"])
def save(p,value):
 with p.open("x",encoding="utf-8") as out:out.write(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n")

def run():
 pins=load(HERE/"input-pins.json")
 assert all(digest(ROOT/f)==h for f,h in pins["files"].items())
 assert digest(OLD)=="e6837e96945198db88bbd0341acd5591553313567e3efb2aa45a0deae45fe38f"
 old=load(OLD);assert len(old["companies"])==39 and old["fact_count"]==202
 assert sum(len(e["facts"]) for e in old["companies"])==202
 bundle_path=P/"normalized-bundle.json";bundle=load(bundle_path);original,derived=bundle["sources"]
 acceptance=load(P/"parent-acceptance.json")
 assert digest(bundle_path)==acceptance["bundle_SHA"]=="3d7e02520e26853f2e8f8066454f01b18d2f407d68f08db5b264ee3dbb234523"
 assert derived["id"]==acceptance["derived_source_id"] and acceptance["facts"]==12
 assert original==load(P/"normalization-input.json")["source"]==load(BASE/"2341/initial-public-review-2026-10-16/source-bundle.json")["sources"][0]
 replay=load(P/"reproduction.json");assert replay["original_wholeobject_exact"] and replay["report"]["status"]=="reproduced"
 parent=load(ROOT/"research/ir-2341-initial-intake-2026-10-16/parent-acceptance.json")
 assert parent["status"]=="accepted_actual_single_source_intake_and_classification"
 assert native(original)==parent["source_native_SHA"]==load(P/"source-reference.json")["original_source_native_SHA"]
 assert sha256(canonical_json(original).encode()).hexdigest()==derived["metadata"]["original_source_snapshot_sha256"]
 assert sha256(original["content"].encode()).hexdigest()==derived["metadata"]["original_source_content_sha256"]
 facts=json.loads(derived["content"])["facts"]
 assert len(facts)==12 and [f["value"] for f in facts]==acceptance["independent_Decimal_values"]
 assert all(f["source_id"]==f["original_source_id"]==original["id"] and not f["financial_inputs_verified"] for f in facts)
 selection=load(BASE/"2341/initial-public-review-2026-10-16/selection.json")
 assert selection["company_snapshot"]["id"]=="jp:2341" and any(x["selected_row"]["security_code"]=="2341" for x in selection["rosters"])
 value=deepcopy(old)
 entry={"artifact":str(bundle_path.relative_to(ROOT)),"artifact_sha256":digest(bundle_path),
  "company_id":"jp:2341","contact_catalog_member":True,"derived_retrieved_at":derived["retrieved_at"],
  "derived_source_imported_into_actual_database":False,
  "facts":[{k:deepcopy(f[k]) for k in ("id","concept","kind","period","scope","unit","value")} for f in facts],
  "original_retrieved_at":original["retrieved_at"],"original_source_id":original["id"],"source_id":derived["id"]}
 value["companies"].append(entry)
 assert value["companies"][:39]==old["companies"]
 assert all("source_id" not in f and resolved(entry,f)==derived["id"] for f in entry["facts"])
 flat=[(e,f) for e in value["companies"] for f in e["facts"]]
 counts={"facts":len(flat),"parents":len(value["companies"]),"companies":len({e["company_id"] for e in value["companies"]}),
  "derived_sources":len({resolved(e,f) for e,f in flat}),
  "company_original_pairs":len({(e["company_id"],f.get("original_source_id",e["original_source_id"])) for e,f in flat})}
 assert counts=={"facts":214,"parents":40,"companies":27,"derived_sources":42,"company_original_pairs":33}
 assert len({f["id"] for _,f in flat})==214
 assert value["actual_research_source_connections"]==old["actual_research_source_connections"]
 value.update(recorded_at=pins["recorded_at"],previous_index=str(OLD.relative_to(ROOT)),previous_index_sha256=digest(OLD),
  fact_count=214,company_source_entry_count=40,unique_company_count=27,unique_derived_source_count=42,unique_original_company_source_pair_count=33)
 value["layout_note"]="PREPARATION CANDIDATE ONLY:40 parents/42 resolved derivedsources/214 facts/27 companies/33 company-original pairs. Old v35 connection snapshot is historical and unchanged. New2341 derived1/facts12 are file-only per assignment, not actual connected. Publish only after root accepts actual derivedsource storage/classification."
 value["limitations"].append("2341 interim thousand-JPY P/L actuals and basicEPS are separate from dated issuer FY5 guidance and annualDPS5.00 total. Explicit interimDPS0 is not payment; dividend dates/record/accounting/consolidation nulls remain. No specialgain/tax/NCI adjustment, normalearnings, cancellation-effect EPS, current forecast or model adoption. This is a file-only candidate, not shared indexv36.")
 value["revision_basis"]={"kind":"file_only_candidate_append_2341_accepted12facts_pending_actual_derived_save","added_fact_count":12,"added_parent_entry_count":1,"prior39_parent_entries_202facts_all_fields_exact":True,"existing_per_fact_source_artifact_overrides_preserved":True,"financial_model_adoption":False}
 value["candidate_connection_state"]={"status":"prepared_not_published_not_current_DB_checked","requires_root_actual_derived_intake_acceptance_before_shared_connection":True,
  "new_original_source_id":original["id"],"new_original_actual_save_receipt":str((ROOT/"research/ir-2341-initial-intake-2026-10-16/parent-acceptance.json").relative_to(ROOT)),
  "new_original_actual_first_saved_at_as_receipt":parent["source_first_saved_at"],"new_original_actual_save_verified_by_this_worker_DB":False,
  "new_derived_source_id":derived["id"],"new_derived_actual_first_saved_at":None,"new_derived_actual_connection":False,
  "new_file_only_fact_count":12,"new_file_only_derived_count":1,
  "historical_v35_actual_connection_snapshot_kept_exact":True,
  "historical_v35_connected_facts":195,"historical_v35_connected_derived":39,
  "candidate_unconnected_facts_including_unchanged_old7":19,"candidate_unconnected_derived_including_unchanged_old2":3,
  "conditional_after_future_accepted_derived_intake":{"connected_facts":207,"connected_derived":40,"unchanged_outside_facts":7,"unchanged_outside_derived":2,"not_observed_or_claimed_actual":True}}
 validation={"status":"file_only_v36_candidate_pending_root_actual_derived_save","counts":counts,
  "old_v35_SHA":digest(OLD),"old39_parent_objects_202facts_whole_exact":True,
  "old_parent_objects_SHA_before":native(old["companies"]),"old_parent_objects_SHA_after":native(value["companies"][:39]),
  "old_perfact_source_artifact_overrides_unchanged":True,
  "new12_index_projection_fields_whole_exact":all(entry["facts"][i]=={k:f[k] for k in ("id","concept","kind","period","scope","unit","value")} for i,f in enumerate(facts)),
  "rawfact_primary_sourceid_not_copied_as_index_override":True,"newfacts_resolve_to_enclosing_derived_id":True,
  "source_native_bindings":{"original_source_id":original["id"],"original_native_models_json_text_SHA":native(original),"original_normalizer_compact_snapshot_SHA":derived["metadata"]["original_source_snapshot_sha256"],"derived_source_id":derived["id"],"derived_native_models_json_text_SHA":native(derived),"serialization_methods_not_conflated":True},
  "original_actual_firstsave_from_root_receipt":parent["source_first_saved_at"],"derived_actual_firstsave":None,
  "newentry_derived_imported_into_actual_database":False,"historical_actual_connections_object_unchanged":True,
  "no_new_actual_DB_state_claimed":True,"shared_v35_unchanged":True,"shared_v36_not_written":True,
  "normalizer_reproducer_generation_calls":0,"DB_Store_GET_code_shared_docs_edits":0,"financial_adoption":False,
  "input_pins":pins["files"]}
 assert all(digest(ROOT/f)==h for f,h in pins["files"].items())
 return value,validation

if __name__=="__main__":
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--write",action="store_true");args=parser.parse_args()
 candidate,validation=run()
 if args.write:
  save(HERE/"proposed-index-v36.json",candidate);save(HERE/"validation.json",validation)
  print(json.dumps({"status":validation["status"],"counts":validation["counts"],"candidate_SHA":digest(HERE/"proposed-index-v36.json")},ensure_ascii=False))
 else:print(json.dumps({"candidate":candidate,"validation":validation},ensure_ascii=False,sort_keys=True,indent=2))
