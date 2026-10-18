# 継続作業の状態

利用者の2026-10-15の指示: 停止の指示があるまで、目前のタスクからIR投資判断ロジックを構築する。既存の方針・ベストプラクティスを優先し、出典のない投資条件を独自に作らない。実IR送信・注文・有料契約をこの指示から推定しない。

## 最新状態（実DB・case台帳19:55 UTC／コード19:53 UTC／研究20:02 UTC）

現在の検証は[全1,425件成功](../research/ir-qualitative-independent-code-review-2026-10-15/parent-acceptance.json)。native監視は13case・17版・68既読資料、管理日を全件設定済みで今回の新job0。公表値の[索引v21](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v21.json)は18社97fact・24artifact entry・21会社/原典組。[31taskの進捗overlay v5](../research/ir-issue-owner-backlog-2026-10-15/README-v5.md)は元task/owner/DAGを固定し、有限完了と新材料待ち・会社定義・著者仕様・金融未採用を区別する。

保存DBは122資料（公開121・市場1）、公開資料あり21社・財務内容あり20社、分類121・完了job54（intake51・定性3）。計測attempt51/events102/receipt51は分類と定性3件のleaseで、全工程の能力ではない。source来歴はlegacy28/trusted94。会社台帳1,819社のwatch/held:falseは実保有の確認ではなく、明示保有申告・金融thesis・正式質問・返信・実policy採用・実送信・注文は0。定性job接続時点の検証は[1,396テスト・39.381秒](../research/ir-qualitative-job-integration-2026-10-15/parent-full-suite.json)・[受入](../research/ir-qualitative-job-integration-2026-10-15/parent-acceptance.json)完了。新しい定性job接続の16統合検証を含み、全体検証中の実DB116資料は不変。前の[株数単位1,380件](../research/ir-disclosed-share-unit-integration-2026-10-15/parent-acceptance.json)、[任意保存照合1,372件](../research/ir-public-capture-validation-2026-10-15/README.md)、[保有申告境界1,351件](../research/ir-catalog-position-boundary-review-2026-10-15/README-v3.md)も当時の記録として保持。

後続の起票上限修正は[1,397テスト・38.907秒](../research/ir-qualitative-queue-fairness-2026-10-15/README.md)。limit1で既存triggerが後続caseを遮る不具合を再現・修正し、新規jobだけを上限へ数える。実DB117資料のSHAは検証前後で不変。先の1,396件は接続時点の履歴で、旧artifactは書き換えていない。

[daily/intakeの新規のみ起票](../research/ir-new-only-queue-integration-2026-10-15/README.md)も接続した。`--new-only`の明示指定で既存triggerを枠から除き、旧modeの再表示契約・packetを保持。全1,400件・37.961秒成功、実DB117資料SHA不変。

[定性worker向け表示](../research/ir-qualitative-worker-view-2026-10-15/README.md)を追加し、全1,405件・37.213秒成功。原packet不変で、実1980 jobの表示は185,844→50,444 UTF8 bytes。元case文書・新規source全文・SHAを保持し、現在の完了権限は認定しない。token数や会社数能力の実測へ換算しない。実DB117資料SHA不変。

[前回観測の固定引継ぎ](../research/ir-qualitative-prior-review-2026-10-15/README.md)を追加し、全1,409件・39.328秒成功。新packetは元caseを保持したまま直前完了の観測・結果/source SHAを固定する。旧packetへ後付けせず、実1980/5831の完了参照もread-onlyで照合。実DB121資料SHA不変。

[規制資本FCFE中間計算](../research/ir-regulatory-fcfe-integration-2026-10-15/README.md)を原典p22へ照合して接続し、全1,421件・37.099秒成功。年次NI−明示規制資本再投資のみで、終価/株価/再投資予測を作らない。DBを開かないCLI、負値/0・株主/主体/通貨/期間の不一致を確認し、実DB121資料SHA不変。[5831の入力map](../research/ir-case-studies-2026-10-15/5831/regulatory-fcfe-input-map/README.md)は会社通期NI候補115000百万円と、未確認の同期間再投資・株主範囲を区別し、計算未実施。後続の[公式プレゼン3頁](../research/ir-case-studies-2026-10-15/5831/capital-policy-followup/README.md)で公表資本/還元方針を確認し、既答の再質問を除いた。

[独立コードレビュー](../research/ir-qualitative-independent-code-review-2026-10-15/README.md)で、一時保留後の復旧でも旧superseded署名が再起票を妨げるP2を1件修正した。旧job/packet/attemptを保持して新しい時点のjobへ連鎖し、保留継続中・既存pending/leased/completedは迂回しない。新規4件を含む全1,425件・36.665秒成功、実DB122資料のSHA不変。旧1,421件以下は当時のcheckpointとして保持。

[研究監視v19](../research/ir-research-monitoring-integration-2026-10-15/README-v19.md)は12case62保存source。旧10caseを完全保持し、全旧管理日/論点IDを維持。3023会社原本2件との比較と、1980の入口/本文2件の入力適用点検を追加した。新triggerなし12、論点確認待ち0、根拠不足0、job0は保存資料の確認範囲であり、全Web更新や数値仮説の完成ではない。1980のbusiness条件は固定引用内で未確認0件、source適用研究と金融仮説を区別する。観測後の登録でblind予測でもない。[数値索引v20](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v20.json)は17社95fact・23派生artifact（会社/原典20組）。旧22entry/93記録を保持し、[2983の会社予想2値v2](../research/ir-case-studies-2026-10-15/2983/issuer-disclosed-facts-v2/README.md)を追加。[独立点検](../research/ir-case-studies-2026-10-15/2983/issuer-disclosed-facts-v2/independent-recheck.md)でv1の原典記録不足を解消した。v1と指摘は保持し、派生source・金融モデルへ未採用。[索引の独立確認](../research/ir-case-studies-2026-10-15/2983/issuer-disclosed-facts-v2/root-index-v20-independent-recheck.md)も完了し、95参照・25artifactの解決と旧93記録の保持が一致。

[2983の会社原本3本](../research/ir-case-studies-2026-10-15/2983/issuer-quarter-followup/README.md)は[独立確認の指摘0](../research/ir-case-studies-2026-10-15/2983/issuer-quarter-followup/independent-recheck.md)で[実保存](../research/ir-case-studies-2026-10-15/2983/actual-issuer-import/README.md)を完了。会社EPS304.27円・NI3,250百万円と著者EPS308.31円を分け、株式分割の会社注記を外部著者の分母へ移さない。[著者条件との対応](../research/ir-case-studies-2026-10-15/2983/author-issuer-comparison/README.md)は公開済みの粗利・販管費・販売数量をIR再質問から除外し、追加3頁・受注定義4頁・ASP2頁の独立確認も完了。市場規模の仮定単価を会社ASPへ移さず、この有限ASP探索を終了した。精密ASP/将来株数の未確認だけで永久待ちやIR必須とせず、評価倍率・価格条件の未採用を別に保つ。[直接EPSの適用点検](../research/ir-case-studies-2026-10-15/2983/eps-applicability-review/README.md)も完了し、著者仕様taskは候補範囲/比較保留の有限列挙として終了。金融採用は別task。

[1518の追加ニュース一覧](../research/ir-case-studies-2026-10-15/1518/acquisition-completion-followup/README.md)では山洋の完了は未確認。[7525の公開FAQ10問](../research/ir-case-studies-2026-10-15/7525/public-definition-faq-review/README.md)も比率定義を解消せず、両資料を独立点検後に実保存した。

[JPX予定4件](../research/ir-research-monitoring-integration-2026-10-15/jpx-event-report-v1.json)は1721が11/6、7525・8151が11/11、1518が11/13（2026年、原表10/8時点）。8151は9月期本決算、他3社は3月期第2四半期。timezone/時刻不明、実施未確認。1枚の原表の4行であり独立確認4件ではない。[10社31タスクv4](../research/ir-issue-owner-backlog-2026-10-15/README-v4.md)は旧6社19taskの全object/担当/DAGを保持し、4社各3taskを追加。2983の同版に残るp44/48候補は後続のASP確認で実施済みのため再読しない。Pの有限結果を未試行へ戻さず、Cを実返信待ちと呼ばない。親も旧19taskの全field保持を確認した。

[3023の著者論点](../research/ir-case-studies-2026-10-15/3023/author-conditions/README.md)は大型案件反動減という推察1件だけ。[独立確認済み原本](../research/ir-case-studies-2026-10-15/3023/first-author-report/independent-recheck.md)を[実保存](../research/ir-case-studies-2026-10-15/3023/actual-author-import/README.md)し、会社通期・新1Qの[保存URL棚卸し](../research/ir-case-studies-2026-10-15/3023/saved-issuer-route-inventory/README.md)から[通期・1Qの原本比較](../research/ir-case-studies-2026-10-15/3023/issuer-annual-quarter-followup/README.md)と[独立確認](../research/ir-case-studies-2026-10-15/3023/issuer-annual-quarter-followup/independent-recheck.md)を完了、[会社2sourceも保存](../research/ir-case-studies-2026-10-15/3023/actual-issuer-import/README.md)。反動説明/予想据置は既答。環境設備の1Q減収・販管費減/増益を通期減益の成立/反証にせず、会社資本コスト/還元方針は売買ルール未採用。

具体的なIR候補は[7525の1問草案v3](../research/ir-case-studies-2026-10-15/7525/original-product-ratio-question-preflight/preflight-v3.md)。売上範囲とGP/LV共通性に絞り、A/B/Cを比較可否へだけ対応する。『情報価値は0ではない』というv1表現を訂正し、未推定のまま0/正を断定しない。質問・分岐等の不変と、実DBの同社質問0/thesis0を[親が確認](../research/ir-case-studies-2026-10-15/7525/original-product-ratio-question-preflight/root-v3-recheck.json)。v3は公表済み沈黙規則とJPX予定等の新根拠だけを追加し、本文・ABC・数値未設定を維持。金融入力・現在窓口等が不足し、正式登録・送信は未準備。

[8151の著者比較](../research/ir-case-studies-2026-10-15/8151/cross-author-comparison/README.md)はQUICK会社NI由来EPSとAstris独自予測を混ぜない。[1721原HTMLの精度確認](../research/ir-case-studies-2026-10-15/1721/plan-display-precision-review/README.md)でも丸め注記は見つからず、NI表示差の原因は未解決。[明示評価式の探索](../research/ir-explicit-valuation-route-review-2026-10-15/iwaicosmo-entry-followup/README.md)は公開サンプル1件の限定確認で終了。[保存済み著者資料15例の能力比較v6](../research/ir-author-source-capabilities-2026-10-15/README-v6.md)は旧12例を保持し、3023・1980と2134の告知のみの経路を追加した。独自予測・会社予想転載・取引PER・定性的条件を区別し、今回の2983会社原本・追加頁は別の比較記録で確認する。旧版・数値・採用状態は不変。

