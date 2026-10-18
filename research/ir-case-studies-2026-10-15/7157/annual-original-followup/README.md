# 年次原本：配信hostのrobots403で停止

会社IR索引に明示された年次PDF1件だけを対象とし、実配信host`data.swcms.net`のfresh robotsを1GETした。**HTTP403・完全本文199 bytes**が返り、[capture](capture.json)と原entityを保存した。robots規則として解釈できないHTMLであり、[guard](guard.json)はproceed:false。**PDFへのGETは0**、残り1GETは使わずにこの経路を閉じた。

原entity SHAは`5b13fb5957b84ef7bb9d0b6cd509c947ff6a37d67efdac2b896ddd3b908aad10`、完了時刻2026-10-15T20:23:10.963399UTC。固定UAのprepared headerと時刻を記録するが、wire headerを独立確認したものではない。本文403・wildcard禁止・クラウド設定やレート制限の原因を確認したとは扱わない。

[終了記録](route-outcome.json)と[中央8host保留v4](../../../ir-source-access-holds-2026-10-15/README-v4.md)へ停止を引き継いだ。retry・UA変更・redirect・別host/転載/JS経由の探索は0。過去の同host資料の公開性・分類を遡及変更せず、この収集保留を銘柄の投資除外へ広げない。

配当可能額・契約負債・IFRS17/CSM・原本内の会計bridgeは未確認。今回のcapturesはfile-onlyで、実DBは124資料のまま、金融thesis/質問/モデル採用/送信/注文0。必要な数字を補ったり、原本未取得だけで新たなIR質問を作ったりしない。[独立点検](../../../ir-source-access-holds-2026-10-15/independent-recheck-v4.md)で取得・UA/時計・phase・原本GET0とDB不変を照合済み。
