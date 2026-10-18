# 実企業への適用：round2の完了と残る採用条件

[round2-plan.json](round2-plan.json)の3件は、会社別の公開情報を評価・IRへ結ぶための限定研究として完了した。1379の検証項目、135AのCFの意味、1社の予測と実行方針の不足を具体化した。金融モデル・数値予測・投資方針・IR質問の実採用はまだない。算術や汎用監査機能の追加を、この不足への既定の次作業にはしない。

## 3件で具体的に解けたこと

| 完了したtaskと成果物 | 明確になった内容 | 採用せず残した内容 |
|---|---|---|
| 1. [1379の決算preview](../ir-case-studies-2026-10-15/1379/earnings-preview-candidate.md) / [JSON](../ir-case-studies-2026-10-15/1379/earnings-preview-candidate.json) | 国内きのこの価格/需要、生産/販売、化成品の価格改定/供給、費用の4論点を、会社の説明・代替説明・反証候補・次回公表指標へ対応付けた。公表5値は既存成果物を参照し、再抽出していない。 | 会社予想の成立を保証する条件ではない。Q1の4倍や独立した数値Bull/Base/Bear、確率、数量感応度、評価法は作成せず、採用入力pathは全null。公開で答えた問いは聞き直さず、質問は登録していない。 |
| 2. [135Aの現在CF→予測基準](../ir-case-studies-2026-10-15/135A/current-cashflow-to-forecast-basis.md) / [JSON](../ir-case-studies-2026-10-15/135A/current-cashflow-to-forecast-basis.json) | 中間CF表30行について、現在実績の役割と、各予測期・安定n+1期で別途必要な入力を分けた。税前利益起点、税費用と支払税、利息、WC調整の符号、設備取得支出と他の投資、財務CFを区別した。PDF画像と58逐語引用を保存した。 | CFO223百万円をFCFFや年率値にせず、現在FCFFも未計算。前払費用/未払金のCFとBSの不一致、設備取得と償却/支払範囲は未解決。表示0/△0を厳密な経済ゼロとしない。将来CF、NOPAT_next、ROC_new、g、n、r、採用pathはnull。 |
| 3. [1379の採用前提](../ir-case-studies-2026-10-15/1379/adoption-prerequisites.md) / [JSON](../ir-case-studies-2026-10-15/1379/adoption-prerequisites.json) | EPS倍率・DCF・DDMについて、会社公表値が充足候補になる箇所と、期間/範囲の確認、将来予測、倍率/率、価格、実行policyの不足を別欄にした。必要な文書種類・提供者・対象期と次作業を1社分に限定した。 | 会社の1期予想は独立予測や将来CF/配当列ではない。methodやモデル値、費用・リスク・鮮度・目標scenarioを採用していない。会社予想の使用自体を一律禁止する結論でもない。 |

[親照合記録](round2-parent-recheck.json)は135Aのraw/text hash・実DB原典一致・58引用・30行・採用path0、1379 previewの3原典・13引用・4論点を確認した。これは原資料との対応の照合であり、予測や金融的意味の検証済み認定ではない。各成果物の限定調査では新GET、DB変更、production追加、送信を行っていない。

## 横断レビューと外部資料の区分

[質問準備レビューv2](../ir-case-studies-2026-10-15/ir-question-readiness-review-v2.md) / [JSON](../ir-case-studies-2026-10-15/ir-question-readiness-review-v2.json)は、窓口台帳内7社と台帳外の千葉銀行8331を分けた8社の限定レビューである。公開解決、次の公開確認、条件付きで残り得る定義、モデル未採用理由を整理した。全社の実採用canonical pathはnull。5480/1375の取得保留を解除せず、未取得を非開示や質問価値の証明にしない。05:30時点の記録は変更せず、後続のpreview・CF対応・採用前提を本索引から辿る。

[Shared Researchの探索](../ir-case-studies-2026-10-15/1379/external-report-discovery/README.md)では、提供者・更新日・会社関与と、本文にある会社予想の再掲を確認した。確認した通期数値は`issuer_guidance`のまま。SRの定性見解と区別し、著者自身の独立数値予測は限定確認で候補0件だった。外部媒体への到達を独立性や将来数値の採用へ格上げしていない。[実intake](../ir-case-studies-2026-10-15/1379/external-report-discovery/actual-intake.json)も保存されている。

