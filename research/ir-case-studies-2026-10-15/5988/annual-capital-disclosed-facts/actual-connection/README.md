# 5988 年次14表示値：台帳接続のshadow検証

状態は **shadow成功・actual未実行・接続scriptの独立レビューと親受入待ち**。実DBへはmode=ro/query_onlyで接続し、SQLite backupで作った `/tmp/ir-5988-capital-shadow-ad_k54h3.sqlite3` だけをStore/Harnessの対象にした。実DB main SHAは前後とも `2a36bf74a54c61905bb44926692d2ec89570c66315d0ebbd0bbb4b13f4ad93ce`。実DBの全table行・schemaも前後一致した。実DB書込み、新GET、production code・共有文書・索引・金融入力の採用は0。

`derived-only-bundle.json` は親の凍結済みnormalized-bundleから新派生source `disclosed-facts:1fce07909a0b48066cb45e14c7b72920922a97f859d1efe6b3589f49dd23c94b` だけを元objectのまま切り出す。companies/thesesは空。既存primary原sourceは読取照合だけで、ingestしない。実DB内の元snapshotと全object/日時が一致することを確認した。

`prepare_connection.py` のshadow実行は、source-only ingest → 5988 intake(new_only) → request-ID付きobserved claim（measurement_synthetic=false）→ source_classification complete。各段階で会社、source、job、packet kind/stage、source SHA、lease世代を照合し、begin/succeededをfsync付きjournalへ記録する。実時計を各APIへ渡し、取得宣言時刻と保存receiptを分ける。shadow側first-save `2026-10-16T00:10:51.523354+00:00` はコピー内の保存時刻で、実DB first-saveではない。派生source retrieved_atの00:02:48もbundle生成時刻であり、実DB保存を証明しない。

コピーではsource、availability、classification、job、attempt、request receiptが各+1、attempt eventが+2。旧84jobの全行、30case版、最新16caseの既読source計97、会社/position/金融関連全行を保持。全tableの旧row集合と期待差分を検証し、単なる件数一致には依存しない。分類は `other`/financial_content=true、正規化content内の逐語引用と「両期・両年度の14歴史表示値の構造化」という理由を保存した。分類は財務数値の意味・現時点適合・金融モデル採用を認証しない。

最初のshadowはStore初期化直後の検査で停止した。raw sqliteのtupleとStoreのsqlite3.Rowをschema比較で直接比べた検証scriptの型差だった。保存したコピーと実DBをreadonlyで再照合すると全行・schemaは一致し、ingest/queue/claim/completeは呼ばれていなかった。初版scriptと失敗receiptは `failed-shadow-initial/` に完全保存。schema結果をtuple化するだけ修正し、新しいコピーで1回成功した。成功済mutatorの再送はない。

9件のoffline guard checksは、欠けた受入、SHA不一致、未受入status、script/shadow pin差、親受入と独立レビューの不一致、actor誤り、およびrow_factory比較の回帰を検証した。合格形式のテストJSONも一時的なsynthetic parser fixtureであり、actual実行や承認には使っていない。full suiteは実行していない。

親によるactual実行は同scriptで `--mode actual --actor root` を明示し、独立接続レビュー/親接続受入のパスと期待SHAをそれぞれ `--independent-review` / `--independent-review-sha256` / `--parent-acceptance` / `--parent-acceptance-sha256` で渡す。JSONの必要status/keysと固定pinは `acceptance-requirements.json` に記録。親ディレクトリの14fact原文レビューとは別に、このscript/shadowを受け入れるreceiptを要求する。scriptはactorの認証基盤ではなく、親がレビューしたファイルを明示する運用guardである。

actualでは期待main SHA、実DBの派生ID不在、pending/leased=0、元source snapshot一致、旧84job/30case版/97reviewed、全table一致のbackup完了、同modeの新規journalを要求する。Storeを実DBへ開く直前にもmain SHA/全行/schemaを再確認する。親が単独writerであることが前提で、同時書込みを調停する機構ではない。実行中の各APIは個別commitであり、全pipelineは単一transactionではない。失敗/不確定時はerrorとjournalを確認して止め、成功mutatorを無条件に再送しない。同modeのjournal/completion/errorが既存なら再実行を拒否する。

freeze時点のSHA一覧はmanifest、全table比較はshadow-completion、実呼出し順はshadow-stage、検証要約はvalidationに保持。未準備のIR質問、数値thesis、売買判断、ROC/EV/税率計算は追加していない。
