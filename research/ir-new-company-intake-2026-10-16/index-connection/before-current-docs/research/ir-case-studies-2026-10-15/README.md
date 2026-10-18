# 実企業資料によるIR研究の例

公開資料を読んで質問を減らし、事実・会社予想・未確認のモデル入力を分ける。会社別研究と追加の比較研究を収録し、投資先の選定や共通の金融条件を作るものではない。

現在は実DB153資料（公開152・市場1）・公開資料あり23社、native監視16case/32版/99既読。[構造化v27](disclosed-fact-index-v27.json)は18社129factで、29親entryからfact別参照を解決すると31派生sourceになる。[5988資本残高8値の保存・比較](5988/annual-capital-balance-disclosed-facts/qualitative-review/parent-acceptance.json)まで、29source/122factを実台帳へ保存・分類した。[歴史ROICの参考計算](../ir-historical-roic-role-reproduction-2026-10-16/README.md)は明示した研究mappingに限る。金融入力・実policy・正式IRは未採用。個社記録内の旧件数と未確認は各時点の履歴として保持する。

後続研究では、[コムシスの著者6論点](1721/author-conditions/case-record.md)を3社の[研究監視v4](../ir-research-monitoring-integration-2026-10-15/README.md)へ接続し、[リックスの製品構成比](7525/author-original-product-review/case-record.md)は会社目標と著者の判断条件を分離した。[東陽テクニカの正式資料追補](8151/issuer-annual-followup/README.md)はrobots確認で停止し、著者予測との実績比較は未確認のままである。

