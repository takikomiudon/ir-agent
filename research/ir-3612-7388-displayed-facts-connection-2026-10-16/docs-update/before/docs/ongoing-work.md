# 継続作業の状態

利用者の停止指示があるまで、目前のタスクからIRに基づく投資判断ロジックを構築する。既存著者の手順を優先し、金融予測・倍率・確率・売買条件を独自に補わない。サブエージェント利用は許可済み。実送信・注文・有料契約・deploymentは指示されていない。

## 現在の台帳と受入

2026-10-16 11:40 UTC（[会社予想・公開事業本文の実処理検証](../research/ir-6814-guidance-and-business-reading-connection-2026-10-16/actual-verification.json)の完了時点）。実DB `data/ir-research-2026-10-15.sqlite3` は253資料（公開252・市場1）・分類252。全166job完了（intake127・定性39）、attempt163/event326/request receipt163・pending/leased0、source来歴はlegacy28/trusted225。native監視は32case・72版・187既読、内部管理日はJan15が12case・Jan16が20case。公開資料あり55社・財務内容あり41社。main DB SHA256は `9baff7307207746bbc6402e4a0123e9d1dc6eadb6aca0f960283409e4789a1d6`。財務内容分類には会社目標・収益discussionも含み、年次財務認証や金融adoptionではない。

native監視は32case・72版・187既読資料。1904は既読通知の3配当表示を円銭版2で再表現した派生1sourceを比較し、source unchanged/case unresolvedを保持した。旧元条件と旧全行不変、再queue0。公表済みの税method/CF未作成/個別千円・契約変更の[追加読解](../research/ir-case-studies-2026-10-15/1904/operating-driver-followup-2026-10-16/parent-acceptance.json)も[固定handoff](../research/ir-case-studies-2026-10-15/1904/question-residual-review-2026-10-16/parent-acceptance.json)からsummaryとcase_observationへ日時・file/SHA/source-nativeSHA付きで引き継ぎ、現prior投影に両方残ることを確認した。旧Q1/追補を新pending証拠へ追加せず、自動受領保証とも扱わない。

[索引v41](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v41.json)は33社247fact・50親entry・52解決済み派生source・会社/原典43組。実50source/240factを保存・分類し、対象外8331/9702の2source/7factはfile-only。[今回index接続の受入](../research/ir-6814-guidance-and-business-reading-connection-2026-10-16/index-connection/parent-acceptance.json)で旧v40全体を保持した。旧v40のactual227資料観測は10:54 UTC時点の歴史snapshotで、calendar時点に新v41を作らなかった事実も保持する。今回の7factsは会社予想・Q3累計で、旧年次reported/Graham入力を変更せず、金融採用0。

1,819社のwatch/held:falseは実保有確認ではない。明示保有申告・金融thesis・正式質問・返信・実policy・research_decision_reviews・送信・注文は0。管理日は12caseが2027-01-15、5831/7325/7157/5988/1866/1870/1904/1950/1963/1975/2163/2315/2341/2410/5480/3817/2929/4318/6200/6814の20caseが2027-01-16 Asia/Tokyo。会社予定・売却期限ではない。外部scheduler・定時Web取得・LLMの定時実行は未設置。

コードの最新受入は[1,585件・37.349秒成功](../research/ir-reference-value-integration-2026-10-16/parent-acceptance.json)。公開`calculate_reference_value`と`reference-value`は既存6methodを価格・dummyprice・価格比率・actionなしで再利用する。weightedは明示確率だけ、unweightedは期待参考値nullと範囲。独立reviewは必須指摘0、旧priced本体は不変で111結果/エラーが同値。従前の[1,573件・38.890秒](../research/ir-graham-number-valuation-integration-2026-10-16/parent-acceptance.json)では、新method graham_numberは正の明示EPS/BPSから著者の固定式を計算し、期間・金融採用・売買は自動認証しない。極端な価格/確率等による総精度の指摘を修正し、独立再確認で必須指摘0。従前の[1,558件の受入](../research/ir-public-information-review-binding-integration-2026-10-16/parent-acceptance.json)では任意のquestion.public_information_reviewで、確認範囲/時点/source native SHA/逐語引用と残余理由を固定し、全原典の実保存来歴/公開性訂正を照合する。独立F1/F2の2指摘を修正し、旧5planの全出力はbyte同値。レビュー用sourceを評価根拠へ自動採用せず、旧fieldなしの経路も保持。[1963実資料binding-only probe](../research/ir-case-studies-2026-10-15/1963/public-review-binding-probe-2026-10-16/README.md)の参照照合成功は回答不存在/IR価値/送信ready/投資判断の認証ではない。

円銭変換の既存受入は[1,534件・37.088秒成功](../research/ir-yen-sen-normalization-integration-2026-10-16/parent-acceptance.json)。円・銭を明示指定時だけ変換し、原表示・成分・位置を保持する。独立175合成組合せと拒否/改変/消費側の点検は指摘0、旧33source/143factの全再現結果は編集前後でbyte一致。旧形式は版1/JSON/ID不変、新形式ありだけ版2。モデル点検・意味確認の保留を維持し、金融採用0。従来のvalid legacy_presenceのknown-by以後の現在の定性読解と、firstsave不明・非新着・元receiptの区別も維持する。実行中のleaseはない。1904配当3表示の生成・原文照合・実保存・定性比較・索引v30接続まで完了した。

## 直近に完了したこと

- [外部公表選別からの研究ベースライン採用](../research/ir-jpx-smallmid-research-baseline-adoption-2026-10-16/adoption.json)は200公表予定銘柄→保存IR受付121→個人明示23。1975で公開比較・実台帳レビュー・予定原典結合まで接続した。

