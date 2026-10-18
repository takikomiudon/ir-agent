"""Offline preparation only. Does not import Store, open DB, fetch, or run reports."""
from pathlib import Path
import json,hashlib,sys
from copy import deepcopy
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from ir_agent.models import json_text,validate_source
from ir_agent.catalyst_schedule import _validate_requests
B=ROOT/'research/ir-case-studies-2026-10-15'
load=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=lambda s:hashlib.sha256(json_text(s).encode()).hexdigest()
inputs={}
def read(p):
 inputs[str(p.relative_to(ROOT))]=sha(p)
 return load(p)
CHECK = '--check' in sys.argv
def save(name,x):
 data=(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
 if CHECK: assert (OUT/name).read_bytes()==data, name+' differs'
 else: (OUT/name).write_bytes(data)
def folder(c):return B/c/'public-catalyst-calendar-discovery-2026-10-16'
def pin(p):inputs[str(p.relative_to(ROOT))]=sha(p);return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
sources={};new=[];records=[]
for code in ['2929','4318','3817','6200','6814']:
 p=folder(code)/'source-only-bundle.json';bundle=read(p);assert bundle['theses']==[] and len(bundle['sources'])==1
 s=bundle['sources'][0];assert s['company_id']=='jp:'+code;assert validate_source(s)==s;assert s['published_at'] is None
 sources[code]=s;new.append(deepcopy(s));records.append({'company_id':s['company_id'],'source_id':s['id'],'native_source_SHA256':native(s),'original_bundle':pin(p),'original_object_pointer':'$.sources[0]','original_whole_object_preserved':True,'original_bundle_company_stub_count':len(bundle['companies']),'company_stubs_omitted_from_aggregate':True,'url':s['url'],'published_at':s['published_at'],'retrieved_at':s['retrieved_at'],'actual_DB_first_saved_at':None,'DB_presence':'pending_ROOT_write_not_observed_here','classification':'pending_ROOT_intake_not_fabricated'})
# Existing sources referenced, not included for ingestion.
p=B/'1518/catalyst-calendar-followup/source-bundle.json';s=read(p)['sources'][0];sources['1518issuer']=s
pj=ROOT/'research/ir-jpx-earnings-schedule-review-2026-10-15/company-scoped-sources/1518/source-bundle.json';sources['1518']=read(pj)['sources'][0]
p1975=B/'1975/public-qa-and-calendar-discovery-2026-10-16/calendar-source-candidate/source-only-bundle.json';sources['1975']=read(p1975)['sources'][0]
for key,p in [('1518issuer',p),('1518',pj),('1975',p1975)]:
 s=sources[key];assert validate_source(s)==s
 records.append({'company_id':s['company_id'],'source_id':s['id'],'native_source_SHA256':native(s),'original_bundle':pin(p),'original_object_pointer':'$.sources[0]','original_whole_object_preserved':True,'url':s['url'],'published_at':s['published_at'],'retrieved_at':s['retrieved_at'],'source_registration':'already_saved_not_in_new_bundle','used_in_requests':key!='1518issuer','first_save_provenance':'See existing actual report or saved receipt below; no actual DB read this phase.'})
newbundle={'schema_version':1,'companies':[],'sources':new,'theses':[]};assert len({s['id'] for s in new})==5
requests=deepcopy(read(B/'1975/catalyst-schedule-connection-2026-10-16/catalyst-schedule-requests.json'))
old1975=deepcopy(requests)
# Create only current discovered forward verification candidates, not repeated historical events.
def event(code,eid,kind,label,rawperiod,fy,quarter,basis,rawdate,date,context,rationale,textfile,interpretation):
 s=sources[code];assert all(q in basis for q in [rawdate,context]);i=s['content'].index(basis)
 return {'id':eid,'company_id':s['company_id'],'synthetic':False,'kind':kind,'label':label,'period':{'raw_label':rawperiod,'fiscal_year_label':fy,'quarter_label':quarter,'basis_quote':basis,'interpretation':interpretation},'claims':[{'id':eid+':schedule-1','kind':'schedule','source_id':s['id'],'source_snapshot_sha256':native(s),'basis_quote':basis,'basis_quote_location':{'character_start':i,'character_end':i+len(basis),'offset_unit':'Unicode code points, source.content local; zero-based end-exclusive','pdf_page':None,'printed_page':None,'saved_text_file':textfile,'section':'Published calendar schedule; caller period/date mapping only'},'raw_date_label':rawdate,'date':date,'time':None,'timezone':None,'date_context_quote':context,'date_context_rationale':rationale,'supersedes_claim_id':None}]}
common='原文ラベルをdescriptorとして保持。会計期間のexact開始終了日、予定の実施・業績・現在の有効性を補完しない。'
#1518 company calendar no exact next day. Existing JPX source has already disclosed exact-code serial-date conversion.
s=sources['1518'];basis=s['content'];requests.append(event('1518','jp:1518:jpx-20261008-fy2027-q2-release','earnings_release','JPX会社別予定：2027年3月期 第２四半期決算発表','第２四半期 / Second quarter','決算期末 2027-03-31（原表serial変換）','第２四半期 / Second quarter',basis,'2026-11-13','2026-11-13','2026年10月8日 現在','既存JPX表の1518完全一致行、Excel1900日付系46339を2026-11-13へ変換した既存representation。会社calendarの直接日付や現在再確認として扱わない。',str(pj.relative_to(ROOT))+'#$.sources[0].content',common))
#4318 explicit calendar year from selector/table binding preserved in parent raw evidence.
f=folder('4318');obs=read(f/'calendar-observations.json');q=read(f/'source-quotes.json');q=q['quotes'] if isinstance(q,dict) else q;by={x['id']:x for x in q};r=obs['read_rows'][0];s=sources['4318'];basis=s['content'][by['visible-calendar-year']['character_start']:by[r['quote_id']]['character_end']];requests.append(event('4318','jp:4318:2027fy-q2-release','earnings_release',r['label_raw'],'2027年3月期 第2四半期',r['fiscal_year_label'],r['quarter_label'],basis,r['date_raw'],r['date_candidate'],'2026年','2026年option value=y2026と同id原HTMLtableの対応を保存reviewが確認。source.content上の年selectorと該当行を引用し、rawDOM結合はprovenance参照。FY2027から暦年逆算しない。',str((f/'text/02.txt').relative_to(ROOT)),common));review4318=read(f/'review.json')
#3817 rough month slots stay null. Presentation FY/quarter are explicitly missing in original observation.
f=folder('3817');rv=read(f/'review.json');q=read(f/'source-quotes.json')['quotes'];by={x['id']:x for x in q};basis=by['annual-schedule-scope']['quote'];unknowns=[]
for e in rv['events']:
 fy=e['fiscal_year_label'] or '未記載（2026年度カレンダー欄）';quarter=e['quarter_label'] or '未記載';rawperiod=(e['fiscal_year_label']+' '+e['quarter_label']) if e['fiscal_year_label'] and e['quarter_label'] else '機関投資家向け説明会（対象決算期未記載）'
 if e['fiscal_year_label'] is None:unknowns.append({'event_id':'jp:'+e['id'],'original_fiscal_year_label':None,'original_quarter_label':None,'descriptor_note':'API必須非空strには未記載を明示。Q2直後の行からQ2対象説明会とは認定しない。','statement_is_earnings_specific':None})
 requests.append(event('3817','jp:'+e['id'],e['kind'],e['label'],rawperiod,fy,quarter,basis,e['raw_date_label'],None,'2026年度','11月中旬/下旬・２月中旬の原表示のみ。2026年度ラベルからexact暦年/dayを作らずdate:null。説明会の対象期は明記なし。',by[e['source_quote_id']]['text_file'],common+' '+e['interpretation']))
#6814 four previously reviewed forward dates and exact fiscal-section quote context.
f=folder('6814');rv=read(f/'review.json');q=read(f/'source-quotes.json')['quotes'];by={x['id']:x for x in q}
for e in rv['events']:
 fyq=by['FY2027-section' if e['fiscal_year_label']=='2027年2月期' else 'FY2028-section'];basis=fyq['quote'];requests.append(event('6814','jp:'+e['id'],e['kind'],e['fiscal_year_label']+' '+e['label'],e['fiscal_year_label']+' '+e['quarter_label'],e['fiscal_year_label'],e['quarter_label'],basis,e['raw_date_label'],e['date'],e['fiscal_year_label'],'原文FYsectionとyear/month/day表示を対応するcaller mapping。FY月区間を四半期会計開始終了日へ変換せず、time/timezone/実施を補完しない。',by[e['source_quote_id']]['text_file'],common+' '+e['interpretation']))
# Support records for omitted cases, not API invented kinds/placeholders.
omitted=[]
f=folder('2929');obs=read(f/'calendar-observations.json');r=obs['read_rows'][0];read(f/'source-quotes.json')
omitted.append({'company_id':'jp:2929','raw_date_label':r['date_raw'],'date':r['date_candidate'],'raw_label':r['label_raw'],'raw_kind':r['kind'],'reason':'Existing schedule-only API supports earnings_release/earnings_presentation only; shareholder meeting remains visible here, not coerced.','source_id':sources['2929']['id'],'native_source_SHA256':native(sources['2929']),'quote_id':r['quote_id'],'observation_ref':str((f/'calendar-observations.json').relative_to(ROOT)),'occurrence':'not_established','due':None})
for code,reason in [('2929','No next earnings date in reviewed text; all observed earnings rows are historical.'),('6200','No next dated earnings/presentation in reviewed static text; annual image unrequested/unread. Past 2025 dates not shifted to next year.')]:omitted.append({'company_id':'jp:'+code,'event_request_count':0,'reason':reason,'observation_ref':str((folder(code)/('calendar-observations.json' if code=='2929' else 'review.json')).relative_to(ROOT))})
read(folder('6200')/'review.json');re1518=read(folder('1518')/'review.json')
# Existing first-save evidence read, not regenerated or projected onto new5.
rec1518=read(ROOT/'research/ir-research-monitoring-integration-2026-10-15/actual-report-v19.json');actual1975=read(B/'1975/catalyst-schedule-connection-2026-10-16/actual-report/report.stdout.json')
for rec in records:
 if rec.get('source_registration'):
  if rec['company_id']=='jp:1518':
   old=next(z for c in rec1518['cases'] for z in c.get('sources',[]) if z['source_id']==rec['source_id']);assert old['source_snapshot_sha256']==rec['native_source_SHA256'];rec['actual_DB_first_saved_at']=old['first_saved_at'];rec['firstsave_receipt_ref']='research/ir-research-monitoring-integration-2026-10-15/actual-report-v19.json'
  else:
   receipt=actual1975['events'][0]['lineage_checks'][0]['current_availability']['availability']['receipt'];assert receipt['entity_id']==rec['source_id'] and receipt['snapshot_sha256']==rec['native_source_SHA256'];rec['actual_DB_first_saved_at']=receipt['first_saved_at'];rec['firstsave_receipt_ref']='research/ir-case-studies-2026-10-15/1975/catalyst-schedule-connection-2026-10-16/actual-report/report.stdout.json'
# Cases are references only; all conditions and management dates remain unchanged.
cases=[]
for code in ['1518','1975','2929','3817','4318','6200','6814']:
 if code=='1518':p=B/code/'author-condition-followup/case-record.json'
 elif code=='1975':p=B/code/'native-case-setup-2026-10-16/actual-inputs/case-context.json'
 else:p=B/code/'native-case-setup-2026-10-16/prepare-only/case-context.json'
 c=read(p);cases.append({'company_id':'jp:'+code,'existing_context_ref':pin(p),'original_conditions_and_management_unchanged':True,'action':'Await actual disclosed results and compare existing issuer period/share/profit basis, or original1518 author drivers. Calendar is not a financial input or condition result.'})
for p in [ROOT/'docs/catalyst-monitor-design.md',ROOT/'scripts/report_catalyst_schedule.py',ROOT/'src/ir_agent/catalyst_schedule.py',ROOT/'third_party/anthropic/skills/catalyst-calendar/SKILL.md']:pin(p)
_validate_requests(requests)
for e in requests:
 s=next(s for s in sources.values() if s['id']==e['claims'][0]['source_id']);c=e['claims'][0];assert native(s)==c['source_snapshot_sha256'];loc=c['basis_quote_location'];assert s['content'][loc['character_start']:loc['character_end']]==c['basis_quote'];assert e['period']['basis_quote'] in s['content'];assert c['date_context_quote'] in c['basis_quote'] and c['raw_date_label'] in c['basis_quote']
counts={c:sum(e['company_id']=='jp:'+c for e in requests) for c in ['1518','1975','2929','3817','4318','6200','6814']};assert counts=={'1518':1,'1975':4,'2929':0,'3817':3,'4318':1,'6200':0,'6814':4};assert requests[:4]==old1975
save('source-bundle.json',newbundle);save('catalyst-schedule-requests.json',requests)
rows=[]
for code in counts:
 for e in [e for e in requests if e['company_id']=='jp:'+code]:
  c=e['claims'][0];rows.append({'company_id':e['company_id'],'event_id':e['id'],'kind':e['kind'],'label':e['label'],'raw_date_label':c['raw_date_label'],'date':c['date'],'time':None,'timezone':None,'due':None,'occurrence':'not_established','source_id':c['source_id']})
save('schedule-inventory.json',{'status':'prepare_only_not_executed_or_registered','event_counts':counts,'events':rows,'omitted':omitted,'period_unknown_descriptors':unknowns,'case_followups':cases,'scope':'Reuse existing producer selected forward-verification scope; no company-wide full calendar coverage claim, no future year inferred from historical rows. User horizon is not exitdeadline.'})
save('provenance.json',{'status':'prepare_only_pending_ROOT_acceptance_copy_and_ingest','prepared_at':load(OUT/'provenance.json')['prepared_at'] if (OUT/'provenance.json').exists() else datetime.now(timezone.utc).isoformat(),'source_records':records,'new_source_count':5,'reused_existing_source_count':3,'existing1975_requests_unchanged':True,'4318_raw_year_binding':review4318['raw_year_binding'],'hash_semantics':'native_source_SHA256 = sha256(ir_agent.models.json_text(whole_source).encode(UTF-8)); not raw entity/content SHA or normalizer compact domain.','source_binding_status':'Not evaluated against actualDB in this phase; no source_bound_candidate claim. Newsource firstsave null until trusted ROOTreceipt.','input_pins':inputs,'DB_Store_accesses':0,'GETs':0,'production_or_oldfile_changes':0})
save('validation.json',{'prepare_only':True,'source_count':5,'companies_theses_empty':True,'original_whole_objects_equal':all(new[i]==sources[c] for i,c in enumerate(['2929','4318','3817','6200','6814'])),'all_sources_validate':True,'existing_contract_pure_shape_validation':'_validate_requests(requests) passes; no report call or DB connection','event_count':len(requests),'event_counts':counts,'native_SHA_and_quote_locations_match':True,'date_null_count':sum(e['claims'][0]['date'] is None for e in requests),'all_time_timezone_supersedes_null':True,'all_new_sources_publication_and_DBfirstsave_null':True,'existing1975_requests_exact_value_preserved':True,'all_original_input_pins_match':all(sha(ROOT/p)==v for p,v in inputs.items()),'DB_Store_GET_mutator_calls':0,'financial_adoption_forecast_price_or_IR':0,'limitations':['Pure shape and exact quotes do not certify fiscal mapping, actualsource availability/classification, current schedule unchanged or occurrence.','3817 institutional presentation has no explicit fiscalyear/quarter; required descriptors say missing, and earnings-specific status remains unknown.','New5 source stable metadata retains original producerfolder references; aggregate path does not relocate/rewrite raw provenance.']})
print(json.dumps({'new_sources':len(new),'events':len(requests),'counts':counts,'request_SHA':sha(OUT/'catalyst-schedule-requests.json'),'bundle_SHA':sha(OUT/'source-bundle.json')},ensure_ascii=False))
