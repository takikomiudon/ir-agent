# 明示株数単位の換算を追加

保存済み公表値のnormalizerへ、shares・株・千株・万株・百万株からcanonical sharesへの5組を追加した。既存の表と原典再現を再利用し、評価器や意味判定は変更していない。

**全1,380テスト成功（40.582秒）**。[全件結果](parent-full-suite.json)・[親の受入](parent-acceptance.json)を保存した。新8件を含む対象41件と[限定独立レビュー](independent-review.md)で、係数・欠損/0・符号/小数・異次元・改変時の保留・旧出力を確認した。旧52例のhash/IDと億円4区分の完全出力は不変。

旧億円testの全表一致条件は、旧14組の金額/比率の保持と、新testによる旧14＋新5だけの全表条件へ分担した。元の52例の全assertを保持し、[変更前全文と範囲](additional-test-scope-before.json)を残した。4変更fileの前後全文も保持する。

発行済（自己株含む）・自己株控除後・期中平均・希薄化後は別の定義。単位変換で評価用株数を選択せず、意味は未確認・金融入力未採用のままである。旧ID・記録・schema/versionは変更していない。検証中の実DB101sourceとmain SHAも不変。

[対応単位と境界](../../docs/disclosed-share-units.md)・[設計](../ir-disclosed-share-unit-design-2026-10-15/design.md)・[実装](implementation.md)を参照。
