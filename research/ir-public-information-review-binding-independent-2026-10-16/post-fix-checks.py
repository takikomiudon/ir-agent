"""Recheck only F1/F2 after separately scoped producer fix."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'src'),str(root/'tests')]
from test_public_information_review import PublicInformationPersistenceTests,source,binding,BEFORE,SENT
from ir_agent.models import validate_source
fix=root/'research/ir-public-information-review-binding-fix-2026-10-16/implementation.json';impl=json.loads(fix.read_bytes());pins={v['path']:v['sha256'] for v in impl['after_files']};assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in pins.items());results=[]
f=PublicInformationPersistenceTests('test_binding_freezes_scope_and_keeps_review_roots_outside_financial_sources');f.setUp()
try:
 depth=1100;chain=[]
 for i in range(depth):
  md={'synthetic':True}
  if i+1<depth:md['original_source_id']='independent-parent-'+str(i+1)
  chain.append(source('independent-parent-'+str(i),company=f.company,metadata=md))
 leaf=source('independent-review-root',company=f.company,metadata={'synthetic':True,'original_source_id':chain[0]['id']})
 for s in [*reversed(chain),leaf]:f.store.put_source(validate_source(s),now=BEFORE)
 q=f.question(contracted=False);q['public_information_review']=binding(leaf);saved=f.save(q);c=f.check(saved);assert c['reason_codes']==[];assert len(c['availability_at_review'])==1101;assert all(v['available'] is True for v in c['availability_at_review'].values());sent=f.harness.mark_sent(q['id'],SENT.isoformat(),now=SENT);assert sent['status']=='awaiting_reply';assert f.save(q)['public_information_review_check']==saved['public_information_review_check'];results.append({'id':'F1-persistent-long-DAG','status':'resolved_in_finite_counterexample','same_1100_ancestor_input':True,'saved_and_synthetic_sent_state_without_recursion':True,'closure_receipts':1101,'reason_codes':c['reason_codes'],'original_request_retry_keeps_frozen_check':True})
finally:f.doCleanups()
f=PublicInformationPersistenceTests('test_binding_freezes_scope_and_keeps_review_roots_outside_financial_sources');f.setUp()
try:
 reply=f.ir_source();wrong=source('samecompany-wrong-reply-text',company=f.company,source_type='ir_reply',content='A different response not found in the stored reply raw_text.',metadata={'synthetic':True,'reply_id':reply['id'],'information_status':'public_clarification'});f.store.put_source(validate_source(wrong),now=BEFORE);f.qa=wrong;q=f.question(contracted=False);snap=f.snapshot()
 try:f.save(q)
 except ValueError as e:assert 'differs from its saved reply' in str(e);error=str(e)
 else:raise AssertionError('different samecompany reply text still accepted')
 assert f.snapshot()==snap;results.append({'id':'F2-samecompany-reply-content','status':'resolved_in_finite_counterexample','same_different_body_input_rejected':True,'error_type':'ValueError','error':error,'memory_DB_unchanged':True})
finally:f.doCleanups()
result={'recorded_at':datetime.now(timezone.utc).isoformat(),'fix_implementation':str(fix.relative_to(root)),'fix_implementation_sha256':hashlib.sha256(fix.read_bytes()).hexdigest(),'fixed_file_pins':pins,'checks':results,'GETs':0,'actual_DB_connections_or_writes':0,'synthetic_memory_DBs':2,'production_code_changes':0,'fullsuite_run':False,'scope':'Only prior F1/F2 inputs rechecked; no new branches/financial adoption/IRsend. Root runs fullsuite and broader legacy byte comparison.'};Path(__file__).with_name('post-fix-results.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode());print(json.dumps(result,ensure_ascii=False,indent=2))
