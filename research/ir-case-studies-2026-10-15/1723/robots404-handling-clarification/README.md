# 1723 robots404の扱い

取得済み404 HTMLをrobots規則や明示許可として扱わず、Python3.12標準実装と既存141Aのmissing-robots処理を適用する。初回停止記録は保持し、robots再GET0、既知失敗URLの再試行0。未試行の既知公式IR資料室1URLだけを初回取得する。403・5xx・TLS・明示AI制限や中央7holdは変更しない。

[根拠](clarification.json)は標準ライブラリの実装逐語引用/位置/全fileSHA、既存projectcase、今回の保存404raw/captureを保持する。この確認自体のGET/DB/金融採用は0。