[保存5経路の初回確認](../research/ir-author-routing-remaining-catalog-2026-10-15/README-five-route-outcomes.md)を完了。1980は会社NIからのQUICK換算EPSで[原本独立点検](../research/ir-case-studies-2026-10-15/1980/first-author-report/independent-recheck.md)の指摘0、2134は会社告知/実リンクのみ、本体host robots301で停止し本文未取得。いずれも予測/評価式を推測せず、同じ失敗URLや別経路を再探索しない。5経路の完了は1476社全ての金融研究完了ではない。

[1980の入力適用点検](../research/ir-case-studies-2026-10-15/1980/source-applicability-review/README.md)は会社NI→QUICK EPS/日次netshares・歴史平均/発行済・CAPM/debt/WACCの役割を限定。入口/原本は[実保存済](../research/ir-case-studies-2026-10-15/1980/actual-author-import/README.md)。外部の金融条件を補完せず、この有限点検は完了した。[定性レビューjob](qualitative-research-jobs.md)のopt-in接続を実装・受入済み。12case・62資料を[実台帳へ引継ぎ](../research/ir-qualitative-job-integration-2026-10-15/actual-bootstrap.json)、新規job0・既存全テーブル不変を確認。登録済みの現在進捗はqualitative show/queueから読み、旧manifestのreportはそのファイルの時点を表す。外部scheduler/Web巡回/LLM自動実行は未設置。

[1980会社原本との比較](../research/ir-case-studies-2026-10-15/1980/issuer-quarter-followup/README.md)で純利益273億円・EPS211.42円とQUICK換算EPS210.89円を区別した。新公式PDFだけを実定性jobで処理し、case v1→v2・既読2→3・完了後再起票0。旧manifest v19は12case62資料の当時の範囲として保持し、現在台帳は12case・63既読source・13版。新資料の確認は利益見通しの独立信号や売買判断ではない。

[2983受注取消の1問草案](../research/ir-case-studies-2026-10-15/2983/order-netting-question-preflight/README.md)も保存した。販売棟数に関する著者論点へ対応する会社定義だけに絞り、純額/総額・差異/不明のA/B/Cを比較範囲に対応する。保存2本文の指定語検索hit0と再利用5引用の照合だけで、全公式資料の不開示とはしない。金融path/価格判断への影響・現行窓口は未確認、正式登録・送信は未準備。

[1,819社のモデル点検母集団](../research/ir-universe-model-routing-intake-2026-10-15/README.md)を全件照合。銀行10・証券18・保険8・その他金融20の56社を、金融構造の会社根拠を確認する手掛かりとして分けた。業種からmodelや除外を自動確定せず、残る1,763社も通常model適合とはしない。56社には現DBの公表財務sourceがなく、コード順の5831を最初の会社原本確認にする。これは投資順位ではない。

[5831の会社原本による金融構造点検](../research/ir-case-studies-2026-10-15/5831/financial-structure-followup/README.md)は3GET・1PDF・意味4頁で完了し、入口/原本2件を保存・分類した。預金利息の営業費用としての役割、銀行/リースの連結範囲を根拠に金融株主価値モデルの研究へ振り分ける。表紙自己資本比率8.0%は会社が規制比率でないと明記し、規制必要資本へ転用しない。13番目のnative caseへ既読2件を引継ぎ、現在13case・65既読・14版。管理日未設定、追加job0・金融採用0。母集団の56社にsource0という記録は作成時点で、後続の5831を未試行へ戻さない。

[5831の規制資本原本](../research/ir-case-studies-2026-10-15/5831/regulatory-capital-followup/README.md)を追加2GET・意味2頁で確認。持株会社連結16.24%、銀行連結14.43%/単体13.33%、所要資本計算RWA×8%を区別する。会計8.0%や配当可能余剰へ代用せず、buffer/目標/将来RWA等は未設定。原2sourceの分類と実定性jobを完了し、5831 case v2・既読4・再起票0。現在native13case・67既読・15版。

[5831の公表還元/資本方針](../research/ir-case-studies-2026-10-15/5831/capital-policy-followup/README.md)を物理p18/19/20で確認。配当性向50%以上への方針、自己株取得上限、評価差額金の扱いは既答として再質問しない。期末CET1予想14.29%と完全適用試算13.56%、Q1実績16.24%と同試算14.00%を区別し、年間再投資額へ代入しない。新1sourceの分類・実定性jobを完了し、5831v3/既読5、全13case・16版・68既読、再起票0。前回観測の固定引継ぎも実packetで確認した。 [独立点検](../research/ir-case-studies-2026-10-15/5831/capital-policy-followup/independent-recheck.md)は94項目・指摘0。追加の[p17基準確認と入力map v2](../research/ir-case-studies-2026-10-15/5831/public-capital-basis-check/README.md)はGET/DB/job追加0で、評価差額金/最終化基準の既答を除いた。年間再投資は未設定、質問を増やしていない。

[5831の研究管理日設定](../research/ir-case-studies-2026-10-15/5831/management-review-setup/README.md)を完了。Anthropicの四半期点検から2027-01-16 Tokyoへ明示適応し、case v4/config2・既読5を保持した。設定改版のlast_review_id resetに伴い、旧条件と完了2job観測を固定case文書へ継承。全13case・17版・68既読・全管理日設定、今回queue新規0、他全table不変。独立107項目・指摘0。p17追補も独立35項目・指摘0。

[担当依頼テンプレート](../.agents/skills/jp-equity-ir/references/roles.md)へpacket種別の振分けと定性job専用の主担当/独立点検依頼を追加した。金融thesis作成の指示を定性jobへ渡さず、5項目結果契約・限定読取・管理日・lease/復旧を明示。変更前の完全byte版とSHAは[更新記録](../research/ir-qualitative-independent-code-review-2026-10-15/roles-update.json)に保存し、旧実験fingerprintは遡及変更しない。

[5831会社予想2値](../research/ir-case-studies-2026-10-15/5831/issuer-guidance-facts/README.md)を単一原典から構造化し、[親が受入](../research/ir-case-studies-2026-10-15/5831/issuer-guidance-facts/parent-acceptance.json)。通期NI115000百万円→115000000000JPY、EPS217.91円/株、2026-04-01〜2027-03-31/日本基準連結/会社予想を保持。旧23entry/95factを完全保持したv21は18社97fact、派生資料のDB登録・金融採用0。

[backlog進捗v5](../research/ir-issue-owner-backlog-2026-10-15/README-v5.md)も[親が31task/10caseの完全objectと全参照を照合](../research/ir-issue-owner-backlog-2026-10-15/parent-v5-recheck.json)。旧v4を編集せず、2983のASP/直接EPS仕様の有限完了等を別mappingへ記録した。全31taskの解消や送信準備完了とはしない。

手順は[処理図](decision-flow.md)、[研究担当テンプレート](../.agents/skills/jp-equity-ir/references/roles.md)、[収集保留7host](../research/ir-source-access-holds-2026-10-15/README-v3.md)を参照。著者の原文、会社情報、プロジェクトの観測設計を分け、欠けた価格・倍率・確率・退出条件を独自に補わない。

[原文抜粋8例の点検](../research/ir-source-reasoning-benchmark-2026-10-15/README.md)は固定キーとの分類・引用対応8/8。キー独立確認と親の理由読取を完了。必須運用文書に関連実例があり、未見データ/一般性能/金融成績/確率校正の検証とはしない。[新取得の保存契約案](../research/ir-public-capture-contract-review-2026-10-15/README.md)は不足8点を整理した段階で、未実装・旧source不変。

[価値と価格の方針範囲](../research/ir-value-price-policy-scope-review-2026-10-15/README.md)では既存原典4箇所・7引用を確認し、明示購入規則は今回の範囲で未特定。値の範囲による判断も原文にあり、確率加重だけを著者の普遍要件としないが、閾値を補完せずコードは不変。[CAN SLIMの公式確認](../research/ir-oneil-policy-review-2026-10-15/README.md)はrobotsの固定UA向け全path禁止により1GETで終了し、記事本文0・規則未採用。別経路探索や記憶で補完しない。続くRixの架空回答点検と返信処理の修正は、以下の完了記録を参照する。

[Rix架空回答8件](../research/ir-rix-reply-branch-exercise-2026-10-15/README.md)は固定キーとの分岐・適用保留・金融変更なしが8/8一致。親が理由全文と意味を点検し、独立keyレビューも保存した。枝IDとしての参照は解決できるが、有効なJSONPathという主張はしない。合成公表抜粋と同一agent再利用を明示し、実IRの精度や成績へ一般化しない。[返信解釈の5原則](../research/ir-reply-interpretation-practices-2026-10-15/README.md)は原典・適応・意味レビューを区別した有限チェックリスト。

[runtimeの最終修正](../research/ir-reply-runtime-gap-review-2026-10-15/README-v2.md)は、旧依存返信の訂正と、元原典自体の公開性不明を金融更新前に点検する。新返信自身のpublic分類を保持し、reply ID/訂正版のholdとsource ID/snapshot SHAのholdを別fieldへ保存。新規20＋既存関連91テスト、全1332件が成功。独立v2レビューは3memory probe・固定コード5copyのbyte一致を確認し、親も実DBのSHA不変を確認した。[運用上の意味と再評価](reply-dependency-holds.md)を追補し、元資料と旧仮説の自動巻戻しはしない。旧1324件・最初の再現とレビューは別checkpointとして保持する。

[FD原典の限定探索](../research/ir-fd-interpretation-scope-2026-10-15/README.md)は保存資料から公式Q&Aを特定できず、検索toolも利用できないためGET0で終了した。法的対象者・重要性境界・公表方法は未確認で、会社policyやプロジェクト分類を法的自動判定へ転用しない。

[実公表Q&A6組の確認](../research/ir-public-qa-interpretation-cases-2026-10-15/current-review.md)を保存した。会社FAQ・決算Q&A要旨3原典から質問/回答を抽出し、原18spanとraw HTMLの対応を独立確認。会議日を公表日と読める2labelは旧版を保持してv2で訂正し、親もQ/A不変を確認した。意味レビューは会社予想/実績、短期限定/影響0、一般的な粗利構造/案件固有数値、calendar案内/日付、売買単位/本人保有を区別し、金融変更・売買・正式返信登録0。続くIIJ FAQと正式Q1開示の比較は完了し、以下へ記録した。現在最新やFAQ更新日を推定しない。

