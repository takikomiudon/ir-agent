# 日付のみの決算予定監視

全1,230テスト成功（35.163秒）。[全件ログ](tests.log)、[独立確認](independent-recheck.json)、[コードSHA](source-code-sha256.json)を保存した。

Anthropic catalyst-calendarの手順を、保存した原文・時点・分類と結ぶ最小read-only報告へ適応。ニッスイの予定3件を11月の表示でも保持し、期間内2件/外1件を分ける。時刻とtimezoneが未確認なので全件due:null、実施not_established、意味のレビュー未了を維持する。

[実予定の結果要約](actual-monitor-summary.json)を保存。別担当がメモリfixtureと実DBのmode=ro/query_onlyで確認し、未来/後着/非公開/未分類の第二親、現在の分類保留、共有DAG、外側transactionとDB SHA不変を確認した。予定変更・取消・実施・結果の採用、厳密時刻、差分、自動jobは未実装。新しい資料・会社を取得する操作とは別で、この機能でDB・仮説・質問・送信・注文は変更していない。
