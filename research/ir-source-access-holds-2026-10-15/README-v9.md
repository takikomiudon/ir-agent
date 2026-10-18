# 保存済み収集保留 v9：13 exact host

[holds-v9.json](holds-v9.json)はv8の旧12entryを全fieldのJSON値として保持し、`query1.finance.yahoo.com`を1件追加した。旧版と過去captureは不変。

公開robotsの完全200/26Bにはwildcardの`Disallow: /`があり、2026-10-16T16:12:45.048076UTCに取得完了した。原文は[robots本文](query1-robots-2026-10-16.txt)、取得情報は[公開robots記録](query1-robots-capture-2026-10-16.json)。本文の実LFと文字列escapeを分け、現helperで指定chart URLへの全確認UAがfalseとなった。chart・価格・銘柄情報の取得は0、追加の再試行/UA変更/query2/ミラー回避は行わない。

exact hostの収集保留であり、企業の投資除外や全Yahooの恒久禁止へ拡張しない。独立した正当なデータ源の利用条件は別に確認し、この停止の回避に使わない。新しいruntime guardは追加していない。市場データ原文は取得しておらず、公表robots26Bだけをこの索引へ転記した。