[Toyota元workbookの限定確認](../research/ir-toyota-workbook-route-2026-10-15/README.md)は保存原PDF1件40頁のURL情報と本文で実リンク未特定、候補0・GET0で終了した。3943円と表示入力再計算3944.09円の差の理由は未確認のまま、再計算やURL推測を重ねず、現代の同社評価・購入規則へ転用しない。

[IIJのFAQ/正式通期表比較](../research/ir-case-studies-2026-10-15/3774/faq-to-filing-guidance-comparison/README.md)は2原典・4指標・正規化8factで、億円/百万円の表示額が全一致。正式表の通期行・連結IFRS・期間を親も原画像で確認し、「百万円未満四捨五入」と表示精度を保持した。同一版/FAQ更新日/現在最新/達成の認定はしない。API/CLI/再現の一致を保存し、CLIは変更前SHAの時点でメモリDB2接続、実運用DB0。独立点検も完了し、[索引v13への追加確認](../research/ir-case-studies-2026-10-15/3774/faq-to-filing-guidance-comparison/parent-index-v13.json)を保存。旧67記録を保持したまま8factを索引へ追加し、実DBやモデルへは未追加。

[PTC GPUの公開範囲](../research/ir-case-studies-2026-10-15/3774/ptc-gpu-public-basis-review/README.md)は既存2原典・関連5頁に限定して確認。受注約120億円は構築100億・運用保守20億の5年間総額で、2Q26に一部売上予定。Q1の約60億円の受注・売上は別のEC案件。120億を年額や利益へ変換しない。p24半期列とQ1受注説明の関係は未解決。[期・連結範囲の追補](../research/ir-case-studies-2026-10-15/3774/ptc-period-scope-followup/README.md)も2原典4頁で終了し、持分法対象の決算日差異注記をPTCへ転用しなかった。

PTCの主要主張は[独立レビュー](../research/ir-case-studies-2026-10-15/3774/ptc-gpu-public-basis-review/independent-recheck.md)で合計6頁を確認。[期間表示の1問preflight](../research/ir-case-studies-2026-10-15/3774/ptc-period-reading-question-preflight/README.md)は半期欄とQ1説明の基準の対応だけに限定した研究草案で、数値path/actionはnull、情報価値未推定、正式登録/送信notready。比較への必要性がない場合は質問しない。既存CAPEX/運用粗利率の除外済み質問を再開しない。

[7525の営業利益増減・区分再編](../research/ir-case-studies-2026-10-15/7525/quarter-profit-bridge-review/README.md)は保存QUICK p61–63を処理し、独立点検も完了。会社転載図は営業利益639→874百万円・+235、業界別売上増減と原価/販管費の表示を保持し、segment利益合計やオリジナル品全体の利益寄与へ転用しない。前年同期は再編に合わせ遡及修正されたとの明示を確認。13棒の表示合計+234と矢印+235の差は原因不明、調整なし。p66の営業+19%/純利益-6%という会社計画と特別利益反動の説明は[既存引用](../research/ir-case-studies-2026-10-15/7525/pdf-size-followup/quotes.json)に処理済みなので重複成果を作らなかった。

この7525成果はstable宣言後に同名4filesを追記上書きした版管理ミスがある。旧完全bytecopyは未保存で再構成しない。[来歴](../research/ir-case-studies-2026-10-15/7525/quarter-profit-bridge-review/revision-provenance.json)と[最終版だけの独立点検](../research/ir-case-studies-2026-10-15/7525/quarter-profit-bridge-review/independent-recheck.md)、[親確認](../research/ir-case-studies-2026-10-15/7525/quarter-profit-bridge-review/parent-acceptance.json)へ限界を記録した。最終版は固定、金融入力/実DB/質問は変更0。

[台帳のheld既定値と保有確認の境界](../research/ir-catalog-position-boundary-review-2026-10-15/README.md)は2つの合成DBで欠陥を再現。窓口台帳に保有情報がなくてもfalse/observedとなり、他の数値入力が揃うとposition gateを解除する。status held省略・bootstrapも対象。修正前の完全bytecopyを保存し、明示status --held/専用APIだけが新観測と申告receiptを保存する最小修正を開始した。旧companyのboolはmetadata/queue互換として保持し、来歴不明の旧観測を新しい判断の確認済み状態へ移さない。対象80件・全1351件に加えて[独立レビュー](../research/ir-catalog-position-boundary-review-2026-10-15/independent-review.md)も完了し、固定コード一致・旧履歴/実DB主SHA不変を確認。実台帳への申告登録は0。[global policy登録と契約なしlegacy質問の境界](../research/ir-adopted-policy-question-boundary-review-2026-10-15/README.md)は既知の互換仕様と確認し、新P2所見0・追加gateなしで終了。[現在表示と保有確認の境界](../research/ir-current-position-view-boundary-review-2026-10-15/README.md)も既知仕様として新所見0で終了。 [7525著者論点のv2](../research/ir-case-studies-2026-10-15/7525/author-original-product-review/case-record-v2.md)は独立点検まで完了し、[v10更新](../research/ir-research-monitoring-integration-2026-10-15/actual-run-validation-v10.json)へ接続済み。会社新発表や独立原典の追加とは数えない。[明示申告の操作](position-declarations.md)を追補し、研究担当テンプレートには図の画像転記とstable後の版固定を追補した。

1379の年次CF確認は[既存の有限試行](../research/ir-case-studies-2026-10-15/1379/annual-cashflow-followup/README.md)が実施済みで、既知配信host保留・PDFリンク未確認のため再GET0で終了。原資料の不足は維持する。同記録のhref位置だけ[旧版保持の訂正v2](../research/ir-case-studies-2026-10-15/1379/annual-cashflow-followup/correction-v2.md)へ40666:40729と訂正し、原raw/保存text/snapshot本文の同一性を確認した。19タスクv3への実処理状態更新は完了し、有限確認済みの未解決点を未試行と取り違えないよう担当テンプレートへ接続した。

新たに[141Aの著者仮説v2](../research/ir-case-studies-2026-10-15/141A/author-hypothesis-review/README-v2.md)を保存Iwai NO335の物理4頁から抽出。西友統合/価格と既存店客数/中計/GO首都圏の4注視点はformal ANDにせず、2026/3/23の著者見解・会社中計・当時の実績を分けた。[v1独立点検](../research/ir-case-studies-2026-10-15/141A/author-hypothesis-review/independent-recheck.md)の時刻ラベル指摘は旧版を残すv2で訂正し、[独立追記](../research/ir-case-studies-2026-10-15/141A/author-hypothesis-review/independent-v2-addendum.md)で解消を確認した。実初回保存時刻はnull、HTTP本文完了時刻は別fieldである。[公式入口の有限確認](../research/ir-case-studies-2026-10-15/141A/initial-public-followup/README.md)はrobots404と決算入口200の2GETで終了、静的169anchorのPDF0/財務本文0。残1GET未使用、JS/API/別経路へ拡大せず未importの入口1sourceだけを保存し、[独立点検](../research/ir-case-studies-2026-10-15/141A/initial-public-followup/independent-recheck.md)を完了した。この141A確認時点では実DB98資料/公開14社/財務本文13社のままで、同社への金融採用・質問・監視登録は0。



[次作業の対応表](../research/ir-next-decision-workmap-2026-10-15/README.md)から135Aの保存B/S入力候補を具体化し、[現金2表示と株/借入のraw候補](../research/ir-case-studies-2026-10-15/135A/balance-sheet-input-candidates/README.md)を[独立点検](../research/ir-case-studies-2026-10-15/135A/balance-sheet-input-candidates/independent-recheck.md)まで完了。[W1の進捗](../research/ir-next-decision-workmap-2026-10-15/parent-progress.json)を別記し、旧workmapの時点を保持した。2現金表示は同残高で非加算、株数/借入dashは0化せず、全9評価入力は未採用。別途、[株数単位の最小追加](../research/ir-disclosed-share-unit-integration-2026-10-15/implementation.md)は関連41件・全1,380件・独立レビュー不備0で受入済。保存p2の発行済普通株数（自己株含む）1件を、新しい別fileで正規化し独立点検・索引v17接続まで完了した。自己株控除後/期中平均/希薄化後/現在評価分母へ採用せず、同機能のコード検証中は実DB101sourceを固定した。6323追加は後続の別処理である。

[6323の短信](../research/ir-case-studies-2026-10-15/6323/initial-public-statement-followup/README.md)と[説明資料](../research/ir-case-studies-2026-10-15/6323/quarter-presentation-followup/README.md)を保存・分類し、[著者3論点との比較](../research/ir-case-studies-2026-10-15/6323/author-condition-followup/case-record.md)・[追補](../research/ir-case-studies-2026-10-15/6323/author-condition-followup/presentation-addendum.md)を完了。[AP用途/製品例](../research/ir-case-studies-2026-10-15/6323/advanced-packaging-public-check/review.md)、供給対応方針、会社内の工場前倒し計画は公開既答。効果や利益bridgeは未確認。[一般Q定義](../research/ir-case-studies-2026-10-15/6323/factory-period-definition-check/review.md)は国内/海外で異なり、工場図への適用はunknown。旧calendar-year表現は[限定訂正の独立追補](../research/ir-case-studies-2026-10-15/6323/quarter-presentation-followup/addendum-factory-period-definition.md)で解消し、旧source/所見を保持した。予定を稼働済み、会社見通しを著者予測の成功、床面積を利益へ変換しない。過去の503や禁止hostの再試行は0。金融採用・IR草案・送信は0。

[未探索だった台帳1476社の著者経路](../research/ir-author-routing-remaining-catalog-2026-10-15/README.md)を保存証拠9063件から調べ、1723/1980/2134/2983/3023の5社5URLを固定。[親参照照合](../research/ir-author-routing-remaining-catalog-2026-10-15/parent-route-recheck.json)は旧343社を除く母集団、5snapshot/link/quoteの一致を確認した。残1476社は個人受付not_statedで拒否確認でも現送信適格確認でもない。既存12caseは再探索せず、47社は該当保存本文なしunknown。

