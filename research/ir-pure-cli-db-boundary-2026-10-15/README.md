# 純計算CLIと既定DBの境界：P2を1件確認

**`normalize-facts`等のファイル計算でも、CLIが先に無関係な既定DBを開く。** `main`の`Store(args.db)`は全分岐に先行し、`run`も先に`Harness(store)`を作る。StoreはSQLite接続だけでなく、親directory作成、schema DDL、旧行の保存来歴／保有状態の観測を行う。この依存を必要とする計算ではないため、別workerの作業directoryで余分なDBを作り、DB用pathが使えなければ正常な入力も計算できない。

[reproduce.py](reproduce.py)で、同じ保存済み合成`disclosed-facts.json`を使う**2件だけ**を一時directoryで実行した。

1. `normalize-facts FILE`を`--db`なしで実行すると成功したが、`data/ir-agent.sqlite3`（241,664bytes）と24テーブルができた。sources／theses／companiesの行は0で、bundleをDBへ取り込んだという所見ではない。
2. 別の一時directoryで`data`を通常fileにすると、同じ入力が計算前のmkdirでexit1・stdout空になった。これは再現性のあるpath衝突で、chmod/EACCESの試験ではない。元blockerは不変。

結果は[reproduction.json](reproduction.json)、元code／docs／testsとSHA、正確なallowlistは[review.json](review.json)へ保存した。実研究DBは開いていない。既存DBをStoreが観測・初期化し得ることはcode読取による所見であり、実DBの書換えを再現したという主張ではない。

| DBを開かずに処理できる既存route | 現在の入力境界 |
|---|---|
| `value`、`cycle-margin`、`stable-reinvestment` | 明示ファイルから計算 |
| `information-value`、`screen`、`capacity`、`model-inputs`、`score-probabilities` | 明示configuration／measurements／source snapshot等を読む |
| `normalize-quote`、`normalize-facts` | ファイルの元資料から未importのbundleを返す。normalize-factsのtrusted時計は保持 |
| `decision FILE`、`ir-plan FILE` | **実分岐と文書で確認したsnapshot-only計算**。現在訂正・保存来歴・PITをDBから読む操作ではない |
| `observations summarize FILE` | 明示したrecordsを集計する場合だけ。FILEなしはDB必須 |
| `contacts import --dry-run` | catalogを読んだsummaryだけ。通常importはDB必須 |

上の常時ファイル入力は12 top command、条件付き2 route。他の22 top commandはDB必須で、条件付き2つもその他の操作ではDBを使う。`decision`という名前だけでpureと判定したわけではなく、CLI分岐の`evaluate_decision(load_json(FILE))`、docs/workflowの「仮説・質問・評価履歴をDBへ追加する操作ではない」、保存来歴仕様のcaller snapshotとPITの区別まで確認した。

`decision-review`、`reply evaluate/show/classify`、`question`、`thesis`／`thesis-view`、観測台帳、予測台帳、policy、daily/intake等のStore依存を外さない。`quote from-source`も保存資料の取得と派生資料の永続化が必要で、`normalize-quote FILE`とは別。部分的に入力不正で早期returnする通常importを、結果依存のpure allowlistに含めない。

最小修正案は、明示したファイル計算／dry-runを**Store/Harness生成前に分岐する**こと。既存関数・引数・JSON検証／出力／例外・時計・数値契約は変えない。観測FILE分岐ではregistry生成も後へ移し、contacts明示dry-runは既存builderとsummaryを再利用する。新しい汎用dispatch frameworkやコマンド名変更は不要である。単に`run(args, None)`へ変えるだけでは冒頭のHarness生成で失敗する。

既存CLIテストは一時DB又は`:memory:`を明示し、sources／thesesが増えないことを確認しているが、Store未生成やpath不要は検証していない。修正後は固定allowlistでStoreを呼ばないこと、既定DBを作らないこと、不可能なDBpathでも同じ有効入力を計算できることを追加確認する。保存系／PIT／現在訂正の既存テストを弱めない。

新GET・実DBアクセス・production／tests／旧file変更・全suiteは0。P2の1issueで有限終了し、修正は実施していない。
