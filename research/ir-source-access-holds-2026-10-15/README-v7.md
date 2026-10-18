# 保存済み収集保留 v7：11 exact host

[holds-v7.json](holds-v7.json)は[v6の10entry](holds-v6.json)を全fieldのJSON値として完全保持し、`alphaarchitect.com`を1件だけ追加した。旧v6以前の索引・READMEも不変。この記録は取得運用の有限停止で、runtime自動guardの設置ではない。

Alpha Architectの[調査](../ir-alpha-architect-author-policy-discovery-2026-10-15/README.md)は、fresh `https://alphaarchitect.com/robots.txt` の1GETでHTTP403・完全6,025bytesを受信した。完全entity受信のローカル観測時刻は `2026-10-15T22:57:36.654662+00:00`。homepage・戦略本文GETは0で終了した。有効robots規則は未確認であり、Disallowを解析した結果、記事本文のHTTP403、レート制限・Cloud等の原因診断、永久禁止や投資除外ではない。方法が存在しない/非公開という結論でもない。

追加対象は`alphaarchitect.com`のexact hostのみで、`www.alphaarchitect.com`等へ広げない。再試行・UA/TLS変更・別host/転載・JavaScript/ブラウザによる回避を行わず、過去保存資料を遡及変更しない。元capture/rawのSHA・6,025bytes・HTTP状態・完了時刻を[validation-v7.json](validation-v7.json)に固定した。保存bytesはrequestsのresponse entityで、gzipのwire転送bytesや独立wire header認証ではない。Content-Lengthは保存headerになくnullのまま。

旧10hostは`contents.xj-storage.jp`、`ssl4.eir-parts.net`、`web.fisco.jp`、`sharedresearch.jp`、`www.toyo.co.jp`、`www.xj-storage.jp`、`www.investors.com`、`data.swcms.net`、`jpx-jquants.com`、`www.aaii.com`。wildcard禁止、AI個別禁止を受けた運用保留、403規則未確認、202・完全空本文の有限停止を別の理由として維持する。`jpx-jquants.com`から`api.jquants.com`へも広げない。

今回の索引更新で新GET・実DB・sourcecode変更0。4共有ファイルは編集前完全bytesを`before-active-v7/`に保存し、active link/件数とrolesの今回増分説明だけ更新した。他の著者比較v6・DD質問準備・raw保存の本文、ongoing-work/caseREADMEは変更していない。4fileの正確な差分と保存SHAは[active-instructions-update-v7.json](active-instructions-update-v7.json)および`active-instructions-v7.diff`を参照する。