[1723のEnvalith公開章](../research/ir-case-studies-2026-10-15/1723/author-public-chapters/README.md)と入口を保存し、[著者2条件](../research/ir-case-studies-2026-10-15/1723/author-conditions/case-record.md)を整理。[会社source3件](../research/ir-case-studies-2026-10-15/1723/actual-author-import/README.md)を実台帳へ保存・分類。プラットフォーム規約のnull会社IDは元file-onlyに残し、[会社subsetの独立追補](../research/ir-case-studies-2026-10-15/1723/author-public-chapters/addendum-company-source-subset.md)で構造の不適合を解消した。会社側は[未試行資料室の初回取得](../research/ir-case-studies-2026-10-15/1723/issuer-financial-index-missing-robots-followup/README.md)・[短信/説明カテゴリ](../research/ir-case-studies-2026-10-15/1723/issuer-first-quarter-followup/README.md)が200、静的PDF未特定で停止。robots再試行・JS/API探索0、同期間原本との比較は未完了。case末尾のfile-only表現は[root checkpoint](../research/ir-research-monitoring-integration-2026-10-15/1723-author-condition-review-checkpoint.json)で実DB保存時刻へ限定訂正した。

[2983のAstris掲載入口](../research/ir-case-studies-2026-10-15/2983/author-entry-followup/README.md)は既存8151の静的JSON parserを再利用し、[Oct1原本](../research/ir-case-studies-2026-10-15/2983/first-author-report/README.md)を取得。著者3期EPS・[販売棟数/粗利mix/販管費の3条件](../research/ir-case-studies-2026-10-15/2983/author-conditions/case-record.md)を会社転載と区別した。NI英語unit-keyの過剰な10billion表記は[訂正](../research/ir-case-studies-2026-10-15/2983/first-author-report/review-unit-label-correction.md)・[独立追補](../research/ir-case-studies-2026-10-15/2983/first-author-report/addendum-unit-label-correction.md)で10億円=1billionへ限定訂正、元数値/source/EPSは不変。[author原2source](../research/ir-case-studies-2026-10-15/2983/actual-author-import/README.md)を保存・分類した。次の[会社同期間3PDF経路](../research/ir-case-studies-2026-10-15/2983/saved-issuer-route-inventory/README.md)は別担当が4GET全200で取得し、6頁を確認中。実DB未保存で、会社304.27円・2:1split表示の作者EPSへの適用は未認定。

## 当日の作業ログ（各時点の記録）

以下は保存順の履歴であり、最新状態は上記を参照する。


[処理の図](decision-flow.md)に、著者条件の研究・質問前の固定・返信適用・価格条件点検の関係をまとめた。元の判断方針は参照hashを保ち、図は別ファイルとして保存した。

最新の[研究監視v7](../research/ir-research-monitoring-integration-2026-10-15/actual-report-v7.json)は6社33保存source。8151の[著者間比較](../research/ir-case-studies-2026-10-15/8151/cross-author-comparison/README.md)で、QUICKの会社NI由来EPSをAstris独自予測の改訂へ混ぜず、旧4条件との対応不明を維持した。7525の[追加索引](../research/ir-case-studies-2026-10-15/7525/issuer-presentation-followup/README.md)は静的資料欄が空で、最新比率は未取得。[数値索引v12](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v12.json)は14社67項目・15会社/出典エントリ、旧64項目を維持。QUICK新3表示値の親CLI再現/実DB原典一致を確認し、派生資料とモデルは未採用。研究担当の[依頼テンプレート](../.agents/skills/jp-equity-ir/references/roles.md)も数値仮説前の比較・次版inventory更新へ接続した。

最新の[研究監視v6](../research/ir-research-monitoring-integration-2026-10-15/actual-report-v6.json)は6社30保存source。新資料2件の実保存で7525が[確認待ちへ戻ること](../research/ir-research-monitoring-integration-2026-10-15/actual-new-source-trigger-validation.json)を確認後、[会社目標との比較](../research/ir-case-studies-2026-10-15/7525/issuer-plan-comparison/case-record.md)を反映した。9765も著者の定性仮説・会社転載・資料索引の限界を分けて追加。新しい金融条件は作成していない。Rix会社HTML2件と9765索引1件の[後続実保存](../research/ir-case-studies-2026-10-15/9765/issuer-financial-followup/actual-intake.json)でも、旧source/会社状態は不変。

[研究監視v5](../research/ir-research-monitoring-integration-2026-10-15/actual-report-v5.json)は135A・1518・1721・7525・8151の5社25保存source。追加した2社は逐語引用・独立点検を確認し、著者の数値条件は未設定のまま。実行前後のDBは不変で、Web確認や金融的な結論を意味しない。並行取得の新しい会社一次資料は、まだDBへ入れていない段階ではこのinventoryの外に残る。

[著者論点からIR質問前までの5社比較](../research/ir-author-to-question-readiness-2026-10-15/README.md)は公開解決・会社定義・著者許容幅・投資家評価を分離した。全モデルpathは未採用。[9765 SESSA](../research/ir-case-studies-2026-10-15/9765/pdf-redirect-followup/README.md)の告知/PDF2資料を独立点検後に[実保存](../research/ir-case-studies-2026-10-15/9765/pdf-redirect-followup/actual-intake.json)し、会社予想と定性上振れ見通し・市場PERを区別した。[収集保留5host](../research/ir-source-access-holds-2026-10-15/README.md)を技能とデータ取得手順へ接続し、同じ取得の再試行を防ぐ。

研究監視の[実入力v4](../research/ir-research-monitoring-integration-2026-10-15/actual-case-requests-v4.json)は135A・1518・1721の3社21保存source。1721の著者6論点と18引用を親が照合し、全論点を未解決のまま登録した。[出力](../research/ir-research-monitoring-integration-2026-10-15/actual-report-v4.json)は追加triggerなし、実行前後のDBは不変。金融的な結論やWeb更新の確認とは別である。7525の[オリジナル品構成比](../research/ir-case-studies-2026-10-15/7525/author-original-product-review/case-record.md)は著者注視・会社目標・集計定義を分離した。8151の[会社一次資料追補](../research/ir-case-studies-2026-10-15/8151/issuer-annual-followup/README.md)はrobotsのAI個別禁止を確認して1GETで停止し、短信・実績比較は未確認。再試行や別経路へ広げない。

最後の全件成功は[1,312件・35.209秒](../research/ir-research-monitoring-integration-2026-10-15/README.md)。研究点検reportの16テスト・独立合成10ケース・実2ケース18sourceの確認を含む。直前の[1,296件](../research/ir-oku-yen-normalization-2026-10-15/README.md)で億円換算と旧出力互換を検証済み。直前の[1,288件](../research/ir-external-estimate-extraction-2026-10-15/README.md)は履歴として保持する。実sourcesは**87（公開86＋市場1）**、classifications86、公開資料あり14社/財務本文あり13社、完了intake26、計測attempt23/events46/receipt23、source来歴はlegacy28/trusted59。[1721の会社予想HTMLと短信索引の取り込み](../research/ir-case-studies-2026-10-15/1721/initial-public-review/actual-intake.json)を参照。5月12日更新の予想が取得時点の最新かは未確認。1,819社は台帳上watch・held:falseのまま、金融仮説/質問/返信/実policy採用/送信/注文0。分類leaseの件数や経過時間を全工程の分析能力へ変換しない。

1417・145A・1721の初期確認は10GETで終了。1417/145Aは静的索引だけで財務本文0、1721は会社予想HTML1。1417/145Aの旧research source集合にはfull ingest schemaがなく、145Aの会社ID・取得開始/完了時刻にも差がある。原記録を残し、共通ID・canonical会社ID・応答完了時刻を使う別版 `canonical-source-bundle.json` と照合記録を保存、メモリ内ingestを確認した。実DBには両社を未登録。1417の旧IDは独自capture識別式で、共通IDとの差とID自体の誤りを区別する。[事実索引v9](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v9.json)は1721の実績6/会社計画6を追加し、10社49項目。1813は索引のみで2GET終了、1827/1833は[正式資料を確認](../research/ir-next-case-routing-round2-2026-10-15/README.md)し、[1827の2資料](../research/ir-case-studies-2026-10-15/1827/initial-public-review/actual-intake.json)と[1833の3資料](../research/ir-case-studies-2026-10-15/1833/initial-public-review/actual-intake.json)を取り込んだ。[索引v10](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v10.json)は各社のQ1EPS/通期会社EPS/年間DPSを追加し12社55項目。研究段階の点検reportを完成し、[入力v3](../research/ir-research-monitoring-integration-2026-10-15/actual-case-requests-v3.json)と[実行照合](../research/ir-research-monitoring-integration-2026-10-15/actual-run-validation.json)を保存。135Aの未比較10件は関連確認を終え、既存5件の数値/AND条件を変えず、両社とも新保存/未確認/管理日到来の追加triggerなし。著者レポートの[保存リンク10社12経路](../research/ir-author-report-routing-wide-2026-10-15/README.md)も保存した。3386は既知robots拒否でGET0、1827外部コメントはrobots403で未読、1721のShared Research本文確認と[6著者見解の監視整理](../research/ir-case-studies-2026-10-15/1721/author-conditions/case-record.md)も完了した。共有サイトは明示AI crawler制限を確認し追加取得を保留。[別著者経路](../research/ir-author-report-routing-other-authors-2026-10-15/README.md)の343社列挙では、既存4社を除く339社の保存証拠を検索し、331社に公式200本文、8社は本文なしunknown。[7525の96頁](../research/ir-case-studies-2026-10-15/7525/pdf-size-followup/README.md)と[8151の11頁](../research/ir-case-studies-2026-10-15/8151/external-report-review/README.md)を限定読取し、1721と合わせて5sourceを実取り込み。[索引v11](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v11.json)は14社64項目。QUICK算出EPS/株主資本コスト/平均とAstris2025時点の予測を現在の採用入力へ変えず、WACCは対象時点不足で構造化を見送った。次は7525の製品比率定義と8151の後続会社原典経路を確認する。

05:42 UTCの親照合時点はsources60/classifications60、legacy28/trusted32、市場source0（snapshot作成中）だった。05:43:42の[市場source取り込み](../research/ir-case-studies-2026-10-15/1379/provider-market-snapshot/actual-ingest.json)後は61sources/60classifications、intake13、attempt10/events20/receipt10、legacy28/trusted33。[05:44のread-only不足棚卸し](../research/ir-case-studies-2026-10-15/coverage-after-provider-market.json)の市場1社/財務本文6社というcoverageは今回も変わらず、再実行していない。価格は提供者申告の2,048円、quote時刻2026-10-14T06:30:00.000Zで、live/current価格や鮮度policy採用ではない。旧記録の件数や「未取得」は各保存時点の状態として残す。

