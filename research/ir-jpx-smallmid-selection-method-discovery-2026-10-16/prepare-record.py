from pathlib import Path
from datetime import datetime, timezone
import json,hashlib,subprocess
P=Path(__file__).resolve().parent
rel=lambda p:str(p.relative_to(Path('/workspace/ir-agent')))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda n,v:(P/n).write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
cap=json.loads((P/'capture.json').read_bytes());pdfrow=cap['GETs'][2];pdf=P/pdfrow['raw_file'];text=(P/'methodology-full.txt').read_bytes().decode('utf-8');pages=text.split('\f');html=(P/'text/02.txt').read_bytes().decode('utf-8')
(P/'pdfinfo.txt').write_bytes(subprocess.run(['pdfinfo',str(pdf)],check=True,capture_output=True).stdout)
(P/'text/cover.txt').write_bytes(pages[0].encode());(P/'text/toc.txt').write_bytes(pages[1].encode())
Q=[]
def quote(i,n,s,kind='PDF'):
 t=text if kind=='PDF' else html
 if kind=='PDF':
  page=pages[n-1];startpage=sum(len(x)+1 for x in pages[:n-1]);assert s in page;start=startpage+page.index(s);pagen=n
 else:start=t.index(s);pagen=None
 end=start+len(s);assert s.strip() and end>start and t[start:end]==s
 Q.append({'id':i,'source_kind':kind,'text_file':rel(P/('methodology-full.txt' if kind=='PDF' else 'text/02.txt')),'text_sha256':sha(P/('methodology-full.txt' if kind=='PDF' else 'text/02.txt')),'physical_page':pagen,'printed_page':n-1 if kind=='PDF' else None,'quote':s,'unicode_start':start,'unicode_end':end,'utf8_start':len(t[:start].encode()),'utf8_end':len(t[:end].encode())})
