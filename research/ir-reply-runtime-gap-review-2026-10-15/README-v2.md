# IR返信の適用前に依存資料の公開性を確認する修正

**公開性が保留された情報に依存する場合、新しい返信による金融入力の更新前に止める。全1,332テスト成功、独立レビューの阻害所見0。** 実企業のモデルや投資方針を採用した変更ではない。

| 確認した不足 | 修正後 |
|---|---|
| 旧返信の公開性を訂正しても、次の質問の事前確認・送信済み記録が通る | 契約付き質問の確認を`needs_review`とし、新しい送信済み記録を拒否する |
| 新しい返信の金融入力を保存した後で、依存側の訂正を見てactionだけ保留する | source・仮説を追加する前に保留し、新返信自身の公開性は保持する |
| 取り込み時から公開性不明のIR原典を、訂正履歴のないlegacy経路で使える | 全原典を調べ、元snapshot由来の保留を返信訂正の保留とは別fieldへ残す |

派生資料の第二親と共有DAG、現在既知の訂正を申告過去日時で回避しない処理、無関係訂正の不波及、明示再評価、再送とrollbackを確認した。IR原典の分類欠損は保留し、通常の公開開示の分類省略は通す。元snapshotを書き換えず、元public資料への訂正を再確認する場合と、元資料自体が不明な場合を区別する。運用と再評価は[追補](../../docs/reply-dependency-holds.md)を参照。

修正前の[RG01再現](README.md)、[最初の実装](implementation.json)、[全1,324件](parent-full-suite.json)、[初回独立レビュー](independent-implementation-review.md)を保持した。そこで判明した隣接不足を[別の修正前証拠](adjacent-source-gap-before.json)へ固定し、[v2実装](implementation-v2.json)と[修正後の合成確認](adjacent-source-gap-recheck.json)を追加した。

最終checkpointは[全1,332件・37.939秒](parent-full-suite-v2.json)。新規20件と既存関連91件の対象確認も成功した。[独立v2レビュー](independent-implementation-review-v2.md)は3件の合成probeと、[完全なコードコピー5件](source-snapshots-v2.json)のSHA一致を確認。親も現コードとコピーのbyte一致、実DBのSHA不変を確認した。初回レビューには全文copyを残せなかった限界があるため、最終レビューは先に保存したコピーへ固定した。

変更は`harness.py`と`decision_lifecycle.py`、新しいテスト。原文、旧仮説、再現証跡は不変。実DBは98資料・仮説/質問/返信/実方針0のまま。新GET、実IR送信、発注は0。guard通過は、回答の意味、財務入力や将来予測、投資成績を検証したことにはならない。適用済みモデルの自動巻戻しも行わない。