[round2の3task](../research/ir-next-actions-2026-10-15/README.md)は会社別の限定適用記録として完了した。[1379 preview](../research/ir-case-studies-2026-10-15/1379/earnings-preview-candidate.md)は価格/需要、生産/販売、化成品、費用の4論点を反証・次回指標へ結んだ。[135A CF対応](../research/ir-case-studies-2026-10-15/135A/current-cashflow-to-forecast-basis.md)は30行を現在実績/各予測期/安定n+1期へ分け、税・利息・WC・設備支出の範囲不足を具体化した。[1379採用前提](../research/ir-case-studies-2026-10-15/1379/adoption-prerequisites.md)は会社予想の候補、将来予測、モデル適合、価格、実行policyの不足を別欄にした。[親照合](../research/ir-next-actions-2026-10-15/round2-parent-recheck.json)はCF58引用/30行とpreview13引用/4論点を確認しているが、金融的意味や予測の採用は認定していない。

[質問準備レビューv2](../research/ir-case-studies-2026-10-15/ir-question-readiness-review-v2.md)は台帳内7社と台帳外8331の公開解決/次の公開確認/条件付き定義を分け、全社の実採用pathはnull。[Shared Research探索](../research/ir-case-studies-2026-10-15/1379/external-report-discovery/README.md)で確認した通期数値は会社予想の再掲であり、独立数値予測へ採用していない。previewの条件記述やCFの行対応も数値予測や質問登録ではない。

[135Aの外部予測探索](../research/ir-case-studies-2026-10-15/135A/external-forecast-discovery/README.md)は3GET全200で終了し、親が[13外部引用＋4会社比較引用と原典hashを照合](../research/ir-case-studies-2026-10-15/135A/external-forecast-discovery/root-recheck.json)して取り込んだ。AENTRO自身の将来目安/条件付き推計3件を確認した。会社委託・報酬の開示と数値の作者は別軸で記録し、独立検証済みとはしない。拠点立上げ遅延**かつ**継続顧客比率45%近辺で頭打ち、という条件を遅延単独の反証へ変えない。No Rating/No Target Price、FY27 EPSは会社予想の再掲、過去PER50.2倍は将来採用倍率ではない。候補は研究ファイルであり、実予測のcommitment・評価器入力・金融仮説への採用は0のまま。

VRAINの[著者条件と最新公表KPIの照合v2](../research/ir-case-studies-2026-10-15/135A/author-condition-followup/case-record-v2.md) / [JSON](../research/ir-case-studies-2026-10-15/135A/author-condition-followup/case-record-v2.json)が完成した。受注基準の累計394社、継続顧客売上比率57.5%、年度内累計AI単価20百万円、中間営業利益率21.7%・Q2単独35.7%・通期会社予想30.1%、金沢7月1日営業開始を原表の期・概念へ対応させた。独立レビューで見つかった358社の「前期末」表記だけを「7月14日当時の現在、図のFY27 Q1」へ訂正し、Q&Aが明示しない正確な期末日を補わない。[原版](../research/ir-case-studies-2026-10-15/135A/author-condition-followup/case-record.md)は不変で保持し、親の[v2照合](../research/ir-case-studies-2026-10-15/135A/author-condition-followup/root-recheck-v2.json)は一field差以外の完全一致、引用・数値・期間・AND判定・再点検日の不変を確認した。57.5%から著者の45%近辺頭打ち条件全体は確認できず、正式IR質問は0。管理用再点検日2027-01-15は会社の決算予定・売却期限ではない。

[保存済み日本株レポートの評価例](../research/ir-author-valuation-example-2026-10-15/README.md)では、岩井コスモのローツェ6323に対する著者EPS予想と目標4,500円を画像確認し、親も[PDF1・2頁を再視認](../research/ir-author-valuation-example-2026-10-15/root-recheck.json)した。算式・採用EPS年度・目標倍率は未確認なので評価再現は行わない。目標値は日付付き参照値として保持し、市場PERの転用や逆算で著者の式を作らない。新GET/実DB追加0で、現在の投資選定や過去の前向き成績へ転用していない。[技能](../.agents/skills/jp-equity-ir/SKILL.md)と[判断方針](decision-policy.md)へ数値評価前の会社別研究と外部目標値の扱いを追記済み。当該点検そのものはコードを変えず、当時の全件1,253件チェックポイントを維持した。後続の株主価値調整では1,281件、外部予測区分追加後の最新結果は冒頭の1,288件である。

[予測データ調達の有限調査](../research/ir-forecast-data-sourcing-2026-10-15/README.md)は6GET全200で完了し、親も[6raw/text/snapshot・4HTML再抽出・20公式引用＋6既存引用を照合](../research/ir-forecast-data-sourcing-2026-10-15/root-recheck.json)した。IFISの日次bulkはアナリスト個別予想・コンセンサス・会社予想を分ける具体候補で、個別予想等には証券会社の許可が必要。QUICK APIは確認したが、そのAPIからの業績予測供給は未確認。銘柄coverage、対象FY、作者/改訂時点、料金、個人利用、クラウド/AI利用等は未確認で、契約・データ受領・API実装・実DB追加・モデル採用はない。

[135Aの価格確認](../research/ir-case-studies-2026-10-15/135A/public-price-discovery/README.md)は公式の明示リンクから3GET全200で終了した。表示4,195/14:42は読めたが、価格に対応する通貨と完全な観測日時は確認できず、他指標の日時を転用せずmarket source候補・実DB追加を見送った。追加取得や別経路探索は続けない。

[保有期間と検証材料の照合](../research/ir-case-studies-2026-10-15/135A/horizon-and-catalyst-review.md)では、最終業績の対象期、期間内の途中証拠、価格差修正、利用者の保有期間を分けた。FY29最終成果が窓外でも長期CFを現在価値へ使えないという意味ではない。FAQの約1年は初売上まで、約3カ月は受注から納品までで、加算しない。親も6原典・15引用・旧10artifact不変を[照合](../research/ir-case-studies-2026-10-15/135A/horizon-and-catalyst-root-recheck.json)した。

[価格期待の原典確認](../research/ir-market-expectations-2026-10-15/README.md)はGET0で完了し、親も8source・16引用・旧14inputを[照合](../research/ir-market-expectations-2026-10-15/root-recheck.json)した。DamodaranのExxon例で確認したのは、他の仮定・driverの関係に依存する条件付き整合値。真の市場予想や確率、価格差修正時刻の同定ではない。会社指標、外部著者の条件、投資家側の前提を分ける手順を技能・判断方針へ反映し、reverseDCF演算器は追加していない。

[Toyota原典の9入力点検](../research/ir-toyota-author-valuation-readiness-2026-10-15/readiness.md)と[独立原典レビュー](../research/ir-toyota-author-valuation-readiness-2026-10-15/independent-review.json)を完了し、[株主価値調整を分ける別method](explicit-equity-bridge-spec.md)を追加した。3期FCFFと明示4年目、現金・非営業資産・負債・少数持分を独立入力で扱い、旧方式・旧質問は再解釈しない。[親の独立Fraction照合](../research/ir-equity-bridge-integration-2026-10-15/independent-recheck.json)でも表示入力から3,944.09円、著者表示3,943円との差は終価から残る。1,281全件成功、追加28件で出典監査・事前IR変更範囲・CLIを確認。n=0/年別率は範囲外、簿価や他請求権は適合認定していない。実DBはread-onlyで64資料/金融仮説・質問0を確認した。

**1518の取得・取り込み・既存著者論点への比較と予想改訂の構造化を完了した。1417/145A/1721の初期確認を終え、1813/1827/1833の初期確認も終え、研究管理日のread-only点検と著者レポート経路を確認している。** 会社IRで確認できる定義、外部著者にしか分からない条件、投資家側の評価前提を分け、原典と現行CLIから次の有限作業を選ぶ。現企業の予測・投資先選定へ歴史的算術を転用せず、同義previewや汎用機能で不足を埋めない。

独立点検では、実装上の最初の不足は135Aの採用済み数値thesisであり、確率を足して解けるものではなかった。AENTROの監視条件は既に研究できるが、売買/利確規則や評価式は示されていない。既存`customer-counting-unit`論点を[保存15本文で確認](../research/ir-case-studies-2026-10-15/135A/customer-counting-definition-review.md)し、受注基準は既答、法人/工場等の集計単位は未確認とした。[親照合](../research/ir-case-studies-2026-10-15/135A/customer-counting-definition-root-recheck.json)は11引用・5原典・実DB原文一致と45/48頁画像を確認。[初回草案v2](../research/ir-case-studies-2026-10-15/135A/customer-counting-question-preflight-v2.md)は単位と変更有無へ絞り、重なっていた旧A/Bを単位種類と期間一貫性の別軸へ整理した。会社系列内の単位と著者550–600社目安の対応を分け、回答からEPS・倍率・actionへ飛ばさない。CLIは数値path変更のない質問を禁止していないが、保存thesis版は必要で、登録用の数値を作らない。[流れ](ir-decision-flow.md)へ研究段階の分岐を明記した。[私的面談の学術調査](../research/ir-direct-contact-evidence-2026-10-15/README.md)は3GETで終了し、正式書誌とpreprintの寄託要約まで確認。出版社robotsのAI向け拒否を尊重して本文取得を止め、別経路へ進まない。[親](../research/ir-direct-contact-evidence-2026-10-15/root-recheck.json)も3capture/5引用/2書誌path/旧2文書不変を確認した。本文の推定方法・効果量や日本のメール/フォームIRの有効性は未確認で、尤度・売買規則へ採用していない。

[5988の費用/CF対応](../research/ir-case-studies-2026-10-15/5988/cashflow-oneoff-bridge-review.md)は有限完了。連結特損423が税前利益へ入りCFで正調整されること、東莞337/英国86の表示内訳、印度戻入59/CF△59を別区分で確認した。約6億円のcash/包含/期間は未解決で、既存草案を増やさない。[親照合](../research/ir-case-studies-2026-10-15/5988/cashflow-oneoff-bridge-root-recheck.json)は9原典/実DB一致、著者2PDF/本文、24頁内引用、旧50files不変と69/79頁画像を確認。CFOや営業利益へ再加算せず、続く[アジア予想と中国費用の対応点検](../research/ir-case-studies-2026-10-15/5988/asia-forecast-china-cost-link-review.md)では、予想図の+6.3億円は海外自動車内、旧中国約6億との明示対応は未立証と確定した。最新Q1所在地表との事業範囲/地域/消去/FX・期間対応も未確認で同一系列としない。[親](../research/ir-case-studies-2026-10-15/5988/asia-forecast-china-cost-link-root-recheck.json)は4原典/11引用/旧19files不変と図9画像を確認。新規同義草案を作らずこの点検を終了した。[1332の長期買掛金点検](../research/ir-case-studies-2026-10-15/1332/longterm-trade-payables-review/README.md)も有限完了。補足9頁は南米養殖会社取得による返済を運転資本説明欄に置き、長期借入金行とは別。個別額/契約条件/正式CF分類/モデル上の負債解釈は未解決。正式年次資料の索引を取得したが、配信先robotsの禁止に従い2GETで停止しPDF本文0。[親](../research/ir-case-studies-2026-10-15/1332/longterm-trade-payables-review/root-recheck.json)は7原典/実DB一致、10引用、2経路captureと実CRLF26bytesのguard、補足9頁画像を確認。経路だけの資料は実DBへ追加せず、今回の禁止規則を旧取得時へ後付けしない。