quote('P0-version',1,'2026 年 8 月 3 日版')
quote('P1-schedule',11,'基準日は、毎年 6 月最終営業日')
quote('P2-marketcap-basis',11,'「時価総額」は指数用上場株式数')
quote('P3-exclusion-financial-period-ref',11,'下記４．（１）①の決算期間')
quote('P4-existing-largecap-PDF',12,'上位 14%以内の銘柄のみを除外する。')
quote('P5-liquidity-floors',12,'150 億円以下')
quote('P6-liquidity-relaxation',12,'500 銘柄を超えるまで売買\n 代金及び時価総額の基準を 10 億円刻みで引き下げる。')
quote('P7-quant-weight',12,'0.7 × (a) 3 年平均 ROE の順位スコア\n                               ＋ 0.3 × (b) 3 年累積営業利益の順位スコア')
quote('P8-qualitative-scale',13,'差異が最大でも 10 銘柄程度')
quote('P9-qualitative-female',13,'30%以上')
quote('P10-ranking-tie',13,'「⑤(a) 3 年平均 ROE の順位スコア」が高いものを優先する。')
quote('P11-incumbent-retention',13,'250 位以内')
quote('P12-addition-median',14,'中央値を上回ってい')
quote('P13-irregular-exclusion',14,'上場廃止、整理銘柄への指定、特別注意銘柄への指定')
quote('P14-no-deficit-topup',14,'原則数を満たすための非定期の追加は行わない。')
quote('H1-existing-largecap-HTML',None,'上位18%以内の銘柄のみを除外する。','HTML')
quote('H2-html-update',None,'2026/08/07 更新','HTML')
save('quotes.json',{'offset_semantics':'Zero-based half-open Unicode character / UTF-8 byte offsets in pinned decoded text, preserved form-feed separators. Quotes are short evidence anchors; procedural descriptions are paraphrases, not further quotations.','quotes':Q})
rule=lambda id,page,clause,summary,anchors=[]:{'id':id,'physical_pages':page,'clause':clause,'paraphrase_ja':summary,'quote_ids':anchors}
rules=[
rule('S1',[11],'III.1(1)','定期入替基準日は毎年6月最終営業日、公表は8月第5営業日、入替後算出は8月最終営業日。初期選定の2016-06-30とは区別。',['P1-schedule']),
rule('S2',[11],'III.1(2)①','基準日時点の東証Prime/Standard/Growth上場普通株。重複上場外国株は原則、直近1年の東証売買代金が最大の場合のみ。普通株同等として算出者が特に必要と認める例外あり。2016初期選定の旧市場列挙を現在母集団に使わない。'),
rule('S3',[11,12],'III.1(2)②(a)–(i)','以下をいずれか満たす銘柄を除外: 上場3年未経過（明記のテクニカル上場例外あり）、直近期短信又は内部統制報告未開示（算出者のやむを得ない事情例外）、参照決算期間のいずれかの期首又は期末に債務超過、参照期間全期営業赤字（OP非開示時はIII.4(1)③の代替利益）、参照期間全期最終赤字、直近期財務諸表等にGC注記（その後提出の四半期含む）、直近期内部統制報告に開示すべき重要不備又は評価結果表明不能、基準日時点で整理/特別注意指定、基準日から1年以内の公表措置/改善報告徴求（再提出含む）/上場契約違約金徴求/RRI75以上の該当かつ程度が大きい場合。(f)–(i)は必要に応じ基準日後から選定までの状況も勘案。決算期間の正確な定義は未読III.4(1)①へ参照されており、今回独自補完しない。',['P3-exclusion-financial-period-ref']),
rule('S4',[11,12],'III.1(2)③','②後の集合で基準日時価総額順位上位20%を大型株として除外。ただし既存構成銘柄はPDF上14%。HTML概要18%と不一致のため採用境界は未解決。時価総額は指数用上場株式数ベースで、浮動株時価総額と同一視しない。',['P2-marketcap-basis','P4-existing-largecap-PDF','H1-existing-largecap-HTML']),
rule('S5',[12],'III.1(2)④','③後の集合から直近1年売買代金合計150億円以下、及び基準日時価総額100億円以下の銘柄を除外。候補500未満の場合は500を超えるまで両閾値を10億円刻みで下げる（500に達したら停止とは読み替えない）。合併/株式交換前は原則存続/親会社の売買代金、株式移転等テクニカル上場前は算出者が主体とみなす会社の売買代金を使用。',['P5-liquidity-floors','P6-liquidity-relaxation']),
rule('S6',[12],'III.1(2)⑤','④の集合を3年平均ROEと3年累積営業利益でそれぞれ順位化。各1位は候補数と同点、最下位1点。ROE順位点0.7＋累積OP順位点0.3が総合スコア。財務値そのものの70/30加重平均ではない。詳細データ定義はIII.4参照で今回は未読。',['P7-quant-weight']),
rule('S7',[13],'III.1(2)⑥','④の集合に独立社外取締役（独立役員指定人数が取締役総数の過半数）/女性役員（有報役員状況による30%以上）、IFRS採用又は適用開示、決算情報及びCG報告のTDnet英文開示の状況を勘案した定性加点。定量のみの選定との差異が最大10銘柄程度の規模、項目は将来変更可能。今回4頁には各項目の具体加点数が示されず、均等点や独自点数を補わない。',['P8-qualitative-scale','P9-qualitative-female']),
rule('S8',[13],'III.1(2)⑦','定量＋定性の最終点降順。ただし3年平均ROEと直近ROEの両方が④集合の下位10%若しくは負に該当する銘柄、又は3年累積OP負の銘柄はそれらを除いた銘柄の後順位。最終点同点は3年平均ROE順位点の高い方優先。ROEも同点の残余処理を今回の本文から補わない。',['P10-ranking-tie']),
rule('S9',[13,14],'III.1(2)⑧','初期選定は上位200。定期入替は既存構成で最終順位250以内を維持。200未満なら最終順位上位から、3年平均又は直近ROEが④集合中央値超、かつ最終順位200以内の2条件を満たす銘柄を追加。なお不足すれば最終順位200以内の未採用を3年平均ROEの高い順に200まで追加。250以内維持は②～④の除外を飛び越える規則ではない。',['P11-incumbent-retention','P12-addition-median']),
rule('S10',[14],'III.1(2)⑨及び末尾','将来の組織再編等による上場廃止見込みは必要に応じ調整。著しく不適当なら算出者が非採用可能。指数コンサルテーションで決定された場合は投資機能性/安定性から新規追加を見送る。機械ルールのみで完全一致を保証しない。'),
rule('S11',[14],'III.2','上場廃止、整理銘柄又は特別注意銘柄指定で非定期除外。算出者が継続を著しく不適当と認める裁量除外あり。詳細の指数修正日はIV参照で未読、ここから株式の実売却日を生成しない。',['P13-irregular-exclusion']),
rule('S12',[14],'III.3','株式移転等で旧構成が上場廃止され新設等会社が遅滞なく上場する場合、算出者が主体とみなす会社が旧構成なら追加。スピンオフ対象が権利落日～効力発生日に新規上場する場合も追加。構成不足の穴埋めを目的とした非定期追加は行わない（続きは未読次頁）；特殊コーポレートアクション追加まで禁止した規則ではない。',['P14-no-deficit-topup'])]
review={'recorded_at':datetime.now(timezone.utc).isoformat(),'purpose':'Historical-results-based research candidate selection source discovery, limited to JPX-Nikkei Mid and Small Cap Index; no numeric screening or policy adoption.','source':{'title':'JPX日経中小型株指数算出要領','authors':['株式会社ＪＰＸ総研','株式会社 日本経済新聞社'],'version_label':'2026年8月3日版','printed_issue_date':'2026-08-03','all_clause_effective_date':None,'effective_date_limit':'Cover edition/issue date is not a separately verified effective date for every historical clause. Change-history pages were used only as front-matter/version locators, not fully reviewed methodology.','source_url':pdfrow['url'],'retrieved_at':pdfrow['http_get_completed_at'],'raw_entity_file':rel(pdf),'raw_sha256':sha(pdf),'text_file':rel(P/'methodology-full.txt'),'text_sha256':sha(P/'methodology-full.txt'),'page_count':22,'meaning_and_image_review_physical_pages':[11,12,13,14],'printed_pages':[10,11,12,13],'locator_only':['cover physical1 edition/authors/issue','TOC physical2','front matter physical3/4 edition history locator','first headings physical15/16 to locate unreviewed data definitions'],'not_reviewed':'Other pages not semantically reviewed; no full-book or complete index replication claim.','publication_time':None,'actual_database_first_save':None},'discovery_result':{'historical_results_selection_workflow_found':True,'complete_machine_reproducible_policy_confirmed':False,'forecast_values_required_by_read_selection_clauses':False,'meaning':'Read selection clauses use historical ROE/cumulative operating profit, corporate disclosures and market size/liquidity; no company EPS forecast or target price is required in these clauses. Missing data definitions do not license surrogate inputs.','implementation_or_investment_adoption':False},'rules':rules,'conflicts':[{'id':'D1','topic':'Incumbent large-cap exclusion','PDF':'14%','HTML':'18%','PDF_quote':'P4-existing-largecap-PDF','HTML_quote':'H1-existing-largecap-HTML','HTML_page_update_label':'2026/08/07','resolved':False,'handling':'Preserve both labelled versions. Do not decide a numerical production threshold or attribute an unverified reason for discrepancy.'}], 'remaining_for_possible_replication':[{'topic':'Financial data definitions','location':'III.4, physical15–16 onward','status':'Saved full PDF, not meaning/image reviewed','needs':'Applicable latest fiscal periods, precise ROE/equity/profit basis, irregular-period adjustments and OP alternatives must be read before mapping data.'},{'topic':'Exact qualitative scoring','location':'III.1(2)⑥ physical13','status':'Criteria and approximate turnover scale stated; exact per-item points not established in read pages','needs':'Do not invent scores or label a quantitative-only adaptation exact index reproduction.'},{'topic':'Original universe and status/data availability','status':'Not acquired or screened','needs':'A fixed343-company contact list is not the index-wide population for percentile ranks, thresholds, medians or membership buffers. RepRisk and calculator judgements are not automatically available as public inputs.'},{'topic':'Residual tie and boundary mechanics','status':'Do not infer','needs':'PDF supplies score tie preference but no invented final tie ordering or rounded percentile method.'}], 'horizon_boundaries':{'index_reconstitution':'Annual June reference / August publication and effective index calculation.','internal_research_monitoring':'Existing author quarterly review is a separate management practice.','user_holding_horizon':'A few months to one year; not imposed by index rules.','profit_taking_price_or_order_rule':None,'IR_effectiveness_or_answer_likelihood':None,'company_exclusion_as_investment_recommendation':False},'operations':{'new_GETs':3,'GET_budget':4,'budget_exhaustion_not_pursued':True,'PDFs_acquired':1,'additional_hosts':0,'redirect_followed':0,'retries':0,'DB_access':0,'Store_initializations':0,'company_screening':0,'formal_policy_adoption':0,'financial_input_adoption':0,'IR_contact':0},'stop_reason':'Target methodology acquired in3GET; prescribed4selection pages read and visually checked. Other indices, constituent data, data-definition pages and implementation are outside this finite phase.'}
save('review.json',review)
checks=[]
for q in Q:
 t=Path('/workspace/ir-agent',q['text_file']).read_bytes().decode('utf-8');b=t.encode();checks.append({'id':q['id'],'nonempty':bool(q['quote'].strip()),'unicode_exact':t[q['unicode_start']:q['unicode_end']]==q['quote'],'utf8_exact':b[q['utf8_start']:q['utf8_end']].decode()==q['quote'],'positive_spans':q['unicode_end']>q['unicode_start'] and q['utf8_end']>q['utf8_start'],'text_sha_match':sha(Path('/workspace/ir-agent',q['text_file']))==q['text_sha256'],'within_physical_page':q['source_kind']!='PDF' or q['quote'] in pages[q['physical_page']-1]})
assert len(Q)==17 and all(all(v is True for k,v in r.items() if k!='id') for r in checks)
assert len(cap['GETs'])==3 and all(r['HTTP_status']==200 and r['complete_body'] and not r['error'] for r in cap['GETs'])
save('validation.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'pass_for_finite_source_capture_and_quote_binding_only','new_GET_count':3,'quote_count':len(Q),'nonempty_quote_count':sum(bool(q['quote'].strip()) for q in Q),'checks':checks,'all_quotes_nonempty_and_positive_exact':True,'PDF_raw_SHA':sha(pdf),'full_text_SHA':sha(P/'methodology-full.txt'),'PDF_page_count':22,'selected_image_count':4,'selected_images_visually_read':True,'source_interpretation_limits':['HTML/PDF14vs18conflict unresolved','Detailed data definitions not read','No actual index-screen reproduction or financial policy adoption','Content-Encoding-decoded entity, not wire capture','No DB first-save claim'],'network_stop':'Success at necessary methodology; unused fourthGET was not dispatched.'})