- 2341は原短信＋派生12値を保存・分類し、[native v1・既読2](../research/ir-case-studies-2026-10-15/2341/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)を登録、初回queue0。商品売上/ARR、全社費用/OP、特益/親会社利益予想、消却/cash/株数scopeを分け、正常利益・現在EPS・金融採用は作らない。
- 2410は原短信・10/1通知・10/15結果・公開QA・派生12値を保存・分類し、[native v1・既読5](../research/ir-case-studies-2026-10-15/2410/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)を登録、初回queue0。会社公表Prime継続結果は既答だが独立取下完了/取引保証ではない。非連結Q3と終了年度向けJuly guide、普通/特別配当・取消認識を分け、会社3,000円目標を投資家評価額にしない。金融未採用・正式質問0。

- [25source/91factのbatch接続](../research/ir-normalized-facts-batch-db-integration-2026-10-15/README-actual.md)、[5988税6値の接続](../research/ir-case-studies-2026-10-15/5988/tax-disclosed-facts/actual-connection/README.md)、[5988の元9原本によるcase登録](../research/ir-case-studies-2026-10-15/5988/native-case-setup/known-by-native-acceptance/README.md)。旧全行を保持。旧v1/v2の拒否/copy候補は履歴で、現在の実登録を再実行しない。
- [Anthropicの5番目のDD技能を参照採用](../research/ir-management-meeting-skill-adoption-2026-10-15/adoption-receipt.json)。旧4技能/LICENSE/manifest旧entry不変、独立15項目・指摘0。[既存3問への適用](../research/ir-dd-question-application-2026-10-15/README.md)は独立22項目・指摘0、rootも元草案/3票/全入力と旧分岐SHAを照合済み。正式登録・送信は未準備。技能の質問手順へ実例と期間比較の参照を接続した。
- [3社の期間比較](../research/ir-three-draft-horizon-comparison-2026-10-15/README.md)。135A/7525/2983の著者条件・会社期・次観測・内部管理日・最大1年の比較windowを分離。定義回答だけで長期目標や売買を判定しない。root読解・全10入力SHAと27pointer/引用の照合済み。現行DBや原PDFを再認証した記録ではない。
- [入力所有者](../research/ir-decision-input-ownership-2026-10-15/README.md)。v1の6必須はproject契約で、既にuser/external_policyの両方を受け付ける。費用/保有は実執行と利用者、quote鮮度/精度は明示したデータ利用方針、将来予測/投資閾値は適合する採用方針と分ける。rootもコード/契約と6出典SHAを照合。値や採用記録は補わず、共通gateは維持。
- [最初のMagic Formula maintainer](../research/ir-greenblatt-maintainer-implementation-review-2026-10-15/parent-acceptance.json)は追加4GET・全25cellを確認しscreen-onlyで終了。購入数/保有/入替/売却はなく、TEV近似・US/長期条件・許諾未確認を残す。
- Brazil候補は[作者説明4GET](../research/ir-brazil-magic-formula-maintainer-review-2026-10-15/parent-acceptance.json)、[順位/returnコード3GET](../research/ir-brazil-magic-formula-ranking-sale-code-2026-10-15/parent-acceptance.json)、[財務列の定義1GET](../research/ir-brazil-magic-formula-financial-definitions-2026-10-15/parent-acceptance.json)を終了。dense順位和/first行順/最大30と期間指数は確認したが、ROIC構成式は未読の前処理データ依存。宣言税率0.34は未使用、要約の負NetDebt除外も選択コードに対応せず。日本適合/実売買/金融採用0。[独立設計検討](../research/ir-author-ranking-intermediate-feasibility-2026-10-15/README.md)に従い、実入力がない順位API/CLIを増やさず、privateデータ/別repo等の探索へ広げない。
- [10jobの初回実測](../research/ir-structured-cohort-capacity-observation-2026-10-15/README.md)は窓396.428602秒、lease経過p50=395.990073/p90=396.048264秒。同じworker名を保持したまま重複を除くと占有区間unionは396.428601秒。実作業/並列分析者数/全社分析の処理能力ではない。利用量・予算は不明、会社数上限は未推定。親も全12pinと区間/分位点を直接再現した。同じcohortの再計測は次taskにしない。

## 進行中と、次の具体作業

現在は[最初の研究ベースライン](research-baseline.md)を運用へ接続している。[JPXの選別方法](../research/ir-jpx-smallmid-selection-method-discovery-2026-10-16/README.md)と[公式公表一覧200銘柄](../research/ir-jpx-smallmid-constituents-2026-10-16/README.md)を確認し、[保存済み窓口との交差](../research/ir-jpx-smallmid-ir-universe-intersection-2026-10-16/README.md)は受付候補121社・個人受付明示23社。原一覧は8月7日公表・8月31日適用予定の版で、10月16日現在の構成認証とはしない。日付付きの外部選別結果を研究集合として採用し、初期接続例は既存資料がある1975とする。新会社の一律拡大や独自の投資順位は作らない。

1975では[既読説明資料10/13頁の追補](../research/ir-case-studies-2026-10-15/1975/backlog-and-full-year-input-followup-2026-10-16/README.md)に加え、公式library/calendarと[8月6日個人説明会資料の33頁](../research/ir-case-studies-2026-10-15/1975/public-qa-presentation-followup-2026-10-16/README.md)を確認した。新calendar/PDF原本2sourceは08:48:49UTCに実保存しintake完了、[native v2・既読6](../research/ir-case-studies-2026-10-15/1975/public-source-calendar-and-presentation-connection-2026-10-16/qualitative-review/actual-verification.json)へ比較を追記した。連結繰越117,864と施設別110,795は別の公表系列として保持し、差額帰属・取消調整・現金化は未解決。管理Jan16は維持、再queue0。[予定4件の実DBレポート](../research/ir-case-studies-2026-10-15/1975/catalyst-schedule-connection-2026-10-16/actual-report/parent-acceptance.json)も受入済みで、11/12発表・11/17説明会等を実施/売却期限へ変換しない。旧Mayログミー本文や動画は所在のみで、現在必要な入力へ関係しないまま探索を続けない。

