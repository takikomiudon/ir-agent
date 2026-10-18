"""One-use operator; no retrieval, messaging, financial adoption or orders."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json, sqlite3, sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'src'))
from ir_agent.models import json_text
from ir_agent.store import Store
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.qualitative_research import QualitativeResearch
OUT=Path(__file__).resolve().parent;DB=ROOT/'data/ir-research-2026-10-15.sqlite3'
now=lambda:datetime.now(timezone.utc).isoformat()
def save(name,value):
    with (OUT/name).open('x') as f:f.write(json_text(value)+'\n')
load=lambda name:json.loads((OUT/name).read_bytes())
assert sys.argv[1:]==['--execute'] and not (OUT/'execution-start.json').exists()
assert sha256(DB.read_bytes()).hexdigest()=='90307d2c650642e7eff6150ee2877ae49d603a9192ccce45cba46b01c9330555'
bundle=load('source-only-bundle.json');source=bundle['sources'][0]
assert len(bundle['sources'])==1 and load('review.json')['semantic_pages_and_images']==[18,19,20]
ro=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True);ro.execute('pragma query_only=on')
assert ro.execute('select count(*) from sources').fetchone()[0]==121
assert ro.execute("select count(*) from jobs where status<>'completed'").fetchone()[0]==0
before={t:ro.execute('select * from '+t).fetchall() for t in ('companies','sources','source_classifications','qualitative_case_versions')}
backup=ROOT/('data/before-5831-policy-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.sqlite3')
dest=sqlite3.connect(backup);ro.backup(dest);dest.close();ro.close()
save('execution-start.json',{'recorded_at':now(),'backup_path':str(backup.relative_to(ROOT)),
                            'backup_sha256':sha256(backup.read_bytes()).hexdigest(),
                            'database_main_sha256_before':sha256(DB.read_bytes()).hexdigest(),
                            'independent_semantic_review_completed':False})
store=Store(str(DB));h=Harness(store);q=QualitativeResearch(store);case='5831-financial-structure-monitor'
old=q.show_case(case);assert old['version']==2;save('case-before.json',old)
save('ingest-result.json',h.ingest(bundle))
queued=Intake(store).queue(now(),company_id='jp:5831',limit=1,new_only=True);save('intake-queue.json',queued)
assert queued['jobs_created']==1
worker='parent-5831-policy-classifier'
claim=h.claim(worker,measurement_synthetic=False,caller_namespace='research-session-2026-10-15',request_id='5831-capital-policy-intake-20261015')
save('intake-claim.json',claim);assert claim['current_lease']['valid_now']
job=store.job(claim['original_response']['job_id']);save('intake-packet.json',job['packet'])
assert job['id']==queued['selected'][0]['job_id'] and [s['id'] for s in job['packet']['sources']]==[source['id']]
result={'classifications':[{'source_id':source['id'],'expected_version':0,'kind':'earnings_presentation','financial_content':True,
                           'basis_quote':'株主還元方針','rationale':'公式決算説明資料。公表資本/還元方針と金融入力の採用を区別する。意味確認はp18–20のみ。'}]}
save('classification-input.json',result);save('intake-completed.json',h.complete(job['id'],worker,result,expected_attempt=job['attempts']))
current=datetime.now(timezone.utc);queued=q.queue_cases([case],current.isoformat(),now=current);save('qualitative-queue.json',queued)
assert queued['jobs_created']==1
worker='parent-5831-policy-reviewer'
claim=h.claim(worker,measurement_synthetic=False,caller_namespace='research-session-2026-10-15',request_id='5831-capital-policy-review-20261015')
save('qualitative-claim.json',claim);assert claim['current_lease']['valid_now']
job=store.job(claim['original_response']['job_id']);packet=job['packet'];save('qualitative-packet.json',packet)
assert packet['pending_source_ids']==[source['id']] and packet['prior_review']['case_version']==2
save('worker-view.json',q.worker_packet(job['id']))
quotes=load('quotes.json')
result={'summary':'会社の配当・自己株取得・評価差額金の公表方針を確認。資本比率の時点/最終化基準を区別し、年間再投資は未解決として保持。',
        'recorded_at':now(),'source_reviews':[{'source_id':source['id'],'snapshot_sha256':packet['source_snapshot_sha256'][source['id']],
        'read_state':'reviewed','outcome':'supports','basis_quote':quotes[2]['quote'],
        'rationale':'p18/19/20を原文と画像で照合。公表方針・予想は資料の値として保持し、残る26頁の意味確認や将来再投資の確定とはしない。'}],
        'case_observation':{'issue_id':old['record']['issue_id'],'outcome':'supports',
        'rationale':'資本定義と株主分配を分ける既存モデル点検を支持する。p20の期末CET1予想14.29%と最終化完全適用試算13.56%、Q1実績16.24%と同試算14.00%は別基準/時点。p19の配当方針50%以上・買戻し上限300億円は既答で再質問しない。これらから年間規制資本再投資額やFCFEは確定せず、金融仮説や売買条件は作らない。',
        'evidence_source_ids':[source['id']]},'management_review_update':{'mode':'retain'}}
save('qualitative-result-input.json',result);save('qualitative-completed.json',h.complete(job['id'],worker,result,expected_attempt=job['attempts']))
after=q.show_case(case);save('case-after.json',after);assert after['version']==3 and len(after['record']['reviewed_sources'])==5
current=datetime.now(timezone.utc);queued=q.queue_cases([case],current.isoformat(),now=current);save('after-review-queue.json',queued);assert queued['jobs_created']==0
unchanged={t:all(tuple(r) in {tuple(n) for n in store.connection.execute('select * from '+t)} for r in rows) for t,rows in before.items()}
assert all(unchanged.values())
tables=('companies','sources','source_classifications','jobs','job_attempts','job_attempt_events','job_request_receipts','qualitative_case_versions','theses','questions','replies','decision_policies','position_declarations')
counts={t:store.connection.execute('select count(*) from '+t).fetchone()[0] for t in tables}
assert counts['sources']==122 and all(counts[t]==0 for t in ('theses','questions','replies','decision_policies','position_declarations'))
assert store.connection.execute("select count(*) from jobs where status<>'completed'").fetchone()[0]==0
receipt=dict(store.connection.execute("select * from record_availability where entity_type='source' and entity_id=?",(source['id'],)).fetchone())
availability=dict(store.connection.execute("select basis,count(*) from record_availability where entity_type='source' group by basis"))
assert store.source(source['id'])==source
store.close()
save('actual-completion.json',{'recorded_at':now(),'status':'completed','actual_counts':counts,
    'source_availability_counts':availability,'new_source_first_save_receipt':receipt,'old_rows_preserved':unchanged,
    'case_head_version':3,'case_reviewed_sources':5,'case_heads':13,'all_case_reviewed_source_entries':68,
    'prior_review_frozen':True,'after_review_new_jobs':0,'source_snapshot_unchanged':True,
    'database_main_sha256_after':sha256(DB.read_bytes()).hexdigest(),'financial_inputs_verified':False,
    'model_adopted':False,'independent_semantic_review_completed':False,'external_sends_orders':0})
print(json_text({'status':'completed','actual_counts':counts,'case_head_version':3,'after_review_new_jobs':0}))
