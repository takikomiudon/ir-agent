# 既存方針を使う最初のIR研究ベースライン

候補選別はJPX日経中小型株指数の公表結果、仮説・反証と質問準備はAnthropic、評価入力への対応はDamodaran、価値と価格・継続保有理由の点検はTweedy, Browneを使う。[段階別の設計と原典](../research/ir-author-derived-baseline-design-2026-10-16/README.md)と[回答反映の流れ](ir-decision-flow.md)を参照する。個社の予測や売買価格は、これらの方法を参照しただけでは確定しない。

## 最初に調べる集合

[JPXの公式公表一覧](../research/ir-jpx-smallmid-constituents-2026-10-16/README.md)は200銘柄。2026年8月7日公表・8月31日適用予定の版で、10月16日現在の構成維持を確認したものではない。この日付付きの選別結果を研究に採用し、保存済み窓口台帳とコードで照合する。

| 集合 | 件数 | 用途 |
|---|---:|---|
| 公式公表一覧 | 200 | 他者の選別方針による入口 |
| 保存済みIR受付候補との交差 | 121 | メール・フォームの受付記録がある調査候補 |
| 個人受付の明示343社との交差 | 23 | 最初の研究集合 |

[全200社の対応](../research/ir-jpx-smallmid-ir-universe-intersection-2026-10-16/published-plan-all.csv)、[受付候補121社](../research/ir-jpx-smallmid-ir-universe-intersection-2026-10-16/ir-accepted.csv)、[最初の23社](../research/ir-jpx-smallmid-ir-universe-intersection-2026-10-16/fixed343.csv)を保持する。受付の確認日は各行の記録に従い、現在の受付保証へ置き換えない。交差に入らない会社も、取得保留・受付条件・投資不適格を混同しない。

JPXの実績・流動性による選別を利用するため、業界名や低い値動きだけで独自に一括除外しない。公式HTMLと算出要領にある既存構成向け大型株境界の差も残し、343社だけで全市場の順位を再現しない。[方法の確認範囲](../research/ir-jpx-smallmid-selection-method-discovery-2026-10-16/README.md)を参照する。

## 各社を進める手順

1. 既存caseと既読・未読資料を確認し、事業の仮説と評価入力のつながりを一つ選ぶ。
2. 公開資料・Q&Aで答えがある部分を除く。実績、会社予想、外部予測、評価者の仮定を分ける。
3. 採用する評価方法が必要とする入力を確認する。外部著者の独自予測を全社共通の必須条件にせず、会社公表値を使える経路も残す。
4. 残る会社定義の確認が、どの比較・仮説・モデル入力を変えるかを質問前に記録する。倍率や投資家の退出条件は、その所有者側で設定する。
5. 実際の返信があれば、原文・公開性・対象期と事前分岐を照合する。定義の補足と金融入力の変更を区別する。
6. 評価額、価格、保有状態と採用方針が揃った段階で、既存の`decision`／`ir-plan`／判断履歴を使う。

前段の研究は、数値valuationや6項目policyが未完成でも進める。正式質問と金融判断は[現行契約](decision-policy.md)に従う。変化のない案件を毎日深掘りせず、新開示・返信・反証・管理日で再点検し、少なくとも四半期を目安に仮説を見直す。[継続監視](research-stage-monitoring.md)の仕組みを再利用する。

## 1975を接続例にする

朝日工業社は公表一覧と個人受付集合に含まれ、既に会社資料・native監視case・通期会社予想EPS357.49円の候補入力がある。保存済み作業を再利用するための選択で、投資順位ではない。EPSは2026年8月4日資料のFY2027年3月期予想であり、現在の最新予想の確認や金融入力への採用とは区別する。

| 得られた内容 | 反映する先 | 数値評価への扱い |
|---|---|---|
| Q1高粗利の竣工・利益計上時期の説明 | 既存の事業仮説と対象期の注記 | この説明だけでは通期EPS・適正PERを変えない |
| 繰越高の公表値・対象範囲が確認できる | stockと受注flowの比較、既答部分の除去 | 売上化率・利益・現金回収を自動生成しない |
| 根拠が既存の事業見方を弱める | 支持・反証候補と次の公開確認 | 正式な売買判断と区別して再研究する |
| 後日、会社が予想そのものを改訂する | 新しい会社予想の版と根拠 | 採用モデルと事前契約がある場合に変更可能pathを点検する |
| 曖昧・拒否・無回答 | 未解決の記録 | 値や評価額を自動で下げない |

[説明資料10・13頁の照合](../research/ir-case-studies-2026-10-15/1975/backlog-and-full-year-input-followup-2026-10-16/README.md)では、当Q1の繰越高110,795百万円を確認した。表の集計範囲・機器事業の包含は未確認のまま残す。通期会社予想は売上総利益率20.5%→19.6%、営業利益率11.1%→10.8%で、親会社純利益は9,240→9,250百万円。Q1の高粗利から通期EPSの上方修正を導かない。「繰越高の公表自体が不明」という問いは解消した。