1975の数値条件は保存済みcribleのNCAV式で再現した。6月末NCAV21,537百万円・2/3条件の時価総額上限14,358百万円、[期末普通株数（会社表示自己株式控除後）への換算](../research/ir-case-studies-2026-10-15/1975/ncav-per-share-input-bridge-2026-10-16/parent-acceptance.json)は25,875,283株、正確な境界14,358,000,000/25,875,283円／株（参考554.89円）。[市場表示の取得](../research/ir-case-studies-2026-10-15/1975/market-comparison-input-discovery-2026-10-16/README.md)は公式経由の埋込HTMLまで4GETで終了し「2026/10/16 15:30・3,860」を保持したが、通貨/timezone・現在株数・NCAV合否・金融採用は未確認。[公式株式状況](../research/ir-case-studies-2026-10-15/1975/stock-count-basis-followup-2026-10-16/parent-acceptance.json)は3月末basisの掲示で現在株数へ置換しない。通期原本を09:34:32UTCに実保存・分類し、[native v3・既読7](../research/ir-case-studies-2026-10-15/1975/annual-earnings-book-input-discovery-2026-10-16/actual-connection/actual-verification.json)へ比較を追記した。[候補整理](../research/ir-case-studies-2026-10-15/1975/ir-question-disposition-after-public-review-2026-10-16/parent-acceptance.json)の手動文脈をsummary/観測双方に実保存し、公開既答を削除・C2の条件付き比較だけ残した。現優先IR0、NCAV/EPSへの変換path0。

[5480の実監視接続](../research/ir-case-studies-2026-10-15/5480/native-case-setup-2026-10-16/actual-inputs/actual-verification.json)を完了し、C1〜C3の循環正常化の未解決を維持した。native v2/config1・既読10、内部管理Jan16・再queue0。登録後確認でclaim応答のid/job_idを読み違えたが、保存済み応答からread-only回復し成功mutatorは再実行していない。

[Graham Numberの独立算術](../research/ir-case-studies-2026-10-15/1975/graham-number-annual-arithmetic-2026-10-16/parent-acceptance.json)は直接表示EPS/BPSで3,979.69円、丸め総額からの別laneで3,979.53円。価格表示を見た後に選んだ探索で、事前固定の投資試験ではない。同式を[既存valuationの新methodへ接続](graham-number-valuation-spec.md)し、新1,573テストで受入した。1975/3817の年次EPS・BPSは原典と派生sourceを実保存・分類し、actual-source bindingを4値で確認した。1975はnative v4/config1・既読8、3817はv2/config1・既読2へ比較を保存済み。意味確認と金融採用は別に残す。3817の市場表示「4,820・15:30」は通貨・価格日付等が未確認で、正式な価格入力にはしていない。

2983の新目的は完了した。[日本PE回帰の公式原典](../research/ir-damodaran-regional-regression-discovery-2026-10-16/README.md)、[一般変数定義の有限追補](../research/ir-damodaran-regression-definitions-followup-2026-10-16/README.md)、[会社入力への対応](../research/ir-case-studies-2026-10-15/2983/damodaran-relative-method-input-mapping-2026-10-16/README.md)、[著者例の算術再現](../research/ir-damodaran-regression-arithmetic-reproduction-2026-10-16/README.md)、[国内比較表の再現](../research/ir-case-studies-2026-10-15/2983/domestic-peer-table-reproduction-2026-10-16/README.md)を受入済み。5年成長率/Beta等の入力不足を未解決のまま残し、3年EPS系列の延長や比較平均23.5倍の公正倍率化はしない。定義route、旧EPS確認・取消票のIR0は閉鎖を維持する。

[既存EPS入力の所在一覧](../research/ir-existing-eps-input-readiness-2026-10-16/README.md)も受入済み。固定v37の28社226factsを対象とし、EPSは21社46facts。会社予想・外部独自予想・会社利益からの外部計算、終了FY予想・未終了FY予想・期間境界不明を分け、最新性や金融採用を認定していない。外部会社forecastを全方法の共通必須にしない扱いは[判断方針](decision-policy.md)へ明記した。

2459の初期資料は[訂正版quotes-v2/manifest-v2による受入](../research/ir-case-studies-2026-10-15/2459/initial-public-review-2026-10-16/parent-acceptance.json)済みだがfile-only・DB外で、実台帳・監視caseへ加算しない。

日本IR協議会の[2026年調査](../research/ir-jira-practice-survey-discovery-2026-10-15/parent-acceptance.json)を4GET、[2018年対話指針](../research/ir-jira-dialogue-best-practices-2026-10-15/parent-acceptance.json)を追加2GETで確認済み。調査の個人投資家対応強化率をメール受付率へ変換せず、前年度とは設問が異なる点を保持する。指針の9/14/25頁から公表実績の変動理由・計画の前提・FAQ照合を[質問準備](ir-question-preparation.md)へ反映した。[変更の受入](../research/ir-jira-question-method-adoption-2026-10-15/parent-acceptance.json)は独立12項目・指摘0、親も34pinと全差分を照合済み。会社側の当時の推奨を、現在の法令判定・返答保証・売買規則にはしない。

固定契約の[入力変更範囲の監査](../research/ir-precommitted-parameter-boundary-review-2026-10-15/README.md)も完了。`target_parameter`は説明ラベルであり、新しい正式利用は`decision_contract`と`parameter_paths`を使う。旧APIは事前固定した枝全体を使い、個別path制約は提供しない。workflowと技能にこの差を明記し、コードと旧分岐は変更していない。

