"""One file-only extraction of nine image-reviewed issuer display tokens."""
from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
from ir_agent.disclosed_facts import normalize_disclosed_facts

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PRIOR=HERE.parent/'initial-public-review-2026-10-16'
CODE_SHA='d434b41cfa19568d0cef1a2e6710365f447012d75a4b07ca950cc62b6bd9db51'
SID='case-public:33917957734a3f4b705072164e8e3526e23fec79c9f1b2265a7131a17e6253b1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(n,o):
 with (HERE/n).open('x',encoding='utf-8')as f:f.write(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def rel(p):return str(p.relative_to(ROOT))

def main():
 assert not (HERE/'normalized-bundle.json').exists()
 assert digest(ROOT/'src/ir_agent/disclosed_facts.py')==CODE_SHA
 oldpins={rel(p):digest(p)for p in sorted(PRIOR.rglob('*'))if p.is_file()}
 source=next(s for s in load(PRIOR/'source-bundle.json')['sources']if s['id']==SID)
 saved_original=deepcopy(source);content=source['content'];page1=content.split('\f')[0]
 assert source['published_at'] is None and source['metadata']['publication_date']=='2026-08-07'
 assert digest(PRIOR/source['metadata']['original_raw_file'])==source['metadata']['original_raw_sha256']
 oldquotes=load(PRIOR/'source-quotes.json');byid={q['id']:q for q in oldquotes}
 selected=[]
 for qid in ['actual-period-unit-and-profit','full-year-issuer-guidance']:
  q=deepcopy(byid[qid]);assert content[q['character_start']:q['character_end']]==q['quote'];selected.append(q)
 start=page1.index('２．配当の状況');end=page1.index('３．2027年３月期の連結業績予想',start)
 selected.append({'id':'issuer-annual-dividend-total-guidance','source_id':SID,'quote':content[start:end],
  'character_start':start,'character_end':end,'UTF8_byte_start':len(content[:start].encode()),'UTF8_byte_end':len(content[:end].encode()),'pdf_physical_page':1,
  'offset_basis':'Zero-based Unicode character/UTF8 bytes in exact source.content, half-open; total column image checked'})
 quote_by_id={q['id']:q for q in selected}
 context_refs={}
 for qid in ['scope-new-company-shares-and-treatment','explanatory-text-referred-to-public-summary','PL-operating-FX-tax-and-NCI']:
  q=byid[qid];assert content[q['character_start']:q['character_end']]==q['quote']
  context_refs[qid]={'path':rel(PRIOR/'source-quotes.json'),'file_sha256':digest(PRIOR/'source-quotes.json'),'quote_id':qid,'json_pointer':f'/{oldquotes.index(q)}','pdf_page':q['pdf_physical_page'],'character_start':q['character_start'],'character_end':q['character_end']}
 common={'company_id':'jp:1963','original_author':{'kind':'issuer','name':'日揮ホールディングス株式会社'},'extraction_author':'Codex offline display reviewer; not issuer forecast author',
  'observed_source_disclosure_date':'2026-08-07','publication_clock_unknown':True,'historical_issuer_disclosure_only':True,'October_current_guidance_or_share_basis_verified':False,
  'source_context_references':context_refs,'period_scope_column_are_reviewer_assertions':True,
  'new_consolidation_context':'p2 states new1 JGC Emirates L.L.C-FZ within Q1; mechanism/inclusion dates/contribution not established by these pages, not automatically organic comparison',
  'quarter_specific_accounting_treatment':'p2 states applies (有); details in later unread note not adopted',
  'profit_scope_context':'p7 FX gain3882m is nonoperating; operating/ordinary/pretax/tax/consolidated quarter profit11624m/NCI7m/parentNI11617m remain separate. No normal profit/tax/CF computed.',
  'share_scope_context':'p2 issued-at-end incl treasury, end treasury and cumulative average shares are separate historical definitions; neither current nor diluted valuation denominator is inferred.',
  'financial_inputs_verified':False,'model_or_policy_adopted':False,'canonical_model_input_path':None,'future_cashflow_or_normal_profit_adopted':False,'Q1_annualization_applied':False}
 actual_label='１．2027年３月期第１四半期の連結業績（2026年４月１日～2026年６月30日）'
 annual_label='３．2027年３月期の連結業績予想（2026年４月１日～2027年３月31日）'
 actual={'label':actual_label,'period_kind':'quarterly_cumulative_reported','start_date':'2026-04-01','end_date':'2026-06-30','observed_in_source_disclosure_date':'2026-08-07','date_basis':'Exact dates printed in this same actual/EPS table heading'}
 annual={'label':annual_label,'period_kind':'annual_issuer_guidance','start_date':'2026-04-01','end_date':'2027-03-31','observed_in_source_disclosure_date':'2026-08-07','previous_forecast_announcement_date':None,'date_basis':'Exact dates printed in this same annual earnings table heading; previous publication date not printed'}
 rows=[
  ('reported-revenue','revenue','reported_fact','159,299','百万円','JPY','actual-period-unit-and-profit','売上高','current Q1 actual sales',actual,'consolidated_company_amount'),
  ('reported-operating-income','reported_operating_income','reported_fact','12,355','百万円','JPY','actual-period-unit-and-profit','営業利益','current Q1 reported operating profit, not normalized earnings or NOPAT',actual,'consolidated_company_amount'),
  ('reported-parent-NI','net_income_attributable_to_parent_owners','reported_fact','11,617','百万円','JPY','actual-period-unit-and-profit','親会社株主に帰属する四半期純利益','current Q1 parent-attributable profit; distinct from consolidated quarterly profit11624m',actual,'parent_owners_company_amount'),
  ('issuer-guidance-revenue','revenue','issuer_guidance','670,000','百万円','JPY','full-year-issuer-guidance','売上高','Aug7 annual company revenue forecast, not investor forecast or observed outcome',annual,'consolidated_company_amount'),
  ('issuer-guidance-operating-income','reported_operating_income','issuer_guidance','40,000','百万円','JPY','full-year-issuer-guidance','営業利益','Aug7 annual company operating profit forecast; financial model unadopted',annual,'consolidated_company_amount'),
  ('issuer-guidance-parent-NI','net_income_attributable_to_parent_owners','issuer_guidance','46,000','百万円','JPY','full-year-issuer-guidance','親会社株主に帰属する当期純利益','Aug7 annual company parent-profit forecast; second46000 is parent NI, first is ordinary income',annual,'parent_owners_company_amount'),
  ('reported-Q1-EPS','reported_quarter_earnings_per_share','reported_fact','48.03','円','JPY-per-share','actual-period-unit-and-profit','１株当たり四半期純利益','Basic Q1 EPS48.03, not diluted47.96; direct displayed decimal, not rebuilt from rounded company NI',actual,'basic_parent_profit_per_share'),
  ('issuer-guidance-FY-EPS','issuer_forecast_full_year_earnings_per_share','issuer_guidance','190.25','円','JPY-per-share','full-year-issuer-guidance','１株当たり当期純利益','Aug7 annual company EPS forecast, not investor/current October EPS prediction',annual,'issuer_annual_forecast_per_share'),
  ('issuer-guidance-annual-DPS','issuer_forecast_annual_dividend_per_share','issuer_guidance','52.00','円','JPY-per-share','issuer-annual-dividend-total-guidance','年間配当金・合計','Annual total DPS52.00 in forecast row; not year-end column token or prior FY row, not confirmed payment or DDM series',
   {'label':'2027年３月期(予想)','period_kind':'annual_dividend_forecast_label_only','fiscal_year_end_month':'2027-03','start_date':None,'end_date':None,'dividend_record_date':None,'observed_in_source_disclosure_date':'2026-08-07','date_basis':'Only FY label in this dividend table; earnings-table start/end dates not inherited; no record date inference'},'issuer_dividend_total_forecast_per_share')]
 facts=[];locations=[]
 for idx,(suffix,concept,kind,raw,rawunit,unit,qid,column,definition,period,profitbasis)in enumerate(rows):
  q=quote_by_id[qid];quote=q['quote'];a=q['character_start'];scope=deepcopy(common)
  if suffix=='issuer-guidance-parent-NI':local=quote.rindex(raw)
  elif suffix=='issuer-guidance-annual-DPS':
   row_start=quote.index('2027年３月期(予想)');row_end=quote.index('\n',row_start);local=quote.rindex(raw,row_start,row_end)
  else:local=quote.index(raw)
  raw_start=a+local;raw_end=raw_start+len(raw);assert content[raw_start:raw_end]==raw
  scope.update(accounting_basis='Japanese_GAAP' if idx!=8 else None,consolidation_scope='連結' if idx!=8 else None,profit_or_distribution_basis=profitbasis,
   company_wide_amount_not_per_share=unit=='JPY',per_share_display_not_reconstructed=unit=='JPY-per-share',
   display_precision='百万円未満切捨て; unprinted sub-million precision unknown' if unit=='JPY' else 'Printed decimal only; unprinted precision and future share denominator unknown')
  if kind=='issuer_guidance':scope.update(issuer_guidance_observed_at_source_date='2026-08-07',forecast_changed_from_latest_previously_published='無',previous_forecast_announcement_date=None,no_current_October_forecast_certification=True)
  if idx==6:scope.update(EPS_basis='basic displayed Q1 EPS; diluted display47.96 is separate and not extracted')
  if idx==8:scope.update(accounting_and_consolidation_scope_not_inferred_for_dividend=True,dividend_record_date_verified=False,issuer_forecast_not_payment_confirmation=True,investor_DDM_dividend_column_adopted=False)
  loc={'pdf_page':1,'table_quote_id':qid,'row':'2027年３月期第１四半期' if kind=='reported_fact' else '2027年３月期(予想)' if idx==8 else '通期','column':column,
   'source_character_start':a,'source_character_end':q['character_end'],'raw_token_source_character_start':raw_start,'raw_token_source_character_end':raw_end,
   'raw_token_UTF8_byte_start':len(content[:raw_start].encode()),'raw_token_UTF8_byte_end':len(content[:raw_end].encode()),
   'image_file':rel(PRIOR/'images/physical-1.png'),'image_sha256':digest(PRIOR/'images/physical-1.png'),'image_visually_checked_in_this_extraction':True,
   'displayed_decimal_not_yen_sen_composite_format':unit=='JPY-per-share'}
  fact={'id':'1963-'+suffix+'-observed-20260807','company_id':'jp:1963','source_id':SID,'concept':concept,'kind':kind,'raw_value':raw,'raw_unit_label':rawunit,'unit':unit,
   'raw_period_label':period['label'],'period':period,'basis_quote':quote,'definition':definition,'scope':scope,'location':loc};facts.append(fact);locations.append({'fact_index':idx,'fact_id':fact['id'],'raw_value':raw,**loc})
 assert facts[5]['location']['raw_token_source_character_start']>facts[5]['basis_quote'].index('46,000')+facts[5]['location']['source_character_start']
 now=datetime.now(timezone.utc).isoformat();request={'company_id':'jp:1963','source':source,'review':{'author':'Codex offline extraction reviewer; issuer 日揮ホールディングス株式会社 authored financial facts and guidance','recorded_at':now,'rationale':'Nine direct p1 display tokens independently image checked. Preserve Q1 vs Aug7 company annual guidance, basic vs diluted EPS, forecast annual DPS total column, p2 new1 and quarterly treatment, p7 FX/nonoperating/tax/NCI. Context refs are fixed paths/SHA/id/page/offset, not automatic meaning certification. No financial/current October input adoption.'},'facts':facts}
 save('source-reference.json',{'recorded_at':now,'source_id':SID,'source_bundle':rel(PRIOR/'source-bundle.json'),'source_bundle_sha256':digest(PRIOR/'source-bundle.json'),'source_pointer':'/sources/2','source_snapshot_sha256':sha256(json.dumps(source,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'native_snapshot_algorithm':'SHA256 UTF8 sorted JSON default separators','source_compact_sha256_separate_domain':sha256(json.dumps(source,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'source_content_sha256':sha256(content.encode()).hexdigest(),'raw_sha256':source['metadata']['original_raw_sha256'],'source_pub_retrieval_preserved':True,'source_context_references':context_refs,'old_input_pins':oldpins,'normalizer_code_sha256':CODE_SHA,'meaning_images_own_recheck':[1,2,7],'parent_previously_reviewed_pages':[1,2,4,7]})
 save('quotes.json',{'recorded_at':now,'source_id':SID,'source_content_sha256':sha256(content.encode()).hexdigest(),'quotes':selected,'per_fact_raw_token_locations':locations,'context_reference_only':True})
 save('normalization-input.json',request)
 bundle=normalize_disclosed_facts(request,now=now)
 assert request['source']==saved_original==bundle['sources'][0]
 assert all(digest(ROOT/p)==h for p,h in oldpins.items())
 save('normalized-bundle.json',bundle)
 save('generation.log',{'status':'generated_nine_direct_tokens_file_only','generation_now':now,'completed_at':datetime.now(timezone.utc).isoformat(),'producer_calls':1,'normalizer_sha256':CODE_SHA,'input_sha256':digest(HERE/'normalization-input.json'),'bundle_sha256':digest(HERE/'normalized-bundle.json'),'derived_source_id':bundle['sources'][1]['id'],'original_source_unchanged':True,'old_pins_unchanged':len(oldpins),'DB_connections':0,'GETs':0,'financial_inputs_adopted':False})
 print(json.dumps({'derived_source_id':bundle['sources'][1]['id'],'generation_now':now,'bundle_sha256':digest(HERE/'normalized-bundle.json'),'facts':len(facts)}))
if __name__=='__main__':main()