| 会社 | 保存資料から分かったこと | 現在の扱い |
|---|---|---|
| [IIJ 3774](3774/README.md) | CAPEX・リース等の区分、会社予想と実績の期、配当方針・過去の分割とEPS定義。 | CAPEX質問の追加判断価値が未立証のため不送信。正式な有効質問0件。[公開Q&Aと通期表の照合](3774/faq-to-filing-guidance-comparison/README.md)を完了。[PTCの期間表示草案](3774/ptc-period-reading-question-preflight/README.md)は研究用で数値評価へ未接続。 |
| [パイオラックス 5988](5988/README.md) | 一時費用と減損の範囲の違い、2027年3月期までの配当方針、信託自己株式の控除。 | [減損423のP/L・CF対応](5988/cashflow-oneoff-bridge-review.md)を確認。約6億円の現金内訳・包含・期間は未解決。[次回準備票](5988/question-residual-review-2026-10-16/README.md)で既知と残余を分け、送信準備未完了。 |
| [千葉銀行 8331](8331/README.md) | 年間・中間配当、配当性向と期限付き還元方針。一般的規制説明を資本コストへ流用しない。 | 金融モデルの研究例。窓口未確認のため1,819社の窓口台帳には含めない。送信可能質問0件。 |
| [日本冶金工業 5480](5480/README.md) | 用途別需要・輸入競争・固定費の説明を確認。正常利益だけでなく再投資・資本収益・資金調達の点検が必要。 | 最新決算本文と全サイクル等は未確認。8資料を保存・分類し、watchを維持。 |
| [ニッスイ 1332](1332/README.md) | 正式1Q短信・公開Q&A・予定表を確認。連結基準と部分指標、正式CF未作成と補足表示を区別。 | 7資料を保存・分類。[予定3件](1332/catalyst-schedule-candidates.md)は時刻・timezone未確認。予定と実施を分ける。 |
| [VRAIN Solution 135A](135A/presentation-followup/README.md) | 最新中間短信・説明・FAQ・会社想定Q&Aと、AENTROの委託分析を確認。会社予想と著者の条件付き見通しを区別。 | 15資料を保存・分類。[著者条件と最新KPIの照合v2](135A/author-condition-followup/case-record-v2.md)と[顧客数定義の照会草案v2](135A/customer-counting-question-preflight-v2.md)を保存。会社の集計単位と著者目安の対応は未解決、AND条件の成立も未確認。[9公表値の入力対応](135A/model-input-mapping.md)はモデル未採用。 |
| [ユキグニファクトリー 1375](1375/README.md) | 公式事業紹介・一般FAQを確認。追加の公開feedは503で保留。 | 初期4資料を保存・分類。設定ファイルの到達を財務本文の取得と数えない。[追加取得の区切り](1375/statement-followup/README.md)。 |
| [ホクト 1379](1379/README.md) | 正式Q1短信・説明・予定表に加え、配当方針とShared Research本文を取得。外部本文の通期数値は会社予想の再掲。 | 公開8資料を保存・分類。[4条件の決算preview](1379/earnings-preview-candidate.md)と[価格snapshot](1379/provider-market-snapshot/README.md)を保存。予定表の年度表記不整合は未確認のまま保持。 |
| [三井松島HD 1518](1518/author-conditions/README.md) | 著者の定性見解と会社計画の転載を区別。7/22の予想修正と8/7維持、投資収益のP/L区分、CF未作成、株式基準を確認。 | [会社3資料](1518/issuer-quarter-followup/README.md)を保存・分類。[既存1論点への照合](1518/author-condition-followup/case-record.md)を完了し、公開解決6項目を再質問から除外。[旧/新会社予想の4facts](1518/guidance-revision-facts/README.md)も保存。数値モデル/新IR質問は未採用。 |
| [ミライト・ワン 1417](1417/initial-public-review/README.md) | 公式入口・決算一覧を取得、静的HTMLに短信PDFのリンクなし。 | 索引2件、財務本文0。旧capture IDと共有IDの差を[追補](1417/initial-public-review/id-contract-followup.json)で区別。[共通schema別版](1417/initial-public-review/canonical-source-validation.json)は実DB未登録。 |
| [L is B 145A](145A/initial-public-review/README.md) | 公式短信・説明資料の索引を取得、静的HTMLにPDFリンクなし。 | 索引2件、財務本文0。[別版](145A/initial-public-review/canonical-source-validation.json)で会社IDと取得完了時刻を保持。原記録は残し、実DB未登録。 |
| [コムシスHD 1721](1721/initial-public-review/README.md) | 会社予想HTMLは億円、2026年3月期実績と2027年3月期会社計画を別列で表示。 | 会社予想HTML1・短信索引1を[取り込み](1721/initial-public-review/actual-intake.json)。5月12日以降の改定・正式短信・CFは未確認。[12項目の構造化](1721/actual-and-plan-facts/README.md)はモデル未採用。 |
| [不動テトラ 1813](1813/initial-public-review/README.md) | 決算一覧を取得したが静的応答の資料欄は空。 | 2GETで終了。索引1件、財務本文0。別経路探索は続けず実DB未登録。 |
| [ナカノフドー建設 1827](1827/initial-public-review/review.md) | 正式Q1は日本基準連結、国内外の採算差・受注/繰越、5/14予想の据置、CF未作成を確認。 | [2資料を取り込み](1827/initial-public-review/actual-intake.json)、[EPS/DPS3項目](1827/eps-dividend-facts/README.md)を保存。FISCO元本文はrobots403で[未取得](1827/external-comment-review/review.md)、題名PBRを公正倍率へ転用しない。 |
| [奥村組 1833](1833/initial-public-review/README.md) | Q1営業利益と経常利益の方向差、予想のFX除外、セグメント組替、株式処分考慮済みEPS/DPSを区別。 | [3資料を取り込み](1833/initial-public-review/actual-intake.json)。[意味レビュー](1833/initial-public-review/independent-meaning-review.md)と[EPS/DPS3項目](1833/eps-dividend-facts/README.md)を保存。為替損益をOPへ移したり予想未織込みを将来ゼロとしない。 |
| [リックス 7525](7525/pdf-size-followup/README.md) | QUICKの96頁。会社NIから計算したEPS、著者CAPM推計、製品比率の注視点を区別。 | [案内と完全PDFを取り込み](7525/external-report-review/actual-intake.json)。[3項目](7525/external-parameter-facts/README.md)と[1問草案v3](7525/original-product-ratio-question-preflight/preflight-v3.md)を保存。[著者論点v2](7525/author-original-product-review/case-record-v2.md)へ当期費用・区分再編・営業/純利益の違いを統合済み。草案は比較範囲の確認に限定し正式登録は未準備。WACC/目標倍率は未採用。 |
| [東陽テクニカ 8151](8151/external-report-review/README.md) | Astrisの独自EPS/DPS予測とQUICKの会社NI由来EPSを[比較](8151/cross-author-comparison/README.md)。 | [Astris2資料](8151/external-report-review/actual-intake.json)と[QUICK2資料](8151/quick-nomura-review/actual-intake.json)を保存。[旧6予測値](8151/external-estimate-facts/README.md)・[別の3表示値](8151/quick-external-parameter-facts/README.md)を混ぜず、現在採用予測・会社原典確認・前向き評価とはしない。 |
| [オオバ 9765](9765/pdf-redirect-followup/README.md) | SESSAの民間案件・単価・人員と利益率上振れの見方を、会社予想転載と分離。 | [告知とPDFを取り込み](9765/pdf-redirect-followup/actual-intake.json)。[著者論点](9765/author-conditions/case-record.md)は数値反証・評価式未設定。市場PERを目標倍率へ転用せず、年度表示差を保持。 |
| [トライアルHD 141A](141A/author-hypothesis-review/README-v2.md) | 岩井コスモの4注視点を、会社の累計計画・著者予想・当時の市場PERと分離。 | [著者記録v2の独立確認](141A/author-hypothesis-review/independent-v2-addendum.md)まで完了。[公式決算一覧の限定確認](141A/initial-public-followup/README.md)は索引1件・財務本文0。両研究は実DB未登録、現在の業績確認・評価条件・質問は未準備。 |
| [アンリツ 6754](6754/initial-public-qa-followup/README.md) | 会社Q&Aと説明資料を取得。通信受注の増加に前倒しが含まれ、売上計画どおりで通期予想据置。 | [原2資料](6754/actual-public-import/README.md)と[ノート版1資料](6754/actual-notes-import/README.md)を保存・分類。[著者論点との比較v2](6754/author-condition-followup/case-record-v2.md)で既答5問を再質問から除外。評価入力・実IRは未採用。 |
| [ローツェ 6323](6323/initial-public-statement-followup/README.md) | 連結中間短信と決算説明資料を取得。需要観測・会社見通し、供給施策、工場計画を区別。 | [原2資料を保存・分類](6323/actual-presentation-import/README.md)。[著者比較](6323/author-condition-followup/case-record.md)・[追補](6323/author-condition-followup/presentation-addendum.md)、[5公表値](6323/disclosed-facts/README.md)、[AP製品説明](6323/advanced-packaging-public-check/review.md)を確認。工場の期間対応と利益効果は保留、IR・金融採用0。 |
| [日本電技 1723](1723/author-conditions/case-record.md) | Envalithの通期収益定着/繰越と施工能力の2論点。個別report本文は未取得。 | [著者3sourceを保存](1723/actual-author-import/README.md)。会社IRの静的カテゴリに同期間PDF未特定、原本比較は未完了。参考PERを公正倍率にせず金融採用/IR0。 |
| [アールプランナー 2983](2983/author-conditions/case-record.md) | Astrisの独自EPS3期と販売棟数/粗利mix/販管費効率を区別。 | [著者入口/原本2source保存](2983/actual-author-import/README.md)、[3EPS](2983/disclosed-facts/README.md)独立確認済。NI英語単位の限定訂正は旧履歴保持。[会社原本3本](2983/issuer-quarter-followup/README.md)・著者比較・受注/ASP有限確認を完了。[会社2数値v2](2983/issuer-disclosed-facts-v2/README.md)は出典訂正済み。[受注取消の1問草案](2983/order-netting-question-preflight/README.md)は比較定義だけの候補で正式登録未準備、金融採用/IR0。 |
| [アイリック 7325](7325/business-structure-followup/README.md) | 会社の保険選択/直営店・FC支援・技術サービス。 | 新原source1件を分類しcase初回既読1。保険業タグだけで引受/規制資本/通常モデルを確定しない。 |
| [ライフネット 7157](7157/saved-FAQ-accounting-scope/README.md) | 保存FAQの連結IFRSと日本基準個別配当基準、保険/運用の説明。 | 保存原文1件をqa分類しcase初回既読1。原raw/現在freshness・IFRS17/CSM/配当余力・modelは未認定。 |

