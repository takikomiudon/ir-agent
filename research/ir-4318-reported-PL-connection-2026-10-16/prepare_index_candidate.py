"""Pure file-only v43 candidate; root finalizes actual connection separately."""
import argparse, json, hashlib
from pathlib import Path
from copy import deepcopy
from datetime import datetime
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main(output,recorded_at):
    stamp=datetime.fromisoformat(recorded_at);assert stamp.tzinfo is not None
    dest=Path(output).resolve();assert ROOT/'research' in dest.parents and dest.name!='disclosed-fact-index-v43.json'
    assert not dest.exists(), 'Never replace a saved candidate'
    pins=load(HERE/'input-pins.json');assert all(sha(ROOT/p)==h for p,h in pins.items())
    oldpath=ROOT/'research/ir-case-studies-2026-10-15/disclosed-fact-index-v42.json';old=load(oldpath)
    bundle=load(HERE/'source-bundle.json');derived=bundle['sources'][0];facts=json.loads(derived['content'])['facts'];assert len(facts)==4
    sourcepath=ROOT/'research/ir-case-studies-2026-10-15/4318/operating-profit-components-disclosed-facts-2026-10-16/normalized-bundle.json'
    original=load(sourcepath)['sources'][0]
    entry={'artifact':str(sourcepath.relative_to(ROOT)),'artifact_sha256':sha(sourcepath),'company_id':'jp:4318','contact_catalog_member':True,'original_source_id':original['id'],'source_id':derived['id'],'original_retrieved_at':original['retrieved_at'],'derived_retrieved_at':derived['retrieved_at'],'derived_source_imported_into_actual_database':False,'original_first_saved_at':None,'derived_first_saved_at':None,'facts':[{k:deepcopy(f[k]) for k in ['id','concept','kind','value','unit','period','scope']} for f in facts]}
    assert not any(e.get('source_id')==derived['id'] for e in old['companies'])
    new=deepcopy(old);new['companies'].append(entry);new['recorded_at']=recorded_at
    new['previous_v42_actual_research_source_connections_historical_snapshot']=deepcopy(old['actual_research_source_connections'])
    new['actual_research_source_connections_snapshot_note']='Historical v42 receipt retained; new derived/facts are not certified connected by this pure candidate helper.'
    new['previous_index']=str(oldpath.relative_to(ROOT));new['previous_index_sha256']=sha(oldpath)
    new['company_source_entry_count']=len(new['companies']);new['fact_count']=old['fact_count']+4
    # Existing per-fact override rule is preserved; do not replace fact original_source_id.
    resolutions=[(e['company_id'],f.get('source_id',e['source_id']),e['original_source_id']) for e in new['companies'] for f in e['facts']]
    new['unique_company_count']=len({r[0] for r in resolutions});new['unique_derived_source_count']=len({r[1] for r in resolutions});new['unique_original_company_source_pair_count']=len({(r[0],r[2]) for r in resolutions})
    new['connection_preparation']={'status':'candidate_only_after_4318_PL_preparation','new_derived_sources':1,'new_reported_facts':4,'financial_model_adoption':False,'actual_DB_connection_verified':False,'root_actual_verification_required_before_publication':True}
    assert new['companies'][:-1]==old['companies'] and sum(len(e['facts']) for e in new['companies'])==new['fact_count']
    with dest.open('x',encoding='utf-8') as f:json.dump(new,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'candidate':str(dest),'SHA256':sha(dest),'counts':{k:new[k] for k in ['fact_count','company_source_entry_count','unique_company_count','unique_derived_source_count','unique_original_company_source_pair_count']}}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--recorded-at',required=True);a=p.parse_args();main(a.output,a.recorded_at)
