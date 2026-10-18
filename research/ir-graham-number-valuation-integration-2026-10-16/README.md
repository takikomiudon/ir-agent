# 外部著者のGraham Number式を既存評価器へ接続

maxgfr/crible固定commitの式 `sqrt(22.5 × EPS × BVPS)` を、既存value/model-inputs経路で選べる `graham_number` として独立実装した。入力は正の有限なeps_jpy/book_value_per_share_jpyだけ。原著Grahamの全適格条件、個社予測・購入/退出方針の採用ではない。[仕様](../../docs/graham-number-valuation-spec.md)と[未記入template](../../examples/valuation-graham-number.template.json)を参照。

変更したproduction codeはvaluation.pyだけで、新method以外の有効入力の出力を維持した。新15テストと既存関連82を担当が確認し、旧5method24ケースのJSON出力・代表4例外の同値も確認。独立レビューのF1（価格/確率/混在入力による資源guard迂回）を修正し、Grahamを含む場合の総精度をContext作成前に制限した。独立再確認で追加の必須指摘なし。

rootの[全体テスト](full-suite-metadata.json)は2026-10-16 09:48:53～09:49:32UTC、1,573件成功（unittest38.890秒、process39.459秒）。当該コード/テストSHAは実行前後同一。旧版全bytesはbefore-valuation.py、全ログはfull-suite.logに保持する。

1975の直接表示358.13/1965.51から3,979.69円を再現できる。株式basis・対象年度・実績/予想の意味確認と、出典付き価格・保有・金融policyによる判断は別の段階。入力由来の監査は市場価格を補わず実行でき、内部の数値検証用価格1を相場観測へ転用しない。
