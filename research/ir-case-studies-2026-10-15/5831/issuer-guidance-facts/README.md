# 5831 会社通期予想の限定構造化

保存済みのしずおかフィナンシャルグループ公式「2027年3月期 第1四半期決算短信」物理p1から、通期の親会社株主に帰属する当期純利益 **115,000百万円** と1株当たり当期純利益 **217.91円** の2項目だけを既存 `normalize_disclosed_facts` で構造化した。百万円からJPYへの表示単位換算後は115,000,000,000 JPY。未表示端数を復元した金額ではない。EPSは会社直接表示値を保持し、NIから計算していない。

対象期間は原文に明記された **2026-04-01〜2027-03-31**、日本基準・連結。原文日付は2026-08-06で、公表時刻は不明のため `published_at: null` と保存済みmetadataを保持する。抽出担当と予想主体の会社を分け、`issuer_guidance` とし、実績や外部著者の独自予想へ変換しない。

[入力](normalization-input.json)・[正規化bundle](normalized-bundle.json)・[照合記録](validation.json)に、同じ原典source、原数値token、表の行列、逐語引用の文字/UTF8 byte offset、既存p1画像とSHAを保存した。公式短信1sourceだけが原典であり、株数分母、潜在株式、分割調整の未確認条件、配当列、将来利益、価格・倍率、規制再投資、FCFEは補完しない。原本と実DBのsource全fieldはread-onlyで一致を確認した。

[開示fact index v21](../../disclosed-fact-index-v21.json)はv20の23entry・95factの全fieldを保持し、今回の1entry・2factだけを追記した（計24entry・97fact、18社・21会社/原典pair）。過去indexを変更していない。

正規化bundleは原典と別IDの派生資料を含むファイル成果物であり、実DBへの派生資料登録やモデル採用はしていない。原本の変更、新GET、実DB書込み、外部送信、発注は0。引用・単位演算の再現成功と、投資モデルの入力採用は別で、`financial_inputs_verified: false` を維持する。[主担当の受入](parent-acceptance.json)も完了し、p1画像・単一原典のAPI再現・実DB不変と旧95factの保持を確認した。
