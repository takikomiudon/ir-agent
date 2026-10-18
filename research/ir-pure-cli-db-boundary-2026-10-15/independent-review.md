# 独立review：pure CLIのDB起動回避

**固定差分の範囲でblocking所見0。** 修正前後のCLI全文と新test全文を読み、currentの `cli.py`／`test_pure_cli_db_boundary.py` がsource-afterとbyte一致することを開始・終了時に確認した。SHAはそれぞれ `2eed88fd33a8a005ec8597254323fe02bd04383f37c434d9f78b11bc39eacca2`／`7dadfeda4cddce8b90111b53c8d992939b7d29935f2ef622c99ac88ab1d57186`。

- 12 top pureと、FILE付き `observations summarize`／明示 `contacts import --dry-run` だけがStore/Harness生成前へ進む。no-FILE、空文字FILE、その他観測操作と通常contacts importはDB側のまま。入力の拒否行があるという理由で通常importをpureにしていない。
- 移動した11個のif文（12 command）、残るDB run文、parser、mainの出力・例外・finallyはAST一致。既存の計算関数・引数・JSON検証・金銭計算・close契約を変更していない。
- `decision`／`ir-plan` は修正前も `evaluate(load_json(FILE))` のsnapshot計算で、DBの現在訂正・PIT・保存来歴を検証する分岐ではなかった。保存系のreview/reply/question等をDBから切り離した変更ではない。
- `normalize-facts` はtrusted `now_iso()` を引き続き渡す。時計不要になったわけではなく、Store起動時間がなくなる前後で実際のmicrosecondまで同じと主張しない。
- 条件付き2経路は既存records/as_of・catalog builder/summary/rejected_rowsを使う。通常DB経路の構造は不変。

[独立probe](independent-probe.py)を1回実行し、3比較（main計6呼出）に限定した。[結果](independent-probe.json)は、固定時計normalize-factsの全出力、拒否1行入りcontacts明示dry-runの全出力、no-FILE観測集計の全出力が修正前後で一致。前者2件は修正後のStore/Harness呼出を禁止し、後者は両方で1回ずつmemory Storeを開閉した。起動したSQLiteは合計4個の`:memory:`だけ。一時blockerと既定data未作成も確認した。

修正前側はStoreを`:memory:`へ置換して副作用なしに出力比較した。元CLIが不可能なDBpathで成功したという再現ではない。旧12入力のhashは不変で、実研究DB・GET・code/tests/旧ファイル変更は0。新7testの実行成功は既存implementation記録を参照し、ここではtarget/full suiteを重複実行していない。

[independent-review.json](independent-review.json)に固定対象・引用位置・照合・限界を保存した。全DB routeのruntime動作や今後のparser変更まで保証するものではない。親の予定している全suite1回へ進める妨げとなる修正要求はない。
