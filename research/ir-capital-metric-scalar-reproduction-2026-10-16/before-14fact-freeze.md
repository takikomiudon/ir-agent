# 5988：公開式の独立scalar算術（入力freeze待ち）

2026-10-16。14fact bundleの親からのfreeze通知を待っている。未完成の入力を使用せず、まだ計算・実会社数値出力は0。既読canonical/extrasの式とMIT本文参照、projectの将来ROC_new境界を[preparation.json](preparation.json)へSHA固定した。

対象は2期それぞれのPBT＋支払利息、流動資産−流動負債、税前ROC、原表示税額/PBTとmaintainer clipによるNOPATだけ。reported operating incomeは比較表示に留め、独自の営業利益版ROCは作らない。7概念×2期の出典・ID・pointer・期・範囲・JPY単位を原本から生成されたimmutable bundleへ厳格結合する。concept名は実bundle schemaを読んでから確定する。

独立scriptは標準ライブラリDecimalのみ、precision80・ROUND_HALF_EVEN、比の分子分母とdecimal近似を保持する予定。upstream pandas runtimeの再現ではない。税clipはmaintainerの金融的conventionで、元会計税率・会社の正常税率・Greenblatt本人方式・将来ROC_newとは別。p94の比率は丸め前内部額が不明なので、表示額比と厳密一致を要求しない。

ROIC/EY/valuation/rankは不足を列挙してnullのまま。GET、product src/CLI/DB、pip・外部依存、upstreamコードimport/実行、他担当file編集は0。実会社数値を使う後段も研究再記述に限定し、モデル金融入力/financepolicyへの採用はfalseを維持する。