| [ラサ商事 3023](3023/author-conditions/README.md) | 大型案件反動減という著者推察1件。会社計画転載と独自予測を区別。 | [著者原本1sourceを実保存](3023/actual-author-import/README.md)。[通期・1Q会社原本との比較](3023/issuer-annual-quarter-followup/README.md)完了。1Q減収でも利益増の要因を区別し、金融採用/IR0。 |

| [ダイダン 1980](1980/source-applicability-review/README.md) | 会社NI由来のQUICK EPSと3株数basis、TSR恒等式/peer/cost推計の役割を整理。 | [入口/本文2sourceを実保存](1980/actual-author-import/README.md)。[会社原本との比較](1980/issuer-quarter-followup/README.md)で同じNI273億円・原EPS211.42円とQUICK換算210.89円を区別。実定性job1件完了、case v2。固定引用内の具体business条件0、金融採用/IR0。 |
| [しずおかFG 5831](5831/financial-structure-followup/README.md) | 会社連結原本で銀行/リース、貸出/預金・預金利息の役割を確認。 | 原2sourceに[規制資本の入口/原本2件](5831/regulatory-capital-followup/README.md)と[公表資本/還元方針1件](5831/capital-policy-followup/README.md)を追加しcase v3・既読5。会計8.0%・規制16.24%・所要資本の8%計算を区別。金融採用/IR0。 |

