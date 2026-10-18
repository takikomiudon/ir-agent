"""Build this bounded research draft and verify exact saved citations offline."""
from datetime import datetime, timezone
import hashlib,json
from pathlib import Path
B=Path(__file__).parent
PAGES={n:(B/f'{n:02}.txt').read_text().split('\f') for n in [7,8,9,11]}
def cite(id,n,page,start,end=None):
 text=PAGES[n][page-1]
 beginning=text.index(start)
 ending=text.index(end,beginning) if end else len(text)
 q=text[beginning:ending].strip()
 p=json.loads((B/f'{n:02}.json').read_text())
 return {'id':id,'snapshot':f'{n:02}.json','text_file':f'{n:02}.txt','url':p['url'],'retrieved_at':p['retrieved_at'],'pdf_page':page,'printed_page':{7:page-2,8:page,9:page,11:page-3}[n],'quote':q}
citations=[
 cite('q1-cost-and-growth',7,4,'このような需要環境','セグメントごとの経営成績'),
 cite('fy26-forecast-assumptions',8,7,'１．主要OEM','3．構造改革フェーズ'),
 cite('revenue-guidance',8,8,'2026年度','All Rights Reserved'),
 cite('expansion-kpi',9,11,'売上高向上','収益体質改善'),
 cite('china-oneoff',9,15,'FY25       中華系拡販','FY26は補助金減額'),
 cite('income-statement-classification',11,65,'営業利益','税金等調整前当期純利益'),
 cite('china-impairment',11,79,'当連結会計年度','当社の連結子会社である東莞'),
 cite('public-capital-policy',8,10,'■年間92円','All Rights Reserved'),
]
manifest=json.loads((B/'manifest.json').read_text())
actual=[x for x in manifest if json.loads((B/x['snapshot']).read_text()).get('http_get_attempted')]
sources=[]
for row in actual:
 p=json.loads((B/row['snapshot']).read_text())
 date={2:'2026-08-05',7:'2026-08-05',8:'2026-05-12',9:'2026-05-12',11:'2026-06-18'}.get(int(row['snapshot'][:2]))
 source={**row,'published_date':date,'published_at':None,'publication_precision':'day' if date else 'unknown','publication_note':'Document cover or official index states a date; exact time is unknown. Revised PDFs may have a later replacement date that is not established here.','raw_file':p['capture_files'][p['url']]['raw_file'],'sha256':p['sha256']}
 sources.append(source)
common_unresolved={'action':'unresolved','valuation_change':None,'numeric_parameter_change':None,'reason':'Definition confirmation alone does not establish forecast earnings, price attractiveness or a position decision.'}
def branch(id,condition,interpretation,next_action):
 return {'id':id,'condition':condition,'interpretation':interpretation,'next_research_action':next_action,**common_unresolved}
