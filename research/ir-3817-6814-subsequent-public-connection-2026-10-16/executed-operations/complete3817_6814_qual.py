from pathlib import Path
from datetime import datetime,timezone
from contextlib import closing
from hashlib import sha256
import json,sys
r=Path('/workspace/ir-agent');sys.path.insert(0,str(r/'src'))
from ir_agent.store import Store
from ir_agent.harness import Harness
from ir_agent.qualitative_research import QualitativeResearch
from ir_agent.models import json_text
base=r/'research/ir-3817-6814-subsequent-public-connection-2026-10-16';out=base/'qualitative';load=lambda p:json.loads(p.read_bytes());sha=lambda p:sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (out/n).open('x',encoding='utf8') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n');f.flush()
assert not (out/'completion-started.json').exists();save('completion-started.json',{'recorded_at':datetime.now(timezone.utc).isoformat()})
folders={'3817':'subsequent-Q1-public-review-2026-10-16','6814':'subsequent-interim-public-review-2026-10-16'};cases=load(base/'cases-before.json');packets={code:load(out/(code+'-full-packet.json')) for code in folders};results={}
prior=r/'research/ir-case-studies-2026-10-15/3817/ordinary-book-basis-saved-followup-2026-10-16/review.json';prior_accept=prior.parent/'parent-acceptance.json';assert prior_accept.exists();pr=load(prior)
manual=f'既読年次p8/12のfile-only追補を今回の正当jobへ手動継承する: {prior.relative_to(r)} SHA256={sha(prior)} recorded_at={pr["recorded_at"]}、parent SHA256={sha(prior_accept)}、原source={pr["source"]["id"]}/native={pr["source"]["native_sha256"]}。株主資本/OCI/NCI/新株予約権dashの別区分は既答、BPS正式分子/信託調整/provider対応は未解決、逆算/年次443.34/2659.88差替えなし。新pending sourceではない。'
save('3817-prior-additional-reading-handoff.json',{'read_reference':str(prior.relative_to(r)),'SHA256':sha(prior),'original_read_at':pr['recorded_at'],'text':manual,'not_a_new_source_or_financial_adoption':True})
for code,folder in folders.items():
 p=packets[code];src=r/'research/ir-case-studies-2026-10-15'/code/folder;s=p['sources'][0];sid=s['id'];assert s==load(src/'source-only-bundle.json')['sources'][0] and p['pending_source_ids']==[sid] and p['head_version']==cases[code]['version'] and p['config_revision']==1;assert p['source_snapshot_sha256'][sid]==sha256(json_text(s).encode()).hexdigest()
 qq=load(src/'source-quotes.json');quotes=qq['quotes'] if code=='3817' else qq;key='post-quarter-buyback' if code=='3817' else 'interim-full-year-guidance-revised';quote=next(x['quote'] for x in quotes if x['id']==key);assert quote in s['content']
 refs=f'原典/限定読解={src.relative_to(r)}/review.json SHA256={sha(src/"review.json")}、root受入SHA256={sha(src/"parent-acceptance.json")}。公開日と取得/実保存を区別し10月現在の全Web最新性は認証しない。'
 if code=='3817':
  summary='8/12公表Q1の限定4頁を比較し、未取得Q1gapを解消。C1:2026-04-01〜06-30連結Q1 EPS96.69は年次443.34と別期間、当時通期会社予想435.34修正無は予想/版を分離。C2:7/17取得決議・7/21普通株300,000株/1,356,000,000円の実取得は6/30末自己株2,606,114株・Q1平均12,633,888株より後の事象で、上限960,000株/43億円や現在分母へ置換しない。'+refs+' '+manual
  rationale='年次443.34/BPS2659.88・式参考入力を維持。Q1末発行済15,240,000株、自己株2,606,114対前年度末2,606,111、Q1平均12,633,888対前年Q1平均12,633,889を区別。選定頁にQ1BPS直値未確認で、純資産/自己資本/株数から作らない。自己株取得結果は公開既答だが期間全体・実消却・10月現在株数・将来平均分母を認証しない。Q1 CFは未作成で0ではなく、D&AをFCF/維持投資にしない。営業利益/経常/親会社利益の方向や為替・税/NCIを同一視して正常EPSを作らない。旧calendarの中旬/下旬はdate:null・実施未確認を保持。'+refs+' '+manual
 else:
  summary='10/9公表中間短信を限定3頁で比較し、未取得中間本文gapを解消。C1:2026-03-01〜08-31中間EPS314.72と前年度年次529.53を分離。C2:8/31 BPS3103.27/旧2月末2826.61、末/中間平均/前年中間を区別。C3:通期会社予想EPS537.80・修正有は同日通知と整合する当時予想で、中間実績へ代用しない。'+refs
  rationale='年次529.53/BPS2826.61・式参考入力を維持。発行済31,894,554株は両末同じ、自己株は282,050/前末285,730、中間平均31,610,379/前年中間31,601,130を区別し旧年次平均31,604,751/期末分母31,608,824を現在又は予想分母へ流用しない。普通株欄のESOP/split独立注記未確認を不存在とせず、将来EPS分母/BPS正式分子を逆算しない。10/9予想/配当改訂は旧4/9予想と別版で、期末配当95は予想。p2当中間期の会計変更等無は旧年度の会計変更を否定しない。既受入annual p19の会計/軽微≠0の既答は維持し未読へ戻さない。10/19説明会予定を実施/結果にせず、現在価格/正常利益/金融方針/IR価値は未認定。'+refs
 result={'summary':summary,'recorded_at':datetime.now(timezone.utc).isoformat(),'source_reviews':[{'source_id':sid,'snapshot_sha256':p['source_snapshot_sha256'][sid],'read_state':'reviewed','outcome':'unresolved','basis_quote':quote,'rationale':rationale}],'case_observation':{'issue_id':p['case_snapshot']['issue_id'],'outcome':'unresolved','rationale':rationale+'既存C1〜C3を保持し、後発本文のgapだけ解消。元issue全体と金融採用は未解決、Jan16内部管理日は未到来でretain。','evidence_source_ids':[sid]},'management_review_update':{'mode':'retain'}};results[code]=result;save(code+'-worker-result.json',result)
