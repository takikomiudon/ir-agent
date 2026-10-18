from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib,sqlite3,collections,sys
ROOT=Path('/workspace/ir-agent');sys.path.insert(0,str(ROOT/'src'))
from ir_agent.models import json_text
OUT=ROOT/'research/ir-universe-model-routing-intake-2026-10-15';master=ROOT/'research/ir-recovery-2026-10-13/all-companies.csv';db=ROOT/'data/ir-research-2026-10-15.sqlite3';policy=ROOT/'research/valuation-model-routing-2026-10-15/routing.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();now=lambda:datetime.now(timezone.utc).isoformat()
def save(n,v):
 with (OUT/n).open('x') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=list(csv.DictReader(master.open(encoding='utf-8-sig',newline='')));assert len(rows)==3686;codes=[r['security_code'] for r in rows];assert len(codes)==len(set(codes));lookup={r['security_code']:(i,r) for i,r in enumerate(rows)}
original_db=sha(db);c=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON');companies=[json.loads(r[0]) for r in c.execute('select data from companies order by id')];assert len(companies)==1819
sources=collections.Counter();financial=collections.Counter()
for row in c.execute('select id,company_id,data from sources'):
 s=json.loads(row['data'])
 if s['source_type']=='public_disclosure':
  sources[s['company_id']]+=1
  cl=c.execute('select data from source_classifications where source_id=? order by version desc limit 1',(s['id'],)).fetchone()
  if cl and json.loads(cl['data'])['financial_content'] is True:financial[s['company_id']]+=1
all_jobs_completed=c.execute("select count(*) from jobs where status<>'completed'").fetchone()[0]==0;c.close();assert sha(db)==original_db
sectors=collections.Counter();output=[];hints=[];mismatches=[];finance_sectors={'銀行業','証券、商品先物取引業','保険業','その他金融業'}
for company in companies:
 index,row=lookup[company['security_code']];sector=row['jpx_sector'];sectors[sector]+=1
 if company['name']!=row['company_name']:mismatches.append({'company_id':company['id'],'DB_name':company['name'],'master_name':row['company_name']})
 item={'company_id':company['id'],'security_code':company['security_code'],'company_name':company['name'],'catalog_company_name':row['company_name'],'identity_join_status':'code_and_name_match' if company['name']==row['company_name'] else 'code_matched_name_label_differs','catalog_JPX_sector':sector,'catalog_market':row['market'],'master_record_index_zero_based':index,'company_snapshot_sha256':hashlib.sha256(json_text(company).encode()).hexdigest(),'saved_public_sources':sources[company['id']],'classified_financial_sources':financial[company['id']],'next_check_hint':'financial_structure_public_evidence' if sector in finance_sectors else 'issuer_business_and_model_fit_unassessed','routing_status':'issuer_evidence_not_assessed','investment_eligibility':'not_assessed','DB_status_unchanged':company['status']};output.append(item)
 if sector in finance_sectors:hints.append({'company_id':company['id'],'security_code':company['security_code'],'company_name':company['name'],'catalog_JPX_sector':sector,'catalog_record_index_zero_based':index,'status':'sector_hint_only_not_model_assignment','policy_route_to_consider':'financial_service_equity_review','required_issuer_checks':['主体と主な事業、金融仲介/保険引受等の営業構造を会社原本で確認する。','資金負債の営業上の意味と、規制資本が成長/分配へ与える制約を当該主体/期間で確認する。'],'method_reference_ids':['financial-debt','financial-cf-definition','financial-regcapital'],'next_source':'A saved literal route to issuer business/financial or regulatory-capital material; no URL guess or failed-route retry.','industry_tag_is_not_sufficient':True,'automatic_model_or_exclusion':False})
assert {x['company_id'] for x in mismatches} == {'jp:3774','jp:5988'}
assert all(x['DB_name']=='株式会社'+x['master_name'] for x in mismatches)
assert not ({x['company_id'] for x in mismatches} & {x['company_id'] for x in hints})
fields=list(output[0]);
with (OUT/'all-1819-model-intake.csv').open('x',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(output)
save('financial-structure-evidence-tasks.json',{'recorded_at':now(),'task_kind':'issuer_evidence_intake_not_financial_model_assignment','selection_basis':'Exact four catalog financial-sector labels, a project work-allocation hint only. Damodaran observable conditions still require issuer evidence.','ordering':'security code; no investment ranking','count':len(hints),'tasks':hints})
save('validation.json',{'recorded_at':now(),'master_path':str(master.relative_to(ROOT)),'master_sha256':sha(master),'master_record_count':len(rows),'master_codes_unique':True,'actual_company_count':len(companies),'all_company_codes_joined':True,'name_display_variants':mismatches,'name_variant_disposition':'Code match retained; issuer legal-name prefix versus listing short label preserved in separate columns. No identity relabeling or DB correction. All 56 financial-hint names match exactly.','policy_path':str(policy.relative_to(ROOT)),'policy_sha256':sha(policy),'sector_counts':dict(sorted(sectors.items())),'financial_sector_hint_counts':dict(sorted(collections.Counter(x['catalog_JPX_sector'] for x in hints).items())),'hint_company_count':len(hints),'not_yet_routed_company_count':len(companies),'saved_public_company_count':len(sources),'classified_financial_company_count':len(financial),'hint_companies_with_saved_public_sources':sum(sources[x['company_id']]>0 for x in hints),'database_main_sha256_before_and_after':original_db,'read_only_SQLite':True,'all_jobs_completed_at_read':all_jobs_completed,'code_or_DB_new_GET_external_sends_orders':0,'new_output_hashes':{p.name:sha(p) for p in (OUT/'all-1819-model-intake.csv',OUT/'financial-structure-evidence-tasks.json')}})
print(json.dumps({'companies':len(companies),'financial_sector_hints':len(hints),'hint_sector_counts':dict(collections.Counter(x['catalog_JPX_sector'] for x in hints)),'public_source_companies':len(sources),'hint_companies_with_public_sources':sum(sources[x['company_id']]>0 for x in hints),'database_unchanged':sha(db)==original_db},ensure_ascii=False))
