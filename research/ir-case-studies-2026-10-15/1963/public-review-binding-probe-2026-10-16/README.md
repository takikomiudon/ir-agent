# 保存済み実資料による参照固定の確認

日揮HDの公開Q&Aと短信注記を使い、新しい公開情報レビューの参照確認APIを台帳の一時コピーで点検した。2原典のnative JSON SHA・逐語引用・確認範囲・時点と、全原典の実保存来歴を照合し、未解決理由は0だった。[結果](binding-check.json)には意味確認が別途必要で、回答の不存在を認証しないことも残る。

[入力](binding-subject.json)は参照点検用で、質問ID・質問文・回答分岐・評価額を持たない。正式質問として登録できるJSONではなく、質問の必要性・IR価値・売買判断・送信準備の確認ではない。

実DBはmode=ro/query_onlyで開き、一時バックアップだけをStoreへ渡した。コピーの全行・schemaと実DB SHAが不変であることを[検証](validation.json)した。新しい質問・job・金融入力・送信は0。[script](probe_once.py)はこの時点のDB SHAを要求する有限記録であり、後の台帳での再実行を指示しない。

[機能の受入](../../../ir-public-information-review-binding-integration-2026-10-16/parent-acceptance.json)と[原6資料の実保存](../../../ir-1963-initial-with-facts-intake-2026-10-16/parent-acceptance.json)は別の記録として保持する。
