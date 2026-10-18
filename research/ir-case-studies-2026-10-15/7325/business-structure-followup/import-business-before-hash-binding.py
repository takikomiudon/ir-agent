"""One-use source classification and research-case bootstrap; no external actions."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import sqlite3, json, sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from ir_agent.models import json_text, validate_source
from ir_agent.store import Store
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.qualitative_research import QualitativeResearch
import research_ir_universe as repo
OUT=Path(__file__).resolve().parent;DB=ROOT/'data/ir-research-2026-10-15.sqlite3'
now=lambda:datetime.now(timezone.utc).isoformat();digest=lambda p:sha256(p.read_bytes()).hexdigest()
load=lambda n:json.loads((OUT/n).read_bytes())
def save(name,value):
    with (OUT/name).open('x') as f:f.write(json_text(value)+'\n')
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':digest(p)}
assert sys.argv[1:]==['--execute'] and not (OUT/'execution-start.json').exists()
assert digest(DB)=='97d58be6ab4a8e52de41fe5d6e82f1048e1ec1c4adc3b99591f9a4e36b3aaaa4'
bundle=load('source-only-bundle.json');assert len(bundle['sources'])==1
source=bundle['sources'][0];assert validate_source(source)==source
quotes=load('quotes.json')['quotes'];case=load('case-record.json');assert len(quotes)==3 and case['conditions']==[]
raw=ROOT/source['metadata']['raw_file'];text=ROOT/source['metadata']['text_file']
assert digest(raw)==source['metadata']['raw_sha256'];assert text.read_bytes().decode()==source['content']
page=repo.Page();page.feed(raw.read_bytes().decode());assert page.extract(source['url'])['text']==source['content']
for q in quotes:
    assert source['content'][q['source_character_start']:q['source_character_end']]==q['quote']
    assert len(source['content'][:q['source_character_start']].encode())==q['source_UTF8_byte_start']
    assert len(source['content'][:q['source_character_end']].encode())==q['source_UTF8_byte_end']
assert sha256(json_text(source).encode()).hexdigest()==case['source_snapshot_sha256']
memory=Store(':memory:');checked=Harness(memory).ingest({'schema_version':1,'companies':[{'id':'jp:7325','name':'Schema check only'}],'sources':[source]});assert checked['sources_added']==1 and memory.source(source['id'])==source;memory.close()
save('parent-acceptance.json',{'recorded_at':now(),'status':'accepted_with_documented_limits','source_schema_memory_ingest_and_raw_text_replay':True,'quoted3_blocks_offsets_match':True,'issuer_operations_supported_only':True,'group_underwriting_absence_commission_regulation_model_fit_unknown':True,'no_investment_rule_added':True,'producer_source_bundle_sha256':digest(OUT/'source-only-bundle.json'),'producer_case_sha256':digest(OUT/'case-record.json'),'actual_DB_written_yet':False})
ro=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True);ro.execute('pragma query_only=on')
assert ro.execute('select count(*) from sources').fetchone()[0]==122
assert ro.execute("select count(*) from jobs where status<>'completed'").fetchone()[0]==0
tables=[r[0] for r in ro.execute("select name from sqlite_master where type='table'")]
before={t:ro.execute('select * from '+t).fetchall() for t in tables}
backup=ROOT/('data/before-7325-business-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.sqlite3');dest=sqlite3.connect(backup);ro.backup(dest);dest.close();ro.close()
save('execution-start.json',{'recorded_at':now(),'database_sha256_before':digest(DB),'backup_path':str(backup.relative_to(ROOT)),'backup_sha256':digest(backup)})
store=Store(str(DB));h=Harness(store);q=QualitativeResearch(store)
save('ingest-result.json',h.ingest(bundle));queued=Intake(store).queue(now(),company_id='jp:7325',limit=1,new_only=True);save('intake-queue.json',queued);assert queued['jobs_created']==1
worker='parent-7325-business-classifier';claim=h.claim(worker,measurement_synthetic=False,caller_namespace='research-session-2026-10-15',request_id='7325-business-intake-20261015');save('intake-claim.json',claim);assert claim['current_lease']['valid_now']
job=store.job(claim['original_response']['job_id']);save('intake-packet.json',job['packet']);assert job['id']==queued['selected'][0]['job_id'] and [s['id'] for s in job['packet']['sources']]==[source['id']]
result={'classifications':[{'source_id':source['id'],'expected_version':0,'kind':'business_description','financial_content':False,'basis_quote':quotes[0]['quote'],'rationale':'会社の保険選択/直営店・FC・技術サービスの定性的事業説明。金額財務・契約負債・規制資本やモデル適合の確認ではない。'}]}
save('classification-input.json',result);save('intake-completed.json',h.complete(job['id'],worker,result,expected_attempt=job['attempts']))
first=dict(store.connection.execute("select * from record_availability where entity_type='source' and entity_id=?",(source['id'],)).fetchone())
checkpoint={'recorded_at':now(),'company_id':'jp:7325','issue_id':case['issue_id'],'source_id':source['id'],'source_snapshot_sha256':case['source_snapshot_sha256'],'case_ref':ref(OUT/'case-record.json'),'quote_ref':ref(OUT/'quotes.json'),'source_first_save_receipt':first,'scope':'Reuse three-block source review after actual source save/classification. Producer file timestamp is not historical DB presence; no new full-document semantic reading.'};save('review-binding-checkpoint.json',checkpoint)
author=ROOT/'third_party/anthropic/skills/thesis-tracker/SKILL.md';aq='Review theses at least quarterly, even when nothing dramatic has happened';assert aq in author.read_bytes().decode()
note={'recorded_at':now(),'company_id':'jp:7325','date':'2027-01-16','timezone':'Asia/Tokyo','basis_quote':'次回の研究管理日は2027-01-16（Asia/Tokyo）とする。','author_quote':aq,'author_ref':ref(author),'adaptation':'Three local calendar months from research date2026-10-16; explicit project management date, not issuer event, author falsification or sale deadline. New source can trigger earlier.'};save('management-basis.json',note)
request={'case_id':'7325-business-model-scope-monitor','company_id':'jp:7325','issue_id':case['issue_id'],'synthetic':False,'enabled':True,'recorded_at':now(),'case_ref':ref(OUT/'case-record.json'),'manifest_ref':ref(OUT/'review-binding-checkpoint.json'),'management_review':{'date':note['date'],'timezone':note['timezone'],'basis_ref':ref(OUT/'management-basis.json'),'basis_quote':note['basis_quote']},'bootstrap_reviews':[{'source_id':source['id'],'source_snapshot_sha256':case['source_snapshot_sha256'],'reviewed_at':checkpoint['recorded_at'],'review_ref':ref(OUT/'review-binding-checkpoint.json')}]};save('case-register-input.json',request)
registered=q.register_case(request,0,research_root=ROOT);save('case-registered.json',registered);assert registered['version']==1 and len(registered['record']['reviewed_sources'])==1
ids=[r[0] for r in store.connection.execute('select distinct case_id from qualitative_case_versions order by case_id')];assert len(ids)==14
current=datetime.now(timezone.utc);queued=q.queue_cases(ids,current.isoformat(),limit=14,now=current);save('all-cases-queue.json',queued);assert queued['jobs_created']==0 and len(queued['skipped'])==14
changes={}
append_tables={'sources','source_classifications','jobs','job_attempts','job_attempt_events','job_request_receipts','record_availability','qualitative_case_versions'}
for table,rows in before.items():
    after=[tuple(r) for r in store.connection.execute('select * from '+table)]
    if table in append_tables:
        aset=set(after);changes[table]=all(tuple(r) in aset for r in rows)
    else:changes[table]=rows==after
assert all(changes.values())
counts={t:store.connection.execute('select count(*) from '+t).fetchone()[0] for t in tables}
assert counts['sources']==123 and all(counts[t]==0 for t in ('theses','questions','replies','decision_policies','position_declarations'))
assert store.source(source['id'])==source
availability=dict(store.connection.execute("select basis,count(*) from record_availability where entity_type='source' group by basis"));assert availability=={'legacy_presence':28,'trusted_insert':95}
assert sum(len(q.show_case(i)['record']['reviewed_sources']) for i in ids)==69
assert store.connection.execute("select count(*) from jobs where status<>'completed'").fetchone()[0]==0
store.close();save('actual-completion.json',{'recorded_at':now(),'status':'completed','actual_counts':counts,'old_rows_preserved_and_unrelated_tables_exact':changes,'source_first_save_receipt':first,'source_availability_counts':availability,'source_snapshot_unchanged':True,'case_heads':14,'case_version_rows':18,'all_case_reviewed_source_entries':69,'management_date':note['date'],'after_review_new_jobs':0,'database_sha256_after':digest(DB),'financial_inputs_verified':False,'model_adopted':False,'new_GETs_this_import_external_sends_orders':0})
print(json_text({'status':'completed','sources':123,'case_heads':14,'case_versions':18,'new_jobs_after_review':0}))