draft={
 'schema_version':1,'artifact_type':'research_draft_not_harness_ingest_bundle','company':{'security_code':'5988','company_id':'jp:5988','name':'株式会社パイオラックス'},
 'recorded_at':datetime.now(timezone.utc).isoformat(),'research_as_of':'2026-10-15','status':'research_only_unresolved','investment_horizon':'数カ月〜1年',
 'methodology':{'adopted_sources':[{'local_path':'third_party/anthropic/skills/earnings-preview/SKILL.md','upstream_commit':'574ed3624aebd0418c7e96cd101262f30210ab26','adopted':'Use company-specific revenue/margin metrics and conditional operating scenarios.'},{'local_path':'third_party/anthropic/skills/thesis-tracker/SKILL.md','upstream_commit':'574ed3624aebd0418c7e96cd101262f30210ab26','adopted':'Record falsification, catalysts and no-change outcomes with the thesis.'}],'adaptation':'This project maps public-definition questions to driver changes before any valuation inputs are updated; this is not an upstream numerical investment strategy.'},
 'business_context':{'statement':'自動車関連等と医療機器を展開。主要OEM生産減の影響、高付加価値品・非日系OEM拡販、生産再配置が公開説明上の論点。最新1Qは売上増加と営業減益が同時に生じている。','citation_ids':['q1-cost-and-growth','fy26-forecast-assumptions']},
 'sources':sources,'citations':citations,
 'public_information_review':{'reviewed_document_urls':[x['url'] for x in sources],'dedicated_qa_documents_found':[],'status':'bounded_review_complete_additional_public_qa_coverage_unconfirmed','details':'IRライブラリ、財務レポート、IRカレンダーの公開リンク・本文および取得4PDFを確認。専用の質疑応答/Q&Aリンクはこの範囲で見つからなかった。別公開先、未取得の説明会動画、全Webの不存在は確認していない。','question_send_readiness':'not_ready','reason':'Complete current public-answer coverage and freeze a sourced thesis/valuation/decision policy before selecting a sendable question.'},
 'documented_company_figures':[{'period':'2027年3月期1Q','scope':'連結','unit':'百万円','revenue':'15761','operating_income':'266','citation_id':'q1-cost-and-growth','type':'reported_actual'},{'period':'2027年3月期通期','scope':'連結','unit':'百万円','revenue':'63000','operating_income':'1500','parent_net_income':'700','eps_jpy':'27.45','citation_id':'revenue-guidance','type':'company_forecast_not_analyst_scenario'},{'period':'FY2025','unit':'億円','kpi':'グローバル拡販','existing_products':'68','case_products':'13','citation_id':'expansion-kpi','image_check':'management-plan-p11.png','type':'company_kpi_definition_unconfirmed'},{'period':'FY2026','unit':'億円','kpi':'グローバル拡販','existing_products':'100','case_products':'15','citation_id':'expansion-kpi','image_check':'management-plan-p11.png','type':'company_kpi_target_definition_unconfirmed'}],
 'issues':[
 {'id':'5988-expansion-kpi-definition','status':'candidate_definition_question','business_issue':'グローバル拡販というKPIを連結売上ブリッジへどう対応させるか。','citation_ids':['expansion-kpi','revenue-guidance','q1-cost-and-growth'],'hypothesis_under_test':'KPIが示す新規拡販と既存販売の継続・減少、為替の影響を区別できれば、OEM台数だけに依存しない成長の検証が可能になる。会社の成長達成を仮定していない。','unresolved_point':'グラフの年度値が当該年度の実売上/計画売上、基準期比増収寄与、複数年度の累計案件などのいずれであるか、同じ案件の年度間継続計上の扱い。','valuation_mapping':{'driver_paths':['revenue_bridge.expansion_kpi_basis','revenue_bridge.overlap_with_existing_sales'],'eventual_calculator_paths':['scenarios.base.inputs.eps_jpy','scenarios.base.inputs.fcf_jpy'],'dependency':'売上ブリッジ→原価/費用・税/株数/運転資本等の公開根拠付きモデル→EPS又はFCF。定義回答から直接EPSへ数値を代入しない。','current_input_values':None,'prohibited_changes':['PE倍率の同時引上げ','回答確率の推定','KPI全額を連結売上に自動加算','会社予想への二重加算']},'falsification':'KPIが将来受注累計等であり年度売上に変換できない、又は既存売上との重複が区分できない場合、KPIから追加売上を推計する仮説を採用しない。','question':'2026年5月12日公表「中期経営計画の見直し」11ページの「グローバル拡販」について、グラフの各年度の値は、その年度に計上する売上高、基準年度からの増収寄与、あるいは累計の案件規模のどれを表す指標でしょうか。また、前年度から継続する案件も当年度の値に含まれる定義でしょうか。公表済み資料の数値を重複して売上予測へ加算しないための定義確認です。公表範囲で説明のある資料があれば、その箇所をご教示ください。','branches':[branch('annual-sales','当該年度の売上高で継続案件も含むと明確に説明された場合','KPIは売上の内数。合計を連結売上へ足さず、比較可能な前年差と他の増減要因に分解する。','区分の継続性・為替・他要因を公開資料で照合してから売上ブリッジを再構築'),branch('incremental-or-cumulative','基準期比増収寄与又は受注累計等と明確に説明された場合','基準期/計上期間/計上単位を固定。年度売上への換算条件がない値は年次モデルへ使わない。','該当する定義に対応する売上ブリッジへ修正し、期間が不明なら変換を保留'),branch('unclear','曖昧・定義不明・回答拒否・無回答の場合','新たな増収を仮定せず、既存公開売上予想を変更しない。','次回公開資料で定義の明示を待つ')]},
 {'id':'5988-china-oneoff-scope','status':'candidate_accounting_scope_question','business_issue':'中国の生産再配置費用と特別損失の重複調整を防ぐ。','citation_ids':['china-oneoff','income-statement-classification','china-impairment','q1-cost-and-growth'],'hypothesis_under_test':'過年度の費用区分が明確なら、営業収益力の変化と純利益だけに影響する損失を混同せず検証できる。将来の費用消失・利益回復を保証する仮説ではない。','unresolved_point':'中計15ページの約6億円が営業費用のみか、特別損失の中国減損337百万円などを含む集計か、公開有報の費用項目との対応。','valuation_mapping':{'driver_paths':['normalized_earnings.china_relocation_scope','normalized_earnings.overlap_with_impairment'],'eventual_calculator_paths':['scenarios.base.inputs.eps_jpy','scenarios.bear.inputs.eps_jpy'],'dependency':'会計区分確認→過年度利益ブリッジの重複修正→税/非支配/株数の根拠確認→別途将来シナリオ。過年度約6億円を将来EPSへ自動加算しない。','current_input_values':None,'prohibited_changes':['特別損失減損の営業利益への加算','約6億円と337百万円の重複加算','減損のFCFへの二重加算','一時という表現だけによる将来回復の断定']},'falsification':'営業/特別損失区分又は重複が確認できなければ、約6億円を調整営業利益や将来利益の加算項目として採用しない。','question':'2026年5月12日公表「中期経営計画の見直し」15ページの中国に関する「生産再配置による一時費用（約6億円）」の集計範囲について確認させてください。これは売上原価・販管費等の営業費用に限る説明でしょうか、それとも有価証券報告書76ページの中国固定資産減損337百万円など、特別損失に計上した費用も含む説明でしょうか。既に公表された過年度費用と財務諸表上の区分の対応を確認する趣旨です。公表済みの説明箇所があれば、その箇所をご教示ください。','branches':[branch('operating-only','約6億円が営業費用のみと公開説明に基づき確認できた場合','中国減損は営業利益の下位にあるため調整営業利益へ加えない。約6億円も将来利益に自動加算しない。','実績の営業利益/純利益ブリッジを分離し、再発や恒常コストを別の公開根拠で検証'),branch('includes-special-loss','約6億円に減損等が含まれると公開説明に基づき確認できた場合','約6億円全額を営業費用の一過性要因として扱えない。重複する区分を除く必要がある。','内訳が明らかな区分のみ整理し、不明分は調整しない'),branch('unclear','範囲不明・曖昧・回答拒否・無回答の場合','区分を推定せず、調整利益の加算は行わない。','今後の公開財務資料を待つ')]}],
 'excluded_questions':[{'question':'中国の生産再配置費用は一時費用ですか','reason':'中計15ページに既に「一時費用（約６億円）」と明記。追加質問は会計範囲だけ。','citation_ids':['china-oneoff']},{'question':'直近1Qで営業減益・経常増益なのはなぜですか','reason':'最新短信の定性説明にコスト増と前年支払手数料不発生の説明がある。','citation_ids':['q1-cost-and-growth']},{'question':'2027年3月期までの配当方針は何ですか','reason':'公開説明資料に92円下限と配当性向方針が明示。','citation_ids':['public-capital-policy']}],
 'investment_decision':{'status':'unresolved','proposed_action':'unresolved','valuation':None,'quote':None,'buy_price_jpy':None,'take_profit_price_jpy':None,'scenario_probabilities':None,'reason_codes':['no_verified_market_quote','no_sourced_analyst_valuation_inputs','no_adopted_numeric_investment_policy','position_not_verified','public_answer_coverage_incomplete'],'note':'Published company forecasts are recorded facts about company guidance, not adopted analyst scenarios or trade triggers.'},
 'next_catalyst':{'event':'2027年3月期第2四半期業績発表','window':'2026年11月初旬','exact_date':None,'source_snapshot':'06.json','note':'公式カレンダーの概算時期。変更可能性の記載あり。日付や時刻を補わない。'},
 'ir_contact':{'url':'https://www.piolax.co.jp/jp/shareholder/contact/form02/','verified_at':'2026-10-12T15:56:25.696076+00:00','verification_source':'research/ir-recovery-2026-10-13/recovery_c-page-observations.jsonl','conditions':['個人投資家の所属選択を既存調査で確認。現時点での再送信/再確認はしていない。','メール回答の無許可転用・二次利用・当該顧客以外への開示は禁止と案内。返信を得てもその制約を確認して保存/利用範囲を決める。','全問い合わせに回答するとは限らず、書面/電話/FAXになる場合もある。'],'form_fields_entered':False,'submitted':False},
 'limitations':['対象企業の投資候補採用や購入を決めた研究ではない。','市場価格・コンセンサス・保有情報・将来利益・投資閾値を取得/推定していない。','株価評価に必要な入力がないため回答ごとのbuy/exit分岐はまだ固定できず、全回答分岐の投資判断はunresolved。','最新資料の特定は取得した公式索引表示に基づく。全チャネルの完全な探索ではない。','専用Q&Aは範囲内で未発見。公開回答が他所で見つかれば質問を削除する。','PDF内の表と図で費用区分や範囲が曖昧なものを暗算で補っていない。'],
}
(B/'draft.json').write_text(json.dumps(draft,ensure_ascii=False,indent=2)+'\n')
checks=[]
for item in citations:
 page=(B/item['text_file']).read_text().split('\f')[item['pdf_page']-1]
 assert item['quote'] in page,item['id']
 checks.append({'citation_id':item['id'],'exact_quote_in_saved_page':True})
for s in sources:
 assert hashlib.sha256((B/s['raw_file']).read_bytes()).hexdigest()==s['sha256']
assert len({x['requested_url'] for x in manifest})==8
assert len(actual)==8
assert all(x['http_status']==200 for x in actual)
verification={'verified_at':datetime.now(timezone.utc).isoformat(),'unique_document_urls':8,'actual_document_gets':8,'retried_document_gets':0,'successful_documents':8,'html_documents':4,'pdf_documents':4,'local_pre_dispatch_filter_stops':3,'exact_citations':checks,'raw_document_hashes_verified':True,'ir_submissions':0,'form_fields_entered':0,'actual_trade_decision_made':False}
(B/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(verification,ensure_ascii=False))