[公表評価レポートの発見](../research/ir-public-valuation-report-discovery-2026-10-15/README.md)は保存公式20ページで終了し、HTTP0で1518/1444の次読取リンクを確認した。[親照合](../research/ir-public-valuation-report-discovery-2026-10-15/root-recheck.json)はsnapshot/text20組、リンクpath2件、窓口CSV1,819行を確認。9702のAlpha-Win告知は唯一実名一致だが窓口provisional・台帳外で、投資対象へ昇格しない。続く[1518 FISCO本文](../research/ir-public-valuation-report-discovery-2026-10-15/1518-fisco/README.md)は2GETで20頁を取得、会社計画の再掲と著者の定性見解を分けた。独自EPS/評価倍率/式は未確認で逆算しない。[親](../research/ir-public-valuation-report-discovery-2026-10-15/1518-fisco/root-recheck.json)も11頁内引用/原典SHA/旧5filesと予想表16頁画像を確認。[9702 Alpha-Win本文](../research/ir-public-valuation-report-discovery-2026-10-15/9702-alpha-win/README.md)は4GETで取得し限定点検を完了した。著者自身の新Eは2026/12期EPS161.17、2027/12期181.21、2028/12期196.02円/株。会社CE161.40と区別し、2021年1月の株式分割遡及注記を保持する。掲載PER15.4/13.7/12.7は8月21日株価2,480円を固定した記述で、採用目標倍率・公正値式は未確認。[親照合](../research/ir-public-valuation-report-discovery-2026-10-15/9702-alpha-win/root-recheck.json)は4raw/capture、19頁再抽出、19頁内引用、旧3filesと16/18頁画像を確認した。本文表示8月24日・会社告知9月2日・PDF作成8月30日等を保ち、正確な初回公表/改訂履歴は推定しない。9702は窓口確認済み台帳外のまま、両レポートとも実DB/金融モデルへ未採用。

[外部予測の抽出](../research/ir-external-estimate-extraction-2026-10-15/README.md)は、受理kindとエラー文の2行を変更し、新field/新version/評価前提を追加していない。全1,288件成功、旧3kindは変更前のbundle全体SHAとIDが一致。[9702の実抽出](../research/ir-external-estimate-extraction-2026-10-15/9702/README.md)は新E3件と会社CE1件を別factへ保存し、親もCLIから同じ派生ID/内容を確認した。作者と抽出担当、株式基準、公表日不整合を保持し、金融採用/実DB追加0。

[IIJのCAPEX/現金CF対応](../research/ir-case-studies-2026-10-15/3774/capex-cashflow-bridge-review/README.md)を保存資料で点検した。Q1のIFRS連結CFは実在し、管理現金6,278/リース取得1,349と、CFの有形/無形取得支出・助成金入金・その他金融負債支払を別概念で保持した。前年度単体P/L助成金2,157とQ1連結CF2,157を同額で対応させない。完全bridgeは未立証、既存closed/no-sendを維持。[親](../research/ir-case-studies-2026-10-15/3774/capex-cashflow-bridge-review/root-recheck.json)は3原典/実DB本文一致、22頁内引用、旧18files不変、2画像を確認した。

[研究段階の継続監視](research-stage-monitoring.md)は、通常dailyのactive/数値thesis要件では研究ファイルの管理日を拾わないことを明記し、担当workerが新しい保存資料と既存管理日を別枠で点検する手順へ反映した。[135Aの限定実確認](../research/ir-research-monitoring-2026-10-15/135A-manual-check.json)は同社保存15資料すべて初回保存既知、前回研究後の保存0、管理日未到来。Web更新の有無や全社点検を主張せず、当時は自動スケジューラ/新APIを作っていなかった。後続のread-only reportは冒頭を参照。実DBを07:47 UTCにread-onlyで64資料/金融仮説・質問・返信0と再確認、前後hash不変。

[1518の著者条件](../research/ir-case-studies-2026-10-15/1518/author-conditions/README.md)は既存事業と投資収益の寄与を追う1論点に限定し、作者の定性見解・会社計画の転載・次の公開観測を分けた。保存公式リンクを[5件照合](../research/ir-case-studies-2026-10-15/1518/issuer-source-routes/root-recheck.json)し、[会社の3PDF](../research/ir-case-studies-2026-10-15/1518/issuer-quarter-followup/README.md)をrobots込み4GET全200で取得。7/22の会社予想改訂と8/7の修正版維持、Q1投資益の営業外/特別利益区分、CF未作成、2025年1:5splitとBBT/平均株数、山洋の当時予定/予想範囲を保持した。親も3再抽出・20引用・旧11files不変を確認し、08:03 UTCに実DBへ3本文を追加・intake完了。既存source64件と会社状態は不変。現providerは既存byte verifier未対応のためunknown3で、成功と扱わず別途原バイト/本文を照合した。

[1518の既存著者論点との比較](../research/ir-case-studies-2026-10-15/1518/author-condition-followup/case-record.md)を完了し、同じ1論点・3観測部へQ1実績/会社予想改訂を対応付けた。親は4原典/18頁・file内引用/旧54filesを確認し、会社3本文の実DB一致と67資料不変を再確認。投資益の存在と将来重要性、旧通期436/744とQ1 472/1,553、会社計画と作者の見方を分け、公開解決6項目を再質問しない。[山洋の完了確認経路](../research/ir-case-studies-2026-10-15/1518/acquisition-completion-routes/README.md)は保存4pagesに旧7/22告知1件だけで、後日の完了は未確認。追加GETせず閉じた。

[旧/新会社予想4facts](../research/ir-case-studies-2026-10-15/1518/guidance-revision-facts/README.md)は、EPS185.40/229.67と年間DPS74/130を同FYの別版として保存し、親のCLIでも同じ派生ID/本文を確認した。DPSの元表記は00銭付きで、人の限定意味確認と円tokenの機械確認を分ける。[索引v8](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v8.json)は旧29件を変えず1518と台帳外9702の計8件を追加し9社37件。モデルへの採用は0。[1518の別枠監視実施](../research/ir-research-monitoring-2026-10-15/1518-manual-review.json)と[親の管理日](../research/ir-case-studies-2026-10-15/1518/author-condition-followup/review-cadence.json)も保存し、新資料又は2027-01-15の四半期点検へ戻す。会社予定/売却期限/自動schedulerではない。

追加の[架空返信適用](../research/ir-equity-bridge-integration-2026-10-15/synthetic-workflow-result.json)は、非営業資産だけ10→20、少数持分/他入力/旧版/原文不変、仮説v2と固定policy/新価格を参照する判断reviewの保存まで完了した。実DBは使わず、全件テストの理由のない再実行もしていない。

ホクトの[正式通期資料の追補](../research/ir-case-studies-2026-10-15/1379/annual-cashflow-followup/README.md)は一覧script/robotsの2GETで終了し、禁止規則に従いfeed/PDFへHTTP未実行、金融本文取得・実DB追加0。再試行や別経路へ進まない。

[確率不要の判断範囲点検](../research/ir-decision-scope-2026-10-15/README.md)は完了し、親も[24引用/9合成対照を再確認](../research/ir-decision-scope-2026-10-15/root-recheck.json)した。確率を全研究の前提とする原著要件は確認されず、既存previewの支持/反証候補/未解決の記録を使う。完全な数値thesis・6方針等を求める現API契約と区別し、買い条件を弱めない。価格が得られても予測・倍率/率・費用/リスク/鮮度・質問前分岐の不足は残る。均等確率や独自閾値で埋めず、コード増強を既定の次作業にしない。

## 過去のチェックポイントと作業メモ

以下は各保存時点の履歴である。「作業中」「未実装」「現在」の記述や旧件数を最新状態へ書き換えず保持する。現在の進行状況は上の最新状態とround2索引を参照する。

## 保存したチェックポイント

[方針と判断の統合](../research/ir-policy-integration-2026-10-15/README.md)に全789テスト成功、架空デモ、実台帳の不足資料を保存。前回651件は以前のチェックポイントの結果として保持する。前回の09時までの実行が未達である記録は修正しない。

- 方針版の不変保存、質問前の固定、返信後の価格条件付き判断履歴、後日価格のみの再判定。
- 保有状態の実観測履歴と未知時点の保留、synthetic明示仮定の分離。
- 公開性の訂正履歴、依存判断の現在表示を保留、未参照の訂正版番号の検出。
- J-Quants原文由来の価格、日付精度の明示、原典closure検証。
- BaioらのEVSI定義に従う有限状態計算と、未校正尤度の保持。
- 出典結合の選別、窓口CSVの取り込み、全社不足資料のread-only棚卸し。
- 原典調査: Damodaranモデル適合3類型を研究用に採用。近似的なTOPIX相対レーティングを絶対利確条件に変換しない。
- 実台帳: data/ir-research-2026-10-15.sqlite3 に1,819社watch、公開資料20件（3774/5988）、仮説0・実送信0。

## 追加したチェックポイント

[初期処理・観測・訂正再調査](../research/ir-operation-integration-2026-10-15/README.md)に全844テスト成功（35.722秒）と資料分類結果を保存。観測台帳CLI、訂正dailyjob、数値仮説が不要なintake、能力レポートまで接続済み。

実DBの2社20資料は分類済み、intake jobs 2件完了。13資料に財務の内容があるが金融入力は未検証。会社は全1819 watch/held false、仮説0・送信0。2社モデル事実確認は各6確認・18不明、強制分類はしない。

DDM追加後は全858テスト成功（33.969秒）。原典p15の2種類の株主資本コスト、明示翌期DPSの式を実装。IR分岐と保存判断の4統合テストを含む。規制資本FCFEの計算器/終価は未実装。[仕様](financial-equity-valuation-spec.md)。

