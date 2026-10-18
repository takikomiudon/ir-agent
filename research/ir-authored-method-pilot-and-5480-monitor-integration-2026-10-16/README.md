# 著者式の実績入力と継続監視の接続

1975の年次実績を公開資料から確認して外部実装の式を再現し、5480の既存研究を監視台帳へ接続した。金融policy・購入/退出条件・IR送信の採用は行っていない。

| 実処理 | 結果 | 根拠 |
|---|---|---|
| 5480初回監視 | native v2/config1・既読10、全サイクル等は未解決、Jan16retain・再queue0 | [実検証](../ir-case-studies-2026-10-15/5480/native-case-setup-2026-10-16/actual-inputs/actual-verification.json) |
| 1975年次原本1件の保存・分類・比較 | native v3/config1・既読7、質問整理も明示handoff、再queue0 | [実検証](../ir-case-studies-2026-10-15/1975/annual-earnings-book-input-discovery-2026-10-16/actual-connection/actual-verification.json) |
| 1975Graham Number式 | 会社直接表示358.13/1965.51→3979.69円、丸め総額からの別lane→3979.53円 | [算術受入](../ir-case-studies-2026-10-15/1975/graham-number-annual-arithmetic-2026-10-16/parent-acceptance.json) |
| 1975残余質問 | 既答を削除、C2の比較定義だけ条件付き残余。現優先IR0 | [整理の受入](../ir-case-studies-2026-10-15/1975/ir-question-disposition-after-public-review-2026-10-16/parent-acceptance.json) |

09:40UTCの実台帳は213source/分類212、全122job完了、native27case/52版/162既読。旧27tableの全旧行/schemaを保持し、各実検証へ差分を保存した。年次source実初保存は09:34:32.723062UTCで、公表5月14日と分ける。3817の年次候補はfile-onlyで未算入。

Graham Numberは株価表示の観測後に追加した方法探索であり、事前固定の投資試験ではない。NCAV・Graham式・原Graham全条件・金融policyを区別し、望む結果のために方法を選び替えない。新methodのproduction実装・全テストは別の作業として進める。

before-*は共有5文書の変更前全bytes。5480は登録後の確認でclaim応答のid/job_idを読み違えたが、既存receiptのread-only確認で回復し、成功した登録/queue/claimを再実行していない。
