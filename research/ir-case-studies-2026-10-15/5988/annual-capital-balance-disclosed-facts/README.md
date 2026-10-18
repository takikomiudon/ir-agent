# 5988：年次残高8表示値の構造化

保存済み会社有報の直接表示8値を既存 `normalize_disclosed_facts` でreported_factとして構造化した。原会計名を保ち、百万円からJPYへの明示換算だけを行う。canonical equity/debtの認定、成分足算・平均化・ROIC/EV・金融採用は0。実DBへ保存せず、親レビュー待ちでfreezeする。

| 表示科目 | 左 / 右の原token（百万円） | 期の契約 |
|---|---|---|
| 現金及び現金同等物 | 30,236 / 22,773 | p83のCF期末残高対応注記：2025-03-31 / 2026-03-31 |
| 普通株式に係る期末の純資産額 | 90,446 / 64,854 | p103の直接期末日：2025-03-31 / 2026-03-31 |
| 資産合計 | 105,464 / 101,415 | p63の直接BS期末日：2025-03-31 / 2026-03-31 |
| 借入金等明細表・合計 | 615 / 24,575 | p104の当期首残高 / 当期末残高。正確な暦日未確認、as_of_date/end_date/start_dateはnull |

p104のperiodにはopening_balance/closing_balanceというboundary_roleと原列ラベルを保持した。p104に書かれていないBS前期末日をend_dateへ補完していない。同reportの当連結会計年度2025-04-01〜2026-03-31は、旧14factのp65損益表見出しをsource/文字/UTF8 offset付きで参照する別の `scope.report_fiscal_year_context` に置く。この年度と明細表を関連付けるのはreviewer assertionであり、当期首/当期末の精確暦日bindingではない。後段への暦変換も今回行わない。

普通株式対応純資産を純資産合計や株主資本合計へ改名せず、BPS×株数や純資産−NCIから逆算しない。C&Eを現金及び預金へ同一視しない。借入金等合計615/24,575は表示値をそのまま換算し、成分合計や丸めで補正しない。ダッシュの0補完はない。百万円表示の端数処理・未表示精度は未確定で、JPY換算値を未丸めの正確な経済額とはしない。選択表の会計基準ラベルは未確認のnullを残す。

元sourceは `annual-capital-disclosed-facts/normalization-input.json` `/source` の全objectをそのまま再利用。原primary IDは `case-public:5d5a98a7770af91318e9bb24fd4bdac483b20cb5fc96a79f58474dbd77f57365`。metadata、本文、公表/取得時刻を変更せず、元sourceを再取得していない。原著者は会社、抽出review担当はCodexとして別記した。派生IDは `disclosed-facts:cba31cbae3e2b2d78353862ceb382b11f3d92efc2195eb944dc0871209e49bd5`。派生bundle生成時刻/派生source retrieved_atは2026-10-16T00:25:58.909474+00:00であり、実DB first-saveではない。

input/bundleとquotesに単位・期・列・行を含む同一原全文substring、文字/UTF8 byte offset、物理/印字頁、既読120dpi画像SHAを保存。p83/p103は受入済み分母discovery、p63/p104は受入済み6頁discoveryの画像/読解を参照した。`reproduce_disclosed_fact_source` はreproduced、原content matched、原snapshot matched_supplied_snapshot。同じ生成時刻でnormalizerを再実行したbundleも完全一致した。

旧索引107factと別途の年次14fact、計121factに対しIDと会社/concept/期間の重複0を確認。期間比較ではas_of/endとstart、boundary_roleを使い、日付nullは原ラベルも保持した。旧BPS・税・14fact・discovery・各索引等141既存fileのSHA不変。新GET、実DB接続、source/schema/production code/共有文書/索引の変更、数値thesis・IR質問の作成は0。full suiteは再実行していない。

`audit-source-paths.json` は再現可能なbundle内value pathの参照表で、金融モデルへの割当requestではない。全financial_inputs_verified=false、meaning_review_required=true、companies/theses空を維持する。8値の所在・引用・単位換算が再現できても、著者式への対応や金融意味の認定をengineが完了したことにはならない。
