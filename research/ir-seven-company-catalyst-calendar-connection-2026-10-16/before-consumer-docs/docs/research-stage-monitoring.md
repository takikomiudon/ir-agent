# 数値評価前の研究を継続する

数値thesisが未完成の会社は、会社別の研究ファイルで継続する。日次workerは通常のjobに加えて、この段階の新しい保存資料と既存管理日を点検する。[研究点検レポート](../scripts/report_research_monitoring.py)で、明示した研究一覧と保存DBを読み取れる。通常のdailyとは別の読取専用レポートで、自動起票はしない。明示したcaseを実jobへつなぐ場合は、[定性レビューjob](qualitative-research-jobs.md)のopt-in台帳を使う。通常dailyの金融thesis要件を外したり、intake分類で研究を代用したりしない。

```bash
.venv/bin/python scripts/report_research_monitoring.py \
  --db data/research.sqlite3 \
  --cases path/to/case-requests.json \
  --research-root .
```

[入力契約](../research/ir-research-monitoring-integration-2026-10-15/contract.md)に従って、前回研究の固定file/hash、資料inventoryと論点に対する確認状態、既存管理日・timezone・根拠を明示する。新保存、以前からある未列挙資料、既存未確認資料、管理日、根拠不足は別々に表示する。`reviewed`は担当者の確認記録で、仮説を支持することや金融入力の妥当性を意味しない。日時やfileが不足すれば保留し、現在作成した一覧を過去の事前仮説と扱わない。既存DBはread-onlyで開き、欠損DBを新規作成しない。

登録済caseの現在進捗は`qualitative show`／`qualitative queue`から読む。固定manifestを渡す読取専用レポートは、そのファイルが記録した範囲を点検する。台帳の完了結果を外部manifestへ自動転記しないため、両者の時点を区別し、旧manifestだけで再精読を要求しない。

## 採用する既存手順

固定した[Anthropic thesis-tracker](../third_party/anthropic/skills/thesis-tracker/SKILL.md)のStep 2は、新しいデータがどのpillarを強めるか・弱めるか等を記録する。Important Notesには次の指示がある。

> Review theses at least quarterly, even when nothing dramatic has happened

本プロジェクトでは、この更新・反証・定期レビューを会社別研究にも適用する。日次の起動は利用者の希望であり、著者が全社を毎日再分析することや個別の売買期限を指定した意味ではない。

## 日次workerの作業

1. [継続作業の最新状態](ongoing-work.md)と[会社別の研究一覧](../research/ir-case-studies-2026-10-15/README.md)を読み、今回担当する会社・前回の研究ファイル・既存の論点ID・管理日・未取得の資料を明示する。一覧は現時点の限られた研究対象で、窓口台帳1,819社の調査完了を意味しない。
2. 新しい公開資料が保存されていれば、通常のingestとintakeによる分類を行う。保存された原文と時点を確認してから、同じ会社の前回研究・著者条件・定義の問いへ対応付ける。**資料分類の完了と、条件への影響を点検したことを分ける。** intakeの結果へ分類以外の内容を混ぜない。
3. 資料の変化がなくても、研究ファイルに既に記録された管理日の到来を別枠で確認する。日付がない場合は未設定と記録し、会社の発表予定や売却期限を代用しない。管理日や時計のtimezoneを曖昧にしたまま期日到来を判定しない。
4. 新しい根拠又は管理日の到来があれば、会社別の旧記録を残して比較結果を追記する。支持・反証候補・変更なし・未取得を区別し、回答済みの質問を除く。変化も期日到来もない場合は、同義のpreviewや仮の予測を作らない。
5. `daily`のselectedだけでなくskipped等も読む。jobが空なら、今回の研究対象、新しい保存資料の有無、管理日の到来、確認できていない範囲を報告する。これだけで全社のWeb更新を監視したことにはしない。

数値モデルと根拠が揃った会社は[通常の仮説・質問・返信処理](workflow.md)へ進む。数値thesisを登録するためにEPS、倍率、確率や価格を補わない。

