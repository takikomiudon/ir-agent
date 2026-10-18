# 構造化25資料を実台帳へ接続

2026-10-15 22:28:52.999091 UTCに、既存16社の派生25source・91factを保存し、16件の分類jobを完了した。実台帳は150source（公開149・市場1）、分類149、完了job73、attempt70/event140/request receipt70。金融入力・policy・質問・保有申告の採用は0で、native監視は15case/19版/70既読のまま。

[受入記録](parent-acceptance.json)は候補・原典snapshot・一時検証・実stage・実保存receiptを固定する。索引v23は26親entryだが、fact単位のoverrideを解決すると28source・101factになる。既存5988BS1sourceと、実会社/原典がない8331/9702の2sourceを除いた25sourceを接続した。最初の親entryだけの候補23sourceに含まれていなかった5480売上1値と135A CF4値も、既存再現証拠と原典同値を確認した。旧候補/件数の記録は保持した。

全27tableの既存全行を保持し、20tableは全行完全一致。追加はsource/availability/classification各25、job/attempt/request receipt各16、event32だけ。全分類は派生財務資料としてother・financial_content:trueで、原典のfinancial statement分類やfinancial_inputs_verified:falseを変えていない。

保存・分類の全API完了後、最終照合SQLで存在しないrecord_id列を参照した。段階記録と[エラー](actual-error-v2.json)を保持し、entity_type/entity_idで読み取り専用に照合し直した。[最終結果](actual-completion-v2.json)は全既存行・25原snapshot・分類内容・16完了job・実初回保存receiptを照合済み。ingest/queue/claim/completeは再実行していない。各APIは通常の個別transactionであり、全工程が単一transactionではない。

元のretrieved_atを保持し、今回の実firstsaveを過去へ遡らせない。新GET・コード変更・実送信・注文は0。データだけの変更のため、受入済み1,512件の全コードテストは繰り返していない。producerの[候補/一時DB記録](README.md)とfreezeは過去時点のまま保持し、本書を実適用後の状態として読む。
