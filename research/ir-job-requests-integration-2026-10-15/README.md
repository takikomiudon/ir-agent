# 要求ID付きclaim/renewの接続

全1,111テスト成功（36.360秒）。[AWS/Googleの保存原典](../idempotent-job-requests-2026-10-15/README.md)に基づき、再送ID、意味のあるpayload比較、変更とreceiptの原子的保存を採用した。SQLiteスキーマやnull応答固定は本プロジェクトへの適応。[利用契約](../../docs/idempotent-job-requests.md)。

- 同namespace+IDの再送は元応答を返し、別会社のclaim・renew再適用・イベント追加をしない。
- 元の応答と現在の有効性を分離し、期限切れ/再確保/完了で元処理の実行権を作り直さない。
- 待機前の時刻で期限を作らないよう、通常時計はwriter取得後に読む。
- 34対象テストに並行connection、rollback、CLI、時計位置を含む。別担当の独立再現でも、DB dump/total_changesの不変を確認した。

[全件ログ](tests.log)、[対象ログ](target-tests.log)、[独立再確認](independent-recheck.json)、[コードSHA](source-code-sha256.json)、[実台帳のスキーマ変更](actual-receipt-schema.json)、[要約](summary.json)を保持する。実DBには空のtableだけを追加し、過去の要求や計測開始を捏造していない。28source原JSONと既存28件のlegacy存在観測は不変。

同じreceiptを受け取った複数プロセスの分析重複、認証、TTL削除、黙った古いbackupへの復元検出は未実装。実IR送信・注文0件。
