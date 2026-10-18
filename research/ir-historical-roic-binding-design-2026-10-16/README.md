# 5988歴史ROICの入力対応：計算前の限定設計

2026-10-16T00:31:42.070541+00:00 時点の保存物だけを読んだ。**strictな日付行によるC.average再現では、Dの暦日がnullのため2026FYのROICまで閉じない。一方、期首/期末roleを使う明示した研究用mappingなら、日付nullを保持した条件付きscalar算術は設計可能。両者を同じ再現とは呼ばない。** 8fact意味独立reviewは本設計で未受領、金融binding・計算実行・DB・GET・product/元file編集0。

既読C＝canonical.py、E＝extras.py（固定commit00944e3b8fe853d8b82050f5ffb0f8c0fc6fb1b7）。C:102–127の平均は前年**日付行**を300–430日窓でshiftして足す。E:67–69は平均(E+D−C)と平均総資産を使い、資本>0かつ平均資本≥10%平均総資産を要求する。opening/closingという説明だけから、Dの当期首を前年日付行へ無言で書き換えない。税clip0〜50%/10%guardはmaintainerのconventionで、会社の正常税やGreenblatt本人の規則ではない。

## 元8factの役割・日付・引用根拠

金額は原factのJPY値をそのまま転記し、平均やROICは計算していない。Eは**仮の**canonical total_equity、Dは仮total_debt、Cは仮cash_and_equivalents、Aは仮total_assets。以下のroleはFY2026研究の対応候補で、元factのperiodを変更しない。

| 原fact ID | role候補 | 原factの実期日 | JPY表示換算値 | 原文位置/列とfact位置 |
|---|---|---|---|---|
| `5988-reported-20250331-cash-and-cash-equivalents-annual-20260618` | C: 前期末→FY2026期首参照候補 | 2025-03-31 | 30236000000 | p83「現金及び現金同等物」/前連結会計年度、decoded `/facts/0` |
| `5988-reported-20260331-cash-and-cash-equivalents-annual-20260618` | C: FY2026期末 | 2026-03-31 | 22773000000 | p83「現金及び現金同等物」/当連結会計年度、decoded `/facts/1` |
| `5988-reported-20250331-net-assets-for-common-shares-annual-20260618` | E: 前期末→FY2026期首参照候補 | 2025-03-31 | 90446000000 | p103「普通株式に係る期末の純資産額（百万円）」/前連結会計年度、decoded `/facts/2` |
| `5988-reported-20260331-net-assets-for-common-shares-annual-20260618` | E: FY2026期末 | 2026-03-31 | 64854000000 | p103「普通株式に係る期末の純資産額（百万円）」/当連結会計年度、decoded `/facts/3` |
| `5988-reported-20250331-total-assets-annual-20260618` | A: 前期末→FY2026期首参照候補 | 2025-03-31 | 105464000000 | p63「資産合計」/前連結会計年度、decoded `/facts/4` |
| `5988-reported-20260331-total-assets-annual-20260618` | A: FY2026期末 | 2026-03-31 | 101415000000 | p63「資産合計」/当連結会計年度、decoded `/facts/5` |
| `5988-reported-annual-20260618-borrowings-schedule-total-opening_balance` | D: 原表opening_balance | null（roleのみ） | 615000000 | p104「合計」/当期首残高、decoded `/facts/6` |
| `5988-reported-annual-20260618-borrowings-schedule-total-closing_balance` | D: 原表closing_balance | null（roleのみ） | 24575000000 | p104「合計」/当期末残高、decoded `/facts/7` |

pointerはbundle `/sources/1/content`をJSON parseした**後**の位置。各factのbasis_quoteは同一原sourceの保存text offsetへ一致することを確認した。引用内の値と列の経済的適合まで独立認証した意味ではない。8factは旧14factと**元source object全体が同じ**：ID `case-public:5d5a98a7770af91318e9bb24fd4bdac483b20cb5fc96a79f58474dbd77f57365`、compact-sorted object SHA `382ca26face7fb8747748035adfb5fef47ceddcef47009a75b8cbe1e360b915a`、content SHA `a9acbc3544e789cae8369d1e45f02747928fadda584c1839780a12a55fe4bd01`。

p104のDは原表で当期首/当期末ラベルのみ。start/end/as_of/exact_calendar_date_bindingはnull。scope.report_fiscal_year_contextは別p65の2025-04-01〜2026-03-31のP/L見出しを参照し、**scheduleへの関連付けはreviewer assertion、日付そのものではない**と明示している。その既存主張を原p104の直接印字と呼ばない。2025-04-01という年度開始日をDの観測日や2025-03-31へ変換しない。

## strictに保てるもの／条件付きmapping／未充足

| 区分 | 現時点の最小範囲・次の条件 |
|---|---|
| 1. 現契約のままstrictに保てる | 8表示値、原行名、6つの明示期末日、Dの2roleとnull、会社/連結/JPYの構造、旧14factの研究用PBT/利息/税の再現範囲。Aの2期末は平均用日付候補が明示されているが、ここでは平均を実行しない。**D日付を要するcompleteなC.average入力はまだない**ためstrict日付版ROICはnull。 |
| 2. 明示した研究用mappingなら条件付き | 2025-03-31のE/C/AをFY2026のopeningに対応させる**前期末→期首参照**と、p104のopening/closingがp65の当FYに属するという別の**報告年度role対応**を根拠付きで採用した場合、暦日を付けずに両roleの資本を別々に置き平均するscalar研究は可能。C.averageのdated-row/window経路のstrict再現にはしない。E/D/C各行の範囲対応と意味独立reviewの受入が必要。 |
| 3. 原典/意味確認が必要 | E/D/C/Aの範囲、同一年度との関係と期首接続、税/利益との会計主体対応。strict日付版を目指すならDに暦日を与える直接の根拠または明示した日付対応記録が別途必要で、nullを事実に昇格させない。まず取得済み原表・文脈と進行中reviewで足りるか確認し、根拠がなければnull停止。新GETや無制限な探索を予定しない。 |

