# 現在表示と保有状態：既知の限定として終了

**新しい契約違反/P2は今回確認せず。** `current_decision_view`は情報訂正・最新thesis版・価格鮮度を点検する一方、現在保有又はposition宣言receiptを参照しない。従って他のholdがなければ旧reviewの候補が表示に残り得るが、それを現在の保有/来歴の確認済みと読まない。

[現在表示の文書](../../docs/current-price-views.md)は、`fresh`が価格時間条件だけであり、保有等を再検証した意味ではないと明記する。保存raw/context/resultを歴史として残すこと自体は意図した境界。現在の保有は別途確認する。既知の限定viewを、今回すべての現在資格を保証する契約へ拡張しない。

既存のhistorical-position testも過去のreview/再送を保持する意図を示すが、旧runtimeを注入しているため、後の実際の現在時刻でpositionが変わった場合の再現証拠とはしない。[review.json](review.json)に未変更表示file・docs・既存testの6参照SHAと6逐語anchorを残した。

主修正のfreeze前はruntime probe禁止という指示を守り、最終的に追加probe不要で終了した。probe/engine実行/GET/実DB/code/旧ファイル変更/fullsuiteは0。別担当のposition receipt主修正を検証済みとせず、新gate又はcurrentview変更も提案しない。
