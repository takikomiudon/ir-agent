from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json
root=Path('/workspace/ir-agent')
outrel=Path('research/ir-four-company-public-QA-connection-2026-10-16');out=root/outrel
assert not out.exists(), 'new phase already exists; no overwrite'
rows=[('4318','public-earnings-QA-index-review-2026-10-16'),('6200','second-quarter-public-QA-review-2026-10-16'),('6814','public-IR-FAQ-public-review-2026-10-16'),('7187','public-IR-FAQ-public-review-2026-10-16')]

def sha(data):return hashlib.sha256(data).hexdigest()
def fh(p):return sha(p.read_bytes())
def native(s):return sha(json.dumps(s,ensure_ascii=False,sort_keys=True,allow_nan=False).encode('utf-8'))
def load(p):return json.loads(p.read_bytes().decode('utf-8'))
def as_ref(p):return {'path':str(p.relative_to(root)),'sha256':fh(p)}
def resolve_manifest_file(base,name):
 p=Path(name)
 if p.is_absolute():resolved=p.resolve()
 elif (root/p).is_file():resolved=(root/p).resolve()
 else:resolved=(base/p).resolve()
 assert resolved.is_relative_to(root.resolve()) and resolved.is_file(), str(resolved)
 return resolved

initial_pins={};manifest_pin_checks=[];sources=[];producer_records=[];classifications=[];basis_refs=[];removed_stubs=[]
now=datetime.now(timezone.utc).isoformat()
for co,folder in rows:
 base=root/'research/ir-case-studies-2026-10-15'/co/folder
 bundle_file=base/'source-only-bundle.json';manifest_file=base/'manifest.json';review_file=base/'review.json';quote_file=base/('quotes.json' if co=='4318' else 'source-quotes.json')
 for p in [bundle_file,manifest_file,review_file,quote_file]:initial_pins[str(p.relative_to(root))]=fh(p)
 bundle=load(bundle_file);manifest=load(manifest_file);review=load(review_file);quoted=load(quote_file)
 assert bundle['schema_version']==1 and len(bundle['sources'])==1 and bundle['theses']==[]
 source=deepcopy(bundle['sources'][0]);assert source['company_id']=='jp:'+co and source['source_type']=='public_disclosure'
 assert source.get('metadata',{}).get('provider')!='project_disclosed_fact_normalization'
 if bundle['companies']:removed_stubs.append({'company_id':'jp:'+co,'producer_bundle_company_descriptor_count':len(bundle['companies']),'action':'Excluded company descriptors from aggregation; source whole object unchanged'})
 # A finite verification of each producer's declared artifact and old-input pins.
 for field in ['artifacts_excluding_this_manifest','files','pins','input_pins','old_input_pins']:
  collection=manifest.get(field)
  if collection is None:continue
  entries=[]
  if isinstance(collection,dict):
   for name,value in collection.items():
    expected=value if isinstance(value,str) else value['sha256'];entries.append((name,expected))
  else:
   assert isinstance(collection,list)
   for value in collection:entries.append((value.get('file',value.get('path')),value['sha256']))
  for name,expected in entries:
   p=resolve_manifest_file(base,name);actual=fh(p);assert actual==expected,(co,field,name,expected,actual)
   rel=str(p.relative_to(root));initial_pins.setdefault(rel,actual);assert initial_pins[rel]==actual
   manifest_pin_checks.append({'producer_company_id':'jp:'+co,'manifest_field':field,'path':rel,'expected_sha256':expected,'matched':True})
 metadata=source['metadata']
 if co=='4318':raw_path=resolve_manifest_file(base,metadata['raw_file']);raw_sha=metadata['raw_sha256']
 else:raw_path=(base/metadata['original_raw_file']).resolve();raw_sha=metadata['original_raw_sha256']
 assert raw_path.is_relative_to(base.resolve()) and fh(raw_path)==raw_sha
 initial_pins[str(raw_path.relative_to(root))]=raw_sha
 if co=='4318':
  q=next(x for x in quoted['quotes'] if x['id']=='4318-QA-FY2026-annual-Q2-FY2027-SG&A-cost-outlook')
  basis=q['answer']
  rationale='公式の静的決算説明会Q&A。2026年3月期決算説明会（2026-05-12開催）の選択2回答のうち会社回答はFY2027/3の販管費約12億円増と主な費目増を当時の見通しとして説明するためfinancial_content=true。質問者の減益前提だけを認証した分類ではない。主な費目を完全bridge/税後EPSへ合算せず、先行投資/ROE目標を実現/独立利益支持にしない。開催日は公表日ではなく、10月現在のguide/最新性は未認定。'
  fin=True
  scope=deepcopy(review['semantic_scope'])
  dates={'meeting_date_as_printed':'2026-05-12','meeting_fiscal_label':'2026年3月期','answer_outlook_period':'2027年3月期','publication_at':source['published_at'],'publication_time_unknown':True,'meeting_not_publication':True}
 elif co=='6200':
  q=next(x for x in quoted['quotes'] if x['id']=='Q3-sales-guide-reasons');basis=q['quote']
  rationale='会社公表のFY2026/9第2四半期説明会の加筆・修正済みQ&Aまとめ（全2頁がproducer既読）。会社回答3が当時の業績予想の事業別理由・長いlead time/ITカスタマイズ売上の想定未達を説明するのでfinancial_content=true。質問3のOJT負担、別質問の41%/採用人数を会社が認証したとは扱わない。文書/会合表示2026-05-11とURL26051301を公表日時へ補完せず、後続Q3/10月currentguideや確定受注へ移さない。'
  fin=True;scope={'physical_meaning_pages':[1,2],'full_source_pages':2,'source':'Producer full2-page reading/images reused; no additional PDFpage rendered/read here','questioner_premises_not_issuer_authenticated':deepcopy(review['questioner_premises_not_issuer_authenticated'])}
  dates=deepcopy(review['dates'])
 elif co=='6814':
  q=next(x for x in quoted['quotes'] if x['id']=='FAQ-fiscal-period');basis=q['quote']
  rationale='公式静的IR FAQ原典wholeは沿革/決算関係/株式関連の13質問と回答等を含む。producerの意味読解は決算期・財務資料掲載先の2QAだけで、選択引用は一般案内だが、未読の他回答も含むsource全体に金融内容がないとは認定できないためfinancial_content=nullの保留案。事業/利益要因の新回答を得ていないという限定結果を全source非金融認証へ拡張しない。旧4/9年次reported529.53/2826.61、10/9当時guide537.80/DPS210は不変で、FAQを現在最新予想/実現/モデル採用にしない。'
  fin=None;scope=deepcopy(review['static_page_scope']);dates=deepcopy(review['source_publication'])
 else:
  suggestion=review['classification_suggestion_only'];assert suggestion['financial_content'] is None
  basis=suggestion['basis_quote'];q=next(x for x in quoted['quotes'] if basis==x.get('quote'))
  rationale='producer元のqa/financial_content=null案を保持。会社FAQの既読2QAは創業目的/歴史（過去資本金を含む）と財務資料への案内であり、保証料収益/信用損失/回収/会計指標の対象定義や未読回答まで財務意味を認証しない。歴史的創業資本金を現在資本へ、会社の配当方針/目標が他記載にあっても投資policy/売買条件へ採用しない。選択外の新しい回答意味読解は行わず、金融内容は保留のまま。'
  fin=None;scope={'meaning_QA_count':review['meaning_QA_count'],'meaning_quote_ids':deepcopy(review['meaning_quote_ids']),'meaning_scope':review['meaning_scope'],'other_QA_answers_semantically_reviewed':False}
  dates={'publication_date':review['publication_date'],'publication_time':review['publication_time'],'retrieved_at':source['retrieved_at'],'actual_DB_firstsave':review['actual_DB_firstsave']}
 assert isinstance(basis,str) and basis in source['content']
 start=source['content'].index(basis);end=start+len(basis)
 if q.get('pdf_page') is not None:
  assert basis in source['content'].split('\f')[q['pdf_page']-1]
 basis_ref={'source_id':source['id'],'company_id':source['company_id'],'quote':basis,'quote_origin_ref':{**as_ref(quote_file),'quote_id':q.get('id')},'source_character_start':start,'source_character_end':end,'source_UTF8_byte_start':len(source['content'][:start].encode('utf-8')),'source_UTF8_byte_end':len(source['content'][:end].encode('utf-8')),'pdf_page':q.get('pdf_page'),'offset_domain':'source.content exact Unicode characters/UTF8 bytes zero-based end-exclusive','classification_scope':'Only a source-type/financial-content proposal; not verification of numerical values, all-source semantics or financial fitness'}
 basis_refs.append(basis_ref)
 classifications.append({'source_id':source['id'],'expected_version':0,'kind':'qa','financial_content':fin,'basis_quote':basis,'rationale':rationale})
 source_native=native(source)
 declared=(review.get('source_native_models_json_text_sha256') or review.get('source',{}).get('native_sha256') or review.get('source_native_sha256') or review.get('native_source_SHA256'))
 assert declared==source_native,(co,declared,source_native)
 producer_records.append({'company_id':source['company_id'],'producer_directory':str(base.relative_to(root)),'producer_bundle':as_ref(bundle_file),'producer_manifest':as_ref(manifest_file),'producer_meaning_review':as_ref(review_file),'producer_quotes':as_ref(quote_file),
  'source_id':source['id'],'native_source_sha256':source_native,'native_hash_domain':'SHA256 UTF8 json.dumps(source, ensure_ascii=False, sort_keys=True, allow_nan=False), default separators (=models.json_text); not compact JSON/transport/bundle file domain',
  'source_content_sha256':sha(source['content'].encode('utf-8')),'raw_entity':{'path':str(raw_path.relative_to(root)),'sha256':raw_sha,'bytes':raw_path.stat().st_size},
  'source_url':source['url'],'source_retrieved_at':source['retrieved_at'],'source_published_at':source['published_at'],'actual_DB_firstsave_not_assigned_here':True,
  'whole_source_object_equal_to_producer':True,'source_metadata_and_ID_unchanged':True,'source_is_local_raw_capture_identifier_as_declared':bool(metadata.get('source_id_is_local_raw_capture_identifier_not_system_derivation',False)),
  'producer_meaning_scope_preserved':scope,'dates_and_authorship_limits_preserved':dates,
  'classification_proposal':{'kind':'qa','financial_content':fin,'inputs_verified':False},'classification_basis_ref':basis_ref})
 sources.append(source)