公式library/calendarと8月6日資料33頁の確認を終え、[新2資料の実保存・native v2への比較](../research/ir-1975-public-review-and-calendar-integration-2026-10-16/README.md)を完了した。連結繰越高117,864百万円と施設別表110,795百万円は別系列として保持し、差額の帰属は補わない。会社予定4件は原典付きの読取専用レポートへ接続したが、実施・結果・売却期限とはしない。残る定義は、どの比較を変えるかを確認してから質問候補にする。会社に適正PER、他者の予測の意図、目標株価への到達を保証させない。

数値条件の最初の再現には、保存済みmaxgfr/cribleのNCAV式とnet-net条件を使った。[公表会計入力](../research/ir-case-studies-2026-10-15/1975/ncav-accounting-input-review-2026-10-16/README.md)による2026年6月末の流動資産62,374−総負債40,837＝NCAV21,537百万円、条件は時価総額≤2/3 NCAV＝14,358百万円。[期末株数への換算](../research/ir-case-studies-2026-10-15/1975/ncav-per-share-input-bridge-2026-10-16/README.md)は27,200,000−会社表示自己株式1,324,717＝25,875,283株、境界は正確な分数14,358,000,000/25,875,283円／株（参考554.89円）。これはmaintainerのスクリーニング条件の再現であり、Graham原典の全条件、回収価値、公正価値、買値・利確価格の採用ではない。

[公式サイト経由の市場表示](../research/ir-case-studies-2026-10-15/1975/market-comparison-input-discovery-2026-10-16/README.md)は「2026/10/16 15:30・3,860」を取得した。表示内の通貨・timezoneは未確認、6月末以降の株数基準も別入力として残す。数値の大小だけで現在のnet-net合否や売買へ進めない。この方法の直接入力でない繰越高の定義回答からNCAV境界を変えない。

[通期原本の追加保存と比較](../research/ir-case-studies-2026-10-15/1975/annual-earnings-book-input-discovery-2026-10-16/actual-connection/actual-verification.json)で、1975はその時点でnative v3・既読7となった。年次EPS/BPS派生sourceの比較後はv4・既読8。会社表示のFY2026年3月期実績EPS358.13円・BPS1,965.51円から、保存済みcribleの別式 `sqrt(22.5 × EPS × BVPS)` を[独立算術](../research/ir-case-studies-2026-10-15/1975/graham-number-annual-arithmetic-2026-10-16/parent-acceptance.json)で再現すると3,979.69円。丸め総額/別の平均・期末株数から計算するlaneは3,979.53円で、会社直接表示と置換しない。OCIを含む普通株式純資産と日本基準「株主資本」を区別した。

これは価格表示を知った後の方法探索であり、事前固定された成績検証ではない。NCAVとGraham Numberの目的・期間・入力・版を別々に保持し、望む判定を得るための切替や二つの境界の合成はしない。どちらも原Grahamの全適格条件、1年以内の到達予測や売買規則を実装したものではない。同式は[既存valuationの新method](graham-number-valuation-spec.md)から再利用でき、全1,573テストの受入を完了した。

[既存質問の整理](../research/ir-case-studies-2026-10-15/1975/ir-question-disposition-after-public-review-2026-10-16/parent-acceptance.json)では、公開既答を除き、繰越高のscope/取消変更をC2の条件付き比較論点として残した。現NCAVや採用済みforward EPSへ回答を変換する経路はなく、優先IRは0。この文脈を次の正当な年次資料レビューで実際に引き継いだ。数値評価に直結しない定義研究を一律禁止するのではなく、比較に使う目的を先に具体化する。

[5480](../research/ir-case-studies-2026-10-15/5480/native-case-setup-2026-10-16/actual-inputs/actual-verification.json)も同じ23社集合から既存資料を利用し、Damodaranの循環正常化の3論点を監視へ接続した。全サイクル・正常利益・再投資は未解決のまま、native v2・既読10・内部管理Jan16を保持する。3817も[年次原典とEPS/BPSの実入力接続](../research/ir-graham-number-two-company-input-connection-2026-10-16/README.md)を完了し、native v2・既読2を登録した。報告実績EPS443.34円/BPS2,659.88円を保持し、当時の翌期会社予想435.34円や個別値とは混ぜない。両社のsource数値照合は金融採用と区別する。

購入価格・利確価格は採用評価と方針から求める。Tweedyの価値到達時の売却・継続保有理由の点検を使うが、原典にない一律の割安率・利確率を補わない。価格が価値を超える場合も、継続保有理由を含めて検討する。[評価と退出の参照範囲](tweedy-value-research.md)を維持する。


[2929・4318の年次入力接続](../research/ir-2929-4318-annual-input-connection-2026-10-16/README.md)も完了した。2929は原年次と9/17訂正を別sourceのまま保持し、連結実績68.61/BPS453.35を個別損失や翌期会社予想と分ける。4318は74.11/345.24、分割既調整/ESOP控除/平均と期末・表示精度を保持する。両caseの初回比較は未解決で、IR質問や買値・利確率は補っていない。


