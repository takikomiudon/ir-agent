"""Single synthetic same-company reply-content provenance counterexample."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import sys,json
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'src'),str(root/'tests')]
from test_public_information_review import PublicInformationPersistenceTests,source,BEFORE,SENT
from ir_agent.models import validate_source
from ir_agent.decision_lifecycle import DecisionLifecycle
from ir_agent.information_review import add_assessment
f=PublicInformationPersistenceTests('test_binding_freezes_scope_and_keeps_review_roots_outside_financial_sources');f.setUp()
try:
 reply=f.ir_source();wrong=source('samecompany-wrong-reply-text',company=f.company,source_type='ir_reply',content='A different response not found in the stored reply raw_text.',metadata={'synthetic':True,'reply_id':reply['id'],'information_status':'public_clarification'});f.store.put_source(validate_source(wrong),now=BEFORE);f.qa=wrong;q=f.question(contracted=False);saved=f.save(q);initial=f.check(saved);assert wrong['content']!=reply['raw_text'];assert initial['reason_codes']==[]
 when=SENT+timedelta(minutes=1);add_assessment(f.store,{'reply_id':reply['id'],'expected_version':0,'information_status':'unclear','basis_quote':reply['raw_text'],'rationale':'Synthetic correction to the OTHER stored reply text.','recorded_at':when.isoformat()},now=when.isoformat())
 after=DecisionLifecycle(f.store).review_public_information(q,as_of=SENT.isoformat(),now=(SENT+timedelta(minutes=2)).isoformat());assert after['information_reviews']['at_runtime'][reply['id']]['information_status']=='unclear';assert 'public_information_review_information_held_for_review' in after['reason_codes']
 result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'counterexample','same_company':True,'source_content_equals_bound_reply_raw_text':False,'initial_draft_accepted_with_reason_codes':initial['reason_codes'],'later_correction_subject':reply['id'],'later_other_reply_correction_was_attached':True,'reason_codes':after['reason_codes'],'scope':'No semantic/financial claims. Stored reply content identity is not verified before the new field consumes that reply correction lineage.','actual_DB_or_GET_or_code_changes':0}
finally:f.doCleanups()
Path(__file__).with_name('reply-content-results.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode());print(json.dumps(result,ensure_ascii=False,indent=2))
