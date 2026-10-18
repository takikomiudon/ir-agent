# ローツェ6323 短信の実取り込み

2026-10-15 15:54:47.678750 UTCに原source1件を初回DB保存し、同じattempt 1で分類完了。[実行結果](actual-import.json)、[完了job](completed-job.json)、[backup記録](execution-start.json)を保持した。表紙2026年10月8日・HTTP本文完了・今回のDB初回保存は別の時刻である。

旧101source/100分類/全1,819社metadataは不変。source-only ingestで会社statusや保有申告を更新せず、ID・元JSON・snapshot SHAも不変。実DBは102資料（公開101・市場1）、公開資料あり16社・財務内容あり15社。[coverage summary](coverage-summary.json)は分類の存在を示し、評価・投資適格性の認定ではない。

[新case登録v14](../../../ir-research-monitoring-integration-2026-10-15/6323-registration-v14.json)はDB0を確認して原source初回保存前に作った。ただしPDFはその前にfile保存/読取済みであり、blind/4月事前の予測評価ではない。[v14検出](../../../ir-research-monitoring-integration-2026-10-15/actual-run-validation-v14.json)は新保存/論点未確認1件を表示し、intake分類だけで著者論点を比較済みにしないことを確認した。

外部著者3論点と会社一次資料の意味比較は別task。会社中間期実績と通期会社予想、受注前年比水準と増減率、棚卸増と供給安定の因果は分ける。金融thesis・モデル・価格条件・IR送信・注文は0。

[実行手順](import-reviewed-source.py)は先行の成功手順を対象/記録先だけ変更して再利用した一度のoperator実行。計測attempt37/events74/receipt37は全分類leaseの累積で、全工程の分析能力には換算しない。
