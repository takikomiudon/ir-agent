# 定性レビューjobの独立コードレビュー

原実装を担当していない別agentが、case/CAS、sourceの時点・公開性・SHA、prior_review、lease世代と会社排他、原子的完了、再送、limit、worker表示、金融処理との境界を読みました。根拠のある指摘は **P2 1件**で、修正とfocused検証まで完了しました。

`QR-REQUEUE-01`: ファイルの一時変更によりclaimでsupersededになったjobは、同じbyteへ復旧しても同一triggerが既存と判定され、監視が再開しませんでした。[修正前の再現](finding-before-fix.json)はmemory DBと一時fileだけで確認しています。

修正はqualitative queueだけです。supersededの履歴を参照した決定的な署名で、新しい時点のpacketを作ります。`supersedes_job_id`は直前のjobを示し、旧packet・job・attemptは編集しません。pending／leased／completedは引き続き既存として扱います。case fileやsource分類の保留が残る間は起票しません。新しい起票にも通常のlimitを適用します。

新しい回帰4件と既存の定性／prior／workerテストを合わせ、**30件・0.256秒・成功**でした。[ログ](focused-tests.log)と[SHA付きレビュー記録](review.json)を保存しています。rootがこの修正後の全suiteを別途実行します。以前の1,421件成功は修正前の履歴であり、このagentが全suiteを再実行した結果ではありません。

実DBの読み書き、ネットGET、IR送信、注文は0です。投資の妥当性・全文読了・金融の意味・著者の独立性・成績の検証ではありません。共用README/docsは編集していません。

親による修正後の[全件検証](parent-full-suite.json)も完了した。**1,425件・36.665秒で成功**し、実DB122資料のSHAは前後で一致した。[受入](parent-acceptance.json)はこの修正と検証に限り、投資成績や金融入力の意味の認定ではない。