[135Aの外部予測探索](../ir-case-studies-2026-10-15/135A/external-forecast-discovery/README.md)では、AENTRO自身の将来目安/条件付き推計3件を確認した。会社委託・報酬を受領するという開示と、当該数値の作者は別軸で記録する。スポンサー関係を理由に著者推計を否定せず、独立検証済みとも扱わない。3GET全200で取得を終え、親が[3原典hash・13外部引用＋4会社比較引用を照合](../ir-case-studies-2026-10-15/135A/external-forecast-discovery/root-recheck.json)した。

著者の下振れ見通しは「拠点立上げ遅延」**かつ**「継続顧客比率45%近辺で頭打ち」という条件付きで、遅延1点だけでは同じ枝へ進めない。No Rating/No Target Price、FY27 EPS94.85円は会社予想の再掲、FY25実績PER50.2倍は将来の採用倍率ではない。著者自身の見通し候補を得たことと、現行評価器へ入れるEPS/FCF列・倍率や実予測のcommitmentを採用したことを分ける。金融モデル/金融仮説への採用は0のままである。

## 後続の実照合と調達調査（06:08 UTCまで）

[135Aの著者条件と最新KPIの実照合v2](../ir-case-studies-2026-10-15/135A/author-condition-followup/case-record-v2.md) / [JSON](../ir-case-studies-2026-10-15/135A/author-condition-followup/case-record-v2.json)が完成した。原表では受注基準の累計394社、継続顧客売上比率57.5%、年度内累計AI単価20百万円、中間営業利益率21.7%・Q2単独35.7%・通期会社予想30.1%、金沢7月1日営業開始を確認した。累計/単独、実績/会社予想、売上比率/社数維持率、営業開始/受注や売上寄与を分ける。継続比率57.5%は45%近辺頭打ちを支持する観測ではなく、著者のAND条件全体の成立は確認できない。将来の減速を永久に否定した結論でもない。

独立レビューで、過去Q&Aの358社を「前期末」とした期間表現1件を発見した。v2は「7月14日当時の現在、図のFY27 Q1」へ帰属を訂正し、Q&Aが明記しない正確な期末日を指定しない。[原版](../ir-case-studies-2026-10-15/135A/author-condition-followup/case-record.md)と原JSONは変更せず、[親v2照合](../ir-case-studies-2026-10-15/135A/author-condition-followup/root-recheck-v2.json)は一field差以外の完全一致と、引用・数値・期間・AND判定・管理用再点検日2027-01-15の不変を確認した。研究の定義対応は具体化したが、採用pathはnull、正式IR質問・金融予測への採用は0。再点検日は会社の決算予定や売却期限ではない。

[岩井コスモの著者評価例](../ir-author-valuation-example-2026-10-15/README.md)では、保存済みローツェ6323レポートに著者自身のEPS予想と目標4,500円があることを確認し、親も[PDF1・2頁を再視認](../ir-author-valuation-example-2026-10-15/root-recheck.json)した。目標PER・採用EPS年度・算式は未確認なので、目標値は日付付き参照値とし、逆算や市場PERの転用で評価式を作らない。現在の投資選定や実DBへの採用はない。この境界と数値評価前の会社別研究は[技能](../../.agents/skills/jp-equity-ir/SKILL.md)・[判断方針](../../docs/decision-policy.md)にも反映済みで、通常dailyや数値thesisの契約変更ではない。

[IFIS/QUICKの予測データ調達調査](../ir-forecast-data-sourcing-2026-10-15/README.md)は公式6GET全200で完了し、親が[6raw/text/snapshot・4HTML再抽出・20公式引用＋6既存引用を照合](../ir-forecast-data-sourcing-2026-10-15/root-recheck.json)した。IFISは日次bulkでアナリスト個別予想・コンセンサス・会社予想を分ける具体候補だが、個別予想等には証券会社の許可が必要。QUICK APIの存在は確認したが、そのAPIからの業績予測供給は未確認。対象銘柄/FY、作者/改訂時点、料金、個人契約、保存・クラウド/AI利用等は未確認で、契約・データ本体の受領・API実装・実DB追加・モデル採用は行っていない。製品説明への到達を入力不足の解消としない。

## 保存状態の更新

05:42 UTCの親照合時点は実sources60/classifications60、市場source0だった。その後、保存済みShared Research HTMLの静的JSONから指定4fieldだけを抽出した[価格snapshot](../ir-case-studies-2026-10-15/1379/provider-market-snapshot/README.md)を、親が[独立照合](../ir-case-studies-2026-10-15/1379/provider-market-snapshot/root-recheck.json)し、**05:43:42 UTCに取り込んだ**。[actual-ingest.json](../ir-case-studies-2026-10-15/1379/provider-market-snapshot/actual-ingest.json)と[05:44の不足棚卸し](../ir-case-studies-2026-10-15/coverage-after-provider-market.json)が後続記録である。採用前提packetの05:34時点の価格未取得、snapshot作成担当の取り込み前の記述は当時のまま残す。

