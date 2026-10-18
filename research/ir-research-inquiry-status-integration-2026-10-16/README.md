既存statusへの研究inquiry可視化

実運用の研究draftが旧金融questions集計に現れないため、Harness.statusだけを拡張。research_inquiriesを状態別dict、research_inquiry_repliesとresearch_inquiry_reviewsを独立件数として追加。旧keys/意味は保持し、inbox/判断/金融処理/Store/CLI/schemaは変更していない。

編集前harness全文/SHAはharness-before.pyとbefore.json、差分はstatus.diff。専用synthetic 2 testsがPASS（0.013s）。空DBの新3集計と旧全keys、draft→返信待ち→回答済・別draft並存・返信1/レビュー2版を検証し、金融質問/返信/evaluationと旧inboxへの混入なしを確認。

実台帳や実Storeを開いていない。rootがdiff/対象test・fullsuiteを受入後、実台帳のstatusをreadbackする。優先度/公開性の認証/金融gateは追加0。共有docs編集0。


2026-10-16 14:14 UTCの[root受入](parent-acceptance.json)で、全1,614テストPASS（unittest38.900秒、runner39.439秒）と7runtime pins不変を確認した。[実CLI status](actual-status.stdout.json)は `research_inquiries:{draft:3}`、研究返信0・レビュー0、旧金融 `questions:{}` を別に返し、実DB main SHAは `4783600606ed244710f0a0febf7a03b5b177980ad35df12a6791d64eec0227c1` のまま。inbox/金融gate/送信は変更0。上段の「実台帳や実Storeを開いていない」はproducer実装時の範囲で、このrootによる後続readbackとは区別する。今回の文書更新ではDB接続・テスト再実行をしていない。