[固定23社の年次入力経路](../research/ir-jpx-smallmid-annual-input-coverage-2026-10-16/README.md)は全社に有限結果があり、原典取得7・静的対象PDFなし14・保留host1・旧503終了1。取得できない経路と投資除外を分け、同じ閉鎖経路の再探索はしない。coverageの実221資料snapshotは当時の記録として保持する。

[1518・6200・6814の実接続](../research/ir-1518-6200-6814-annual-input-connection-2026-10-16/README.md)により、[7社の年次実績EPS/BPS全14入力](../research/ir-seven-company-annual-input-reference-summary-2026-10-16/README.md)の原典・派生を保存・分類し、native条件との年次比較を完了した時点では、1518は既存case v3・既読9、6200/6814は各v2・既読2。後続の会社予想/公開事業比較・FAQ/native接続と後続Q&A条件比較を含む現在全体は34case・79版・197既読で、元期間・普通株/平均と期末・split/BBT/ESOP・訂正・BPS詳細分母の未確認を保持する。価格なし参考値は現在価格との割安判定や適正価格・売買方針の採用ではなく、IRがどの入力を変えるかも別に検討する。


次の公表確認は[7社calendarの実接続](../research/ir-seven-company-catalyst-calendar-connection-2026-10-16/actual-README.md)へ対応した。新5sourceの保存・分類と既存条件への定性比較を完了し、calendar比較時点の2929v3/4既読、3817・4318・6200・6814各v3/3既読、1518v3/9・1975v4/8を記録した。13予定は全てsource_bound_candidate・due:null・実施未確認、3件は具体日null。年次2値・索引v40・金融採用は変更せず、公表予定と内部研究管理日/売買期限を分ける。[IR用途review](../research/ir-seven-company-reference-to-IR-routing-2026-10-16/README.md)では、今回の固定年次2値screenに優先するIRは0。公開既答の過去表示を説明回答で変えず、将来の訂正/新年度は別のsourceと入力版で扱う。


[16社の公開基礎調査coverage](../research/ir-jpx-smallmid-business-reading-coverage-2026-10-16/README.md)は全primary経路を有限試行し、限定事業/計画本文12社・入口のみ3社・robots503で本文未取得1社を区別した。17原典は[会社予想7factsと同batchで実接続](../research/ir-6814-guidance-and-business-reading-connection-2026-10-16/README.md)し、5480v3/12既読、6200/6814各v4/5既読へ比較を保存した。入口成功や会社目標の説明を年度財務認証/モデル適合とせず、業種だけで除外しない。新しい会社guideと累計EPSは旧年次2値screenとは別入力で、[索引v41](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v41.json)へ区分保存した。[3社のIR用途更新](../research/ir-three-company-public-update-IR-disposition-2026-10-16/README.md)も受入済みで、旧未確認の解消と残余のownerを分けた。金融予測・倍率・売買条件は補わず、現用途のIR優先0を他の研究用途の禁止にしない。

[3612・7388の表示3値の実保存](../research/ir-3612-7388-displayed-facts-connection-2026-10-16/README.md)は[索引v42](../research/ir-case-studies-2026-10-15/disclosed-fact-index-v42.json)へ接続済み（35社250fact・52親entry・54派生source・会社/原典45組、実52派生243fact、対象外2派生7factはfile-only）。3612のBPS、両社の未確認期間・会計・普通株/分母を補わず、既存7社の年次Graham入力集合や参考計算へ加えていない。派生2件の保存・分類と金融採用を区別する。索引v42のactual255資料/native32case snapshotは12:07時点の履歴のまま保持し、後続の[同DD/JIRA論点のnative接続](../research/ir-3612-7388-FAQ-native-connection-2026-10-16/README.md)で新2caseを登録した時点は34case・76版・194既読。3612/7388各v2/config1・既読4/3、unresolved・内部管理Jan16retainであり、Graham7社集合・金融採用・正式IRは変更していない。

後続の[4社Q&A実接続](../research/ir-four-company-public-QA-connection-2026-10-16/README.md)は原4sourceの保存/分類と既存3caseの比較を完了し、現在34case・79版・197既読（4318v4/4既読、6200/6814各v5/6既読）。当時会社の費用/業績予想理由、提案から成約への課題、一般FAQ案内を年次reported値の訂正や著者の将来予測にせず、Graham7社集合・参考計算・金融採用・正式IRは増やしていない。内部管理Jan15=12case/Jan16=22caseと未解決を保持する。

[研究inquiryの接続](../research/ir-research-inquiry-integration-2026-10-16/README.md)により、数値thesis前の定義確認をcase/公開既答/事前比較分岐に結び付けて保存できる。7388の未送信draft1件だけを保存し、研究返信0/review0・sent_at:null・no_reply。これは正式金融question/reply0と別母数で、旧case/job/入力/policy・Graham7社集合・索引v42の歴史snapshotは変更していない。focused27件・全1,612件成功は実装契約の検証であり、個人受付・送信ready・IRの金銭価値・金融採用を保証しない。
