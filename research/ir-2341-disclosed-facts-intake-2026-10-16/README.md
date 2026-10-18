2341受入済み12factの **派生source1件だけを投入するfile-only準備** です。[受入bundle](../ir-case-studies-2026-10-15/2341/disclosed-facts-2026-10-16/normalized-bundle.json)の `/sources/1` を全object不変で抽出しました。既存 `/sources/0` は準備bundleに含めず、再ingest・再分類しません。primary normalizer／reproducerの再実行も0です。

分類は既存Intake enumの `other` / `financial_content:true` / expected_version0。受入済み2315派生の分類例と同じ区分で、原PDFのfinancial_statementと区別します。原文引用は派生source.contentのcanonical JSON内に直接あるraw_period_label／raw_unit_label／raw_valueの連続部分です。表示整形を新たに作らず、Unicode/UTF8 byte位置・native source SHAへ固定しました。厳密な6field requestにinputs_verifiedを追加せず、既存Intake.completeが保存するfalseを維持します。

中間P/L千円実績4値・基本EPS・当時会社通期予想5値・明示中間DPS0.00・会社予想年間合計5.00という12表示の区別を保存します。年間合計は右端セルで、期末セルや合算から作りません。配当の年度両端・基準日・会計/連結null、現在予想/現在EPS分母未認証、予想修正の比較点・特別益/正常利益の区別は受入scopeのままです。原metadata/content/ID/派生処理時刻を変更せず、実初回保存を先付けしません。

root受入済み直前のbaselineはmain SHA `69c954bc8b218cba99ae7b2f0a152efdb6025a11f0eee70c3604fa11823c720d`、204source/203分類/113全完了jobs、110attempt220event110receipt、24case46版142既読、2341既存source1件です。`baseline-reference.json`は親の成功receiptへの参照で、今回実DBの接続・file読取は行っていません。実行時は既存原source全objectが受入bundleのsource[0]と一致することもROでguardします。

`input-pins.json`は受入済み派生producer manifest列挙ファイル＋manifest/親受入と、既存原source bundle/実受入の16files。後続未受入資料は依存へ足しません。`prepared-code-pins.json`は現src44filesで受入済み1558テストのmanifest SHA `9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60` と同bytesです。

`run_once.py`は成功済み初回1source runnerを新folderへ限定adaptしました。新baseline/counts、既存2341資料1件、worker/request ID、backup名、原source全object照合だけを変更し、`adapted-runner.diff`を保存。AST parseのみでimport/実行は0です。旧成功runnerは再実行しません。

rootが新 `parent-input-acceptance.json` を作成し、rootのみが一度shadowを実行します。

```bash
.venv/bin/python research/ir-2341-disclosed-facts-intake-2026-10-16/run_once.py shadow --execution-code-pins research/ir-2341-disclosed-facts-intake-2026-10-16/prepared-code-pins.json --execution-code-pins-sha256 9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60
```

同じrunner/data/codeの成功shadowと全旧row/schema保持をrootが確認した後、stageをactualに変えてrootのみ一度実行します。actualは親入力受入、shadow/pins一致、main SHA、新stage journal、新規backupを要求。copy-firstでsource-only ingest→new_only intake1job→要求ID付きobserved claim→complete(expected_attempt1)です。各API直前の実UTCを用い、begin/succeededをfsyncします。全pipelineは単一transactionではないため、失敗・不明時はjournal/backupを点検し、既成功/不確実mutatorを再送しません。

検証すべき将来増分はsource/availability/classification/job/attempt/requestreceipt各+1・event+2だけ。将来205source/204分類/114全完了jobs、111attempt222event111receipt、2341資料1→2、24case46版142既読と全27旧tableの旧row/schema・企業master・金融recordは不変であるべきです。これは今回の成功件数ではありません。

DB接続/書込/file読取・Store初期化・backup/copy・runner/shadow/actual・GET・normalizer再実行・共有/旧producer/production変更・金融採用・IR/注文はいずれも0。rootレビュー待ちでfreeze停止します。
