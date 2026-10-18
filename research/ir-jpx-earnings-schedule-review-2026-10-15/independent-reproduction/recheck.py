from pathlib import Path
from datetime import datetime,date,timedelta,timezone
from hashlib import sha256
from urllib.parse import urljoin,urlsplit
from urllib.robotparser import RobotFileParser
from copy import deepcopy
from io import BytesIO
import zipfile,posixpath,xml.etree.ElementTree as ET,json,sys
R=Path('/workspace/ir-agent');B=R/'research/ir-jpx-earnings-schedule-review-2026-10-15';C=B/'company-scoped-sources';sys.path[:0]=[str(R/'src'),str(R/'scripts')]
from ir_agent.models import parse_json,validate_source,json_text
from ir_agent.adapters.common import stable_source_id
import research_ir_universe as page
load=lambda p:parse_json(p.read_bytes().decode('utf-8'));sha=lambda b:sha256(b).hexdigest();now=lambda:datetime.now(timezone.utc).isoformat()
protected={str(p.relative_to(R)):sha(p.read_bytes())for p in B.rglob('*')if p.is_file()}
cap=load(B/'capture.json');review=load(B/'review.json');selected=load(B/'selected-rows.json');quotes=load(B/'quotes.json');combined=load(C/'source-bundle.json');projection=load(C/'per-company-projections.json');manifest=load(C/'manifest.json');repquotes=load(C/'representation-quotes.json')
common=[]
def ck(bucket,name,v):bucket.append({'name':name,'passed':bool(v)})
cc=lambda n,v:ck(common,n,v)
cc('three_original_unique_GETs',len(cap['GETs'])==len({x['url']for x in cap['GETs']})==3)
for i,c in enumerate(cap['GETs']):
 raw=(B/c['raw_file']).read_bytes();cc(f'GET{i+1}_raw_SHA_bytes',sha(raw)==c['raw_sha256']and len(raw)==c['byte_count']);cc(f'GET{i+1}_200_complete',c['http_status']==200 and c['complete_body']is True and c['error']is None);cc(f'GET{i+1}_retrieval_completion_time',c['retrieved_at']==c['http_get_completed_at']and datetime.fromisoformat(c['http_get_started_at'])<=datetime.fromisoformat(c['http_response_received_at'])<=datetime.fromisoformat(c['http_get_completed_at']))
