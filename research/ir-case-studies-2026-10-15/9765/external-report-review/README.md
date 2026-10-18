# 9765 オオバ：SESSA配信の会社案内は確認、本文は転送先未取得

会社の保存「Full Report」リンクをSHA/anchorと照合し、robotsと会社notice本文を取得しました。noticeは**2026年9月28日にSESSAパートナーズ株式会社から配信**と明記しています。著者企業は表題だけで推定せず、この会社本文から確認しました。noticeの表示日/配信日であり、レポート表紙の日付や個人著者は未確認です。

noticeの実PDFhrefはHTTPでした。そのままHTTP robots→実HTTP PDFを要求した結果、いずれも302でHTTPSへ転送され、**4GET上限に達して終了**しました。HTTP robotsのLocationは最初に取得済みのHTTPS robotsそのもので、追加GETせず保存原文を再利用して許可を確認しています。PDFのLocationは保存するだけで未要求、HTTPSへ先回り変更もせず自動redirectも追っていません。

| 実要求 | 結果 |
|---|---|
| HTTPS会社robots | 200・対象notice/レポートpath許可 |
| 保存された会社notice URL | 200・SESSA配信と実href確認 |
| HTTP会社robots | 302・Locationは保存済みHTTPS robots |
| 実HTTPレポートhref | 302・HTTPS PDF先へは予算上未到達 |

PDF本文は取得していません。個人著者・報酬/委託契約・作者独自EPSと会社計画の別・目標価格・評価式/公正倍率・期間・反証条件は**unknown**で、不在とは判断しません。この案内だけで著者の投資判断条件を借りられるとも認定しません。

`source-bundle.json`は会社notice本文1件のみ、canonical jp:9765、companies/theses空、financial_inputs_verified=false。robots/302ページを金融本文にしません。source.retrieved_atは当該HTTP本文完了時刻、公表時刻nullを維持。raw/text/captureSHA・2逐語引用・原リンクprovenance・旧input不変を保存しました。metadataパスは`research/ir-case-studies-2026-10-15`基準、新providerのgeneric verifier未対応はunknownです。

PDF上限16MiB、共有2秒lock、retry/JS/自動redirect0。既知停止/AI禁止host・別経路/URL推測・DB/code/旧資料変更・新予測/閾値/モデル採用・IR草案/送信は0。この4GETで完了します。