既存候補4の[maxgfr/crible](../research/ir-transparent-metric-library-discovery-2026-10-15/README.md)は4GETの固定commit/tree/README/MIT確認、[3GETの式とデータ条件](../research/ir-transparent-metric-formula-review-2026-10-15/README.md)、[3GETの計算本体](../research/ir-transparent-metric-core-review-2026-10-15/README.md)を終了。局所ROIC/ROC/EYと平均期/株数/非有限除去を特定した。日本原典の取込はYahoo scraped依存というmaintainer記載があり、導入で原典対応が済むわけではない。税率clip0〜50%・資本10%guardはmaintainer固有の慣行で、原会計税率・将来税後ROC_new・Greenblatt本人規則と混同しない。追加のrank/外部依存探索はしない。

[5988年次14fact](../research/ir-case-studies-2026-10-15/5988/annual-capital-disclosed-facts/parent-acceptance.json)は独立14fact/9契約確認・指摘0、親も62pin/14換算を照合した。[実保存](../research/ir-case-studies-2026-10-15/5988/annual-capital-disclosed-facts/actual-connection/parent-actual-verification.json)のfirstsaveは00:15:52.528146 UTC。旧全rowを保持しintake1件完了後、[nativecase比較](../research/ir-case-studies-2026-10-15/5988/annual-capital-disclosed-facts/qualitative-review/parent-acceptance.json)を独立12確認・指摘0で完了した。5988case v3・source/case unchanged、2027-01-16管理日を維持、再queue0/mainSHA不変。比較結果は新しい会社開示や将来税/CFの採用ではない。

[独立scalar算術](../research/ir-capital-metric-scalar-reproduction-2026-10-16/parent-acceptance.json)は元14factにbindingし、2期のEBIT/WC/税前ROCとmaintainer税clip/NOPATを再記述。親は別のexact Fraction計算で全分子/分母を一致確認した。ROIC/EY/valuation/rank/futureROC_newは不足理由つきnullで、product API/依存runtimeの追加はない。

[資本残高8fact](../research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/parent-acceptance.json)は表示行の独立意味確認とroot受入を完了し、[実保存・分類](../research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/actual-connection/root-actual-verification.json)後に[既存caseへ照合](../research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/qualitative-review/parent-acceptance.json)した。5988 v4/source・case unchanged、管理日Jan16JST維持、再queue0。完了後のroot検証はattempt rowが書換わるとの誤った期待で一度停止したが、保存は再送せずprequeue backup全行と期待追加差分を照合して受入した。debtの当期首/末のnull暦日は維持した。

[条件付き歴史ROIC](../research/ir-historical-roic-role-reproduction-2026-10-16/parent-acceptance.json)は明示した研究role/scope対応でFY2026だけを算術再現し、平均資本63,740.5百万円、maintainer clip後NOPAT508.5百万円、比率1017/127481（約0.7978%）をrootの別Fraction計算と一致確認した。strict日付窓のFY2026、FY2025、futureROC_new/EY/valuation/rankは理由付きnull。crible固有の税率clipや範囲仮定を将来税・正常利益・売買条件に移さない。

[5988次回準備票](../research/ir-case-studies-2026-10-15/5988/question-residual-review-2026-10-16/parent-acceptance.json)は旧文6句を18根拠へ対応し、既知の前提を再質問せず、約6億円の範囲/337との重複と、その額の期間対応だけを保留した。旧草案の背景は元々質問ではなく、元3分岐も不変。

[新3社の原8source](../research/ir-new-company-intake-2026-10-16/README.md)を保存・分類済み。1861は静的索引のみで財務0、1866/1870は完全テキストを保存した原本と限定した意味レビューの範囲を分けた。1870の[利益橋渡し](../research/ir-case-studies-2026-10-15/1870/profit-bridge-review-2026-10-16/README.md)で、特別利益2620百万円・管理事業譲渡益1000百万円・開発販売事業譲渡の損益なし・Q1 CF未作成が公表済みと分かった。これらを再質問せず、[買収注記2頁の追加読解](../research/ir-case-studies-2026-10-15/1870/acquisition-note-followup-2026-10-16/parent-acceptance.json)で取得対価/原価2500・暫定のれん3398百万円/10年・損益算入5月1日〜6月30日を確認した。4月1日取引とみなし取得日を区別し、仮定期首効果省略を0としない。[準備票](../research/ir-case-studies-2026-10-15/1870/question-residual-review-2026-10-16/parent-acceptance.json)は7既答/6残前提で、追加IR価値は未立証。既読sourceの追加読解は[監視手順](research-stage-monitoring.md)に従いfile-only補足として時刻・source/quote・解消論点を残す。新source/config/管理日を偽装してnative再実行しない。1375の旧503停止は維持。

[1866の追加読解](../research/ir-case-studies-2026-10-15/1866/operating-driver-followup-2026-10-16/parent-acceptance.json)はp10/11を確認。受注/完成/繰越は提出会社単独建設で契約変更額を含み、Q1連結CF計算書は非作成と明記。採算/工期/現金化を補わず、p9セグメント表は未読のまま。[残余準備票と固定handoff](../research/ir-case-studies-2026-10-15/1866/question-residual-review-2026-10-16/parent-acceptance.json)を受入済み。4既答群/残る3比較前提、IR価値未立証を保持。

[既読資料の追補handoff設計](../research/ir-1870-additional-reading-native-handoff-design-2026-10-16/parent-acceptance.json)は新API不要。次の正当なjobへ原source/file/SHA/read_atを明示して渡し、summaryとcase_observationへ既知/残余を残す。packet自動探索/機械受領保証はない。[役割テンプレートの1節追加](../research/ir-additional-reading-role-integration-2026-10-16/parent-acceptance.json)は独立10項目・指摘0、旧全文を保持。

