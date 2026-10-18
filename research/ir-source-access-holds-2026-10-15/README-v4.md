# 収集保留索引 v4：8 exact host

[holds-v4.json](holds-v4.json)は[v3](holds-v3.json)の旧7entryをJSON値として完全保持し、`data.swcms.net`を1件追加した。新しい原本収集の前はv4を参照する。これは運用上の索引であり、自動runtime guardを設置したものではない。

7157の正式年次短信への明示リンクは会社IR索引で確認できたが、実配信hostの`https://data.swcms.net/robots.txt`への固定UAの1GETが**HTTP403・完全本文199 bytes**を返した。本文完了は2026-10-15T20:23:10.963399UTC、原entity SHAは`5b13fb5957b84ef7bb9d0b6cd509c947ff6a37d67efdac2b896ddd3b908aad10`。[取得記録](../ir-case-studies-2026-10-15/7157/annual-original-followup/capture.json)と原バイト、prepared UA、開始/headers/完了時刻を結び付けた。wire headerの独立確認ではない。

403 HTMLはrobots規則として解析せず、規則/access未確認による収集保留とした。wildcard禁止やAI固有拒否を確認した意味ではなく、クラウド設定・レート制限等の原因も判定していない。年次PDFへのGETは0、再試行・UA変更・redirect・別host/転載/JS経由の探索は0。[有限経路の終了記録](../ir-case-studies-2026-10-15/7157/annual-original-followup/route-outcome.json)を保持する。

旧7hostは`contents.xj-storage.jp`、`ssl4.eir-parts.net`、`web.fisco.jp`、`sharedresearch.jp`、`www.toyo.co.jp`、`www.xj-storage.jp`、`www.investors.com`で、理由を統合せず保持した。今回の停止を他hostや銘柄の投資除外へ広げない。過去に保存した同host資料があっても、その公開性や分類を遡及変更しない。ドメインの利用許可を未確認規則の免除と扱わず、同じ停止経路をworkerが自動で再開しない。

[validation-v4.json](validation-v4.json)は旧7entryの保持、原capture/raw/quote/UA/時計の対応、本文GET0を確認した。索引作成自体は新GET・DB書込み・金融判断0。[独立点検](independent-recheck-v4.md)は58項目・指摘0で、旧7entry保持・新403・active指示の旧bytearchive・実DB124資料不変を照合した。旧7raw全体の意味を再レビューした結果ではない。
