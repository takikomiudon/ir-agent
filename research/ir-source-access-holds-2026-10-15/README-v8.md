# 保存済み収集保留 v8：12 exact host

[holds-v8.json](holds-v8.json)は[v7の11entry](holds-v7.json)を全fieldのJSON値として完全保持し、`www.journals.uchicago.edu`を1件だけ追加した。旧v7以前の索引/READMEは不変。取得運用上の保留記録で、自動runtime guardの設置ではない。

[掲載誌の有限調査](../ir-private-investor-meetings-journal-source-2026-10-15/README.md)はrobots1GETでHTTP200・完全820bytesを受信し、GPTBot向けの個別 `Disallow: /` を確認した。元raw SHAは `821d8bfdedf96d4b1f86db2590302e0c743d1ca6fe782c4b38ecc6eca27f275c`。規則引用は原UTF8の文字/byte offset773–803（0始まり・end除外）。完全entityのiteration終了観測は `2026-10-15T23:27:25.818422+00:00`、HTTP呼出し終了は `2026-10-15T23:27:25.828400+00:00`、申告retrieved_atは開始側として別に保持する。

現設定UA `ir-agent-public-research/0.1` とwildcardの選択DOI URLに対するliteral can_fetchはともにtrue、GPTBotはfalse。個別groupを現UAのliteral一致やwildcard全面禁止へ読み替えず、AI個別禁止を受けた既存project運用保留として止めた。robots403・規則未知・掲載本文の禁止/403ではない。掲載頁/fulltext GETは0で、無料/会員/本文の内容・不存在・個人IRへの効果も未確認。

対象はこのexact hostのみで、他subdomainや全uchicago.eduへ広げず、投資除外・永久禁止にしない。同じGETの再試行・UA変更・別経路・ブラウザ/JS回避を行わず、過去資料を遡及変更しない。旧11hostのwildcard禁止、403規則未知、202空本文、AI個別運用保留の区別はすべて保持する。

[validation-v8.json](validation-v8.json)で旧11entry保持、全12capture/raw SHA/bytes、新引用offsetと完了時刻、producer原証拠不変を照合した。4共有ファイルの編集前完全bytesは`before-active-v8/`、変更はactive link/件数/最新版entry説明だけで、他段落は完全不変。正確な差分は`active-instructions-v8.diff`と[active-instructions-update-v8.json](active-instructions-update-v8.json)。新GET・DB・コード変更0、ongoing-workとroot README/他producerは変更していない。