05:43:42時点は61sources（公開60＋市場1）/60classifications、intake13、attempt10/events20/receipt10、legacy28/trusted33だった。**05:52:45 UTCに135Aの外部資料3件の[実intake](../ir-case-studies-2026-10-15/135A/external-forecast-discovery/actual-intake.json)を完了**し、最新状態は次のとおり。後続のKPI照合v2・保存レポート例・調達調査で実DB件数は増えていない。05:44棚卸しの市場1社/財務本文6社というcoverageは変わらず、棚卸しは再実行していない。

| 項目 | 最新の保存記録 |
|---|---|
| 全件テスト | [1,281件成功・34.985秒](../ir-equity-bridge-integration-2026-10-15/README.md)。追加28件で9入力の株主価値調整・IR変更範囲を確認。 |
| 実source / 分類 | 64（公開63＋市場1）/ 63。市場sourceは`requires_research:false`で新intakeは発生しない。 |
| 公開資料のある会社 / 財務本文あり | 7社 / 6社。8331は別の研究ファイルで、実DBの会社別取り込みに混ぜない。 |
| 完了intake / 計測attempt / event / receipt | 14 / 11 / 22 / 11。計測は分類leaseであり、active分析や会社の全工程時間ではない。 |
| source来歴 | legacy28 / trusted36。旧資料の初回保存時刻を後付けしない。 |
| 会社状態 | 1,819社watch、非保有。 |
| 実採用・実行 | 金融仮説、質問、返信、実予測、実policy採用、送信、注文はすべて0。 |

市場sourceが保持するのは提供者申告の2,048円、quote時刻`2026-10-14T06:30:00.000Z`である。live/current価格、取引所による独立検証、鮮度policyや金融モデルへの採用は未確認のまま。価格sourceの追加だけでは、将来予測や実行方針の不足は解消しない。

[価格取得後の採用前提追補](../ir-case-studies-2026-10-15/1379/adoption-prerequisites-market-supplement.md)は、原HTML取得・派生抽出・実DB初回保存を分け、価格候補の不足だけが一部解消したことを記録する。05:34の元packetは変更していない。

## 現在進めている次作業

[135Aの価格確認](../ir-case-studies-2026-10-15/135A/public-price-discovery/README.md)は3GET全200で終了。価格表示と時刻だけでは通貨・完全な観測日時が不足し、market source化/実DB追加は見送った。KPI照合v2は完成しており、5月の著者資料と10月の会社資料を10月15日に取得した後日の比較という限界は維持する。

[期間と営業立ち上がりの照合](../ir-case-studies-2026-10-15/135A/horizon-and-catalyst-review.md)で、長期CFの対象期と1年以内の検証証拠・価格修正時期を区別した。初売上まで約1年と受注後納品まで約3カ月を加算せず、研究管理日を会社予定や売却日にしない。[価格期待の原典研究](../ir-market-expectations-2026-10-15/README.md)もGET0で完了し、逆算結果を市場の真の予想とせず、会社・著者・投資家の不明点をそれぞれの主体へ戻す手順を反映した。

[Toyota原典の9入力点検](../ir-toyota-author-valuation-readiness-2026-10-15/readiness.md)と独立レビューを完了し、[別methodの最小実装と統合確認](../ir-equity-bridge-integration-2026-10-15/README.md)を完了した。表示入力は3,944.09円で著者3,943円と終価段階から差がある。非営業資産・少数持分を明示し、旧方式・質問は不変。n=0は範囲外、新規取得・現在のトヨタ株の予測は行っていない。

