from pathlib import Path
from datetime import datetime,timezone
from html.parser import HTMLParser
from copy import deepcopy
import hashlib,json,sys
root=Path('/workspace/ir-agent');outrel=Path('research/ir-case-studies-2026-10-15/6814/public-IR-FAQ-public-review-2026-10-16');out=root/outrel
sys.path.insert(0,str(root/'scripts'));from build_case_source_bundle import build_case_source_bundle

def sha(data):return hashlib.sha256(data).hexdigest()
def fh(p):return sha((root/p).read_bytes())
def load(p):return json.loads((root/p).read_bytes().decode('utf-8'))
def save(name,obj):
 raw=obj.encode('utf-8') if isinstance(obj,str) else (json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
 with (out/name).open('xb') as h:h.write(raw)
 return sha(raw)

now=datetime.now(timezone.utc).isoformat();g=load(outrel/'guard.json');cap=load(outrel/'capture.json');assert len(cap['GETs'])==2 and cap['new_GETs']==2
robots,body=cap['GETs'];assert all(x['complete_body'] and x['HTTP_status']==200 and not x['error'] for x in cap['GETs'])
assert body['url']=='https://www.furuno.co.jp/ir/faq/'
for x in cap['GETs']:assert fh(outrel/x['raw_file'])==x['raw_sha256']
raw=(out/body['raw_file']).read_bytes();html=raw.decode('utf-8');assert '\ufffd' not in html
text=body['html_visible_text']['text'];assert (out/body['text_file']).read_bytes()==text.encode('utf-8')
assert g['robots_reviews']['www.furuno.co.jp']['proceed'] is True
pins=deepcopy(g['input_pins']);capture_script_source=g['capture_script_source'];pins[capture_script_source['path']]=capture_script_source['sha256']
for path,h in pins.items():assert fh(Path(path))==h,path
questions=['決算期はいつですか？','財務資料（決算短信、有価証券報告書・半期報告書など）はどこで見ることができますか？']
answers=['2月末日ですが、四半期ごとに決算発表を行っております。詳細は IRカレンダー をご覧ください。','当社サイトの 決算短信・決算説明資料 、 有価証券報告書 をご覧ください。']
quotes=[]
for n,(q,a) in enumerate(zip(questions,answers)):
 joined=q+' '+a;start=text.index(joined);end=start+len(joined)
 assert text[start:end]==joined
 quotes.append({'id':['FAQ-fiscal-period','FAQ-financial-document-location'][n],'url':body['url'],'quote':joined,'question':q,'answer':a,'character_start':start,'character_end':end,'byte_start':len(text[:start].encode('utf-8')),'byte_end':len(text[:end].encode('utf-8')),'offset_unit':'Exact saved source.content Unicode/UTF8 bytes zero-based end-exclusive','text_file':str(outrel/body['text_file']),'text_sha256':body['text_sha256'],'raw_entity_sha256':body['raw_sha256'],'pdf_page':None})
save('source-quotes.json',{'recorded_at':now,'url':body['url'],'questions_and_answers_meaning_read':2,'quotes':quotes,'reading_scope':'Only fiscal-period and financial-document-location Q/A read as substantive answers; other static FAQ question headings located only. No child link opened.'})
snapshot={'url':body['url'],'sha256':body['raw_sha256'],'http_status':200,'error':None,'retrieved_at':body['http_get_completed_at'],'publication_time':None,'content_type':body['response_headers']['content-type'],'text':text,'links':deepcopy(body['html_visible_text']['links']),'extraction_method':'Existing Page HTMLParser static complete response visible text; no JavaScript or child requests.',
 'original_complete_capture':{'file':str(outrel/'capture.json'),'sha256':fh(outrel/'capture.json'),'pointer':'/GETs/1'},'adapter_note':'Field adapter only; retrieved_at is bounded response completion, not page publication or actual DB first-save.'}
save('FAQ-builder-snapshot.json',snapshot)
save('source-manifest-adapter.json',{'sources':[{'id':'6814-IR-FAQ-complete-response-2','url':body['url'],'sha256':body['raw_sha256'],'http_status':200,'error':None,'retrieved_at':body['http_get_completed_at'],'published_at':None,'publication_date':None,'publication_note':'Page publication date/time not established. Response HTTP Date and fiscal-period answer are not a publication clock; later updated FAQ text is not the issuer earnings-release or a new forecast.'}]})
source_map={'schema_version':1,'companies':[{'id':'jp:6814','security_code':'6814','name':'古野電気','status':'watch','held':False}],
 'sources':[{'key':'issuer_IR_FAQ','company_id':'jp:6814','manifest':{'document':'source-manifest-adapter.json','path':['sources',0]},'snapshot':'FAQ-builder-snapshot.json','snapshot_sha256':fh(outrel/'FAQ-builder-snapshot.json'),'raw_file':body['raw_file'],'raw_sha256':body['raw_sha256'],'content_kind':'html_visible_text','content_sha256':body['text_sha256'],'document_kind':'issuer_IR_FAQ_fiscal_and_general_shareholder_information','title':'古野電気 公式IR FAQ（決算期・財務資料案内の限定読解）'}],
 'citations':[{'source_key':'issuer_IR_FAQ','document':'source-quotes.json','path':['quotes',i]} for i in range(2)]}
save('source-map.json',source_map)
bundle=build_case_source_bundle(out/'source-map.json');assert bundle==build_case_source_bundle(out/'source-map.json');save('builder-output.json',bundle)
source_only={'schema_version':1,'companies':[],'sources':bundle['sources'],'theses':[]};save('source-only-bundle.json',source_only)
source=source_only['sources'][0];assert source['content']==text and source['published_at'] is None
native=sha(json.dumps(source,ensure_ascii=False,sort_keys=True,allow_nan=False).encode('utf-8'))
priorpaths=[Path('research/ir-case-studies-2026-10-15/6814/annual-per-share-disclosed-facts-2026-10-16/normalized-bundle.json'),Path('research/ir-case-studies-2026-10-15/6814/latest-guidance-disclosed-facts-2026-10-16/normalized-bundle.json')]
priorfacts=[]
for path in priorpaths:
 d=load(path);pins[str(path)]=fh(path)
 for s in d['sources']:
  if s.get('metadata',{}).get('provider')=='project_disclosed_fact_normalization':
   for f in json.loads(s['content'])['facts']:priorfacts.append({'source_ref':{'path':str(path),'sha256':pins[str(path)]},'source_id':s['id'],'concept':f['concept'],'raw_value':f['raw_value'],'value':f['value'],'kind':f['kind'],'period':f['period']})
assert {'529.53','2826.61','537.80','210'}<={f['raw_value'] for f in priorfacts}|{f['value'] for f in priorfacts}
class HeadingLocator(HTMLParser):
 def __init__(self):super().__init__();self.stack=[];self.items=[]
 def handle_starttag(self,t,a):
  if t in ['h1','h2','dt']:self.stack.append({'tag':t,'attrs':dict(a),'text':[]})
 def handle_data(self,d):
  for entry in self.stack:entry['text'].append(d)
 def handle_endtag(self,t):
  if self.stack and t==self.stack[-1]['tag']:
   entry=self.stack.pop();entry['text']=' '.join(' '.join(entry['text']).split());self.items.append(entry)
loc=HeadingLocator();loc.feed(html)
save('question-locator.json',{'recorded_at':now,'raw_sha256':body['raw_sha256'],'scope':'Staticheading/question locations only; not all-answer semantic review','headings_and_questions':loc.items,'selected_semantic_questions':questions,'question_count':len([x for x in loc.items if x['tag']=='dt']),'all_answers_semantically_read':False,'no_child_or_script_requests':True})
review={'recorded_at':now,'company_id':'jp:6814','company_name':'古野電気','purpose':'Finite selected officialIRFAQ body review only','source_id':source['id'],'source_native_sha256':native,
 'source_bundle_ref':{'path':str(outrel/'source-only-bundle.json'),'sha256':fh(outrel/'source-only-bundle.json')},
 'literal_provenance':deepcopy(g['literal_provenance']),
 'duplicate_check':deepcopy(g['GET0_duplicate_check']),
 'GET_budget':{'maximum':3,'actual':2,'robots':1,'selected_FAQ':1,'redirects':0,'retries':0,'child_GETs':0,'automatic_redirects':0},
 'robots':deepcopy(g['robots_reviews']),
 'source_publication':{'published_at':None,'publication_date':None,'actual_DB_firstsave':None,'retrieved_at':source['retrieved_at'],'HTTP_Date_not_publication':True},
 'static_page_scope':{'visible_questions_located':len([x for x in loc.items if x['tag']=='dt']),'sections':['沿革','決算関係','株式について'],'answer_QA_pairs_meaning_read':2,'selected_questions':questions,'other_QA_answers':'not meaning reviewed','business_or_profit_driver_QA_found_in_question_locator':False,'not_whole_site_or_latest_filing_verification':True},
 'selected_answers':[
  {'quote_id':'FAQ-fiscal-period','fact':'決算期を2月末日とし、四半期ごとに決算発表を行うと説明。詳細はIRカレンダーへ案内。','limit':'特定年度の予定日・実施確認・予想修正・資料全体の対象期/普通株基準を確認する答えではない。カレンダーの子リンクは取得0。'},
  {'quote_id':'FAQ-financial-document-location','fact':'財務資料の参照先として決算短信・決算説明資料と有価証券報告書のサイト内掲載箇所を案内。','limit':'資料への案内が本文であり、現業績・利益変動・会計定義や具体的予想値をこのFAQが答えたとはしない。子資料の取得/最新版認定0。'}],
 'existing_annual_and_guidance_unchanged':{'references':priorfacts,'annual_reported_values':['529.53','2826.61'],'October9_asof_issuer_guidance':['537.80','210'],'no_replacement_or_recalculation':True,'no_current_latest_forecast_or_guidance_realization_certified':True},
 'research_disposition':'General IR/fiscal/document-location FAQ scope completed; no new answer to business structure, earnings/profit-change drivers or model accounting-basis questions. Do not expand this into another route or interpret no matching question on this page as issuer-wide non-disclosure.',
 'author_project_boundary':'Existing public DD procedure checks already published answers before a new inquiry. Issuer fiscal/document-location explanations are not external-author forecasts, financial inputs or investment support.',
 'termination':'SelectedFAQ complete; 1GETunused deliberately, no child/JS/feed/search/held/oldclosedroute reopened.',
 'operations':{'DB_Store_CLI':0,'normalizer_or_financial_calculation':0,'new_IR_draft_or_send':0,'bank_model_or_financial_adoption':False,'oldsource_sharedfile_code_index_edits':0},
 'financial_inputs_verified':False,'source_only_candidate_not_ingested':True,'input_pins':pins}
save('review.json',review)
for q in quotes:
 assert source['content'][q['character_start']:q['character_end']]==q['quote']
 assert source['content'].encode('utf-8')[q['byte_start']:q['byte_end']].decode('utf-8')==q['quote']
for path,h in pins.items():assert fh(Path(path))==h,path
save('validation.json',{'recorded_at':now,'status':'finite_static_general_FAQ_review_completed','new_GETs':2,'max_GETs':3,'raw_complete_HTTP200_bodies':2,'all_raw_sha_match':True,'utf8_decode_replacement_count':0,'selected_literal_parent_exact_href_label_and131index_confirmed':True,'holds_exacthost_not_held':True,'freshrobots200_exacttarget_literalchecks':g['robots_reviews']['www.furuno.co.jp']['literal_checks'],'selected_QA_pair_limit':2,'actual_QA_pairs_read':2,'quote_exact_Unicode_UTF8_and_saved_content_matches':2,'builder_whole_reproduction_equal':True,'sourceonly_company_thesis_empty':True,'sourcewhole_preserved_from_builder_output':True,'prior_annual_and_guidance_bundles_prepost_SHA_unchanged':True,'no_current_forecast_or_guidance_revalidation':True,'GET_to_child_JS_search_or_feed':0,'DB_Store_financialcalc_old_edits':0,'financial_inputs_verified':False})
save('README.md','''# 6814 古野電気：公式IR FAQの限定確認

保存済み公式親ページの実リンク`/ir/faq/`（parent captureのlinks[131]）から、選択したFAQだけを確認した。既存66JSONに同一URL本文captureがないこと、holds-v8非該当を確認し、freshrobots200＋FAQ200の**2GET**で終了した。最大3GET、リトライ・子リンク・JS・feed・検索・旧closedroute再開は0。

静的質問見出しは沿革・決算関係・株式手続き等の一般案内。意味読解は次の2組だけ。

- 決算期：2月末日、四半期ごとの決算発表。詳細はIRカレンダーへ案内。
- 財務資料の掲載先：決算短信・決算説明資料、有価証券報告書へ案内。

このFAQから事業構造・業績/利益変動・会計指標の追加回答は得ていない。他頁・全公式資料の不存在とはしない。案内先は取得していない。

4/9年次reported EPS529.53/BPS2826.61と10/9当時の会社guideEPS537.80/DPS210は既存資料のまま。FAQを現在最新予想・guide実現・銀行model・金融入力や売買条件へ置換しない。

`source-only-bundle.json`は既存offlinebuilderを使う新原典候補で、companies/thesesは空。raw・capture・visibletext・2逐語引用/offset・親literalを保持し、公開日時/実DBfirstsaveは未設定。DB/Store/金融計算/IR草案・送信/旧file変更は0。
''')
manifest={'recorded_at':now,'company_id':'jp:6814','source_id':source['id'],'source_native_sha256':native,'source_bundle_sha256':fh(outrel/'source-only-bundle.json'),'raw_entity_sha256':body['raw_sha256'],'retrieved_at':source['retrieved_at'],'published_at':None,'actual_DB_firstsave':None,'GET_budget':{'maximum':3,'actual':2,'redirects':0,'retries':0,'child':0},'reading_scope':'2 selected general fiscal/document-locationQAs only; all staticquestionheadings located, not all answers read','input_pins':pins,'files':{str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()},'source_ingested':False,'financial_inputs_verified':False,'DB_Store_normalizer_financialcalc_oldfile_changes':0}
save('manifest.json',manifest)
for path,h in pins.items():assert fh(Path(path))==h,path
print(json.dumps({'folder':str(outrel),'source_id':source['id'],'native_sha256':native,'bundle_sha256':fh(outrel/'source-only-bundle.json'),'manifest_sha256':fh(outrel/'manifest.json'),'GETs':2,'QA_pairs':2,'DB_oldchanges':0},ensure_ascii=False,indent=2))
