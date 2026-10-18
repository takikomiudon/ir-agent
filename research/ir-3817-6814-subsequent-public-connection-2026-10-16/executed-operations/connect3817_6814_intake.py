from pathlib import Path
from datetime import datetime,timezone
from contextlib import closing
from collections import Counter
from hashlib import sha256
import json,sqlite3,sys
ROOT=Path('/workspace/ir-agent');sys.path.insert(0,str(ROOT/'src'))
from ir_agent.store import Store
from ir_agent.harness import Harness
from ir_agent.intake import Intake
from ir_agent.qualitative_research import QualitativeResearch
DB=ROOT/'data/ir-research-2026-10-15.sqlite3';OUT=ROOT/'research/ir-3817-6814-subsequent-public-connection-2026-10-16'
EXPECTED='c3bdbbf82f4e88553e8bb1dec89cc42488c4a5147f228cb4da6b4e0d95ccf93d'
FOLDERS={'3817':'subsequent-Q1-public-review-2026-10-16','6814':'subsequent-interim-public-review-2026-10-16'}
now=lambda:datetime.now(timezone.utc);sha=lambda p:sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
def save(name,value):
 with (OUT/name).open('x',encoding='utf8') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n');f.flush()
def rows(c):return {n:Counter(tuple(v) for v in c.execute('select * from "'+n.replace('"','""')+'"')) for n, in c.execute("select name from sqlite_master where type='table'")}
def schema(c):return [tuple(v) for v in c.execute('select type,name,tbl_name,sql from sqlite_master order by type,name')]
assert sha(DB)==EXPECTED and not OUT.exists()
sources={};pins={}
for code,folder in FOLDERS.items():
 src=ROOT/'research/ir-case-studies-2026-10-15'/code/folder;accept=load(src/'parent-acceptance.json');assert accept['accepted_for']=='public_source_intake_and_existing_case_comparison_only'
 b=load(src/'source-only-bundle.json');assert len(b['sources'])==1;s=b['sources'][0];assert s['company_id']=='jp:'+code and s['source_type']=='public_disclosure';assert s['content'].encode()==(src/s['metadata']['extraction']['saved_file']).read_bytes();sources[code]=s;pins[str((src/'source-only-bundle.json').relative_to(ROOT))]=sha(src/'source-only-bundle.json')
OUT.mkdir();save('started.json',{'recorded_at':now().isoformat(),'DB_before_SHA256':EXPECTED,'source_bundle_pins':pins})
backup=ROOT/'data/backups/ir-research-before-3817-6814-subsequent-public-2026-10-16.sqlite3';assert not backup.exists()
with closing(sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True)) as c:
 c.execute('pragma query_only=on');c.execute('begin');before=rows(c);old_schema=schema(c);assert len(before)==30 and sum(before['sources'].values())==263 and sum(before['jobs'].values())==183
 assert c.execute("select count(*) from jobs where status!='completed'").fetchone()[0]==0
 with closing(sqlite3.connect(backup)) as copy:c.backup(copy);assert rows(copy)==before and schema(copy)==old_schema
 c.rollback()
with closing(Store(DB)) as store:
 assert rows(store.connection)==before and schema(store.connection)==old_schema;h=Harness(store);q=QualitativeResearch(store);cases={code:q.show_case(code+'-reported-annual-per-share-basis-monitor') for code in sources};save('cases-before.json',cases);assert [(cases[x]['version'],cases[x]['config_revision']) for x in ('3817','6814')]==[(3,1),(5,1)]
 inserted=h.ingest({'schema_version':1,'companies':[],'sources':list(sources.values()),'theses':[]},now=now());save('ingest-success.json',inserted);assert inserted=={'companies':0,'sources_added':2,'theses_added':0}
 for code,s in sources.items():
  boundary=now();queued=Intake(store).queue(boundary.isoformat(),company_id='jp:'+code,new_only=True,now=boundary);save(code+'-intake-queue-success.json',queued);assert queued['jobs_created']==1 and queued['selected'][0]['source_count']==1
  worker='root-'+code+'-subsequent-public-intake';claim=h.claim(worker,lease_seconds=600,measurement_synthetic=False,caller_namespace='root:3817-6814-subsequent:20261016',request_id=code+'-intake-claim-1');save(code+'-intake-claim-success.json',claim);assert not claim['replayed'] and claim['current_lease']['valid_now'];job=store.job(claim['original_response']['job_id']);save(code+'-intake-job-at-claim.json',job);assert job['packet']['sources']==[s]
  quote=s['content'].splitlines()[0].strip();assert '決算短信' in quote
  result={'classifications':[{'source_id':s['id'],'expected_version':0,'kind':'financial_statement','financial_content':True,'basis_quote':quote,'rationale':'公式後発短信の原文。全文保存と限定意味/画像頁を区別し、年次実績・新期累計・当時会社予想・平均/末株式basisの比較に使う。現在予想の完全性、年次値の置換、金融入力採用を認定しない。'}]};save(code+'-intake-result.json',result)
  done=h.complete(job['id'],worker,result,expected_attempt=job['attempts']);save(code+'-intake-completion-success.json',done);assert done['status']=='completed'
 after=rows(store.connection);deltas={'sources':2,'record_availability':2,'source_classifications':2,'jobs':2,'job_attempts':2,'job_attempt_events':4,'job_request_receipts':2};assert set(after)==set(before) and schema(store.connection)==old_schema
 for t in before:assert not before[t]-after[t],t;assert sum(after[t].values())-sum(before[t].values())==deltas.get(t,0),t
 assert all(q.show_case(cases[x]['case_id'])==cases[x] for x in cases)
 save('intake-verification.json',{'verified_at':now().isoformat(),'old_all_rows_schema_and_cases_preserved':True,'deltas':deltas,'source_ids':{x:s['id'] for x,s in sources.items()}})
print(json.dumps({'stage':'two_sources_intake_completed_cases_unchanged','main_DB_SHA256':sha(DB)}))
