# 5988資本残高8項目：実保存と比較の完了

[接続準備](README.md)後、rootが派生1資料を一度だけ保存し、intake分類を完了した。実初回保存は `2026-10-16T00:42:45.749872+00:00`。元会社有報の取得時刻、構造化bundleの生成時刻、コピーDBでの保存とは区別する。

[保存後の照合](root-actual-verification.json)で旧全行を保持し、source/availability/classification/job/attempt/request receiptが各+1、event+2だけだった。初回完了receiptのmain SHAはWAL反映前の物理mainを表す。記録を残し、checkpoint前後で論理全行が同一のままmainへ反映されたことを別receiptに保存した。保存・分類を再送していない。

[既存論点への比較](../qualitative-review/parent-acceptance.json)は反証レビュー10項目・指摘0を経て完了。5988 case v4、source/case unchanged、管理日2027-01-16 Asia/Tokyoを維持し、再queueは0。完了後のroot検証でattempt行の書換えを誤って期待した件は[訂正記録](../qualitative-review/postcompletion-check-correction.json)に残し、prequeue backup全行と期待差分で再照合した。完了処理の再送はない。

[索引v27](../../../disclosed-fact-index-v27.json)の8追加値は元の表示・単位・期末・借入金等の当期首/末roleとnull暦日を維持する。[条件付き歴史ROIC](../../../../ir-historical-roic-role-reproduction-2026-10-16/parent-acceptance.json)は別の研究結果で、会社公表値・金融モデル・将来ROC・IR回答分岐へは採用していない。

完了時の実台帳は153資料・全88job完了、native16case/32版/99既読。main SHAは `312b051258311f125aee1cfd2a5680cca839f29338a366234f5349e1c5a8a09f`。この件数は当時のsnapshotで、後続会社の保存数とは区別する。
