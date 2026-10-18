"""Independent bounded synthetic counterexamples; no operational DB or network."""
from pathlib import Path
from copy import deepcopy
from datetime import timedelta,datetime,timezone
import importlib.util,json,hashlib,sys,traceback
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'src'));sys.path.insert(0,str(root/'tests'))
from ir_agent.decision import evaluate_ir_plan
from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.models import validate_source,json_text
from test_decision import plan
from test_public_information_review import PublicInformationPersistenceTests,source,binding,BEFORE,REVIEWED,CREATED,SAVED,SENT
out={'recorded_at':datetime.now(timezone.utc).isoformat(),'GETs':0,'actual_DB_connections_or_writes':0,'synthetic_memory_only':True,'checks':[]}
# Compare actual frozen prior decision.py; no new optional field is present.
before=root/'research/ir-public-information-review-binding-2026-10-16/before/src/ir_agent/decision.py';spec=importlib.util.spec_from_file_location('ir_agent._independent_before_decision',before);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
comp=[]
for mode in ('plain','same_named_legacy_extra','found_status'):
 v=plan()
 if mode=='same_named_legacy_extra':v['question']['public_information_review_check']={'answer_absence_verified':True,'reason_codes':['legacy-nonconsumed']}
 if mode=='found_status':v['question']['public_answer_status']='found'
 pre=mod.evaluate_ir_plan(v);post=evaluate_ir_plan(v);assert pre==post;comp.append({'variant':mode,'exact_JSON_equal':True,'sha256':hashlib.sha256(json_text(post).encode()).hexdigest()})
out['checks'].append({'id':'legacy_pure_differential','status':'pass','cases':comp,'scope':'Frozen prior decision.py with current no-newfield models validator; conditional model change separately read. No older packages imported or production code altered.'})
# An unclear review-time correction later reaffirmed before creation still holds.
f=PublicInformationPersistenceTests('test_binding_freezes_scope_and_keeps_review_roots_outside_financial_sources');f.setUp()
try:
 f.ir_source();f.correct('unclear',REVIEWED-timedelta(seconds=1));f.correct('public_clarification',REVIEWED+timedelta(seconds=1),version=1);q=f.question(contracted=False);saved=f.save(q);c=f.check(saved);assert c['information_reviews']['at_review']['prior-reply']['information_status']=='unclear';assert c['information_reviews']['at_boundary']['prior-reply']['information_status']=='public_clarification';assert 'public_information_review_information_held_for_review' in c['reason_codes'];snap=f.snapshot()
 try:f.harness.mark_sent(q['id'],SENT.isoformat(),now=SENT)
 except ValueError as e:assert 'needs review' in str(e)
 else:raise AssertionError('review-time hold accepted at send')
 assert snap==f.snapshot();out['checks'].append({'id':'review_time_only_correction','status':'pass','at_review':'unclear','at_boundary_and_runtime':'public_clarification','new_sent_record_rejected_and_memory_DB_unchanged':True})
finally:f.doCleanups()
# Pure accepts the existing dedicated-test 1100-parent graph; persisted review
# invokes the reused receipt walker. Record its actual outcome without repair.
f=PublicInformationPersistenceTests('test_binding_freezes_scope_and_keeps_review_roots_outside_financial_sources');f.setUp()
try:
 depth=1100;chain=[]
 for i in range(depth):
  md={'synthetic':True}
  if i+1<depth:md['original_source_id']='independent-parent-'+str(i+1)
  chain.append(source('independent-parent-'+str(i),company=f.company,metadata=md))
 leaf=source('independent-review-root',company=f.company,metadata={'synthetic':True,'original_source_id':chain[0]['id']})
 for s in [*reversed(chain),leaf]:f.store.put_source(validate_source(s),now=BEFORE)
 q=f.question(contracted=False);q['public_information_review']=binding(leaf);snap=f.snapshot()
 try:
  saved=f.save(q);out['checks'].append({'id':'persistent_long_DAG','status':'pass','ancestor_count':depth,'reasons':f.check(saved)['reason_codes']})
 except Exception as e:
  out['checks'].append({'id':'persistent_long_DAG','status':'counterexample','ancestor_count':depth,'error_type':type(e).__name__,'error':str(e),'memory_DB_unchanged_after_rejected_save':snap==f.snapshot(),'traceback_tail':traceback.format_exc().splitlines()[-14:]})
finally:f.doCleanups()
path=Path(__file__).with_name('synthetic-results.json');path.write_bytes((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode());print(json.dumps(out,ensure_ascii=False,indent=2))
