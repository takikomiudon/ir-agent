既存statusへの研究inquiry可視化

実運用の研究draftが旧金融questions集計に現れないため、Harness.statusだけを拡張。research_inquiriesを状態別dict、research_inquiry_repliesとresearch_inquiry_reviewsを独立件数として追加。旧keys/意味は保持し、inbox/判断/金融処理/Store/CLI/schemaは変更していない。

編集前harness全文/SHAはharness-before.pyとbefore.json、差分はstatus.diff。専用synthetic 2 testsがPASS（0.013s）。空DBの新3集計と旧全keys、draft→返信待ち→回答済・別draft並存・返信1/レビュー2版を検証し、金融質問/返信/evaluationと旧inboxへの混入なしを確認。

実台帳や実Storeを開いていない。rootがdiff/対象test・fullsuiteを受入後、実台帳のstatusをreadbackする。優先度/公開性の認証/金融gateは追加0。共有docs編集0。
