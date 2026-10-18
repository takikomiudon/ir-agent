# RG01修正の独立レビュー：固定checkpoint

**RG01の訂正依存guardは受入可。今回の修正を阻止する所見は0。隣接するlegacy元公開性の不足1件（P2）は、別タスクとして具体的に再現・記録した。** 根拠と13受入条件への対応は[independent-implementation-review.json](independent-implementation-review.json)にある。このレビューはimplementation SHA `82d517a49c0cfbb69c0edc1a6187bf3a724cf9b3918e4a5d33cccb00260d1c46`の時点を固定し、後続修正で上書きしない。

RG01では、既存`source_origins`の全親closureを再利用し、Store-backed plan/freeze/sendに歴史時点とtrusted runtimeの訂正holdを接続した。planは`needs_review`と両締切を明示し、過去as_ofだけで現在holdを隠さない。新評価も同一writer transaction内のsource/thesis追加より前に依存を検査する。`now`の既定採取はBEGIN IMMEDIATE取得後で、書込待ち中に確定した訂正を古い開始時計で無視しない。当該public返信の分類を旧依存のunclearへ転記せず、依存reply ID/版/理由を別に保持する。legacyも**訂正済み依存**なら同じ金融適用guardを通る。

共有DAG・第二親訂正、無関係返信／別会社の不波及、原文／旧版不変、hold評価の例外rollback、public再確認後の明示再評価とCAS、同一要求の再送無変更は、stable codeと新12件の対象テストを読んで照合した。担当の12＋既存91件成功は保存済み実行結果として参照し、独立レビューで再実行したとはしていない。再確認publicだけで自動適用せず、新しい明示評価要求を必要とする。既存モデルの自動差戻しも行わない。

独立に[probe](independent-probe.py)を3件、すべてSQLite `:memory:`で実行した。訂正17:09・新評価申告17:08・runtime17:10でも`applied:false`となり、own返信はpublic、thesis/source/replyは不変。同じ要求の再送でも新writeなしだった。

別の対照で、source `independent-original-unclear`（type `ir_reply`、metadata.reply_id=`demo-reply-cost`、information_status=`unclear`、訂正行0）を持つ場合、契約付き質問はpure preflightで`needs_review`。一方、**契約なしlegacyの新返信適用はv3→v4を保存できた**。actionは`unresolved`／`missing_decision_contract`で、買売候補の無保留昇格ではない。新helperが訂正台帳を読む一方、元metadataの公開性を別途検証しないための隣接不足である。以前からのmutation経路と今回の限定修正の境界に基づきRG01回帰と分けたが、旧moduleを復元・再実行したわけではない。親の指示どおり次の修正・別checkpointで扱い、このレビュー担当はcode/testを変更していない。

親の[全件結果](parent-full-suite.json)は1,324件・40.812秒・exit0。独立レビューはその原記録とSHAを参照した。実DB不変は親の保存証拠であり、こちらで実DBを開いた確認ではない。独立レビューのGET・実DBアクセス・code/test/旧file変更・全suite再実行・金融方針追加・外部送信は0。訂正guard通過を金融入力妥当性やIR追加価値の実証としない。

レビューの時点は、implementationに記録された3ファイルのSHA一致を確認してからcodeを読み、3probeを実行した後、隣接修正が始まったという順序で区別した。最終記録時のSHA再照合では変更を検出し、その新codeは旧レビューの証拠へ混ぜていない。旧code全文copyは保存しておらず、この限界をJSONへ明示した。当時のtool読取抜粋とcheckpointのline/hashだけを示し、原文全体の推定復元やbyte offsetの補完はしていない。probeはRG01時点の隣接欠陥もassertする固定再現で、次修正後の成功テストではない。
