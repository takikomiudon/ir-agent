# Tweedy内部者投資資料：紹介頁まで取得、PDFはフォーム導線で停止

**指定資料の紹介頁は取得できたが、同hostの直接PDFリンクはなく、数値選別・売却/見直し条件・保有期間を埋められなかった。** フォーム送信やJSによる追加探索は行わず、2GETで有限終了した。資料本文の非存在や恒久的な取得不可を認定した結果ではない。

既存 `ir-tweedy-managed-author-source-2026-10-15/literature-extraction.json` の`links[44]`が保持する実hrefを使った。旧scope外だった未試行hostを別資料1件の対象にしたもので、既存保留hostの迂回ではない。AGENTS・ローカルIR skill・hold v6の10 exact hostを照合し、`insights.tweedy.com`は索引に含まれなかった。

## 取得した範囲

1. `https://insights.tweedy.com/robots.txt`：HTTP200、165bytes。wildcardの禁止対象はpreview・preferences等で、指定本文pathは既存parser上許可。raw SHA `ea8e85a2b5420fc4539c4997c85a6821500c4e4a4ebb410b0c926f648fddb5ce`。
2. `https://insights.tweedy.com/insider-investment-factor`：HTTP200、27,028bytes。raw SHA `a7f8456bdb6a9557c862d924a0371b705f0d78e1ed77270f5ac08639589c3220`。完全entityのiteration終了観測は2026-10-15T22:19:21.261281+00:00、collectorの処理完了は同21.266372+00:00。

新しく凍結した`Fetcher(raw_directory=...)`を使用し、元HTMLをdecode/可視抽出前に保存した。rawはrequestsが返した完全response entityであり、wire・gzip転送bytesではない。既存`retrieved_at`は開始側の記録として残し、本文完了と混同しない。公表日時は未確認でnull、DB初回保存日時も認定していない。環境policyはunrestricted/state unknownの観測で、適用済みとは主張しない。通常proxy・CA・TLS検証・固定UAを維持した。

本文には、PDF受領のためフォームを完成するよう求める見出しがある。保存rawからも同hostの直接PDF URLを確認できなかった。別hostのフォームCRS・旧ADVというPDFリンク2件は対象の論文ではなく、取得していない。最大3GETの残り1GETを別探索に使わず停止した。redirect・retry・別host取得・JS・フォーム送信は0。

## 得られた説明と未取得の判断条件

| 区分・原位置 | 確認できた説明 | 残る不足 |
|---|---|---|
| 著者の研究方向：紹介本文の冒頭 | 内部者購入や自己株買いと、割安さを示す評価指標を組み合わせる研究を紹介する。 | 買付額・件数・相対比率・評価倍率・観測期間等の具体的選別閾値、実運用への採用条件は未確認。 |
| 他者研究と独自研究：紹介文の研究説明 | 既知の学術研究を再検討し、12,000件超の内部者購入・26年間の独自知見も扱うと同社が説明する。 | 原PDF未取得のため、研究方法・対象市場・サンプル・費用・結果・再現性は未確認。26年を個々の投資の保有期間にしない。 |
| 売却・見直し・保有期間：紹介範囲 | 数値ルールとして借りられる条件は得られなかった。 | 未指定を0や固定期間で補わず、他のTweedy一般方針を当該研究の規則として移植しない。 |
| 日本株への適合：同紹介範囲 | 日本株の具体的な適用証拠を確認していない。 | 一般的な海外投資リスク記述を、日本の内部者開示や自己株買いへの適用実証にしない。 |

原文の短い説明・条件付き表現・フォーム導線は[quotes.json](quotes.json)へ合計47英語語で限定保存し、可視textのSHA/offsetと元HTML SHAを付けた。引用は可視抽出の空白正規化後の位置であり、元HTMLの同一offsetだとはしない。このREADMEでは引用を重複掲載しない。本文原本を読めていないため、同社の紹介上の主張と、検証された研究結果を区別する。

原応答は[capture.json](capture.json)と`raw/`、抽出本文は`text/`、実リンクの確認は[literal-route-check.json](literal-route-check.json)、制約・原文位置と結論は[guard.json](guard.json)・[review.json](review.json)、SHA/byte数の照合は[validation.json](validation.json)に保存した。今後の取得やフォーム送信を予約したものではない。

新GETは2、実DB操作・policy/index採用・source code変更・外部連絡は0。閾値不足は未解決として残し、この別資料の調達を終了する。
