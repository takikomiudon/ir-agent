# 135A 期末発行済普通株式数1件の入力準備

記録: 2026-10-15T15:30:24.133560+00:00。既存正式中間短信のp2・原source・保存引用/画像・独立点検を再利用し、`normalization-input.json` 1factを準備した。**API/CLI normalizeはまだ実行していない**。親の受入と別途実行指示を待つ段階で、normalized-bundle/derivedsourceは作っていない。

対象は2026-08-31（2027年２月期中間期）の「期末発行済株式数 (自己株式を含む)」普通株式10,256,000株だけ。raw単位「株」→canonical `shares`、明示乗数1での期待表示値10256000を候補対応表に記したが、これは実行済み出力ではない。期中平均株式数・希薄化後分母や自己株控除後net株数とは別であり、自己株の「－」を0にしない。現在評価分母/株主価値帰属との適合も未採用。

元sourceIDは `case-public:4b9aaae627aa90731140aa648b9c8bf60be1767accaab06041ac23dc5f6955fb`。原snapshot/引用/Unicode半開offset/頁2/画像SHAを保持し、原legacy取得時刻とpublished_at nullは不変。review時刻は今回の準備時計で、派生取得時刻・DB first-saveは作っていない。金額の百万円未満切捨て注記を株数へ適用しない。

[model-input-map-addendum-candidate.json](model-input-map-addendum-candidate.json) は既存Damodaran9入力仕様への補助対応で、全9採用path/値とscenario/価格/確率/閾値/IR条件/売買はnull。cash2factsを再抽出せず旧bundleへ追加していない。

GET・DB/Store・API/CLI normalize・コード/テスト・原source/旧facts/index/monitor変更・金融/IR採用は0。原PDF再抽出/再描画はせず、先行独立確認を再利用した。[preparation-validation.json](preparation-validation.json) にexact引用と参照SHAの準備検証を保存する。入力と補助候補を固定し、次段の実行で必要な成果は別ファイルへ追加する。