135Aの[顧客数定義の点検](../ir-case-studies-2026-10-15/135A/customer-counting-definition-review.md)で、受注基準は公開解決、法人/工場等の単位は保存15本文で未確認と整理した。[初回草案v2](../ir-case-studies-2026-10-15/135A/customer-counting-question-preflight-v2.md)は単位と比較期間の変更有無へ絞り、単位種類と期間一貫性を別軸にした。親も11引用/5原典と実DB一致を確認、登録・採用・送信0。[5988の保存有報CF/注記点検](../ir-case-studies-2026-10-15/5988/cashflow-oneoff-bridge-review.md)で、423のP/L→税前利益→CF加算、東莞337/英国86の表示内訳を確認した。約6億円のcash/包含/期は未解決のまま。続く[地域予想との対応点検](../ir-case-studies-2026-10-15/5988/asia-forecast-china-cost-link-review.md)で、+6.3億円は海外自動車内アジア、中国約6億との直接対応は未立証と確定。Q1所在地表との範囲/消去/FX・期間を同じ系列とせず、草案を増やさず終了した。[1332の長期買掛金点検](../ir-case-studies-2026-10-15/1332/longterm-trade-payables-review/README.md)は2GETで終了。経路と返済の説明欄は確認したが、年次PDFはrobotsに従い未取得、個別額/契約/正式CF分類は未解決。[公式保存リンクから見つけた外部レポート](../ir-public-valuation-report-discovery-2026-10-15/README.md)2本の限定読取を完了した。1518 FISCOは会社計画の再掲、[9702 Alpha-Win](../ir-public-valuation-report-discovery-2026-10-15/9702-alpha-win/README.md)は著者自身の3期のEPS予測を確認したが、公正倍率/評価式は未確認。株価一定の記述PERを目標倍率へ転用しない。両者の実DB/モデル採用は0。続く[外部予測区分の最小修正](../ir-external-estimate-extraction-2026-10-15/README.md)は全1,288件成功。9702新E3件/転載CE1件の研究用抽出をCLIでも確認し、実DB/モデル採用0を維持した。[IIJの保存CAPEX/CF対応](../ir-case-studies-2026-10-15/3774/capex-cashflow-bridge-review/README.md)と[研究段階の継続監視](../../docs/research-stage-monitoring.md)も有限確認を完了した。1518の[著者条件](../ir-case-studies-2026-10-15/1518/author-conditions/README.md)と公式保存5リンクを確認後、[会社3PDF](../ir-case-studies-2026-10-15/1518/issuer-quarter-followup/README.md)を4GETで取得・親照合し、実DBへ取り込み分類した。現67資料/8社、財務本文7社。[既存著者論点への比較](../ir-case-studies-2026-10-15/1518/author-condition-followup/case-record.md)と[旧/新会社予想4facts](../ir-case-studies-2026-10-15/1518/guidance-revision-facts/README.md)を完了し、公開解決6項目を再質問から外した。管理日2027-01-15/新資料で前倒しとし、実モデル/質問採用は0。現在は未調査の個人IR受付explicit企業をコード順に1417/145A/1721の保存資料経路から点検している。

次に埋める具体不足は、価格の意味と鮮度方針、著者条件と会社KPIの集計単位/範囲、利用できる外部予測の銘柄/FY/作者/版と許諾、評価倍率/率と回答が変える入力の根拠である。調達候補の存在から契約やデータ受領を推定せず、同義previewや汎用コードを追加して不足を埋めない。新しい正式資料が保存された場合は既存の条件IDへ照合し、公開で解けた問いは除く。

ホクトの[正式通期資料の追補](../ir-case-studies-2026-10-15/1379/annual-cashflow-followup/README.md)は一覧scriptとrobotsの2GETで終了した。配信先の禁止規則に従いfeed/PDFへのHTTPは未実行で、財務本文の取得や実台帳への追加はない。再試行・別経路の探索は続けない。

[確率を置かない判断の範囲点検](../ir-decision-scope-2026-10-15/README.md)は完了した。既存previewで公開事実の支持・反証候補・未解決を記録でき、新しい汎用APIは不要。親も[24引用と9合成対照の再現を確認](../ir-decision-scope-2026-10-15/root-recheck.json)した。現コードの買い条件や必要な価格・方針を緩めず、研究の部分手順と数値投資判断を区別する。現時点で実企業の予測・金融入力の採用成功は主張しない。

確率なしで可能な事業条件・反証・個別scenarioの比較と、期待値/IR情報価値の計算や現在のbuy条件を分けて確認する。均等確率や平均で補完せず、現行の未設定による保留を解除しない。必要な入力・方針が外部根拠や明示採用で揃うなら既存機能を使い、現契約との具体的な不一致が判明した場合にだけ別の仕様検討へ切り出す。

135Aは未一致の会計範囲を示す原行/注記と独立予測の必要を分け、会社に将来利益やROCの保証を求めない。1379はpreviewの次回公表指標、年度ラベルの不整合、配当の基準日/支払と投資時点を継続点検する。保存済みthesisと質問の目的・許可する変更範囲・価格/方針等の必要な条件が揃うまでは、研究上の問いをIR質問登録へ移さない。数値pathの変更を全質問へ必須とはしない。