条件付きscalarの式案（実行0）を記号で固定する：

- 期首参照資本* ＝ E前期末 ＋ D原表opening − C前期末。
- 期末参照資本* ＝ E当期末 ＋ D原表closing − C当期末。
- 平均資本* ＝ (期首参照資本*＋期末参照資本*)÷2。平均総資産* ＝ (A前期末＋A当期末)÷2。
- 条件付き歴史ROIC* ＝ 旧14factの**FY2026用maintainer clip後NOPAT**÷平均資本*。正資本/10%guardも同じmaintainer条件として表示する。

*は研究仮対応を含む記号。新日付・欠損0・新税率を足さず元8factを編集しない。価格/株数を使うEYは本task対象外。

各行の意味差は残す。EはBPS基礎の**普通株式に係る期末純資産額**で、同表は純資産合計と非支配持分控除を別表示する。provider StockholdersEquity/CommonStockEquityとの同値、OCI/クラス株/連結利益との範囲を未確認のままtotal_equityへ認証しない。Dは**リース債務も並ぶ借入金等明細表の合計**で、provider TotalDebtの範囲と同じとは未認定。内訳足算・ダッシュ0化・丸め修正はしない。CはCF注記の**現金及び現金同等物**で、BSの現金及び預金にすり替えず、現金控除の経済的妥当性も別。Aは**資産合計**の直接行だが、会計基準null同士を適合確認と呼ばない。scope.canonical_financial_field_bindingも全件nullのまま。

## 次に行う有限手順と停止条件

1. 進行中の8fact独立意味reviewを受け取り、行/列/期末とp104 role/FY文脈の不一致があれば元factを変えず保留する。
2. 親が研究用mappingの有無を決める。E/D/Cの範囲・p104年度role・前期末→期首参照を明示して採用できる場合だけ、**別の研究計算**で22fact（旧14＋新8）をSHA/factID/二段pointerへ固定し、role版算術として出力する。strict日付版の既存14scriptへDの日付を暗黙補完しない。
3. 根拠/採用がなければ2026ROICは理由付きnullで止める。2025ROICは2024のopening一式が不足し、Dの当期首を2025FY用closingへ無条件流用できないので、今回の22factだけではnullを維持する。歴史研究値をfuture ROC_new、将来税、IR後の倍率/予測、financepolicyへ転用しない。

新しい頁探索や、日付のための別paper探索は行わない。8fact独立reviewと親の別途計算許可を待つ。新規計算・追加抽出やscript実装は行っていない。source行の存在、研究mapping、会計適合認証、金融採用は別の段階である。この1枚で有限設計を終了する。

## 読取pin（全byte SHA-256）

| file | SHA-256 |
|---|---|
| [research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/normalized-bundle.json](../../research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/normalized-bundle.json) | `642534fa52fa27c14be6f5a0943b36483a1fa66c65eaabb1a09100af68242eab` |
| [research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/normalization-input.json](../../research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/normalization-input.json) | `71002c614fa979857ccc72a52a6dfdaabe45dd5bf7a90f1c793d2d1c238640c4` |
| [research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/source-reference.json](../../research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/source-reference.json) | `8e5a929cdf467ac590624be1dd8a3af6254b59f5b1a93faa8fad25dda01dced3` |
| [research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/validation.json](../../research/ir-case-studies-2026-10-15/5988/annual-capital-balance-disclosed-facts/validation.json) | `19ed1b2d855f2f2cefc601fe9b3a19c96bc042d7de916c1c5f9cb5c9fee65ea3` |
| [research/ir-case-studies-2026-10-15/5988/annual-capital-disclosed-facts/normalized-bundle.json](../../research/ir-case-studies-2026-10-15/5988/annual-capital-disclosed-facts/normalized-bundle.json) | `4c7723e2667252489997eaa2abaf99862c6c87b3d1fd02cef4053a890ec9683e` |
| [research/ir-capital-metric-scalar-reproduction-2026-10-16/reproduce.py](../../research/ir-capital-metric-scalar-reproduction-2026-10-16/reproduce.py) | `b32b66b23b35a5dbfe2743f87f5e17eab7c6f99815a493a3161f8451f993e2ef` |
| [research/ir-capital-metric-scalar-reproduction-2026-10-16/reproduction.stdout.json](../../research/ir-capital-metric-scalar-reproduction-2026-10-16/reproduction.stdout.json) | `a528deaf2889c276496018828be3560ca21f4b36bf8a61ad53b02c4fcca217a7` |
| [research/ir-transparent-metric-core-review-2026-10-15/upstream-canonical.py](../../research/ir-transparent-metric-core-review-2026-10-15/upstream-canonical.py) | `2933aa8ff2ac2407a56293efcd0bcd7c923c41ec2250fe69bea88ec499ff9ede` |
| [research/ir-transparent-metric-core-review-2026-10-15/upstream-extras.py](../../research/ir-transparent-metric-core-review-2026-10-15/upstream-extras.py) | `3038a489679aa163f5a4d930ac7cb4dcf320d72a62122ccd45e9d9242b593631` |
