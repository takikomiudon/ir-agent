# 1975 Graham Numberの入力仕様（計算前）

maintainer定義と保存コードから、EPSは報告NI/期中平均、BVPSは株主持分/期末株数（例外時平均fallback）という別の分母を確認した。NIはNetIncome/NetIncomeCommonStockholders、持分はStockholdersEquity/CommonStockEquityであり、日本基準の親会社帰属利益・連結純資産合計と無条件に同一視しない。

既定はannualだが関数は年次/TTMを強制せず、Q1を年率化しない。正EPSかつ正BVPSのguardがあり、実装上はGraham Number自体も価格非None block内にある。価格なし純式の入力仕様確認とupstream実行可否を区別する。

保存1975原本にはQ1 EPSと当時の会社forecast EPS、Q1平均株数、BPS比較の所在があるが、同一FY2026/3の年間実績EPS/年間平均株数・普通株持分のbindingは未完了。forecast357.49の代用、Q1年率化、理論価格/合否は作らない。未読説明p11のBPS行は所在検索だけ。

次のliteralは公式library保存captureのactualリンク `/ir/library/summary` 1本。年次PDFそのもののhrefはまだ確認できず推測しない。[仕様と根拠](specification.json)に列候補・逐語quote/line/SHAと実linkを固定した。Graham原典の独立認定ではなくmaintainerによる説明。GET・DB・旧file・共有code変更0。