[数値出典・未設定確率の統合](../research/ir-model-input-integration-2026-10-15/README.md)では全911テスト成功（33.617秒）。公表数値の構造化、全数値pathの由来点検、全原典の追跡、未設定確率を補わない評価と保有点検、埋め込みJSONの厳密読取を検証した。観測分類訂正の実装前のチェックポイントである。

[観測訂正・公表値再現の統合](../research/ir-observation-corrections-2026-10-15/README.md)では全946テスト成功（33.612秒）。初回945件中1失敗のログも保持。原因はDecimal SignalDictとdictのテスト比較表現で、既存エラーflags保持の回帰を追加して修正した。計算器の値は変更していない。観測訂正、原文と換算の再現確認、Brier/log lossの純粋計算器を統合済み。

[候補予測の保存と循環企業資料](../research/ir-prediction-storage-2026-10-15/README.md)では全963テスト成功（33.815秒）。保存境界の後追加テストを含む対象18件も成功との担当報告あり（全件件数の更新ではない）。predictions CLIと不変モデルcommitmentを接続。5480の8資料を実DBへ取り込み分類し、実台帳は3社28資料・28分類・完了intake3件。1,819社watch、仮説/質問/実予測/送信/注文0件。

[準備状況と根拠照合の監査](../research/ir-readiness-audit-2026-10-15/README.md)では全976テスト成功（35.819秒）。架空原典を実観測へ混ぜる不備と、古い申告時刻で実保存時点の公開性保留を回避できる不備の2件を修正し、別担当が元の再現を再確認した。既存retryと旧履歴は保持する。binding後に新たに発生した保留の自動再照合は未実装。

[リース世代の照合](../research/ir-job-fencing-2026-10-15/README.md)では全983テスト成功（33.526秒）。同名workerの再確保後に旧処理を拒否する。CLIのrenew/completeはclaimで受け取った `--expected-attempt` を必須にした。実DBはこの修正で変更していない。

[実行計測の接続](../research/ir-attempt-integration-2026-10-15/README.md)では全1033テスト成功（33.573秒）。leaseの不変台帳、原子的な本体接続、read-only投影を実装した。実DBに台帳2tableを追加し、旧3ジョブは未計測のまま。source JSON群の前後hash一致を確認。active/tokens/費用は未計測、receiptは未実装。

[保存来歴とPITの接続](../research/ir-availability-integration-2026-10-15/README.md)では全1056テスト成功（34.052秒）。後着返信による過去仮説/daily packetの混入を修正し、別担当も元の再現を再確認した。source/thesis/reply/questionの初回保存を元JSONと別台帳へ記録し、旧28sourceには今回のknown-by観測のみを追加した。全28件のfirst_savedはnull、raw JSON群の前後hash一致。現在表示、strict PIT、明示read-only retrospectiveを分離した。

[現在表示の価格期限](../research/ir-current-price-integration-2026-10-15/README.md)では全1069テスト成功（33.098秒）。古い評価日時を指定して期限切れquoteを現在actionへ流せる不備を修正した。情報保留と価格保留を併記し、保存履歴・ID・元JSONは不変。初回1069件中2失敗は過去価格へhost現在時刻を使ったfixtureで、明示した架空runtime時計へ修正。既存の財務値・閾値・売買assertは維持、元失敗ログも保持する。

[現在表示の仮説版整合](../research/ir-thesis-version-integration-2026-10-15/README.md)では全1077テスト成功（34.187秒）。価格freshでも旧版の判断が現在候補に残るP2を修正し、別担当が元の再現を再確認した。raw版の不一致/不明をrequires_thesis_reviewへ回し、情報>版>価格の優先と全保留の併記、履歴・旧分岐・DB原文の不変を維持する。

[要求ID付き再送の接続](../research/ir-job-requests-integration-2026-10-15/README.md)では全1111テスト成功（36.360秒）。AWS/Google原典を採用し、任意のnamespace+IDでclaim/renewの再送を識別する。元応答と現在lease、null pollと新pollを分離。別担当も同ID再送のDB不変を再確認した。実DBには空receipt tableのみ追加し、source原JSONと28件のlegacy来歴は不変。

[原文照合の接続](../research/ir-evidence-binding-integration-2026-10-15/README.md)では全1129テスト成功（35.447秒）。全親・SHA/引用・来歴・歴史/現在公開性を照合するが、state意味/独立性・訓練・校正はunknown、scoreはnull。別担当も第二親・循環・legacy・後日保留・DB不変を再確認し、実台帳の観測/予測0件でのread-only実行もDB byte SHA不変だった。

[評価手順の不変記録](../research/ir-evaluation-protocol-integration-2026-10-15/README.md)では全1154テスト成功（35.163秒）。record-only registryとCLI/statusを接続し、別担当も再送・競合・rollback・late記録の非昇格・他table不変を再確認。実DBには空tableだけを追加、全旧table行は不変、実protocol0件。

## 当時の作業中メモ（履歴・最新状態ではない）

1. 最後の全件成功は1154件（35.163秒）。policy_documentation担当は[循環利益率の原典仕様](cyclical-normalization-spec.md)に基づき、新cyclical_margin.py/newtestsを実装中。親CLI cycle-margin FILEと架空2年例は接続し、CLI対象2件成功。著者Toyota表12行の平均再現を確認し、full-cycle/意味/再投資/financingの採用はunresolved固定。ROC/DCF/目標価格へつなげない。
2. information_value担当のread-only scripts/verify_case_source_bundle.py＋newtestsは完成、9合成testと1332/135A計12資料の照合成功。raw/text/snapshot/bytecountをCRLF保持で比べ、意味/財務/真正性は認定しない。次の全件は循環計算器が安定してから合わせて実行する。
3. 1332初期5資料と追加短信/カレンダー2資料は分類完了。親が引用見出しだけの2件を見つけ、旧artifact保存後に本文を含む引用へ訂正・12引用再確認済み。正式1Qは日本基準連結2026-04〜06、CF計算書未作成、次回2Q発表11/6予定を確認。正規化4事実は親もPDF画像・再現・実DB原典一致を確認した。
4. 135A VRAIN Solutionの5資料を親も照合し分類完了。財務本文・最新期は未取得のまま。adoption_research担当が別の限定followup最大3GETで、公式IR loaderの明示先だけを確認中。JSは実行せず、JSONP callbackにcaller生成名ir_agent_reviewを使うtransport上の処理のみ許可。企業ID/doctype/日付/endpointの不明値は推測しない、エラー再試行・接続診断なし。
5. 現在の実台帳: 1,819社watch/非保有、公開source41/分類41（1332/135A/3774/5480/5988）、legacy存在観測28＋trusted_insert13、完了intake7（旧3未計測/新4leaseのみ）、attempt4/events8/要求receipt4。仮説/質問/実予測/実protocol/送信/注文0件。金融内容を確認した会社は4社で、135Aは事業/索引/予定目安のみ。source取得や分類を全工程分析能力へ変換しない。

[予測の保存](probability-prediction-storage.md)は実装済み。既存観測の版とhash、全state×signal確率、model/training manifestを不変保存するが、candidate_prediction_only、training/calibration未検証を維持する。実観測採点・学習・EVSIへの採用は未接続。

5480の[循環モデルの例](../research/ir-case-studies-2026-10-15/5480/README.md)は8URL各1GETで完了。用途別需要・固定費の説明はあるが、最新決算/在庫評価/全サイクル/正常再投資/資金調達は欠損。原データを照合して実DBへ8資料を追加、仮説や投資選定はしていない。

IIJ・パイオラックス・千葉銀行の旧9項目と5480追加後の旧10項目索引を保持。[索引v3](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v3.json)は1332の4事実を追加し5社14項目。親も原PDF1/7頁の画像で表列を確認し、保存bundle再現と実DB原典との一致を確認した。派生数値資料は実DB未登録、モデル予測の採用なし。観測訂正は既存appendで利用できるが、予測時点やstate判明後の再分類を独立に点検する採点接続は未実装。

千葉銀行8331は8URLの公開調査と配当3項目の構造化まで完了。年間64.0円、中間32.0円、連結配当性向0.411を引用・期間ラベル付きで保存した。会社年度予想を将来DPSへ採用せず、評価額・仮説は作成していない。構造化bundleは研究ファイルだけで、実DBへ未登録。窓口未確認なので既存1819窓口台帳にも追加しない。[実行記録](../research/ir-case-studies-2026-10-15/8331/extraction-notes.md)。

## 当時の次タスク（履歴・最新の実行予定ではない）

- 金融モデルの追加を著者式・独立算術例で検証し、元のFCFFと混同しない。
- 計測APIへ本物の全工程の実測を渡す。架空デモや分類保存だけの時間を金融分析能力にしない。
- 実企業の最新資料と、著者モデルに必要な事実/不足を区別して記録する。3社28資料の初期分類は完了し、最新性・意味・予測入力の確認は継続する。
- 方針・質問・回答・現在価格・判断変更を前向きに記録する評価方法。
- 永続化・起動基盤・モデル予算・情報更新・失敗時の再開方法。

各作業は観測できる成果と必要な検証で区切る。同じテストや取得を理由なく繰り返して稼働時間を埋めない。取得障害を全体の作業停止や無限再試行の理由にしない。外部の承認・認証が必要な部分を分離して、独立に進められる作業を継続する。

## 循環利益率の中間計算と最新資料（04:52 UTC時点）

[統合記録](../research/ir-cyclical-margin-integration-2026-10-15/README.md)に全1,186テスト成功（36.325秒）と独立再計算を保存した。Damodaranの等重み年間営業利益率×指定売上高を `cycle-margin` として接続。全サイクル・比較可能性・正常再投資・金融入力採用は未検証で、評価額へ自動接続しない。既知2capture形式のオフラインraw/text/snapshot照合も追加し、unknown/emptyは成功trueにしない。

135Aの公式ライブラリから最新中間短信を取得し、親が3raw/text/snapshot、PDF再抽出、11本文引用、8設定引用、JSONP wrapperを独立照合した。[実intake記録](../research/ir-case-studies-2026-10-15/135A/library-followup/actual-intake.json)により実DBは44sources/44classifications、完了intake8件。新5件は実計測の分類lease（events10/receipts5）、旧3件は未計測。1,819社watch、held false、仮説/質問/返信/予測/送信/注文0。新規取得は初回保存を持つ16source、旧28sourceはlegacyのまま。