17:45時点の[公表数値索引v20](disclosed-fact-index-v20.json)は17社95fact・23派生artifact（会社/原典20組）。旧22entry/93記録を保持し、[2983会社予想2値v2](2983/issuer-disclosed-facts-v2/README.md)を追加。[独立点検](2983/issuer-disclosed-facts-v2/independent-recheck.md)で原典記録の不備を訂正、[索引の独立確認](2983/issuer-disclosed-facts-v2/root-index-v20-independent-recheck.md)も完了。金融モデルへ未採用。実DBは2026-10-15 17:45 UTC時点で20社116資料（公開115・市場1）、財務内容あり19社。[研究監視v19](../ir-research-monitoring-integration-2026-10-15/README-v19.md)は12case62sourceで今回範囲の新triggerなし。数値仮説の完成ではなく、[定性review job](../ir-qualitative-job-integration-2026-10-15/README.md)へ12caseを引継ぎ済み、通常dailyの金融要件は保持。[31タスクv4](../ir-issue-owner-backlog-2026-10-15/README-v4.md)は旧19taskの元担当/DAGを保持。2983 p44/48は後続確認済み。以下の件数は各時点の履歴。

08:54時点の[公表数値索引v10](disclosed-fact-index-v10.json)は12社55項目。実DBは2026-10-15 08:54 UTC時点で11社74資料（公開73・市場1）、財務本文あり10社。以下のv9/v8はそれぞれの時点の履歴として保持する。

[公表数値の索引v9](disclosed-fact-index-v9.json)は10社49項目。1721の実績6項目と会社計画6項目を追加し、原文の億円と更新時点を保持した。実DBは2026-10-15 08:44 UTC時点で9社69資料（公開68・市場1）、財務本文あり8社。以下のv8記録は08:03 UTC時点の履歴として保持する。

