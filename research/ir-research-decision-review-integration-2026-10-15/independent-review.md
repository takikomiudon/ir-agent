# 保存研究の判断保存：最終独立レビュー

独立に再現した**P2 2件は修正され、再確認済み**。残る対応必須指摘は0です。最終freezeに対する独立63チェックは不一致0。[JSON記録](independent-review.json)に修正前再現、行番号、最小修正、個別結果、最終SHAと限界を保存しました。

1. source価格と一致する0/負値が、position/policy不足でunresolved保存される問題。供給済みpriceを先に正・有限検査し、partial quoteを含む21組合せで新行0を確認しました。旧pureの早期return順序は保持しています。
2. metadata等のoptional既定欄を省略したvalid raw sourceでKeyErrorとなる問題。raw snapshot/hash/receiptとvalidated計算用copyを分離し、有効なraw marketはbuy_reviewを計算、raw IRのmetadata欠損は明示holdとなることを確認しました。原raw/SHA/receiptは不変です。

抽出前後の旧pure22ケースと旧IR plan3ケースは、返却object又は例外type/messageが完全一致しました。不足policy/未知positionの優先順、価格0/負、時点/原典/precision/pathを含みます。追加の7組合せ、temp旧schema移行2件、root memory demoも通過しました。rawreply初期unclear→public source互換、固定policy・最新CAS、全DAG/公開性/来歴、明示position、再送、current holdの境界は実装/32新testsとも照合しています。

実DB・network・コード編集は0。memory/tempの架空fixtureだけで検証しました。親の全suiteはまだ未実行として引き渡します。これは金融入力・判断の正しさや投資成績の認定ではありません。