with closing(Store(r/'data/ir-research-2026-10-15.sqlite3')) as s:
 h=Harness(s);q=QualitativeResearch(s);completed=[]
 for i in (1,2):
  worker='root-3817-6814-subsequent-qualitative';claim=h.claim(worker,lease_seconds=600,measurement_synthetic=False,caller_namespace='root:3817-6814-subsequent:20261016',request_id='qualitative-claim-'+str(i));save('claim-'+str(i)+'-success.json',claim);assert not claim['replayed'] and claim['current_lease']['valid_now'];job=s.job(claim['original_response']['job_id']);code=job['company_id'][3:];assert code in results and code not in completed;save(code+'-job-at-claim.json',job);assert job['packet']==packets[code] and q.show_case(cases[code]['case_id'])==cases[code]
  done=h.complete(job['id'],worker,results[code],expected_attempt=job['attempts']);save(code+'-completion-success.json',done);assert done['status']=='completed';after=q.show_case(cases[code]['case_id']);save(code+'-case-after.json',after);assert after['version']==cases[code]['version']+1 and after['config_revision']==1 and len(after['record']['reviewed_sources'])==len(cases[code]['record']['reviewed_sources'])+1;assert after['record']['management_review']==cases[code]['record']['management_review'];completed.append(code)
 requeued=q.queue_cases([cases[x]['case_id'] for x in folders],datetime.now(timezone.utc).isoformat(),limit=2);save('requeue-success.json',requeued);assert requeued['jobs_created']==0
 save('completed.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'company_ids':completed,'requeued':0})
print(json.dumps({'completed':completed,'main_DB_SHA256':sha(r/'data/ir-research-2026-10-15.sqlite3')}))
