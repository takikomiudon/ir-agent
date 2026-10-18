# 税注記6値を実台帳へ保存・分類

2026-10-15 22:35:13.773122 UTCに、新しい派生source1件（税率差異表2値・DTA残高4値）を実保存し、分類job1件を完了した。実台帳は151source（公開150・市場1）、分類150、完了job74、attempt71/event142/request receipt71。実金融入力・policy・正式IR・native caseは変更していない。

[一時DB検証](shadow-preflight.json)では、実台帳のコピーへ同じsource-only ingestとintake/claim/completeを適用し、全旧rowを保持した。実適用の[固定入力](actual-preapply.json)、[段階記録](actual-stage.jsonl)、[完了と実firstsave receipt](actual-completion.json)を保持する。source/availability/classification/job/attempt/request receipt各1とevent2だけの追加を確認。元source snapshot、旧取得日時、実績/予測区分、未採用状態を変えていない。各APIの通常transactionを使い、全工程が単一transactionとは主張しない。

100.77%はratio1.0077のまま、評価性引当の負号も保持した。初回保存は今回の実時刻で、原有報の公表/取得時刻へ遡らせない。元の構造化[受入記録](../parent-acceptance.json)はfile-onlyだった時点のものとして保持する。接続は正常税率・NOL利用・予測・金融モデルへの採用ではない。新GET・本体code変更・実送信・注文は0。
