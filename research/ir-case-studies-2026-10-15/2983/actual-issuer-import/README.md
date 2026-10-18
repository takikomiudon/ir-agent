# 2983 会社原本の取り込み準備

会社原本3資料のsource objectを変更せずに保存し、短信・説明資料・修正通知の分類入力を準備した。準備時は独立確認待ちで未登録だった（`preparation.json`は108資料の時点）。その後、独立確認の指摘0を確認して2026-10-15 17:21 UTCに登録し、1件の分類jobを完了した。3資料のtrusted first-saveは17:21:13.605908 UTC。実DBは111資料（公開110・市場1）、分類110、job44・attempt41・event82・要求receipt41、legacy28/trusted83。旧source・分類・会社metadataは不変。`actual-import.json`と`coverage-summary.json`が実行後の記録。

分類の完了は、会社説明の因果の認証、著者予測の採用、金融モデル・投資方針・IR質問の作成を意味しない。HTTP本文受信時刻、書面の表示日、今後の実DB初回保存時刻を分ける。実行時にはバックアップ、旧資料不変、追加sourceのみのjob、実保存receiptを確認する。
