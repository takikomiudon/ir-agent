"""Finite synthetic memory-only probes for the stable RG01 correction gate.

No real DB, network, new financial inputs, source edits or full suite. Existing
synthetic values and helper setup are reused; outcomes below are read separately
from the producer's tests rather than reporting their full suite as rerun.
"""
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
import json,sys
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'src'),str(R/'tests')]
from test_dependency_information_gates import DependencyInformationGatesTests,clock
from ir_agent.decision_lifecycle import DecisionLifecycle

def setup():
 t=DependencyInformationGatesTests();t.setUp();assert str(t.store.connection.execute('PRAGMA database_list').fetchone()['file'])==''
 return t

def new_unclear_origin(t):
 s=deepcopy(t.original_source);s['id']='independent-original-unclear';s['retrieved_at']='2026-10-09T17:03:00+09:00';s['metadata']['information_status']='unclear'
 th=deepcopy(t.original);th.update(version=3,recorded_at=s['retrieved_at'],evidence_ids=[*th['evidence_ids'],s['id']])
 t.harness.ingest({'schema_version':1,'sources':[s],'theses':[th]},now=clock(s['retrieved_at']))
 return th

def run():
 out=[]
 t=setup()
 try:
  t.send_and_receive();t.correction(at='2026-10-09T17:09:00+09:00');th=t.store.thesis('demo-services');oldsource=t.store.source(t.original_source['id']);reply=t.store.reply(t.second_reply['id'])
  req=t.evaluation(recorded='2026-10-09T17:08:00+09:00');r=t.harness.evaluate_reply(req,now=clock('2026-10-09T17:10:00+09:00'))
  assert r['applied']is False and r['information_status']=='public_clarification'and t.store.thesis('demo-services')==th and t.store.source(oldsource['id'])==oldsource and t.store.reply(reply['id'])==reply
  before=t.dump();retry=t.harness.evaluate_reply(req,now=clock('2026-10-09T17:10:00+09:00'));assert t.dump()==before and retry==r
  out.append({'case':'backdated_public_new_reply_on_current_corrected_dependency','applied':r['applied'],'own_information_status':r['information_status'],'dependency_reply_ids':list(r['dependency_information_holds']),'thesis_unchanged':True,'old_source_and_new_reply_unchanged':True,'exact_request_retry_no_new_write':True,'status':r['status']})
 finally:t.doCleanups()
 t=setup()
 try:
  th=new_unclear_origin(t);q=t.new_question();saved=t.harness.add_question(q,now=clock(q['created_at']));assert saved['decision_contract']['preflight']['question_value']=='needs_review'
  out.append({'case':'original_metadata_unclear_no_correction_contracted_question','correction_hold_rows':DecisionLifecycle(t.store).dependency_information_holds(th,as_of='2026-10-09T17:10:00+09:00'),'pure_preflight':saved['decision_contract']['preflight']['question_value'],'notes':'Pure source-publicity guards already hold; correction overlay alone is not a complete source-publicity validator.'})
 finally:t.doCleanups()
 t=setup()
 try:
  th=new_unclear_origin(t);t.send_and_receive(legacy=True);req=t.evaluation();r=t.harness.evaluate_reply(req,now=clock(req['recorded_at']))
  assert r['applied']is True and t.store.thesis('demo-services')['version']==4 and r['action']=='unresolved'and r['decision_status']=='missing_decision_contract'
  out.append({'case':'original_metadata_unclear_no_correction_legacy_question','before_thesis_version':3,'after_thesis_version':4,'applied':r['applied'],'own_information_status':r['information_status'],'action':r['action'],'decision_status':r['decision_status'],'dependency_hold':r.get('dependency_information_holds'),'source_metadata_status':'unclear','review_classification_rows':0,'classification':'adjacent pre-existing legacy source-publicity gap, not a regression of the new classification-correction gate'})
 finally:t.doCleanups()
 return {'schema_version':1,'status':'three_finite_memory_probes_complete','cases':out,'execution':{'memory_SQLite_cases':3,'actual_DB_accesses':0,'new_GETs':0,'production_or_existing_test_or_research_edits':0,'full_suite_runs':0}}
if __name__=='__main__':
 result=run();output=Path(sys.argv[1])if len(sys.argv)>1 else Path('/tmp/ir_reply_dependency_independent_probes.json');output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