[1871の初期研究](../research/ir-case-studies-2026-10-15/1871/initial-public-review-2026-10-16/parent-acceptance.json)は3GETで公式root/静的一覧2source、財務本文0。財務PDF literalなしで有限停止後、[原2sourceを実保存・分類](../research/ir-next-company-intake-2026-10-16/parent-acceptance.json)した。技術/掲載告知を金融本文の確認へ格上げしない。

[金融庁公式資料の限定確認](ir-fd-source-context.md)は入口4GET/新たに明示された本文1GETを完了し、原9頁のうち物理5/7だけを意味/画像確認した。公表済み補足の一般的/それ自体という限定と、補足内の重要情報に関する留保を保持。project3分類の法的自動mapping、2018当時版とのbyte同一性/版履歴・現行法全体は未確認。[方針への参照追加](../research/ir-fsa-fd-context-integration-2026-10-16/parent-acceptance.json)は独立所見0で、新gate/金融条件0。

1904はQ1後の分割/配当修正とユニティー取得通知を[取得・意味確認](../research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/parent-acceptance.json)し、[実保存・分類](../research/ir-case-studies-2026-10-15/1904/post-quarter-corporate-action-followup-2026-10-16/actual-connection/actual-completion.json)とnative定性比較を完了。中間99pre/期末24.75post/年間dash・会社参考198、優待新基準2027-03-31、9月30日取得完了を既答へ移した。分割日程の独立実施確認、現在EPS、取得価格・正確な連結開始と寄与は残る。資本金1000万円を対価、軽微見込みを0としない。Q1実績/8月会社予想の6公表値は実保存・分類・定性比較を完了し、索引v29へ追加済み。分割DPS3表示の[当時APIの限界記録](../research/ir-case-studies-2026-10-15/1904/split-dividend-disclosed-facts-2026-10-16/parent-acceptance.json)と旧入力票は保持し、別の[生成済み記録](../research/ir-case-studies-2026-10-15/1904/split-dividend-composite-facts-2026-10-16/generated/parent-acceptance.json)を実接続済み。

[1904の追加3頁](../research/ir-case-studies-2026-10-15/1904/operating-driver-followup-2026-10-16/parent-acceptance.json)では税計算方針、Q1連結CF非作成、個別・千円の受注表と契約変更額を含む定義を確認した。具体税率や営業CF・将来利益は補わず、物理10頁のセグメント注記は未読。追加読解自体は新source化せず、次の正当なjobでcase v4の要約・観測へ手動で引き継いだ。

[1904セグメント注記p10](../research/ir-case-studies-2026-10-15/1904/segment-note-followup-2026-10-16/parent-acceptance.json)はcase v4後の追加読解で、比較期・千円・地域列・セグメント間取引消去・営業利益への調整を確認した。P1の定義は部分解消、原因分解/親会社利益/税CF/正常予測は残る。旧v4の未読表示は当時の状態として保持し、この追補はまだfile-onlyでnative更新なし。個別工事表へ自動対応させず、調整額を本社費と読まない。

[1904残余票v2](../research/ir-case-studies-2026-10-15/1904/question-residual-review-v2-2026-10-16/parent-acceptance.json)はp10による比較定義の部分解消を記録したfile-only補足。旧case v4の当時未読表示と既存条件を保持し、native更新や将来jobの実行権にはしていない。

[1950の完全短信](../research/ir-case-studies-2026-10-15/1950/statement-followup-2026-10-16/parent-acceptance.json)は13頁全文と限定意味1/2/4/8頁を保存。[原4sourceと推奨派生1sourceの初期分類](../research/ir-1950-initial-with-facts-intake-2026-10-16/parent-acceptance.json)、[firstsave記録](../research/ir-1950-initial-with-facts-intake-2026-10-16/source-firstsave.json)、[native case v1/既読5](../research/ir-case-studies-2026-10-15/1950/native-case-setup-2026-10-16/parent-acceptance.json)を受入済み、初回queue0。[推奨9値](../research/ir-case-studies-2026-10-15/1950/disclosed-facts-2026-10-16/context-reference-only/parent-acceptance.json)は主引用・金融scopeを保持し文脈引用の重複だけを参照へ置換した表現を索引採用した。旧full-context版85fe…は未投入で二重計上しない。Q1年率化、当時予想を現在へ持越し、EPS分母再構築、正常利益/将来DPS列への採用は0。配当年度両端/recorddate/会計/連結nullを維持する。

1963は[初回原3source](../research/ir-case-studies-2026-10-15/1963/initial-public-review-2026-10-16/parent-acceptance.json)に[公開概要/QA2source](../research/ir-case-studies-2026-10-15/1963/public-explanation-followup-2026-10-16/parent-acceptance.json)と短信9表示の派生1sourceを加え、[6sourceを実保存・分類](../research/ir-1963-initial-with-facts-intake-2026-10-16/parent-acceptance.json)した。[native v1/既読6の登録](../research/ir-case-studies-2026-10-15/1963/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)も完了、初回queue0。[公開既答9群と残余6の準備](../research/ir-case-studies-2026-10-15/1963/question-residual-preparation-2026-10-16/parent-acceptance.json)を保持し、Indonesiaの6か月混在/2026年1–3月別掲と全社Q1を区別し機械控除しない。水ingは7月1日完了/配当調整後25,068百万円と会社原文の期・連結/個別利益を保持し、QA質問者25,608と混ぜない。Q2会社予想約200億をQ1 OP/CFOへ移さない。DPS年度両端等null、営業外FX/税NCI/新連結/株式scopeと将来正常利益/CF未採用を維持する。旧初期producerのfile-onlyは当時の記録で、現在の実登録を否定する状態ではない。

