# 公開情報レビュー参照固定の独立点検

設計とfreeze v1の6変更fileを読み、有限4項目だけ合成確認した。2点の反例を報告し、別freezeの修正diffを読んで同じ2反例だけ再確認した。**両方、今回の合成範囲で解消済み。** 実DB/GET/共有コード変更は0。

1. **F1：長い原典参照の保存時失敗。** pureは1100祖先を受理するが、保存時の既存`Store.source_availability`再帰で`RecursionError`。メモリDBはrollbackし不変。既存walker由来の境界であり、新field以外を勝手に拡張しない。`synthetic-results.json`。
2. **F2：同社の別返信本文への訂正履歴の誤結合。** source.contentとstored reply.raw_textが違っても会社一致だけで初回理由なしを保存でき、そのreplyへの後日訂正が当sourceへ結び付く。既存`ResearchDecisions._reply_bindings`同様の本文identity点検が、新fieldの参照消費時の最小候補。`reply-content-results.json`。

未導入pure出力は保存済旧decision.pyと3variantでexact JSON一致。同名余剰servercheckだけの旧入力は非consumeをコード/既存専用testで確認。review時のみunclear→質問境界/runtimeでpublicへ再確認した場合も保留を保持し、送信状態記録を拒否、メモリDB不変を独立確認した。

原文SHA/quote・scopeは意味上の不存在や実読の証明ではない。review資料はplan専用poolで、thesis証拠・金融採用・他用途sources_forへ昇格しない。immutable retry/新規書込の外側BEGIN IMMEDIATE・receipt原子性は差分と専用testsを読んだ。フルsuite再実行はroot担当。この点検から新金融ルール/送信許可は作らない。

`review.json`と最初の結果はfreeze v1の履歴として不変。別freezeの`fix.diff`を読んだ後、`post-fix-checks.py`/`post-fix-results.json`で同じ2反例だけを再確認した。

- F1修正：反復で検証済みの全closureについて、既存RecordAvailability.atを各sourceに平坦適用。1100祖先inputで1101receiptがavailableとなり、合成draft保存・送信状態記録・元requestretryに成功した。Store全体や金融経路を変更していない。
- F2修正：新fieldが訂正履歴を消費する前にreply/questionの保存ID・会社・source.contentとreply.raw_textの完全一致を点検。同一wrongbody反例はValueErrorで拒否し、メモリDB不変を確認した。

修正後6fileのpinとimplementation SHAはpost-fix結果へ保持した。全文suite・より広い旧出力byte比較はroot担当。ここで追加探索を終了しfreezeする。意味上の回答不存在・実読・金融採用・外部送信は認証していない。
