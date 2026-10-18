# 保存済み収集保留 v6：10 exact host

[holds-v6.json](holds-v6.json)は[v5の9entry](holds-v5.json)をJSON値として完全保持し、`www.aaii.com`を1件追加した。v5以前も不変。これは調査時点の取得運用の記録で、runtimeの自動guardを設置したものではない。

AAIIの[新規調査](../ir-aaii-author-screen-discovery-2026-10-15/README.md)では、2026-10-15T22:02:52.624186+00:00にrobots.txtをHTTP403・完全963bytesとして受信した。有効なrobots規則は確認できず、記事・criteria本文の取得は0。HTTP状態とraw/captureの対応は[検証記録](validation-v6.json)に保存した。原文からDisallowを読んだ結果でも、記事本文のHTTP403でもない。レート制限・Cloud環境・永久禁止という原因は認定しない。

対象は`www.aaii.com`のexact hostだけで、他subdomain・発行者の全著作・投資対象企業へ広げない。過去の保存資料も遡及変更しない。同じrobots/本文の再試行、UA変更、別hostや転載による迂回、ブラウザ・JavaScriptによる回避は行わない。

旧9hostは`contents.xj-storage.jp`、`ssl4.eir-parts.net`、`web.fisco.jp`、`sharedresearch.jp`、`www.toyo.co.jp`、`www.xj-storage.jp`、`www.investors.com`、`data.swcms.net`、`jpx-jquants.com`。wildcard禁止、AI個別禁止を受けた保留、403で規則不明、202・完全空本文での有限停止を同じ理由にまとめない。`jpx-jquants.com`の記録を`api.jquants.com`へ広げない。

この索引更新は新GET・実DB操作0。更新前のAGENTS/skill/roles/data-sources本文は`before-active-v6/`へ完全byteで保存した。担当は取得前にこの版と個別経路の後続記録を確認し、未解決を未試行へ戻さない。
