# 収集保留索引 v5：9 exact host

[holds-v5.json](holds-v5.json)は[v4](holds-v4.json)の8entryを完全保持し、`jpx-jquants.com`の有限停止を1件追加した。新しい公開Web収集の前はv5を参照する。自動runtime guardを追加したものではない。

[公式仕様の棚卸し](../ir-jquants-financial-summary-semantics-2026-10-15/README.md)で、保存済literalからfresh robotsを1GETした。HTTP202、完全entity 0bytes、完了2026-10-15T20:53:14.285495UTC。空ファイルのSHAは`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。本文引用は存在せず、captureのstatus/byte数/完了と原byteを根拠にする。prepared UAは確認したがwire独立確認ではない。

現在の収集guardで規則を確認できなかったため、その有限経路を停止した。HTTP失敗・wildcard/AI禁止を確認した意味ではなく、HTTP2xx一般のrobots解釈、Cloud設定やレート制限の原因も判定していない。仕様本文/APIへのGETは0、再試行・UA変更・別host探索・診断0。財務列の意味・単位は未確認のまま。

この保留はexact hostの公開文書経路に限り、別hostの`api.jquants.com`、SDK利用権、投資適格性や過去資料へ広げない。旧8hostと理由はそのまま。[検証記録](validation-v5.json)で保持と原byte/capture対応を確認した。索引作成自体はGET・実DB操作・金融条件変更0。