assert len(sources)==4 and len({s['id'] for s in sources})==4 and {s['company_id'] for s in sources}=={'jp:4318','jp:6200','jp:6814','jp:7187'}
assert all(s['published_at'] is None for s in sources)
for path,h in initial_pins.items():assert fh(root/path)==h,path
out.mkdir()
def save(name,obj):
 data=obj.encode('utf-8') if isinstance(obj,str) else (json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
 with (out/name).open('xb') as f:f.write(data)
 return sha(data)
aggregate={'schema_version':1,'companies':[],'sources':deepcopy(sources),'theses':[]}
save('source-bundle.json',aggregate)
save('intake-classification-plan.json',{'classifications':classifications})
save('classification-quotes.json',{'recorded_at':now,'scope':'Exact short basisquotes from already read producer Q/A scopes; no added web/PDFpage meaning review','quotes':basis_refs})
provenance={'phase':str(outrel),'prepared_at':now,'status':'file_only_root_acceptance_and_actual_ingestion_pending','source_bundle_ref':{'path':str(outrel/'source-bundle.json'),'sha256':fh(out/'source-bundle.json')},
 'source_count':4,'unique_source_ID_count':4,'company_and_thesis_updates':0,'whole_source_objects_equal_to_original':4,'source_records':producer_records,
 'excluded_company_descriptors':removed_stubs,'source_selection_boundary':'Exactly4 newly obtained originalsource objects from named frozen producerbundles. No archive7FAQ, old originals, normalized facts, prior contexts or company stubs added.',
 'producer_manifest_pin_checks':manifest_pin_checks,'input_pins':initial_pins,
 'intake_plan_ref':{'path':str(outrel/'intake-classification-plan.json'),'sha256':fh(out/'intake-classification-plan.json')},
 'authorship_and_time_rules':['Issuer answers remain distinct from questioner assumptions; questions about OJT/41%/hiring are not company-certified facts.',
 'Meeting/document/URLdates and HTTPDate are not an inferred publication timestamp. Preserve source published_at:null and each original retrieved_at.',
 'Historical issuer forecast/strategy/ROE or dividend target is not a current forecast, realized result, investor forecast, investment policy or trading condition.',
 'General FAQ selected2answers do not certify absence of all financial content in the entire preservedsource;6814/7187 financial_content:null remain explicit unknowns.',
 'A classification proposal does not certify EPS/BPS/modelscope or carry out source intake/nativecase review.'],
 'operations':{'GET':0,'DB_connections':0,'Store_calls':0,'CLI_calls':0,'financial_calculations':0,'new_PDF_pages_or_web_pages_meaning_review':0,'normalizer_or_new_financialfacts':0,'new_nativecases_or_financialtheses':0,'IR_questions_or_sends':0,'producer_shareddocs_code_index_edits':0},
 'root_execution_only':'Independent image/quote/type acceptance, copypreflight then one actualingestion/intake sequence; no mutator in this worker.'}
save('aggregation-provenance.json',provenance)
# Independently reload the newly written aggregate and compare every fullsource.
reloaded=load(out/'source-bundle.json');assert reloaded['companies']==[] and reloaded['theses']==[]
for i,(co,folder) in enumerate(rows):
 original=load(root/'research/ir-case-studies-2026-10-15'/co/folder/'source-only-bundle.json')['sources'][0]
 assert reloaded['sources'][i]==original and native(reloaded['sources'][i])==producer_records[i]['native_source_sha256']
for br in basis_refs:
 src=next(s for s in reloaded['sources'] if s['id']==br['source_id'])
 assert src['content'][br['source_character_start']:br['source_character_end']]==br['quote']
 assert src['content'].encode('utf-8')[br['source_UTF8_byte_start']:br['source_UTF8_byte_end']].decode('utf-8')==br['quote']
for path,h in initial_pins.items():assert fh(root/path)==h,path
save('validation.json',{'recorded_at':now,'status':'file_only_aggregate_prepared','selected_companies':['4318','6200','6814','7187'],'sources':4,'unique_source_IDs':4,'whole_source_equality_pre_post':4,'native_source_SHA_matches_producer_declarations':4,'raw_entity_SHA_matches':4,'short_basisquote_character_UTF8_spans_checked':4,'producer_declared_manifest_pin_checks':len(manifest_pin_checks),'unique_input_filepins':len(initial_pins),'all_inputpins_before_after_unchanged':True,
 'classification_proposals':{'kind':'qa','financial_content_true':['4318','6200'],'financial_content_null':['6814','7187'],'financial_content_false':[],'inputs_verified':False},
 '6200_company_stub_excluded':True,'aggregate_company_thesis_count':0,'archive7FAQ_oldsource_or_disclosedfacts_added':0,'extra_semantic_scope':0,'source_ID_or_wholemetadata_rebuilt':False,
 'published_at_all_null_preserved':True,'source_storage_or_latestness_not_fabricated':True,'questioner_premises_not_companyfacts':True,'historical_outlook_not_current_or_realized':True,'company_targets_not_investment_policy':True,
 'root_current_actual_state':'Parent stated257sources/34cases/76versions/194reads/172completed before this preparation; not independently queried or asserted as current live state by this worker.',
 'DB_connections_Store_CLI_GET_normalizer_financial_adoption_nativecase_IR_sharededits':0,'parent_acceptance_pending':True})
save('README.md','''# 4社の公表Q&A原典：接続準備のみ

4318・6200・6814・7187の指定producer bundleから、新原典sourceを各1個、**全オブジェクト同一**で集約した。`source-bundle.json`はschema1、companies/thesesは空。6200のproducerに含まれるcompany stubは追加せず、旧原典・正規化facts・archive7FAQも加えていない。

分類案は全て`kind: qa`。4318/6200は既読の会社回答が当時の費用見通し・業績予想理由を含むためfinancial_content=true。6814/7187は一般FAQの限定2回答を読んだ範囲で、原sourceの選択外回答まで非金融とは認証しないためnullを保持する。引用・原文位置・根拠は分類案と`classification-quotes.json`、4producerのbundle/manifest/native/rawSHA・scopeは`aggregation-provenance.json`に保存した。

会社回答と質問者の前提を分ける。会合日・文書日・URL日・HTTP Dateから公表日時を補わず、当時の予想を現在最新予想や実現値へ移さない。会社のROE/配当等の目標を投資policy・売買条件へ採用せず、費目を合算した利益bridge・EPS/CFも作らない。

producerの読解範囲は不変で、追加Web/PDF頁の意味読解は0。原4bundle・source・contextとmanifest宣言pinsの前後一致、4source whole/native・rawSHA、4短引用のUnicode/UTF8位置を点検した。

**file-only**。DB接続・Store・CLI・GET・財務更新・normalize・新nativecase・IR・共有docs/index編集は0。rootが画像/引用/分類案を独立受入し、copy→actual保存/intakeを行う前の準備である。
''')
manifest={'schema_version':1,'recorded_at':now,'status':'file_only_preparation_frozen_root_acceptance_pending','selected_company_ids':['jp:4318','jp:6200','jp:6814','jp:7187'],'source_count':4,'source_ids':[s['id'] for s in sources],
 'source_bundle_sha256':fh(out/'source-bundle.json'),'classification_plan_sha256':fh(out/'intake-classification-plan.json'),'aggregation_provenance_sha256':fh(out/'aggregation-provenance.json'),'input_pins':initial_pins,
 'files':{str(p.relative_to(out)):fh(p) for p in sorted(out.iterdir()) if p.is_file()},'source_objects_modified':0,'DB_Store_CLI_GET_normalizer_financial_nativecase_IR_sharedcode_doc_index_changes':0}
save('manifest.json',manifest)
for path,h in initial_pins.items():assert fh(root/path)==h,path
print(json.dumps({'folder':str(outrel),'source_bundle_SHA256':fh(out/'source-bundle.json'),'classification_plan_SHA256':fh(out/'intake-classification-plan.json'),'provenance_SHA256':fh(out/'aggregation-provenance.json'),'manifest_SHA256':fh(out/'manifest.json'),'manifest_pin_checks':len(manifest_pin_checks),'whole_sources_preserved':4,'financial_content':{r['company_id']:r['classification_proposal']['financial_content'] for r in producer_records},'GET_DB_Store_CLI':0},ensure_ascii=False,indent=2))
