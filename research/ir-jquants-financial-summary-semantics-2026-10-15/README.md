J-Quants V2財務summaryの公式意味仕様を有限に棚卸しし、公開資料経路はrobots1GETで停止した。SDK2.8には選択列の名前とAPI引数の説明があるが、NP/EPS/FEPS/NC系の金額単位・予想期・連結範囲を確定する保存済み公式response仕様は今回の検索範囲では未特定。列名から意味を補っていない。

SDK constants.py:357に直接のliteral仕様URL `https://jpx-jquants.com/ja/spec/fin-summary` がある。docs/data-sources.md:51のdata-spec/rate-limitsとともに在庫へ保持した。仕様本文はいずれも未取得・未読。111列全体への意味解析には広げていない。

`https://jpx-jquants.com/robots.txt` は2026-10-15T20:53:14.285495+00:00にHTTP202・完全本文0bytes（text/html）で終了した。200規則本文でも既存404分岐でもないので規則未確認として停止。403やwildcard禁止、Cloud設定障害やレート制限と判定していない。固定UA `Codex-IR-Research/0.1` はprepared requestとcaptureで確認し、wire headerの独立確認とは区別する。

[route-outcome.json](route-outcome.json)に正確URL/開始・完了/UA/停止範囲、[capture.json](capture.json)と[原entity](raw/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855)へ結び付けた。新GET1、spec/API本文0、再試行・UA変更・別host探索・診断0、未使用2GET。exacthostの公開資料保留をAPIの別hostへ一般化しない。

[棚卸し](inventory.json)にはSDK/READMEの引用・SHA・列名だけを保持。[validation](validation.json)は記録の一致を確認するもので、意味・単位・モデル採用を承認しない。src/tests/実DB/共有docs/中央holds変更0。
