# 明示された決算短信索引の有限確認

保存FAQのliteral「決算短信」リンクから、fresh IR-host robotsと当該indexを各1GETした。ともに200・完全本文で、[capture](capture.json)に原バイトと取得時刻を保持する。UA固定、TLS/proxy/CAを維持し、retry・redirect・JS/API推測は0。

indexのlinks[39]に、2026年3月期の年次短信と対応する`決算短信〔IFRS〕（連結）`の明示PDFリンクを確認した。[原hrefと周辺HTML](route-outcome.json)を保持し、ファイル名から公表時刻や財務内容を作っていない。テンプレートの0KB PDFや月次契約速報は選んでいない。

実配信hostは会社IR hostとは別の`data.swcms.net`だったため、当初のsame-host・3GET以内のphaseでは2GET使用・1GET未使用で終了した。新しい配信hostのrobotsと指定原本に限る[別の有限phase](../annual-original-followup/README.md)を設けたが、robots403により本文は未取得。元indexや旧失敗URLの再取得・別経路探索はしていない。

このindex/captureは経路証跡としてfile-onlyで保持する。取得した年次本文や新しい数値入力として実DB・金融モデルへ登録していない。FAQの会計/配当基準の記録は維持し、金融bridgeは未解決。相場や投資条件は変更していない。