[1975の原3source＋派生1source/9値](../research/ir-1975-initial-with-facts-intake-2026-10-16/parent-acceptance.json)は実保存・分類済み。[native v1・3条件・既読4](../research/ir-case-studies-2026-10-15/1975/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)を登録し初回queue0。公開既知8群/残余7を保持し、Q1高粗利の竣工件数/利益計上時期、設備工事/機器の異なる採算、FPD需要回復へのFY受注期待と旧大型ドライヤ案件の売上見込みを分ける。連結/個別受注はフローで残高や利益保証にせず、CF非作成をゼロとしない。年次正常利益/将来CF/現在予想/IR判断への採用は0。

1963の[受入済み概要p6/8追補](../research/ir-case-studies-2026-10-15/1963/segment-explanation-followup-2026-10-16/parent-acceptance.json)と[残余票v2](../research/ir-case-studies-2026-10-15/1963/question-residual-review-v2-2026-10-16/parent-acceptance.json)は同一sourceのfile-only文脈。旧既知9群/残余6とnative v1を保持し、追加job/sourceを作らない。セグメント前年同期利益、FY想定粗利率差、全社OP、営業外FXを同一化せず、持続性/未来margin/税CF/金融採用は未確認のまま。

[2163原4source＋派生1source/10値](../research/ir-2163-initial-with-facts-intake-2026-10-16/parent-acceptance.json)は実保存・分類済み。[native v1・3条件・既読5](../research/ir-case-studies-2026-10-15/2163/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)を登録し初回queue0。公開既知10群/残余7を保持し、FAQ選定5scopeを全FAQ/会議QA読了にしない。単体平均と期末・Q2チャートは窓/重み未確定、未配属給与の販管費から原価への移動は費用消失ではない。賞与・新卒給与・休日工数の季節性、税前利益からの営業CF調整と保険/証券の投資cashを分け、二重加算しない。EPSは会社の既split表示、中間43pre/期末21.50post・年間dash・会社分割前参考86を区別し、年額合算/DDM/正常利益/将来CF/IR判断への採用は0。

2315は[初期原5＋派生1](../research/ir-2315-initial-with-facts-intake-2026-10-16/parent-acceptance.json)に[補足原1](../research/ir-2315-supplement-intake-2026-10-16/parent-acceptance.json)を加え、[native v1・3論点・既読7](../research/ir-case-studies-2026-10-15/2315/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)を登録、初回queue0。12表示値は千円Q3実績・百万円会社指標/予想、OP/経常/親会社利益段階、負EPS、明示中間DPS0.00を保持する。特別益/減損・税NCIを相殺/足戻しせず、期末/年額未定を0にしない。[会社別modelscope](../research/ir-case-studies-2026-10-15/2315/model-scope-review-2026-10-16/parent-acceptance.json)はmethod null/needs_dataで、金融/young/cycle/通常default/投資除外を決めていない。

[補足の追加20/57/58頁](../research/ir-case-studies-2026-10-15/2315/financial-definition-saved-pages-followup-2026-10-16/parent-acceptance.json)は四半期売上図の内部控除と事業紹介を確認。BTC売却損等の原因説明と負売上gross/net・実現/評価の認識定義は別で、自己発行tokenを保有/顧客資産へ移さない。善光の3〜5月寄与には3月検収ピークを含み年率化しない。[単一研究票1問/定性3区分](../research/ir-case-studies-2026-10-15/2315/question-residual-review-2026-10-16/parent-acceptance.json)は公表会計方針の案内を求める研究設計で、正式登録/送信準備や金融branch/評価法採用ではない。

2163の[公式スポンサーindex](../research/ir-case-studies-2026-10-15/2163/external-research-entry-followup-2026-10-16/parent-acceptance.json)と[ActionLearning原本4頁](../research/ir-case-studies-2026-10-15/2163/actionlearning-report-review-2026-10-16/parent-acceptance.json)は受入済みfile-onlyで202資料へ未算入。作成日3月27日/掲載日5月8日、会社説明由来の旧基準年間86と過去分割調整を分け、図凡例EPS×PERから採用倍率/targetを作らない。独自予測は確認4頁で未認定、他14頁未読。

[2315年次1sourceの実保存・分類](../research/ir-2315-annual-accounting-intake-2026-10-16/parent-acceptance.json)と[年次定性job](../research/ir-case-studies-2026-10-15/2315/annual-accounting-qualitative-review-2026-10-16/parent-acceptance.json)を完了し、case v2/config1・既読8へ進めた。旧7bootstrap/旧ticket/configは不変、Jan16管理日retain・再queue0。[旧202資料状態の記録](../research/ir-2315-current-state-integration-2026-10-16/parent-acceptance.json)は05:49:30受入の履歴として保持し、v35全factと201資料時点snapshotも書き換えない。

年次意味範囲は1/66/67/71/72と[分解表87/88](../research/ir-case-studies-2026-10-15/2315/annual-revenue-disaggregation-saved-pages-2026-10-16/parent-acceptance.json)だけ。特定Zaif/顧客取引の売買差額・約定日認識、市場有無別評価、会社/一部子会社の年次B/Sその他scope、PL非区分表示・非活発市場評価損の原価注記、年度別顧客契約/その他/外部売上区分は公表既答へ移した。旧一般定義問を一部削減する結果をsummaryとcase_observation双方に実保存したが、その他収益行をメディア等Othersegment列や暗号資産評価へ割当てず、年次方針を現Q3の対象法人/取引mix・売却/評価/手数料含有へ自動適用しない。現Q3当てはめ/金融モデルはunresolved、IR価値unproven/ready false、将来税CF・正常利益・価格・新金融branchは未採用。

