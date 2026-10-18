# 未カバー3社の公開資料を実台帳へ接続

個人IR受付の過去明示候補から未カバー順で選んだ1861・1866・1870の8資料を、保存済みbundleの全objectのまま一度だけ登録し、3社のintake分類を完了した。投資順位や現在の送信適格性の確認ではない。

| 会社 | 保存した資料 | 財務本文 | 公開確認の結果 |
|---|---|---|---|
| [熊谷組1861](../ir-case-studies-2026-10-15/1861/initial-public-review-2026-10-16/README.md) | root・静的決算一覧2件 | 0 | 事業説明を確認。一覧の動的内容を取得済みにしない。 |
| [北野建設1866](../ir-case-studies-2026-10-15/1866/initial-public-review-2026-10-16/README.md) | root・一覧・短信3件 | 1 | Q1実績、通期会社予想の据置、分割調整の注記を限定確認。 |
| [矢作建設工業1870](../ir-case-studies-2026-10-15/1870/initial-public-review-2026-10-16/README.md) | root・短信・説明3件 | 2 | 営業利益と特別利益、旧新予想、譲渡と連結範囲を分けた。 |

PDFは全文text版だけを実登録した。旧partial版はfile-only履歴で保持し、元取得時刻・URL・rawSHAを変えず、全旧部分本文が全文のexact prefixであることを照合した。全文抽出は全冊の意味読解ではない。1870の[追加3頁](../ir-case-studies-2026-10-15/1870/profit-bridge-review-2026-10-16/parent-full-source-acceptance.json)も後段で実sourceへ引用位置を直接結合した。

実firstsaveは `2026-10-16T01:07:53.577025+00:00`。原取得・公表日・全文抽出時刻と区別する。分類はbusiness3/index2/financial_statement2/earnings_presentation1、financial_content true3/false5。金融モデル入力を検証・採用した結果ではない。

[実行結果](actual-completion.json)で旧全行を保持し、source/availability/classification各+8、job/attempt/requestreceipt各+3、event+6だけを確認した。既存case・全金融記録・会社/保有状態は不変。原source objectも全件一致した。成功したmutatorの再送はない。

完了時は161資料（公開160・市場1）、公開資料あり26社・財務内容あり23社、分類160、全91job完了、attempt88/event176/requestreceipt88、native16case/32版/99既読。main SHA `2f564bee9fce54684e7f4a6214d433d6248f2b86182e273838d29ddfaddacb6a`。後続の監視case登録・数値の正規化接続は別の段階である。