135Aは日本基準・非連結、中間実績2026-03-01〜08-31と通期会社予想2026-03-01〜2027-02-28を分離。公開資料で分かる期間・CF・予想変更有無はIR質問にしない。説明資料/Q&Aの有限確認と公表事実の構造化を続け、正常利益・将来予測・株価条件を独自に設定しない。

[公表事実索引v4](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v4.json)は135Aの5項目追加により6社19項目。親も原PDF1頁の表列を画像確認し、基本EPS26.06円と潜在株式調整後25.94円、半期/通期、実績/会社予想、配当の明示0を区別した。派生sourceは実DBへ未登録。最新の[read-only不足棚卸し](../research/ir-case-studies-2026-10-15/coverage-after-vrain.json)は財務本文あり5社、価格・仮説・会社方針採用は各0。旧36source時点の棚卸しも保持する。

## 公開定義とモデル入力の対応（2026-10-15T05:00:15.795852+00:00）

135Aの[説明追補](../research/ir-case-studies-2026-10-15/135A/presentation-followup/README.md)は4GET全200で終了。親が4raw/text/snapshot・2PDF再抽出・HTML再抽出・12本文引用・8ローダー設定引用・JSONPを独立照合し実intake完了。実DBは48sources/48classifications、完了intake9件、実測分類attempt6/events12/receipts6。旧28sourceのlegacy来歴と既存会社状態は維持。仮説/質問/返信/予測/送信/注文は0。

[公表事実索引v5](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v5.json)は6社23項目。135Aの中間CFO223百万円・D&A30百万円・有形固定資産取得支出△100百万円・売上債権および契約資産CF調整154百万円の4項目を別派生として追加し、親も原PDF8頁の表を確認。追加factはper-fact artifact/source_idを持つ。派生は全て実DB未登録。

[135Aの入力対応](../research/ir-case-studies-2026-10-15/135A/model-input-mapping.md)は9公表値と既存モデルkeyの候補を区別し、assigned pathは全null。90%以上指標と継続顧客売上式を分離し、IR質問の未解決点が採用モデルを変える経路はまだ立証されていない。[4社の質問準備レビュー](../research/ir-case-studies-2026-10-15/ir-question-readiness-review.md)には公開解決/次の公開確認/条件付きIRの余地を保存した。

[正常再投資の仕様](cyclical-reinvestment-spec.md)を著者原典から設計。stable-reinvestmentの純計算とCLIを接続し、library21/CLI2成功。全件テスト・独立算術確認は進行中で、現時点の完了チェックポイントは1,186件のまま。[材料監視の設計](catalyst-monitor-design.md)は予定/実施/結果到着を分ける案で未実装。ニッスイの予定fixtureと5480の年間入力資料を次に確認している。

[安定期再投資の統合記録](../research/ir-stable-reinvestment-integration-2026-10-15/README.md)に全1,209テスト成功（34.480秒）・library21/CLI2・独立Fraction照合を保存した。NOPATへtax/growth再適用なし、g>ROCの負FCFFを保持、g0scope/ROC0未定義を区別。機能による実DB変更なし。合成例と2009Exxon著者表示例だけで、現企業予測・金融適合・評価額・投資条件を採用していない。

[予定監視の統合](../research/ir-catalyst-schedule-integration-2026-10-15/README.md)は全1,230テスト成功（35.163秒）、library17/CLI4と独立確認済み。ニッスイ3件を保持し11月内2/外1、due全null・実施未確認。source全親/当時と現在の分類/来歴を読むだけで、予定の実施判定・変更採用・差分・自動jobは未実装。実DB/SHA不変を確認した。

1375初期4sourceを親がraw/text/snapshot/10引用・HTML再抽出で照合し実intake完了。実DB52sources/52classifications、6社にsource/財務本文5社、完了intake10、実測分類attempt7/events14/receipts7。1819社watch・held false、仮説/質問/返信/予測/送信/注文0。新1375 capture形式は既存2形式verifierとは別なので親の明示的照合を保存し、対応済みと主張しない。5480追加取得は[設定2成功/feed503](../research/ir-case-studies-2026-10-15/5480/annual-input-followup/README.md)で終了し実DB未import。[事実索引v6](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v6.json)は5480年間売上の別派生追加で6社24項目。同じ元株主メッセージからの売上/OIであり、独立した正式短信の裏付けではない。

[明示終価FCFFの統合](../research/ir-explicit-terminal-integration-2026-10-15/README.md)は全1,253テスト成功（36.735秒）、valuation17/統合6・独立Fraction照合・メモリ内架空workflow成功。別method dcf_explicit_terminalで旧DCF未消費fieldの意味を変えず、n+1分子を二重成長せずn期割引、canonical出典監査/IR許可pathと接続した。割引率は予測/安定で単一r、意味/予測/実企業採用は未検証。

1379の正式1Q短信11頁/説明35頁/IRindex2/予定表の5sourceを親が5raw/text/snapshot・PDF2再抽出/HTML3再抽出・15引用で照合し実intake。実DB57sources/57classifications、7社にsource/財務本文6社、完了intake11、実測分類attempt8/events16/receipts8、旧28legacy+新29trusted。全1819watch・held false、仮説/質問/返信/予測/送信/注文0。1375追加は[公開feed503で保留](../research/ir-case-studies-2026-10-15/1375/statement-followup/README.md)を確定し、新しいphaseや再試行はしない。

[1332 CFの限定意味レビュー](../research/ir-case-studies-2026-10-15/1332/cashflow-scope-review/README.md)は公開解決8問/未解決bridge5。親が3原典/hash/14引用の位置と実DB原文一致を再確認。長期買掛金返済と長期借入金を分け、D&Aののれん包含差は公開解決、未一致金額を推計で補完せずFCFFへ転用しない。

[公表事実索引v7](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v7.json)は7社29項目。1379の基本EPS14.44/通期会社予想167.22、Q1営業利益418百万円/通期予想7260百万円、年間配当予想62円を追加。親もPDF1頁画像で希薄化後12.37/中間EPS予想△3.00/期末配当52と区別し、normalize replay/reproduce・実DB原文との完全一致を確認。派生source未登録。日付のみ予定表の期見出しは不整合のため自動訂正せず、説明資料の存在を説明会実施と扱わない。[coverage-after-hokto](../research/ir-case-studies-2026-10-15/coverage-after-hokto.json)は財務本文6社/市場・仮説・会社別方針採用0社。

[追加6社の著者仮説v2](../research/ir-iwai-business-hypotheses-2026-10-15/README-v2.md)を保存し、[独立訂正確認](../research/ir-iwai-business-hypotheses-2026-10-15/independent-v2-addendum.md)まで完了。141Aと合わせIwai NO335の7社を事業論点へ展開したが、数値評価条件は増やしていない。[親の実DB照合](../research/ir-iwai-business-hypotheses-2026-10-15/issuer-route-inventory/parent-target-membership.json)では残6社中5社が現1,819社DB内、8725は台帳調査表に行があるだけの窓口未確認・DB外研究例。[2社のモデル点検](../research/ir-iwai-business-hypotheses-2026-10-15/model-route-review/README.md)は第三者情報による暫定で、会社原開示未確認を保持する。[モデル案内の現状訂正](../research/ir-model-routing-documentation-followup-2026-10-15/README.md)は前後の全文を保持し、DDM実装済みと規制資本FCFE未実装を区別した。

[6754公開2資料の実取り込み](../research/ir-case-studies-2026-10-15/6754/actual-public-import/README.md)は14:22 UTCに分類完了。旧98source/97分類/全会社metadata不変、保有申告tableの実行確認で実申告0。claim戻り値の取り違えによるローカル処理エラーは同じattempt 1で回復し、履歴とbackupを保存した。[Q&A独立点検](../research/ir-case-studies-2026-10-15/6754/initial-public-qa-followup/independent-recheck.md)と[説明資料独立点検](../research/ir-case-studies-2026-10-15/6754/quarter-presentation-followup/independent-recheck.md)は完了。[7公表値の独立点検](../research/ir-case-studies-2026-10-15/6754/disclosed-facts/independent-recheck.md)を完了し派生はfile-onlyのまま、[著者論点比較v2](../research/ir-case-studies-2026-10-15/6754/author-condition-followup/case-record-v2.md)と研究監視登録まで完了。

[追加6社の会社資料確認結果](../research/ir-iwai-business-hypotheses-2026-10-15/issuer-followup-outcomes.md)を固定。6754は2PDF保存・実取り込み、290A/6080/7741/8252は各初回robots接続のTLS検証失敗で停止、8725は既知403を保持して新要求0。取得失敗を投資除外へ変換せず、診断・再試行はしない。同じ6754原PDFのp7–8にある[PQA地域範囲・利益率の確認](../research/ir-case-studies-2026-10-15/6754/PQA-demand-margin-followup/README.md)を完了し、親も2画像/5引用を確認した。需要・率は既答、費用寄与は未確認を維持。

[公開資料保存契約の既存提案](../research/ir-public-capture-contract-review-2026-10-15/README.md)から[新取得用の最小照合](../research/ir-public-capture-validation-2026-10-15/README.md)を実装・受入完了。既存scriptの明示opt-in API/CLIと新test/docに限定し、旧provider出力・旧source/IDは保持する。独立レビューで再現した2P2を最小修正し、関連41件・全1,372件・修正後の独立再確認が成功。編集前/初回実装/修正後の全文・所見を保持した。native schemaはv1、実装修正はrevision 2で、抽出replay・金融意味・真正性・DB保存証明は対象外。

[6754のノート付説明資料](../research/ir-case-studies-2026-10-15/6754/notes-cost-explanation-followup/README.md)は1GETで保存し、[4頁の独立点検](../research/ir-case-studies-2026-10-15/6754/notes-cost-explanation-followup/independent-recheck.md)と[著者論点追補](../research/ir-case-studies-2026-10-15/6754/author-condition-followup/notes-observation-addendum.md)を完了。コード検証後、[実取り込み](../research/ir-case-studies-2026-10-15/6754/actual-notes-import/README.md)を15:14に完了した。公開の需要要因は解決部分として保持し、費用継続・利益寄与分解は未確認。同じ会社/四半期の表示を独立予測へ数えない。[追加4頁](../research/ir-case-studies-2026-10-15/6754/notes-additional-cost-search/README.md)は[独立点検](../research/ir-case-studies-2026-10-15/6754/notes-additional-cost-search/independent-recheck.md)まで完了し、v13へ接続した。図中文字の抽出missを画像転記で保持し、架空text offsetを作っていない。