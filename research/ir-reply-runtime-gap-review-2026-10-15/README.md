# 返信適用runtimeの限定レビュー

**P1・1件：旧依存返信の公開性訂正が、新質問の送信検査と新しい財務入力適用の直前に接続されていない。** 現在の売買候補は正しく保留されるが、財務仮説の新しい版は既に保存される。

既存synthetic fixtureだけを使い、SQLite `:memory:` で再現した。旧q1のpublic返信を適用したv2（base EPS70）について、旧返信を17:02にunclearへ訂正する。その返信を根拠とする新q2は17:06のpreflightが`decision_distinguishing`となり、17:07の`mark_sent`も`awaiting_reply`を返す。新しい別public返信へ既存persistent分岐を17:10に適用すると、`applied:true`でv3（EPS40）を保存する。その後のdecision reviewで初めて旧依存の訂正を見て、actionを`unresolved`へ保留する。価格は有効、版も整合し、変更は事前許可されたEPS pathのみなので、別の防御を故意に破った再現ではない。

| 接続点 | 修正前のコードと不足 |
|---|---|
| 新question/send | [lifecycle.py:88](../../src/ir_agent/decision_lifecycle.py#L88)のplanはsource snapshotをpure ir-planへ渡すだけ。[100](../../src/ir_agent/decision_lifecycle.py#L100)のsend再点検も同じ経路で、live分類訂正を重ねない。 |
| 新replyの金融適用 | [harness.py:477](../../src/ir_agent/harness.py#L477)の訂正確認は当該replyだけ。[496](../../src/ir_agent/harness.py#L496)以降のsource/thesis保存後、[lifecycle.py:138](../../src/ir_agent/decision_lifecycle.py#L138)で依存側holdを確認する。 |
| 全parentの取扱い | [sources_for:25](../../src/ir_agent/decision_lifecycle.py#L25)は既に全parent closureを収集する。一方[source_assessments:154](../../src/ir_agent/information_review.py#L154)は渡されたIDだけを見る。前者の全closureを後者へ渡してguardする最小接続が必要。 |

根拠は[方針の適応#4](../../docs/decision-policy.md#L37)の「公開情報の補足と確認できない返信は適用を保留する」。これは過去のv2を自動差戻しする要求ではなく、未解決の依存上で新たな処理を進めないための接続不足である。pure `ir-plan FILE`へlive DB参照を付ける必要はない。

最小修正は、Store-backed plan/sendで全依存の最新visible分類を点検して保留を返し、reply適用の同じtransaction内ではsource/thesis追加より前に同じ依存holdを確認すること。当該新返信の`information_status`と、旧依存側のhold理由・ID/版を区別し、publicである新返信を旧依存の理由でunclearと誤分類しない。新規writeではtrusted runtimeで既知の訂正を申告過去時刻で回避させず、過去結果と正当な再送の不変性は維持する。

対照も2件確認した。当該新返信自体をunclear訂正すると`applied:false`でv2/EPS70を維持する。後段で未知quote sourceを参照させると例外になり、全DB dumpが前後一致する。現在の原子的rollbackに欠陥があるという報告ではない。

既存テストは、当該返信の訂正hold、current表示、分岐不変、許可path、rollback、全parent収集、第二親訂正によるdaily jobを既に検証している。今回不足するのは、次のquestion/sendと別replyの適用の接続である。詳しいテスト名・修正範囲・checkpoint hashは[review.json](review.json)。実行可能な[再現script](reproduce.py)と[3ケースの保存結果](reproduction.json)を残した。修正前挙動を固定したassertionであり、修正後はbug-path assertionが失敗することを期待する。

GET・実DBアクセス/変更・本体/既存テスト/既存研究変更・全suite・新金融方針・外部送信は0。この1件で有限終了した。
