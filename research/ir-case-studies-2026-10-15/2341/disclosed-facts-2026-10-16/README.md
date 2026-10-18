# 2341：公表12表示値の構造化（file-only）

受入済み原短信1sourceを全object無改変で保持し、既存normalize_disclosed_facts version1で派生1sourceを生成した。実績はp8千円の当中間PL4値とp1基本EPS、予想はp1の10月8日時点会社FYguide5値、配当は当中間DPSと年間予想合計の2値のみ。数値thesis/採用forecast/投資評価ではない。

| kind / concept | 原表示 | 原単位 | 保存値 / unit |
| --- | ---: | --- | --- |
| reported_fact / revenue | 2,441,162 | 千円 | 2441162000 JPY |
| reported_fact / reported_operating_income | 151,425 | 千円 | 151425000 JPY |
| reported_fact / reported_ordinary_income_or_loss | 156,453 | 千円 | 156453000 JPY |
| reported_fact / net_income_attributable_to_parent_owners | 115,644 | 千円 | 115644000 JPY |
| reported_fact / reported_interim_basic_earnings_per_share | 6.32 | 円 | 6.32 JPY-per-share |
| issuer_guidance / revenue | 5,024 | 百万円 | 5024000000 JPY |
| issuer_guidance / reported_operating_income | 280 | 百万円 | 280000000 JPY |
| issuer_guidance / reported_ordinary_income_or_loss | 277 | 百万円 | 277000000 JPY |
| issuer_guidance / net_income_attributable_to_parent_owners | 167 | 百万円 | 167000000 JPY |
| issuer_guidance / issuer_forecast_earnings_per_share | 9.18 | 円 | 9.18 JPY-per-share |
| reported_fact / reported_interim_dividend_per_share | 0.00 | 円 | 0 JPY-per-share |
| issuer_guidance / annual_dividend_per_share | 5.00 | 円 | 5.00 JPY-per-share |

中間連結実績は2026-03-01〜08-31、会社FYguideは2026-03-01〜2027-02-28。会計は日本基準、表紙百万円未満切捨てと詳細PL千円を区別し、OP/経常/親NIを混ぜない。EPSは基本欄6.32で、希薄化後dashを0にしない。円銭という見出しの単一小数tokenを既存円→JPY-per-shareで処理し、複合円・銭新formatは使っていない。DPSは正確period両端/recorddate/会計・連結basisをnull保持し、中間0を支払実施にせず、年間5.00は右端合計欄だけを取得した。既存v1は正数5.00の表記も保持する（Decimal値5と同値）。

p6のApr9→Oct7親NI139→167/EPS7.63→9.18は特益26百万円「等」による会社修正説明、表紙の直近修正無とは比較時点が違う。実績特益26,207千円と予想増28百万円を税後1対1調整・正常OP/CFへ足戻ししない。株式の期末発行/自己株/期中平均・信託控除、CFの売却益調整と投資売却収入、期中消却実施と後発消却予定は、受入済み3成果の7引用をfile/SHA/JSONpointer/原文spanで参照するだけ。長文文脈を各factへ再コピーせず、新読解/消却完了・現在分母/EPS効果の認証は0。

原公表日10月8日day precision/published_at null、原取得06:14:37.993737UTC、今回抽出review06:28:15.155239、生成06:28:30.498133を分離する。実DB初回保存はこの作業で行っていない。

normalization-input/quotes/source-referenceに原表示・全basis/tokenのUnicode/UTF8spanと原nativeSHAを固定。generation.logはprimary1回。reproduction.jsonはsame-now wholebundle/ID完全一致、標準source再現matched_supplied、独立Decimal12件/84文脈参照・旧13files不変を確認した。初回検証scriptの期待文字列が5へ末尾ゼロ除去を仮定し停止したが、既存v1の正値5.00を保持する期待へ訂正した。before/validation-correctionを保存し、bundle/input/金融値/コードは変更していない。明示wholebundle replay2回・標準reproducer1回、primary1回。

新GET/DB接続/Store/API/共有code/旧facts・索引変更/金融採用/新forecast/IR0。12点でfreezeしrootレビュー待ち。実台帳や索引への接続は別作業。