[2327日鉄ソリューションズの初回入口](../research/ir-case-studies-2026-10-15/2327/initial-public-review-2026-10-16/parent-acceptance.json)はrobotsと一覧の2GETで停止。静的HTMLは空のJS/library容器でPDF href0、入口1source・財務本文0のfile-onlyで、210資料・監視caseへ未算入。取得限界を投資除外・会社資料の不存在とせず、JS/feed/別経路の自動再開には進まない。

1. IR効果の[研究候補の書誌確認](../research/ir-private-investor-meetings-paper-discovery-2026-10-15/README.md)を2GETで終了。2011年SSRN登録の要旨はNYSE1社の個別面談が対象で、2015年掲載版と内容同一性/因果/日本の個人メールIR効果は未確認。公式掲載siteの[robots1GET](../research/ir-private-investor-meetings-journal-source-2026-10-15/README.md)はGPTBot個別禁止のため本文0で停止。旧v7全11entryを保持した[中央holds-v8/12host](../research/ir-source-access-holds-2026-10-15/README-v8.md)への更新を完了し、active4fileの旧bytesと限定差分を保存した。旧Crossref要旨を掲載本文の結論に昇格させず、予測尤度/金融値を設定しない。
2. 3社の期間比較を踏まえ、次の公表観測で照合する元条件を使う。会社系列内の定義確認と、著者予測/評価前提の不足を分け、FY29/31/3期等の目標を1年の退出期限へ縮めない。
3. 新しい原典/明示された著者仕様/正しい入力が得られた課題へ進む。[31taskの進捗v5](../research/ir-issue-owner-backlog-2026-10-15/README-v5.md)のowner/DAG/未解決を保持し、取得停止や金融入力不足を新機能・架空値で隠さない。optionalな投資スタイル質問は未回答で、回答を仮定しない。

## 引継ぎの規則

[技能](../.agents/skills/jp-equity-ir/SKILL.md)、[担当依頼](../.agents/skills/jp-equity-ir/references/roles.md)、[workflow](workflow.md)、[定性job](qualitative-research-jobs.md)を使う。packet.kind/stageを確認し、intake分類・定性観測・金融researchの契約を混ぜない。会社の保存担当を一人にし、rootだけが実DBを書き込む。状態確認はURI mode=roとquery_onlyを使い、Store初期化を呼ばない。旧receipt・原文・引用位置・実firstsaveとknown-byを保持する。

金融条件は[判断方針](decision-policy.md)、[モデル点検](model-routing-inputs.md)、[13段階の運用](ir-operation-design.md)に従う。Anthropicの仮説/反証/四半期/DD準備、Damodaranの説明→数値/モデル適合、Tweedyの原典/対話研究、EVSI原式を研究手順へ採用済み。具体的な将来予測・公正倍率・価格条件・IR尤度の採用とは別で、会社予想転載を著者独自予測にしない。

公開GET前に[12 exact hostの収集保留v8](../research/ir-source-access-holds-2026-10-15/README-v8.md)と後続記録を確認する。alphaarchitect.comはrobots403の1GETで本文0・原因不明として終了。QuantConnect/AAII/旧Graham・Greenblatt原典/Tweedy What Has Worked/Piotroski/Fisher/動的E-IR/各社取得停止の既存有限経路を再開せず、UA/別host/JS/Cloud診断で迂回しない。9702の専用IRフォームは過去GET200だが入力field/個人受付未確認、旧HTML/rawなしであり、未試行/受付拒否へ書き換えない。将来raw保存の修正で過去captureが復元されたとはしない。

## 過去の完全記録

以下は旧v35接続時点の記録であり、現在値ではない。旧段落の全bytesを保持する。

[索引v35](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v35.json)は26社202fact・39親entry・41解決済み派生source・会社/原典32組。39source/195factを実保存・分類済み、対象外8331/9702の2source/7factはfile-only。[親の照合](../research/ir-case-studies-2026-10-15/2315/disclosed-facts-2026-10-16/index-connection/parent-acceptance.json)で旧190fact/38親entryを全object保持した。index SHA256は `e6837e96945198db88bbd0341acd5591553313567e3efb2aa45a0deae45fe38f`。2315の受入済み12factだけを1親entryで追加し、千円Q3実績の損失符号/会社nonGAAP EBITDA/当時FY予想の別OP107・経常107/明示中間DPS0.00と期末年額未定・null scopeを保持した。索引接続のDB観測は補足と2315case登録前の201source/23case/44版/134既読であり、その歴史snapshotは現在202資料へ書き換えない。1950旧full-context版85fe…は追加していない。1904の中間pre/期末post/会社分割前参考と年間dash非合算の境界も不変。全financial model入力は未採用。

[23:25までの旧継続記録](research-history-2026-10-15-through-2325.md)を完全byteで保存した。さらに前の[20:05までの詳細記録](research-history-2026-10-15-through-2005.md)も保持する。旧件数・作業中・未確認・テスト数・source予算は当時の状態であり、現在の再実行指示ではない。個社原典と後続比較は[事例索引](../research/ir-case-studies-2026-10-15/README.md)へ。


## 次の作業を引き継ぐ位置（10:10 UTC時点の履歴）

1975・3817の入力接続、native初回比較、索引v38を完了した。3817は公開既答と残余IRの対応を準備中。次の公表順2471は[静的一覧の確認](../research/ir-case-studies-2026-10-15/2471/annual-accounting-input-discovery-2026-10-16/README.md)を2GETで終了し、動的配信/held hostへ進まない。年次入力未取得は投資除外ではない。次は2929の公式年次原典と訂正の関係を確認している。23社の既存作業と次の最小taskも整理し、同じ閉鎖経路を再探索しない。