担当を分ける場合は[研究段階の依頼テンプレート](../.agents/skills/jp-equity-ir/references/roles.md#数値仮説前の研究担当に渡す依頼)を使い、会社・旧論点・固定研究・manifest・reportを同じ時点で渡す。資料の関連確認と次版inventoryの登録担当を分け、未登録の研究資料がreportの対象外であることも返す。

## 保存済み資料の未読ページを追加で読む場合

同じsourceの別ページから新たに意味を確認しても、会社が新しく公表した資料にはしない。元source ID・snapshot SHA・公表/取得/初保存時点を保ち、今回の読解日時・新しく読んだページ・逐語引用・旧観測から分かったこと・残る不足を会社別の追記ファイルへ保存する。`reviewed`の旧記録を全冊読了と解釈しない。[1870の追加3頁](../research/ir-case-studies-2026-10-15/1870/profit-bridge-review-2026-10-16/parent-full-source-acceptance.json)は、元の部分抽出を変えず、新しい引用を同じ原PDFの全文sourceへ結合した例である。

既存のnative `queue`は未確認source又は管理日到来を対象とし、既読sourceの追加読解だけを手動起票する機能はない。観測だけの更新のためにsourceを作り直したり、case条件/configや管理日を偽って変更したりしない。追加研究ファイルがnativeの前回観測へ未接続なら、その状態を明記する。caseの元条件を本当に改める場合の設定改版と、追加読解の記録を分ける。

四半期の比較では累計期間も揃える。Q2/3Qの累計にQ1の特別利益が残っているだけで、その利益が再発したとは判定しない。前年同期比、旧会社予想比、当期実績と通期予想は別の基準として保存する。これはAnthropicの指標・会社予想比較を本プロジェクトへ適応した読解上の確認で、売買閾値を追加するものではない。

## 接続されている範囲

| 機能 | 現在行うこと | この段階で別途必要なこと |
|---|---|---|
| `intake` | 保存済みの未分類公開資料を分類する | 著者条件や前回の定性研究との比較 |
| `daily` | activeで利用可能な数値thesisがある会社の新資料・再点検日を起票する | 数値thesis前の研究管理日の点検 |
| 研究点検レポート | 明示した研究一覧の新保存・未確認・管理日と保存来歴を表示する | 著者条件への影響の比較、研究記録と次回inventoryの更新 |
| `qualitative` | 明示caseの新保存・管理日から定性reviewを起票し、独立したcase進捗を保存 | 凍結資料に対する担当workerの比較、必要時の設定改版 |
| `inbox` | 質問・返信の作業を表示する | 会社別研究ファイルの点検 |
| 公開材料の予定レポート | 明示した予定日と原典の対応を表示する | 実施/結果確認、研究管理日との区別 |
| 外部の起動基盤 | このリポジトリの外でworkerを起動する必要がある | 起動設定、永続DB、取得・分類・比較を行う担当 |

`daily`はWebを巡回せず、watchや数値thesisのない会社をskipする。statusだけをactiveへ変えてもthesis要件は残る。架空thesisやintake jobで研究管理を代用しない。外部の定時起動や自動Web取得が設定済みとも主張しない。

## 実データで行った限定確認

[135Aの手作業確認](../research/ir-research-monitoring-2026-10-15/135A-manual-check.json)では、記録済みの管理日2027-01-15は未到来で、前回研究時刻より後に実DBへ保存された同社の資料は0件だった。保存15資料の初回保存時刻はすべて既知で、DBは読取専用・前後hash一致。Web上の新資料の有無、前回以前の全資料の意味確認、他社はこの確認の範囲外である。

この会社はwatch・数値thesis0のため、通常dailyに自動で研究が戻らないという静的な到達経路も確認した。将来日を実行したテストや、自動スケジューラの設置を表す記録ではない。

[1518の実施記録](../research/ir-research-monitoring-2026-10-15/1518-manual-review.json)では、会社資料3件の取り込み・intake分類後、既存の著者論点を会社別ファイルで比較した。数値research jobやthesisは作らず、分類後の研究を担当workerの別枠作業として完了した。[親の管理日](../research/ir-case-studies-2026-10-15/1518/author-condition-followup/review-cadence.json)は同じ四半期レビュー手順から2027-01-15とした。これは会社の公表予定や売却日ではなく、新しい保存資料があれば前倒しする。DB保存順と研究JSONの申告日時だけから、過去に未見の情報で事前仮説を検証したとは扱わない。

後続の[実レポートv6](../research/ir-research-monitoring-integration-2026-10-15/actual-report-v6.json)では6社30保存sourceを点検した。7525では、v5後に会社本文2件を実保存すると[確認待ちへ戻り](../research/ir-research-monitoring-integration-2026-10-15/actual-new-source-trigger-validation.json)、[旧著者論点との比較](../research/ir-case-studies-2026-10-15/7525/issuer-plan-comparison/case-record.md)を完了してv6へ反映した。会社目標の裏付けは増えたが、比率定義・著者の反証幅・金融入力の採用は未解決のままである。

## 現在の登録済み監視（2026-10-16）

[1975の追加2sourceによる実処理](../research/ir-case-studies-2026-10-15/1975/public-source-calendar-and-presentation-connection-2026-10-16/qualitative-review/actual-verification.json)はnative v2・既読6へ進み、管理Jan16維持・再queue0。既読sourceのp10/13追加読解は新pendingへ偽装せず、summaryとcase_observationにfile/SHA/読解時刻付きで手動引継ぎした。[公式予定4件の実DBレポート](../research/ir-case-studies-2026-10-15/1975/catalyst-schedule-connection-2026-10-16/actual-report/report.stdout.json)は原典と結合するが、日付のみ・due:null・実施未確定を保持する。

[現在値のRO点検](../research/ir-1518-6200-6814-annual-input-connection-2026-10-16/actual-verification.json)では227資料（公開226・市場1）・分類226。全136job完了（intake105・定性31）、attempt133/event266/request receipt133・pending/leased0、source来歴はlegacy28/trusted199。native監視は32case・64版・176既読、内部管理日はJan15が12case・Jan16が20case。公開資料41社・財務内容36社。管理日は内部研究日であり、会社予定や売却期限ではない。

[2341のnative v1](../research/ir-case-studies-2026-10-15/2341/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)は原短信/派生12値の2既読、[2410のnative v1](../research/ir-case-studies-2026-10-15/2410/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)は原短信・10/1通知・10/15結果・公開QA・派生12値の5既読で、どちらも初回queue0。2341は商品売上/ARR・特益/利益予想・株数定義、2410は非連結Q3/終了年度向け7月予想・普通/特別配当・取消認識を分ける。2410の会社公表Prime継続結果を未確認へ戻さず、独立した取下完了や取引保証とも区別する。

[索引v37の受入](../research/ir-case-studies-2026-10-15/2410/disclosed-facts-2026-10-16/index-connection/parent-acceptance.json)は28社226fact（実41派生/219fact、対象外2派生/7factはfile-only）。その210source・25case/47版/144既読は2410登録前の歴史snapshotで、現在値へ書き換えない。同原本の追加読解や[2163の帰属確認](../research/ir-case-studies-2026-10-15/2163/actionlearning-authorship-saved-pages-2026-10-16/parent-acceptance.json)、[2327の静的入口](../research/ir-case-studies-2026-10-15/2327/initial-public-review-2026-10-16/parent-acceptance.json)はfile-only補足。[2445](../research/ir-case-studies-2026-10-15/2445/initial-public-review-2026-10-16/parent-acceptance.json)はrobots302で規則未確認・1GET停止/source0であり資料不存在や投資除外ではない。2459候補もfile-only・DB外で実台帳へ加算しない。

個社の具体的将来予測・金融policy・売買閾値は未採用で、金融thesis・実policy・明示position・正式質問・返信・送信・注文は0。外部schedulerは未設置。[既存1,558テストの受入](../research/ir-public-information-review-binding-integration-2026-10-16/parent-acceptance.json)は従前checkpointとして保持し、Graham Number新methodは[別途1,573テストで受入](../research/ir-graham-number-valuation-integration-2026-10-16/parent-acceptance.json)した。

[5480の初回監視](../research/ir-case-studies-2026-10-15/5480/native-case-setup-2026-10-16/actual-inputs/actual-verification.json)と[1975通期原本の比較](../research/ir-case-studies-2026-10-15/1975/annual-earnings-book-input-discovery-2026-10-16/actual-connection/actual-verification.json)を完了した。5480は旧資料6件の初読で新着ではなく、1975は旧年度原本の現在新保存。後者の質問整理は明示file/SHA/読解日時でsummaryと観測へ引き継いだ。


[二社の年次入力接続](../research/ir-graham-number-two-company-input-connection-2026-10-16/README.md)で1975はv4/config1・既読8、3817はv2/config1・既読2へ進めた。新規保存時点以後にactual input auditを実行し、file-only時代の古いauditと区別する。[索引v38](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v38.json)は29社230fact、実43派生/223fact。両社のEPS/BPS値の照合は金融採用や現価格による買い・売り判断を認証しない。


[2929・4318の初回比較](../research/ir-2929-4318-annual-input-connection-2026-10-16/README.md)は両case v2・既読3/2、再queue0。2929は訂正原文の画像表/テキスト限界を残し、EPS/BPSへ自動適用しない。4318は既調整splitとESOPの平均/期末を区別した。元3条件・管理Jan16を保持し、金融採用・IR質問は0。


[1518・6200・6814の年次入力比較](../research/ir-1518-6200-6814-annual-input-connection-2026-10-16/README.md)を完了し、1518は既存case v3・既読9（管理Jan15維持）、6200/6814は各v2・既読2（内部管理Jan16）へ進めた。原本reported basisの支持と、派生の再表現unchanged、case全体unresolvedを区別する。6200のBPS詳細分母未確認、6814の平均/期末・NCI/会計変更、1518のsplit/BBT・利益scopeを保持し、現在予測や金融採用へ変えない。旧prepare-only票/23社coverageの221資料snapshotは履歴であり、現在の未読や再登録要求へ戻さない。
