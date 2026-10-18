# 290A 初回公表資料の有限確認

指定hostのrobotsへ1回だけ接続を試みたところ、TLS証明書チェーン検証に失敗し、HTTP応答本文を受信できませんでした。再試行なしの条件に従って停止しました。一覧・PDFは未取得です。

- 指定URL: https://www.synspective.com:443/jp/ir/results/
- 取得前確認: 中央holds-v3の7 exact hostsに対象hostなし。既存の別host表記トップページの503・circuit-breaker記録は保持し、再試行していません。
- URLの根拠: 保存snapshotの `$.links[42]` にあるresolved URLと「決算短信」のlabel。元hrefや原HTMLは未保存であり、復元したとは扱いません。
- 接続試行: robots 1、HTTP応答0、一覧0、PDF0。UAはCodex-IR-Research/0.1、timeout40秒、response上限10MiB、redirect追跡なし、retryなし。TLS検証を無効にせず、代替host・URLguess・JS/APIも使っていません。

`capture.json` に実開始・終了とエラー、`route-quotes.json` に保存経路引用位置とSHA、`sourcebundle.json` にsources空の取得結果、`review.json` に未確認範囲を記録しました。raw配下の空ファイルは失敗処理が作ったローカルmarkerであり、受信した原文ではありません。text配下は未取得状況の説明だけです。

取得完了時刻・会社公表日時/精度・会社原典の初回保存来歴は確認できていません。今回のローカル証跡保存時計を原典取得完了や過去のfirst-saveへ付け替えていません。

IwaiNO335p5の「10機前後で営業黒字想定」は上位指示で与えられた外部著者仮説で、会社実績ではありません。衛星稼働・打上げ/運用・OP・補助金の営業外区分に関する会社資料は読めていないため、支持/反証・予測・数値採用は行っていません。実DB・コード・監視・旧ファイル変更・IR送信は0です。

この失敗だけから企業側の拒否、robots禁止、投資不適格又は指定一覧の不存在は判断できません。