## 10:38/10:54/11:18 UTC時点の履歴と、11:40 UTC以後の引継ぎ

2929・4318は新原典/訂正/派生の計5sourceを実保存・分類し、native両v2（既読3/2）へ比較を完了、全130job完了・lease0。索引v39の旧230facts保持と実接続も受入済み。2929完了後の表示確認でrecordの階層を読み違えたが、保存済み成功とRO SQLを確認し、未完了4318だけを完了した。成功mutator再実行0。

新APIの[価格なし参考計算](reference-value-spec.md)は1,585テスト成功・独立必須指摘0で受入済み。1975/3817を新公開CLIで実再現した。2929/4318のactual-source入力監査は2値ずつsource_values_matchedで完了し、公開CLI参考値836.57/758.74円をroot独立算術でも照合した。金融採用・価格観測は0。

[23社coverage](../research/ir-jpx-smallmid-annual-input-coverage-2026-10-16/parent-acceptance.json)は受入済みで、今回対象年次経路の未着手0。7原典取得・14静的対象PDFなし・8704保留host・5480旧annualfeed503を区別し、221資料snapshotは当時の履歴として保持する。coverageのRO保留は解除済み。1518/6200/6814の原典と各2factsの計6sourceは[実保存・分類・定性比較](../research/ir-1518-6200-6814-annual-input-connection-2026-10-16/README.md)まで完了した年次接続時点では、1518は既存case v3・既読9、6200/6814は新case各v2・既読2。後続calendar比較後の現在版は下記に分ける。1518の既存条件/管理Jan15を維持し、6200/6814は内部管理Jan16。新case重複登録や成功mutator再実行は不要。3社の初期file-only/prepare-only票は当時の履歴で、現在の実保存・監視を否定しない。7社全14年次入力は[まとめ](../research/ir-seven-company-annual-input-reference-summary-2026-10-16/README.md)へ接続済み。閉じた動的一覧・held配信先・旧503を再取得しない。


[公開calendar5sourceの実接続](../research/ir-seven-company-catalyst-calendar-connection-2026-10-16/actual-README.md)はintake5＋定性5を完了し、再queue0。その時点の2929はv3・既読4、3817/4318/6200/6814は各v3・既読3、1518v3/9読・1975v4/8読と各内部管理日は不変。[13予定の実レポート](../research/ir-seven-company-catalyst-calendar-connection-2026-10-16/actual-schedule-report.json)は全てsource_bound_candidate・due:null・実施未確認、3件は具体日null。2929の10/28株主総会は決算発表APIの対象外、6200の次回発表日は未確認。予定を売買日・会社発表の実施済みへ変えない。4318の[営業実績追補](../research/ir-case-studies-2026-10-15/4318/operating-performance-public-review-2026-10-16/README.md)と6814の[会計方針追補](../research/ir-case-studies-2026-10-15/6814/accounting-policy-public-review-2026-10-16/README.md)は既存sourceの追加読解で、新金融値を作らず、定性結果のsummary/rationaleへfile SHA・時刻付きで手動引継ぎ済み。


[7社のIR用途review](../research/ir-seven-company-reference-to-IR-routing-2026-10-16/parent-acceptance.json)は受入済み。今回固定した年次reported EPS/BPS2値screenへの優先IRは0であり、1518の既存定性componentや1975/3817の条件付き比較を永久に閉じる結論ではない。6814の当時会社予想修正通知と4facts、6200の選定8/3 Q3版と3factsは[実保存・分類・既存条件への比較](../research/ir-6814-guidance-and-business-reading-connection-2026-10-16/README.md)まで完了した。6200v4/5既読・6814v4/5既読、5480は中計/事業説明の新2sourceを比較してv3/12既読、全config1・case unresolvedを維持。旧annual reportedと当時会社guideを分け、C3の公開確認を金融入力の採用としない。16社のGET0 literal inventoryと23社annualcoverageは当時記録として保持する。現コード1,585テストの受入は不変で、このphaseで再実行していない。


[別用途businesscoverage](../research/ir-jpx-smallmid-business-reading-coverage-2026-10-16/parent-acceptance.json)は全16primary試行済、限定本文12社・入口のみ6547/7085/9928の3社・2471robots503対象本文0/source0。17原典（primary15＋3612/5480の別scope PDF2）を今回batchへ保存済み。入口200と事業本文、会社計画/目標と実績、財務内容分類と年次財務認証を区別する。閉じたannual/JS/feed/provider経路を再探索せず、旧記録を本文取得済みに書き換えない。[5480/6200/6814のIR残余更新](../research/ir-three-company-public-update-IR-disposition-2026-10-16/parent-acceptance.json)も受入済み。公開で解けた旧疑問を再質問から外し、現用途の優先IRは0・金融更新許可も0のまま。全方法のIR価値0とはしていない。

6200は[既存の対象期を維持](../research/ir-three-company-public-update-IR-disposition-2026-10-16/6200-period-continuity.json)する。既存FY2025のreported年次参考値に、FY2026の累計実績・当時予想を代入しない。別の数値比較を新規設定せず、新年次資料が保存された時に新しい版として点検する。会社予定やFY2026資料の現公表有無を確定する判断ではない。

現在は保存済み統合報告書の追加読解を進めている。3612は年次1株利益の表示を見つけたがBPS未特定、7388はEPS/BPS表示を見つけたが会計・株式basisに未確認がある。表示factの構造化はfile-only作業中で、7社の年次Graham入力コホートや実台帳・索引へ追加認定していない。4318の一時利益についても、保存著者原典の調整手順と必要入力を限定確認中で、aftertax調整式・税率・正常EPSを自作しない。
