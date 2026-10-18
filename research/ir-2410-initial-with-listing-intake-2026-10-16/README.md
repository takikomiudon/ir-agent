2410キャリアデザインセンターの受入済み原PDF2件を、1intake job／2分類で実保存する **file-only準備** です。初回Q3短信と10月1日監理銘柄告知の各 `/sources/0` 全objectだけを抽出し、新bundleはcompanies/theses空としました。producer bundle内の既存会社snapshotは再投入せず、企業masterの変更を防ぎます。原source/producerは不変です。

| 原source | 分類 | 原文basis |
|---|---|---|
| 7月31日Q3短信 | financial_statement / financial_content:true | p1の日本基準・非連結の短信題名 |
| 10月1日監理銘柄（審査中）告知 | other / financial_content:false | p1の正式告知題名 |

両方expected_version0、厳密6field requestです。既存Intake.completeは保存inputs_verified:falseを固定するため、requestへ追加fieldを足しません。逐語basisのUnicode/UTF8位置、元quote ID/file SHA、native source SHAを `classification-evidence.json` に固定しました。

短信はQ3累計2025-10-01〜2026-06-30と当時FY会社予想2025-10-01〜2026-09-30を分け、初回意味1/2/4/5頁のscopeを保存します。告知は指定/申請・条件付き審査手続の公表で、財務数値・将来利益の資料ではありません。監理を整理/廃止/TOBへ移さず、当時の通常売買説明を現在の指定解除・市場・約定保証としません。投資除外や投機推奨、金融値採用はいずれも0です。双方の公表日は日精度・published_at:null、原HTTP完了時刻を保持し、actual firstsaveを先付けしません。

追加PL/notes読解は同じ短信原sourceの補助で、新sourceにせず、この準備pinにも含めません。normalizer／新numeric fact／派生sourceの生成は0。入力pinは初回・告知の凍結manifest列挙＋manifest/親受入だけの52filesです。

baselineはroot指定main SHA `206575b65cfba0876b277656bc253f02cd43cc4116d107058c42d61d33b86c5b`、205source204分類114全完了jobs、111attempt222event111receipt、24case46版142既読、2410既存source0です。`baseline-reference.json`は直前のroot受入receiptへの参照で、今回実DBへの接続・file読取は行っていません。実行時にrunnerがbaseline/新ID未登録/既存companyをROで確認します。

`run_once.py`は受入済みsingle-source runnerから会社/baseline/worker/要求ID/backup名・source/分類数2・期待増分だけを変更しました。`adapted-runner.diff`保存、AST parseのみ。現44codeは1558テスト受入のmanifest SHA `9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60` と同bytes・全SHA一致です。将来code変更時は旧preparedを上書きせずrootが別受入manifestを明示します。

rootが新 `parent-input-acceptance.json` を作成後、rootのみshadowを一度実行します。

```bash
.venv/bin/python research/ir-2410-initial-with-listing-intake-2026-10-16/run_once.py shadow --execution-code-pins research/ir-2410-initial-with-listing-intake-2026-10-16/prepared-code-pins.json --execution-code-pins-sha256 9c8e77b590094942fcd3fd9f2fbe260e02559b0cd29b9dc3caf9c3f03e711e60
```

同じdata/runner/codeの成功shadow・全27table旧row/schema/case保持をrootが確認してから、stageをactualにしてrootのみ一度実行します。actualは親入力受入・成功shadow/pins一致・main SHA・新stage journal/backupを要求。copy-firstでsource-only ingest2→new_only intake1job/2source→要求ID付きobserved claim→complete(expected_attempt1)。各API直前の実UTCとfsyncするbegin/succeeded journalを使います。全pipelineは単一transactionではなく、失敗/不明時はjournal/backupを点検し、成功済み/不確実mutatorを再送しません。

将来期待増分はsources/availability/classes各+2、job/attempt/requestreceipt各+1、event+2のみ。207source206分類115全完了jobs、112attempt224event112receipt、2410資料0→2、case24/46/142・全旧row/schema/金融records不変を検証する予定であり、今回の成功件数ではありません。

初回のfile-only外形検査はproducer companies:[]を想定して停止したため、各source全objectだけの抽出へ訂正しました。DB/出力生成前の診断であり、元会社snapshot/sourceは変更していません。`preparation-correction.json`を保持します。

実DB接続/読取/書込・Store初期化・backup/copy・runner/shadow/actual・GET・normalizer・共有docs/旧producer/production変更・金融採用・IR/注文0。14準備filesをfreezeし、rootレビュー待ちで停止します。