[公表数値の索引v8](disclosed-fact-index-v8.json)は9社37項目を、実績・会社予想・外部予測、単位・期間/予想版、原文と派生資料のハッシュ付きで参照する。1518の旧/新予想4件と、台帳外9702の著者新E3件/会社CE再掲1件を追加した。8331/9702は窓口台帳外、1375は構造化財務factがないため、この索引の9社と上の研究例9社は同じ集合ではない。[索引v7](disclosed-fact-index-v7.json)の7社29項目も不変で保持する。追加CF/売上項目はfactごとにartifact/sourceを明記する。[初回3社9項目](disclosed-fact-index.json)と中間版も保持した。2026-10-15 08:03 UTC時点の実DBは窓口台帳内8社67資料（公開66資料を分類済み、市場1資料）、財務本文を含む会社は7社。[1518取り込み](1518/issuer-quarter-followup/actual-intake.json)を参照。[05:44時点の不足棚卸し](coverage-after-provider-market.json)と[旧57資料時点](coverage-after-hokto.json)も保持した。市場資料は提供者申告の10月14日15:30日本時間の2,048円で、現在価格・取引所との独立照合や鮮度方針の採用は未完了。千葉銀行と派生数値資料は研究ファイルのみ。金融入力の検証、予測や倍率・確率の採用、投資仮説の作成はしていない。

[8社の質問準備レビューv2](ir-question-readiness-review-v2.md)は、公開情報で閉じた問い、次に行う公開確認、条件付きでIRに残る定義/橋渡しを区別する。[旧4社版](ir-question-readiness-review.md)も保持した。未解決の定義は研究草案に残す。現在の登録には保存済み数値thesis版が必要で、未完成の会社は質問登録へ進めていない。数値path変更のない質問自体を禁止する規則とは区別する。VRAINの[現在CFから予測への対応](135A/current-cashflow-to-forecast-basis.md)とホクトの[採用前提](1379/adoption-prerequisites.md)で、追加計算器では解けない期間・予測・実行条件を具体化した。

意味の点検は [IIJ](3774/financial-input-meaning-review.md)と[パイオラックス](5988/financial-input-meaning-review.md)、抽出の手順と限界は各社の `extraction-notes.md` に記録した。公開資料で解けた内容は未解決IR質問として再利用せず、残る不明点も判断価値を確認する前に送信対象へしない。

[保存済みIwai NO335の追加6社比較v2](../ir-iwai-business-hypotheses-2026-10-15/README-v2.md)で著者と会社計画を分けた。[対象台帳の親照合](../ir-iwai-business-hypotheses-2026-10-15/issuer-route-inventory/parent-target-membership.json)では6社中5社が現1,819社DBにあり、8725は窓口未確認・DB外の研究例である。

[追加6社の会社資料確認結果](../ir-iwai-business-hypotheses-2026-10-15/issuer-followup-outcomes.md)は全6社の有限結果を区分し、接続停止を投資除外としない。


現在の構造化索引は[v25・18社107fact](disclosed-fact-index-v25.json)。[5988税注記6値](5988/tax-disclosed-facts/README.md)を追加して旧107factの値/期間/意味区分を保持し、現在は[実保存・分類済み](5988/tax-disclosed-facts/actual-connection/README.md)。全27source/100factが接続済み、対象外8331/9702の2source/7factだけfile-only。金融入力の採用とは別で、年度末BPSや過去税率を現在評価へ持ち越さない。監視は16case/30版/97既読で、[known-by修正後の5988登録](5988/native-case-setup/known-by-native-acceptance/README.md)を完了。[10社18sourceの定性比較](../ir-structured-facts-qualitative-review-2026-10-15/README.md)を反証後に実保存し、全84job完了・pending/leased0を確認。元原典の再表現は新期資料として扱わず、全source unchangedと各caseの未解決を保持した。旧記録の件数はその時点を表す。

[銀行/保険業3例の会社構造比較](../ir-financial-business-scope-comparison-2026-10-15/README.md)に、業種タグからモデルやIR質問へ飛ばさない具体例をまとめた。