robot,entry,xlcap=cap['GETs'];rt=(B/robot['raw_file']).read_bytes().decode(robot['encoding']);rp=RobotFileParser();rp.parse(rt.splitlines());cc('robots_both_exactpaths_allowed',all(page.robots_can_fetch(rp,x['actual_UA'],x['url'])for x in [entry,xlcap]));cc('no_new_namedAI_rule',not any(x in rt.lower()for x in ['gptbot','chatgpt','claudebot','claude-searchbot']));cc('UA_configuration_same',len({x['actual_UA']for x in cap['GETs']})==1);cc('no_retry_redirect_JS',cap['retry_count']==cap['automatic_redirects']==0 and cap['JS_execution']is False)
html=(B/entry['raw_file']).read_bytes().decode(entry['encoding']);parser=page.Page();parser.feed(html);fresh=parser.extract(entry['url']);cc('entry_text_and_links_Page_reextract',fresh['text']==entry['text']and fresh['links']==entry['links']);cc('entry_text_saved_bytes',fresh['text'].encode()==(B/'02.txt').read_bytes());anchor=entry['links'][38];cc('Excel_actual_anchor38',anchor['href']==review['selected_workbook']['actual_href']and anchor['url']==xlcap['url']and urljoin(entry['url'],anchor['href'])==xlcap['url']);cc('Excel_href_in_original_HTML',anchor['href']in html)
oldentry=review['saved_prior_entry_actualhref_found'];oldpath=R/oldentry['snapshot'];od=load(oldpath);cc('initial8697_snapshot_SHA',sha(oldpath.read_bytes())==oldentry['snapshot_sha256']);cc('initial_entry_actual_link57',od['links'][57]['url']==entry['url']and od['links'][57]['href']==oldentry['href'])
rawxl=(B/xlcap['raw_file']).read_bytes();cc('XLSX_234337_and_ZIP_magic',len(rawxl)==234337 and rawxl.startswith(b'PK\x03\x04'));cc('XLSX_MIME_exact',xlcap['content_type']=='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');cc('XLSX_complete_exact',xlcap['retrieved_at']=='2026-10-15T11:11:18.128793+00:00'and review['selected_workbook']['retrieved_at']==xlcap['retrieved_at'])
z=zipfile.ZipFile(BytesIO(rawxl));members={name:z.read(name)for name in ['xl/workbook.xml','xl/_rels/workbook.xml.rels','xl/styles.xml','xl/sharedStrings.xml','xl/worksheets/sheet1.xml']};cc('ZIP_integrity',z.testzip()is None);cc('no_macro_member',not any('vbaproject'in x.lower()for x in z.namelist()))
for name,b in members.items():info=review['xlsx_members'][name];cc('member_'+name,sha(b)==info['SHA256']and len(b)==info['byte_count']and (B/info['saved_file']).read_bytes()==b)
N={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','p':'http://schemas.openxmlformats.org/package/2006/relationships'}
work=ET.fromstring(members['xl/workbook.xml']);rels=ET.fromstring(members['xl/_rels/workbook.xml.rels']);styles=ET.fromstring(members['xl/styles.xml']);ss=ET.fromstring(members['xl/sharedStrings.xml']);sheet=ET.fromstring(members['xl/worksheets/sheet1.xml']);workpr=work.find('m:workbookPr',N);date1904=None if workpr is None else workpr.get('date1904');cc('date1904_omitted_default_false',date1904 is None)
list_sheet=[s for s in work.findall('m:sheets/m:sheet',N)if s.get('name')=='List'];cc('one_List_sheet',len(list_sheet)==1);rid=list_sheet[0].get('{'+N['r']+'}id');relation=[r for r in rels if r.get('Id')==rid];cc('List_relationship_unique_internal',len(relation)==1 and relation[0].get('TargetMode')!='External');target=relation[0].get('Target');resolved=posixpath.normpath(target.lstrip('/')if target.startswith('/')else posixpath.join('xl',target));cc('List_targets_original_sheet1',resolved=='xl/worksheets/sheet1.xml')
strings=[''.join(si.itertext())for si in []] # intentionally do not use author-produced selected-rows to decode
strings=[''.join(t.text or ''for t in si.iter('{'+N['m']+'}t'))for si in ss.findall('m:si',N)]
cellmap={c.get('r'):c for c in sheet.findall('.//m:sheetData/m:row/m:c',N)}
def cell(addr):
 c=cellmap[addr];raw=c.findtext('m:v',default=None,namespaces=N);typ=c.get('t');idx=int(raw)if typ=='s'else None
 value=strings[idx]if typ=='s'else(''.join(t.text or ''for t in c.findall('.//m:t',N))if typ=='inlineStr'else raw)
 return {'cell':addr,'type':typ,'style_index':c.get('s'),'raw_v':raw,'shared_string_index':idx,'value':value,'formula':c.findtext('m:f',default=None,namespaces=N)}
header={col:cell(col+'5')for col in 'ABCDEFGHIJK'};titles=[cell('A'+str(i))for i in range(1,5)];cc('header_exact_decoded_and_metadata',header==selected['header_cells']);cc('title_asof_exact_decoded',titles==selected['title_cells']);cc('dataset_asof_oct8',cell('A3')['value']=='2026年10月8日 現在'and cell('A4')['value']=='As of 2026/10/8');cc('code_header_original',header['B']['value']=='コード\nCode');cc('no_formula_cells',len(sheet.findall('.//m:f',N))==0)
xfs=styles.find('m:cellXfs',N);numfmts={x.get('numFmtId'):x.get('formatCode')for x in styles.findall('m:numFmts/m:numFmt',N)};cc('style5_format176_md',xfs[5].get('numFmtId')=='176'and numfmts['176']=='m/d;@')
for q in quotes['quotes']:
 qb=(B/q['file']).read_bytes();qt=qb.decode('utf-8');cc(q['id']+'_quote_exact_SHA_offset',sha(qb)==q['file_sha256']and qt[q['character_start']:q['character_end']]==q['quote'])
cc('entry_table_scope_oct8_not_update15',quotes['quotes'][0]['quote']=='2026/10/15 更新'and '2026年10月8日時点'in quotes['quotes'][1]['quote'])
cc('JPX_omission_change_caution_present','掲載されていない会社'in quotes['quotes'][2]['quote']and'予定の変更'in quotes['quotes'][2]['quote'])
cc('5pm_update_not_company_time',quotes['quotes'][3]['id']=='tomorrow-file-update-frequency-not-company-release-time')
results={x['security_code']:x for x in selected['code_match_results']};codes=['135A','1518','1721','7525','8151','9765'];matches={code:[]for code in codes}
for addr in cellmap:
 if addr.startswith('B')and addr[1:].isdigit()and int(addr[1:])>=6:
  val=cell(addr)['value']
  if val in matches:matches[val].append(int(addr[1:]))
cc('independent_B_code_match_counts',all(len(matches[x])==1 for x in ['1518','1721','7525','8151'])and matches['135A']==matches['9765']==[])
cc('unfound135A9765_not_no_schedule',all(results[c]['scheduled_date']is None and results[c]['not_evidence_no_schedule']is True for c in ['135A','9765']))
cc('combined4_sources_empty_companies_theses',len(combined['sources'])==4 and combined['companies']==combined['theses']==[])
cc('combined_bundle_manifest_SHA',sha((C/'source-bundle.json').read_bytes())==manifest['source_bundle_sha256']==projection['combined_source_bundle_sha256'])
cc('materialization_separate_after_HTTP',datetime.fromisoformat(manifest['representation_materialized_at'])>datetime.fromisoformat(xlcap['retrieved_at']))
for k,h in load(B/'old-input-hashes.json').items():cc('original_protected_'+k,sha((R/k).read_bytes())==h)
cc('no_old_artifact_changes',all(sha((R/p).read_bytes())==h for p,h in protected.items()))
# Independent Excel arithmetic: serial1=1900-01-01; for serial>=61 remove the phantom leap day.
def serial_date(token):
 n=int(token);assert str(n)==token and n>60
 return date(1900,1,1)+timedelta(days=n-2)
common_summary={'checks_count':len(common),'passed_count':sum(x['passed']for x in common),'issues':[x['name']for x in common if not x['passed']],'check_names':[x['name']for x in common],'scope':'One static OOXML ZIP parse + saved capture/anchor/quotes/schema/projection integrity. No new acquisition/DB/formula/JS execution.'}
Path('/tmp/ir-jpx-schedule-independent-common-check.json').write_text(json.dumps({'summary':common_summary,'checks':common,'protected_artifacts':protected},ensure_ascii=False,indent=2)+'\n')
expected={'1518':(2070,'2026-11-13','2027-03-31','第２四半期'),'1721':(758,'2026-11-06','2027-03-31','第２四半期'),'7525':(1593,'2026-11-11','2027-03-31','第２四半期'),'8151':(1617,'2026-11-11','2026-09-30','本決算')}
summary=[]
for code,(rn,scheduled,fy,kind)in expected.items():
 checks=[];local=lambda n,v:ck(checks,n,v);folder=C/code;bundle=load(folder/'source-bundle.json');source=bundle['sources'][0];md=source['metadata'];wb=md['original_workbook'];sr=results[code];original={col:cell(col+str(rn))for col in 'ABCDEFGHIJK'};calcdate=serial_date(original['A']['raw_v']).isoformat();calcfy=serial_date(original['E']['raw_v']).isoformat();projectionrow=next(x for x in projection['projections']if x['company_id']=='jp:'+code);sourceq=next(x for x in repquotes['quotes']if x['company_id']=='jp:'+code)
 local('one_company_source_empty_companies_theses',len(bundle['sources'])==1 and bundle['companies']==bundle['theses']==[])
 local('projection_full_object_exact',source==next(x for x in combined['sources']if x['company_id']=='jp:'+code))
 local('projection_file_SHA_exact',sha((folder/'source-bundle.json').read_bytes())==projectionrow['SHA256'])
 local('projection_ID_manifest_same',source['id']==projectionrow['source_id']==manifest['source_ids']['jp:'+code])
 local('full_source_schema',validate_source(deepcopy(source))==source)
 local('shared_full_source_ID',source['id']==stable_source_id('case-public',company_id=source['company_id'],url=source['url'],content=source['content'],metadata=md))
 local('canonical_company',source['company_id']=='jp:'+code)
 local('exact4_character_original_B_token',original['B']['raw_v']==original['B']['value']==code and len(code)==4 and original['B']['type']is None)
 local('one_exact_B_row',matches[code]==[rn]and wb['row']==rn and sr['row']==rn)
 local('all11_cell_tokens_sharedstring_indices_styles_values_exact',wb['original_cells']==original)
 local('all_header_cells_exact',wb['header_cells']==header)
 local('all_title_asof_cells_exact',wb['asof_cells']==titles)
 local('style5_datecells_and_format',original['A']['style_index']==original['E']['style_index']=='5'and wb['style_and_date_interpretation']['cellXf_numFmtId']=='176'and wb['style_and_date_interpretation']['custom_numFmt_literal']=='m/d;@')
 local('date1904_omitted_preserved',wb['style_and_date_interpretation']['workbookPr_date1904_literal']is None)
 local('schedule_date_independent_arithmetic',calcdate==scheduled==sr['scheduled_date']==wb['code_match_result']['scheduled_date'])
 local('fiscal_end_independent_arithmetic',calcfy==fy==sr['fiscal_year_end_date']==wb['code_match_result']['fiscal_year_end_date'])
 local('fiscal_kind_original_JP_EN',original['H']['value']==kind==sr['period_type_Japanese']and original['I']['value']==sr['period_type_English'])
 local('independent_serial_roundtrip',(date.fromisoformat(calcdate)-date(1900,1,1)).days+2==int(original['A']['raw_v'])and(date.fromisoformat(calcfy)-date(1900,1,1)).days+2==int(original['E']['raw_v']))
 local('no_code_suffix_padding',md['company_binding']['original_value']==code and md['company_binding']['exact_match']is True and md['company_binding']['suffix_removed']is False and md['company_binding']['padding_or_company_name_inference']is False)
 local('XLSX_original_raw_link_SHA_bytes',(B/md['original_raw_file']).read_bytes()==rawxl and md['original_raw_sha256']==sha(rawxl)and md['original_raw_byte_count']==len(rawxl))
 local('capture_file_SHA_and_record',(B/md['original_capture_file']).read_bytes()==(B/'capture.json').read_bytes()and md['original_capture_sha256']==sha((B/'capture.json').read_bytes())and md['capture_record_JSONpath']=='$.GETs[2]')
 local('source_URL_actual_Excel_anchor',source['url']==anchor['url']==md['entry_anchor']['resolved_url']and md['entry_anchor']['href']==anchor['href'])
 local('pubnull_not_asof',source['published_at']is None and md['publication_date']is None and md['dataset_asof_label']==cell('A3')['value']and md['dataset_asof_is_not_publication_time']is True)
 local('retrieved_original_HTTP_complete',source['retrieved_at']==md['original_HTTP_complete_body_at']==xlcap['http_get_completed_at'])
 local('partial_adapter_label',md['partial_representation']is True and md['original_dataset_has_multiple_companies']is True and md['extraction']['raw_full_workbook_semantically_equals_this_partial_text']is False and source['content'].startswith('JPX決算発表予定一覧：会社別部分抽出（全体資料ではありません）'))
 local('partial_saved_text_UTF8_exact',(B/md['extraction']['saved_file']).read_bytes()==source['content'].encode()and md['extraction']['sha256']==sha(source['content'].encode()))
 headerline='原表列見出し: '+' | '.join(header[col]['value'].replace('\n',' / ')for col in 'ABCDEFGHIJK')
 rowline=f'原表 List!A{rn}:K{rn}: '+' | '.join(original[col]['value']for col in 'ABCDEFGHIJK')
 local('content_header_and_original_row_exact',headerline in source['content']and rowline in source['content'])
 local('content_serial_to_ISO_explicit',f'発表予定日セル: A{rn} / 原serial={original["A"]["raw_v"]} / 1900日付系変換={calcdate}'in source['content']and f'決算期末セル: E{rn} / 原serial={original["E"]["raw_v"]} / 1900日付系変換={calcfy}'in source['content'])
 local('representation_quote_exact_not_issuer_verbatim',source['content'][sourceq['content_start']:sourceq['content_end']]==sourceq['quote']and sha(sourceq['quote'].encode())==sourceq['quote_utf8_sha256']and 'not a verbatim full-XLSX'in sourceq['basis'])
 local('no_fictional_parent',md['root_document_reference']['DB_parent_source_exists_verified']is False and md['root_document_reference']['fictional_original_source_ID_created']is False and not md.get('original_source_ids')and not md.get('original_source_id'))
 local('time_timezone_scheduledat_due_null',all(wb['code_match_result'][k]is None for k in ['time','timezone','scheduled_at','due']))
 local('occurrence_unestablished',wb['code_match_result']['occurrence']=='not_established'and wb['code_match_result']['publication_or_execution_already_occurred']is False)
 local('no_new_independent_financial_confirmation',md['independent_confirmation_count_added']==0 and md['financial_inputs_verified']is False and md['financial_values_automatically_adopted']is False)
 local('generic_verifier_unknown','unknown'in md['known_provider_byte_verifier'])
 local('all_preexisting_artifact_bytes_unchanged',all(sha((R/p).read_bytes())==h for p,h in protected.items()))
 references=[]
 for path,role in [(B/'review.json','common original acquisition/OOXML review'),(B/'capture.json','common original3 transports; XLSX GETs[2]'),(B/'selected-rows.json','original row/cell representation to compare'),(B/'quotes.json','original8 source/XML quotes'),(B/'validation.json','prior common review validation, not new independent confirmation'),(C/'source-bundle.json','frozen4-source combined bundle'),(C/'per-company-projections.json','four complete source projections'),(C/'manifest.json','original HTTP vs representation materialization'),(folder/'source-bundle.json','this full projection')]:references.append({'path':str(path.relative_to(R)),'sha256':sha(path.read_bytes()),'role':role})
 report={'schema_version':1,'recorded_at':now(),'status':'bounded_independent_recheck_complete','company_id':'jp:'+code,'source_id':source['id'],'scheduled_date':calcdate,'fiscal_year_end_date':calcfy,'fiscal_kind':kind,'original_sheet':'List','original_row':rn,'date_evidence':{'schedule_cell':'A'+str(rn),'schedule_raw_serial':original['A']['raw_v'],'fiscal_end_cell':'E'+str(rn),'fiscal_end_raw_serial':original['E']['raw_v'],'date1904_literal':date1904,'date_system':'OOXML default false (1900 system)','independent_algorithm':'date(1900,1,1) + timedelta(days=int(original_serial)-2), only original integer serial>60; adjust for fictitious1900 leap day, no formula/engine evaluation.','style_index':'5','numFmtId':'176','formatCode':'m/d;@','serial_ISO_not_verbatim_printed_text':True},'temporal_boundary':{'dataset_asof_label':cell('A3')['value'],'entry_update_label':'2026/10/15','original_HTTP_complete_at':xlcap['http_get_completed_at'],'representation_materialized_at':manifest['representation_materialized_at'],'published_at':None,'time':None,'timezone':None,'scheduled_at':None,'due':None,'occurrence':'not_established','DB_first_saved_at':None},'common_original_review':references[0],'common_check_summary':{k:v for k,v in common_summary.items()if k!='check_names'},'company_checks_count':len(checks),'company_passed_count':sum(x['passed']for x in checks),'issues':common_summary['issues']+[x['name']for x in checks if not x['passed']],'company_checks':checks,'references':references,'original_XLSX':{'raw_file':str((B/xlcap['raw_file']).relative_to(R)),'sha256':sha(rawxl),'bytes':len(rawxl),'shared_across_four_row_sources':True},'source_semantic_boundary':'Adapter-authored partial text of header/asof and one exact code row. ISO is a declared serial transformation, not issuer verbatim or four independent sources. Source hash/schema match does not prove occurrence or current schedule.','not_found_boundary':{'135A':{'matching_rows_in_this_selected_file':0,'schedule_absent_claim':False},'9765':{'matching_rows_in_this_selected_file':0,'schedule_absent_claim':False}},'execution':{'new_GETs':0,'database_accesses':0,'old_file_changes':0,'code_changes':0,'financial_decisions_or_IR':0,'formula_or_JS_execution':0,'full_test_runs':0}}
 for name in ['independent-recheck.json','independent-recheck.md']:assert not(folder/name).exists()
 (folder/'independent-recheck.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 mdtext=f'''# {code} JPX決算発表予定の独立確認\n\n**原ExcelのList行{rn}から、発表予定日{calcdate}、決算期末{calcfy}、種別「{kind}」を独立再計算して照合した。** 共通原典チェック{common_summary['passed_count']}/{common_summary['checks_count']}、会社別チェック{sum(x['passed']for x in checks)}/{len(checks)}、不一致{len(report['issues'])}。詳細は[independent-recheck.json](independent-recheck.json)、共通の原取得・読取範囲は[元review](../../review.json)を参照。各参照fileのSHAを記録し、原文・Excelの複製は増やしていない。\n\n原xlsx234,337bytesのZIP/XMLからworkbook→Listのrelationshipを辿り、date1904属性省略（既定false）、style5／numFmt176 `m/d;@`、sharedStringsとheader・全11セルの元token/型/styleを照合した。B{rn}は元の4文字`{code}`と完全一致し、末尾削除・桁補正をしていない。予定A{rn}のserial{original['A']['raw_v']}、期末E{rn}のserial{original['E']['raw_v']}を、1900-01-01起点と架空閏日の調整で再計算した。年をfilename・現在日付から補っていない。\n\n入口の実Excel anchor、capture/rawSHA、対象期、元表as-of「2026年10月8日 現在」、入口更新10/15、本文完了2026-10-15T11:11:18.128793UTCと、後の部分文字化時刻を分けて確認した。公表時刻はnull。会社sourceはadapterが作った**headerと1行の部分表現**であり、元多社xlsx全体を当該会社の逐語資料にしていない。保存本文・shared ID・fullschema・固定4source bundleと各projectionの完全一致を確認した。\n\n予定のみで、時刻・timezone・scheduled_at・dueはnull、実施はnot_establishedのまま。JPXは未掲載会社や変更後の日程があり得ると明記し、135A/9765がこの選択ファイルに未発見でも「予定なし」としない。午後5時頃は翌日分一覧の更新時刻で、会社発表時刻には転用しない。DBの実初回保存・当時利用可能性を検証した記録でもない。\n\n新GET・DB・旧file・code・金融判断・IR・数式／JS実行は0。これは保存原典と表現の独立点検であり、独立した予定情報が4件増えたという主張ではない。\n'''
 (folder/'independent-recheck.md').write_text(mdtext)
 summary.append({'code':code,'schedule':calcdate,'common_checks':common_summary['checks_count'],'company_checks':len(checks),'issues':report['issues']})
print(json.dumps({'common':common_summary|{'check_names':None},'companies':summary,'preexisting_artifacts':len(protected)},ensure_ascii=False))
