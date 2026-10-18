# 点検済みノート資料の実取り込み

2026-10-15 15:14 UTCにノート付き説明資料1件を原sourceのまま取り込み、同じattempt 1で分類完了。[実行結果](actual-import.json)と[初回保存receiptを含む結果](completed-job.json)、[実行前backup記録](execution-start.json)を保持した。初回DB保存は15:14:18.934724 UTCで、14:51の取得完了や原PDFの表紙日付とは別である。

実DBは101資料（公開100・市場1）・分類100・完了intake39。計測attempt36/events72/要求receipt36は分類leaseのみ。source来歴はlegacy28/trusted73。旧100source・旧99分類・全1,819社metadataは不変。sourceのID・JSON・snapshot SHAも不変で、会社metadataや金融仮説を取り込んでいない。

分類完了後に[更新前manifest v12で監視](monitor-before-review-v12.json)し、6754の新保存1件と論点未確認1件を検出した。結果は7case中、要手動確認1・scope内追加triggerなし6・根拠不足0。[検出照合](monitor-trigger-validation.json)ではDB main SHA不変、job追加0を確認した。分類完了を著者論点レビュー済みにはしていない。

資料の[限定4頁読取と独立点検](../notes-cost-explanation-followup/independent-recheck.md)、[著者論点への追補](../author-condition-followup/notes-observation-addendum.md)と[追加4頁の独立点検](../notes-additional-cost-search/independent-recheck.md)を[監視v13](../../../ir-research-monitoring-integration-2026-10-15/README-v13.md)へ接続した。会社全体の棚卸資産CF表示をPQA利益要因へ帰属させない。

[実行用手順](import-reviewed-source.py)は一度だけ実行済み。再実行や要求IDの変更で新leaseを作らない。新GET・金融モデル採用・IR送信・注文は0。
