"""Three finite memory-only v2 guard probes using existing synthetic fixtures."""
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
from unittest.mock import patch
import json,sys
R=Path(__file__).resolve().parents[2];B=Path(__file__).resolve().parent
sys.path[:0]=[str(R/'src'),str(R/'tests')]
from ir_agent.models import json_text
from test_dependency_information_gates import DependencyInformationGatesTests,clock

def checkpoint():
 manifest=json.loads((B/'source-snapshots-v2.json').read_bytes())
 for x in manifest['files']:
  assert sha256((R/x['snapshot_path']).read_bytes()).hexdigest()==x['sha256']
  assert (R/x['snapshot_path']).read_bytes()==(R/x['production_path']).read_bytes()
 return {'manifest_sha256':sha256((B/'source-snapshots-v2.json').read_bytes()).hexdigest(),'source_sha256':{x['production_path']:x['sha256']for x in manifest['files']}}
def setup():
 t=DependencyInformationGatesTests();t.setUp();assert t.store.connection.execute('PRAGMA database_list').fetchone()['file']==''
 return t

def run():
 before=checkpoint();cases=[]
 t=setup()
 try:
  t.add_source_snapshot(None,second_parent=True);t.send_and_receive(legacy=True);t.correction(status='potential_nonpublic')
  source=deepcopy(t.snapshot_source);thesis=deepcopy(t.snapshot_thesis);req=t.evaluation();dump=t.dump()
  with patch('ir_agent.information_review.current_evaluation_view',side_effect=ValueError('independent synthetic view failure')):
   try:t.harness.evaluate_reply(req,now=clock(req['recorded_at']))
   except ValueError as e:assert str(e)=='independent synthetic view failure'
   else:raise AssertionError('Expected injected rollback error')
  assert t.dump()==dump
  held=t.harness.evaluate_reply(req,now=clock(req['recorded_at']));sh=held['dependency_source_information_holds'];ch=held['dependency_information_holds'];assert not held['applied']and held['information_status']=='public_clarification'
  assert set(sh)=={source['id']}and sh[source['id']]['information_status']is None
  assert sh[source['id']]['source_sha256']==sha256(json_text(source).encode()).hexdigest()
  assert 'reply_id'not in sh[source['id']]and'version'not in sh[source['id']]and ch[t.first_reply['id']]['version']==1
  assert t.store.source(source['id'])==source and t.store.thesis('demo-services')==thesis
  t.correction(version=1,status='public_clarification',at='2026-10-09T17:11:00+09:00')
  retry=dict(req,expected_evaluation_version=1,recorded_at='2026-10-09T17:12:00+09:00')
  still=t.harness.evaluate_reply(retry,now=clock(retry['recorded_at']));assert not still['applied']and 'dependency_information_holds'not in still and 'dependency_source_information_holds'in still
  assert t.store.source(source['id'])==source and t.store.thesis('demo-services')==thesis
  cases.append({'case':'explicit_null_IR_second_parent_and_distinct_correction_holds','source_type':'ir_reply','original_status':None,'before_and_after_thesis_version':thesis['version'],'held_applied':held['applied'],'incoming_status':held['information_status'],'source_hold_key':list(sh),'source_hash_exact':True,'source_hold_has_reply_id_or_version':False,'correction_reply_id':t.first_reply['id'],'correction_version':ch[t.first_reply['id']]['version'],'public_reconfirmation_still_source_held':not still['applied'],'old_source_and_model_unchanged':True,'injected_hold_failure_full_dump_rollback':True})
 finally:t.doCleanups()
 t=setup()
 try:
  t.add_source_snapshot(None,source_type='public_disclosure');t.send_and_receive();source=deepcopy(t.snapshot_source);req=t.evaluation();r=t.harness.evaluate_reply(req,now=clock(req['recorded_at']))
  assert r['applied']and 'dependency_source_information_holds'not in r and t.store.source(source['id'])==source
  cases.append({'case':'explicit_null_public_disclosure_classification_is_not_an_IR_hold','source_type':'public_disclosure','original_status':None,'applied':r['applied'],'after_thesis_version':t.store.thesis('demo-services')['version'],'old_source_unchanged':True,'scope':'Synthetic type/null classification contrast only; not assertion that relabelling real IR text public is valid.'})
 finally:t.doCleanups()
 t=setup()
 try:
  t.send_and_receive();source=deepcopy(t.original_source);thesis=deepcopy(t.original);t.correction(status='potential_nonpublic');req=t.evaluation(recorded='2026-10-09T17:08:00+09:00');r=t.harness.evaluate_reply(req,now=clock('2026-10-09T17:10:00+09:00'))
  assert not r['applied']and t.store.thesis('demo-services')==thesis and r['information_status']=='public_clarification'
  t.correction(version=1,status='public_clarification',at='2026-10-09T17:11:00+09:00');assert t.store.thesis('demo-services')==thesis
  dump=t.dump();changes=t.store.connection.total_changes;oldretry=t.harness.evaluate_reply(req,now=clock('2026-10-09T17:12:00+09:00'));assert oldretry['status']==r['status']and t.dump()==dump and t.store.connection.total_changes==changes
  retry=dict(req,expected_evaluation_version=1,recorded_at='2026-10-09T17:12:00+09:00');applied=t.harness.evaluate_reply(retry,now=clock(retry['recorded_at']))
  assert applied['applied']and t.store.thesis('demo-services')['version']==3 and t.store.source(source['id'])==source
  assert applied['decision_review']['context']['information_review_versions'][t.first_reply['id']]==2
  dump=t.dump();changes=t.store.connection.total_changes;again=t.harness.evaluate_reply(retry,now=clock(retry['recorded_at']));assert again==applied and t.dump()==dump and t.store.connection.total_changes==changes
  cases.append({'case':'RG01_backdated_new_attempt_and_explicit_public_reassessment_recovery','original_source_status':source['metadata']['information_status'],'initial_held':not r['applied'],'incoming_status':r['information_status'],'old_model_stays_until_new_request':True,'public_correction_alone_did_not_apply':True,'old_request_retry_no_writes':True,'new_CAS_request_applies':applied['applied'],'reviewed_correction_version':2,'after_thesis_version':3,'immutable_original_source':True,'successful_request_retry_no_writes':True})
 finally:t.doCleanups()
 after=checkpoint();assert after==before
 return {'schema_version':1,'status':'v2_three_finite_memory_probes_passed','checkpoint_before_and_after':before,'cases':cases,'execution':{'memory_cases':3,'actual_DB_accesses':0,'new_GETs':0,'production_test_or_old_file_edits':0,'full_suite_runs':0,'new_financial_rule':0}}
if __name__=='__main__':
 r=run();p=Path(sys.argv[1])if len(sys.argv)>1 else Path('/tmp/ir_reply_dependency_independent_probes_v2.json');p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
